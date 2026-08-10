# ADR-016 — Observabilidade Distribuída via OpenTelemetry OTLP v1.0.0 (Tracing + Métricas + Logs)

- **Status**: Aprovado e especificado Sprint 28
- **Decisores**: Arquiteto Observabilidade + SRE + DPO (LGPD logs PII) + CTO
- **Data de aprovação**: Sprint 28 (2026-08-10)

---

## 1. Contexto

Até o ciclo S1→S27, a infraestrutura de observabilidade existia apenas em fragmentos dispersos:
1.  **Logs estruturados parcialmente**: `logging.info()` em alguns serviços (investigation-api, compliance-api)
    mas sem schema unificado (sem correlation_id obrigatório em todos os registros).
2.  **Prometheus + Grafana 8 dashboards básicos**: Latência/throughput de API mas **sem atributos
    por tenant/organização** (impossível cobrar tiers B2B por uso medido).
3.  **Tracing distribuído inexistente**: Fluxos cross-serviço ai-service → investigation-api worker →
    compliance-api worker → public-api-v2 eram caixas-pretas (demorava até 8min para diagnosticar
    a causa raiz em incidentes P1 do staging S14).
4.  **LGPD Art.32 (registro de acesso) e Art.41 (DPO auditar quem acessou dado PII de quem)**:
    Não havia forma determinística de mapear `trace_id` → `session_id` → `user_id` → `cpf_tokenizado`
    em menos de 24h (prazo ANPD CD-004 RIPD Art.15 é 72h para incidente de vazamento PII).

### Restrições Obrigatórias (não negociáveis):
- **LGPD Art.32 e Art.33**: NUNCA enviar CPF/CNPJ, email plaintext, token YubiKey PII para
    backend de observabilidade (Grafana Cloud, Datadog, etc.). **Apenas token hasheado SHA-256**
    `sha256(org_id || cpf_token || secret_salt_256bit_rotacionado_90d)`.
- **Segurança de transportes (M5-cond.3A pós implantação)**: Tudo OTLP/gRPC mTLS Istio STRICT
    (spiffe id). Nenhum OTLP HTTP plaintext permitido fora do loopback.
- **BACEN Due Diligence Art.12 retenção 120 meses (10 anos)**: Traces de submissão ROS/COAF
    (compliance-api `report-api/submit/ros-coaf`) devem ser retidos **120 meses** em bucket frio
    GCS/S3 Retação WORM (Write Once Read Many). NÃO pode ser deletado antes.
- **Custo controlado**: Ingestão diária < ~350 GB/dia (25% da cota Enterprise Grafana Cloud
    contratada em 2026). Sobre-ingestão = automaticamente sampled via `TailSampling` OTel Collector.

---

## 2. Requisitos Funcionais e Não-Funcionais Mapeados

### 2.1 Funcionais (8 itens):

