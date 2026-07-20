from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import unittest
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


class _FakeResponse:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}


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


if __name__ == "__main__":
    unittest.main()
