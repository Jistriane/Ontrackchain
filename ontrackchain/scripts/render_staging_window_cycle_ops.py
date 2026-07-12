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


WEEKLY_MODULE = load_module(
    "render_staging_window_weekly_governance",
    "scripts/render_staging_window_weekly_governance.py",
)
DECISION_PACKET_MODULE = load_module(
    "render_staging_window_decision_packet",
    "scripts/render_staging_window_decision_packet.py",
)
SIGNOFF_MODULE = load_module(
    "render_staging_window_signoff",
    "scripts/render_staging_window_signoff.py",
)


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_get_value(value: Any, *, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


def replace_line(lines: list[str], prefix: str, new_line: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = new_line
            return
    raise ValueError(f"linha_nao_encontrada: {prefix}")


def find_section_range(lines: list[str], section_prefix: str) -> tuple[int, int]:
    for index, line in enumerate(lines):
        if line.startswith(section_prefix):
            start = index + 1
            end = len(lines)
            for nested_index in range(start, len(lines)):
                if lines[nested_index].startswith("## "):
                    end = nested_index
                    break
            return start, end
    raise ValueError(f"secao_nao_encontrada: {section_prefix}")


def replace_after_anchor(
    lines: list[str],
    *,
    section_prefix: str,
    anchor_prefix: str,
    relative_prefix: str,
    new_line: str,
) -> None:
    section_start, section_end = find_section_range(lines, section_prefix)
    for index in range(section_start, section_end):
        if lines[index].startswith(anchor_prefix):
            for nested_index in range(index + 1, section_end):
                current = lines[nested_index]
                if current.startswith("- `") and nested_index > index + 1:
                    break
                if current.startswith(relative_prefix):
                    lines[nested_index] = new_line
                    return
            raise ValueError(f"linha_relativa_nao_encontrada: {anchor_prefix} -> {relative_prefix}")
    raise ValueError(f"ancora_nao_encontrada: {anchor_prefix}")


def derive_p0_04_status(*, p0_02_status: str, p0_03_status: str) -> str:
    if p0_02_status in PROMOTABLE_STATUSES and p0_03_status in PROMOTABLE_STATUSES:
        return "ready_for_validation"
    if p0_02_status == "blocked" or p0_03_status == "blocked":
        return "blocked"
    return "pending"


def derive_tracking_status(decision: str) -> str:
    if decision == "approved":
        return "done"
    if decision == "pending_go":
        return "in_progress"
    if decision == "no_go":
        return "blocked"
    return "pending"


def derive_blocker_status(status: str) -> str:
    if status in PROMOTABLE_STATUSES:
        return "closed"
    if status == "blocked":
        return "open"
    return "open"


def default_war_room_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = SIGNOFF_MODULE.extract_window_date(window_id)
    return (
        governance_weekly_dir
        / "cycles"
        / window_date
        / f"{window_date}-staging-serious-window-war-room.md"
    )


def default_live_tracking_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = SIGNOFF_MODULE.extract_window_date(window_id)
    return (
        governance_weekly_dir
        / "cycles"
        / window_date
        / f"{window_date}-staging-serious-window-live-tracking.md"
    )


def build_model(*, payload: dict[str, Any], payload_file: Path, run_url: str) -> dict[str, str]:
    weekly_model = WEEKLY_MODULE.build_weekly_sync_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
    )
    decision_model = DECISION_PACKET_MODULE.build_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
        run_name=None,
        workflow_name="Staging Serious Window",
    )
    p0_04_status = derive_p0_04_status(
        p0_02_status=weekly_model["p0_02_status"],
        p0_03_status=weekly_model["p0_03_status"],
    )
    generated_at = safe_get_value(payload.get("generated_at"), default="pre-run do ciclo ativo")
    tracking_status = derive_tracking_status(decision_model["decision"])
    risk_residual = (
        f"P0-01 continua bloqueado por {weekly_model['p0_01_blocked_dependency']}; a janela combinada nao deve mascarar esse risco"
        if weekly_model["p0_01_is_blocked"] == "true"
        else "monitorar a reconciliacao final do bundle regulatorio e o aceite executivo da tentativa"
    )
    regulatory_scope_label = weekly_model.get("regulatory_scope_label", "none")
    if weekly_model.get("regulatory_scope_is_combined") == "true":
        p0_04_next_evidence = "bundle regulatorio oficial coerente e artifact validado em `ok`"
        gate_follow_criteria = "gate agregado `ok` + `P0-02` e `P0-03` aptos a gerar artefatos revisaveis"
        regulatory_artifact_label = "P0-02/P0-03"
    else:
        p0_04_next_evidence = (
            f"janela atual cobre `{regulatory_scope_label}`; ainda falta tentativa combinada com `P0-02` e `P0-03` para promover o bundle oficial"
        )
        gate_follow_criteria = (
            f"gate agregado `ok` + escopo `{regulatory_scope_label}` coerente nesta tentativa + janela combinada planejada para fechar `P0-04`"
        )
        regulatory_artifact_label = regulatory_scope_label
    return {
        "window_id": weekly_model["window_id"],
        "mode": weekly_model["mode"],
        "environment_name": weekly_model["environment_name"],
        "generated_at": generated_at,
        "decision": decision_model["decision"],
        "primary_reason": decision_model["primary_reason"],
        "tracking_status": tracking_status,
        "risk_residual": risk_residual,
        "run_url": weekly_model["run_url"],
        "run_stg_status": weekly_model["run_stg_status"],
        "next_evidence": weekly_model["next_evidence"],
        "regulatory_scope_label": regulatory_scope_label,
        "p0_01_status": weekly_model["p0_01_status"],
        "p0_01_next_evidence": weekly_model["p0_01_next_evidence"],
        "p0_01_artifact_reviewed": weekly_model["p0_01_artifact_reviewed"],
        "p0_01_blocked_reason": weekly_model["p0_01_blocked_reason"],
        "p0_01_blocked_dependency": weekly_model["p0_01_blocked_dependency"],
        "p0_02_status": weekly_model["p0_02_status"],
        "p0_02_next_evidence": weekly_model["p0_02_next_evidence"],
        "p0_02_artifact_reviewed": weekly_model["p0_02_artifact_reviewed"],
        "p0_02_blocked_reason": weekly_model["p0_02_blocked_reason"],
        "p0_02_blocked_dependency": weekly_model["p0_02_blocked_dependency"],
        "p0_03_status": weekly_model["p0_03_status"],
        "p0_03_next_evidence": weekly_model["p0_03_next_evidence"],
        "p0_03_artifact_reviewed": weekly_model["p0_03_artifact_reviewed"],
        "p0_03_blocked_reason": weekly_model["p0_03_blocked_reason"],
        "p0_03_blocked_dependency": weekly_model["p0_03_blocked_dependency"],
        "p0_04_status": p0_04_status,
        "p0_04_next_evidence": p0_04_next_evidence,
        "p0_04_artifact_reviewed": safe_get_value(
            weekly_model["regulatory_bundle_path"],
            default="bundle regulatorio ainda pendente",
        ),
        "gate_status": tracking_status,
        "gate_last_checkpoint": f"workflow `Staging Serious Window` + {weekly_model['artifact_ref']}",
        "gate_next_checkpoint": weekly_model["next_evidence"],
        "gate_follow_criteria": gate_follow_criteria,
        "regulatory_artifact_label": regulatory_artifact_label,
        "oidc_bundle_path": weekly_model["oidc_bundle_path"],
        "regulatory_bundle_path": weekly_model["regulatory_bundle_path"],
        "dossier_path": weekly_model["dossier_path"],
    }