| ID | Funcionalidade | Sistema de Destino |
|---|---|---|
| R-OTEL-01 | **Tracing distribuído por request/response HTTP e gRPC**: Cada chamada FastAPI middleware gera `trace_id` obrigatório em todas as 8 rotas T2-12 billing enforcement + todas rotas ROS/COAF. | OTel Collector → Grafana Tempo (LGTM stack self-hosted ou Grafana Cloud Traces). |
| R-OTEL-02 | **Métricas RED (Rate/Error/Duration) por rota + por tier billing + por organization_id hash**: 4 métricas obrigatórias: `http_server_requests_count`, `http_server_requests_duration_seconds_bucket`, `ai_token_total_consumed`, `b2b_quota_usage_ratio` (0..1). | Prometheus via OTLP Prometheus Remote Write / OTel Collector Metrics → Grafana Mimir. |
| R-OTEL-03 | **Logs estruturados OTLP Logs schema unificado 14 campos**: timestamp_iso, severity, trace_id, span_id, correlation_id OTK request ID, service_name (8 serviços investigados: auth/case/compliance/investigation/public/report/monitoring/ai), user_id_hash, org_id_hash, role_family, message_code (ENUM 30 códigos), pii_touched (bool: true se rotina tocou CPF tokenizado), duration_ms, error_type (se houver). | OTel Collector → Grafana Loki (ou Splunk Cloud SIEM 180d LGPD mínimo). |
| R-OTEL-04 | **Sampling Inteligente**: Erros (HTTP 4xx/5xx) e billing enforcement blocks (402/429) **100% retidos sempre**; 2xx success sampled em 10% nominal + 100% se billing tier=enterprise (SLA contratual 99.9%). | TailSampling Processor OTel Collector. |
| R-OTEL-05 | **Atributos Billing obrigatórios (SSOT com T2-10 OTK_PLAN_CAPABILITIES)**: Cada span/metric tem `billing.tier=startup|business|enterprise`, `billing.ai_credits_used_delta`, `billing.b2b_hourly_quota_used_delta`. | OpenTelemetry Resource Detector custom do shared package (`ontrackchain_shared.middleware_rls.py` já tem auth info). |
| R-OTEL-06 | **Propagação W3C Trace Context obrigatória**: headers `traceparent` + `tracestate` em TODAS as chamadas internas service-a → service-b (incluindo redis pipeline `CLIENT SETINFO` e pg application_name). | OTel SDK Python auto-instrumentation `opentelemetry-instrument`. |
| R-OTEL-07 | **Roteamento condicional LGPD**: Se `pii_touched=true` no log → route do OTel Collector envia cópia EXTRA para Splunk SIEM retention 180 dias + bucket long retention 10 anos WORM se `flow_code = ROS_COAF_SUBMISSION`. | OTel Collector `routing` processor. |
| R-OTEL-08 | **CI QA Gateway nova asserção (Q3-10 futuro)**: `qa-gateway scan-observability-schema` valida que 14 campos OTLP Logs presentes em todos `logger.info/warn/error` do código. Falta 1 campo → exit 1 bloqueia PR. | qa-gateway cli.py (a ser implementado após M5). |

### 2.2 Não Funcionais (6 itens):
| ID | RNF | Valor alvo |
|---|---|---|
| RN-OTEL-01 | **Overhead de latência p99**: Tracing + métricas adicionam **≤ 8ms** sobre p99 baseline 500ms do B2B screening. |
| RN-OTEL-02 | **Backpressure/Outage-safe**: OTel Collector in-memory queue ≥ 10k spans; se backend down → drop apenas traces success (sampling 0%), nunca erros ou PII flows ROS/COAF. |
| RN-OTEL-03 | **Retention compliance**: 180d hot (SIEM/Loki), 12 meses warm (Mimir/Tempo), 120 meses cold ROS/COAF WORM S3/GCS (LGPD BACEN). |
| RN-OTEL-04 | **Segurança**: Nodes OTel Collector correm como PSP restricted não-root, service account só pode OTLP 4317 (gRPC) e 4318 (HTTP), nunca escrevem em disco a menos queue. |
| RN-OTEL-05 | **Multi-tenant seguro**: Painéis Grafana são RLS por organization_id_hash — cliente enterprise consegue ver APENAS suas métricas (mesmo backend compartilhado). |
| RN-OTEL-06 | **Alertas P0/P1/P2 obrigatórios ADR-025 são baseados no OTel Metrics (não em healthz).**: Billing fail-closed counter Redis indisponível (HTTP 402 spike 2x acima EMA 1h) → P0. |

---

## 3. Alternativas Avaliadas (3 Opções + Trade-offs)

### Opção A: Datadog SaaS completo (tudo 1 fornecedor)
- **Prós**: 1 painel, config zero, dashboards prontos, log anomaly detection nativo.
- **Contras**:
  1.  **Custo ~3x maior**: Em ~350GB ingestão/dia, Datadog custa **USD 14.000/mês** vs Grafana Cloud self-hosted parcial **USD 4.800/mês**.
  2.  **LGPD Data Residency risco**: Datadog default usa us-east-1; contrato EU-West-1 (Frankfurt) com SCCs UE ANPD CD-002/2023 requer cláusula extra e negociação jurídica 60 dias.
  3.  **Vendor lock-in muito forte**: OTLP export to Datadog é beta e custom; trocar provider = rewrite 40% dos dashboards/alerts.
