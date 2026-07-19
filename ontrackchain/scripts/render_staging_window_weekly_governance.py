#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_window_date(window_id: str) -> str:
    match = re.fullmatch(r"stg-(\d{4}-\d{2}-\d{2})-[a-z0-9]+", window_id)
    if not match:
        raise ValueError(f"window_id_invalido_para_governanca: {window_id}")
    return match.group(1)


def default_weekly_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = extract_window_date(window_id)
    return governance_weekly_dir / "cycles" / window_date / f"{window_date}-weekly-governance.md"


def safe_get_step(step_payload: dict[str, Any], step_name: str) -> dict[str, Any]:
    return (step_payload.get("steps") or {}).get(step_name) or {}


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


def replace_after_anchor(lines: list[str], anchor_prefix: str, relative_prefix: str, new_line: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith(anchor_prefix):
            for nested_index in range(index + 1, len(lines)):
                current = lines[nested_index]
                if current.startswith("- ID: `") and nested_index > index + 1:
                    break
                if current.startswith(relative_prefix):
                    lines[nested_index] = new_line
                    return
            raise ValueError(f"linha_relativa_nao_encontrada: {anchor_prefix} -> {relative_prefix}")
    raise ValueError(f"ancora_nao_encontrada: {anchor_prefix}")


def find_section_range(lines: list[str], section_prefix: str) -> tuple[int, int]:
    for index, line in enumerate(lines):
        if line.startswith(section_prefix):
            start_index = index + 1
            end_index = len(lines)
            for nested_index in range(start_index, len(lines)):
                if lines[nested_index].startswith("## "):
                    end_index = nested_index
                    break
            return start_index, end_index
    raise ValueError(f"secao_nao_encontrada: {section_prefix}")


def replace_after_anchor_in_section(
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
                if current.startswith("- ID: `") and nested_index > index + 1:
                    break
                if current.startswith(relative_prefix):
                    lines[nested_index] = new_line
                    return
            raise ValueError(f"linha_relativa_nao_encontrada: {anchor_prefix} -> {relative_prefix}")
    raise ValueError(f"ancora_nao_encontrada: {anchor_prefix}")


def find_block_range(
    lines: list[str],
    *,
    section_prefix: str,
    anchor_prefix: str,
) -> tuple[int, int]:
    section_start, section_end = find_section_range(lines, section_prefix)
    for index in range(section_start, section_end):
        if lines[index].startswith(anchor_prefix):
            end_index = section_end
            for nested_index in range(index + 1, section_end):
                current = lines[nested_index]
                if current.startswith("- ID: `"):
                    end_index = nested_index
                    break
            return index, end_index
    raise ValueError(f"ancora_nao_encontrada: {anchor_prefix}")


def replace_line_with_fallbacks(lines: list[str], prefixes: list[str], new_line: str) -> bool:
    for prefix in prefixes:
        try:
            replace_line(lines, prefix, new_line)
            return True
        except ValueError:
            continue
    return False


def derive_p0_01_blocked_dependency(blockers: list[str]) -> str:
    if any("provider mfa/oidc" in blocker.lower() or "homologado" in blocker.lower() for blocker in blockers):
        return "provider de identidade/MFA e homologacao institucional do fluxo serio"
    if any("preflight" in blocker.lower() or "smoke" in blocker.lower() for blocker in blockers):
        return "preflight e smoke OIDC ainda nao estabilizados no ambiente serio"
    return "validacao tecnica e institucional do fluxo serio de OIDC/MFA"


def derive_regulatory_item_model(
    *,
    item_id: str,
    enabled: bool,
    step_status: str,
    bundle_path: str,
    bundle_status: str,
    bundle_errors: list[str],
    readiness_status: str = "",
    readiness_next_action: str = "",
    readiness_blockers: list[str] | None = None,
) -> dict[str, str]:
    normalized_step_status = safe_get_value(step_status, default="skipped")
    normalized_bundle_path = safe_get_value(bundle_path)
    filtered_errors = [str(error) for error in bundle_errors if str(error).strip()]
    filtered_readiness_blockers = [
        str(error) for error in (readiness_blockers or []) if str(error).strip()
    ]

    if item_id == "P0-02":
        default_ready_evidence = "credencial AML/KYT real + checker verde com JSON persistido e bundle regulatorio anexado"
        blocked_dependency = "provider AML/KYT e credencial real homologada no ambiente serio"
        artifact_reviewed = (
            f"bundle regulatorio `{normalized_bundle_path}` e step `compliance_provider_runtime` com status `{normalized_step_status}`"
        )
    else:
        default_ready_evidence = "URL tokenizada valida + JSONs da janela UE + bundle regulatorio anexado"
        blocked_dependency = "feed UE tokenizado, source_url valida e sincronizacao oficial da janela"
        artifact_reviewed = (
            f"bundle regulatorio `{normalized_bundle_path}` e step `eu_sanctions_window` com status `{normalized_step_status}`"
        )

    if not enabled:
        return {
            "status": safe_get_value(readiness_status, default="ready"),
            "next_evidence": safe_get_value(
                readiness_next_action,
                default=f"fora do escopo da tentativa atual; manter {item_id} pronto para a janela combinada oficial",
            ),
            "artifact_reviewed": (
                f"bundle regulatorio `{normalized_bundle_path}` com `{item_id}` fora do escopo desta tentativa"
            ),
            "is_blocked": "false",
            "blocked_reason": "none",
            "blocked_dependency": blocked_dependency,
        }

    effective_status = safe_get_value(
        readiness_status,
        default="ready_for_validation" if normalized_step_status == "ok" else "blocked",
    )

    if effective_status == "ready_for_validation":
        return {
            "status": "ready_for_validation",
            "next_evidence": safe_get_value(
                readiness_next_action,
                default="revisao formal da governanca semanal com bundle regulatorio e artefatos anexados",
            ),
            "artifact_reviewed": artifact_reviewed,
            "is_blocked": "false",
            "blocked_reason": "none",
            "blocked_dependency": blocked_dependency,
        }

    if effective_status == "ready":
        return {
            "status": "ready",
            "next_evidence": safe_get_value(readiness_next_action, default=default_ready_evidence),
            "artifact_reviewed": artifact_reviewed,
            "is_blocked": "false",
            "blocked_reason": "none",
            "blocked_dependency": blocked_dependency,
        }

    blocked_reason = (
        "; ".join(filtered_readiness_blockers or filtered_errors)
        if filtered_errors
        else (
            "; ".join(filtered_readiness_blockers)
            if filtered_readiness_blockers
            else f"bundle regulatorio em `{bundle_status}` com step `{normalized_step_status}`"
        )
    )
    return {
        "status": "blocked",
        "next_evidence": safe_get_value(readiness_next_action, default=default_ready_evidence),
        "artifact_reviewed": artifact_reviewed,
        "is_blocked": "true",
        "blocked_reason": blocked_reason,
        "blocked_dependency": blocked_dependency,
    }


def derive_blocking_classification(
    *,
    overall_status: str,
    validation_status: str,
    preflight_status: str,
    run_status: str,
    p0_01_status: str,
    p0_01_blocked_reason: str,
    p0_02_status: str,
    p0_02_blocked_reason: str,
    p0_03_status: str,
    p0_03_blocked_reason: str,
    regulatory_scope_label: str,
) -> dict[str, str]:
    regulatory_reasons = [
        reason
        for status, reason in (
            (p0_02_status, p0_02_blocked_reason),
            (p0_03_status, p0_03_blocked_reason),
        )
        if status == "blocked" and str(reason).strip() and str(reason).strip() != "none"
    ]
    technical_failures = [
        name
        for name, status in (
            ("validation", validation_status),
            ("preflight", preflight_status),
            ("run", run_status),
        )
        if status == "failed"
    ]

    if regulatory_scope_label != "none" and regulatory_reasons:
        return {
            "blocking_classification": "regulatory_blocked",
            "blocking_summary": "; ".join(regulatory_reasons),
        }
    if p0_01_status == "blocked":
        return {
            "blocking_classification": "identity_blocked",
            "blocking_summary": p0_01_blocked_reason,
        }
    if technical_failures or overall_status == "failed":
        failed_label = ", ".join(technical_failures) if technical_failures else "overall"
        return {
            "blocking_classification": "technical_gate_blocked",
            "blocking_summary": f"falha tecnica registrada em {failed_label}",
        }
    if overall_status == "ok":
        return {
            "blocking_classification": "ready_for_manual_review",
            "blocking_summary": "gates tecnicos concluidos; pendente apenas revisao/aprovacao humana",
        }
    return {
        "blocking_classification": "pending_execution",
        "blocking_summary": "janela ainda nao convergiu na mesma tentativa",
    }


def upsert_blocked_item(
    lines: list[str],
    *,
    item_id: str,
    is_blocked: bool,
    blocked_reason: str,
    blocked_dependency: str,
    owner: str,
) -> None:
    try:
        blocked_start, blocked_end = find_block_range(
            lines,
            section_prefix="## Itens Blocked",
            anchor_prefix=f"- ID: `{item_id}`",
        )
        if is_blocked:
            lines[blocked_start:blocked_end] = [
                f"- ID: `{item_id}`",
                f"  - motivo: {blocked_reason}",
                f"  - dependência externa: {blocked_dependency}",
                f"  - owner da escalação: `{owner}`",
                "",
            ]
        else:
            del lines[blocked_start:blocked_end]
            while blocked_start < len(lines) and lines[blocked_start] == "":
                del lines[blocked_start]
    except ValueError:
        if is_blocked:
            blocked_section_start, _ = find_section_range(lines, "## Itens Blocked")
            lines[blocked_section_start:blocked_section_start] = [
                f"- ID: `{item_id}`",
                f"  - motivo: {blocked_reason}",
                f"  - dependência externa: {blocked_dependency}",
                f"  - owner da escalação: `{owner}`",
                "",
            ]


def build_weekly_sync_model(
    *,
    payload: dict[str, Any],
    payload_file: Path,
    run_url: str,
) -> dict[str, str]:
    window_id = safe_get_value(payload.get("window_id"), default="unknown-window")
    mode = safe_get_value(payload.get("mode"))
    environment_name = safe_get_value(payload.get("environment_name"), default="staging-serious")
    overall_status = safe_get_value(payload.get("status"))
    validation_status = safe_get_value((payload.get("validation") or {}).get("status"))
    preflight_status = safe_get_value((payload.get("preflight") or {}).get("status"))
    run_status = safe_get_value((payload.get("run") or {}).get("status"))

    run_payload = (payload.get("run") or {}).get("payload") or {}
    release_dossier = safe_get_step(run_payload, "release_dossier")
    homologation = safe_get_step(run_payload, "homologation")
    oidc_bundle = safe_get_step(run_payload, "oidc_readiness_bundle")
    regulatory_bundle = safe_get_step(run_payload, "regulatory_readiness_bundle")
    regulatory_scope_items: list[str] = []
    if regulatory_bundle.get("compliance_runtime_enabled") is True:
        regulatory_scope_items.append("P0-02")
    if regulatory_bundle.get("eu_window_enabled") is True:
        regulatory_scope_items.append("P0-03")
    regulatory_scope_label = "/".join(regulatory_scope_items) if regulatory_scope_items else "none"
    artifact_name = f"serious-staging-window-{window_id}"
    artifact_ref = f"artifact `{artifact_name}`"
    oidc_readiness_status = safe_get_value(oidc_bundle.get("readiness_status"))
    oidc_readiness_blockers = oidc_bundle.get("readiness_blockers") or []
    oidc_next_action = safe_get_value(oidc_bundle.get("next_action"))
    regulatory_bundle_status = safe_get_value(regulatory_bundle.get("status"))
    regulatory_bundle_errors = [str(error) for error in (regulatory_bundle.get("errors") or [])]
    regulatory_readiness = regulatory_bundle.get("readiness") or {}
    oidc_bundle_summary = (
        f"status={oidc_readiness_status}; "
        f"blockers={'; '.join(str(item) for item in oidc_readiness_blockers) if oidc_readiness_blockers else 'none_declared'}; "
        f"next_action={oidc_next_action}"
    )
    regulatory_bundle_summary = (
        f"status={regulatory_bundle_status}; "
        f"scope={regulatory_scope_label}; "
        f"output_file={safe_get_value(regulatory_bundle.get('output_file'))}"
    )
    p0_01_status = oidc_readiness_status
    p0_01_next_evidence = oidc_next_action
    p0_01_artifact_reviewed = f"bundle `oidc-readiness-bundle` e gates do trilho serio `OIDC/MFA` com status `{oidc_readiness_status}`"
    p0_01_blocked_reason = (
        "; ".join(str(item) for item in oidc_readiness_blockers)
        if oidc_readiness_blockers
        else "bloqueio OIDC sem blockers declarados no bundle"
    )
    p0_01_blocked_dependency = derive_p0_01_blocked_dependency(
        [str(item) for item in oidc_readiness_blockers]
    )
    p0_02 = derive_regulatory_item_model(
        item_id="P0-02",
        enabled=regulatory_bundle.get("compliance_runtime_enabled") is True,
        step_status=safe_get_value(regulatory_bundle.get("compliance_provider_runtime_status"), default="skipped"),
        bundle_path=safe_get_value(regulatory_bundle.get("output_file")),
        bundle_status=regulatory_bundle_status,
        bundle_errors=regulatory_bundle_errors,
        readiness_status=safe_get_value(
            ((regulatory_readiness.get("compliance_runtime") or {}).get("readiness_status")),
            default="",
        ),
        readiness_next_action=safe_get_value(
            ((regulatory_readiness.get("compliance_runtime") or {}).get("next_action")),
            default="",
        ),
        readiness_blockers=((regulatory_readiness.get("compliance_runtime") or {}).get("blockers") or []),
    )
    p0_03 = derive_regulatory_item_model(
        item_id="P0-03",
        enabled=regulatory_bundle.get("eu_window_enabled") is True,
        step_status=safe_get_value(regulatory_bundle.get("eu_sanctions_window_status"), default="skipped"),
        bundle_path=safe_get_value(regulatory_bundle.get("output_file")),
        bundle_status=regulatory_bundle_status,
        bundle_errors=regulatory_bundle_errors,
        readiness_status=safe_get_value(
            ((regulatory_readiness.get("eu_window") or {}).get("readiness_status")),
            default="",
        ),
        readiness_next_action=safe_get_value(
            ((regulatory_readiness.get("eu_window") or {}).get("next_action")),
            default="",
        ),
        readiness_blockers=((regulatory_readiness.get("eu_window") or {}).get("blockers") or []),
    )

    if overall_status == "ok" and validation_status == "ok" and preflight_status == "ok" and run_status == "ok":
        run_stg_status = "done"
        next_evidence = "sign-off humano com aprovadores preenchidos e decisao final `approved`"
    elif overall_status == "failed":
        run_stg_status = "blocked"
        next_evidence = "registro do ponto de falha e owner da escalacao"
    else:
        run_stg_status = "pending_execucao"
        next_evidence = "sign-off preenchido com links, status e aprovadores humanos"

    blocking_state = derive_blocking_classification(
        overall_status=overall_status,
        validation_status=validation_status,
        preflight_status=preflight_status,
        run_status=run_status,
        p0_01_status=p0_01_status,
        p0_01_blocked_reason=p0_01_blocked_reason,
        p0_02_status=p0_02["status"],
        p0_02_blocked_reason=p0_02["blocked_reason"],
        p0_03_status=p0_03["status"],
        p0_03_blocked_reason=p0_03["blocked_reason"],
        regulatory_scope_label=regulatory_scope_label,
    )

    return {
        "window_id": window_id,
        "mode": mode,
        "environment_name": environment_name,
        "run_url": run_url or "pending",
        "artifact_name": artifact_name,
        "artifact_ref": artifact_ref,
        "overall_status": overall_status,
        "validation_status": validation_status,
        "preflight_status": preflight_status,
        "run_status": run_status,
        "window_packet_path": safe_get_value((payload.get("artifacts") or {}).get("window_packet_file")),
        "dossier_path": safe_get_value(release_dossier.get("artifact_file")),
        "homologation_path": safe_get_value(homologation.get("artifact_file")),
        "oidc_bundle_path": safe_get_value(oidc_bundle.get("output_file")),
        "oidc_readiness_status": oidc_readiness_status,
        "oidc_bundle_summary": oidc_bundle_summary,
        "p0_01_status": p0_01_status,
        "p0_01_next_evidence": p0_01_next_evidence,
        "p0_01_artifact_reviewed": p0_01_artifact_reviewed,
        "p0_01_is_blocked": "true" if oidc_readiness_status == "blocked" else "false",
        "p0_01_blocked_reason": p0_01_blocked_reason,
        "p0_01_blocked_dependency": p0_01_blocked_dependency,
        "p0_02_status": p0_02["status"],
        "p0_02_next_evidence": p0_02["next_evidence"],
        "p0_02_artifact_reviewed": p0_02["artifact_reviewed"],
        "p0_02_is_blocked": p0_02["is_blocked"],
        "p0_02_blocked_reason": p0_02["blocked_reason"],
        "p0_02_blocked_dependency": p0_02["blocked_dependency"],
        "p0_03_status": p0_03["status"],
        "p0_03_next_evidence": p0_03["next_evidence"],
        "p0_03_artifact_reviewed": p0_03["artifact_reviewed"],
        "p0_03_is_blocked": p0_03["is_blocked"],
        "p0_03_blocked_reason": p0_03["blocked_reason"],
        "p0_03_blocked_dependency": p0_03["blocked_dependency"],
        "regulatory_bundle_path": safe_get_value(regulatory_bundle.get("output_file")),
        "regulatory_bundle_summary": regulatory_bundle_summary,
        "regulatory_scope_label": regulatory_scope_label,
        "regulatory_scope_is_combined": "true" if regulatory_scope_label == "P0-02/P0-03" else "false",
        "p0_02_in_scope": "true" if "P0-02" in regulatory_scope_items else "false",
        "p0_03_in_scope": "true" if "P0-03" in regulatory_scope_items else "false",
        "blocking_classification": blocking_state["blocking_classification"],
        "blocking_summary": blocking_state["blocking_summary"],
        "run_stg_status": run_stg_status,
        "next_evidence": next_evidence,
        "payload_json_path": str(payload_file),
    }


def update_weekly_governance_markdown(content: str, model: dict[str, str]) -> str:
    lines = content.splitlines()
    replace_line(lines, "- `window_id`:", f"- `window_id`: `{model['window_id']}`")
    replace_line(lines, "- `mode`:", f"- `mode`: `{model['mode']}`")
    replace_line(lines, "- `environment_name`:", f"- `environment_name`: `{model['environment_name']}`")
    replace_line(lines, "- run do GitHub Actions:", f"- run do GitHub Actions: `{model['run_url']}`")
    replace_line(lines, "- artifact `serious-staging-window-", f"- artifact `{model['artifact_name']}`: `{model['artifact_ref']}`")
    replace_line(lines, "- overall status:", f"- overall status: `{model['overall_status']}`")
    replace_line(lines, "- validation status:", f"- validation status: `{model['validation_status']}`")
    replace_line(lines, "- preflight status:", f"- preflight status: `{model['preflight_status']}`")
    replace_line(lines, "- run status:", f"- run status: `{model['run_status']}`")
    replace_line(lines, "- window packet:", f"- window packet: `{model['window_packet_path']}`")
    replace_line(lines, "- dossier:", f"- dossier: `{model['dossier_path']}`")
    replace_line(lines, "- homologation:", f"- homologation: `{model['homologation_path']}`")
    if not replace_line_with_fallbacks(
        lines,
        ["- oidc bundle summary:", "- oidc-readiness-bundle:"],
        f"- oidc bundle summary: `{model['oidc_bundle_summary']}`",
    ):
        for index, line in enumerate(lines):
            if line.startswith("- homologation:"):
                lines.insert(
                    index + 1,
                    f"- oidc bundle summary: `{model['oidc_bundle_summary']}`",
                )
                break
    if not replace_line_with_fallbacks(
        lines,
        ["- regulatory bundle summary:", "- regulatory-readiness-bundle:"],
        f"- regulatory bundle summary: `{model['regulatory_bundle_summary']}`",
    ):
        for index, line in enumerate(lines):
            if line.startswith("- oidc bundle summary:"):
                lines.insert(
                    index + 1,
                    f"- regulatory bundle summary: `{model['regulatory_bundle_summary']}`",
                )
                break

    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-02`",
        relative_prefix="  - status atual:",
        new_line=f"  - status atual: `{model['p0_02_status']}`",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-02`",
        relative_prefix="  - artefato revisado:",
        new_line=f"  - artefato revisado: {model['p0_02_artifact_reviewed']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-02`",
        relative_prefix="  - próxima evidência esperada:",
        new_line=f"  - próxima evidência esperada: {model['p0_02_next_evidence']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-03`",
        relative_prefix="  - status atual:",
        new_line=f"  - status atual: `{model['p0_03_status']}`",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-03`",
        relative_prefix="  - artefato revisado:",
        new_line=f"  - artefato revisado: {model['p0_03_artifact_reviewed']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-03`",
        relative_prefix="  - próxima evidência esperada:",
        new_line=f"  - próxima evidência esperada: {model['p0_03_next_evidence']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-01`",
        relative_prefix="  - status atual:",
        new_line=f"  - status atual: `{model['p0_01_status']}`",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-01`",
        relative_prefix="  - artefato revisado:",
        new_line=f"  - artefato revisado: {model['p0_01_artifact_reviewed']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `P0-01`",
        relative_prefix="  - próxima evidência esperada:",
        new_line=f"  - próxima evidência esperada: {model['p0_01_next_evidence']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `RUN-STG-01`",
        relative_prefix="  - status atual:",
        new_line=f"  - status atual: `{model['run_stg_status']}`",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `RUN-STG-01`",
        relative_prefix="  - artefato revisado:",
        new_line=f"  - artefato revisado: workflow `Staging Serious Window` + {model['artifact_ref']}",
    )
    replace_after_anchor_in_section(
        lines,
        section_prefix="## Itens Atualizados",
        anchor_prefix="- ID: `RUN-STG-01`",
        relative_prefix="  - próxima evidência esperada:",
        new_line=f"  - próxima evidência esperada: {model['next_evidence']}",
    )

    upsert_blocked_item(
        lines,
        item_id="P0-01",
        is_blocked=model["p0_01_is_blocked"] == "true",
        blocked_reason=model["p0_01_blocked_reason"],
        blocked_dependency=model["p0_01_blocked_dependency"],
        owner="Tech Lead Auth",
    )
    upsert_blocked_item(
        lines,
        item_id="P0-02",
        is_blocked=model["p0_02_is_blocked"] == "true",
        blocked_reason=model["p0_02_blocked_reason"],
        blocked_dependency=model["p0_02_blocked_dependency"],
        owner="Owner de Integracao AML",
    )
    upsert_blocked_item(
        lines,
        item_id="P0-03",
        is_blocked=model["p0_03_is_blocked"] == "true",
        blocked_reason=model["p0_03_blocked_reason"],
        blocked_dependency=model["p0_03_blocked_dependency"],
        owner="Owner de Compliance/Sancoes",
    )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sincroniza o registro semanal da janela seria a partir do payload consolidado do prepare_staging_window."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--weekly-file")
    parser.add_argument("--governance-weekly-dir")
    parser.add_argument("--run-url", default="pending")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)

    try:
        payload = load_json_file(payload_file)
        window_id = safe_get_value(payload.get("window_id"), default="unknown-window")
        if args.weekly_file:
            weekly_file = Path(args.weekly_file)
        elif args.governance_weekly_dir:
            weekly_file = default_weekly_file(window_id, Path(args.governance_weekly_dir))
        else:
            raise ValueError("weekly_file_ou_governance_weekly_dir_obrigatorio")

        model = build_weekly_sync_model(payload=payload, payload_file=payload_file, run_url=args.run_url)
        content = weekly_file.read_text(encoding="utf-8")
        updated_content = update_weekly_governance_markdown(content, model)
        weekly_file.write_text(updated_content, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_weekly_governance_render",
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
                "kind": "staging_window_weekly_governance_render",
                "status": "ok",
                "payload_file": str(payload_file),
                "weekly_file": str(weekly_file),
                "window_id": model["window_id"],
                "run_stg_status": model["run_stg_status"],
                "oidc_readiness_status": model["oidc_readiness_status"],
                "p0_02_status": model["p0_02_status"],
                "p0_03_status": model["p0_03_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
