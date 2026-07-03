# Contratos de API

## Convencoes Gerais

- Base local: `http://localhost:8080`
- Auth protegida por gateway/`ForwardAuth`
- Hierarquia de planos efetiva no runtime: `free -> starter -> professional -> enterprise`
- Formas aceitas:
  - `Authorization: Bearer <jwt>`
  - `X-API-Key: <api_key>`
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
- Erros devem preferir `error codes` estaveis e neutros em idioma.

## Regras Canonicas de Catalogo

- aliases sao aceitos por UX e API, mas devem ser resolvidos para o nome canonico antes de billing, persistencia e auditoria
- `quote -> start` continua sujeito a `plan lock`; downgrade invalida a execucao e upgrade exige novo `quote`
- consumidores devem preferir os endpoints de catalogo, e nao listas estaticas embutidas no frontend:
  - `GET /api/v1/report-types`
  - `GET /api/v1/compliance/operations`
  - `GET /api/v1/monitoring/operations`

## Compliance API

### `GET /api/v1/compliance/operations`

Uso:

- catalogo comercial + operacional das capacidades de compliance

Comportamento atual:

- `kyc_wallet` reflete o readiness do provider AML/KYT
- `due_diligence` e `source_of_funds` respondem `manual_review_required`
- `sanctions_check` agora aparece `live` no catalogo e no endpoint direto, ambos sustentados por cache local sincronizado

### `GET /api/v1/compliance/sanctions-check/{address}`

Uso:

- screening direto de sancoes via cache local sincronizado pelo worker

Comportamento atual:

- usa `sanctions_hits_cache` local
- responde `provider=sanctions_lists_cache`
- responde `provider_status=live`
- emite `SANCTIONS_CHECKED` ou `SANCTIONS_HIT` na trilha regulatoria
- registra `compliance_sanctions_checked` em `audit_logs` quando ha contexto organizacional

