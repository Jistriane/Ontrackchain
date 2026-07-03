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
    "run_oidc_readiness_bundle",
    "scripts/run_oidc_readiness_bundle.py",
)


class RunOidcReadinessBundleTests(unittest.TestCase):
    def test_run_bundle_executes_preflight_and_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            private_env_file = Path(temp_dir) / ".env.staging.private"
            private_env_file.write_text(
                "\n".join(
                    [
                        "MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true",
                        "OIDC_ORG_CLAIM=org_id",
                        "OIDC_PLAN_CLAIM=plan",
                        "OIDC_ROLE_CLAIM=roles",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            checks_dir = Path(temp_dir) / "checks"

            side_effects = [
                (0, {"status": "ok", "errors": []}),
                (0, {"status": "ok", "errors": [], "auth_config": {}}),
            ]

            with patch.object(MODULE, "run_module_capture", side_effect=side_effects):
                exit_code, payload = MODULE.run_bundle(
                    window_id="stg-2026-07-03-oidc",
                    private_env_file=private_env_file,
                    checks_dir=checks_dir,
                    base_url="http://localhost:8080",
                    expected_oidc_provider="keycloak",
                    expected_mfa_provider_homologated="true",
                    expected_org_claim="org_id",
                    expected_plan_claim="plan",
                    expected_role_claim="roles",
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["steps"]["oidc_preflight"]["status"], "ok")
            self.assertEqual(payload["steps"]["smoke_auth_oidc_mode"]["status"], "ok")
            self.assertTrue((checks_dir / "stg-2026-07-03-oidc-oidc-preflight.json").exists())
            self.assertTrue((checks_dir / "stg-2026-07-03-oidc-oidc-smoke-auth.json").exists())

    def test_run_module_capture_wraps_plain_text_failures(self) -> None:
        module_file = Path(tempfile.gettempdir()) / "fake_smoke_auth_module_for_ontrackchain.py"
        module_file.write_text(
            "import sys\n"
            "def main():\n"
            "    sys.stderr.write('assertion failed\\n')\n"
            "    return 1\n",
            encoding="utf-8",
        )

        with patch.object(MODULE, "load_module") as load_module:
            spec = importlib.util.spec_from_file_location("fake_smoke_auth", module_file)
            fake_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fake_module)
            load_module.return_value = fake_module
            exit_code, payload = MODULE.run_module_capture(
                "scripts/smoke_auth_oidc_mode.py",
                ["smoke_auth_oidc_mode.py"],
                "fake_smoke_auth",
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["errors"], ["assertion failed"])

    def test_main_writes_json(self) -> None:
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
                        "window_id": "stg-2026-07-03-oidc",
                        "private_env_file": "/tmp/.env.staging.private",
                        "checks_dir": "/tmp/checks",
                        "base_url": "",
                        "expected_oidc_provider": "keycloak",
                        "expected_mfa_provider_homologated": None,
                        "expected_org_claim": "",
                        "expected_plan_claim": "",
                        "expected_role_claim": "",
                    },
                )(),
            ),
            patch.object(
                MODULE,
                "run_bundle",
                return_value=(0, {"kind": "oidc_readiness_bundle", "status": "ok", "errors": []}),
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