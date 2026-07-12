# Deploy e Staging

## Objetivo

Descrever como promover o scaffold atual para um ambiente de staging controlado, preservando:

- integridade de schema
- validacao automatizada
- trilha auditavel
- seguranca dos fluxos sensiveis

Este documento cobre o processo tecnico. Ele nao substitui automacao futura de CI/CD nem procedimento formal de change management.

Para execucao controlada via GitHub Actions, use tambem o workflow manual [staging-serious-window.yml](../../.github/workflows/staging-serious-window.yml), que materializa `.env.staging.private` a partir de um `GitHub Environment` aprovado e executa o gate unico `prepare -> validate -> preflight -> run`. A configuracao do environment e do secret multi-linha esta detalhada em [GitHub Environment para Staging Sério](github-environment-staging-serious.md).

## Escopo Canonico

Use este documento para:

- preparar e validar o deploy tecnico do ambiente
- executar a cadeia tecnica de `prepare -> validate -> preflight -> run`
- entender os comandos, artefatos e criterios tecnicos do rito consolidado

Use os documentos abaixo quando o foco nao for deploy tecnico:

- [Governanca Semanal](./governance-weekly/README.md): tracking e sign-off por ciclo
- [Gates de Release para Staging Serio](project-release-gates.md): decidir `go/no-go` formal
- [Blueprint Render para Frontend-Only](render-staging-blueprint.md): recorte atual do deploy no Render sem dependencias de backend real

## Estrategia Atual

O projeto esta organizado para deploy baseado em containers, com `docker compose` como mecanismo principal no ambiente local e como referencia funcional para empacotamento.

## Render Atual

O blueprint do Render atualmente versionado na raiz do repositório esta reduzido para `frontend-only`.

Isso significa que o deploy ativo no Render:

- sobe apenas o `frontend` como serviço `web`
- usa `APP_ENV=test`
- mantém `AUTH_MODE=dev` e `DEV_AUTH_ENABLED=true`
- não provisiona `auth-service`, Keycloak, APIs privadas, Postgres, Redis, workers ou observabilidade

Esse recorte existe para destravar a publicação da interface enquanto os segredos e provedores externos reais ainda não estão disponíveis.

Use [Blueprint Render para Frontend-Only](render-staging-blueprint.md) quando o objetivo for:

- preview visual
- validação de shell
- smoke básico de UI

Não use esse deploy como evidência de staging sério, readiness regulatório ou validação OIDC real.

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
python3 scripts/smoke_runtime.py
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
python3 scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md > artifacts/staging/checks/ownership-coverage-stg-YYYY-MM-DD-a.json
python3 scripts/render_staging_window_packet.py --window-id stg-YYYY-MM-DD-a --output-file artifacts/staging/window-packet-stg-YYYY-MM-DD-a.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private > artifacts/staging/checks/placeholders-stg-YYYY-MM-DD-a.json
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md > artifacts/staging/checks/handoff-stg-YYYY-MM-DD-a.json
```

Ou, preferencialmente, execute a janela inteira de forma orquestrada:

```bash
python3 scripts/run_staging_window.py \
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
python3 scripts/preflight_oidc_serious_env.py
```

### 6. Rodar validacoes pos-deploy

Use gates orientados a ambiente real:

```bash
ONTRACKCHAIN_EXPECTED_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE=oidc \
ONTRACKCHAIN_EXPECTED_APP_ENV=staging \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED=false \
python3 scripts/smoke_auth_oidc_mode.py
```

### 7. Rodar E2E pos-deploy

```bash
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
npm run test:e2e
```

O gate `npm run test:e2e:oidc-critical` agora executa preflight explicito de `baseURL`, `/auth/config` e runtime OIDC antes das suites federadas. Se ele falhar cedo, trate como indisponibilidade/configuracao do ambiente serio antes de analisar regressao de UI.

Use `npm run test:e2e:dev-auth` apenas fora deste rito, quando a intencao for regressao local do scaffold em `AUTH_MODE=dev`.

### 8. Publicar evidencia de validacao

Preserve como evidencia:

- logs do deploy
- resultado do `preflight_oidc_serious_env.py`
- resultado do `smoke_auth_oidc_mode.py`
- relatorios do Playwright critico e completo
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, artefato de homologacao contendo download auditado de `legal_report`

### 9. Rito Consolidado da Janela

Fluxo tecnico recomendado:

1. gerar a base da janela:

```bash
python3 scripts/prepare_staging_window.py --window-id <janela> --mode baseline
```

1. preencher `.env.staging.private` fora do repositório e validar ownership/placeholders:

- [Ownership do `.env.staging`](staging-env-ownership.md)

1. executar o gate tecnico unico:

```bash
python3 scripts/prepare_staging_window.py --window-id <janela> --mode baseline --run
```

1. para a execucao ponta a ponta local, preferir:

```bash
make run-serious-window-local WINDOW_ID=<janela> MODE=baseline
```

1. para a conducao operacional, usar:

- [Gates de Release para Staging Serio](project-release-gates.md): decidir `go/no-go` formal
- [Governanca Semanal](./governance-weekly/README.md): tracking e sign-off por ciclo
- [Pacote Final de Execucao da Janela Seria Integrada](governance-weekly/guides/SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md): sequencia canonica, reconciliacao e criterio de sign-off

Quando a execucao gerar `prepare-staging-window-output.json`, sincronizar a camada executiva com:

```bash
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Saida executiva esperada do pós-processamento:

