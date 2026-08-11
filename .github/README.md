# 🛡️ .github/ (RAIZ) · SSOT ATIVO CI/CD + Governança GitHub

## ⚠️ STATUS OFICIAL: **SINGLE SOURCE OF TRUTH (SSOT) PARA TODO O REPOSITÓRIO**

Este diretório `.github/` **na RAIZ do repositório** é o ÚNICO que o GitHub Actions e a interface do GitHub consideram automaticamente.

---

## 📋 O que este diretório contém (13/13 itens HC-3 validados G8):

| Artefato | Quantidade | Propósito | Alterar sem ordem? |
|---|---|---|---|
| **`workflows/`** | **20 arquivos YAML** | CI/CD pipelines oficiais (pre-merge-gates ADR-029, governance-gate, deployments, regulação, QA). **ESTES SÃO OS WORKFLOWS QUE REALMENTE EXECUTAM no GitHub Actions!** | 🚫 **NÃO ALTERAR SEM ORDEM EXPLÍCITA PROPRIETÁRIO** |
| **`settings.yml`** | 1 arquivo | **HC-3 PROTEGIDO** — Repository Settings SSOT: 21 contexts obrigatórios na main, 13 na develop, QA Gate 2 jobs, 0 jobs sonarcloud-* proibidos, 3 environments, 14 labels, GHAS + Push Protection enabled. Validado G8 `make settings-dry-run`. | 🚫 **PROIBIDO ALTERAR SEM ORDEM EXPLÍCITA** (HC-3 fail-closed G8) |
| **`pull_request_template.md`** | 1 arquivo | Template padrão para PRs. | ✅ Pode atualizar em sprint governança dedicada |
| **`GOVERNANCE_CICD_SETUP.md`** | 1 arquivo | Documentação legada de setup de CI/CD Governança. Referência histórica. | ✅ Apenas complementar com links atualizados |

---

## 🚨 AVISO CRÍTICO DE ARQUITETURA GITHUB ACTIONS:

> **Workflows YAML localizados QUALQUER OUTRO LUGAR que não seja `.github/workflows/` NA RAIZ DO REPOSITÓRIO NÃO SÃO EXECUTADOS AUTOMATICAMENTE pelo GitHub Actions.**
>
> Existem outros diretórios `.github/` em **subpastas** (`ontrackchain/.github/`, `github_main/.github/`):
> - **`ontrackchain/.github/workflows/`** = 10 arquivos YAML — **NÃO EXECUTAM** automaticamente, são configuração LEGADA referência de colaboração.
> - **`github_main/.github/workflows/`** = 18 arquivos YAML (incompletos, faltam 2 vs SSOT) — **NÃO EXECUTAM**, diretório LEGADO arquivado.
>
> O diretório `.github/` nesta página (RAIZ) = **ÚNICA FONTE VERDADEIRA** que o GitHub realmente usa.

---

## 🔍 Como validar o estado deste diretório:

```bash
# Validador oficial HC-3 settings.yml (8 itens obrigatórios)
cd /home/jistriane/Ontrackchain
make settings-dry-run  # G8 FAIL-CLOSED

# Ver workflows que realmente rodam: olhar pasta .github/workflows/ na RAIZ
ls -la .github/workflows/   # 20 arquivos = quantidade SSOT
```

---

## 📚 Documentação relacionada:

- Mapa Completo Documentação 7 Tiers: [README raiz `## Mapa Completo da Documentação`](../README.md#mapa-completo-da-documentação--7-tiers-hierárquicos-sprint-s2867-p4)
- Tier 5 GitHub no Mapa: Tabela do README explica status dos 3 diretórios.
- HC-3 (Hard Constraint 3): Seção 1 do [CONTRIBUTING.md](../CONTRIBUTING.md)
- Hardening HC-5 Dotfiles Governança: [CONTRIBUTING.md Seção HC-5](../CONTRIBUTING.md#1-hard-constraints-não-negociáveis-válidos-para-todo-commit-todo-sprint)
