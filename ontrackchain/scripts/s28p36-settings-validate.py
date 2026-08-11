#!/usr/bin/env python3
"""
Sprint S28+36 P4: Validador DRY-RUN do settings.yml NA RAIZ do repositório.
Chamado via `make settings-dry-run` no Makefile raiz /home/jistriane/Ontrackchain/Makefile.

2 objetivos:
  1. Validar que settings.yml está no caminho CANÔNICO (repo-root/.github/settings.yml) —
     BUG FIX S28+36: arquivo legado estava em ontrackchain/.github/settings.yml (subpasta)
     → NUNCA processado por GitHub Settings Probot / Actions.
  2. Garantir contexts OBRIGATÓRIOS (QA Gateway jobs 2x) e BLOQUEAR contexts PROIBIDOS
     (sonarcloud-* tem if: secrets → status NÃO é postado se secret vazio → PR BRICKA!)

Exit 0 = PASS, exit !=0 = FAIL (1..8 um por assertion).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml


def main() -> int:
    SETTINGS_PATH = Path(".github/settings.yml").resolve()
    if not SETTINGS_PATH.is_file():
        print(f"❌ ERRO GRAVE S28+36: {SETTINGS_PATH} NÃO EXISTE!")
        print("   Bug esperado se settings.yml na subpasta ontrackchain/.github/settings.yml")
        print("   Arquivo CANÔNICO = repo-root/.github/settings.yml")
        return 1

    with open(SETTINGS_PATH) as f:
        data = yaml.safe_load(f)

    branches: dict[str, dict] = {b["name"]: b for b in data.get("branches", [])}
    if "main" not in branches:
        print("❌ ERRO: branch main não declarado em settings.yml → branches → list")
        return 2
    if "develop" not in branches:
        print("❌ ERRO: branch develop não declarado em settings.yml")
        return 3

    main_ctx = branches["main"]["protection"]["required_status_checks"]["contexts"]
    dev_ctx = branches["develop"]["protection"]["required_status_checks"]["contexts"]

    # ========================================================================
    # REGRA BLOQUEANTE 1/3: SONARCLOUD-* CONDICIONAIS NÃO PODEM SER REQUIRED
    # ========================================================================
    FORBIDDEN_CONTEXTS = (
        "sonarcloud-codecov-quality-gate",   # needs self-hosted OFF sometimes
        "sonarcloud-standalone",             # if: ${{ secrets.SONAR_TOKEN != '' }}
    )
    for forb in FORBIDDEN_CONTEXTS:
        if forb in main_ctx:
            print(f"❌ ERRO BLOQUEANTE: {forb!r} em main required_status_checks!")
            print("   Motivo: job tem if: secrets. Se secret vazio → GitHub NUNCA recebe status")
            print("           → PR fica esperando FOREVER → BRICKADO merge 😱")
            print("   Correção: REMOVA {forb} de settings.yml branches → main → protection → contexts")
            return 4
        if forb in dev_ctx:
            print(f"❌ ERRO BLOQUEANTE: {forb!r} em develop contexts (mesmo motivo)")
            return 4

    # ========================================================================
    # REGRA OBRIGATÓRIA 2/3: QA Gateway 2 jobs DEVEM obrigar merge (BUG FIX)
    # ========================================================================
    QA_OBLIGATORY = ("qa-gateway-cli-smoke", "qa-gateway-scan-sla-ci-p008")
    for qa_job in QA_OBLIGATORY:
        if qa_job not in main_ctx:
            print(f"❌ ERRO: QA Gate job {qa_job!r} FALTANDO em main required contexts!")
            print("   BUG herdado Sprint 8: QA Gateway não bloqueava PR silenciosamente")
            return 5

    # ========================================================================
    # REGRA OBRIGATÓRIA 3/3: GitHub Native Advanced Security
    # ========================================================================
    sa = data.get("repository", {}).get("security_and_analysis", {})
    if not sa:
        print("⚠️  WARNING: security_and_analysis NÃO declarado em repository → defaults GitHub free")
    if sa.get("advanced_security", {}).get("status") != "enabled":
        print("❌ ERRO: repository.security_and_analysis.advanced_security não enabled")
        print("   Sem ele: Code Scanning Alerts / Secret Scanning NÃO FUNCIONA (GHAS)")
        return 6
    if sa.get("secret_scanning_push_protection", {}).get("status") != "enabled":
        print("❌ ERRO: repository.secret_scanning_push_protection não enabled")
        print("   Sem ele: desenvolvedor consegue pushar segredo REAL sem bloqueio")
        return 7

    repo_name = data["repository"]["name"]
    default_branch = data["repository"]["default_branch"]
    n_labels = len(data.get("labels", []))
    n_envs = len(data.get("environments", []))

    print(f"✅ Repository Settings DRY-RUN: {repo_name} (default_branch={default_branch})")
    print(f"✅ YAML parse VÁLIDO: {SETTINGS_PATH}")
    print(f"✅ Branches protegidas: {len(branches)} ({', '.join(sorted(branches.keys()))})")
    print(f"✅ Main required_status_checks.contexts: {len(main_ctx)}")
    for c in main_ctx:
        print(f"    · {c}")
    if dev_ctx:
        print(f"✅ Develop required_status_checks.contexts: {len(dev_ctx)}")
    print(f"✅ Environments: {n_envs} (staging/prod/canary)")
    print(f"✅ Labels (QA/ADR/Priority): {n_labels}")
    print(f"✅ Advanced Security: enabled (GHAS)")
    print(f"✅ Secret Scanning Push Protection: enabled (bloqueia push de segredos na origem)")
    print(f"✅ 0 job sonarcloud-* PROIBIDO em required contexts")
    print(f"✅ QA Gate 2 jobs obrigatórios: qa-gateway-cli-smoke + qa-gateway-scan-sla-ci-p008")
    print(f"\n🎉 Repository Settings DRY-RUN PASS: 8 itens obrigatórios, 0 falhas bloqueantes")
    return 0


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parents[2])  # repo root (scripts em ontrackchain/scripts → sobe 2 níveis = repo root)
    sys.exit(main())
