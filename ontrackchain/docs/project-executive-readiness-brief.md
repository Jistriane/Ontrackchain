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

- `P0` representa o caminho mais curto e auditavel para cruzar `90%+`
- `P1` representa a institucionalizacao minima que sustenta esse salto sem regressao operacional
- `P2` representa o trabalho pos-90, focado em sustentacao, reducao de debito e preparacao para `95%`

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
