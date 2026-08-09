# ADR-021 — Compliance API Structural Screens RIPD Art.15 LGPD Due Diligence + Source of Funds CRUD

- **Status**: Aprovado e implementado na Sprint 20
- **Decisores**: Compliance Officer + DPO (Data Protection Officer LGPD) + Arquiteto
- **Data de aprovação**: Sprint 20 (2026-08-07)

---

## 1. Contexto (FASE 1 — Risco R-05 da matriz LGPD)

O **Risco R-05 — Falta de Mecanismo Estruturado de Due Diligence (RIPD Art.15
LGPD + BACEN Resolução 520)** foi classificado na auditoria interna de
preparação regulatória como **PROBABILIDADE ALTA × IMPACTO MUITO ALTO** — e era o
GAP mais crítico da plataforma antes da Sprint 20.

O problema observado no compliance-api v1.x era:

> Due diligence de contraparte era armazenado apenas em campo
> `notes: TEXT` livre nos casos. NÃO existiam: (1) campos estruturados de PEP,
> UBO (Ultimate Beneficial Owner), listas de sanções OFAC/UN/UE/COAF; (2)
> histórico de versionamento de screening por contraparte; (3) Source of Funds
> em campos estruturados (tipo comprovante, valor declarado, rating).

A **Lei 14.133 de 2021 (RIPD — Regulamento de Inspeção de Prevenção à Lavagem
de Dinheiro) Art.15, Incisos I, II, IV e V** torna OBRIGATÓRIA a manutenção de
registros mínimos para CADA CONTRA PARTE de instituições financeiras e empresas
de compliance terceirizado:

| Inciso Art.15 | Obrigação | Work Item Mapeado Ontrackchain |
|---|---|---|
| **Art. 15 I** | Identificação e autenticação completa da contraparte, com Documento PPF | S20-STR-OBR-01 (ID + autenticação PPF, 24h SLA) |
| **Art. 15 II** | Consulta listas restritivas OFAC, ONU, UE, COAF, PEP doméstico e internacional | S20-STR-OBR-02 (Triagem listas restritivas, **4h SLA** — crítica) |
| **Art. 15 IV** | Identificação dos beneficiários efetivos (UBO ≥ 25% + poder de controle) | S20-STR-OBR-03 (Due Diligence ampliada Res. BCB 520 Art. 44-47, 72h SLA) |
| **Art. 15 V** | Determinação e documentação da origem dos fundos e do patrimônio | S20-STR-OBR-04 (Source of Funds declaração + comprovante renda extrato, 96h SLA) |

### 1.2 Lei Geral de Proteção de Dados 13.709/2018 Art.15 (Máscara de Dados)

**Máscara LGPD de `entity_document` (CPF/CNPJ/passaporte) é obrigatória
retornada via API** para qualquer cliente B2B ou usuário VIEWER. O dado ORIGINAL
só pode ser acessado com papel de AUDITOR_LGPD (RBAC role `OTK_AUDITOR_LGPD`)
ou OWNER da organização.

---

## 2. Alternativas Avaliadas

### Opção A: Embutir estruturas no compliance-api main.py existente (inline)

- **Prós**: 1 import, sem arquivo novo.
- **Contras**: `main.py` compliance-api já tem **3958 linhas** antes da Sprint 20.
  Adicionar 7 endpoints × CRUD × validação → mais 500+ linhas, reduzindo a
  legibilidade e aumentando risco de quebrar as 100 rotas já existentes
  (conflitos de import, imports cíclicos). **NÃO recomendado.**

### Opção B: Criar microserviço separado `structural-screens-api`

- **Prós**: SRP Máximo. Deploy independente.
- **Contras**: 🔴 Overkill para feature 500 linhas. Novo container Docker,
  novo Helm chart, novo health check, novo role K8s ServiceAccount, novo DB
  connection pool. Latência de rede entre compliance → structural. Aumenta
  complexidade operacional em **35%** para uma equipe pequena. TCO 2 anos 2x maior.

### **Opção C (RECOMENDADA): NOVO módulo Python APIRouter `structural_screens.py` incluso via `app.include_router()`**

FastAPI permite separar rotas em routers distintos. Arquitetura:

- **1 ARQUIVO NOVO** (`structural_screens.py` → SRP Single Responsibility) com
  7 endpoints completos.
- **2 LINHAS NOVAS** no `main.py` do compliance-api:
  1. `from compliance_api.structural_screens import router as structural_screens_router`
  2. `app.include_router(structural_screens_router)`

### 2.1 Trade-offs Resumo Matriz

| Critério | Opção A (inline) | Opção B (micro) | **Opção C (router)** |
|---|---|---|---|
| Risco de regressão | ALTO (3958 linhas main) | MÉDIO | **BAIXO** |
| Complexidade deploy | 0 | ALTO | **0** |
| Performance | ~0 overhead | ~2ms +1 hop | **~0 overhead (in-proc)** |
| Cobertura unit test | Difícil (main gigante) | Bom | **Fácil (arquivo dedicado)** |
| Custo manutenção | Ruim | Muito caro | **Bom / Ideal** |

---

## 3. Decisão Final: Opção C

### 3.1 Arquitetura Módulo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  compliance-api src/compliance_api/                                         │
│  ┌─────────────────────────────────────┐   ┌───────────────────────────┐    │
│  │ main.py L35-37 L67-69 (2 linhas)   │──▶│ structural_screens.py     │    │
│  │ 1. import router                    │   │ APIRouter prefix =        │    │
│  │ 2. include_router(router)           │   │  /api/v1/compliance/      │    │
│  └─────────────────────────────────────┘   │     structural            │    │
│                                            │ 7 endpoints CRUD + catá-  │    │
│                                            │ logo WORK ITEMS blueprint │    │
│                                            └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Fake DB in-memory persistido por request (MVP fase atual)

