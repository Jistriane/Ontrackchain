# Changelog

Todas as mudanças notáveis ​​neste projeto serão documentadas neste arquivo.

Formato baseado em [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
com **hierarquia por Sprint (maior unidade semântica Ontrackchain)** — cada Sprint agrupa `[Added]`, `[Changed]`, `[Deprecated]`, `[Removed]`, `[Fixed]`, `[Security]`.
Versionamento segue **[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)** no release (vX.Y.Z) por Sprint.

*Último arquivo consolidado: Sprint 27, 2026-08-10. Compila Sprints 1→26 (26 releases).*

---

## [v5.11.0] - 2026-08-10 — Sprint 27: Governança Consolidado (CHANGELOG + Assinatura 29 ADRs + Workflow Pre-Merge pronto para sign-off M5) — *Última Sprint ciclo CÓDIGO*

### Added
- CHANGELOG.md S1→S26 hierárquico oficial (cumpriu ADR-023 que descreveu o formato mas nunca criou o arquivo).
- `docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md` — Assinatura consolidado jurídico 29 ADRs linha por linha (ADR 001..029) para Diretor Jurídico/CLO. Campos: Data, ADR ID, Nome, Status (Aprovado/Rejeitado/Pendente Justificativa), Assinatura, Email.
- `.github/workflows/pre-merge-gates.yml` — Workflow GitHub Actions **trigger desativado `on: []`** (workflow_dispatch manual exclusivo para quando sign-off M5 acontecer). Steps: checkout v4, Python 3.11, pip install qa-gateway local, **1 linha**: `qa-gateway run-pre-merge-gates --dpo-email="${{ vars.DPO_EMAIL }}" --report-dir ./qa-reports`. Optional upload-artifact v4 de `./qa-reports` retention-days=180 (mínimo LGPD 6 meses).
- Baseline Executivo project-executive-readiness-brief.md v1.5 → v1.6: 98% → 99% regulatório/operacional. Próximo passo 99%→100% = P0-01 OIDC credenciais reais (8-21 dias úteis), P0-02 AML live provider (7-14 dias úteis), P0-03 sign-off M5 real (1-3 dias jurídicos). NENHUMA outra linha de código necessária.
- README.md v5.10.0 → v5.11.0 + 3 linhas Tabela Consolidado S27-CHANGELOG / S27-GOV-SIGNOFF / S27-ADR029-WORKFLOW. M5: commits ahead origin/main 22 → 23.

### Security
- Nenhuma alteração de código de domínio. Ciclo de implementação de features ONTRACKCHAIN 100% ESGOTADO em S27. Próximos commits = apenas sign-offs jurídicos, auditorias externas, credenciais, push remoto.

---

## [v5.10.0] - 2026-08-09 — Sprint 26: ADR-029 Pre-Merge 5 Gates FAIL-FAST + LGPD RIPD Art.15 Master + Template B2B Cliente + qa-gateway Q3-08 scan-secrets-trufflehog + Q3-09 run-pre-merge-gates + 12 pytest contrato (Baseline v1.5 97%→98%)

### Added
- ADR-029 7 seções + flowchart LR Mermaid Pre-Merge 5 Gates. 3 alternativas: A) Actions inline ❌ / B) script shell ❌ / C ORQUESTRADOR qa-gateway ✅. DoD 029.1..029.8. Índice ADRs 28→29.
- `docs/compliance-ripd/RIPD-OTK-MASTER-v1.0.md` 16 campos obrigatórios ANPD CD-004/2023 (ID, Controladora, Responsável Legal, DPO, Natureza 6 operações, Finalidade Art.7 III/V/II/VII, Categorias titulares PF/PJ × 5, Dados pessoais tokenizados CPF/CNPJ, Dados sensíveis saúde/racial/biométrico YubiKey NUNCA genético/religião, Destinatários RBAC+BACEN+SCCs AML, Transferência internacional SCCs UE, Base legal soma 100%, Medidas Art.32 TLS1.3 AES256 Istio WAF SIEM Vault, Retenção 36/60/120 meses, Destruição Soft30d+HardVACUUMFULL+Cert SHA256 DPO+CLO, Assinaturas 4 obrigatórias DPO+CLO+CEO+Arquiteto validade 12 meses).
- `docs/compliance-ripd/TEMPLATE-RIPD-POR-CLIENTE-B2B.md` mestre 16 campos + **SEÇÃO 17 ESPECÍFICA CLIENTE**: 17.1 Setor, 17.2 Volume titulares/ano, 17.3 Biometria flag SIM consentimento Art.22, 17.4 Nível Risco ANPD, 17.5 Fluxos partilha webhook mTLS cliente, 17.6 Vigência contrato, 17.7 ID contrato+anexo DPA SCCs, 17.8 Próxima revisão 12 meses.
- qa-gateway Q3-08 NOVO `scan-secrets-trufflehog`: helpers _find_trufflehog_bin (PATH/~/.local/bin/usr/local/bin/homebrew), _parse_trufflehog_json_lines Verified=true, _finish_trufflehog STRICT. 3 Issues TS-E001 bin falt / TS-E002 timeout 2h / TS-E003 segredo verificado prefixo raw 32 NÃO full leak. 3 Warnings TS-W001 dry-run bin não / TS-W002 stderr filtros / TS-W003 exit!=0 sem findings rede.
- qa-gateway Q3-09 NOVO `run-pre-merge-gates` ADR-029. Flags dpo-email obrigatório. OTK_CI_PRE_MERGE_ENFORCE_ALL=true bloqueia --skip-q*. Fail-FAST Q1→Q2→Q3→Q4. **Q5 SEMPRE roda (segredos > fail-fast tempo)**. JSON SCHEMA v1.0 `./qa-reports/pre-merge-${SHA}.json` 15 campos auditoria BACEN. Exit !=0 → bloqueia PR sys.exit(1).
- 12 pytest contrato `test_scan_secrets_trufflehog_and_premerge_q3_08_q3_09.py`: 8 Q3-08 (dry bin/sem, 0 findings, timeout, 2 findings, warnings overflow, no-fail-verified) + 4 Q3-09 (dry schema 1.0, ENFORCE_ALL bloqueia, fail-fast Q1→Q234 skips Q5 roda, Q5 bloqueia).

