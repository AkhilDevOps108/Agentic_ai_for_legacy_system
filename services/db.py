"""Mock database service with pre-loaded transaction records."""

from datetime import datetime


class MockDatabase:
    """Simulates a legacy application database with order and payment records."""

    def __init__(self):
        self._orders = [
            {
                "order_id": "ORD-10481",
                "customer_id": "CUST-3021",
                "amount": 249.99,
                "currency": "USD",
                "status": "COMPLETED",
                "payment_status": "PAID",
                "created_at": "2026-04-18 02:14:50",
                "updated_at": "2026-04-18 02:15:08",
                "error_code": None,
                "transaction_id": "TXN-88210",
            },
            {
                "order_id": "ORD-10482",
                "customer_id": "CUST-5510",
                "amount": 89.50,
                "currency": "USD",
                "status": "COMPLETED",
                "payment_status": "PAID",
                "created_at": "2026-04-18 02:14:52",
                "updated_at": "2026-04-18 02:15:14",
                "error_code": None,
                "transaction_id": "TXN-88211",
            },
            {
                "order_id": "ORD-10483",
                "customer_id": "CUST-7892",
                "amount": 1024.00,
                "currency": "USD",
                "status": "FAILED",
                "payment_status": "TIMEOUT",
                "created_at": "2026-04-18 02:14:55",
                "updated_at": "2026-04-18 02:15:25",
                "error_code": "PAYMENT_TIMEOUT",
                "transaction_id": None,
            },
            {
                "order_id": "ORD-10484",
                "customer_id": "CUST-1204",
                "amount": 55.00,
                "currency": "USD",
                "status": "FAILED",
                "payment_status": "ERROR",
                "created_at": "2026-04-18 02:14:58",
                "updated_at": "2026-04-18 02:15:31",
                "error_code": "DB_CONNECTION_EXHAUSTED",
                "transaction_id": None,
            },
            {
                "order_id": "ORD-10485",
                "customer_id": "CUST-9933",
                "amount": 312.75,
                "currency": "USD",
                "status": "FAILED",
                "payment_status": "TIMEOUT",
                "created_at": "2026-04-18 02:15:00",
                "updated_at": "2026-04-18 02:15:33",
                "error_code": "PAYMENT_TIMEOUT",
                "transaction_id": None,
            },
            {
                "order_id": "ORD-10490",
                "customer_id": "CUST-4410",
                "amount": 178.25,
                "currency": "USD",
                "status": "FAILED",
                "payment_status": "TIMEOUT",
                "created_at": "2026-04-18 02:15:02",
                "updated_at": "2026-04-18 02:15:34",
                "error_code": "PAYMENT_TIMEOUT",
                "transaction_id": None,
            },
            {
                "order_id": "ORD-10491",
                "customer_id": "CUST-6601",
                "amount": 430.00,
                "currency": "USD",
                "status": "FAILED",
                "payment_status": "ERROR",
                "created_at": "2026-04-18 02:15:03",
                "updated_at": "2026-04-18 02:15:34",
                "error_code": "DB_CONNECTION_EXHAUSTED",
                "transaction_id": None,
            },
        ]

    def query_orders(self, filters: dict | None = None) -> list[dict]:
        """Query orders with optional filters.

        Supported filter keys: status, payment_status, error_code, order_id, date
        """
        results = self._orders

        if not filters:
            return results

        if "order_id" in filters:
            results = [o for o in results if o["order_id"] == filters["order_id"]]

        if "status" in filters:
            results = [
                o
                for o in results
                if o["status"].upper() == filters["status"].upper()
            ]

        if "payment_status" in filters:
            results = [
                o
                for o in results
                if o["payment_status"].upper() == filters["payment_status"].upper()
            ]

        if "error_code" in filters:
            results = [
                o
                for o in results
                if o["error_code"]
                and o["error_code"].upper() == filters["error_code"].upper()
            ]

        if "date" in filters:
            results = [
                o for o in results if o["created_at"].startswith(filters["date"])
            ]

        return results

    def get_order_summary(self) -> dict:
        """Return aggregate statistics about orders."""
        total = len(self._orders)
        completed = sum(1 for o in self._orders if o["status"] == "COMPLETED")
        failed = sum(1 for o in self._orders if o["status"] == "FAILED")
        total_amount_failed = sum(
            o["amount"] for o in self._orders if o["status"] == "FAILED"
        )
        error_codes = {}
        for o in self._orders:
            if o["error_code"]:
                error_codes[o["error_code"]] = error_codes.get(o["error_code"], 0) + 1

        return {
            "total_orders": total,
            "completed": completed,
            "failed": failed,
            "total_amount_at_risk": round(total_amount_failed, 2),
            "error_breakdown": error_codes,
            "report_generated_at": datetime.now().isoformat(),
        }


# Singleton instance
mock_db = MockDatabase()
