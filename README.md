# Ontrackchain

<p align="center">
  <img src="./ontrackchain/docs/assets/logo.jpeg" alt="Ontrackchain" width="720" />
</p>

Plataforma multi-tenant de investigação e compliance on-chain com foco em trilha auditável, billing controlado por créditos e enforcement de segurança em fluxos sensíveis.

## Estado Atual

- Scaffold executável com `docker compose`
- Gateway central com `Traefik` + `ForwardAuth`
- Banco `PostgreSQL` com `RLS` obrigatório
- Frontend `Next.js` com proxies autenticados
- APIs separadas por domínio:
  - `auth-service`
  - `public-api`
  - `investigation-api`
  - `compliance-api`
  - `monitoring-api`
  - `report-api`
- Validação automatizada por:
  - `scripts/smoke_runtime.py`
  - `Playwright` (`critical-path` + `compliance-flows`)
- Observabilidade central inicial com `Prometheus` para `investigation`
- Dashboard operacional provisionado em `Grafana`
- Observabilidade central expandida para `monitoring`
- Observabilidade central expandida para `compliance`
- Observabilidade central expandida para `report`
- Alerting ativo com `Alertmanager` e receiver interno no `monitoring-api`
- UI administrativa `/audit` consulta `audit_logs` com filtros operacionais para `ADMIN`
- UI administrativa `/monitoring` exibe incidentes globais de plataforma recebidos do `Alertmanager`
- janela séria de `staging` agora pode ser executada ponta a ponta via `run_staging_window.py`, persistindo checks, preflights, homologação e dossier final
- Triagem manual separa `status` técnico do alerta e `triage_status` operacional na UI `/monitoring`
- Lista de incidentes globais agora suporta paginação cursor-based para backlog operacional
- Resumo da lista paginada agora exibe volume filtrado total do backlog operacional
- A triagem administrativa agora suporta filtro adicional por severidade (`info|warning|critical`)
- A triagem administrativa agora também suporta filtro por `receiver`
- Os filtros de `service` e `receiver` da UI administrativa agora são carregados dinamicamente do backend
- A UI administrativa permite reconhecimento em lote dos incidentes pendentes do recorte filtrado
- A UI administrativa agora suporta export do recorte filtrado ou dos incidentes selecionados em `CSV|JSON`
- Cada export administrativo agora gera trilha em `audit_logs` com `request_id`, escopo, formato e filtros aplicados
- A UI administrativa também suporta seleção manual por linha para reconhecimento parcial controlado
- A seleção manual agora pode acumular incidentes em múltiplas páginas dentro do mesmo recorte filtrado
- O recorte e a seleção manual acumulada agora sobrevivem a refresh da página na mesma aba via `sessionStorage`
- A mesma aba agora restaura também a página atual do backlog paginado após refresh

## Objetivo do MVP

Entregar uma base operacional para:

- investigação on-chain multi-chain com foco inicial EVM
- compliance e geração de relatórios auditáveis
- monitoramento com watchlists e alertas
- billing por créditos com cotação prévia e `plan lock`
- isolamento rigoroso por organização

## Princípios Arquiteturais

- `multi-tenant by design`: nenhuma query sensivel deve escapar de `org_id`
- `on-chain mínimo`: o MVP trabalha principalmente off-chain, com preparo para registro/evidência futura
- `quote -> start`: operações cobráveis exigem cotação prévia
- `append-only audit`: eventos relevantes geram trilha em `audit_logs`
- `request correlation`: fluxos criticos propagam `X-Request-Id`
- `segurança > funcionalidade`: `legal_report` exige `JWT + ADMIN + 2FA`

## Arquitetura em 60 segundos

- Edge: `Traefik + ForwardAuth` concentra roteamento e enforcement inicial de auth.
- Identidade: `Keycloak (OIDC)` + `auth-service` para sessão, RBAC e requisitos de `2FA` em fluxos sensíveis.
- Domínios: APIs separadas (`public`, `investigation`, `compliance`, `monitoring`, `report`) para reduzir acoplamento e facilitar governança.
- Dados: `PostgreSQL` com `RLS` como default e `Redis` para fila/cache onde aplicável.
- Observabilidade: `Prometheus -> Alertmanager -> monitoring-api`, com UI de triagem e export auditado.
- Governança: `scripts/` geram checks, manifests e dossier anexável para janelas sérias de `staging`.

## Navegação Rápida

