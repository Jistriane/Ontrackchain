#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"nao_foi_possivel_carregar_modulo: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SIGNOFF_MODULE = load_module("render_staging_window_signoff", "scripts/render_staging_window_signoff.py")
WEEKLY_MODULE = load_module("render_staging_window_weekly_governance", "scripts/render_staging_window_weekly_governance.py")
OPERATIONAL_BOARD_MODULE = load_module(
    "render_staging_window_operational_board",
    "scripts/render_staging_window_operational_board.py",
)
CYCLE_OPS_MODULE = load_module(
    "render_staging_window_cycle_ops",
    "scripts/render_staging_window_cycle_ops.py",
)
DECISION_PACKET_MODULE = load_module(
    "render_staging_window_decision_packet",
    "scripts/render_staging_window_decision_packet.py",
)


def default_signoff_output_file(payload_file: Path) -> Path:
    return payload_file.parent / "staging-serious-window-signoff.md"


def load_payload(payload_file: Path) -> dict[str, Any]:
    return json.loads(payload_file.read_text(encoding="utf-8"))


def build_postprocess_model(
    *,
    payload: dict[str, Any],
    payload_file: Path,
    governance_weekly_dir: Path,
    run_url: str,
    signoff_output_file: Path | None,
    run_name: str | None,
    workflow_name: str,
) -> dict[str, Any]:
    signoff_model = SIGNOFF_MODULE.build_signoff_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
        run_name=run_name,
        workflow_name=workflow_name,
    )
    weekly_model = WEEKLY_MODULE.build_weekly_sync_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
    )
    resolved_signoff_output = signoff_output_file or default_signoff_output_file(payload_file)
    resolved_governance_signoff = SIGNOFF_MODULE.default_governance_output_file(
        signoff_model["window_id"], governance_weekly_dir
    )
    resolved_weekly_file = WEEKLY_MODULE.default_weekly_file(signoff_model["window_id"], governance_weekly_dir)
    operational_board_model = OPERATIONAL_BOARD_MODULE.build_model(
        payload=payload,
        payload_file=payload_file,
    )
    decision_packet_model = DECISION_PACKET_MODULE.build_model(
        payload=payload,
        payload_file=payload_file,
        run_url=run_url,
        run_name=run_name,
        workflow_name=workflow_name,
    )
    resolved_decision_packet_output = DECISION_PACKET_MODULE.default_governance_output_file(
        signoff_model["window_id"], governance_weekly_dir
    )
    resolved_war_room_output = CYCLE_OPS_MODULE.default_war_room_file(
        signoff_model["window_id"], governance_weekly_dir
    )
    resolved_live_tracking_output = CYCLE_OPS_MODULE.default_live_tracking_file(
        signoff_model["window_id"], governance_weekly_dir
    )
    return {
        "window_id": signoff_model["window_id"],
        "signoff_model": signoff_model,
        "weekly_model": weekly_model,
        "operational_board_model": operational_board_model,
        "cycle_ops_model": CYCLE_OPS_MODULE.build_model(
            payload=payload,
            payload_file=payload_file,
            run_url=run_url,
        ),
        "decision_packet_model": decision_packet_model,
        "signoff_output_file": resolved_signoff_output,
        "governance_signoff_output_file": resolved_governance_signoff,
        "decision_packet_output_file": resolved_decision_packet_output,
        "war_room_output_file": resolved_war_room_output,
        "live_tracking_output_file": resolved_live_tracking_output,
        "weekly_file": resolved_weekly_file,
        "operational_board_file": OPERATIONAL_BOARD_MODULE.DEFAULT_BOARD_FILE,
    }


