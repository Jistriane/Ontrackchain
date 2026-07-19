# Run Sheet Operacional - Malha E2E Local

## Uso

Usar esta folha para executar e diagnosticar a malha E2E local do `frontend` com `Playwright`, `Docker Compose` e os guardrails de `global-setup`.

Ela existe para:

- reduzir falso vermelho por malha incompleta (`frontend`, `traefik`, APIs centrais e `investigation-worker`)
- padronizar a ordem minima de preflight e execucao
- diferenciar falha de spec, falha de proxy e falha de upstream
- preservar uma baseline repetivel para suites `browser-mocked`, `ssr-mocked`, `stack-real` e blocos focais

Complementa:

- [deploy-and-staging](../../deploy-and-staging.md)
- [operations](../../operations.md)
- [global-setup.ts](../../../apps/frontend/tests/e2e/global-setup.ts)
- [playwright.config.ts](../../../apps/frontend/playwright.config.ts)

## Quando Usar

- antes de um rerun ampliado das suites E2E locais
- quando houver `Bad Gateway`, `500` inesperado ou timeout opaco em export
- quando for necessario distinguir regressao real de contaminacao de estado entre testes
- depois de alterar helpers compartilhados, `global-setup` ou specs centrais de `monitoring`, `audit`, `reports`, `ros-coaf` e `evidence`

## Identificacao da Janela

- `window_id`: `local-e2e-YYYY-MM-DD-a`
- `data_utc`: `preencher`
- `owner_ativo`: `Frontend`
- `apoio`: `Backend/API` / `Platform`
- `objetivo`: `preencher`
- `suite_alvo`: `browser-mocked | ssr-mocked | stack-real | focal`
- `run_url`: `n/a local`

## Checklist de Prontidao

- [ ] `docker` disponivel no host
- [ ] `docker compose` funcional para `../../docker-compose.yml`
- [ ] `node` e `npm` disponiveis no host
- [ ] dependencias instaladas em `apps/frontend`
- [ ] porta base alvo conhecida: `TEST_BASE_URL` ou `http://localhost:8080`
- [ ] `playwright.config.ts` apontando para `global-setup.ts`
- [ ] `global-setup.ts` coerente com os guardrails atuais
- [ ] sem processo concorrente ocupando a mesma porta do `frontend`

## Guardrails Ativos no `global-setup`

Na baseline atual, o `global-setup` faz preflight estrutural antes dos testes:

- garante `frontend` e `traefik` ativos, salvo override explicito
- garante `auth-service`, `compliance-api`, `report-api`, `investigation-api` e `monitoring-api` ativos
- garante `investigation-worker` ativo
- reinicia `traefik` para limpar efeito residual de rate-limit, salvo override
- reseta estado minimo no `postgres`, salvo override

Variaveis uteis de override:

- `ONTRACKCHAIN_E2E_RESET_STATE=false`
- `ONTRACKCHAIN_E2E_RESET_RATE_LIMIT=false`
- `ONTRACKCHAIN_E2E_ENSURE_FRONTEND=false`
- `ONTRACKCHAIN_E2E_ENSURE_CORE_APIS=false`
- `ONTRACKCHAIN_E2E_ENSURE_WORKERS=false`
- `ONTRACKCHAIN_E2E_ALLOW_NO_POSTGRES=true`

## Preflight Estrutural

Executar na ordem abaixo antes do rerun principal.

### 1. Confirmar servicos criticos

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
docker compose -f docker-compose.yml ps \
  traefik \
  frontend \
  postgres \
  auth-service \
  compliance-api \
  report-api \
  investigation-api \
  monitoring-api \
  investigation-worker
```

Esperado:

- `traefik` em `running`
- `frontend` em `running`
- APIs centrais em `running`
- `postgres` em `running`
- `investigation-worker` em `running`

### 2. Corrigir malha incompleta, se necessario

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
docker compose -f docker-compose.yml up -d \
  traefik \
  frontend \
  postgres \
  auth-service \
  compliance-api \
  report-api \
  investigation-api \
  monitoring-api \
  investigation-worker
```

### 3. Confirmar runtime do `frontend`

```bash
curl --fail --silent http://localhost:8080/ >/dev/null
curl --fail --silent http://localhost:8080/auth/config >/dev/null
```

Esperado:

- raiz da app responde
- `/auth/config` responde com configuracao valida

### 4. Preparar dependencias do `frontend`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm ci
```

## Matriz de Execucao

| Modo | Quando usar | Comando canônico |
| --- | --- | --- |
| `stack-real-light` | smoke leve do runtime local | `npm run test:e2e:stack-real-light` |
| `browser-mocked` | superfícies com mocks de browser e frontend local isolado | `npm run test:e2e:browser-mocked` |
| `ssr-mocked` | superfícies que combinam frontend local com backend SSR mockado | `npm run test:e2e:ssr-mocked` |
| `compliance-flows:real` | fluxo real com proxies e APIs locais | `npm run test:e2e:compliance-flows:real` |
| `oidc-auth:real` | runtime OIDC real | `npm run test:e2e:oidc-auth:real` |
| `oidc-critical` | gate OIDC + compliance principal | `npm run test:e2e:oidc-critical` |
| `focal` | rerun de specs ou cenarios pontuais | `npm run test:e2e -- <specs> [--grep "<texto>"]` |

## Sequencia Recomendada de Execucao

### 1. Smoke leve da base local

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e:stack-real-light
```

