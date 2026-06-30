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
