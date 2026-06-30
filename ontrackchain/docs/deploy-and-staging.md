# Deploy e Staging

## Objetivo

Descrever como promover o scaffold atual para um ambiente de staging controlado, preservando:

- integridade de schema
- validacao automatizada
- trilha auditavel
- seguranca dos fluxos sensiveis

Este documento cobre o processo tecnico. Ele nao substitui automacao futura de CI/CD nem procedimento formal de change management.

Para execucao controlada via GitHub Actions, use tambem o workflow manual [staging-serious-window.yml](../../.github/workflows/staging-serious-window.yml), que materializa `.env.staging.private` a partir de um `GitHub Environment` aprovado e executa o gate unico `prepare -> validate -> preflight -> run`. A configuracao do environment e do secret multi-linha esta detalhada em [GitHub Environment para Staging Sério](github-environment-staging-serious.md).

Para a primeira execucao seria, use tambem o [Checklist de Evidencia Minima da Primeira Janela Seria](first-serious-window-evidence-checklist.md) como filtro explicito de entrada, execucao e saida.

## Estrategia Atual

O projeto esta organizado para deploy baseado em containers, com `docker compose` como mecanismo principal no ambiente local e como referencia funcional para empacotamento.

## Ambientes Recomendados

### Development

- execucao local
- dados descartaveis ou semi-persistidos
- auth/2FA de scaffold
- foco em velocidade de iteracao

### Staging

- infraestrutura separada
- banco persistente proprio
- secrets separados
- smoke e E2E executados apos deploy
- idealmente com auth mais proxima do real
- no corte tecnico atual, o smoke pos-deploy consolidado ainda usa um perfil `dev-compatible` para validar emissao de token e `TOTP` local sem mascarar o gate `OIDC`

### Production

- nao coberta pelo scaffold atual
- exige endurecimento adicional

## Requisitos para Promocao a Staging

- schema atualizado
- migrations aplicadas quando houver volume preexistente
- `docker compose up -d --build` funcionando sem erro localmente
- `scripts/smoke_runtime.py` verde
- Playwright critical/compliance verde
- checklist de seguranca basico atendido

## Fluxo Recomendado de Deploy

### 1. Validar localmente

```bash
docker compose up -d --build
docker build --target runtime -t ontrackchain-frontend-runtime ./apps/frontend
python scripts/smoke_runtime.py
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
npm run test:e2e
```

Antes de preparar `staging`, copie o baseline serio:

```bash
cp .env.staging.example .env.staging.private
```

Depois substitua todos os placeholders `__FILL_*__` por secrets e URLs reais do ambiente.
Use a matriz de ownership em [Ownership do `.env.staging`](staging-env-ownership.md) para distribuir o preenchimento por owner e apoio antes da janela.

Valide o arquivo privado antes dos preflights:

```bash
python scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md > artifacts/staging/checks/ownership-coverage-stg-YYYY-MM-DD-a.json
python scripts/render_staging_window_packet.py --window-id stg-YYYY-MM-DD-a --output-file artifacts/staging/window-packet-stg-YYYY-MM-DD-a.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private > artifacts/staging/checks/placeholders-stg-YYYY-MM-DD-a.json
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md > artifacts/staging/checks/handoff-stg-YYYY-MM-DD-a.json
```

Ou, preferencialmente, execute a janela inteira de forma orquestrada:

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

### 2. Verificar drift de schema

Se o banco alvo ja existe:

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

### 3. Subir servicos

```bash
docker compose up -d --build
```

### 4. Validar gateway

```bash
curl -fsS http://localhost:8080/
```

### 5. Rodar preflight de ambiente serio

Antes do smoke HTTP, valide se o ambiente nao esta reutilizando defaults locais ou endpoints de `localhost`:

```bash
APP_ENV=staging \
AUTH_MODE=oidc \
DEV_AUTH_ENABLED=false \
NEXT_PUBLIC_AUTH_MODE=oidc \
NEXT_PUBLIC_APP_ENV=staging \
NEXT_PUBLIC_DEV_AUTH_ENABLED=false \
OIDC_PROVIDER=keycloak \
OIDC_ISSUER_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain \
OIDC_AUDIENCE=ontrackchain-api \
OIDC_CLIENT_ID=ontrackchain-web \
OIDC_JWKS_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/certs \
OIDC_AUTHORIZATION_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/auth \
OIDC_ORG_CLAIM=org \
OIDC_PLAN_CLAIM=plan \
OIDC_ROLE_CLAIM=otk_role \
MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false \
JWT_HS256_SECRET=*** \
MFA_TOTP_SECRET=*** \
KEYCLOAK_ADMIN_PASSWORD=*** \
KEYCLOAK_B2B_CLIENT_SECRET=*** \
python scripts/preflight_oidc_serious_env.py
```

