#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_output_file(snapshot_file: Path) -> Path:
    if snapshot_file.suffix == ".json":
        return snapshot_file.with_suffix(".md")
    return snapshot_file.parent / f"{snapshot_file.name}.md"


def format_value(value: Any, default: str = "unknown") -> str:
    if value in (None, ""):
        return default
    return str(value)


def render_markdown(payload: dict[str, Any], snapshot_file: Path) -> str:
    blockers = payload.get("blockers") or {}
    prepare = payload.get("prepare") or {}
    run = payload.get("run") or {}
    artifact = payload.get("artifact_validation") or {}

    lines = [
        f"# Staging Window Status Snapshot - {format_value(payload.get('window_id'), 'unknown-window')}",
        "",
        "## Resumo",
        "",
        f"- window_id: `{format_value(payload.get('window_id'))}`",
        f"- gerado em: `{format_value(payload.get('generated_at'))}`",
        f"- status geral: `{format_value(payload.get('overall_status'))}`",
        f"- arquivo fonte: `{snapshot_file}`",
        "",
        "## Steps",
        "",
        "| Step | Status | Exit Code | Generated At |",
        "| --- | --- | --- | --- |",
        f"| prepare_staging_window | `{format_value(prepare.get('status'))}` | `{format_value(prepare.get('exit_code'))}` | `{format_value(prepare.get('generated_at'), 'n/a')}` |",
        f"| run_staging_window | `{format_value(run.get('status'))}` | `{format_value(run.get('exit_code'))}` | `{format_value(run.get('generated_at'), 'n/a')}` |",
        f"| validate_serious_window_artifact | `{format_value(artifact.get('status'))}` | `{format_value(artifact.get('exit_code'))}` | `n/a` |",
        "",
        "## Bloqueios Consolidados",
        "",
        f"- placeholders pendentes: `{format_value(blockers.get('unresolved_placeholders_count'), '0')}`",
        f"- campos handoff pendentes: `{format_value(blockers.get('missing_handoff_fields_count'), '0')}`",
        "",
        "### Placeholders pendentes",
        "",
    ]

    unresolved_placeholders = blockers.get("unresolved_placeholders") or []
    if unresolved_placeholders:
        for name in unresolved_placeholders:
            lines.append(f"- `{name}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### Campos de handoff pendentes", ""])

    missing_handoff_fields = blockers.get("missing_handoff_fields") or []
    if missing_handoff_fields:
        for field in missing_handoff_fields:
            lines.append(f"- `{field}`")
    else:
        lines.append("- `none`")

    run_errors = run.get("errors") or []
    artifact_errors = artifact.get("errors") or []

    lines.extend(["", "## Erros de Execucao", ""])
    if run_errors:
        for error in run_errors:
            lines.append(f"- run: `{error}`")
    else:
        lines.append("- run: `none`")

    if artifact_errors:
        for error in artifact_errors:
            lines.append(f"- artifact: `{error}`")
    else:
        lines.append("- artifact: `none`")

    lines.extend(
        [
            "",
            "## Proximo Passo",
            "",
            "- preencher segredos reais no `.env.staging.private`",
            "- atualizar `docs/staging-env-ownership.md` com `date/status` por dominio",
            "- rerodar o snapshot para confirmar reducao de bloqueios",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renderiza markdown a partir do snapshot consolidado da janela.")
    parser.add_argument("--snapshot-file", required=True)
    parser.add_argument("--output-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_file = Path(args.snapshot_file)
    output_file = Path(args.output_file) if args.output_file else default_output_file(snapshot_file)

    try:
        payload = load_json_file(snapshot_file)
    except (OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_status_snapshot_render",
                    "status": "failed",
                    "snapshot_file": str(snapshot_file),
                    "errors": [str(exc)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(render_markdown(payload, snapshot_file), encoding="utf-8")

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_status_snapshot_render",
                "status": "ok",
                "snapshot_file": str(snapshot_file),
                "output_file": str(output_file),
                "window_id": format_value(payload.get("window_id"), "unknown-window"),
                "overall_status": format_value(payload.get("overall_status")),
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
