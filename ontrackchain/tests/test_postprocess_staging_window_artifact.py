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


MODULE = _load_module("postprocess_staging_window_artifact", "scripts/postprocess_staging_window_artifact.py")


def _write_payload(target: Path, *, overall_status: str = "ok") -> None:
    payload = {
        "kind": "staging_window_preparation",
        "status": overall_status,
        "window_id": "stg-2026-07-06-a",
        "mode": "baseline",
        "environment_name": "staging-serious",
        "summary": {"mfa_external_provider_homologated": "false"},
        "artifacts": {
            "checks_dir": "artifacts/staging/checks",
            "window_packet_file": "artifacts/staging/window-packet-stg-2026-07-06-a.md",
        },
        "validation": {"status": "ok" if overall_status == "ok" else "failed"},
        "preflight": {"status": "ok" if overall_status == "ok" else "failed"},
        "run": {
            "status": "ok" if overall_status == "ok" else "failed",
            "payload": {
                "steps": {
                    "oidc_preflight": {"status": "ok" if overall_status == "ok" else "failed"},
                    "external_preflight": {"status": "ok" if overall_status == "ok" else "failed"},
                    "release_dossier": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json",
                    },
                    "homologation": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/homologation/external_homologation_both_20260706T120000Z.json",
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


def _write_weekly_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "# Governança Semanal — 2026-07-06",
                "",
                "## Leitura do Ciclo",
                "",
                "- Baseline técnica: `89%`",
                "- Readiness regulatório: `76%`",
                "- Foco da semana: executar a primeira janela séria com evidências anexáveis e dossier final",
                "",
                "## Contexto da Janela Séria",
                "",
                "- `window_id`: `stg-2026-07-06-a`",
                "- `mode`: `baseline`",
                "- `environment_name`: `staging-serious`",
                "- run do GitHub Actions: `pending`",
                "- status esperado: `RUN-STG-01` de `ready -> in_progress` ou `ready -> done` (apenas se dossier final estiver `ok`)",
                "",
                "## Evidências Revisadas",
                "",
                "- artifact `serious-staging-window-stg-2026-07-06-a`: `pending`",
                "- overall status: `pending`",
                "- validation status: `pending`",
                "- preflight status: `pending`",
                "- run status: `pending`",
                "- window packet: `pending`",
                "- dossier: `pending`",
                "- homologation: `pending`",
                "",
                "## Itens Atualizados",
                "",
                "- ID: `RUN-STG-01`",
                "  - status anterior: `ready`",
                "  - status atual: `pending_execucao`",
                "  - owner nominal: `Release Manager Tecnico`",
                "  - artefato revisado: workflow `Staging Serious Window` + artifact `serious-staging-window-stg-2026-07-06-a`",
                "  - próxima evidência esperada: sign-off preenchido com `overall status=ok`, `validation=ok`, `preflight=ok` e `run=ok`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class PostprocessStagingWindowArtifactTests(unittest.TestCase):
    maxDiff = None

    def test_main_generates_signoff_and_updates_weekly_board(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "ci-artifacts" / "prepare-staging-window-output.json"
            governance_dir = base / "docs" / "governance-weekly"
            weekly_file = governance_dir / "2026-07-06-weekly-governance.md"
            stdout = io.StringIO()
            payload_file.parent.mkdir(parents=True, exist_ok=True)
            governance_dir.mkdir(parents=True, exist_ok=True)
            _write_payload(payload_file, overall_status="ok")
            _write_weekly_file(weekly_file)

            with patch.object(
                sys,
                "argv",
                [
                    "postprocess_staging_window_artifact.py",
                    "--payload-file",
                    str(payload_file),
                    "--governance-weekly-dir",
                    str(governance_dir),
                    "--run-url",
                    "https://github.com/example/actions/runs/123",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            result = json.loads(stdout.getvalue())
            signoff_file = Path(result["signoff_output_file"])
            governance_signoff_file = Path(result["governance_signoff_output_file"])
            weekly_content = weekly_file.read_text(encoding="utf-8")
            signoff_content = signoff_file.read_text(encoding="utf-8")
            governance_signoff_content = governance_signoff_file.read_text(encoding="utf-8")
            signoff_exists = signoff_file.exists()
            governance_signoff_exists = governance_signoff_file.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["run_stg_status"], "done")
        self.assertEqual(result["decision"], "pending_manual_approval")
        self.assertTrue(signoff_exists)
        self.assertTrue(governance_signoff_exists)
        self.assertEqual(signoff_content, governance_signoff_content)
        self.assertIn("run url: `https://github.com/example/actions/runs/123`", signoff_content)
        self.assertIn("- overall status: `ok`", weekly_content)
        self.assertIn("  - status atual: `done`", weekly_content)


if __name__ == "__main__":
    unittest.main()
