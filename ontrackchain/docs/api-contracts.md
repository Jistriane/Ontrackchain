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

## Frontend/Auth Bootstrap

### `GET /auth/config`

Uso:

- bootstrap canônico do login do frontend
- preflight de `OIDC` para Playwright e troubleshooting operacional
- resolução do modo efetivo de autenticação sem depender do carregamento completo da sessão

Comportamento atual:

- no `standalone showcase`, responde configuração local com `auth_mode=dev`, `effective_auth_mode=dev` e bloco `mfa` marcado como gerenciado pelo showcase
- no `full-stack`, o frontend tenta proxy para `${INTERNAL_AUTH_BASE_URL}/auth/config`
- se o upstream estiver indisponível, o frontend devolve `fallback config` derivado das envs locais para não quebrar o bootstrap da tela de login

Campos mínimos esperados:

- `auth_mode`
- `effective_auth_mode`
- `app_env`
- `dev_auth_enabled`
- `mfa.enabled`
- `mfa.method`
- `mfa.managed_by`
- `mfa.provider`
- `mfa.provider_homologated`
- `oidc.enabled`
- `oidc.provider`
- `oidc.issuer_url`
- `oidc.client_id`
- `oidc.audience`
- `oidc.authorization_url`
- `oidc.token_url`

Response exemplo:

```json
{
  "auth_mode": "oidc",
  "effective_auth_mode": "oidc",
  "app_env": "staging",
  "dev_auth_enabled": false,
  "mfa": {
    "enabled": true,
    "method": "external_provider",
    "managed_by": "external_provider",
    "provider": "keycloak",
    "provider_homologated": false,
    "issuer": "OnTrackChain",
    "account_name": "local-admin@ontrackchain",
    "period_seconds": 30,
    "digits": 6
  },
  "oidc": {
    "enabled": true,
    "provider": "keycloak",
    "issuer_url": "https://auth.staging.ontrackchain.com/realms/ontrackchain",
    "client_id": "ontrackchain-web",
    "audience": "ontrackchain-api",
    "authorization_url": "https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/auth",
    "token_url": "https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/token"
  }
}
```

### `GET /api/healthz` do frontend

Uso:

- verificar drift de env e modelo de deployment do frontend sem depender do login completo

Comportamento atual:

- responde `deploymentModel=render-frontend-standalone-showcase` quando o frontend está explicitamente em showcase
- também pode responder `deploymentModel=render-frontend-standalone-showcase` com `hostedShowcaseFallback=true` quando o runtime hospedado perde `INTERNAL_AUTH_BASE_URL` ou `INTERNAL_KEYCLOAK_BASE_URL`
- no `full-stack` saudável, responde `deploymentModel=render-full-stack-staging`

Campos relevantes:

- `status`
- `deploymentModel`
- `standaloneShowcaseMode`
- `hostedShowcaseFallback`
- `missingEnvKeys`

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

### `POST /api/v1/compliance/kyc-wallet`

Uso:

- screening AML/KYT autenticado com recomendação operacional de onboarding

Comportamento atual:

- usa o provider AML/KYT configurado para screening autenticado
- registra `compliance_kyc_wallet_checked` em `audit_logs` quando há contexto organizacional
- exige `X-Role` operacional (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`)
- retorna `403 kyc_wallet_role_required` quando o ator não pertence ao recorte

### `POST /api/v1/compliance/risk-check`

Uso:

- score AML/KYT autenticado com dimensões analíticas detalhadas

Comportamento atual:

- usa o provider AML/KYT configurado para scoring autenticado
- registra `compliance_risk_checked` em `audit_logs` com dimensões e payload do provider quando há contexto organizacional
- exige `X-Role` operacional (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`)
- retorna `403 risk_check_role_required` quando o ator não pertence ao recorte

### `POST /api/v1/compliance/due-diligence`

Uso:

- triagem manual assistida de due diligence com contexto opcional de contraparte

Comportamento atual:

- responde `manual_review_required` via capability local
- registra `compliance_due_diligence_checked` em `audit_logs` quando há contexto organizacional
- exige `X-Role` operacional (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`)
- retorna `403 due_diligence_role_required` quando o ator não pertence ao recorte

### `POST /api/v1/compliance/source-of-funds`

Uso:

- análise assistida de origem de fundos com contexto de valor e finalidade

Comportamento atual:

- responde `manual_review_required` via capability local
- registra `compliance_source_of_funds_checked` em `audit_logs` quando há contexto organizacional
- exige `X-Role` operacional (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`)
- retorna `403 source_of_funds_role_required` quando o ator não pertence ao recorte

### `GET /api/v1/compliance/sanctions-check/{address}`

Uso:

- screening direto de sancoes via cache local sincronizado pelo worker

Comportamento atual:

