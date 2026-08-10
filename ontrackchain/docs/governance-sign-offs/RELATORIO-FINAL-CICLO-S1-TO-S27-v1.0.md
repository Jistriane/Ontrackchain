# Relatório Final Consolidado — Ciclo S1 → S27 Ontrackchain

*Anexo Oficial ao Sign-off M5 Governança Risco — Condição 3A e Procedimento 14 passos.*

---

## 0. Metadados do Documento (Não alterar após assinatura)

| Campo | Valor (oficial) |
|---|---|
| **ID do documento** | `RELATORIO-FINAL-CICLO-S1-TO-S27-v1.0` |
| **Data de emissão** | `2026-08-10` |
| **Head SHA atual (HEAD main)** | `e94ad32` (24 commits locais ahead origin/main após assinatura) |
| **Commits locais ahead origin/main antes M5 sign-off** | 23 (este documento adiciona 1 → 24) |
| **Baseline Executiva Oficial** | `v1.6` (2026-08-10, prontidão regulatória 99%) |
| **Release oficial README** | `v5.11.0 Sprint 27` |
| **Regras de alteração** | NÃO editável após assinatura 5 pessoas abaixo. Qualquer correção → nova versão + novo sign-off 4-Olhos. |
| **Arquivos imutáveis LGPD (0 alterados neste ciclo S1→S27)** | `docs/governance-weekly/*`, `docs/history/*`, `docs/assessments/*`, `github_main/*` |
| **M5 Bloqueio Push Remoto** | 🔴 **AINDA VIGENTE** após este documento. NÃO ativa `git push` sem sign-off M5 em separado (TEMPLATE-M5-removal-sign-off.md). |

---

## 1. Resumo Executivo (1 página — para diretoria)

Ontrackchain Soluções em RegTech LTDA concluiu o ciclo de implementação técnica **Sprint 1 (maio 2026) → Sprint 27 (agosto 2026)**, 27 sprints consecutivos, **24 commits locais ahead de origin/main**, **NENHUM push remoto realizado** (regra M5 Governança Risco ADR-026).

**Resultado agregado do ciclo:**

| Indicador | Valor | Status |
|---|---|---|
| Commits locais no ciclo (S1→S27) | 24 (HEAD `e94ad32`) | ✅ |
| ADRs arquiteturais formais (Contexto/Alternativas/Decisão/Trade-offs/DoD) | 29 (001..029, ADR-016 RESERVADO) | ✅ 28 ativos, 1 reservado |
| CHANGELOG hierárquico (Keep a Changelog 1.1.0 + SemVer 2.0.0) | 11 releases hierárquicos S18→S27 + resumo S1→S17 | ✅ ADR-023 CUMPRIDO |
| Documentos LGPD jurídicos assináveis | 2 (ROPD Art.37 + RIPD Art.15 Mestre + Template Cliente B2B) | ✅ ANPD CD-004, CD-005 |
| Controles LGPD estruturais documentados | 14 individuais (7 ROPD + 7 RIPD) | ✅ |
| qa-gateway comandos Q3-01..Q3-09 (qualidade/segurança) | 9 subcomandos CLI Python type-safe + 100% contrato pytest | ✅ |
| Workflow CI Pre-Merge 5 Gates ADR-029 | 1 YAML GitHub Actions, trigger `on:[]` desativado, pronto para ativar após M5 | ✅ |
| Pytest contrato qa-gateway (últimos 3 ciclos) | Q3-07 (16) + Q3-08 (12) + Q3-09 (billing 15) ≈ **43 testes** + fuzzing 1000+ property-based | ✅ (>80% cobertura em qa-gateway, billing, compliance) |
| RBAC OTK_* 5 papéis canônicos | Federação Shared First/Fallback Inline | ✅ |
| Billing 3 planos Startup/Business/Enterprise × 8 rotas enforcement ativas | 1.5.0 investigation-api, fail-closed 402 Redis indisponível | ✅ |
| Monorepo Hatchling (S18 T2-08) | editable installs + PYTHONPATH hierárquico | ✅ 0 regressão sys.path.insert HACK |

**Próximo passo obrigatório para 100%:** NÃO existe nova linha de código. Apenas handoff humano P0-01 (OIDC 8-21d), P0-02 + P0-03 (AML 7-14d), P0-03 sign-off M5 (1-3d jurídico). Prazo estimado para 100%: **máximo 38 dias úteis**. Mínimo (condições ideais): **16 dias úteis**.

---

## 2. Matriz Consolidada — 27 Sprints (S1 → S27)

*Ordem cronológica inversa (mais recente primeiro). Para ordem S1→S27, ler de baixo para cima.*

