#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json_from_stdout(stdout: str) -> dict[str, Any]:
    text = stdout.strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def run_command(command: list[str]) -> dict[str, Any]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    payload = parse_json_from_stdout(result.stdout)
    if not payload:
        payload = parse_json_from_stdout(result.stderr)
    if not payload:
        payload = parse_json_from_stdout(result.stdout + "\n" + result.stderr)
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "payload": payload,
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_operational_alerts_rca_summary(checks_dir: Path, window_id: str) -> dict[str, Any]:
    summary_file = checks_dir / f"{window_id}-operational-alerts-rca-summary.json"
    payload = load_json(summary_file)
    if not payload:
        return {
            "status": "not_available",
            "summary_file": str(summary_file),
            "exported_count": 0,
            "tracked_work_items_count": 0,
            "rca_attached_count": 0,
            "confirmed_root_cause_count": 0,
            "firing_count": 0,
            "critical_open_count": 0,
            "pending_triage_count": 0,
            "acknowledged_count": 0,
            "ready_queue_count": 0,
            "containment_status_counts": {},
            "top_rca_domains": [],
            "top_affected_domains": [],
        }

    payload["status"] = "available"
    payload["summary_file"] = str(summary_file)
    payload.setdefault("exported_count", 0)
    payload.setdefault("tracked_work_items_count", 0)
    payload.setdefault("rca_attached_count", 0)
    payload.setdefault("confirmed_root_cause_count", 0)
    payload.setdefault("firing_count", 0)
    payload.setdefault("critical_open_count", 0)
    payload.setdefault("pending_triage_count", 0)
    payload.setdefault("acknowledged_count", 0)
    payload.setdefault("ready_queue_count", 0)
    payload.setdefault("containment_status_counts", {})
    payload.setdefault("top_rca_domains", [])
    payload.setdefault("top_affected_domains", [])
    return payload


def collect_blockers(checks_dir: Path, window_id: str) -> dict[str, Any]:
    placeholders_file = checks_dir / f"placeholders-{window_id}.json"
    handoff_file = checks_dir / f"handoff-{window_id}.json"

    placeholders_payload = load_json(placeholders_file)
    handoff_payload = load_json(handoff_file)

    unresolved = placeholders_payload.get("unresolved_placeholders", [])
    incomplete_groups = handoff_payload.get("incomplete_groups", [])

    unresolved_names = sorted(
        {
            str(item.get("name") or "").strip()
            for item in unresolved
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        }
    )

    missing_handoff_fields: list[str] = []
    for group in incomplete_groups:
        if not isinstance(group, dict):
            continue
        group_name = str(group.get("group") or "").strip()
        for field in group.get("missing_fields", []):
            missing_handoff_fields.append(f"{group_name}.{field}")

    return {
        "placeholders_file": str(placeholders_file),
        "handoff_file": str(handoff_file),
        "unresolved_placeholders_count": len(unresolved_names),
        "unresolved_placeholders": unresolved_names,
        "missing_handoff_fields_count": len(sorted(set(missing_handoff_fields))),
        "missing_handoff_fields": sorted(set(missing_handoff_fields)),
    }


def compute_overall_status(prepare: dict[str, Any], run: dict[str, Any], validate: dict[str, Any]) -> str:
    statuses = []
    for item in (prepare, run, validate):
        payload_status = str(item.get("payload", {}).get("status") or "").strip()
        if payload_status:
            statuses.append(payload_status)
            continue
        statuses.append("ok" if int(item.get("exit_code", 1)) == 0 else "failed")
    if all(status == "ok" for status in statuses):
        return "ok"
    if any(status == "failed" for status in statuses):
        return "failed"
    return "unknown"


def derive_regulatory_scope_label(regulatory_bundle: dict[str, Any]) -> str:
    scope_items: list[str] = []
    if regulatory_bundle.get("compliance_runtime_enabled") is True:
        scope_items.append("P0-02")
    if regulatory_bundle.get("eu_window_enabled") is True:
        scope_items.append("P0-03")
    return "/".join(scope_items) if scope_items else "none"


