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
    return governance_weekly_dir / f"{extract_window_date(window_id)}-staging-serious-window-signoff.md"


def safe_get_step_status(steps: dict[str, Any], step_name: str, *, default: str = "pending") -> str:
    step = steps.get(step_name) or {}
    return str(step.get("status") or default)


def format_inline_value(value: Any, *, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


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
        "payload_json_path": str(payload_file),
        "auth_oidc_status": safe_get_step_status(run_steps, "oidc_preflight", default=preflight_status),
        "mfa_status": (
            "homologated_expected"
            if str(summary.get("mfa_external_provider_homologated") or "").lower() == "true"
            else "baseline_only"
        ),
        "compliance_status": safe_get_step_status(run_steps, "external_preflight", default=preflight_status),
        "investigation_rpc_status": safe_get_step_status(run_steps, "external_preflight", default=preflight_status),
        "reports_evidence_status": safe_get_step_status(run_steps, "release_dossier", default=run_status),
        "ci_cd_status": overall_status,
        "restore_retention_status": safe_get_step_status(run_steps, "release_dossier", default=run_status),
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
        f"- payload JSON: `{format_inline_value(model['payload_json_path'])}`",
        "",
        "## Gates Revisados",
        "",
        f"- auth/OIDC: `{format_inline_value(model['auth_oidc_status'])}`",
        f"- MFA/2FA: `{format_inline_value(model['mfa_status'])}`",
        f"- compliance: `{format_inline_value(model['compliance_status'])}`",
        f"- investigation/RPC: `{format_inline_value(model['investigation_rpc_status'])}`",
        f"- reports e evidencias: `{format_inline_value(model['reports_evidence_status'])}`",
        f"- CI/CD: `{format_inline_value(model['ci_cd_status'])}`",
        f"- restore/retention: `{format_inline_value(model['restore_retention_status'])}`",
        "",
        "## Excecoes ou Bloqueios",
        "",
        "- bloqueios externos: `none_declared`",
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
