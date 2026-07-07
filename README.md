# Ontrackchain

![Ontrackchain](./ontrackchain/docs/assets/logo.jpeg)

Plataforma de investigacao e compliance on-chain com foco em trilha auditavel, fila operacional multiusuario, screening local de sancoes e governanca de release para ambientes serios.

## O Que Este Repositorio Contem

Este repositorio e dividido em dois niveis:

- a raiz concentra onboarding, atalhos operacionais e delegacao de `Makefile`
- a aplicacao principal vive em [`./ontrackchain`](./ontrackchain/README.md)
- a documentacao canonica do produto vive em [`./ontrackchain/docs`](./ontrackchain/docs/README.md)

## Estado Atual

- baseline oficial atual:
  - `91%` de construcao tecnica
  - `78%` de prontidao regulatoria/operacional
  - `87%` de maturidade consolidada
- stack local executavel com `docker compose`:
  - `Traefik`
  - `FastAPI`
  - `Next.js 14`
  - `PostgreSQL`
  - `Redis`
  - `Prometheus`
  - `Alertmanager`
  - `Grafana`
  - `Keycloak` no profile `oidc`
- modulos principais ativos:
  - `auth-service`
  - `public-api`
  - `investigation-api`
  - `compliance-api`
  - `monitoring-api`
  - `report-api`
  - `frontend`
- capacidades ja institucionalizadas:
  - `audit_logs`
  - `evidence_trail` append-only
  - `regulatory_work_items` com timeline e comentarios
  - `preventive_blocks`
  - `counterparties`
  - `ros_records`
  - cockpits operacionais tri-locale no frontend
  - `monitoring` decomposto em hooks, loaders e paineis dedicados

## Politica de Documentacao

- este README da raiz existe para onboarding, visao executiva e navegacao
- [`ontrackchain/README.md`](./ontrackchain/README.md) e a porta de entrada tecnica da aplicacao
- [`ontrackchain/docs/README.md`](./ontrackchain/docs/README.md) e o indice canonico da documentacao
- [Governanca Semanal](./ontrackchain/docs/governance-weekly/README.md) guarda artefatos datados, sign-offs, war room e historico operacional
- documentos paralelos fora dessa trilha devem ser consolidados ou removidos para evitar drift

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

### 2. Validar o baseline local

```bash
cd ontrackchain
python scripts/smoke_runtime.py
make apply-regulatory-work-items-migration
make smoke-work-items-ownership-backend

cd apps/frontend
npm ci
npm run typecheck
npm run test:e2e:stack-real-light
npm run test:e2e:browser-mocked
```

Comandos adicionais de frontend:

- `npm run test:e2e:dev-auth`: usar apenas quando o scaffold local estiver em `AUTH_MODE=dev`
- `npm run test:e2e:oidc-critical`: usar quando o runtime real estiver em `AUTH_MODE=oidc` e o provedor federado estiver pronto
- `npm run test:e2e:ssr-mocked`: usar para suites que dependem de backend SSR mockado

### 3. Validar integracoes externas e readiness serio

```bash
cd ontrackchain
python scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
make run-oidc-readiness-bundle-local WINDOW_ID=stg-$(date +%F)-oidc BASE_URL=http://localhost:8080
make run-regulatory-readiness-bundle-local \
  WINDOW_ID=stg-$(date +%F)-reg \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
```

## Mapa Canonico

- [README Tecnico da Aplicacao](./ontrackchain/README.md)
- [Indice de Documentacao](./ontrackchain/docs/README.md)
- [Arquitetura](./ontrackchain/docs/architecture.md)
- [Contratos de API](./ontrackchain/docs/api-contracts.md)
- [Cobertura do frontend](./ontrackchain/docs/frontend-coverage-matrix.md)
- [Operacao local](./ontrackchain/docs/operations.md)
- [Deploy e staging](./ontrackchain/docs/deploy-and-staging.md)
- [Validacao e auditoria](./ontrackchain/docs/validation-and-audit.md)
- [Readiness Regulatorio](./ontrackchain/docs/regulatory-readiness.md)
- [Gates de release](./ontrackchain/docs/project-release-gates.md)
- [ADRs](./ontrackchain/docs/adrs/README.md)

## Janela Seria

Atalhos principais pela raiz:

```bash
make help-serious-window
make prepare-serious-window-dispatch WINDOW_ID=stg-2026-07-06-a
make render-serious-window-dispatch-packet WINDOW_ID=stg-2026-07-06-a
make run-serious-window-local WINDOW_ID=stg-2026-07-06-a MODE=baseline
make postprocess-serious-window RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Situacao executiva atual:

- `P0-01`: homologacao OIDC + MFA federado ainda depende de evidencia real recorrente
- `P0-02`: provider `AML/KYT live` pronto para validacao com credencial real
- `P0-03`: feed `EU_CONSOLIDATED` pronto para fechar com URL tokenizada real
- janela `stg-2026-07-06-a`: segue `no-go` ate preencher handoff, ownership e secrets reais

## Estrutura do Repositorio

```text
Ontrackchain/
├── .github/
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

## Riscos Residuais

- integracoes externas serias ainda dependem de credenciais e URLs reais
- `due_diligence` e `source_of_funds` seguem intencionalmente em fluxo manual
- `legal_report`, `ROS/COAF` e `block lift` exigem MFA forte homologado
- retention/recovery e sign-off institucional ainda precisam de aceite recorrente

## Proximo Passo Recomendado

As quatro frentes que mais movem a prontidao real do projeto sao:

1. homologar `OIDC` + MFA federado serio
2. fechar `AML/KYT live` com evidencia anexavel
3. ativar feed UE real para `EU_CONSOLIDATED`
4. executar uma janela seria completa com owners, handoff e sign-off formal