def build_regulatory_snapshot(run: dict[str, Any], validate: dict[str, Any]) -> dict[str, Any]:
    run_payload = run.get("payload") or {}
    run_steps = run_payload.get("steps") or {}
    regulatory_bundle = run_steps.get("regulatory_readiness_bundle") or {}
    readiness = regulatory_bundle.get("readiness") or {}
    validation_payload = validate.get("payload") or {}
    validation_scope = validation_payload.get("scope") or []
    regulatory_scope_label = derive_regulatory_scope_label(regulatory_bundle)
    combined_scope = regulatory_scope_label == "P0-02/P0-03"
    if combined_scope:
        promotion_note = "tentativa combinada; P0-04 pode ser promovido se a validacao final convergir"
    elif regulatory_scope_label == "none":
        promotion_note = "sem escopo regulatorio material nesta tentativa"
    else:
        promotion_note = (
            f"tentativa parcial ({regulatory_scope_label}); endurece a trilha, "
            "mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03"
        )

    return {
        "scope_label": regulatory_scope_label,
        "scope_is_combined": combined_scope,
        "validation_scope": validation_scope,
        "aml_kyt_runtime_status": regulatory_bundle.get("compliance_provider_runtime_status") or "unknown",
        "aml_kyt_runtime_readiness": (readiness.get("compliance_runtime") or {}).get("readiness_status")
        or "unknown",
        "eu_feed_status": regulatory_bundle.get("eu_sanctions_window_status") or "unknown",
        "eu_feed_readiness": (readiness.get("eu_window") or {}).get("readiness_status") or "unknown",
        "p0_04_bundle_readiness": (readiness.get("regulatory_bundle") or {}).get("readiness_status")
        or "unknown",
        "promotion_note": promotion_note,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa prepare+run+validate e gera snapshot consolidado da janela seria."
    )
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--private-env-file", default=".env.staging.private")
    parser.add_argument("--checks-dir", default="artifacts/staging/checks")
    parser.add_argument("--dossiers-dir", default="artifacts/staging/dossiers")
    parser.add_argument("--scope", default="P0-01,P0-02,P0-03")
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--history-dir")
    return parser.parse_args()


def timestamp_slug(value: str) -> str:
    # Exemplo: 2026-07-03T21:45:44.296518+00:00 -> 20260703T214544Z
    safe = value.replace("-", "").replace(":", "")
    if "+" in safe:
        safe = safe.split("+")[0]
    if "." in safe:
        safe = safe.split(".")[0]
    if safe.endswith("T"):
        safe = safe[:-1]
    return f"{safe}Z"


def main() -> int:
    args = parse_args()

    prepare_cmd = [
        "python",
        "scripts/prepare_staging_window.py",
        "--window-id",
        args.window_id,
        "--mode",
        "baseline",
        "--private-env-file",
        args.private_env_file,
        "--validate",
        "--preflight",
    ]
    run_cmd = [
        "python",
        "scripts/run_staging_window.py",
        "--window-id",
        args.window_id,
        "--private-env-file",
        args.private_env_file,
    ]
    validate_cmd = [
        "python",
        "scripts/validate_serious_window_artifact.py",
        "--window-id",
        args.window_id,
        "--checks-dir",
        args.checks_dir,
        "--dossiers-dir",
        args.dossiers_dir,
        "--scope",
        args.scope,
    ]

    prepare_result = run_command(prepare_cmd)
    run_result = run_command(run_cmd)
    validate_result = run_command(validate_cmd)

    blockers = collect_blockers(Path(args.checks_dir), args.window_id)
    operational_incidents = load_operational_alerts_rca_summary(Path(args.checks_dir), args.window_id)

    snapshot = {
        "kind": "staging_window_status_snapshot",
        "generated_at": utc_now_iso(),
        "window_id": args.window_id,
        "overall_status": compute_overall_status(prepare_result, run_result, validate_result),
        "regulatory": build_regulatory_snapshot(run_result, validate_result),
        "operational_incidents": operational_incidents,
        "blockers": blockers,
        "prepare": {
            "exit_code": prepare_result["exit_code"],
            "status": prepare_result.get("payload", {}).get("status")
            or ("ok" if prepare_result["exit_code"] == 0 else "failed"),
            "generated_at": prepare_result.get("payload", {}).get("generated_at"),
        },
        "run": {
            "exit_code": run_result["exit_code"],
            "status": run_result.get("payload", {}).get("status")
            or ("ok" if run_result["exit_code"] == 0 else "failed"),
            "generated_at": run_result.get("payload", {}).get("generated_at"),
            "errors": run_result.get("payload", {}).get("errors", []),
        },
        "artifact_validation": {
            "exit_code": validate_result["exit_code"],
            "status": validate_result.get("payload", {}).get("status")
            or ("ok" if validate_result["exit_code"] == 0 else "failed"),
            "errors": validate_result.get("payload", {}).get("errors", []),
            "missing_artifacts": validate_result.get("payload", {}).get("missing_artifacts", []),
        },
    }

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    history_file: str | None = None
    if args.history_dir:
        history_dir = Path(args.history_dir)
        history_dir.mkdir(parents=True, exist_ok=True)
        suffix = timestamp_slug(str(snapshot["generated_at"]))
        file_name = f"{args.window_id}-status-snapshot-{suffix}.json"
        history_path = history_dir / file_name
        history_path.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        history_file = str(history_path)
        snapshot["history_file"] = history_file
        output_file.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(snapshot, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