### Security
- Q5 SEMPRE roda mesmo se Q1 RBAC quebrar. Risco P0 segredos > risco de gastar 20-40 min TruffleHog desnecessariamente.
- Parser issues/warnings filhos não armazena raw completo de segredos detectados (prefixo 32 chars apenas) para evitar revictimizar leak dentro do próprio qa-report JSON.

---

## [v5.9.0] - 2026-08-08 — Sprint 25: LGPD ROPD Art.37 7 Operações + Billing Enforcement Integrado 8 Rotas Reais + qa-gateway Q3-07 scan-lgpd-ropd + Template Sign-off M5 Governança Risco (Baseline v1.4 96%→97%)

### Added
- ADR-028 LGPD Art.37 ROPD Registro Operações Tratamento Dados Pessoais 7 seções. 3 alternativas (Excel / Tabela PG / Markdown+CSV+Git). DoD 028.1..028.6. Índice ADRs 27→28.
- `docs/compliance-ropd/` 7 arquivos individuais ROPD OTK-0001..0007: Onboarding triagem RIPD Art.15; B2B HMAC Public API v2; AI LLM Análise Documental; OIDC MFA WebAuthn YubiKey; Billing Stripe Cadastro Invoice; Feed PEP OFAC Interpol UE Tokenizado; AML KYT Chainalysis TRM Elliptic.
- `ROPD-OTK-CONSOLIDADO.csv` 8 linhas (header+7 ops) × 13 colunas, delimitador ; padrão pt-BR Excel, 12 campos obrigatórios ANPD CD-005/2023 + coluna DPO extra.
- 4 NOVOS routers SRP feature-based investigation-api: ai_service.py (/analyze 1 AI, /summarize-docs 3 AI); public_b2b_v2.py (POST screening 429 hourly, GET entity/{id}); users_org.py (POST invite max_users startup=5 + regex OTK_* roles); graph_intelligence.py (POST layout valida SSOT allowed layouts 403 GRAPH_LAYOUT_NOT_ALLOWED NÃO incrementa counter).
- Investigation-api main.py include_router dos 4 routers novos. POST /estimate ganhou Depends enforcement amount=2 AI; POST /start ganhou Depends amount=5 AI. Total 8 rotas enforcement T2-12 ativas.
- pyproject investigation-api bump v1.4.0 → v1.5.0 (Feature release enforcement integrado).
- 16 pytest `test_enforcement_integrated_t2_12.py` 8 rotas × (200 sucesso business tier / 402 ou 429 ou 403 overflow). Monkey patch InMemoryBillingCounter padrão S24 T2-11.
- qa-gateway NOVO subcomando Q3-07 `scan-lgpd-ropd`. 5 warnings LR-001 pasta / LR-002 <7 arquivos / LR-003 CSV faltante / LR-004 <12 campos obrigatórios por arquivo / LR-005 DPO ausente. 3 issues E001 campo falt / E002 CSV <12 col / E003 Art.7 ausente. Helper _finish_ropd strict default true max-warnings=0 warnings→issues exit=1.
- NOVO `docs/governance-sign-offs/TEMPLATE-M5-removal-sign-off.md` 5 blocos: 0 Regras; 1 Info básicas (data, motivo, ahead count, método, janela 48h); 2 Condição 3A pré-requisitos TODOS SIM (TruffleHog 0 secrets HIGH, método seguro NÃO basic auth, sign 4-olhos SIM); 3 Procedimento 14 passos (snapshot criptografado, git clean, git fetch + ahead confirm, IMUTÁVEIS 0, qa-gateways 4 scans, TruffleHog, auth, push, verificar 0 ahead, notificar time, salvar doc commit); 4 Assinaturas 4-olhos CTO/DSI/CEO/Arquiteto; 5 Engenheiro executor declaração responsabilidade individual CLT/LGPD Art.43 §4. Válido 48h após assinatura; depois NOVO sign-off.

