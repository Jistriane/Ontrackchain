# Ontrackchain

![Ontrackchain](./ontrackchain/docs/assets/logo.jpeg)

Plataforma multi-tenant de investigacao e compliance on-chain com foco em trilha auditavel, billing por creditos, screening local de sancoes e enforcement forte em fluxos regulatorios sensiveis.

## Visao Geral

Este repositorio tem dois papeis:

- a raiz concentra onboarding, workflows e atalhos operacionais via `Makefile`
- a aplicacao vive em [`./ontrackchain`](./ontrackchain/README.md), com servicos, docs, infra, scripts e testes

Hoje o projeto ja opera como plataforma funcional, mas ainda nao concluiu toda a prontidao regulatoria/operacional para uma janela seria com prova real de ponta a ponta.

## Navegacao Rapida

- [Ontrackchain](#ontrackchain)
  - [Visao Geral](#visao-geral)
  - [Navegacao Rapida](#navegacao-rapida)
  - [Estado Atual](#estado-atual)
  - [Scorecard Oficial](#scorecard-oficial)
  - [Bloqueadores Atuais](#bloqueadores-atuais)
  - [Arquitetura em 60 Segundos](#arquitetura-em-60-segundos)
  - [Servicos Principais](#servicos-principais)
  - [Fluxos Canonicos](#fluxos-canonicos)
    - [Fluxo de Autenticacao OIDC e MFA](#fluxo-de-autenticacao-oidc-e-mfa)
    - [Fluxo de Investigacao e Billing](#fluxo-de-investigacao-e-billing)
    - [Fluxo de Screening, Bloqueio e ROS](#fluxo-de-screening-bloqueio-e-ros)
    - [Modelo do Core Regulatorio](#modelo-do-core-regulatorio)
    - [Fluxo ROS e COAF](#fluxo-ros-e-coaf)
    - [Fluxo de Block Lift e Manual Review](#fluxo-de-block-lift-e-manual-review)
    - [Fluxo de Operacao Global](#fluxo-de-operacao-global)
    - [Fluxo da Janela Seria](#fluxo-da-janela-seria)
    - [Fluxo Detalhado da Janela Seria](#fluxo-detalhado-da-janela-seria)
    - [Fluxo de CI/CD e Promocao](#fluxo-de-cicd-e-promocao)
  - [Validacao e Qualidade](#validacao-e-qualidade)
  - [Operacao da Janela Seria](#operacao-da-janela-seria)
  - [Quick Start](#quick-start)
    - [1. Subir a stack local](#1-subir-a-stack-local)
    - [2. Validar runtime e UI](#2-validar-runtime-e-ui)
    - [3. Endpoints locais padrao](#3-endpoints-locais-padrao)
    - [4. Rotas locais principais do frontend](#4-rotas-locais-principais-do-frontend)
    - [5. Atalhos operacionais localhost atualizados](#5-atalhos-operacionais-localhost-atualizados)
  - [Navegacao Canonica](#navegacao-canonica)
  - [Estrutura do Repositorio](#estrutura-do-repositorio)
  - [Riscos Residuais Conhecidos](#riscos-residuais-conhecidos)
  - [Proximo Passo Recomendado](#proximo-passo-recomendado)

## Estado Atual

- scorecard oficial atual:
  - `91%` de construcao tecnica
  - `78%` de prontidao regulatoria/operacional
  - `87%` de construcao total consolidada
- stack executavel com `docker compose`:
  - `Traefik`
  - `FastAPI`
  - `Next.js 14`
  - `PostgreSQL`
  - `Redis`
  - `Prometheus`
  - `Alertmanager`
  - `Grafana`
  - `Keycloak` no profile `oidc`
- runtime segmentado por dominio:
  - `auth-service`
  - `public-api`
  - `investigation-api`
  - `investigation-worker`
  - `compliance-api`
  - `compliance-worker`
  - `monitoring-api`
  - `report-api`
  - `frontend`
- trilha operacional e regulatoria implementada:
  - `audit_logs`
  - `evidence_trail` append-only com encadeamento `SHA-256`
  - `regulatory_work_items` + `regulatory_work_events` + `regulatory_work_comments`
  - `preventive_blocks`
  - `counterparties` + `counterparty_history`
  - `sanctions_lists_meta` + `sanctions_hits_cache`
  - `ros_records`
- camada operacional compartilhada ja conectada ao frontend:
  - `sanctions` usa backend como fonte primaria da fila operacional, com fallback local
  - `alerts` rastreia incidentes em `work-items` e sincroniza encerramento via `ack`
- observabilidade operacional madura:
  - backlog global em `/monitoring`
  - ack em lote
  - filtros dinamicos
  - export auditado em `CSV|JSON`
- janela seria de staging consolidada com:
  - `prepare_staging_window.py`
  - `run_staging_window.py`
  - `run_regulatory_readiness_bundle.py`
  - war room
  - live tracking
  - sign-off
  - dossier anexavel

## Scorecard Oficial

| Lente | Leitura Atual | Fonte Canonica |
| --- | ---: | --- |
| Construcao tecnica | `91%` | [`project-kpi-scorecard.md`](./ontrackchain/docs/project-kpi-scorecard.md) |
| Prontidao regulatoria/operacional | `78%` | [`project-kpi-scorecard.md`](./ontrackchain/docs/project-kpi-scorecard.md) |
| Total consolidado | `87%` | [`project-kpi-scorecard.md`](./ontrackchain/docs/project-kpi-scorecard.md) |

Leitura mais honesta do momento:

- o produto esta majoritariamente construido
- o principal gargalo atual nao e mais ausencia de codigo
- o gap residual esta concentrado em homologacao externa, credenciais reais, URL tokenizada da UE, MFA federado serio e sign-off institucional recorrente

## Bloqueadores Atuais

| Iniciativa | Estado | O que falta para fechar |
| --- | --- | --- |
| `P0-01` OIDC + MFA federado serio | `blocked` | homologacao formal recorrente e trilho serio com evidencia real |
| `P0-02` `AML/KYT live` | `ready` | credencial real, gate de runtime verde e evidencia anexavel da janela |
| `P0-03` feed UE `EU_CONSOLIDATED` | `ready` | `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada e JSONs persistidos |
| Janela `stg-2026-07-06-a` | `no-go` | owners online, handoff, placeholders e secrets reais no `.env.staging.private` |

## Arquitetura em 60 Segundos

- edge: `Traefik + ForwardAuth` concentram roteamento, middleware e contexto autenticado
- identidade: `auth-service` suporta `dev` e `oidc`; `Keycloak` entra no profile `oidc`
- investigacao: `investigation-api` e `investigation-worker` fazem `estimate -> start -> queue -> result` com retry/backoff e metadados do provider RPC
- compliance: `compliance-api` expone `kyc-wallet`, `sanctions-check`, `preventive blocks` e `counterparties`; `compliance-worker` sincroniza OFAC, UN, EU e deadlines de ROS
- operacoes: `compliance-api` tambem expõe `work-items` multiusuario por modulo para fila compartilhada, timeline e handoff operacional
- reports: `report-api` gera relatorios deterministas e implementa o fluxo `ROS/COAF`
- monitoring: `monitoring-api` recebe webhooks do `Alertmanager` e alimenta o backlog global operacional
- dados: `PostgreSQL` usa `RLS`; `Redis` suporta fila/cache; migrations versionam o core regulatorio e a fila compartilhada
- governanca: scripts de preflight, homologacao, packet, dossier e postprocess sustentam o rito da janela seria

```mermaid
flowchart LR
  user[Usuario Admin] --> frontend[Frontend Next.js]
  frontend --> traefik[Traefik ForwardAuth]

  traefik --> auth[auth-service]
  traefik --> public[public-api]
  traefik --> inv[investigation-api]
  traefik --> comp[compliance-api]
  traefik --> mon[monitoring-api]
  traefik --> rep[report-api]

  keycloak[Keycloak OIDC profile] --> auth
  auth --> keycloak

  invw[investigation-worker] --> inv
  compw[compliance-worker] --> comp

  pg[(PostgreSQL RLS)]
  redis[(Redis)]

  auth --> pg
  public --> pg
  inv --> pg
  inv --> redis
  invw --> pg
  invw --> redis
  comp --> pg
  compw --> pg
  mon --> pg
  mon --> redis
  rep --> pg
  work[(regulatory_work_items)]
  comp --> work
  frontend --> work

  rpc[RPC primary fallback] --> inv
  trm[AML KYT provider] --> comp
  feeds[OFAC UN EU OpenSanctions] --> compw

  prom[Prometheus] --> am[Alertmanager]
  inv --> prom
  comp --> prom
  mon --> prom
  rep --> prom
  am --> mon

  scripts[scripts staging compliance readiness] --> artifacts[artifacts checks dossiers homologation]
```

## Servicos Principais

| Componente | Responsabilidade |
| --- | --- |
| `auth-service` | `JWT`, `OIDC`, `2FA`, RBAC e headers de contexto |
| `public-api` | superficie publica e catalogos expostos pelo gateway |
| `investigation-api` | `estimate`, `start`, `status`, billing e metadados RPC |
| `investigation-worker` | fila real, retry/backoff, concorrencia e processamento assincrono |
| `compliance-api` | `kyc-wallet`, `sanctions-check`, `preventive blocks` e `counterparties` |
| `operations` via `compliance-api` | fila compartilhada por modulo, status, comentarios e timeline de handoff |
| `compliance-worker` | sync de listas, override de `source_url`, deadlines de ROS e readiness regulatorio |
| `monitoring-api` | webhooks do `Alertmanager`, backlog global e exports auditados |
| `report-api` | downloads fortes, relatorios deterministas e fluxo `ROS/COAF` |
| `frontend` | UI operacional, `/audit`, `/monitoring`, dashboard e callbacks OIDC |

## Fluxos Canonicos

### Fluxo de Autenticacao OIDC e MFA

```mermaid
sequenceDiagram
  autonumber
  participant U as Usuario/Admin
  participant FE as Frontend
  participant GW as Gateway
  participant AUTH as auth-service
  participant KC as Keycloak
  participant PG as PostgreSQL

  U->>FE: Acessa area protegida
  FE->>GW: Request sem sessao valida
  GW->>AUTH: Verifica contexto autenticado
  AUTH-->>FE: Exige login OIDC

  FE->>KC: Redirect para autenticacao
  KC-->>FE: Callback com code/token
  FE->>AUTH: Troca code por sessao
  AUTH->>KC: Valida issuer, audience e claims
  AUTH->>PG: Persiste sessao, org_id, plano e papel
  AUTH-->>FE: JWT/sessao autenticada

  FE->>GW: Nova request autenticada
  GW->>AUTH: Verifica JWT, RBAC e requisito de 2FA

  alt Fluxo comum
    AUTH-->>GW: Acesso permitido
    GW-->>FE: Request segue para API alvo
  else Fluxo sensivel
    AUTH->>PG: Verifica TOTP ou MFA federado homologado
    alt MFA valido
      AUTH-->>GW: Acesso permitido
      GW-->>FE: Request segue para API alvo
    else MFA ausente ou invalido
      AUTH-->>FE: Bloqueia operacao sensivel
    end
  end
```

### Fluxo de Investigacao e Billing

```mermaid
sequenceDiagram
  autonumber
  participant U as Usuario/Admin
  participant FE as Frontend
  participant GW as Gateway
  participant INV as investigation-api
  participant W as investigation-worker
  participant PG as PostgreSQL
  participant R as Redis
  participant RPC as RPC primary/fallback

  U->>FE: Solicita estimate
  FE->>GW: POST /estimate
  GW->>INV: Encaminha request autenticada
  INV->>PG: Persiste quote e auditoria
  INV-->>FE: quote_id + custo

  U->>FE: Confirma start
  FE->>GW: POST /start (quote_id)
  GW->>INV: Encaminha request
  INV->>PG: Cria PRE_HOLD e operacao
  INV->>R: Enfileira job
  R-->>W: Entrega workload
  W->>RPC: Consulta on-chain com retry/fallback
  W->>PG: Persiste resultado + status final

  alt Execucao bem-sucedida
    W->>PG: Confirma hold
    W-->>FE: Resultado completo
  else Falha ou cancelamento
    W->>PG: Reverte/refunda hold
    W-->>FE: Status failed/refund
  end
```

### Fluxo de Screening, Bloqueio e ROS

```mermaid
flowchart TD
  feeds[Feeds OFAC UN EU OpenSanctions] --> worker[compliance-worker]
  worker --> meta[sanctions_lists_meta]
  worker --> cache[sanctions_hits_cache]

  user[Usuario ou operador] --> api[compliance-api]
  api --> check[GET sanctions-check]
  check --> cache
  cache --> decision{Hit ou risco relevante?}

  decision -- Nao --> audit[audit_logs]
  decision -- Sim --> block[preventive_blocks]
  block --> evidence[evidence_trail]
  block --> rosDecision{Caso exige ROS/COAF?}
  rosDecision -- Sim --> ros[ros_records]
  ros --> report[report-api]
  rosDecision -- Nao --> report
  report --> audit
  evidence --> audit
```

### Modelo do Core Regulatorio

```mermaid
flowchart TD
  subgraph Intake[Onboarding e screening]
    cp[counterparties]
    hist[counterparty_history]
    cache[sanctions_hits_cache]
    meta[sanctions_lists_meta]
  end

  subgraph Controls[Controles regulatorios]
    block[preventive_blocks]
    ros[ros_records]
  end

  subgraph Evidence[Evidencia e auditoria]
    ev[evidence_trail]
    audit[audit_logs]
    reports[report-api / reports]
  end

  meta --> cache
  cp --> hist
  cp --> cache
  cache --> block
  cache --> ros
  block --> ev
  ros --> ev
  ros --> reports
  block --> audit
  ros --> audit
  ev --> audit
```

### Fluxo ROS e COAF

```mermaid
sequenceDiagram
  autonumber
  participant OP as Operador/Admin
  participant API as compliance-api
  participant PG as PostgreSQL
  participant EV as evidence_trail
  participant REP as report-api
  participant AUD as audit_logs

  OP->>API: Avalia contraparte ou caso sensivel
  API->>PG: Consulta counterparties, hits e bloqueios
  API->>PG: Decide gerar ROS/COAF
  API->>PG: Cria ros_records com status inicial
  API->>EV: Registra coaf_report_generated
  API->>REP: Gera artefato do relatorio
  REP-->>API: report_id + file_hash
  API->>AUD: Audita geracao do ROS

  alt Caso aprovado
    OP->>API: Aprova ROS
    API->>PG: Atualiza ros_records para approved
    API->>EV: Registra coaf_report_approved
    API->>AUD: Audita aprovacao
  else Caso rejeitado
    OP->>API: Rejeita ROS com motivo
    API->>PG: Atualiza ros_records para rejected
    API->>EV: Registra coaf_report_rejected
    API->>AUD: Audita rejeicao
  end

  opt Submissao manual ao COAF
    OP->>API: Informa protocolo e recibo
    API->>PG: Atualiza ros_records para submitted_manual
    API->>EV: Registra coaf_report_submitted_manual
    API->>AUD: Audita protocolo e recibo
  end
```

### Fluxo de Block Lift e Manual Review

```mermaid
flowchart TD
  start[Operador solicita acao sensivel] --> kind{Tipo de operacao}

  kind -->|block lift| lift[POST compliance blocks slash block_id slash lift]
  kind -->|due_diligence ou source_of_funds| manual[manual_review_required]
  kind -->|legal_report ou ROS/COAF| sensitive[MFA forte obrigatorio]

  manual --> queue[Fila e rito manual]
  queue --> auditManual[audit_logs]

  lift --> auth[Validar usuario vinculado]
  auth --> mfa{X-MFA-Mode external_provider e provider homologado?}
  mfa -- Nao --> deny[403 external_provider_mfa_required]
  mfa -- Sim --> liftOk[Atualiza preventive_blocks]
  liftOk --> ev[Registra preventive_block_lifted]
  ev --> audit[audit_logs]

  sensitive --> mfa2{MFA homologado disponivel?}
  mfa2 -- Nao --> deny2[403 provider_mfa_required]
  mfa2 -- Sim --> execute[Permite fluxo sensivel]
  execute --> audit
```

### Fluxo de Operacao Global

```mermaid
flowchart LR
  prom[Prometheus] --> am[Alertmanager]
  am --> mon[monitoring-api]
  mon --> pg[(PostgreSQL)]
  mon --> ui[UI /monitoring]

  ui --> filters[Filtros dinamicos]
  ui --> ack[Ack individual/em lote]
  ui --> export[Export CSV/JSON]

  ack --> audit[audit_logs]
  export --> audit
  filters --> pg
```

### Fluxo da Janela Seria

```mermaid
flowchart TD
  start[Definir window_id] --> gate[Gate agregado da janela]
  gate --> ownership[Ownership handoff placeholders]
  ownership --> env[.env.staging.private com dados reais]
  env --> preflight[prepare validate preflight]
  preflight --> bundle[regulatory readiness bundle quando aplicavel]
  bundle --> run{Execucao local ou GitHub Actions?}
  run --> dossier[dossier checks homologation]
  dossier --> signoff[sign-off weekly governance]
  signoff --> decision[go no-go com evidencia anexavel]
```

### Fluxo Detalhado da Janela Seria

```mermaid
flowchart TD
  start[Definir window_id] --> sheet[Manual fill sheet]
  sheet --> owners[Ownership e handoff]
  owners --> env[.env.staging.private]

  env --> prepare[prepare_staging_window.py]
  prepare --> packet[window packet]
  prepare --> checks[artifacts slash staging slash checks]

  checks --> validate{validate e preflight ok?}
  validate -- Nao --> warroom[war room e live tracking]
  warroom --> rerun[rerodar prepare validate preflight]
  rerun --> validate

  validate -- Sim --> bundle[run_regulatory_readiness_bundle.py quando aplicavel]
  bundle --> homolog[artifacts slash homologation]
  bundle --> dossier[build_staging_release_dossier.py]

  dossier --> run{run_staging_window local ou GitHub Actions}
  run --> signoff[sign-off draft]
  signoff --> weekly[weekly governance]
  weekly --> decision{go ou no-go}

  decision -- no-go --> warroom
  decision -- go --> archive[dossier e evidencias anexadas]
```

### Fluxo de CI/CD e Promocao

```mermaid
flowchart TD
  dev[Push ou PR] --> qg[quality-gates.yml]
  qg --> unit[Checks por app]
  qg --> contracts[Lint typecheck validacoes]

  dev --> e2e[e2e-tests.yml]
  e2e --> auth[Playwright dev-auth e oidc-critical]
  e2e --> critical[Critical path e compliance flows]

  unit --> gate{Pipeline verde?}
  contracts --> gate
  auth --> gate
  critical --> gate

  gate -- Nao --> fix[Corrigir codigo ou config]
  fix --> dev

  gate -- Sim --> prep[prepare-serious-window-dispatch]
  prep --> serious[staging-serious-window.yml ou run_staging_window.py]
  serious --> artifacts[checks homologation dossier sign-off draft]
  artifacts --> review[war room e weekly governance]
  review --> promote{go ou no-go}
  promote -- no-go --> prep
  promote -- go --> main[Promocao controlada e evidencia anexada]
```

## Validacao e Qualidade

O baseline atual de validacao combina:

- `scripts/smoke_runtime.py` para fluxos core, `plan lock`, hashes e auditoria
- `Playwright` para `critical-path`, `compliance-flows`, `oidc-critical` e `dev-auth`
- testes focados de preflight, dossier, packet, postprocess, sanctions sync, provider runtime e readiness bundle
- quality gates por app em [`.github/workflows/quality-gates.yml`](./.github/workflows/quality-gates.yml)
- workflow dedicado da janela seria em [`.github/workflows/staging-serious-window.yml`](./.github/workflows/staging-serious-window.yml)

Comandos recomendados:

```bash
cd ontrackchain
python scripts/smoke_runtime.py

docker compose exec -T postgres psql -U ontrackchain -d ontrackchain \
  < infra/postgres/migrations/0013_regulatory_work_items.sql

cd apps/frontend
npm ci
npm run typecheck
npm run test:e2e:oidc-critical
npm run test:e2e
```

## Operacao da Janela Seria

Atalhos principais pela raiz:

```bash
make help-serious-window
make prepare-serious-window-dispatch WINDOW_ID=stg-2026-07-06-a
make render-serious-window-dispatch-packet WINDOW_ID=stg-2026-07-06-a
make postprocess-serious-window-dry-run RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
make postprocess-serious-window RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Atalhos adicionais relevantes:

```bash
make run-serious-window-local WINDOW_ID=stg-2026-07-06-a MODE=baseline
make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080
make run-eu-sanctions-window-local WINDOW_ID=stg-2026-07-06-a
make run-regulatory-readiness-bundle WINDOW_ID=stg-2026-07-06-a
```

O workflow serio no GitHub Actions:

- materializa `.env.staging.private` a partir de secret do environment
- executa `prepare_staging_window.py --run`
- publica resumo do payload
- renderiza draft de sign-off
- sobe `ci-artifacts`, `artifacts/staging/*` e `artifacts/homologation`

Estado operacional atual da janela canônica:

- `window_id`: `stg-2026-07-06-a`
- status: `no-go`
- motivo principal: handoff humano e placeholders ainda nao preenchidos com dados reais
- artefatos vivos: war room, live tracking, manual fill sheet e sign-off versionado em `docs/governance-weekly/`

## Quick Start

### 1. Subir a stack local

```bash
cd ontrackchain
cp .env.example .env
docker compose up -d --build
```

Para exercitar OIDC localmente:

```bash
cd ontrackchain
docker compose --profile oidc up -d --build
```

### 2. Validar runtime e UI

```bash
cd ontrackchain
python scripts/smoke_runtime.py

cd apps/frontend
npm ci
npm run test:e2e:dev-auth
```

### 3. Endpoints locais padrao

Os ports abaixo refletem `ontrackchain/.env.example`.

- app gateway: `http://localhost:8080`
- dashboard do Traefik: `http://localhost:8081`
- Keycloak OIDC publico: `http://auth.localhost:8080`
- Keycloak profile `oidc` admin/debug: `http://localhost:8088`
- Prometheus: `http://localhost:9091`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3002`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 4. Rotas locais principais do frontend

Todas as rotas abaixo passam pelo gateway local em `http://localhost:8080`.

- landing/app shell: `http://localhost:8080/`
- dashboard operacional: `http://localhost:8080/dashboard`
- investigação: `http://localhost:8080/investigate`
- monitoramento: `http://localhost:8080/monitoring`
- auditoria: `http://localhost:8080/audit`
- trilha de evidências: `http://localhost:8080/evidence`
- central de alertas: `http://localhost:8080/alerts`
- fila compartilhada conectada em alertas: `http://localhost:8080/alerts?status=firing&triage_status=pending`
- reports formais: `http://localhost:8080/reports`
- contrapartes: `http://localhost:8080/counterparties`
- sanções: `http://localhost:8080/sanctions`
- fila compartilhada conectada em sanções: `http://localhost:8080/sanctions?address=<address>&chain=<chain>&case_id=<case_id>&autostart=1`
- bloqueios preventivos: `http://localhost:8080/blocks`
- ROS/COAF: `http://localhost:8080/ros-coaf`
- billing: `http://localhost:8080/billing`
- team management local-first: `http://localhost:8080/team`

### 5. Atalhos operacionais localhost atualizados

- alertas pendentes: `http://localhost:8080/alerts?status=firing&triage_status=pending`
- billing com usuários convidados: `http://localhost:8080/team?filter_status=invited`
- reports com caso pré-selecionado: `http://localhost:8080/reports?case_id=<case_id>`
- sanctions com autostart: `http://localhost:8080/sanctions?address=<address>&chain=<chain>&case_id=<case_id>&autostart=1`
- blocks com autostart: `http://localhost:8080/blocks?address=<address>&chain=<chain>&case_id=<case_id>&autostart=1`
- audit filtrado por caso: `http://localhost:8080/audit?resource_type=case&resource_id=<case_id>&request_id=<case_id>`
- evidence filtrado por caso: `http://localhost:8080/evidence?domain=all&resource_type=case&resource_id=<case_id>&request_id=<case_id>`

## Navegacao Canonica

- [README interno da aplicacao](./ontrackchain/README.md)
- [Indice de documentacao](./ontrackchain/docs/README.md)
- [Arquitetura](./ontrackchain/docs/architecture.md)
- [Contratos de API](./ontrackchain/docs/api-contracts.md)
- [Cobertura do Frontend](./ontrackchain/docs/frontend-coverage-matrix.md)
- [Deploy e Staging](./ontrackchain/docs/deploy-and-staging.md)
- [Gates de Release para Staging Serio](./ontrackchain/docs/project-release-gates.md)
- [Validacao e Auditoria](./ontrackchain/docs/validation-and-audit.md)
- [Scorecard Oficial do Projeto](./ontrackchain/docs/project-kpi-scorecard.md)
- [Readiness Regulatorio](./ontrackchain/docs/regulatory-readiness.md)
- [ADRs](./ontrackchain/docs/adrs/README.md)
- [Migrations PostgreSQL](./ontrackchain/infra/postgres/migrations/README.md)

## Estrutura do Repositorio

```text
Ontrackchain/
├── .github/
│   └── workflows/
├── Makefile
├── README.md
└── ontrackchain/
    ├── apps/
    │   ├── auth-service/
    │   ├── public-api/
    │   ├── investigation-api/
    │   ├── compliance-api/
    │   ├── monitoring-api/
    │   ├── report-api/
    │   └── frontend/
    ├── docs/
    ├── infra/
    ├── packages/
    ├── scripts/
    ├── tests/
    ├── docker-compose.yml
    ├── Makefile
    ├── .env.example
    └── README.md
```

## Riscos Residuais Conhecidos

- `AML/KYT` live ainda depende de credenciais reais e homologacao recorrente
- `due_diligence` e `source_of_funds` seguem intencionalmente em `manual_review_required`
- o feed `EU_CONSOLIDATED` ainda depende de URL tokenizada real para fechar prova operacional seria
- `legal_report`, `ROS/COAF` e `block lift` exigem MFA serio homologado para janela forte
- retention/recovery, owners e sign-off ainda precisam de aceite institucional recorrente
- a janela `stg-2026-07-06-a` continua `no-go` ate o preenchimento humano dos placeholders e handoffs

## Proximo Passo Recomendado

Focar nas iniciativas que mais movem o scorecard e destravam a janela seria:

- fechar `P0-02` com provider `AML/KYT live` real
- fechar `P0-03` com feed UE tokenizado e bundle anexado
- avancar `P0-01` com MFA/OIDC federado serio homologado
- executar a primeira janela seria completa com owners online, artefatos reais e sign-off formal