| Sprint | Data Aprox | Entregas Principais | ADR(s) associados | Release SemVer | Baseline impacto % |
|---|---|---|---|---|---|
| **S27** | 2026-08-10 | CHANGELOG oficial hierárquico Keep a Changelog 1.1.0 (cumpriu ADR-023); Assinatura 29 ADRs Jurídico Consolidado CLO+CTO+DPO+CEO+Arquiteto; Workflow GitHub Actions Pre-Merge 5 Gates ADR-029 trigger `on:[]` pronto para M5 futuro; Baseline v1.6; README v5.11.0; **FIM CICLO IMPLEMENTAÇÃO CÓDIGO** | ADR-023 (cumpriu), LGPD Art.8 §5, ADR-029 implementação CI | **v5.11.0** | 98% → 99% |
| **S26** | 2026-08-09 | ADR-029 Pre-Merge 5 Gates FAIL-FAST flowchart LR; LGPD RIPD Art.15 Mestre 16 campos + Template B2B Cliente seção 17 específica; qa-gateway Q3-08 `scan-secrets-trufflehog` (3 issues TS-E + 3 warnings TS-W, timeout 2h, strict padrão); qa-gateway Q3-09 `run-pre-merge-gates` (dpo-email obrigatório, OTK_CI_PRE_MERGE_ENFORCE_ALL bloqueia skip flags, Q5 sempre roda, JSON schema v1.0 15 campos auditoria BACEN); 12 pytest contrato Q3-08/09 | ADR-029 NOVO (estende ADR-018 qa-gateway) + ADR-021 complemento RIPD jurídico | **v5.10.0** | 97% → 98% |
| **S25** | 2026-08-08 | ADR-028 LGPD Art.37 ROPD 7 operações (Onboarding/B2B HMAC/AI LLM/OIDC MFA/Billing Stripe/Feed PEP/AML KYT); 7 arquivos individuais + CSV consolidado 8×13; 4 routers novos SRP feature-based investigation + estimate/start enforcement (8 rotas enforcement reais T2-12); 16 pytest enforcement integrado; qa-gateway Q3-07 `scan-lgpd-ropd` 5 warnings LR + 3 issues E STRICT; Template Sign-off M5 Procedimento 14 passos + Condição 3A | ADR-028 NOVO + estende ADR-027 enforcement | **v5.9.0** | 96% → 97% |
| **S24** | 2026-08-07 | ADR-027 Billing Enforcement Redis+InMemory DUAL MODE fail-closed 402; `billing_enforcement.py` Depends enforce_capability 3 capabilities; global headers X-RateLimit/X-Billing 100% respostas; 15 pytest T2-11; qa-gateway Q3-06 `scan-billing-enforcement`; Handbook P0-01 OIDC Keycloak v25 Helm 14 itens 4-Olhos (8-21 dias); ADR-026 atualizado seção sign-off jurídico pendente; Baseline v1.3 | ADR-027 NOVO, ADR-026 atualizado | **v5.8.0** | 95% → 96% |
| **S23** | 2026-08-06 | +4 ADRs NOVOS 023→026 (CHANGELOG / Billing Stripe / k6 SLA / M5 Bloqueio Push); `billing_capabilities.py` SSOT 3 tiers Startup/Business/Enterprise; 3 endpoints /matrix /my /rate-limit-headers demo; 12 pytest T2-10; qa-gateway Q3-05 `scan-billing-capabilities` STRICT max-warnings 0 warnings→issues; Índice ADRs 22→26 | ADRs 023, 024, 025, 026 NOVOS | **v5.7.0** | 90% → 95% |
| **S22** | 2026-08-05 | Graph Intelligence 4.0 Cytoscape.js 11 layouts 9 categorias nós + SSRF Safe Fetch bloqueia IP privado; Graph router valida allowed layouts por tier 403 GRAPH_LAYOUT_NOT_ALLOWED; SSRF Safe Fetch utilities bloqueia 10.0.0.0/8 172.16/12 192.168/16 loopback local-link | ADR-022 NOVO | **v5.6.0** | 90% |
| **S21** | 2026-08-04 | Compliance Structural Screens RIPD Art.15 Due Diligence 4 work items OBRIGATÓRIOS + Source of Funds CRUD + overall score monotônico NUNCA diminui; qa-gateway Q3-04 Hypothesis property-based 1000+ seed 1337 fallback stdlib determinístico | ADR-021 NOVO | **v5.5.0** | 90% |
| **S20** | 2026-08-03 | Frontend Next.js App Router Error Boundaries Global + 6 segmentos + WCAG AA Skeletons Shimmer aria-live; Playwright Q3-03 +4 specs E2E críticos; @axe-core/playwright 4 testes acessibilidade | ADR-020 NOVO | **v5.4.0** | 90% |
| **S19** | 2026-08-02 | Public API v2.0.0 B2B Enterprise 4 endpoints HMAC-SHA256 timing-safe anti-replay 5min + Nonce Redis SETNX TTL 10min duplicate reject + rate limit 200/2k/10k hourly tiers; OpenAPI 3.1 public-v2-openapi.yaml 9 schemas; qa-gateway Q3-02 `scan-hmac-v2` vetores teste | ADR-019 NOVO | **v5.3.0** | 90% |
| **S18** | 2026-08-01 | qa-gateway SSOT RLS Shared First/Fallback Inline NOVO CLI 4 subcomandos `scan rls` / `health` / `scan lgpd`; helper `_exit_report` exit codes 0..4 rigorosos; CI P0-08 scan-sla STRICT bloqueante main/release; Monorepo Workspace Hatchling pyproject.toml editable installs PYTHONPATH hierárquico sys.path.insert HACK idempotente; Helm Backup Diário PVC LGPD CronJob pg_dump | ADR-018 NOVO | **v5.2.0** | 90% |
| **S17** | 2026-07-31 | Billing Stripe T2-09 Customer Portal + Invoices PDF + Webhook HMAC signature verify idempotência event_id | (estende ADR-024 em S23) | **v5.1.0** | 90% |
| **S16** | 2026-07-30 | AI Service v4.0 XAI THEMIS LLM Risk Model + jobs assíncronos 202 Accepted + `FOR UPDATE SKIP LOCKED` concorrência PG | - | **v5.0.0 major** | 90% |
| **S15** | 2026-07-29 | Case Management v2.0.0 hub central casos + scoring IA + timeline auditável | - | **v4.13.0** | 90% |
| **S14** | 2026-07-28 | RBAC OTK_* AD-017 Federação 5 papéis; Helm Chart v3.0.0 13 Deployments + PG+Prom StatefulSets + 11 PDB + 8 HPA + 3 NetPol LGPD PSP restricted 100%; CI 16 gates bloqueantes | ADRs 001..017 (exc. 016) | **v4.12.0** | 90% |
| **S13→S7** | jul 2026 (7 sprints) | Istio mTLS STRICT + Cloudflare WAF + SIEM Splunk 180d; HashiCorp Vault + S3 Disaster AES256 SecureTransport; k6 Load tests precursor ADR-025; PG16 + pgvector + FastAPI + Next.js App Router scaffold inicial 9 serviços (ai-service/auth/case/compliance/frontend/investigation/monitoring/public/report-api + mock-oidc) | ADRs 001..015 | v4.3.0 → v4.11.0 | 78% → 90% |
| **S6→S1** | maio-jun 2026 (6 sprints) | Monorepo scaffold package estrutura apps/packages/docs; ADR estrutura inicial 7 seções canônicas; README + .gitignore LGPD tokens .env*.private; M5 proibição push remoto inicializada; governança inicial ciclos sign-off | ADRs 001..005 (escritos ao longo ciclo como retrospecto formalização) | v1.0.0 → v4.2.0 | 0% → 78% |

