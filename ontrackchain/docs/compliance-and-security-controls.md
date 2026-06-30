# Compliance e Controles de Seguranca

## Objetivo

Consolidar os controles tecnicos e operacionais que ja existem no scaffold e indicar os gaps residuais para uma Fase 2 mais aderente a cenarios regulados.

`[[diagram: fluxo de controle de seguranca e compliance do Ontrackchain mostrando cliente -> frontend -> Traefik/ForwardAuth -> APIs de dominio; propagacao de X-Org-Id, X-User-Id, X-Plan, X-Role, X-Auth-Method e X-Request-Id; PostgreSQL com RLS e audit_logs como trilha central; download de legal_report bloqueado antes de 2FA e liberado apenas para JWT ADMIN com X-2FA=ok ]]`

## Controles Implementados

### 1. Isolamento Multi-tenant

- Controle principal: `PostgreSQL RLS`
- Regra: tabelas sensiveis exigem contexto de organizacao
- Objetivo: impedir vazamento cross-tenant mesmo em caso de erro de aplicacao
- Complemento:
  - contexto injetado por sessao SQL
  - uso de guarda SQL para evitar queries sem `org_id`

### 2. Autenticacao e Contexto Centralizados

- Controle principal: `Traefik ForwardAuth`
- Fontes aceitas:
  - JWT
  - API Key
- Contexto propagado:
  - `X-Org-Id`
  - `X-User-Id`
  - `X-Plan`
  - `X-Role`
  - `X-Auth-Method`

### 3. Controle Financeiro e Billing

- Fluxo obrigatorio:
  - `estimate -> quote_id -> start`
- Controles:
  - `quote` com TTL
  - `plan lock`
  - reserva via `PRE_HOLD`
  - fechamento via `CONFIRMED` ou `REFUND`
- Objetivo:
  - previsibilidade de cobranca
  - bloqueio de downgrade oportunista
  - rastreabilidade financeira

### 4. Auditoria e Correlacao

- Tabela central: `audit_logs`
- Eventos auditados no estado atual:
  - `case_started`
  - `case_completed`
  - `case_failed`
  - `case_flagged_billing_recalc_required`
  - `compliance_risk_checked`
  - `report_generated`
  - `report_downloaded`
  - `operational_alerts_exported`
- Correlacao:
  - `X-Request-Id`
  - `resource_type`
  - `resource_id`
  - `report_id`
  - `file_hash_sha256`

### 5. Controle de Acesso a Relatorios Sensiveis

- Escopo atual: `legal_report`
- Requisitos obrigatorios:
  - `X-Auth-Method=jwt`
  - `X-Role=ADMIN`
  - `X-2FA=ok`
- Garantia validada:
  - tentativa antes do 2FA retorna `403`
  - tentativa negada nao gera `report_downloaded`
  - sucesso apos 2FA gera `report_downloaded`

### 6. Integridade de Relatorios

- `report_id` deterministico
- `download` reproduzivel a partir de:
  - `case_id`
  - `report_type`
  - `created_at`
- Hash de integridade:
  - `file_hash_sha256`
- Garantia validada:
  - hash retornado pela API bate com o arquivo baixado
  - hash bate com `audit_logs.metadata.file_hash_sha256`

### 7. Contencao Operacional de Carga

- Investigacao com limite por plano
- Limite global de concorrencia para MVP
- Comportamento:
  - dentro do limite: `processing`
  - acima do limite: `202 queued` com `position_in_queue`
- Objetivo:
  - evitar degradacao abrupta
  - proteger estabilidade do scaffold

## Controles Validados Automaticamente

### Smoke Runtime

- `quote -> start`
- `plan lock`
- fila/concurrency de investigation
- `report_generated`
- `report_downloaded`
- correlacao por `request_id`
- hash do arquivo
- `legal_report` antes/depois do 2FA

### Playwright

- fluxo `OIDC` critico e regressao local de autenticacao controlada
- jornada critica do usuario
- trilha de auditoria via browser real
- validacao negativa e positiva do `legal_report`

## Gaps Residuais

### 1. Autenticacao de Producao

- Estado atual:
  - `OIDC` local validado com `Keycloak + PKCE`
  - `TOTP` real no fluxo JWT local
- Gap:
  - homologar IdP corporativo e MFA serio em ambiente nao-dev

### 2. Controles de Tentativa Negada

- Estado atual:
  - tentativa negada de `legal_report` e validada, mas nao ha evento dedicado de auditoria negativa persistido
- Gap:
  - registrar `download_blocked_pre_2fa` ou equivalente

### 3. Retention e Governanca de Logs

- Estado atual:
  - `audit_logs` existe e possui RLS
- Gap:
  - retention policy
  - estrategia de arquivamento
  - trilha de exportacao segura

### 4. Compliance Regulatorio Profundo

- Estado atual:
  - baseline de COAF/BCB
  - `risk-check` com dimensoes
- Gap:
  - schema mais completo
  - versao de formularios/relatorios
  - classificacao de evidencias

### 5. Execucao Assincrona Real

- Estado atual:
  - worker real com Redis para investigation
  - DLQ operacional, retry/backoff e snapshot administrativo
- Gap:
  - isolamento mais forte, idempotencia ampliada e hardening de producao

## Matriz Resumida

| Area | Controle Atual | Nivel | Gap Principal |
|---|---|---|---|
| Tenant isolation | `RLS` + contexto SQL | Forte | auditar queries negadas |
| Auth | `ForwardAuth` + JWT/API Key | Medio | IdP/MFA real |
| Billing | `quote -> start -> PRE_HOLD` | Forte | reconciliação mais rica |
| Audit trail | `audit_logs` + `request_id` | Forte | retention/export |
| Reports sensiveis | `JWT + ADMIN + 2FA` | Forte | auditar negacoes explicitamente |
| Concurrency | worker Redis + DLQ + limites por plano | Forte | hardening/idempotencia |
| Compliance | baseline KYW/COAF | Medio | schema regulatorio ampliado |

## Recomendacoes Imediatas

- adicionar auditoria explicita para acessos negados sensiveis
- expandir a tela de auditoria atual com exportacao e filtros mais ricos
- formalizar retention de `audit_logs`
- evoluir autenticacao dev para fluxo real antes de staging regulado

## Criterio de Maturidade para Proxima Fase

O projeto pode avancar para uma Fase 2 regulatoria quando:

- auth serio deixar de depender de trilhos locais controlados
- auditoria puder ser consultada pela operacao
- eventos negativos sensiveis forem persistidos
- trilha operacional e exportacao auditada estiverem maduras para uso controlado
- schema de compliance/report estiver versionado
