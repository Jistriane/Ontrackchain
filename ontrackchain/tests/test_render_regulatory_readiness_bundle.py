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
    "render_regulatory_readiness_bundle",
    "scripts/render_regulatory_readiness_bundle.py",
)


class RenderRegulatoryReadinessBundleTests(unittest.TestCase):
    def test_build_model_and_render_markdown(self) -> None:
        payload = {
            "window_id": "stg-2026-07-03-reg",
            "generated_at": "2026-07-03T12:00:00+00:00",
            "status": "ok",
            "scope": {
                "compliance_runtime_enabled": True,
                "eu_window_enabled": True,
            },
            "errors": [],
            "steps": {
                "compliance_provider_runtime": {
                    "status": "ok",
                    "output_file": "artifacts/staging/checks/stg-2026-07-03-reg-compliance-provider-runtime.json",
                    "errors": [],
                },
                "eu_sanctions_window": {
                    "status": "ok",
                    "output_file": "artifacts/staging/checks/stg-2026-07-03-reg-eu-sanctions-window.json",
                    "errors": [],
                },
            },
        }

        model = MODULE.build_model(payload, Path("bundle.json"))
        rendered = MODULE.render_markdown(model)

        self.assertEqual(model["status"], "ok")
        self.assertIn("Regulatory Readiness Bundle - stg-2026-07-03-reg", rendered)
        self.assertIn("compliance_provider_runtime", rendered)
        self.assertIn("eu_sanctions_window", rendered)

    def test_main_writes_markdown_and_json_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            bundle_file = base / "bundle.json"
            output_file = base / "bundle.md"
            bundle_file.write_text(
                json.dumps(
                    {
                        "window_id": "stg-2026-07-03-reg",
                        "generated_at": "2026-07-03T12:00:00+00:00",
                        "status": "failed",
                        "scope": {
                            "compliance_runtime_enabled": True,
                            "eu_window_enabled": False,
                        },
                        "errors": ["compliance_provider_runtime: falhou"],
                        "steps": {
                            "compliance_provider_runtime": {
                                "status": "failed",
                                "output_file": "checks/a.json",
                                "errors": ["provider unreachable"],
                            },
                            "eu_sanctions_window": {
                                "status": "skipped",
                                "output_file": "pending",
                                "errors": [],
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
            self.assertIn("provider unreachable", output_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()