### 6. Rodar validacoes pos-deploy

Use gates orientados a ambiente real:

```bash
ONTRACKCHAIN_EXPECTED_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_APP_ENV=staging \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED=false \
python scripts/smoke_auth_oidc_mode.py
```

### 7. Rodar E2E pos-deploy

```bash
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
npm run test:e2e
```

### 8. Publicar evidencia de validacao

Preserve como evidencia:

- logs do deploy
- resultado do `preflight_oidc_serious_env.py`
- resultado do `smoke_auth_oidc_mode.py`
- relatorios do Playwright critico e completo
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, artefato de homologacao contendo download auditado de `legal_report`

### 9. Preflight antes de homologacao AML/KYT e RPC

Antes de abrir janela de provider real, valide a configuracao esperada:

- baseline recomendado: [`.env.staging.example`](../.env.staging.example)
- ownership recomendado: [Ownership do `.env.staging`](staging-env-ownership.md)
- execute `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated` para gerar template privado, `window packet` e diretórios-base da janela
- apos preencher `.env.staging.private`, execute `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated --validate` para persistir os gates locais antes da janela completa
- se quiser antecipar tambem os preflights reais, execute `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated --preflight`; esse modo implica validacao local
- para um gate unico, execute `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated --run`; esse modo implica validacao local, preflights e chama o runner completo apenas quando tudo estiver verde
- execute `python scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md` para bloquear drift entre placeholders do baseline e a matriz de owners
- execute `python scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md` para gerar um pacote redigido da janela antes do preenchimento dos secrets
- nao promova o ambiente enquanto existir qualquer placeholder `__FILL_*__`
- execute `python scripts/check_staging_env_placeholders.py --file .env.staging.private` antes de `preflight_oidc_serious_env.py` e `preflight_external_integrations.py`
- execute `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` para bloquear grupos ainda em `pending`, datas invalidas ou status fora da politica da janela
- persista os JSONs dos checkers em `artifacts/staging/checks/` para alimentar o dossier final da janela
- prefira `python scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` para executar a cadeia completa com falha honesta e saídas persistidas

```bash
APP_ENV=staging \
ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live \
ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only \
COMPLIANCE_TRM_ENABLED=true \
COMPLIANCE_TRM_SCREENING_URL=https://provider.example/screening \
COMPLIANCE_TRM_API_KEY=*** \
COMPLIANCE_TRM_TIMEOUT_MS=1500 \
COMPLIANCE_TRM_MAX_RETRIES=1 \
INVESTIGATION_RPC_ENABLED=true \
INVESTIGATION_RPC_PRIMARY_URL= \
INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example \
INVESTIGATION_RPC_TIMEOUT_MS=1500 \
INVESTIGATION_RPC_MAX_RETRIES=1 \
python scripts/preflight_external_integrations.py
```

Atalho recomendado:

```bash
python scripts/prepare_staging_window.py --window-id <janela> --mode baseline
set -a
. ./.env.staging.private
set +a
python scripts/preflight_external_integrations.py
```

Ou, depois do preenchimento do `.env.staging.private`, prefira:

```bash
python scripts/prepare_staging_window.py --window-id <janela> --mode baseline --run
```

Opcao equivalente em CI/CD controlado:

- abrir o workflow manual `Staging Serious Window`
- informar `window_id`, `mode` e `environment_name`
- garantir que o `GitHub Environment` selecionado possui o secret `STAGING_WINDOW_PRIVATE_ENV`
- usar o artefato `serious-staging-window-<janela>` como pacote oficial de `checks`, `dossier`, `window packet` e `homologation`

Depois do preflight e durante a janela controlada, gere a trilha anexavel:

```bash
APP_ENV=staging \
ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live \
ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only \
python scripts/homologation_external_evidence.py --mode both --rpc-expected-mode fallback_only
```

Atalho recomendado:

```bash
set -a
. ./.env.staging.private
set +a
python scripts/homologation_external_evidence.py --mode both --rpc-expected-mode fallback_only
```

Resultado esperado:

- artefato `.json` em `artifacts/homologation/`
- manifesto `.manifest.json` com `sha256` e `size`
- evidencias correlacionadas por `request_id` para compliance e RPC

Consolidacao final recomendada:

```bash
python scripts/build_staging_release_dossier.py \
  --window-id stg-YYYY-MM-DD-a \
  --window-packet artifacts/staging/window-packet-stg-YYYY-MM-DD-a.md \
  --ownership-coverage-check artifacts/staging/checks/ownership-coverage-stg-YYYY-MM-DD-a.json \
  --placeholder-check artifacts/staging/checks/placeholders-stg-YYYY-MM-DD-a.json \
  --handoff-check artifacts/staging/checks/handoff-stg-YYYY-MM-DD-a.json \
  --homologation-artifact artifacts/homologation/<artefato>.json \
  --homologation-manifest artifacts/homologation/<artefato>.json.manifest.json
```

