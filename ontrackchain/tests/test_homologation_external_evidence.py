import importlib.util
import tempfile
import unittest
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


MODULE = _load_module("homologation_external_evidence", "scripts/homologation_external_evidence.py")


class HomologationExternalEvidenceTests(unittest.TestCase):
    def test_run_compliance_homologation_succeeds_with_live_contract(self) -> None:
        responses = iter(
            [
                (
                    200,
                    {"ready": True, "details": {"operating_mode": "live"}},
                    {},
                ),
                (
                    200,
                    {
                        "operations": [
                            {
                                "canonical": "kyc_wallet",
                                "provider": "trm_labs",
                                "provider_status": "live",
                                "capability_status": "live",
                                "delivery_mode": "risk_check_instant",
                            }
                        ]
                    },
                    {},
                ),
                (
                    200,
                    {"provider_status": "live", "provider": "trm_labs"},
                    {},
                ),
                (
                    200,
                    {"sections": {"audit_logs": {"count": 2}}},
                    {},
                ),
            ]
        )

        with patch.object(MODULE, "request_json", side_effect=lambda **_: next(responses)), patch.object(
            MODULE.os, "getenv", return_value=None
        ):
            payload = MODULE.run_compliance_homologation(
                base_url="http://localhost:8080",
                api_key="demo",
                org_id="org",
                user_id="user",
                plan="professional",
                role="ADMIN",
                address="0xabc",
                chain="ethereum",
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertIn("request_id", payload)

    def test_run_rpc_homologation_succeeds_in_fallback_only_mode(self) -> None:
        responses = iter(
            [
                (
                    200,
                    {"ready": True, "details": {"operating_mode": "fallback_only"}},
                    {},
                ),
                (
                    200,
                    {"quote_id": "quote-123"},
                    {},
                ),
                (
                    202,
                    {"case_id": "case-123", "status": "queued"},
                    {},
                ),
                (
                    200,
                    {"sections": {"audit_logs": {"count": 3}}},
                    {},
                ),
            ]
        )
        terminal_result = (
            200,
            {
                "status": "completed",
                "kyw_summary": {
                    "analysis_version": "rpc_provider_v1",
                    "rpc": {
                        "provider_status": "degraded",
                        "rpc_source": "provider_fallback",
                    },
                },
            },
        )

        def _request_json(**_: object):
            return next(responses)

        with patch.object(MODULE, "request_json", side_effect=_request_json), patch.object(
            MODULE, "wait_for_investigation_terminal_result", return_value=terminal_result
        ), patch.object(MODULE.os, "getenv", return_value=None):
            payload = MODULE.run_rpc_homologation(
                base_url="http://localhost:8080",
                api_key="demo",
                org_id="org",
                user_id="user",
                plan="professional",
                role="ADMIN",
                address="0xabc",
                chain="ethereum",
                expected_mode="fallback_only",
                timeout_seconds=10,
                poll_seconds=0.1,
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["case_id"], "case-123")
        self.assertEqual(payload["errors"], [])

    def test_run_rpc_homologation_flags_mismatched_result_contract(self) -> None:
        responses = iter(
            [
                (
                    200,
                    {"ready": True, "details": {"operating_mode": "live"}},
                    {},
                ),
                (
                    200,
                    {"quote_id": "quote-123"},
                    {},
                ),
                (
                    200,
                    {"case_id": "case-123", "status": "queued"},
                    {},
                ),
                (
                    200,
                    {"sections": {"audit_logs": {"count": 1}}},
                    {},
                ),
            ]
        )
        terminal_result = (
            200,
            {
                "status": "completed",
                "kyw_summary": {
                    "analysis_version": "unexpected",
                    "rpc": {
                        "provider_status": "live",
                        "rpc_source": "provider_fallback",
                    },
                },
            },
        )

        with patch.object(MODULE, "request_json", side_effect=lambda **_: next(responses)), patch.object(
            MODULE, "wait_for_investigation_terminal_result", return_value=terminal_result
        ), patch.object(MODULE.os, "getenv", return_value=None):
            payload = MODULE.run_rpc_homologation(
                base_url="http://localhost:8080",
                api_key="demo",
                org_id="org",
                user_id="user",
                plan="professional",
                role="ADMIN",
                address="0xabc",
                chain="ethereum",
                expected_mode="live",
                timeout_seconds=10,
                poll_seconds=0.1,
            )

        self.assertEqual(payload["status"], "failed")
        self.assertIn(
            "investigation-result: esperado analysis_version=rpc_provider_v1, recebido=unexpected",
            payload["errors"],
        )
        self.assertIn(
            "investigation-result: esperado rpc_source=provider_primary em modo live, recebido=provider_fallback",
            payload["errors"],
        )

    def test_write_artifacts_generates_manifest_with_sha256(self) -> None:
        payload = {
            "generated_at": "2026-06-28T00:00:00+00:00",
            "status": "ok",
            "runs": {"compliance": {"request_id": "req-1"}, "rpc": {"request_id": "req-2", "case_id": "case-1"}},
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifact_path, manifest_path = MODULE.write_artifacts(
                payload=payload,
                mode="both",
                output_dir=Path(tmp_dir),
            )

            self.assertTrue(artifact_path.exists())
            self.assertTrue(manifest_path.exists())
            manifest = __import__("json").loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["runs"]["rpc_case_id"], "case-1")
            self.assertTrue(manifest["artifact_file_sha256"])


if __name__ == "__main__":
    unittest.main()
