import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_module("check_compliance_provider_runtime", "scripts/check_compliance_provider_runtime.py")


class CheckComplianceProviderRuntimeTests(unittest.TestCase):
    maxDiff = None

    def test_build_payload_accepts_live_internal_catalog_and_runtime(self) -> None:
        responses = [
            (
                200,
                {
                    "provider": "trm_labs",
                    "provider_supported": True,
                    "enabled": True,
                    "configured": True,
                    "ready": True,
                    "degraded_reason": None,
                    "details": {
                        "operating_mode": "live",
                        "screening_url_configured": True,
                        "api_key_configured": True,
                    },
                },
                {},
            ),
            (
                200,
                {
                    "provider": "trm_labs",
                    "provider_status": "live",
                    "degraded_reason": None,
                    "capability_status": "live",
                    "delivery_mode": "risk_check_instant",
                },
                {},
            ),
            (
                200,
                {
                    "provider": "trm_labs",
                    "provider_status": "live",
                    "degraded_reason": None,
                    "capability_status": "live",
                    "risk_score": 72,
                },
                {},
            ),
        ]

        captured_headers: list[dict[str, str]] = []

        def _request_json(**kwargs):
            captured_headers.append(dict(kwargs["headers"]))
            return responses[len(captured_headers) - 1]

        with patch.object(MODULE, "request_json", side_effect=_request_json):
            payload = MODULE.build_payload(
                internal_base_url="http://localhost:8002",
                public_base_url="http://localhost:8002",
                expected_provider="trm_labs",
                plan="professional",
                sample_address="0x000000000000000000000000000000000000dEaD",
                sample_chain="ethereum",
                bearer_token="",
                api_key="",
                timeout_seconds=5.0,
                request_id="req-compliance-1",
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["request_id"], "req-compliance-1")
        self.assertEqual([check["status"] for check in payload["checks"]], ["ok", "ok", "ok"])
        self.assertTrue(payload["correlation"]["provider_converges_live"])
        self.assertEqual(payload["correlation"]["internal_operating_mode"], "live")
        self.assertEqual(payload["correlation"]["catalog_provider_status"], "live")
        self.assertEqual(payload["correlation"]["runtime_provider_status"], "live")
        self.assertTrue(all(headers.get("X-Request-Id") == "req-compliance-1" for headers in captured_headers))

    def test_build_payload_flags_degraded_runtime_and_internal_failures(self) -> None:
        responses = [
            (
                200,
                {
                    "provider": "trm_labs",
                    "ready": False,
                    "degraded_reason": "provider_not_configured",
                    "details": {"operating_mode": "misconfigured"},
                },
                {},
            ),
            (
                200,
                {
                    "provider": "trm_labs",
                    "provider_status": "degraded",
                    "degraded_reason": "provider_not_configured",
                    "capability_status": "degraded",
                },
                {},
            ),
            (
                200,
                {
                    "provider": "trm_labs",
                    "provider_status": "degraded",
                    "degraded_reason": "provider_unavailable",
                    "capability_status": "degraded",
                },
                {},
            ),
        ]

        with patch.object(MODULE, "request_json", side_effect=responses):
            payload = MODULE.build_payload(
                internal_base_url="http://localhost:8002",
                public_base_url="http://localhost:8002",
                expected_provider="trm_labs",
                plan="professional",
                sample_address="0x000000000000000000000000000000000000dEaD",
                sample_chain="ethereum",
                bearer_token="",
                api_key="",
                timeout_seconds=5.0,
                request_id="req-compliance-2",
            )

        self.assertEqual(payload["status"], "failed")
        self.assertIn("internal/provider-readiness: ready esperado=true", payload["errors"][0])
        self.assertIn("operations/kyc_wallet: provider_status esperado=live recebido=degraded", payload["errors"])
        self.assertIn("kyc-wallet: provider_status esperado=live recebido=degraded degraded_reason=provider_unavailable", payload["errors"])
        self.assertFalse(payload["correlation"]["provider_converges_live"])

    def test_main_emits_json_and_non_zero_exit_code_on_failure(self) -> None:
        payload = {
            "status": "failed",
            "errors": ["provider unavailable"],
            "checks": [],
        }
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch.object(MODULE, "parse_args", return_value=type("Args", (), {
                "internal_base_url": "http://localhost:8002",
                "public_base_url": "http://localhost:8002",
                "expected_provider": "trm_labs",
                "plan": "professional",
                "sample_address": "0x000000000000000000000000000000000000dEaD",
                "sample_chain": "ethereum",
                "bearer_token": "",
                "api_key": "",
                "timeout_seconds": 5.0,
                "request_id": "req-compliance-3",
            })()),
            patch.object(MODULE, "build_payload", return_value=payload),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        rendered = stderr.getvalue().strip() or stdout.getvalue().strip()
        self.assertEqual(json.loads(rendered)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
