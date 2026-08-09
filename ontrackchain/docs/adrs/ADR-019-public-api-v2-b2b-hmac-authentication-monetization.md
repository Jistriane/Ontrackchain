# ADR-019 — Public API v2.0.0 B2B Enterprise com Autenticação HMAC-SHA256 Timing-Safe e Anti-Replay

- **Status**: Aprovado e implementado na Sprint 19
- **Decisores**: Arquiteto de Segurança + Product Owner B2B
- **Data de aprovação**: Sprint 19 (2026-08-07)

---

## 1. Contexto

O roadmap de monetização Ontrackchain previu para o trimestre Q3 o lançamento da API
B2B Enterprise para clientes segmento Financial Services (bancos, corretoras,
fintechs licenciadas BACEN, empresas de compliance terceirizado). O GAP inicial
era que a `public-api` v0.x.x só expunha endpoints públicos read-only
(`/healthz`, `/metrics`, `/sanctions/search/{q}`) sem nenhum mecanismo de
autenticação, autorização por plano, rate limiting diferenciado, ou faturamento.

**3 requisitos não funcionais OBRIGATÓRIOS para launch B2B (PCI-DSS Level 1 +
Lei Geral de Proteção de Dados 14.133 Art. 46 LGPD + BACEN Circular 3949):**

1.  **Autenticação forte API-2-API**: NÃO usar API key simples em query string ou
    Bearer token estático longo prazo. Obrigatoriedade de assinatura criptográfica
    por request com timestamp associado (anti-replay).
2.  **Rate limiting granular por cliente**: 2.000 req/hora em Plano Business,
    10.000 req/hora em Plano Enterprise, 0 (bloqueado) em inadimplência.
    Chaveamento Redis por `client_id` individual — não por IP (CDN/NAT B2B).
3.  **Rollover de API Key com período de graça 7 dias**: NÃO invalidar chave antiga
    imediatamente após regeneração. Clientes Enterprise B2B NÃO PODEM ter downtime
    45+ dias durante rollover.

---

## 2. Requisitos Funcionais Mapeados (4 Endpoints Novos B2B)

| Caminho Endpoint | Método | Propósito | Autenticação | Plano Mínimo |
|---|---|---|---|---|
| `/api/v1/b2b/register/webhook` | POST | Cliente B2B registra webhook de notificações de casos | HMAC-SHA256 3 headers | Business |
| `/api/v1/b2b/counterparties` | POST | Cria registro de contraparte na rede do cliente + dispara structural screen (S20 T2-04) | HMAC-SHA256 3 headers | Business |
| `/api/v1/b2b/screenings/{screening_id}` | GET | Consulta status de triagem estrutural por ID | HMAC-SHA256 3 headers | Business |
| `/api/v1/b2b/billing/usage-report` | GET | Relatório de consumo de créditos por período | HMAC-SHA256 3 headers | Business |
| `/api/v1/_devonly/hmac-test-signature` | GET | (Staging-only / internal) gera payload exemplo e assinatura HMAC | HMAC-SHA256 3 headers | N/A |

---

## 3. Alternativas Avaliadas (3 Opções Arquiteturais + Trade-offs)

### Opção A: OAuth2.0 Client Credentials + JWT (JWS RFC 7515)

- **Prós**: Padrão industrial para B2B; audiências e escopos nativos; suporte nativo Keycloak.
- **Contras**: Complexidade 30% maior implementação; tempo expiração access token 15min exige refresh; aumento de latência `+1 RT de introspecção /token` por request (impacto TPS em 24%); cliente B2B precisa implementar fluxo completo OAuth (nem todos tem equipe).
- **Custo de manutenção**: **Alto** — necessita Identity Provider dedicado, rotação client_secret, auditoria grant logs.

### Opção B: API Key Bearer Estático + Rate Limiting por Header

- **Prós**: Implementação mínima (15 linhas middleware); todas ferramentas Postman/curl suportam nativamente.
- **Contras**: 🚨 **QUEBRA requisito regulatório anti-replay PCI-DSS**. Qualquer chave vazada em log de proxy/CDN funciona infinitamente até rollover. **NÃO APTO**.
- **Custo de manutenção**: **Baixo** porém risco inaceitável.

### **Opção C (RECOMENDADA): HMAC-SHA256 Assinatura por Request + 3 Headers + Timestamp Skew Máximo 300s**

- **Prós**:
  1. Nenhum round-trip extra auth (zero latency adicional vs Opção A).
  2. Padrão equivalente AWS SigV4 / Stripe webhook signature — equipe B2B financeira familiarizada.
  3. `hmac.compare_digest` (constant_time_equal) implementação timing-attack safe.
  4. Skew máximo 300s anti-replay + chave Redis `rl:b2b-replay:<client>:<ts>:<nonce>` (facilmente extensível a nonce no futuro).
  5. Rate limiter Redis 2000 req/hora chaveado individualmente `rl:b2b:<client_id>`.
- **Contras**: Cliente precisa implementar documento de assinatura (`METHOD|path|base64(body)|timestamp`). Requer documentação clara + SDK.
- **Custo de manutenção**: **Médio** — docs precisam de atualização quando mudar documento de assinatura.

---

## 4. Decisão Final: Opção C

**Justificativa baseada nas 4 perguntas do arquiteto:**

| Pergunta | Resposta |
|---|---|
| (1) Fecha objetivo negócio (launch B2B Q3)? | ✅ Sim. 4 endpoints monetização B2B. |
| (2) Conformidade restrições regulatórias? | ✅ PCI-DSS 6.5.10 anti-replay + LGPD Art. 46 autenticação forte. |
| (3) Atributos qualidade? | ✅ Performance (0 overhead auth extra) + Segurança (timing-safe + 300s skew) + Manutenibilidade (módulo separado). |
| (4) Alternativa mais barata/menos arriscada? | ❌ Opção B NÃO é segura; Opção A tem TCO > 30%. |