- **Complexidade implementação**: Baixa (1 semana).
- **Risco**: Alto (custo + LGPD residência).

### Opção B: Stack Open Source pura self-hosted (Prometheus + Grafana OSS + Jaeger + Loki)
- **Prós**: Costo marginal zero (hardware k8s já existe no EKS). Total controle LGPD (nenhum dado sai VPC).
- **Contras**:
  1.  **SLA operacional risco alto**: Self-hosted Prometheus HA (Thanos/Ruler) + Jaeger com Cassandra/Cassandra multi-AZ = SRE time 2 FTE dedicado ~80% do mês operando.
  2.  **Long-term storage 120 meses (10 anos) ROS/COAF**: Ter que operar Thanos + bucket lifecycle + backup cripto = sobrecarga engenharia enorme (equivalente a 1 sprint inteira S29 e S30).
  3.  **Long tail sampling 100% erros + billing enterprise**: Requer implementar Tail Sampling manualmente no OTel Collector com routing; dashboards enterprise compliance ANPD são buildados do zero sem template.
- **Complexidade implementação**: Muito Alta (5-6 semanas + FTE SRE contínuo).
- **Risco**: Médio (falta SRE → outage observabilidade = incidente P0 às escuras).

### Opção C: **Híbrido Recomendado** — Grafana Cloud Enterprise Traces + Metrics + Logs (OTLP nativo) para hot/warm + bucket on-prem S3 WORM para cold retention ROS/COAF 120 meses
- **Prós**:
  1.  **OTLP nativo primeira classe**: Grafana Cloud Tempo/Mimir/Loki falam OTLP nativamente. Sem adapters.
  2.  **LGPD Data Residency EU-West-1 (Irlanda ou Frankfurt) SCCs ANPD CD-002/2023 já incluso no contrato Grafana Labs (assinado CLO em 2026-07-28; evidência em `docs/legal/grafana-sccs-2026-07.pdf`).**
  3.  **Custo ótimo (~USD 4.800/mês)**: Mantém bucket S3 frio WORM independente ($0.004/GB/mês → 120 meses de ROS/COAF = ~USD 350 total irrisório).
  4.  **Compliance ready**: Dashboards LGPD Art.32 "Quem acessou PII do titular X?" já são templates disponíveis em Grafana Cloud Compliance Pack (Sprint 29 customiza para roles OTK_AUDITOR e OTK_COMPLIANCE_OFFICER).
  5.  **OTel Collector self-hosted inside VPC**: Nenhum dado PII sai do ambiente sem ser sanitizado hash 256-bit salted no collector ANTES de chegar ao Grafana.
- **Contras**:
  1.  **Split-brain de retenção**: Operar 2 pipelines (Grafana hot/warm + bucket S3 cold). Mitigado: OTel routing processor 1 regra `if flow_code == ROS_COAF_SUBMISSION envia também para s3 exporter`.
  2.  **Grafana Cloud rate limits**: 400k spans/min default. Mitigado: pedir upgrade 1.2M spans/min no contrato (já negociado CLO).
- **Complexidade implementação**: Média (3 sprints S29→S31).
- **Risco**: Baixo (menor trade-off).

**→ Decisão: OPÇÃO C HÍBRIDA RECOMENDADA.**

---

## 4. Decisão — Arquitetura Física e Componentes

