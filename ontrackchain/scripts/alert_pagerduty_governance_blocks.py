#!/usr/bin/env python3
"""
Alert PagerDuty when governance gate blocks deployments.

Sends incidents/alerts to PagerDuty for critical gate blocks.
Integrates with deployment workflows for operational awareness.

Usage:
  python3 alert_pagerduty_governance_blocks.py \
    --consolidated-json docs/governance-weekly/{window_id}-consolidated.json \
    --pagerduty-integration-key YOUR_KEY \
    --severity error|warning \
    --component production \
    --on-block  # Only alert on block
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


def load_consolidated_json(filepath):
    """Load consolidated governance JSON."""
    if not filepath or not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {filepath}: {e}")
        return {}


def extract_gate_details(consolidated):
    """Extract gate decision details from consolidated JSON."""
    governance_state = consolidated.get('governance_state', {})
    return {
        'signal': governance_state.get('signal', 'unknown'),
        'status': governance_state.get('status', 'unknown'),
        'decision': governance_state.get('decision', 'unknown'),
        'blockers': governance_state.get('blockers', {}),
        'blocker_count': sum(
            v if isinstance(v, int) else 0
            for v in (governance_state.get('blockers', {}) or {}).values()
        )
    }


def should_alert(gate_details, on_block=True):
    """Determine if alert should be sent."""
    if on_block:
        # Only alert if status is failed or signal is not verde
        status_failed = gate_details['status'] == 'failed'
        signal_not_allowed = gate_details['signal'] != 'verde'
        return status_failed and signal_not_allowed
    return True


def build_pagerduty_event(consolidated, gate_details, severity='error', component='production'):
    """Build PagerDuty event payload."""
    
    blocker_list = []
    blockers = gate_details.get('blockers', {}) or {}
    for blocker_type, count in blockers.items():
        blocker_list.append(f"- {blocker_type}: {count}")
    
    blocker_text = "\n".join(blocker_list) if blocker_list else "No specific blockers"
    
    summary = f"🔴 Governance Gate Blocked - {component.upper()}"
    
    description = f"""Governance gate evaluation has blocked deployment.

**Signal:** {gate_details['signal']}
**Status:** {gate_details['status']}
**Decision:** {gate_details['decision']}
**Total Blockers:** {gate_details['blocker_count']}

**Blocker Details:**
{blocker_text}

**Severity:** {severity.upper()}
**Component:** {component.upper()}
**Timestamp:** {datetime.now(timezone.utc).isoformat()}
"""
    
    event = {
        "routing_key": None,  # Will be set in send function
        "event_action": "trigger",
        "dedup_key": f"governance-gate-{component}-{int(datetime.now().timestamp())}",
        "payload": {
            "summary": summary,
            "severity": severity,
            "source": component,
            "component": "governance-gate",
            "custom_details": {
                "signal": gate_details['signal'],
                "status": gate_details['status'],
                "decision": gate_details['decision'],
                "blocker_count": gate_details['blocker_count'],
                "blockers": gate_details['blockers'],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        },
        "client": "Governance Automation Framework",
        "client_url": "https://github.com/Jistriane/Ontracktchain"
    }
    
    return event


def send_pagerduty_event(event, integration_key):
    """Send event to PagerDuty Events API v2."""
    
    if not integration_key:
        print("Error: PagerDuty integration key not provided")
        return False
    
    event['routing_key'] = integration_key
    
    url = 'https://events.pagerduty.com/v2/enqueue'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.pagerduty+json;version=2'
    }
    
    payload = json.dumps(event).encode('utf-8')
    
    try:
        request = urllib.request.Request(
            url,
            data=payload,
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(request, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            if response.status == 202:
                print(f"✅ PagerDuty alert sent successfully")
                print(f"   Dedup Key: {event['dedup_key']}")
                print(f"   Response: {response_data.get('status', 'accepted')}")
                return True
            else:
                print(f"Warning: Unexpected response code {response.status}")
                return False
    
    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code}")
        try:
            error_response = json.loads(e.read().decode('utf-8'))
            print(f"   Details: {error_response}")
        except:
            pass
        return False
    
    except urllib.error.URLError as e:
        print(f"Error: Connection failed - {e.reason}")
        return False
    
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Alert PagerDuty on governance gate blocks"
    )
    parser.add_argument('--consolidated-json', required=True,
                        help='Consolidated governance JSON file')
    parser.add_argument('--pagerduty-integration-key', default='',
                        help='PagerDuty Events integration key (or env: PAGERDUTY_INTEGRATION_KEY)')
    parser.add_argument('--severity', default='error', choices=['critical', 'error', 'warning', 'info'],
                        help='Alert severity level')
    parser.add_argument('--component', default='production',
                        help='Component/environment name')
    parser.add_argument('--on-block', action='store_true',
                        help='Only alert if gate is blocked')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print event without sending')
    
    args = parser.parse_args()
    
    # Get integration key from argument or environment
    integration_key = args.pagerduty_integration_key or os.environ.get('PAGERDUTY_INTEGRATION_KEY', '')
    
    # Load consolidated JSON
    consolidated = load_consolidated_json(args.consolidated_json)
    if not consolidated:
        print("❌ No governance data available")
        return 1
    
    # Extract gate details
    gate_details = extract_gate_details(consolidated)
    
    # Check if alert should be sent
    if args.on_block and not should_alert(gate_details, on_block=True):
        print("ℹ️  Gate is healthy - no alert needed")
        return 0
    
    # Build event
    event = build_pagerduty_event(
        consolidated,
        gate_details,
        severity=args.severity,
        component=args.component
    )
    
    # Dry run: print and exit
    if args.dry_run:
        print("📋 PagerDuty Event (Dry-Run):")
        print(json.dumps(event, indent=2))
        return 0
    
    # Send event
    if not integration_key:
        print("⚠️  Warning: PagerDuty integration key not configured")
        print("   Set PAGERDUTY_INTEGRATION_KEY environment variable or use --pagerduty-integration-key")
        print("   Dry-run only:")
        print(json.dumps(event, indent=2))
        return 0
    
    success = send_pagerduty_event(event, integration_key)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
