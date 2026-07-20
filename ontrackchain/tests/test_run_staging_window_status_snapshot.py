import importlib.util
import sys
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


MODULE = _load_module(
    "run_staging_window_status_snapshot",
    "scripts/run_staging_window_status_snapshot.py",
)


class RunStagingWindowStatusSnapshotTests(unittest.TestCase):
    def test_build_regulatory_snapshot_marks_partial_scope(self) -> None:
        run = {
            "payload": {
                "steps": {
                    "regulatory_readiness_bundle": {
                        "compliance_runtime_enabled": True,
                        "eu_window_enabled": False,
                        "compliance_provider_runtime_status": "ok",
                        "eu_sanctions_window_status": "skipped",
                        "readiness": {
                            "compliance_runtime": {"readiness_status": "ready_for_validation"},
                            "eu_window": {"readiness_status": "ready"},
                            "regulatory_bundle": {"readiness_status": "ready"},
                        },
                    }
                }
            }
        }
        validate = {"payload": {"scope": ["P0-01", "P0-02"]}}

        result = MODULE.build_regulatory_snapshot(run, validate)

        self.assertEqual(result["scope_label"], "P0-02")
        self.assertFalse(result["scope_is_combined"])
        self.assertEqual(result["validation_scope"], ["P0-01", "P0-02"])
        self.assertEqual(result["p0_04_bundle_readiness"], "ready")
        self.assertIn("tentativa parcial", result["promotion_note"])

    def test_build_regulatory_snapshot_marks_combined_scope(self) -> None:
        run = {
            "payload": {
                "steps": {
                    "regulatory_readiness_bundle": {
                        "compliance_runtime_enabled": True,
                        "eu_window_enabled": True,
                        "compliance_provider_runtime_status": "ok",
                        "eu_sanctions_window_status": "ok",
                        "readiness": {
                            "compliance_runtime": {"readiness_status": "ready_for_validation"},
                            "eu_window": {"readiness_status": "ready_for_validation"},
                            "regulatory_bundle": {"readiness_status": "ready_for_validation"},
                        },
                    }
                }
            }
        }
        validate = {"payload": {"scope": ["P0-01", "P0-02", "P0-03"]}}

        result = MODULE.build_regulatory_snapshot(run, validate)

        self.assertEqual(result["scope_label"], "P0-02/P0-03")
        self.assertTrue(result["scope_is_combined"])
        self.assertEqual(result["p0_04_bundle_readiness"], "ready_for_validation")
        self.assertIn("tentativa combinada", result["promotion_note"])

    def test_load_operational_alerts_rca_summary_defaults_when_file_missing(self) -> None:
        result = MODULE.load_operational_alerts_rca_summary(Path("artifacts/staging/checks"), "stg-2026-07-13-a")

        self.assertEqual(result["status"], "not_available")
        self.assertEqual(result["rca_attached_count"], 0)
        self.assertEqual(result["critical_open_count"], 0)

    def test_main_uses_current_python_executable(self) -> None:
        captured_commands: list[list[str]] = []

        def fake_run_command(command: list[str]) -> dict:
            captured_commands.append(command)
            return {"exit_code": 0, "stdout": "{}", "stderr": "", "payload": {"status": "ok"}}

        with patch.object(
            MODULE,
            "parse_args",
            return_value=type(
                "Args",
                (),
                {
                    "window_id": "stg-2026-07-19-a",
                    "private_env_file": ".env.staging.private",
                    "checks_dir": "artifacts/staging/checks",
                    "dossiers_dir": "artifacts/staging/dossiers",
                    "scope": "P0-01,P0-02,P0-03",
                    "output_file": "/tmp/status-snapshot.json",
                    "history_dir": None,
                },
            )(),
        ), patch.object(MODULE, "run_command", side_effect=fake_run_command), patch.object(
            MODULE,
            "collect_blockers",
            return_value={"unresolved_placeholders_count": 0, "missing_handoff_fields_count": 0},
        ), patch.object(
            MODULE,
            "load_operational_alerts_rca_summary",
            return_value={"status": "not_available"},
        ), patch("pathlib.Path.write_text"):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured_commands[0][0], sys.executable)
        self.assertEqual(captured_commands[1][0], sys.executable)
        self.assertEqual(captured_commands[2][0], sys.executable)


if __name__ == "__main__":
    unittest.main()
