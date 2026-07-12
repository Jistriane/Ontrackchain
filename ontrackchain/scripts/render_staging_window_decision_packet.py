#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
PROMOTABLE_STATUSES = {"ready_for_validation", "done"}


def load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"nao_foi_possivel_carregar_modulo: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SIGNOFF_MODULE = load_module("render_staging_window_signoff", "scripts/render_staging_window_signoff.py")
WEEKLY_MODULE = load_module(
    "render_staging_window_weekly_governance",
    "scripts/render_staging_window_weekly_governance.py",
)


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_output_file(payload_file: Path) -> Path:
    if payload_file.suffix == ".json":
        return payload_file.with_suffix(".decision-packet.md")
    return payload_file.parent / f"{payload_file.name}.decision-packet.md"


def default_governance_output_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = SIGNOFF_MODULE.extract_window_date(window_id)
    return (
        governance_weekly_dir
        / "cycles"
        / window_date
        / f"{window_date}-staging-serious-window-go-no-go-decision-packet.md"
    )


def format_inline_value(value: Any, *, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


def derive_p0_04_status(*, p0_02_status: str, p0_03_status: str) -> str:
    if p0_02_status in PROMOTABLE_STATUSES and p0_03_status in PROMOTABLE_STATUSES:
        return "ready_for_validation"
    if p0_02_status == "blocked" or p0_03_status == "blocked":
        return "blocked"
    return "pending"


def derive_current_decision(
    *,
    overall_status: str,
    validation_status: str,
    preflight_status: str,
    run_status: str,
    p0_02_status: str,
    p0_03_status: str,
    p0_04_status: str,
) -> str:
    technical_statuses = {overall_status, validation_status, preflight_status, run_status}
    if "failed" in technical_statuses:
        return "no_go"
    if (
        overall_status == "ok"
        and validation_status == "ok"
        and preflight_status == "ok"
        and run_status == "ok"
        and p0_02_status in PROMOTABLE_STATUSES
        and p0_03_status in PROMOTABLE_STATUSES
        and p0_04_status in PROMOTABLE_STATUSES
    ):
        return "approved"
    if (
        validation_status == "ok"
        and preflight_status == "ok"
        and p0_02_status in PROMOTABLE_STATUSES
        and p0_03_status in PROMOTABLE_STATUSES
    ):
        return "pending_go"
    return "pending_no_go"


def derive_primary_reason(
    *,
    decision: str,
    weekly_model: dict[str, str],
    p0_04_status: str,
) -> str:
    if decision == "approved":
        return "todos os gates tecnicos e regulatorios obrigatorios estao verdes e coerentes"
    if decision == "no_go":
        failed_parts = [
            name
            for name, status in (
                ("overall", weekly_model["overall_status"]),
                ("validation", weekly_model["validation_status"]),
                ("preflight", weekly_model["preflight_status"]),
                ("run", weekly_model["run_status"]),
            )
            if status == "failed"
        ]
        if failed_parts:
            return "falha tecnica registrada em " + ", ".join(failed_parts)
        return "houve falha impeditiva no gate agregado da janela"
    if weekly_model["p0_02_status"] not in PROMOTABLE_STATUSES:
        if weekly_model.get("p0_02_in_scope") != "true":
            return "tentativa atual nao cobriu P0-02; ainda falta prova material AML/KYT na janela combinada"
        return "aguardando prova material de P0-02 com correlator auditavel"
    if weekly_model["p0_03_status"] not in PROMOTABLE_STATUSES:
        if weekly_model.get("p0_03_in_scope") != "true":
            return "tentativa parcial valida apenas parte do escopo regulatorio; ainda falta P0-03 com source_url reconciliada"
        return "aguardando prova material de P0-03 com source_url reconciliada"
    if p0_04_status not in PROMOTABLE_STATUSES:
        return "aguardando consolidacao final do bundle regulatorio sem incoerencias"
    return "aguardando checkpoint executivo final para promover a janela"


def build_blockers(*, weekly_model: dict[str, str], p0_04_status: str) -> list[str]:
    blockers: list[str] = []
    if weekly_model["p0_02_status"] not in PROMOTABLE_STATUSES:
        blockers.append(f"P0-02: {weekly_model['p0_02_next_evidence']}")
    if weekly_model["p0_03_status"] not in PROMOTABLE_STATUSES:
        blockers.append(f"P0-03: {weekly_model['p0_03_next_evidence']}")
    if weekly_model["p0_01_is_blocked"] == "true":
        blockers.append(f"P0-01: {weekly_model['p0_01_blocked_reason']}")
    if p0_04_status not in PROMOTABLE_STATUSES:
        blockers.append("P0-04: bundle regulatorio ainda nao esta simultaneamente pronto para validacao")
    if (
        weekly_model["overall_status"] != "ok"
        or weekly_model["validation_status"] != "ok"
        or weekly_model["preflight_status"] != "ok"
        or weekly_model["run_status"] != "ok"
    ):
        blockers.append(
            "Gate agregado: overall/validation/preflight/run ainda nao convergiram em `ok` na mesma tentativa"
        )
    return blockers or ["none_declared"]


def build_missing_evidence(*, weekly_model: dict[str, str], p0_04_status: str) -> list[str]:
    missing = [
        f"P0-02: {weekly_model['p0_02_next_evidence']}",
        f"P0-03: {weekly_model['p0_03_next_evidence']}",
        "Gate agregado: sign-off preenchido, owners online confirmados e checkpoint tecnico agregado verde",
    ]
    if p0_04_status not in PROMOTABLE_STATUSES:
        missing.append("P0-04: bundle regulatorio coerente com validacao final do artifact em `ok`")
    if weekly_model["p0_01_is_blocked"] == "true":
        missing.append(f"P0-01: {weekly_model['p0_01_next_evidence']}")
    return missing


def derive_honest_output(status: str) -> str:
    if status in PROMOTABLE_STATUSES:
        return "ready_for_validation"
    if status == "blocked":
        return "blocked"
    if status == "pending_execucao":
        return "pending"
    return status


def build_model(
    *,
    payload: dict[str, Any],
    payload_file: Path,
    run_url: str,
    run_name: str | None,
    workflow_name: str,
) -> dict[str, Any]:
    signoff_model = SIGNOFF_MODULE.build_signoff_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
        run_name=run_name,
        workflow_name=workflow_name,
    )
    weekly_model = WEEKLY_MODULE.build_weekly_sync_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
    )
    p0_04_status = derive_p0_04_status(
        p0_02_status=weekly_model["p0_02_status"],
        p0_03_status=weekly_model["p0_03_status"],
    )
    decision = derive_current_decision(
        overall_status=weekly_model["overall_status"],
        validation_status=weekly_model["validation_status"],
        preflight_status=weekly_model["preflight_status"],
        run_status=weekly_model["run_status"],
        p0_02_status=weekly_model["p0_02_status"],
        p0_03_status=weekly_model["p0_03_status"],
        p0_04_status=p0_04_status,
    )
    blockers = build_blockers(weekly_model=weekly_model, p0_04_status=p0_04_status)
    missing_evidence = build_missing_evidence(weekly_model=weekly_model, p0_04_status=p0_04_status)
    return {
        "window_id": weekly_model["window_id"],
        "mode": weekly_model["mode"],
        "regulatory_scope_label": weekly_model.get("regulatory_scope_label", "none"),
        "run_url": weekly_model["run_url"],
        "workflow_name": signoff_model["workflow_name"],
        "run_name": signoff_model["run_name"],
        "decision": decision,
        "primary_reason": derive_primary_reason(
            decision=decision,
            weekly_model=weekly_model,
            p0_04_status=p0_04_status,
        ),
        "owner": "Release Manager Tecnico",
        "next_checkpoint": "revisar checkpoint agregado apos atualizacao material de owners e evidencias",
        "blockers": blockers,
        "missing_evidence": missing_evidence,
        "fronts": [
            {
                "label": "P0-02 AML/KYT",
                "status": weekly_model["p0_02_status"],
                "missing": weekly_model["p0_02_next_evidence"],
                "honest_output": derive_honest_output(weekly_model["p0_02_status"]),
            },
            {
                "label": "P0-03 Feed UE",
                "status": weekly_model["p0_03_status"],
                "missing": weekly_model["p0_03_next_evidence"],
                "honest_output": derive_honest_output(weekly_model["p0_03_status"]),
            },
            {
                "label": "P0-04 Bundle Regulatorio",
                "status": p0_04_status,
                "missing": "bundle regulatorio oficial coerente e artifact validado em `ok`",
                "honest_output": derive_honest_output(p0_04_status),
            },
            {
                "label": "P0-01 Auth/OIDC",
                "status": weekly_model["p0_01_status"],
                "missing": weekly_model["p0_01_next_evidence"],
                "honest_output": derive_honest_output(weekly_model["p0_01_status"]),
            },
            {
                "label": "RUN-STG-01",
                "status": weekly_model["run_stg_status"],
                "missing": weekly_model["next_evidence"],
                "honest_output": derive_honest_output(weekly_model["run_stg_status"]),
            },
        ],
        "overall_status": weekly_model["overall_status"],
        "validation_status": weekly_model["validation_status"],
        "preflight_status": weekly_model["preflight_status"],
        "run_status": weekly_model["run_status"],
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        f"# Go/No-Go Decision Packet - `{model['window_id']}`",
        "",
        "> Gerado automaticamente a partir do payload consolidado da janela seria. Usar como leitura executiva curta antes do war room final.",
        "",
        "## Objetivo",
        "",
        "Dar uma leitura executiva unica da tentativa, condensando decisao atual, bloqueadores, evidencias faltantes e criterio de promocao.",
        "",
        "## Decisao Atual",
        "",
        f"- `window_id`: `{format_inline_value(model['window_id'])}`",
        f"- `modo`: `{format_inline_value(model['mode'])}`",
        f"- `escopo_regulatorio_desta_tentativa`: `{format_inline_value(model['regulatory_scope_label'])}`",
        f"- `decisao_atual`: `{format_inline_value(model['decision'])}`",
        f"- `motivo_principal`: {format_inline_value(model['primary_reason'])}",
        f"- `owner_da_decisao`: `{format_inline_value(model['owner'])}`",
        f"- `proximo_checkpoint`: `{format_inline_value(model['next_checkpoint'])}`",
        "",
        "## Leitura Curta por Frente",
        "",
        "| Frente | Estado atual | O que falta | Saida honesta hoje |",
        "| --- | --- | --- | --- |",
    ]
    for front in model["fronts"]:
        lines.append(
            f"| {front['label']} | `{format_inline_value(front['status'])}` | {format_inline_value(front['missing'])} | `{format_inline_value(front['honest_output'])}` |"
        )
    lines.extend(
        [
            "",
            "## Bloqueadores Ativos",
            "",
        ]
    )
    for blocker in model["blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(
        [
            "",
            "## Evidencias Minimas Faltantes",
            "",
        ]
    )
    for item in model["missing_evidence"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Criterio Objetivo de Promocao",
            "",
            "Promover de `pending_no_go` para `pending_go` somente se todos forem verdadeiros:",
            "",
            "- `validation` e `preflight` em `ok`",
            "- `P0-02` em `ready_for_validation` ou `done`",
            "- `P0-03` em `ready_for_validation` ou `done`",
            "- gate agregado sem bloqueio humano imediato",
            "",
            "Promover para `approved` somente se todos forem verdadeiros:",
            "",
            "- `overall`, `validation`, `preflight` e `run` em `ok`",
            "- `P0-02`, `P0-03` e `P0-04` coerentes para validacao formal",
            "- war room, sign-off e artefatos consolidados sem drift semantico",
            "",
            "## No-Go Imediato",
            "",
            "- `validation`, `preflight` ou `run` falhar",
            "- correlator obrigatorio faltar em `P0-02` ou `P0-03`",
            "- `P0-04` bloquear por inconsistência entre as trilhas",
            "- owners criticos permanecerem indisponiveis no checkpoint agregado",
            "",
            "## Proximo Passo Executivo",
            "",
            "- acao: atualizar owners/canais, materializar as proximas evidencias e rerodar o gate agregado",
            f"- owner: `{format_inline_value(model['owner'])}`",
            f"- destino esperado apos o checkpoint: `{format_inline_value(model['decision'])}` ou `approved`",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um decision packet executivo da janela seria a partir do payload consolidado."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--output-file")
    parser.add_argument("--governance-output-file")
    parser.add_argument("--governance-weekly-dir")
    parser.add_argument("--run-url", default="pending")
    parser.add_argument("--run-name")
    parser.add_argument("--workflow-name", default="Staging Serious Window")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)
    output_file = Path(args.output_file) if args.output_file else default_output_file(payload_file)

    try:
        payload = load_json_file(payload_file)
        model = build_model(
            payload=payload,
            payload_file=payload_file,
            run_url=args.run_url,
            run_name=args.run_name,
            workflow_name=args.workflow_name,
        )
        governance_output_file: Path | None = None
        if args.governance_output_file:
            governance_output_file = Path(args.governance_output_file)
        elif args.governance_weekly_dir:
            governance_output_file = default_governance_output_file(
                model["window_id"],
                Path(args.governance_weekly_dir),
            )

        rendered_markdown = render_markdown(model)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(rendered_markdown, encoding="utf-8")
        if governance_output_file is not None:
            governance_output_file.parent.mkdir(parents=True, exist_ok=True)
            governance_output_file.write_text(rendered_markdown, encoding="utf-8")
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_decision_packet_render",
                    "status": "failed",
                    "payload_file": str(payload_file),
                    "errors": [str(exc)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_decision_packet_render",
                "status": "ok",
                "payload_file": str(payload_file),
                "output_file": str(output_file),
                "governance_output_file": str(governance_output_file) if governance_output_file else None,
                "window_id": model["window_id"],
                "decision": model["decision"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
