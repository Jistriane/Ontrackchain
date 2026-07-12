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


MODULE = _load_module("render_staging_window_weekly_governance", "scripts/render_staging_window_weekly_governance.py")


def _write_payload(
    target: Path,
    *,
    overall_status: str = "ok",
    oidc_readiness_status: str = "ready",
    oidc_readiness_blockers: list[str] | None = None,
    oidc_next_action: str = "Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais.",
    compliance_runtime_enabled: bool = True,
    compliance_provider_runtime_status: str = "ok",
    eu_window_enabled: bool = False,
    eu_sanctions_window_status: str = "skipped",
    regulatory_errors: list[str] | None = None,
) -> None:
    payload = {
        "kind": "staging_window_preparation",
        "status": overall_status,
        "window_id": "stg-2026-07-06-a",
        "mode": "baseline",
        "environment_name": "staging-serious",
        "artifacts": {
            "window_packet_file": "artifacts/staging/window-packet-stg-2026-07-06-a.md",
        },
        "validation": {"status": "ok" if overall_status == "ok" else "failed"},
        "preflight": {"status": "ok" if overall_status == "ok" else "failed"},
        "run": {
            "status": "ok" if overall_status == "ok" else "failed",
            "payload": {
                "steps": {
                    "release_dossier": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json",
                    },
                    "homologation": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "artifact_file": "artifacts/homologation/external_homologation_both_20260706T120000Z.json",
                    },
                    "oidc_readiness_bundle": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json",
                        "readiness_status": oidc_readiness_status,
                        "readiness_blockers": oidc_readiness_blockers or [],
                        "next_action": oidc_next_action,
                    },
                    "regulatory_readiness_bundle": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json",
                        "compliance_runtime_enabled": compliance_runtime_enabled,
                        "eu_window_enabled": eu_window_enabled,
                        "compliance_provider_runtime_status": compliance_provider_runtime_status,
                        "eu_sanctions_window_status": eu_sanctions_window_status,
                        "errors": regulatory_errors or [],
                    },
                }
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
                "- oidc bundle summary: `pending`",
                "- regulatory bundle summary: `pending`",
                "",
                "## Itens Atualizados",
                "",
                "- ID: `P0-01`",
                "  - status anterior: `blocked`",
                "  - status atual: `blocked`",
                "  - owner nominal: `Tech Lead Auth`",
                "  - artefato revisado: trilho serio de `OIDC/MFA` e critérios de aceite institucional",
                "  - próxima evidência esperada: evidência externa homologada com `X-MFA-Mode=external_provider`",
                "",
                "- ID: `P0-02`",
                "  - status anterior: `ready`",
                "  - status atual: `ready`",
                "  - owner nominal: `Owner de Integracao AML`",
                "  - artefato revisado: gate `make check-compliance-provider-runtime` e bundle de homologação `AML/KYT live`",
                "  - próxima evidência esperada: execução verde com credenciais reais e bundle anexado",
                "",
                "- ID: `P0-03`",
                "  - status anterior: `ready`",
                "  - status atual: `ready`",
                "  - owner nominal: `Owner de Compliance/Sancoes`",
                "  - artefato revisado: runner `make run-eu-sanctions-window-local` e checker `EU_CONSOLIDATED`",
                "  - próxima evidência esperada: `source_url` tokenizada válida + JSONs `<janela>-eu-sanctions-*.json`",
                "",
                "- ID: `RUN-STG-01`",
                "  - status anterior: `ready`",
                "  - status atual: `pending_execucao`",
                "  - owner nominal: `Release Manager Tecnico`",
                "  - artefato revisado: workflow `Staging Serious Window` + artifact `serious-staging-window-stg-2026-07-06-a`",
                "  - próxima evidência esperada: sign-off preenchido com `overall status=ok`, `validation=ok`, `preflight=ok` e `run=ok`",
                "",
                "## Itens Blocked",
                "",
                "- ID: `P0-01`",
                "  - motivo: homologação formal de identidade forte ainda depende de evidência externa e aceite institucional",
                "  - dependência externa: provider de identidade e validação do fluxo sério com `external_provider`",
                "  - owner da escalação: `Tech Lead Auth`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class RenderStagingWindowWeeklyGovernanceTests(unittest.TestCase):
    maxDiff = None

    def test_updates_weekly_governance_file_from_successful_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            weekly_file = base / "2026-07-06-weekly-governance.md"
            _write_payload(payload_file, overall_status="ok")
            _write_weekly_file(weekly_file)

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_weekly_sync_model(
                payload=payload,
                payload_file=payload_file,
                run_url="https://github.com/example/actions/runs/123",
            )
            updated = MODULE.update_weekly_governance_markdown(weekly_file.read_text(encoding="utf-8"), model)
            weekly_file.write_text(updated, encoding="utf-8")
            content = weekly_file.read_text(encoding="utf-8")

        self.assertIn("- run do GitHub Actions: `https://github.com/example/actions/runs/123`", content)
        self.assertIn("- overall status: `ok`", content)
        self.assertIn("- dossier: `artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json`", content)
        self.assertIn("- homologation: `artifacts/homologation/external_homologation_both_20260706T120000Z.json`", content)
        self.assertIn(
            "- oidc bundle summary: `status=ready; blockers=none_declared; next_action=Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais.`",
            content,
        )
        self.assertIn(
            "- regulatory bundle summary: `status=ok; scope=P0-02; output_file=artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json`",
            content,
        )
        self.assertIn("  - status atual: `ready`", content)
        self.assertIn(
            "  - artefato revisado: bundle `oidc-readiness-bundle` e gates do trilho serio `OIDC/MFA` com status `ready`",
            content,
        )
        self.assertIn(
            "  - próxima evidência esperada: Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais.",
            content,
        )
        self.assertIn("  - status atual: `ready_for_validation`", content)
        self.assertIn(
            "  - artefato revisado: bundle regulatorio `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` e step `compliance_provider_runtime` com status `ok`",
            content,
        )
        self.assertIn(
            "  - próxima evidência esperada: revisao formal da governanca semanal com bundle regulatorio e artefatos anexados",
            content,
        )
        self.assertIn(
            "  - artefato revisado: bundle regulatorio `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` com `P0-03` fora do escopo desta tentativa",
            content,
        )
        self.assertIn(
            "  - próxima evidência esperada: fora do escopo da tentativa atual; manter P0-03 pronto para a janela combinada oficial",
            content,
        )
        self.assertIn("  - status atual: `done`", content)
        self.assertNotIn("## Itens Blocked\n\n- ID: `P0-01`", content)

    def test_main_can_resolve_weekly_file_from_governance_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            governance_dir = base / "docs" / "governance-weekly"
            weekly_file = governance_dir / "cycles" / "2026-07-06" / "2026-07-06-weekly-governance.md"
            stdout = io.StringIO()
            weekly_file.parent.mkdir(parents=True, exist_ok=True)
            _write_payload(
                payload_file,
                overall_status="failed",
                oidc_readiness_status="blocked",
                oidc_readiness_blockers=["preflight_oidc_serious_env ainda nao esta verde"],
                oidc_next_action="Corrigir preflight/smoke OIDC e rerodar o bundle antes de qualquer promocao.",
                compliance_runtime_enabled=True,
                compliance_provider_runtime_status="failed",
                eu_window_enabled=True,
                eu_sanctions_window_status="failed",
                regulatory_errors=["compliance_provider_runtime: falhou", "eu_sanctions_window: falhou"],
            )
            _write_weekly_file(weekly_file)

            with patch.object(
                sys,
                "argv",
                [
                    "render_staging_window_weekly_governance.py",
                    "--payload-file",
                    str(payload_file),
                    "--governance-weekly-dir",
                    str(governance_dir),
                    "--run-url",
                    "https://github.com/example/actions/runs/999",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            result = json.loads(stdout.getvalue())
            content = weekly_file.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["run_stg_status"], "blocked")
        self.assertEqual(result["oidc_readiness_status"], "blocked")
        self.assertEqual(result["p0_02_status"], "blocked")
        self.assertEqual(result["p0_03_status"], "blocked")
        self.assertIn("- run do GitHub Actions: `https://github.com/example/actions/runs/999`", content)
        self.assertIn("- overall status: `failed`", content)
        self.assertIn(
            "- oidc bundle summary: `status=blocked; blockers=preflight_oidc_serious_env ainda nao esta verde; next_action=Corrigir preflight/smoke OIDC e rerodar o bundle antes de qualquer promocao.`",
            content,
        )
        self.assertIn("  - status atual: `blocked`", content)
        self.assertIn(
            "  - motivo: preflight_oidc_serious_env ainda nao esta verde",
            content,
        )
        self.assertIn(
            "  - dependência externa: preflight e smoke OIDC ainda nao estabilizados no ambiente serio",
            content,
        )
        self.assertIn(
            "  - próxima evidência esperada: Corrigir preflight/smoke OIDC e rerodar o bundle antes de qualquer promocao.",
            content,
        )
        self.assertIn(
            "  - artefato revisado: bundle `oidc-readiness-bundle` e gates do trilho serio `OIDC/MFA` com status `blocked`",
            content,
        )
        self.assertIn(
            "  - artefato revisado: bundle regulatorio `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` e step `compliance_provider_runtime` com status `failed`",
            content,
        )
        self.assertIn(
            "  - artefato revisado: bundle regulatorio `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` e step `eu_sanctions_window` com status `failed`",
            content,
        )
        self.assertIn("- ID: `P0-02`", content)
        self.assertIn("- ID: `P0-03`", content)
        self.assertIn(
            "  - dependência externa: provider AML/KYT e credencial real homologada no ambiente serio",
            content,
        )
        self.assertIn(
            "  - dependência externa: feed UE tokenizado, source_url valida e sincronizacao oficial da janela",
            content,
        )
        self.assertIn("## Itens Blocked", content)
        self.assertIn("  - status atual: `blocked`", content)

    def test_updates_p0_01_to_ready_for_validation_without_blocked_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            weekly_file = base / "2026-07-06-weekly-governance.md"
            _write_payload(
                payload_file,
                overall_status="ok",
                oidc_readiness_status="ready_for_validation",
                oidc_next_action="Anexar bundle ao war room/sign-off e executar validacao formal com fluxo critico OIDC.",
            )
            _write_weekly_file(weekly_file)

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_weekly_sync_model(
                payload=payload,
                payload_file=payload_file,
                run_url="https://github.com/example/actions/runs/456",
            )
            updated = MODULE.update_weekly_governance_markdown(weekly_file.read_text(encoding="utf-8"), model)
            weekly_file.write_text(updated, encoding="utf-8")
            content = weekly_file.read_text(encoding="utf-8")

        self.assertIn("  - status atual: `ready_for_validation`", content)
        self.assertIn(
            "  - próxima evidência esperada: Anexar bundle ao war room/sign-off e executar validacao formal com fluxo critico OIDC.",
            content,
        )
        self.assertNotIn("- ID: `P0-01`\n  - motivo:", content)

    def test_updates_p0_03_to_ready_for_validation_when_feed_is_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "prepare-staging-window-output.json"
            weekly_file = base / "2026-07-06-weekly-governance.md"
            _write_payload(
                payload_file,
                overall_status="ok",
                compliance_runtime_enabled=False,
                compliance_provider_runtime_status="skipped",
                eu_window_enabled=True,
                eu_sanctions_window_status="ok",
            )
            _write_weekly_file(weekly_file)

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_weekly_sync_model(
                payload=payload,
                payload_file=payload_file,
                run_url="https://github.com/example/actions/runs/457",
            )
            updated = MODULE.update_weekly_governance_markdown(weekly_file.read_text(encoding="utf-8"), model)
            weekly_file.write_text(updated, encoding="utf-8")
            content = weekly_file.read_text(encoding="utf-8")

        self.assertEqual(model["p0_02_status"], "ready")
        self.assertEqual(model["p0_03_status"], "ready_for_validation")
        self.assertIn(
            "  - artefato revisado: bundle regulatorio `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` e step `eu_sanctions_window` com status `ok`",
            content,
        )


if __name__ == "__main__":
    unittest.main()
