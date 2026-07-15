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


def build_model(payload: dict[str, Any], bundle_file: Path) -> dict[str, Any]:
    steps = payload.get("steps") or {}
    preflight = steps.get("oidc_preflight") or {}
    smoke = steps.get("smoke_auth_oidc_mode") or {}
    playwright = steps.get("oidc_playwright_critical") or {}
    readiness = payload.get("readiness") or {}
    return {
        "window_id": format_value(payload.get("window_id"), "unknown-window"),
        "generated_at": format_value(payload.get("generated_at")),
        "status": format_value(payload.get("status"), "unknown"),
        "readiness_status": format_value(readiness.get("readiness_status"), "unknown"),
        "readiness_blockers": readiness.get("blockers") or [],
        "next_action": format_value(readiness.get("next_action"), "pending"),
        "bundle_file": str(bundle_file),
        "mfa_external_provider_homologated": format_value(
            (payload.get("scope") or {}).get("mfa_external_provider_homologated"),
            "false",
        ),
        "expected_oidc_provider": format_value(
            (payload.get("scope") or {}).get("expected_oidc_provider"),
            "pending",
        ),
        "preflight_status": format_value(preflight.get("status"), "skipped"),
        "preflight_output_file": format_value(preflight.get("output_file")),
        "preflight_errors": preflight.get("errors") or [],
        "smoke_status": format_value(smoke.get("status"), "skipped"),
        "smoke_output_file": format_value(smoke.get("output_file")),
        "smoke_errors": smoke.get("errors") or [],
        "playwright_status": format_value(playwright.get("status"), "skipped"),
        "playwright_output_file": format_value(playwright.get("output_file")),
        "playwright_errors": playwright.get("errors") or [],
        "errors": payload.get("errors") or [],
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        f"# OIDC Readiness Bundle - {model['window_id']}",
        "",
        "## Resumo",
        "",
        f"- window_id: `{model['window_id']}`",
        f"- gerado em: `{model['generated_at']}`",
        f"- status geral: `{model['status']}`",
        f"- status de readiness: `{model['readiness_status']}`",
        f"- arquivo fonte: `{model['bundle_file']}`",
        f"- provider esperado: `{model['expected_oidc_provider']}`",
        f"- MFA federado homologado: `{model['mfa_external_provider_homologated']}`",
        "",
        "## Steps",
        "",
        "| Step | Status | Artifact |",
        "| --- | --- | --- |",
        f"| oidc_preflight | `{model['preflight_status']}` | `{model['preflight_output_file']}` |",
        f"| smoke_auth_oidc_mode | `{model['smoke_status']}` | `{model['smoke_output_file']}` |",
        f"| oidc_playwright_critical | `{model['playwright_status']}` | `{model['playwright_output_file']}` |",
        "",
        "## Bloqueios",
        "",
    ]
    if model["errors"]:
        for error in model["errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Bloqueadores de Readiness", ""])
    if model["readiness_blockers"]:
        for error in model["readiness_blockers"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Observacoes por Step", "", "### oidc_preflight", ""])
    if model["preflight_errors"]:
        for error in model["preflight_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### smoke_auth_oidc_mode", ""])
    if model["smoke_errors"]:
        for error in model["smoke_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### oidc_playwright_critical", ""])
    if model["playwright_errors"]:
        for error in model["playwright_errors"]:
            lines.append(f"- `{error}`")
    else:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## Proximo Passo",
            "",
            f"- {model['next_action']}",
            "- anexar este markdown ao war room e ao sign-off quando a janela incluir P0-01",
            "- usar o artefato `oidc_playwright_critical` como evidencia primaria de navegador real quando o gate estiver habilitado",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renderiza um resumo Markdown do bundle OIDC.")
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
                    "kind": "oidc_readiness_bundle_render",
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
                "kind": "oidc_readiness_bundle_render",
                "status": "ok",
                "bundle_file": str(bundle_file),
                "output_file": str(output_file),
                "window_id": model["window_id"],
                "overall_status": model["status"],
                "readiness_status": model["readiness_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
