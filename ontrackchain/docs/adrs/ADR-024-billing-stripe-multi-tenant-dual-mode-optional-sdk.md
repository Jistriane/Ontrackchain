# ADR-024 — Billing Stripe Multi-Tenant com DUAL MODE (SDK Oficial Opcional + Fake Fallback Idêntico)

- **Status**: Aprovado e implementado na Sprint 22
- **Decisores**: Arquiteto de Backend + Head de Engenharia + Produto Billing
- **Data de aprovação**: Sprint 22 (2026-08-09)

---

## 1. Contexto

O roadmap de faturamento para Q3 exigia integração com gateway de pagamento
Stripe (referência global SaaS B2B). O problema do início da Sprint 22 foi:

1.  **Pipeline CI NÃO pode instalar SDK Stripe por padrão**: Sem a variável
    `STRIPE_API_KEY=sk_test_...` os testes locais ou de CI quebravam com
    `stripe.error.AuthenticationError`. NÃO podemos expor secrets no CI.
2.  **Desenvolvedores do frontend e do investigation-core devem rodar `pytest`
    sem ter stripe instalado localmente**: O módulo `investigation-api` tem
    370+ testes de outras áreas (cases, audit, rpc_provider, dlq, reconciliation)
    e a ausência de stripe SDK NÃO pode regredir nenhum desses testes.
3.  **Contrato de API deve ser 100% idêntico entre "modo de desenvolvimento" e
    "produção":** Frontend, QA, e testes E2E NÃO podem saber internamente se
    estão usando Stripe real ou Fake — preço, status, session_id, portal_url,
    side effects precisam ser indistinguíveis exceto `provider_mode` no response.

**4 RNF Obrigatórios ADR-024:**
1.  `pip install investigation-api` → SEM stripe instalado → funciona 100%.
2.  `pip install investigation-api[stripe]` → com stripe SDK ≥9 → usa stripe oficial.
3.  Nenhum import-level de `stripe_stripe_lib` (renomeado para evitar conflito) que quebre import do módulo.
4.  Webhook assinatura HMAC `Stripe-Signature` validada mesmo em modo Fake (testar contrato localmente sem ter conta Stripe).

---

## 2. Requisitos Funcionais Mapeados (5 Endpoints Billing)

| Endpoint `/api/v1/billing/stripe/*` | Método | Propósito | DUAL MODE |
|---|---|---|---|
| `GET /pricing` | GET | Catálogo 3 tiers × 3 moedas (9 entradas) | Mesmo contrato. Price IDs canônicos `price_{tier}_{currency}`. |
| `POST /checkout/session` | POST | Criar sessão checkout → 201 Created | Fake retorna `cs_xxx` + URL `https://checkout.stripe.com/fake/...`. |
| `POST /customer-portal/session` | POST | Customer Portal Stripe | Fake retorna `bps_xxx` + URL fake portal. |
| `GET /subscription/{org_id}` | GET | Skeleton default startup/brl/incomplete | Mesma estrutura Pydantic. |
| `POST /webhook` | POST | HMAC verify + idempotência + side effects | HMAC FAKE_WHSEC local + event_id idempotente. |

---

## 3. Alternativas Avaliadas (3 Opções + Trade-offs)

### Opção A: Sempre instalar SDK Stripe + mock global via `unittest.mock.patch()`

- **Prós**: Implementação tradicional; muita equipe familiarizada.
- **Contras**:
  1.  **Quebra 100% de cobertura CI sem `.env.stripe`**: O import de stripe no nível
      módulo (fora de função) eleva `ImportError` antes de qualquer mock poder atuar.
  2.  Risco de testes passarem em mock e falharem em staging por incompatibilidade contrato mock↔real.
- **Custo de manutenção**: Alto (mock é frágil a mudanças de SDK Stripe).

### Opção B: Feature flag `BILLING_ENABLED=false` global. Routes só carregam se true.

- **Prós**: Zero dependência opcional; CI sem stripe simplesmente não carrega router.
- **Contras**: 🚨 **Quebra requisito "Contrato 100% idêntico"**: QA não consegue
  testar fluxo /pricing e /checkout em ambiente local sem stripe = risco de
  regressão pós-deploy. Frontend build showcase (vitrine pública) NÃO teria tela de planos.