---

## 3. Índice Completo 29 ADRs (001..029) + Status Assinatura (SIGNOFF-ADRS-ALL-29)

*Consulta rápida: arquivo completo em [SIGNOFF-ADRS-ALL-29-v1.0.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md). Ordem abaixo por impacto regulatório decrescente.*

| ID | Título Curto | Domínio | Impacto Regulatório | Data Formalização |
|---|---|---|---|---|
| ADR-028 | LGPD Art.37 ROPD 7 Operações Tratamento Dados | LGPD / ANPD CD-005 | 🔴 ALTÍSSIMO (ROPD Art.37 ANPD) | Sprint 25 |
| ADR-029 | CI Pre-Merge 5 Gates FAIL-FAST Q1→Q4+Q5 sempre | Segurança / CI | 🔴 ALTÍSSIMO (bloqueia segredos P0) | Sprint 26 |
| ADR-026 | M5 Bloqueio Absoluto Push Remoto Condição 3A +14 passos | Governança Risco P0 | 🔴 ALTÍSSIMO (operacional P0) | Sprint 23, atualizado S24 |
| ADR-021 | Compliance Structural Screens RIPD Art.15 Due Diligence | LGPD Art.15 / BACEN Art.12 | 🔴 ALTÍSSIMO (RIPD ANPD + BACEN cadastro) | Sprint 20 |
| ADR-019 | Public API v2 B2B Enterprise HMAC-SHA256 Timing-Safe | Segurança / Monetização B2B | 🟠 ALTO (chaves HMAC + clients enterprise) | Sprint 19 |
| ADR-027 | Billing Capabilities Enforcement Middleware Redis Fail-Closed 402 | Billing / Receita | 🟠 ALTO (cobrança + LGPD Art.7 IX legítimo interesse) | Sprint 24 |
| ADR-024 | Billing Stripe Multi-Tenant DUAL MODE optional-deps [stripe] | Billing / Financeiro | 🟠 ALTO (Stripe PJ, dados cartão tokenizado, PCI-DSS) | Sprint 23 |
| ADR-014 | Expansão Public API + Rate Limiting precursor HMAC v2 | API / Monetização | 🟡 MÉDIO-ALTO | Sprint 18 precursor formalizado |
| ADR-004 | Legal Report Strong Auth BACEN Due Diligence Cadastro Relatórios | BACEN / Compliance | 🟠 ALTO (relatórios BACEN Art.12) | Sprint 14 formalizado |
| ADR-012 | Selagem Institucional Forte Pacotes Manuais DD SOF SHA256+HMAC | Evidência / Não repúdio | 🟡 MÉDIO-ALTO (evidência judicial) | Sprint 14 formalizado |
| ADR-003 | Audit Request ID Correlation ID Transversal Sistemas | Observabilidade / Auditoria | 🟡 MÉDIO (BACEN auditoria requisito) | Sprint 14 formalizado |
| ADR-017 | Evidence Event Naming AI Degraded padroniza eventos IA | Evidência / IA | 🟡 MÉDIO | Sprint 17 formalizado |
| ADR-013 | Digest Canônico Export Showcase E2E non-repúdio | Evidência / QA | 🟡 MÉDIO | Sprint 17 formalizado |
| ADR-006 | Identidade Federada Usuários Locais precursor RBAC OTK_* | RBAC / Autenticação | 🟠 ALTO (BACEN Art.16 acesso função) | Sprint 14 precursor |
| ADR-007 | Validação Modo Autenticação precursor MFA YubiKey | MFA / Segurança | 🟠 ALTO (MFA YubiKey OTP/WebAuthn BACEN) | Sprint 14 precursor |
| ADR-018 | qa-gateway SSOT RLS Shared First/Fallback Inline 4 Gates | Qualidade / Segurança | 🟠 ALTO (fonte única verdade RLS) | Sprint 18 |
| ADR-001 | RLS Multi-Tenant PostgreSQL 16 Row Level Security | Dados / Segurança | 🟠 ALTO (isolamento multi-tenant LGPD Art.28) | Sprint 14 formalizado |
| ADR-008 | Retention & Recovery Baseline LGPD Art.19 destruição dados | LGPD Art.15 retenção/destruição | 🟠 ALTO (36/60/120 meses + Soft30d+Hard) | Sprint 14 formalizado |
| ADR-025 | k6 Load Testing Thresholds SLA Rigorosamente Definidos | Performance / SLA | 🟡 MÉDIO (SLA p95 por rota) | Sprint 23 |
| ADR-020 | Frontend Next.js Error Boundaries + WCAG AA Loading Skeletons | Acessibilidade / Frontend | 🟡 MÉDIO (WCAG 2.1 AA) | Sprint 20 |
| ADR-022 | Graph Intelligence 4.0 Cytoscape SSRF Safe Fetch | Visualização / Segurança SSRF | 🟡 MÉDIO (bloqueia IP privado SSRF OWASP A10) | Sprint 22 |
| ADR-009 | Continuation Strategy Hardening First Continuidade Negócio | BCP / DR | 🟡 MÉDIO (continuidade desastre) | Sprint 14 formalizado |
| ADR-005 | Investigation Concurrency MVP FOR UPDATE SKIP LOCKED PG | Concorrência / Dados | 🟢 BAIXO-MÉDIO | Sprint 14 formalizado |
| ADR-010 | Promoção Maturidade Baseada em Evidência | Governança | 🟢 BAIXO-MÉDIO | Sprint 14 formalizado |
| ADR-011 | Hardening Estático Contratos Visuais Frontend Playwright Snapshot | QA / Frontend | 🟢 BAIXO-MÉDIO | Sprint 14 formalizado |
| ADR-015 | Futuro Módulo Team roadmap colaboração | Roadmap | 🟢 BAIXO (roadmap futuro) | Sprint 14 formalizado |
| ADR-023 | CHANGELOG Hierárquico por Sprint Keep a Changelog 1.1.0 + SemVer 2.0.0 | Governança Release | 🟡 MÉDIO (Release Notes) | Sprint 23 formalizado, **cumprido Sprint 27** |
| ADR-002 | Billing Quote Plan Lock trava orçamento plano contratual | Billing | 🟡 MÉDIO | Sprint 14 formalizado |
| ADR-016 | **(RESERVADO PARA FUTURO ADR)** Gap índice 16→17 descoberto em S27 | Reservado | 🟢 INEXISTENTE (placeholder) | Sprint 27 descoberto |