### Security
- Billing enforcement 8 rotas reais agora fail-closed. Antes era enforcement teórico (módulo billing_enforcement existia mas NENHUMA rota usava). Agora AUTH → HMAC → BILLING → BUSINESS ordem garantida.
- M5 sign-off proibição push remoto absoluto. Sem 4 assinaturas + 14 passos + condição 3A → commit fica local indefinidamente.

---

## [v5.8.0] - 2026-08-07 — Sprint 24: Billing Enforcement Middleware Redis Fail-Closed 402 + qa-gateway Q3-06 scan-billing-enforcement + Handbook OIDC Keycloak v25 Helm Self-Hosted 14 itens 4-Olhos + ADR-026 sign-off update (Baseline v1.3 95%→96%)

### Added
- ADR-027 Billing Capabilities Enforcement Middleware Redis DUAL MODE Fail-Closed 402. 3 alternativas (Direct PG / Redis + InMemory opcional / Shared Counter service). DoD T2-11. Índice ADRs 26→27.
- investigation-api billing_enforcement.py NOVO SRP: 2 counters DUAL MODE Redis (optional-deps [billing-redis]) + InMemory time.monotonic() TTL. Função `Depends(enforce_capability("b2b_hourly_quota" | "ai_credits" | "max_users_per_org", amount=...))`. Result HTTP 429 Too Many Requests / 402 Payment Required / 200. Middleware global headers X-RateLimit / X-Billing / X-Response-Time-Ms EM TODAS respostas. Fail-closed: 402 + log CRITICAL [BILLING-FAILCLOSED] se counter indisponível. NUNCA fail-open.
- 15 pytest contrato test_billing_enforcement_t2_11.py: 4 InMemory counter (incr monotônico get reset TTL expire); 7 enforce capability (sucesso business, 429 startup B2B, 402 AI enterprise 999.999+2, 402 max users, FailingCounter 402 critical, org None warn, factory fallback); 4 Headers billing global (sucesso 5, 402 tem headers, startup remaining 2500, Reset epoch futuro).
- qa-gateway NOVO Q3-06 subcomando scan-billing-enforcement. 4 warnings BE-001 módulo aus / BE-002 middleware aus / BE-003 monotonicidade SSOT AI strict cresc / B2B cresc / BE-004 prod obriga OTK_REDIS_URL overlays Helm. 2 Issues E001/E002 monotonicidade quebrada. Flags --check-prod-redis default true, --skip-prod-redis. Strict default true max-warnings 0.
- Handbook P0-01 OIDC Keycloak v25 Helm Self-Hosted 14 itens checklist 4-olhos P0-01.01..14: realm otk-realm banner LGPD; 4 clients PKCE token 15min; MFA WebAuthn YubiKey 3 roles; roles OTK_* client level; SAML IdP-initiated enterprise; LDAP AD memberOf sync; Helm 3 réplicas + PG Patroni SEPARADO investigation; Istio mTLS STRICT; Cloudflare WAF auth DDoS; SIEM Splunk 180d; backup 6h RPO 6h RTO 2h; Prometheus alertas P0; Playwright E2E Q3-07 futuro; sign off 4 CTO/DSI/DPO/Arquiteto. Diagrama Mermaid ordem 14 passos. 4 riscos mitigação. Previsão handoff 8–21 dias úteis.
- ADR-026 M5 Nova seção Sign-off: PENDENTE JURÍDICO / CONSELHO EXECUTIVO. CTO/DSI/CEO/Arquiteto campos data. Assinatura deve estar em docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md FORA do corpo do ADR.
- Baseline v1.3 95%→96%. Índice ADRs 25→27. Commits ahead origin/main 19→20.

