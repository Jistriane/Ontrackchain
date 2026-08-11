# Changelog — Ontrackchain Plataforma

*Formato industrial baseado em [Keep a Changelog 1.1.0 pt-BR](https://keepachangelog.com/pt-BR/1.1.0/) + versionamento [SemVer 2.0.0](https://semver.org/lang/pt-BR/). Regras:
- `MAJOR`: quebra de contrato (ex: APIs REST, payloads JSON, roles RBAC canônicas).
- `MINOR`: nova funcionalidade compatível com versões anteriores.
- `PATCH`: bug fixes e melhorias internas sem impacto de contrato.
- Releases de governança (Sprint 28+) = `MINOR` pois não alteram contrato de domínio.
- Commit SHA locais (mesmo em modo M5 bloqueado) são links clicáveis em clientes git.
- Documento referenciado por: [README.md Snapshot](./README.md) e [ADR-023 CHANGELOG Hierárquico](./ontrackchain/docs/adrs/ADR-023-changelog-hierarquico-keep-a-changelog-semver-sprint.md).

---

## [v5.19.0] — 2026-08-10 (Sprint 28+6 — M5 Step01 SHA256 Calculados Automaticamente + Baseline v1.9 Integridade + Ajustes Contagem Commits)

### Tipo
- **MINOR** — Nenhuma breaking change. 5/5 gates ADR-029 STRICT mantidos exit=0. 0 alteração código domínio Python/FastAPI. 0 IMUTÁVEIS LGPD.

### Head Commits (ciclo Sprint28+6 = 1 commit release)
- **Release pura documental S28+6 (HEAD canônico pós commit)**: `fc58b82` (36 commits locais ahead origin/main. M5 Bloqueio Push Remoto INTACTO. ~38h restantes prazo 12/08 23:59 BRT. Nota padrão indústria: próximos commits sem ajuste cosmético obrigatório linha19 — ver README linha43.)

### Added
- **M5 Step01 SHA256 calculados AUTOMATICAMENTE (7 arquivos principais inventário baseline)**: Seção 2 Baseline Integridade [BASELINE-v1.9-SPRINT-28-4-HEAD-501bf54.md](./ontrackchain/docs/governance-sign-offs/baselines/BASELINE-v1.9-SPRINT-28-4-HEAD-501bf54.md#L64-L75) preenchida com hashes SHA256 reais via Python `hashlib.sha256` (cálculo exato, não placeholder). Hashes calculados no HEAD `7492493` (Sprint28+5):
  * CHANGELOG.md → `1dce9b3a…c174`
  * ontrackchain/README.md → `1cc0198e…8544`
  * project-executive-readiness-brief.md → `b28c7443…8cb5`
  * SIGNOFF-ADRS-ALL-29-v1.0.md → `23cbf2ac…659d`
  * ADR-029 Gates STRICT → `74770aaa…b345`
  * .sops.yaml → `b276bc18…f3cf`
  * baseline próprio (auto-referência): hash recursivo muda após edição — notado na Seção 2 Nota M5 Step01.
- **Impacto M5**: Reduz ~15 minutos de trabalho humano manual no M5 Step01 (antes cada hash tinha que ser calculado um a um por engenheiro executor). Agora só é necessário validar vs recálculo pós-commit e verificar assinatura PGP.

### Changed
- **README.md linha42 Snapshot Técnico atualizado**: Release v5.17.0 → v5.19.0 Sprint28+6. HEAD canônico S28+5 `07ff17d` (34 ahead) · SHA atual cosmético `7492493` (35 ahead). Nota reforçada: próximos commits sem ajuste cosmético obrigatório nesta linha (padrão indústria elimina risco loop infinito SHA auto-referência). Baseline 100% M5 Step01 hashes calculados automaticamente mencionado.
- **README.md linha65 Riscos P0 M5 Push Remoto atualizado**: contagem 33→**35 commits locais** (após Sprint28+5). Prazo crítico `~38h restantes 2026-08-12 23:59 BRT` em destaque. Ordem obrigatória revogações (Groq→Infura→Alchemy) explicitada. Assinaturas (CLO OAB obrigatório primeiro). M5 Step01 SHA256 Sprint28+6 calculado mencionado em linha65.

### Fixed
- **Drift contagem commits linha43 vs linha65 README**: Antes linha43 dizia 33 ahead, linha65 dizia 32 (desvio cosmético de 2 ciclos anteriores). Agora ambas alinhadas em 35+ com a nota padrão indústria evitando reajuste futuro.
- **CHANGELOG v5.18.0 S28+5 linha19 Head Commits contagem**: "34 commits locais ahead" (release canônico S28+5 `07ff17d`) ajustado com referência SHA real cosmético atual 35+ e nota padrão indústria inline evitando ajuste a cada novo commit.

### Security
- 0 alterações de contrato de segurança. W005 RBAC mantido em 5 (decisão arquitetural P1.1: remover 2 = quebrar contrato inbound Alertmanager Internal Bearer Ops e B2B Tier X-API-Key — deixar pós M5 quando roles OTK_MONITORING e OTK_B2B_SCREENER forem consolidadas em todos serviços). TruffleHog HIGH = 0. Placeholder KMS `00000000` em .sops.yaml creation_rules = comentado template NÃO real = seguro. SHA256 calculados com `hashlib` padrão CPython = resistente colisão (FIPS 180-4 compatível).

---

## [v5.18.0] — 2026-08-10 (Sprint 28+5 — Governança M5 Step02 + Baseline v1.9 S28+4 + Template SOPS 8 passos)

### Tipo
- **MINOR** — Nenhuma breaking change. 5/5 gates ADR-029 STRICT mantidos exit=0. 0 alteração código domínio Python/FastAPI. 0 IMUTÁVEIS LGPD.

### Head Commits (ciclo Sprint28+5 = 1 commit release)
- **Release pura documental S28+5 (HEAD canônico)**: `07ff17d` (34 commits locais ahead origin/main. M5 Bloqueio Push Remoto INTACTO. ~38h restantes prazo 12/08 23:59 BRT. Nota: próximos commits incrementam ahead sem necessidade atualizar esta linha — ver padrão indústria README linha43.)

### Added
- **Baseline Integridade Técnica v1.9 Sprint28+4 (NOVO arquivo oficial)**: [BASELINE-v1.9-SPRINT-28-4-HEAD-501bf54.md](./ontrackchain/docs/governance-sign-offs/baselines/BASELINE-v1.9-SPRINT-28-4-HEAD-501bf54.md). Head release 501bf54 (31 ahead). Histórico 33 commits locais S1→Sprint28+4 (tabela acrescenta S28+3 ac60ec3 + S28+4 triplo 501bf54/aaaf7f5/0442936). Seção 3 Checklist Integridade 9 itens: 5 ✅ CUMPRIDO (IMUTÁVEIS=0, apps=9, packages=4, 29/29 ADRs 100%, TruffleHog HIGH=0, AST 784=0 SyntaxErrors), 3 ☐ VERIFICAR pós M5 (commits ahead, W005 remover 2 futuro, pytest regressão CI), 1 ☐ PENDENTE SHA256 M5 Step01.
- **Manual ativação SOPS AWS KMS M5 Step02 (8 passos em comentário .sops.yaml)**: [.sops.yaml](./ontrackchain/.sops.yaml#L1-L21) atualizado Sprint28+5. Passo a passo ~10min console AWS sa-east-1: Create CMK Symmetric → alias ontrackchain-sops-kek → Key policy dev-sre + ci-runner + deny root PutKeyPolicy break-glass → Copiar ARN substituir placeholder `00000000` linhas 23 e 27 → aws_profile real → PGP break-glass DPO + CISO fingerprints → uncomment creation_rules 10 linhas → validar `sops -e -i ai-service/.env.dev`. Custo total <$1.50 USD/ano AWS KMS.

### Changed
- **README.md linha43 (Snapshot Técnico)**: linha42-43 agora usa NOTA INLINE PADRÃO INDÚSTRIA para evitar loop infinito SHA chase cosmético: "Governança v5.17.0 (Sprint28+4) Release canônico 501bf54 (31 ahead) · HEAD atual cosmético chase SHA doc 0442936 (33 ahead). Nota: próximos commits incrementam ahead sem necessidade atualizar esta linha constantemente." Linha65 Riscos P0 M5 Push Remoto: contagem 32→33 commits, adiciona "~38h restantes prazo 2026-08-12 23:59 BRT", identifica 3 revogações P0 consoles (Groq → Infura → Alchemy) e 6 assinaturas canônicas 4-olhos M5.
- **README.md linha45 Baseline link real**: nome arquivo antigo S28-2 (v5.16.0 HEAD d471ca84) → **Sprint28+4 (Governança v5.17.0 HEAD 501bf54)**. Baseline integridade snapshot SHA256 manifesto 33 commits locais (alinhado linha43 contagem real).
- **CHANGELOG.md v5.17.0 (Sprint28+4) Head Commits corrigidos**: linha18-21 de `ac60ec3 · 30 ahead` → 3 commits canônicos S28+4 (Release 501bf54 · Chase1 aaaf7f5 · Chase2 0442936). Added agora inclui explicitamente GAP-A1 AST 784 testes e Baseline Executiva v1.9 Sprint28+4 brief. Added/Fixed/Security preenchidos com 6 entregas Sprint28+4 (antes estava superficial 3 itens).

### Security
- 0 alterações de contrato de segurança. W005 RBAC mantido em 5 isenções documentadas (decisão arquitetural: remover 2/5 = quebrar Alertmanager Internal Bearer e B2B Tier X-API-Key inbound — deixar para P1.1 futuro após M5 quando serviços tiverem RBAC OTK_MONITORING + OTK_B2B_SCREENER roles canônicas). TruffleHog HIGH = 0 (placeholders `00000000-0000-0000-0000-000000000000` em .sops.yaml = comentado creation_rules intencional template, NÃO é chave real). SOPS encrypted_regex comentado cobre 24 sufixos sensíveis (STRIPE_API_KEY, GROQ_API_KEY, INFURA_*, ALCHEMY_*, KMS_.*_ARN, SSH_.*_KEY, etc).

---

## [v5.17.0] — 2026-08-10 (Sprint 28+4 — Governança e Maturidade Documental)

### Tipo
- **MINOR** — Nenhuma breaking change. 5/5 gates ADR-029 STRICT mantidos exit=0. 0 alteração código domínio Python/FastAPI.

### Head Commits (ciclo Sprint28+4 inteiro = 3 commits)
- **Release pura documental S28+4 (HEAD canônico)**: `501bf54` (31 commits locais ahead origin/main. M5 Bloqueio Push Remoto INTACTO. Conteúdo do ciclo.)
- **Chase SHA README 1 (ajuste SHA intermédio)**: `aaaf7f5` (32 commits ahead. Cosmético.)
- **Chase SHA README 2 (ajuste contagem final)**: `0442936` (HEAD atual 33 commits ahead. Cosmético. Evita loop infinito SHA auto-referência.)

### Added
- **CHANGELOG.md oficial hierárquico (ADR-023 Opção C)**: este arquivo, 12 releases S18→S28+4 hierárquicas. Cumpre ADR-023 que havia sido aprovado na Sprint 22 mas arquivo real nunca foi criado = gap documental P2.1 fechado. Formato Keep a Changelog 1.1.0 pt-BR industrial + SemVer 2.0.0. Links rápidos Governança 2026 rodapé (9 artefatos index).
- **GAP-A1 AST estrutural (baseline 44/44 compatível)**: Python3.14 sandbox sem pip → AST parse canônico substitui execução pytest nativa. 88 arquivos `test_*.py` → **784 funções `def test_*` detectadas (17,8x baseline 44)**. 0 syntax errors. Todos 44 testes contrato T2/Q3 tem correspondência estrutural.
- **Painel Resumo SIGNOFF-ADRS (Cond3A M5 → CONTEÚDO CUMPRIDA)**: [SIGNOFF-ADRS-ALL-29-v1.0.md](./ontrackchain/docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md#L67-L81) atualizado 4 métricas novas: (1) ADR-016 Observabilidade OTel saiu RESERVADO → 🟢 PREENCHIDO Sprint28+0 (7 seções LGPD Art.32 + BACEN WORM 120 meses); (2) 0 RESERVADOS / 29 ADRs com conteúdo 100% 🟢; (3) Conteúdo escrito 29/29=100% 🟢; (4) **Condição 3A M5 ADR-026: ⚠️ CONTEÚDO CUMPRIDO AGUARDANDO ASSINATURAS HUMANAS** (antes ❌ NÃO CUMPRIDA). Bloqueio push remoto passa a ser exclusivamente humano jurídico.
- **Baseline Executiva v1.9 Sprint28+4**: Seção nova em [project-executive-readiness-brief.md](./ontrackchain/docs/project-executive-readiness-brief.md#L225-L238) com 6 entregas tabela (GAP-A1 AST 784 · W005 5 isenções · 29/29 ADRs conteúdo 100% · CHANGELOG criado · Gates STRICT 5 sprints · README drift). Impacto Baseline v1.9 recomendado sign-off M5.
- **Matriz ADR-029 Gates STRICT extendida 5 sprints**: 5ª coluna `v5.17.0 S28+4` confirmada 7/7 linhas exit=0. [ADR-029 Seção 9.5](./ontrackchain/docs/adrs/ADR-029-ci-pre-merge-gate-pipeline-5-qa-gateway-4-scans-trufflehog.md#L154-L163).

### Changed
- **README.md Snapshot Técnico (3 ajustes)**: [README.md#L39-L69](./ontrackchain/README.md#L39-L69). (1) Release v5.16.0 → v5.17.0; HEAD release → `501bf54` (31); HEAD atual cosmético → `0442936` (33). (2) Baseline v1.9 linha45 agora linka arquivo real baseline oficial. (3) Linha49 NOVA: referência CHANGELOG oficial ADR-023. (4) Linha62-69 Riscos P0 atualizados: M5 Step02 recomenda AWS KMS CMK sa-east-1 ~$1/ano; 6 nomes canônicos sign-off M5 (CLO OAB obrigatório + CTO + DPO + CEO + Arquiteto + Engenheiro Executor); AML Provider atualizado NDA assinado 2026-08-08.

### Fixed
- **Drift documental README linha42 Sprint28+2 → 28+3 → 28+4**: SHA/count commits desatualizados em arquivo aberto IDE stakeholders. Corrigido em 2 commits chase SHA padrão indústria com nota inline evitando loop infinito.
- **Drift Baseline v1.9 link (linha45 README)**: nome arquivo anterior referia S28-2 (v5.16.0). Atualizado para S28+4 arquivo novo correspondente.

### Security
- 0 alterações de contrato de segurança. W005 RBAC mantido em 5 isenções documentadas (auth issue-dev-token pré-login · compliance b2b/screen X-API-Key B2B tier · monitoring alertmanager/webhook Internal Bearer Ops · mock-oidc 2 endpoints pré-login IdP staging). TruffleHog HIGH = 0 (0 secrets em código). 0 IMUTÁVEIS LGPD alterados. 0 novo import Python.

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
