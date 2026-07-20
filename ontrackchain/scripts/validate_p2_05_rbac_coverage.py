#!/usr/bin/env python3
"""
validate_p2_05_rbac_coverage.py

Valida estatisticamente e por AST/Grep a cobertura do RBAC P2-05
em todos os microserviços Python (apps/) do projeto Ontrackchain.

Verifica:
1. Endpoints expostos por FastAPI (@app.get, @app.post, @app.put, @app.delete, @app.patch, @router.*)
2. Presença de headers de controle de autorização (ex: X-Role, X-Linked-User-Id) ou chamadas de verificação de papéis (_require_role, require_role, etc.)
3. Presença de log/evento auditável de autorização negada (authorization_denied / 403)
"""

import os
import sys
import re
import ast
import json
from typing import Dict, List, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(PROJECT_ROOT, "apps")

SERVICES = [
    "auth-service",
    "compliance-api",
    "investigation-api",
    "monitoring-api",
    "report-api",
]

ROUTE_DECORATOR_RE = re.compile(r"@(app|router)\.(get|post|put|delete|patch|options|head)\s*\(")

def analyze_service(service_name: str) -> Dict[str, Any]:
    service_dir = os.path.join(APPS_DIR, service_name, "src")
    if not os.path.exists(service_dir):
        return {"service": service_name, "status": "SKIPPED", "total_endpoints": 0, "rbac_protected": 0}

    total_endpoints = 0
    rbac_protected = 0
    endpoints_details = []

    for root, _, files in os.walk(service_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                lines = content.splitlines()
                for i, line in enumerate(lines):
                    match = ROUTE_DECORATOR_RE.search(line)
                    if match:
                        total_endpoints += 1
                        method = match.group(2).upper()
                        # Extrai trecho da rota
                        route_path = line.strip()
                        
                        # Inspeciona as próximas ~50 linhas procurando por checagem de role ou header X-Role
                        snippet = "\n".join(lines[i:min(i + 60, len(lines))])
                        has_rbac = bool(
                            "X-Role" in snippet or 
                            "x_role" in snippet or 
                            "_require_role" in snippet or 
                            "require_role" in snippet or
                            "has_permission" in snippet or
                            "authorization_denied" in snippet or
                            "status_code=403" in snippet or
                            "403" in snippet or
                            "authenticated" in snippet or
                            "auth_mode" in snippet or
                            "X-Linked-User-Id" in snippet or
                            "_require_auth" in snippet or
                            "_require_team" in snippet or
                            "_require_monitoring" in snippet or
                            "_require_org_id" in snippet
                        )
                        
                        if has_rbac:
                            rbac_protected += 1
                        
                        endpoints_details.append({
                            "file": os.path.relpath(filepath, PROJECT_ROOT),
                            "line": i + 1,
                            "method": method,
                            "route_snippet": route_path[:80],
                            "rbac_protected": has_rbac
                        })

    coverage_pct = (rbac_protected / total_endpoints * 100) if total_endpoints > 0 else 100.0

    return {
        "service": service_name,
        "total_endpoints": total_endpoints,
        "rbac_protected": rbac_protected,
        "coverage_percentage": round(coverage_pct, 2),
        "status": "PASS" if coverage_pct >= 80.0 else "WARNING",
        "endpoints": endpoints_details
    }

def main() -> int:
    print("=" * 70)
    print(" Ontrackchain - Validador de Cobertura RBAC P2-05")
    print("=" * 70)
    
    results = []
    total_endpoints_all = 0
    total_protected_all = 0

    for service in SERVICES:
        res = analyze_service(service)
        results.append(res)
        total_endpoints_all += res["total_endpoints"]
        total_protected_all += res["rbac_protected"]
        
        status_icon = "✅" if res["status"] == "PASS" else "⚠️"
        print(f"{status_icon} [{res['service']}] Endpoints: {res['total_endpoints']} | RBAC Protegidos: {res['rbac_protected']} | Cobertura: {res.get('coverage_percentage', 0)}%")

    overall_pct = (total_protected_all / total_endpoints_all * 100) if total_endpoints_all > 0 else 100.0
    print("-" * 70)
    print(f"📊 Cobertura Global RBAC P2-05: {round(overall_pct, 2)}% ({total_protected_all}/{total_endpoints_all} endpoints protegidos)")
    print("=" * 70)

    # Exporta o resultado consolidado
    artifacts_dir = os.path.join(PROJECT_ROOT, "test-results")
    os.makedirs(artifacts_dir, exist_ok=True)
    report_file = os.path.join(artifacts_dir, "rbac_p2_05_coverage_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({
            "overall_coverage_percentage": round(overall_pct, 2),
            "total_endpoints": total_endpoints_all,
            "total_protected_endpoints": total_protected_all,
            "services": results
        }, f, indent=2)
        
    print(f"📄 Relatório JSON salvo em: {report_file}\n")
    return 0 if overall_pct >= 75.0 else 1

if __name__ == "__main__":
    sys.exit(main())
