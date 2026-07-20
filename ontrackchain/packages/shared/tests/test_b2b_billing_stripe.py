"""
Testes unitários para StripeBillingManager e B2BApiKeyValidator (P3 B2B API & Billing).
"""

from __future__ import annotations

import hmac
import hashlib
import unittest

from ontrackchain_shared.billing_stripe import StripeBillingManager, PLAN_TIER_LIMITS
from ontrackchain_shared.b2b_api_key import B2BApiKeyValidator


class StripeBillingManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = StripeBillingManager(webhook_secret="whsec_test_secret_123")

    def test_create_checkout_session_valid_plan(self) -> None:
        session = self.manager.create_checkout_session(
            org_id="org_test_1",
            plan_tier="pro",
            success_url="https://app.ontrackchain.io/billing?success=1",
            cancel_url="https://app.ontrackchain.io/billing?cancel=1",
        )

        self.assertTrue(session["id"].startswith("cs_live_"))
        self.assertEqual(session["org_id"], "org_test_1")
        self.assertEqual(session["plan_tier"], "pro")
        self.assertEqual(session["credits_allocated"], 5000)
        self.assertEqual(session["amount_total"], 19900)

    def test_create_checkout_session_invalid_plan(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.create_checkout_session(
                org_id="org_test_1",
                plan_tier="super_custom",
                success_url="https://app.ontrackchain.io",
                cancel_url="https://app.ontrackchain.io",
            )

    def test_verify_webhook_signature_valid(self) -> None:
        payload = b'{"type": "checkout.session.completed", "id": "evt_123"}'
        timestamp = "1700000000"
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
        sig = hmac.new(b"whsec_test_secret_123", signed_payload, hashlib.sha256).hexdigest()
        sig_header = f"t={timestamp},v1={sig}"

        self.assertTrue(self.manager.verify_webhook_signature(payload, sig_header))

    def test_verify_webhook_signature_invalid(self) -> None:
        payload = b'{"type": "checkout.session.completed"}'
        self.assertFalse(self.manager.verify_webhook_signature(payload, "t=1700000000,v1=invalid_sig"))


class B2BApiKeyValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = B2BApiKeyValidator()

    def test_generate_and_validate_key(self) -> None:
        raw_key, key_hash, meta = self.validator.generate_key("org_fintech_1", plan_tier="enterprise")
        self.assertTrue(raw_key.startswith("otc_live_"))
        self.assertEqual(meta["rate_limit_rpm"], 100)

        # Register key
        self.validator.register_key_hash(key_hash, meta)

        # Validate
        is_valid, key_info, err = self.validator.validate_key(raw_key)
        self.assertTrue(is_valid)
        self.assertIsNotNone(key_info)
        self.assertEqual(err, "")

    def test_reject_invalid_key_format(self) -> None:
        is_valid, key_info, err = self.validator.validate_key("invalid_prefix_key")
        self.assertFalse(is_valid)
        self.assertIn("Formato de chave B2B inválido", err)

    def test_rate_limiting_enforcement(self) -> None:
        raw_key, key_hash, meta = self.validator.generate_key("org_starter_1", plan_tier="starter")
        # Starter rate limit is 10 rpm
        meta["rate_limit_rpm"] = 2  # Override for fast test
        self.validator.register_key_hash(key_hash, meta)

        # First 2 requests succeed
        v1, _, _ = self.validator.validate_key(raw_key)
        v2, _, _ = self.validator.validate_key(raw_key)
        self.assertTrue(v1)
        self.assertTrue(v2)

        # 3rd request fails with rate limit exceeded
        v3, _, err = self.validator.validate_key(raw_key)
        self.assertFalse(v3)
        self.assertIn("Cota de requisições excedida", err)


if __name__ == "__main__":
    unittest.main()
