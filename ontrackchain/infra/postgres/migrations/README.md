# PostgreSQL Migrations

Esta pasta contem migrations incrementais para ambientes que ja possuem volume persistido e nao devem ser reinicializados com `docker compose down -v`.

## Papel das Migrations

- `infra/postgres/init.sql` continua sendo a fonte de bootstrap para ambientes novos
- as migrations alinham volumes antigos ao schema atual
- cada migration deve ser preferencialmente idempotente

## Convencao

- prefixo numerico crescente: `0001_*.sql`, `0002_*.sql`, ...
- uma migration por mudanca coerente de schema
- sempre refletir a mesma mudanca tambem em `init.sql`

## Migrations Atuais

### `0001_align_reports_table.sql`

Alinha a tabela `reports` para o fluxo atual de relatorios:

- `external_report_id`
- `report_type_requested`
- `content_type`
- indice parcial `uq_reports_external_report_id`

### `0002_add_monitoring_alerts.sql`

Adiciona persistencia de alertas de monitoramento:

- tabela `monitoring_alerts`
- indices
- `RLS`

### `0003_add_audit_logs.sql`

Adiciona trilha auditavel central:

- tabela `audit_logs`
- indices
- `RLS`

### `0004_add_audit_log_filter_indexes.sql`

Adiciona indices extras para consulta operacional de auditoria:

- filtros por `request_id`
- filtros por `report_id`
- filtros compostos por `organization_id/action/resource_type`

### `0005_add_operational_alert_events.sql`

Adiciona persistencia global de incidentes operacionais recebidos do `Alertmanager`:

- tabela `operational_alert_events`
- indices por `status` e `service`

### `0006_add_operational_alert_triage.sql`

Adiciona metadados de triagem manual em incidentes operacionais:

- `triage_status`
- `triaged_at`
- `triaged_by`
- `triage_note`

### `0007_add_operational_alert_cursor_index.sql`

Adiciona indice para paginação cursor-based de incidentes operacionais:

- ordenacao estavel por `last_received_at DESC, id DESC`

### `0008_add_external_identities.sql`

Adiciona tabela de identidades federadas (OIDC/Keycloak):

- tabela `external_identities`
- indices por `provider/subject/org`

### `0009_evidence_trail.sql` — Sprint 1 (2026-07-01)

Trilha de evidências append-only com encadeamento SHA-256.
**Base regulatória: BCB 520 Art. 45 II (retenção 5 anos) + IN BCB 739 Art. 1° VIII.**

- tabela `evidence_trail` (INSERT ONLY — UPDATE e DELETE bloqueados por trigger)
- trigger `prevent_evidence_modification()` — imutabilidade garantida no banco
- trigger `set_evidence_chain()` — encadeamento automático de hashes
- RLS por `organization_id`
- índices para auditoria rápida por org, case, event_type, hash
- coluna `soroban_tx_hash` reservada para âncora Stellar/Soroban (Fase 3 — 2027)
- retenção calculada automaticamente: `recorded_at + 5 anos`

### `0010_preventive_blocks.sql` — Sprint 1 (2026-07-01)

Registro de bloqueios preventivos de ilícitos.
**Base regulatória: BCB 520 Art. 43 §2° VI + Lei 13.810/2019 + IN BCB 739 Art. 1° VII.**

- tabela `preventive_blocks` com 8 tipos de ação (BLOCK_IMMEDIATE, BLOCK_AND_FREEZE, etc.)
- suporte a Stage 1 (gateway) e Stage 2 (backend)
- FK para `evidence_trail.event_hash` (trilha de integridade cruzada)
- campos para workflow de ROS COAF (deadline 24h, Lei 9.613/98 Art. 11-B)
- RLS por `organization_id`
- retenção: 5 anos

### `0011_counterparties.sql` — Sprint 1 (2026-07-01)

Cadastro de contrapartes com KYC/KYB regulado.
**Base regulatória: BCB 520 Art. 47 + IN BCB 739 Art. 1° IV + Circular BCB 3.978/2020.**

- tabela `counterparties` com 4 níveis de risco (BAIXO→CRÍTICO)
- campos PEP, Due Diligence aprimorada, sanctions_cleared
- tabela `counterparty_history` (auditoria de alterações)
- próxima data de revisão calculada por nível de risco
- RLS por `organization_id`
- constraint de unicidade por documento+organização
- retenção: 5 anos

### `0012_sanctions_cache_ros_records.sql` — Sprint 1 (2026-07-01)

Cache de listas de sanções e registros de ROS COAF.
**Base regulatória: BCB 520 Art. 34 III + Lei 13.810/2019 + Lei 9.613/98 Art. 11.**

- tabela `sanctions_lists_meta` — configuração de 5 listas pré-configuradas:
  - OFAC_SDN (sync 6h, confiança 0.95)
  - UN_CSNU (sync 24h, confiança 0.90)
  - EU_CONSOLIDATED (sync 24h)
  - COAF_INTERNAL (sync 12h)
  - OPENSANCTIONS (PENDING_CONFIG — aguarda API key)
- tabela `sanctions_hits_cache` — cache local com GIN index para full-text search
- tabela `ros_records` — Relatório de Operação Suspeita com workflow:
  - geração automática → aprovação CO (2FA obrigatório) → submissão manual COAF ONLINE
  - prazo 24h com alerta em T+20h (Lei 9.613/98 Art. 11-B)

### `0013_regulatory_work_items.sql` — Sprint 2 (2026-07-02)

