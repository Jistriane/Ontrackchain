from __future__ import annotations

import importlib
import json
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

risk_provider = importlib.import_module("compliance_api.risk_provider")
describe_provider_readiness = risk_provider.describe_provider_readiness
TrmRiskProviderConfig = risk_provider.TrmRiskProviderConfig
screen_address = risk_provider.screen_address
screen_address_with_trm = risk_provider.screen_address_with_trm


class _FakeResponse:
    def __init__(self, payload: dict, status: int = 200):
        self._payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class RiskProviderTests(unittest.TestCase):
    def _config(self, **overrides) -> TrmRiskProviderConfig:
        base = {
            "enabled": True,
            "screening_url": "https://provider.example/screen",
            "api_key": "test-key",
            "api_key_header": "Authorization",
            "api_key_prefix": "Bearer ",
            "timeout_ms": 1500,
            "max_retries": 1,
        }
        base.update(overrides)
        return TrmRiskProviderConfig(**base)

    def test_returns_degraded_when_provider_disabled(self) -> None:
        outcome = screen_address_with_trm(
            config=self._config(enabled=False),
            address="0x123",
            chain="ethereum",
            entity_name=None,
            declared_source=None,
        )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_disabled")
        self.assertIsNone(outcome.risk_score)
        self.assertEqual(outcome.retries_used, 0)

    def test_returns_degraded_when_provider_not_configured(self) -> None:
        outcome = screen_address_with_trm(
            config=self._config(api_key=""),
            address="0x123",
            chain="ethereum",
            entity_name=None,
            declared_source=None,
        )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_not_configured")
        self.assertEqual(outcome.raw_payload, {})

    def test_returns_live_when_provider_score_is_mappable(self) -> None:
        payload = {
            "data": {"riskScore": 87},
            "dimensions": {
                "ownership": 10,
                "behavioral": 20,
                "counterparty": 30,
                "exposure": 40,
                "aml": 50,
            },
        }

        with patch("compliance_api.risk_provider.urllib.request.urlopen", return_value=_FakeResponse(payload)):
            outcome = screen_address_with_trm(
                config=self._config(),
                address="0x123",
                chain="ethereum",
                entity_name="Alice",
                declared_source="tests",
            )

        self.assertEqual(outcome.provider_status, "live")
        self.assertIsNone(outcome.degraded_reason)
        self.assertEqual(outcome.risk_score, 87)
        self.assertEqual(outcome.dimensions, payload["dimensions"])
        self.assertEqual(outcome.score_source, "provider_live")
        self.assertEqual(outcome.upstream_status_code, 200)
        self.assertEqual(outcome.screening_host, "provider.example")
        self.assertFalse(outcome.request_id_forwarded)

    def test_forwards_request_id_and_tracks_screening_host(self) -> None:
        captured_headers: dict[str, str] = {}

        def _fake_urlopen(request, timeout):
            del timeout
            captured_headers.update(dict(request.header_items()))
            return _FakeResponse({"riskScore": 75})

        with patch("compliance_api.risk_provider.urllib.request.urlopen", side_effect=_fake_urlopen):
            outcome = screen_address_with_trm(
                config=self._config(),
                address="0x123",
                chain="ethereum",
                entity_name=None,
                declared_source=None,
                request_id="req-risk-provider-1",
            )

        self.assertEqual(captured_headers.get("X-request-id"), "req-risk-provider-1")
        self.assertTrue(outcome.request_id_forwarded)
        self.assertEqual(outcome.screening_host, "provider.example")

    def test_returns_degraded_when_provider_payload_is_unmapped(self) -> None:
        payload = {"status": "ok", "data": {"note": "no score"}}

        with patch("compliance_api.risk_provider.urllib.request.urlopen", return_value=_FakeResponse(payload)):
            outcome = screen_address_with_trm(
                config=self._config(),
                address="0x123",
                chain="ethereum",
                entity_name=None,
                declared_source=None,
            )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_response_unmapped")
        self.assertEqual(outcome.raw_payload, payload)

    def test_retries_and_returns_unavailable_on_network_error(self) -> None:
        with patch(
            "compliance_api.risk_provider.urllib.request.urlopen",
            side_effect=[urllib.error.URLError("down"), urllib.error.URLError("down")],
        ):
            outcome = screen_address_with_trm(
                config=self._config(max_retries=1),
                address="0x123",
                chain="ethereum",
                entity_name=None,
                declared_source=None,
            )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unavailable")
        self.assertEqual(outcome.retries_used, 1)
        self.assertGreaterEqual(outcome.latency_ms, 0)
        self.assertIsNone(outcome.upstream_status_code)

    def test_captures_http_status_on_provider_http_error(self) -> None:
        request = risk_provider.urllib.request.Request("https://provider.example/screen")
        error = urllib.error.HTTPError(
            url="https://provider.example/screen",
            code=429,
            msg="too many requests",
            hdrs=Message(),
            fp=None,
        )
        error.filename = request.full_url
        with patch("compliance_api.risk_provider.urllib.request.urlopen", side_effect=[error, error]):
            outcome = screen_address_with_trm(
                config=self._config(max_retries=1),
                address="0x123",
                chain="ethereum",
                entity_name=None,
                declared_source=None,
                request_id="req-risk-provider-http",
            )

        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unavailable")
        self.assertEqual(outcome.upstream_status_code, 429)
        self.assertTrue(outcome.request_id_forwarded)

    def test_routes_to_trm_provider_via_router(self) -> None:
        payload = {"riskScore": 64}

        with patch("compliance_api.risk_provider.urllib.request.urlopen", return_value=_FakeResponse(payload)):
            outcome = screen_address(
                provider_name="trm_labs",
                trm_config=self._config(),
                address="0x123",
                chain="ethereum",
                entity_name=None,
                declared_source=None,
            )

        self.assertEqual(outcome.provider_name, "trm_labs")
        self.assertEqual(outcome.provider_status, "live")
        self.assertEqual(outcome.risk_score, 64)

    def test_returns_degraded_when_provider_is_unsupported(self) -> None:
        outcome = screen_address(
            provider_name="elliptic",
            trm_config=self._config(),
            address="0x123",
            chain="ethereum",
            entity_name=None,
            declared_source=None,
        )

        self.assertEqual(outcome.provider_name, "elliptic")
        self.assertEqual(outcome.provider_status, "degraded")
        self.assertEqual(outcome.degraded_reason, "provider_unsupported")
        self.assertEqual(
            outcome.raw_payload,
            {
                "requested_provider": "elliptic",
                "supported_providers": ["trm_labs"],
            },
        )

    def test_readiness_returns_ready_for_supported_and_configured_provider(self) -> None:
        readiness = describe_provider_readiness(
            provider_name="trm_labs",
            trm_config=self._config(),
        )

        self.assertTrue(readiness.provider_supported)
        self.assertTrue(readiness.enabled)
        self.assertTrue(readiness.configured)
        self.assertTrue(readiness.ready)
        self.assertIsNone(readiness.degraded_reason)
        self.assertEqual(readiness.details["screening_host"], "provider.example")

    def test_readiness_returns_not_configured_for_missing_credentials(self) -> None:
        readiness = describe_provider_readiness(
            provider_name="trm_labs",
            trm_config=self._config(api_key=""),
        )

        self.assertTrue(readiness.provider_supported)
        self.assertTrue(readiness.enabled)
        self.assertFalse(readiness.configured)
        self.assertFalse(readiness.ready)
        self.assertEqual(readiness.degraded_reason, "provider_not_configured")
        self.assertEqual(readiness.details["operating_mode"], "misconfigured")

    def test_readiness_returns_unsupported_for_unknown_provider(self) -> None:
        readiness = describe_provider_readiness(
            provider_name="chainalysis",
            trm_config=self._config(),
        )

        self.assertFalse(readiness.provider_supported)
        self.assertFalse(readiness.enabled)
        self.assertFalse(readiness.configured)
        self.assertFalse(readiness.ready)
        self.assertEqual(readiness.degraded_reason, "provider_unsupported")


if __name__ == "__main__":
    unittest.main()
