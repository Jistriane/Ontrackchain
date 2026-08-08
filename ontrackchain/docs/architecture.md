# Arquitetura

## Visao Geral

O `Ontrackchain` e uma plataforma modular para investigacao e compliance on-chain, organizada como servicos independentes atras de um gateway unico, com enforcement de tenant no banco e camadas separadas de auditoria operacional e evidência regulatoria.

O diagrama abaixo resume a topologia corrente do sistema e destaca onde os fluxos operacionais, regulatórios e de governança se conectam, incluindo Stack de Observabilidade e Helm Kubernetes Sprint 14 M8.

```mermaid
flowchart LR
    U[Operadores e sistemas externos] --> T[Traefik IngressClass]
    subgraph K8s_NS[ontrackchain Namespace — NetPol default-deny LGPD RLS]
      direction TB
      T --> A[auth-service v3.0.0]
      T --> MO[mock-oidc v1.5.0 dev IdP]
      T --> PA[public-api v2.0.0 B2B rate limit]
      T --> F[frontend Next.js 14]
      F --> I[investigation-api v2.0.0]
      F --> C[compliance-api v2.0.0]
      F --> M[monitoring-api v2.0.0]
      F --> R[report-api v2.0.0]
      F --> AI[ai-service v4.1.0]
      F --> CM[case-management v2.0.0]
      C --> CW[compliance-worker]
      A -->|OIDC federado| KC[Keycloak v25 realm import]
      T --> KC

      I --> P[(PostgreSQL 16 pgvector RLS)]
      C --> P
      M --> P
      R --> P
      AI --> P
      CM --> P
      PA --> P
      A --> P

      I --> X[(Redis)]
      C --> X
      M --> X
      R --> X

      subgraph OBS[Stack Observabilidade M16b Sprint 13]
        direction TB
        PR[(Prometheus v2.53 StatefulSet 20Gi PVC)]
        G[Grafana 11.2 Dashboard Único QA]
        AM[Alertmanager v0.27 webhook routes]
        PR -->|scrape /metrics annotations| A
        PR -->|scrape| MO
        PR -->|scrape| PA
        PR -->|scrape| I
        PR -->|scrape| C
        PR -->|scrape| M
        PR -->|scrape| R
        PR -->|scrape| AI
        PR -->|scrape| CM
        G --> PR
        G --> AM
        AM -->|webhook /monitoring| M
      end

      C --> GOV[governance-weekly/generated]
      M --> GOV
      R --> GOV
      AI --> GOV
      GOV --> CY[governance-weekly/cycles]
    end
    classDef svc fill:#dbeafe,stroke:#2563eb,color:#111827;
    classDef infra fill:#dcfce7,stroke:#16a34a,color:#111827;
    classDef stateful fill:#fef3c7,stroke:#d97706,color:#111827;
    class A,MO,PA,I,C,M,R,AI,CM,F svc;
    class T,X,CW,GOV,CY,KC infra;
    class P,PR,G,AM stateful;
```

## Boundaries do Sistema

### Edge e Identidade

- `Traefik` faz roteamento por `PathPrefix`.
- `auth-service` valida `JWT`, `API Key` e contexto `OIDC`.
- Headers propagados:
  - `X-Org-Id`
  - `X-User-Id`
  - `X-Linked-User-Id`
  - `X-Plan`
  - `X-Role`
  - `X-Auth-Method`
  - `X-MFA-Mode`
  - `X-MFA-Provider-Homologated`
  - `X-Request-Id`

### Investigacao

- `investigation-api` concentra `estimate`, `start`, `status`, `result` e trilha de billing.
- `Redis` suporta fila real, retry/backoff, DLQ e contadores de concorrencia.
- `RPC readiness` e metadados do provider entram no payload final do caso.

### Compliance

- `compliance-api` concentra catalogo, `risk-check`, `kyc-wallet`, `sanctions-check`, `preventive blocks` e `counterparties`.
- `SanctionsEngine` consulta `sanctions_hits_cache` e `sanctions_lists_meta` localmente.
- `PreventiveBlockAgent` encapsula a decisao regulatoria e persiste `preventive_blocks`.
- `CounterpartyAgent` classifica risco, PEP, KYC/KYB e periodicidade de revisao.

### operações Compartilhadas

