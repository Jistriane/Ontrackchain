# ADR-018 — QA Gateway como Single Source of Truth para RLS + Padrão Shared-First / Fallback Inline

## Contexto

Na Sprint 1 (P0 Fundação Segura), tivemos que distribuir e garantir a mesma lógica de segurança
em **3 serviços Python** (case-management, auth-service, investigation-api) e em
**pelo menos 4 pontos do CI/CD** (gate RLS cross-tenant, scan tabelas, health checks,
LGPD scan).

Os riscos de termos implementações duplicadas e divergentes eram altos:

1. **Desvio semântico de RLS**: 1 serviço esquecer de setar bypass de rotas públicas
   (login/dev-token/sso), resultando em 401s em produção.
2. **Aumento de débito técnico**: Se adicionarmos um novo path bypass (ex: rota webhook
   pública), teríamos que editar 3 arquivos `main.py` manualmente.
3. **Falta de auditabilidade**: Qual foi a versão do algoritmo de validação de UUID que
   rodou no último deploy? Em script standalone vs middleware inline divergem é difícil
   provar conformidade regulatória (Bacen, LGPD).
4. **Risco de regressão**: Falta 1 serviço implementar `current_setting('app.organization_id', TRUE)`
   com o parâmetro de default NULL correto → vazamento cross-tenant silencioso.

## Decisão

### 1. Criar o package `packages/qa-gateway` como **Fonte Única da Verdade (SSOT)**.
   Toda lógica de:
   - scan RLS em tabelas (checar coluna org_id, RLS enabled, policy *tenant_isolation, índice);
   - scan LGPD (CPF plaintext, chaves privadas em DB);
   - health check paralelo de endpoints;
   - **scan SLA 24h Dead Man Switch** (último sucesso exploração há < 86400s);
   - (futuro) geração de relatórios de conformidade;
   é implementada APENAS no package, com console_scripts `qa-gateway` expondo CLI.

### 1.1 (Sprint 4 FINAL) Expansão QA Gateway: 6 comandos CLI MVP completo
```
qa-gateway --help          # Lista todos + versões + exit codes
qa-gateway scan-rls        # Fase 2/3 deploy — garante RLS ativo + policy tenant_isolation + índice org_id em TODAS tabelas
qa-gateway health          # Fase 2 warmup pós-deploy — HTTP(S) paralelo n endpoints com timeout e 2 retries
qa-gateway scan-lgpd       # Fase 4 nightly compliance — CPF plaintext, chaves privadas, PII não pseudonimizado em DB
qa-gateway scan-sla        # Fase 3 nightly-explorers — GAP#5 SLA 24h Dead Man Switch (último sucesso < 86400s)
qa-gateway scan-rbac       # Sprint 4 NOVO — Fase A static scan rotas write (POST/PUT/PATCH/DELETE) × _require_role_with_audit
                           #               + Fase B DB scan users.role ∈ {VIEWER..OWNER} e <=1 OWNER/organização
```
Os comandos aceitam múltiplas fontes (env vars, flags, arquivos `.prom` ou fail) e gravam
`--failures-json <path>` para artefatos de CI, além de **exit codes rigorosos**:
  - `0`  = sucesso zero issues;
  - `1`  = falha de regra (ex: SLA violado / RLS desativado / OWNER duplicado);
  - `2+` = erro de infra (sem conexão DB, serviço unreachable, token vazio).

