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


MODULE = _load_module(
    "run_regulatory_readiness_bundle",
    "scripts/run_regulatory_readiness_bundle.py",
)


class RunRegulatoryReadinessBundleTests(unittest.TestCase):
    maxDiff = None

    def test_run_bundle_executes_compliance_and_eu_steps_when_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "\n".join(
                    [
                        "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                        "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://example.test/eu.xml?token=abc123",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            side_effects = [
                (
                    0,
                    {
                        "status": "ok",
                        "request_id": "req-compliance-runtime-1",
                        "errors": [],
                        "checks": [],
                        "correlation": {
                            "internal_operating_mode": "live",
                            "catalog_provider_status": "live",
                            "runtime_provider_status": "live",
                            "provider_converges_live": True,
                        },
                    },
                ),
                (
                    0,
                    {
                        "kind": "eu_sanctions_window_run",
                        "status": "ok",
                        "errors": [],
                        "request_id": "req-eu-window-1",
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
                        "steps": {},
                    },
                ),
            ]

            with patch.object(MODULE, "run_module_main", side_effect=side_effects):
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-06-a",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    internal_base_url="http://compliance-api:8002",
                    public_base_url="http://localhost:8080",
                    force_compliance_runtime=False,
                    force_eu_window=False,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(
                payload["steps"]["compliance_provider_runtime"]["request_id"],
                "req-compliance-runtime-1",
            )
            self.assertTrue(
                payload["steps"]["compliance_provider_runtime"]["correlation"]["provider_converges_live"]
            )
            self.assertEqual(
                payload["readiness"]["compliance_runtime"]["readiness_status"],
                "ready_for_validation",
            )
            self.assertEqual(
                payload["readiness"]["eu_window"]["readiness_status"],
                "ready_for_validation",
            )
            self.assertEqual(
                payload["steps"]["eu_sanctions_window"]["request_id"],
                "req-eu-window-1",
            )
            self.assertTrue(
                payload["steps"]["eu_sanctions_window"]["correlation"]["source_url_matches_expected"]
            )
            self.assertTrue(
                payload["steps"]["eu_sanctions_window"]["correlation"]["eu_window_converges_ready"]
            )
            self.assertEqual(
                payload["readiness"]["regulatory_bundle"]["readiness_status"],
                "ready_for_validation",
            )
            self.assertEqual(
                payload["scope"],
                {
                    "compliance_runtime_enabled": True,
                    "eu_window_enabled": True,
                },
            )
            self.assertTrue(
                (checks_dir / "stg-2026-07-06-a-compliance-provider-runtime.json").exists()
            )
            self.assertTrue(
                (checks_dir / "stg-2026-07-06-a-eu-sanctions-window.json").exists()
            )

    def test_run_bundle_skips_out_of_scope_steps_when_only_compliance_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            with patch.object(
                MODULE,
                "run_module_main",
                return_value=(
                    0,
                    {
                        "status": "ok",
                        "errors": [],
                        "checks": [],
                        "correlation": {"provider_converges_live": True},
                    },
                ),
            ) as run_module_main:
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-06-a",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    internal_base_url="",
                    public_base_url="",
                    force_compliance_runtime=False,
                    force_eu_window=False,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(run_module_main.call_count, 1)
            self.assertTrue(
                payload["steps"]["compliance_provider_runtime"]["request_id"].startswith("stg-2026-07-06-a-compliance-")
            )
            self.assertEqual(
                payload["readiness"]["compliance_runtime"]["readiness_status"],
                "ready_for_validation",
            )
            self.assertEqual(
                payload["readiness"]["eu_window"]["readiness_status"],
                "ready",
            )
            self.assertEqual(
                payload["readiness"]["regulatory_bundle"]["readiness_status"],
                "ready",
            )
            self.assertIn(
                "P0-02 e P0-03 simultaneamente",
                payload["readiness"]["regulatory_bundle"]["next_action"],
            )
            self.assertEqual(
                payload["steps"]["eu_sanctions_window"]["status"],
                "skipped",
            )
            self.assertEqual(
                payload["steps"]["eu_sanctions_window"]["reason"],
                "out_of_scope",
            )

    def test_run_bundle_skips_when_no_regulatory_gate_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text("", encoding="utf-8")
            checks_dir = Path(temp_dir) / "checks"

            exit_code, payload = MODULE.run_bundle(
                window_id="stg-2026-07-06-a",
                private_env_file=private_env_file,
                checks_dir=checks_dir,
                internal_base_url="",
                public_base_url="",
                force_compliance_runtime=False,
                force_eu_window=False,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "skipped")
            self.assertEqual(
                payload["readiness"]["regulatory_bundle"]["readiness_status"],
                "ready",
            )
            self.assertEqual(payload["steps"]["compliance_provider_runtime"]["reason"], "out_of_scope")

    def test_run_bundle_marks_compliance_as_blocked_when_runtime_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            with patch.object(
                MODULE,
                "run_module_main",
                return_value=(1, {"status": "failed", "errors": ["provider unreachable"], "checks": []}),
            ):
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-06-a",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    internal_base_url="",
                    public_base_url="",
                    force_compliance_runtime=False,
                    force_eu_window=False,
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["readiness"]["compliance_runtime"]["readiness_status"], "blocked")
        self.assertIn("provider unreachable", payload["readiness"]["compliance_runtime"]["blockers"])

    def test_run_bundle_blocks_when_compliance_correlation_does_not_confirm_live_convergence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            with patch.object(
                MODULE,
                "run_module_main",
                return_value=(
                    0,
                    {
                        "status": "ok",
                        "errors": [],
                        "checks": [],
                        "request_id": "req-compliance-runtime-3",
                        "correlation": {
                            "internal_operating_mode": "live",
                            "catalog_provider_status": "live",
                            "runtime_provider_status": "degraded",
                            "provider_converges_live": False,
                        },
                    },
                ),
            ):
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-06-a",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    internal_base_url="",
                    public_base_url="",
                    force_compliance_runtime=False,
                    force_eu_window=False,
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["readiness"]["compliance_runtime"]["readiness_status"], "blocked")
        self.assertIn(
            "correlacao estruturada do provider nao confirma convergencia live",
            "; ".join(payload["readiness"]["compliance_runtime"]["blockers"]),
        )

    def test_run_bundle_blocks_when_eu_correlation_is_inconsistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://example.test/eu.xml?token=abc123\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            with patch.object(
                MODULE,
                "run_module_main",
                return_value=(
                    0,
                    {
                        "kind": "eu_sanctions_window_run",
                        "status": "ok",
                        "errors": [],
                        "request_id": "req-eu-window-2",
                        "correlation": {
                            "expected_source_url": "https://example.test/eu.xml?token=abc123",
                            "observed_source_url": "https://example.test/other.xml?token=zzz",
                            "source_url_matches_expected": False,
                            "override_tokenized": True,
                            "persisted_status": "ACTIVE",
                            "persisted_status_active": True,
                            "last_sync_status": "FAILED",
                            "last_sync_status_success": False,
                            "eu_window_converges_ready": False,
                        },
                        "steps": {},
                    },
                ),
            ):
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-06-a",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    internal_base_url="",
                    public_base_url="",
                    force_compliance_runtime=False,
                    force_eu_window=False,
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["readiness"]["eu_window"]["readiness_status"], "blocked")
        self.assertEqual(payload["readiness"]["regulatory_bundle"]["readiness_status"], "blocked")
        self.assertIn(
            "correlacao estruturada da janela UE nao confirma convergencia pronta para validacao",
            "; ".join(payload["readiness"]["eu_window"]["blockers"]),
        )

    def test_main_writes_json_to_stdout_on_success(self) -> None:
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
                        "window_id": "stg-2026-07-06-a",
                        "private_env_file": "/tmp/.env.staging.private",
                        "checks_dir": "/tmp/checks",
                        "internal_base_url": "",
                        "public_base_url": "",
                        "include_compliance_runtime": False,
                        "include_eu_window": False,
                    },
                )(),
            ),
            patch.object(
                MODULE,
                "run_bundle",
                return_value=(0, {"kind": "regulatory_readiness_bundle", "status": "ok", "errors": []}),
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