Camada operacional multiusuário persistida para módulos regulatórios.
**Base regulatória: BCB 520 Art. 45 II + IN BCB 739 Art. 1° IV, V, VII e VIII.**

- tabela `regulatory_work_items` — fila operacional compartilhada por `tenant`
- tabela `regulatory_work_events` — timeline auditável de transições
- tabela `regulatory_work_comments` — comentários estruturados para handoff e decisão
- `RLS` por `organization_id`
- índices por módulo, owner, SLA, atividade e correlação por recurso
- suporte inicial aos módulos:
  - `alerts`
  - `sanctions`
  - `blocks`
  - `reports`
  - `ros_coaf`
  - `counterparties`
  - `evidence`

### `0014_regulatory_work_items_contract_guardrails.sql` — Sprint 2 (2026-07-07)

Endurece o contrato de `regulatory_work_items` sem quebrar compatibilidade incremental.

- função para validar o par canônico `module -> resource_type`
- função para validar shape mínimo e tipos conhecidos de `metadata`
- backfill de `workspace_status` e aliases legados (`local_workspace_status`, `local_block_status`, `ros_status`)
- novas constraints de contrato aplicadas diretamente na tabela
- alvo operacional no `Makefile`: `make apply-regulatory-work-items-contract-guardrails-migration`

### `0015_evidence_package_seals.sql` — Sprint 4 (2026-07-08)

Persistencia da selagem institucional forte para pacotes manuais DD/SoF.

- tabela `evidence_package_seals` — estado de selagem por `tenant`, digest e politica
- tabela `evidence_package_signoffs` — decisoes institucionais por papel
- `RLS` por `organization_id`
- trigger `update_evidence_package_seals_updated_at()` para `updated_at`
- indices por correlacao de `request_id`, `package_sha256`, `seal_status` e `signed_at`

### `0016_team_users_directory.sql` — Sprint 5 (2026-07-12)

Endurece o diretorio multiusuario usado por `team`, `billing` e pelos fluxos que exigem
resolucao consistente do ator persistido.

- adiciona `display_name`, `status`, `note` e `updated_at` em `users`
- aplica a constraint `users_status_check` com os estados `active`, `invited` e `disabled`
- faz backfill idempotente dos novos campos a partir de `email` e `created_at`
- alvo operacional no `Makefile`: `make apply-team-users-directory-migration`

## Aplicacao Local

Rode as migrations em ordem:

```bash
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0001_align_reports_table.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0002_add_monitoring_alerts.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0003_add_audit_logs.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0004_add_audit_log_filter_indexes.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0005_add_operational_alert_events.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0006_add_operational_alert_triage.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0007_add_operational_alert_cursor_index.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0008_add_external_identities.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0009_evidence_trail.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0010_preventive_blocks.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0011_counterparties.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0012_sanctions_cache_ros_records.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0013_regulatory_work_items.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0014_regulatory_work_items_contract_guardrails.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0015_evidence_package_seals.sql
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0016_team_users_directory.sql
```

## Validacao de Suites do Compliance API

Para validar a suite canonica principal do `compliance-api`, use:

```bash
make check-compliance-api-tests
```

O alvo compila os modulos Python criticos (`main`, `worker`, `operations`) e roda as suites:

- `tests.test_compliance_endpoints`
- `tests.test_operations_catalog`
- `tests.test_compliance_rbac`
- `tests.test_internal_metrics`
- `tests.test_worker_source_url_overrides`
- `tests.test_work_item_contracts`

Quando o runtime Python local nao possui as dependencias do `compliance-api`, o runner faz fallback automatico para `docker compose run --no-deps compliance-api`, montando a raiz do monorepo para preservar imports de `packages/agents` e `packages/shared` e validar a suite real em vez de retornar um falso verde por `skip`.

Para a trilha focada apenas em `work-items`, use:

```bash
make check-work-items-contracts
```

O alvo executa `python3`, compila os arquivos Python criticos da trilha e roda a suite focada `tests.test_work_item_contracts`.
Quando o runtime Python local nao possui as dependencias do `compliance-api`, o runner faz fallback automatico para `docker compose run --no-deps compliance-api`, montando o worktree atual para validar a suite real em vez de retornar um falso verde por `skip`.

Para validacao operacional local ponta a ponta da trilha `work-items`, use:

```bash
make validate-work-items-runtime-local
```

O alvo sobe `postgres`, `redis` e `compliance-api`, aplica a migration `0014` e executa o smoke backend de ownership/work-items.

Se a validacao envolver `team`, `billing` ou resolucao de `linked_user_id` para atores persistidos,
aplique tambem a `0016` antes do smoke funcional correspondente.

## Quando Usar

Use migrations quando:

- o ambiente ja possui volume persistido
- surgirem erros de tabela/coluna ausente apos evolucao de schema
- o objetivo for alinhar a base sem destruir dados locais

## Quando Nao Usar

Nao dependa apenas desta pasta quando criar um ambiente totalmente novo. Nesses casos:

- suba o ambiente com `init.sql`
- depois valide que nao existe drift entre bootstrap e migrations

## Boas Praticas

- antes de criar uma migration, confirme se a mudanca tambem foi aplicada em `init.sql`
- depois de aplicar migrations, rode:
  - `python scripts/smoke_runtime.py`
  - `npx playwright test tests/e2e/critical-path.spec.ts tests/e2e/compliance-flows.spec.ts`
- evite resetar volume como solucao padrao para drift de schema