- `ci-artifacts/staging-serious-window-signoff.md`
- sign-off versionado em `docs/governance-weekly/cycles/<data>/`
- `go/no-go decision packet` versionado em `docs/governance-weekly/cycles/<data>/`
- sincronizacao do registro semanal e do board operacional global

Comandos auxiliares continuam canônicos para janelas com provedores reais:

- `make check-compliance-provider-runtime`
- `make run-oidc-readiness-bundle-local`
- `make run-eu-sanctions-window-local`
- `make run-regulatory-readiness-bundle`
- `make run-regulatory-readiness-bundle-local`
- `python3 scripts/check_sanctions_sync_status.py`

Se o checker rodar fora da rede do `docker compose`, substitua `INTERNAL_BASE_URL` por um endpoint interno realmente alcancavel no ambiente-alvo. O `compose` atual nao publica `8002` no host.

Opcao equivalente em CI/CD controlado:

- abrir o workflow manual `Staging Serious Window`
- informar `window_id`, `mode` e `environment_name`
- garantir que o `GitHub Environment` selecionado possui o secret `STAGING_WINDOW_PRIVATE_ENV`
- usar o artefato `serious-staging-window-<janela>` como pacote oficial de `checks`, `dossier`, `window packet`, `homologation` e resumo regulatório quando o escopo incluir `P0-02/P0-03`

Depois do preflight e durante a janela controlada, gere a trilha anexavel:

```bash
APP_ENV=staging \
ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live \
ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only \
python3 scripts/homologation_external_evidence.py --mode both --rpc-expected-mode fallback_only
```

Atalho recomendado:

```bash
set -a
. ./.env.staging.private
set +a
python3 scripts/homologation_external_evidence.py --mode both --rpc-expected-mode fallback_only
```

Resultado esperado:

- artefato `.json` em `artifacts/homologation/`
- manifesto `.manifest.json` com `sha256` e `size`
- evidencias correlacionadas por `request_id` para compliance e RPC

Para `P0-01`, preferir um pacote operacional único antes do war room completo:

```bash
make run-oidc-readiness-bundle-local \
  WINDOW_ID=stg-YYYY-MM-DD-oidc \
  BASE_URL=http://localhost:8080
```

Saída esperada para `P0-01`:

- `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md`
- `oidc-preflight` e `smoke_auth_oidc_mode` consolidados em um único pacote revisável

Consolidacao final recomendada:

```bash
python3 scripts/build_staging_release_dossier.py \
  --window-id stg-YYYY-MM-DD-a \
  --window-packet artifacts/staging/window-packet-stg-YYYY-MM-DD-a.md \
  --ownership-coverage-check artifacts/staging/checks/ownership-coverage-stg-YYYY-MM-DD-a.json \
  --placeholder-check artifacts/staging/checks/placeholders-stg-YYYY-MM-DD-a.json \
  --handoff-check artifacts/staging/checks/handoff-stg-YYYY-MM-DD-a.json \
  --homologation-artifact artifacts/homologation/<artefato>.json \
  --homologation-manifest artifacts/homologation/<artefato>.json.manifest.json \
  --oidc-readiness-bundle artifacts/staging/checks/stg-YYYY-MM-DD-a-oidc-readiness-bundle.json \
  --oidc-readiness-bundle-summary artifacts/staging/dossiers/stg-YYYY-MM-DD-a-oidc-readiness-bundle.md \
  --regulatory-readiness-bundle artifacts/staging/checks/stg-YYYY-MM-DD-a-regulatory-readiness-bundle.json \
  --regulatory-readiness-bundle-summary artifacts/staging/dossiers/stg-YYYY-MM-DD-a-regulatory-readiness-bundle.md
```

Atalho operacional recomendado:

```bash
python3 scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

Saida esperada:

- JSON consolidado da execucao da janela em `stdout|stderr`
- dossier `.json` em `artifacts/staging/dossiers/`
- manifesto `.manifest.json` do dossier com `sha256`
- resumo `.md` do bundle OIDC em `artifacts/staging/dossiers/` para a trilha `P0-01`
- resumo `.md` do bundle regulatório em `artifacts/staging/dossiers/` quando `AML/KYT live` e/ou feed UE estiverem no escopo
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

O comando aplica preflight de `http://localhost:8080/` e `/auth/config` antes do Playwright. Se o ambiente nao estiver realmente em `AUTH_MODE=dev`, a falha deve ser tratada como configuracao incorreta do scaffold local.

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
python3 scripts/smoke_auth_oidc_mode.py
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
