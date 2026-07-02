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
```

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
