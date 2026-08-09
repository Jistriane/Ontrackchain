from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import importlib
import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("public_api.main")
else:
    main = None


class _FakeRedis:
    def __init__(self, *, initial_count: int = 0) -> None:
        self.count = initial_count
        self.incr_calls: list[str] = []
        self.expire_calls: list[tuple[str, int]] = []

    async def incr(self, key: str) -> int:
        self.incr_calls.append(key)
        self.count += 1
        return self.count

    async def expire(self, key: str, ttl_seconds: int) -> None:
        self.expire_calls.append((key, ttl_seconds))

    async def aclose(self) -> None:  # pragma: no cover - compatibilidade
        return None


class _FakeResponse:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}


def _make_valid_b2b_signature(
    *,
    method: str,
    path: str,
    body: bytes,
    secret: str,
    timestamp: str,
) -> str:
    body_b64 = base64.b64encode(body).decode("ascii")
    payload = f"{method.upper()}|{path}|{body_b64}|{timestamp}"
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _fake_request(method: str, path: str, body: bytes = b"", headers=None, client_ip: str = "127.0.0.1"):
    return main.Request(
        {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "headers": headers or [],
            "client": (client_ip, 8000),
            "query_string": b"",
            "_body": body,
        }
    )


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class PublicApiContractTests(unittest.TestCase):
    def test_validate_chain_normalizes_supported_values(self) -> None:
        self.assertEqual(main._validate_chain("  BASE "), "base")
        self.assertEqual(main._validate_chain("bitcoin"), "bitcoin")

    def test_validate_chain_rejects_unknown_chain_with_supported_list(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._validate_chain("solana")

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail["code"], "unsupported_chain")
        self.assertIn("ethereum", ctx.exception.detail["supported_chains"])

    def test_public_rate_limiter_sets_ttl_on_first_seen_ip(self) -> None:
        redis = _FakeRedis()
        request = main.Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/public/wallet/0xabc",
                "headers": [],
                "client": ("198.51.100.10", 443),
                "query_string": b"",
            }
        )

        asyncio.run(main.public_rate_limiter(request=request, redis=redis, x_forwarded_for=None))

        self.assertEqual(redis.incr_calls, ["rl:public:198.51.100.10"])
        self.assertEqual(redis.expire_calls, [("rl:public:198.51.100.10", 3600)])

    def test_public_rate_limiter_rejects_requests_above_hourly_limit(self) -> None:
        redis = _FakeRedis(initial_count=10)
        request = main.Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/public/entity/search",
                "headers": [],
                "client": ("203.0.113.7", 443),
                "query_string": b"",
            }
        )

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(main.public_rate_limiter(request=request, redis=redis, x_forwarded_for="203.0.113.7"))

        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.detail, "rate_limited")
        self.assertEqual(redis.expire_calls, [])

    def test_wallet_basic_returns_bitcoin_scope_and_provider_hint(self) -> None:
        response = asyncio.run(main.get_wallet_basic(address="bc1-test", chain="bitcoin", _=None))

        self.assertEqual(response.address, "bc1-test")
        self.assertEqual(response.chain, "bitcoin")
        self.assertEqual(response.data_scope, "basic_bitcoin")
        self.assertEqual(response.provider_hint, "blockchair_oklink")

    def test_cache_headers_are_applied_only_to_public_routes(self) -> None:
        public_request = main.Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/public/wallet/0xabc",
                "headers": [],
                "client": ("127.0.0.1", 8000),
                "query_string": b"",
            }
        )
        private_request = main.Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/health",
                "headers": [],
                "client": ("127.0.0.1", 8000),
                "query_string": b"",
            }
        )

        async def call_next(_: Any) -> Any:
            return _FakeResponse()

        public_response = asyncio.run(main.add_cache_headers(public_request, call_next))
        private_response = asyncio.run(main.add_cache_headers(private_request, call_next))

        self.assertEqual(public_response.headers["Cache-Control"], "public, max-age=300")
        self.assertEqual(public_response.headers["CDN-Cache-Control"], "max-age=300")
        self.assertNotIn("Cache-Control", private_response.headers)
        self.assertNotIn("CDN-Cache-Control", private_response.headers)

    def test_get_supported_chains_returns_all_active_chains(self) -> None:
        response = asyncio.run(main.get_supported_chains(_=None))

        self.assertEqual(response.total, 6)
        chain_names = [c.chain for c in response.chains]
        self.assertIn("ethereum", chain_names)
        self.assertIn("bitcoin", chain_names)
        self.assertIn("polygon", chain_names)

    def test_public_sanctions_check_returns_cache_provider(self) -> None:
        response = asyncio.run(main.public_sanctions_check(address="0x1111", chain="ethereum", _=None))

        self.assertEqual(response.address, "0x1111")
        self.assertEqual(response.chain, "ethereum")
        self.assertEqual(response.provider, "sanctions_lists_cache")
        self.assertEqual(response.provider_status, "live")
        self.assertFalse(response.hit)

    # ======================================================================
    # 12 novos testes T2-01 B2B v2.0.0 Public API Monetização
    # ======================================================================
    def test_b2b_authenticate_rejects_missing_headers(self) -> None:
        req = _fake_request("GET", "/api/v1/b2b/case-status/CASE-DEMO-2026-00001")
        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.b2b_authenticate(
                    request=req,
                    x_ot_client_id=None,
                    x_ot_timestamp=None,
                    x_ot_signature=None,
                )
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail["code"], "b2b_auth_missing_headers")

    def test_b2b_authenticate_rejects_unknown_client_id(self) -> None:
        ts = str(int(datetime.now(timezone.utc).timestamp()))
        req = _fake_request("GET", "/api/v1/b2b/case-status/CASE-DEMO-2026-00001")
        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.b2b_authenticate(
                    request=req,
                    x_ot_client_id="b2b_client_hacker_999",
                    x_ot_timestamp=ts,
                    x_ot_signature="0" * 64,
                )
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail["code"], "b2b_client_unknown_or_disabled")

    def test_b2b_authenticate_rejects_timestamp_outside_skew(self) -> None:
        old_ts = str(int(datetime.now(timezone.utc).timestamp()) - 3600)  # 1h atrás
        req = _fake_request("GET", "/api/v1/b2b/case-status/CASE-DEMO-2026-00001")
        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.b2b_authenticate(
                    request=req,
                    x_ot_client_id="b2b_ontrack_demo_client_001",
                    x_ot_timestamp=old_ts,
                    x_ot_signature="0" * 64,
                )
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail["code"], "b2b_timestamp_outside_skew")
        self.assertGreater(ctx.exception.detail["observed_skew_seconds"], 2000)

    def test_b2b_authenticate_rejects_signature_mismatch(self) -> None:
        ts = str(int(datetime.now(timezone.utc).timestamp()))
        req = _fake_request("GET", "/api/v1/b2b/case-status/CASE-DEMO-2026-00001")
        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.b2b_authenticate(
                    request=req,
                    x_ot_client_id="b2b_ontrack_demo_client_001",
                    x_ot_timestamp=ts,
                    x_ot_signature="0" * 64,  # assinatura falsa
                )
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail["code"], "b2b_signature_mismatch")

    def test_b2b_authenticate_passes_with_valid_signature(self) -> None:
        ts = str(int(datetime.now(timezone.utc).timestamp()))
        secret = main._B2B_API_KEYS_FAKE_DB["b2b_ontrack_demo_client_001"]["secret"]
        path = "/api/v1/b2b/case-status/CASE-DEMO-2026-00001"
        sig = _make_valid_b2b_signature(
            method="GET", path=path, body=b"", secret=secret, timestamp=ts
        )
        req = _fake_request("GET", path)
        result = asyncio.run(
            main.b2b_authenticate(
                request=req,
                x_ot_client_id="b2b_ontrack_demo_client_001",
                x_ot_timestamp=ts,
                x_ot_signature=sig,
            )
        )
        self.assertEqual(result["client_id"], "b2b_ontrack_demo_client_001")
        self.assertEqual(result["tenant_slug"], "ontrackchain-demo")
        self.assertEqual(result["plan"], "business")

    def test_b2b_rate_limiter_uses_b2b_key(self) -> None:
        client_ctx = {
            "client_id": "b2b_ontrack_demo_client_001",
            "tenant_slug": "ontrackchain-demo",
            "plan": "business",
        }
        redis = _FakeRedis()
        asyncio.run(main.b2b_rate_limiter(client_ctx=client_ctx, redis=redis))
        self.assertTrue(redis.incr_calls[0].startswith("rl:b2b:"))
        self.assertIn("b2b_ontrack_demo_client_001", redis.incr_calls[0])
        self.assertEqual(redis.expire_calls[0][1], 3600)

    def test_b2b_get_case_status_returns_demo_tenant_data(self) -> None:
        client_ctx = {
            "client_id": "b2b_ontrack_demo_client_001",
            "tenant_slug": "ontrackchain-demo",
            "plan": "business",
        }
        result = asyncio.run(
            main.b2b_get_case_status(
                correlation_id="CASE-DEMO-2026-00001",
                client_ctx=client_ctx,
                _=None,  # skip rate limiter no teste
            )
        )
        self.assertEqual(result.status, "closed_sanctions_hit")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.risk_score_final, 91)
        self.assertFalse(result.sla_breached)
        self.assertIn("OFAC", result.tags)

    def test_b2b_get_case_status_404_for_unknown_correlation(self) -> None:
        client_ctx = {
            "client_id": "b2b_ontrack_demo_client_001",
            "tenant_slug": "ontrackchain-demo",
            "plan": "business",
        }
        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.b2b_get_case_status(
                    correlation_id="CASE-NAO-EXISTE-999",
                    client_ctx=client_ctx,
                    _=None,
                )
            )
        self.assertEqual(ctx.exception.status_code, 404)

    def test_b2b_get_evidence_package_contains_sealing_hash(self) -> None:
        client_ctx = {
            "client_id": "b2b_ontrack_demo_client_001",
            "tenant_slug": "ontrackchain-demo",
            "plan": "business",
        }
        result = asyncio.run(
            main.b2b_get_evidence_package(
                correlation_id="CASE-DEMO-2026-00001",
                client_ctx=client_ctx,
                _=None,
            )
        )
        self.assertEqual(len(result.sealing_hash), 64)  # SHA-256 hex
        self.assertEqual(result.sealing_hash_algorithm, "SHA-256")
        self.assertEqual(result.evidence_item_count, 7)
        self.assertGreaterEqual(len(result.files), 2)
        self.assertTrue(result.pdf_package_url.startswith("https://"))

    def test_b2b_validate_webhook_events_rejects_missing_required(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            main.B2BWebhookSubscriptionIn.validate_events(["evidence.package.created"])
        self.assertIn("case.status.updated", str(ctx.exception))
        self.assertIn("sanctions.alert.created", str(ctx.exception))

    def test_b2b_validate_webhook_events_accepts_all_three_required(self) -> None:
        good = ["case.status.updated", "evidence.package.created", "sanctions.alert.created", "extra.customer.custom"]
        cleaned = main.B2BWebhookSubscriptionIn.validate_events(good)
        self.assertIn("case.status.updated", cleaned)
        self.assertIn("extra.customer.custom", cleaned)

    def test_b2b_rotate_key_returns_7_day_grace_period(self) -> None:
        client_ctx = {
            "client_id": "b2b_ontrack_demo_client_001",
            "tenant_slug": "ontrackchain-demo",
            "plan": "business",
        }
        result = asyncio.run(
            main.b2b_rotate_api_key(
                client_ctx=client_ctx,
                _=None,
            )
        )
        self.assertTrue(result.new_secret.startswith("sk_b2b_"))
        self.assertEqual(result.client_id, "b2b_ontrack_demo_client_001")
        self.assertIn("T", result.old_secret_valid_until_utc)  # ISO8601
        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(result.old_secret_valid_until_utc.replace("Z", "+00:00"))
        delta_days = (expiry - now).total_seconds() / 86400
        self.assertGreaterEqual(delta_days, 6.5)  # 7 dias (tolerância 12h)
        self.assertLessEqual(delta_days, 7.5)


if __name__ == "__main__":
    unittest.main()