Response exemplo:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "sanctions_lists_cache",
  "provider_status": "live",
  "degraded_reason": null,
  "capability_status": "live",
  "lists": ["OFAC", "UN", "EU", "COAF"],
  "hit": false,
  "matched_lists": [],
  "entity_name": null,
  "designation_date": null,
  "checked_at": "2026-07-01T12:00:00+00:00"
}
```

### `POST /api/v1/compliance/blocks/evaluate`

Uso:

- avaliar bloqueio preventivo com base em sancoes, score AML e contexto operacional

Request:

```json
{
  "address": "0x1111111111111111111111111111111111111111",
  "chain": "ethereum",
  "aml_score": 92,
  "is_self_custody": false,
  "owner_identified": true,
  "is_international_transfer": true,
  "has_direct_mixer_contact": false,
  "has_chain_hopping": true,
  "structuring_detected": false,
  "entity_name": "Example Wallet",
  "entity_document": "12345678900",
  "case_id": null
}
```

Response:

```json
{
  "address": "0x1111111111111111111111111111111111111111",
  "chain": "ethereum",
  "action": "BLOCK_AND_ALERT",
  "requires_coaf_report": false,
  "decision_confidence": 0.97,
  "regulatory_basis": ["BCB 520 Art. 43 §2° V"],
  "matched_lists": ["OFAC_SDN"],
  "evidence_hash": "sha256",
  "block_id": "uuid",
  "screened_at": "2026-07-01T12:00:00+00:00"
}
```

### `POST /api/v1/compliance/blocks/{block_id}/lift`

Uso:

- remover bloqueio preventivo com prova de MFA externo homologado

Requisitos:

- `X-MFA-Mode=external_provider`
- `X-MFA-Provider-Homologated=true`
- `X-Org-Id` e usuario persistido valido

Erros relevantes:

- `401 missing_user_context`
- `403 linked_user_required_for_block_lift`
- `403 external_provider_mfa_required`
- `404 preventive_block_not_found`

### `POST /api/v1/compliance/counterparties`

Uso:

- criar contraparte com avaliacao KYC/KYB deterministica

Comportamento atual:

- calcula `risk_level`, `risk_rationale`, `enhanced_dd_required`, `next_review_date`
- persiste `counterparties` e `counterparty_history`
- registra evidencia `COUNTERPARTY_ONBOARDED`

### `GET /api/v1/compliance/counterparties`

Uso:

- listar contrapartes da organizacao com paginacao basica por `limit/offset`

## Report API

### `GET /api/v1/report-types`

Uso:

- catalogo comercial e operacional dos tipos de relatorio suportados pela plataforma

Comportamento atual:

- resolve aliases para o nome canonico antes do `quote` e do `start`
- reflete a hierarquia `free -> starter -> professional -> enterprise`
- preserva `plan lock` entre a cotacao e a execucao

Leitura canonica atual:

| Tipo canonico | Plano minimo | Formato | Observacao |
| --- | --- | --- | --- |
| `risk_check_instant` | `starter` | `json` | score AML 5D sem PDF |
| `technical_basic` | `starter` | `pdf` | relatorio tecnico basico |
| `technical_full` | `professional` | `pdf` | analise aprofundada |
| `compliance_aml` | `starter` | `pdf` | compliance/AML/KYT |
| `coaf_ready_report` | `professional` | `pdf` | baseline regulatoria |
| `legal_report` | `enterprise` | `pdf` | exige auth forte no download |
| `full_investigation` | `enterprise` | `pdf` | pacote mais completo |

Aliases relevantes:

- `technical`, `tech`, `basic` -> `technical_basic`
- `coaf`, `coaf_report`, `ros` -> `coaf_ready_report`
- `aml`, `kyt`, `compliance` -> `compliance_aml`
- `legal`, `juridico`, `parecer` -> `legal_report`
- `full`, `investigation` -> `full_investigation`
- `risk`, `instant`, `quick_check` -> `risk_check_instant`

### `GET /api/v1/reports`

Uso:

- listagem oficial de relatorios persistidos da organizacao com paginacao e filtros

Query params:

- `page` (default `1`)
- `limit` (default `20`, max `100`)
- `case_id` (opcional, UUID)
- `report_type` (opcional; aceita alias e resolve para canonico)

Response:

```json
{
  "data": [
    {
      "report_id": "f47ac10b58cc4372",
      "case_id": "11111111-1111-1111-1111-111111111111",
      "report_type_requested": "technical",
      "report_type": "technical_basic",
      "content_type": "application/pdf",
      "file_hash_sha256": "sha256",
      "onchain_hash": null,
      "created_at": "2026-07-03T12:00:00+00:00",
      "has_download_audit": true
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1,
  "has_more": false
}
```

### `POST /api/v1/reports/ros-coaf`

Uso:

- gerar draft `coaf_ready_report` e mover `ros_record` para `PENDING_APPROVAL`

Requisitos:

- role `ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- `X-MFA-Mode=external_provider`
- `X-MFA-Provider-Homologated=true`
- `X-2FA in {managed_externally, managed_externally_homologated, ok}`

Response:

```json
{
  "ros_id": "uuid",
  "report_id": "report-id",
  "report_type": "coaf_ready_report",
  "status": "PENDING_APPROVAL",
  "created_at": "2026-07-01T12:00:00+00:00",
  "file_hash_sha256": "sha256",
  "content_type": "application/pdf"
}
```

### `POST /api/v1/reports/ros-coaf/{ros_id}/approve`

Uso:

- aprovar ou rejeitar o ROS

Request:

```json
{
  "approved": false,
  "rejection_reason": "false_positive_documented"
}
```

Response:

```json
{
  "ros_id": "uuid",
  "status": "REJECTED",
  "approved_at": "2026-07-01T12:05:00+00:00",
  "approval_2fa_verified": false
}
```

### `POST /api/v1/reports/ros-coaf/{ros_id}/submitted`

Uso:

- registrar submissao manual ao COAF ONLINE

Request:

```json
{
  "coaf_protocol_number": "PROTOCOLO-123",
  "coaf_receipt_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

Response:

```json
{
  "ros_id": "uuid",
  "status": "SUBMITTED_MANUAL",
  "submitted_at": "2026-07-01T12:10:00+00:00",
  "coaf_protocol_number": "PROTOCOLO-123",
  "coaf_receipt_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
}
```

### `GET /api/v1/reports/{report_id}` e `GET /api/v1/reports/{report_id}/download`

Uso:

- metadados e download de relatorios deterministas

Regra para `legal_report`:

- `X-Auth-Method=jwt`
- `X-Role=ADMIN`
- `X-2FA=ok` no trilho local
- ou `X-MFA-Mode=external_provider` + `X-MFA-Provider-Homologated=true` + `X-2FA=managed_externally|managed_externally_homologated`

## Monitoring API

### `GET /api/v1/monitoring/operations`

Uso:

- catalogo comercial e operacional das janelas de monitoring suportadas

Leitura canonica atual:

| Operacao canonica | Plano minimo | Duracao | Formato |
| --- | --- | --- | --- |
| `monitoring_30days` | `starter` | 30 dias | `json+alerts` |
| `monitoring_90days` | `professional` | 90 dias | `json+alerts` |
| `monitoring_365days` | `enterprise` | 365 dias | `json+alerts` |

Aliases relevantes:

- `30d`, `monthly` -> `monitoring_30days`
- `90d`, `quarterly` -> `monitoring_90days`
- `365d`, `annual` -> `monitoring_365days`

### `GET /api/v1/monitoring/admin/operational-alerts`

Uso:

- listar incidentes operacionais globais com `status`, `triage_status`, `service`, `receiver`, `severity`, `cursor` e `limit`

### `POST /api/v1/monitoring/admin/operational-alerts/export`

Uso:

- exportar backlog global em `csv|json`
- gera `operational_alerts_exported` em `audit_logs`

## Operations API

### `GET /api/v1/operations/work-items`

Uso:

- listar a fila operacional compartilhada por `module`, `resource_type`, `queue_status`, `owner_user_id` e `limit`

Comportamento atual:

- roda no `compliance-api`
- aplica `RLS` por `organization_id`
- suporta o bootstrap atual do frontend em `sanctions` e `alerts`

Query params relevantes:

- `module`
- `resource_type`
- `queue_status`
- `owner_user_id`
- `limit`

Response exemplo:

```json
{
  "data": [
    {
      "id": "uuid",
      "module": "sanctions",
      "resource_type": "sanctions_screening",
      "resource_id": "uuid",
      "case_id": null,
      "owner_user_id": null,
      "queue_status": "UNDER_REVIEW",
      "priority": "high",
      "due_at": "2026-07-02T20:00:00Z",
      "title": "Sanctions HIT • 0xabc...",
      "note": "hit exige triagem",
      "metadata": {
        "address": "0xabc...",
        "chain": "ethereum",
        "owner_label": "analyst-a"
      },
      "created_at": "2026-07-02T12:00:00Z",
      "updated_at": "2026-07-02T12:05:00Z",
      "last_activity_at": "2026-07-02T12:05:00Z"
    }
  ]
}
```

### `POST /api/v1/operations/work-items`

Uso:

- criar ou fazer `upsert` da fila compartilhada por `organization_id + resource_type + resource_id`

Corpo:

```json
{
  "module": "alerts",
  "resource_type": "operational_alert",
  "resource_id": "uuid",
  "case_id": null,
  "priority": "critical",
  "queue_status": "UNDER_REVIEW",
  "due_at": null,
  "title": "Alert HighErrorRate",
  "note": "incidente aberto para triagem",
  "metadata": {
    "service": "monitoring-api",
    "severity": "critical",
    "triage_status": "pending"
  }
}
```

Observacoes:

- o endpoint aceita os modulos `alerts`, `sanctions`, `blocks`, `reports`, `ros_coaf`, `counterparties` e `evidence`
- `sanctions` persiste o `owner` textual atual em `metadata.owner_label`, porque o assignment formal por `owner_user_id` ainda nao esta completo no frontend

### `PATCH /api/v1/operations/work-items/{work_item_id}`

Uso:

- atualizar prioridade, status, prazo, titulo, nota e `metadata`

Regras importantes:

- transicoes invalidas retornam `409 invalid_transition`
- `REJECTED` exige nota e retorna `422 note_required_for_rejected` se ausente

### `GET /api/v1/operations/work-items/{work_item_id}/timeline`

Uso:

- recuperar timeline operacional de transicoes e eventos do work-item

### `POST /api/v1/operations/work-items/{work_item_id}/comments`

Uso:

- registrar comentario estruturado de `note`, `decision` ou `handoff`

Leitura canonica atual do frontend:

- `/sanctions` consome `GET/POST/PATCH /work-items` como fonte primaria da fila operacional
- `/alerts` consome `GET/POST/PATCH /work-items` para rastrear incidentes e encerrar o item compartilhado ao fazer `ack`

## Erros Relevantes

### Auth e RBAC

- `401 missing_authorization`
- `401 invalid_token`
- `401 invalid_api_key`
- `403 admin_required`
- `403 privileged_read_role_required`
- `403 legal_report_requires_jwt_auth`
- `403 legal_report_requires_admin_role`
- `403 2fa_required`
- `403 coaf_report_requires_external_provider_mfa`
- `403 coaf_report_requires_homologated_provider`

### Compliance e ROS

- `404 ros_record_not_found`
- `409 ros_record_not_pending_approval`
- `409 ros_record_not_approved`
- `422 rejection_reason_required`
- `422 coaf_protocol_number_required`
- `422 coaf_receipt_hash_must_be_sha256`
- `409 invalid_transition`
- `422 note_required_for_rejected`

## Notas de Contrato

- degradacao honesta e parte do contrato do produto atual; ausencia de score nao e bug quando a capability e manual ou depende de provider nao homologado
- `sanctions-check` direto e o catalogo de operacoes agora convergem para `live` via cache local sincronizado