- `compliance-api` agora tambem expõe `POST/GET/PATCH /api/v1/operations/work-items*`.
- a camada `operations` persiste fila multiusuario por `organization_id`, com `RLS`, timeline e comentarios estruturados.
- a primeira integração ativa no frontend cobre:
  - `sanctions` como workspace multiusuario primario, sem fallback local de negocio no navegador
  - `alerts` com rastreamento por incidente e sincronizacao de fechamento via `ack`
- o modelo evita criar um microservico novo e reaproveita o mesmo contexto de auth, tenant e auditoria do `compliance-api`.

### Reports e ROS/COAF

- `report-api` gera relatórios deterministas e controla downloads sensiveis.
- O mesmo servico implementa o workflow `ROS/COAF`:
  - `PENDING_GENERATION`
  - `PENDING_APPROVAL`
  - `APPROVED`
  - `REJECTED`
  - `SUBMITTED_MANUAL`

### Monitoring e operação Global

- `monitoring-api` recebe webhooks do `Alertmanager`.
- `operational_alert_events` guarda incidentes globais fora do dominio multi-tenant de negocio.
- UI `/monitoring` suporta filtros, paginacao cursor-based, ack em lote e export auditado.
- no frontend, `/monitoring` deixou de concentrar toda a logica operacional em um unico arquivo e passou a atuar como hub de composicao.
- `use-monitoring-watchlist-alerts.ts` isola o bootstrap de watchlists, o refresh de alertas de teste e o disparo controlado do fluxo de validação operacional.
- `app/lib/monitoring-api.ts` centraliza loaders puros para watchlists, alertas, worker, alertas operacionais, metricas, DLQ e filtros de plataforma.
- `use-monitoring-platform-alerts.ts` isola persistencia em `sessionStorage`, filtros, selecao, paginacao por cursor, ack individual/lote e export de alertas de plataforma.
- `use-monitoring-operations.ts` isola bootstrap e mutacoes de `worker operations`, `operational alerts` e remediacao de `DLQ`, incluindo `requeue` e resolucao auditavel.
- `watchlist-alerts-panel.tsx`, `platform-alert-triage-panel.tsx`, `investigation-operations-panel.tsx` e `dlq-remediation-panel.tsx` concentram a renderizacao dos bounded contexts operacionais sem alterar RBAC, endpoints ou `data-testid` existentes.
- deep-links para `audit` e `evidence` passaram a reutilizar helpers compartilhados de `operational-context`, reduzindo drift entre cockpits operacionais.

### mock-oidc (Ambiente Dev/Staging leve)

- `mock-oidc v1.5.0`: substituto leve de Keycloak para ambientes locais ou staging sem IdP real.
- Porta 8009 interna, exposta via Traefik em `/auth/`.
- Claims opcionais de organização (`organization_id`, default role `OTK_ADMIN`) suportados com normalização provider `keycloak → mock`.
- Normaliza `linked_user_id` persistência corretamente: `provider = mock` em vez de `keycloak` para evitar drift de identidade federada.
- **Não usar em produção**: Sem criptografia de sessão forte, sem MFA, sem integração SCIM. Produção = Keycloak v25.

### Public API B2B e Rate Limiting

- `public-api v2.0.0` é a superfície pública para clientes B2B institucionais.
- Porta 8008 interna, exposta via Traefik em `/api/v1/b2b/`.
- `B2BApiKeyValidator` valida chaves `otc_live_<uuid>`, hash SHA-256 armazenado.
- Rate limiting por janela deslizante de 60 segundos por plan tier: `Enterprise: 100 req/min`, `Pro: 50`, `Starter: 10`.
- Endpoint principal: `POST /api/v1/b2b/screen` → screening AML endereço/carteira → retorna risk_score + sanctions_hits + evidence_trail event.
- Todas as chamadas B2B são auditadas em `audit_logs` com `resource_type = b2b_api_call` e `X-B2B-Request-Id` correlacionado.

### Case Management

- `case-management` e um microservico independente para gestao persistida de casos de investigacao e compliance.
- CRUD completo persistido em PostgreSQL (`case_management_cases`, `case_management_timeline`).
- RBAC: leitura requer ADMIN|ANALYST|COMPLIANCE_OFFICER|AUDITOR|VIEWER; escrita requer ADMIN|ANALYST|COMPLIANCE_OFFICER.
- timeline auditavel com registro de todas as acoes (criacao, atualizacao, escalação).
- metricas agregadas: total, abertos, fechados, tempo medio de resolucao, por prioridade e categoria.
- integração com AI Service para geracao de risk_score automatico na criacao de casos.
- portas: interna 8006, exposta via Traefik em `/api/v1/cases`.

