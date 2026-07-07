#!/usr/bin/env python3
"""
Slack webhook notification for governance updates.

Sends consolidated governance state to Slack with rich formatting.

Usage:
  python3 notify_slack_governance.py \
    --consolidated-json docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-consolidated.json \
    --webhook-url https://hooks.slack.com/services/... \
    [--channel governance] \
    [--mention-on-red true]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


def load_consolidated_json(path):
    """Load consolidated governance JSON."""
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON: {e}")
        return None


def semaforo_to_emoji(signal):
    """Map semaforo signal to emoji."""
    signal_map = {
        "verde": "🟢",
        "amarelo": "🟡",
        "vermelho": "🔴",
    }
    return signal_map.get(signal, "⚪")


def build_slack_message(consolidated, channel="governance", mention_on_red=False):
    """Build rich Slack message from consolidated governance JSON."""
    
    gov_state = consolidated.get("governance_state", {})
    status = gov_state.get("status", "unknown")
    signal = gov_state.get("signal", "unknown")
    decision = gov_state.get("decision", "unknown")
    blockers = gov_state.get("blockers", {})
    window_id = consolidated.get("window_id", "unknown")
    
    # Build color based on signal
    color_map = {
        "verde": "#28a745",
        "amarelo": "#ffc107",
        "vermelho": "#dc3545",
    }
    color = color_map.get(signal, "#999999")
    
    # Build emoji
    emoji = semaforo_to_emoji(signal)
    
    # Build decision text with formatting
    decision_text = decision.replace("_", " ").upper()
    decision_prefix = "✅" if decision == "recomendado_go" else "🛑" if decision == "recomendado_no_go" else "⚠️"
    
    # Build slack message
    message = {
        "channel": f"#{channel}",
        "username": "Ontrackchain Governance",
        "icon_emoji": ":bar_chart:",
        "attachments": [
            {
                "fallback": f"Ontrackchain | {window_id} | {status} | {signal}",
                "color": color,
                "title": f"{emoji} Ontrackchain Governance Update",
                "fields": [
                    {
                        "title": "Window ID",
                        "value": window_id,
                        "short": True
                    },
                    {
                        "title": "Status",
                        "value": status.upper(),
                        "short": True
                    },
                    {
                        "title": "Signal",
                        "value": f"{emoji} {signal.upper()}",
                        "short": True
                    },
                    {
                        "title": "Decision",
                        "value": f"{decision_prefix} {decision_text}",
                        "short": True
                    },
                    {
                        "title": "Placeholders",
                        "value": str(blockers.get("placeholders", 0)),
                        "short": True
                    },
                    {
                        "title": "Handoff Fields",
                        "value": str(blockers.get("handoff", 0)),
                        "short": True
                    }
                ],
                "text": f"*Governance State*\n" +
                        f"Generated: {consolidated.get('generated_at', 'unknown')}\n" +
                        f"Decision: *{decision_text}*",
                "ts": int(datetime.now().timestamp())
            }
        ]
    }
    
    # Add mention on red signal
    if signal == "vermelho" and mention_on_red:
        message["attachments"][0]["pretext"] = "🚨 <!channel> Critical governance state!"
    
    # Add artefact files as context
    artefact_files = consolidated.get("artefact_files", {})
    if artefact_files:
        artefacts_text = "*Generated Artefacts*:\n"
        for name, path in artefact_files.items():
            if path:
                # Format name nicely
                pretty_name = name.replace("_", " ").title()
                artefacts_text += f"• {pretty_name}\n"
        
        if len(artefacts_text) > len("*Generated Artefacts*:\n"):
            message["attachments"][0]["fields"].append({
                "title": "Artefacts",
                "value": artefacts_text.strip(),
                "short": False
            })
    
    return message


def send_slack_webhook(message, webhook_url):
    """Send message to Slack via webhook."""
    if not webhook_url:
        print("Error: SLACK_WEBHOOK_URL not provided")
        return False
    
    try:
        json_data = json.dumps(message).encode('utf-8')
        req = Request(
            webhook_url,
            data=json_data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urlopen(req) as response:
            result = response.read().decode('utf-8')
            if result == "ok":
                print(json.dumps({"status": "ok", "platform": "slack", "webhook": webhook_url[:30] + "..."}))
                return True
            else:
                print(f"Error: Slack returned {result}")
                return False
    except URLError as e:
        print(f"Error sending to Slack: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Send governance update to Slack"
    )
    parser.add_argument('--consolidated-json', required=True, help='Path to consolidated JSON')
    parser.add_argument('--webhook-url', help='Slack webhook URL (or set SLACK_WEBHOOK_URL env var)')
    parser.add_argument('--channel', default='governance', help='Slack channel name (without #)')
    parser.add_argument('--mention-on-red', action='store_true', help='Mention @channel on red signal')
    parser.add_argument('--dry-run', action='store_true', help='Print message without sending')
    
    args = parser.parse_args()
    
    # Load consolidated JSON
    consolidated = load_consolidated_json(args.consolidated_json)
    if not consolidated:
        sys.exit(1)
    
    # Build Slack message
    message = build_slack_message(
        consolidated,
        channel=args.channel,
        mention_on_red=args.mention_on_red
    )
    
    if args.dry_run:
        print("DRY RUN - Message that would be sent:")
        print(json.dumps(message, indent=2))
        return
    
    # Get webhook URL from args or env
    webhook_url = args.webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
    
    # Send to Slack
    success = send_slack_webhook(message, webhook_url)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
