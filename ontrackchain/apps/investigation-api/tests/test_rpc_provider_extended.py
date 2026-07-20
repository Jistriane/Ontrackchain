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


class RpcProviderErrorTests(unittest.TestCase):
    """Cobre os cenários de falha que os testes originais não atingem."""

    def _config(self, **overrides) -> RpcProviderConfig:
        base = {
            "enabled": True,
            "primary_url": "https://primary.rpc.example",
            "fallback_url": "https://fallback.rpc.example",
            "timeout_ms": 1500,
            "max_retries": 0,
        }
        base.update(overrides)
        return RpcProviderConfig(**base)

    def test_returns_degraded_for_unsupported_provider(self) -> None:
        outcome = fetch_chain_context(
            provider_name="solana_rpc",
            config=self._config(),
            address="addr123",
            chain="ethereum",
        )
        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unsupported")
        self.assertIn("solana_rpc", outcome.raw_payload.get("requested_provider", ""))

    def test_unsupported_provider_name_is_normalized_in_outcome(self) -> None:
        outcome = fetch_chain_context(
            provider_name="  EVM_JSON_RPC  ",
            config=self._config(),
            address="0x123",
            chain="ethereum",
        )
        self.assertEqual(outcome.degraded_reason, "provider_unsupported")
        self.assertEqual(outcome.provider_name, "evm_json_rpc")

    def test_returns_degraded_when_both_urls_empty(self) -> None:
        outcome = fetch_chain_context(
            provider_name="evm_rpc",
            config=self._config(primary_url="", fallback_url=""),
            address="0x123",
            chain="ethereum",
        )
        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_not_configured")

    def test_primary_and_fallback_both_fail_returns_unavailable(self) -> None:
        with patch(
            "investigation_api.rpc_provider.urllib.request.urlopen",
            side_effect=urllib.error.URLError("network error"),
        ):
            outcome = fetch_chain_context(
                provider_name="evm_rpc",
                config=self._config(max_retries=0),
                address="0x123",
                chain="ethereum",
            )
        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unavailable")
        self.assertEqual(outcome.rpc_source, "provider_fallback_exhausted")

    def test_primary_only_fail_uses_primary_exhausted_source(self) -> None:
        with patch(
            "investigation_api.rpc_provider.urllib.request.urlopen",
            side_effect=urllib.error.URLError("network error"),
        ):
            outcome = fetch_chain_context(
                provider_name="evm_rpc",
                config=self._config(fallback_url="", max_retries=0),
                address="0x123",
                chain="ethereum",
            )
        self.assertEqual(outcome.degraded_reason, "provider_unavailable")
        self.assertEqual(outcome.rpc_source, "provider_primary_exhausted")

    def test_json_decode_error_triggers_degraded(self) -> None:
        def _bad_response(*_args, **_kwargs):
            class _BadBody:
                def read(self): return b"<html>error</html>"
                def __enter__(self): return self
                def __exit__(self, *_): return None
            return _BadBody()

        with patch("investigation_api.rpc_provider.urllib.request.urlopen", side_effect=_bad_response):
            outcome = fetch_chain_context(
                provider_name="evm_rpc",
                config=self._config(fallback_url="", max_retries=0),
                address="0x123",
                chain="ethereum",
            )
        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unavailable")

    def test_primary_success_returns_provider_primary_source(self) -> None:
        payloads = [
            _FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x10"}),
            _FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x20"}),
        ]

        def _side_effect(*_args, **_kwargs):
            return payloads.pop(0)

        with patch("investigation_api.rpc_provider.urllib.request.urlopen", side_effect=_side_effect):
            outcome = fetch_chain_context(
                provider_name="evm_rpc",
                config=self._config(max_retries=0),
                address="0x123",
                chain="ethereum",
            )
        self.assertEqual(outcome.provider_status, "live")
        self.assertEqual(outcome.rpc_source, "provider_primary")


class RpcProviderReadinessExtendedTests(unittest.TestCase):
    """Cobre os cenários de readiness não testados."""

    def _config(self, **overrides) -> RpcProviderConfig:
        base = {
            "enabled": True,
            "primary_url": "https://primary.rpc.example",
            "fallback_url": "https://fallback.rpc.example",
            "timeout_ms": 1500,
            "max_retries": 0,
        }
        base.update(overrides)
        return RpcProviderConfig(**base)

    def test_readiness_returns_unsupported_for_unknown_provider(self) -> None:
        readiness = describe_rpc_readiness(
            provider_name="chainalysis",
            config=self._config(),
        )
        self.assertFalse(readiness.provider_supported)
        self.assertFalse(readiness.ready)
        self.assertEqual(readiness.degraded_reason, "provider_unsupported")

    def test_readiness_returns_disabled_when_provider_disabled(self) -> None:
        readiness = describe_rpc_readiness(
            provider_name="evm_rpc",
            config=self._config(enabled=False),
        )
        self.assertFalse(readiness.ready)
        self.assertEqual(readiness.degraded_reason, "provider_disabled")
        self.assertEqual(readiness.details["operating_mode"], "disabled")

    def test_readiness_returns_fallback_only_when_primary_empty(self) -> None:
        readiness = describe_rpc_readiness(
            provider_name="evm_rpc",
            config=self._config(primary_url=""),
        )
        # fallback_only ainda é operacional: ready=True, sem degraded_reason
        self.assertTrue(readiness.ready)
        self.assertIsNone(readiness.degraded_reason)
        self.assertEqual(readiness.details["operating_mode"], "fallback_only")

    def test_readiness_returns_not_configured_when_both_empty(self) -> None:
        readiness = describe_rpc_readiness(
            provider_name="evm_rpc",
            config=self._config(primary_url="", fallback_url=""),
        )
        self.assertFalse(readiness.ready)
        self.assertEqual(readiness.degraded_reason, "provider_not_configured")


class RpcProviderCoerceIntTests(unittest.TestCase):
    """Cobre a função _coerce_int com seus edge cases."""

    _coerce_int = staticmethod(rpc_provider._coerce_int)

    def test_coerce_int_returns_none_for_bool_true(self) -> None:
        self.assertIsNone(self._coerce_int(True))

    def test_coerce_int_returns_none_for_bool_false(self) -> None:
        self.assertIsNone(self._coerce_int(False))

    def test_coerce_int_parses_hex_string(self) -> None:
        self.assertEqual(self._coerce_int("0x1a"), 26)

    def test_coerce_int_returns_none_for_invalid_hex(self) -> None:
        self.assertIsNone(self._coerce_int("0xGGGG"))

    def test_coerce_int_parses_decimal_string(self) -> None:
        self.assertEqual(self._coerce_int("12345"), 12345)

    def test_coerce_int_returns_int_directly(self) -> None:
        self.assertEqual(self._coerce_int(42), 42)

    def test_coerce_int_returns_none_for_none(self) -> None:
        self.assertIsNone(self._coerce_int(None))


if __name__ == "__main__":
    unittest.main()
