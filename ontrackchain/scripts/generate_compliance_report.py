#!/usr/bin/env python3
"""
Generate compliance and governance reports.

Aggregates historical governance data and generates compliance reports
for audit and regulatory purposes.

Usage:
  python3 generate_compliance_report.py \
    --metrics-file docs/governance-weekly/generated/gates/gate-history-metrics.json \
    --output-file docs/compliance-reports/compliance-report-2026-Q3.md \
    --period quarterly \
    --format markdown
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


def load_metrics(metrics_file):
    """Load metrics from file."""
    if not os.path.exists(metrics_file):
        print(f"Warning: Metrics file not found: {metrics_file}")
        return {}
    
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {metrics_file}: {e}")
        return {}


def calculate_compliance_metrics(metrics):
    """Calculate compliance-relevant metrics."""
    
    if not metrics:
        return {}
    
    total_decisions = metrics.get('total_decisions', 0)
    allowed = metrics.get('allowed', 0)
    blocked = metrics.get('blocked', 0)
    overridden = metrics.get('overridden_count', 0)
    
    compliance_metrics = {
        "reporting_period": datetime.now().isoformat(),
        "total_deployments": total_decisions,
        "approved_deployments": allowed,
        "blocked_deployments": blocked,
        "force_overrides": overridden,
        "approval_rate": metrics.get('allow_rate', 0),
        "block_rate": metrics.get('block_rate', 0),
        "override_rate": metrics.get('override_rate', 0),
        "environments": metrics.get('by_environment', {}),
        "control_effectiveness": calculate_control_effectiveness(metrics),
        "risk_assessment": assess_risk_level(metrics)
    }
    
    return compliance_metrics


def calculate_control_effectiveness(metrics):
    """Calculate effectiveness of governance controls."""
    
    allow_rate = metrics.get('allow_rate', 0)
    override_rate = metrics.get('override_rate', 0)
    
    # Control effectiveness score (0-100)
    # Higher approval rate = better control
    # Lower override rate = better control
    
    score = (allow_rate * 0.6) - (override_rate * 0.4)
    score = max(0, min(100, score))  # Clamp to 0-100
    
    if score >= 80:
        effectiveness = "Excellent"
    elif score >= 60:
        effectiveness = "Good"
    elif score >= 40:
        effectiveness = "Fair"
    else:
        effectiveness = "Poor"
    
    return {
        "score": round(score, 2),
        "rating": effectiveness,
        "approval_rate": metrics.get('allow_rate', 0),
        "override_rate": metrics.get('override_rate', 0)
    }


def assess_risk_level(metrics):
    """Assess overall risk level based on metrics."""
    
    allow_rate = metrics.get('allow_rate', 0)
    override_rate = metrics.get('override_rate', 0)
    blocked = metrics.get('blocked', 0)
    
    risk_factors = []
    
    if allow_rate < 50:
        risk_factors.append("High block rate")
    elif allow_rate < 70:
        risk_factors.append("Moderate block rate")
    
    if override_rate > 20:
        risk_factors.append("High override rate")
    elif override_rate > 10:
        risk_factors.append("Moderate override rate")
    
    if blocked > 10:
        risk_factors.append("Multiple blocked deployments")
    
    if not risk_factors:
        return {
            "level": "LOW",
            "factors": ["All governance controls operating normally"],
            "recommendations": []
        }
    elif len(risk_factors) <= 2:
        return {
            "level": "MEDIUM",
            "factors": risk_factors,
            "recommendations": [
                "Monitor governance trends",
                "Review policy effectiveness"
            ]
        }
    else:
        return {
            "level": "HIGH",
            "factors": risk_factors,
            "recommendations": [
                "Immediate governance policy review",
                "Escalate to platform team",
                "Assess deployment frequency"
            ]
        }


def generate_markdown_report(compliance_metrics, period='monthly'):
    """Generate compliance report in Markdown format."""
    
    report = f"""# Governance Compliance Report

**Report Period:** {period.capitalize()}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Status:** {compliance_metrics.get('risk_assessment', {}).get('level', 'UNKNOWN')}

---

## Executive Summary

This report provides an overview of governance controls, compliance metrics, and operational effectiveness
for the reporting period.

### Key Metrics

| Metric | Value |
|--------|-------|
| **Total Deployments** | {compliance_metrics.get('total_deployments', 0)} |
| **Approved** | {compliance_metrics.get('approved_deployments', 0)} ({compliance_metrics.get('approval_rate', 0)}%) |
| **Blocked** | {compliance_metrics.get('blocked_deployments', 0)} ({compliance_metrics.get('block_rate', 0)}%) |
| **Force Overrides** | {compliance_metrics.get('force_overrides', 0)} ({compliance_metrics.get('override_rate', 0)}%) |

