# 🤖 Agentic AI for Legacy Applications

An AI-powered autonomous agent that investigates production incidents in legacy systems using natural language. Built with **LangChain**, **Gemini 2.5 Flash**, and the **ReAct reasoning pattern**.

> **⚠️ This is a Proof of Concept (POC).**
> All data sources (logs, database, APIs) are **simulated locally** with realistic mock data.
> No real production systems are connected. See [From POC to Production](#-from-poc-to-production) for how to connect real data sources.

## 🎯 Problem Statement

Legacy enterprise applications often lack modern observability (no Datadog, no Grafana, no structured logging). When production incidents happen, engineers must **manually** grep through flat log files, query databases with hand-written SQL, and follow runbook procedures — a process that takes hours and requires deep tribal knowledge.

**This agent automates that entire workflow.** A user asks a question in plain English, and the agent autonomously investigates, correlates evidence across multiple sources, and delivers a structured incident report — in seconds.

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                      CLI (main.py)                   │
│            Interactive input/output loop              │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│              AgentExecutor (ReAct Pattern)            │
│                                                      │
│  ┌─────────┐   ┌──────────┐   ┌──────────────────┐  │
│  │ Thought  │──▶│  Action   │──▶│   Observation    │  │
│  └─────────┘   └──────────┘   └──────────────────┘  │
│       ▲                              │               │
│       └──────────────────────────────┘               │
│                                                      │
│  LLM: Google Gemini 2.5 Flash                        │
│  Memory: ConversationBufferWindowMemory (k=3)        │
└──────────────────────┬───────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌──────────┐ ┌──────────────┐
   │ search_logs│ │query_db  │ │recovery_api  │
   │            │ │  (mock)  │ │ (simulated)  │
   └─────┬──────┘ └────┬─────┘ └──────┬───────┘
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐  ┌───────────┐  ┌────────────┐
   │ logs.txt │  │ MockDB    │  │ API Sim    │
   └──────────┘  └───────────┘  └────────────┘
```

### How the Agent Works

1. **User submits a query** via the CLI (e.g., "Why did payments fail yesterday?")
2. **Agent reasons** using the ReAct pattern: Thought → Action → Observation, looping until it has enough evidence
3. **Tool selection** — the agent autonomously decides which tools to call:
   - `search_logs` — scans application logs for relevant entries
   - `query_database` — queries mock order/transaction database
   - `trigger_recovery_api` — simulates triggering a payment retry
4. **Structured output** — the agent produces a JSON investigation report with root cause, suggested fix, and confidence score

### Key Design Decisions

- **ReAct pattern** ensures transparent, explainable reasoning (every step is visible)
- **Tool registry** (`get_all_tools()`) makes it trivial to add new tools
- **Retry logic** at the agent level (2 attempts) handles transient LLM errors
- **Sliding window memory** (k=3) keeps conversation context without unbounded growth
- **All external calls are simulated** — safe for demos and development

## 📁 Project Structure

```
agentic_poc/
├── main.py                  # CLI entry point
├── .env.example             # API key template
├── requirements.txt         # Python dependencies
│
├── agent/
│   ├── agent.py             # AgentExecutor assembly, retry logic, output parsing
│   ├── tools.py             # Tool definitions + modular registry
│   ├── prompts.py           # System prompt with ReAct instructions
│   └── memory.py            # Conversation memory factory
│
├── config/
│   └── settings.py          # Pydantic-settings configuration
│
├── data/
│   └── logs.txt             # Realistic sample application logs
│
└── services/
    ├── db.py                # Mock database with order/transaction records
    └── api_simulator.py     # Simulated recovery API
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Google Gemini 2.5 Flash | Natural language understanding, reasoning, tool selection |
| **Agent Framework** | LangChain (AgentExecutor) | ReAct loop orchestration, tool binding, memory |
| **Configuration** | Pydantic Settings | Type-safe, env-based configuration |
| **Data Sources** | Local mock data | Simulated logs, database, and APIs (see [POC to Production](#-from-poc-to-production)) |
| **Language** | Python 3.11+ | Core implementation |

## ⚙️ Setup

### Prerequisites

- Python 3.11+
- A Google AI API key ([get one here](https://aistudio.google.com/apikey))

### Installation

```bash
# 1. Navigate to the project
cd agentic_poc

# 2. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Edit .env and set your GOOGLE_API_KEY
```

### Run

```bash
python main.py
```

## 📋 Example Inputs and Outputs

### Example 1: Investigating payment failures

**Input:**
```
Why did order processing fail yesterday?
```

**Expected Output:**
```json
{
  "query": "Why did order processing fail yesterday?",
  "thoughts": "I searched the logs and found multiple ERROR entries indicating payment timeouts and DB connection pool exhaustion during the batch processing job at 02:15. The payment gateway was timing out after 5000ms, and the connection pool hit its limit of 20 connections. The circuit breaker eventually opened, halting processing. Database query confirmed 5 failed orders.",
  "actions_taken": [
    "search_logs(error fail) — found 15 matching log entries",
    "query_database(show failed orders) — found 5 failed orders",
    "query_database(order summary) — confirmed 62.5% failure rate"
  ],
  "root_cause": "Two concurrent issues caused the failures: (1) The upstream payment gateway became unresponsive, causing PAYMENT_TIMEOUT errors for orders ORD-10483, ORD-10485, ORD-10490. (2) The database connection pool was exhausted (20/20 connections), causing DB_CONNECTION_EXHAUSTED errors for orders ORD-10484 and ORD-10491. The combination triggered the circuit breaker, halting the batch.",
  "suggested_fix": "1. Increase DB connection pool size or add connection timeout/eviction policies. 2. Add shorter timeouts for the payment gateway with proper fallback. 3. Retry the 5 failed orders: ORD-10483, ORD-10484, ORD-10485, ORD-10490, ORD-10491.",
  "confidence": "high"
}
```

### Example 2: Checking a specific order

**Input:**
```
What happened to order ORD-10483?
```

**Expected Output:**
```json
{
  "query": "What happened to order ORD-10483?",
  "thoughts": "Log search shows ORD-10483 ($1,024.00) had 3 payment attempts, all timing out after 5000ms each. The retry handler scheduled retries with exponential backoff (2s, 4s). Database confirms status FAILED with error code PAYMENT_TIMEOUT and no transaction ID assigned.",
  "actions_taken": [
    "search_logs(ORD-10483) — found payment timeout and retry entries",
    "query_database(order ORD-10483) — confirmed FAILED status"
  ],
  "root_cause": "Order ORD-10483 failed because the upstream payment provider was unresponsive. All 3 retry attempts timed out after 5000ms each.",
  "suggested_fix": "Trigger a manual payment retry now that the payment gateway has recovered (logs show it came back online at 02:15:42).",
  "confidence": "high"
}
```

### Example 3: Triggering recovery

**Input:**
```
Can you retry the payment for ORD-10483?
```

**Expected Output:**
```json
{
  "query": "Can you retry the payment for ORD-10483?",
  "thoughts": "User requested a payment retry for ORD-10483. I verified the order is in FAILED state with PAYMENT_TIMEOUT error, making it eligible for retry. Triggered the simulated recovery API.",
  "actions_taken": [
    "query_database(order ORD-10483) — confirmed FAILED/PAYMENT_TIMEOUT",
    "trigger_recovery_api(ORD-10483) — retry initiated successfully"
  ],
  "root_cause": "ORD-10483 originally failed due to payment gateway timeout.",
  "suggested_fix": "Retry has been initiated. Monitor for completion in 2-5 minutes. If it fails again, escalate to the payment provider.",
  "confidence": "high"
}
```

## 🔧 Tools Reference

| Tool | Purpose | Input | Safety |
|------|---------|-------|--------|
| `search_logs` | Scan application logs by keyword | Keywords (e.g., "payment timeout") | Read-only |
| `query_database` | Query order/transaction records | Natural language query | Read-only (mock) |
| `trigger_recovery_api` | Retry a failed payment | Order ID (e.g., "ORD-10483") | Simulated only |

> **Note:** In this POC, all tools operate on **local mock data**. No real systems are contacted. The log file is a pre-generated text file, the database is an in-memory Python object, and the recovery API simulates responses locally.

## ➕ Adding New Tools

1. Create a new `@tool`-decorated function in `agent/tools.py`
2. Add it to the `_ALL_TOOLS` list
3. The agent will automatically discover and use it based on the tool's docstring

```python
@tool
def check_service_health(service_name: str) -> str:
    """Check the health status of a legacy service component."""
    # Your implementation here
    ...

_ALL_TOOLS = [search_logs, query_database, trigger_recovery_api, check_service_health]
```

## 🚀 From POC to Production

This POC uses **simulated local data** to demonstrate the agentic pattern without requiring any infrastructure. In a real-world deployment, you would swap the mock tools for real integrations — **without changing the agent core or prompt logic**.

### What's Simulated vs. What's Real

| Component | POC (This Repo) | Production |
|-----------|-----------------|------------|
| **Log Source** | Local `logs.txt` file with pre-generated entries | Splunk, ELK/OpenSearch, CloudWatch Logs, or Datadog API |
| **Database** | In-memory Python dict with 7 mock orders | Read-only SQL connection to legacy Oracle/MySQL/PostgreSQL DB |
| **Recovery API** | Simulated locally with random success/failure | REST/SOAP call to actual legacy system (with approval gates) |
| **LLM** | Google Gemini 2.5 Flash (cloud API) | Self-hosted LLM (Ollama/vLLM) for data privacy, or Azure OpenAI with enterprise data agreements |
| **Interface** | CLI (`input()` loop) | Slack bot, web dashboard, or ServiceNow integration |
| **Authentication** | None | SSO, role-based access, audit logging |
| **Memory** | In-process sliding window (lost on restart) | Redis/PostgreSQL-backed persistent memory |

### Example: Replacing the Mock Database with Real SQL

```python
# POC (current) — mock data in services/db.py
@tool
def query_database(query: str) -> str:
    results = mock_db.query_orders(filters)
    return json.dumps(results)

# Production — real database connection
import sqlalchemy

@tool
def query_database(query: str) -> str:
    engine = sqlalchemy.create_engine(settings.db_connection_string)
    with engine.connect() as conn:
        # Use LLM to generate safe, parameterized SQL from natural language
        # Or use predefined query templates
        result = conn.execute(text("SELECT * FROM orders WHERE status = :status"), {"status": "FAILED"})
        return json.dumps([dict(row) for row in result])
```

### Production Considerations

- **Data Privacy**: LLM API calls send tool outputs (log lines, DB records) to the cloud provider. For sensitive data, use a self-hosted LLM or redact PII before sending.
- **Safety Gates**: The `trigger_recovery_api` tool should require human approval before executing destructive/mutating actions in production.
- **Observability**: Add LangSmith or custom tracing to monitor agent reasoning, tool calls, and token usage.
- **Rate Limiting**: Implement per-user rate limits to prevent runaway agent loops from exhausting API quotas.

## 📄 License

MIT

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) — Agent framework
- [Google Gemini](https://ai.google.dev/) — LLM provider
- Built as a portfolio project demonstrating **Agentic AI patterns for enterprise legacy systems**
