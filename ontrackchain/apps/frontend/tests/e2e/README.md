# E2E Frontend

Este diretorio concentra as suites E2E do `frontend` com `Playwright`.

Use este README como ponto de entrada rapido para:

- entender quais suites rodam com stack real vs mocks
- localizar os scripts canonicos de execucao
- entender o papel do `global-setup`
- reaproveitar helpers compartilhados antes de duplicar logica

Referencia operacional principal:

- [Run Sheet Operacional da Malha E2E Local](../../../../docs/governance-weekly/guides/E2E_LOCAL_MESH_RUN_SHEET.md)

## Classes de Suite

### Stack real

Suites que dependem da malha local por tras do `traefik`, com proxies e APIs reais:

- `compliance-flows.spec.ts`
- `api-consumer.spec.ts`
- `critical-path.spec.ts`
- `oidc-auth.spec.ts`

Scripts principais:

- `npm run test:e2e:stack-real-light`
- `npm run test:e2e:compliance-flows:real`
- `npm run test:e2e:api-consumer:real`
- `npm run test:e2e:critical-path:real`
- `npm run test:e2e:oidc-auth:real`
- `npm run test:e2e:oidc-critical`

Para execucao local canonica do gate `P0-01` (sobe Keycloak + stack e roda preflight/smoke/playwright):

- `make gate-p0-01-oidc-local`

### Browser-mocked

Suites com foco em fluxo de UI e contratos locais de browser, tipicamente sem depender da malha inteira atras do proxy:

- `audit-labels.spec.ts`
- `reports-history.spec.ts`
- `roscoaf-regulatory-dossier.spec.ts`
- `evidence-roscoaf-dossier.spec.ts`
- `evidence-custody.spec.ts`
- `operational-context-links.spec.ts`
- `timeline-workspace.spec.ts`
- `team-role-labels.spec.ts`
- `billing-users.spec.ts`
- `ui-home.spec.ts`

Script principal:

- `npm run test:e2e:browser-mocked`

### SSR-mocked

Suites que exigem backend SSR mockado ou combinam frontend local com `INTERNAL_API_BASE_URL` apontando para mocks dedicados:

- `alerts-dashboard-context-links.spec.ts`

Scripts principais:

- `npm run test:e2e:ssr-mocked`
- `npm run test:e2e:alerts-dashboard-context:mocked`

### Suites focais e utilitarias

Usar para rerun cirurgico, isolamento de regressao e investigacao:

- `npm run test:e2e -- tests/e2e/<spec>.spec.ts`
- `npm run test:e2e -- tests/e2e/<spec>.spec.ts --grep "<cenario>"`
- `npm run test:e2e:alerts-dashboard-context`
- `npm run test:e2e:ssr-mocked`
- `npm run test:e2e:showcase`

`test:e2e:showcase` e o comando canonico da suíte publica minima do `standalone showcase`. Ele assume o frontend ativo em `http://127.0.0.1:3001` com as envs do blueprint `render.yaml` e desliga o `global-setup` da malha full-stack para nao contaminar a validacao com dependencias que esse recorte nao usa.

## Guardrails de Execucao

O `playwright.config.ts` aponta para `global-setup.ts`.

Na baseline atual, o `global-setup` faz preflight estrutural antes dos testes:

- garante `frontend` e `traefik`
- garante `auth-service`, `compliance-api`, `report-api`, `investigation-api` e `monitoring-api`
- garante `investigation-worker`
- reinicia `traefik` para limpar efeito residual de rate-limit, salvo override
- tenta resetar estado minimo no `postgres`

Variaveis uteis:

- `ONTRACKCHAIN_E2E_RESET_STATE=false`
- `ONTRACKCHAIN_E2E_RESET_RATE_LIMIT=false`
- `ONTRACKCHAIN_E2E_ENSURE_FRONTEND=false`
- `ONTRACKCHAIN_E2E_ENSURE_CORE_APIS=false`
- `ONTRACKCHAIN_E2E_ENSURE_WORKERS=false`
- `ONTRACKCHAIN_E2E_ALLOW_NO_POSTGRES=true`

## Helpers Compartilhados

Antes de duplicar logica em um spec, revisar estes arquivos:

- `download-helpers.ts`
  - `expectDownloadLikeResponse(...)`
  - `expectDownloadLikeResponseWithRequest(...)`
  - usar para superficies `fetch/blob` validadas por `waitForResponse` + `content-disposition`
- `audit.ts`
  - helpers de oraculos e contratos relacionados a auditoria
- `federated-identity.ts`
  - setup e seeds auxiliares para OIDC e identidade federada
- `oidc.ts`
  - helpers especificos de autenticacao OIDC
- `totp.ts`
  - auxiliares de MFA/TOTP

Regra pratica:

- `fetch/blob` -> preferir helper HTTP, nao `waitForEvent("download")`
- payload critico -> capturar por `waitForRequest`
- evitar `expect(...)` dentro de `page.route(...)` quando isso puder mascarar timeout

## Convencoes de Estabilidade

- para cenarios sensiveis a persistencia, limpar `sessionStorage` antes da navegacao
- preferir oraculos de request/response e `sessionStorage` a estados visuais frageis
- quando o produto usa proxy real, tratar `Bad Gateway` e `500` primeiro como sinal de malha incompleta
- em handoff `alerts -> monitoring`, aceitar a normalizacao de status para `all`

## Fluxo Recomendado

1. Ler o run sheet operacional.
2. Escolher `stack-real`, `browser-mocked`, `ssr-mocked` ou `focal`.
3. Rodar o menor comando que prove a hipotese.
4. Preservar artefatos em `playwright-report/` e `test-results/`.
5. So ampliar o rerun depois que o bloco focal ficar diagnostico e estavel.
