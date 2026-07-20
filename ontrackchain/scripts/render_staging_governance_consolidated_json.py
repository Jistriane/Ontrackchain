#!/usr/bin/env python3
"""
Consolidated governance JSON aggregator.

Reads all 7 generated markdown artefacts and the snapshot/delta JSON files,
consolidates them into a single machine-readable JSON for downstream integration
(dashboards, CI/CD gates, Slack bots, etc.).

Usage:
  python3 render_staging_governance_consolidated_json.py \
    --window-id stg-2026-07-06-a \
    --checks-dir artifacts/staging/checks \
    --dossiers-dir artifacts/staging/dossiers \
    --docs-dir docs/governance-weekly/generated/windows/stg-2026-07-06-a \
    --output-file docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-consolidated.json
"""

import argparse
import json
import os
from datetime import datetime, timezone


def load_json_file(path):
    """Load JSON file, return dict or empty dict if not found."""
    if path is None or not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def extract_markdown_content(path, delimiter=None):
    """Extract text content from markdown file."""
    if path is None or not os.path.exists(path):
        return ""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if delimiter:
                # Return content between first and second occurrence of delimiter
                parts = content.split(delimiter)
                if len(parts) >= 2:
                    return parts[1].strip()
            return content
    except IOError:
        return ""


def parse_markdown_table(content):
    """Parse markdown table into list of dicts."""
    lines = content.strip().split('\n')
    if len(lines) < 3:
        return []
    
    # Parse header
    header_line = lines[0].strip()
    if not header_line.startswith('|'):
        return []
    
    headers = [h.strip() for h in header_line.split('|')[1:-1]]
    
    # Skip separator line (lines[1])
    
    # Parse rows
    rows = []
    for line in lines[2:]:
        if not line.strip() or not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    
    return rows


def extract_executive_bullet(content):
    """Extract one-line executive summary from markdown."""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and 'Ontrackchain' in line:
            return line
    return ""


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def regulatory_summary(snapshot):
    """Extract normalized regulatory summary from snapshot."""
    regulatory = snapshot.get("regulatory") if isinstance(snapshot, dict) else {}
    if not isinstance(regulatory, dict):
        regulatory = {}
    return {
        "scope_label": str(regulatory.get("scope_label") or "none"),
        "validation_scope": regulatory.get("validation_scope") or [],
        "p0_04_bundle_readiness": str(regulatory.get("p0_04_bundle_readiness") or "unknown"),
        "promotion_note": str(regulatory.get("promotion_note") or "indisponivel"),
    }


def blocking_summary(snapshot):
    """Extract normalized blocking classification from snapshot."""
    blocking = snapshot.get("blocking_state") if isinstance(snapshot, dict) else {}
    if not isinstance(blocking, dict):
        blocking = {}
    return {
        "classification": str(blocking.get("classification") or "unknown"),
        "summary": str(blocking.get("summary") or "indisponivel"),
    }


def operational_summary(snapshot):
    operational = snapshot.get("operational_incidents") if isinstance(snapshot, dict) else {}
    if not isinstance(operational, dict):
        operational = {}
    return {
        "status": str(operational.get("status") or "not_available"),
        "exported_count": int(operational.get("exported_count") or 0),
        "tracked_work_items_count": int(operational.get("tracked_work_items_count") or 0),
        "rca_attached_count": int(operational.get("rca_attached_count") or 0),
        "confirmed_root_cause_count": int(operational.get("confirmed_root_cause_count") or 0),
        "critical_open_count": int(operational.get("critical_open_count") or 0),
        "pending_triage_count": int(operational.get("pending_triage_count") or 0),
        "top_rca_domains": operational.get("top_rca_domains") or [],
        "top_affected_domains": operational.get("top_affected_domains") or [],
    }


def regulatory_unblock_summary(payload):
    if not isinstance(payload, dict):
        payload = {}
    summary = payload.get("summary") or {}
    return {
        "status": str(payload.get("status") or "unknown"),
        "blocking_classification": str(payload.get("blocking_classification") or "unknown"),
        "blocked_scopes": summary.get("blocked_scopes") or [],
        "owner_action_groups_count": int(summary.get("owner_action_groups_count") or 0),
        "dominant_blocking_summary": str(summary.get("dominant_blocking_summary") or "indisponivel"),
    }


def find_latest_history_file(checks_dir, window_id):
    """Find the latest status snapshot in history dir."""
    history_dir = os.path.join(checks_dir, 'history')
    if not os.path.exists(history_dir):
        return None
    
    files = [f for f in os.listdir(history_dir) 
             if f.startswith(window_id) and f.endswith('.json')]
    if not files:
        return None
    
    # Sort by modification time, return latest
    files.sort(key=lambda f: os.path.getmtime(os.path.join(history_dir, f)), reverse=True)
    return os.path.join(history_dir, files[0])


