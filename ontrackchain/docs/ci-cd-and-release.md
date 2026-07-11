# CI/CD e Release

## Objetivo

Documentar o pipeline atual de validacao automatizada e o processo recomendado de release para o scaffold.

## Pipeline Atual

Workflows canônicos:

- [e2e-tests.yml](../../.github/workflows/e2e-tests.yml)
- [quality-gates.yml](../../.github/workflows/quality-gates.yml)
- [staging-serious-window.yml](../../.github/workflows/staging-serious-window.yml)

Workflow de regressao end-to-end:

- `Validation — Smoke and E2E`

Jobs atuais em `Validation — Smoke and E2E`:

- `build`
- `smoke`
- `playwright`
- `playwright-dev-auth`

Workflow de qualidade por componente:

- `Quality Gates — Per App`

Jobs atuais em `Quality Gates — Per App`:

- `security-baseline`
- `preflight-regressions`
- `frontend-audit`
- `postgres-schema`
- `frontend-typecheck`
- `python-quality`

Workflow manual dedicado:

- `Staging Serious Window`
- disparo via `workflow_dispatch`
- exige `GitHub Environment` com aprovacoes e secret `STAGING_WINDOW_PRIVATE_ENV`
- executa `python scripts/prepare_staging_window.py --window-id <janela> --mode <baseline|homologated> --run`
- publica `checks`, `dossiers`, `window packet`, templates redigidos e evidencias de homologacao como artefato anexavel
- configuracao operacional detalhada em [GitHub Environment para Staging Sério](github-environment-staging-serious.md)

## O que a Pipeline Faz

As secoes abaixo descrevem primeiro o workflow `Validation — Smoke and E2E`, depois os gates adicionais de `Quality Gates — Per App` e por fim o workflow manual `Staging Serious Window`.

## Job `build`

### 1. Checkout

- baixa o repositorio

### 2. Build e Start da Stack

```bash
docker compose up -d --build
```

Objetivo:

- validar que a stack inteira ainda sobe

### 3. Espera o Gateway

Faz polling de:

```bash
curl -fsS http://localhost:8080/
```

Objetivo:

- garantir que o entrypoint ficou disponivel antes dos testes

### 4. Publica Diagnosticos do Docker

- artefato `build-diagnostics`

## Job `smoke`

### 5. Checkout + Build da Stack

- sobe novamente a stack em runner isolado

### 6. Espera o Gateway

- repete o gate de readiness

### 7. Setup Python

- usa Python `3.11`

### 8. Executa Smoke Runtime

Variaveis atuais:

- `ONTRACKCHAIN_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`

Comando:

```bash
python scripts/smoke_runtime.py
```

Objetivo:

- validar os fluxos criticos backend/proxy/auditoria antes da camada de browser

### 9. Publica Diagnosticos do Docker

- artefato `smoke-diagnostics`

## Job `playwright`

### 10. Checkout + Build da Stack

- sobe novamente a stack em runner isolado

### 11. Espera o Gateway

- repete o gate de readiness

### 12. Setup Node.js

- usa Node `20`

### 13. Instala Dependencias do Frontend

```bash
npm install
```

### 14. Instala Browser do Playwright

```bash
npx playwright install chromium --with-deps
```

### 15. Executa Suite Playwright

Variaveis atuais:

- `TEST_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`

Comando:

```bash
npx playwright test
```

### 16. Publica Artefatos

- sobe `test-results`
- sobe `playwright-diagnostics`

## Job `playwright-dev-auth`

### 17. Checkout + Build da Stack em `dev auth`

- sobe a stack com `AUTH_MODE=dev` e `DEV_AUTH_ENABLED=true`

### 18. Espera o Gateway

- repete o gate de readiness

### 19. Setup Node.js + Dependencias

- instala dependencias do frontend e browsers do Playwright

### 20. Executa Suite `dev-auth`

Variaveis atuais:

- `TEST_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`
- `AUTH_MODE=dev`

Comando:

```bash
npm run test:e2e:dev-auth
```

Observacao operacional:

- o comando agora executa preflight explicito de `baseURL` e `/auth/config`
- falha cedo se o ambiente nao estiver em `AUTH_MODE=dev`
- valida apenas a regressao local de `2FA` no scaffold `dev`

### 21. Publica Artefatos

- sobe `playwright-dev-auth-results`
- sobe `playwright-dev-auth-html-report`
- sobe `playwright-dev-auth-diagnostics`

## Cobertura Atual da CI

### Coberto