### Stack Observabilidade (M16b Sprint 13 Gate Observabilidade)

- **Tríplice enforcement obrigatória**: (a) Job `observability-endpoints-gate` em ci.yml bash grep exit 16; (b) Policy OPA #04 `04_deny_missing_observability_endpoints_fastapi.rego`; (c) 9 endpoints implementados em todos FastAPI.
- **`/healthz`**: JSON liveness `{service, version, timestamp_utc, status: ok}`. Usado por kubelet livenessProbe/readinessProbe HTTP GET no Helm Chart.
- **`/metrics`**: Estratégia try → `prometheus_fastapi_instrumentator` primeiro; fallback inline `PlainTextResponse` 4 métricas base (`fastapi_info`, `http_requests_total{method,path,status_code,org_id,service}`, `up{service}`, `metrics_scrape_timestamp_seconds`).
- **Prometheus v2.53 StatefulSet (Helm M8)**: 20Gi PVC, ServiceMonitor `monitoring.coreos.com/v1` matchLabels `kube-prometheus-stack`, job `kubernetes_sd_configs` scrape annotations `prometheus.io/scrape: true` nos 9 Services FastAPI. Retention 30d.
- **Grafana 11.2 Deployment**: 5Gi PVC, `GF_SERVER_ROOT_URL=/grafana/`, `GF_SERVER_SERVE_FROM_SUB_PATH=true`. Dashboard Único QA 9 painéis: RLS leak, E2E Playwright shard, pytest matrix, Load P95 ≤3000ms, SBOM Grype, Policy OPA violations, Observabilidade Gate endpoints, Sonar Coverage %80/85, DR restore status LGPD.
- **Alertmanager v0.27 Deployment**: webhook receiver `http://monitoring-api:8004/api/v1/monitoring/alertmanager-webhook` → monitoring-api persist `operational_alert_events` P0/P1/P2/P3 severidade. Route tree: `continue: true` por serviço, inibição Prometheus alertname.
- **HPA autoscaling/v2**: 9 HPAs para FastAPI, behavior `scaleUp stabilizationWindowSeconds: 60`, `scaleDown 300s`, CPU 80% / Memory 75% Utilização média.
- **PDB PodDisruptionBudget policy/v1**: 13 PDBs (9 FastAPI + PG + Prom + Grafana + Alertmgr + Keycloak + mock-oidc), `minAvailable: 1` (exceto mock-oidc PDB `minAvailable: 0` para permitir drain nó quando desnecessário — flag `needs-security-review` se mudar).

### Helm Kubernetes Single Chart (M8 Sprint 14 — PSP + NetPol LGPD)

- **Single Chart `ontrackchain-platform` v1.0.0**: `infra/k8s/charts/ontrackchain-platform/` — evita drift de 20+ charts múltiplos (risco R22).
- **Deployments DRY range-loop**: 9 serviços (`auth-service`, `mock-oidc`, `public-api`, `investigation-api`, `compliance-api`, `monitoring-api`, `report-api`, `ai-service`, `case-management`) gerados por `{{- range $svcName, $svc := .Values.services }}`.
- **PSP PodSecurity Standards (M8b Sprint 14 restrito)**: runAsUser=10001, runAsNonRoot=true, runAsGroup=10001, fsGroup=10001, capabilities.drop=[ALL], seccompProfile.type=RuntimeDefault, readOnlyRootFilesystem=true (tmpfs emptyDir medium=Memory para /tmp e Python cache automountServiceAccountToken=false). Labels namespace: `pod-security.kubernetes.io/enforce=restricted`, warn=baseline.
- **4 NetworkPolicy LGPD RLS (default-deny)**:
  1. `default-deny-lgpd-rls`: Ingress Egress ALL block (pedido explícito necessário).
  2. `block-ec2-instance-metadata-service-169-254`: Egress deny CIDR `169.254.169.254/32` IMDS (credenciais role nó).
  3. `allow-intra-namespace-same-ns`: Ingress allow `podSelector.matchLabels: ontrackchain.io/component` mútuo.
  4. `allow-from-traefik-ingress-ns`: Ingress allow From namespace `traefik-system` IngressClass.
