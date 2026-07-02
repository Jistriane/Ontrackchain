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
                        "errors": [],
                        "checks": [],
                    },
                ),
                (
                    0,
                    {
                        "kind": "eu_sanctions_window_run",
                        "status": "ok",
                        "errors": [],
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
                return_value=(0, {"status": "ok", "errors": [], "checks": []}),
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
            self.assertEqual(payload["steps"]["compliance_provider_runtime"]["reason"], "out_of_scope")

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