```
[[diagram: Arquitetura Observabilidade OTel. Flowchart LR:
Users_Wallets_OIDC --HTTP/mTLS Istio--> Frontend_NextJS
Frontend_NextJS --W3C_TraceContext--> 8_Servicos_FastAPI (Auth Case Compliance Investigation Public Report Monitoring AI)
8_Servicos_FastAPI --OTLP_gRPC_4317_mTLS_SPIFFE--> OTel_Collector_SelfHosted_3replicas_K8s
OTel_Collector_SelfHosted_3replicas_K8s --> Processor_TailSampling_100pct_erros_enterprise
OTel_Collector_SelfHosted_3replicas_K8s --> Processor_Routing_ROS_COAF_route_2destinos
OTel_Collector_SelfHosted_3replicas_K8s --OTLP--> GrafanaCloud_EUWest1: Traces_Tempo + Metrics_Mimir + Logs_Loki (180d_hot + 12m_warm)
OTel_Collector_SelfHosted_3replicas_K8s --S3_Exporter_WORM--> AWS_S3_Immutability_GLGD_120_meses_BACEN (só ROS_COAF)
GrafanaCloud_EUWest1 --OAuth2_Proxy_Keycloak_Roles--> Dashboards_Grafana: OTK_ADMIN(100pct) OTK_AUDITOR(read_180d) OTK_COMPLIANCE_OFFICER(ROPD_submissions) OTK_ANALYST(own_org_only)
Alertmanager_Grafana --> SIEM_Splunk_OTK_M5PUSH_correlationID + Slack_P0 + PagerDuty_P0
DPO_Email --> Dashboards_Grafana Painel_LGPD_Art_32_Auditoria_Acesso_PII (quartal review)
]]
```

### Componentes por responsabilidade única (12 peças):
| ID | Componente | Responsabilidade | Linguagem/Tecnologia | Falta? |
|---|---|---|---|---|
| C01 | **OTel SDK Python OpenTelemetry 1.28+ (opentelemetry-distro[otlp])** | Instrumenta automaticamente FastAPI, Requests, Redis, Psycopg 3, Pydantic. Injetado em `apps/*/main.py` no inicio da lifespan. | Python 3.11+ | ✅ Lib existe, falta integrar |
| C02 | **Shared middleware OTel Setup Builder** | Package shared: `ontrackchain_shared/otel_setup.py` factory cria `TracerProvider`, `MeterProvider`, `LoggerProvider` 1 vez. Todos serviços chamam `setup_otel(service_name="investigation-api")` no inicio. | Python shared package | ❌ CRIAR em S29 |
| C03 | **Middleware Billing Attributes Injetor** | Em middleware_rls.py já existe current_org_id e current_org_tier; injeta atributos OTel `billing.tier`, `org_id_hash=sha256`, `user_id_hash=sha256`. | Já existente middleware_rls | ✅ Apenas adicionar atributos |
| C04 | **OTel Collector (Helm Chart open-telemetry/opentelemetry-collector 0.107+)** | 3 réplicas k8s, Istio mTLS STRICT, processors: batch/memory_limiter/tailsampling/routing. Exporters: otlp/grafana_cloud, s3/immutable_worm | Helm Values | ❌ CRIAR helm S30 |
| C05 | **Grafana Cloud (Tempo Traces / Mimir Metrics / Loki Logs)** | Hot/warm storage, alerting, dashboards role-based RLS | SaaS | ✅ Contrato CLO assinado |
| C06 | **Bucket S3 (AWS us-east-2 ou GCP europe-west1) Object Lock Compliance 10 anos WORM** | Exclusivo ROS/COAF submissions + logs PII; lifecycle depois de 12 meses mover para Glacier Instant Retrieval. Versionamento + SHA256 checksum. | IaC Terraform | ❌ Criar via Terraform S29 |
| C07 | **Custom OTel Exporter SIEM Splunk HEC** | Routing processor: se `pii_touched=true` → envia cópia para SIEM Splunk index `ontrackchain_lgpd_pii_access` retention 180 dias mínimo. | OTel Splunk HEC Exporter Community | ✅ Existe community |
| C08 | **Dashboards Grafana (obrigatórios 8 painéis LGPD/BACEN/BILLING)**: 01 Billing Tier Usage Ratio; 02 RED by Route & Tier; 03 AI Credit Consumption EMA; 04 LGPD Art.32 Who Accessed; 05 ROS/COAF Submission Audit Trail; 06 AI Service Worker Queue Size; 07 Public API v2 HMAC 429 Spike; 08 SLO 99.9% Enterprise Tier Uptime Heatmap | Grafana Provisioning YAML + Jsonnet/Tanka | ❌ Criar templates S30 |
| C09 | **Alertas P0/P1/P2 ADR-025 atualizados**: 8 alertas de billing fail-closed; 5 alertas LGPD não conformidade; 10 alertas RED erro spike. | Contact points Slack + PagerDuty + SIEM Splunk | ❌ Atualizar PrometheusRules S31 |
| C10 | **OTel e2e QA test**: Playwright E2E (Q3-07 futuro): faz um request POST /screening → verifica no OTel mock backend que trace_id tem billing.tier=business e org_id_hash presente. | OTel In Memory Exporter pytest | ❌ 1 teste futuro Q3-07 |
| C11 | **QA Gateway Q3-10 scan-observability-schema**: Varre arquivos Python `logger.*` e valida 14 campos OTLP Log schema; valida que nenhum logger envia `payload.cpf=` plaintext (Grep regex). | qa-gateway cli.py futuro | ❌ Fase 5 (após M5) |
| C12 | **Métricas Billing Charging Backend (Dataflow/BigQuery)**: Diário, lê billing metrics Mimir e reconcilia com Stripe subscriptions (T2-09). Diferença > 5% → alerta P2. | Airflow DAG futuro | ❌ Fase Handoff Pós M5 |

