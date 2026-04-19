"""Core agent assembly — wires LLM, tools, memory, and prompt into an AgentExecutor."""

import json
import time
import traceback

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.memory import create_memory
from agent.prompts import SYSTEM_PROMPT
from agent.tools import get_all_tools
from config.settings import settings


def _build_prompt() -> ChatPromptTemplate:
    """Construct the full prompt template for the tool-calling agent."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


def create_agent() -> tuple[AgentExecutor, "ConversationBufferWindowMemory"]:
    """Create and return the configured AgentExecutor and its memory.

    Returns:
        A tuple of (agent_executor, memory) so the caller can manage the
        lifecycle and reuse memory across interactions.
    """
    if not settings.google_api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        google_api_key=settings.google_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_tokens,
    )

    tools = get_all_tools()
    memory = create_memory()
    prompt = _build_prompt()

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=settings.max_agent_iterations,
        return_intermediate_steps=True,
    )

    return executor, memory


def run_agent_with_retry(
    executor: AgentExecutor, user_input: str
) -> dict:
    """Invoke the agent with retry logic. Returns structured output dict.

    Retries up to `settings.agent_retry_attempts` times on transient errors.
    """
    last_error = None

    for attempt in range(1, settings.agent_retry_attempts + 1):
        try:
            raw_result = executor.invoke({"input": user_input})
            return parse_agent_output(raw_result, user_input)

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            last_error = exc
            if attempt < settings.agent_retry_attempts:
                wait = 2 ** attempt
                print(
                    f"\n⚠ Agent error (attempt {attempt}/"
                    f"{settings.agent_retry_attempts}): {exc}"
                )
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"\n✗ Agent failed after {attempt} attempts.")

    # All retries exhausted — return error envelope
    return {
        "query": user_input,
        "thoughts": "Agent encountered an error during processing.",
        "actions_taken": [],
        "root_cause": f"Agent error: {last_error}",
        "suggested_fix": "Check API key, network connectivity, and try again.",
        "confidence": "low",
    }


def parse_agent_output(raw_result: dict, original_query: str) -> dict:
    """Extract structured JSON from the agent's final answer.

    Falls back to wrapping the raw text if JSON extraction fails.
    """
    output_text = raw_result.get("output", "")

    # Collect tool names from intermediate steps
    actions_taken = []
    for step in raw_result.get("intermediate_steps", []):
        action = step[0] if step else None
        if action and hasattr(action, "tool"):
            actions_taken.append(f"{action.tool}({action.tool_input})")

    # Try to extract JSON from the output
    try:
        # Look for JSON block (possibly wrapped in markdown fences)
        json_match = _extract_json(output_text)
        if json_match:
            parsed = json.loads(json_match)
            # Ensure required fields exist, merge in what we know
            parsed.setdefault("query", original_query)
            parsed.setdefault("actions_taken", actions_taken)
            parsed.setdefault("confidence", "medium")
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: wrap raw text into the expected schema
    return {
        "query": original_query,
        "thoughts": output_text,
        "actions_taken": actions_taken,
        "root_cause": _extract_section(output_text, "root cause"),
        "suggested_fix": _extract_section(output_text, "suggested fix", "recommendation"),
        "confidence": _extract_confidence(output_text),
    }


def _extract_json(text: str) -> str | None:
    """Try to pull a JSON object from text, handling markdown fences."""
    # Try markdown-fenced JSON first
    import re

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    # Try bare JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]

    return None


def _extract_section(text: str, *keywords: str) -> str:
    """Best-effort extraction of a section from unstructured text."""
    lower = text.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1:
            # Grab text after the keyword until next double newline or end
            after = text[idx:]
            end = after.find("\n\n")
            return after[: end].strip() if end != -1 else after.strip()
    return "Unable to extract — see thoughts for full analysis."


def _extract_confidence(text: str) -> str:
    """Extract confidence level from free text."""
    lower = text.lower()
    if "high" in lower and "confidence" in lower:
        return "high"
    if "low" in lower and "confidence" in lower:
        return "low"
    return "medium"
