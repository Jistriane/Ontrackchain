# Apêndice Técnico (Ontrackchain)

Este apêndice consolida os caminhos técnicos (engenharia/ops) sem competir com o Sumário Executivo do repositório.

## Portas de Entrada

- Sumário Executivo (fonte): [README.md](../../README.md)
- Readiness canônico: [project-executive-readiness-brief.md](./project-executive-readiness-brief.md)
- Índice completo da documentação: [docs/README.md](./README.md)
- Quick start técnico: [ontrackchain/README.md](../README.md)

## Arquitetura e Contratos

- Arquitetura: [architecture.md](./architecture.md)
- Contratos de API: [api-contracts.md](./api-contracts.md)
- RBAC e permissões: [rbac-and-permissions.md](./rbac-and-permissions.md)
- ADRs: [adrs/README.md](./adrs/README.md)

## Operação e Deploy

- Operação local: [operations.md](./operations.md)
- Deploy e staging: [deploy-and-staging.md](./deploy-and-staging.md)
- Variáveis de ambiente: [environment-variables.md](./environment-variables.md)
- Runbooks: [runbooks.md](./runbooks.md)

## Banco e Migrations (runner automático)

O `docker-compose.yml` inclui `postgres-bootstrap`, que aplica `infra/postgres/init.sql` (quando necessário) e depois executa todas as migrations em ordem.

- Migrations: [infra/postgres/migrations/README.md](../infra/postgres/migrations/README.md)
- Compose: [docker-compose.yml](../docker-compose.yml)

## AI Service — Jobs assíncronos (v4.0.7)

Ponto de entrada: `POST /api/v1/ai/themis` e `POST /api/v1/ai/law-enforcement-export` retornam `202` e geram um `job_id`. Um worker separado consome `ai_service_jobs` e atualiza status/resultados, com `human gate` quando aplicável.

- Contrato de jobs: [api-contracts.md](./api-contracts.md)
- Worker: [worker.py](../apps/ai-service/src/ai_service/worker.py)
- Tabela: `ai_service_jobs` (migration 0019): [0019_ai_service_jobs.sql](../infra/postgres/migrations/0019_ai_service_jobs.sql)

## Auditoria e Evidência

- Matriz: [evidence-and-audit-matrix.md](./evidence-and-audit-matrix.md)
- Catálogo de eventos: [evidence-event-catalog.md](./evidence-event-catalog.md)
- Política: [validation-and-audit.md](./validation-and-audit.md)

---

## Governança e Qualidade (Sprints S28+30 → S28+68 P1..P4)

> **Referencia canônica**: 8 Gates FAIL-CLOSED padrao em TODO VAL/COMMIT sprint.
> **Mapa completo 7 Tiers**: `[Projeto raiz](../../README.md) → ## Mapa Completo Documentação 7 Tiers (Sprint S28+67)`

### 8 Gates Padrão Obrigatórios (G1 → G8)

| Gate | Nome | Como rodar | O que valida |
|---|---|---|---|
| G1 | `gov-m5-verify` | `bash ontrackchain/scripts/gov-m5-verify-pre-sign.sh` | Hash L7 SIGNOFF-M5.md = `9dc536985265d3cc1c054eb4e2e47bc3697900899fef1b8c5ecfb2affc474cc6` (HC-1) |
| G2 | `gov-m5-unit-test` | `bash ontrackchain/scripts/s28p25-test-gov-m5-verify.sh` | 2 cenarios: hash OK exit 0, hash RUIM exit 1 (2/2) |
| G3 | `shell-syntax` | `bash ontrackchain/scripts/s28p25-bash-syntax-check.sh` | `bash -n` em 21 scripts bash monorepo (21/21) |
| G4 | `healthz-bypass` | `bash ontrackchain/scripts/s28p24-check-healthz-metrics-bypass.sh` | 9 FastAPI apps × 2 endpoints `/healthz` + `/metrics` bypassam RBAC (18/18) |
| G5 | `all-checks -n` | `make all-checks -n` | Parse Makefile aggregator 15 gates + sintaxe (155 linhas) |
| G6 | `typecheck -n` | `make typecheck -n` | Parse mypy strict via hatch (3 linhas) |
| G7 | `qa-gateway-all-strict-ci -n` | `make qa-gateway-all-strict-ci -n` | Parse 4 scans QA Gateway STRICT: RBAC / LGPD ROPD / Billing / AML Live (46 linhas) |
| G8 | `settings-dry-run` | `make settings-dry-run` | Valida 8 itens HC-3: 21 main / 13 dev contexts, 0 sonarcloud-*, QA Gate 2 jobs, 3 envs, 14 labels, GHAS, Push Protection |

### Stack Atualizado

- **mypy strict global** (S28+46): Hatch mypy, target `make typecheck`, gate G6.
- **QA Gateway ADR-029** (S28+47→S28+50): 4 scans, 2 jobs HC-3 obrigatorios (`qa-gateway-cli-smoke` + `qa-gateway-scan-sla-ci-p008`), target `make qa-gateway-all-strict-ci` gate G7.
- **TruffleHog --only-verified** (S28+36): Segredos 0 hardcoded, Push Protection habilitado (HC-2).
- **15 Gates all-checks FAIL-CLOSED** (S28+54): Aggregator Makefile, ordem de risco, G5 dry-run.
- **HC-5 Dotfiles + Trindade Docs** (S28+58/59/60): `.editorconfig` plug-in obrigatorio / `.gitattributes` LF / `make changelog / contributing / readme`.

### Como rodar o ciclo completo de validação

```bash
# VAL padrão de qualquer sprint (executar ANTES de COMMIT)
bash ontrackchain/scripts/gov-m5-verify-pre-sign.sh && \
bash ontrackchain/scripts/s28p25-test-gov-m5-verify.sh && \
bash ontrackchain/scripts/s28p25-bash-syntax-check.sh && \
bash ontrackchain/scripts/s28p24-check-healthz-metrics-bypass.sh && \
make all-checks -n >/dev/null && echo "G5 PASS" && \
make typecheck -n >/dev/null && echo "G6 PASS" && \
make qa-gateway-all-strict-ci -n >/dev/null && echo "G7 PASS" && \
make settings-dry-run
# 8/8 → 0 exit codes = aprovado para COMMIT
```

### Convenções Linguagem Dual

| Artefato | Idioma |
|---|---|
| Docs dev-facing (README, CONTRIBUTING, CHANGELOG, docs/*.md Tier 0..6) | **pt-BR** |
| Código, docstrings, comentários roadmap pyproject.toml, YAML keys, testes unitários | **EN (inglês)** |
