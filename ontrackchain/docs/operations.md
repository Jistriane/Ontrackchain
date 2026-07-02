# Operacao Local

## Requisitos

- Docker + Docker Compose
- Python 3.11+
- Node.js 20+

## Configuracao Basica

```bash
cp .env.example .env
```

Variaveis que merecem revisao imediata:

- `AUTH_MODE`
- `DEV_AUTH_ENABLED`
- `INTERNAL_API_BASE_URL`
- `INTERNAL_AUTH_BASE_URL`
- `COMPLIANCE_TRM_*`
- `INVESTIGATION_RPC_*`
- `COMPLIANCE_OFAC_SDN_SOURCE_URL`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

## Subir a Stack

```bash
docker compose up -d --build
```

## Verificacoes Minimas

### Containers

```bash
docker compose ps
```

### Gateway

```bash
curl -fsS http://localhost:8080/
```

### Observabilidade

```bash
curl -fsS http://localhost:9091/api/v1/targets
curl -fsS http://localhost:9093/-/ready
curl -u admin:admin http://localhost:3002/api/health
```

### Runtime do projeto

```bash
python scripts/smoke_runtime.py
cd apps/frontend
npm ci
npx playwright test tests/e2e/critical-path.spec.ts tests/e2e/compliance-flows.spec.ts
```

## Migrations

Ambientes novos usam `infra/postgres/init.sql`.

Ambientes com volume persistido devem aplicar as migrations incrementais:

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
```

## Compliance e Sancoes

### Preflight de integracoes externas

```bash
python scripts/preflight_external_integrations.py
```

### Pos-sync das listas

```bash
python scripts/check_sanctions_sync_status.py
```

### Runtime do provider AML/KYT

```bash
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
```

Observacoes:

- `INTERNAL_BASE_URL` deve apontar para um endpoint que consiga resolver `GET /internal/provider-readiness`
- no host local via `docker compose`, prefira rodar o target acima de dentro da rede/container ou informar uma URL interna realmente roteavel; `localhost:8002` nao e publicado pelo `compose` atual
- `PUBLIC_BASE_URL` deve apontar para a rota publica que expoe `/api/v1/compliance/*`

## Fila Operacional Compartilhada

Primeira camada multiusuario persistida no servidor:

- backend: `apps/compliance-api/src/compliance_api/operations.py`
- proxies frontend: `apps/frontend/app/api/app/operations/work-items/*`
- tabelas: `regulatory_work_items`, `regulatory_work_events`, `regulatory_work_comments`

Validacao minima em ambiente com volume persistido:

```bash
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain \
  < infra/postgres/migrations/0013_regulatory_work_items.sql
```

Leitura operacional atual:

- `/sanctions` usa a fila compartilhada como fonte primaria e degrada para `localStorage` apenas quando o backend nao responde
- `/alerts` rastreia incidentes em `work-items` e tenta fechar o item compartilhado quando o `ack` e concluido
- os demais cockpits regulatorios ainda aguardam migracao gradual para a mesma camada

### Quando o feed da UE responder `403`

Preencha `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` com a URL XML tokenizada oficial e reexecute:

```bash
python scripts/preflight_external_integrations.py
export WINDOW_ID=stg-$(date +%F)-eu
make run-eu-sanctions-window-local WINDOW_ID=$WINDOW_ID
```

Ou, se quiser apenas a validacao pontual sem persistencia consolidada:

```bash
make check-eu-sanctions-window
```

## Janela Seria de Staging

Fluxo recomendado:

```bash
cp .env.staging.example .env.staging.private
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

Antes desse fluxo, quando a janela ainda estiver em `no-go`, usar o checklist por owner para preencher o `.env.staging.private` e o handoff por dominio:

- [Checklist de Provisionamento por Owner para Janela Seria](staging-serious-window-owner-provisioning-checklist.md)

## Troubleshooting

### 1. `sanctions-check` continua sem convergir com a documentacao

Verifique:

- `sanctions_hits_cache` populado
- `sanctions_lists_meta.last_sync_status`
- resultado de `check_sanctions_sync_status.py`
- diferenca entre endpoint direto e catalogo `operations`

### 2. Feed da UE falha com `403`

Verifique:

- se `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` foi preenchida com URL tokenizada real
- se o override persistiu em `sanctions_lists_meta.source_url`
- se o worker foi rebuildado/reexecutado

### 3. `ROS/COAF` falha com `linked_user_required_for_coaf_report`

Verifique:

- presenca de `X-Linked-User-Id`
- mapeamento correto em `external_identities`
- usuario federado resolvido para `users.id`

### 4. `block lift` falha com MFA

Verifique:

- `X-MFA-Mode=external_provider`
- `X-MFA-Provider-Homologated=true`
- usuario persistido associado ao ator federado

### 5. Drift de schema em ambiente persistido

- nao use `docker compose down -v` como correcao padrao
- prefira aplicar as migrations faltantes

### 6. `sanctions` ou `alerts` nao persistem na fila compartilhada

Verifique:

- se a migration `0013_regulatory_work_items.sql` foi aplicada no volume atual
- se o gateway/auth esta propagando `X-Org-Id`, `X-User-Id`, `X-Linked-User-Id`, `X-MFA-Mode` e `X-2FA`
- se o `compliance-api` foi rebuildado apos a adicao de `operations.py`
- se os proxies App Router em `apps/frontend/app/api/app/operations/work-items/*` estao respondendo sem `401`

## Operacao Segura de Mudancas

Quando tocar compliance/regulatorio:

- validar migrations
- validar `smoke_runtime.py`
- validar suites Playwright relevantes
- rodar `preflight_external_integrations.py` quando a mudanca envolver providers
- rodar `check_sanctions_sync_status.py` quando a mudanca envolver sync de sancoes
- rodar `make check-compliance-provider-runtime` quando a mudanca envolver homologacao `AML/KYT live`
- rodar `make run-eu-sanctions-window-local` quando a mudanca envolver a janela UE com artefatos persistidos
- aplicar `0013_regulatory_work_items.sql` quando a mudanca envolver a fila operacional compartilhada
- revisar `audit_logs` e `evidence_trail` no fluxo alterado
