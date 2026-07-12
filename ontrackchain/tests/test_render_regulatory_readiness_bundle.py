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
                    "request_id": "req-compliance-runtime-1",
                    "output_file": "artifacts/staging/checks/stg-2026-07-03-reg-compliance-provider-runtime.json",
                    "errors": [],
                    "correlation": {
                        "internal_operating_mode": "live",
                        "catalog_provider_status": "live",
                        "catalog_capability_status": "live",
                        "runtime_provider_status": "live",
                        "runtime_capability_status": "live",
                        "runtime_delivery_mode": "risk_check_instant",
                        "provider_converges_live": True,
                    },
                },
                "eu_sanctions_window": {
                    "status": "ok",
                    "request_id": "req-eu-window-1",
                    "output_file": "artifacts/staging/checks/stg-2026-07-03-reg-eu-sanctions-window.json",
                    "errors": [],
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
            },
            "readiness": {
                "compliance_runtime": {
                    "readiness_status": "ready_for_validation",
                    "blockers": [],
                    "next_action": "Revisar o artefato de `compliance_provider_runtime` e anexar o bundle regulatorio a governanca semanal.",
                },
                "eu_window": {
                    "readiness_status": "ready_for_validation",
                    "blockers": [],
                    "next_action": "Revisar o artefato de `eu_sanctions_window` e anexar o bundle regulatorio a governanca semanal.",
                },
                "regulatory_bundle": {
                    "readiness_status": "ready_for_validation",
                    "blockers": [],
                    "next_action": "Anexar o bundle regulatorio ao dossier/governanca e executar revisao formal das evidencias.",
                },
            },
        }

        model = MODULE.build_model(payload, Path("bundle.json"))
        rendered = MODULE.render_markdown(model)

        self.assertEqual(model["status"], "ok")
        self.assertEqual(model["bundle_readiness_status"], "ready_for_validation")
        self.assertEqual(model["compliance_request_id"], "req-compliance-runtime-1")
        self.assertIn("Regulatory Readiness Bundle - stg-2026-07-03-reg", rendered)
        self.assertIn("compliance_provider_runtime", rendered)
        self.assertIn("eu_sanctions_window", rendered)
        self.assertIn("bundle regulatorio readiness: `ready_for_validation`", rendered)
        self.assertIn("request_id: `req-compliance-runtime-1`", rendered)
        self.assertIn("convergencia live do provider: `True`", rendered)
        self.assertIn("delivery_mode do runtime AML/KYT: `risk_check_instant`", rendered)
        self.assertIn("request_id: `req-eu-window-1`", rendered)
        self.assertIn("source_url converge com override: `True`", rendered)
        self.assertIn("override tokenizado: `True`", rendered)
        self.assertIn("convergencia pronta da janela UE: `True`", rendered)

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
                            "eu_window_enabled": True,
                        },
                        "errors": ["compliance_provider_runtime: falhou"],
                        "steps": {
                            "compliance_provider_runtime": {
                                "status": "failed",
                                "request_id": "req-compliance-runtime-2",
                                "output_file": "checks/a.json",
                                "errors": ["provider unreachable"],
                                "correlation": {
                                    "internal_operating_mode": "misconfigured",
                                    "catalog_provider_status": "degraded",
                                    "catalog_capability_status": "degraded",
                                    "runtime_provider_status": "degraded",
                                    "runtime_capability_status": "degraded",
                                    "runtime_delivery_mode": "risk_check_instant",
                                    "provider_converges_live": False,
                                },
                            },
                            "eu_sanctions_window": {
                                "status": "skipped",
                                "request_id": "req-eu-window-2",
                                "output_file": "pending",
                                "errors": [],
                                "correlation": {
                                    "expected_source_url": "https://example.test/eu.xml?token=abc123",
                                    "observed_source_url": "",
                                    "source_url_matches_expected": False,
                                    "override_tokenized": True,
                                    "persisted_status": "FAILED",
                                    "persisted_status_active": False,
                                    "last_sync_status": "FAILED",
                                    "last_sync_status_success": False,
                                    "eu_window_converges_ready": False,
                                },
                            },
                        },
                        "readiness": {
                            "compliance_runtime": {
                                "readiness_status": "blocked",
                                "blockers": ["provider unreachable"],
                                "next_action": "Corrigir a trilha `compliance_provider_runtime` e rerodar o bundle regulatorio com insumos reais.",
                            },
                            "eu_window": {
                                "readiness_status": "blocked",
                                "blockers": ["eu_sanctions_window: correlacao estruturada da janela UE nao confirma convergencia pronta para validacao"],
                                "next_action": "Corrigir a correlacao auditavel de `eu_sanctions_window` antes de promover o bundle regulatorio.",
                            },
                            "regulatory_bundle": {
                                "readiness_status": "blocked",
                                "blockers": ["eu_sanctions_window: correlacao estruturada da janela UE nao confirma convergencia pronta para validacao"],
                                "next_action": "Corrigir correlacao ou falhas das trilhas regulatorias antes de promover o bundle oficial.",
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
            self.assertIn("bundle regulatorio readiness: `blocked`", output_file.read_text(encoding="utf-8"))
            self.assertIn(
                "readiness bundle: `eu_sanctions_window: correlacao estruturada da janela UE nao confirma convergencia pronta para validacao`",
                output_file.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