- **PVC LGPD labels**: `ontrackchain.io/lgpd-class: restricted-dados-pessoais` em Postgres 10Gi e Prometheus 20Gi volumeClaimTemplates (Art.19 CD/ANPD LGPD restringe acesso aos dados pessoais em volumes).
- **Keycloak v25**: realm import `realm-ontrackchain.json` ConfigMap, clients `ontrackchain-b2b` + `ontrackchain-public`, realm roles `OTK_ADMIN`, `OTK_ANALYST`, `OTK_COMPLIANCE_OFFICER`, `OTK_AUDITOR`, `OTK_VIEWER` para federação.
- **Traefik Ingress**: IngressClass `traefik.io/ingress-controller`, 13 paths multi-host (`auth.localhost`, `api.localhost`, `app.localhost`), TLS `cert-manager.io/cluster-issuer=letsencrypt-prod`.
- **ExistingSecret Helm**: `.Values.global.existingSecret.name` opcional (production usa ExternalSecret Vault em vez de 12 placeholders inline).

### AI Service (Graph Intelligence 4.0)

- `ai-service` e um microservico independente que expoe 8 endpoints de IA explicativa, analise de grafos blockchain e inteligencia de casos.
- módulos: XAI Layer (explicabilidade), Risk Model Assessment, Confidence Engine, Case Insights, Graph Analysis, Graph Narrator, Law Enforcement Export, THEMIS (orquestrador).
- persiste analises em `ai_analysis_results` com input/output JSON para auditoria.
- emite eventos de evidência para `evidence_trail` (AI_EXPLAIN_GENERATED, AI_CASE_INSIGHTS_GENERATED, AI_LAW_ENFORCEMENT_EXPORT_GENERATED, AI_THEMIS_CASE_INTELLIGENCE_GENERATED).
- RBAC: leitura requer ADMIN|ANALYST|COMPLIANCE_OFFICER|AUDITOR; escrita requer ADMIN|ANALYST|COMPLIANCE_OFFICER; export e THEMIS tem roles restritas.
- dados reais: buscas em `cases`, `case_management_cases`, `regulatory_work_events` e `evidence_trail` para gerar insights contextualizados.
- portas: interna 8005, exposta via Traefik em `/api/v1/ai`.

### Case Management

- `case-management` e um microservico independente para gestao persistida de casos de investigacao e compliance.
- CRUD completo persistido em PostgreSQL (`case_management_cases`, `case_management_timeline`).
- RBAC: leitura requer ADMIN|ANALYST|COMPLIANCE_OFFICER|AUDITOR|VIEWER; escrita requer ADMIN|ANALYST|COMPLIANCE_OFFICER.
- timeline auditavel com registro de todas as acoes (criacao, atualizacao, escalação).
- metricas agregadas: total, abertos, fechados, tempo medio de resolucao, por prioridade e categoria.
- integração com AI Service para geracao de risk_score automatico na criacao de casos.
- portas: interna 8006, exposta via Traefik em `/api/v1/cases`.

## Camadas de Dados

### Trilha Operacional

- `audit_logs`: eventos de negocio e administracao correlacionados por `request_id`.
- `credit_ledger`: trilha financeira do `quote -> start -> PRE_HOLD -> CONFIRMED/REFUND`.
- `regulatory_work_items`: fila operacional compartilhada por modulo/recurso com prioridade, owner, SLA e status.
- `regulatory_work_events`: timeline auditavel das transicoes da fila compartilhada.
- `regulatory_work_comments`: comentarios estruturados para handoff, decisao e contexto operacional.

### Trilha Regulatoria

- `evidence_trail`: append-only com `event_hash`, `prev_event_hash`, `retain_until` e base regulatoria.
- `preventive_blocks`: snapshot da decisao de bloqueio, hash de evidência e vinculo opcional com `evidence_trail`.
- `ros_records`: estado do ROS, prazo de submissao, comprovante e hash de recibo.
- `counterparties` e `counterparty_history`: onboarding e historico regulado de contraparte.

### Cache e Metadados de Sancoes

- `sanctions_lists_meta`: configuração do feed, status, source, hash e agenda de sync.
- `sanctions_hits_cache`: entidades sancionadas e enderecos por lista.
- `compliance-worker`: sincroniza OFAC, UN, EU, OpenSanctions e deadlines de ROS.

## Tabelas-Chave