- build da stack
- readiness do gateway
- `scripts/smoke_runtime.py`
- regressao E2E do frontend
- diagnosticos separados por etapa

### Cobertura adicional ja institucionalizada

- drift de schema e coerencia entre migrations via [check_postgres_schema.py](../scripts/check_postgres_schema.py)
- baseline de seguranca contra placeholders/defaults via [check_security_baseline.py](../scripts/check_security_baseline.py)
- regressao de preflights, homologacao, `window packet`, `release dossier` e `staging window runner`

## Workflow `quality-gates`

### Security Baseline

- executa [check_security_baseline.py](../scripts/check_security_baseline.py)
- bloqueia placeholders/secrets de demo fora da allowlist explicita do projeto
- protege especialmente contra reintroducao acidental de `change-me`, `default TOTP secret`, hashes fake e blocos de private key em caminhos sensiveis

### Preflight Regressions

- executa regressao dos scripts de janela séria e homologação:
  - `check_staging_env_placeholders.py`
  - `check_staging_env_ownership_coverage.py`
  - `check_staging_env_handoff.py`
  - `render_staging_private_env_templates.py`
  - `render_staging_window_packet.py`
  - `prepare_staging_window.py`
  - `build_staging_release_dossier.py`
  - `run_staging_window.py`
  - `preflight_oidc_serious_env.py`
  - `preflight_external_integrations.py`
  - `homologation_external_evidence.py`
- garante que a trilha `checks -> packet -> preflight -> homologacao -> dossier` continue íntegra

### Frontend Audit

- instala dependencias do frontend com `npm ci`
- executa `npm audit --omit=dev --audit-level=critical`
- usa o frontend atualizado para [package.json](../apps/frontend/package.json) e [package-lock.json](../apps/frontend/package-lock.json)
- criterio bloqueante atual: apenas `critical`
- findings `high` conhecidos do ecossistema `Next.js` permanecem sinalizados como backlog de upgrade major e nao bloqueiam este gate inicial

### Postgres Schema

- executa [check_postgres_schema.py](../scripts/check_postgres_schema.py)
- valida numeração contínua das migrations
- valida que `README.md` referencia todas as migrations atuais
- valida que contratos de schema introduzidos em `infra/postgres/migrations/*.sql` também existem em [init.sql](../infra/postgres/init.sql)

### Frontend Typecheck

- instala dependencias do frontend com `npm ci`
- executa `npm run typecheck`
- usa [package.json](../apps/frontend/package.json) com `tsc -p tsconfig.json --noEmit`

### Python Quality

- executa em matriz por app/pacote:
  - `apps/auth-service`
  - `apps/public-api`
  - `apps/monitoring-api`
  - `apps/investigation-api`
  - `apps/compliance-api`
  - `apps/report-api`
  - `packages/shared`
  - `packages/agents`
- instala `ruff`
- roda `ruff check --select F,E9`
- roda [check_python_app.py](../scripts/check_python_app.py) para validação sintática localizável por app

Objetivo:

- transformar `P1-05` em gate real e preparar `P1-06` e `P1-07` sobre uma base de qualidade mínima por componente

## Workflow `staging-serious-window`

### Proposito do workflow

- executar a janela séria em trilho controlado de CI/CD, sem depender de shell local e sem versionar `.env.staging.private`

### Quando usar

- apos merge ou cut controlado que precise de evidência oficial de `staging`
- quando a janela exigir aprovação manual antes de tocar providers reais
- quando o sign-off precisar de artefatos anexáveis produzidos pelo runner oficial

### Entradas obrigatorias

- `window_id`: identificador operacional da janela, no formato `stg-YYYY-MM-DD-x`
- `mode`: `baseline` ou `homologated`
- `environment_name`: `GitHub Environment` que centraliza aprovacoes e o secret `STAGING_WINDOW_PRIVATE_ENV`

### Preparacao local recomendada antes do disparo

Antes de abrir o `workflow_dispatch`, preparar o rito com:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
```

### Sequencia executada

1. faz `checkout` do repositorio
2. prepara `ci-artifacts/`
3. valida que o secret `STAGING_WINDOW_PRIVATE_ENV` existe no `GitHub Environment`
4. materializa `.env.staging.private` apenas no runner efemero
5. executa `python scripts/prepare_staging_window.py --window-id <janela> --mode <modo> --run`
6. publica artefato unico contendo:
   - `ci-artifacts/prepare-staging-window-output.json`
   - `ci-artifacts/staging-serious-window-signoff.md`
   - `artifacts/staging/checks/`
   - `artifacts/staging/dossiers/`
   - `artifacts/staging/templates/`
   - `artifacts/staging/window-packet-<janela>.md`
   - `artifacts/homologation/`

### Pos-processamento local recomendado

Depois de baixar o artifact do workflow, executar o pos-processamento local completo com:

```bash
make postprocess-serious-window-dry-run \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

