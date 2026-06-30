# Arquitetura

## Visao Geral

O `Ontrackchain` e uma plataforma modular para investigacao e compliance on-chain, estruturada como um conjunto de servicos independentes atras de um gateway unico.

`[[diagram: arquitetura do scaffold Ontrackchain com Traefik como gateway na borda, encaminhando requests autenticadas para auth-service, investigation-api, compliance-api, monitoring-api, report-api e frontend Next.js; PostgreSQL com RLS compartilhado pelos servicos de dominio; Redis apoiando investigation e monitoring; fluxo de browser -> frontend -> proxies internos -> gateway -> APIs; audit_logs e credit_ledger como trilhas centrais; legal_report exigindo JWT ADMIN e 2FA antes do report-api ]]`

## Componentes

### Gateway

- `Traefik`
- Responsabilidade:
  - roteamento por `PathPrefix`
  - `ForwardAuth` central
  - propagacao de contexto autenticado
- Headers propagados:
  - `X-Org-Id`
  - `X-User-Id`
  - `X-Plan`
  - `X-Role`
  - `X-Auth-Method`

### Auth Service

- Emite token JWT de desenvolvimento
- Valida `Bearer token` e `X-API-Key`
- Resolve contexto autorizado para o gateway
- Funciona como pilar de:
  - autenticacao
  - enriquecimento de contexto
  - enforcement inicial de RBAC

### Investigation API

- Dominio de investigacao on-chain
- Responsabilidades:
  - catalogo de `report-types`
  - cotacao (`estimate`)
  - execucao (`start`)
  - status/resultados
  - billing de investigation
  - audit logs consolidados
- Regras criticas:
  - fluxo obrigatorio `quote -> start`
  - `plan lock` entre cotacao e execucao
  - controle de concorrencia por plano e global
  - se limite estourar: retorna `202` com `position_in_queue`
  - Bitcoin MVP limitado a `3 hops`

### Compliance API

- Dominio de screening e relatorios de compliance
- Responsabilidades:
  - catalogo de operacoes
  - `estimate/start`
  - `risk-check`
  - geracao de report compliance
  - trilha auditavel por `request_id`
  - métricas agregadas internas para observabilidade central
- Regras criticas:
  - aliases resolvidos para identificadores canonicos
  - `report_generated` registra `report_id`, `file_hash_sha256`, `created_at`

### Monitoring API

- Dominio de watchlists e alertas
- Responsabilidades:
  - catalogo de operacoes
  - `estimate/start`
  - criacao/listagem de watchlists
  - persistencia de alertas
  - endpoint de teste para disparo de alerta
  - receiver interno do `Alertmanager` para incidentes globais de plataforma
  - listagem administrativa de incidentes globais com filtros, cursor e total filtrado
  - catalogo dinamico de `service` e `receiver` para a UI administrativa
  - acknowledge unitario e em lote para triagem operacional
  - export administrativo `CSV|JSON` com trilha em `audit_logs`
- Regras criticas:
  - `plan lock`
  - `audit_logs` em `case_started`
  - tabela `monitoring_alerts` com RLS

### Report API

- Dominio de renderizacao/download de relatorios
- Responsabilidades:
  - gerar bytes deterministas de PDF
  - disponibilizar download reproduzivel
  - registrar auditoria de download
  - métricas agregadas internas para observabilidade central
- Regras criticas:
  - `report_id` deterministico
  - `file_hash_sha256` deterministico
  - `legal_report` exige:
    - `X-Auth-Method=jwt`
    - `X-Role=ADMIN`
    - `X-2FA=ok`
  - `report_downloaded` gera audit log quando ha contexto de org

### Frontend

- `Next.js 14`
- Responsabilidades:
  - UI operacional do scaffold
  - fluxo `OIDC` com callback dedicado e sessao local controlada
  - proxies internos para o gateway
  - propagacao de `X-Request-Id`
  - consulta operacional de `audit_logs` para operadores `ADMIN`
  - tela `/monitoring` com filtros dinamicos, selecao acumulada e export administrativo auditado
- Papeis principais:
  - impedir acesso a `legal_report` antes do 2FA
  - servir como caminho real para validacao E2E
  - persistir recorte, cursor e selecao da triagem administrativa em `sessionStorage`

### PostgreSQL

- Fonte central de estado
- Tabelas-chave:
  - `organizations`
  - `users`
  - `cases`
  - `reports`
  - `credit_ledger`
  - `audit_logs`
  - `watchlists`
  - `watchlist_items`
  - `monitoring_alerts`
  - `operational_alert_events`
- Regras criticas:
  - `RLS` habilitado nas tabelas multi-tenant
  - contexto obrigatorio via `app.organization_id`
  - validacao de API Key via funcao SQL segura

### Redis

- Apoio a `public-api`, `investigation-api` e `monitoring-api`
- No estado atual, sustenta o worker assíncrono real de `investigation`
- Filas canônicas:
  - `investigation:queue:ready`
  - `investigation:queue:waiting`
  - `investigation:queue:retry`
- Também armazena contadores voláteis de concorrência por organização e global

## Fluxos Canonicos

### Billing

```text
estimate -> quote_id (TTL 15 min) -> start -> PRE_HOLD -> CONFIRMED | REFUND
```

Regras:

- downgrade apos quote bloqueia execucao com `402`
- upgrade apos quote exige `202 requote_required`
- execucao sem confirmacao explicita falha

### Investigacao

```text
cliente -> estimate -> quote
cliente -> start
  -> se dentro do limite: case processing/queued
  -> se acima do limite: 202 + position_in_queue
worker interno (Redis) -> promote waiting -> process -> retry/backoff -> complete/fail
billing -> confirmed/refund
audit -> case_started/case_promoted_from_queue/case_completed/case_failed
```

