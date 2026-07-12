#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _top_labels(counter: Counter[str], *, limit: int = 3) -> list[str]:
    return [name for name, _ in counter.most_common(limit) if name]


def build_summary(*, window_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    rows = _normalize_items(payload)
    status_counter: Counter[str] = Counter()
    triage_counter: Counter[str] = Counter()
    containment_counter: Counter[str] = Counter()
    domain_counter: Counter[str] = Counter()
    affected_domain_counter: Counter[str] = Counter()
    critical_open = 0
    tracked_work_items = 0
    rca_attached = 0
    confirmed_root_cause = 0

    for row in rows:
        status = str(row.get("status") or "unknown")
        triage = str(row.get("triage_status") or "unknown")
        severity = str(row.get("severity") or "").lower()
        status_counter[status] += 1
        triage_counter[triage] += 1

        if status == "firing" and severity == "critical":
            critical_open += 1

        if row.get("work_item_id"):
            tracked_work_items += 1

        containment = str(row.get("rca_containment_status") or "").strip()
        if containment:
            containment_counter[containment] += 1

        domain = str(row.get("rca_domain") or "").strip()
        if domain:
            domain_counter[domain] += 1

        affected_domains = row.get("rca_affected_domains") or []
        if isinstance(affected_domains, list):
            for affected in affected_domains:
                if isinstance(affected, str) and affected.strip():
                    affected_domain_counter[affected.strip()] += 1

        has_rca = any(
            row.get(key)
            for key in (
                "rca_domain",
                "rca_containment_status",
                "rca_incident_commander",
                "rca_impact_summary",
                "rca_suspected_root_cause",
                "rca_confirmed_root_cause",
            )
        ) or bool(row.get("rca_affected_domains")) or bool(row.get("rca_corrective_actions")) or bool(row.get("rca_evidence_refs"))
        if has_rca:
            rca_attached += 1

        if row.get("rca_confirmed_root_cause"):
            confirmed_root_cause += 1

    return {
        "kind": "operational_alerts_rca_summary",
        "window_id": window_id,
        "exported_count": len(rows),
        "tracked_work_items_count": tracked_work_items,
        "rca_attached_count": rca_attached,
        "confirmed_root_cause_count": confirmed_root_cause,
        "firing_count": status_counter.get("firing", 0),
        "critical_open_count": critical_open,
        "pending_triage_count": triage_counter.get("pending", 0),
        "acknowledged_count": triage_counter.get("acknowledged", 0),
        "containment_status_counts": dict(containment_counter),
        "top_rca_domains": _top_labels(domain_counter),
        "top_affected_domains": _top_labels(affected_domain_counter),
        "ready_queue_count": sum(
            1 for row in rows if str(row.get("work_item_queue_status") or "").upper() == "READY"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera resumo canônico de RCA a partir do export JSON de incidentes operacionais.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_file = Path(args.input_file)
    output_file = Path(args.output_file)
    payload = load_json(input_file)
    summary = build_summary(window_id=args.window_id, payload=payload)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(summary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output_file": str(output_file), "window_id": args.window_id}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