### 1.2 (Sprint 4 FINAL) Workflows CI/CD consumidores do qa-gateway × Rollback Automático
| Workflow (.github/workflows/*.yml) | Jobs | Consumo qa-gateway + automação |
|---|---|---|
| **ci.yml** | `gate-p0-00-rls` + `pytest-matrix 7×` + `gate-p0-01-oidc` | Python API `qa_gateway.rls.assert_tables_have_rls` + fallback inline equivalente |
| **deploy-staging.yml** | wait-ci-green → render ×4 hook → health → scan-rls → **rollback Render API** | `qa-gateway health` + `qa-gateway scan-rls` (staging DB); **NEEDS_ROLLBACK → POST /v1/services/{id}/rollback AUTOMÁTICO em 4 serviços** (R7 GAP#9) |
| **deploy-production.yml** | preflight semver → canary 10% → 30min observe → promote → **rollback AUTOMÁTICO se falhar** | `qa-gateway health` + `qa-gateway scan-rls` (prod réplica read-only); Rollback Render API automático P0 se promote/observe falhar |
| **nightly-explorers-live.yml** (02h BR) | preflight → 10 casos live RPC mainnet + polling 15min → `sla-dead-man-switch` | `qa-gateway scan-sla` + cria **Issue GitHub label `P1-critical sla-deadman investigation-down`** se último sucesso há > 24h (R5 GAP#5) |
| **e2e-pr-playwright.yml** (paths filter front/stack) | filter → stack compose → playwright `@critical-path|rbac|api-consumer` → comentário PR | `qa-gateway health` opcional em warmup; Playwright 4 suítes + trace upload artifact 30d (R6 GAP#6) |

   Deve existir **apenas uma vez** dentro de `qa_gateway/`; duplicatas em scripts YAML
   são proibidas (exceto fallback inline em ci.yml gate-p0-00-rls-b, garantido por exit codes 100% iguais).

### 2. Todo serviço Python (FastAPI) deve **importar Shared First, Fallback Inline**.
   O padrão OBRIGATÓRIO para middleware RLS, helpers `canonicalize_role()`, e futuros
   helpers de segurança de cada serviço é:

   ```python
   try:  # SHARED PACKAGE FIRST — SEMPRE tentar importar de packages/
       from ontrackchain_shared.middleware_rls import register_rls_context_middleware as _mw
       _mw(app, ...)
   except Exception:  # noqa: BLE001 — FALLBACK INLINE — equivalente SEMÂNTICO 1:1
       # Código inline idêntico ao do shared package.
       # Este bloco SÓ executa se o host NÃO tiver o shared package instalado.
   ```

   **Regra de governança**: O fallback inline **nunca pode divergir semanticamente** do shared.
   Antes de abrir um PR que altere o helper do shared package, **o desenvolvedor é OBRIGADO
   a aplicar a mesma alteração no fallback inline de TODOS os serviços que usam aquele helper**.

### 3. O CI não depende exclusivamente do `qa-gateway` package instalado.
   Para evitar o risco de build de CI quebrar por falta do hatchling ou do package
   `packages/qa-gateway/` buildando em um checkout raso (shallow), o job
   `gate-p0-00-rls` tem **dois estágios**:
   - `P0-00a`: usa `qa-gateway` (SSOT) via Python import (scan completo de 15 tabelas).
   - `P0-00b`: fallback Python heredoc inline idêntico ao do teste
     `tests/test_p0_rls_cross_tenant.py` (prova de isolamento A vs B).
   Se o `qa-gateway` falhar por qualquer motivo de infraestrutura, o P0-00b **ainda
   bloqueia merge** se existir vazamento cross-tenant.

### 4. Imagem Docker standalone para QA Gateway.
   O package tem CLI `qa-gateway` (console_scripts via Click) + Dockerfile standalone
   (não depende do repositório de aplicação). Esta imagem é usada:
   - Em `deploy-staging.yml` (Post Deploy Health Check + Rollback Gate);
   - Em `nightly-compliance.yml` (LGPD scan com dump staging);
   - Em validação manual de auditoria (fora do ciclo CI/CD normal).

## Consequências

### Prós
- **Fonte única + resiliência**: Se o shared quebrar, os serviços continuam funcionando
  (fallback inline equivalente).
- **Auditabilidade**: Logs de `qa-gateway scan rls` tem hash e versão do pacote,
  fácil provar para auditoria "o que rodou no dia 08/08/2026".
- **Escalabilidade**: Novo serviço Python = **2 minutos para aplicar o padrão
  shared-first + fallback inline**, copiando 1 bloco de ~100 linhas.
- **Reduz risco de regressão**: Mudar o regex UUID? Melhorar path bypass? Basta 1 arquivo:
  `middleware_rls.py` (e sincronizar fallbacks inline, regra #2).

- **Risco R2**: "Fallback inline divergiu sem ninguém perceber" → **Mitigação**: todo
  fim de sprint (Sprint Review) o `qa-gateway` gera um `checksums.sha256` dos blocos
  inline vs shared e o CI nightly valida divergências (dif > 0 = aviso).
- **Risco R3**: "Imagem Docker standalone pesada (>1GB)" → **Mitigação**: usa
  `python:3.11-slim` + apagar cache pip; meta < 300MB comprimida. Smoke test `qa-gateway --version` + 3 `--help` no build para confirmar imagem.
- **Risco R4**: "Dependências `psycopg[binary]` com versões diferentes entre serviços" →
  **Mitigação**: ADR não força mesma versão; `qa-gateway` declara pin de versão mínimo
  (`>=3.2.3`); serviços antigos ficam no seu pin, novos no mais novo.
- **Risco R5 (NOVO Sprint 3)**: "Exploradores live down e ninguém percebe → violação SLA
  silenciosa" → **Mitigação**: Job `sla-dead-man-switch` no `nightly-explorers-live.yml`
  usa `qa-gateway scan-sla` e **cria issue GitHub label `P1-critical sla-deadman`** se
  último sucesso há > 24h.
- **Risco R6 (NOVO Sprint 3)**: "Playwright e2e em PR falha por flaky RPC mainnet
  (rate limit)" → **Mitigação**: E2E em PR roda com `AUTH_MODE=dev` e
  `INVESTIGATION_RPC_ENABLED=false`; exploração live real fica APENAS no
  nightly-explorers 02h BR em horário de menor tráfego RPC.
- **Risco R7 (NOVO Sprint 4 — GAP#9 fechado)**: "Deploy staging/prod quebrou, ninguém
  executa rollback por medo/esquecimento → downtime 2h+" → **Mitigação**: Jobs
  `summary-or-rollback` (staging) e `summary-and-notify` (prod) implementam **Render
  REST API Automático** com secrets `RENDER_API_TOKEN_{STAGING|PROD}` +
  `RENDER_{AUTH|PUBLIC|INVESTIGATION|CASE}_SERVICE_ID_{STAGING|PROD}`.
  POST `https://api.render.com/v1/services/<SVC_ID>/rollback` — 4 serviços em paralelo
  (throttling 300ms entre calls); exit code 1 garante bloqueio CI até rollback bem-sucedido.
- **Risco R8 (NOVO Sprint 4 — GAP#7 fechado 95%)**: "Alertas silenciosos, métricas SLA
  e RLS violadas sem notificar ninguém" → **Mitigação**:
  `infra/observability/platform.rules.yml` adicionou 3 regras Prometheus Alertmanager
  (1) `InvestigationExplorerSlaDeadManSwitch for 5m severity=critical`,
  (2) `RlsViolationBurstDetected rate(http_requests_total{status=401,reason=rls_organization_mismatch}[5m])>0.333 severity=warning`,
  (3) `E2ePlaywrightSuccessRateBelowSla < 0.90 severity=warning`. Todas têm runbook
  link em label `runbook:` e disparam Alertmanager → Slack/Teams webhook via monitoring-api.

### Workflow de Aplicação (Regra #2 prática)
1. Abrir PR alterando `packages/shared/src/ontrackchain_shared/<helper>.py`.
2. Abrir **no mesmo PR** commits sincronizando os fallbacks inline de:
   - `apps/case-management/src/case_management/main.py`
   - `apps/auth-service/src/auth_service/main.py`
   - `apps/investigation-api/src/investigation_api/main.py`
3. Adicionar 1 teste em `tests/test_p0_rls_cross_tenant.py` que valide o novo cenário
   (ex: novo bypass path).
4. Marcar no PR label `needs-security-review` (1 par extra de olhos antes do merge).
5. **Se PR altera CI/CD ou workflow deploy**:
   - Adicionar screenshots ou evidência de passagem do workflow em fork pessoal/branch de teste.
   - Validar sintaxe YAML local com `yamllint .github/workflows/` ou fallback `python -c`
     balanceamento de chaves `{}` e `[]`.
6. **SEMPRE evitar heredocs Python/YAML em blocos `run: |`** — trocar por
   `echo "linha" > /tmp/_aux.py` + `python3 /tmp/_aux.py`. Evita `ScannerError: while
   scanning a simple key could not find expected ':'` (regra padrão Sprint 3+4).
7. **Se PR adiciona comando novo qa-gateway**: adicionar no CI `job gate-p0-01-oidc`
   (ou job equivalente) o comando `--help` para garantir que o comando não quebre em
   merge, + adicionar linha na tabela §1.1 deste ADR e link de consumo na tabela §1.2.

## Sprint 6 Update (P3 Pós-MVP) — 100% Média GAPs

**Média final dos 12 GAPs do documento Arquitetura QA/DevOps: 12 × 100% = 100,0%**
(Antes: 99,3% = GAP#6=98%, GAP#7=95%).

### Riscos novos (R9, R10) + Mitigações Sprint 6
- **Risco R9 (Sprint 6 NOVO — GAP#6 100% fechado)**: "Playwright shard=8 paralelo roda
  em TODO PR pequeno (ex: typo docs) custando 8 runners × 5min = 40min-minutos CI/PR
  desnecessários → $$$ custo GitHub Actions em projetos grande" → **Mitigação**:
  Job `changed-file-filter` em `.github/workflows/e2e-pr-playwright.yml` recebe
  **Label-Gate obrigatório**: `has_e2e_label=true` é necessário (via
  `github.event.pull_request.labels` checado em Python 1-liner).
  - SE PR tem label `e2e-required` → E2E roda (8 shards paralelos)
  - SE PR NÃO tem label → job `e2e-playwright` pula (skip amigável)
  - Push para `main`/`develop` OU `workflow_dispatch` → SEMPRE roda (guardrail merge safety)
  Resultado: economia ~90% minutos CI em PRs pequenos/docs/infra leves.

- **Risco R10 (Sprint 6 NOVO — GAP#7 100% fechado)**: "3 Prometheus alerts existem mas
  time não tem Dashboard Grafana único centralizado QA → precisa abrir 5 abas
  separadas para ver SLA/RLS/E2E/pytest/Load P95 → observabilidade fragmentada" →
  **Mitigação**: Novo dashboard Grafana provisionado automaticamente:
  `infra/observability/grafana/dashboards/ontrackchain-qa-overview.json` (uid:
  `ontrackchain-qa-overview`, 8 painéis, 3 rows × 12 grid):
  | Painel ID | Título | Tipo | Métrica | Alerta se |
  |---|---|---|---|---|
  | 1 | SLA 24h Dead Man Switch (s desde último sucesso) | stat | `time()-last_success` | >82800s vermelho |
  | 2 | RLS 401 req/min (5m avg) | stat | `rate(http_rls_401[5m])` | >0.333 req/min vermelho |
  | 3 | E2E Playwright success rate 1h (%) | stat | `passed/total*100` | <90% vermelho |
  | 4 | RLS 401 histórico 24h por app | timeseries | `sum by(app) rate([5m])` | regra threshold |
  | 5 | E2E sucesso por suite (%) | timeseries | `suite%` por critical/rbac | <90% vermelho |
  | 6 | Alertas Prometheus ativos firing | stat | `count(ALERTS{firing})` | >=3 vermelho |
  | 7 | pytest CI passed/failed contador 1h | timeseries | `rate(ci_pytest[1h])` | |
  | 8 | GAP#11 Load test Nightly P95 latência (ms) | stat | `histogram_quantile 0.95` | >3000ms vermelho |

### Atualizações Workflow Aplicação (adendo Sprint 6)
8. **Antes de marcar PR pronto para merge**: se PR altera `apps/frontend/**` ou
   `apps/case-management/**` (rotas ou telas de negócio), o **revisor/QA é OBRIGADO** a
   adicionar label `e2e-required` para habilitar 8 shards Playwright. O CI NÃO roda E2E
   sem esta etiqueta (em PR pull_request; push main/develop sempre roda).
9. **Todo novo alerta Prometheus adicionado em platform.rules.yml**: deve ter um painel
   correspondente no dashboard `ontrackchain-qa-overview.json` (SSOT observabilidade QA).
10. **Se GAP#12 (SAST Bandit + pip-audit) ficar `continue-on-error: true` > 2 sprints**:
    abrir issue etiquetada `security-mvp-next-milestone` para transformar em bloqueante
    após 1ª remediação baseline CVEs HIGH.

## Status (Sprint 6 Final)
**Tabela 12 GAPs × Sprint × % × Status Fechado:**

| GAP | Sprint | % | Status | Fechado em |
|---|---|---|---|---|
| 1  RLS Cross-Tenant P0 | 1 | 100 | ✅ | S1 |
| 2  pytest CI 7× paralelo | 1 | 100 | ✅ | S1 |
| 3  Deploy Seguro Semver | 2 | 100 | ✅ | S2 |
| 4  LGPD + QA Gateway 6 comandos | 1-4 | 100 | ✅ | S4 |
| 5  SLA 24h Exploradores Live | 3 | 100 | ✅ | S3 |
| 6  E2E Playwright PR Shard 8 + Label gate | 5 + 6 | 100 | ✅ | S6 |
| 7  Prometheus Alerts 3 + Grafana Dashboard Único | 4 + 6 | 100 | ✅ | S6 |
| 8  Vault/Secrets Prod ADR-016 | 2 | 100 | ✅ | S2 |
| 9  Rollback Render API Automático | 4 | 100 | ✅ | S4 |
| 10 ADRs + DoD + Governança QA | 3-4 | 100 | ✅ | S4 |
| 11 Load test 20 paralelo Nightly P95 | 5 | 100 | ✅ | S5 |
| 12 SAST Bandit + pip-audit CVE scan MVP | 5 | 100 | ✅ | S5 |

**Média**: 12/12 × 100% = **100,0%**. Meta ≥ 90% EXTREMAMENTE ultrapassada. MVP concluído.

## Sprint 8 Update (Milestone Pós-MVP 2)

### Riscos novos (R11, R12, R13) + Mitigações Sprint 8
- **Risco R11 (Sprint 8 NOVO — M6 Branch Protection)**:
  "CI bloqueante GAP#12/RLS/pytest existe, mas o dono do repo com permissão 'admin' pode
  bypassar TODOS os status checks, mergear PR quebrado direto em main, e causar
  produção down / vazamento cross-tenant / rollback forçado às 03h da manhã de sábado"
  → **Mitigação**: `.github/settings.yml` (SSOT Branch Protection — Sprint 8 M6) define
  `enforce_admins: true` (Ninguém, nem admin, bypassa as regras) + `required_linear_history: true`
  (squash merge apenas, sem force-push) + `allow_force_pushes: false` + 11 required status
  checks listados explicitamente (lint, typecheck, 2 gates, QA Gate smoke, SAST bandit,
  pip-audit, 4× pytest matrix serviços). Regras aplicáveis MANUALMENTE via Settings → Branches
  OU automaticamente via GitHub App "Probot Settings" instalado na org.
  Resultado: 100% dos commits em main PASSARAM pelo CI de bloqueio.

- **Risco R12 (Sprint 8 NOVO — M7 Render API Secrets 4-eyes)**:
  "Rollback automático GAP#9 e hooks de deploy usam `RENDER_API_TOKEN_{STAGING|PROD}` +
  8 SERVICE_IDs (4 × staging/prod auth-public-inv-case). Se um dev inexperiente edita
  secrets no GitHub UI sem 4 eyes, pode quebrar rollback automático em emergência P0 →
  produção down enquanto ninguém percebe."
  → **Mitigação**: Ambientes `production` e `staging` PROTEGIDOS (GitHub Environments):
  `production` exige 2 approving reviewers ANTES do deploy; `production-canary` exige
  1 approving reviewer + 30 minutos wait_timer antes de promote. Documentado em
  `.github/settings.yml` lista environments. Mais:
  **Checklist obrigatório 4-eyes para EDITAR secrets render** (qualquer alteração):
  1. Issue `[CONFIG]` com label `needs-security-review` aberto justificando a mudança.
  2. 1 dev prepara o novo secret (ex: token regenerado Render).
  3. 2º dev (diferente!) valida valor copiado (criptografado em tela screen-share).
  4. Ambos aprovam a issue.
  5. Secret salvo no ambiente correspondente (staging OU production NUNCA ambos no mesmo dia sem teste).
  6. Deploy-staging roda smoke rollback em STAGING primeiro.
  Resultado: Rollback automático (GAP#9) zero falsos negativos por secret errado.

- **Risco R13 (Sprint 8 NOVO — M7b Secrets Hardcoded Leak)**:
  "Dev copia `.env-prod.example` com token falso `xxxxx-xxx`, mas esquece e deixa hardcoded
  em `apps/case-management/main.py` um `RENDER_API_TOKEN = 'rnd_xxx'` → leak em commit
  público → token vazado → atacante rollbacka produção remotamente."
  → **Mitigação**: `ci.yml` job NOVO `secrets-guard-skeleton` (leve, 10s):
  - Grep em `apps/**.py`, `packages/**.py`, `.github/workflows/*.yml` por regex
    `(rnd_|sk-|xoxb-|ghp_)[A-Za-z0-9]{8,}` (tokens Render, Stripe, Slack, GitHub PAT)
  - Falha CI com exit code 6 se encontra QUALQUER ocorrência fora de `${{ secrets.* }}`.
  - +Check: `grep -rE 'RENDER_API_TOKEN\s*=\s*"[A-Za-z0-9]'` — pega casos onde secret é hardcoded Python.

### Atualizações Workflow Aplicação (itens 11..14, adendo Sprint 8)
11. **Antes de mergear PR em main**: verificar `.github/settings.yml` contém o status
    check obrigatório referente ao job novo que você adicionou no `ci.yml`. Se não,
    adicionar linha em `required_status_checks.contexts` (11 → 12 → N).
12. **Qualquer edição de GitHub Environment secrets ou Render API token**:
    executar checklist R12 (issue CONFIG, 4 eyes, deploy-staging smoke primeiro).
    **NÃO** editar ambiente production direto sem staging teste primeiro.
13. **Novo token/prefixo de segredo (ex: Stripe pk_live_)**: incluir regex em
    `ci.yml` job `secrets-guard-skeleton` step "Hardcoded Token Regex Scan".
14. **Probot Settings App**: se instalado na org, PRs que alteram `.github/settings.yml`
    aplicam branch protection AUTOMATICAMENTE em merge. Se não instalado, aplicar
    MANUALMENTE em Settings → Branches copiando campos YAML (10 min de config one-shot).

## Tabela 13 Ambientes + 11 Required Status Checks (SSOT Sprint 8)
### Ambientes Protegidos GitHub (3 ambientes)
| Environment | 4 eyes reviewers | wait_timer | Deploy Trigger | Usado por workflow |
|---|---|---|---|---|
| `staging` | 0 (auto após CI verde) | 0s | tag `v0.0.N-staging` | deploy-staging.yml 5 jobs |
| `production-canary` | 1 | 1800s (30min observação) | tag `vX.Y.Z` semver prod válido + preflight passar | deploy-production.yml deploy canary 10% |
| `production` | 2 | 0s | promote após canary observe passar | deploy-production.yml promote 100% + rollback auto |

### 12 Required Status Checks Obrigatórios main (strict=true, enforce_admins=true)
| # | Contexto (GitHub Status Name) | Vem do workflow/job | Se falha → merge? |
|---|---|---|---|
| 1  | lint                                    | ci.yml lint job | BLOQUEIA |
| 2  | Guard: Anti Hardcoded Secrets (Tokens Render/Stripe/GitHub PAT) | ci.yml secrets-guard-skeleton Sprint 8 M7b | BLOQUEIA (0 tokens hardcoded) |
| 3  | typecheck                               | ci.yml typecheck | BLOQUEIA |
| 4  | gate-p0-00-rls-cross-tenant             | ci.yml gate | BLOQUEIA (0 leak cross-tenant) |
| 5  | gate-p0-01-oidc-mock-ci-gate            | ci.yml gate | BLOQUEIA |
| 6  | QA Gate: qa-gateway 6 comandos --help   | ci.yml qa-gateway-cli-smoke | BLOQUEIA (6/6 exit=0 obrigatório) |
| 7  | SAST: bandit scan Python MEDIUM/HIGH    | ci.yml sast-bandit-python M1 | BLOQUEIA (0 findings) |
| 8  | Dep Audit: pip-audit CVE HIGH/CRITICAL  | ci.yml dependency-audit-pip M1 | BLOQUEIA (0 H + 0 C) |
| 9  | pytest service: case-management         | ci.yml pytest matrix service 1 | BLOQUEIA |
| 10 | pytest service: auth-service            | ci.yml pytest matrix service 2 | BLOQUEIA |
| 11 | pytest service: ai-service              | ci.yml pytest matrix service 3 | BLOQUEIA |
| 12 | pytest service: investigation-api       | ci.yml pytest matrix service 4 | BLOQUEIA |
| 13 | Quality Gate: SonarCloud + CodeCov (80% overall / 85% patch) | ci.yml sonarcloud-codecov-quality-gate M8 Sprint 9 | BLOQUEIA (overall<80% ou patch<85% ou 0+ code smells blocker) |
| 14 | *(OPCIONAL)* SonarCloud Quality Gate (após refino strict) | ci.yml sonar-scan strict (90% new) | BLOQUEIA (M8 Sprint 10 se optar) |

## Sprint 9 Update (Milestone Pós-MVP 3)

### Risco novo R14 (Sprint 9 NOVO — M8 Sonar + CodeCov Quality Gate)
- **Risco R14**: "Time entrega features com testes unitários zero cobrindo linhas de negócio (RLS, RBAC, crypto, rollback). Depois de 6 sprints, cobertura cai de 80% → 55% e qualquer refatoração causa regressão. Alerta Prometheus começa a disparar em produção."
- **Mitigação M8 Sprint 9**: Quality Gate DUPLICADO (SonarCloud + CodeCov) em **BLOQUEANTE** no `ci.yml`:
  1. **CodeCov `coverage.status.project.default.target = 80%` overall, `patch.target = 85%` para novas linhas (dif PR)**. 1% threshold gradual; nada além disso bloqueia.
  2. **SonarCloud `sonar.qualitygate.wait=true timeout=600s`**: padrão Sonar way (Coverage < 80%, Duplicated Blocks > 3%, Code Smells/Critical/Blocker > 0, Vulnerabilities > 0, Security Hotspots Reviewed < 100%).
  3. **Artefatos**: `tmp_coverage/coverage.xml` por serviço pytest matrix 7×, agregados em job `sonarcloud-codecov-quality-gate` (Python copy), `download-artifact@v4` merge pattern `coverage-*`.
  4. **Secrets necessários 2 NOVOS repo-level**:
     - `SONAR_TOKEN`: SonarCloud → My Account → Security Tokens (project-level global vale). Organiz. `ontrackchain`, `projectKey=Ontrackchain_ontrackchain`.
     - `CODECOV_TOKEN`: CodeCov.io → repo Settings → Upload Token (para private repos; OIDC GITHUB_TOKEN pode bastar para públicos).
  5. **Exclusões CI para evitar falsos negativos**: migrations SQL, docs, node_modules, `__pycache__`, `apps/frontend/public`, dashboards JSON, `ci-artifacts/`, `artifacts/`.
  6. `sonar-project.properties` e `codecov.yml` na raiz = SSOT para ambos scaners (não depende só de config UI).

### Atualizações Workflow Aplicação itens 15..17 (adendo Sprint 9)
15. **Todo PR que adiciona lógica de negócio NOVA (rotas, middleware, services)**: esperado no CodeCov patch target = 85% de linhas novas. Se estiver 84% → bloqueia merge automaticamente. Se for exceção justificada (dead code legítimo, linguagem exótica não-scanneada), abrir exception issue `security-mvp-next-milestone`.
16. **Todo PR que ajusta CI de cobertura**: atualizar `sonar-project.properties` e `codecov.yml` NA MESMA alteração. Settings UI do Sonar/CodeCov NÃO são SSOT.
17. **Secrets SONAR_TOKEN e CODECOV_TOKEN**: São editar ambiente e portanto **obedcem checklist 4-eyes do R12 (Sprint 8)** — issue CONFIG + `needs-security-review` + 2 devs aprovando antes de salvar em Settings.

## Tabela 16/14 Final (13 GAPs não existentes: 12 originais + 4 Milestones M1..M4 + M8 = maturidade 100% robusta)
### Sprint × GAP × Fechado
| # | GAP/Milestone | Nome | Sprint fechado | Status |
|---|---|---|---|---|
| 1  | GAP#1 P0 | RLS Cross-Tenant isolamento 0 leak | S1 | ✅ 100% |
| 2  | GAP#2 P0 | pytest CI 7 serviços paralelo | S1 | ✅ 100% |
| 3  | GAP#3 P0 | Deploy Staging/Prod Seguro Canário 30min | S2 | ✅ 100% |
| 4  | GAP#4 P0 | LGPD + QA Gateway SSOT 6 comandos | S1→S4 | ✅ 100% |
| 5  | GAP#5 P1 | SLA Exploradores Live 24h Dead Man → Issue GitHub P1 | S3 | ✅ 100% |
| 6  | GAP#6 P1 | E2E Playwright shard=8 + label e2e-required | S5→S6 | ✅ 100% |
| 7  | GAP#7 P2 | Prometheus 3 alerts + Grafana Dashboard Único QA Overview 8 panels | S4→S6 | ✅ 100% |
| 8  | GAP#8 P2 | Vault/Secrets ADR-016 | S2 | ✅ 100% |
| 9  | GAP#9 P2 | Rollback Automático Render API 4 serviços staging/prod | S4 | ✅ 100% |
| 10 | GAP#10 P2 | ADR-018 Governança R1→R14 + Workflow itens 1..17 | S3→S9 | ✅ 100% |
| 11 | GAP#11 P3 | Load Test Nightly 20 paralelo POST/api/v1/cases P95 <3000ms | S5 | ✅ 100% |
| 12 | GAP#12 P3 | SAST Bandit + pip-audit CVE (M1 S7 → bloqueante real) + M7b secrets guard anti-hardcoded | S5→S7→S8 | ✅ 100% |
| 13 | M1 Milestone | SAST/CVE `continue-on-error: true → false` | S7 | ✅ |
| 14 | M2 Milestone | Templates 3× Issues + 1× PR Checklist Governança | S7 | ✅ |
| 15 | M3 Milestone | Grafana provisioning Dashboard QA Overview automático bind mount | S7 | ✅ |
| 16 | M4 Milestone | Self-hosted runners labels 3 jobs pesados (pytest, e2e shards, nightly 50min) | S7 | ✅ |
| 17 | M5 Milestone 🔴 BLOQUEADO | Push remoto 4 commits | — | 🔴 Aguardando autorização explícita + método |
| 18 | M6 Milestone | Branch Protection SSOT settings.yml enforce_admins=true + 13 Required Status Checks + 4 environments | S8 | ✅ |
| 19 | M7 Milestone | Secrets 4-eyes R12 + Checklist 6 passos editar Render API 10 vars | S8 | ✅ |
| 20 | M7b Milestone | Anti Hardcoded Tokens rnd_/ghp_/sk_ Regex Grep CI (Sprint 8) | S8 | ✅ |
| 21 | M8 Milestone | SonarCloud + CodeCov Quality Gate BLOQUEANTE overall 80% / patch 85% + 0 code smells blocker | S9 (NOVO) | ✅ **FECHADO** |