### Security
- Redis billing primeiro connection failure: 402 + log CRITICAL (fail-closed). NUNCA continua negócio se billing indisponível → evita "uso grátis por engenharia social" outage Redis.
- Handbook OIDC MFA YubiKey 3 roles obrigatórias (OTK_ADMIN, OTK_COMPLIANCE_OFFICER, Auditoria) → cumpre BACEN Art. 12 16 controle de acesso por função.

---

## [v5.7.0] - 2026-08-06 — Sprint 23: Usage Meters Billing Capabilities SSOT 22×3 Tiers Startup/Business/Enterprise + qa-gateway Q3-05 scan-billing-capabilities STRICT + Governança Arquitetura +4 ADRs (023→026)

### Added
- ADR-023 CHANGELOG Hierárquico por Sprint Keep a Changelog 1.1.0 + SemVer 2.0.0.
- ADR-024 Billing Stripe Multi-Tenant DUAL MODE optional-deps [stripe] Fake fallback contrato idêntico (sem SDK real usa InMemory).
- ADR-025 Load Testing k6 Thresholds SLA Rigorosamente Definidos por Rota Crítica (investigation start ≤1500ms p95, AI analyze ≤3000ms p95, B2B screening ≤600ms p95).
- ADR-026 Bloqueio Absoluto Push Remoto M5 Governança Risco Condição 3A (TruffleHog 0 HIGH + método seguro PAT SSO / SSH deploy key / GitHub App + sign-off 4 olhos + Procedimento 14 passos). Índice ADRs 22→26.
- investigation-api billing_capabilities.py NOVO SRP APIRouter /api/v1/billing/capabilities + SSOT `OTK_PLAN_CAPABILITIES` 3 tiers: startup 5 users max, business B2B HMAC ilimitado, enterprise SSO SAML + AI credits 1M. 3 endpoints /matrix público 3×22, /my/{org_id} skeleton subscription, /my/{org_id}/rate-limit-headers demo X-RateLimit. Monotonicidade: AI estrita cresc, B2B estrita cresc, SSO só enterprise, startup 5 users.
- investigation-api pyproject bump v1.2.0 → v1.3.0. include_router main.py.
- 12 pytest contrato T2-10 billing capabilities.
- qa-gateway NOVO Q3-05 subcomando `scan-billing-capabilities`. 4 warnings BW-001 arquivo aus / BW-002 include_router aus / BW-003 import dyn SSOT monotonicidade / BW-004 T2-09 stripe pré-requisito. 4 issues E001 tiers aus / E002 monotonicidade quebrada / E003 enterprise sem SSO / E004. --strict default true max-warnings=0 warnings→issues exit=1.

