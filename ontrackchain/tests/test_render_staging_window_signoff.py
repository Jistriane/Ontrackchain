import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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


MODULE = _load_module("render_staging_window_signoff", "scripts/render_staging_window_signoff.py")


def _write_payload(target: Path, *, overall_status: str = "ok") -> None:
    payload = {
        "kind": "staging_window_preparation",
        "status": overall_status,
        "window_id": "stg-2026-07-06-a",
        "mode": "baseline",
        "environment_name": "staging-serious",
        "artifacts": {
            "checks_dir": "artifacts/staging/checks",
            "window_packet_file": "artifacts/staging/window-packet-stg-2026-07-06-a.md",
        },
        "summary": {
            "mfa_external_provider_homologated": "false",
        },
        "validation": {"status": "ok"},
        "preflight": {"status": "ok"},
        "run": {
            "status": "ok" if overall_status == "ok" else "failed",
            "payload": {
                "steps": {
                    "oidc_preflight": {"status": "ok"},
                    "external_preflight": {"status": "ok" if overall_status == "ok" else "failed"},
                    "homologation": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/homologation/homologation-stg-2026-07-06-a.json",
                    },
                    "regulatory_readiness_bundle": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json",
                    },
                    "release_dossier": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json",
                    },
                },
                "files": {
                    "checks_dir": "artifacts/staging/checks",
                    "window_packet_file": "artifacts/staging/window-packet-stg-2026-07-06-a.md",
                },
            },
        },
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RenderStagingWindowSignoffTests(unittest.TestCase):
    maxDiff = None

    def test_render_signoff_markdown_from_successful_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            output_file = base / "staging-serious-window-signoff.md"
            _write_payload(payload_file, overall_status="ok")

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_signoff_model(
                payload=payload,
                payload_file=payload_file,
                run_url="https://github.com/example/actions/runs/123",
                run_name=None,
                workflow_name="Staging Serious Window",
            )
            output_file.write_text(MODULE.render_signoff_markdown(model), encoding="utf-8")
            content = output_file.read_text(encoding="utf-8")

        self.assertEqual(model["decision"], "pending_manual_approval")
        self.assertIn("run url: `https://github.com/example/actions/runs/123`", content)
        self.assertIn("artifact: `serious-staging-window-stg-2026-07-06-a`", content)
        self.assertIn("overall status: `ok`", content)
        self.assertIn("preflight status: `ok`", content)
        self.assertIn("dossier: `artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json`", content)
        self.assertIn("regulatory-readiness-bundle: `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json`", content)
        self.assertIn("AML/KYT runtime gate: `ok`", content)
        self.assertIn("## Regras de Atualizacao", content)

    def test_main_marks_failed_payload_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            output_file = base / "staging-serious-window-signoff.md"
            stdout = io.StringIO()
            _write_payload(payload_file, overall_status="failed")

            with patch.object(
                sys,
                "argv",
                [
                    "render_staging_window_signoff.py",
                    "--payload-file",
                    str(payload_file),
                    "--output-file",
                    str(output_file),
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            result = json.loads(stdout.getvalue())
            content = output_file.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("decisao: `blocked`", content)
        self.assertIn("overall status: `failed`", content)

    def test_main_can_write_versioned_governance_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            output_file = base / "staging-serious-window-signoff.md"
            governance_dir = base / "docs" / "governance-weekly"
            stdout = io.StringIO()
            _write_payload(payload_file, overall_status="ok")

            with patch.object(
                sys,
                "argv",
                [
                    "render_staging_window_signoff.py",
                    "--payload-file",
                    str(payload_file),
                    "--output-file",
                    str(output_file),
                    "--governance-weekly-dir",
                    str(governance_dir),
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            result = json.loads(stdout.getvalue())
            governance_output_file = Path(str(result["governance_output_file"]))
            governance_content = governance_output_file.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(governance_output_file.name, "2026-07-06-staging-serious-window-signoff.md")
        self.assertIn("window_id: `stg-2026-07-06-a`", governance_content)
        self.assertIn("decisao: `pending_manual_approval`", governance_content)


if __name__ == "__main__":
    unittest.main()
