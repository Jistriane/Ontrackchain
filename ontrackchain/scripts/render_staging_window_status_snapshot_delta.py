#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sort_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def latest_two_snapshots(history_dir: Path, window_id: str) -> list[Path]:
    pattern = f"{window_id}-status-snapshot-*.json"
    files = sorted(history_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
    if len(files) < 2:
        return files
    return files[-2:]


def default_output_file(window_id: str) -> Path:
    return Path("docs/governance-weekly") / f"{window_id}-status-snapshot-delta.md"


def compute_executive_signal(
    prev_status: str,
    cur_status: str,
    delta_placeholders: int,
    delta_handoff: int,
    added_placeholders: list[str],
    added_handoff: list[str],
) -> tuple[str, str]:
    if cur_status == "ok" and delta_placeholders <= 0 and delta_handoff <= 0:
        return ("verde", "janela elegivel para go tecnico, manter monitoramento")

    if added_placeholders or added_handoff or delta_placeholders > 0 or delta_handoff > 0:
        return ("vermelho", "houve regressao de bloqueios; manter no-go e abrir acao corretiva")

    if prev_status == "failed" and cur_status == "failed":
        if delta_placeholders < 0 or delta_handoff < 0:
            return ("amarelo", "houve progresso parcial, mas ainda sem condicao de go")
        return ("amarelo", "estado estavel sem progresso material; manter no-go")

    return ("amarelo", "avaliar manualmente o contexto antes de decisao de go/no-go")


def render_markdown(window_id: str, current: dict[str, Any], previous: dict[str, Any], current_file: Path, previous_file: Path) -> str:
    cur_blockers = current.get("blockers") or {}
    prev_blockers = previous.get("blockers") or {}

    cur_placeholders = sort_unique(cur_blockers.get("unresolved_placeholders") or [])
    prev_placeholders = sort_unique(prev_blockers.get("unresolved_placeholders") or [])

    cur_handoff = sort_unique(cur_blockers.get("missing_handoff_fields") or [])
    prev_handoff = sort_unique(prev_blockers.get("missing_handoff_fields") or [])

    placeholders_resolved = sorted(set(prev_placeholders) - set(cur_placeholders))
    placeholders_added = sorted(set(cur_placeholders) - set(prev_placeholders))

    handoff_resolved = sorted(set(prev_handoff) - set(cur_handoff))
    handoff_added = sorted(set(cur_handoff) - set(prev_handoff))

    cur_count_p = int(cur_blockers.get("unresolved_placeholders_count") or len(cur_placeholders))
    prev_count_p = int(prev_blockers.get("unresolved_placeholders_count") or len(prev_placeholders))
    delta_p = cur_count_p - prev_count_p

    cur_count_h = int(cur_blockers.get("missing_handoff_fields_count") or len(cur_handoff))
    prev_count_h = int(prev_blockers.get("missing_handoff_fields_count") or len(prev_handoff))
    delta_h = cur_count_h - prev_count_h

    prev_status = str(previous.get("overall_status", "unknown"))
    cur_status = str(current.get("overall_status", "unknown"))
    signal, signal_note = compute_executive_signal(
        prev_status,
        cur_status,
        delta_p,
        delta_h,
        placeholders_added,
        handoff_added,
    )

    lines = [
        f"# Staging Window Status Delta - {window_id}",
        "",
        "## Fontes",
        "",
        f"- anterior: `{previous_file}`",
        f"- atual: `{current_file}`",
        "",
        "## Resumo",
        "",
        f"- status anterior: `{prev_status}`",
        f"- status atual: `{cur_status}`",
        f"- placeholders: `{prev_count_p}` -> `{cur_count_p}` (delta `{delta_p:+d}`)",
        f"- handoff pendente: `{prev_count_h}` -> `{cur_count_h}` (delta `{delta_h:+d}`)",
        "",
        "## Semaforo Executivo",
        "",
        f"- sinal: `{signal}`",
        f"- leitura: {signal_note}",
        "",
        "## Placeholders",
        "",
        "### Placeholders Resolvidos",
        "",
    ]

    if placeholders_resolved:
        for item in placeholders_resolved:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### Placeholders Novos", ""])
    if placeholders_added:
        for item in placeholders_added:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Handoff", "", "### Handoff Resolvidos", ""])
    if handoff_resolved:
        for item in handoff_resolved:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "### Handoff Novos", ""])
    if handoff_added:
        for item in handoff_added:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `none`")

    lines.extend(
        [
            "",
            "## Proximo Passo",
            "",
            "- se houver delta negativo, atualizar war room com itens desbloqueados",
            "- se houver delta positivo, registrar regressao e abrir acao corretiva",
            "- rerodar snapshot apos qualquer mudanca em `.env.staging.private` ou `staging-env-ownership.md`",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera delta entre os dois snapshots mais recentes da janela.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--history-dir", required=True)
    parser.add_argument("--output-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    history_dir = Path(args.history_dir)
    output_file = Path(args.output_file) if args.output_file else default_output_file(args.window_id)

    files = latest_two_snapshots(history_dir, args.window_id)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if len(files) < 2:
        content = "\n".join(
            [
                f"# Staging Window Status Delta - {args.window_id}",
                "",
                "## Resumo",
                "",
                "- `insufficient_history`: menos de 2 snapshots historicos disponiveis",
                f"- history_dir: `{history_dir}`",
                "",
                "## Proximo Passo",
                "",
                "- executar novamente `make run-staging-window-status-snapshot-local WINDOW_ID=<window_id>` para criar base de comparacao",
                "",
            ]
        )
        output_file.write_text(content, encoding="utf-8")
        print(
            json.dumps(
                {
                    "kind": "staging_window_status_snapshot_delta",
                    "status": "insufficient_history",
                    "window_id": args.window_id,
                    "history_dir": str(history_dir),
                    "output_file": str(output_file),
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    previous_file, current_file = files[0], files[1]
    previous = load_json(previous_file)
    current = load_json(current_file)

    output_file.write_text(
        render_markdown(args.window_id, current, previous, current_file, previous_file),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "kind": "staging_window_status_snapshot_delta",
                "status": "ok",
                "window_id": args.window_id,
                "history_dir": str(history_dir),
                "previous_file": str(previous_file),
                "current_file": str(current_file),
                "output_file": str(output_file),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