---

## [v5.6.0] - 2026-08-05 — Sprint 22: Graph Intelligence 4.0 Cytoscape.js Counterparty↔Wallet↔Risk Network Multi-Layout Frontend + Graph layout APIs + SSRF Safe Fetch

### Added
- ADR-022 Graph Intelligence 4.0 7 seções. Cytoscape.js 11 layouts (cola, euler, concentric, breadthfirst, circle, dagre, cose-bilkent, spread, grid, klay, avsdf). Camadas: Contrapartes Nós PF/PJ, Carteiras BTC/ETH/ERC20 coloridas por risco, Arestas transação value USD.
- Frontend Graph Intelligence 4.0 componente `GraphCanvas.tsx` + hooks useCytoscapeLayouts.ts, useRiskColorScale.ts (vermelho #ef4444 alto, amarelo #f59e0b médio, verde #10b981 baixo).
- Investigation-api NOVO graph router `/api/v1/graph/layout` valida allowed layouts por tier (OTK_PLAN_CAPABILITIES[tier].graph_intelligence_layouts_allowed). Layout proibido → 403 GRAPH_LAYOUT_NOT_ALLOWED.
- SSRF Safe Fetch utilities `safe_fetch_graph_third_party(url, allow_private_ranges=False, timeout=2.0)` bloqueia IP privado 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 127.0.0.0/8 169.254.0.0/16 [::1] fc00::/7.

---

## [v5.5.0] - 2026-08-04 — Sprint 21: Compliance API Structural Screens RIPD Art.15 LGPD Due Diligence + Source of Funds CRUD + qa-gateway Q3-04 NOVOS casos teste Property-Based Hypothesis fuzzing 1000+

### Added
- ADR-021 Compliance API Structural Screens RIPD Art.15 LGPD 4 work items OBRIGATÓRIOS por contraparte nova (S20-STR-OBR-01 documentação PEP, 02 biográficos validados, 03 fonte fundos, 04 transacional primeiros 90 dias).
- compliance-api NOVO structural_screens.py 7 endpoints: POST /screening-onboarding (201 Created retorna 4 work items obrigatórios, documento MASKED LGPD RIPD Art.15 MASK), GET /work-items-blueprint público, PATCH /work-item/{id}, POST /source-of-funds, GET /entity/{id}/structural-dd, POST /risk-overall-monotonic (overall score monotônico NUNCA diminui após nova evidência), DELETE (soft delete).
- qa-gateway Q3-04 NOVOS 1000+ testes property-based Hypothesis determinísticos seed=1337 stdlib fallback se Hypothesis não instalado. Propriedades: score monotônico nunca diminui, máscara LGPD CPF sempre 3 primeiros + asteriscos + 2 últimos dígitos, documentação nunca vazia PEP, work-item obrigatório nunca uncheckable.

---

## [v5.4.0] - 2026-08-03 — Sprint 20: ADR-020 Frontend Next.js App Router Error Boundaries Global + Segmentos + WCAG AA Loading Skeletons a11y + Playwright E2E Q3-03

### Added
- ADR-020 Frontend Next.js 14 App Router. Error Boundary Global app/error.tsx, segmentos (dashboard, investigação, compliance, billing, admin, auth) cada com seu error.tsx + layout.tsx.
- Loading Skeletons página por página WCAG AA aria-busy=true role=status. Componentes SkeletonCard.tsx, SkeletonTable.tsx, SkeletonGraph.tsx.
- Playwright E2E Q3-03 NOVOS testes: login happy path, login MFA WebAuthn YubiKey, investigação create caso, structural screens PEP work item, billing capabilities, AI analyze. Contrato 40 testes E2E.

---

## [v5.3.0] - 2026-08-02 — Sprint 19: Public API v2.0.0 B2B Enterprise Autenticação HMAC-SHA256 Timing-Safe Anti-Replay Nonce + Rate Limit 200/2k/10k hourly tiers + API Blueprint OpenAPI 3.1

### Added
- ADR-019 Public API v2.0.0 HMAC-SHA256 Timing-Safe. Header X-OTK-Timestamp (±5min janel anti-replay), X-OTK-Nonce (Redis SET NX TTL 10min duplicate reject), X-OTK-Signature (HMAC-SHA256 hex).
- 4 endpoints v2 B2B: POST /screening (retorna match PEP/OFAC/Interpol score), GET /entity/{id}, POST /monitoring/subscription (webhook mTLS), GET /monitoring/alerts. Rate limit tiers: Startup 200/h, Business 2.000/h, Enterprise 10.000/h.
- OpenAPI 3.1 public-v2-openapi.yaml 9 schemas (ScreeningRequest, ScreeningMatch, Entity, MonitoringSubscription, Alert, Error, Pagination, RateLimitHeaders, HMACAuth).
- qa-gateway NOVO subcomando Q3-02 `scan-hmac-v2` para validar signatures local contra vetores de teste.

---

## [v5.2.0] - 2026-08-01 — Sprint 18: qa-gateway SSOT RLS Shared First / Fallback Inline NOVO 4 Gates RBAC/RIPD/Secrets/Billing + Diagrama 15 Gates CI Pipeline

### Added
- ADR-018 qa-gateway SSOT RLS Shared First Fallback Inline. 15 Status Checks pipeline pre-merge futuro.
- qa-gateway CLI 4 comandos iniciais: `scan rls --db-url ...` (valida tabelas x RLS + POLICY + INDEX), `health --endpoints ...` (health check paralelo timeout), `scan lgpd --dump-file ...` (CPF plaintext + chaves privadas regex).
- Helper `_exit_report` exit codes rigorosos (0 sucesso, 1 problema scan, 2 erro conexão infra, 3 parâmetro inválido, 4 arquivo não existe).

---

## [v5.1.0 - v1.0.0] — Sprints 17→1 Ciclo Inicial: Scaffold Arquitetura (ver tabela consolidado README v5.11.0 S1→S17 para resumo)

- **Sprint 17**: Billing Stripe T2-09 Customer Portal + Invoices PDF + Webhook signature verification.
- **Sprint 16**: AI Service v4.0 XAI Risk Model THEMIS LLM + jobs assíncronos 202 Accepted FOR UPDATE SKIP LOCKED.
- **Sprint 15**: Case Management v2.0.0 hub central casos scoring IA.
- **Sprint 14**: RBAC OTK_* 5 roles federação Shared First Fallback Inline AD-017.
- **Sprint 13**: Istio mTLS STRICT + Cloudflare WAF + SIEM Splunk 180d.
- **Sprint 12**: HashiCorp Vault secrets never plaintext + S3 Disaster Recover AES256 bucket policy SecureTransport.
- **Sprint 11**: k6 SLA Load tests ADR-025 precursor S23.
- **Sprints 10→7**: PG16 + pgvector, FastAPI, Next.js App Router scaffolding.
- **Sprints 6→1**: Monorepo scaffold, package structure (apps/, packages/, docs/), ADR estrutura inicial, README, .gitignore LGPD tokens .env*.private, M5 proibição push remoto inicializada.

---

### Tipos de Mudança Abreviatura (Keep a Changelog 1.1.0):
- `Added` para novas funcionalidades.
- `Changed` para mudanças em funcionalidades existentes.
- `Deprecated` para funcionalidades estáveis sendo removidas em breve.
- `Removed` para funcionalidades removidas nesta versão.
- `Fixed` para qualquer correção de bug.
- `Security` em caso de vulnerabilidades corrigidas ou controles de segurança adicionados.
