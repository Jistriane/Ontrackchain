# auth-service

Serviço FastAPI de autenticação e identidade — OIDC federado (Keycloak), identidades locais, MFA TOTP (YubiKey/WebAuthn para Strong Auth), RBAC 9 roles canônicas e sincronização de grupos/claims para o monorepo.

## Portas e base path

- Porta padrão: `9000`
- Base path: `/api/v1/auth`
- Endpoints públicos bypass RLS: `/auth/dev-token`, `/auth/login`, `/auth/callback`, `/auth/sso/login`, `/auth/sso/callback`, `/healthz`, `/metrics`, `/openapi.json`, `/docs`.

## Features principais

| Feature | Detalhe |
|---|---|
| Identity | OIDC federado (Keycloak default `auth.localhost:8080/realms/ontrackchain`) + usuários locais BCrypt |
| MFA | TOTP padrão RFC 6238 (período 30s, 6 dígitos, janela ±1). Strong Auth WebAuthn para roles legais (ADR-004) |
| RBAC | 9 roles canônicas do `CanonicalRole` (OTK_ADMIN, OTK_ANALYST, OTK_COMPLIANCE_OFFICER, OTK_LEGAL_REVIEWER, OTK_AUDITOR, OTK_VIEWER, …) |
| JWT | HS256 dev / RS256 + JWKS em produção. Claims obrigatórios: `organization_id`, `otk_role`, `plan`. |
| Token lifecycle | Access token (audience = `OTK_AUDIENCE`); refresh token c/ rotação; device tracking básico. |

## Banco e RLS

Auth-service **NÃO seta** `app.organization_id` no RLS (login não tem org ainda); pós-autenticação, emite claim `organization_id` para os outros serviços setarem contexto via middleware RLS.

Migrações relevantes:

- `0001_auth_schema_users_roles.sql` (tabelas users, local_credentials, mfa_factors)
- `0005_federated_sync.sql` (tabelas `federated_identities` + sync cron Keycloak SCIM)

## Headers exigidos pós-login (para apps internos)

- `Authorization: Bearer <jwt>`
- `X-Organization-Id` (opcional: se omitido, pega claim do JWT)
- `X-Role` (opcional: fallback inline RBAC ADR-018 se JWT inválido/missing em dev)

## Desenvolvimento local (fora do Docker)

No diretório do monorepo, com Python 3.11+:

```bash
python3 -m pip install -U pip
python3 -m pip install -e "ontrackchain/apps/auth-service[dev,mfa]"
```

Rodar API:

```bash
# dev mode: identidades locais + MFA TOTP + DEV_AUTH_ENABLED=true (sem OIDC)
export DEV_AUTH_ENABLED=true
export JWT_HS256_SECRET=change-me
export MFA_TOTP_SECRET=JBSWY3DPEHPK3PXP
uvicorn auth_service.main:app --host 0.0.0.0 --port 9000
```

Para modo OIDC federado:

```bash
export OIDC_PROVIDER=keycloak
export OIDC_ISSUER_URL=http://auth.localhost:8080/realms/ontrackchain
export OIDC_JWKS_URL=http://keycloak:8080/realms/ontrackchain/protocol/openid-connect/certs
export INTERNAL_KEYCLOAK_BASE_URL=http://keycloak:8080
uvicorn auth_service.main:app --host 0.0.0.0 --port 9000
```

## Docker

Recomendado: subir via `ontrackchain/docker-compose.yml` (já tem Postgres + Redis + Keycloak + Traefik).

Build:

```bash
docker build -f ontrackchain/apps/auth-service/Dockerfile -t ontrackchain-auth-service .
```

Rodar standalone (DEV_AUTH_ENABLED):

```bash
docker run --rm -p 9000:9000 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=ontrackchain \
  -e POSTGRES_PASSWORD=ontrackchain \
  -e POSTGRES_DB=ontrackchain \
  -e DEV_AUTH_ENABLED=true \
  -e JWT_HS256_SECRET=change-me \
  ontrackchain-auth-service
```

## Variáveis de ambiente

Ver `.env.example` neste diretório (Sprint S28+23). Principais:

- Obrigatórias: `POSTGRES_*`, `JWT_HS256_SECRET` (dev) **ou** `OIDC_JWKS_URL` (prod).
- MFA: `MFA_TOTP_SECRET`, `MFA_TOTP_ISSUER`, `MFA_EXTERNAL_PROVIDER_HOMOLOGATED`.
- Keycloak (federado): `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`, `KEYCLOAK_REALM`.

## Observabilidade

- `/healthz` → RFC 9292 `application/health+json; charset=utf-8`, status=`pass`, `releaseId=3.1.0-m5`.
- `/metrics` → Prometheus `prometheus_fastapi_instrumentator` (se disponível) + fallback inline com `fastapi_info{version="3.1.0-m5"}`.
- Rate limit: 4 rotas de autenticação pública têm rate limit ADR-014 via `rbac_guard.rate_limit_response()`.