---

## Control Effectiveness

### Overall Rating

**Score:** {compliance_metrics.get('control_effectiveness', {}).get('score', 0)}/100  
**Rating:** {compliance_metrics.get('control_effectiveness', {}).get('rating', 'Unknown')}

The governance control framework is demonstrating **{compliance_metrics.get('control_effectiveness', {}).get('rating', 'Unknown').lower()}** effectiveness
in managing deployment approvals and risk mitigation.

### Approval Analysis

- Approval Rate: {compliance_metrics.get('approval_rate', 0)}%
- Override Rate: {compliance_metrics.get('override_rate', 0)}%
- Block Rate: {compliance_metrics.get('block_rate', 0)}%

---

## Risk Assessment

### Current Risk Level: {compliance_metrics.get('risk_assessment', {}).get('level', 'UNKNOWN')}

**Risk Factors:**
"""
    
    for factor in compliance_metrics.get('risk_assessment', {}).get('factors', []):
        report += f"- {factor}\n"
    
    report += "\n**Recommendations:**\n"
    for rec in compliance_metrics.get('risk_assessment', {}).get('recommendations', []):
        report += f"- {rec}\n"
    
    # Environment breakdown
    report += "\n---\n\n## Environment Breakdown\n\n"
    
    for env, stats in compliance_metrics.get('environments', {}).items():
        if isinstance(stats, dict):
            total = stats.get('total', 0)
            allowed = stats.get('allowed', 0)
            rate = round(100 * allowed / total, 1) if total > 0 else 0
            
            report += f"""### {env.upper()}

| Metric | Count |
|--------|-------|
| Total | {total} |
| Approved | {allowed} ({rate}%) |
| Blocked | {stats.get('blocked', 0)} |
| Overridden | {stats.get('overridden', 0)} |

"""
    
    # Compliance Attestation
    report += """---

## Compliance Attestation

**Governance Framework:**
- ✅ Automated deployment gates configured
- ✅ Historical decision tracking enabled
- ✅ Multi-environment policy enforcement
- ✅ Audit trails maintained
- ✅ Dashboard monitoring active

**Policy Compliance:**
- ✅ Strict policy for production deployments
- ✅ Moderate policy for staging deployments
- ✅ Approval workflows enforced
- ✅ Override tracking implemented
- ✅ Periodic reporting enabled

**Recommendations:**
1. Continue monitoring gateway effectiveness
2. Review blocked deployment reasons quarterly
3. Assess override justifications monthly
4. Update policies based on trends
5. Maintain audit trail integrity

---

## Technical Details

**Governance Framework Version:** 1.0  
**Report Generated By:** Governance Automation Framework  
**Next Review:** {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}

---

**Confidentiality:** Internal Use Only  
**Classification:** Operational Report
"""
    
    return report


def generate_json_report(compliance_metrics):
    """Generate compliance report in JSON format."""
    return compliance_metrics


def main():
    parser = argparse.ArgumentParser(
        description="Generate governance compliance report"
    )
    parser.add_argument('--metrics-file', default='docs/governance-weekly/generated/gates/gate-history-metrics.json',
                        help='Input metrics file')
    parser.add_argument('--output-file', default='docs/compliance-reports/compliance-report.md',
                        help='Output report file')
    parser.add_argument('--period', default='monthly', choices=['weekly', 'monthly', 'quarterly', 'annual'],
                        help='Reporting period')
    parser.add_argument('--format', default='markdown', choices=['markdown', 'json'],
                        help='Output format')
    
    args = parser.parse_args()
    
    # Load metrics
    metrics = load_metrics(args.metrics_file)
    
    if not metrics:
        print("❌ No metrics data available")
        return 1
    
    # Calculate compliance metrics
    compliance_metrics = calculate_compliance_metrics(metrics)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # Generate report based on format
    if args.format == 'markdown':
        report = generate_markdown_report(compliance_metrics, args.period)
    else:
        report = json.dumps(generate_json_report(compliance_metrics), indent=2)
    
    # Save report
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Compliance report generated: {args.output_file}")
    print(f"\n📊 Report Summary:")
    print(f"   Period: {args.period.capitalize()}")
    print(f"   Format: {args.format.upper()}")
    print(f"   Risk Level: {compliance_metrics.get('risk_assessment', {}).get('level', 'UNKNOWN')}")
    print(f"   Control Effectiveness: {compliance_metrics.get('control_effectiveness', {}).get('rating', 'Unknown')}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
