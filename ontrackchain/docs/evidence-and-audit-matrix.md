# Matriz de Evidencias e Auditoria

## Objetivo

Relacionar cada fluxo critico do scaffold com:

- eventos auditados
- identificadores de correlacao
- artefatos gerados
- validacao automatizada existente

Este documento ajuda a responder: "que evidencia tecnica o sistema gera hoje para provar que um fluxo ocorreu da forma esperada?"

## Estrutura da Evidencia

Cada evidencia relevante deve idealmente permitir correlacao entre:

- request
- usuario/organizacao
- recurso afetado
- relatorio gerado ou baixado
- hash do artefato

## Matriz Atual

| Fluxo | Evento(s) | Chaves de Correlacao | Artefato | Validacao Atual |
|---|---|---|---|---|
| Investigation start | `case_started` | `request_id`, `resource_id` | case | smoke |
| Investigation complete | `case_completed` | `request_id`, `resource_id` | status final | smoke parcial |
| Investigation fail | `case_failed` | `request_id`, `resource_id` | status final | cobertura indireta |
| Billing drift | `case_flagged_billing_recalc_required` | `request_id`, `resource_id` | ajuste pendente | smoke |
| Compliance risk check | `compliance_risk_checked` | `request_id`, endereco, chain | score e dimensoes | Playwright |
| Compliance report generate | `report_generated` | `request_id`, `resource_id`, `report_id`, `file_hash_sha256` | report logico | smoke + Playwright |
| Compliance report download | `report_downloaded` | `request_id`, `case_id`, `report_id`, `file_hash_sha256` | PDF baixado | smoke |
| Legal report pre-2FA | ausencia de `report_downloaded` | `request_id` | tentativa negada | smoke + Playwright |
| Legal report pos-2FA | `report_downloaded` | `request_id`, `case_id`, `report_id`, `file_hash_sha256` | PDF baixado | smoke + Playwright |
| Monitoring start | `case_started` | `request_id`, `resource_id` | case/watchlist | smoke |
| Monitoring alert | alerta persistido | `watchlist_id`, `address`, `chain` | `monitoring_alerts` | smoke + Playwright |
| Operational alert export | `operational_alerts_exported` | `request_id`, `organization_id`, `filters`, `scope` | arquivo `CSV/JSON` + trilha de auditoria | Playwright |
| RBAC deny (core admin) | `authorization_denied` | `request_id`, `effective_role`, `allowed_roles`, `endpoint` | tentativa negada em `monitoring`, `investigation` ou `audit/logs` | Playwright |

## Evidencias por Dominio

### Investigation

Evidencias disponiveis:

- `audit_logs` com `case_started`, `case_completed`, `case_failed`
- `credit_ledger` com trilha financeira
- `cases` com estado final

Principais chaves:

- `request_id`
- `case_id`
- `organization_id`

### Compliance

Evidencias disponiveis:

- `compliance_risk_checked`
- `report_generated`
- `report_downloaded`
- `file_hash_sha256`

Principais chaves:

- `request_id`
- `case_id`
- `report_id`
- `file_hash_sha256`

### Monitoring

Evidencias disponiveis:

- `case_started`
- `monitoring_alerts`
- `operational_alert_events`
- `operational_alerts_exported`

Principais chaves:

- `request_id`
- `watchlist_id`
- `address`
- `receiver`
- `service`

## Artefatos Auditaveis

### `audit_logs`

Campos de maior valor:

- `organization_id`
- `user_id`
- `action`
- `resource_type`
- `resource_id`
- `metadata.request_id`
- `metadata.report_id`
- `metadata.file_hash_sha256`

### `credit_ledger`

Campos de maior valor:

- `organization_id`
- `entry_type`
- `credits`
- `metadata.quote_id`
- `metadata.request_id`

### `reports`

Campos de maior valor:

- `case_id`
- `report_type_requested`
- `external_report_id`
- `content_type`

## O que o Smoke Valida Hoje

- request IDs deterministas por etapa
- correlacao `request_id -> action`
- correlacao `request_id -> resource_id`
- correlacao `request_id -> report_id`
- correlacao `request_id -> file_hash_sha256`
- ausencia de download auditado antes do 2FA
- presenca de download auditado apos o 2FA

## O que o Playwright Valida Hoje

- jornada real do browser
- fluxo `OIDC` critico e regressao local de autenticacao controlada
- tentativa negada de `legal_report`
- tentativa bem-sucedida apos 2FA
- presenca/ausencia correta de `report_downloaded`

## Gaps de Evidencia

### 1. Eventos Negados Persistidos

- hoje a tentativa negada pode ser inferida por ausencia de evento de download
- gap:
  - nao existe ainda um evento dedicado como `report_download_blocked`

### 2. Exportacao de Evidencia

- existe export administrativo auditado para incidentes globais de plataforma
- avancou:
  - agora existe bundle auditado e filtravel cruzando `audit_logs`, `credit_ledger` e metadados de `reports`
- gap residual:
  - ainda falta expandir o bundle para artefatos complementares de compliance/manual review quando houver necessidade regulatoria especifica

### 3. Versionamento de Artefatos

- os relatorios sao deterministas, mas ainda nao ha versionamento de template/renderer

### 4. Cadeia Operacional

- nao ha trilha formal de aprovacao humana ou revisao juridica

## Uso Recomendado

Esta matriz deve ser consultada quando:

- houver incidente
- for necessario demonstrar trilha de auditoria
- uma nova feature impactar fluxo sensivel
- for criada nova validacao automatizada

## Evolucao Recomendada

- adicionar eventos explicitos de negacao
- expandir o bundle atual para incluir mais dominios alem de `audit_logs`, `credit_ledger` e `reports`, preservando filtros por `request_id`, `case_id`, `report_id`
- incluir hash e versionamento de template em todos os reports sensiveis
- ligar esta matriz a dashboards/consultas operacionais no frontend
