#!/usr/bin/env python3
"""
CI/CD gate controller based on governance state.

Evaluates consolidated governance JSON and decides whether to allow/block operations.
Can be used in GitHub Actions, GitLab CI, or any CI/CD platform.

Usage:
  python3 evaluate_governance_gate.py \
    --consolidated-json docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-consolidated.json \
    --gate-policy strict \
    [--operation merge|deploy|release]
"""

import argparse
import json
import os
import sys
from datetime import datetime


def load_consolidated_json(path):
    """Load consolidated governance JSON."""
    if not os.path.exists(path):
        print(json.dumps({"status": "error", "message": f"JSON not found: {path}"}))
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(json.dumps({"status": "error", "message": f"Failed to load JSON: {e}"}))
        return None


def evaluate_gate(consolidated, policy="strict", operation="merge"):
    """
    Evaluate governance gate based on policy.
    
    Policies:
    - strict: only VERDE + GO allows operation
    - moderate: AMARELO + GO-or-NO-GO allows operation, VERMELHO blocks
    - relaxed: any state allows operation (logging only)
    
    Operations:
    - merge: code merge to main
    - deploy: deployment to staging/production
    - release: tagged release
    """
    
    gov_state = consolidated.get("governance_state", {})
    status = gov_state.get("status", "failed")
    signal = gov_state.get("signal", "unknown")
    decision = gov_state.get("decision", "unknown")
    blockers = gov_state.get("blockers", {})
    window_id = consolidated.get("window_id", "unknown")
    
    result = {
        "window_id": window_id,
        "policy": policy,
        "operation": operation,
        "governance_state": {
            "status": status,
            "signal": signal,
            "decision": decision,
            "blockers": blockers
        },
        "evaluated_at": datetime.now().isoformat(),
        "allowed": False,
        "reason": ""
    }
    
    # Evaluate based on policy
    if policy == "strict":
        # STRICT: only VERDE + GO allows
        if signal == "verde" and decision == "recomendado_go":
            result["allowed"] = True
            result["reason"] = f"Governance is verde with go decision"
        elif signal == "vermelho":
            result["allowed"] = False
            result["reason"] = f"Governance signal is vermelho - critical blockers present"
        elif signal == "amarelo":
            result["allowed"] = False
            result["reason"] = f"Governance signal is amarelo - unstable state, policy requires verde"
        elif decision == "recomendado_no_go":
            result["allowed"] = False
            result["reason"] = f"Governance decision is no-go"
        else:
            result["allowed"] = False
            result["reason"] = f"Governance state does not meet strict policy requirements"
    
    elif policy == "moderate":
        # MODERATE: AMARELO + any decision is OK, VERMELHO blocks, GO decision is required
        if signal == "vermelho":
            result["allowed"] = False
            result["reason"] = f"Governance signal is vermelho - critical blockers present, policy blocks"
        elif decision == "recomendado_no_go":
            result["allowed"] = False
            result["reason"] = f"Governance decision is no-go"
        elif signal in ["verde", "amarelo"]:
            result["allowed"] = True
            result["reason"] = f"Governance signal is {signal}, policy allows (moderate mode)"
        else:
            result["allowed"] = False
            result["reason"] = f"Unknown governance state"
    
    elif policy == "relaxed":
        # RELAXED: always allow, just log
        result["allowed"] = True
        result["reason"] = f"Policy is relaxed - all states allowed (logging only)"
    
    else:
        result["allowed"] = False
        result["reason"] = f"Unknown policy: {policy}"
    
    # Add blocker details
    placeholder_count = blockers.get("placeholders", 0)
    handoff_count = blockers.get("handoff", 0)
    total_blockers = placeholder_count + handoff_count
    
    result["blocker_summary"] = {
        "total": total_blockers,
        "placeholders": placeholder_count,
        "handoff": handoff_count
    }
    
    # Add gate-specific checks for operations
    if operation == "deploy" and policy != "relaxed":
        # For deployments, stricter checks
        if total_blockers > 0 and policy != "relaxed":
            result["allowed"] = False
            result["reason"] = f"Deployment blocked: {total_blockers} blockers present"
    
    elif operation == "release" and policy != "relaxed":
        # For releases, only verde + go allowed
        if signal != "verde" or decision != "recomendado_go":
            result["allowed"] = False
            result["reason"] = f"Release blocked: requires verde signal + go decision"
    
    return result


def format_github_actions_output(result):
    """Format output for GitHub Actions."""
    allowed = "true" if result["allowed"] else "false"
    return f"gate_allowed={allowed}\ngate_reason={result['reason']}"


def format_gitlab_ci_output(result):
    """Format output for GitLab CI."""
    if result["allowed"]:
        return f"✅ Gate Passed: {result['reason']}\nGOVERNANCE_GATE_PASSED=true"
    else:
        return f"❌ Gate Failed: {result['reason']}\nGOVERNANCE_GATE_PASSED=false"


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate governance gate for CI/CD operations"
    )
    parser.add_argument('--consolidated-json', required=True, help='Path to consolidated JSON')
    parser.add_argument('--gate-policy', default='strict', choices=['strict', 'moderate', 'relaxed'],
                        help='Gate policy level')
    parser.add_argument('--operation', default='merge', choices=['merge', 'deploy', 'release'],
                        help='Operation type')
    parser.add_argument('--format', default='json', choices=['json', 'github', 'gitlab'],
                        help='Output format')
    parser.add_argument('--exit-code', action='store_true',
                        help='Exit with code 0=allowed, 1=blocked (for CI/CD scripts)')
    
    args = parser.parse_args()
    
    # Load consolidated JSON
    consolidated = load_consolidated_json(args.consolidated_json)
    if not consolidated:
        sys.exit(1)
    
    # Evaluate gate
    result = evaluate_gate(consolidated, policy=args.gate_policy, operation=args.operation)
    
    # Output result
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    elif args.format == 'github':
        print(format_github_actions_output(result))
    elif args.format == 'gitlab':
        print(format_gitlab_ci_output(result))
    
    # Exit code
    if args.exit_code:
        sys.exit(0 if result["allowed"] else 1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
