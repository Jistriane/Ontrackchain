#!/usr/bin/env python3
"""
Generate governance gate history dashboard.

Visualizes historical gate decisions with trends, statistics, and recommendations.

Usage:
  python3 render_governance_gate_history_dashboard.py \
    --metrics-file docs/governance-weekly/gate-history-metrics.json \
    --output-file docs/governance-weekly/gate-history-dashboard.md \
    --include-trending
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == 'true'
    return False


def _latest_allowed(latest):
    if not isinstance(latest, dict):
        return False
    if 'gate_allowed' in latest:
        return _as_bool(latest.get('gate_allowed'))
    return _as_bool(latest.get('allowed'))


def load_metrics(metrics_file):
    """Load metrics from JSON file."""
    if not os.path.exists(metrics_file):
        print(f"Error: Metrics file not found: {metrics_file}")
        return None
    
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {metrics_file}: {e}")
        return None


def get_health_status(allow_rate):
    """Determine health status based on allow rate."""
    if allow_rate >= 80:
        return "🟢 HEALTHY", "Allow rate above 80%"
    elif allow_rate >= 50:
        return "🟡 CAUTION", "Allow rate 50-80%"
    else:
        return "🔴 WARNING", "Allow rate below 50%"


def get_trend_indicator(metrics):
    """Get trend indicator (improving/stable/degrading)."""
    if not metrics or 'by_environment' not in metrics:
        return "📊 No trend data"
    
    # Simple trend: if overall allow_rate >= 75%, improving
    allow_rate = metrics.get('allow_rate', 0)
    if allow_rate >= 80:
        return "📈 IMPROVING"
    elif allow_rate >= 70:
        return "➡️ STABLE"
    else:
        return "📉 DEGRADING"


def generate_dashboard(metrics, include_trending=False):
    """Generate dashboard markdown."""
    
    if not metrics:
        return "# Governance Gate Dashboard\n\nNo metrics data available.\n"
    
    total_decisions = int(metrics.get('total_decisions', 0) or 0)
    if total_decisions == 0:
        status = "⚪ NO DATA"
        status_msg = "No gate decision history available yet"
        trend = "📊 NO HISTORY"
    else:
        status, status_msg = get_health_status(metrics.get('allow_rate', 0))
        trend = get_trend_indicator(metrics)
    
    dashboard = f"""# Governance Gate Historical Dashboard

**Generated:** {metrics.get('generated_at', 'N/A')}

---

## 🎯 Executive Summary

| Metric | Value |
|--------|-------|
| **Health Status** | {status} |
| **Trend** | {trend} |
| **Allow Rate** | {metrics.get('allow_rate', 0)}% |
| **Total Decisions** | {metrics.get('total_decisions', 0)} |

**Status Message:** {status_msg}

---

## 📊 Overall Statistics

| Category | Count | Percentage |
|----------|-------|-----------|
| ✅ **Allowed** | {metrics.get('allowed', 0)} | {metrics.get('allow_rate', 0)}% |
| ❌ **Blocked** | {metrics.get('blocked', 0)} | {metrics.get('block_rate', 0)}% |
| ⚠️ **Overridden** | {metrics.get('overridden_count', 0)} | {metrics.get('override_rate', 0)}% |
| **Total** | {metrics.get('total_decisions', 0)} | 100% |

---

## 🏢 By Environment

"""
    
    for env, stats in sorted(metrics.get('by_environment', {}).items()):
        allow_pct = round(100 * stats['allowed'] / stats['total'], 2) if stats['total'] > 0 else 0
        env_status = "🟢" if allow_pct >= 80 else ("🟡" if allow_pct >= 50 else "🔴")
        
        dashboard += f"""### {env_status} {env.upper()}

| Metric | Value |
|--------|-------|
| Total Decisions | {stats['total']} |
| ✅ Allowed | {stats['allowed']} ({allow_pct}%) |
| ❌ Blocked | {stats['blocked']} |
| ⚠️ Overridden | {stats['overridden']} |

"""
    
    # Add latest decision
    latest = metrics.get('latest_decision')
    if latest:
        dashboard += f"""---

## 📌 Latest Decision

- **Decision ID:** {latest.get('workflow_run_id', 'N/A')}
- **Timestamp:** {latest.get('timestamp', 'N/A')}
- **Status:** {"✅ ALLOWED" if _latest_allowed(latest) else "❌ BLOCKED"}
- **Environment:** {latest.get('environment', 'N/A')}
- **Actor:** @{latest.get('github_actor', 'unknown')}
- **Commit:** `{latest.get('commit_sha', 'N/A')[:8]}...`
- **Override:** {"⚠️ YES" if _as_bool(latest.get('force_override')) else "❌ No"}

