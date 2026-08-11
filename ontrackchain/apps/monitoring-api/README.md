# monitoring-api

Serviço FastAPI **OnTrackChain Monitoring API** (v3.1.0-m5) — parte da plataforma Ontrackchain Regtech.

## Portas e base path

- Porta padrão: `8003` (Docker EXPOSE 8003)
- Base path (root_path): `/api/v1/monitoring`

## Banco e RLS

Usa Postgres com RLS **multi-tenant** habilitado em todas tabelas de domínio. Contexto injetado por `make_rls_context_middleware()` (ADR-018 Shared-First): `set_config('app.organization_id', $org_id, true)` via psycopg3.

Headers exigidos em rotas autenticadas (bypass em `/healthz`, `/metrics`, `/docs`, `/openapi.json`):

- `X-Org-Id` (obrigatório, UUID v4)
- `Authorization: Bearer <jwt>` OU fallback `X-Role` header inline (dev only, ADR-018)
- `X-User-Id` (opcional, para trilha de auditoria)

Migrações relevantes (fonte: `packages/qa-gateway/migrations/`):

- Nenhuma migração específica mapeada ainda.

## Principais features

| Feature | Detalhe |
|---|---|
| Alertmanager webhook → platform_alerts | Alertmanager webhook → platform_alerts |
| Operational Alerts | Operational Alerts (trigger, acknowledge batch) |
| Watchlists | Watchlists (items) |
| Grafana Alert → monitoring_api ingestion | Grafana Alert → monitoring_api ingestion |
| Acknowledge triage | Acknowledge triage (severity P0/P1/P2) |

## Desenvolvimento local (fora do Docker)

Python 3.11+ no diretório raiz do monorepo:

```bash
python3 -m pip install -U pip
python3 -m pip install -e "ontrackchain/apps/monitoring-api[dev,monitoring]"
```

Rodar API via uvicorn:

```bash
cd ontrackchain/apps/monitoring-api
uvicorn monitoring_api.main:app --host 0.0.0.0 --port 8003 --reload
```

## Docker

Build standalone (imagem alvo 1 serviço):

```bash
docker build -f ontrackchain/apps/monitoring-api/Dockerfile -t ontrackchain-monitoring-api .
```

Rodar com conexão PG/Redis do docker-compose:

```bash
docker run --rm -p 8003:8003 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=ontrackchain \
  -e POSTGRES_PASSWORD=ontrackchain \
  -e POSTGRES_DB=ontrackchain \
  ontrackchain-monitoring-api
```

Stack completa recomendada: subir via `ontrackchain/docker-compose.yml` (PG + Redis + 9 serviços + frontend Next.js).

## Observabilidade (ADR-018 + M16b)

| Endpoint | Propósito |
|---|---|
| `GET /healthz` | liveness/readiness probe k8s. Retorno `application/health+json; charset=utf-8` (RFC 9292). Bypass RLS. |
| `GET /metrics` | Prometheus scraper (contadores RBAC, RLS, HTTP latência). Bypass RLS. |
| `GET /docs` | Swagger OpenAPI 3.1 (apenas `APP_ENV=dev/qa`). Bypass RLS. |

## Variáveis de ambiente

Referência completa em [.env.example](./.env.example). Principais blocos:

- **Runtime**: `APP_ENV=(dev\|qa\|staging\|prod)`, `MONITORING_API_PORT`
- **Postgres**: `POSTGRES_HOST/PORT/USER/PASSWORD/DB`
- **Redis**: `REDIS_HOST/REDIS_PORT` (rate limit ADR-014)
- **RBAC/JWT**: `JWT_ISSUER`, `JWT_HS256_SECRET` (dev), `OIDC_JWKS_URL` (prod), `OTK_AUDIENCE`

## Testes

Pytest cobre RBAC, endpoints principais, casos de erro (401/403/404). Para rodar:

```bash
cd ontrackchain/apps/monitoring-api
python3 -m pip install -e ".[dev]"
python3 -m pytest tests -q --tb=short
```
