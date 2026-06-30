# Validacao e Auditoria

## Objetivo

Garantir que o scaffold continue:

- executavel
- rastreavel
- consistente financeiramente
- seguro em fluxos sensiveis

## Camadas de Validacao

### 1. Smoke Runtime

Arquivo:

- [smoke_runtime.py](../scripts/smoke_runtime.py)

Executa validacao end-to-end por HTTP real contra o gateway.

### Cobertura atual do smoke

- monitoring:
  - catalogo
  - estimate
  - start
- compliance:
  - catalogo
  - catalogo com capability operacional (`provider_status`, `capability_status`, `delivery_mode`) validando `kyc_wallet` e `due_diligence`
  - estimate
  - start
  - report
- `legal_report`:
  - bloqueio antes do 2FA
  - download liberado apos 2FA
- investigation:
  - concorrencia/queue
  - finalizacao
  - resultado final preservando `kyw_summary.rpc.provider_status` e `rpc_source`
- billing:
  - efeitos colaterais de `PRE_HOLD`
  - `plan lock`
- auditoria:
  - `case_started`
  - `report_generated`
  - `report_downloaded`
- integridade:
  - hash do arquivo baixado igual ao hash informado

### Como rodar o smoke

```bash
python scripts/smoke_runtime.py
```

### O que o smoke prova hoje

- `X-Request-Id` e propagado ponta a ponta
- `audit_logs.metadata.request_id` recebe o valor esperado
- `resource_type/resource_id` batem com o case correto
- `report_id` e `file_hash_sha256` do audit log batem com a resposta da API
- `report_downloaded` so aparece apos acesso efetivo ao `report-api`
- `legal_download_pre_2fa` nao gera `report_downloaded`
- `investigation/{case_id}/result` preserva metadados do provider RPC no payload final do caso

## 2. Playwright E2E

Arquivos:

- [critical-path.spec.ts](../apps/frontend/tests/e2e/critical-path.spec.ts)
- [compliance-flows.spec.ts](../apps/frontend/tests/e2e/compliance-flows.spec.ts)
- [ui-home.spec.ts](../apps/frontend/tests/e2e/ui-home.spec.ts)
- [api-consumer.spec.ts](../apps/frontend/tests/e2e/api-consumer.spec.ts)

### Cobertura relevante

- fluxo `OIDC` critico validado por browser real
- regressao local de `dev auth` isolada do gate sério
- dashboard e navegação principal
- consulta administrativa de auditoria em `/audit`
- investigation estimate/start/status
- billing balance
- monitoramento e alertas
- incidentes globais de plataforma com:
  - filtro por `severity` e `receiver`
  - paginação cursor-based
  - selecao acumulada com persistencia em `sessionStorage`
  - export `CSV|JSON` do recorte filtrado ou dos itens selecionados
- compliance risk-check/report
- `legal_report`:
  - `403` antes do 2FA
  - `200` apos 2FA
  - audit log sem `report_downloaded` antes
  - audit log com `report_downloaded` depois

### Como rodar

```bash
cd apps/frontend
npx playwright test tests/e2e/critical-path.spec.ts tests/e2e/compliance-flows.spec.ts
```

## 3. CI

Workflows:

- [e2e-tests.yml](../.github/workflows/e2e-tests.yml)
- [quality-gates.yml](../.github/workflows/quality-gates.yml)

### O que a pipeline faz

- sobe a stack docker
- espera o gateway responder
- instala dependencias do frontend
- instala browser do Playwright
- roda toda a suite Playwright
- publica artefatos
- executa quality gates de schema, baseline de seguranca, qualidade Python/TypeScript e regressao dos preflights/homologacao

## Trilha de Auditoria

## Eventos principais auditados

- `case_started`
- `case_completed`
- `case_failed`
- `case_flagged_billing_recalc_required`
- `compliance_risk_checked`
- `report_generated`
- `report_downloaded`
- `operational_alerts_exported`

## Estrategia de correlacao

Cada fluxo critico deve carregar `X-Request-Id`.

Esse identificador e propagado por:

- frontend proxies
- APIs de dominio
- smoke runtime
- testes E2E sensiveis

## O que validar em `audit_logs`

- `metadata.request_id`
- `action`
- `resource_type`
- `resource_id`
- `report_id` quando aplicavel
- `file_hash_sha256` quando aplicavel
- `selected_count`, `exported_count` e `filters` quando `action=operational_alerts_exported`

## Exemplo de trilha completa

```text
smoke-<run>-compliance_report
  -> report_generated
  -> resource_type=case
  -> resource_id=<case_id>
  -> metadata.report_id=<report_id>
  -> metadata.file_hash_sha256=<sha256>

smoke-<run>-compliance_report_download
  -> report_downloaded
  -> metadata.case_id=<case_id>
  -> metadata.report_id=<report_id>
  -> metadata.file_hash_sha256=<sha256>

pw-monitoring-export-audit-<run>
  -> operational_alerts_exported
  -> resource_type=operational_alerts
  -> metadata.request_id=<request_id>
  -> metadata.scope=filtered|selected
  -> metadata.format=json|csv
  -> metadata.exported_count=<n>
```

## Seguranca Validada

### Legal Report

Requisitos de sucesso:

- auth deve ser `jwt`
- role deve ser `ADMIN`
- `X-2FA=ok`

### O que e testado

- tentativa negada antes do 2FA
- ausencia de `report_downloaded` na tentativa negada
- sucesso apos 2FA
- presenca de `report_downloaded` no sucesso

## Critérios de Aceitacao Tecnica Atuais

- stack sobe localmente
- smoke runtime passa
- Playwright critical/compliance passa
- hashes de report sao reproduziveis
- `report_downloaded` fica auditado
- `operational_alerts_exported` fica auditado quando operadores exportam backlog global
- `legal_report` respeita `JWT + ADMIN + 2FA`
- `audit_logs` continua acessivel apenas para `ADMIN`

## Riscos Residuais

- smoke runtime tecnico ainda usa trilho `dev-compatible` em parte da validacao local
- a tela `/audit` ja possui paginação operacional `page/limit`, mas ainda nao possui paginação cursor-based propria para volumes extremos
- a retention policy ainda precisa de aprovacao formal de Security/Compliance
- o bundle multi-dominio atual cobre `audit_logs`, `credit_ledger` e metadados persistidos de `reports`, mas ainda nao toda a trilha ampliada de compliance/manual review

## Recomendacoes de Evolucao

- evoluir a tela `/audit` de paginação `page/limit` para cursor-based e filtros operacionais mais ricos quando o volume exigir
- ampliar o bundle atual para artefatos de compliance/manual review mais especializados
- adicionar metricas/alertas para downloads sensiveis
- incluir esses checks em gates de PR mais restritivos
- expandir validacao negativa para outros fluxos sensiveis alem de `legal_report`