Observabilidade operacional atual:

- snapshot `ADMIN` via `GET /api/v1/investigation/admin/operations`
- métricas de fila (`ready`, `waiting`, `retry_pending`, `retry_due`)
- contadores de concorrência por organização e global
- throughput da última hora e média recente de duração dos `agent_runs`
- DLQ explícita para falhas permanentes com `GET /api/v1/investigation/admin/dlq`
- requeue manual controlado por `ADMIN`, com novo `PRE_HOLD` antes de retornar o case para `queued|processing`
- resolução administrativa da DLQ com `acknowledged|discarded`, sem alterar o `status=failed`
- alertas operacionais avaliados em `GET /api/v1/investigation/admin/alerts`
- métricas Prometheus compatíveis em `GET /api/v1/investigation/admin/metrics`
- scraping central real via endpoint interno `GET /internal/metrics/prometheus` consumido pelo `Prometheus`
- regras de alerta carregadas em `infra/observability/investigation.rules.yml`
- dashboards operacionais provisionados no `Grafana`, alimentados pelo datasource `Prometheus`
- `monitoring-api` tambem exporta agregados internos para `GET /internal/metrics/prometheus`
- regras de `monitoring` carregadas em `infra/observability/monitoring.rules.yml`
- `compliance-api` tambem exporta agregados internos para `GET /internal/metrics/prometheus`
- regras de `compliance` carregadas em `infra/observability/compliance.rules.yml`
- `report-api` tambem exporta agregados internos para `GET /internal/metrics/prometheus`
- regras de `report` carregadas em `infra/observability/report.rules.yml`
- `Alertmanager` recebe as regras do `Prometheus` e entrega webhooks internos ao `monitoring-api`
- `platform.rules.yml` adiciona um watchdog sentinela para validar a cadeia `Prometheus -> Alertmanager -> receiver`
- incidentes globais sao persistidos em `operational_alert_events`, sem acoplamento com `audit_logs` multi-tenant
- `operational_alert_events` agora separa `status` tecnico (`firing/resolved`) de `triage_status` operacional (`pending/acknowledged`)
- a UI `/monitoring` permite triagem manual de incidentes globais sem alterar a verdade tecnica do alerta
- a UI `/monitoring` suporta recorte por `status`, `triage_status`, `service`, `receiver` e `severity`, com paginação cursor-based e `total_count`
- a UI `/monitoring` permite selecionar incidentes em multiplas paginas do mesmo recorte, persistir esse estado na aba atual e exportar `filtered|selected` em `CSV|JSON`
- cada export administrativo gera `operational_alerts_exported` em `audit_logs`, correlacionado por `request_id`
- trade-off atual: endpoint interno nao e publico via Traefik, mas ainda depende de isolamento de rede do ambiente

### Incidentes Globais de Plataforma

```text
Prometheus rules -> Alertmanager -> monitoring-api webhook
  -> operational_alert_events
  -> UI /monitoring (filtros dinamicos + cursor + selecao acumulada)
    -> acknowledge unitario/lote
    -> export filtered|selected
      -> frontend proxy valida token no auth-service
      -> monitoring-api exporta arquivo
      -> audit_logs registra operational_alerts_exported
```

### Compliance Report

```text
estimate -> start -> report_generated -> download -> report_downloaded
```

Correlacao validada:

- `request_id`
- `resource_id`
- `report_id`
- `file_hash_sha256`

### Legal Report com 2FA

```text
login -> cookie otc_token
2FA pendente -> cookie otc_2fa=pending
download legal_report -> 403
verificacao 2FA -> otc_2fa=ok
download legal_report -> 200
audit -> report_downloaded
```

## Decisoes Arquiteturais Relevantes

### 1. RLS no banco em vez de isolamento apenas na aplicacao

- Motivo: reduzir risco de vazamento cross-tenant
- Beneficio: ultima linha de defesa no banco
- Trade-off: maior rigor nas queries e no bootstrap

### 2. Gateway com ForwardAuth central

- Motivo: padronizar contexto e evitar replicacao de auth em cada servico
- Beneficio: uniformidade de `X-* headers`
- Trade-off: dependencia forte do `auth-service`

### 3. Billing por quote explicito

- Motivo: previsibilidade financeira e enforcement por plano
- Beneficio: trilha clara de cobranca
- Trade-off: mais estados de negocio

### 4. Auditoria append-only

- Motivo: compliance, rastreabilidade e investigacao forense
- Beneficio: correlacao ponta a ponta
- Trade-off: necessidade de filtros e retention futura

### 5. Report deterministico

- Motivo: permitir reproducao de hash e validacao automatizada
- Beneficio: smoke/E2E conseguem comprovar integridade
- Trade-off: ainda nao representa renderer final de producao

## Regras de Negocio Criticas

- `org_id` sempre obrigatorio para dominios protegidos
- aliases de operacao e report sao sempre resolvidos para valores canonicos
- `legal_report` nao pode ser baixado por API Key
- `audit_logs` e `credit_ledger` devem receber `request_id` nos fluxos criticos
- `report_downloaded` so deve existir quando o report-api e realmente alcançado

## Escopo Atual vs Futuro

### MVP

- EVM-first
- Bitcoin basico ate `3 hops`
- watchlists e alertas persistidos
- compliance/reporting scaffold

### Fase 2

- autenticacao OIDC e 2FA reais para ambientes fortes
- provedores reais AML/KYT e RPC com fallback
- politicas de retention, backup/restore e exportacao segura multi-dominio
- OpenAPI formal e paginacao mais rica para trilhas de auditoria
- schema regulatorio e versionamento de evidencias mais maduros
