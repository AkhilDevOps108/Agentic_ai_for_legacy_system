"""Agent tools — modular tool registry for the ReAct agent.

Each tool is a @tool-decorated function. The `get_all_tools()` function collects
them all, making it easy to add new tools without changing agent wiring.
"""

import json
import re
from pathlib import Path

from langchain_core.tools import tool

from config.settings import settings
from services.db import mock_db
from services.api_simulator import recovery_api


# ---------------------------------------------------------------------------
# Tool 1: Log Analyzer
# ---------------------------------------------------------------------------

@tool
def search_logs(query: str) -> str:
    """Search application logs for entries matching the given keywords.

    Use this tool to investigate errors, warnings, or events in the legacy
    application's log file. Provide descriptive keywords like 'payment timeout',
    'error', 'ORD-10483', 'connection pool', etc.

    Args:
        query: Space-separated keywords to search for in the logs.

    Returns:
        Matching log lines (up to 20), or a message if no matches found.
    """
    if not query or not query.strip():
        return "Error: Please provide a non-empty search query."

    log_path = Path(settings.log_file_path)
    if not log_path.exists():
        return f"Error: Log file not found at {log_path}"

    text = log_path.read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    # Split query into individual keywords and match any
    keywords = [kw.strip().lower() for kw in query.split() if kw.strip()]
    matching = []
    for line in lines:
        lower_line = line.lower()
        if any(kw in lower_line for kw in keywords):
            matching.append(line)

    if not matching:
        return f"No log entries found matching: '{query}'"

    # Cap results to avoid token overflow
    cap = 20
    result_lines = matching[:cap]
    header = f"Found {len(matching)} matching log entries"
    if len(matching) > cap:
        header += f" (showing first {cap})"
    header += f" for query '{query}':\n"

    return header + "\n".join(result_lines)


# ---------------------------------------------------------------------------
# Tool 2: SQL Query Tool (Mock)
# ---------------------------------------------------------------------------

@tool
def query_database(query: str) -> str:
    """Query the legacy application database for order and transaction data.

    Use this tool to look up order details, check payment statuses, or get
    aggregate statistics. Supports natural language queries like:
    - 'show failed orders'
    - 'get order ORD-10483'
    - 'summary of all orders'
    - 'orders with payment timeout'
    - 'orders from 2026-04-18'

    Args:
        query: Natural language description of the data you need.

    Returns:
        JSON-formatted query results.
    """
    if not query or not query.strip():
        return "Error: Please provide a non-empty query."

    q = query.lower()

    # Route based on intent detection
    if "summary" in q or "statistics" in q or "aggregate" in q or "overview" in q:
        data = mock_db.get_order_summary()
        return json.dumps(data, indent=2)

    filters = {}

    # Detect specific order ID
    order_match = re.search(r"ord-\d+", q, re.IGNORECASE)
    if order_match:
        filters["order_id"] = order_match.group(0).upper()

    # Detect status filters
    if "failed" in q or "failure" in q:
        filters["status"] = "FAILED"
    elif "completed" in q or "success" in q:
        filters["status"] = "COMPLETED"

    # Detect error code filters
    if "timeout" in q:
        filters["error_code"] = "PAYMENT_TIMEOUT"
    elif "connection" in q or "db_connection" in q or "pool" in q:
        filters["error_code"] = "DB_CONNECTION_EXHAUSTED"

    # Detect date filters
    date_match = re.search(r"\d{4}-\d{2}-\d{2}", q)
    if date_match:
        filters["date"] = date_match.group(0)

    results = mock_db.query_orders(filters if filters else None)

    if not results:
        return f"No orders found matching: '{query}'"

    return json.dumps(
        {
            "query_interpreted": filters or "all orders",
            "result_count": len(results),
            "results": results,
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# Tool 3: Recovery API Trigger (Simulated)
# ---------------------------------------------------------------------------

@tool
def trigger_recovery_api(order_id: str) -> str:
    """Trigger a simulated payment retry for a failed order.

    IMPORTANT: This is a SIMULATED API call. No real transactions are processed.
    Use this only after confirming an order has failed and a retry is appropriate.

    Args:
        order_id: The order ID to retry (e.g., 'ORD-10483').

    Returns:
        JSON response from the simulated recovery API.
    """
    if not order_id or not order_id.strip():
        return "Error: Please provide a valid order ID."

    # Validate before execution
    is_valid, msg = recovery_api.validate_order_id(order_id.strip())
    if not is_valid:
        return json.dumps({"success": False, "error": msg})

    result = recovery_api.trigger_retry(order_id.strip())
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

_ALL_TOOLS = [search_logs, query_database, trigger_recovery_api]


def get_all_tools() -> list:
    """Return all registered tools. Add new @tool functions to _ALL_TOOLS."""
    return list(_ALL_TOOLS)