def update_war_room_markdown(content: str, model: dict[str, str]) -> str:
    lines = content.splitlines()
    replace_line(lines, "- window_id:", f"- window_id: `{model['window_id']}`")
    replace_line(lines, "- mode:", f"- mode: `{model['mode']}`")
    replace_line(lines, "- environment_name:", f"- environment_name: `{model['environment_name']}`")
    replace_line(lines, "- status atual:", f"- status atual: `{model['decision']}`")
    replace_line(lines, "- motivo principal:", f"- motivo principal: {model['primary_reason']}")
    replace_line(lines, "- risco residual:", f"- risco residual: `{model['risk_residual']}`")
    replace_line(lines, "- proximo checkpoint:", f"- proximo checkpoint: {model['next_evidence']}")

    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-02 / Compliance AML-KYT`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{model['p0_02_status']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-02 / Compliance AML-KYT`",
        relative_prefix="  - ultima atualizacao:",
        new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-02 / Compliance AML-KYT`",
        relative_prefix="  - evidencia minima:",
        new_line=f"  - evidencia minima: {model['p0_02_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-02 / Compliance AML-KYT`",
        relative_prefix="  - observacoes:",
        new_line=f"  - observacoes: {model['p0_02_artifact_reviewed']}",
    )

    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-03 / Feed UE`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{model['p0_03_status']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-03 / Feed UE`",
        relative_prefix="  - ultima atualizacao:",
        new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-03 / Feed UE`",
        relative_prefix="  - evidencia minima:",
        new_line=f"  - evidencia minima: {model['p0_03_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-03 / Feed UE`",
        relative_prefix="  - observacoes:",
        new_line=f"  - observacoes: {model['p0_03_artifact_reviewed']}",
    )

    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-04 / Bundle Regulatorio`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{model['p0_04_status']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-04 / Bundle Regulatorio`",
        relative_prefix="  - ultima atualizacao:",
        new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-04 / Bundle Regulatorio`",
        relative_prefix="  - evidencia minima:",
        new_line=f"  - evidencia minima: {model['p0_04_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-04 / Bundle Regulatorio`",
        relative_prefix="  - observacoes:",
        new_line=f"  - observacoes: {model['p0_04_artifact_reviewed']}",
    )

    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-01 / Auth OIDC`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{model['p0_01_status']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-01 / Auth OIDC`",
        relative_prefix="  - ultima atualizacao:",
        new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-01 / Auth OIDC`",
        relative_prefix="  - evidencia minima:",
        new_line=f"  - evidencia minima: {model['p0_01_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `P0-01 / Auth OIDC`",
        relative_prefix="  - observacoes:",
        new_line=f"  - observacoes: {model['p0_01_artifact_reviewed']}",
    )

    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `Gate Agregado da Janela`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{model['gate_status']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `Gate Agregado da Janela`",
        relative_prefix="  - ultima atualizacao:",
        new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `Gate Agregado da Janela`",
        relative_prefix="  - evidencia minima:",
        new_line=f"  - evidencia minima: {model['gate_next_checkpoint']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Trilhas do War Room",
        anchor_prefix="- `Gate Agregado da Janela`",
        relative_prefix="  - observacoes:",
        new_line=f"  - observacoes: {model['gate_last_checkpoint']}",
    )

    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-01`",
        relative_prefix="  - descricao:",
        new_line=f"  - descricao: {model['p0_02_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-01`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_02_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-02`",
        relative_prefix="  - descricao:",
        new_line=f"  - descricao: {model['p0_03_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-02`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_03_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-03`",
        relative_prefix="  - descricao:",
        new_line=f"  - descricao: {model['p0_01_blocked_reason']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-03`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_01_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-04`",
        relative_prefix="  - descricao:",
        new_line=f"  - descricao: {model['gate_next_checkpoint']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores Ativos",
        anchor_prefix="- ID: `WR-04`",
        relative_prefix="  - status:",
        new_line="  - status: `closed`" if model["gate_status"] in {"in_progress", "done"} else "  - status: `watching`",
    )

    replace_line(
        lines,
        "- `artifacts/staging/checks/",
        f"- `{model['oidc_bundle_path']}`: `{model['p0_01_status']}`",
    )
    replace_line(
        lines,
        "- `artifacts/staging/checks/stg-",
        f"- `{model['regulatory_bundle_path']}`: `{model['p0_04_status']}`",
    )
    replace_line(
        lines,
        "- `artifacts/staging/dossiers/stg-",
        f"- `{model['dossier_path']}`: `{model['run_stg_status']}`",
    )

    replace_line(
        lines,
        "- acao:",
        f"- acao: {model['next_evidence']}",
    )
    replace_line(
        lines,
        "- criterio para seguir:",
        f"- criterio para seguir: {model['gate_follow_criteria']}",
    )
    replace_line(lines, "- decisao final:", f"- decisao final: `{model['decision']}`")
    replace_line(lines, "- justificativa:", f"- justificativa: {model['primary_reason']}")
    return "\n".join(lines) + "\n"


