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
    compliance_step = steps.get("compliance_provider_runtime") or {}
    eu_step = steps.get("eu_sanctions_window") or {}
    errors = payload.get("errors") or []

    return {
        "window_id": format_value(payload.get("window_id"), "unknown-window"),
        "generated_at": format_value(payload.get("generated_at")),
        "status": format_value(payload.get("status"), "unknown"),
        "bundle_file": str(bundle_file),
        "compliance_runtime_enabled": bool(scope.get("compliance_runtime_enabled")),
        "eu_window_enabled": bool(scope.get("eu_window_enabled")),
        "compliance_status": format_value(compliance_step.get("status"), "skipped"),
        "compliance_output_file": format_value(compliance_step.get("output_file")),
        "compliance_errors": compliance_step.get("errors") or [],
        "eu_status": format_value(eu_step.get("status"), "skipped"),
        "eu_output_file": format_value(eu_step.get("output_file")),
        "eu_errors": eu_step.get("errors") or [],
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

    if model["errors"]:
        for error in model["errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Observacoes por Step", ""])

    lines.append("### compliance_provider_runtime")
    lines.append("")
    if model["compliance_errors"]:
        for error in model["compliance_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### eu_sanctions_window", ""])
    if model["eu_errors"]:
        for error in model["eu_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## Proximo Passo",
            "",
            "- revisar os JSONs gerados nos steps acima",
            "- anexar este markdown ao dossie ou board semanal da Sprint 7",
            "- promover para a janela seria completa apenas quando o status geral estiver `ok`",
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