"""
    
    # Add recommendations
    dashboard += """---

## 💡 Recommendations

### Based on Current Metrics

"""
    
    allow_rate = metrics.get('allow_rate', 0)
    override_rate = metrics.get('override_rate', 0)
    
    if total_decisions == 0:
        dashboard += """- ⚪ **No historical decisions yet** - Run one governed deployment to start trend tracking
- 🧪 **Bootstrap recommended** - Record at least one `gate_decision_*.json` to enable meaningful metrics
- 📚 **Keep automation running** - Scheduled collection is healthy; data will populate automatically
"""
    elif allow_rate >= 80:
        dashboard += """- ✅ **Governance policies are healthy** - Low block rate indicates policies are well-calibrated
- 📈 **Continue monitoring** - Maintain current policy settings
- ✨ **Consider tightening** - If willing to accept more blocks for safety
"""
    elif allow_rate >= 50:
        dashboard += """- 🟡 **Review blocking policies** - Some deployments consistently blocked
- 🔍 **Investigate blockers** - Identify root causes of blocks
- ⚖️ **Policy adjustment** - Consider if current thresholds are appropriate
"""
    else:
        dashboard += """- 🔴 **CRITICAL - Review governance policies** - High block rate may indicate misconfiguration
- 🚨 **Immediate action required** - Investigate why most deployments are blocked
- 📋 **Check gate logic** - Verify policy rules and thresholds
"""
    
    if override_rate > 20:
        dashboard += """
- ⚠️ **High override rate** - Many deployments forcing through governance gates
- 📝 **Audit overrides** - Review override reasons and justifications
- 🔒 **Strengthen policies** - Consider if overrides indicate weak gate logic
"""
    
    dashboard += f"""
### General Best Practices

1. **Monitor Regularly** - Review dashboard weekly
2. **Track Trends** - Look for patterns over time
3. **Audit Overrides** - Every override should have documented justification
4. **Iterate Policies** - Adjust gate thresholds based on real data
5. **Communicate** - Share metrics with team for transparency

---

## 📈 Interpretation Guide

### Allow Rate Zones

| Zone | Rate | Meaning | Action |
|------|------|---------|--------|
| 🟢 Healthy | ≥ 80% | Policies working well | Monitor & maintain |
| 🟡 Caution | 50-80% | Some friction | Review blockers |
| 🔴 Warning | < 50% | High friction | Immediate review |

### Override Rate Implications

- **0-5%:** Excellent - Gates working as intended
- **5-20%:** Acceptable - Occasional need for overrides
- **> 20%:** Concern - Consider policy adjustments

---

## 🔄 Historical Trend

Older data not available. Dashboard will show trends after multiple days of operation.

---

## 📋 Next Steps

1. **Setup Slack Alerts** - Get notified on policy changes
2. **Integrate with PagerDuty** - Critical blocks escalation
3. **Generate Weekly Reports** - Automated governance metrics
4. **Create Archive** - Store historical data for compliance
5. **Share Metrics** - Team dashboards and visibility

---

**Last Updated:** {datetime.now().isoformat()}
"""
    
    return dashboard


def main():
    parser = argparse.ArgumentParser(
        description="Generate governance gate history dashboard"
    )
    parser.add_argument('--metrics-file', default='docs/governance-weekly/gate-history-metrics.json',
                        help='Input metrics JSON file')
    parser.add_argument('--output-file', default='docs/governance-weekly/gate-history-dashboard.md',
                        help='Output dashboard markdown file')
    parser.add_argument('--include-trending', action='store_true',
                        help='Include trending analysis')
    
    args = parser.parse_args()
    
    # Load metrics
    metrics = load_metrics(args.metrics_file)
    
    if not metrics:
        print("❌ Error loading metrics")
        return 1
    
    # Generate dashboard
    dashboard = generate_dashboard(metrics, args.include_trending)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # Save dashboard
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(dashboard)
    
    print(f"✅ Dashboard generated: {args.output_file}")
    total_decisions = int(metrics.get('total_decisions', 0) or 0)
    allow_rate = metrics.get('allow_rate', 0)
    if total_decisions == 0:
        health = "no_data"
    elif allow_rate >= 80:
        health = "healthy"
    elif allow_rate >= 50:
        health = "caution"
    else:
        health = "warning"

    print(json.dumps({
        "status": "ok",
        "dashboard_file": args.output_file,
        "total_decisions": metrics.get('total_decisions', 0),
        "allow_rate": allow_rate,
        "health": health
    }))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