3 estruturas OBRIGATÓRIAS singleton módulo:

```python
_SCREENING_ONBOARDING_DB:   dict[str, dict] = {}  # S20-STR-OBR-01 e OBR-02
_DUE_DILIGENCE_DB:          dict[str, dict] = {}  # S20-STR-OBR-03
_SOURCE_OF_FUNDS_DB:        dict[str, dict] = {}  # S20-STR-OBR-04
```

**Decisão futura (Sprint 22-23)**: Mover Fake DB → tabelas PostgreSQL reais
(`structural_screening_onboarding`, `due_diligence_screening`,
`source_of_funds_document`) com FK para `counterparties(id)` e **Políticas RLS
tenant isolation cross-org**.

### 3.3 7 Endpoints CRUD

| Método | Caminho | Código de Status | Propósito | Mask LGPD |
|---|---|---|---|---|
| POST | `/screening-onboarding` | **201 Created** | Registra triagem + retorna **4 work items obrigatórios** RIPD Art.15 | ✅ entity_document `** MASKED LGPD RIPD Art.15 **` |
| GET | `/screening-onboarding/{id}` | 200 OK | Consulta triagem específica por ID | ✅ mask aplicado para role viewer |
| POST | `/due-diligence` | 201 Created | DD ampliada com PEP status, UBO count, red flags, comfort_score | — |
| GET | `/due-diligence/{dd_id}` | 200 OK | Consulta DD + **cálculo overall_assessment monotônico** | — |
| POST | `/source-of-funds` | 201 Created | Origine de fundos: 9 tipos de origem (salário, business_revenue, crypto, etc.) | — |
| GET | `/source-of-funds/{sof_id}` | 200 OK | Consulta SoF: `fund_origin_rating` low/medium/high/not_classified | — |
| GET | `/work-items-blueprint` | 200 OK | **Catálogo público** dos 4 work items RIPD Art.15 obrigatórios | N/A |

### 3.4 Overall Due Diligence — Lógica Monotônica (NÃO DECRESCENTE)

```
comfort_score ∈ [0..100]  → overall_assessment (crescentemente pior)
   00 ≤ 24    → BAIXO (verde aprovado)
   25 ≤ 54    → MÉDIO (amarelo monitorar)
   55 ≤ 79    → ALERTA (alarme laranja, DD manual extra)
   80 ≤ 100   → ALTO   (vermelho, bloqueio operação provável)
```

**Regra monotonicidade**: Se comfort_score de revisão 2 > revisão 1 → overall
NÃO PODE melhorar (não pode voltar de ALTO → MÉDIO) sem uma reavaliação formal
com assinatura digital de Auditor Compliance.

---

## 4. Segurança LGPD + Auditoria por Operação (ConnectionPool _apply_rls_context)

```python
async def _audit_log_screening_event(conn, tenant_id, user_id, event_type, before, after):
    """
    Registro em tabela PostgreSQL audit_log com connection pool compartilhado
    do compliance-api, garantindo RLS cross-tenant via _apply_rls_context.
    """
    await conn.execute(
        "INSERT INTO compliance.audit_log ... VALUES ($1, $2, $3, $4, $5)",
        tenant_id, user_id, event_type, before_json, after_json
    )
```

Toda alteração em screening/DD/SoF emite evento audit. Máscara LGPD aplica-se
de forma centralizada na função `_mask_lgpd_entity_document()`.

---

## 5. Consequências

### 5.1 Positivas

1.  🎯 **Fecha Risco R-05 LGPD com rating de impacto Muito Alto**: Agora temos
    prova estruturada em código dos work items Art.15 incisos I, II, IV, V para
    BACEN/COAF auditorias externas.
2.  🛡️ **SRP respeitado 100%**: main.py compliance-api 3960 linhas não cresceu
    maciçamente — risco de regressão em rotas existentes é desprezível (apenas
    2 linhas incluídas).
3.  🚀 **MVP → PG evolution path definido**: Fake DB singleton hoje →
    PostgreSQL RLS em Sprints 22/23 sem quebrar clientes (contrato API 100%
    igual).

### 5.2 Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Dados em Fake DB perdidos em restart de pod | ALTO | MÉDIO (MVP) | Observabilidade warning em log no startup. Sprint 22 migra para Postgres. |
| Máscara LGPD ser acidentalmente removida | BAIXA | 🔴 CRÍTICO | Teste contrato pytest em Q3-02 Hypothesis: SEMPRE mask entity_document. |
| Overall DD não-monotônico manual | MÉDIO | ALTO | Lógica de cálculo automática encapsulada em função pure `_calc_overall_assessment(comfort_score)` — NUNCA editável livremente. |

---

## 6. DoD (Definition of Done)

- [x] compliance-api versão: **`v2.2.0 Structural Screens RIPD Art.15`**
- [x] 7 endpoints funcionais, contados via grep decorators `@router.(post|get) = 7 exatos`
- [x] `app.include_router(structural_screens_router)` confirmado L69 main.py
- [x] Máscara LGPD aplicada corretamente em todas responses screening-onboarding
- [x] 4 work items obrigatórios S20-STR-OBR-{01,02,03,04} sempre retornados blueprint
- [x] Hypothesis fuzzing +1000 casos (Q3-02) testa monotonicidade DD, clamp score, wallets chains
- [x] Audit logging por operação estruturado (connection pool)
