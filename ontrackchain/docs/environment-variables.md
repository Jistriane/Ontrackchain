# Variaveis de Ambiente

## Objetivo

Documentar as variaveis de ambiente relevantes do scaffold atual e como elas se distribuem por servico.

Fonte principal:

- [`.env.example`](../.env.example)
- [`.env.staging.example`](../.env.staging.example)
- [Ownership do `.env.staging`](staging-env-ownership.md)
- [`docker-compose.yml`](../docker-compose.yml)
- classes `Settings` dos servicos

Template serio para homologacao:

- use [`.env.staging.example`](../.env.staging.example) como baseline de `staging` para OIDC, AML/KYT e RPC
- o arquivo assume `APP_ENV=staging`, `AUTH_MODE=oidc`, `DEV_AUTH_ENABLED=false`, `COMPLIANCE_TRM_ENABLED=true` e `INVESTIGATION_RPC_ENABLED=true`
- todos os campos `__FILL_*__` devem ser substituidos por secrets/URLs reais antes de rodar `preflight_oidc_serious_env.py`, `preflight_external_integrations.py` e `homologation_external_evidence.py`
- execute `python3 scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md` para garantir que nenhum placeholder novo entrou no baseline sem owner, apoio e evidencia
- execute `python3 scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md` para registrar um pacote redigido da janela antes do preenchimento do `.env.staging.private`
- execute `python3 scripts/check_staging_env_placeholders.py --file .env.staging.private` antes dos preflights para bloquear placeholders, ausencias e valores vazios em chaves criticas
- distribua cada placeholder `__FILL_*__` conforme a matriz em [Ownership do `.env.staging`](staging-env-ownership.md) antes do preenchimento
- execute `python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` antes da janela para validar que todos os grupos obrigatorios sairam de `pending`
- persista os JSONs desses checkers em `artifacts/staging/checks/` para que possam ser consolidados depois por `python3 scripts/build_staging_release_dossier.py`
- para executar a janela ponta a ponta e persistir checks, preflights, homologacao e dossier em uma unica chamada, prefira `python3 scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private`

## Variaveis Globais

| Variavel | Padrao | Uso |
|---|---|---|
| `COMPOSE_PROJECT_NAME` | `ontrackchain` | nome do projeto docker |
| `TRAEFIK_HTTP_PORT` | `8080` | porta publica do gateway |
| `TRAEFIK_DASHBOARD_PORT` | `8081` | porta do dashboard Traefik |
| `PROMETHEUS_PORT` | `9091` | porta publica local do Prometheus |
| `GRAFANA_PORT` | `3002` | porta publica local do Grafana |
| `ALERTMANAGER_PORT` | `9093` | porta publica local do Alertmanager |
| `APP_ENV` | `local` | classifica o ambiente (`local`, `test`, `staging`, `production`) |
| `AUTH_MODE` | `dev` | modo global de autenticacao do scaffold |
| `DEV_AUTH_ENABLED` | vazio ou `true` em local | gate explicito para permitir auth dev fora do fallback por ambiente |
| `NEXT_PUBLIC_AUTH_MODE` | `dev` | modo de auth exposto ao frontend |
| `NEXT_PUBLIC_APP_ENV` | `local` | ambiente exposto ao frontend para fallback de UX |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | vazio ou `true` em local | gate publico de auth dev usado no fallback da UI |
| `OIDC_PROVIDER` | `keycloak` | preset de provider OIDC (`generic`, `keycloak`, `auth0`, `entra`) |
| `KEYCLOAK_PUBLIC_URL` | `http://auth.localhost:8080` | URL publica esperada do Keycloak no scaffold local |
| `KEYCLOAK_HOSTNAME` | `auth.localhost` | hostname usado pelo router do Traefik para o Keycloak local |
| `KEYCLOAK_HTTP_PORT` | `8088` | porta direta opcional para admin/debug do Keycloak local |
| `KEYCLOAK_ADMIN` | `admin` | usuario administrativo inicial do Keycloak |
| `KEYCLOAK_ADMIN_PASSWORD` | `admin` | senha administrativa inicial do Keycloak |
| `KEYCLOAK_REALM` | `ontrackchain` | realm importado pelo scaffold local |
| `KEYCLOAK_B2B_CLIENT_SECRET` | `change-me-b2b-secret` | secret de referencia do client `ontrackchain-b2b` |
| `INTERNAL_KEYCLOAK_BASE_URL` | `http://keycloak:8080` | base URL interna usada pelo frontend server-side para `token exchange` OIDC |
| `CREDIT_VALUE_BRL` | `1.0` | valor base do credito em BRL |

