# CI/CD e Release (Atualizado Sprint 14)

## Objetivo

Documentar o pipeline atual de validação automatizada e o processo recomendado de release para a plataforma Ontrackchain pós-MVP Sprint 6-14.

## Estado Atual Geral

- **10 workflows YAML** em `.github/workflows/`:
  - **`ci.yml` (16 jobs/status checks, BLOQUEANTE)**: Push main/develop + PR para main
  - **6 nightly (cron + workflow_dispatch)**:
    - `nightly-dr-backup-restore.yml` (M16 Sprint 13 PG16 DR sáb 02UTC)
    - `nightly-explorers-live.yml` (M? exploradores fontes blockchain)
    - `nightly-load-test.yml` (P95 ≤3000ms SLA)
    - `e2e-pr-playwright.yml` (E2E shard=8 Playwright, label `e2e-required` gate)
    - `dependabot-auto-merge-security-only.yml` (M13 SQUASH Merge Queue 0-day CVE)
  - **4 deploy/aux**: `deploy.yml`, `deploy-staging.yml` (Render API auto rollback GAP#9), `deploy-production.yml`, `agent-eval.yml`
- **Branch Protection Probot Settings SSOT**: `.github/settings.yml`
  - `main`: 16 status checks obrigatórios, `enforce_admins=true`, `required_approving_review_count=1`
  - `develop`: 10 status checks obrigatórios, `enforce_admins=true`
  - Ninguém — nem CODEOWNERS, nem admins — bypassa gates P0.
- **Policies OPA/Conftest 4 regras (M10 Sprint 10 + M16b Sprint 13)** em `policies/` — job `policy-gate-conftest` valida 15 YAMLs.

## Pipeline Atual: `ci.yml` 16 Jobs (Sprint 14)

**Ordem de dependências (DAG topo → bottom):**
```text
lint → [sbom-cyclonedx-grype, observability-endpoints-gate, secrets-guard-skeleton,
        conftest-policy-gate, typecheck-mypy]
→ gate-p0-00-rls-shared-first (RLS shared == inline)
→ gate-p0-01-oidc-authz (OTK_* federação)
→ qa-gateway-cli-smoke (scan-rbac/scan-rls/scan-sla)
→ sast-bandit-python (SAST BANDIT -lll -iii)
→ dep-audit-pip-audit (CVE HIGH/CRITICAL 7 roots apps+packages)
→ pytest-matrix-services (4× self-hosted: case-management 24t, ai-service 22t)
→ sonarcloud + codecov-quality-gate (80% overall / 85% patch)
```

**Detalhamento 16 Jobs ci.yml (Sprint 14):**

| # | Job Nome | Runner | Bloqueante | Propósito | P |
|---|---|---|---|---|---|
| 1 | `lint` | ubuntu-latest | Sim | Ruff check + format --check (packages/agents + ai-service + scripts) | P2 |
| 2 | `sbom-cyclonedx-grype` | ubuntu-latest | **Sim P0** | Syft CycloneDX ISO/IEC 5962 sbom-python-monorepo.cdx.json → Grype `--fail-on high`. Retenção artifact 90d LGPD/SOC2. | **P0 M12** |
| 3 | `observability-endpoints-gate` | ubuntu-latest | **Sim P0** | Grep 9× FastAPI `main.py` → `FastAPI(` + `/healthz` + `/metrics`. tot_ok != tot_fastapi → `exit 16` | **P0 M16b** |
| 4 | `secrets-guard-skeleton` | ubuntu-latest | **Sim P0** | Regex 11 prefixos tokens reais (ghp_, gho_, glpat-, sk-, xoxb-, AKIA, etc.) — match real >0 → bloqueia. Nenhum hardcoded permitido. | **P0 M7b** |
| 5 | `conftest-policy-gate` | ubuntu-latest | **Sim P0** | OPA Conftest v0.52.0 4 Rego (01 P0 continue-on-error, 02 heavy self-hosted, 03 timeout, 04 endpoints obs) contra 15 YAMLs. | **P0 M10** |
| 6 | `typecheck-mypy` | ubuntu-latest | Sim | MyPy strict apps/{case,auth,ai,inv} + packages/ | P2 |
| 7 | `gate-p0-00-rls-shared-first` | ubuntu-latest | **Sim P0** | qa-gateway CLI: `middleware_rls` shared == fallback inline 3× main.py semanticamente idênticos (ADR-018 §2) | **P0** |
| 8 | `gate-p0-01-oidc-authz` | ubuntu-latest | **Sim P0** | qa-gateway CLI: roles OTK_* canônicas em todos serviços (`OTK_ADMIN→ADMIN` etc.) | **P0** |
| 9 | `qa-gateway-cli-smoke` | ubuntu-latest | **Sim P0** | `qa-gateway --help` + 3 comandos obrigatórios (scan-rbac, scan-rls, scan-sla) 0 exit. | **P0** |
| 10 | `sast-bandit-python` | ubuntu-latest | **Sim P0** | Bandit -lll -iii MEDIUM+/HIGH+ confiança MEDIUM+ findings 0 | **P0 M1** |
| 11 | `dep-audit-pip-audit` | ubuntu-latest | **Sim P0** | pip-audit 7 roots (apps/case/auth/inv/ai + pkgs/shared/qa/agents) CVE HIGH+CRITICAL 0 | **P0 M1** |
| 12 | `pytest-matrix-case-management` | **self-hosted** | **Sim P0** | 24 testes unitários, conftest Postgres seeding, RLS+RBAC+scoring 100% PASS | **P0** |
| 13 | `pytest-matrix-ai-service` | **self-hosted** | **Sim P0** | 22 testes unitários, TestClient lazy-init app.state, lazy pool PG 100% PASS | **P0** |
| 14 | `pytest-matrix-packages-shared` | **self-hosted** | Sim | shared + qa-gateway unit tests | P1 |
| 15 | `sonarcloud-analysis` | ubuntu-latest | Sim | SonarCloud code smells, bugs, security hotspots | P1 M8 |
| 16 | `codecov-quality-gate` | ubuntu-latest | **Sim P0** | CodeCov ≥80% overall / ≥85% patch. Fail CI abaixo. | **P0 M8** |

*Jobs pesados (pytest matrix, E2E shard=8, run-explorers) usam `runs-on: self-hosted`. NÃO ubuntu-latest — validado por Policy OPA #02.*

## 4 Policies OPA Rego (M10 + M16b)

Local: `ontrackchain/policies/01_..04_.rego`. Job: `conftest-policy-gate`.

| # | Regra | Ação | Gatilho |
|---|---|---|---|
| 01 | `deny_continue_on_error_p0_gate` | Nega | Qualquer gate P0/P1/P2/P3 com `continue-on-error = true` |
| 02 | `deny_ubuntu_latest_on_heavy_jobs` | Nega | Jobs pesados (pytest-matrix-services, "pytest service:", e2e-playwright, run-explorers-live) com `runs-on: ubuntu-latest` → exige array self-hosted labels |
| 03 | `deny_missing_timeout_minutes` | Nega | **Código Rego Sprint28+7 (política 03 implementada)** — Nega TODO job CI/nightly sem `timeout-minutes` explícito (evita 6h GHA hard desperdício minutos). Inclui exceções whitelist para jobs de trigger tipo `workflow_dispatch` sem timeout explícito opcional (desativado por padrão). |

**Código Rego Política 03 Sprint28+7 (salvar como `ontrackchain/policies/03_deny_missing_timeout_minutes.rego`):**

```rego
package ontrackchain.policies.deny_missing_timeout_minutes

import future.keywords.if
import future.keywords.in
import future.keywords.contains

# 5 jobs GHA conhecidos onde timeout-minutes é SEMPRE obrigatório (lista pode ser extendida)
heavy_job_keywords := [
  "pytest", "playwright", "e2e", "nightly", "load", "explorers",
  "dr-restore", "sonarcloud", "codecov", "trufflehog", "scan", "build", "deploy"
]

# Whitelist global EXCEÇÃO: jobs exatos que NÃO exigem timeout (ex: trigger-only, 2min)
whitelist_jobs := [
  "label-gate-check",
  "auto-merge-security-only"
]

deny contains msg if {
  some job_id, job_spec in input.jobs
  not job_spec["timeout-minutes"]
  not job_id in whitelist_jobs

  # Match por nome job contendo palavra-chave pesada
  some kw in heavy_job_keywords
  contains(lower(job_id), kw)

  msg := sprintf(
    "❌ CI GATE P0-08 (deny_missing_timeout_minutes): job '%s' SEM campo 'timeout-minutes' obrigatório. Adicione `timeout-minutes: N` onde N∈[5..120]. Exemplo abaixo no snippet. (Palavra-chave pesada detectada: '%s')",
    [job_id, kw]
  )
}

# Deny também TODO NIGHTLY independentemente de keyword (cron = SEMPRE timeout)
deny contains msg if {
  some workflow_name in ["nightly-dr-backup-restore", "nightly-explorers-live", "nightly-load-test"]
  true

  some job_id, job_spec in input.jobs
  not job_spec["timeout-minutes"]
  not job_id in whitelist_jobs

  # Workflow name contém "nightly"
  contains(lower(object.get(input, "name", "")), "nightly")

  msg := sprintf(
    "❌ CI GATE P0-08 NIGHTLY SEM TIMEOUT: workflow name='%s' job '%s' é nightly/cron mas não tem `timeout-minutes`. Obrigatorio por Dead Man Switch ADR-018. Exemplo: timeout-minutes: 60",
    [object.get(input, "name", "desconhecido"), job_id]
  )
}
```

**Exemplo YAML Job CI Sprint28+7 SEMPRE com timeout-minutes (colar em workflows GHA):**

```yaml
name: pytest-matrix-ontrackchain-9-services
on:
  pull_request:
  push:
    branches: [main, develop]
jobs:
  pytest-matrix-ai-service:
    name: "AI Service Unit Tests (44 contrato baseline)"
    runs-on: [self-hosted, ontrackchain, sa-east-1]
    timeout-minutes: 25          # <-- OBRIGATÓRIO por política 03 ADR-018 Sprint28+7
    continue-on-error: false      # <-- OBRIGATÓRIO por política 01 deny_continue_on_error_p0_gate
    env:
      OTK_ENV: staging-ci
    steps:
      - uses: actions/checkout@v4
      - name: Python 3.11 setup (pgvector 0.7.4 psycopg3 FastAPI 0.115)
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: pytest (44 contrato T2/Q3)
        run: |
          set -euo pipefail
          python -m venv /tmp/otk-venv
          source /tmp/otk-venv/bin/activate
          pip install --quiet -r requirements-cicd.txt
          pytest apps/ai-service -x -q --cov=. --cov-report=xml:coverage.xml --cov-fail-under=80
```

> **Notas Sprint28+7:** (a) timeout-minutes em jobs cron nightly SEMPRE ≤60min. (b) Jobs deploy staging ≤30. (c) Jobs pesados (Playwright e2e shard=8) ≤40 por shard. (d) Limite GHA ubuntu-latest por job hard = 360min = 6h → política 03 evita chegar perto disto.
| 04 | `deny_missing_observability_endpoints_fastapi` | Nega (NOVO M16b) | Arquivos `apps/*/src/*/main.py` usando `FastAPI(` sem rota `/healthz` E/OU `/metrics` definida |

## 6 Nightly Workflows (Cron + Dead Man Switch Duplo)

Todo nightly tem: **(a) timeout-minutes explícito**, **(b) Dead Man interno (cria GitHub Issue P1 se SLA breach)**, **(c) Healthchecks.io ping externo com secret `HEALTHCHECKS_IO_<UUID>` (checklist 4-eyes R12)**.

| Workflow | Cron | Runner | Propósito | SLA |
|---|---|---|---|---|
| `nightly-dr-backup-restore.yml` | sáb 02:00UTC | self-hosted 60min | DR PG16 pgvector: same-run restore container porta 5433, 1% LGPD, row count val 5 tabelas core, S3 sa-east-1 AES256 opcional, artifact 180d fallback | 24h (Healthchecks.io + Dead Man) |
| `nightly-explorers-live.yml` | diário 03:00UTC | self-hosted 50min | Exploradores fontes multi-chain reais; qa-gateway `scan-sla` sucesso % | 99% fontes |
| `nightly-load-test.yml` | seg-sex 01:00UTC | self-hosted 90min | Locust k6 Load P95 latência ≤3000ms SLA (GAP#11) | P95 ≤3000ms |
| `e2e-pr-playwright.yml` | PRs com label `e2e-required` (Sprint 6 M4 gate label) | self-hosted shard=8 40min | Playwright E2E caminhos críticos OIDC/RBAC/ROS/Compliance | 8 shards 100% PASS |
| `dependabot-auto-merge-security-only.yml` | quartas 04:00UTC | ubuntu-latest 20min | Dependabot security-only → enableAutoMerge → SQUASH Merge Queue (15 gates) → Canary 30min → Prod 4-eyes | 0-day CVE <2h |

## 3 Deploys (Render API GAP#9 Rollback Automático)

| Workflow | Gatilho | Propósito |
|---|---|---|
| `deploy-staging.yml` | Push develop / PR merge develop | Render API deploy staging → `summary-or-rollback` automático se healthz 5min falhar |
| `deploy-production.yml` | Tag release v*.*.* (workflow_dispatch + aprovação Environment production) | Render API prod com 4-eyes approval + rollback Render API |
| `deploy.yml` | Push main (ambiente agregador legado) | Compatibilidade workspace agregador pai |

## Backlog Implementado (Sprint 6→14, NÃO É MAIS BACKLOG)

**Itens originalmente em "Backlog Recomendado CI/CD" — agora FECHADOS:**
- ✅ **Adicionar lint/typecheck por app**: FECHADO (jobs `lint` ruff + `typecheck-mypy` strict)
- ✅ **Gates de schema/migrations**: FECHADO (seeding pytest conftest Postgres migrations 0001-0021 rodam em cada teste)
- ✅ **Publicar artefatos mais ricos**: FECHADO (SBOM Grype artifact 90d, Playwright merged reports, qa-gateway scans)
- ✅ **Release automation com versionamento**: FECHADO (Dependabot SQUASH Merge Queue + deploy-production.yml tag trigger)

## Riscos Residuais (Sprint 14)

- **R19 Risco Helm Ingress**: Ingress default-deny NetworkPolicy desativado temporariamente por necessidade de troubleshooting → Data Leak LGPD R$50M Art.49. Mitigação: label `needs-security-review` obrigatório qualquer alteração NetPol.
- **R20 Node Drain PDB=0**: Qualquer PDB com `minAvailable=0` (exceto `mock-oidc`) → drain nó causa downtime não planejado SLA 24h breach. Mitigação: qa-gateway T6 verifica PDBs sempre.
- **R21 Black Friday 10× carga**: HPA behavior scaleUp 60s pode ser insuficiente para 10× pico. Mitigação: Load Test nightly P95 ≤3000ms (GAP#11) detecta antes + HPA behavior customizável values.yaml.
- **R22 Drift 20+ Charts**: Multiplos charts pequenos ao invés de 1 single chart causa drift. Mitigação: Opção A Single Chart `ontrackchain-platform` + `helm diff` 2-eyes em staging antes de prod.
- **M5 Push Remoto**: 10 commits locais da branch main ahead origin/main. 🔴 Bloqueado até método de auth definido e autorização explícita do usuário.

## Recomendação Imediata (Sprint 14)

1. Resolver M5 Push Remoto: definir método de auth (PAT SSO SAML, SSH deploy key read/write ou Render GitHub App) + solicitar autorização escrita.
2. **Habilitar Merge Queue UI GitHub** (requerimento do Dependabot Security Auto-Merge SQUASH — configuração one-shot Settings → Branches → Merge Queue Rules).
3. Provisionar 10 Secrets `.env-secrets.template` via interface Settings → Secrets → Actions (2 SREs 4-eyes assinatura UI one-shot).
4. Rodar `helm install --dry-run --debug ontrackchain ontrackchain-platform/` + `helm diff` staging antes da primeira implantação K8s.
5. Ativar **GitHub Environment `staging-serious`** approvals + secret multi-linha `STAGING_WINDOW_PRIVATE_ENV`.

---

## Anexo: Legado Sprint ≤5 (Referência Histórica NÃO ATUAL)

> ⚠️ **A partir da Sprint 6, os workflows abaixo foram consolidados/substituídos por `ci.yml` 16 jobs + 6 nightly + 4 deploy (ver seções acima).**
> As descrições abaixo são preservadas apenas para referência histórica e não representam o estado atual.

---

## Job `build` (LEGADO Sprint ≤5)

### 1. Checkout

- baixa o repositorio

### 2. Build e Start da Stack

```bash
docker compose up -d --build
```

Objetivo:

- validar que a stack inteira ainda sobe

### 3. Espera o Gateway

Faz polling de:

```bash
curl -fsS http://localhost:8080/
```

Objetivo:

- garantir que o entrypoint ficou disponivel antes dos testes

### 4. Publica Diagnosticos do Docker

- artefato `build-diagnostics`

## Job `smoke`

### 5. Checkout + Build da Stack

- sobe novamente a stack em runner isolado

### 6. Espera o Gateway

- repete o gate de readiness

### 7. Setup Python

- usa Python `3.11`

### 8. Executa Smoke Runtime

Variaveis atuais:

- `ONTRACKCHAIN_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`

Comando:

```bash
python scripts/smoke_runtime.py
```

Objetivo:

- validar os fluxos criticos backend/proxy/auditoria antes da camada de browser

### 9. Publica Diagnosticos do Docker

- artefato `smoke-diagnostics`

## Job `playwright`

### 10. Checkout + Build da Stack

- sobe novamente a stack em runner isolado

### 11. Espera o Gateway

- repete o gate de readiness

### 12. Setup Node.js

- usa Node `20`

### 13. Instala Dependencias do Frontend

```bash
npm install
```

### 14. Instala Browser do Playwright

```bash
npx playwright install chromium --with-deps
```

### 15. Executa Suite Playwright

Variaveis atuais:

- `TEST_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`

Comando:

```bash
npx playwright test
```

### 16. Publica Artefatos

- sobe `test-results`
- sobe `playwright-diagnostics`

## Job `playwright-dev-auth`

### 17. Checkout + Build da Stack em `dev auth`

- sobe a stack com `AUTH_MODE=dev` e `DEV_AUTH_ENABLED=true`

### 18. Espera o Gateway

- repete o gate de readiness

### 19. Setup Node.js + Dependencias

- instala dependencias do frontend e browsers do Playwright

### 20. Executa Suite `dev-auth`

Variaveis atuais:

- `TEST_BASE_URL=http://localhost:8080`
- `ONTRACKCHAIN_API_KEY=otc_live_demo_key`
- `AUTH_MODE=dev`

Comando:

```bash
npm run test:e2e:dev-auth
```

Observação operacional:

- o comando agora executa preflight explicito de `baseURL` e `/auth/config`
- falha cedo se o ambiente nao estiver em `AUTH_MODE=dev`
- valida apenas a regressao local de `2FA` no scaffold `dev`

### 21. Publica Artefatos

- sobe `playwright-dev-auth-results`
- sobe `playwright-dev-auth-html-report`
- sobe `playwright-dev-auth-diagnostics`

## Cobertura Atual da CI

### Coberto

- build da stack
- readiness do gateway
- `scripts/smoke_runtime.py`
- regressao E2E do frontend
- diagnosticos separados por etapa

### Cobertura adicional ja institucionalizada

- drift de schema e coerencia entre migrations via [check_postgres_schema.py](../scripts/check_postgres_schema.py)
- baseline de segurança contra placeholders/defaults via [check_security_baseline.py](../scripts/check_security_baseline.py)
- regressao de preflights, homologacao, `window packet`, `release dossier` e `staging window runner`

## Workflow `quality-gates`

### Security Baseline

- executa [check_security_baseline.py](../scripts/check_security_baseline.py)
- bloqueia placeholders/secrets de demo fora da allowlist explicita do projeto
- protege especialmente contra reintroducao acidental de `change-me`, `default TOTP secret`, hashes fake e blocos de private key em caminhos sensiveis

### Preflight Regressions

- executa regressao dos scripts de janela séria e homologação:
  - `check_staging_env_placeholders.py`
  - `check_staging_env_ownership_coverage.py`
  - `check_staging_env_handoff.py`
  - `render_staging_private_env_templates.py`
  - `render_staging_window_packet.py`
  - `prepare_staging_window.py`
  - `build_staging_release_dossier.py`
  - `run_staging_window.py`
  - `preflight_oidc_serious_env.py`
  - `preflight_external_integrations.py`
  - `homologation_external_evidence.py`
- garante que a trilha `checks -> packet -> preflight -> homologacao -> dossier` continue íntegra

### Frontend Audit

- instala dependencias do frontend com `npm ci`
- executa `npm audit --omit=dev --audit-level=critical`
- usa o frontend atualizado para [package.json](../apps/frontend/package.json) e [package-lock.json](../apps/frontend/package-lock.json)
- criterio bloqueante atual: apenas `critical`
- findings `high` conhecidos do ecossistema `Next.js` permanecem sinalizados como backlog de upgrade major e nao bloqueiam este gate inicial

### Postgres Schema

- executa [check_postgres_schema.py](../scripts/check_postgres_schema.py)
- valida numeração contínua das migrations
- valida que `README.md` referencia todas as migrations atuais
- valida que contratos de schema introduzidos em `infra/postgres/migrations/*.sql` também existem em [init.sql](../infra/postgres/init.sql)

### Frontend Typecheck

- instala dependencias do frontend com `npm ci`
- executa `npm run typecheck`
- usa [package.json](../apps/frontend/package.json) com `tsc -p tsconfig.json --noEmit`

### Python Quality

- executa em matriz por app/pacote:
  - `apps/auth-service`
  - `apps/public-api`
  - `apps/monitoring-api`
  - `apps/investigation-api`
  - `apps/compliance-api`
  - `apps/report-api`
  - `packages/shared`
  - `packages/agents`
- instala `ruff`
- roda `ruff check --select F,E9`
- roda [check_python_app.py](../scripts/check_python_app.py) para validação sintática localizável por app

Objetivo:

- transformar `P1-05` em gate real e preparar `P1-06` e `P1-07` sobre uma base de qualidade mínima por componente

## Workflow `staging-serious-window`

### Proposito do workflow

- executar a janela séria em trilho controlado de CI/CD, sem depender de shell local e sem versionar `.env.staging.private`

### Quando usar

- apos merge ou cut controlado que precise de evidência oficial de `staging`
- quando a janela exigir aprovação manual antes de tocar providers reais
- quando o sign-off precisar de artefatos anexáveis produzidos pelo runner oficial

### Entradas obrigatorias

- `window_id`: identificador operacional da janela, no formato `stg-YYYY-MM-DD-x`
- `mode`: `baseline` ou `homologated`
- `environment_name`: `GitHub Environment` que centraliza aprovacoes e o secret `STAGING_WINDOW_PRIVATE_ENV`

### Preparacao local recomendada antes do disparo

Antes de abrir o `workflow_dispatch`, preparar o rito com:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
```

### Sequencia executada

1. faz `checkout` do repositorio
2. prepara `ci-artifacts/`
3. valida que o secret `STAGING_WINDOW_PRIVATE_ENV` existe no `GitHub Environment`
4. materializa `.env.staging.private` apenas no runner efemero
5. executa `python scripts/prepare_staging_window.py --window-id <janela> --mode <modo> --run`
6. publica artefato unico contendo:
   - `ci-artifacts/prepare-staging-window-output.json`
   - `ci-artifacts/staging-serious-window-signoff.md`
   - `artifacts/staging/checks/`
   - `artifacts/staging/dossiers/`
   - `artifacts/staging/templates/`
   - `artifacts/staging/window-packet-<janela>.md`
   - `artifacts/homologation/`

### Pos-processamento local recomendado

Depois de baixar o artifact do workflow, executar o pos-processamento local completo com:

```bash
make postprocess-serious-window-dry-run \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

O comando acima:

- atualiza `ci-artifacts/staging-serious-window-signoff.md`
- gera o sign-off versionado em `docs/governance-weekly/`
- gera o `go/no-go decision packet` versionado em `docs/governance-weekly/cycles/<data>/`
- sincroniza o registro semanal da mesma janela
- sincroniza o board operacional global

Se precisar executar os passos separadamente:

```bash
python scripts/render_staging_window_signoff.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --output-file ci-artifacts/staging-serious-window-signoff.md \
  --governance-weekly-dir docs/governance-weekly

python scripts/render_staging_window_weekly_governance.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"

python scripts/render_staging_window_decision_packet.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

### Controles de segurança

- o secret nao e publicado como artefato nem escrito em documentação
- aprovacoes podem ser forçadas pelo proprio `GitHub Environment`
- a execucao falha cedo quando o secret da janela nao esta presente ou quando `validate/preflight/run` retornam erro

## Estrategia de Release Recomendada

### Pull Request

Objetivo:

- bloquear regressao funcional evidente

Gates recomendados:

- CI com smoke e Playwright verde
- job de build verde
- revisao de codigo
- revisao de mudancas de schema quando aplicavel

### Merge em Branch de integração

Objetivo:

- preparar promocao para staging

Gates recomendados:

- stack sobe
- smoke runtime verde
- Playwright verde
- docs relevantes atualizadas

### Staging regulatório

Objetivo:

- validar controles, auditoria e operação

Checklist:

- trilha auditavel consultavel
- `legal_report` com enforcement correto
- readiness regulatório revisado
- bundle `AML/KYT live` e gate de runtime anexados quando o escopo exigir
- JSONs da janela UE anexados quando o escopo exigir `EU_CONSOLIDATED`
- quando houver `AML/KYT live`, `make check-compliance-provider-runtime` verde e anexado
- quando houver feed UE, `make gate-p0-03-eu-live` com `WINDOW_ID` e `REQUEST_ID` ou fluxo equivalente com JSONs anexados

## Processo Recomendado de Release

```text
PR -> CI -> merge -> staging tecnico -> staging regulatorio -> aprovacao -> producao
```

## Convencao de Tags e Releases

Objetivo:

- evitar colisao de tags em releases editoriais (docs-only)
- garantir que `Latest` continue representando releases de produto
- preservar rastreabilidade entre tag, commit e release notes

### Tipos de tag

| Tipo | Quando usar | Nome recomendado | Deve ser `Latest`? |
| --- | --- | --- | --- |
| release de produto | mudanca funcional/regulatoria/codigo | `vX.Y.Z` | sim |
| release docs-only | mudanca editorial/documentacao | `vX.Y.Z-docs.N` | nao |

Regras:

- nunca reaproveitar ou mover uma tag existente
- se o nome base ja existir, incremente apenas o sufixo `.N` (`.1`, `.2`, ...)
- releases docs-only devem ser publicadas como `None` (nao `Latest`)
- a tag deve apontar para um commit da `main` (ou branch alvo explicitamente acordada) e o texto da release deve citar o hash curto do commit

Nota (escopo):

- tags/releases `docs-only` sao informativas: servem para rastrear navegacao, guias operacionais e consolidacoes de documentacao.
- elas nao representam mudanca de produto/semantica de runtime e nao devem substituir a release de produto marcada como `Latest`.

### Fluxo recomendado (docs-only)

1. merge/commit na `main` com a mudanca documental
2. criar tag anotada `vX.Y.Z-docs.N` apontando para o `HEAD` atual
3. publicar release com:
   - titulo igual a tag
   - `Set as the latest release`: **None**
   - release notes curtas com:
     - lista do que mudou
     - commit hash
     - portas canônicas (`docs/README.md`, `TECHNICAL_APPENDIX.md`, `operations.md`)

### Exemplo de nomenclatura

- `v4.0.7` (produto)
- `v4.0.8-docs.2` (docs-only subsequente, quando houver mais de uma rodada editorial)

### Higiene de tags (evitar duplicidade)

Antes de criar uma nova tag docs-only, valide se a tag base ja aponta para o commit correto:

```bash
git rev-parse HEAD
git rev-parse vX.Y.Z-docs || true
git ls-remote --tags origin vX.Y.Z-docs || true
```

Regras praticas:

- se `vX.Y.Z-docs` ja existir e apontar para o `HEAD`, nao crie `.1`
- se `vX.Y.Z-docs` ja existir e apontar para outro commit, use `vX.Y.Z-docs.1` (ou incremente `.N`) em vez de mover a tag existente
- se existir `vX.Y.Z-docs.1` e a base nao existir, mantenha o sufixo `.1` e siga com o próximo numero apenas quando houver nova rodada

## Criterios Minimos de Aprovacao

- CI verde
- smoke verde no ambiente alvo
- artefatos obrigatorios da janela anexados quando houver provider real
- nenhuma regressao em:
  - `plan lock`
  - `report_generated`
  - `report_downloaded`
  - `legal_report`
  - concorrencia de investigation

## Mudancas que Exigem Mais Cuidado

### Schema

Sempre que houver mudanca de schema:

- atualizar `init.sql`
- criar migration correspondente
- validar com volume persistido

### Auth/Proxy

Sempre que houver mudanca em auth/proxy:

- rerodar smoke
- rerodar Playwright compliance
- verificar `audit_logs`

### Billing

Sempre que houver mudanca em pricing/quote:

- validar `estimate -> start`
- validar `plan lock`
- validar ledger

## Backlog Recomendado para CI/CD

### Alta prioridade

- adicionar lint/typecheck por app
- adicionar gates de schema/migrations

### Media prioridade

- publicar artefatos mais ricos
- adicionar matrix de navegadores
- reduzir duplicacao de startup entre jobs

### Baixa prioridade

- release automation com versionamento
- changelog automatizado

## Exemplo de Pipeline Alvo

```text
job 1: lint + typecheck
job 2: build stack
job 3: smoke runtime
job 4: Playwright critical/compliance
job 5: aprovacao manual para staging
job 6: deploy staging
job 7: smoke pos-deploy
```

## Riscos Atuais

- CI ainda rebuilda a stack em runners diferentes
- a promocao tecnica automatizada ainda usa trilho `dev-compatible` para cobrir o smoke runtime
- a janela séria de `staging` agora possui workflow dedicado, mas a execucao real ainda depende de providers externos homologados e da qualidade do secret entregue ao `GitHub Environment`

## Recomendacao Imediata

O próximo passo mais valioso para CI/CD e:

- reduzir duplicacao entre jobs com imagem/cache ou compose reaproveitavel
- promover `staging-serious-window.yml` a rito oficial da janela regulatoria, anexando o artefato `serious-staging-window-<janela>` como evidência oficial de release
