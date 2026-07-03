import importlib.util
import io
import json
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


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
    "render_oidc_readiness_bundle",
    "scripts/render_oidc_readiness_bundle.py",
)


class RenderOidcReadinessBundleTests(unittest.TestCase):
    def test_build_model_and_render_markdown(self) -> None:
        payload = {
            "window_id": "stg-2026-07-03-oidc",
            "generated_at": "2026-07-03T12:00:00+00:00",
            "status": "ok",
            "scope": {
                "mfa_external_provider_homologated": "true",
                "expected_oidc_provider": "keycloak",
            },
            "errors": [],
            "steps": {
                "oidc_preflight": {
                    "status": "ok",
                    "output_file": "checks/oidc-preflight.json",
                    "errors": [],
                },
                "smoke_auth_oidc_mode": {
                    "status": "ok",
                    "output_file": "checks/oidc-smoke-auth.json",
                    "errors": [],
                },
            },
        }

        model = MODULE.build_model(payload, Path("bundle.json"))
        rendered = MODULE.render_markdown(model)

        self.assertEqual(model["status"], "ok")
        self.assertIn("OIDC Readiness Bundle - stg-2026-07-03-oidc", rendered)
        self.assertIn("smoke_auth_oidc_mode", rendered)

    def test_main_writes_markdown_and_json_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            bundle_file = base / "bundle.json"
            output_file = base / "bundle.md"
            bundle_file.write_text(
                json.dumps(
                    {
                        "window_id": "stg-2026-07-03-oidc",
                        "generated_at": "2026-07-03T12:00:00+00:00",
                        "status": "failed",
                        "scope": {
                            "mfa_external_provider_homologated": "false",
                            "expected_oidc_provider": "keycloak",
                        },
                        "errors": ["smoke_auth_oidc_mode: falhou"],
                        "steps": {
                            "oidc_preflight": {
                                "status": "ok",
                                "output_file": "checks/a.json",
                                "errors": [],
                            },
                            "smoke_auth_oidc_mode": {
                                "status": "failed",
                                "output_file": "checks/b.json",
                                "errors": ["auth_config mismatch"],
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                with unittest.mock.patch.object(
                    MODULE,
                    "parse_args",
                    return_value=type(
                        "Args",
                        (),
                        {
                            "bundle_file": str(bundle_file),
                            "output_file": str(output_file),
                        },
                    )(),
                ):
                    exit_code = MODULE.main()

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue().strip() or stderr.getvalue().strip())
            self.assertEqual(payload["status"], "ok")
            self.assertTrue(output_file.exists())
            self.assertIn("auth_config mismatch", output_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()