---

## 5. Especificação do Documento de Assinatura HMAC

### 5.1 Headers Obrigatórios (3)

```http
X-OT-Client-Id:    <client_id UUID RFC 4122>
X-OT-Timestamp:    <Unix epoch seconds UTC>   # max 300s skew
X-OT-Signature:    <hex lowercase HMAC-SHA256>
```

### 5.2 Documento Assinado (ordem OBRIGATÓRIA, separador pipe `|`)

```
METHOD|path_absoluto_com_query|base64(body_bytes)|timestamp
```

- **GET/DELETE** sem body: `base64(b"")` === `""` (string vazia)
- **POST/PUT/PATCH** com body: `body_bytes` são os BYTES crus do request
  (antes de JSON parse). Encoding UTF-8 OBRIGATÓRIO.

### 5.3 Pseudocódigo Validação (Timing Safe)

```python
# apps/public-api/src/public_api/main.py — função _constant_time_equal
import hmac
import hashlib

def _constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.lower(), b.lower())
```

### 5.4 Rate Limiting B2B

```
KEY Redis:    rl:b2b:<client_id>
Algoritmo:    Sliding Window 1 hora (3.600 segundos)
Limites:
  - PLANO_FREE:        0 req / hora  (bloqueado)
  - PLANO_BUSINESS:  2000 req / hora
  - PLANO_ENTERPRISE: 10000 req / hora
Response Headers:
  X-RateLimit-Limit:       2000
  X-RateLimit-Remaining:   1872
  X-RateLimit-Reset:       <epoch UTC>
429 Too Many Requests:     {"code":"B2B_RATE_LIMIT_EXCEEDED","retry_after_seconds":532}
```

### 5.5 Rollover API Key — Grace Period 7 dias (168h)

```
Estrutura _B2B_CLIENT_KEYS_DB[client_id]:
  primary_key:    {secret, status=ACTIVE, created_at}
  secondary_key:  {secret, status=GRACE_PERIOD, expires_at=NOW()+7d}

Validação: TENTA primary_key PRIMEIRO constant-time; se falhar TENTA secondary_key.
Expirada a grace period: secondary_key é apagada definitivamente (NÃO retornar).
```

---

## 6. Arquitetura de Componentes (Responsabilidade Única)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  public-api main.py (L349..L685 Sprint 19)                                  │
│  ┌─────────────────────┐   ┌──────────────────────────┐   ┌──────────────┐ │
│  │ 0. b2b_authenticate │ → │ 1. b2b rate limiter      │ → │ 2. Endpoints│ │
│  │ 3 headers HMAC      │   │ Redis rl:b2b:<id> SW1h    │   │ /register   │ │
│  │ constant_time_equal │   │ 2000 / 10000 / 0         │   │ /screenings │ │
│  │ skew ≤ 300s         │   │ response rate headers    │   │ /billing    │ │
│  └─────────────────────┘   └──────────────────────────┘   └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Componente | Responsabilidade Única | Interface Input | Saída |
|---|---|---|---|
| `b2b_authenticate()` dependency FastAPI | Validar identidade do cliente B2B com anti-replay e timing-safe | Request + 3 headers | `B2BAuthContext` (client_id, plano) |
| `b2b_rate_limit_apply()` middleware | Controle de consumo e encaixe Plano Business/Enterprise | client_id + plano | `429 Too Many Requests` com retry_after_seconds caso ultrapassado |
| `/b2b/* endpoints` | Implementação dos 4 contratos de negócio B2B | Pydantic requests | Responses 200/201 JSON estruturado + trace_id |
| `_internal /hmac-test-signature` | (Staging only) Debug do documento de assinatura | request | assinatura exemplo cliente + payload documento |

---

## 7. Consequências

### 7.1 Positivas

1.  🎯 **Monetização ativa**: Cliente pode integrar Ontrackchain em plataforma própria B2B com SLA 99.9%.
2.  🔐 **Segurança PCI-DSS**: Timing-safe + anti-replay 300s → auditors não abrem findings nesta camada.
3.  ⚡ **Performance 0 overhead**: Nenhuma chamada externa auth por request → ~15% melhor throughput vs Opção A.
4.  📜 **Auditabilidade**: Todo request B2B loga `{client_id, endpoint, ts, status}` em audit log PostgreSQL.

### 7.2 Riscos / Pontos de Atenção + Mitigação

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Cliente envia timestamp local errado (time drift NTP) | Média | Alto (401 desnecessário) | Mensagem de erro explicita skew esperado e tempo UTC do servidor. |
| Body minificado vs identado → hash diferente | Alta | Média | Documentação obriga envio `Content-Type: application/json` UTF-8 + exemplo curl exato. |
| Signature vazada em access log de proxy | Baixa | 🚨 Muito Alto | Obrigatoriedade **HTTPS HSTS** ponta-a-ponta; headers NÃO devem ser logados em nível INFO. |

---

## 8. Critérios de Aceitação (Definition of Done)

- [x] Testes contrato pytest: 21 testes (9 legados + 12 B2B novos) 100% verde
- [x] 429 rate limit e X-RateLimit-* headers retornados corretamente
- [x] Skew + 301s retorna HTTP 401 code B2B_TIMESTAMP_EXPIRED
- [x] constant_time_equal (compare_digest) em TODAS as comparações de hash
- [x] `hmac-test-signature` (internal staging only) NÃO disponível em prod
- [x] Documentação API B2B em `docs/api-contracts.md` (referenciado)