def update_live_tracking_markdown(content: str, model: dict[str, str]) -> str:
    lines = content.splitlines()
    replace_line(lines, "- window_id:", f"- window_id: `{model['window_id']}`")
    replace_line(lines, "- mode:", f"- mode: `{model['mode']}`")
    replace_line(lines, "- environment_name:", f"- environment_name: `{model['environment_name']}`")
    replace_line(lines, "- status global:", f"- status global: `{model['tracking_status']}`")
    replace_line(lines, "- checkpoint atual:", f"- checkpoint atual: `{model['primary_reason']}`")
    replace_line(lines, "- ultima atualizacao:", f"- ultima atualizacao: `{model['generated_at']}`")

    for anchor_prefix, status, artifact_reviewed, next_evidence in (
        ("- `P0-02 / Compliance AML-KYT`", model["p0_02_status"], model["p0_02_artifact_reviewed"], model["p0_02_next_evidence"]),
        ("- `P0-03 / Feed UE`", model["p0_03_status"], model["p0_03_artifact_reviewed"], model["p0_03_next_evidence"]),
        ("- `P0-04 / Bundle Regulatorio`", model["p0_04_status"], model["p0_04_artifact_reviewed"], model["p0_04_next_evidence"]),
        ("- `P0-01 / Auth OIDC`", model["p0_01_status"], model["p0_01_artifact_reviewed"], model["p0_01_next_evidence"]),
        ("- `Gate Agregado da Janela`", model["gate_status"], model["gate_last_checkpoint"], model["gate_next_checkpoint"]),
    ):
        replace_after_anchor(
            lines,
            section_prefix="## Painel de Trilhas",
            anchor_prefix=anchor_prefix,
            relative_prefix="  - status atual:",
            new_line=f"  - status atual: `{status}`",
        )
        replace_after_anchor(
            lines,
            section_prefix="## Painel de Trilhas",
            anchor_prefix=anchor_prefix,
            relative_prefix="  - ultima atualizacao:",
            new_line=f"  - ultima atualizacao: `{model['generated_at']}`",
        )
        replace_after_anchor(
            lines,
            section_prefix="## Painel de Trilhas",
            anchor_prefix=anchor_prefix,
            relative_prefix="  - ultimo checkpoint:",
            new_line=f"  - ultimo checkpoint: {artifact_reviewed}",
        )
        replace_after_anchor(
            lines,
            section_prefix="## Painel de Trilhas",
            anchor_prefix=anchor_prefix,
            relative_prefix="  - proximo checkpoint:",
            new_line=f"  - proximo checkpoint: {next_evidence}",
        )

    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-01`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_02_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-01`",
        relative_prefix="  - observacao:",
        new_line=f"  - observacao: {model['p0_02_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-02`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_03_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-02`",
        relative_prefix="  - observacao:",
        new_line=f"  - observacao: {model['p0_03_next_evidence']}",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-03`",
        relative_prefix="  - status:",
        new_line=f"  - status: `{derive_blocker_status(model['p0_01_status'])}`",
    )
    replace_after_anchor(
        lines,
        section_prefix="## Bloqueadores em Curso",
        anchor_prefix="- ID: `WR-03`",
        relative_prefix="  - observacao:",
        new_line=f"  - observacao: {model['p0_01_blocked_reason']}",
    )

    replace_line(
        lines,
        "- manter `status global=",
        f"- manter `status global={model['tracking_status']}` ate confirmacao material do escopo `{model['regulatory_scope_label']}` e fechamento do proximo checkpoint executivo",
    )
    replace_line(lines, "- artefato OIDC esperado para `P0-01`:", f"- artefato OIDC esperado para `P0-01`: `{model['oidc_bundle_path']}`")
    replace_line(
        lines,
        "- artefato regulatorio esperado para `P0-02/P0-03`:",
        f"- artefato regulatorio esperado para `{model['regulatory_artifact_label']}`: `{model['regulatory_bundle_path']}`",
    )
    replace_line(lines, "- dossie executivo esperado:", f"- dossie executivo esperado: `{model['dossier_path']}`")
    replace_line(lines, "- decisao recomendada:", f"- decisao recomendada: `{model['decision']}`")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sincroniza war room e live tracking do ciclo datado a partir do payload consolidado da janela seria."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--governance-weekly-dir", required=True)
    parser.add_argument("--run-url", default="pending")
    parser.add_argument("--war-room-file")
    parser.add_argument("--live-tracking-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)
    governance_weekly_dir = Path(args.governance_weekly_dir)
    try:
        payload = load_json_file(payload_file)
        window_id = safe_get_value(payload.get("window_id"), default="unknown-window")
        war_room_file = Path(args.war_room_file) if args.war_room_file else default_war_room_file(window_id, governance_weekly_dir)
        live_tracking_file = (
            Path(args.live_tracking_file)
            if args.live_tracking_file
            else default_live_tracking_file(window_id, governance_weekly_dir)
        )
        model = build_model(payload=payload, payload_file=payload_file, run_url=args.run_url)
        war_room_content = war_room_file.read_text(encoding="utf-8")
        live_tracking_content = live_tracking_file.read_text(encoding="utf-8")
        war_room_file.write_text(update_war_room_markdown(war_room_content, model), encoding="utf-8")
        live_tracking_file.write_text(
            update_live_tracking_markdown(live_tracking_content, model),
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_cycle_ops_render",
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
                "kind": "staging_window_cycle_ops_render",
                "status": "ok",
                "payload_file": str(payload_file),
                "war_room_file": str(war_room_file),
                "live_tracking_file": str(live_tracking_file),
                "window_id": model["window_id"],
                "decision": model["decision"],
                "tracking_status": model["tracking_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
