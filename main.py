#!/usr/bin/env python3
"""Agentic AI for Legacy Applications — CLI entry point.

Run:
    cd agentic_poc
    python main.py
"""

import json
import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv

from agent.agent import create_agent, run_agent_with_retry


BANNER = r"""
╔═══════════════════════════════════════════════════════════╗
║        Agentic AI — Legacy Application Investigator       ║
║                                                           ║
║  Ask questions about production issues in natural language ║
║  Type 'exit' or 'quit' to leave.                          ║
╚═══════════════════════════════════════════════════════════╝
"""

EXAMPLE_QUERIES = [
    "Why did order processing fail yesterday?",
    "Show me all payment timeout errors",
    "What happened to order ORD-10483?",
    "Can you retry the failed payments?",
]


def main() -> None:
    # Load .env from project root
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)

    print(BANNER)

    # Initialize agent
    try:
        executor, memory = create_agent()
    except EnvironmentError as exc:
        print(f"\n✗ Configuration error: {exc}")
        print("  → Copy .env.example to .env and set your GOOGLE_API_KEY.")
        sys.exit(1)
    except Exception as exc:
        print(f"\n✗ Failed to initialize agent: {exc}")
        sys.exit(1)

    print("Agent ready. Example queries you can try:\n")
    for i, q in enumerate(EXAMPLE_QUERIES, 1):
        print(f"  {i}. {q}")
    print()

    # Interactive loop
    while True:
        try:
            user_input = input("\n🔍 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break

        print("\n⏳ Investigating...\n")

        result = run_agent_with_retry(executor, user_input)

        print("\n" + "=" * 60)
        print("📋 INVESTIGATION REPORT")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=" * 60)


if __name__ == "__main__":
    main()
