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


def parse_delta_signal(delta_file: Path) -> tuple[str, str]:
    if not delta_file.exists():
        return ("unknown", "delta indisponivel")

    signal = "unknown"
    reading = "delta indisponivel"
    for raw_line in delta_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- sinal:"):
            signal = line.split("`", maxsplit=2)[1] if "`" in line else line.replace("- sinal:", "").strip()
        if line.startswith("- leitura:"):
            reading = line.replace("- leitura:", "").strip()
    return (signal, reading)


def render_markdown(
    window_id: str,
    snapshot_file: Path,
    delta_file: Path,
    dashboard_file: Path,
    unblock_file: Path,
    payload: dict[str, Any],
) -> str:
    blockers = payload.get("blockers") or {}
    prepare = payload.get("prepare") or {}
    run = payload.get("run") or {}
    artifact = payload.get("artifact_validation") or {}

    signal, reading = parse_delta_signal(delta_file)

    lines = [
        f"# Resumo de Comunicacao - {window_id}",
        "",
        "## Bloco Curto (Slack/Teams)",
        "",
        f"Janela {window_id}: status `{payload.get('overall_status', 'unknown')}` | semaforo `{signal}`.",
        f"Bloqueios: `{blockers.get('unresolved_placeholders_count', 0)}` placeholders e `{blockers.get('missing_handoff_fields_count', 0)}` handoff.",
        f"Steps: prepare `{prepare.get('status', 'unknown')}`, run `{run.get('status', 'unknown')}`, artifact `{artifact.get('status', 'unknown')}`.",
        f"Leitura: {reading}",
        "Acao: owners por trilha devem executar o checklist de desbloqueio e rerodar o comando unico.",
        "",
        "## Mensagem Expandida",
        "",
        f"- janela: `{window_id}`",
        f"- snapshot: `{snapshot_file}`",
        f"- status geral: `{payload.get('overall_status', 'unknown')}`",
        f"- semaforo executivo: `{signal}`",
        f"- leitura do delta: {reading}",
        f"- placeholders pendentes: `{blockers.get('unresolved_placeholders_count', 0)}`",
        f"- handoff pendente: `{blockers.get('missing_handoff_fields_count', 0)}`",
        "",
        "Referencias para o war room:",
        f"- dashboard executivo: `{dashboard_file}`",
        f"- checklist de desbloqueio: `{unblock_file}`",
        f"- delta de status: `{delta_file}`",
        "",
        "Comando unico:",
        f"- `make refresh-staging-war-room-governance-local WINDOW_ID={window_id}`",
    ]

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera resumo de comunicacao do war room para Slack/Teams.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--snapshot-file", required=True)
    parser.add_argument("--delta-file", required=True)
    parser.add_argument("--dashboard-file", required=True)
    parser.add_argument("--unblock-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_file = Path(args.snapshot_file)
    delta_file = Path(args.delta_file)
    dashboard_file = Path(args.dashboard_file)
    unblock_file = Path(args.unblock_file)
    output_file = Path(args.output_file)

    payload = load_json(snapshot_file)
    markdown = render_markdown(
        args.window_id,
        snapshot_file,
        delta_file,
        dashboard_file,
        unblock_file,
        payload,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "kind": "staging_comms_summary",
                "status": "ok",
                "window_id": args.window_id,
                "snapshot_file": str(snapshot_file),
                "output_file": str(output_file),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
