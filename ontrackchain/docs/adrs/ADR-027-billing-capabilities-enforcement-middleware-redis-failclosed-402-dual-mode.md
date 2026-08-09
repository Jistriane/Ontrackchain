# ADR-027 — Billing Capabilities Enforcement Middleware (Redis Compartilhado + Fail-Closed 402 + DUAL MODE Opcional)

- **Status**: Aprovado Sprint 24
- **Decisores**: Arquiteto de Software + Compliance BACEN + Head de Engenharia
- **Data de aprovação**: Sprint 24 (2026-08-09)

---

## 1. Contexto

A **Fonte Única da Verdade `OTK_PLAN_CAPABILITIES` (Sprint 23 T2-10)** define 3 tiers
com 22 capabilities cada, **mas não tem enforcement**. Em 2026-Q4 a entrada do
primeiro cliente Business B2B (cota de 2.000 req/h B2B, AI credits 50k/mês)
exige validação *antes* de consumir recursos da API — caso contrário
**contornar tier é trivial** via frontend e a auditoria BACEN Circular 3.978
(Art. 16 — Controles de acesso e trilha de auditoria) reprovará.

### 4 RNF Obrigatórios que geram o ADR:
1.  **Fail-Closed (PADRÃO)**: Qualquer falha de consulta ao Redis / billing
    storage → bloqueio imediato HTTP 402 Payment Required com X-Correlation-ID.
    NUNCA fail-open em tier Business / Enterprise.
2.  **Contadores Compartilhados (Redis Obrigatório ≥ 2 Pods)**: `b2b_api_calls_per_hour_quota`
    e `included_ai_credits_per_month` são globais por organização em todas as
    réplicas do investigation-api. In-memory por Pod NÃO serve multi-pod.
3.  **DUAL MODE (Compatível CI)**: Se `redis-py-cluster` NÃO estiver instalado
    OU `OTK_REDIS_URL` não configurado, fallback transparente para `InMemoryBillingCounter`
    monolítico — só recomendado staging 1 pod / CI local.
4.  **Headers Sempre Presentes**: Toda resposta, sucesso ou falha 402, tem 5
    headers canônicos (X-RateLimit-Limit / Remaining / Reset; X-Billing-Tier;
    X-Billing-AI-Credits-Remaining) para frontend e B2B clients implementarem
    grace UI.

---

## 2. Capabilities Enforcement Implementadas por este ADR

| Capability `OTK_PLAN_CAPABILITIES[tier][key]` | Middleware enforce | Counter Redis | HTTP Code se exceder |
|---|---|---|---|
| `b2b_api_calls_per_hour_quota` (startup=200 / business=2.000 / enterprise=10.000) | ✅ `Depends(enforce_capability("b2b_hourly_quota"))` | `billing:b2b:{org_id}:{YYYYMMDDHH}` 1h sliding | 429 Too Many Requests |
| `included_ai_credits_per_month` (2.500 / 50.000 / 1.000.000) | ✅ `Depends(enforce_capability("ai_credits"))` em rotas `ai_service/*` | `billing:ai:{org_id}:{YYYYMM}` 30d | 402 Payment Required |
| `max_users_per_org` (startup=5 / business=enterprise=None ilimitado) | ✅ em `POST /users/invite` only | Counter set `billing:users:{org_id}` | 402 Payment Required |
| `graph_intelligence_layouts_allowed` (startup=[cose,grid], business=+cola+breadthfirst, enterprise=+forceatlas2+concentric) | ✅ em `POST /graph/layout` | N/A (validação direta SSOT) | 403 Forbidden |
| `has_sso_saml_oidc_federation` (enterprise only) | ✅ no authz `SSO callback` | N/A | 401 Unauthorized |
| `has_rbac_custom_roles` (business=False, enterprise=True) | ✅ em `POST /roles/custom` | N/A | 403 Forbidden |

---

## 3. Alternativas Avaliadas (3 Opções + Trade-offs)

### Opção A: In-memory contadores por Pod (sem Redis) — "simples, rápido"

- **Prós**: Nenhuma nova dependência, zero setup local.
- **Contras**:
  1.  🔴 **Quebra RNF 2 (Compartilhado)**: Investigation-api rodando 3 pods em
      staging → cliente Business 2.000 req/h real pode chegar a **6.000 req/h**
      (2.000 × 3 pods = contagem independente cada). Vazamento de cota.
  2.  Contador AI Credits resetado em cada deploy (Pod restart). Contadores
      sobem e descem sem trilha.
- **Complexidade implementação**: 4h.
- **Adequação**: ❌ Rejeitada — BACEN Circular 3.978 Art.12 Consistência de Dados.

### Opção B: PostgreSQL tabela `billing_usage_events` com triggers row-level — "sem Redis, usa PG16 existente"

- **Prós**: Usa PG16 já existente; tabela auditável por LGPD Art.15.
- **Contras**:
  1.  🟠 **Problema Performance 1**: Cada B2B request (pico 50 VUs Q3-04) = 1 INSERT
      + 1 SELECT SUM GROUP BY. Gera **2 I/O DB por request de leitura simples**.
      k6 01-public-api-b2b-screening.js P95<500ms → vira P95 ~850ms (sob carga).
  2.  🟠 **Problema Race**: 2 requests simultâneos na mesma org não veem o
      contador do outro em `READ COMMITTED`; precisa `SELECT ... FOR UPDATE`
      (serialização) que reduz throughput AI creditos em 50%.
- **Complexidade implementação**: 12h + 4h tuning índices.
- **Adequação**: ⚠️ Não recomendada para hot path de enforcement. PG bom para
  auditoria (fora do request hot path), RUIM para contadores low-latência.

