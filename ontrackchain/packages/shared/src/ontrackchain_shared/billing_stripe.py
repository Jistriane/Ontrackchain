"""
Ontrackchain - Stripe Billing & SaaS Metering Manager (P3 B2B API & Billing)

Provides Stripe checkout session simulation and credit top-up management.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional


PLAN_TIER_LIMITS = {
    "starter": {"credits": 1000, "rate_limit_rpm": 10, "price_usd": 49},
    "pro": {"credits": 5000, "rate_limit_rpm": 30, "price_usd": 199},
    "enterprise": {"credits": 25000, "rate_limit_rpm": 100, "price_usd": 799},
}


class StripeBillingManager:
    """Manages SaaS billing, Stripe checkout sessions, and webhook validation."""

    def __init__(self, webhook_secret: Optional[str] = None) -> None:
        self.webhook_secret = webhook_secret or "whsec_ontrackchain_stg_secret_key"

    def create_checkout_session(
        self,
        org_id: str,
        plan_tier: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a mock/live Stripe Checkout session for plan upgrades or credit packages."""
        tier = plan_tier.lower()
        if tier not in PLAN_TIER_LIMITS:
            raise ValueError(f"Plano inválido: {plan_tier}. Planos aceitos: {list(PLAN_TIER_LIMITS.keys())}")

        plan_info = PLAN_TIER_LIMITS[tier]
        session_id = f"cs_live_{hashlib.sha256(f'{org_id}:{tier}:{time.time()}'.encode()).hexdigest()[:24]}"

        return {
            "id": session_id,
            "object": "checkout.session",
            "url": f"https://checkout.stripe.com/c/pay/{session_id}",
            "payment_status": "unpaid",
            "org_id": org_id,
            "plan_tier": tier,
            "amount_total": plan_info["price_usd"] * 100,  # Em centavos USD
            "currency": "usd",
            "credits_allocated": plan_info["credits"],
            "customer_email": customer_email or f"admin@{org_id}.ontrackchain.io",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "created_at": int(time.time()),
        }

    def verify_webhook_signature(self, payload: bytes, signature_header: str) -> bool:
        """Verifies HMAC-SHA256 signature of incoming Stripe Webhook events."""
        if not signature_header or not signature_header.startswith("t="):
            return False

        try:
            parts = dict(pair.split("=", 1) for pair in signature_header.split(","))
            timestamp = parts.get("t", "")
            expected_sig = parts.get("v1", "")

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
            computed_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                signed_payload,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(computed_sig, expected_sig)
        except Exception:
            return False

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes completed checkout webhooks and returns credit top-up metadata."""
        event_type = event_data.get("type", "")

        if event_type == "checkout.session.completed":
            session = event_data.get("data", {}).get("object", {})
            org_id = session.get("org_id", "default_org")
            plan_tier = session.get("plan_tier", "pro")
            credits = session.get("credits_allocated", PLAN_TIER_LIMITS.get(plan_tier, {}).get("credits", 5000))

            return {
                "status": "processed",
                "org_id": org_id,
                "plan_tier": plan_tier,
                "credits_to_add": credits,
                "transaction_id": session.get("id", "tx_unknown"),
            }

        return {"status": "ignored", "event_type": event_type}
