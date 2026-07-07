# Validacao e Auditoria

## Objetivo

Garantir que o Ontrackchain continue:

- executavel
- rastreavel
- auditavel
- honesto em cenarios degradados
- seguro em fluxos regulatorios sensiveis

## Camadas de Validacao

### 1. Smoke Runtime

Arquivo principal:

- `scripts/smoke_runtime.py`

O que prova hoje:

- `quote -> start` e `plan lock`
- investigation assincrona com worker real
- `report_generated` e `report_downloaded`
- enforcement de `legal_report`
- correlacao por `request_id`
- metadados do provider RPC no resultado final
- consistencia de hash do arquivo baixado

### 2. Playwright E2E

Suites relevantes:

- `tests/e2e/critical-path.spec.ts`
- `tests/e2e/compliance-flows.spec.ts`
- trilho `OIDC` critico
- trilho `dev-auth` apenas para regressao do scaffold local

O que cobre hoje:

- login e callback OIDC
- dashboard e navegacao principal
- `/audit` e `/monitoring`
- export administrativo auditado
- `legal_report` antes/depois de `2FA`
- fluxos de compliance e monitoring visiveis pelo browser real

Comandos focados uteis:

- `npm run test:e2e:stack-real-light` para a smoke suite SSR leve da homepage, subindo o frontend local automaticamente e validando o estado anonimo sem depender de backend autenticado
- `npm run test:e2e:api-consumer:real` para validar a API publica e os endpoints `/api/v1/*` contra a stack real, com preflight explicito de `baseURL` e `auth/config`
- `npm run test:e2e:critical-path:real` para o fluxo OIDC com investigacao, worker, billing e download reais, falhando cedo se o runtime OIDC nao estiver pronto
- `npm run test:e2e:compliance-flows:real` para RBAC, auditoria e trilhas administrativas na stack real com preflight explicito do frontend
- `npm run test:e2e:oidc-auth:real` para o spec de autenticacao federada, falhando cedo se `AUTH_MODE=oidc` ou o runtime OIDC nao estiverem prontos
- `npm run test:e2e:dev-auth` para a regressao local do scaffold `AUTH_MODE=dev`, com preflight explicito de frontend e validacao focada do fluxo `2FA` local
- `npm run test:e2e:browser-mocked` para as suites que mockam `page.route(...)` no browser, sobem o frontend local automaticamente e nao exigem backend real
- `npm run test:e2e:ssr-mocked` para suites que exigem backend SSR mockado e frontend iniciado com `INTERNAL_API_BASE_URL` apontando para o mock
- `npm run test:e2e:alerts-dashboard-context`
- `npm run test:e2e:alerts-dashboard-context:mocked` para subir mock SSR do `dashboard`, iniciar o frontend com `INTERNAL_API_BASE_URL` apontando para o mock e executar o spec combinado de links contextuais sem depender de terminais manuais
- `npm run test:e2e:oidc-critical` permanece como comando canonico agregado para o rito serio de OIDC, agora com preflight explicito de prontidao antes da execucao

Classificacao operacional atual:

| Suite | Classe | Dependencia principal | Comando recomendado |
| --- | --- | --- | --- |
| `ui-home.spec.ts` | stack real leve | homepage SSR anonima com frontend local; so consulta catalogos reais quando houver sessao autenticada | `npm run test:e2e:stack-real-light` |
| `api-consumer.spec.ts` | stack real | API publica e `/api/v1/*` | `npm run test:e2e:api-consumer:real` |
| `critical-path.spec.ts` | stack real | auth, worker, billing e download real | `npm run test:e2e:critical-path:real` |
| `compliance-flows.spec.ts` | stack real | OIDC/dev auth, RBAC, audit, monitoring e investigacao reais | `npm run test:e2e:compliance-flows:real` |
| `oidc-auth.spec.ts` | stack real | provedor OIDC e sessoes reais | `npm run test:e2e:oidc-auth:real` |
| `reports-history.spec.ts` | browser mockavel | `page.route(...)` para `api/app/*` com frontend local | `npm run test:e2e:browser-mocked` |
| `audit-labels.spec.ts` | browser mockavel | `page.route(...)` para `api/app/audit/logs` com frontend local | `npm run test:e2e:browser-mocked` |
| `team-role-labels.spec.ts` | browser mockavel | frontend local + `auth/context` mockado + roster local no browser | `npm run test:e2e:browser-mocked` |
| `case-report-type-fallback.spec.ts` | browser mockavel | `page.route(...)` para `investigation/status` e fallback de `report-types` com frontend local | `npm run test:e2e:browser-mocked` |
| `evidence-custody.spec.ts` | browser mockavel | `page.route(...)` para `api/app/*` e downloads mockados com frontend local | `npm run test:e2e:browser-mocked` |
| `operational-context-links.spec.ts` | browser mockavel | `page.route(...)` para `sanctions` e `blocks` com frontend local | `npm run test:e2e:browser-mocked` |
| `timeline-workspace.spec.ts` | browser mockavel | `page.route(...)` para timeline/work-items por cockpit com frontend local | `npm run test:e2e:browser-mocked` |
| `alerts-dashboard-context-links.spec.ts` | SSR mockado misto | `alerts` mockavel no browser e `dashboard` dependente de backend SSR mockado | `npm run test:e2e:ssr-mocked` |