Gate:

- [ ] sem `Bad Gateway`
- [ ] `frontend` responde localmente
- [ ] `global-setup` nao aborta a execucao

### 2. Suites `browser-mocked`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e:browser-mocked
```

Usar quando a validacao depender de `next dev` local e mocks diretos de browser, sem stack inteira atras do `traefik`.

### 3. Suites `ssr-mocked`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e:ssr-mocked
```

Usar quando a validacao depender de frontend local com backend SSR mockado, como nos fluxos contextuais do `dashboard`.

### 4. Suite real de `compliance-flows`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e:compliance-flows:real
```

Usar como canario primario para detectar:

- malha incompleta
- `500` em proxies
- contaminacao de `sessionStorage`

### 5. Gate focal de export/download endurecido

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e -- \
  tests/e2e/audit-labels.spec.ts \
  tests/e2e/reports-history.spec.ts \
  tests/e2e/roscoaf-regulatory-dossier.spec.ts \
  tests/e2e/evidence-roscoaf-dossier.spec.ts \
  tests/e2e/evidence-custody.spec.ts
```

Esperado:

- exports validados por `waitForResponse` + `content-disposition`
- sem dependencia de `waitForEvent("download")` em superfícies `fetch/blob`

### 6. Rerun ampliado da baseline endurecida

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm run test:e2e -- \
  tests/e2e/compliance-flows.spec.ts \
  tests/e2e/audit-labels.spec.ts \
  tests/e2e/reports-history.spec.ts \
  tests/e2e/roscoaf-regulatory-dossier.spec.ts \
  tests/e2e/evidence-roscoaf-dossier.spec.ts \
  tests/e2e/evidence-custody.spec.ts
```

Baseline validada nesta rodada:

- `66 passed`
- `2 skipped`

## Playbooks de Triagem

### Sintoma: `Bad Gateway` ao abrir pagina

Causa mais provavel:

- `frontend` parado
- `traefik` roteando para upstream indisponivel

Verificar:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
docker compose -f docker-compose.yml ps frontend traefik
```

Acao:

```bash
docker compose -f docker-compose.yml up -d frontend traefik
```

### Sintoma: `500` em endpoints reais do `frontend`

Causa mais provavel:

- APIs centrais desligadas ou `Exited (0)`

Verificar:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
docker compose -f docker-compose.yml ps -a \
  auth-service \
  compliance-api \
  report-api \
  investigation-api \
  monitoring-api
```

Acao:

```bash
docker compose -f docker-compose.yml up -d \
  auth-service \
  compliance-api \
  report-api \
  investigation-api \
  monitoring-api
```

### Sintoma: timeout em export/download

Causa mais provavel:

- teste esperando endpoint errado
- uso de oraculo fragil para superficie `fetch/blob`
- assert interno em mock abortando a resposta

Regra:

- `fetch/blob` -> validar por `waitForResponse` + `content-disposition`
- request critico -> validar payload com `waitForRequest`
- evitar `expect(...)` dentro de `page.route(...)` quando isso puder mascarar timeout

Mapeamentos criticos validados:

- `evidence-manual-package-export-chain` -> `/api/app/audit/evidence-export`
- `evidence-manual-package-export-package` -> `/api/app/evidence/manual-package`

### Sintoma: selecao/paginacao nao reidratada entre testes

Causa mais provavel:

- contaminacao residual de `sessionStorage`

Regra:

- para cenarios sensiveis de persistencia, iniciar com `openPageWithCleanSessionStorage(page, "/monitoring")`
- ao validar handoff `alerts -> monitoring`, aceitar a normalizacao do `status` para `all`

## Artefatos a Preservar

- `apps/frontend/playwright-report/`
- `apps/frontend/test-results/junit.xml`
- screenshots e videos de `test-results/`
- logs temporarios:
  - `/tmp/ontrackchain-browser-mocked-dev.log`
  - `/tmp/ontrackchain-stack-real-light-dev.log`
- anotar o comando exato executado
- anotar o primeiro sintoma observavel e o servico raiz da falha

## Gate de Saida

Marcar a malha local como pronta para a proxima frente somente se todos forem verdadeiros:

- [ ] preflight estrutural concluido
- [ ] `stack-real-light` verde
- [ ] suite focal do alvo em verde
- [ ] nenhum `Bad Gateway` residual
- [ ] nenhum `500` residual de upstream critico
- [ ] artefatos minimos preservados
- [ ] causa raiz do ultimo vermelho classificada como `spec`, `proxy`, `upstream` ou `estado`

## Resultado da Janela

- `decisao_sugerida`: `go | pending | no-go`
- `motivo_resumido`: `preencher`
- `maior_bloqueio`: `preencher`
- `owner_da_escalacao`: `preencher`
- `proximo_passo`: `preencher`