---

## 5. Modelo de Dados (OTel Unified Schema para Ontrackchain)

### 5.1 Resource Attributes (obrigatórios em TODOS os sinais):
```
service.name:              investigation-api | ai-service | compliance-api | report-api | auth-service | monitoring-api | public-api | case-management-api
service.version:           ${GIT_COMMIT_SHA} (mesmo SHA do CI commit pre-merge)
service.instance.id:       ${K8S_POD_NAME}
deployment.environment:    dev | staging | prod
cloud.provider:            aws | gcp
cloud.region:              sa-east-1 | europe-west1
k8s.cluster.name:          ontrackchain-production
k8s.namespace.name:        ontrackchain-services
org.id.sha256:             sha256(otk_salt_rot_2026_Q3 || raw_uuid_org)    [NUNCA plaintext]
billing.tier:              startup | business | enterprise
security.m5.enforced:      true | false    [true=sign-off M5 ativo; observa alertas]
```

### 5.2 Métricas (4 obrigatórias + 12 recomendadas):
```
http_server_requests_count_total            Counter    labels: {service, route, method, status_code_class_2xx_3xx_4xx_5xx, billing_tier, org_id_sha256}
http_server_requests_duration_seconds       Histogram  buckets [0.005,0.01,0.025,0.05,0.1,0.25,0.5,1.0,2.5,5.0,10.0] (mesmo ADR-025 k6 p95 alvo)
ai_token_consumed_total                     Counter    labels: {service, ai_model_family, billing_tier, org_id_sha256}  [para faturar overage AI]
b2b_hourly_quota_usage_ratio                UpDown     labels: {billing_tier, org_id_sha256}   [0..1; >0.95 → warning; >1 → 429 enviado]
* (recomendadas 12): redis_hit_ratio, pg_active_connections, worker_queue_size, ai_service_pending_tasks, graph_intelligence_cose_duration_seconds, etc.
```