O comando acima:

- atualiza `ci-artifacts/staging-serious-window-signoff.md`
- gera o sign-off versionado em `docs/governance-weekly/`
- gera o `go/no-go decision packet` versionado em `docs/governance-weekly/cycles/<data>/`
- sincroniza o registro semanal da mesma janela
- sincroniza o board operacional global

Se precisar executar os passos separadamente:

```bash
python scripts/render_staging_window_signoff.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --output-file ci-artifacts/staging-serious-window-signoff.md \
  --governance-weekly-dir docs/governance-weekly

python scripts/render_staging_window_weekly_governance.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"

python scripts/render_staging_window_decision_packet.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

### Controles de seguranca

- o secret nao e publicado como artefato nem escrito em documentação
- aprovacoes podem ser forçadas pelo proprio `GitHub Environment`
- a execucao falha cedo quando o secret da janela nao esta presente ou quando `validate/preflight/run` retornam erro

## Estrategia de Release Recomendada

### Pull Request

Objetivo:

- bloquear regressao funcional evidente

Gates recomendados:

- CI com smoke e Playwright verde
- job de build verde
- revisao de codigo
- revisao de mudancas de schema quando aplicavel

### Merge em Branch de Integracao

Objetivo:

- preparar promocao para staging

Gates recomendados:

- stack sobe
- smoke runtime verde
- Playwright verde
- docs relevantes atualizadas

### Staging Regulatorio

Objetivo:

- validar controles, auditoria e operacao

Checklist:

- trilha auditavel consultavel
- `legal_report` com enforcement correto
- readiness regulatorio revisado
- bundle `AML/KYT live` e gate de runtime anexados quando o escopo exigir
- JSONs da janela UE anexados quando o escopo exigir `EU_CONSOLIDATED`
- quando houver `AML/KYT live`, `make check-compliance-provider-runtime` verde e anexado
- quando houver feed UE, `make run-eu-sanctions-window-local` ou fluxo equivalente com JSONs anexados

## Processo Recomendado de Release

```text
PR -> CI -> merge -> staging tecnico -> staging regulatorio -> aprovacao -> producao
```

## Criterios Minimos de Aprovacao

- CI verde
- smoke verde no ambiente alvo
- artefatos obrigatorios da janela anexados quando houver provider real
- nenhuma regressao em:
  - `plan lock`
  - `report_generated`
  - `report_downloaded`
  - `legal_report`
  - concorrencia de investigation

## Mudancas que Exigem Mais Cuidado

### Schema

Sempre que houver mudanca de schema:

- atualizar `init.sql`
- criar migration correspondente
- validar com volume persistido

### Auth/Proxy

Sempre que houver mudanca em auth/proxy:

- rerodar smoke
- rerodar Playwright compliance
- verificar `audit_logs`

### Billing

Sempre que houver mudanca em pricing/quote:

- validar `estimate -> start`
- validar `plan lock`
- validar ledger

## Backlog Recomendado para CI/CD

### Alta prioridade

- adicionar lint/typecheck por app
- adicionar gates de schema/migrations

### Media prioridade

- publicar artefatos mais ricos
- adicionar matrix de navegadores
- reduzir duplicacao de startup entre jobs

### Baixa prioridade

- release automation com versionamento
- changelog automatizado

## Exemplo de Pipeline Alvo

```text
job 1: lint + typecheck
job 2: build stack
job 3: smoke runtime
job 4: Playwright critical/compliance
job 5: aprovacao manual para staging
job 6: deploy staging
job 7: smoke pos-deploy
```

## Riscos Atuais

- CI ainda rebuilda a stack em runners diferentes
- a promocao tecnica automatizada ainda usa trilho `dev-compatible` para cobrir o smoke runtime
- a janela séria de `staging` agora possui workflow dedicado, mas a execucao real ainda depende de providers externos homologados e da qualidade do secret entregue ao `GitHub Environment`

## Recomendacao Imediata

O proximo passo mais valioso para CI/CD e:

- reduzir duplicacao entre jobs com imagem/cache ou compose reaproveitavel
- promover `staging-serious-window.yml` a rito oficial da janela regulatoria, anexando o artefato `serious-staging-window-<janela>` como evidência oficial de release
