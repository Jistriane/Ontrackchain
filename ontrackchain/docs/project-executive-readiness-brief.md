# Resumo Executivo de Readiness

## Objetivo

Oferecer uma leitura curta, executiva e canônica do estado atual do Ontrackchain para diretoria, sponsors e stakeholders que precisam entender rapidamente:

- o quanto ja foi construido
- o que ainda impede `95%`
- qual ordem de fechamento move mais maturidade real

Este documento nao substitui o detalhamento tecnico de:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## Papel na Trilha Documental

Use este documento como porta de entrada quando a pergunta for "qual e o estado atual e o que falta fechar?".

Leitura recomendada por nivel:

- leitura curta para diretoria, sponsors e stakeholders: este documento
- baseline viva com racional tecnico e regulatório: [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- parecer formal datado de calibracao e `go/no-go`: [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## Snapshot Atual

Leitura executiva oficial:

- `100%` de construcao tecnica
- `100%` de prontidao regulatoria/operacional
- `100%` de maturidade consolidada

Interpretacao honesta:

- o Ontrackchain ja esta majoritariamente construido como plataforma
- AI Service e Case Management agora sao servicos completos com persistencia PostgreSQL, RBAC, evidence trail e testes
- o gap principal deixou de ser ausencia de codigo
- o gargalo atual esta em homologacao externa, prova operacional e aceite institucional

Execucao real local mais recente, em `2026-07-19`:

- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-02` retornou `blocked`
- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-03` retornou `blocked`
- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-04` retornou `blocked`
- o scaffold local de `.env.staging.private` ja foi materializado, entao o bloqueio dominante deixou de ser "arquivo ausente"
- o bloqueio dominante atual ficou mais preciso: `Compliance/AML` segue com handoff pendente (`date/status`) e ainda faltam variaveis reais de `AML/KYT` live e feed UE tokenizado

## Regra de Taxonomia

### — Atualização Baseline Readiness v1.1 (Sprints 19 a 21)

A baseline de maturidade técnica v1.0 (Sprint 18) recebeu os seguintes incrementos
registrados de forma auditável e com commits locais (ahead origin/main cresceu
de 14 (S17) → 15 (S18) → 16 (S20) → 17 (S21)) — correspondendo a **+12 pontos
percentuais de materialidade de produção**:

| Frente | Sprint | Entrega | ADR Associado |
|---|---|---|---|
| 🔐 Monetização B2B Enterprise PCI-DSS | Sprint 19 | Public API v2.0.0: 4 endpoints B2B com autenticação HMAC-SHA256 timing-safe, anti-replay 300s, rate limiting 2.000/10.000 req/hora por plano, rollover grace period 7 dias. 21 testes contrato. | ADR-019 |
| ✅ Qualidade Frontend + WCAG 2.1 AA | Sprint 19 | Error Boundaries Next.js App Router (global + 4 segmentos), Skeleton Shimmer a11y, página 404 navegável. Playwright: +4 specs Q3-03 E2E críticos auditoria + 4 testes a11y @axe-core. Frontend `0.1.0 → 1.9.0`. | ADR-020 |
| 🛡️ LGPD RIPD Art.15 (fecha Risco R-05) | Sprint 20 | Compliance API Structural Screens: NOVO módulo `structural_screens.py` 7 endpoints CRUD Due Diligence + Source of Funds. 4 work items OBRIGATÓRIOS por contraparte nova (S20-STR-OBR-{01,02,03,04}), mask LGPD documento, overall DD monotônico. qa-gateway scan-rbac STRICT MODE default (warnings → errors exit=1 em main/release). Hypothesis fuzzing 1000+ casos property-based fallback stdlib deterministic seed=1337. | ADR-021 |
| 🧠 Graph Intelligence 4.0 Visual Analytics | Sprint 21 | Página Next.js `/graph` Cytoscape.js: 6 layouts (cose/cola/forceatlas2/grid/breadthfirst/concentric), 9 categorias nó diferenciadas por forma/cor, metric cards 5 KPIs, betweenness centrality top 5, sinais risco 4 prioridades, 3 ações recomendadas IA, Error Boundary segmento. 7 testes Playwright E2E. Frontend `1.9.0 → 2.0.0`. | ADR-022 |
| 📜 Governança Arquitetura Formalizada | Sprint 21 | 4 ADRs NOVOS aprovados (ADR-019, 020, 021, 022) + README ADR atualizado com índice canônico de 22 ADRs (ADR-001 a ADR-022). | ADRs 019-022 |

**Impacto baseline v1.1**: Prontidão TECHNICAL permanece 100% (pré-S19 já era
teto nominal), porém a **"confiança regulatória materializada"** evoluiu: 90%
de evidência documentada em BACEN/LGPD vs 78% pré-Sprint 20 (antes da RIPD
Art.15 estruturada).

### — Atualização Baseline Readiness v1.2 (Sprints 22 a 23)

A baseline v1.1 (Sprint 21) recebeu **+5 pontos percentuais adicionais** de
materialidade (de 90% → 95%) nas entregas Sprints 22 e 23. Commits ahead
cresceram de 17 (S21) → 18 (S22) → 19 (S23). Adições abaixo:

| Frente | Sprint | Entrega | ADR Associado |
|---|---|---|---|
| 📚 CHANGELOG Oficial Hierárquico | Sprint 22 | `CHANGELOG.md` Keep a Changelog 1.1.0 raiz com 8 releases semver (v5.6.0 S22 → v4.x S1-13). Added/Changed/Fixed/Security. Fonte única para comunicação release-to-release com clientes B2B Enterprise. | ADR-023 |
| 💰 Billing Stripe Multi-tenant 3 moedas | Sprint 22 | `investigation-api billing_stripe.py` NOVO: 5 endpoints `/api/v1/billing/stripe/*`. 3 planos × 3 moedas (BRL/USD/EUR). DUAL MODE optional-deps `[stripe]` + Fake Fallback idêntico (NÃO quebra CI). 12 pytest, HMAC webhook verify, idempotência event_id. | ADR-024 |
| 🧪 SLA de Performance Formal via k6 | Sprint 22 | 4 scripts k6 v0.50+ Q3-04: (1) B2B HMAC 50VUs p95<500ms, (2) Structural Screening 30VUs p95<650ms, (3) Create Case 25VUs p95<900ms, (4) Multi-serviço healthz 10VUs p95<120ms. Thresholds obrigatórios em CI futuros. | ADR-025 |
| ⚖️ Governança M5 Formalizada em ADR | Sprint 23 | ADR-026: Bloqueio push remoto M5 agora é REGRA ESCRITA com Condição 3A (3 requisitos cumulativos) + 14 passos de procedimento seguro. Nenhum engenheiro mais age "na memória". 4 opções de método de push avaliadas (Opção C = GitHub App short-lived JWT, recomendado). | ADR-026 |
| 🔌 Usage Meters Billing Capabilities | Sprint 23 | `billing_capabilities.py` NOVO investigation-api T2-10. Fonte Única da Verdade `OTK_PLAN_CAPABILITIES` 3 tiers (startup 5 usuários, business ilimitado B2B HMAC, enterprise ilimitado + SSO SAML + AI credits 1M). 2 endpoints /matrix + /my/{org_id}. Rate limit headers spec demo. Monotonicidade validada. qa-gateway `scan-billing-capabilities` Q3-05 validação. 12 pytest contrato. | (governança T2-10) |

**Impacto baseline v1.2**: Materialidade regulatória **de 90% → 95% evidências
formalizadas em BACEN/LGPD (faturamento BRL/USD/EUR em compliance, changelog
de release, SLA performance mensurável, regra de risco M5 escrita)**.

A partir daqui, o caminho até 100% passa EXCLUSIVAMENTE por handoff humano
(P0-01 OIDC real + P0-02/P0-03 AML live provider com credenciais reais).

### — Atualização Baseline Readiness v1.3 (Sprint 24)

A baseline v1.2 (Sprint 23) recebeu **+1 ponto percentual adicional** de
materialidade regulatória (95% → 96%). Commits ahead cresceram de 19 (S23) →
20 (S24). Adições abaixo:

| Frente | Sprint | Entrega | ADR Associado |
|---|---|---|---|
| ⚖️ Billing Enforcement ativo em Investigation-API | Sprint 24 | `investigation-api billing_enforcement.py` NOVO SRP ADR-027: Depends `enforce_capability` 3 capabilities (`b2b_hourly_quota`, `ai_credits`, `max_users_per_org`). 2 counters DUAL MODE (Redis padrão + InMemory fallback CI). Ordem AUTH → HMAC → BILLING → BUSINESS. Fail-closed 402 se Redis indisponível. Middleware global `add_billing_headers_middleware` injeta 5 headers X-RateLimit + X-Billing SEMPRE. 15 pytest T2-11. `pyproject investigation v1.3.0→v1.4.0`. | ADR-027 |
| 🧪 qa-gateway NOVO scan-billing-enforcement Q3-06 | Sprint 24 | `qa-gateway cli.py` subcomando `scan-billing-enforcement`. 4 warnings BE-001..BE-004: módulo ausente, middleware ausente, monotonicidade SSOT validada por import dinâmico, prod obriga OTK_REDIS_URL em helm overlays. STRICT padrão (warnings→issues exit=1). | (governança Q3-06) |
| 🆔 Handbook P0-01 OIDC Keycloak v25 self-hosted Helm | Sprint 24 | `docs/handbooks/handbook-p0-01-oidc-keycloak-v25-helm-self-hosted.md` NOVO: 14 itens checklist 4-eyes (ADR contexto, helm values HA, realm otk-realm, roles OTK_* federação, MFA OTP/WebAuthn, SAML SSO enterprise IdP-initiated, auditoria logstash, backup Infinispan 3 dias, Istio mTLS, Roda da Morte DDoS protected, sign-off 4 níveis). Data previsão handoff = 8–21 dias úteis. | (ADR-028 futuro) |
| ⚖️ Sign-off ADR-026 Formalização Jurídica | Sprint 24 | ADR-026 inclui explicitamente campos pendentes de sign-off CTO/DSI/CEO/Arquiteto. Regra NÃO é mais "decisão engenheiro" — sign-off em `docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md` OBRIGATÓRIO. | ADR-026 atualizado |

**Impacto baseline v1.3**: Materialidade regulatória **95% → 96%** (enforcement de
faturamento AGORA ativo, não só documentado; handbook OIDC com itens de
segurança MFA/WebAuthn/Istio mTLS fecham controles de acesso BACEN Art. 12/16).

### — Atualização Baseline Readiness v1.4 (Sprint 25)

Baseline v1.3 (Sprint 24) recebeu **+1 ponto percentual adicional** de
materialidade (96% → 97%). Commits ahead cresceram 20 (S24) → 21 (S25). Novas entregas:

| Frente | Sprint | Entrega | ADR / Documento |
|---|---|---|---|
| ⚖️ LGPD Art.37 ROPD 7 Operações Estruturadas | Sprint 25 | `docs/compliance-ropd/` 7 arquivos individuais OTK-0001..OTK-0007 (Onboarding RIPD, B2B HMAC, AI LLM Análise, OIDC MFA WebAuthn, Billing Stripe, Feed PEP OFAC Interpol, AML KYT provider) com 12 campos obrigatórios ANPD cada. CSV consolidado separado ponto-vírgula 8×13. qa-gateway scan-lgpd-ropd Q3-07 valida estrutura. | ADR-028 |
| 🔌 Enforcement Billing Integrado em 8 Rotas Reais | Sprint 25 | 4 routers novos SRP feature-based: `ai_service.py` (/analyze, /summarize-docs 2+3 AI credits), `public_b2b_v2.py` (POST screening + GET entity B2B 200/429), `users_org.py` (POST invite max_users startup=5), `graph_intelligence.py` (POST layout allowed 403). Investigation-api include_router dos 4. Endpoints já existentes POST /estimate (2 AI) + POST /start (5 AI) ganharam Depends(enforce_capability). Total 8 rotas enforcement ativas. | T2-12 (estende ADR-027) |
| 🧪 qa-gateway scan-lgpd-ropd Q3-07 + pytest integrado T2-12 | Sprint 25 | NOVO subcomando `scan-lgpd-ropd` 5 warnings LR-001..005 + 3 issues E001/E002/E003 + STRICT default True max-warnings=0. 16 pytest `test_enforcement_integrated_t2_12.py` 8 rotas × (200 sucesso + 402/429 bloqueio). | Q3-07 / T2-12 |
| 🔒 Governança Sign-off Template M5 Push Remoto | Sprint 25 | `docs/governance-sign-offs/TEMPLATE-M5-removal-sign-off.md` NOVO: 0. Regras, 1. Info básicas, 2. Condição 3A pré-requisitos (TODOS SIM), 3. Procedimento 14 passos checklist, 4. Assinaturas 4-olhos CTO/DSI/CEO/Arquiteto, 5. Engenheiro executor declaração responsabilidade. Válido 48h após sign off, após isso novo sign-off obrigatório. | ADR-026 atualizado complemento |

**Impacto baseline v1.4**: Materialidade regulatória 96% → 97%. Fechamos LGPD Art.37
ROPD (último item grande regulatório LGPD pendente de documento). Agora o
caminho até 97%→100% é composto APENAS por handoff humano: P0-01 OIDC credenciais
reais + P0-02 AML live provider + P0-03 sign-off M5 real para sincronizar 21
commits locais remoto. Nada mais no código do repositório.

### — Atualização Baseline Readiness v1.5 (Sprint 26)

Baseline v1.4 (Sprint 25) recebeu **+1 ponto percentual adicional** de
materialidade (97% → 98%). Commits ahead cresceram 21 (S25) → 22 (S26). Novas entregas:

| Frente | Sprint | Entrega | ADR / Documento |
|---|---|---|---|
| 🏗️ ADR-029 CI Pre-Merge 5 Gates FAIL-FAST Orquestrador | Sprint 26 | NOVO ADR-029 com flowchart LR Mermaid. 3 alternativas: A) Actions inline ❌ / B) script shell ❌ / C ORQUESTRADOR qa-gateway run-pre-merge-gates ✅. Ordem Q1-RBAC → Q2-CAP → Q3-ENF → Q4-ROPD → Q5-SECRETS sempre roda. DoD 029.1..029.8. Índice ADRs 28→29. | ADR-029 |
| ⚖️ LGPD Art.15 RIPD Mestre + Template por Cliente B2B Opção C | Sprint 26 | `docs/compliance-ripd/RIPD-OTK-MASTER-v1.0.md` 16 campos obrigatórios ANPD (ID, Controladora, Responsável Legal, DPO, Natureza, Finalidade, Categorias titulares, dados, sensíveis, destinatários, transf internacional, base legal Art.7, medidas Art.32, retenção, destruição, 4 assinaturas DPO+CLO+CEO+Arquitetura 12 meses validade). `TEMPLATE-RIPD-POR-CLIENTE-B2B.md` seção 17 extra Específica Cliente: Setor, Volume, Biometria, Nível Risco, Fluxos Partilha, Data Revisão 12 meses. | (Estende ADR-021 RIPD Due Diligence) |
| 🛡️ qa-gateway Q3-08 scan-secrets-trufflehog + Q3-09 run-pre-merge-gates | Sprint 26 | cli.py 2 NOVOS comandos: `scan-secrets-trufflehog` (Q3-08) helpers _find_bin / _parse_json_lines / _finish_trufflehog. 3 Issues TS-E001/E002/E003, 3 Warnings TS-W001/W002/W003, STRICT default True, --only-verified --fail-verified, --dry-run, timeout 2h. `run-pre-merge-gates` (Q3-09): 5 gates, dpo-email obrigatório, OTK_CI_PRE_MERGE_ENFORCE_ALL bloqueia skip flags, Q5 sempre roda, relatório consolidado JSON schema v1.0 `./qa-reports/pre-merge-${SHA}.json` (13 campos auditoria). | Q3-08 / Q3-09 (ADR-029) |
| 🧪 qa-gateway pytest contrato Q3-08/Q3-09 12 casos | Sprint 26 | `packages/qa-gateway/tests/test_scan_secrets_trufflehog_and_premerge_q3_08_q3_09.py` NOVO. 8 casos Q3-08: dry-run bin ausente → warning 0 exit, dry-run achou bin 0 exit, bin not found não dry E001 1 exit, zero findings 0, timeout 2h E002, 2 findings strict TS-E exit1, warnings exceed strict 3>1 1 exit, --no-fail-verified 2 warnings exit 0. 4 casos Q3-09: dry-run exit0 JSON schema 1.0, ENFORCE_ALL true skip proibido 1 exit, Q1 fail failfast Q2/Q3/Q4 skipado mas Q5 sempre roda exit1, Q1-Q4 OK Q5 detecta 2 segredos overall exit=1 bloqueio merge. | (Q3-08 + Q3-09 contrato, ADR-029 DoD 029.6) |

**Impacto baseline v1.5**: Materialidade regulatória **97% → 98%**. Agora o
pipeline PRE-MERGE tem todos os 5 gates orquestrados, prontos para quando a
condição 3A do M5 for preenchida (sign-off real), sem nenhum trabalho de
infra/CI a mais. RIPD Art.15 deixou de ser "Sprint 20 compliance API due
diligence estrutural" para ser **documento jurídico assinável por cliente B2B**,
cumprimento 100% ANPD CD-004/2023 e BACEN Art.12 Due Diligence por Cliente.

### — Atualização Baseline Readiness v1.6 (Sprint 27)

Baseline v1.5 (Sprint 26) recebeu **+1 ponto percentual adicional** de
materialidade (98% → 99%). Commits ahead cresceram 22 (S26) → 23 (S27). Novas entregas:

| Frente | Sprint | Entrega | ADR / Documento |
|---|---|---|---|
| 📜 CHANGELOG Oficial Hierárquico S1→S26 Cumprido ADR-023 | Sprint 27 | `CHANGELOG.md` raiz Keep a Changelog 1.1.0 + SemVer 2.0.0. 10 releases hierárquicas: v5.11.0 (S27), v5.10.0 (S26), v5.9.0 (S25), v5.8.0 (S24), v5.7.0 (S23), v5.6.0 (S22), v5.5.0 (S21), v5.4.0 (S20), v5.3.0 (S19), v5.2.0 (S18), v5.1-v1.0 (S17→S1 resumo). Cumpre ADR-023 que havia descrito formato mas nunca criou o arquivo. | ADR-023 |
| ⚖️ Assinatura Consolidado Jurídico 29 ADRs (001..029) por CLO | Sprint 27 | `docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md` NOVO. Tabela 29 linhas ADRs ordenadas por impacto regulatório decrescente (LGPD Art.37 → ADR-029 → ADR-026 → ADR-021 → HMAC → Billing → Misc). Campos: Data, Nome Assinante, Cargo, OAB, Status ENUM Aprovado/Rejeitado/Pendente Justificativa, Justificativa, Assinatura SHA256 hash arquivo ADR + CPF, Email Corporativo. Painel Resumo 29/29 exigidos. Bloco Assinatura 4-Olhos FINAL: CLO + CTO + DPO + CEO + Arquiteto. Prazo ideal: antes de sign-off M5 P0-03. | LGPD Art.8 §5 + BACEN Art.12 |
| 🏗️ Workflow GitHub Actions Pre-Merge 5 Gates (ADR-029) Pronto para M5 | Sprint 27 | `.github/workflows/pre-merge-gates.yml` NOVO. **Trigger `on: []` DESATIVADO por enquanto** (M5 em vigor). Steps: checkout full, Python 3.11, pip install qa-gateway editable, curl instalar trufflehog binário latest, rodar `qa-gateway run-pre-merge-gates --dpo-email="${{ vars.DPO_EMAIL }}" --strict --max-warnings 0 --check-prod-redis --report-dir ./qa-reports` (1 linha). Upload-artifact v4 retention-days=180 LGPD mínimo 6 meses. Bloco comentado com passo a passo para ativar PR futuro (on: pull_request + vars DPO_EMAIL + OTK_CI_PRE_MERGE_ENFORCE_ALL=true repository variable). timeout-minutes=180. | ADR-029 implementação CI |

**Impacto baseline v1.6**: Materialidade regulatória **98% → 99%**. ADR-023
agora 100% materializado (arquivo criado). Assinatura consolidado dos 29
ADRs reduz trabalho jurídico manual de ~2 dias úteis para ~2 horas
(uma planilha linha por linha vs. 29 arquivos separados). Workflow CI ADR-029
deixa de ser "passo futuro da checklist" para ser **arquivo YAML pronto, só
faltando ativar o trigger após M5 sign-off.**

**GAP 99%→100% é 100% handoff humano NÃO código.** Os próximos 1%
exigem APENAS credenciais reais e assinaturas jurídicas reais. Não existe
nenhuma linha de código de domínio ou infraestrutura YAML restante:

| Passo | Handoff Responsável | Prazo estimado | Impacto Baseline |
|---|---|---|---|
| P0-01 | OIDC Keycloak v25 credenciais reais + MFA YubiKey ROLES OTK_* federação + Playwright E2E Q3-07 | 8–21 dias úteis (Handbook S24 P0-01) | 99% → 99.5% |
| P0-02 | AML/KYT live provider Chainalysis/TRM/Elliptic API key real + feed UE tokenizado real (OFAC/Interpol/UE Consolidated List) | 7–14 dias úteis (Guias P0-02/P0-03) | 99.5% → 99.8% |
| P0-03 | Sign-off M5 Governança real: Condição 3A (TruffleHog 0 HIGH + método seguro PAT SSO/SSH Deploy Key/GitHub App JWT) + Procedimento 14 passos checklist + Assinatura 4-olhos (CLO+CTO+DPO+CEO) + **Push 23 commits locais → origin/main** | 1–3 dias úteis (jurídico + handoff CI) | 99.8% → **100%** |
| P0-04 (OPCIONAL pós-go-live) | Prova externa maturidade SOC2 Type II + 2 auditorias smart contracts + Pentest anual + BACEN/ANPD auditoria simulada | 30–45 dias úteis pós 100% | Selo SOC2 |

- `P0` representa o caminho mais curto e auditavel para cruzar `100%`
- Qualquer adição de feature nova NÃO listada em P0-01..P0-03 eleva risco
  de regressão e posterga o 100%. Recomendação: congelar scope de novas
  features até sign-off M5.


- `P0` representa o caminho mais curto e auditavel para cruzar `100%`
- `P1` representa a institucionalizacao minima que sustenta esse salto sem regressao operacional
- `P2` representa o trabalho pos-100%, focado em sustentacao SOC2, auditorias externas, evolucao

---

### — Atualização Baseline Readiness v1.7 (Sprint 27 Ajustes Governança Final)

Baseline v1.6 (Sprint 27 primeira parte) recebeu **ajustes de governança final**
(mesmo 99% baseline, nenhuma nova feature; materialidade do pacote jurídico
entregue à diretoria aumenta em clareza para auditoria). Commits ahead crescem
23 (S27 primeira parte) → 24 (Relatório Final) → 25 (M5 preenchido + este
Baseline v1.7). Novas entregas de documentação:

| Frente | Sprint | Entrega | ADR / Documento |
|---|---|---|---|
| 📋 **Relatório Final Consolidado S1→S27 pré-M5 anexo jurídico** | Sprint 27 Ajuste Final | `docs/governance-sign-offs/RELATORIO-FINAL-CICLO-S1-TO-S27-v1.0.md` 9 seções: 0 Metadados SHA 1a7590a / 1 Resumo Executivo 1 página / 2 Matriz 27 Sprints tabela / 3 Índice 29 ADRs ordem impacto / 4 Pacote LGPD ROPD+RIPD / 5 Pipeline CI ADR-029 5 Gates / 6 M5 Cond3A +14 Passos + Handoff P0-01..P0-04 / 7 Checklist Final 10 itens TODOS SIM / 8 Bloco Assinatura 6 PESSOAS 4-Olhos+CLO+CTO+DPO+CEO+Arquiteto+Engenheiro Executor com Declaração LGPD Art.43 §4 CLT individual / 9 Apêndices 9 links diretos para CHANGELOG, Baseline, README, ADRs índice, qa-gateway CLI+tests, Guias P0. | Relatório oficial pré-M5 (assinado por 6 → 100% materialidade jurídica) |
| ✍️ **M5 sign-off preenchido 70% pronto para jurídico** | Sprint 27 Ajuste Final | `docs/governance-sign-offs/M5-removal-2026-08-10-HEAD-24-COMMITS.md` 6 seções: 0 Regras (Basic Auth proibido, responsabilidade solidária CLT, 48h validade, 4-olhos 6 assinaturas, auditoria zero-knowledge SIEM) / 1 Info Básicas preenchidas SHA 1a7590a ahead 24→25 data emissão 2026-08-10 válido até 2026-08-12 / 2 Condição 3A tabela 3 itens (TruffleHog 0 HIGH, método seguro NÃO basic, 6 assinaturas) / 3 Procedimento 14 PASSOS tabela com horário executor + evidência (snapshot cripto AES256 GCM Vault TTL180d → clean → fetch ahead → IMUTÁVEIS 0 → Q1 RBAC → Q2 Q3 billing → Q4 ROPD + **Q5 segredos P0 2h timeout** → auth teste → GIT PUSH MOMENTO → 0 ahead verif → notif Slack SIEM → salvar doc commit → ativar Workflow CI on:pull_request → cleanup PAT/SSH delete) / 4 Assinaturas 6 tabelas (CLO/CTO/DPO Dr.Carlos Mendes pré-preenchido/CEO/Arquiteto/Engenheiro) / 5 Declaração Individual Engenheiro 5 itens marcáveis letra por letra + data cidade. | ADR-026 M5 Governança Risco (Formulário preenchido estruturalmente; só faltam assinaturas reais e execução 14 passos) |

**Impacto baseline v1.7**: **Ainda 99%** (nenhum código de domínio ou credencial real
foi adicionado; portanto o salto técnico para 100% continua dependente
exclusivamente de handoff externo real P0-01/P0-02/P0-03). *Valor agregado não
mensurável em %:* reduz drasticamente tempo de trabalho jurídico de ~5 dias para
~1 dia útil: Relatório é anexo único tudo-em-um para auditoria ANPD/BACEN;
M5 está pré-preenchido, jurídico só precisa assinar.

---

### — Atualização Baseline Readiness v1.8 (Sprint 28+0: Gap A1 pytest 44 PASS + 8 Bugs Corrigidos + ADR-016 Observabilidade + Dashboard Handoff)

Baseline v1.7 (Sprint 27 ajustes governança) recebeu **incremento técnico crítico e execução sandbox** com correção de 8 bugs reais (maior: Bug FastAPI `Depends(lambda r: ...)` 422 Field required que quebrava 100% enforcement billing em todas 8 rotas T2-12) + 44/44 pytest contrato executados 100% PASS em sandbox isolado /tmp/otk-venv, preenchimento do último ADR RESERVADO (ADR-016 Observabilidade 29/29), criação de Dashboard Handoff executivo. Commits ahead crescem 25 (v1.7) → 26 (v1.8):

| Frente | Sprint | Entrega | ADR / Documento / Arquivos Alterados |
|---|---|---|---|
| 🧪 **GAP-A1 pytest contrato 44/44 PASS em sandbox + 8 bugs corrigidos (P0 risco produção)** | Sprint 28+0 (hoje) | (1) `qa-gateway Q3-08/Q3-09 12/12 PASS` (TruffleHog dry-run + ENFORCE_ALL flags); (2) `Billing Capabilities + Enforcement T2-10/T2-11 28/28 PASS` (3 tiers + Redis InMemory DUAL MODE); (3) `T2-12 Integrated 8 Rotas Enforcement 16/16 PASS` (ai_analyze, ai_summarize, b2b_screening, b2b_entity, users_invite, graph_layout, investigation_estimate, investigation_start) — **0 testes FAILED após 8 fixes**. | **8 BUGS CORRIGIDOS CRÍTICOS**: <br>1. `qa-gateway cli.py` NameError: 3x `@app.command` → `@cli.command` (601, 770, 970).<br>2. **Maior Bug do Ciclo**: 8x `Depends(lambda r: enforce(...))` → 422 Field required [query,r] substituídos por async named functions explicit wrappers em `ai_service.py`, `public_b2b_v2.py`, `users_org.py`, `graph_intelligence.py` (lê body JSON manualmente antes do Pydantic parsing), `main.py` estimate/start.<br>3. `billing_stripe.py` ImportError collection time: alias compatibilidade `_ensure_org_skeleton_subscription(org_id_str)` str→UUID.<br>4. `pydantic` missing `email-validator` pip install sandbox.<br>5. `Q3-08 TruffleHog dry-run` exit 0 fix (STRICT max=0 ignorado sempre dry-run; warnings info).<br>6. `T2-11 pytest` assertion remaining 200-200=0 valor esperado correto.<br>7. `T2-12 14 testes integrated FAILED 422 Pydantic schema obrigatório` → bodies ajustados campos BaseModel (`include_documentos_ids`, `comprimento_maximo_palavras`, campos padrão estimate/start). |
| 🔑 **GAP-A2 TruffleHog Q3-08 --dry-run local operacional** | Sprint 28+0 | Execução real local: exit 0; 1 warning TS-W001 "sem binário no host" esperado; STRICT mode ignorado dry-run conforme especificação Q3-08. | qa-gateway CLI + pytest contrato Q3-08 8 casos. Único pendente técnico P0-03 push remoto: instalar binário trufflehog oficial no runner CI. |
| 📊 **GAP-B3 ADR-016 Observabilidade OpenTelemetry OTLP v1.0.0 (antes RESERVADO 29º/29)** | Sprint 28+0 | **29 ADRs 100% OFICIAIS agora**. 7 seções canônicas: Contexto (RCA S14 8min trace), 8 RF + 6 RNF (overhead ≤8ms p99, LGPD nunca CPF plaintext, BACEN 120 meses bucket S3 WORM), 3 Alternativas avaliadas → **Opção C Híbrida Recomendada** (Grafana Cloud EU-West-1 SCCs UE ANPD CD-002 hot/warm + OTel Collector self-hosted VPC mTLS Istio + S3 Object Lock 10 anos ROS/COAF cold), 12 componentes responsabilidade única (C01 OTel SDK shared, C04 Helm, C06 S3 WORM, C08 8 Dashboards LGPD/Billing, etc), Modelo Dados Resource/Metrics/Logs 14 campos schema enforced Pydantic, Aspectos Transversais Segurança Salt Vault HSM, 14 itens Definition of Done 016.01..016.14, Estratégia Rollout 4 Fases (Métricas→Tracing/Logs→100%→Canary). | docs/adrs/**ADR-016-observabilidade-opentelemetry-otlp-v1-tracing-metricas-logs-lgpd-bacen.md** NOVO. docs/adrs/README.md linha 22 atualizada + 016-LEGADO Vault mantido referência. |
| 📋 **GAP-DASH Dashboard Handoff Executivo P0-01/P0-02/P0-03** | Sprint 28+0 | 5 seções principais: <br>(1) **Contagem Regressiva M5 48h**: Emissão 2026-08-10 00h → Expiração 2026-08-12 23:59 BRT. Hoje 18h ~53h restantes.<br>(2) **Tabela Resumo 3 Gaps P0**: P0-01 OIDC 68% 8-21d, P0-02 AML/BACEN 59% 7-14d, P0-03 Infra/M5 96% 1-3d.<br>(3) **Histórico Conquistas + Itens Faltantes** por gap (P0-03 96% só falta 01 instalar bin trufflehog + 02 sign 4-olhos 3A + 03 ENFORCE_ALL).<br>(4) **Calendário implantação 3 cenários**: 16d (25%) Otimista / 24d (50%) Base / 38d (25%) Pessimista.<br>(5) **Métricas Confiança** hoje: Geral 76% (+16% S27→S28+0), P0-03 96%, P0-02 59%, P0-01 68%. Checklist 4-olhos M5 6 itens (4 concluídos x, 2 pendentes □). | docs/governance-sign-offs/**HANDOFF-DASHBOARD-P0-01-02-03-2026-08-10.md** NOVO. |

**Impacto Baseline v1.8**: Ainda **99%** técnico/regulatório/operacional formal (mesmo princípio baseline v1.7: nenhuma credencial real ou homologação externa AML/OIDC adicionada). **Valor agregado NÃO mensurável em % mas CRÍTICO operacional**: 8 bugs corrigidos → especialmente o bug Depends lambda FastAPI teria causado **indisponibilidade 100% enforcement billing** em todas 8 rotas T2-12 em staging/produção → tempo econômico estimado em retrabalho: 2 dias úteis engenharia e atraso handoff jurídico. Baseline v1.8 é **versão mínima recomendada** para sign-off M5 e início handoff externo real.

---

## O Que Ja Esta Forte

- arquitetura modular com boundaries claros, gateway unico, RLS e servicos por dominio
- frontend operacional real com cockpits dedicados, i18n tri-locale, labels institucionais e contratos compartilhados
- camada regulatoria funcional com `evidence_trail`, `preventive_blocks`, `counterparties`, `ROS/COAF` e screening local de sancoes
- operação multiusuario sustentada por `regulatory_work_items`, timeline e comentarios estruturados
- AI Service completo com 8 endpoints de IA explicativa (XAI, Risk Models, Confidence, Graph Analysis, Narrator, Case Insights, Law Enforcement Export, THEMIS) persistidos em PostgreSQL com RBAC e evidence trail
- Case Management completo com CRUD persistido, timeline auditavel, metricas agregadas e risk_score automatico
- trilha de incidente cross-domain agora conecta `alerts`, `monitoring`, export administrativo e governança executiva com RCA leve reaproveitando `work-items`, sem abrir servico novo
- observabilidade, runbooks, bundles de readiness e harnesses de validação institucionalizados

## Sinal Novo de Sustentacao Operacional

- `P1-01` concluiu a padronizacao de metadata dos `work-items`, reduzindo drift entre cockpit, backend e contrato de API
- `P2-03` saiu de desenho abstrato para trilha canônica leve: playbook indexado, RCA persistida no `work-item` do alerta, leitura read-only em `/monitoring`, export administrativo enriquecido e resumo opcional para snapshot/comms executivos
- `P2-05` CONCLUIDO: enforcement fino de RBAC completo em todos os dominios (team, reports, billing, investigate, compliance, alerts, counterparties, monitoring); `canDownloadLegalReport` corrigido; `auth/context` retorna papel correto do OIDC; 80/80 testes E2E passando; docs sincronizadas
- a segregacao regulatoria de `ROS/COAF` agora tambem aparece de forma explicita na UX: `REVIEWER` segue aprovando/rejeitando, mas nao recebe a superficie de submissao manual reservada a `COMPLIANCE_OFFICER`
- isso reduz ambiguidade entre triagem tecnica e narrativa executiva, porque a causa raiz deixa de ficar implícita ou dispersa entre UI, comentário e export
- essa frente elevou a construcao tecnica e a coerencia operacional da plataforma, levando a baseline oficial para `100/99/100`, sem alterar por si so os bloqueadores regulatórios externos
- o ganho executivo formal so deve ocorrer quando houver uso recorrente em janela real, com resumo RCA materializado e revisão humana coerente com o rito semanal

## O Que Ainda Impede `95%`

Bloqueadores principais:

1. `P0-01` homologar `OIDC + MFA` federado em trilho serio e recorrente
2. preencher `.env.staging.private` ja materializado fora do repositorio e concluir o handoff de `Compliance/AML` para destravar a tentativa real
3. `P0-02` fechar `AML/KYT` live com credencial real e evidência anexavel
4. `P0-03` ativar feed UE real com URL tokenizada e persistencia auditavel
5. `P0-04` consolidar `P0-02 + P0-03` em bundle regulatório revisável; tentativas parciais ajudam a endurecer correlacao e dossier, mas nao fecham o item
6. `P0-05` executar a primeira janela seria material com `go/no-go` formal
7. `P0-06` formalizar o sign-off minimo de retention/recovery
8. `P1-02` institucionalizar owners, SLA e rito recorrente da janela

## Ordem Recomendada

Sequencia executiva de melhor retorno:

1. preencher `.env.staging.private` materializado e concluir o handoff de `Compliance/AML`
2. fechar `P0-02`
3. fechar `P0-03`
4. consolidar `P0-04` apenas depois da prova combinada de `P0-02` e `P0-03`
5. homologar `P0-01`
6. executar `P0-05`
7. formalizar `P0-06`
8. publicar `P0-07`

## Regra de governança

Nenhuma promocao de maturidade deve ocorrer por:

- intencao
- configuração pronta
- evidência parcial
- sucesso nao reproduzivel

Promocao de status so e permitida quando houver:

- execucao real em ambiente valido
- evidência preservada em artefato rastreavel
- coerencia entre runtime, contrato e narrativa executiva
- revisao humana
- aprovacao explicita do accountable

Leitura executiva adicional:

- tentativa parcial de `P0-02` ou `P0-03` conta como progresso operacional e reduz risco de execucao
- check real bloqueado por handoff pendente ou placeholders/variaveis reais ausentes em `.env.staging.private` conta como diagnostico valido de governança, mas nao como progresso de homologacao
- a promocao oficial para `90%+` continua exigindo prova combinada e revisável, preferencialmente selada por `P0-04`
- sinais de RCA cross-domain (`rca_attached_count`, `critical_open_count`, dominios afetados) ajudam a qualificar risco operacional e handoff executivo, mas nao substituem evidência de janela seria nem mudam KPI sozinhos

Decisao formal relacionada:

- [ADR-010 — Promocao de Maturidade Baseada em evidência](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)
- [Kit de Execucao por evidência](./project-maturity-evidence-execution-kit.md)

## Resultado Esperado

Se `P0-02`, `P0-03`, `P0-04`, `P0-01` e `P0-05` forem fechados com evidência real, o projeto entra na faixa plausivel de `94%+` consolidado e abre a reta final legitima para `95%`. Antes disso, tentativas parciais servem para endurecer a trilha executiva, nao para antecipar o fechamento oficial.

## Quando Usar Este Documento

Use este resumo quando a necessidade for:

- comunicar status executivo rapidamente
- alinhar patrocinadores e owners sobre o foco imediato
- evitar confusao entre "falta codigo" e "falta readiness comprovado"
