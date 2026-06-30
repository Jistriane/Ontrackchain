# Operacao Local

## Requisitos

- Docker + Docker Compose
- Python 3.11+ para rodar o smoke localmente
- Node.js 20+ para Playwright local

## Configuracao

Copie e ajuste o arquivo de ambiente se necessario:

```bash
cp .env.example .env
```

Variaveis principais:

- `POSTGRES_*`
- `REDIS_*`
- `TRAEFIK_HTTP_PORT`
- `TRAEFIK_DASHBOARD_PORT`
- `PROMETHEUS_PORT`
- `GRAFANA_PORT`
- `ALERTMANAGER_PORT`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `APP_ENV`
- `JWT_*`
- `DEV_AUTH_ENABLED`
- `CREDIT_VALUE_BRL`
- `INTERNAL_API_BASE_URL`
- `INTERNAL_AUTH_BASE_URL` (override opcional para proxies server-side do frontend)

Observacoes:

- `scripts/smoke_runtime.py` le `.env` automaticamente para resolver os ports do stack local antes de consultar Prometheus, Grafana e Alertmanager
- o baseline atual do repositório usa `PROMETHEUS_PORT=9091` e `GRAFANA_PORT=3002` para reduzir colisao com outras stacks locais

Recomendacao de ambiente serio:

- usar `APP_ENV=staging` ou `APP_ENV=production`
- preferir `AUTH_MODE=oidc`
- garantir `DEV_AUTH_ENABLED=false`

## Subir a Stack

```bash
docker compose up -d --build
```

## Verificar a Stack

### Containers

```bash
docker compose ps
```

### Gateway

```bash
curl -fsS http://localhost:8080/
```

### Prometheus

```bash
curl -fsS http://localhost:9091/api/v1/targets
curl -fsS http://localhost:9091/api/v1/rules
```

Targets esperados:

- `investigation-api`
- `monitoring-api`
- `compliance-api`
- `report-api`

### Alertmanager

```bash
curl -fsS http://localhost:9093/-/ready
curl -fsS http://localhost:9093/api/v2/alerts
```

### Grafana

```bash
curl -u admin:admin http://localhost:3002/api/health
curl -u admin:admin http://localhost:3002/api/dashboards/uid/ontrack-investigation-operations
curl -u admin:admin http://localhost:3002/api/dashboards/uid/ontrack-monitoring-operations
curl -u admin:admin http://localhost:3002/api/dashboards/uid/ontrack-compliance-operations
curl -u admin:admin http://localhost:3002/api/dashboards/uid/ontrack-report-operations
curl -u admin:admin http://localhost:3002/api/dashboards/uid/ontrack-platform-alerting
```

### Dashboard do Traefik

```bash
open http://localhost:8081
```

## Portas

- `8080`: gateway/app
- `8081`: dashboard Traefik
- `9091`: Prometheus
- `9093`: Alertmanager
- `3002`: Grafana
- `5432`: PostgreSQL
- `6379`: Redis

## Servicos

| Servico | Porta interna | Papel |
| --- | ---: | --- |
| `auth-service` | `9000` | auth e contexto |
| `public-api` | `8000` | endpoints publicos/rate limit |
| `investigation-api` | `8001` | investigacao + billing + audit |
| `compliance-api` | `8002` | compliance + reports |
| `monitoring-api` | `8003` | watchlists + alerts |
| `report-api` | `8004` | geracao/download de relatorios |
| `frontend` | `3000` | UI + proxies internos |
| `prometheus` | `9091` | scraping central + regras de alerta |
| `alertmanager` | `9093` | roteamento de alertas para receiver interno |
| `grafana` | `3000` | dashboards operacionais provisionados |

## Fluxo de Desenvolvimento

### Rebuild completo

```bash
docker compose up -d --build
```

### Rebuild de um servico especifico

```bash
docker compose up -d --build report-api
docker compose up -d --build frontend
```

- `frontend` no `docker compose` usa explicitamente o target `dev` do `Dockerfile`
- para validar a imagem de runtime do frontend isoladamente:

```bash
docker build --target runtime -t ontrackchain-frontend-runtime ./apps/frontend
```

### Logs

```bash
docker compose logs -f report-api
docker compose logs -f investigation-api
docker compose logs -f frontend
```

### Shell no banco

```bash
docker compose exec postgres psql -U ontrackchain -d ontrackchain
```

### Backup e Restore Baseline

```bash
bash scripts/backup_postgres.sh
RESTORE_TARGET_DB=ontrackchain_restore_check bash scripts/restore_postgres.sh artifacts/backups/<arquivo>.dump
```

- `backup_postgres.sh` gera dump logico em formato custom do PostgreSQL
- `backup_postgres.sh` grava manifesto estruturado em `${ARQUIVO_DUMP}.manifest.json`
- `restore_postgres.sh` restaura por padrao em banco isolado `${POSTGRES_DB}_restore_check`
- `restore_postgres.sh` grava manifesto estruturado em `${ARQUIVO_DUMP}.restore.${RESTORE_TARGET_DB}.manifest.json`
- restore no banco principal exige `ONTRACKCHAIN_RESTORE_CONFIRM=OVERWRITE_MAIN_DB`
- registrar o `rto_seconds`, o `sha256` e o caminho do manifesto como evidencia minima de recovery

## Bootstrap de Banco

