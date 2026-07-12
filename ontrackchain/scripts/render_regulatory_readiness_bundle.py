#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_output_file(bundle_file: Path) -> Path:
    if bundle_file.suffix == ".json":
        return bundle_file.with_suffix(".md")
    return bundle_file.parent / f"{bundle_file.name}.md"


def format_value(value: Any, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


def format_bool(value: Any) -> str:
    return "yes" if bool(value) else "no"


def build_model(payload: dict[str, Any], bundle_file: Path) -> dict[str, Any]:
    steps = payload.get("steps") or {}
    scope = payload.get("scope") or {}
    readiness = payload.get("readiness") or {}
    compliance_step = steps.get("compliance_provider_runtime") or {}
    eu_step = steps.get("eu_sanctions_window") or {}
    compliance_readiness = readiness.get("compliance_runtime") or {}
    eu_readiness = readiness.get("eu_window") or {}
    bundle_readiness = readiness.get("regulatory_bundle") or {}
    compliance_correlation = compliance_step.get("correlation") or {}
    eu_correlation = eu_step.get("correlation") or {}
    errors = payload.get("errors") or []

    return {
        "window_id": format_value(payload.get("window_id"), "unknown-window"),
        "generated_at": format_value(payload.get("generated_at")),
        "status": format_value(payload.get("status"), "unknown"),
        "bundle_file": str(bundle_file),
        "compliance_runtime_enabled": bool(scope.get("compliance_runtime_enabled")),
        "eu_window_enabled": bool(scope.get("eu_window_enabled")),
        "compliance_status": format_value(compliance_step.get("status"), "skipped"),
        "compliance_request_id": format_value(compliance_step.get("request_id")),
        "compliance_output_file": format_value(compliance_step.get("output_file")),
        "compliance_errors": compliance_step.get("errors") or [],
        "compliance_internal_operating_mode": format_value(
            compliance_correlation.get("internal_operating_mode")
        ),
        "compliance_catalog_provider_status": format_value(
            compliance_correlation.get("catalog_provider_status")
        ),
        "compliance_catalog_capability_status": format_value(
            compliance_correlation.get("catalog_capability_status")
        ),
        "compliance_runtime_provider_status": format_value(
            compliance_correlation.get("runtime_provider_status")
        ),
        "compliance_runtime_capability_status": format_value(
            compliance_correlation.get("runtime_capability_status")
        ),
        "compliance_runtime_delivery_mode": format_value(
            compliance_correlation.get("runtime_delivery_mode")
        ),
        "compliance_provider_converges_live": format_value(
            compliance_correlation.get("provider_converges_live"), "false"
        ),
        "compliance_readiness_status": format_value(
            compliance_readiness.get("readiness_status"), "pending"
        ),
        "compliance_next_action": format_value(compliance_readiness.get("next_action")),
        "compliance_blockers": compliance_readiness.get("blockers") or [],
        "eu_status": format_value(eu_step.get("status"), "skipped"),
        "eu_request_id": format_value(eu_step.get("request_id")),
        "eu_output_file": format_value(eu_step.get("output_file")),
        "eu_errors": eu_step.get("errors") or [],
        "eu_expected_source_url": format_value(eu_correlation.get("expected_source_url")),
        "eu_observed_source_url": format_value(eu_correlation.get("observed_source_url")),
        "eu_source_url_matches_expected": format_value(
            eu_correlation.get("source_url_matches_expected"), "false"
        ),
        "eu_override_tokenized": format_value(eu_correlation.get("override_tokenized"), "false"),
        "eu_persisted_status": format_value(eu_correlation.get("persisted_status")),
        "eu_persisted_status_active": format_value(
            eu_correlation.get("persisted_status_active"), "false"
        ),
        "eu_last_sync_status": format_value(eu_correlation.get("last_sync_status")),
        "eu_last_sync_status_success": format_value(
            eu_correlation.get("last_sync_status_success"), "false"
        ),
        "eu_window_converges_ready": format_value(
            eu_correlation.get("eu_window_converges_ready"), "false"
        ),
        "eu_readiness_status": format_value(eu_readiness.get("readiness_status"), "pending"),
        "eu_next_action": format_value(eu_readiness.get("next_action")),
        "eu_blockers": eu_readiness.get("blockers") or [],
        "bundle_readiness_status": format_value(bundle_readiness.get("readiness_status"), "pending"),
        "bundle_next_action": format_value(bundle_readiness.get("next_action")),
        "bundle_blockers": bundle_readiness.get("blockers") or [],
        "errors": errors,
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        f"# Regulatory Readiness Bundle - {model['window_id']}",
        "",
        "## Resumo",
        "",
        f"- window_id: `{model['window_id']}`",
        f"- gerado em: `{model['generated_at']}`",
        f"- status geral: `{model['status']}`",
        f"- arquivo fonte: `{model['bundle_file']}`",
        "",
        "## Escopo",
        "",
        f"- AML/KYT runtime no escopo: `{format_bool(model['compliance_runtime_enabled'])}`",
        f"- feed UE no escopo: `{format_bool(model['eu_window_enabled'])}`",
        "",
        "## Readiness Executivo",
        "",
        f"- AML/KYT readiness: `{model['compliance_readiness_status']}`",
        f"- feed UE readiness: `{model['eu_readiness_status']}`",
        f"- bundle regulatorio readiness: `{model['bundle_readiness_status']}`",
        "",
        "## Steps",
        "",
        "| Step | Enabled | Status | Artifact |",
        "| --- | --- | --- | --- |",
        f"| compliance_provider_runtime | `{format_bool(model['compliance_runtime_enabled'])}` | `{model['compliance_status']}` | `{model['compliance_output_file']}` |",
        f"| eu_sanctions_window | `{format_bool(model['eu_window_enabled'])}` | `{model['eu_status']}` | `{model['eu_output_file']}` |",
        "",
        "## Bloqueios",
        "",
    ]

    if model["errors"] or model["bundle_blockers"]:
        for error in model["errors"]:
            lines.append(f"- `{error}`")
        for error in model["bundle_blockers"]:
            lines.append(f"- readiness bundle: `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Proximo Passo Executivo", ""])
    lines.append(f"- AML/KYT: `{model['compliance_next_action']}`")
    lines.append(f"- feed UE: `{model['eu_next_action']}`")
    lines.append(f"- bundle regulatorio: `{model['bundle_next_action']}`")

    lines.extend(["", "## Observacoes por Step", ""])

    lines.append("### compliance_provider_runtime")
    lines.append("")
    lines.append(f"- request_id: `{model['compliance_request_id']}`")
    lines.append(
        f"- operating_mode interno: `{model['compliance_internal_operating_mode']}`"
    )
    lines.append(
        f"- status do catalogo publico: `{model['compliance_catalog_provider_status']}`"
    )
    lines.append(
        f"- capability do catalogo publico: `{model['compliance_catalog_capability_status']}`"
    )
    lines.append(
        f"- status do runtime AML/KYT: `{model['compliance_runtime_provider_status']}`"
    )
    lines.append(
        f"- capability do runtime AML/KYT: `{model['compliance_runtime_capability_status']}`"
    )
    lines.append(
        f"- delivery_mode do runtime AML/KYT: `{model['compliance_runtime_delivery_mode']}`"
    )
    lines.append(
        f"- convergencia live do provider: `{model['compliance_provider_converges_live']}`"
    )
    if model["compliance_blockers"]:
        for error in model["compliance_blockers"]:
            lines.append(f"- readiness: `{error}`")
    if model["compliance_errors"]:
        for error in model["compliance_errors"]:
            lines.append(f"- `{error}`")
    elif not model["compliance_blockers"]:
        lines.append("- `none`")

    lines.extend(["", "### eu_sanctions_window", ""])
    lines.append(f"- request_id: `{model['eu_request_id']}`")
    lines.append(f"- source_url esperada: `{model['eu_expected_source_url']}`")
    lines.append(f"- source_url observada: `{model['eu_observed_source_url']}`")
    lines.append(f"- source_url converge com override: `{model['eu_source_url_matches_expected']}`")
    lines.append(f"- override tokenizado: `{model['eu_override_tokenized']}`")
    lines.append(f"- persisted_status UE: `{model['eu_persisted_status']}`")
    lines.append(f"- persisted_status ativo: `{model['eu_persisted_status_active']}`")
    lines.append(f"- last_sync_status UE: `{model['eu_last_sync_status']}`")
    lines.append(f"- last_sync_status em sucesso: `{model['eu_last_sync_status_success']}`")
    lines.append(f"- convergencia pronta da janela UE: `{model['eu_window_converges_ready']}`")
    if model["eu_blockers"]:
        for error in model["eu_blockers"]:
            lines.append(f"- readiness: `{error}`")
    if model["eu_errors"]:
        for error in model["eu_errors"]:
            lines.append(f"- `{error}`")
    elif not model["eu_blockers"]:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## Proximo Passo",
            "",
            "- revisar os JSONs gerados nos steps acima",
            "- anexar este markdown ao dossie ou board semanal da Sprint 7",
            "- promover para a janela seria completa apenas quando o readiness do bundle estiver `ready_for_validation`",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Renderiza um resumo Markdown do regulatory readiness bundle."
    )
    parser.add_argument("--bundle-file", required=True)
    parser.add_argument("--output-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle_file = Path(args.bundle_file)
    output_file = Path(args.output_file) if args.output_file else default_output_file(bundle_file)

    try:
        payload = load_json_file(bundle_file)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "regulatory_readiness_bundle_render",
                    "status": "failed",
                    "bundle_file": str(bundle_file),
                    "errors": [str(exc)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    model = build_model(payload, bundle_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(render_markdown(model), encoding="utf-8")

    sys.stdout.write(
        json.dumps(
            {
                "kind": "regulatory_readiness_bundle_render",
                "status": "ok",
                "bundle_file": str(bundle_file),
                "output_file": str(output_file),
                "window_id": model["window_id"],
                "overall_status": model["status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
