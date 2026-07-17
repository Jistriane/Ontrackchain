# Run Sheet Operacional - Frontend em Staging no Render

## Uso

Preencher e executar esta folha durante o `sync` do blueprint `staging full-stack` no Render quando o objetivo imediato for colocar o frontend operacional atras do `gateway`.

Ela existe para:

- reduzir ambiguidade entre `gateway`, `frontend`, `auth-service` e `Keycloak`
- concentrar os checks minimos do primeiro `sync`
- validar o contrato operacional do frontend sem depender apenas do login completo
- preservar evidencias minimas antes de seguir para smoke, Playwright e `go/no-go`

Complementa:

- [Blueprint Render para Staging Full-Stack](../../render-staging-blueprint.md)
- [Deploy e Staging](../../deploy-and-staging.md)
- [GitHub Environment para Staging Serio](../../github-environment-staging-serious.md)
- [Run Sheet Operacional de `P0-01` OIDC + MFA serio](./P0-01_OIDC_MFA_RUN_SHEET.md)

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `owner_ativo`: `Platform/SRE`
- `apoio`: `Frontend` / `Backend/Auth`
- `facilitador`: `preencher`
- `bridge`: `preencher`
- `run_url`: `preencher`
- `render_blueprint_file`: `render.full-stack.yaml`

## Estado Inicial Observado

No momento desta revisao, o frontend publico de staging conhecido responde:

- `https://ontrackchain-frontend-staging.onrender.com/api/healthz`
- `deploymentModel=render-frontend-standalone-showcase`
- `hostedShowcaseFallback=true`

Interpretacao operacional:

- a vitrine publica esta navegavel
- o staging full-stack ainda nao convergiu
- o primeiro disparo real deve provar a saida desse fallback

## Checklist de GitHub Actions Antes do Primeiro Disparo

- [ ] workflow alvo confirmado: `../.github/workflows/deploy-to-production.yml`
- [ ] secret `RENDER_STAGING_DEPLOY_HOOK_URL` cadastrado em `Settings -> Secrets and variables -> Actions -> Secrets`
- [ ] variable `RENDER_STAGING_HEALTHCHECK_URL=https://ontrackchain-frontend-staging.onrender.com/api/healthz`
- [ ] variable `RENDER_STAGING_EXPECTED_DEPLOYMENT_MODEL=render-full-stack-staging`
- [ ] variable `RENDER_STAGING_ALLOW_SHOWCASE_FALLBACK=false`
- [ ] hook do Render aponta para o servico de staging real, e nao para um showcase isolado
- [ ] owner humano do disparo registrado nesta folha
- [ ] aprovacao de governanca disponivel caso o gate do workflow exija

## Checklist de Prontidao

- [ ] blueprint aberto a partir de `ontrackchain/render.full-stack.yaml`
- [ ] objetivo desta rodada limitado ao `staging full-stack` com URLs `onrender.com`
- [ ] `ontrackchain-gateway-staging` definido como unico ponto publico principal da aplicacao
- [ ] `ontrackchain-frontend-staging` configurado como `pserv`
- [ ] `ontrackchain-frontend-staging.healthCheckPath=/api/healthz`
- [ ] `APP_ENV=staging` no frontend
- [ ] `AUTH_MODE=oidc` no frontend
- [ ] `DEV_AUTH_ENABLED=false` no frontend
- [ ] `NEXT_PUBLIC_APP_ENV=staging`
- [ ] `NEXT_PUBLIC_AUTH_MODE=oidc`
- [ ] `NEXT_PUBLIC_DEV_AUTH_ENABLED=false`
- [ ] `INTERNAL_API_BASE_URL=https://ontrackchain-gateway-staging.onrender.com`
- [ ] `INTERNAL_AUTH_BASE_URL=https://ontrackchain-auth-service-staging.onrender.com`
- [ ] `INTERNAL_KEYCLOAK_BASE_URL=https://ontrackchain-keycloak-staging.onrender.com`
- [ ] `NEXT_PUBLIC_API_BASE_URL=https://ontrackchain-gateway-staging.onrender.com`
- [ ] segredos minimos do primeiro `sync` separados para `Keycloak`, `auth-service`, `monitoring-api` e `Grafana`

## Ordem de Execucao

### 1. Confirmar topologia no painel

Conferir antes do `sync`:

1. `gateway` como `web` publico
2. `frontend` como `pserv`
3. `auth-service` como `web`
4. `Keycloak` como `web`
5. `gateway -> frontend` ligado por `FRONTEND_HOSTPORT`

Registrar:

- `topology_check_status`: `pending | failed | done`
- `observacao_curta`: `preencher`

### 2. Executar o primeiro `sync`

