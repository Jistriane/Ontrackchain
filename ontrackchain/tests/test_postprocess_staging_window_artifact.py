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
                    "oidc_readiness_bundle": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json",
                        "readiness_status": "ready",
                        "readiness_blockers": [],
                        "next_action": "Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais.",
                    },
                    "regulatory_readiness_bundle": {
                        "status": "ok" if overall_status == "ok" else "failed",
                        "output_file": "artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json",
                        "compliance_runtime_enabled": True,
                        "eu_window_enabled": False,
                        "compliance_provider_runtime_status": "ok",
                        "eu_sanctions_window_status": "skipped",
                        "errors": [],
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


def _write_operational_board_file(target: Path) -> None:
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


def _write_war_room_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "# War Room da Janela Seria — `stg-2026-07-06-a`",
                "",
                "## Contexto",
                "",
                "- data: `2026-07-06`",
                "- window_id: `stg-2026-07-06-a`",
                "- mode: `baseline`",
                "- environment_name: `staging-serious`",
                "- facilitador: `Release Manager Tecnico`",
                "",
                "## Leitura de Go/No-Go",
                "",
                "- status atual: `pending_no_go`",
                "- motivo principal: aguardando insumos reais",
                "- risco residual: `pending`",
                "- proximo checkpoint: preencher checklist e rerodar gate",
                "- hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "",
                "## Trilhas do War Room",
                "",
                "- `P0-02 / Compliance AML-KYT`",
                "  - owner primario: `<preencher>`",
                "  - status: `ready`",
                "  - ultima atualizacao: `pending`",
                "  - dependencia critica: credencial real do provider AML/KYT no ambiente alvo",
                "  - comando: `make check-compliance-provider-runtime`",
                "  - evidencia minima: JSON do runtime verde + homologacao externa preservada + `request_id`",
                "  - criterio de go/no-go: credencial real validada e correlator reconciliado com a homologacao",
                "  - observacoes: candidato mais proximo a mover a baseline",
                "- `P0-03 / Feed UE`",
                "  - owner primario: `<preencher>`",
                "  - status: `ready`",
                "  - ultima atualizacao: `pending`",
                "  - dependencia critica: URL tokenizada real e sincronizacao coerente da janela UE",
                "  - comando: `make run-eu-sanctions-window-local`",
                "  - evidencia minima: JSONs de `preflight` e `sync` + `source_url_matches_expected=true` + `request_id`",
                "  - criterio de go/no-go: feed real validado com correlator e prova persistida",
                "  - observacoes: segunda metade obrigatoria para promover `P0-04`",
                "- `P0-04 / Bundle Regulatorio`",
                "  - owner primario: `<preencher>`",
                "  - status: `pending`",
                "  - ultima atualizacao: `pending`",
                "  - dependencia critica: `P0-02` e `P0-03` com prova revisavel na mesma janela",
                "  - comando: `make run-regulatory-readiness-bundle-local`",
                "  - evidencia minima: bundle oficial em `ready_for_validation` + validacao final do artifact `ok`",
                "  - criterio de go/no-go: consolidacao sem incoerencia de correlator",
                "  - observacoes: principal ponte documental para `90%+`",
                "- `P0-01 / Auth OIDC`",
                "  - owner primario: `<preencher>`",
                "  - status: `blocked`",
                "  - ultima atualizacao: `pending`",
                "  - dependencia critica: provider OIDC serio homologado e MFA institucional",
                "  - comando: `make run-oidc-readiness-bundle-local`",
                "  - evidencia minima: bundle OIDC com `readiness_status=ready_for_validation`",
                "  - criterio de go/no-go: nao bloquear a janela combinada, mas impedir promocao institucional completa",
                "  - observacoes: risco residual permanece vermelho ate homologacao externa",
                "- `Gate Agregado da Janela`",
                "  - owner primario: `<preencher>`",
                "  - status: `pending`",
                "  - ultima atualizacao: `pending`",
                "  - dependencia critica: `P0-02` e `P0-03` com insumos reais + owners online + gate agregado verde",
                "  - comando: `python3 scripts/prepare_staging_window.py --validate --preflight`",
                "  - evidencia minima: `status=ok` no gate agregado antes do disparo de execucao real",
                "  - criterio de go/no-go: somente seguir para workflow oficial com `go` ou `go_with_exception` formal",
                "  - observacoes: janela planejada para a semana corrente",
                "",
                "## Bloqueadores Ativos",
                "",
                "- ID: `WR-01`",
                "  - trilha: `P0-02 / Compliance AML-KYT`",
                "  - descricao: credencial real do provider AML/KYT ainda nao confirmada neste ciclo",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - tempo alvo: `2026-07-07`",
                "  - status: `open`",
                "- ID: `WR-02`",
                "  - trilha: `P0-03 / Feed UE`",
                "  - descricao: URL tokenizada real do feed UE ainda nao confirmada neste ciclo",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - tempo alvo: `2026-07-07`",
                "  - status: `open`",
                "- ID: `WR-03`",
                "  - trilha: `P0-01 / Auth OIDC`",
                "  - descricao: provider OIDC serio e homologacao institucional de MFA seguem pendentes",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - tempo alvo: `2026-07-08`",
                "  - status: `open`",
                "- ID: `WR-04`",
                "  - trilha: `Gate Agregado da Janela`",
                "  - descricao: owners online e checkpoint agregado ainda nao registrados",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - tempo alvo: `2026-07-09`",
                "  - status: `watching`",
                "",
                "## Evidencias Revisadas",
                "",
                "- `run sheet datada`: `docs/governance-weekly/cycles/2026-07-06/run-sheet.md`",
                "- `governanca semanal operacional`: `docs/governance-weekly/cycles/2026-07-06/weekly-operational.md`",
                "- `execucao por evidencia`: `docs/governance-weekly/cycles/2026-07-06/evidence-draft.md`",
                "- `artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json`: `pending`",
                "- `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json`: `pending`",
                "- `artifacts/staging/dossiers/stg-2026-07-06-a-dossier.json`: `pending`",
                "",
                "## Proximo Passo Autorizado",
                "",
                "- acao: preencher owners e bridges, confirmar credencial AML/KYT e URL UE tokenizada, depois rerodar o gate agregado",
                "- owner: `Release Manager Tecnico` com coordenacao de `Compliance/AML`, `Compliance/Backend`, `Platform/SRE` e `Security/Auth`",
                "- canal: `<preencher_canal_principal_war_room>`",
                "- criterio para seguir: gate agregado `ok` + `P0-02` e `P0-03` aptos a gerar artefatos revisaveis",
                "",
                "## Resultado Final do War Room",
                "",
                "- decisao final: `pending_no_go`",
                "- justificativa: tentativa preparada documentalmente, mas ainda sem insumos reais",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_live_tracking_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "# Tracking ao Vivo da Janela Seria — `stg-2026-07-06-a`",
                "",
                "## Contexto Operacional",
                "",
                "- data: `2026-07-06`",
                "- window_id: `stg-2026-07-06-a`",
                "- mode: `baseline`",
                "- environment_name: `staging-serious`",
                "- facilitador: `Release Manager Tecnico`",
                "- status global: `pending`",
                "- checkpoint atual: `aguardando evidencias materiais`",
                "- ultima atualizacao: `pre-run`",
                "- cadencia de atualizacao recomendada: `15 min`",
                "",
                "## Painel de Trilhas",
                "",
                "- `P0-02 / Compliance AML-KYT`",
                "  - status atual: `ready`",
                "  - responsavel online: `<preencher>`",
                "  - canal de contato: `<preencher>`",
                "  - ack do owner: `no`",
                "  - ultima atualizacao: `pre-run`",
                "  - ultimo checkpoint: checker preparado",
                "  - proximo checkpoint: validar credencial real",
                "  - hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "  - ETA desbloqueio: `2026-07-07`",
                "  - dependencia ativa: credencial AML/KYT real",
                "  - bridge de escalacao: `<preencher>`",
                "  - observacoes: primeiro item com maior potencial de mudar a baseline",
                "- `P0-03 / Feed UE`",
                "  - status atual: `ready`",
                "  - responsavel online: `<preencher>`",
                "  - canal de contato: `<preencher>`",
                "  - ack do owner: `no`",
                "  - ultima atualizacao: `pre-run`",
                "  - ultimo checkpoint: checker preparado",
                "  - proximo checkpoint: validar URL real",
                "  - hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "  - ETA desbloqueio: `2026-07-07`",
                "  - dependencia ativa: URL tokenizada real",
                "  - bridge de escalacao: `<preencher>`",
                "  - observacoes: precisa convergir com `P0-02`",
                "- `P0-04 / Bundle Regulatorio`",
                "  - status atual: `pending`",
                "  - responsavel online: `<preencher>`",
                "  - canal de contato: `<preencher>`",
                "  - ack do owner: `no`",
                "  - ultima atualizacao: `pre-run`",
                "  - ultimo checkpoint: sem execucao real ainda",
                "  - proximo checkpoint: executar bundle regulatorio",
                "  - hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "  - ETA desbloqueio: `2026-07-09`",
                "  - dependencia ativa: `P0-02` e `P0-03` em `ready_for_validation`",
                "  - bridge de escalacao: `<preencher>`",
                "  - observacoes: ponte obrigatoria para discutir `90%+`",
                "- `P0-01 / Auth OIDC`",
                "  - status atual: `blocked`",
                "  - responsavel online: `<preencher>`",
                "  - canal de contato: `<preencher>`",
                "  - ack do owner: `no`",
                "  - ultima atualizacao: `pre-run`",
                "  - ultimo checkpoint: bundle modelado",
                "  - proximo checkpoint: homologar provider serio",
                "  - hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "  - ETA desbloqueio: `2026-07-08`",
                "  - dependencia ativa: provider OIDC serio e MFA homologado",
                "  - bridge de escalacao: `<preencher>`",
                "  - observacoes: risco institucional ainda vermelho",
                "- `Gate Agregado da Janela`",
                "  - status atual: `pending`",
                "  - responsavel online: `<preencher>`",
                "  - canal de contato: `<preencher>`",
                "  - ack do owner: `yes`",
                "  - ultima atualizacao: `pre-run`",
                "  - ultimo checkpoint: tentativa datada criada",
                "  - proximo checkpoint: `prepare_staging_window.py --validate --preflight`",
                "  - hora do proximo checkpoint: `<preencher_HH:MMZ>`",
                "  - ETA desbloqueio: `2026-07-09`",
                "  - dependencia ativa: owners online e insumos reais disponiveis",
                "  - bridge de escalacao: `<preencher>`",
                "  - observacoes: nao disparar execucao final sem `go` formal",
                "",
                "## Bloqueadores em Curso",
                "",
                "- ID: `WR-01`",
                "  - trilha: `P0-02 / Compliance AML-KYT`",
                "  - status: `open`",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - ETA: `2026-07-07`",
                "  - observacao: sem credencial real, o ciclo continua apenas documental",
                "- ID: `WR-02`",
                "  - trilha: `P0-03 / Feed UE`",
                "  - status: `open`",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - ETA: `2026-07-07`",
                "  - observacao: sem URL tokenizada, o correlator do feed nao pode ser validado",
                "- ID: `WR-03`",
                "  - trilha: `P0-01 / Auth OIDC`",
                "  - status: `open`",
                "  - owner da escalacao: `<preencher>`",
                "  - canal da escalacao: `<preencher>`",
                "  - ETA: `2026-07-08`",
                "  - observacao: nao impede o dress rehearsal combinado, mas impede o fechamento institucional completo",
                "",
                "## Decisoes Operacionais",
                "",
                "- manter `status global=pending` ate confirmacao material de `P0-02` e `P0-03`",
                "- atualizar este tracking em cada checkpoint material do war room",
                "- nao mover o sign-off para `approved` ou `approved_with_exception` enquanto `P0-04` nao estiver ao menos em `ready_for_validation`",
                "",
                "## Hand-off para Sign-Off",
                "",
                "- artefato OIDC esperado para `P0-01`: `artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json`",
                "- artefato regulatorio esperado para `P0-02/P0-03`: `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json`",
                "- dossie executivo esperado: `artifacts/staging/dossiers/stg-2026-07-06-a-dossier.json`",
                "- decisao recomendada: `pending_no_go`",
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
            weekly_file = governance_dir / "cycles" / "2026-07-06" / "2026-07-06-weekly-governance.md"
            war_room_file = governance_dir / "cycles" / "2026-07-06" / "2026-07-06-staging-serious-window-war-room.md"
            live_tracking_file = governance_dir / "cycles" / "2026-07-06" / "2026-07-06-staging-serious-window-live-tracking.md"
            board_file = base / "docs" / "project-operational-execution-board.md"
            stdout = io.StringIO()
            payload_file.parent.mkdir(parents=True, exist_ok=True)
            weekly_file.parent.mkdir(parents=True, exist_ok=True)
            _write_payload(payload_file, overall_status="ok")
            _write_weekly_file(weekly_file)
            _write_war_room_file(war_room_file)
            _write_live_tracking_file(live_tracking_file)
            _write_operational_board_file(board_file)

            with patch.object(MODULE.OPERATIONAL_BOARD_MODULE, "DEFAULT_BOARD_FILE", board_file):
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
            decision_packet_file = Path(result["decision_packet_output_file"])
            updated_war_room_file = Path(result["war_room_output_file"])
            updated_live_tracking_file = Path(result["live_tracking_output_file"])
            weekly_content = weekly_file.read_text(encoding="utf-8")
            board_content = board_file.read_text(encoding="utf-8")
            signoff_content = signoff_file.read_text(encoding="utf-8")
            governance_signoff_content = governance_signoff_file.read_text(encoding="utf-8")
            decision_packet_content = decision_packet_file.read_text(encoding="utf-8")
            war_room_content = updated_war_room_file.read_text(encoding="utf-8")
            live_tracking_content = updated_live_tracking_file.read_text(encoding="utf-8")
            signoff_exists = signoff_file.exists()
            governance_signoff_exists = governance_signoff_file.exists()
            decision_packet_exists = decision_packet_file.exists()
            war_room_exists = updated_war_room_file.exists()
            live_tracking_exists = updated_live_tracking_file.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["run_stg_status"], "done")
        self.assertEqual(result["decision"], "pending_manual_approval")
        self.assertEqual(result["go_no_go_decision"], "pending_no_go")
        self.assertEqual(result["tracking_status"], "pending")
        self.assertEqual(result["regulatory_scope_label"], "P0-02")
        self.assertTrue(signoff_exists)
        self.assertTrue(governance_signoff_exists)
        self.assertTrue(decision_packet_exists)
        self.assertTrue(war_room_exists)
        self.assertTrue(live_tracking_exists)
        self.assertEqual(signoff_content, governance_signoff_content)
        self.assertIn("run url: `https://github.com/example/actions/runs/123`", signoff_content)
        self.assertIn("# Go/No-Go Decision Packet - `stg-2026-07-06-a`", decision_packet_content)
        self.assertIn("- `escopo_regulatorio_desta_tentativa`: `P0-02`", decision_packet_content)
        self.assertIn("- `decisao_atual`: `pending_no_go`", decision_packet_content)
        self.assertIn("| P0-02 AML/KYT | `ready_for_validation` |", decision_packet_content)
        self.assertIn("- status atual: `pending_no_go`", war_room_content)
        self.assertIn("  - status: `ready_for_validation`", war_room_content)
        self.assertIn("- status global: `pending`", live_tracking_content)
        self.assertIn(
            "- manter `status global=pending` ate confirmacao material do escopo `P0-02` e fechamento do proximo checkpoint executivo",
            live_tracking_content,
        )
        self.assertIn("  - ultimo checkpoint: bundle `oidc-readiness-bundle`", live_tracking_content)
        self.assertIn("- overall status: `ok`", weekly_content)
        self.assertIn("  - status atual: `done`", weekly_content)
        self.assertIn("| `P0-02` | `ready_for_validation` | Homologar `AML/KYT live` |", board_content)
        self.assertIn("| `P0-03` | `ready` | Ativar feed UE real |", board_content)
        self.assertIn(
            "| `P0-04` | `todo` | Gerar bundle regulatorio oficial | Platform/SRE | tentativa atual: `P0-02`; promocao oficial ainda exige `P0-02` + `P0-03` |",
            board_content,
        )
        self.assertIn(
            "| `P0-03` | `ready` | trilha fora do escopo da tentativa atual; manter `P0-03` pronta para a janela combinada oficial |",
            board_content,
        )


if __name__ == "__main__":
    unittest.main()
