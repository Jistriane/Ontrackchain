#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def latest_two_snapshots(history_dir: Path, window_id: str) -> list[Path]:
    files = sorted(
        history_dir.glob(f"{window_id}-status-snapshot-*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if len(files) < 2:
        return files
    return files[-2:]


def compute_signal(previous: dict[str, Any], current: dict[str, Any]) -> tuple[str, str]:
    prev_blockers = previous.get("blockers") or {}
    cur_blockers = current.get("blockers") or {}

    prev_p = int(prev_blockers.get("unresolved_placeholders_count") or 0)
    cur_p = int(cur_blockers.get("unresolved_placeholders_count") or 0)
    prev_h = int(prev_blockers.get("missing_handoff_fields_count") or 0)
    cur_h = int(cur_blockers.get("missing_handoff_fields_count") or 0)

    delta_p = cur_p - prev_p
    delta_h = cur_h - prev_h
    status = str(current.get("overall_status") or "unknown")

    if status == "ok" and delta_p <= 0 and delta_h <= 0:
        return ("verde", "condicao tecnica para go")
    if delta_p > 0 or delta_h > 0:
        return ("vermelho", "regressao de bloqueios")
    if delta_p < 0 or delta_h < 0:
        return ("amarelo", "progresso parcial com bloqueios remanescentes")
    return ("amarelo", "estado estavel sem progresso material")


def render_markdown(window_id: str, current_snapshot_file: Path, previous_snapshot_file: Path | None, action_plan_file: Path, status_snapshot_md: Path, status_delta_md: Path, dashboard_generated_at: str, current: dict[str, Any], previous: dict[str, Any]) -> str:
    blockers = current.get("blockers") or {}
    prepare = current.get("prepare") or {}
    run = current.get("run") or {}
    artifact = current.get("artifact_validation") or {}

    signal, signal_note = compute_signal(previous, current)

    lines = [
        f"# Governance Dashboard - {window_id}",
        "",
        "## Leitura Executiva",
        "",
        f"- atualizado em: `{dashboard_generated_at}`",
        f"- status geral: `{current.get('overall_status', 'unknown')}`",
        f"- semaforo executivo: `{signal}`",
        f"- leitura: {signal_note}",
        f"- placeholders pendentes: `{blockers.get('unresolved_placeholders_count', 0)}`",
        f"- handoff pendente: `{blockers.get('missing_handoff_fields_count', 0)}`",
        "",
        "## Status dos Steps",
        "",
        "| Step | Status |",
        "| --- | --- |",
        f"| prepare_staging_window | `{prepare.get('status', 'unknown')}` |",
        f"| run_staging_window | `{run.get('status', 'unknown')}` |",
        f"| validate_serious_window_artifact | `{artifact.get('status', 'unknown')}` |",
        "",
        "## Artefatos de Referencia",
        "",
        f"- action plan: `{action_plan_file}`",
        f"- status snapshot (md): `{status_snapshot_md}`",
        f"- status delta (md): `{status_delta_md}`",
        f"- snapshot atual (json): `{current_snapshot_file}`",
    ]

    if previous_snapshot_file:
        lines.append(f"- snapshot anterior (json): `{previous_snapshot_file}`")

    lines.extend(
        [
            "",
            "## Comando Unico",
            "",
            f"- `make refresh-staging-war-room-governance-local WINDOW_ID={window_id}`",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera dashboard executivo da janela seria.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--history-dir", default="artifacts/staging/checks/history")
    parser.add_argument("--action-plan-file", default="")
    parser.add_argument("--status-snapshot-file", default="")
    parser.add_argument("--status-delta-file", default="")
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    history_dir = Path(args.history_dir)
    output_file = Path(args.output_file)

    snapshots = latest_two_snapshots(history_dir, args.window_id)
    if not snapshots:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(
            "\n".join(
                [
                    f"# Governance Dashboard - {args.window_id}",
                    "",
                    "- status: `insufficient_history`",
                    f"- history_dir: `{history_dir}`",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "kind": "staging_governance_dashboard",
                    "status": "insufficient_history",
                    "window_id": args.window_id,
                    "output_file": str(output_file),
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    current_snapshot_file = snapshots[-1]
    previous_snapshot_file = snapshots[-2] if len(snapshots) > 1 else None

    current = load_json(current_snapshot_file)
    previous = load_json(previous_snapshot_file) if previous_snapshot_file else {}

    action_plan_file = Path(args.action_plan_file) if args.action_plan_file else Path(
        f"docs/governance-weekly/{args.window_id}-war-room-action-plan.md"
    )
    status_snapshot_md = Path(args.status_snapshot_file) if args.status_snapshot_file else Path(
        f"docs/governance-weekly/{args.window_id}-status-snapshot.md"
    )
    status_delta_md = Path(args.status_delta_file) if args.status_delta_file else Path(
        f"docs/governance-weekly/{args.window_id}-status-snapshot-delta.md"
    )

    generated_at = str(current.get("generated_at") or "unknown")
    markdown = render_markdown(
        args.window_id,
        current_snapshot_file,
        previous_snapshot_file,
        action_plan_file,
        status_snapshot_md,
        status_delta_md,
        generated_at,
        current,
        previous,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "kind": "staging_governance_dashboard",
                "status": "ok",
                "window_id": args.window_id,
                "output_file": str(output_file),
                "current_snapshot_file": str(current_snapshot_file),
                "previous_snapshot_file": str(previous_snapshot_file) if previous_snapshot_file else None,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
