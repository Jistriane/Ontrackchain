# Ontrackchain

![Ontrackchain](./docs/assets/logo.jpeg)

Aplicacao principal do projeto Ontrackchain: servicos FastAPI por dominio, frontend `Next.js 14`, infraestrutura local com `docker compose`, scripts de readiness e documentacao canonica do produto.

## Escopo Deste Diretorio

Aqui vivem:

- servicos de negocio e APIs
- frontend operacional
- infraestrutura local e observabilidade
- migrations do banco
- scripts de validacao, bundles e janela seria
- testes automatizados
- ADRs e documentacao canonica

## Estado Atual

- baseline oficial:
  - `91%` de construcao tecnica
  - `78%` de prontidao regulatoria/operacional
  - `87%` de maturidade consolidada
- stack local suportada:
  - `Traefik`
  - `FastAPI`
  - `Next.js 14`
  - `PostgreSQL`
  - `Redis`
  - `Prometheus`
  - `Alertmanager`
  - `Grafana`
  - `Keycloak` no profile `oidc`
- capacidades ja conectadas ponta a ponta:
  - investigacao com `quote -> start -> worker -> result`
  - screening local de sancoes
  - `preventive_blocks`
  - `counterparties`
  - `ROS/COAF`
  - `audit_logs`
  - `evidence_trail`
  - `regulatory_work_items`
  - cockpit `/monitoring` modularizado
  - frontend tri-locale com labels institucionais e helpers compartilhados

## Servicos e Dominios

| Componente | Papel principal |
| --- | --- |
| `auth-service` | autenticacao `dev` e `oidc`, `2FA`, RBAC e contexto de sessao |
| `public-api` | superficie publica e catalogos expostos pelo gateway |
| `investigation-api` | `estimate`, `start`, `status`, billing e metadados RPC |
| `investigation-worker` | fila, retry/backoff e processamento assincrono |
| `compliance-api` | sanctions, counterparties, blocks, work-items e controles regulatorios |
| `compliance-worker` | sync de listas, readiness regulatorio e checks de provider |
| `monitoring-api` | webhooks do `Alertmanager`, triagem e export operacional |
| `report-api` | relatorios deterministas, download sensivel e fluxo `ROS/COAF` |
| `frontend` | cockpits operacionais, audit, monitoring, evidence, reports e callbacks OIDC |

## Frontend Operacional

O frontend em `apps/frontend` hoje segue quatro linhas estruturais importantes:

- tri-locale obrigatorio (`pt-BR`, `en`, `es`)
- labels institucionais `Label Amigavel (codigo_tecnico)` nos cockpits operacionais
- contratos compartilhados em `app/lib/`
- decomposicao progressiva dos cockpits densos, com `monitoring` ja fatiado em hooks, loaders e paineis dedicados

Classes de suite Playwright atualmente institucionalizadas:

| Classe | Uso | Comando canonico |
| --- | --- | --- |
| `stack real leve` | smoke SSR local | `npm run test:e2e:stack-real-light` |
| `browser-mocked` | mocks por `page.route(...)` com frontend local | `npm run test:e2e:browser-mocked` |
| `ssr-mocked` | backend SSR mockado + frontend local | `npm run test:e2e:ssr-mocked` |
| `dev-auth` | regressao local com `AUTH_MODE=dev` | `npm run test:e2e:dev-auth` |
| `stack real / oidc-critical` | validacao seria OIDC e fluxo real | `npm run test:e2e:oidc-critical` |

## Quick Start

### 1. Subir o ambiente local

```bash
cp .env.example .env
docker compose up -d --build
```

Para exercitar OIDC localmente:

```bash
docker compose --profile oidc up -d --build
```

### 2. Validar runtime, banco e frontend

```bash
python scripts/smoke_runtime.py
make apply-regulatory-work-items-migration
make smoke-work-items-ownership-backend

cd apps/frontend
npm ci
npm run typecheck
npm run test:e2e:stack-real-light
npm run test:e2e:browser-mocked
```

Observacoes:

- use `npm run test:e2e:dev-auth` apenas quando o scaffold local estiver em `AUTH_MODE=dev`
- use `npm run test:e2e:oidc-critical` apenas quando o runtime real estiver em `AUTH_MODE=oidc`
- para mudancas server-side no frontend, prefira `docker compose up -d --build frontend`

### 3. Validar readiness serio

```bash
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

Artefatos esperados:

- `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md`
- `artifacts/staging/checks/<janela>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<janela>-regulatory-readiness-bundle.md`

## Operacao de Janela Seria

Comandos principais:

```bash
make help-serious-window
make prepare-serious-window-dispatch WINDOW_ID=stg-2026-07-06-a
make render-serious-window-dispatch-packet WINDOW_ID=stg-2026-07-06-a
make run-serious-window-local WINDOW_ID=stg-2026-07-06-a MODE=baseline
make postprocess-serious-window RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Situacao executiva atual:

- `P0-01`: OIDC + MFA federado serio ainda bloqueado por homologacao externa
- `P0-02`: provider `AML/KYT live` pronto para fechar com credencial real
- `P0-03`: feed UE pronto para fechar com URL tokenizada real
- janela `stg-2026-07-06-a`: segue `no-go` ate preencher ownership, handoff e secrets reais

## Documentacao Canonica

- [Indice Canonico](./docs/README.md): indice principal da documentacao
- [Arquitetura](./docs/architecture.md): arquitetura real dos servicos e dados
- [Contratos de API](./docs/api-contracts.md): contratos HTTP e fluxos expostos
- [Cobertura do Frontend](./docs/frontend-coverage-matrix.md): cobertura das rotas reais do frontend
- [Operacao Local](./docs/operations.md): operacao local, troubleshooting e migrations
- [Deploy e Staging](./docs/deploy-and-staging.md): fluxo tecnico de staging e bundles
- [Validacao e Auditoria](./docs/validation-and-audit.md): smoke, Playwright, preflights e evidencias
- [Scorecard Oficial](./docs/project-kpi-scorecard.md): baseline oficial do projeto

## Estrutura

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
├── docs/
├── infra/
│   ├── keycloak/
│   ├── observability/
│   ├── postgres/
│   └── traefik/
├── packages/
│   ├── agents/
│   └── shared/
├── scripts/
├── tests/
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Riscos Residuais

- integracoes externas serias ainda dependem de credenciais e URLs reais
- `due_diligence` e `source_of_funds` permanecem em rito manual por decisao de produto
- `legal_report`, `ROS/COAF` e `block lift` exigem MFA forte homologado
- retention/recovery e sign-off institucional ainda precisam de recorrencia formal

## Proximo Passo Recomendado

1. fechar `P0-02` com provider `AML/KYT live`
2. fechar `P0-03` com feed UE tokenizado
3. homologar `P0-01` com evidencias reais
4. executar uma janela seria completa com `go/no-go` formal