- usa `sanctions_hits_cache` local
- responde `provider=sanctions_lists_cache`
- responde `provider_status=live`
- emite `SANCTIONS_CHECKED` ou `SANCTIONS_HIT` na trilha regulatoria
- registra `compliance_sanctions_checked` em `audit_logs` quando ha contexto organizacional
- exige `X-Role` operacional (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`) e retorna `sanctions_check_role_required` quando o ator nao pertence ao recorte

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

### `POST /api/v1/compliance/start`

Uso:

- materializar um `case` de compliance a partir de um `quote` valido, respeitando plan lock e billing do snapshot

Requisitos:

- `X-Org-Id` valido
- body com `confirmed=true`
- role `ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

Erros relevantes:

- `403 compliance_start_role_required`
- `412 quote_confirmation_required`
- `404 quote_not_found`
- `409 quote_already_used`
- `410 quote_expired`

### `POST /api/v1/compliance/cases/{case_id}/report`

Uso:

- gerar o relatório operacional do `case` de compliance já materializado, delegando a geração canônica ao `report-api`

Requisitos:

- `X-Org-Id` valido
- `case_id` pertencente à organizacao e com `case_type='compliance'`
- role `ADMIN|ANALYST`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint
- a política do ponto de entrada espelha o gate já aplicado em `POST /api/v1/reports/generate`, evitando drift entre `compliance-api` e `report-api`

Erros relevantes:

- `403 compliance_case_report_role_required`
- `404 compliance_case_not_found`

### `POST /api/v1/compliance/blocks/evaluate`

Uso:

- avaliar bloqueio preventivo com base em sancoes, score AML e contexto operacional

Requisitos:

- `X-Org-Id` valido
- role `ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

Erros relevantes:

- `403 counterparty_create_role_required`
- `403 linked_user_required_for_counterparty_creation`

Erros relevantes:

- `403 block_evaluate_role_required`

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
- role `ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- `ANALYST` permanece em `blocks/evaluate`, mas nao executa o lift regulatorio

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

Requisitos:

- `X-Org-Id` valido
- role `ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

### `POST /api/v1/compliance/estimate`

Uso:

- cotar custo e operacao canonica antes da abertura de um case de compliance

Comportamento atual:

- resolve alias operacional para o identificador canônico antes do quote
- persiste `compliance_quotes` com `quote_id`, plano, operação e tabela de pricing aplicada
- exige `X-Role` operacional compatível (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER`, `OTK_COMPLIANCE_OFFICER`)
- retorna `403 compliance_estimate_role_required` quando a sessão não pertence ao recorte humano de contratação
- persiste `authorization_denied` auditado com `request_id`, `effective_role`, `allowed_roles` e endpoint quando a role não atende

### `PATCH /api/v1/compliance/counterparties/{counterparty_id}/review`

Uso:

- registrar revisao DD/SoF e decisao operacional sobre contraparte

Requisitos:

- `X-Org-Id` valido
- usuario persistido valido
- role `ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER|REVIEWER|OTK_REVIEWER`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint
- `ANALYST` permanece no onboarding/operacao de `counterparties`, mas nao executa a revisao formal DD/SoF

### `GET /api/v1/compliance/counterparties`

Uso:

- listar contrapartes da organizacao com paginacao basica por `limit/offset`

Comportamento atual:

- retorna carteira operacional com `risk_level`, `kyc_status`, `PEP`, janela de revisao e snapshot DD/SoF
- exige `X-Role` regulatorio compativel (`ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER`, `OTK_COMPLIANCE_OFFICER`, `REVIEWER`, `OTK_REVIEWER`)
- retorna `403 counterparty_read_role_required` quando a sessao nao possui leitura operacional regulatoria
- persiste `authorization_denied` auditado com `request_id`, `effective_role`, `allowed_roles` e endpoint quando a role nao atende

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

## Billing API

### `GET /api/v1/billing/balance`

Uso:

- leitura do saldo financeiro consolidado do tenant (`credits_available`, `credits_reserved`, `credits_used_total`)

Requisitos:

- role `ADMIN|BILLING_ADMIN|OTK_BILLING_ADMIN`
- `X-Org-Id` valido
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

Response:

```json
{
  "credits_available": 120.0,
  "credits_reserved": 15.5,
  "credits_used_total": 420.75
}
```

### `GET /api/v1/billing/reconciliation`

Uso:

- snapshot reconciliavel do dominio financeiro para conciliacao administrativa do tenant
- agrega saldo consolidado, backlog de `quotes` por dominio e movimentos recentes do `credit_ledger`

Query params:

- `limit` (default `10`, min `1`, max `25`) para limitar os movimentos recentes retornados do `credit_ledger`

Requisitos:

- role `ADMIN|BILLING_ADMIN|OTK_BILLING_ADMIN`
- `X-Org-Id` valido
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

Response:

```json
{
  "generated_at": "2026-07-11T15:30:00+00:00",
  "balance": {
    "credits_available": 120.0,
    "credits_reserved": 15.5,
    "credits_used_total": 420.75
  },
  "quotes": {
    "investigation": {
      "open_total": 2,
      "expired_total": 1
    },
    "compliance": {
      "open_total": 1,
      "expired_total": 0
    },
    "monitoring": {
      "open_total": 3,
      "expired_total": 2
    },
    "open_total": 6,
    "expired_total": 3
  },
  "ledger": {
    "total_entries": 3,
    "action_totals": [
      {
        "action": "CONFIRMED",
        "entry_count": 2,
        "amount_total": 7.5
      },
      {
        "action": "PRE_HOLD",
        "entry_count": 1,
        "amount_total": 3.0
      }
    ],
    "recent": [
      {
        "id": "ledger-1",
        "case_id": "case-1",
        "action": "CONFIRMED",
        "amount": 4.5,
        "balance_after": 120.0,
        "request_id": "req-1",
        "quote_id": "quote-1",
        "metadata": {
          "quote_id": "quote-1",
          "request_id": "req-1"
        },
        "created_at": "2026-07-11T15:25:00+00:00"
      }
    ]
  }
}
```