### 3. Testes Focados de Compliance e Worker

Coberturas importantes:

- `tests/test_sanctions_sync_worker.py`
- `tests/test_worker_source_url_overrides.py`
- `tests/test_preflight_guards.py`
- `tests/test_check_sanctions_sync_status.py`
- `tests/test_check_compliance_provider_runtime.py`
- `tests/test_sprint2_compliance_agents.py`

O que essas suites cobrem:

- sync de listas com fallback
- override de `source_url` por env
- preflight de feeds externos e URLs serias
- validacao pos-sync em `sanctions_lists_meta`
- agentes de bloqueio, contraparte e ROS

### 4. Preflights e Janela Seria

Scripts canonicos:

- `preflight_oidc_serious_env.py`
- `run_oidc_readiness_bundle.py`
- `preflight_external_integrations.py`
- `check_staging_env_placeholders.py`
- `check_staging_env_handoff.py`
- `check_staging_env_ownership_coverage.py`
- `run_staging_window.py`

O que eles validam:

- auth serio sem fallback indevido para `dev`
- consolidacao de `P0-01` em bundle OIDC anexavel
- URLs, retries, timeouts e secrets de integracoes externas
- ausencia de placeholders criticos
- ownership e handoff do `.env.staging.private`
- consolidacao da janela em dossier e manifestos

### 5. Runtime do Provider AML/KYT

Script canonico:

- `scripts/check_compliance_provider_runtime.py`

O que valida:

- `GET /internal/provider-readiness` em `ready=true`
- `GET /api/v1/compliance/operations/kyc_wallet` com `provider_status=live`
- `POST /api/v1/compliance/kyc-wallet` com `provider_status=live`
- convergencia entre configuracao interna e contrato publico do runtime

### 6. Pos-Sync de Sancoes

Script canonico:

- `scripts/check_sanctions_sync_status.py`

O que valida:

- `OFAC_SDN`, `UN_CSNU` e `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`
- divergencia entre `source_url` persistido e override configurado
- endurecimento adicional quando `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` esta preenchida

## Trilha de Auditoria

### `audit_logs`

Eventos principais observados:

- `case_started`
- `case_completed`
- `case_failed`
- `compliance_risk_checked`
- `compliance_sanctions_checked`
- `preventive_block_evaluated`
- `coaf_report_generated`
- `coaf_report_approved`
- `coaf_report_rejected`
- `coaf_report_submitted_manual`
- `report_downloaded`
- `operational_alerts_exported`
- `authorization_denied`

### `evidence_trail`

Eventos relevantes em uso:

- `SANCTIONS_CHECKED`
- `SANCTIONS_HIT`
- `BLOCK_*`
- `COUNTERPARTY_ONBOARDED`
- `COAF_ROS_GENERATED`
- `COAF_ROS_APPROVED`
- `COAF_ROS_REJECTED`
- `COAF_ROS_SUBMITTED_MANUAL`

## Comandos Recomendados

### Runtime local

```bash
python scripts/smoke_runtime.py
make apply-regulatory-work-items-migration
make smoke-work-items-ownership-backend
cd apps/frontend
npm ci
npm run test:e2e:oidc-critical
npm run test:e2e
```

### Integracoes externas e sancoes

```bash
python scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
make run-eu-sanctions-window-local WINDOW_ID=stg-YYYY-MM-DD-eu
python scripts/check_sanctions_sync_status.py
```

### Janela seria completa

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

Pacote esperado quando aplicável:

- `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json` para `P0-01`
- `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md` para `P0-01`
- `artifacts/staging/checks/<janela>-regulatory-readiness-bundle.json` para `P0-02/P0-03`
- `artifacts/staging/dossiers/<janela>-regulatory-readiness-bundle.md` para `P0-02/P0-03`

## Gaps Residuais de Validacao

- `AML/KYT` live ainda depende de credenciais reais e homologacao recorrente; o checker novo valida runtime, mas nao substitui a evidencia institucional da janela seria
- o feed da UE pode depender de URL tokenizada real para fechar a prova operacional
- `due_diligence` e `source_of_funds` ainda nao possuem harness regulatorio equivalente ao screening local de sancoes
- os runners e checkers atuais ainda precisam ser exercitados de forma recorrente nas janelas homologadas

## Criterios Tecnicos Atuais

- stack sobe com `docker compose`
- smoke runtime passa
- smoke backend de ownership de `work-items` (`make smoke-work-items-ownership-backend`) passa
- Playwright critico/compliance passa
- hashes de report continuam reproduziveis
- `report_downloaded` continua auditado
- `coaf_report_*` deixa trilha em `audit_logs` e `evidence_trail`
- `check_compliance_provider_runtime.py` e parte do rito quando houver janela de homologacao `AML/KYT live`
- `make run-eu-sanctions-window-local` e parte do rito quando houver janela de sancoes da UE com persistencia de artefatos
- `make run-eu-sanctions-window` permanece disponivel para execucao mais controlada
- `make check-eu-sanctions-window` permanece como validacao pontual do estado persistido
- `check_sanctions_sync_status.py` continua como checker generico para o estado persistido das listas