## Banco de Dados

| Variavel | Padrao | Uso |
|---|---|---|
| `POSTGRES_HOST` | `postgres` | host do banco |
| `POSTGRES_PORT` | `5432` | porta do banco |
| `POSTGRES_USER` | `ontrackchain` | usuario do banco |
| `POSTGRES_PASSWORD` | `ontrackchain` | senha do banco |
| `POSTGRES_DB` | `ontrackchain` | nome do banco |

Servicos que usam:

- `auth-service`
- `investigation-api`
- `compliance-api`
- `monitoring-api`
- `report-api`

## Redis

| Variavel | Padrao | Uso |
|---|---|---|
| `REDIS_HOST` | `redis` | host do Redis |
| `REDIS_PORT` | `6379` | porta do Redis |
| `INVESTIGATION_WORKER_PROCESSING_SECONDS` | `2` | tempo simulado de execucao do worker |
| `INVESTIGATION_WORKER_LOCAL_CONCURRENCY` | `8` | paralelismo local do container `investigation-worker` |
| `INVESTIGATION_WORKER_BASE_BACKOFF_SECONDS` | `5` | backoff base para retries do worker |
| `INVESTIGATION_INTERNAL_METRICS_ENABLED` | `true` | habilita endpoint interno agregado para scraping do Prometheus |
| `INVESTIGATION_RPC_PROVIDER` | `evm_rpc` | provider RPC primario esperado pelo worker de investigation |
| `INVESTIGATION_RPC_ENABLED` | `false` | habilita integracao RPC explicita no worker de investigation |
| `INVESTIGATION_RPC_PRIMARY_URL` | vazio | URL primaria do provider RPC |
| `INVESTIGATION_RPC_FALLBACK_URL` | vazio | URL secundaria para fallback de RPC |
| `INVESTIGATION_RPC_TIMEOUT_MS` | `1500` | timeout por tentativa do provider RPC |
| `INVESTIGATION_RPC_MAX_RETRIES` | `1` | numero maximo de retries por provider RPC antes do fallback |
| `MONITORING_INTERNAL_METRICS_ENABLED` | `true` | habilita endpoint interno agregado do monitoring para scraping do Prometheus |
| `MONITORING_ALERTS_LAST_HOUR_WARN_THRESHOLD` | `5` | limiar de alerta para pico recente de alertas de monitoring |
| `MONITORING_CRITICAL_ALERTS_LAST_24H_CRITICAL_THRESHOLD` | `1` | limiar critico para alertas criticos recentes em monitoring |
| `MONITORING_EXPIRED_QUOTES_WARN_THRESHOLD` | `10` | limiar de alerta para backlog de quotes expirados |
| `MONITORING_OPEN_QUOTES_WARN_THRESHOLD` | `25` | limiar de alerta para quotes em aberto |
| `ALERTMANAGER_WEBHOOK_BEARER_TOKEN` | `alertmanager-local-token` | token interno compartilhado entre `Alertmanager` e receiver do `monitoring-api` |
| `COMPLIANCE_INTERNAL_METRICS_ENABLED` | `true` | habilita endpoint interno agregado de compliance para scraping do Prometheus |
| `COMPLIANCE_QUEUED_CASES_WARN_THRESHOLD` | `5` | limiar de alerta para backlog de casos de compliance em queued |
| `COMPLIANCE_FAILED_LAST_24H_CRITICAL_THRESHOLD` | `1` | limiar critico para falhas recentes em compliance |
| `COMPLIANCE_EXPIRED_QUOTES_WARN_THRESHOLD` | `10` | limiar de alerta para backlog de quotes expirados de compliance |
| `COMPLIANCE_COMPLETED_WITHOUT_REPORT_WARN_THRESHOLD` | `3` | limiar para casos concluidos sem relatorio persistido |
| `COMPLIANCE_PROVIDER_DEGRADED_WARN_THRESHOLD` | `1` | limiar para abrir alerta operacional quando o provider AML/KYT entra em degradacao |
| `COMPLIANCE_RISK_PROVIDER` | `trm_labs` | provider primario esperado para `risk-check`; valores nao suportados degradam com `provider_unsupported` |
| `COMPLIANCE_TRM_ENABLED` | `false` | habilita tentativa de chamada externa do adapter TRM |
| `COMPLIANCE_TRM_SCREENING_URL` | vazio | URL completa do endpoint de screening do provider |
| `COMPLIANCE_TRM_API_KEY` | vazio | credencial do provider AML/KYT |
| `COMPLIANCE_TRM_API_KEY_HEADER` | `Authorization` | nome do header usado para enviar a credencial |
| `COMPLIANCE_TRM_API_KEY_PREFIX` | `Bearer ` | prefixo aplicado antes da credencial no header |
| `COMPLIANCE_TRM_TIMEOUT_MS` | `1500` | timeout por tentativa do provider AML/KYT |
| `COMPLIANCE_TRM_MAX_RETRIES` | `1` | numero maximo de retries no adapter de `risk-check` |
| `COMPLIANCE_OFAC_SDN_SOURCE_URL` | vazio | override opcional do `source_url` persistido em `sanctions_lists_meta` para o feed OFAC/SDN; o worker aplica o valor antes do sync |
| `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` | vazio | override opcional do `source_url` persistido em `sanctions_lists_meta` para o feed EU; use para URLs XML tokenizadas obtidas no portal oficial |
| `REPORT_INTERNAL_METRICS_ENABLED` | `true` | habilita endpoint interno agregado de report para scraping do Prometheus |
| `REPORT_DOWNLOADS_LAST_24H_WARN_THRESHOLD` | `10` | limiar de alerta para volume alto de downloads de relatorio |
| `REPORT_PENDING_ONCHAIN_WARN_THRESHOLD` | `3` | limiar para backlog de hash on-chain pendente |
| `REPORT_LEGAL_DOWNLOAD_SECURITY_VIOLATION_THRESHOLD` | `1` | limiar critico para download juridico auditado sem 2FA valido |
| `REPORT_PERSISTED_WITHOUT_DOWNLOAD_WARN_THRESHOLD` | `3` | limiar para relatorios persistidos ainda sem download auditado |
| `GRAFANA_ADMIN_USER` | `admin` | usuario local do Grafana |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | senha local do Grafana |
| `GRAFANA_ANONYMOUS_ENABLED` | `false` | habilita acesso anonimo ao Grafana no ambiente local |
| `GRAFANA_DISABLE_LOGIN_FORM` | `false` | desabilita formulario de login quando houver auth externa |