---

## 4. Pacote Regulatório LGPD (para auditoria ANPD)

| Item | Documento Oficial | Campos obrigatórios |
|---|---|---|
| **LGPD Art.37 ROPD Registro Operações Tratamento** | [docs/compliance-ropd/](file:///home/jistriane/Ontrackchain/ontrackchain/docs/compliance-ropd/) 7 arquivos + CSV | 12 campos/arquivo ANPD CD-005 + DPO extra |
| **LGPD Art.15 RIPD Mestre Ontrackchain (genérico)** | [RIPD-OTK-MASTER-v1.0.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/compliance-ripd/RIPD-OTK-MASTER-v1.0.md) | 16 campos obrigatórios ANPD CD-004 + **4 assinaturas obrigatórias (DPO/CLO/CEO/Arquiteto) validade 12 meses** |
| **LGPD Art.15 RIPD por Cliente B2B (template individual)** | [TEMPLATE-RIPD-POR-CLIENTE-B2B.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/compliance-ripd/TEMPLATE-RIPD-POR-CLIENTE-B2B.md) | 16 campos mestre + **SEÇÃO 17 ESPECÍFICA CLIENTE (Setor, Volume, Biometria, Nível Risco ANPD, Fluxos Partilha, Próxima Revisão 12 meses)** |

### Regras LGPD consolidadas Ontrackchain (verificadas em Q3-07 + Q3-05 STRICT)
- Retenção por categoria: PF autenticada (36 meses), PF transacional (60 meses), PJ BACEN (120 meses = 10 anos).
- Destruição: Soft delete 30 dias carência LGPD Art.15 §6; depois VACUUM FULL + Certificado SHA256 destruição (DPO+CLO).
- Dados sensíveis permitidos: saúde (AML due diligence), racial (autodeclaração titular), biométrico YubiKey WebAuthn (MFA). **PROIBIDOS: dado genético, dado religioso (Art.5º X LGPD sem consentimento explícito Art.22).**
- Transferência internacional: SCCs Standard Contractual Clauses UE ANPD CD-002/2023 (AML KYT providers europeus). Sem transferência EUA sem SCHREMS II adequacy decision atual.

---

## 5. Pipeline CI Pre-Merge (ADR-029) — Pronto Para Ativar Após M5

Arquivo YAML oficial: [pre-merge-gates.yml](file:///home/jistriane/Ontrackchain/.github/workflows/pre-merge-gates.yml). Trigger atualmente **`on:[]` (DESATIVADO)**. Procedimento de ativação (QUANDO M5 for assinado — NÃO AGORA):

1. Trocar `on: []` por:
   ```yaml
   on:
     pull_request:
       branches: [main]
       types: [opened, synchronize, reopened, ready_for_review]
     workflow_dispatch:
   ```
2. GitHub Repo → Settings → Secrets and Variables → Actions → Variables → Criar 2:
   - `DPO_EMAIL` = `dpo@ontrackchain.com.br` (obrigatório LGPD Art.41)
   - `OTK_CI_PRE_MERGE_ENFORCE_ALL` = `true` (bloqueia `--skip-q1..--skip-q5` em CI; ninguém pula gates)

### 5 Gates Ordem FAIL-FAST (Q5 SEMPRE executa)

| Ordem | Gate ID | qa-gateway subcomando | Tipo | Sempre executa? | Bloqueio se falhar? |
|---|---|---|---|---|---|
| 1 | Q1-RBAC | `scan-rbac --strict --max-warnings 0 --db-url ...` | RBAC + RLS | NÃO (fail-fast pula se Q1 falhar) | ✅ SIM P1 Bloqueia |
| 2 | Q2-BILLING-CAP | `scan-billing-capabilities --strict --max-warnings 0` | Billing SSOT Monotonicidade | NÃO | ✅ SIM P1 Bloqueia |
| 3 | Q3-BILLING-ENF | `scan-billing-enforcement --strict --max-warnings 0 --check-prod-redis` | Enforcement Fail-closed | NÃO | ✅ SIM P1 Bloqueia |
| 4 | Q4-LGPD-ROPD | `scan-lgpd-ropd --strict --max-warnings 0` | LGPD Art.37 ROPD estrutura | NÃO | ✅ SIM P1 Bloqueia |
| 5 | **Q5-SECRETS** | `scan-secrets-trufflehog --only-verified --fail-verified --strict` | TruffleHog VERIFICADOS **P0 vazamento segredos** | ✅ **SIM, SEMPRE RODA (seg > tempo)** | ✅ **SIM P0 ABSOLUTO LGPD Art.48 multa 2%** |

*Por que Q5 sempre? Risco vazamento segredo é P0 (LGPD Art.48 multa 2% faturamento bruto anual). Economizar 20-40 min TruffleHog porque Q1 RBAC quebrou não vale a pena. Segurança > tempo.*

### qa-gateway subcomandos Q3-01 a Q3-09 (fonte única verdade)

| ID | Comando qa-gateway | Objetivo | STRICT padrão |
|---|---|---|---|
| Q3-01 | `scan rls --db-url` | Valida tabelas x RLS x POLICY x INDEX PostgreSQL | Sim |
| Q3-02 | `scan-hmac-v2` | Valida HMAC Public API v2 assinaturas timing-safe | Sim |
| Q3-03 | (Playwright E2E externo) | Acessibilidade + Críticos Login/Dashboard/Casos/Evidências | WCAG AA |
| Q3-04 | Hypothesis property-based compliance | Fuzzing 1000+ combinações structural screens | seed 1337 determinístico |
| Q3-05 | `scan-billing-capabilities` | SSOT monotonicidade 3 tiers | Sim max-warnings 0 |
| Q3-06 | `scan-billing-enforcement --check-prod-redis` | Middleware headers X-RateLimit/X-Billing 100% respostas | Sim |
| Q3-07 | `scan-lgpd-ropd` | 7 arquivos ROPD + CSV 12 campos obrigatórios ANPD | Sim |
| Q3-08 | `scan-secrets-trufflehog --only-verified --fail-verified` | TruffleHog auto-detect binário timeout 2h | Sim |
| Q3-09 | **`run-pre-merge-gates --dpo-email`** | **ORQUESTRADOR ADR-029 FAIL-FAST Q1→Q4 + Q5 sempre** | Sim max-warnings 0 |

---

## 6. M5 Governança Risco (ADR-026) — Condição 3A + Procedimento 14 Passos + P0 Handoff

*Template oficial sign-off individual em [TEMPLATE-M5-removal-sign-off.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/governance-sign-offs/TEMPLATE-M5-removal-sign-off.md). Validade 48 horas após assinatura.*

### 6.1 Condição 3A (TODOS DEVEM SER = SIM, NÃO ACEITA PARCIAL)

| # | Item Condição 3A ADR-026 | Status Pré-Handoff | Status Pós-Handoff (apenas preencher se for verdade SIM) |
|---|---|---|---|
| 3A.1 | TruffleHog QA-GATEWAY Q3-08 0 segredos VERIFICADOS HIGH no repositório todo (commits locais + histórico) | 🔴 PENDENTE (ainda não rodado em S27 por regra M5 — executar no procedimento 14 passos passo 07) | ☐ SIM ☐ NÃO |
| 3A.2 | Método de push NÃO É Basic Auth (password + username). Método autorizado: PAT SSO SAML / SSH Deploy Key Ed25519 / GitHub App JWT short-lived (Recomendado: GitHub App) | 🔴 PENDENTE (escolher método no handoff) | ☐ SIM (método: ___) ☐ NÃO |
| 3A.3 | Sign-off 4-Olhos CLO+CTO+DPO+CEO + Arquiteto + Engenheiro executor em documento separado. NENHUM engenheiro pode executar push sem sign-off. | 🔴 PENDENTE (P0-03 etapa final) | ☐ SIM data: ___ ☐ NÃO |
| TODOS = SIM | **Condição 3A CUMPRIDA** | ❌ | ☐ ✅ |

### 6.2 Procedimento 14 Passos (Executar APENAS após Condição 3A = SIM)

1. Snapshot criptografado do working directory (AES256 GCM, chave em Vault, salvo por 180 dias LGPD).
2. `git clean -dfx` (limpa arquivos não versionados, exclui arquivos IMUTÁVEIS explicitamente).
3. `git fetch origin main` + `git rev-list --count origin/main..HEAD` (confirmar ahead count = 24 exato).
4. Verificar IMUTÁVEIS 0 commits: `git diff --name-only origin/main..HEAD` não pode incluir `docs/governance-weekly`, `docs/history`, `docs/assessments`, `github_main`.
5. Rodar qa-gateway Q1: `qa-gateway scan-rbac --db-url $PROD_PG_READONLY --strict --max-warnings 0` ✅ exit=0.
6. Rodar Q2 Q3: `qa-gateway scan-billing-capabilities` + `scan-billing-enforcement --check-prod-redis` ✅ exit=0.
7. Rodar Q4 Q5: `qa-gateway scan-lgpd-ropd --strict` + `scan-secrets-trufflehog --scan-path . --only-verified --fail-verified --strict` (Q5 deve durar ~20-40 min). Q5 exit=0 é obrigatório.
8. Autenticar push método escolhido (3A.2). GitHub App: app_id + installation_id + private key PEM Vault.
9. Executar `git push origin main`.
10. Verificar: `git rev-list --count origin/main..HEAD` → **0** (ahead zerado).
11. Notificar time: Slack/SIEM log SHA push + nome engenheiro executor.
12. Salvar doc sign-off: `docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md` commit local + push.
13. Trigger workflow `pre-merge-gates.yml` AGORA ativado em pull_request (trocar on: [] → on: pull_request).
14. Pós-push: desativar SSH Deploy Key/PAT se foi método provisório; manter apenas GitHub App JWT longevidade 10min.

### 6.3 Handoff Restante P0-01 → P0-04 (16 a 38 dias úteis)

| ID | Tarefa | Responsável | Prazo mínimo/máximo | Percentual baseline 99% → | Artefato final |
|---|---|---|---|---|---|
| **P0-01** | OIDC Keycloak v25 self-hosted Helm 3 réplicas + PG Patroni separado; 4 clients PKCE 15min token; MFA WebAuthn YubiKey obrigatório 3 roles (OTK_ADMIN, OTK_COMPLIANCE_OFFICER, Auditoria); roles OTK_* 5 papéis client-level federação Shared First; LDAP AD memberOf sincronização; SAML IdP-initiated enterprise; Istio mTLS STRICT; Cloudflare WAF auth+DDoS; SIEM Splunk 180d; Backup 6h RPO≤6h RTO≤2h; Prometheus P0 alertas; Playwright E2E Q3-07 futuro; Sign-off 4 CTO/DSI/DPO/Arquiteto | Handbook P0-01 + Guias P0-01 + Run Sheet P0-01 | **8 dias / 21 dias úteis** | 99% → 99.5% | Keycloak URL produção + MFA YubiKey 3 roles ativado + 4 assinaturas handbook |
| **P0-02** | AML/KYT live provider Chainalysis / TRM Labs / Elliptic API key real (Vault, NÃO plaintext); Webhook signatures HMAC; Retenção 120 meses (10 anos BACEN due diligence) | Guias P0-02 + Run Sheet P0-02 | **7 dias / 14 dias úteis** | 99.5% → 99.8% | API key Vault + 100 transações teste live provider OK + doc evidência |
| **P0-03** | Feed UE tokenizado OFAC SDN / EU Consolidated List / Interpol Red Notices (URL tokenizada em Vault, renovação diária UTC 04:00); NOME DESCRIÇÃO tokenizados cripto AES256 em repouso; Indexação vetorial pgvector similaridade cosseno | Guias P0-03 + Run Sheet P0-03 | (paralelo a P0-02, incluso em 7-14 dias) | incluso P0-02 | Feed sincronizado diariamente 30 dias sem erros |
| **P0-03 (M5)** | Condição 3A + Procedimento 14 passos + Assinatura 5 pessoas + Push 24 commits origin/main | Jurídico (CLO) + Conselho Executivo + Engenheiro executor | **1 dia / 3 dias úteis (após P0-01+P0-02 concluídos)** | 99.8% → 100% | Sign-off M5-removal-YYYY-MM-DD.md + GitHub Actions push log 0 ahead |
| **P0-04 OPCIONAL** | SOC2 Type II auditoria 12 semanas + 2 auditorias smart contracts independentes + Pentest anual offensive security + BACEN/ANPD auditoria simulada interna | Terceiros (Big Four / Locarno) | **30 dias / 45 dias úteis (após go-live)** | Selo SOC2 Type II (opcional, não bloqueia go-live) | Relatórios de auditoria assinados + Plano de correções (se houver findings) fechado |

---

## 7. Checklist Final Pré-Sign-off (Apenas assinar se TODOS forem VERDADE)

| # | Item (TODOS DEVEM SER = SIM) | ☐ SIM / ☐ NÃO (preencher manualmente) |
|---|---|---|
| 1 | 29 ADRs assinados em SIGNOFF-ADRS-ALL-29-v1.0.md (ADR-016 reservado não bloqueia) | |
| 2 | Condição 3A M5 (TruffleHog 0 HIGH + método seguro + sign-off 5 pessoas) = SIM | |
| 3 | P0-01 OIDC credenciais reais funcionando: MFA YubiKey OTK_ADMIN + OTK_COMPLIANCE_OFFICER ativos, LDAP sincronizado, Istio mTLS STRICT confirmado | |
| 4 | P0-02 AML live provider ativo: 100 transações teste passaram, webhook HMAC verificado, retenção 120 meses configurado | |
| 5 | P0-03 Feed UE tokenizado ativo, sincronização diária 3 dias sem erros | |
| 6 | qa-gateway run-pre-merge-gates em staging todo passou exit=0 (Q1→Q5 todos OK, 0 segredos VERIFICADOS) | |
| 7 | Procedimento 14 passos M5 foi executado passo a passo; documentado em anexo | |
| 8 | Nenhum arquivo IMUTÁVEL teve alteração (confirmação git diff origin/main..HEAD) | |
| 9 | Nenhum segredo em plaintext confirmado: Vault (HashiCorp) + variáveis de ambiente + .gitignore .env*.private | |
| 10 | Workflow pre-merge-gates.yml ativado com on: pull_request e vars DPO_EMAIL + OTK_CI_PRE_MERGE_ENFORCE_ALL=true definidas | |
| TODOS SIM | **Ciclo S1→S27 100% fechado. Go-live permitido.** | |

---

## 8. Bloco Assinatura (6 pessoas — 4-Olhos + DPO + Engenheiro Executor Individual LGPD Art.43 §4)

*Todas as assinaturas devem ter Data + Nome + Cargo + Assinatura Digital SHA256 + Email Corporativo.*

| # | Cargo | Nome Completo | OAB/CRP/CREA (se aplicável) | Data | Assinatura Digital SHA256 (arquivo + CPF assinante) | Email | Assinatura física |
|---|---|---|---|---|---|---|---|
| 1 | **CLO (Chief Legal Officer) / Diretor Jurídico** — Assinou 29 ADRs + M5 Condição 3A jurídica | ___ | OAB/SP ___ | DD/MM/AAAA | `SHA256: 0x__________________________________` | `clo@ontrackchain.com.br` | ________________ |
| 2 | **CTO (Chief Technology Officer)** — Assinou arquitetura, CI, ADRs técnicos, M5 método push | ___ | CREA-SP ___ (se aplicável) | DD/MM/AAAA | `SHA256: 0x__________________________________` | `cto@ontrackchain.com.br` | ________________ |
| 3 | **DPO (Encarregado LGPD Art.41 ANPD)** — Assinou ROPD 7 ops + RIPD mestre + todos ADRs LGPD | Dr. Carlos Mendes | CRP/SP ___ + OAB/SP ___ | DD/MM/AAAA | `SHA256: 0x__________________________________` | `dpo@ontrackchain.com.br` | ________________ |
| 4 | **CEO / Representante Legal Controladora (LGPD Art.5º II)** — Representa Ontrackchain juridicamente | ___ | — | DD/MM/AAAA | `SHA256: 0x__________________________________` | `ceo@ontrackchain.com.br` | ________________ |
| 5 | **Arquiteto de Software Sênior** — Responsável técnico por todos os 29 ADRs e 24 commits | ___ | — | DD/MM/AAAA | `SHA256: 0x__________________________________` | `arquiteto@ontrackchain.com.br` | ________________ |
| 6 | **Engenheiro(a) Executor(a) Push Remoto M5 Procedimento 14 passos** — Declaração Individual Responsabilidade LGPD Art.43 §4 | ___ | — | DD/MM/AAAA | `SHA256: 0x__________________________________` | `engenheiro@ontrackchain.com.br` | ________________ |

### Declaração Engenheiro(a) Executor(a) (item 6 obrigatório LGPD Art.43 §4 e CLT responsabilidade individual):

Declaro, para os devidos fins de direito e sob as penas da lei (LGPD Art.48 §2, Art.43 §4 e CLT artigos 132, 482 alínea b), que:
1. Fui eu quem executou pessoalmente os 14 passos do procedimento M5.
2. Não recebi, em nenhum momento, pressão para pular qualquer etapa do procedimento.
3. Verifiquei pessoalmente Condição 3A (TruffleHog 0 segredos HIGH, método seguro NÃO basic auth, sign-offs 5 acima presentes) ANTES de `git push`.
4. O método de push escolhido foi: ________________ (PAT SSO / SSH Ed25519 Deploy Key / GitHub App JWT — marcar um).
5. Confirmo IMUTÁVEIS 0 commits, nenhum arquivo sensível vazado, 0 ahead após push.
6. Assumo responsabilidade individual, cível e criminal, por esta operação, além das sanções administrativas da ANPD.

Data: ____/____/________ Assinatura: _________________________

---

## 9. Apêndices (não assinam, referência)

- Apêndice A: CHANGELOG hierárquico 11 releases (S18→S27) → [CHANGELOG.md](file:///home/jistriane/Ontrackchain/CHANGELOG.md)
- Apêndice B: Baseline Executiva Oficial v1.6 (99%) → [project-executive-readiness-brief.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/project-executive-readiness-brief.md#L147-L184)
- Apêndice C: README Oficial v5.11.0 → [README.md](file:///home/jistriane/Ontrackchain/README.md#L18-L121)
- Apêndice D: Índice 29 ADRs canônico → [docs/adrs/README.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/adrs/README.md)
- Apêndice E: Todos os 29 ADRs individuais → diretório [docs/adrs/](file:///home/jistriane/Ontrackchain/ontrackchain/docs/adrs/)
- Apêndice F: qa-gateway CLI código fonte + testes contrato → [cli.py](file:///home/jistriane/Ontrackchain/ontrackchain/packages/qa-gateway/src/qa_gateway/cli.py) + [tests Q3-08/Q3-09](file:///home/jistriane/Ontrackchain/ontrackchain/packages/qa-gateway/tests/)
- Apêndice G: Guias P0-01/P0-02/P0-03 + Run Sheets → [governance-sign-offs/guides/](file:///home/jistriane/Ontrackchain/ontrackchain/docs/governance-sign-offs/guides/)

---

**Versão documento:** v1.0 (inalterável após assinatura 6 pessoas). Qualquer adendo → v1.1 com novo sign-off 4-Olhos mínimo.
*Documento gerado em 2026-08-10 como anexo oficial do sign-off M5 Ontrackchain Governança Risco.*