### `GET /api/v1/reports`

Uso:

- listagem oficial de relatorios persistidos da organizacao com paginacao e filtros

Query params:

- `page` (default `1`)
- `limit` (default `20`, max `100`)
- `report_id` (opcional; match exato do `external_report_id`)
- `case_id` (opcional, UUID)
- `report_type` (opcional; aceita alias e resolve para canonico)
- `created_from` (opcional; ISO datetime, inclusivo)
- `created_to` (opcional; ISO datetime, inclusivo)

Erros relevantes:

- `422 invalid_case_id`
- `422 invalid_created_range`

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

### `POST /api/v1/reports/generate`

Uso:

- gerar relatorio basico on-demand a partir de `case_id` e `report_type`

Requisitos:

- contexto organizacional valido
- role `ADMIN|ANALYST`
- quando a role nao atende, o backend persiste `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint

Request:

```json
{
  "case_id": "case-123",
  "report_type": "technical",
  "include_onchain_hash": false
}
```

Response:

```json
{
  "report_id": "f47ac10b58cc4372",
  "case_id": "case-123",
  "report_type_requested": "technical",
  "report_type": "technical_basic",
  "created_at": "2026-07-10T12:00:00+00:00",
  "file_hash_sha256": "sha256",
  "onchain_hash": null,
  "content_type": "application/pdf"
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

Requisitos:

- role `ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER|LEGAL_REVIEWER|OTK_LEGAL_REVIEWER|REVIEWER|OTK_REVIEWER`
- `X-MFA-Mode=external_provider`
- `X-MFA-Provider-Homologated=true`
- `X-2FA in {managed_externally, managed_externally_homologated, ok}`
- o backend registra `authorization_denied` quando a role nao pertence ao conjunto permitido para aprovacao formal

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

Requisitos:

- role `ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`
- `X-MFA-Mode=external_provider`
- `X-MFA-Provider-Homologated=true`
- `X-2FA in {managed_externally, managed_externally_homologated, ok}`
- o backend registra `authorization_denied` quando papeis de revisao formal tentam executar a submissao manual

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

### `GET /api/v1/reports/ros-coaf`

Uso:

- listagem oficial paginada de `ros_records` com filtros por `ros_id`, `case_id`, `report_id` e `status`

Response:

```json
{
  "data": [
    {
      "ros_id": "uuid",
      "case_id": "uuid",
      "status": "PENDING_APPROVAL",
      "report_id": "f47ac10b58cc4372",
      "created_at": "2026-07-01T12:00:00+00:00",
      "approved_at": null,
      "submitted_at": null,
      "coaf_protocol_number": "",
      "coaf_receipt_hash": "",
      "rejection_reason": "",
      "approval_2fa_verified": false,
      "submission_deadline": "2026-07-03T12:00:00+00:00",
      "deadline_breached": false,
      "last_activity_at": "2026-07-01T12:00:00+00:00"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1,
  "has_more": false
}
```

### `GET /api/v1/reports/ros-coaf/{ros_id}`

Uso:

- leitura oficial do `ros_record` com a trilha de auditoria de domínio (`audit_logs`)

Response:

```json
{
  "ros_id": "uuid",
  "case_id": "uuid",
  "report_id": "f47ac10b58cc4372",
  "status": "PENDING_APPROVAL",
  "tipologia_code": "COAF",
  "tipologia_description": "Tipologia",
  "trigger_reason": "reason",
  "suspected_amount_brl": 0,
  "suspected_address": "0x...",
  "suspected_chain": "ethereum",
  "pdf_hash": "sha256",
  "pdf_path": "/reports/....pdf",
  "generated_at": "2026-07-01T12:00:00+00:00",
  "approved_at": null,
  "submitted_at": null,
  "approval_2fa_verified": false,
  "rejection_reason": "",
  "submission_deadline": "2026-07-03T12:00:00+00:00",
  "deadline_breached": false,
  "coaf_protocol_number": "",
  "coaf_receipt_hash": "",
  "evidence_hash": "sha256",
  "evidence_trail_ref": "ref",
  "created_at": "2026-07-01T12:00:00+00:00",
  "updated_at": "2026-07-01T12:00:00+00:00",
  "retain_until": "2026-08-01T12:00:00+00:00",
  "audit": [
    {
      "id": "uuid",
      "action": "coaf_report_generated",
      "user_id": "uuid",
      "created_at": "2026-07-01T12:00:00+00:00",
      "metadata": {}
    }
  ]
}
```

### `GET /api/v1/reports/ros-coaf/{ros_id}/regulatory-dossier`

Uso:

- emissao do dossie regulatorio unificado (dominio + operacao) para o `ros_id`, consolidando:
  - leitura oficial do `ros_record` (inclui `audit_logs`)
  - snapshot do `regulatory_work_item` (quando existir)
  - eventos e comentarios operacionais persistidos (`regulatory_work_events`/`regulatory_work_comments`)
  - timeline unificada em ordem cronologica

Query:

- `limit` (default 50, max 200)

Contrato HTTP:

- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="ontrackchain-ros-coaf-regulatory-dossier-{ros_id}.json"`
- `X-Ontrack-Dossier-SHA256: {sha256-do-json-do-dossie}`
- a emissao/download do artefato gera `audit_log` oficial com `action=coaf_regulatory_dossier_downloaded` em `resource_type=ros_record`

Response:

```json
{
  "version": "v1",
  "generated_at": "2026-07-01T12:00:00+00:00",
  "dossier_sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
  "ros_record": { "ros_id": "uuid", "audit": [] },
  "work_item": { "id": "uuid", "module": "ros_coaf", "resource_type": "ros_record", "resource_id": "uuid" },
  "work_events": [],
  "work_comments": [],
  "unified_timeline": [
    {
      "id": "audit-uuid",
      "source": "domain_audit",
      "label": "coaf_report_generated",
      "detail": "request_id: ...",
      "actor": "uuid",
      "created_at": "2026-07-01T12:00:00+00:00"
    }
  ]
}
```

### `GET /api/v1/reports/{report_id}` e `GET /api/v1/reports/{report_id}/download`

Uso:

- metadados e download de relatorios deterministas

Requisitos para `GET /api/v1/reports/{report_id}`:

- `ADMIN`, `AUDITOR` e `ANALYST` podem ler metadados e contexto operacional rico do relatório
- `VIEWER` permanece apenas no trilho de catálogo/listagem e recebe `403 report_detail_role_required` ao tentar abrir o detalhe dedicado
- o App Router de `/api/app/reports/{reportId}` preserva esse recorte e devolve o `detail` canônico para o cockpit

Requisitos para `GET /api/v1/reports/{report_id}/download`:

- `ADMIN`, `AUDITOR` e `ANALYST` podem baixar o artefato comum do relatório
- `VIEWER` nao pode baixar o artefato comum e recebe `403 report_download_role_required`
- o App Router de `/api/app/reports/download` preserva o recorte e faz bloqueio precoce coerente com a UX

Regra para `legal_report`:

- `X-Auth-Method=jwt`
- `X-Role=ADMIN`
- `X-2FA=ok` no trilho local
- ou `X-MFA-Mode=external_provider` + `X-MFA-Provider-Homologated=true` + `X-2FA=managed_externally|managed_externally_homologated`

## Auth Service

### `POST /api/v1/team/users`

Uso:

- criar administrativamente um usuário local no diretório do tenant

Requisitos:

- `X-Org-Id` valido
- role `ADMIN`
- body com `email`, `role`, `status` e opcionais `name`, `note`
- quando a role nao atende, o backend retorna `403 team_user_create_role_required`
- o App Router de `/api/app/team/users` preserva o `detail` canônico do backend mesmo quando a resposta chega sem corpo útil

Erros relevantes:

- `403 team_user_create_role_required`
- `409 team_user_email_already_exists`
- `500 team_user_create_failed`

### `PATCH /api/v1/team/users/{member_id}`

Uso:

- editar administrativamente um usuário local do tenant ou desativá-lo por `status=disabled`

Requisitos:

- `X-Org-Id` valido
- role `ADMIN`
- `member_id` válido e pertencente ao tenant atual
- quando a operação é edição comum, o backend retorna `403 team_user_update_role_required` para role não autorizada
- quando a operação é desativação (`status=disabled`), o backend retorna `403 team_user_disable_role_required` para role não autorizada
- o App Router de `/api/app/team/users/{memberId}` preserva o `detail` canônico do backend, diferenciando `update` de `disable`

Erros relevantes:

- `403 team_user_update_role_required`
- `403 team_user_disable_role_required`
- `404 team_user_not_found`
- `409 team_user_email_already_exists`
- `422 invalid_team_user_id`
- `500 team_user_update_failed`

### `GET /api/v1/team/users/{member_id}/external-identities`

Uso:

- ler administrativamente os vínculos federados persistidos de um usuário local do tenant

Requisitos:

- `X-Org-Id` valido
- role `ADMIN`
- `member_id` válido e pertencente ao tenant atual
- quando a role nao atende, o backend retorna `403 team_federated_identity_read_role_required`
- o App Router de `/api/app/team/users/{memberId}/external-identities` preserva o `detail` canônico do backend mesmo quando a resposta chega sem corpo útil

Erros relevantes:

- `403 team_federated_identity_read_role_required`
- `404 team_user_not_found`
- `422 invalid_team_user_id`

### `POST /api/v1/team/users/{member_id}/external-identities`

Uso:

- vincular manualmente um principal federado persistido ao usuário local selecionado do tenant

Requisitos:

- `X-Org-Id` valido
- `member_id` pertencente ao tenant atual
- role `ADMIN`
- body com `provider` e `external_subject` validos; `email_snapshot` e `role_snapshot` permanecem opcionais
- quando a role nao atende, o backend retorna `403 team_federated_identity_link_role_required`
- o App Router de `/api/app/team/users/{memberId}/external-identities` preserva o `detail` canônico do backend, evitando drift entre BFF e `auth-service`
- o backend emite trilha auditavel local com `team_external_identity_linked`

Erros relevantes:

- `403 team_federated_identity_link_role_required`
- `409 team_external_identity_already_linked`
- `422 team_external_identity_provider_required`
- `422 team_external_identity_provider_invalid`
- `422 team_external_identity_subject_required`

### `DELETE /api/v1/team/users/{member_id}/external-identities`

Uso:

- desvincular manualmente um principal federado persistido do usuário local selecionado do tenant

Requisitos:

- `X-Org-Id` valido
- `member_id` pertencente ao tenant atual
- role `ADMIN`
- body com `provider` e `external_subject` validos
- quando a role nao atende, o backend retorna `403 team_federated_identity_unlink_role_required`
- o App Router de `/api/app/team/users/{memberId}/external-identities` preserva o `detail` canônico do backend, evitando mascarar recusas de autorizacao
- o backend emite trilha auditavel local com `team_external_identity_unlinked`

Erros relevantes:

- `403 team_federated_identity_unlink_role_required`
- `404 team_external_identity_not_found`
- `422 team_external_identity_provider_required`
- `422 team_external_identity_provider_invalid`
- `422 team_external_identity_subject_required`

### `GET /api/v1/team/federated-directory/users`

Uso:

- buscar candidatos no diretório federado do IdP com enriquecimento local de vínculo, match por tenant e validação preliminar de role

Query:

- `query` obrigatório
- `limit` opcional (default `20`)

Requisitos:

- `X-Org-Id` valido
- role `ADMIN`
- quando a role nao atende, o backend retorna `403 team_federated_directory_search_role_required`
- o App Router de `/api/app/team/federated-directory/users` preserva o `detail` canônico do backend mesmo quando a resposta chega sem corpo útil
- o backend registra `team_federated_directory_searched` em `audit_logs`

Erros relevantes:

- `403 team_federated_directory_search_role_required`
- `422 federated_directory_query_required`
- `422 federated_directory_limit_invalid`
- `503 federated_directory_unavailable`
- `503 federated_directory_forbidden`

### `POST /api/v1/team/federated-directory/suggestions`

Uso:

- validar tardiamente uma sugestão de vínculo federado antes do `link` efetivo, consultando o IdP e cruzando `member_id`, `org`, `email` e `role`

Requisitos:

- `X-Org-Id` valido
- role `ADMIN`
- body com `member_id`, `provider` e `external_subject`
- quando a role nao atende, o backend retorna `403 team_federated_directory_suggestion_role_required`
- o App Router de `/api/app/team/federated-directory/suggestions` preserva o `detail` canônico do backend mesmo quando a resposta chega sem corpo útil
- o backend registra `team_federated_directory_suggestion_validated` em `audit_logs`

Erros relevantes:

- `403 team_federated_directory_suggestion_role_required`
- `404 federated_directory_candidate_not_found`
- `422 invalid_team_user_id`
- `422 team_external_identity_provider_invalid`
- `422 team_external_identity_subject_required`
- `503 federated_directory_unavailable`

## Evidence API

### `POST /api/app/reports/formal-dossier`

Uso:

- compor e exportar o dossiê formal JSON de um relatório a partir do cockpit `reports`

Comportamento atual:

- autentica a sessão via `auth-service /validate`
- exige role `ADMIN` ou `AUDITOR`
- quando a role nao atende, retorna `403 report_formal_dossier_role_required`
- chama `POST /api/v1/audit/evidence-export` para compor o bundle correlacionado
- responde com JSON baixável e `Content-Disposition` próprio do dossiê formal

Erros relevantes:

- `403 report_formal_dossier_role_required`
- `422 invalid_formal_dossier_payload`

### `POST /api/app/evidence/manual-package`

Uso:

- exportar o pacote manual canonico DD/SoF com manifesto `manual_review_package/v2`
- emitir o evento oficial `evidence_manual_review_package_exported` em `audit_logs`

Comportamento atual:

- monta o pacote canônico no App Router
- chama `POST /api/v1/audit/evidence-export` para compor o bundle correlacionado
- chama `POST /api/v1/audit/manual-package-export` para registrar o evento oficial
- retorna JSON baixável com header `X-Ontrack-Manual-Package-SHA256`

Contrato HTTP:

- `Content-Type: application/json`
- `Content-Disposition: attachment; filename="ontrackchain-manual-review-<dominio>-<scope_id>.json"`
- `X-Ontrack-Manual-Package-SHA256: {payload_sha256}`

### `POST /api/v1/evidence/manual-package/signoff-requests`

Uso:

- iniciar a trilha institucional de selagem forte para um `package_sha256`

Regras:

- roles permitidas: `ADMIN`
- idempotencia logica por `(organization_id, package_sha256, policy_version)`
- cria ou reaproveita `evidence_package_seals`
- abre o status em `pending_signoff`
- emite `evidence_manual_review_package_signoff_requested`

Request:

```json
{
  "request_id": "req-dd-1",
  "report_id": "rep-dd-1",
  "scope_id": "req-dd-1",
  "manual_review_action": "compliance_due_diligence_checked",
  "package_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "manifest_schema_version": "manual_review_package/v2",
  "classification": "restricted_regulatory",
  "signoff_mode": "compliance_ops_signoff",
  "package_kind": "manual_review_package",
  "policy_version": "manual_package_sealing/v1"
}
```

Response:

```json
{
  "seal_id": "8d5f1111-2222-3333-4444-555555555555",
  "request_id": "req-dd-1",
  "report_id": "rep-dd-1",
  "scope_id": "req-dd-1",
  "manual_review_action": "compliance_due_diligence_checked",
  "package_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "seal_status": "pending_signoff",
  "required_signers": ["compliance_owner", "ops_owner"],
  "completed_signoffs": 0,
  "approved_required_signoffs": 0,
  "required_signoffs": 2,
  "signoffs": []
}
```

Erros relevantes:

- `403 manual_package_admin_role_required`
- `500 manual_package_seal_not_created`

### `POST /api/v1/evidence/manual-package/seals/{seal_id}/signoffs`

Uso:

- registrar um sign-off institucional por papel

Regras:

- roles permitidas: `ADMIN`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER`
- papeis suportados: `compliance_owner`, `ops_owner`, `legal_owner_optional`
- metodos suportados: `platform_authenticated_2fa`, `governance_ticket`
- o status evolui para `ready_to_seal` quando o quorum `Compliance + Ops` estiver completo
- vinculo obrigatorio entre role autenticada e `signer_role`
- quando `signoff_method=platform_authenticated_2fa`, o backend exige MFA real:
- `local_totp` com `X-2FA=ok`; ou
- `external_provider` homologado com `X-MFA-Provider-Homologated=true` e `X-2FA` em `managed_externally|managed_externally_homologated|ok`
- quando a validacao MFA falha, o backend registra `evidence_manual_review_package_mfa_violation` em `audit_logs`
- o snapshot operacional e o Prometheus passam a expor total + breakdown `last_hour` para `2fa_required` e `mfa_not_homologated_for_oidc`
- `ADMIN` pode assinar qualquer papel
- `COMPLIANCE_OFFICER` pode assinar apenas `compliance_owner`
- `LEGAL_REVIEWER` pode assinar apenas `legal_owner_optional`
- `REVIEWER` pode assinar apenas `legal_owner_optional`
- emite `evidence_manual_review_package_signoff_recorded`

Request:

```json
{
  "decision": "approved",
  "signer_role": "compliance_owner",
  "signoff_method": "governance_ticket",
  "ticket_ref": "GOV-142",
  "notes": "Checklist aprovado",
  "signer_display_name": "Compliance Owner",
  "metadata": {
    "source": "evidence_manual_package_ui"
  }
}
```

Erros relevantes:

- `403 manual_package_signoff_role_required`
- `403 manual_package_signer_role_mismatch`
- `403 2fa_required`
- `403 mfa_not_homologated_for_oidc`
- `404 manual_package_seal_not_found`
- `409 manual_package_seal_locked`
- `409 manual_package_signoff_role_already_recorded`
- `500 manual_package_signoff_not_recorded`

### `POST /api/v1/evidence/manual-package/seals/{seal_id}/finalize`

Uso:

- finalizar a selagem institucional quando o selo estiver em `ready_to_seal`

Regras:

- roles permitidas: `ADMIN`
- exige quorum aprovado conforme `signoff_mode`
- persiste `signature_algorithm`, `certificate_bundle_ref`, `seal_envelope` e `verification_summary`
- emite `evidence_manual_review_package_sealed`

Request:

```json
{
  "metadata": {
    "source": "evidence_manual_package_ui",
    "request_id": "req-dd-1",
    "report_id": "rep-dd-1"
  }
}
```

Response relevante:

```json
{
  "seal_id": "8d5f1111-2222-3333-4444-555555555555",
  "seal_status": "sealed",
  "signature_algorithm": "HS256",
  "certificate_bundle_ref": "local-hs256-trust-bundle",
  "sealed_at": "2026-07-09T21:00:00+00:00",
  "verification_summary": {
    "seal_backend": "local_hs256",
    "verification_method": "local_hs256_self_check"
  }
}
```

Erros relevantes:

- `403 manual_package_admin_role_required`
- `404 manual_package_seal_not_found`
- `409 manual_package_seal_not_ready`
- `409 manual_package_signoff_incomplete`
- `424 manual_seal_secret_missing`

### `POST /api/v1/evidence/manual-package/seals/{seal_id}/revoke`

Uso:

- revogar formalmente um selo institucional existente

Regras:

- roles permitidas: `ADMIN`
- requer `ticket_ref` e `reason`
- permitido em qualquer estado, exceto `revoked` e `superseded`
- emite `evidence_manual_review_package_seal_revoked`

Request:

```json
{
  "ticket_ref": "GOV-555",
  "reason": "Documento substituido",
  "metadata": {
    "source": "evidence_manual_package_ui"
  }
}
```

Erros relevantes:

- `403 manual_package_admin_role_required`
- `404 manual_package_seal_not_found`
- `409 manual_package_seal_already_revoked`
- `409 manual_package_seal_already_superseded`

### `POST /api/v1/evidence/manual-package/seals/{seal_id}/supersede`

Uso:

- superseder um selo apontando explicitamente para um novo selo `sealed`

Regras:

- roles permitidas: `ADMIN`
- requer `superseded_by_seal_id`, `ticket_ref` e `reason`
- o selo substituto deve existir, pertencer ao mesmo tenant e estar em `sealed`
- emite `evidence_manual_review_package_seal_superseded`

Request:

```json
{
  "superseded_by_seal_id": "99999999-8888-7777-6666-555555555555",
  "ticket_ref": "GOV-777",
  "reason": "Nova versao aprovada",
  "metadata": {
    "source": "evidence_manual_package_ui"
  }
}
```

Erros relevantes:

- `403 manual_package_admin_role_required`
- `404 manual_package_seal_not_found`
- `409 manual_package_seal_revoked`
- `409 manual_package_seal_already_superseded`
- `409 manual_package_supersede_target_not_sealed`
- `409 manual_package_supersede_target_revoked`
- `409 manual_package_supersede_target_superseded`
- `422 manual_package_supersede_target_invalid`

### `GET /api/v1/evidence/manual-package/seals/{seal_id}`

Uso:

- leitura direta do selo por identificador tecnico
- contrato secundario, util para auditoria, governanca e correlacao administrativa

Regras:

- roles permitidas: `ADMIN`, `AUDITOR`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER`
- retorna o mesmo payload serializado das operacoes de escrita

Erros relevantes:

- `403 manual_package_read_role_required`
- `404 manual_package_seal_not_found`

### `GET /api/v1/evidence/manual-package/seals/by-digest`

Uso:

- leitura canonica do selo no frontend a partir de `package_sha256`

Query:

- `package_sha256` obrigatorio
- `policy_version` opcional, default `manual_package_sealing/v1`

Regras:

- roles permitidas: `ADMIN`, `AUDITOR`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER`
- contrato preferencial para `evidence`, pois correlaciona o selo ao pacote exportado e aos eventos de auditoria

Erros relevantes:

- `403 manual_package_read_role_required`
- `404 manual_package_seal_not_found`

### Payload serializado de `ManualPackageSeal`

Campos principais:

- `seal_id`
- `request_id`
- `report_id`
- `scope_id`
- `manual_review_action`
- `package_sha256`
- `seal_status`
- `signature_algorithm`
- `certificate_bundle_ref`
- `sealed_at`
- `revoked_at`
- `superseded_by_seal_id`
- `required_signers`
- `completed_signoffs`
- `approved_required_signoffs`
- `required_signoffs`
- `signoffs`
- `seal_envelope`
- `verification_summary`
- `created_at`
- `updated_at`

### App Router canônico do frontend

Rotas autenticadas relevantes:

- `POST /api/app/evidence/manual-package`
- `GET /api/app/evidence/manual-package/seal?package_sha256=...&policy_version=...`
- `POST /api/app/evidence/manual-package/signoff-requests`
- `POST /api/app/evidence/manual-package/seals/{sealId}/signoffs`
- `POST /api/app/evidence/manual-package/seals/{sealId}/finalize`
- `POST /api/app/evidence/manual-package/seals/{sealId}/revoke`
- `POST /api/app/evidence/manual-package/seals/{sealId}/supersede`

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

### `POST /api/v1/monitoring/estimate`

Uso:

- gerar quote operacional para iniciar uma watchlist/case de monitoring

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- persiste `authorization_denied` com `detail=monitoring_operational_role_required` para roles fora desse recorte

### `POST /api/v1/monitoring/start`

Uso:

- consumir um `quote` válido e abrir o case/watchlist operacional de monitoring

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- persiste `authorization_denied` com `detail=monitoring_operational_role_required` para roles fora desse recorte

### `GET /api/v1/monitoring/watchlists`

Uso:

- listar watchlists da organização autenticada no cockpit de monitoring

Controles atuais:

- exige leitura compatível `ADMIN|ANALYST|AUDITOR|VIEWER|TESTER` e aliases legados `OTK_ANALYST|OTK_VIEWER|OTK_TESTER`
- persiste `authorization_denied` com `detail=monitoring_read_role_required` para roles fora desse recorte

### `GET /api/v1/monitoring/watchlists/{watchlist_id}/items`

Uso:

- listar os itens monitorados da watchlist selecionada

Controles atuais:

- exige o mesmo recorte de leitura do core de monitoring
- persiste `authorization_denied` com `detail=monitoring_read_role_required` para roles fora desse recorte

### `GET /api/v1/monitoring/alerts`

Uso:

- listar alertas do core de monitoring filtrados por `watchlist_id`

Controles atuais:

- exige o mesmo recorte de leitura do core de monitoring
- persiste `authorization_denied` com `detail=monitoring_read_role_required` para roles fora desse recorte

### `POST /api/v1/monitoring/watchlists`

Uso:

- criar watchlist operacional manual fora do fluxo `estimate -> start`

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- persiste `authorization_denied` com `detail=monitoring_operational_role_required` para roles fora desse recorte

### `POST /api/v1/monitoring/watchlists/{watchlist_id}/items`

Uso:

- adicionar manualmente um item monitorado a uma watchlist existente

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- persiste `authorization_denied` com `detail=monitoring_operational_role_required` para roles fora desse recorte

### `GET /api/v1/monitoring/admin/operational-alerts`

Uso:

- listar incidentes operacionais globais com `status`, `triage_status`, `service`, `receiver`, `severity`, `cursor` e `limit`

### `POST /api/v1/monitoring/admin/operational-alerts/export`

Uso:

- exportar backlog global em `csv|json`
- gera `operational_alerts_exported` em `audit_logs`

Comportamento atual:

- quando existir `work-item` rastreado para `resource_type=operational_alert` na organizacao atual, o export inclui colunas/campos `work_item_*`
- o mesmo export propaga o resumo leve de RCA via `rca_*`, incluindo dominio, contencao, commander, dominios afetados, impacto, causa suspeita/confirmada, acoes corretivas e referencias de evidencia
- no formato `csv`, os campos de lista (`affected_domains`, `corrective_actions`, `evidence_refs`) saem serializados como JSON em colunas `*_json`
- a ausencia de `work-item` nao bloqueia o export; os campos `work_item_*` e `rca_*` permanecem `null` ou listas vazias

### `POST /api/v1/monitoring/test/trigger-alert`

Uso:

- disparar um alerta sintetico ligado a uma `watchlist` existente para validacao/QA do cockpit de monitoring

Controles atuais:

- endpoint disponivel apenas quando `enable_test_endpoints=true`
- exige `X-Role` efetivo dentro de `ADMIN|TESTER|OTK_TESTER`
- persiste `authorization_denied` quando uma role fora desse recorte tenta operar o endpoint

## Investigation API

### `POST /api/v1/investigation/estimate`

Uso:

- gerar quote operacional para abertura de investigação

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- integrações server-to-server continuam no trilho de `API Key`

### `POST /api/v1/investigation/start`

Uso:

- consumir quote válido e abrir o case operacional de investigação

Controles atuais:

- exige papel humano operacional `ADMIN|ANALYST|OTK_ANALYST`
- integrações server-to-server continuam no trilho de `API Key`

### `POST /api/v1/investigation/{case_id}/internal/complete`

Uso:

- endpoint interno usado pelo `investigation-worker` para finalizar casos e consolidar cobrança/ledger

Controles atuais:

- exige `X-Internal-Token` (segredo interno compartilhado entre worker e API)
- o segredo é configurado via `INVESTIGATION_INTERNAL_WORKER_TOKEN`

### `POST /api/v1/investigation/{case_id}/internal/fail`

Uso:

- endpoint interno usado pelo `investigation-worker` para marcar caso como falho e efetuar refund/ledger

Controles atuais:

- exige `X-Internal-Token` (segredo interno compartilhado entre worker e API)
- o segredo é configurado via `INVESTIGATION_INTERNAL_WORKER_TOKEN`

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
- a camada frontend passa a tratar `metadata.workspace_status` como chave canonica de status de workspace
- aliases legados como `metadata.local_workspace_status`, `metadata.local_block_status`, `metadata.local_case_id` e `metadata.ros_status` seguem aceitos na leitura durante a migracao incremental
- `owner_label` continua como contexto humano de handoff; `owner_user_id` permanece como identificador tecnico de assignment quando disponivel
- o backend agora valida o par canonico `module + resource_type` e retorna `422 invalid_module_resource_type_pair` quando houver combinacao invalida
- o backend normaliza aliases canonicos de `metadata` na escrita (`workspace_status`, `case_id`, `owner_user_id`, `note`) sem bloquear campos extras de compatibilidade
- o backend valida tipos dos campos conhecidos de `metadata` e retorna `422 invalid_work_item_metadata` quando houver shape claramente invalido
- o frontend deve preferir helpers compartilhados para convergencia incremental do contrato: `withCanonicalWorkItemMetadata(...)` na escrita, `resolveWorkItemOwnerDisplay(...)` para ownership legivel e `resolveWorkItemWorkspaceStatus(...)` para leitura resiliente de status
- a fila operacional compartilhada ja utiliza esse padrao nos cockpits `alerts`, `evidence`, `ros-coaf`, `blocks`, `sanctions`, `reports` e `counterparties`, reduzindo drift entre leitura e persistencia de `metadata`

Politica canonica atual de aliases:

- campos canonicos de transporte e persistencia: `case_id`, `workspace_status`, `owner_user_id`, `note`
- aliases tolerados durante a migracao: `local_case_id`, `local_workspace_status`, `local_block_status`, `ros_status`
- na escrita, o backend promove aliases tolerados para o campo canonico correspondente quando este nao vier preenchido
- para compatibilidade de leitura, o backend reemite aliases por `resource_type` quando necessario:
  - `sanctions_screening` e `preventive_block`: mantem `local_case_id` sincronizado com `case_id`
  - `sanctions_screening`, `formal_report_case`, `counterparty`, `evidence_event` e `preventive_block`: mantem `local_workspace_status` sincronizado com `workspace_status`
  - `preventive_block`: mantem `local_block_status` sincronizado com `workspace_status`
  - `ros_record`: mantem `ros_status` sincronizado com `workspace_status`

Campos canonizados por `resource_type` nesta rodada `P1-01`:

- `operational_alert`: alem dos campos base de alerta (`alertname`, `receiver`, `service`, `severity`, `fingerprint`, `triage_*`), aceita o bloco leve de RCA (`domain`, `affected_domains`, `incident_commander`, `containment_status`, `runbook_ref`, `impact_summary`, `suspected_root_cause`, `confirmed_root_cause`, `corrective_actions`, `evidence_refs`)
- `evidence_event`: alem de `event_id`, `audit_*`, `request_id`, `report_id` e `file_hash_sha256`, aceita o contexto de revisao manual (`provider`, `provider_status`, `degraded_reason`, `capability_status`, `delivery_mode`, `origin_analysis_status`, `requires_human_review`, `counterparty_context_present`, `counterparty_context`, `purpose`, `amount`, `manual_review_action`, `package_sha256`, `filename`)
- `ros_record`: mantem compatibilidade com `ros_status` e adiciona `ros_phase`, `approval_2fa_verified` e `rejection_reason` como extensoes canonicas do workspace operacional

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
- `/blocks`, `/reports`, `/evidence`, `/counterparties` e `/ros-coaf` agora compartilham a mesma base tipada de transporte de `work-items`, reduzindo drift de `metadata`

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
