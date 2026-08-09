# ADR-025 — Regime de Load Testing k6 com Thresholds SLA Rigorosamente Definidos por Rota Crítica

- **Status**: Aprovado e implementado na Sprint 22
- **Decisores**: Arquiteto de Qualidade + SRE + Product Owner
- **Data de aprovação**: Sprint 22 (2026-08-09)

---

## 1. Contexto

Até a Sprint 21, a única garantia de performance era:
1.  Testes de integração unitários passando (100% `pytest` de fluxo happy-path).
2.  Gatling script único legado em `tests/archive/` que não era mantido há 9 meses.
3.  Nenhum **threshold formal p95/p99** por endpoint crítico.

Problemas identificados na RCA do S14 incidente de performance (fora de produção, homologação):
- Post `/api/v1/cases` de criação tinha p95 de 1.8s em carga nominal 25VUs (acima do SLA
  "900ms orçado" mas não tinha sido medido).
- `/healthz` smoke test multi-serviço não existia formalizado = deploy de versão quebrada
  do compliance-api foi detectado tarde por erro humano manual.
- Public API B2B não tinha testes de carga com header HMAC (ADR-019), portanto ninguém
  tinha provado que 2000 req/hora do Plano Business era realmente suportado.

**4 RNF obrigatórios ADR-025:**
1.  Cada endpoint crítico do fluxo monetização B2B + regulatório LGPD tem threshold formal
    p95/p99 definido e validado por script k6.
2.  Scripts devem rodar tanto local (`k6 run tests/k6/...`) quanto em homologação
    (Kubernetes CronJob load test noturno).
3.  Cada script tem métricas customizadas por endpoint (`tags: route=X, phase=Q3-04`).
4.  Nenhum script de load testing pode ser executado em produção sem "go/no-go"
    formal de SRE + assinatura operacional.

---

## 2. Requisitos Funcionais Mapeados (4 Scripts Q3-04 Sprint 22)

| Script k6 `tests/k6/*.js` | VUs | Duração nominal | Rota Alvo | Threshold P95 | Threshold Falha |
|---|---|---|---|---|---|
| 01-public-api-b2b-screening.js | 50 VUs (ramp 10→50→0 40s) | ~40 segundos | `POST /api/v2/b2b/screening` (ADR-019 HMAC) | p95 < 500ms | http_req_failed < 1% |
| 02-structural-screening-onboarding.js | 30 VUs (ramp 5→30→0 35s) | ~35 segundos | `POST /api/v1/compliance/structural-screens` T2-04 LGPD | p95 < 650ms | http_req_failed < 1.5% |
| 03-case-management-create-case.js | 25 VUs (ramp 5→25→0 43s) | ~43 segundos | `POST /api/v1/cases` RBAC ANALYST create | p95 < 900ms | http_req_failed < 2% |
| 04-all-healthz-smoke.js | 10 VUs steady-state | 10 segundos | `GET /healthz` + `GET /readyz` 3 serviços | p95 < 120ms | http_req_failed < 0.1% (99.9% de sucesso) |

---

## 3. Alternativas Avaliadas (3 Opções + Trade-offs)

### Opção A: Apache JMeter (ferramenta Java tradicional)

- **Prós**: Muito difundido; plugins para GraphQL; UI gráfica para analistas não-desenvolvedores.
- **Contras**: XML verboso de teste (3x mais linhas que k6 JS); curva de aprendizado JVM;
  não tem suporte nativo a ES modules modernos; integração CI com Docker imagem 700MB+ vs k6 ~130MB.
- **Custo de manutenção**: Alto.

### Opção B: Artillery (Node.js based)

- **Prós**: JS simples; suporte nativo a HTTP/2; plugins GraphQL e Socket.io nativos.
- **Contras**: Performance do worker em Node.js V8 single thread = overhead maior que Go runtime do k6;
  reports nativos pagos (Artillery Pro); licença MPL-2.0 restrita vs k6 AGPL-3.0 estável.
- **Custo de manutenção**: Médio.

### **Opção C (RECOMENDADA): k6.io (Grafana Labs) v0.50+, runtime Go + módulos JS ES6**