Servicos que usam:

- `public-api`
- `investigation-api` via compose
- `investigation-worker`
- `monitoring-api`

## JWT/Auth

| Variavel | Padrao | Uso |
|---|---|---|
| `JWT_ISSUER` | `ontrackchain` | emissor do token |
| `JWT_AUDIENCE` | `ontrackchain` | audiencia do token |
| `JWT_HS256_SECRET` | `change-me` | segredo HS256 |
| `MFA_TOTP_SECRET` | `JBSWY3DPEHPK3PXP` | segredo base32 do TOTP usado no 2FA real do scaffold |
| `MFA_TOTP_ISSUER` | `OnTrackChain` | issuer exibido no autenticador TOTP |
| `MFA_TOTP_ACCOUNT_NAME` | `local-admin@ontrackchain` | identificador da conta no autenticador |
| `MFA_TOTP_PERIOD_SECONDS` | `30` | janela base do TOTP |
| `MFA_TOTP_DIGITS` | `6` | numero de digitos do codigo TOTP |
| `MFA_TOTP_WINDOW` | `1` | tolerancia de janelas adjacentes para validacao do TOTP |
| `MFA_EXTERNAL_PROVIDER_HOMOLOGATED` | `false` | quando `true`, permite tratar o MFA federado do provedor OIDC como homologado para fluxos sensiveis |
| `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` | vazio | token OIDC administrativo temporario usado para provar download homologado de `legal_report` via runner de janela |
| `ONTRACKCHAIN_COMPLIANCE_INTERNAL_BASE_URL` | vazio | override opcional da base usada por `check_compliance_provider_runtime.py` para acessar `GET /internal/provider-readiness` |
| `ONTRACKCHAIN_COMPLIANCE_PUBLIC_BASE_URL` | vazio | override opcional da base publica usada por `check_compliance_provider_runtime.py` para acessar o catalogo e `kyc-wallet` |
| `ONTRACKCHAIN_EXPECTED_PLAN` | `professional` | plano enviado no checker leve de runtime AML/KYT quando a rota publica exigir contexto de plano |
| `ONTRACKCHAIN_COMPLIANCE_SAMPLE_ADDRESS` | `0x000000000000000000000000000000000000dEaD` | carteira de amostra usada pelo checker leve de runtime AML/KYT |
| `ONTRACKCHAIN_COMPLIANCE_SAMPLE_CHAIN` | `ethereum` | chain da carteira de amostra usada pelo checker leve de runtime AML/KYT |
| `ONTRACKCHAIN_BEARER_TOKEN` | vazio | token opcional para o checker leve de runtime AML/KYT quando a rota publica exigir `Authorization: Bearer` |
| `ONTRACKCHAIN_API_KEY` | vazio | API key opcional para o checker leve de runtime AML/KYT e para homologacoes externas |
| `ONTRACKCHAIN_HTTP_TIMEOUT_SECONDS` | `10` | timeout HTTP do checker leve de runtime AML/KYT |
| `OIDC_ISSUER_URL` | `http://auth.localhost:8080/realms/ontrackchain` | issuer do provedor OIDC |
| `OIDC_AUDIENCE` | `ontrackchain-api` | audience do token OIDC |
| `OIDC_CLIENT_ID` | `ontrackchain-web` | client id OIDC, usado como fallback de audience |
| `OIDC_JWKS_URL` | `http://keycloak:8080/realms/ontrackchain/protocol/openid-connect/certs` | URL explicita do JWKS; no scaffold local usa a rede interna Docker |
| `OIDC_AUTHORIZATION_URL` | `http://auth.localhost:8080/realms/ontrackchain/protocol/openid-connect/auth` | URL explicita do fluxo de login OIDC |
| `OIDC_ORG_CLAIM` | `org` | override manual da claim usada como organizacao |
| `OIDC_PLAN_CLAIM` | `plan` | override manual da claim usada como plano |
| `OIDC_ROLE_CLAIM` | `otk_role` | override manual da claim usada como papel |

