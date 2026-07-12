import importlib.util
import io
import json
import tempfile
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


MODULE = _load_module("run_eu_sanctions_window", "scripts/run_eu_sanctions_window.py")


class RunEuSanctionsWindowTests(unittest.TestCase):
    maxDiff = None

    def test_run_window_persists_preflight_and_sync_outputs_on_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://example.test/eu.xml?token=abc123\nDATABASE_URL=postgresql://example\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            side_effects = [
                (
                    0,
                    {
                        "status": "ok",
                        "errors": [],
                        "request_id": "req-eu-window-1",
                    },
                ),
                (
                    0,
                    {
                        "status": "ok",
                        "errors": [],
                        "request_id": "req-eu-window-1",
                        "checks": [
                            {
                                "list_name": "EU_CONSOLIDATED",
                                "status": "ok",
                                "source_url": "https://example.test/eu.xml?token=abc123",
                                "persisted_status": "ACTIVE",
                                "last_sync_status": "SUCCESS",
                                "status_reason": "",
                                "updated_at": "2026-07-01T12:00:00+00:00",
                            }
                        ],
                        "correlation": {
                            "expected_source_url": "https://example.test/eu.xml?token=abc123",
                            "observed_source_url": "https://example.test/eu.xml?token=abc123",
                            "source_url_matches_expected": True,
                            "override_tokenized": True,
                            "persisted_status": "ACTIVE",
                            "persisted_status_active": True,
                            "last_sync_status": "SUCCESS",
                            "last_sync_status_success": True,
                            "eu_window_converges_ready": True,
                        },
                    },
                ),
            ]

            with patch.object(MODULE, "run_module_main", side_effect=side_effects):
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-07-01-eu",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    request_id="req-eu-window-1",
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["request_id"], "req-eu-window-1")
            self.assertEqual(payload["errors"], [])
            self.assertTrue((checks_dir / "stg-2026-07-01-eu-eu-sanctions-preflight.json").exists())
            self.assertTrue((checks_dir / "stg-2026-07-01-eu-eu-sanctions-sync.json").exists())
            self.assertEqual(payload["steps"]["external_preflight"]["status"], "ok")
            self.assertEqual(payload["steps"]["eu_sync_status"]["status"], "ok")
            self.assertEqual(payload["steps"]["eu_sync_status"]["request_id"], "req-eu-window-1")
            self.assertTrue(payload["correlation"]["source_url_matches_expected"])
            self.assertTrue(payload["correlation"]["eu_window_converges_ready"])

    def test_run_window_skips_sync_when_preflight_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text("", encoding="utf-8")
            checks_dir = Path(temp_dir) / "checks"

            with patch.object(
                MODULE,
                "run_module_main",
                return_value=(
                    1,
                    {
                        "status": "failed",
                        "errors": ["COMPLIANCE_EU_SANCTIONS_SOURCE_URL ausente"],
                    },
                ),
            ) as run_module_main:
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-07-01-eu",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    request_id="req-eu-window-2",
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(run_module_main.call_count, 1)
            self.assertEqual(payload["steps"]["eu_sync_status"]["status"], "skipped")
            self.assertEqual(payload["steps"]["eu_sync_status"]["request_id"], "req-eu-window-2")
            self.assertIn("external_preflight: falhou", payload["errors"])

    def test_main_renders_json_to_stdout_on_success(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            patch.object(
                MODULE,
                "parse_args",
                return_value=type(
                    "Args",
                    (),
                    {
                        "window_id": "stg-2026-07-01-eu",
                        "private_env_file": "/tmp/.env.staging.private",
                        "checks_dir": "/tmp/checks",
                        "request_id": "req-eu-window-3",
                    },
                )(),
            ),
            patch.object(
                MODULE,
                "run_window",
                return_value=(
                    0,
                    {
                        "kind": "eu_sanctions_window_run",
                        "status": "ok",
                        "errors": [],
                        "request_id": "req-eu-window-3",
                    },
                ),
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue().strip() or stderr.getvalue().strip())
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()