def write_postprocessed_outputs(model: dict[str, Any]) -> None:
    signoff_markdown = SIGNOFF_MODULE.render_signoff_markdown(model["signoff_model"])
    weekly_file = model["weekly_file"]
    weekly_content = weekly_file.read_text(encoding="utf-8")
    updated_weekly_content = WEEKLY_MODULE.update_weekly_governance_markdown(weekly_content, model["weekly_model"])
    operational_board_file = model["operational_board_file"]
    operational_board_content = operational_board_file.read_text(encoding="utf-8")
    updated_operational_board_content = OPERATIONAL_BOARD_MODULE.update_operational_board_markdown(
        operational_board_content,
        model["operational_board_model"],
    )
    war_room_output_file = model["war_room_output_file"]
    live_tracking_output_file = model["live_tracking_output_file"]
    war_room_content = war_room_output_file.read_text(encoding="utf-8")
    live_tracking_content = live_tracking_output_file.read_text(encoding="utf-8")
    updated_war_room_content = CYCLE_OPS_MODULE.update_war_room_markdown(
        war_room_content,
        model["cycle_ops_model"],
    )
    updated_live_tracking_content = CYCLE_OPS_MODULE.update_live_tracking_markdown(
        live_tracking_content,
        model["cycle_ops_model"],
    )
    decision_packet_markdown = DECISION_PACKET_MODULE.render_markdown(model["decision_packet_model"])

    signoff_output_file = model["signoff_output_file"]
    governance_signoff_output_file = model["governance_signoff_output_file"]
    decision_packet_output_file = model["decision_packet_output_file"]

    signoff_output_file.parent.mkdir(parents=True, exist_ok=True)
    governance_signoff_output_file.parent.mkdir(parents=True, exist_ok=True)
    decision_packet_output_file.parent.mkdir(parents=True, exist_ok=True)
    weekly_file.parent.mkdir(parents=True, exist_ok=True)
    operational_board_file.parent.mkdir(parents=True, exist_ok=True)
    war_room_output_file.parent.mkdir(parents=True, exist_ok=True)
    live_tracking_output_file.parent.mkdir(parents=True, exist_ok=True)

    signoff_output_file.write_text(signoff_markdown, encoding="utf-8")
    governance_signoff_output_file.write_text(signoff_markdown, encoding="utf-8")
    decision_packet_output_file.write_text(decision_packet_markdown, encoding="utf-8")
    weekly_file.write_text(updated_weekly_content, encoding="utf-8")
    operational_board_file.write_text(updated_operational_board_content, encoding="utf-8")
    war_room_output_file.write_text(updated_war_room_content, encoding="utf-8")
    live_tracking_output_file.write_text(updated_live_tracking_content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o pos-processamento completo do artifact da janela seria: sign-off draft, copia versionada e sincronizacao do board semanal."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--governance-weekly-dir", required=True)
    parser.add_argument("--run-url", default="pending")
    parser.add_argument("--signoff-output-file")
    parser.add_argument("--run-name")
    parser.add_argument("--workflow-name", default="Staging Serious Window")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)
    governance_weekly_dir = Path(args.governance_weekly_dir)
    signoff_output_file = Path(args.signoff_output_file) if args.signoff_output_file else None

    try:
        payload = load_payload(payload_file)
        model = build_postprocess_model(
            payload=payload,
            payload_file=payload_file,
            governance_weekly_dir=governance_weekly_dir,
            run_url=args.run_url,
            signoff_output_file=signoff_output_file,
            run_name=args.run_name,
            workflow_name=args.workflow_name,
        )
        write_postprocessed_outputs(model)
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_artifact_postprocess",
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

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_artifact_postprocess",
                "status": "ok",
                "payload_file": str(payload_file),
                "window_id": model["window_id"],
                "signoff_output_file": str(model["signoff_output_file"]),
                "governance_signoff_output_file": str(model["governance_signoff_output_file"]),
                "decision_packet_output_file": str(model["decision_packet_output_file"]),
                "war_room_output_file": str(model["war_room_output_file"]),
                "live_tracking_output_file": str(model["live_tracking_output_file"]),
                "weekly_file": str(model["weekly_file"]),
                "operational_board_file": str(model["operational_board_file"]),
                "run_stg_status": model["weekly_model"]["run_stg_status"],
                "decision": model["signoff_model"]["decision"],
                "go_no_go_decision": model["decision_packet_model"]["decision"],
                "tracking_status": model["cycle_ops_model"]["tracking_status"],
                "regulatory_scope_label": model["weekly_model"]["regulatory_scope_label"],
                "p0_02_status": model["operational_board_model"]["p0_02_status"],
                "p0_03_status": model["operational_board_model"]["p0_03_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