Preencher apenas:

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `KEYCLOAK_ADMIN_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Nao preencher nesta rodada:

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`
- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `OPENSANCTIONS_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Registrar:

- `initial_sync_status`: `pending | failed | done`
- `last_service_redeployed`: `preencher`

### 3. Confirmar convergencia do frontend

Validar no painel do Render:

1. `ontrackchain-frontend-staging` saiu de `deploying`
2. health check do frontend ficou verde em `/api/healthz`
3. `ontrackchain-gateway-staging` continua verde

Registrar:

- `frontend_service_status`: `healthy | degraded | failed`
- `frontend_healthz_status`: `200 | 503 | n/a`
- `frontend_deployment_model`: `render-full-stack-staging | render-frontend-standalone-showcase | outro`
- `frontend_hosted_showcase_fallback`: `true | false | n/a`
- `frontend_missing_env_keys`: `preencher ou []`

### 3.1. Confirmar convergencia pelo endpoint publico

Executar e registrar:

```bash
curl -fsS https://ontrackchain-frontend-staging.onrender.com/api/healthz
curl -fsS https://ontrackchain-frontend-staging.onrender.com/auth/config
```

Esperado apos o primeiro disparo real:

- `/api/healthz` com `status=ok`
- `deploymentModel=render-full-stack-staging`
- `hostedShowcaseFallback=false`
- `/auth/config` sem regressao para `auth_mode=dev`
- `/auth/config` sem regressao para `app_env=test`

Registrar:

- `public_healthz_status`: `ok | degraded | failed`
- `public_deployment_model`: `render-full-stack-staging | render-frontend-standalone-showcase | outro`
- `public_hosted_showcase_fallback`: `true | false | n/a`
- `public_auth_mode`: `oidc | dev | outro | n/a`
- `public_auth_app_env`: `staging | test | outro | n/a`

### 4. Validar rotas minimas publicas

Validar:

- `https://ontrackchain-gateway-staging.onrender.com/login`
- `https://ontrackchain-auth-service-staging.onrender.com/health`
- `https://ontrackchain-keycloak-staging.onrender.com/realms/ontrackchain`

Registrar:

- `gateway_login_status`: `ok | failed`
- `auth_health_status`: `ok | failed`
- `keycloak_realm_status`: `ok | failed`

### 5. Confirmar contrato do frontend

O frontend so pode ser considerado pronto para o rito tecnico seguinte quando:

- o servico privado responde no health check do painel
- o `gateway` roteia `/login` corretamente
- `AUTH_MODE=oidc` fica coerente na UI
- nao existe drift de env obrigatoria no `/api/healthz`
- `hostedShowcaseFallback` permanece `false`; se vier `true`, trate como contingencia visual e nao como frontend `full-stack` pronto

Registrar:

- `frontend_contract_status`: `pending | failed | done`
- `auth_mode_visual`: `oidc | outro | n/a`
- `erro_observado`: `preencher ou n/a`

### 6. Passar o bastao para o rito tecnico

Quando os gates acima estiverem verdes, seguir para:

1. rito de [Deploy e Staging](../../deploy-and-staging.md)
2. smoke remoto do ambiente
3. Playwright critico
4. trilha `P0-01` quando a janela exigir prova OIDC mais forte

Registrar:

- `handoff_status`: `pending | failed | done`
- `next_owner`: `preencher`
- `next_step`: `preencher`

### 6.1. Critério explícito de no-go

Marcar `no-go` imediato se qualquer um ocorrer:

- `RENDER_STAGING_DEPLOY_HOOK_URL` ausente no GitHub
- `RENDER_STAGING_HEALTHCHECK_URL` ausente ou apontando para URL errada
- `/api/healthz` continuar em `render-frontend-standalone-showcase`
- `/api/healthz` continuar com `hostedShowcaseFallback=true`
- `/auth/config` continuar com `auth_mode=dev` ou `app_env=test`
- `missingEnvKeys` aparecer no payload do `healthz`

## Artefatos a Preservar

- screenshot do painel do Render com `ontrackchain-frontend-staging` verde
- screenshot ou log do `gateway` respondendo em `/login`
- screenshot ou log do `auth-service` respondendo em `/health`
- screenshot ou log do realm do `Keycloak`
- anotacao de qualquer `missingEnvKeys` retornada por `/api/healthz`
- link do run/deploy do Render utilizado na rodada

## Gate de Saida

Marcar esta trilha como pronta para handoff tecnico somente se todos estiverem verdadeiros:

- [ ] `frontend` convergiu no health check `/api/healthz`
- [ ] `gateway` respondeu em `/login`
- [ ] `auth-service` respondeu em `/health`
- [ ] `Keycloak` respondeu no realm
- [ ] nao houve drift de env obrigatoria no frontend
- [ ] `hostedShowcaseFallback=false` no frontend
- [ ] `deploymentModel=render-full-stack-staging` no endpoint publico
- [ ] `/auth/config` retornou `auth_mode=oidc`
- [ ] `/auth/config` retornou `app_env=staging`
- [ ] owner humano revisou as evidencias minimas

## Resultado da Janela

- `decisao_sugerida`: `go | go_with_exception | pending | no-go`
- `motivo_resumido`: `preencher`
- `maior_bloqueio`: `preencher`
- `owner_da_escalacao`: `preencher`
- `proximo_passo`: `preencher`
