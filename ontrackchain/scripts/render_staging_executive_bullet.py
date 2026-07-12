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


def parse_delta_signal(delta_file: Path) -> str:
    if not delta_file.exists():
        return "unknown"
    for raw_line in delta_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- sinal:"):
            if "`" in line:
                return line.split("`", maxsplit=2)[1]
            return line.replace("- sinal:", "").strip()
    return "unknown"


def render_markdown(window_id: str, snapshot_file: Path, delta_file: Path, payload: dict[str, Any]) -> str:
    blockers = payload.get("blockers") or {}
    status = str(payload.get("overall_status") or "unknown")
    signal = parse_delta_signal(delta_file)
    regulatory = payload.get("regulatory") or {}
    operational = payload.get("operational_incidents") or {}
    placeholders = int(blockers.get("unresolved_placeholders_count") or 0)
    handoff = int(blockers.get("missing_handoff_fields_count") or 0)
    scope_label = str(regulatory.get("scope_label") or "unknown")
    p0_04_readiness = str(regulatory.get("p0_04_bundle_readiness") or "unknown")
    rca_attached = int(operational.get("rca_attached_count") or 0)
    critical_open = int(operational.get("critical_open_count") or 0)

    line = (
        f"Ontrackchain | janela {window_id} | status={status} | semaforo={signal} | "
        f"escopo_regulatorio={scope_label} | p0_04={p0_04_readiness} | "
        f"rca={rca_attached} | criticos_abertos={critical_open} | "
        f"bloqueios={placeholders} placeholders/{handoff} handoff | decisao=recomendado_no_go"
    )

    lines = [
        f"# Resumo Executivo Curto - {window_id}",
        "",
        "## Linha Unica",
        "",
        line,
        "",
        "## Fonte",
        "",
        f"- snapshot: `{snapshot_file}`",
        f"- delta: `{delta_file}`",
    ]
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera resumo executivo curto da janela seria.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--snapshot-file", required=True)
    parser.add_argument("--delta-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_file = Path(args.snapshot_file)
    delta_file = Path(args.delta_file)
    output_file = Path(args.output_file)

    payload = load_json(snapshot_file)
    markdown = render_markdown(args.window_id, snapshot_file, delta_file, payload)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "kind": "staging_executive_bullet",
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
