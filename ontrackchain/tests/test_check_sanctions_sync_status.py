import importlib.util
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
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


MODULE = _load_module("check_sanctions_sync_status", "scripts/check_sanctions_sync_status.py")


class CheckSanctionsSyncStatusTests(unittest.TestCase):
    maxDiff = None

    def test_build_payload_accepts_expected_success_states(self) -> None:
        rows = [
            {
                "list_name": "EU_CONSOLIDATED",
                "source_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
            {
                "list_name": "OFAC_SDN",
                "source_url": "https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
            {
                "list_name": "UN_CSNU",
                "source_url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
        ]

        with patch.object(MODULE, "_load_rows", return_value=rows):
            payload = MODULE.build_payload(
                database_url="postgresql://example",
                list_names=["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED"],
                require_success=["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED"],
                eu_override_url="https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                ofac_override_url="https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML",
                request_id="req-eu-sync-1",
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["request_id"], "req-eu-sync-1")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(len(payload["checks"]), 3)
        eu_check = next(item for item in payload["checks"] if item["list_name"] == "EU_CONSOLIDATED")
        self.assertEqual(eu_check["status"], "ok")
        self.assertEqual(
            eu_check["source_url"],
            "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
        )
        self.assertEqual(eu_check["last_sync_status"], "SUCCESS")
        self.assertTrue(payload["correlation"]["override_tokenized"])
        self.assertTrue(payload["correlation"]["persisted_status_active"])
        self.assertTrue(payload["correlation"]["last_sync_status_success"])
        self.assertTrue(payload["correlation"]["eu_window_converges_ready"])

    def test_build_payload_flags_eu_failure_when_override_requires_success(self) -> None:
        rows = [
            {
                "list_name": "EU_CONSOLIDATED",
                "source_url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                "status": "ACTIVE",
                "last_sync_status": "FAILED",
                "status_reason": "403 from provider",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
            {
                "list_name": "OFAC_SDN",
                "source_url": "https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
            {
                "list_name": "UN_CSNU",
                "source_url": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            },
        ]

        with patch.object(MODULE, "_load_rows", return_value=rows):
            payload = MODULE.build_payload(
                database_url="postgresql://example",
                list_names=["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED"],
                require_success=["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED"],
                eu_override_url="https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                ofac_override_url="",
                request_id="req-eu-sync-2",
            )

        self.assertEqual(payload["status"], "failed")
        self.assertIn("EU_CONSOLIDATED: last_sync_status esperado=SUCCESS recebido=FAILED", payload["errors"])
        self.assertFalse(payload["correlation"]["last_sync_status_success"])
        self.assertFalse(payload["correlation"]["eu_window_converges_ready"])

    def test_build_payload_requires_eu_override_for_eu_window(self) -> None:
        rows = [
            {
                "list_name": "EU_CONSOLIDATED",
                "source_url": "",
                "status": "ACTIVE",
                "last_sync_status": "SUCCESS",
                "status_reason": "",
                "updated_at": "2026-07-01T10:00:00+00:00",
            }
        ]

        with patch.object(MODULE, "_load_rows", return_value=rows):
            payload = MODULE.build_payload(
                database_url="postgresql://example",
                list_names=["EU_CONSOLIDATED"],
                require_success=["EU_CONSOLIDATED"],
                eu_override_url="",
                ofac_override_url="",
                require_eu_override=True,
                request_id="req-eu-sync-3",
            )

        self.assertEqual(payload["status"], "failed")
        self.assertIn(
            "COMPLIANCE_EU_SANCTIONS_SOURCE_URL: override tokenizado obrigatorio para janela UE",
            payload["errors"],
        )
        self.assertTrue(payload["overrides"]["eu_required"])
        self.assertFalse(payload["correlation"]["override_present"])
        self.assertFalse(payload["correlation"]["eu_window_converges_ready"])

    def test_main_eu_window_promotes_eu_to_required_success(self) -> None:
        captured: dict[str, Any] = {}

        def fake_build_payload(**kwargs):
            captured.update(kwargs)
            return {
                "kind": "sanctions_sync_status_check",
                "status": "ok",
                "errors": [],
                "checks": [],
                "list_names": kwargs["list_names"],
                "require_success": kwargs["require_success"],
                "overrides": {
                    "eu_present": bool(kwargs["eu_override_url"]),
                    "eu_required": bool(kwargs["require_eu_override"]),
                    "eu_tokenized": True,
                    "ofac_present": False,
                },
                "request_id": kwargs["request_id"],
            }

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(MODULE, "build_payload", side_effect=fake_build_payload),
            patch(
                "sys.argv",
                [
                    "check_sanctions_sync_status.py",
                    "--database-url",
                    "postgresql://example",
                    "--lists",
                    "OFAC_SDN,UN_CSNU",
                    "--eu-window",
                    "--eu-override-url",
                    "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                    "--request-id",
                    "req-eu-sync-4",
                ],
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("EU_CONSOLIDATED", captured["list_names"])
        self.assertIn("EU_CONSOLIDATED", captured["require_success"])
        self.assertTrue(captured["require_eu_override"])
        self.assertEqual(captured["request_id"], "req-eu-sync-4")

    def test_main_requires_database_url(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.argv", ["check_sanctions_sync_status.py"]):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = MODULE.main()

        payload = json.loads(stderr.getvalue().strip() or stdout.getvalue().strip())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("DATABASE_URL: variavel obrigatoria ausente", payload["errors"])


if __name__ == "__main__":
    unittest.main()
