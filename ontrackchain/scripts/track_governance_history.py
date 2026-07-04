#!/usr/bin/env python3
"""
Track historical governance gate decisions.

Aggregates gate decision records and generates metrics/trends.

Usage:
  python3 track_governance_history.py \
    --history-dir artifacts/deployment-history/ \
    --output-file docs/governance-weekly/gate-history-metrics.json \
    --generate-report
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


def _as_bool(value):
    """Normalize bool-like values from JSON records."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == 'true'
    return False


def _is_allowed(decision):
    """Support both legacy `gate_allowed` and new `allowed` fields."""
    if 'gate_allowed' in decision:
        return _as_bool(decision.get('gate_allowed'))
    return _as_bool(decision.get('allowed'))


def _is_overridden(decision):
    """Support override flags stored as bool or string."""
    return _as_bool(decision.get('force_override'))


def load_gate_decisions(history_dir):
    """Load all gate decision files from history directory."""
    decisions = []
    
    if not os.path.exists(history_dir):
        print(f"Warning: History directory not found: {history_dir}")
        return decisions
    
    for filename in sorted(os.listdir(history_dir)):
        if filename.startswith('gate_decision_') and filename.endswith('.json'):
            filepath = os.path.join(history_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    decision = json.load(f)
                    decision['file'] = filename
                    decisions.append(decision)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {filepath}: {e}")
    
    return decisions


def calculate_metrics(decisions):
    """Calculate metrics from gate decisions."""
    if not decisions:
        return {}
    
    total = len(decisions)
    allowed = sum(1 for d in decisions if _is_allowed(d))
    blocked = total - allowed
    overridden = sum(1 for d in decisions if _is_overridden(d))
    
    # Trend analysis (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent = [d for d in decisions if 'timestamp' in d]
    
    # Stats by environment
    by_env = defaultdict(lambda: {'total': 0, 'allowed': 0, 'blocked': 0, 'overridden': 0})
    for d in decisions:
        env = d.get('environment', 'unknown')
        by_env[env]['total'] += 1
        if _is_allowed(d):
            by_env[env]['allowed'] += 1
        else:
            by_env[env]['blocked'] += 1
        if _is_overridden(d):
            by_env[env]['overridden'] += 1
    
    metrics = {
        'total_decisions': total,
        'allowed': allowed,
        'blocked': blocked,
        'allow_rate': round(100 * allowed / total, 2) if total > 0 else 0,
        'block_rate': round(100 * blocked / total, 2) if total > 0 else 0,
        'overridden_count': overridden,
        'override_rate': round(100 * overridden / total, 2) if total > 0 else 0,
        'by_environment': dict(by_env),
        'latest_decision': decisions[-1] if decisions else None,
        'oldest_decision': decisions[0] if decisions else None,
        'generated_at': datetime.now().isoformat()
    }
    
    return metrics


def empty_metrics():
    """Return an empty metrics payload with stable schema."""
    return {
        'total_decisions': 0,
        'allowed': 0,
        'blocked': 0,
        'allow_rate': 0,
        'block_rate': 0,
        'overridden_count': 0,
        'override_rate': 0,
        'by_environment': {},
        'latest_decision': None,
        'oldest_decision': None,
        'generated_at': datetime.now().isoformat(),
    }


def generate_report(metrics, output_file):
    """Generate markdown report from metrics."""
    report = f"""# Governance Gate Historical Report

Generated: {metrics['generated_at']}

## Overall Statistics

| Metric | Value |
|--------|-------|
| **Total Decisions** | {metrics['total_decisions']} |
| **Allowed** | {metrics['allowed']} ({metrics['allow_rate']}%) |
| **Blocked** | {metrics['blocked']} ({metrics['block_rate']}%) |
| **Overridden** | {metrics['overridden_count']} ({metrics['override_rate']}%) |

## By Environment

"""
    
    for env, stats in metrics['by_environment'].items():
        allow_pct = round(100 * stats['allowed'] / stats['total'], 2) if stats['total'] > 0 else 0
        report += f"""### {env.upper()}

| Metric | Value |
|--------|-------|
| Total | {stats['total']} |
| Allowed | {stats['allowed']} ({allow_pct}%) |
| Blocked | {stats['blocked']} |
| Overridden | {stats['overridden']} |

"""
    
    if metrics['latest_decision']:
        report += f"""## Latest Decision

- **Status:** {"✅ ALLOWED" if _is_allowed(metrics['latest_decision']) else "❌ BLOCKED"}
- **Timestamp:** {metrics['latest_decision'].get('timestamp', 'N/A')}
- **Environment:** {metrics['latest_decision'].get('environment', 'N/A')}
- **Actor:** {metrics['latest_decision'].get('github_actor', 'N/A')}

"""
    
    report += """## Trends

- 🟢 **Healthy State:** Allow rate > 80%
- 🟡 **Caution:** Allow rate 50-80%
- 🔴 **Warning:** Allow rate < 50%

## Recommendations

1. Monitor block rate for pattern anomalies
2. Review overridden deployments for compliance
3. Adjust policies if block rate consistently high
4. Celebrate successful automations!
"""
    
    # Save report as markdown
    report_file = output_file.replace('.json', '.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Track governance gate decision history"
    )
    parser.add_argument('--history-dir', default='artifacts/deployment-history',
                        help='Directory containing gate decision files')
    parser.add_argument('--output-file', default='docs/governance-weekly/gate-history-metrics.json',
                        help='Output file for metrics JSON')
    parser.add_argument('--generate-report', action='store_true',
                        help='Also generate markdown report')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit metrics to last N decisions')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # Load decisions
    decisions = load_gate_decisions(args.history_dir)
    
    if not decisions:
        print("No gate decision history found")
        metrics = empty_metrics()

        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

        if args.generate_report:
            generate_report(metrics, args.output_file)

        print(f"✅ Empty metrics saved: {args.output_file}")
        print(json.dumps({"status": "no_history", "decisions": 0, "metrics_file": args.output_file}))
        return 0
    
    print(f"Loaded {len(decisions)} gate decision records")
    
    # Apply limit if specified
    if args.limit:
        decisions = decisions[-args.limit:]
        print(f"Limited to last {args.limit} decisions")
    
    # Calculate metrics
    metrics = calculate_metrics(decisions)
    
    # Save metrics
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✅ Metrics saved: {args.output_file}")
    
    # Generate report if requested
    if args.generate_report:
        generate_report(metrics, args.output_file)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total: {metrics['total_decisions']}")
    print(f"   Allowed: {metrics['allowed']} ({metrics['allow_rate']}%)")
    print(f"   Blocked: {metrics['blocked']} ({metrics['block_rate']}%)")
    print(f"   Overridden: {metrics['overridden_count']} ({metrics['override_rate']}%)")
    
    print(json.dumps({"status": "ok", "metrics_file": args.output_file}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
