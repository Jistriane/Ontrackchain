from __future__ import annotations

import importlib
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

rpc_provider = importlib.import_module("investigation_api.rpc_provider")
RpcProviderConfig = rpc_provider.RpcProviderConfig
describe_rpc_readiness = rpc_provider.describe_rpc_readiness
fetch_chain_context = rpc_provider.fetch_chain_context


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class RpcProviderTests(unittest.TestCase):
    def _config(self, **overrides) -> RpcProviderConfig:
        base = {
            "enabled": True,
            "primary_url": "https://primary.rpc.example",
            "fallback_url": "https://fallback.rpc.example",
            "timeout_ms": 1500,
            "max_retries": 1,
        }
        base.update(overrides)
        return RpcProviderConfig(**base)

    def test_returns_degraded_when_provider_disabled(self) -> None:
        outcome = fetch_chain_context(
            provider_name="evm_rpc",
            config=self._config(enabled=False),
            address="0x123",
            chain="ethereum",
        )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_disabled")
        self.assertEqual(outcome.rpc_source, "unavailable")

    def test_falls_back_to_secondary_when_primary_fails(self) -> None:
        payloads = [
            urllib.error.URLError("primary down"),
            _FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x20"}),
            _FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x30"}),
        ]

        def _side_effect(*_args, **_kwargs):
            current = payloads.pop(0)
            if isinstance(current, Exception):
                raise current
            return current

        with patch("investigation_api.rpc_provider.urllib.request.urlopen", side_effect=_side_effect):
            outcome = fetch_chain_context(
                provider_name="evm_rpc",
                config=self._config(max_retries=0),
                address="0x123",
                chain="ethereum",
            )

        self.assertEqual(outcome.provider_status, "live")
        self.assertEqual(outcome.latest_block_number, 32)
        self.assertEqual(outcome.balance_wei, 48)
        self.assertEqual(outcome.rpc_source, "provider_fallback")

    def test_returns_degraded_when_chain_is_not_supported(self) -> None:
        outcome = fetch_chain_context(
            provider_name="evm_rpc",
            config=self._config(primary_url="https://primary.rpc.example", fallback_url=""),
            address="bc1abc",
            chain="bitcoin",
        )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "chain_not_supported")

    def test_readiness_returns_ready_for_live_primary(self) -> None:
        readiness = describe_rpc_readiness(
            provider_name="evm_rpc",
            config=self._config(),
        )

        self.assertTrue(readiness.ready)
        self.assertEqual(readiness.details["operating_mode"], "live")
        self.assertTrue(readiness.details["fallback_url_configured"])
