"""Simulated recovery API service — no real HTTP calls are made."""

import random
import time
from datetime import datetime


class RecoveryAPISimulator:
    """Simulates a legacy system recovery API endpoint.

    All calls are local simulations. No external network requests are made.
    """

    VALID_ORDER_PREFIX = "ORD-"

    def validate_order_id(self, order_id: str) -> tuple[bool, str]:
        """Validate order ID format before allowing any action."""
        if not order_id or not isinstance(order_id, str):
            return False, "Order ID must be a non-empty string."
        if not order_id.startswith(self.VALID_ORDER_PREFIX):
            return False, f"Order ID must start with '{self.VALID_ORDER_PREFIX}'."
        if len(order_id) < 5:
            return False, "Order ID is too short."
        return True, "Valid"

    def trigger_retry(self, order_id: str) -> dict:
        """Simulate triggering a payment retry for a failed order.

        Returns a simulated API response dict. Success rate is ~80%.
        """
        is_valid, message = self.validate_order_id(order_id)
        if not is_valid:
            return {
                "success": False,
                "order_id": order_id,
                "action": "RETRY_PAYMENT",
                "error": message,
                "timestamp": datetime.now().isoformat(),
            }

        # Simulate network latency (0.3-0.8s)
        latency = round(random.uniform(0.3, 0.8), 2)
        time.sleep(latency)

        # 80% success rate
        succeeded = random.random() < 0.80

        if succeeded:
            return {
                "success": True,
                "order_id": order_id,
                "action": "RETRY_PAYMENT",
                "message": f"Payment retry initiated for {order_id}. "
                f"New transaction queued for processing.",
                "new_transaction_id": f"TXN-{random.randint(90000, 99999)}",
                "estimated_completion": "2-5 minutes",
                "latency_ms": int(latency * 1000),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "success": False,
                "order_id": order_id,
                "action": "RETRY_PAYMENT",
                "error": "Upstream payment provider still experiencing issues. "
                "Retry queued for next available window.",
                "retry_scheduled_at": "Next batch cycle",
                "latency_ms": int(latency * 1000),
                "timestamp": datetime.now().isoformat(),
            }


# Singleton instance
recovery_api = RecoveryAPISimulator()
