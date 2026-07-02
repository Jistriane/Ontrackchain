# Arquitetura

## Visao Geral

O `Ontrackchain` e uma plataforma modular para investigacao e compliance on-chain, organizada como servicos independentes atras de um gateway unico, com enforcement de tenant no banco e camadas separadas de auditoria operacional e evidencia regulatoria.

`[[diagram: arquitetura atual do Ontrackchain com Traefik e ForwardAuth na borda; frontend Next.js; auth-service; investigation-api; compliance-api; monitoring-api; report-api; PostgreSQL com RLS; Redis; evidence_trail append-only; audit_logs; sanctions_hits_cache; preventive_blocks; counterparties; ros_records; compliance-worker sincronizando OFAC, UN e EU; fluxo de staging serio com preflight, homologation e dossier ]]`

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

### Operacoes Compartilhadas

- `compliance-api` agora tambem expõe `POST/GET/PATCH /api/v1/operations/work-items*`.
- a camada `operations` persiste fila multiusuario por `organization_id`, com `RLS`, timeline e comentarios estruturados.
- a primeira integracao ativa no frontend cobre:
  - `sanctions` como workspace multiusuario primario, mantendo fallback local
  - `alerts` com rastreamento por incidente e sincronizacao de fechamento via `ack`
- o modelo evita criar um microservico novo e reaproveita o mesmo contexto de auth, tenant e auditoria do `compliance-api`.

### Reports e ROS/COAF

- `report-api` gera relatorios deterministas e controla downloads sensiveis.
- O mesmo servico implementa o workflow `ROS/COAF`:
  - `PENDING_GENERATION`
  - `PENDING_APPROVAL`
  - `APPROVED`
  - `REJECTED`
  - `SUBMITTED_MANUAL`

### Monitoring e Operacao Global

- `monitoring-api` recebe webhooks do `Alertmanager`.
- `operational_alert_events` guarda incidentes globais fora do dominio multi-tenant de negocio.
- UI `/monitoring` suporta filtros, paginacao cursor-based, ack em lote e export auditado.

## Camadas de Dados

### Trilha Operacional

- `audit_logs`: eventos de negocio e administracao correlacionados por `request_id`.
- `credit_ledger`: trilha financeira do `quote -> start -> PRE_HOLD -> CONFIRMED/REFUND`.
- `regulatory_work_items`: fila operacional compartilhada por modulo/recurso com prioridade, owner, SLA e status.
- `regulatory_work_events`: timeline auditavel das transicoes da fila compartilhada.
- `regulatory_work_comments`: comentarios estruturados para handoff, decisao e contexto operacional.

### Trilha Regulatoria

- `evidence_trail`: append-only com `event_hash`, `prev_event_hash`, `retain_until` e base regulatoria.
- `preventive_blocks`: snapshot da decisao de bloqueio, hash de evidencia e vinculo opcional com `evidence_trail`.
- `ros_records`: estado do ROS, prazo de submissao, comprovante e hash de recibo.
- `counterparties` e `counterparty_history`: onboarding e historico regulado de contraparte.

### Cache e Metadados de Sancoes

- `sanctions_lists_meta`: configuracao do feed, status, source, hash e agenda de sync.
- `sanctions_hits_cache`: entidades sancionadas e enderecos por lista.
- `compliance-worker`: sincroniza OFAC, UN, EU, OpenSanctions e deadlines de ROS.

## Tabelas-Chave

| Tabela | Papel |
| --- | --- |
| `audit_logs` | auditoria operacional multi-tenant |
| `evidence_trail` | cadeia imutavel de evidencias regulatorias |
| `credit_ledger` | trilha de cobranca e reserva |
| `preventive_blocks` | decisao e revisao de bloqueios |
| `counterparties` | cadastro regulado de contrapartes |
| `counterparty_history` | historico de mudancas em contrapartes |
| `sanctions_lists_meta` | configuracao/sync das listas |
| `sanctions_hits_cache` | cache local para screening |
| `ros_records` | workflow de ROS/COAF |
| `operational_alert_events` | incidentes globais de plataforma |
| `regulatory_work_items` | fila compartilhada multiusuario por modulo/recurso |
| `regulatory_work_events` | timeline das transicoes dos work-items |
| `regulatory_work_comments` | comentarios de handoff e decisao |

## Fluxos Canonicos

### Screening de Sancoes

```text
compliance-worker -> sanctions_lists_meta/sanctions_hits_cache
  -> GET /api/v1/compliance/sanctions-check/{address}
  -> audit_logs + evidence_trail
```

Observacao importante:

- o endpoint direto `sanctions-check` e o catalogo de operacoes agora convergem para `provider=sanctions_lists_cache`, `provider_status=live` e `delivery_mode=local_cache`
- a UI `/sanctions` agora sincroniza o resultado em `regulatory_work_items` como fila compartilhada primaria, com fallback local para continuidade operacional

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
- permite operacao degradada controlada durante falhas de provider
- exige governanca forte de sync, hash e preflight de feed

### 2. Dupla trilha `audit_logs` + `evidence_trail`

- `audit_logs` cobre operacao e suporte
- `evidence_trail` cobre prova regulatoria e integridade temporal
- aumenta custo documental, mas evita misturar observabilidade com cadeia de custodia

### 3. ROS/COAF manual assistido, nao submissao automatica externa

- reduz risco de acoplamento prematuro com portal/regulador
- preserva trilha de aprovacao humana obrigatoria
- deixa a submissao final como passo humano auditado