Observacao atual de planejamento:

- para a `Sprint 1` o preset arquitetural escolhido e `OIDC_PROVIDER=keycloak`
- `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false` continua sendo o default conservador; so deve virar `true` apos validacao formal do MFA federado no ambiente serio
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, a janela seria deve fornecer `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` para que a homologacao externa prove o download auditado de `legal_report`
- `check_compliance_provider_runtime.py` usa `ONTRACKCHAIN_COMPLIANCE_INTERNAL_BASE_URL` e `ONTRACKCHAIN_COMPLIANCE_PUBLIC_BASE_URL` quando presentes; se ausentes, cai para defaults locais e pode exigir execucao de dentro da rede do ambiente
- o primeiro corte serio de login deve usar `Redirect Web`, nao token manual colado no frontend
- o preset `generic` continua util como fallback tecnico, mas nao e mais a referencia principal do proximo incremento
- o host recomendado do Keycloak passou a ser um subdominio dedicado, preferencialmente `auth.ontrackchain.com`
- a referencia principal de redirect no stack dockerizado local e `http://localhost:8080`
- a audience exigida pelas APIs passa a ser `ontrackchain-api`, distinta do client web `ontrackchain-web`
- o scaffold local do `Keycloak` sobe via `COMPOSE_PROFILES=oidc` usando `dev-file`, sem acoplar o IdP ao banco principal da plataforma neste primeiro corte
- no modo local containerizado, `issuer` e `authorization_url` permanecem publicos em `auth.localhost`, enquanto `JWKS` e `token exchange` usam a rota interna `http://keycloak:8080`

Checklist minimo para Keycloak:

1. `OIDC_ISSUER_URL` apontando para `auth.ontrackchain.com/realms/ontrackchain` ou equivalente do ambiente
2. `OIDC_JWKS_URL` resolvendo as chaves publicas do realm
3. `OIDC_AUTHORIZATION_URL` configurada para o fluxo web
4. `OIDC_CLIENT_ID=ontrackchain-web` para o client do frontend
5. `OIDC_AUDIENCE=ontrackchain-api` para a validacao das APIs
6. `OIDC_ORG_CLAIM=org`, `OIDC_PLAN_CLAIM=plan` e `OIDC_ROLE_CLAIM=otk_role`
7. `JWT_HS256_SECRET`, `KEYCLOAK_B2B_CLIENT_SECRET`, `KEYCLOAK_ADMIN_PASSWORD` e `MFA_TOTP_SECRET` substituidos por secrets nao-dev
8. `OIDC_ISSUER_URL` e `OIDC_AUTHORIZATION_URL` usando dominios serios do ambiente, nao `localhost`

Template de preenchimento:

- ver [keycloak-oidc-template.md](keycloak-oidc-template.md) para um bloco `env`, exemplo de realm/client e checklist de rollout
- ver [README.md](../infra/keycloak/README.md) para subir o `Keycloak` local, credenciais iniciais e limites conhecidos do scaffold
- copiar [`.env.staging.example`](../.env.staging.example) para o arquivo privado do ambiente-alvo e substituir todos os placeholders `__FILL_*__`
- executar `python3 scripts/check_staging_env_placeholders.py --file .env.staging.private` antes dos preflights para garantir que nao restaram placeholders ou secrets vazios
- executar `python3 scripts/preflight_oidc_serious_env.py` antes do `smoke_auth_oidc_mode.py` em `staging|production`
- executar `python3 scripts/preflight_external_integrations.py` antes das janelas de homologacao AML/KYT e RPC em `staging|production`
- preferir `python3 scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` quando o objetivo for gerar toda a trilha operacional da janela com saidas persistidas

Servico principal:

- `auth-service`

## Frontend

| Variavel | Padrao | Uso |
|---|---|---|
| `INTERNAL_API_BASE_URL` | `http://traefik` | base interna para proxies server-side |
| `INTERNAL_AUTH_BASE_URL` | `http://auth-service:9000` | override opcional para validacao direta de token em proxies server-side sensiveis |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:${TRAEFIK_HTTP_PORT}` | base publica no browser |
| `NEXT_PUBLIC_APP_ENV` | `local` | ambiente refletido na UI para fallback seguro |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | vazio ou `true` em local | informa ao frontend se o login dev pode permanecer habilitado |

Observacao critica:

- no container do frontend, o Traefik deve ser acessado como `http://traefik`, nao `http://traefik:8080`
- o proxy de export administrativo dos incidentes globais usa `INTERNAL_AUTH_BASE_URL` quando presente; no compose local o fallback direto para `auth-service:9000` e suficiente
- quando `APP_ENV` for `staging` ou `production`, o recomendado e deixar `DEV_AUTH_ENABLED=false` para impedir o uso acidental de `issue-dev-token`

Observacao de escopo:

- thresholds especificos de backlog/DLQ de `investigation` ainda nao sao configurados por env no runtime atual; quando forem promovidos para configuracao real, devem entrar simultaneamente em `.env.example`, `docker-compose.yml` e nesta tabela

## Variaveis por Servico

### Auth Service

Variaveis observadas em [main.py](../apps/auth-service/src/auth_service/main.py):

- `APP_ENV`
- `AUTH_MODE`
- `DEV_AUTH_ENABLED`
- `MFA_TOTP_SECRET`
- `MFA_TOTP_ISSUER`
- `MFA_TOTP_ACCOUNT_NAME`
- `MFA_TOTP_PERIOD_SECONDS`
- `MFA_TOTP_DIGITS`
- `MFA_TOTP_WINDOW`
- `OIDC_PROVIDER`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_HS256_SECRET`
- `OIDC_ISSUER_URL`
- `OIDC_AUDIENCE`
- `OIDC_CLIENT_ID`
- `OIDC_JWKS_URL`
- `OIDC_AUTHORIZATION_URL`
- `OIDC_ORG_CLAIM`
- `OIDC_PLAN_CLAIM`
- `OIDC_ROLE_CLAIM`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

### Public API

Variaveis observadas em [main.py](../apps/public-api/src/public_api/main.py):

- `REDIS_HOST`
- `REDIS_PORT`

### Investigation API

Variaveis observadas em [main.py](../apps/investigation-api/src/investigation_api/main.py):

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `CREDIT_VALUE_BRL`
- `INVESTIGATION_INTERNAL_METRICS_ENABLED`

### Compliance API

Variaveis observadas em [main.py](../apps/compliance-api/src/compliance_api/main.py):

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `CREDIT_VALUE_BRL`
- `REPORT_API_BASE_URL`

Observacao:

- `REPORT_API_BASE_URL` tem default `http://report-api:8004`
- o worker de compliance tambem observa `COMPLIANCE_OFAC_SDN_SOURCE_URL` e `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` para sobrescrever o `source_url` persistido antes da sincronizacao das listas