Atalho operacional recomendado:

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

Saida esperada:

- JSON consolidado da execucao da janela em `stdout|stderr`
- dossier `.json` em `artifacts/staging/dossiers/`
- manifesto `.manifest.json` do dossier com `sha256`
- status consolidado `ok` apenas quando checks e homologacao estiverem verdes

Observacao:

- o baseline `local` do repositório usa `COMPLIANCE_TRM_ENABLED=false` e `INVESTIGATION_RPC_ENABLED=false`
- por isso, `status=ok` para `homologation_external_evidence.py` e meta de `staging|production`, nao de scaffold local sem overrides serios

### Regressao opcional de auth local

Use apenas em ambiente local/scaffold para preservar cobertura do fluxo legado com `TOTP` local. Nao faz parte do gate de staging/producao em `AUTH_MODE=oidc`.

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

## Sequencia de Promocao Recomendada

```text
local -> staging serio/regulatorio -> producao
```

### Local

- foco em desenvolvimento

### Staging serio/regulatorio

- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- validar [smoke_auth_oidc_mode.py](../scripts/smoke_auth_oidc_mode.py) antes do `playwright` critico

```bash
ONTRACKCHAIN_EXPECTED_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_APP_ENV=staging \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED=false \
python scripts/smoke_auth_oidc_mode.py
```

### Staging regulatorio

- foco em controles, auditoria, readiness e operacao

## Checklist de Deploy

### Aplicacao

- imagens/builds atualizados
- rotas Traefik alinhadas com servicos
- variaveis de ambiente coerentes
- `INTERNAL_API_BASE_URL` correto para o frontend
- override `INTERNAL_AUTH_BASE_URL` revisado quando o frontend nao estiver na rede padrao do compose

### Banco

- `init.sql` e migrations coerentes
- backup disponivel antes de mudanca estrutural
- RLS preservado

### Validacao

- smoke verde
- Playwright verde
- audit logs acessiveis por `ADMIN`
- UI `/audit` responde com os filtros administrativos esperados
- `legal_report` continua exigindo `JWT + ADMIN + 2FA`
- Prometheus com target `investigation-api` healthy e regras carregadas
- Prometheus com target `monitoring-api` healthy e regras carregadas
- Prometheus com target `compliance-api` healthy e regras carregadas
- Prometheus com target `report-api` healthy e regras carregadas
- Alertmanager healthy com rota para `monitoring-api`
- Grafana com dashboard `ontrack-investigation-operations` provisionado
- Grafana com dashboard `ontrack-monitoring-operations` provisionado
- Grafana com dashboard `ontrack-compliance-operations` provisionado
- Grafana com dashboard `ontrack-report-operations` provisionado
- Grafana com dashboard `ontrack-platform-alerting` provisionado
- `/monitoring` permite triagem, selecao acumulada e export `CSV|JSON`
- export administrativo de incidentes globais registra `operational_alerts_exported` no run atual

## Secrets e Configuracao

### Minimo exigido para staging

- segregar `.env` por ambiente
- nao reutilizar secrets de development
- rotacionar JWT secrets entre ambientes
- separar banco e Redis de staging

### Ainda pendente para ambientes mais fortes

- vault real
- rotacao automatizada
- politica formal de expiracao
- rotacao do token interno `Alertmanager -> monitoring-api`

## Rollback

## Principio de Rollback

Toda mudanca em staging deve poder ser revertida sem perda de entendimento do estado.

### Rollback de Aplicacao

- manter imagem/tag anterior disponivel
- reverter compose para a versao anterior

### Rollback de Banco

- preferir migrations idempotentes e incrementais
- nao confiar em `down -v` como rollback de staging
- sempre tirar backup antes de alteracoes destrutivas

## Sinais de Aceite de Deploy

Um deploy pode ser considerado aceito quando:

- gateway responde
- smoke passa
- Playwright passa
- `audit_logs` registra eventos do run atual
- `report_downloaded` continua sendo gerado apenas quando apropriado
- `operational_alerts_exported` aparece quando a operacao administrativa exporta backlog global
- nao ha regressao em `plan lock` nem em concorrencia de investigation

## Riscos de Deploy Conhecidos

- drift entre `init.sql` e migrations futuras
- dependencias de auth ainda dev-like
- ausencia de automacao formal de deploy
- observabilidade central agora cobre `investigation`, `monitoring`, `compliance` e `report`, com roteamento ativo via `Alertmanager`

## Proximos Passos Recomendados

- institucionalizar `staging-serious-window.yml` como gate manual oficial da janela regulatoria
- introduzir secrets manager
- separar staging tecnico de staging regulatorio
- adicionar validacao de backup/restore ao processo