- Diagramas:
  - [Fluxo do Projeto](#diagram-project)
  - [Janela Séria de Staging](#diagram-staging-window)
  - [Investigação e Compliance (MVP)](#diagram-mvp-flows)
  - [Billing por Créditos (MVP)](#diagram-billing)
  - [Trilha de Auditoria (request_id)](#diagram-audit)
- Docs operacionais: [Índice de Documentação](./ontrackchain/docs/README.md)

<a id="diagram-project"></a>
## Diagrama de Fluxo do Projeto

```mermaid
flowchart LR
  user[Usuário/Admin] --> ui[Frontend Next.js]

  subgraph edge[Gateway - Edge]
    traefik[Traefik + ForwardAuth]
  end

  ui --> traefik

  subgraph identity[Identidade]
    keycloak[Keycloak (OIDC)]
  end

  traefik --> auth[auth-service]
  auth --> keycloak
  keycloak --> auth

  traefik --> public[public-api]
  traefik --> inv[investigation-api]
  traefik --> comp[compliance-api]
  traefik --> mon[monitoring-api]
  traefik --> rep[report-api]

  subgraph data[Dados]
    pg[(PostgreSQL + RLS)]
    redis[(Redis)]
  end

  auth --> pg
  public --> pg
  inv --> pg
  comp --> pg
  mon --> pg
  rep --> pg

  inv --> redis
  rep --> redis

  subgraph external[Integrações Externas]
    trm[AML-KYT Provider (TRM)]
    rpc[RPC Providers (primary + fallback)]
  end

  comp --> trm
  inv --> rpc
  comp --> rpc

  subgraph obs[Observabilidade]
    prom[Prometheus]
    am[Alertmanager]
  end

  inv --> prom
  mon --> prom
  comp --> prom
  rep --> prom
  prom --> am
  am --> mon
  mon --> ui

  subgraph governance[Governança e Evidências]
    scripts[scripts (preflights, homologation, staging window)]
    artifacts[(artifacts (checks, manifests, dossier))]
  end

  scripts --> artifacts
  scripts --> traefik
  scripts --> auth
  scripts --> comp
  scripts --> inv
  scripts --> mon
```

<a id="diagram-staging-window"></a>
## Diagrama de Fluxo — Janela Séria de Staging

```mermaid
flowchart TD
  start([Iniciar janela]) --> windowId[Definir window_id]
  windowId --> envExample[.env.staging.example]
  envExample --> envPrivate[Gerar .env.staging.private e preencher em canal seguro]
  envExample --> ownershipDoc[docs: staging-env-ownership.md]

  envExample --> coverage[check_staging_env_ownership_coverage.py]
  ownershipDoc --> coverage
  coverage --> checks1[artifacts: staging: checks: ownership-coverage-<window_id>.json]

  ownershipDoc --> handoff[check_staging_env_handoff.py]
  handoff --> checks2[artifacts: staging: checks: handoff-<window_id>.json]

  envPrivate --> placeholders[check_staging_env_placeholders.py]
  placeholders --> checks3[artifacts: staging: checks: placeholders-<window_id>.json]

  envExample --> packet[render_staging_window_packet.py]
  ownershipDoc --> packet
  packet --> windowPacket[artifacts: staging: window-packet-<window_id>.md]

  envPrivate --> preOidc[preflight_oidc_serious_env.py]
  preOidc --> checks4[artifacts: staging: checks: oidc-preflight-<window_id>.json]

  envPrivate --> preExt[preflight_external_integrations.py]
  preExt --> checks5[artifacts: staging: checks: external-preflight-<window_id>.json]

  envPrivate --> homolog[homologation_external_evidence.py (mode both)]
  homolog --> homologJson[artifacts: homologation: external_homologation_<mode>_<stamp>.json]
  homolog --> homologManifest[artifacts: homologation: external_homologation_<mode>_<stamp>.json.manifest.json]
  homolog --> checks6[artifacts: staging: checks: homologation-<window_id>.json]

  windowPacket --> dossier[build_staging_release_dossier.py]
  checks1 --> dossier
  checks2 --> dossier
  checks3 --> dossier
  homologJson --> dossier
  homologManifest --> dossier
  dossier --> dossierJson[artifacts: staging: dossiers: staging_release_dossier_<window_id>_<stamp>.json]
  dossier --> dossierManifest[artifacts: staging: dossiers: staging_release_dossier_<window_id>_<stamp>.json.manifest.json]

  dossierManifest --> done([Go-No-Go: status ok + manifests anexaveis])
```

<a id="diagram-mvp-flows"></a>
## Diagrama de Fluxo — Investigação e Compliance (MVP)

```mermaid
sequenceDiagram
  autonumber
  participant U as Usuário/Admin (UI)
  participant FE as Frontend (Next.js)
  participant GW as Gateway (Traefik + ForwardAuth)
  participant AUTH as auth-service
  participant INV as investigation-api
  participant COMP as compliance-api
  participant REP as report-api
  participant MON as monitoring-api
  participant PG as PostgreSQL (RLS)
  participant R as Redis/Queue
  participant RPC as RPC Provider (primary/fallback)
  participant TRM as AML-KYT Provider (TRM)

  U->>FE: Solicita fluxo (estimate)
  FE->>GW: Request autenticada (X-Request-Id)
  GW->>AUTH: Validação JWT + RBAC (+2FA quando exigido)
  AUTH->>PG: Leitura/escrita de sessão/2FA (RLS)
  AUTH-->>GW: Resultado authz

  alt Investigação (quote -> start)
    GW->>INV: POST /estimate
    INV->>PG: Persistir cotacao e auditoria (RLS)
    INV-->>FE: Cotacao + custo em creditos
    FE->>GW: POST /start (quote_id)
    GW->>INV: POST /start
    INV->>PG: Reservar créditos / registrar operação (RLS)
    INV->>R: Enfileirar job
    R-->>INV: Processar job
    INV->>RPC: Consultas on-chain (retry + fallback)
    INV->>PG: Persistir resultados + audit trail (RLS)
    INV-->>FE: Status + resultado
  end

  alt Compliance e Relatório
    GW->>COMP: POST /estimate
    COMP->>PG: Persistir cotacao + auditoria (RLS)
    COMP-->>FE: Cotacao
    FE->>GW: POST /start (quote_id)
    GW->>COMP: POST /start
    COMP->>TRM: Verificação AML-KYT (quando habilitado)
    COMP->>RPC: Evidências on-chain (quando aplicável)
    COMP->>PG: Persistir achados + auditoria (RLS)
    COMP-->>FE: report_id
    GW->>REP: GET /reports/{report_id}
    REP->>PG: Carregar metadados + trilha (RLS)
    REP-->>FE: Download (com audit)
  end

  opt Monitoramento (operação global)
    MON->>PG: Registrar incidentes/triagem (RLS quando aplicavel)
    MON-->>FE: UI /monitoring (filtros, ack, export auditado)
  end
```

<a id="diagram-billing"></a>
## Diagrama de Fluxo — Billing por Créditos (MVP)

```mermaid
sequenceDiagram
  autonumber
  participant U as Usuário/Admin (UI)
  participant FE as Frontend (Next.js)
  participant GW as Gateway (Traefik + ForwardAuth)
  participant S as Serviço Domínio (investigation/compliance/report)
  participant PG as PostgreSQL (RLS)
  participant AUD as audit_logs

  U->>FE: Solicita cotação (estimate)
  FE->>GW: POST /estimate (X-Org-Id + X-Request-Id)
  GW->>S: POST /estimate
  S->>PG: Registrar quote + custo (RLS)
  S->>AUD: audit(quote_created)
  S-->>FE: quote_id + custo

  U->>FE: Confirma execução (start)
  FE->>GW: POST /start (quote_id)
  GW->>S: POST /start
  S->>PG: Criar credit_hold (PRE_HOLD) e vincular a operacao (RLS)
  S->>AUD: audit(credit_hold_created)

  alt Execução bem-sucedida
    S->>PG: Atualizar hold -> CONFIRMED (debito efetivo)
    S->>AUD: audit(credit_hold_confirmed)
    S-->>FE: status=completed
  else Execução falhou/cancelada
    S->>PG: Atualizar hold -> REFUND (estorno)
    S->>AUD: audit(credit_hold_refunded)
    S-->>FE: status=failed
  end
```

```mermaid
stateDiagram-v2
  [*] --> PRE_HOLD
  PRE_HOLD --> CONFIRMED: sucesso
  PRE_HOLD --> REFUND: falha/cancelamento/timeout
  CONFIRMED --> [*]
  REFUND --> [*]
```

<a id="diagram-audit"></a>
## Diagrama de Fluxo — Trilha de Auditoria (request_id)

```mermaid
sequenceDiagram
  autonumber
  participant FE as Frontend (Next.js)
  participant GW as Gateway (Traefik + ForwardAuth)
  participant S as Serviço (public/investigation/compliance/monitoring/report)
  participant PG as PostgreSQL (RLS)
  participant AUD as audit_logs

  FE->>GW: Request HTTP com X-Request-Id + X-Org-Id
  GW->>S: Encaminha headers (correlation)
  S->>PG: Operação de negócio (RLS)
  S->>AUD: Insert audit_log (request_id, org_id, actor, action, resource, status)
  AUD->>PG: Persistência (append-only)
  S-->>FE: Response (inclui request_id quando aplicavel)
```

```mermaid
flowchart LR
  req[X-Request-Id] --> svc[Serviço]
  org[X-Org-Id] --> svc
  svc --> log[audit_logs]
  log --> query[audit (UI ADMIN)]
  log --> export[export CSV | JSON]
  export --> evidence[file_hash + trilha]
```

## Documentação

- [Índice de Documentação](./ontrackchain/docs/README.md)
- [Arquitetura](./ontrackchain/docs/architecture.md)
- [Contratos de API](./ontrackchain/docs/api-contracts.md)
- [Board de Prioridades do Projeto](./ontrackchain/docs/project-priority-board.md)
- [Plano de Execução para 90%](./ontrackchain/docs/project-execution-plan-to-90.md)
- [Plano Operacional Trimestral para 95%](./ontrackchain/docs/project-operational-plan-to-95.md)
- [Matriz Operacional de Execução para 95%](./ontrackchain/docs/project-operational-execution-board.md)
- [Gates de Release para Staging Sério](./ontrackchain/docs/project-release-gates.md)
- [Deploy e Staging](./ontrackchain/docs/deploy-and-staging.md)
- [Checklist Pré-Produção](./ontrackchain/docs/pre-production-checklist.md)
- [CI/CD e Release](./ontrackchain/docs/ci-cd-and-release.md)
- [Validação e Auditoria](./ontrackchain/docs/validation-and-audit.md)
- [Compliance e Controles de Segurança](./ontrackchain/docs/compliance-and-security-controls.md)
- [Readiness Regulatório](./ontrackchain/docs/regulatory-readiness.md)
- [Variáveis de Ambiente](./ontrackchain/docs/environment-variables.md)
- [ADRs](./ontrackchain/docs/adrs/README.md)
- [Migrations PostgreSQL](./ontrackchain/infra/postgres/migrations/README.md)

## Quick Start

### 1. Subir a stack

```bash
cd ontrackchain
docker compose up -d --build
```

### 2. Validar o scaffold

```bash
cd ontrackchain
python scripts/smoke_runtime.py
cd apps/frontend && npx playwright test tests/e2e/critical-path.spec.ts tests/e2e/compliance-flows.spec.ts
```

### 3. Endpoints locais

Os ports abaixo refletem o baseline atual do `.env.example`. Se o seu `.env` sobrescrever algum valor, use o port configurado localmente.

- App/Gateway: `http://localhost:8080`
- Dashboard Traefik: `http://localhost:8081`
- Prometheus: `http://localhost:9091`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3002`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Estrutura do Repositório

```text
ontrackchain/
├── apps/
│   ├── auth-service/
│   ├── public-api/
│   ├── investigation-api/
│   ├── compliance-api/
│   ├── monitoring-api/
│   ├── report-api/
│   └── frontend/
├── infra/
│   ├── postgres/
│   └── traefik/
├── packages/
│   ├── shared/
│   └── agents/
├── scripts/
│   ├── smoke_runtime.py
│   ├── backup_postgres.sh
│   └── restore_postgres.sh
├── docker-compose.yml
└── .env.example
```

## Fluxos Críticos Cobertos

- Investigação: estimate -> start -> queue/concurrency -> complete/fail
- Compliance: estimate -> start -> report -> download
- Monitoring: estimate -> start -> watchlist -> alert
- Billing: `PRE_HOLD -> CONFIRMED/REFUND`
- Auditoria: `request_id -> action -> resource -> report_id -> file_hash`
- Segurança: `legal_report` bloqueado antes de `2FA`
- Operação global: incidente de plataforma pode ser marcado como `acknowledged` sem alterar `firing|resolved`
- Operação global: backlog administrativo de incidentes pode ser exportado em `CSV|JSON` com trilha `operational_alerts_exported`

## Riscos Residuais Conhecidos

- O fluxo de autenticação ainda depende do scaffold dev em ambiente local, mas o 2FA de sessões JWT agora usa TOTP real no `auth-service`
- A observabilidade central cobre `investigation`, `monitoring`, `compliance` e `report`
- O roteamento ativo de alertas depende do token interno `Alertmanager -> monitoring-api`
- Ambientes com volume persistido precisam aplicar `0006_add_operational_alert_triage.sql` para habilitar a triagem manual
- Ambientes com volume persistido precisam aplicar `0007_add_operational_alert_cursor_index.sql` para paginação estável de incidentes globais
- O export administrativo auditado dos incidentes globais depende de contexto válido no proxy server-side do frontend
- Integrações AML/KYT e providers blockchain ainda são mockadas/parciais
- Bitcoin continua limitado a `3 hops` no MVP

## Próximo Passo Recomendado

Seguir para Fase 2 com foco em:

- endurecimento de compliance/regulatório
- evoluir políticas de alerting, deduplicação e escalonamento
- evolução de UI de auditoria e operação
- integrações reais de dados e scoring
