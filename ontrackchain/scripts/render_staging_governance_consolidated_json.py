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
import sys
from datetime import datetime, timezone
from pathlib import Path


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
    
    # Load JSONs
    current_snapshot = load_json_file(snapshot_file)
    current_snapshot_latest = load_json_file(latest_history)
    previous_snapshot_data = load_json_file(previous_snapshot)
    
    # Load markdown content
    delta_content = extract_markdown_content(delta_file)
    action_plan_content = extract_markdown_content(action_plan_file)
    unblock_checklist_content = extract_markdown_content(unblock_checklist_file)
    comms_summary_content = extract_markdown_content(comms_summary_file)
    executive_bullet_content = extract_markdown_content(executive_bullet_file)
    dashboard_content = extract_markdown_content(dashboard_file)
    status_snapshot_content = extract_markdown_content(status_snapshot_md_file)
    
    # Extract key fields
    executive_bullet = extract_executive_bullet(executive_bullet_content)
    
    # Parse executive bullet for structured fields
    governance_state = {
        "status": "unknown",
        "signal": "unknown",
        "blockers": {"placeholders": 0, "handoff": 0},
        "decision": "unknown"
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
            elif part.startswith('decisao='):
                governance_state['decision'] = part.replace('decisao=', '').strip()
    
    # Parse markdown tables for action items and checklist
    # Note: Current markdown format uses bullets, not tables. Keep arrays for future use.
    action_plan_items = []
    unblock_items = []
    
    # Build consolidated JSON
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
            "unblock_checklist_items": unblock_items
        },
        "communications": {
            "executive_bullet": executive_bullet,
            "comms_summary": {
                "short": comms_summary_content[:500] + "..." if len(comms_summary_content) > 500 else comms_summary_content
            }
        },
        "artefact_files": {
            "war_room_action_plan": action_plan_file if os.path.exists(action_plan_file) else None,
            "status_snapshot": snapshot_file if os.path.exists(snapshot_file) else None,
            "status_snapshot_markdown": status_snapshot_md_file if os.path.exists(status_snapshot_md_file) else None,
            "status_snapshot_delta": delta_file if os.path.exists(delta_file) else None,
            "governance_dashboard": dashboard_file if os.path.exists(dashboard_file) else None,
            "unblock_checklist": unblock_checklist_file if os.path.exists(unblock_checklist_file) else None,
            "comms_summary": comms_summary_file if os.path.exists(comms_summary_file) else None,
            "executive_bullet": executive_bullet_file if os.path.exists(executive_bullet_file) else None
        },
        "metadata": {
            "checks_dir": checks_dir,
            "dossiers_dir": dossiers_dir,
            "docs_dir": docs_dir,
            "previous_snapshot_file": previous_snapshot,
            "current_snapshot_latest_file": latest_history
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
        default='docs/governance-weekly',
        help='Path to the governance artefacts directory for the target window (usually generated/windows/<window_id>)',
    )
    parser.add_argument('--output-file', required=True, help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Build consolidated JSON
    consolidated = build_consolidated_json(
        args.window_id,
        args.checks_dir,
        args.dossiers_dir,
        args.docs_dir
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
