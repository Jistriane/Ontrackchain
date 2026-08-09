# Changelog — Ontrackchain

> Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
> Convenção de versionamento: [Semantic Versioning 2.0.0](https://semver.org/lang/pt-BR/)
>
> **Estrutura hierárquica por Sprint** (agrupamento canônico Ontrackchain). Cada Sprint = uma
> release de plataforma. Componentes internos (frontend, apps/*, packages/*) evoluem com
> seu próprio semver, documentado em cada entrada.

---

## [v5.6.0] — Sprint 22 (projetado em 2026-08-09)

### Adicionado (3 frentes)

- **P1-05 Changelog releases hierárquico oficial (S1→S22)**: arquivo `CHANGELOG.md` no formato
  Keep a Changelog 1.1.0 + SemVer 2.0.0, com entradas por Sprint e links para commits SHA locais.
- **T2-09 Billing Stripe multi-tenant BRL/USD/EUR**: módulo `billing-api/src/billing_api/stripe_integration.py`
  novo com 5 endpoints (criar sessão checkout, portal de assinatura Customer Portal, preços
  por moeda, webhook assinaturas invoice.paid, cancelamento). 3 moedas suportadas:
  BRL (Real Brasil), USD (Dólar Americano), EUR (Euro). Webhook assinatura HMAC `whsec_`.
- **Q3-04 Load Testing k6 4 rotas críticas**: 4 scripts k6 em `tests/k6/`:
  `01-public-api-b2b-screening.js` (HMAC-SHA256 header auth, 50 VUs, 5min),
  `02-structural-screening-onboarding.js` (compliance-api structural, 30 VUs, 3min),
  `03-case-management-create-case.js` (RBAC ANALYST create case, 60 VUs, 4min),
  `04-all-healthz-smoke.js` (smoke 10 VUs 1min paralelo todos serviços).

### Alterado

- `README.md` versão snapshot atualizada de `v5.5.0` → `v5.6.0 Sprint 22`
- Tabela Consolidado +3 entradas S22-P105 / S22-T209 / S22-Q304

---

## [v5.5.0] — Sprint 21 (2026-08-08) · SHA **`7d153b3`**

### Adicionado

- **T2-05 Frontend v2.0.0 Graph Intelligence 4.0 Cytoscape.js**
  ([app/graph/page.tsx](./ontrackchain/apps/frontend/app/graph/page.tsx)):
  - 6 layouts: CoSE, Cola Force-Directed, ForceAtlas2, Grid, BFS Hierárquico, Concêntrico
  - 9 filtros de categoria de nó + toggle "Apenas Risco"
  - 5 KPIs Metric Cards + Top 5 Betweenness Centrality
  - 4 Sinais Prioritários ALERTA/ALTO/MÉDIO/BAIXO + 3 ações recomendadas por IA
  - SSR disabled via `next/dynamic({ssr:false})` obrigatório para Cytoscape DOM
- **Error Boundary segmento /graph**
  ([app/graph/error.tsx](./ontrackchain/apps/frontend/app/graph/error.tsx))
- **Playwright spec Q3-04 Graph Intelligence**: 7 testes E2E em
  ([graph-intelligence-t205.spec.ts](./ontrackchain/apps/frontend/tests/e2e/graph-intelligence-t205.spec.ts))
- **4 ADRs NOVOS (Governança Arquitetura Formal)**:
  - [ADR-019 B2B HMAC Monetização v2.0.0](./ontrackchain/docs/adrs/ADR-019-public-api-v2-b2b-hmac-authentication-monetization.md)
  - [ADR-020 Error Boundaries + WCAG AA Loading Skeletons a11y](./ontrackchain/docs/adrs/ADR-020-frontend-nextjs-error-boundaries-wcag-aa-loading-skeletons.md)
  - [ADR-021 Structural Screens RIPD LGPD Art.15](./ontrackchain/docs/adrs/ADR-021-compliance-api-structural-screens-lgpd-ripd-art15.md)
  - [ADR-022 Graph Intelligence 4.0 Cytoscape](./ontrackchain/docs/adrs/ADR-022-graph-intelligence-4-cytoscape-counterparty-wallet-risk-network.md)

### Alterado

- **`docs/adrs/README.md`**: índice atualizado 18 → 22 ADRs (ADR-001 a ADR-022)
- **`project-executive-readiness-brief.md` Baseline v1.0 → v1.1**:
  materialidade regulatória BACEN/LGPD 78% → 90%

### Versões internas componentes

| Componente | Versão Sprint 20 → Sprint 21 |
|---|---|
| Frontend (Next.js) | `1.9.0` → **`2.0.0` (MAJOR, feature nova Graph)** |
| Número ADRs governança | 18 → **22** (ADR-019 / 020 / 021 / 022) |

---

## [v5.4.0] — Sprint 20 (2026-08-07) · SHA **`f40626a`**

### Adicionado

- **T2-04 compliance-api v2.2.0 Structural Screens LGPD RIPD Art.15**
  ([structural_screens.py](./ontrackchain/apps/compliance-api/src/compliance_api/structural_screens.py)):
  Módulo NOVO SRP separado, 7 endpoints CRUD:
  1. `POST /screening-onboarding` (201 Created, mask LGPD `** MASKED **`)
  2. `GET /screening-onboarding/{id}`
  3. `POST /due-diligence` (overall_assessment monotônico 4 níveis)
  4. `GET /due-diligence/{dd_id}`
  5. `POST /source-of-funds` (9 tipos de origem de fundo)
  6. `GET /source-of-funds/{sof_id}`
  7. `GET /work-items-blueprint` (catálogo público 4 work items OBRIGATÓRIOS Art.15 I,II,IV,V)
- **T2-03 qa-gateway CLI v3.2.0 scan-rbac STRICT MODE warnings→errors**:
  flags `--strict/--no-strict` default STRICT=True, `--max-warnings N` default 0.
  NOVA FASE W WARNINGS estruturais 4 códigos: RBAC-W001 (serviços bypass), W002 (ZERO writes),
  W003 (<3 writes baixa cobertura), W004 (DB skip). Modo STRICT: warnings→issues + exit=1 bloqueia merge.
- **Q3-02 Hypothesis fuzzing compliance screens property-based** em
  ([test_fuzzing_compliance_screens_q3_02.py](./ontrackchain/apps/compliance-api/tests/test_fuzzing_compliance_screens_q3_02.py)):
  6 testes, **DUAL MODE fallback stdlib seed=1337 determinístico**. hypothesis instalado: 1050 combinações;
  fallback: 1000 combinações + manuais.

### Fecha GAP / Risco

- ✅ **Fecha Risco R-05 LGPD RIPD Art.15 Due Diligence Estruturado (prob ALTA × impacto MUITO ALTO)**

### Versões internas componentes

| Componente | Versão Sprint 19 → Sprint 20 |
|---|---|
| compliance-api | `2.0.0` → **`2.2.0` (MINOR)** |
| qa-gateway | `3.1.0` → **`3.2.0` (MINOR)** |

---

## [v5.3.0] — Sprint 19 (2026-08-07) · SHA **`c50bcf0`**

### Adicionado

- **T2-01 public-api v2.0.0 B2B Enterprise Monetização**
  ([main.py L349-L685](./ontrackchain/apps/public-api/src/public_api/main.py#L349-L685)):
  - Autenticação **HMAC-SHA256 timing-safe** 3 headers: `X-OT-Client-Id`, `X-OT-Timestamp` (skew max 300s anti-replay), `X-OT-Signature`
  - Documento assinatura: `METHOD|path|base64(body)|timestamp`
  - 4 endpoints B2B: webhook register, evidence package lacrado SHA-256, case-status SIEM, keys rotate 7d grace
  - Rate limiter Redis Business 2000 req/h, Enterprise 10.000 req/h
  - 21 testes contrato (9 legacy + 12 B2B novos)
- **T2-06 Frontend v1.9.0 WCAG AA + Error Boundaries Next.js App Router**
  ([app/error.tsx](./ontrackchain/apps/frontend/app/error.tsx) + 4 segmentos dashboard/cases/ai/evidence):
  7 arquivos Next.js App Router Error Boundary + Loading Skeletons shimmer + not-found.tsx 404 navegável
- **Q3-03 Playwright +4 specs E2E críticos auditoria regulatória (38 → 42 specs)**:
  `investigation-complete-flow`, `ai-insights-analyst-dashboard`, `case-management-lifecycle`,
  `evidence-package-sealed-b2b`
- **Acessibilidade a11y**: suíte `@axe-core/playwright` 4 testes WCAG 2.1 AA login/dashboard/cases/tabnav

### Versões internas componentes

| Componente | Versão Sprint 18 → Sprint 19 |
|---|---|
| public-api | `0.1.0` → **`2.0.0` (MAJOR launch B2B)** |
| Frontend | `0.1.0` → **`1.9.0` (MINOR)** |

---

## [v5.2.0] — Sprint 18 (2026-08-06) · SHA **`b2f3ab8`** (15 commits ahead)

### Adicionado

- **T2-07 Helm Chart Ontrackchain Platform v3.1.0 PG Backup Diário CronJob**: 63→65 manifests.
  NOVO template `05-backup-cronjob.yaml`: `0 4 * * *` UTC (01:00 BR), `pg_dump -Fc`, retenção 14d,
  PVC `restricted-dados-pessoais` + Velero annotations, PodSecurity strict restricted (runAsNonRoot UID 999,
  drop ALL caps, seccomp RuntimeDefault, RO FS). ConcurrencyPolicy=Forbid, ttl 7d.
- **T2-08 Monorepo Workspace Hatchling pyproject.toml editable**: `shared/qa-gateway/agents`
  como editable installs; `[tool.pytest.ini_options] pythonpath` 13 source/test dirs; `conftest.py`
  hierárquico auto-injetor PYTHONPATH. 5 sys.path.insert HACKs removidos; +48 são no-ops automáticos.
- **T2-02 CI P0-08 Dead Man Switch SLA bloqueante**: novo job `qa-gateway-scan-sla-ci-p008`
  3 modos: STRICT main/release → bloqueia merge; CI_DRY_RUN PRs → apenas reporta; DATA_NA → dummy fallback.

### Versões internas componentes

| Componente | Versão Sprint 17 → Sprint 18 |
|---|---|
| Helm Chart | `v3.0.0` → **`v3.1.0`** |
| CI gates bloqueantes | 16 → **17** |

---

## [v5.1.0] — Sprint 17 (2026-08-05) · 14 commits ahead origin/main

### Adicionado

- S16-Helm validação 3 bugs corrigidos (.helmignore paths, U+002D image tpl, L70 YAML parse).
- Traefik 3 réplicas PDB minAvailable=2 garantido HA.
- 63 manifests `helm template` válidos em staging homolog.

---

## [v5.0.0] — Sprint 14 a Sprint 16 (lançamento plataforma completa v5)

### Lançamento MAJOR (maior release da história do Ontrackchain)

| Frente Sprint 14 | Artefato |
|---|---|
| S14-M8 Helm v3.0.0 | 13 Deployments + 2 StatefulSets PG16/Prom + 11 PDB + 8 HPA + 3 NetPol LGPD = 63 manifests |
| S14-AI AI Service v4.1.0 | XAI, Risk Model, Graph 4.0, THEMIS, LEO Export, jobs `FOR UPDATE SKIP LOCKED`, 22 pytest |
| S14-OTK Federação Roles OTK_* | `canonicalize_role` shared + frontend authz.ts: OTK_ADMIN/ANALYST/COMPLIANCE/AUDITOR/VIEWER |
| S14-CI CI 16 Gates | Grype SBOM + OPA 4 policies + Secrets Guard + pytest matrix 4x + SonarCloud + Bandit + pip-audit |

### Sprints 15 e 16

- `P2-05` RBAC incremental enforcement 8 domínios team/reports/billing/investigate/compliance/alerts/counterparties/monitoring
- 80/80 testes E2E passando; navegacao global sensível a papéis
- `ROS/COAF` segregação REVIEWER vs COMPLIANCE_OFFICER

---

## [v4.x.0] — Sprints 1 a 13 (2026-06 a 2026-07)

> Nota: Período de construção inicial do MVP. Consulte:
> - [Tabela Consolidado completa](./README.md#consolidado) no `README.md`
> - [Avaliação de Status Datada 2026-07-03](./ontrackchain/docs/assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
> - [Governança Semanal Arquivo](./ontrackchain/docs/governance-weekly/archive/)

### Marcos iniciais (S1 a S13)

- **Sprint 1 — P0 Fundação Segura**: RLS PostgreSQL multi-tenant, Auth OIDC, 6 serviços FastAPI base
- **ADR-001 a ADR-013 aprovados** em governança arquitetura
- **Case Management + AI Service + Auth API + Evidence + Compliance + Public-api + Alerting** (7/9 serviços MVP)
- **Frontend 24 páginas Next.js 14 App Router**: cockpits dashboard, cases, ai, evidence, sanctions, alerts, counterparties, monitoring, audit, billing, team, reports, investigate, ros-coaf, enterprise-compliance, incident-response, oidc/callback
- **Keycloak OIDC MFA + PEP doméstico + OFAC/UN/UE triagem local**
- **S2-08 Retention Recovery Diário (LGPD Art.19)**: PG dump + Offsite Object Storage S3 + 3-2-1

---

### Convenção CHANGELOG Ontrackchain (como contribuir)

1. **NÃO edite versões antigas já commitadas** exceto para correções.
2. Quando entregar novo item em sprint:
   - Se é o primeiro item da sprint → CRIAR NOVA ENTRADA `[vX.Y.Z] Sprint N` topo do arquivo.
   - Se a entrada já existe → acrescentar em `## Adicionado` ou `## Alterado` ou `## Corrigido`.
3. Sempre documentar: (a) frentes (P1-05 / T2-09 / Q3-04), (b) arquivo com link absoluto, (c) versão semver interno componente quando alterado.
4. **Mantenha versões alinhadas ao label de release do README raiz**.