### 5.3 Logs (14 campos schema ENFORCED via Pydantic no shared logger):
| Campo | Tipo | Obrigatório | LGPD tratamento |
|---|---|---|---|
| `ts_iso` | RFC3339 UTC | ✅ | |
| `severity` | DEBUG/INFO/WARN/ERROR/FATAL | ✅ | |
| `trace_id` | 16 bytes hex (W3C) | ✅ | |
| `span_id` | 8 bytes hex | ✅ | |
| `correlation_id` | UUID v4 (`OTK-xxxx` request ID middleware) | ✅ | |
| `service` | Enum 8 serviços | ✅ | |
| `user_id_hash` | SHA256 salt 256-bit | ✅ | **NUNCA user_id plaintext** |
| `org_id_hash` | SHA256 salt 256-bit | ✅ | **NUNCA org plaintext** |
| `role_family` | OTK_* 5 roles | ✅ | |
| `message_code` | ENUM 30 códigos (ex: `BILLING_402_FAIL_CLOSED`, `LGPD_ROPD_OP_0003_AI_ANALYZED`, `ROS_COAF_SUBMITTED`) | ✅ | |
| `pii_touched` | bool | ✅ | True=tocou CPF tokenizado |
| `duration_ms` | int | ✅ | |
| `error_type` | Optional[str] (Type Fully Qualified Name) | ✅ (quando erro) | |
| `message` | string sem PII | ✅ | Regex QA Gateway proíbe `\d{3}\.\d{3}\.\d{3}-\d{2}` |

---

## 6. Aspectos Transversais (Segurança, Riscos LGPD, Observabilidade da própria Observabilidade)

### 6.1 Segurança:
- **Antes de qualquer deploy em staging**: Rodar TruffleHog (Q3-08) para confirmar que nenhuma API Key Grafana Cloud OTLP foi commitada em Git.
- **OTLP Exporter Grafana Cloud basic auth username/password**: NÃO usar. **Usar token fine-grained Grafana Cloud Access Policy (scopes: traces:write, metrics:write, logs:write)**. Token armazenado no HashiCorp Vault `kv/observability/grafana-cloud-otlp-token`. Validade 90 dias, rotação automática Vault Agent.
- **Istio AuthorizationPolicy**: Apenas Service Accounts `otk-otel-collector` podem ingressar OTLP 4317; nenhum workload público tem saída direta Grafana Cloud (sai via collector egress gateway).

### 6.2 Riscos (Probabilidade/Impacto/Mitigação):
| Risco | P | I | Mitigação |
|---|---|---|---|
| R1: Stack OTel adicionar >8ms p99 latency (viola RNF-OTEL-01) | Médio | Alto | Testes de carga k6 ADR-025 com/sem OTel em staging antes de prod. Se >8ms → desligar auto-instrument Psycopg3 (sob menor overhead). |
| R2: Salt org_id_hash vazamento = desanonimização LGPD | Baixo | Muito Alto | Salt armazenado em Vault HSM Transit Engine. Rotação a cada 90 dias. Acesso Salt = exclusivo DPO + 2 engenheiros 4-olhos. |
| R3: Grafana Cloud outage 8h → observabilidade às escuras | Médio | Alto | OTel Collector persiste queue em Persistent VolumeClaim 10GB por réplica (emptyDir por padrão; trocar para PVC no Helm values production). |
| R4: TailSampling dropou trace de incidente P0 que precisava debuggar | Baixo | Médio | Regra TailSampling: HTTP 5xx + billing.tier=enterprise + message_code=ROS_* sempre 100%. |
| R5: Enviei por engano CPF plaintext em campo log `message` → vazamento LGPD Art.48 2% faturamento | Médio | Muito Alto | **Dupla prevenção**: (1) QA Gateway Q3-10 (regex + 14 schema); (2) OTel Collector `redaction` processor regex scrubbing antes do exporter Grafana/Splunk; (3) DPO revisa sample 1% logs todo dia às 09:00 via Grafana Explore. |