### Monitoring API

Variaveis observadas em [main.py](../apps/monitoring-api/src/monitoring_api/main.py):

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `ENABLE_TEST_ENDPOINTS`
- `MONITORING_INTERNAL_METRICS_ENABLED`
- `MONITORING_ALERTS_LAST_HOUR_WARN_THRESHOLD`
- `MONITORING_CRITICAL_ALERTS_LAST_24H_CRITICAL_THRESHOLD`
- `MONITORING_EXPIRED_QUOTES_WARN_THRESHOLD`
- `MONITORING_OPEN_QUOTES_WARN_THRESHOLD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `COMPLIANCE_INTERNAL_METRICS_ENABLED`
- `COMPLIANCE_QUEUED_CASES_WARN_THRESHOLD`
- `COMPLIANCE_FAILED_LAST_24H_CRITICAL_THRESHOLD`
- `COMPLIANCE_EXPIRED_QUOTES_WARN_THRESHOLD`
- `COMPLIANCE_COMPLETED_WITHOUT_REPORT_WARN_THRESHOLD`
- `REPORT_INTERNAL_METRICS_ENABLED`
- `REPORT_DOWNLOADS_LAST_24H_WARN_THRESHOLD`
- `REPORT_PENDING_ONCHAIN_WARN_THRESHOLD`
- `REPORT_LEGAL_DOWNLOAD_SECURITY_VIOLATION_THRESHOLD`
- `REPORT_PERSISTED_WITHOUT_DOWNLOAD_WARN_THRESHOLD`

Observacao:

- `ENABLE_TEST_ENDPOINTS=true` e util para smoke/E2E, mas deve ser revisto em staging regulado

### Report API

Variaveis observadas em [main.py](../apps/report-api/src/report_api/main.py):

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

## Recomendacoes por Ambiente

### Development

- defaults sao aceitaveis
- `JWT_HS256_SECRET` ainda deve ser diferente de producao
- `AUTH_MODE=dev` preserva o fluxo atual com `issue-dev-token`

### Staging

- usar secrets distintos
- revisar `ENABLE_TEST_ENDPOINTS`
- separar banco e Redis
- preferir `AUTH_MODE=oidc`
- selecionar `OIDC_PROVIDER` antes de sobrescrever claims manualmente
- preencher issuer, JWKS/authorization endpoint e claims do provedor real quando necessario
- quando o feed publico da UE responder com `403`, preencher `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` com a URL XML tokenizada obtida em `https://webgate.ec.europa.eu/fsd/fsf#!/files`

Presets atuais:

- `generic`: `org_id`, `plan`, `role`
- `keycloak`: `org_id`, `plan`, `role`
- `auth0`: `org_id`, `plan`, `role`
- `entra`: `tenant_id`, `extension_plan`, `roles`

### Production

- nao usar defaults
- nao usar secrets em plain text no `.env`
- usar vault/secret manager
- nao expor `issue-dev-token`

## Gaps Atuais

- `.env.example` ainda nao lista todas as variaveis opcionais/derivadas por servico, como overrides server-side especializados
- nao ha convention doc de nomenclatura por ambiente alem do compose atual
- nao ha secrets manager real

## Boas Praticas

- nunca commitar segredos reais
- manter `.env.example` sincronizado com novos `Settings`
- ao adicionar nova variavel:
  - atualizar `Settings`
  - atualizar `docker-compose.yml` se necessario
  - atualizar este documento
