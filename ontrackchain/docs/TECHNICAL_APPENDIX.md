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