### 6.3 Estratégia de Rollout 4 Fases (Canary Sempre!):
1.  **Fase 1 (Sprint 29) - Dev + Staging só métricas**: Apenas Prometheus Metrics habilitados; traces/logs off. Overhead latência validado k6 ADR-025.
2.  **Fase 2 (Sprint 30) - Staging tudo + Canary 10% prod enterprise**: Enterprise tier (10 clientes maiores) 10% tráfego habilitado tracing/logging OTel.
3.  **Fase 3 (Sprint 31) - 100% prod enterprise + 50% prod business**: Startup tier só métricas (sem tracing/logs para reduzir custo).
4.  **Fase 4 (Sprint 32) - 100% Geral + Otimização Overhead**: TailSampling 5% success em startup; alertas ADR-025 em produção.

---

## 7. Definition of Done (DoD): 14 itens concreto para declarar ADR-016 "implantado"

| ID | Item DoD | Validado por? |
|---|---|---|
| 016.01 | `ontrackchain_shared/otel_setup.py` criado com factory TracerProvider/MeterProvider/LoggerProvider + 14 campos logs enforced via Pydantic. | 2 pytest contrato passando. |
| 016.02 | Todos 8 serviços FastAPI chamam `setup_otel(service_name=...)` no inicio do lifespan. | grep -r "setup_otel" apps/*/main.py = 8 matches. |
| 016.03 | Middleware_rls injeta 6 atributos billing (tier, org_hash, user_hash, role, pii_touched, correlation_id). | QA Gateway futuro Q3-10; por enquanto inspeção manual 2 engenheiros. |
| 016.04 | Helm values OTel Collector: 3 réplicas, memory_limiter 70%, tailsampling 3 regras (100% errors, 100% enterprise, 10% success), routing ROS_COAF → S3. | `helm lint` + `kubent` deprecated. |
| 016.05 | Bucket S3 WORM Object Lock Compliance mode 10 anos criado. Versão + KMS SSE-KMS. Hash SHA256 integrity check habilitado. | IaC Terraform plan + DPO sign-off. |
| 016.06 | 8 Dashboards Grafana provisionados (seção C08). | QA visual Playwright 1 screenshot. |
| 016.07 | 23 Alertas críticos P0/P1/P2 importados para Grafana Contact Points certo. | Alert firing test staging (injetar 5xx). |
| 016.08 | 1 teste k6 ADR-025 com OTel ativo vs desativado: p99 overhead ≤ +8ms → PASS. | k6 report JSON no qa-reports/. |
| 016.09 | TruffleHog (Q3-08) scan todo repo: 0 segredos Grafana OTLP token VERIFICADO → PASS. | qa-gateway Q3-08 exit 0. |
| 016.10 | Q3-10 (qa-gateway scan-observability-schema): Nenhum logger com CPF plaintext regex detectado → exit 0. | qa-gateway Q3-10 exit 0. |
| 016.11 | Fase 1→4 rollout executado conforme seção 6.3. | Sem incidente P0 em 14 dias úteis pós Fase 4. |
| 016.12 | SIEM Splunk recebe logs `pii_touched=true` e retém 180 dias. | Auditoria DPO 1 mês depois. |
| 016.13 | 29 ADRs Sign-off consolidado: ADR-016 linha 16 marcada Aprovado com justificativa ANPD CD-004. | Assinatura DPO + CLO planilha SIGNOFF. |
| 016.14 | Documentação em `docs/observability-handbook-otel-v1.md`: Como adicionar nova métrica, como trocar Grafana → Datadog um dia (vendor-lock-in mitigação), troubleshooting OTel Collector memory_limiter. | Handbook linkado no README Índice Geral. |

---

**Referências normativas citadas neste ADR**:
- LGPD Lei 13.709/2018: Art.5º II, Art.8 §5, Art.15 CD-004 RIPD, Art.32, Art.33, Art.41, Art.48.
- ANPD CD-002/2023 SCCs Standard Contractual Clauses UE.
- BACEN Circular X Due Diligence PJ Art.12 retenção 120 meses (10 anos).
- ADR-018 qa-gateway SSOT, ADR-025 Load Testing k6 thresholds, ADR-026 M5 Push Remoto, ADR-027 Billing Fail-Closed.
