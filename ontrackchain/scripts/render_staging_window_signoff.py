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


def default_output_file(payload_file: Path) -> Path:
    if payload_file.suffix == ".json":
        return payload_file.with_suffix(".signoff.md")
    return payload_file.parent / f"{payload_file.name}.signoff.md"


def extract_window_date(window_id: str) -> str:
    match = re.fullmatch(r"stg-(\d{4}-\d{2}-\d{2})-[a-z0-9]+", window_id)
    if not match:
        raise ValueError(f"window_id_invalido_para_governanca: {window_id}")
    return match.group(1)


def default_governance_output_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = extract_window_date(window_id)
    return (
        governance_weekly_dir
        / "cycles"
        / window_date
        / f"{window_date}-staging-serious-window-signoff.md"
    )


def safe_get_step_status(steps: dict[str, Any], step_name: str, *, default: str = "pending") -> str:
    step = steps.get(step_name) or {}
    return str(step.get("status") or default)


def format_inline_value(value: Any, *, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


def derive_regulatory_scope_label(regulatory_bundle: dict[str, Any]) -> str:
    scope_items: list[str] = []
    if regulatory_bundle.get("compliance_runtime_enabled") is True:
        scope_items.append("P0-02")
    if regulatory_bundle.get("eu_window_enabled") is True:
        scope_items.append("P0-03")
    return "/".join(scope_items) if scope_items else "none"


def collect_regulatory_blockers(regulatory_readiness: dict[str, Any]) -> list[str]:
    return [
        *[
            str(item)
            for item in (((regulatory_readiness.get("compliance_runtime") or {}).get("blockers")) or [])
            if str(item).strip()
        ],
        *[
            str(item)
            for item in (((regulatory_readiness.get("eu_window") or {}).get("blockers")) or [])
            if str(item).strip()
        ],
    ]


def build_decision(overall_status: str) -> str:
    if overall_status == "failed":
        return "blocked"
    if overall_status == "ok":
        return "pending_manual_approval"
    return "pending"


def build_signoff_model(
    *,
    payload: dict[str, Any],
    payload_file: Path,
    run_url: str,
    run_name: str | None,
    workflow_name: str,
) -> dict[str, Any]:
    window_id = str(payload.get("window_id") or "unknown-window")
    mode = str(payload.get("mode") or "unknown")
    environment_name = str(payload.get("environment_name") or "staging-serious")
    overall_status = str(payload.get("status") or "unknown")
    validation_status = str((payload.get("validation") or {}).get("status") or "unknown")
    preflight_status = str((payload.get("preflight") or {}).get("status") or "unknown")
    run_status = str((payload.get("run") or {}).get("status") or "unknown")
    artifact_name = f"serious-staging-window-{window_id}"

    summary = payload.get("summary") or {}
    artifacts = payload.get("artifacts") or {}
    run_payload = (payload.get("run") or {}).get("payload") or {}
    run_steps = run_payload.get("steps") or {}
    run_files = run_payload.get("files") or {}

    release_dossier = run_steps.get("release_dossier") or {}
    homologation = run_steps.get("homologation") or {}
    regulatory_bundle = run_steps.get("regulatory_readiness_bundle") or {}
    oidc_bundle = run_steps.get("oidc_readiness_bundle") or {}
    regulatory_readiness = regulatory_bundle.get("readiness") or {}
    regulatory_scope_label = derive_regulatory_scope_label(regulatory_bundle)
    regulatory_blockers = collect_regulatory_blockers(regulatory_readiness)

    model = {
        "window_id": window_id,
        "workflow_name": workflow_name,
        "run_name": run_name or f"Serious staging window / {window_id} / {mode} / {environment_name}",
        "run_url": run_url or "pending",
        "mode": mode,
        "environment_name": environment_name,
        "artifact_name": artifact_name,
        "overall_status": overall_status,
        "validation_status": validation_status,
        "preflight_status": preflight_status,
        "run_status": run_status,
        "checks_path": artifacts.get("checks_dir") or run_files.get("checks_dir") or "pending",
        "dossier_path": release_dossier.get("artifact_file") or "pending",
        "window_packet_path": artifacts.get("window_packet_file") or run_files.get("window_packet_file") or "pending",
        "homologation_path": homologation.get("artifact_file") or "pending",
        "regulatory_bundle_path": regulatory_bundle.get("output_file") or "pending",
        "payload_json_path": str(payload_file),
        "regulatory_scope_label": regulatory_scope_label,
        "regulatory_scope_is_combined": "true" if regulatory_scope_label == "P0-02/P0-03" else "false",
        "auth_oidc_status": format_inline_value(oidc_bundle.get("readiness_status"), default=safe_get_step_status(run_steps, "oidc_preflight", default=preflight_status)),
        "auth_oidc_technical_status": safe_get_step_status(run_steps, "oidc_preflight", default=preflight_status),
        "auth_oidc_readiness_blockers": oidc_bundle.get("readiness_blockers") or [],
        "auth_oidc_next_action": format_inline_value(oidc_bundle.get("next_action")),
        "mfa_status": (
            "homologated_expected"
            if str(summary.get("mfa_external_provider_homologated") or "").lower() == "true"
            else "baseline_only"
        ),
        "compliance_status": safe_get_step_status(run_steps, "external_preflight", default=preflight_status),
        "aml_kyt_runtime_status": format_inline_value(
            regulatory_bundle.get("compliance_provider_runtime_status"),
            default=safe_get_step_status(run_steps, "regulatory_readiness_bundle", default=run_status),
        ),
        "aml_kyt_runtime_readiness": format_inline_value(
            ((regulatory_readiness.get("compliance_runtime") or {}).get("readiness_status")),
            default="not_in_scope" if regulatory_scope_label == "P0-03" else safe_get_step_status(run_steps, "regulatory_readiness_bundle", default=run_status),
        ),
        "eu_feed_status": format_inline_value(
            regulatory_bundle.get("eu_sanctions_window_status"),
            default=safe_get_step_status(run_steps, "regulatory_readiness_bundle", default=run_status),
        ),
        "eu_feed_readiness": format_inline_value(
            ((regulatory_readiness.get("eu_window") or {}).get("readiness_status")),
            default="not_in_scope" if regulatory_scope_label == "P0-02" else safe_get_step_status(run_steps, "regulatory_readiness_bundle", default=run_status),
        ),
        "p0_04_bundle_readiness": format_inline_value(
            ((regulatory_readiness.get("regulatory_bundle") or {}).get("readiness_status")),
            default=safe_get_step_status(run_steps, "regulatory_readiness_bundle", default=run_status),
        ),
        "investigation_rpc_status": safe_get_step_status(run_steps, "external_preflight", default=preflight_status),
        "reports_evidence_status": safe_get_step_status(run_steps, "release_dossier", default=run_status),
        "ci_cd_status": overall_status,
        "restore_retention_status": safe_get_step_status(run_steps, "release_dossier", default=run_status),
        "blocking_classification": (
            "regulatory_blocked"
            if regulatory_scope_label != "none"
            and (
                ((regulatory_readiness.get("compliance_runtime") or {}).get("readiness_status")) == "blocked"
                or ((regulatory_readiness.get("eu_window") or {}).get("readiness_status")) == "blocked"
            )
            else ("technical_gate_blocked" if overall_status == "failed" else "pending_manual_review")
        ),
        "blocking_summary": (
            "; ".join(regulatory_blockers)
            if regulatory_scope_label != "none" and regulatory_blockers
            else (
                "falha tecnica no gate agregado da janela"
                if overall_status == "failed"
                else "pendente revisao humana final"
            )
        ),
        "decision": build_decision(overall_status),
    }
    return model


def render_signoff_markdown(model: dict[str, Any]) -> str:
    lines = [
        f"# Sign-Off da Janela Seria — `{model['window_id']}`",
        "",
        "> Gerado automaticamente a partir do payload consolidado da janela seria. Revisar e substituir os campos de aprovadores antes do fechamento final.",
        "",
        "## Identificacao",
        "",
        f"- workflow: `{model['workflow_name']}`",
        f"- run name: `{format_inline_value(model['run_name'])}`",
        f"- run url: `{format_inline_value(model['run_url'])}`",
        f"- window_id: `{model['window_id']}`",
        f"- mode: `{format_inline_value(model['mode'])}`",
        f"- environment_name: `{format_inline_value(model['environment_name'])}`",
        f"- escopo regulatorio da tentativa: `{format_inline_value(model['regulatory_scope_label'])}`",
        f"- artifact: `{format_inline_value(model['artifact_name'])}`",
        "",
        "## Status Consolidado",
        "",
        f"- overall status: `{format_inline_value(model['overall_status'])}`",
        f"- validation status: `{format_inline_value(model['validation_status'])}`",
        f"- preflight status: `{format_inline_value(model['preflight_status'])}`",
        f"- run status: `{format_inline_value(model['run_status'])}`",
        "",
        "## Artefatos Revisados",
        "",
        f"- checks: `{format_inline_value(model['checks_path'])}`",
        f"- dossier: `{format_inline_value(model['dossier_path'])}`",
        f"- window packet: `{format_inline_value(model['window_packet_path'])}`",
        f"- homologation: `{format_inline_value(model['homologation_path'])}`",
        f"- regulatory-readiness-bundle: `{format_inline_value(model['regulatory_bundle_path'])}`",
        f"- payload JSON: `{format_inline_value(model['payload_json_path'])}`",
        "",
        "## Gates Revisados",
        "",
        f"- auth/OIDC readiness: `{format_inline_value(model['auth_oidc_status'])}`",
        f"- auth/OIDC technical gate: `{format_inline_value(model['auth_oidc_technical_status'])}`",
        f"- MFA/2FA: `{format_inline_value(model['mfa_status'])}`",
        f"- compliance: `{format_inline_value(model['compliance_status'])}`",
        f"- AML/KYT runtime gate: `{format_inline_value(model['aml_kyt_runtime_status'])}`",
        f"- AML/KYT runtime readiness: `{format_inline_value(model['aml_kyt_runtime_readiness'])}`",
        f"- feed UE tokenizado: `{format_inline_value(model['eu_feed_status'])}`",
        f"- feed UE readiness: `{format_inline_value(model['eu_feed_readiness'])}`",
        f"- bundle regulatorio (`P0-04`) readiness: `{format_inline_value(model['p0_04_bundle_readiness'])}`",
        f"- investigation/RPC: `{format_inline_value(model['investigation_rpc_status'])}`",
        f"- reports e evidencias: `{format_inline_value(model['reports_evidence_status'])}`",
        f"- CI/CD: `{format_inline_value(model['ci_cd_status'])}`",
        f"- restore/retention: `{format_inline_value(model['restore_retention_status'])}`",
        "",
        "## Excecoes ou Bloqueios",
        "",
        f"- bloqueios OIDC readiness: `{format_inline_value('; '.join(model['auth_oidc_readiness_blockers']) if model['auth_oidc_readiness_blockers'] else 'none_declared')}`",
        f"- proximo passo OIDC: `{format_inline_value(model['auth_oidc_next_action'])}`",
        f"- classificacao do bloqueio dominante: `{format_inline_value(model['blocking_classification'])}`",
        f"- bloqueios externos: `{format_inline_value(model['blocking_summary'], default='none_declared')}`",
        "- excecoes aceitas: `none_declared`",
        "- risco residual: `pending_human_review`",
        "",
        "## Aprovadores",
        "",
        "- arquitetura/tech lead: `pending`",
        "- backend/auth: `pending`",
        "- platform/SRE: `pending`",
        "- compliance/security: `pending_if_applicable`",
        "",
        "## Decisao Final",
        "",
        f"- decisao: `{format_inline_value(model['decision'])}`",
        "- proximo passo: revisar este draft, confirmar os artefatos e registrar os aprovadores humanos",
        "- owner do proximo passo: `Release Manager Tecnico`",
        "",
        "## Regras de Atualizacao",
        "",
        "- substituir `run url` pelo link real do GitHub Actions",
        "- manter o nome do artifact exatamente como publicado",
        "- mudar a decisao para `approved` somente se `overall`, `validation`, `preflight` e `run` forem `ok`",
        "- conferir se o escopo regulatorio da tentativa esta coerente com a promotabilidade de `P0-04` antes de aprovar o sign-off",
        "- se houver falha, registrar explicitamente se o bloqueio ocorreu em `validation`, `preflight` ou `run`",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um draft de sign-off da janela seria a partir do payload consolidado do prepare_staging_window."
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
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_signoff_render",
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

    model = build_signoff_model(
        payload=payload,
        payload_file=payload_file,
        run_url=args.run_url,
        run_name=args.run_name,
        workflow_name=args.workflow_name,
    )
    governance_output_file: Path | None = None
    output_file.parent.mkdir(parents=True, exist_ok=True)
    rendered_markdown = render_signoff_markdown(model)
    output_file.write_text(rendered_markdown, encoding="utf-8")
    if args.governance_output_file:
        governance_output_file = Path(args.governance_output_file)
    elif args.governance_weekly_dir:
        governance_output_file = default_governance_output_file(model["window_id"], Path(args.governance_weekly_dir))

    if governance_output_file is not None:
        governance_output_file.parent.mkdir(parents=True, exist_ok=True)
        governance_output_file.write_text(rendered_markdown, encoding="utf-8")

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_signoff_render",
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