def find_previous_snapshot(checks_dir, current_window_id):
    """Find the snapshot file immediately before current window."""
    history_dir = os.path.join(checks_dir, 'history')
    if not os.path.exists(history_dir):
        return None
    
    files = sorted([f for f in os.listdir(history_dir) 
                   if f.endswith('.json')])
    
    # Find current window index, return previous if exists
    current_idx = None
    for i, f in enumerate(files):
        if current_window_id in f:
            current_idx = i
            break
    
    if current_idx is not None and current_idx > 0:
        prev_file = files[current_idx - 1]
        return os.path.join(history_dir, prev_file)
    
    return None


def build_consolidated_json(window_id, checks_dir, dossiers_dir, docs_dir):
    """Build consolidated governance JSON."""
    
    # Paths
    snapshot_file = os.path.join(checks_dir, f'{window_id}-status-snapshot.json')
    latest_history = find_latest_history_file(checks_dir, window_id)
    previous_snapshot = find_previous_snapshot(checks_dir, window_id)
    
    delta_file = os.path.join(docs_dir, f'{window_id}-status-snapshot-delta.md')
    action_plan_file = os.path.join(docs_dir, f'{window_id}-war-room-action-plan.md')
    unblock_checklist_file = os.path.join(docs_dir, f'{window_id}-unblock-checklist.md')
    comms_summary_file = os.path.join(docs_dir, f'{window_id}-comms-summary.md')
    executive_bullet_file = os.path.join(docs_dir, f'{window_id}-executive-bullet.md')
    dashboard_file = os.path.join(docs_dir, f'{window_id}-governance-dashboard.md')
    status_snapshot_md_file = os.path.join(docs_dir, f'{window_id}-status-snapshot.md')
    regulatory_unblock_file = os.path.join(checks_dir, f'{window_id}-regulatory-unblock-checklist.json')
    regulatory_unblock_summary_file = os.path.join(dossiers_dir, f'{window_id}-regulatory-unblock-checklist.md')
    
    # Load JSONs
    current_snapshot = load_json_file(snapshot_file)
    current_snapshot_latest = load_json_file(latest_history)
    previous_snapshot_data = load_json_file(previous_snapshot)
    regulatory_unblock_payload = load_json_file(regulatory_unblock_file)
    
    # Load markdown content
    comms_summary_content = extract_markdown_content(comms_summary_file)
    executive_bullet_content = extract_markdown_content(executive_bullet_file)
    
    # Extract key fields
    executive_bullet = extract_executive_bullet(executive_bullet_content)
    
    # Parse executive bullet for structured fields
    governance_state = {
        "status": "unknown",
        "signal": "unknown",
        "blockers": {"placeholders": 0, "handoff": 0},
        "decision": "unknown",
        "regulatory": {
            "scope_label": "none",
            "p0_04_bundle_readiness": "unknown",
        },
        "blocking": {
            "classification": "unknown",
            "summary": "indisponivel",
        },
        "operational": {
            "status": "not_available",
            "rca_attached_count": 0,
            "critical_open_count": 0,
        },
    }
    
    if 'status=' in executive_bullet:
        # Parse: status=<status>, semaforo=<signal>, bloqueios=<placeholders> placeholders/<handoff> handoff, decisao=<decision>
        parts = executive_bullet.split('|')
        for part in parts:
            part = part.strip()
            if part.startswith('status='):
                governance_state['status'] = part.replace('status=', '').strip()
            elif part.startswith('semaforo='):
                governance_state['signal'] = part.replace('semaforo=', '').strip()
            elif part.startswith('bloqueios='):
                blocker_str = part.replace('bloqueios=', '').strip()
                # Parse: "12 placeholders/8 handoff"
                if 'placeholders' in blocker_str:
                    ph_part = blocker_str.split('placeholders')[0].strip()
                    hf_part = blocker_str.split('/')[1].split('handoff')[0].strip()
                    try:
                        governance_state['blockers']['placeholders'] = int(ph_part)
                        governance_state['blockers']['handoff'] = int(hf_part)
                    except ValueError:
                        pass
            elif part.startswith('escopo_regulatorio='):
                governance_state['regulatory']['scope_label'] = part.replace('escopo_regulatorio=', '').strip()
            elif part.startswith('p0_04='):
                governance_state['regulatory']['p0_04_bundle_readiness'] = part.replace('p0_04=', '').strip()
            elif part.startswith('classificacao='):
                governance_state['blocking']['classification'] = part.replace('classificacao=', '').strip()
            elif part.startswith('rca='):
                governance_state['operational']['rca_attached_count'] = _safe_int(part.replace('rca=', '').strip())
            elif part.startswith('criticos_abertos='):
                governance_state['operational']['critical_open_count'] = _safe_int(part.replace('criticos_abertos=', '').strip())
            elif part.startswith('decisao='):
                governance_state['decision'] = part.replace('decisao=', '').strip()
    
    # Parse markdown tables for action items and checklist
    # Note: Current markdown format uses bullets, not tables. Keep arrays for future use.
    action_plan_items = []
    unblock_items = []
    
    # Build consolidated JSON
    current_regulatory = regulatory_summary(current_snapshot if current_snapshot else {})
    previous_regulatory = regulatory_summary(previous_snapshot_data if previous_snapshot_data else {})
    current_blocking = blocking_summary(current_snapshot if current_snapshot else {})
    previous_blocking = blocking_summary(previous_snapshot_data if previous_snapshot_data else {})
    current_operational = operational_summary(current_snapshot if current_snapshot else {})
    previous_operational = operational_summary(previous_snapshot_data if previous_snapshot_data else {})
    current_regulatory_unblock = regulatory_unblock_summary(regulatory_unblock_payload)
    if governance_state["blocking"]["classification"] == "unknown":
        governance_state["blocking"] = current_blocking
    elif governance_state["blocking"]["summary"] == "indisponivel":
        governance_state["blocking"]["summary"] = current_blocking["summary"]
    consolidated = {
        "window_id": window_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "governance_state": governance_state,
        "snapshots": {
            "current": current_snapshot if current_snapshot else {},
            "current_latest_from_history": current_snapshot_latest if current_snapshot_latest else {},
            "previous": previous_snapshot_data if previous_snapshot_data else {}
        },
        "parsed_content": {
            "action_plan_items": action_plan_items,
            "unblock_checklist_items": unblock_items,
            "regulatory_unblock_owner_actions": (
                (regulatory_unblock_payload.get("owner_actions") or [])
                if isinstance(regulatory_unblock_payload, dict)
                else []
            ),
        },
        "communications": {
            "executive_bullet": executive_bullet,
            "comms_summary": {
                "short": comms_summary_content[:500] + "..." if len(comms_summary_content) > 500 else comms_summary_content
            }
        },
        "regulatory_summary": {
            "current": current_regulatory,
            "previous": previous_regulatory,
        },
        "blocking_summary": {
            "current": current_blocking,
            "previous": previous_blocking,
        },
        "operational_summary": {
            "current": current_operational,
            "previous": previous_operational,
        },
        "regulatory_unblock_summary": current_regulatory_unblock,
        "artefact_files": {
            "war_room_action_plan": action_plan_file if os.path.exists(action_plan_file) else None,
            "status_snapshot": snapshot_file if os.path.exists(snapshot_file) else None,
            "status_snapshot_markdown": status_snapshot_md_file if os.path.exists(status_snapshot_md_file) else None,
            "status_snapshot_delta": delta_file if os.path.exists(delta_file) else None,
            "governance_dashboard": dashboard_file if os.path.exists(dashboard_file) else None,
            "unblock_checklist": unblock_checklist_file if os.path.exists(unblock_checklist_file) else None,
            "regulatory_unblock_checklist": regulatory_unblock_file if os.path.exists(regulatory_unblock_file) else None,
            "regulatory_unblock_checklist_summary": (
                regulatory_unblock_summary_file if os.path.exists(regulatory_unblock_summary_file) else None
            ),
            "comms_summary": comms_summary_file if os.path.exists(comms_summary_file) else None,
            "executive_bullet": executive_bullet_file if os.path.exists(executive_bullet_file) else None
        },
        "metadata": {
            "checks_dir": checks_dir,
            "dossiers_dir": dossiers_dir,
            "docs_dir": docs_dir,
            "previous_snapshot_file": previous_snapshot,
            "current_snapshot_latest_file": latest_history,
            "regulatory_unblock_file": regulatory_unblock_file if os.path.exists(regulatory_unblock_file) else None,
        }
    }
    
    return consolidated


def main():
    parser = argparse.ArgumentParser(
        description="Render consolidated governance JSON from markdown and JSON artefacts"
    )
    parser.add_argument('--window-id', required=True, help='Staging window ID (e.g., stg-2026-07-06-a)')
    parser.add_argument('--checks-dir', default='artifacts/staging/checks', help='Path to checks directory')
    parser.add_argument('--dossiers-dir', default='artifacts/staging/dossiers', help='Path to dossiers directory')
    parser.add_argument(
        '--docs-dir',
        default=None,
        help='Path to the governance artefacts directory for the target window (usually generated/windows/<window_id>)',
    )
    parser.add_argument('--output-file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Build consolidated JSON
    docs_dir = args.docs_dir or f'docs/governance-weekly/generated/windows/{args.window_id}'

    consolidated = build_consolidated_json(
        args.window_id,
        args.checks_dir,
        args.dossiers_dir,
        docs_dir
    )
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)
    
    print(json.dumps({"status": "ok", "output_file": args.output_file}))


if __name__ == '__main__':
    main()
