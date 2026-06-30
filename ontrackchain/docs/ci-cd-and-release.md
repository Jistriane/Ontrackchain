# CI/CD e Release

## Objetivo

Documentar o pipeline atual de validacao automatizada e o processo recomendado de release para o scaffold.

## Pipeline Atual

Workflow existente:

- [e2e-tests.yml](file:///home/jistriane/Ontracktchain/ontrackchain/.github/workflows/e2e-tests.yml)
- [quality-gates.yml](file:///home/jistriane/Ontracktchain/ontrackchain/.github/workflows/quality-gates.yml)

Nome:

- `Validation — Smoke and E2E`

Jobs atuais:

- `security-baseline`
- `preflight-regressions`
- `frontend-audit`
- `postgres-schema`
- `build`
- `smoke`
- `playwright`
- `frontend-typecheck`
- `python-quality`

## O que a Pipeline Faz

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

## Cobertura Atual da CI

### Coberto

- build da stack
- readiness do gateway
- `scripts/smoke_runtime.py`
- regressao E2E do frontend
- diagnosticos separados por etapa

### Cobertura adicional ja institucionalizada

- drift de schema e coerencia entre migrations via [check_postgres_schema.py](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/check_postgres_schema.py)
- baseline de seguranca contra placeholders/defaults via [check_security_baseline.py](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/check_security_baseline.py)
- regressao de preflights, homologacao, `window packet`, `release dossier` e `staging window runner`

## Workflow `quality-gates`

### Security Baseline

- executa [check_security_baseline.py](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/check_security_baseline.py)
- bloqueia placeholders/secrets de demo fora da allowlist explicita do projeto
- protege especialmente contra reintroducao acidental de `change-me`, `default TOTP secret`, hashes fake e blocos de private key em caminhos sensiveis

### Preflight Regressions

- executa regressao dos scripts de janela séria e homologação:
  - `check_staging_env_placeholders.py`
  - `check_staging_env_ownership_coverage.py`
  - `check_staging_env_handoff.py`
  - `render_staging_window_packet.py`
  - `build_staging_release_dossier.py`
  - `run_staging_window.py`
  - `preflight_oidc_serious_env.py`
  - `preflight_external_integrations.py`
  - `homologation_external_evidence.py`
- garante que a trilha `checks -> packet -> preflight -> homologacao -> dossier` continue íntegra

### Frontend Audit

- instala dependencias do frontend com `npm ci`
- executa `npm audit --omit=dev --audit-level=critical`
- usa o frontend atualizado para [package.json](file:///home/jistriane/Ontracktchain/ontrackchain/apps/frontend/package.json) e [package-lock.json](file:///home/jistriane/Ontracktchain/ontrackchain/apps/frontend/package-lock.json)
- criterio bloqueante atual: apenas `critical`
- findings `high` conhecidos do ecossistema `Next.js` permanecem sinalizados como backlog de upgrade major e nao bloqueiam este gate inicial

### Postgres Schema

- executa [check_postgres_schema.py](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/check_postgres_schema.py)
- valida numeração contínua das migrations
- valida que `README.md` referencia todas as migrations atuais
- valida que contratos de schema introduzidos em `infra/postgres/migrations/*.sql` também existem em [init.sql](file:///home/jistriane/Ontracktchain/ontrackchain/infra/postgres/init.sql)

### Frontend Typecheck

- instala dependencias do frontend com `npm ci`
- executa `npm run typecheck`
- usa [package.json](file:///home/jistriane/Ontracktchain/ontrackchain/apps/frontend/package.json) com `tsc -p tsconfig.json --noEmit`

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
- roda [check_python_app.py](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/check_python_app.py) para validação sintática localizável por app

Objetivo:

- transformar `P1-05` em gate real e preparar `P1-06` e `P1-07` sobre uma base de qualidade mínima por componente

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

## Processo Recomendado de Release

```text
PR -> CI -> merge -> staging tecnico -> staging regulatorio -> aprovacao -> producao
```

## Criterios Minimos de Aprovacao

- CI verde
- smoke verde no ambiente alvo
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
- a janela séria de `staging` já possui runner único, mas a execução real ainda depende de segredos e providers externos homologados

## Recomendacao Imediata

O proximo passo mais valioso para CI/CD e:

- reduzir duplicacao entre jobs com imagem/cache ou compose reaproveitavel
- executar `run_staging_window.py` em ambiente sério controlado, anexando o dossier como evidência oficial de release