- **Prós**:
  1.  **Runtime Go de alta performance**: k6 workers são 10x mais eficientes em VUs
      versus Artillery/JMeter single-threaded.
  2.  **Thresholds built-in industrial**: `options.thresholds.http_req_duration=["p95<500"]`
      → falha do script automaticamente se SLA for quebrado (obrigatório em CI gate).
  3.  **Suporte nativo para métricas customizadas `Rate`, `Trend`, `Counter`**: `screeningsSubmitted`,
      `structural_assessment_latency_ms`, `case_created_ms` = acompanhamento granular.
  4.  **Docker image grafana/k6:latest 130MB**: pluginável em CronJob K8s + CI/CD.
  5.  **`group()` nativo por serviço** no script 04-all-healthz-smoke = relatório segmentado.
  6.  **Padrão global SRE**: Adoção k6 por empresas do setor financeiro, BACEN Open Finance,
      Stripe, etc.
- **Contras**: k6 não tem suporte nativo a testes WebSockets bidirecionais complexos (não precisamos hoje).
- **Custo de manutenção**: Baixo; JS ES6 moderno; scripts compactos (~200 linhas cada).

---

## 4. Decisão Final: Opção C - k6

**4 perguntas do arquiteto:**

| Pergunta | Resposta |
|---|---|
| (1) Fecha objetivo de negócio? | ✅ Sim. SLA formal de performance por rota para SLA B2B. |
| (2) Conforme restrições? | ✅ M5 intacto, nenhum push. LGPD: payloads load testing são todos fake dados. |
| (3) Atributos qualidade? | ✅ Perf (runtime Go) + Mant. (JS ES6 modular) + Seg (nunca em prod sem aprovação). |
| (4) Opção mais barata/risco? | ✅ Licença gratuita Grafana Labs, stack leve, 4 scripts simples. |

---

## 5. Trade-offs Aceitos e Riscos Mitigados

1.  **Trade-off**: Não adotar WebSocket k6 agora (não precisamos).
2.  **Risco baixo**: Thresholds podem precisar de ajuste após 1ª rodada real homologação →
    thresholds são parametrizáveis via `-e K6_BASE_URL=` e `options` no topo do arquivo,
    ajuste 3 linhas por script.
3.  **Risco alto mitigado (operacional)**: Rodar load testing em PRODUÇÃO por engano →
    Cada script tem comentário topo: "NÃO executar em PROD sem go/no-go SRE". Além disso,
    `BASE_URL` default dos scripts aponta para `127.0.0.1` LOCALHOST = nunca acerta prod por acidente.

---

## 6. Definition of Done (Sprint 22)

| Critério | Status |
|---|---|
| Pasta `tests/k6/` criada na raiz workspace | ✅ |
| 01-public-api-b2b-screening.js (50 VUs P95<500ms HMAC) | ✅ |
| 02-structural-screening-onboarding.js (30 VUs P95<650ms T2-04 LGPD) | ✅ |
| 03-case-management-create-case.js (25 VUs P95<900ms 6 case types) | ✅ |
| 04-all-healthz-smoke.js (3 serviços 10 VUs 10s P95<120ms) | ✅ |
| Todos com thresholds rígidos + tags phase=Q3-04 + X-Request-ID | ✅ |
| Métricas customizadas Trend/Rate por endpoint | ✅ |
| README.md Snapshot atualizado com bullet Q3-04 + linha tabela Consolidado S22-Q304 | ✅ |

---

## 7. Consequências Operacionais / Próximos Passos

### Agendado S24 Q3-06
1.  **CronJob Kubernetes load test noturno**: rodar script 04 healthz-smoke 2x/hora e
    scripts 01/02/03 1x/noite (03:00 AM).
2.  **Grafana Dashboard Load Testing**: Expor `http_req_duration` e thresholds
    quebrados em panel do Grafana SRE.
3.  **qa-gateway comando `scan-load-thresholds` Q3-06**: varrer pasta `tests/k6/` e
    validar que todo script tem `options.thresholds` definido (proteger alguém criar script
    sem threshold novo).