### Opção C (RECOMENDADA): Redis Obrigatório + DUAL MODE InMemory Fallback

- **Prós**:
  1.  ✅ **Latência ~0.3ms por enforcement**: Redis local no mesmo node (cluster K8s) =
      k6 P95 B2B < 500ms se mantém; `INCR` é atômico (sem race condition).
  2.  ✅ **TTL nativo**: 1h sliding B2B (`EX 3600`) e 30d AI (`EX 2592000`). Reset automático.
  3.  ✅ **DUAL MODE**: CI/dev sem Redis funciona via InMemory; staging/prod 2+ pods tem Redis obrigatório.
  4.  ✅ **Fail-Closed nativo**: `ConnectionError` do Redis retorna HTTP 402 imediatamente
      + log estruturado `level=critical`. Nenhum request passa despercebido.
- **Contras**:
  1.  Nova dependência: `redis-py >= 5.0.0` optional group `[billing-redis]` no
      investigation-api. Helm values `redis.enabled=true` em prod.
  2.  Precisa monitoramento Redis: `redis_memory_used_bytes`, `connected_clients`,
      `connected_slaves` (Prometheus + Redis Exporter).
- **Complexidade implementação**: 8h (baixa).
- **Adequação**: ✅ Recomendada arquitetura. Balanceamento ideal performance/risco.

---

## 4. Decisão — Opção C (Redis Compartilhado + DUAL MODE + Fail-Closed 402)

Stack tecnológico associado a este ADR:
- Middleware Python FastAPI: `Depends(enforce_capability(...))`
- Redis ≥ 7.2 standalone ou Redis Cluster 3 shards (>= 3 pods enterprise)
- Opcional group pip: `ontrackchain-investigation-api[billing-redis]`
- Helm chart investigation-api adiciona `env.OTK_REDIS_URL=redis://...:6379/0`

### 3 Padrões Obrigatórios de Segurança:
1.  **CEI (Checks-Effects-Interactions) adaptado para Middleware**:
    1.  Checks: autenticação org_id valido, RBAC login correto.
    2.  Effects: INCR Redis counter.
    3.  Interactions: chama função business logic APENAS se counter <= limite.
2.  **Não usar tx.origin pattern**: validação sempre `msg.sender` equivalent →
    `request.state.current_organization_id` (nunca confia em path param org direto).
3.  **Rate limit global por IP adicional** em `/healthz`/`/readyz` (NÃO cobrir
    billing — NÃO podemos bloquear monitoramento por billing excedido).

---

## 5. Trade-offs e Riscos Identificados

| Risco | Probabilidade | Impacto | Estratégia de Mitigação |
|---|---|---|---|
| **R-027-01**: Redis em produção OOM (out of memory) por AI credits enterprise 1M de orgs | Baixa (10%) | Alto (todos 402) | `maxmemory-policy noeviction` + alert Prometheus `used_memory > 70%`. Alert fire 24h antes de OOM |
| **R-027-02**: Redis indisponível 5 min por update K8s → todos B2B com 402 | Média (30%) | Alto | Istio circuit breaker `outlierDetection` 50% 30s; fallback em segundo Redis réplica read-only |
| **R-027-03**: Engenheiro muda `OTK_PLAN_CAPABILITIES` business AI credits de 50k→500 por engano | Baixa (15%) | Médio | qa-gateway scan-billing-capabilities BW-003 monotonicidade validado em PRE-MERGE HOOK; + novo comando scan-billing-enforcement Q3-06 |
| **R-027-04**: DUAL MODE InMemory usado em PROD por erro config (env OTK_REDIS_URL apagado) | Baixa (10%) | Alto | qa-gateway scan-billing-enforcement BE-004: valida se `deployment.yaml` tem `redis.enabled=true` em namespace prod → BE issue. |

---

## 6. Definition of Done (ADR-027) — 6 Itens Obrigatórios

- [ ] **DoD 027.1** Módulo SRP `investigation-api billing_enforcement.py` existe
      com 2 classes: `RedisBillingCounter` + `InMemoryBillingCounter` DUAL MODE.
- [ ] **DoD 027.2** Função `enforce_capability(capability: str)` como `Depends`
      assíncrona: usa Redis se disponível, senão InMemory. Emite WARNING log se
      fallback InMemory ativo.
- [ ] **DoD 027.3** Headers X-RateLimit / X-Billing inseridos em todas as
      respostas (através de `APIRouter` response event handler global billing).
- [ ] **DoD 027.4** 15 pytest contrato `test_billing_enforcement_t2_11.py`:
      monotonicidade counters, fail-closed em `RedisConnectionError`, fallback
      InMemory, headers presentes, 402/429 corretos.
- [ ] **DoD 027.5** qa-gateway NOVO subcomando `scan-billing-enforcement`
      Q3-06: 4 warnings BE-001..BE-004 (módulo ausente / include middleware
      ausente / monotonicidade / prod sem Redis). STRICT default True.
- [ ] **DoD 027.6** README.md atualizado + linha S24 Tabela Consolidado
      S24-T211 + Baseline v1.3 materialidade 95%→96%.

---

## 7. Referências Cruzadas

- **ADR-019 Public API v2 B2B HMAC**: Middleware enforcement roda *DEPOIS* do
  HMAC verify de ADR-019 (ordem: HMAC → Billing Enforce → Business Logic).
- **ADR-025 k6 Thresholds SLA**: P95<500ms do 01-public-api-b2b-screening.js é
  garantido aqui (Redis INCR < 1ms adicionado).
- **T2-10 Billing Capabilities SSOT (Sprint 23)**: `investigation_api.billing_capabilities.OTK_PLAN_CAPABILITIES`.
  É a ÚNICA fonte permitida de limites — NUNCA ler de tabela PG.
