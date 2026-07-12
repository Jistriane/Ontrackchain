# Primeiro Sync no Render

## Objetivo

Executar o primeiro sync do blueprint do Render com a menor chance possivel de erro operacional.

## Premissas

- o commit com o blueprint ja esta em `main`
- o arquivo canônico e `render.yaml`
- o fluxo usa `*.onrender.com`
- o primeiro deploy e de `staging`, nao de producao

## Ordem Recomendada

1. conectar o repositório `Jistriane/Ontrackchain` no Render
2. criar um novo `Blueprint` apontando para a branch `main`
3. revisar os servicos detectados a partir de [render.yaml](file:///home/jistriane/Ontrackchain/ontrackchain/render.yaml)
4. antes de confirmar o deploy, preencher todos os `sync: false`
5. disparar o sync inicial
6. validar primeiro o `Keycloak` publico
7. validar depois o gateway publico
8. validar bootstrap do banco e health checks dos servicos privados
9. executar smoke OIDC e testes criticos

## Matriz de Secrets

### `ontrackchain-auth-idp-staging`

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `KEYCLOAK_SYSTEM_USER_PASSWORD`
- `KEYCLOAK_KMD_TESTER_PASSWORD`
- `KEYCLOAK_JIBSO_ADMIN_PASSWORD`
- `KEYCLOAK_AUDITOR_PASSWORD`
- `KEYCLOAK_ANALYST_PASSWORD`
- `KEYCLOAK_VIEWER_PASSWORD`
- `KEYCLOAK_SEM_ORG_PASSWORD`

### `ontrackchain-auth-staging`

- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`

### `ontrackchain-investigation-api-staging`

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

### `ontrackchain-investigation-worker-staging`

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

### `ontrackchain-compliance-api-staging`

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`

### `ontrackchain-compliance-worker-staging`

- `OPENSANCTIONS_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

### `ontrackchain-monitoring-api-staging`

- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`

### `ontrackchain-alertmanager-staging`

- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`

### `ontrackchain-grafana-staging`

- `GF_SECURITY_ADMIN_PASSWORD`

## Checklist de Coerencia

- `KEYCLOAK_B2B_CLIENT_SECRET` deve ser o mesmo valor em `Keycloak` e nos consumidores que dependem do mesmo cadastro de cliente
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN` deve ser identico em `monitoring-api` e `alertmanager`
- `INVESTIGATION_RPC_PRIMARY_URL` e `INVESTIGATION_RPC_FALLBACK_URL` devem ser identicos em `investigation-api` e `investigation-worker`
- os subdominios assumidos no blueprint devem bater com os nomes efetivos criados pelo Render

## URLs que Devem Ser Revisadas Antes do Primeiro Deploy

- `https://ontrackchain-staging.onrender.com`
- `https://ontrackchain-auth-idp-staging.onrender.com`
- `OIDC_ISSUER_URL`
- `OIDC_JWKS_URL`
- `OIDC_AUTHORIZATION_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `ONTRACKCHAIN_PUBLIC_BASE_URL`
- `KEYCLOAK_PUBLIC_URL`

## Validacao Imediata Pos-Sync

### 1. Keycloak

- abrir `https://ontrackchain-auth-idp-staging.onrender.com/realms/ontrackchain/.well-known/openid-configuration`
- confirmar `200 OK`
- confirmar que o `issuer` retornado bate com a URL publica real

### 2. Gateway

- abrir `https://ontrackchain-staging.onrender.com/auth/config`
- confirmar `200 OK`
- confirmar `effective_auth_mode=oidc`

### 3. Frontend

- abrir `https://ontrackchain-staging.onrender.com/login`
- confirmar que o login OIDC carrega sem erro de runtime

### 4. Banco

- verificar logs do `ontrackchain-auth-staging`
- confirmar que `apply_postgres_bootstrap.py` concluiu sem erro
- confirmar que nao houve falha em `preDeployCommand`

### 5. APIs

- verificar `health` de `auth-service`, `public-api`, `investigation-api`, `compliance-api`, `monitoring-api` e `report-api`

## Smoke Recomendado

Depois que o ambiente responder:

```bash
ONTRACKCHAIN_EXPECTED_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_APP_ENV=staging \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED=false \
python3 scripts/smoke_auth_oidc_mode.py
```

E depois:

```bash
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
```

## Falhas Mais Provaveis

- subdominio real do Render diferente do previsto no blueprint
- `KEYCLOAK_PUBLIC_URL` ou `ONTRACKCHAIN_PUBLIC_BASE_URL` desalinhados com a URL real
- `issuer` OIDC nao batendo com o callback do frontend
- token de webhook do Alertmanager diferente entre `alertmanager` e `monitoring-api`
- `preDeployCommand` do `auth-service` falhando por conectividade ou permissao no Postgres
- custo/limite operacional do primeiro sync por quantidade de servicos `starter`

## Decisao Operacional

- se `Keycloak` e `gateway` responderem, continue para smoke e E2E
- se `Keycloak` responder mas `/auth/config` falhar, investigue `auth-service` e `gateway`
- se o bootstrap do banco falhar, nao tente corrigir pelo frontend; trate primeiro `auth-service` e Postgres
