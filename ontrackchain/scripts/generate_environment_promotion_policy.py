#!/usr/bin/env python3
"""
Generate multi-environment promotion workflow.

Creates promotion policies for dev → staging → production.
Defines approval requirements per environment.

Usage:
  python3 generate_environment_promotion_policy.py \
    --output-file docs/environment-promotion-policy.json \
    --include-rbac
"""

import argparse
import json
import os
import sys
from datetime import datetime


def create_promotion_policy():
    """Create multi-environment promotion policy."""
    
    policy = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "environments": [
            {
                "name": "development",
                "order": 1,
                "governance_policy": "relaxed",
                "gate_operation": "merge",
                "approval_required": False,
                "reviewers": [],
                "auto_promote_on_gate": False,
                "retention_days": 7,
                "capabilities": [
                    "deploy-anytime",
                    "force-override",
                    "skip-tests"
                ],
                "description": "Development environment - No restrictions"
            },
            {
                "name": "staging",
                "order": 2,
                "governance_policy": "moderate",
                "gate_operation": "deploy",
                "approval_required": False,
                "reviewers": ["@staging-team"],
                "auto_promote_on_gate": True,
                "retention_days": 30,
                "capabilities": [
                    "deploy-on-gate",
                    "smoke-tests",
                    "performance-tests"
                ],
                "description": "Staging environment - Auto-deploy on gate approval"
            },
            {
                "name": "production",
                "order": 3,
                "governance_policy": "strict",
                "gate_operation": "release",
                "approval_required": True,
                "reviewers": ["@release-team", "@platform-team"],
                "min_approvals": 2,
                "auto_promote_on_gate": False,
                "retention_days": 90,
                "capabilities": [
                    "deploy-with-approval",
                    "blue-green",
                    "canary",
                    "emergency-rollback"
                ],
                "description": "Production environment - Requires manual approval"
            }
        ],
        "promotion_rules": [
            {
                "from": "development",
                "to": "staging",
                "trigger": "manual",
                "gate_check": "moderate",
                "blockers": []
            },
            {
                "from": "staging",
                "to": "production",
                "trigger": "manual",
                "gate_check": "strict",
                "blockers": [
                    "failed_security_scan",
                    "pending_compliance_review",
                    "failed_smoke_tests"
                ]
            }
        ],
        "rbac_roles": [
            {
                "name": "developer",
                "permissions": [
                    "deploy:development",
                    "view:staging",
                    "view:production"
                ]
            },
            {
                "name": "staging-team",
                "permissions": [
                    "deploy:development",
                    "deploy:staging",
                    "view:production",
                    "promote:staging-to-production"
                ]
            },
            {
                "name": "release-team",
                "permissions": [
                    "approve:production",
                    "deploy:production",
                    "rollback:production",
                    "manage:promotion-policy"
                ]
            },
            {
                "name": "platform-team",
                "permissions": [
                    "manage:all-environments",
                    "manage:rbac",
                    "manage:promotion-policy",
                    "manage:governance"
                ]
            }
        ],
        "deployment_gates": {
            "development": {
                "required_checks": [],
                "auto_approve": True
            },
            "staging": {
                "required_checks": [
                    "governance-gate",
                    "smoke-tests",
                    "security-scan"
                ],
                "auto_approve": False,
                "approval_timeout_hours": 24
            },
            "production": {
                "required_checks": [
                    "governance-gate-strict",
                    "smoke-tests",
                    "security-scan",
                    "compliance-review",
                    "performance-tests"
                ],
                "auto_approve": False,
                "approval_timeout_hours": 1,
                "required_approvals": 2,
                "change_advisory_board": True
            }
        }
    }
    
    return policy


def create_rbac_matrix():
    """Create RBAC permission matrix."""
    
    matrix = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "permissions": {
            "deploy:development": {
                "description": "Deploy to development environment",
                "environments": ["development"],
                "risk_level": "low"
            },
            "deploy:staging": {
                "description": "Deploy to staging environment",
                "environments": ["staging"],
                "risk_level": "medium",
                "requires_approval": True
            },
            "deploy:production": {
                "description": "Deploy to production environment",
                "environments": ["production"],
                "risk_level": "high",
                "requires_approval": True,
                "requires_min_approvals": 2
            },
            "approve:production": {
                "description": "Approve production deployments",
                "environments": ["production"],
                "risk_level": "critical"
            },
            "rollback:production": {
                "description": "Rollback production deployments",
                "environments": ["production"],
                "risk_level": "critical",
                "audit_required": True
            },
            "manage:governance": {
                "description": "Manage governance policies",
                "environments": ["all"],
                "risk_level": "critical"
            },
            "manage:rbac": {
                "description": "Manage RBAC roles and permissions",
                "environments": ["all"],
                "risk_level": "critical"
            }
        },
        "role_assignments": [
            {
                "github_team": "@staging-team",
                "permissions": [
                    "deploy:development",
                    "deploy:staging",
                    "view:production"
                ],
                "expires": None
            },
            {
                "github_team": "@release-team",
                "permissions": [
                    "deploy:development",
                    "deploy:staging",
                    "deploy:production",
                    "approve:production"
                ],
                "expires": None
            },
            {
                "github_team": "@platform-team",
                "permissions": [
                    "deploy:development",
                    "deploy:staging",
                    "deploy:production",
                    "approve:production",
                    "rollback:production",
                    "manage:governance",
                    "manage:rbac"
                ],
                "expires": None
            }
        ]
    }
    
    return matrix


def main():
    parser = argparse.ArgumentParser(
        description="Generate environment promotion policy"
    )
    parser.add_argument('--output-file', default='docs/environment-promotion-policy.json',
                        help='Output file for promotion policy')
    parser.add_argument('--include-rbac', action='store_true',
                        help='Also generate RBAC matrix')
    parser.add_argument('--include-examples', action='store_true',
                        help='Include workflow examples')
    
    args = parser.parse_args()
    
    # Create promotion policy
    policy = create_promotion_policy()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # Save policy
    with open(args.output_file, 'w', encoding='utf-8') as f:
        json.dump(policy, f, indent=2)
    
    print(f"✅ Promotion policy generated: {args.output_file}")
    
    # Generate RBAC if requested
    if args.include_rbac:
        rbac_file = args.output_file.replace('.json', '-rbac.json')
        rbac_matrix = create_rbac_matrix()
        
        with open(rbac_file, 'w', encoding='utf-8') as f:
            json.dump(rbac_matrix, f, indent=2)
        
        print(f"✅ RBAC matrix generated: {rbac_file}")
    
    # Summary
    print(f"\n📊 Policy Summary:")
    print(f"   Environments: {len(policy['environments'])}")
    print(f"   Promotion Rules: {len(policy['promotion_rules'])}")
    print(f"   Deployment Gates: {len(policy['deployment_gates'])}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
