import importlib.util
import json
import tempfile
import unittest
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
    "render_staging_window_operational_board",
    "scripts/render_staging_window_operational_board.py",
)


def _write_payload(
    target: Path,
    *,
    oidc_status: str = "ready",
    compliance_enabled: bool = True,
    compliance_status: str = "ok",
    eu_enabled: bool = False,
    eu_status: str = "skipped",
) -> None:
    payload = {
        "kind": "staging_window_preparation",
        "status": "ok",
        "window_id": "stg-2026-07-06-a",
        "mode": "baseline",
        "environment_name": "staging-serious",
        "artifacts": {
            "window_packet_file": "artifacts/staging/window-packet-stg-2026-07-06-a.md",
        },
        "validation": {"status": "ok"},
        "preflight": {"status": "ok"},
        "run": {
            "status": "ok",
            "payload": {
                "steps": {
                    "release_dossier": {
                        "status": "ok",
                        "artifact_file": "artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a.json",
                    },
                    "homologation": {
                        "status": "ok",
                        "artifact_file": "artifacts/homologation/external_homologation_both_20260706T120000Z.json",
                    },
                    "oidc_readiness_bundle": {
                        "status": "ok",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json",
                        "readiness_status": oidc_status,
                        "readiness_blockers": [],
                        "next_action": "pending",
                    },
                    "regulatory_readiness_bundle": {
                        "status": "ok",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json",
                        "compliance_runtime_enabled": compliance_enabled,
                        "eu_window_enabled": eu_enabled,
                        "compliance_provider_runtime_status": compliance_status,
                        "eu_sanctions_window_status": eu_status,
                        "errors": [],
                    },
                }
            },
        },
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_board(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "# Board Operacional Unico ate 90%+",
                "",
                "## Fila Prioritaria",
                "",
                "### P0 — Move KPI e destrava prontidao seria",
                "",
                "| ID | Status Inicial | Iniciativa | Owner Sugerido | Dependencias | Evidencia Exigida | Impacto no KPI | Criterio de Fechamento |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
                "| `P0-01` | `blocked` | Homologar `OIDC + MFA serio` | Backend/Auth | owner IdP, ambiente serio, claims finais | `preflight_oidc_serious_env.py` verde, `smoke_auth_oidc_mode.py` verde, bundle `<window>-oidc-readiness-bundle.json`, Playwright critico verde | muito alto | fluxos sensiveis exigem auth serio e MFA homologado sem fallback silencioso |",
                "| `P0-02` | `ready` | Homologar `AML/KYT live` | Backend/Compliance | credencial real do provider | `check_compliance_provider_runtime.py` verde + artefato JSON | muito alto | readiness interna e API publica convergem com provider `live` |",
                "| `P0-03` | `ready` | Ativar feed UE real | Backend/Compliance | URL tokenizada valida | JSONs da janela UE + `check_sanctions_sync_status.py` verde | muito alto | `EU_CONSOLIDATED` fica valido e os artefatos da janela sao persistidos |",
                "| `P0-04` | `todo` | Gerar bundle regulatorio oficial | Platform/SRE | `P0-02`, `P0-03` | `<window>-regulatory-readiness-bundle.json` | muito alto | bundle reflete AML/KYT + sancoes UE sem erro residual nao classificado |",
                "",
                "### Leitura Sugerida no Inicio do Dia 1",
                "",
                "| Item | Status sugerido | Racional operacional | Condicao para mudar |",
                "| --- | --- | --- | --- |",
                "| `P0-01` | `blocked` | ainda depende de owner IdP, ambiente serio e validacao externa de MFA | mover para `in_progress` so quando houver owner confirmado e trilho serio verificavel |",
                "| `P0-02` | `ready` | a trilha ja tem owner e checker definido, mas ainda depende de credencial real | mover para `in_progress` quando a credencial AML/KYT estiver disponivel para execucao |",
                "| `P0-03` | `ready` | a trilha ja tem owner e rito claro, mas ainda depende de URL tokenizada real da UE | mover para `in_progress` quando a URL real estiver confirmada no ambiente |",
                "| `P0-04` | `todo` | depende diretamente da conclusao operacional de `P0-02` e `P0-03` | mover para `ready` apenas depois que `P0-02` e `P0-03` estiverem ao menos em `ready_for_validation` |",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class RenderStagingWindowOperationalBoardTests(unittest.TestCase):
    def test_updates_board_with_regulatory_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "payload.json"
            board_file = base / "project-operational-execution-board.md"
            _write_payload(
                payload_file,
                oidc_status="ready",
                compliance_enabled=True,
                compliance_status="ok",
                eu_enabled=False,
                eu_status="skipped",
            )
            _write_board(board_file)

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_model(payload=payload, payload_file=payload_file)
            content = board_file.read_text(encoding="utf-8")
            updated = MODULE.update_operational_board_markdown(content, model)
            board_file.write_text(updated, encoding="utf-8")
            final = board_file.read_text(encoding="utf-8")

        self.assertEqual(model["p0_01_status"], "ready")
        self.assertEqual(model["p0_02_status"], "ready_for_validation")
        self.assertEqual(model["p0_03_status"], "ready")
        self.assertEqual(model["p0_04_status"], "todo")
        self.assertEqual(model["regulatory_scope_label"], "P0-02")
        self.assertIn("| `P0-02` | `ready_for_validation` | Homologar `AML/KYT live` |", final)
        self.assertIn("| `P0-03` | `ready` | Ativar feed UE real |", final)
        self.assertIn(
            "| `P0-04` | `todo` | Gerar bundle regulatorio oficial | Platform/SRE | tentativa atual: `P0-02`; promocao oficial ainda exige `P0-02` + `P0-03` |",
            final,
        )
        self.assertIn(
            "| `P0-03` | `ready` | trilha fora do escopo da tentativa atual; manter `P0-03` pronta para a janela combinada oficial |",
            final,
        )

    def test_updates_board_when_both_regulatory_tracks_are_ready_for_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            payload_file = base / "payload.json"
            board_file = base / "project-operational-execution-board.md"
            _write_payload(
                payload_file,
                oidc_status="ready_for_validation",
                compliance_enabled=True,
                compliance_status="ok",
                eu_enabled=True,
                eu_status="ok",
            )
            _write_board(board_file)

            payload = MODULE.load_json_file(payload_file)
            model = MODULE.build_model(payload=payload, payload_file=payload_file)
            updated = MODULE.update_operational_board_markdown(board_file.read_text(encoding="utf-8"), model)
            board_file.write_text(updated, encoding="utf-8")
            final = board_file.read_text(encoding="utf-8")

        self.assertEqual(model["p0_04_status"], "ready")
        self.assertEqual(model["regulatory_scope_label"], "P0-02/P0-03")
        self.assertIn("| `P0-04` | `ready` | Gerar bundle regulatorio oficial |", final)
        self.assertIn("| `P0-01` | `ready_for_validation` | Homologar `OIDC + MFA serio` |", final)
        self.assertIn(
            "| `P0-04` | `ready` | depende diretamente da conclusao operacional de `P0-02` e `P0-03` |",
            final,
        )


if __name__ == "__main__":
    unittest.main()
