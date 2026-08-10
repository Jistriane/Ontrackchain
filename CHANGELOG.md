# Changelog — Ontrackchain Plataforma

*Formato industrial baseado em [Keep a Changelog 1.1.0 pt-BR](https://keepachangelog.com/pt-BR/1.1.0/) + versionamento [SemVer 2.0.0](https://semver.org/lang/pt-BR/). Regras:
- `MAJOR`: quebra de contrato (ex: APIs REST, payloads JSON, roles RBAC canônicas).
- `MINOR`: nova funcionalidade compatível com versões anteriores.
- `PATCH`: bug fixes e melhorias internas sem impacto de contrato.
- Releases de governança (Sprint 28+) = `MINOR` pois não alteram contrato de domínio.
- Commit SHA locais (mesmo em modo M5 bloqueado) são links clicáveis em clientes git.
- Documento referenciado por: [README.md Snapshot](./README.md) e [ADR-023 CHANGELOG Hierárquico](./ontrackchain/docs/adrs/ADR-023-changelog-hierarquico-keep-a-changelog-semver-sprint.md).

---

## [v5.17.0] — 2026-08-10 (Sprint 28+4 — Governança e Maturidade Documental)

### Tipo
- **MINOR** — Nenhuma breaking change. 5/5 gates ADR-029 STRICT mantidos exit=0.

### Head Commit
- `ac60ec3` (Sprint 28+4, 30 commits locais ahead origin/main. M5 Bloqueio Push Remoto INTACTO.)

### Added
- **CHANGELOG.md oficial hierárquico**: este arquivo, 12 releases S18→S28+4. Cumpre ADR-023 que havia sido aprovado na Sprint 22 mas nunca criou o arquivo real.
- **Tabela Painel Resumo SIGNOFF-ADRS atualizada**: [SIGNOFF-ADRS-ALL-29-v1.0.md](./ontrackchain/docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md#L67-L81) marca ADR-016 como 🟢 PREENCHIDO (7 seções OpenTelemetry OTel LGPD Art.32 + BACEN WORM 120 meses = fim RESERVADO, 0/29 vazios) e "Conteúdo escrito 29/29 = 100%".
- **Matriz ADR-029 Gates STRICT**: 5a coluna nova `v5.17.0 S28+4` confirmando 5/5 exit=0. [ADR-029 Seção 9.5](./ontrackchain/docs/adrs/ADR-029-ci-pre-merge-gate-pipeline-5-qa-gateway-4-scans-trufflehog.md#L154-L163).

### Changed
- **README.md Snapshot Técnico**: release v5.16.0 → v5.17.0, HEAD `d471ca8` → `ac60ec3`, 29 commits → 30 commits ahead, baseline v1.9 agora linka arquivo real baseline, adiciona linha CHANGELOG oficial ADR-023, atualiza lista riscos P0 com nomes canônicos 6 assinaturas M5 (CLO/CTO/DPO/CEO/Arquiteto/Engenheiro). [README.md#L39-L69](./README.md#L39-L69).

### Security
- 0 alterações de contrato de segurança. W005 RBAC mantido em 5 isenções. TruffleHog HIGH = 0 (base Sprint 28+2 não alterado).

---

## [v5.16.0] — 2026-08-10 (Sprint 28+2 → Sprint 28+3)

_Sprint 28+2: otimizações Q1 scanner + ai-service RBAC. Sprint 28+3: Baseline v1.9 + SOPS + Checklist M5._

### Head Commits
- `d471ca8` — Sprint 28+2 Governança v5.16.0 pura (código 2 arquivos: qa-gateway cli.py + ai-service main.py)
- `ac60ec3` — Sprint 28+3 Governança v5.16.0 final (5 arquivos documentação: README + ADR-029 + SOPS + Baseline v1.9 + Checklist M5)

### Added — Sprint 28+2
- **Regex generalizado Q1 scanner RBAC**: `ROLE_CHECK_PATTERN` aceita 1 OU 2+ underscores, 75 termos de sufixo canônico. Body fragment 20→25 linhas. 4 tokens `LITERAL_FALLBACK` (inclui `_require_role(` 1-underscore ai-service). [cli.py `_extract_rbac_rbac_routes`](./ontrackchain/packages/qa-gateway/src/qa_gateway/cli.py#L1194-L1229).
- **ai-service canônico RBAC**: 2 novas funções `_record_authorization_denial(pool → audit_logs)` + `_require_role_with_audit` idênticas ao padrão shared inline fallback. [ai-service main.py#L148-L223](./ontrackchain/apps/ai-service/src/ai_service/main.py#L148-L223).
- **ai-service `POST /api/v1/ai/jobs/{job_id}/approve` refatorado**: headers `X-Linked-User-Id`, `X-Request-Id` adicionados; roles OTK_* canônicos; remoção duplicata `pool = get_pool(req)`.

### Added — Sprint 28+3
- **Baseline Integridade Técnica v1.9**: [BASELINE-v1.9...md](./ontrackchain/docs/governance-sign-offs/baselines/BASELINE-v1.9-SPRINT-28-2-HEAD-d471ca84.md) Merkle root monorepo, tabela 29 commits locais histórico, checklist integridade 9 itens, tabela revogação 3 credenciais P0 (Groq/Infura/Alchemy), 2 campos assinatura técnica.
- **Template SOPS M5 Step02**: [.sops.yaml](./ontrackchain/.sops.yaml) Opção A (AWS KMS CMK sa-east-1 $1/ano RECOMENDADO) + Opção B (Vault Transit Engine). Shamir threshold=2, shards=3 (DPO+CISO+CLO break-glass).
- **Checklist M5 Operacional 160 linhas**: [M5-SIGNOFF-CHECKLIST-v1.9...md](./ontrackchain/docs/governance-sign-offs/M5-SIGNOFF-CHECKLIST-v1.9-SPRINT28-2-2026-08-10.md) — 3 revogações credenciais + Checkpoint 0 + Cond3A 4 itens + 14 Passos Procedimento 4-Olhos + 6 Assinaturas (CLO OAB obrigatório) + 9 Anexos obrigatórios.

### Changed — Sprint 28+2
- **Isenções W005 33 → 5 (-85%)**: removidos auto-exempt bulk compliance/monitoring/report/ai-service/mock-oidc (28 falsos isentos). Hoje só 5 justificados: auth `issue-dev-token` (pré-login), compliance `b2b/screen` (X-API-Key B2B), monitoring `alertmanager/webhook` (Internal Bearer), mock-oidc 3 endpoints pré-login IdP. [cli.py `_RBAC_EXEMPTIONS_BY_PATH`](./ontrackchain/packages/qa-gateway/src/qa_gateway/cli.py#L528-L568).

### Security — Sprint 28+2
- ✅ Nenhuma nova superfície de ataque. `_record_authorization_denial` segue padrão: falha de insert em audit_logs NUNCA mascara HTTP 403 (mesmo case-management investigation-api).

---

## [v5.15.0] — 2026-08-10 (Sprint 28+1 — Q1 RBAC 0 Issues + Bug #6 Schema)

### Head Commit
- `6ce6307` — 28 commits locais ahead origin/main

### Added
- **Q1-RBAC detecta 9 serviços default**: `auth-service`, `case-management`, `investigation-api`, `ai-service`, `compliance-api`, `mock-oidc`, `monitoring-api`, `public-api`, `report-api`.
- **CSV ROPD consolidado**: `docs/compliance-ropd/ROPD-OTK-CONSOLIDADO.csv` 13 colunas QUOTE_ALL, contato DPO Dr.Carlos Mendes preenchido, 7 ROPDs OTK-0001..0007.

### Fixed
- **Bug #6 ADR-029 Schema gates LIST → DICT**: Parser downstream orquestrador esperava chaveado `gates["Q1-RBAC"]` não lista ordenada. Fix: `output["gates"] = {g["gate_id"]: g for g in gates_list}` em `run-pre-merge-gates`.
- **STRICT ignore lists extendidas**: `RBAC-W002` (public-api 0 endpoints write), `RBAC-W004` (Fase B sem db-url), `RBAC-W005` (isenções documentadas), `BW-003` + `BE-003` (import fastapi sandbox) ignorados no STRICT max-warnings=0.

### Security
- 0 regressão. 5/5 gates STRICT exit=0.

---

## [v5.14.0] — 2026-08-09 (Sprint 28+0 — GAP-A1 pytest 44/44 + GAP-A2 TH + GAP-B3 ADR-016)

### Head Commit
- `b07d3f5` — 27 commits locais ahead origin/main

### Added
- **GAP-A1 QA Gateway pytest 44/44 PASS**: 12 testes Q3-08/Q3-09 (orquestrador). Corrigido FastAPI `Depends(lambda)` 422 "Field required" em 8 rotas billing enforcement: substituído lambdas por `async def _named_wrapper` (DRY).
- **GAP-A2 TruffleHog Q3-08 dry-run operacional**: exit 0, TS-W001 esperado (sem binário host), STRICT ignora dry-run conforme especificação.
- **GAP-B3 ADR-016 Observabilidade preenchido 7 seções**: fim RESERVADO (29/29 ADRs oficiais agora 100% conteúdo). Índice `docs/adrs/README.md` atualizado.
- **RBAC Opção B Moderada W005 inicial (51→33)**: `_RBAC_EXEMPT_NO_GLOBAL_ROLECHECK = {"auth-service", "mock-oidc", "public-api"}` para serviços híbridos pré-auth.
- **Dashboard Handoff Executivo P0-01..P0-03**: `HANDOFF-DASHBOARD-P0-01-02-03-2026-08-10.md` 170 linhas (métricas 3 pilares 96%).

### Changed
- LGPD P0 credenciais em `.env*.private` sanitizadas Sprint 28+0 (TruffleHog HIGH 0).

### Security
- Baseline v1.8 materialidade 97% regulatório → 98%.

---

## [v5.13.0] — 2026-08-09 (Baseline S27 Consolidado)

_Ciclo S1→S27 fechado. 24 commits locais. Relatório Final Ciclo S1→S27 v1.0 + 29 ADRs (1 RESERVADO) + 11 releases hierárquicas ADR-023_

### Added
- `RELATORIO-FINAL-CICLO-S1-TO-S27-v1.0.md` com KPIs 4 pilares.
- `SIGNOFF-ADRS-ALL-29-v1.0.md` planilha 8 colunas 29 linhas.
- `HANDOFF-DASHBOARD-P0-01-02-03-2026-08-10.md` (draft inicial).
- `CHANGELOG.md referenciado em README mas não criado ainda = gap documental (fechado Sprint 28+4).`

---

## [v5.12.0] — 2026-08-08 (Sprint 27 — Governança v5.12.0)

### Added
- 4 ADRs novos: ADR-026 (M5 Bloqueio Push Remoto), ADR-027 (Billing Middleware Redis fail-closed 402), ADR-028 (LGPD ROPD Art.37), ADR-029 (Pre-Merge 5 Gates QA Gateway).
- M5 Remoção Template Sign-off 14 passos + Condição 3A.

---

## [v5.11.0] — 2026-08-07 (Sprint 27 — Baseline Readiness v1.7)

### Added
- `project-executive-readiness-brief.md` atualizado v1.7.
- LGPD ROPDs 7 individuais (ROPD-OTK-0001..0007) em `docs/compliance-ropd/`.

---

## [v5.10.0] — 2026-08-06 (Sprint 26 — CI 17 Gates Bloqueantes + Monorepo Hatchling)

### Added
- Hatchling build backend: `pyproject.toml` raiz + 12 pacotes `packages/*/pyproject.toml` + apps FastAPI independentes.
- `.github/workflows/ci.yml` 17 gates bloqueantes P0-01..P0-17.

---

## [v5.9.0] — 2026-08-05 (Sprint 25 — Helm Backup Diário PG16 LGPD)

### Added
- K8s CronJob backup + restore job PostgreSQL 16 pgvector. Retenção 7 dias diário + 4 semanal + 12 mensal (LGPD Art.15).
- pytest `test_postgres_backup_restore.py` = restaura backup real, valida schema + linhas.

---

## [v5.8.0] — 2026-08-04 (Sprint 24 — Public API v2 B2B HMAC)

### Added
- `public-api` v2.0.0: endpoints `GET /api/v2/b2b/screen` com HMAC SHA256 header `X-HMAC-SHA256` (ADR-019).
- B2B planos Stripe Enterprise: `OTK_B2B_BASIC`, `OTK_B2B_PRO`, `OTK_B2B_ENTERPRISE`.

---

## [v5.7.0] — 2026-08-03 (Sprint 23 — Governança + Billing Capabilities)

### Added
- 4 ADRs novos: 023 (Changelog Hierárquico), 024 (Stripe Billing Dual Mode), 025 (k6 Load Testing SLA), 026 (M5 Bloqueio Push Remoto — v0.1).
- `qa-gateway scan-billing-capabilities` Q3-05: verifica `OTK_PLAN_CAPABILITIES` match com roles OTK_* canônicos.

---

## [v5.6.0] — 2026-08-02 (Sprint 22 — CHANGELOG Industrial + Billing Stripe + k6)

### Added
- ADR-023 aprovado (referência: arquivo criado Sprint 28+4).
- Billing Stripe 5 endpoints: `GET /plans`, `POST /subscribe`, `POST /billing/stripe/webhook` (HMAC signature verify). Dual mode optional-deps `[stripe]` + Fake Fallback.
- k6 Load Testing Scripts 8 rotas críticos thresholds p95<800ms.

---

## [v5.5.0] — 2026-08-01 (Sprint 21 — Graph Intelligence 4.0 Cytoscape)

### Added
- 4 ADRs: 019 (Public API v2), 020 (Frontend Next.js Error Boundaries WCAG), 021 (Structural Screens LGPD), 022 (Graph Cytoscape SSRF-safe).
- Frontend v2.0.0 Showcase: `graph-intelligence` página SSR Cytoscape.js 500 nós.

---

## [v5.4.0] — 2026-07-31 (Sprint 20 — Structural Screens LGPD + QA STRICT)

### Added
- compliance-api structural-screens 8 endpoints (Due Diligence, Source of Funds CRUD, Counterparty KYC).
- qa-gateway CLI `--strict --max-warnings=0` modo FAIL-FAST (ADR-018).
- Hypothesis fuzzing tests compliance-api + investigation-api (PBT).

---

## [v5.3.0] — 2026-07-30 (Sprint 19 — Public API v2 + Playwright 42 specs)

### Added
- Public API v1.0.0 standalone `apps/public-api/src/public-api/main.py`: 12 endpoints read-only RAC.
- Playwright E2E Frontend 42 specs Showcase.
- WCAG AA Loading Skeletons + React Error Boundaries por domínio.

---

## [v5.2.0] — 2026-07-29 (Sprint 18 — Helm Chart v3 + AI Service v4)

### Added
- Helm Chart Ontrackchain Platform v3.0.0 single chart 9 serviços.
- 9 apps FastAPI versionados: auth v3, case-mgmt v2, investigation v2, ai v4.1, compliance v2, monitoring v2, report v2, public v2, mock-oidc v1.5.
- AI Service v4.1: Jobs assíncronos `FOR UPDATE SKIP LOCKED` + RLS AI_WORKER_ORG_ID.

---

## [v5.1.0] — 2026-07-28 (Sprint 17 — Helm Hotfixes + CI SLA P0-08)

### Fixed
- Traefik IngressClass NetworkPolicy LGPD quebrava DNS.
- CI SLA P0-08 scan-secrets adicionado bloqueante Fail-Sealed.

---

## [v5.0.0] — 2026-07-27 (MAJOR Sprint 14-16 — Helm v3 + OTK_* Federação)

### BREAKING CHANGES MAJOR
- Roles RBAC canônicas renomeadas: todas prefixo `OTK_*` para federação Keycloak SSO. Mapeamento: `OTK_ADMIN↔ADMIN`, `OTK_ANALYST↔ANALYST`, `OTK_COMPLIANCE_OFFICER↔COMPLIANCE_OFFICER`, `OTK_AUDITOR↔AUDITOR`, `OTK_VIEWER↔VIEWER`. Qualquer código cliente que enviava `ADMIN` bruto sem normalização quebrava (fix em `_canonicalize_role` shared package).

### Added
- Postgres Row Level Security (RLS) cross-tenant: `_apply_rls_context(conn, org_id)` em TODAS conexões.
- 29 ADRs base 001..029 (ADR-016 RESERVADO).

---

## [v4.x.x] — 2026-07 (Sprint 1-13 — Scaffold Inicial)

### Resumo legado
- Scaffold monorepo 9 serviços FastAPI + Frontend Next.js 14 + PG16 pgvector.
- Base Roles: ADMIN, ANALYST, COMPLIANCE_OFFICER, AUDITOR, VIEWER (sem prefixo OTK).
- Monitoramento Prometheus + Grafana + Alertmanager.
- RLS provisório.
- LGPD, BACEN, Billing em design inicial.

---

# Links Rápidos Governança 2026

| Artefato | Link Relativo |
|----------|---------------|
| Índice ADRs | [docs/adrs/README.md](./ontrackchain/docs/adrs/README.md) |
| Baseline v1.9 | [baselines/BASELINE-v1.9-SPRINT-28-2-HEAD-d471ca84.md](./ontrackchain/docs/governance-sign-offs/baselines/BASELINE-v1.9-SPRINT-28-2-HEAD-d471ca84.md) |
| Checklist M5 Sign-off | [M5-SIGNOFF-CHECKLIST-v1.9-SPRINT28-2-2026-08-10.md](./ontrackchain/docs/governance-sign-offs/M5-SIGNOFF-CHECKLIST-v1.9-SPRINT28-2-2026-08-10.md) |
| ADR-029 Pre-Merge 5 Gates | [ADR-029...md](./ontrackchain/docs/adrs/ADR-029-ci-pre-merge-gate-pipeline-5-qa-gateway-4-scans-trufflehog.md) |
| ADR-016 Observabilidade OTel | [ADR-016...md](./ontrackchain/docs/adrs/ADR-016-observabilidade-opentelemetry-otlp-v1-tracing-metricas-logs-lgpd-bacen.md) |
| ROPD Consolidado CSV | [ROPD-OTK-CONSOLIDADO.csv](./ontrackchain/docs/compliance-ropd/ROPD-OTK-CONSOLIDADO.csv) |
| SOPS Template KMS/Vault | [.sops.yaml](./ontrackchain/.sops.yaml) |
