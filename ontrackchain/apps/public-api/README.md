# public-api

Porta aberta externamente (B2B Enterprise + telas públicas do Next.js Frontend) — screens estruturais leves, status de cadeias suportadas, cotação de plano pública, WebAuthn Strong Auth (L3 reCAPTCHA + HMAC timing-safe) e B2B API Keys HMAC-SHA256 (ADR-019).

## Portas e base path

- Porta padrão: `8000`
- Base path: `/api/v1/public`
- Rota `/healthz` e `/metrics` são públicas (bypass RLS total).

## Domínios de responsabilidade

| Rota pública | Descrição | Auth |
|---|---|---|
| `GET /api/v1/public/chains/supported` | Cadeias suportadas (eth, polygon, bsc, arbitrum, base, btc) | Nenhuma |
| `GET /api/v1/public/plans/catalog` | Planos free/starter/professional/enterprise + pricing_table_hash | Nenhuma |
| `GET /api/v1/public/plan/minimum-for-report-type/{t}` | Plano mínimo por tipo de relatório (RIPD Art.15 etc.) | Nenhuma |
| `POST /api/v1/public/b2b/screening/lite` | Screen rápido B2B via `X-B2B-Api-Key` HMAC | HMAC Header (ADR-019) |
| `POST /api/v1/public/rate-limit-demo/429` | Demonstração headers Retry-After + 3× X-RateLimit | Nenhuma (rate limited) |

## Headers de segurança

- CORS: origens controladas (não wildcard em staging/prod).
- HSTS + Content-Security-Policy: configurados via middleware no Traefik.
- `X-B2B-Timestamp` + `X-B2B-Signature` = HMAC-SHA256 timing-safe para chamadas B2B Enterprise (ADR-019).

## Rate Limit (ADR-014)

Duas rotas públicas (`/plans/catalog` + `/b2b/screening/lite`) aplicam:

```
X-RateLimit-Limit: <cap>
X-RateLimit-Remaining: <n>
X-RateLimit-Reset: <unix epoch>
Retry-After: <seconds>
```

Implementação via `ontrackchain_shared.rbac_guard.rate_limit_response()` SSOT (Sprint S28+18/19 SharedFirst pattern).

## Banco e RLS

Apenas 2 endpoints de mutação B2B usam RLS: o restante é read-only e lê dados de catálogo estático / tabelas `public_*` sem contexto de organização. Middleware RLS injeta org_id apenas se header/cookie existir.

Migrações relevantes:

- `0021_public_api_b2b_api_keys.sql` (tabela `b2b_api_keys` com key_hash HMAC + rate tiers)
- `0022_public_rate_limit_events.sql` (tabela `rate_limit_events` p/ auditoria)

## Desenvolvimento local (fora do Docker)

No diretório do monorepo, com Python 3.11+:

```bash
python3 -m pip install -U pip
python3 -m pip install -e "ontrackchain/apps/public-api[dev,b2b]"
```

Rodar API:

```bash
export INTERNAL_API_BASE_URL=http://localhost:8080
export INTERNAL_AUTH_BASE_URL=http://localhost:9000
export JWT_HS256_SECRET=change-me
uvicorn public_api.main:app --host 0.0.0.0 --port 8000
```

## Docker

Build:

```bash
docker build -f ontrackchain/apps/public-api/Dockerfile -t ontrackchain-public-api .
```

Rodar standalone:

```bash
docker run --rm -p 8000:8000 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=ontrackchain \
  -e POSTGRES_PASSWORD=ontrackchain \
  -e POSTGRES_DB=ontrackchain \
  -e INTERNAL_API_BASE_URL=http://traefik:80 \
  -e INTERNAL_AUTH_BASE_URL=http://auth-service:9000 \
  ontrackchain-public-api
```

## Variáveis de ambiente

Ver `.env.example` neste diretório (Sprint S28+23). Principais:

- `PUBLIC_API_PORT` = 8000
- `INTERNAL_API_BASE_URL`, `INTERNAL_AUTH_BASE_URL` = URLs internas para serviços auth/compliance/investigation.
- `B2B_API_KEY_SECRET_PEPPER` = HMAC pepper extra para hash de chaves B2B.

## Observabilidade

- `/healthz` → RFC 9292 `application/health+json; charset=utf-8`, `releaseId=3.1.0-m5`.
- `/metrics` → Prometheus + fallback inline `fastapi_info{version="3.1.0-m5"}`.
- `429 Too Many Requests` retornam `rate_limit_response()` com 3 headers X-RateLimit + `Retry-After`.