| Tabela | Papel |
| --- | --- |
| `audit_logs` | auditoria operacional multi-tenant |
| `evidence_trail` | cadeia imutavel de evidências regulatorias |
| `credit_ledger` | trilha de cobranca e reserva |
| `preventive_blocks` | decisao e revisao de bloqueios |
| `counterparties` | cadastro regulado de contrapartes |
| `counterparty_history` | historico de mudancas em contrapartes |
| `sanctions_lists_meta` | configuracao/sync das listas |
| `sanctions_hits_cache` | cache local para screening |
| `ros_records` | workflow de ROS/COAF |
| `case_management_cases` | casos de investigacao e compliance persistidos |
| `case_management_timeline` | timeline de eventos dos casos |
| `ai_analysis_results` | resultados de analises AI (XAI, risk models, graph, etc.) |
| `operational_alert_events` | incidentes globais de plataforma |
| `regulatory_work_items` | fila compartilhada multiusuario por modulo/recurso |
| `regulatory_work_events` | timeline das transicoes dos work-items |
| `regulatory_work_comments` | comentarios de handoff e decisao |

## Fluxos canônicos

### Screening de Sancoes

```text
compliance-worker -> sanctions_lists_meta/sanctions_hits_cache
  -> GET /api/v1/compliance/sanctions-check/{address}
  -> audit_logs + evidence_trail
```

Observação importante:

- o endpoint direto `sanctions-check` e o catalogo de operações agora convergem para `provider=sanctions_lists_cache`, `provider_status=live` e `delivery_mode=local_cache`
- a UI `/sanctions` agora sincroniza o resultado em `regulatory_work_items` como fila compartilhada primaria e falha explicitamente quando a fila compartilhada nao estiver disponivel

### Bloqueio Preventivo

```text
sanctions-check local + contexto AML/manual flags
  -> PreventiveBlockAgent
  -> preventive_blocks
  -> audit_logs
  -> evidence_trail
  -> ros_records (quando exige ROS)
```

### Onboarding de Contrapartes

```text
POST /api/v1/compliance/counterparties
  -> CounterpartyAgent.assess()
  -> counterparties
  -> counterparty_history
  -> evidence_trail
```

### ROS/COAF

```text
POST /api/v1/reports/ros-coaf
  -> reports + ros_records(status=PENDING_APPROVAL)
  -> evidence_trail(COAF_ROS_GENERATED)

POST /api/v1/reports/ros-coaf/{id}/approve
  -> ros_records(APPROVED|REJECTED)
  -> evidence_trail(COAF_ROS_APPROVED|COAF_ROS_REJECTED)

POST /api/v1/reports/ros-coaf/{id}/submitted
  -> ros_records(SUBMITTED_MANUAL)
  -> evidence_trail(COAF_ROS_SUBMITTED_MANUAL)
```

### Fila Operacional Compartilhada

```text
frontend (/sanctions, /alerts)
  -> proxies App Router /api/app/operations/work-items*
  -> compliance-api /api/v1/operations/work-items*
  -> regulatory_work_items + regulatory_work_events + regulatory_work_comments
```

Estados iniciais suportados:

- `UNDER_REVIEW`
- `ESCALATED`
- `READY`
- `APPROVED`
- `SUBMITTED`
- `CLOSED`
- `REJECTED`

## Regras Criticas

- `RLS` sempre baseado em `app.organization_id`
- `linked_user_id` e obrigatorio para mutacoes sensiveis que precisam de usuario persistido
- `lift` de bloqueio exige MFA externo homologado
- `legal_report` e `ROS/COAF` exigem auth forte e MFA homologado
- `evidence_trail` e `INSERT ONLY`
- listas de sancoes sao sincronizadas localmente; a aplicacao nao depende de chamada externa por request

## Drift Tecnico Residual

- o catalogo de eventos da trilha regulatoria agora esta consolidado com `evidence_trail.py` como `source of truth`, importado por `evidence_integration.py` e cruzado por `tests/test_evidence_event_catalog_sync.py`
- `due_diligence` e `source_of_funds` permanecem desenhados para `manual_review_required`, o que e uma decisao atual de produto e nao um bug

## Decisoes Arquiteturais Atuais

### 1. Screening local de sancoes em vez de API call por request

- reduz latencia e dependencia externa em tempo real
- permite operação degradada controlada durante falhas de provider
- exige governança forte de sync, hash e preflight de feed

### 2. Dupla trilha `audit_logs` + `evidence_trail`

- `audit_logs` cobre operação e suporte
- `evidence_trail` cobre prova regulatoria e integridade temporal
- aumenta custo documental, mas evita misturar observabilidade com cadeia de custodia

### 3. ROS/COAF manual assistido, nao submissao automatica externa

- reduz risco de acoplamento prematuro com portal/regulador
- preserva trilha de aprovacao humana obrigatoria
- deixa a submissao final como passo humano auditado