- Ambientes novos usam `infra/postgres/init.sql`
- Ambientes com volume persistido devem usar migrations incrementais

Comandos atuais:

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

## Reset de Ambiente

Use apenas quando quiser descartar os dados locais:

```bash
docker compose down -v
docker compose up -d --build
```

Nao use esse fluxo para corrigir drift de schema em ambiente que precisa preservar volume. Nesses casos, prefira as migrations.

## Troubleshooting

### 1. Gateway responde `404` para rota nova

Verifique:

- se a rota existe em `infra/traefik/dynamic.yml`
- se o servico foi rebuildado
- se o path esta coberto por `PathPrefix`

### 2. Erros de tabela/coluna ausente

Provavel causa:

- volume antigo com schema desatualizado

Acao:

- aplicar migrations incrementais
- evitar resetar volume sem necessidade

### 3. `401` em login/session start

Verifique:

- `auth-service` no ar
- `INTERNAL_API_BASE_URL=http://traefik`
- payload do `/auth/issue-dev-token`

### 4. `404` em billing/audit

Verifique:

- roteadores `billing` e `audit` no `dynamic.yml`

### 5. Export de incidentes operacionais falha com `401` ou sem download

Verifique:

- `frontend` rebuildado apos mudanca no proxy server-side
- conectividade interna do `frontend` com `auth-service:9000`
- override `INTERNAL_AUTH_BASE_URL` quando o runtime nao usa a rede padrao do compose
- se o request chega com cookie `otc_token`
- se o export recebe `X-Org-Id` e `X-User-Id` apos validacao no `auth-service`

### 6. `403` em `legal_report`

Esperado quando:

- auth nao e `jwt`
- role nao e `ADMIN`
- `2FA` nao esta em `ok`

### 7. Playwright falha por artefatos/relatorio

O `playwright.config.ts` ja usa:

- `playwright-report/`
- `test-results/junit.xml`

Se necessario, limpe artefatos antigos:

```bash
rm -rf apps/frontend/playwright-report apps/frontend/test-results
```

### 8. Gate OIDC critico antes da regressao completa

Para mudancas em autenticacao, proxy, RBAC ou identidade federada, rode primeiro o gate focado e depois a regressao inteira:

```bash
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
npm run test:e2e
```

### 9. Regressao local de dev auth e TOTP

Esse fluxo existe apenas para validar o scaffold legado em `AUTH_MODE=dev`. Nao substitui o gate OIDC e nao deve ser tratado como criterio de promocao para ambiente serio.

```bash
cd ontrackchain
AUTH_MODE=dev \
DEV_AUTH_ENABLED=true \
NEXT_PUBLIC_AUTH_MODE=dev \
NEXT_PUBLIC_DEV_AUTH_ENABLED=true \
docker compose up -d --build

cd apps/frontend
npm ci
npm run test:e2e:dev-auth
```

## Operacao Segura de Mudancas

### Quando mudar schema

- atualizar `init.sql`
- criar migration correspondente
- validar no ambiente com volume persistido

### Quando mudar autenticacao/proxy

- validar smoke
- validar gate `test:e2e:oidc-critical`
- validar regressao `test:e2e`
- validar `test:e2e:dev-auth` apenas quando a mudanca tocar o fluxo local/TOTP
- checar `audit_logs` e `report_downloaded`
- validar `/audit`
- validar export administrativo de incidentes globais com `request_id`

### Quando mudar observabilidade

- validar `GET /internal/metrics/prometheus` via container `investigation-api`
- validar `GET /internal/metrics/prometheus` via container `monitoring-api`
- validar `GET /internal/metrics/prometheus` via container `compliance-api`
- validar `GET /internal/metrics/prometheus` via container `report-api`
- validar `http://localhost:9091/api/v1/targets`
- validar `http://localhost:9091/api/v1/rules`
- validar `http://localhost:9093/-/ready`
- validar `http://localhost:9093/api/v2/alerts`
- validar `http://localhost:3002/api/health`
- validar dashboard `ontrack-investigation-operations`
- validar dashboard `ontrack-monitoring-operations`
- validar dashboard `ontrack-compliance-operations`
- validar dashboard `ontrack-report-operations`
- validar dashboard `ontrack-platform-alerting`
- validar UI administrativa `/monitoring` com a secao `Incidentes Globais de Plataforma`
- validar triagem manual `pending -> acknowledged` em `/monitoring`
- confirmar que `status` tecnico (`firing|resolved`) permanece separado de `triage_status` (`pending|acknowledged`)
- validar navegacao `Anterior/Proxima` da lista paginada de incidentes globais
- validar filtros dinamicos de `service` e `receiver` em `/monitoring`
- validar export `CSV|JSON` do recorte administrativo e dos incidentes selecionados
- confirmar `operational_alerts_exported` em `audit_logs` com o mesmo `request_id`

### Quando mudar billing

- validar:
  - `estimate`
  - `start`
  - `PRE_HOLD`
  - `CONFIRMED/REFUND`
  - `plan lock`

## Checklist Operacional

- stack sobe com `docker compose up -d --build`
- gateway responde em `:8080`
- smoke passa
- Playwright passa
- migrations estao alinhadas com `init.sql`
- rotas novas estao refletidas no Traefik
- fluxos sensiveis continuam auditados
- export administrativo de incidentes operacionais continua funcional e auditado