- **Custo de manutenção**: Baixo porém não entrega valor de negócio.

### **Opção C (RECOMENDADA): DUAL MODE via lazy import try/except no nível módulo + SDK como optional-deps `[stripe]`**

- **Prós**:
  1.  **Nível módulo NUNCA quebra**: `try: import stripe as stripe_lib as _STRIPE_AVAILABLE=True`
      se falhar → `_STRIPE_AVAILABLE=False` e todo router instancia. Contrato 100% idêntico.
  2.  **CI 100% verde sem nenhuma variável**: O teste 01 do catálogo funciona com
      Fake Fallback; o teste 12 do contrato webhook HMAC usa `FAKE_STRIPE_WHSEC` local.
  3.  **Padrão reutilizável S22→forward**: Estabelecemos uma receita para toda nova
      integração de terceiros (AML provider, Chainalysis, S3 externo, etc).
  4.  **Optional-deps `[stripe]` group**: `pip install investigation-api[stripe]`
      ativa modo oficial. Nenhuma quebra para quem não usa.
- **Contras**: Módulo billing tem ~15% de linhas a mais por ter o Fake Fallback.
- **Custo de manutenção**: Médio-baixo (stripe SDK v9 é estável; breaking changes ~1/ano).

---

## 4. Decisão Final: Opção C

**Justificativa baseada em 4 perguntas do arquiteto:**

| Pergunta | Resposta |
|---|---|
| (1) Fecha objetivo de negócio? | ✅ Sim. Monetização real 3 planos, 3 moedas, Customer Portal. |
| (2) Restrições técnicas e seg? | ✅ M5 intacto. Sem secrets no CI. Nenhum env obrigatório para pytest. |
| (3) Atributos qualidade? | ✅ Disponibilidade (CI 100% verde) + Segurança (HMAC verify) + Manutenibilidade. |
| (4) Opção mais barata/risco? | ✅ Opção mais barata (nenhum trabalho extra de mock por teste) e menos risco. |

---

## 5. Trade-offs Aceitos e Riscos

1.  **Aceito**: 15% linhas extras Fake Fallback → trocado por CI zero-falha + contrato idêntico.
2.  **Risco baixo**: Stripe v10 fizer breaking changes → atualizar optional-deps pin `stripe>=9,<10`
    primeiro em staging, depois validar side effects; processo simples.
3.  **Risco médio mitigado**: Em produção, alguém instalar sem [stripe] e tentar live →
    `provider_mode` no response sempre retorna "fake-stripe-fallback" para facilitar detecção,
    e emitir warning startup se `STRIPE_API_KEY` está setado porém SDK não instalado.

---

## 6. Definition of Done (DoD) — Sprint 22

| Critério | Status |
|---|---|
| pyproject.toml investigation-api com optional-deps group `[stripe] = ["stripe>=9.0.0"]` | ✅ |
| investigation-api versão bump 0.1.0 → 1.2.0 | ✅ |
| billing_stripe.py SRP router 5 endpoints | ✅ |
| 3 Fake DB singleton (_ORG_SUBSCRIPTIONS_DB, _WEBHOOK_EVENTS_LOG, _ORG_TO_STRIPE_CUSTOMER_ID) | ✅ |
| main.py `include_router(billing_stripe_router)` (2 linhas) | ✅ |
| Stripe-Signature HMAC verify + idempotência event_id | ✅ |
| 6 side effects aplicados (invoice paid, checkout completed, sub created/updated/deleted, payment failed) | ✅ |
| 12 pytest contrato (catalog 4 / checkout+portal 3 / sub+HMAC+idemp 5) | ✅ |
| Nenhum CI break sem stripe instalado | ✅ |

---

## 7. Consequências Futuras

**Governança**: Para toda nova integração com provedor 3rd-party (AML Provider, Chainalysis,
S3 external, Elliptic, TRM Labs) — ADOTAR obrigatoriamente DUAL MODE pattern,
com optional-deps group, Fake Fallback contrato idêntico, e 10+ pytest contrato modo Fake.

**Próximos passos S23 T2-10**: Usage Meters e enforcement de rate limits por tier
(Startup: 5 usuários máx, Business ilimitado básico, Enterprise AI credits).
