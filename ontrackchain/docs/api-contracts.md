# Contratos de API

## Convencoes Gerais

- Base local: `http://localhost:8080`
- Autenticacao protegida por gateway/`ForwardAuth`
- Formas de autenticacao aceitas:
  - `Authorization: Bearer <jwt>`
  - `X-API-Key: <api_key>`
- Headers de contexto propagados pelo gateway:
  - `X-Org-Id`
  - `X-User-Id`
  - `X-Plan`
  - `X-Role`
  - `X-Auth-Method`
- Correlacao:
  - `X-Request-Id` e recomendado em fluxos criticos
- Internacionalizacao de erros:
  - os contratos HTTP devem preferir `error codes` estaveis e neutros em idioma, como `not_authenticated` e `invalid_claims`
  - a traducao para `pt-BR`, `en` e `es` deve ocorrer na camada de UI, preservando compatibilidade entre ambientes e integracoes

## Auth Service

### `GET /health`

- Uso: health check

### `GET /validate`

- Uso: endpoint interno do `ForwardAuth`
- Retorna headers de contexto no response

### `GET /auth/config`

- Uso: expor o modo atual de autenticacao para o frontend em runtime
- Response em `dev`:

```json
{
  "auth_mode": "dev",
  "effective_auth_mode": "dev",
  "app_env": "local",
  "dev_auth_enabled": true,
  "mfa": {
    "enabled": true,
    "method": "totp",
    "issuer": "OnTrackChain",
    "account_name": "local-admin@ontrackchain",
    "period_seconds": 30,
    "digits": 6
  },
  "oidc": {
    "enabled": false,
    "issuer_url": null,
    "client_id": null,
    "audience": null,
    "authorization_url": null
  }
}
```

- Response em `oidc`:

```json
{
  "auth_mode": "oidc",
  "effective_auth_mode": "oidc",
  "app_env": "staging",
  "dev_auth_enabled": false,
  "mfa": {
    "enabled": true,
    "method": "totp",
    "issuer": "OnTrackChain",
    "account_name": "local-admin@ontrackchain",
    "period_seconds": 30,
    "digits": 6
  },
  "oidc": {
    "enabled": true,
    "provider": "keycloak",
    "issuer_url": "https://issuer.example.com",
    "client_id": "ontrackchain-web",
    "audience": "ontrackchain-web",
    "authorization_url": "https://issuer.example.com/oauth2/authorize",
    "claims": {
      "org": "org_id",
      "plan": "plan",
      "role": "role"
    }
  }
}
```

- `provider` suporta presets concretos:
  - `generic`
  - `keycloak`
  - `auth0`
  - `entra`
- `effective_auth_mode` reflete o modo realmente aceito pelo backend
- quando `AUTH_MODE=dev`, mas `DEV_AUTH_ENABLED=false` ou `APP_ENV` estiver fora de `local|test`, o backend expõe `effective_auth_mode=oidc` e o login dev deve ser tratado como bloqueado
- em `effective_auth_mode=dev`, `mfa` expõe metadados do `TOTP` local do scaffold; o segredo compartilhado permanece em variavel de ambiente do `auth-service`
- em `effective_auth_mode=oidc`, `mfa.method=external_provider`, `mfa.managed_by=oidc_provider` e `mfa.provider_homologated=false` deixam explicito que o segundo fator do provedor ainda nao vale como prova homologada para downloads sensiveis

### `POST /auth/issue-dev-token`

- Uso: emissao de JWT de desenvolvimento
- Disponivel apenas quando `AUTH_MODE=dev` e `DEV_AUTH_ENABLED=true`
- Request:

```json
{
  "org_id": "00000000-0000-0000-0000-000000000001",
  "user_id": "00000000-0000-0000-0000-000000000002",
  "plan": "enterprise",
  "role": "ADMIN",
  "expires_in_minutes": 60
}
```

- Response:

```json
{
  "token": "<jwt>",
  "expires_at": "2026-06-26T12:00:00+00:00"
}
```

### `POST /auth/verify-2fa`

- Uso: validar codigo TOTP real para fluxos JWT do scaffold
- Requer:
  - `Authorization: Bearer <jwt>`
- Request:

```json
{
  "code": "123456"
}
```

- Response `200`:

```json
{
  "status": "ok",
  "method": "totp",
  "verified_at": "2026-06-26T12:05:00+00:00"
}
```

- Erros:
  - `401 invalid_2fa`
  - `403 2fa_requires_jwt_auth`

### `POST /api/session/verify-2fa` em `frontend`

- Uso: proxy do `2FA` local baseado em `TOTP` para sessoes `JWT` do scaffold
- Comportamento:
  - exige cookie `otc_token`
  - encaminha o `Bearer` ao `auth-service`
  - em sucesso, grava cookie `otc_2fa=ok`
  - em `effective_auth_mode=oidc`, bloqueia o fluxo local e responde erro explicito
- Erros relevantes:
  - `401 not_authenticated`
  - `400 oidc_2fa_managed_externally`
  - repassa `401 invalid_2fa` quando o `auth-service` rejeita o codigo

Observacao operacional:

- `oidc_2fa_managed_externally` significa que a sessao atual depende do MFA do provedor corporativo, e nao do `TOTP` local do scaffold
- o cookie `otc_2fa=managed_externally` indica apenas que a sessao veio de `OIDC`; nao equivale a prova homologada de MFA forte para `legal_report`

## Investigation API

### `GET /api/v1/report-types`

- Uso: catalogo de tipos de relatorio filtrado por plano

### `GET /api/v1/report-types/{type_identifier}`

- Uso: detalhe de um tipo de relatorio

### `POST /api/v1/investigation/estimate`

- Uso: calcular quote de investigacao
- Request:

```json
{
  "address": "0x1111111111111111111111111111111111111111",
  "chains": ["ethereum"],
  "depth": 3,
  "report_type": "technical_basic",
  "addons": []
}
```

- Response relevante:

```json
{
  "quote_id": "uuid",
  "expires_at": "2026-06-26T12:00:00+00:00",
  "report_type_requested": "technical_basic",
  "report_type_canonical": "technical_basic",
  "total_credits": 2.7,
  "plan": "professional",
  "depth_requested": 3,
  "depth_applied": 3,
  "warnings": []
}
```

### `POST /api/v1/investigation/start`

- Uso: iniciar uma investigation a partir de quote confirmado
- Request:

```json
{
  "quote_id": "uuid",
  "confirmed": true
}
```

- Response `200`:

```json
{
  "case_id": "uuid",
  "status": "processing",
  "estimated_time_seconds": 120,
  "concurrency_limited": false
}
```

- Response `202` quando limitado por concorrencia:

```json
{
  "case_id": "uuid",
  "status": "queued",
  "estimated_time_seconds": 120,
  "position_in_queue": 1,
  "concurrency_limited": true
}
```

### `GET /api/v1/investigation/{case_id}/status`

- Uso: status resumido da investigation

### `GET /api/v1/investigation/{case_id}/result`

- Uso: resultado final resumido
- Response relevante:

```json
{
  "case_id": "uuid",
  "status": "completed",
  "risk_score": 79,
  "risk_level": "high",
  "patterns_detected": ["cluster_overlap"],
  "kyw_summary": {
    "chain": "ethereum",
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "analysis_version": "rpc_provider_v1",
    "rpc": {
      "provider": "evm_rpc",
      "provider_status": "live",
      "rpc_source": "provider_primary",
      "latest_block_number": 21307194,
      "balance_wei": 1000000000000000000,
      "latency_ms": 0,
      "retries_used": 0,
      "degraded_reason": null
    }
  }
}
```

### `GET /api/v1/investigation/admin/operations`

- Uso: snapshot operacional do `investigation-worker`
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 privileged_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint
- Response relevante:

```json
{
  "queue": {
    "ready": 0,
    "waiting": 1,
    "retry_pending": 0,
    "retry_due": 0,
    "wake_signals": 2
  },
  "concurrency": {
    "org_active": 1,
    "org_limit": 2,
    "global_active": 3,
    "global_limit": 10,
    "plan": "professional"
  },
  "throughput": {
    "completed_last_hour": 5,
    "failed_last_hour": 0,
    "billing_recalc_last_hour": 0,
    "avg_duration_ms_last_20": 2005.0
  },
  "states": {
    "queued": 1,
    "processing": 1
  },
  "recent_cases": [
    {
      "case_id": "uuid",
      "status": "completed",
      "queue_state": "completed",
      "attempt_count": 0,
      "duration_ms": 2011
    }
  ],
  "generated_at": "2026-06-26T12:00:00+00:00"
}
```

### `GET /api/v1/investigation/admin/dlq`

- Uso: listar `cases` de `investigation` em falha permanente (`DLQ`)
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 privileged_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint
- Query params suportados:
  - `state=failed_permanent|acknowledged|discarded|resolved|all`
  - `target_chain=<chain>`
  - `can_requeue=true|false`
  - `limit=1..100`

### `POST /api/v1/investigation/admin/dlq/{case_id}/requeue`

- Uso: reenfileirar manualmente um `case` falho
- Restricoes:
  - exige `X-Role=ADMIN`
  - exige creditos disponiveis para um novo `PRE_HOLD`
  - respeita limite atual de concorrencia e disponibilidade do `report_type` no plano atual
- Negacao RBAC:
  - `403 admin_required`
  - registra `authorization_denied` com `resource_type=case`, `resource_id=<case_id>` e `request_id`

### `POST /api/v1/investigation/admin/dlq/{case_id}/acknowledge`

- Uso: resolver operacionalmente um item da DLQ sem reenfileirar
- Body:

```json
{
  "action": "acknowledged",
  "note": "ack_from_monitoring_ui"
}
```

- Acoes suportadas:
  - `acknowledged`
  - `discarded`

### `GET /api/v1/investigation/admin/alerts`

- Uso: retornar alertas operacionais avaliados a partir do estado do worker e da DLQ
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 privileged_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint

### `GET /api/v1/investigation/admin/metrics`

- Uso: expor métricas operacionais em formato Prometheus text exposition
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 privileged_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint

### `GET /internal/metrics/prometheus`

- Uso: expor métricas agregadas de `investigation` para scraping central do `Prometheus`
- Escopo:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - nao retorna dados por organizacao nem detalhes de `cases`
- Metricas relevantes:
  - `ontrack_investigation_platform_queue_*`
  - `ontrack_investigation_platform_states_*`
  - `ontrack_investigation_platform_concurrency_*`
  - `ontrack_investigation_platform_provider_*`
  - `ontrack_investigation_platform_operational_alert_status{code=...}`

### `GET /internal/rpc-readiness` em `investigation-api`

- Uso: expor readiness/configuracao do provider RPC para `staging tecnico`
- Escopo:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - nao executa chamada externa ao provider
  - distingue provider suportado, habilitado, configurado e pronto
  - expõe `details.operating_mode` para diferenciar `live`, `fallback_only`, `disabled` e `misconfigured`
- Response relevante:

```json
{
  "provider": "evm_rpc",
  "provider_supported": true,
  "enabled": true,
  "configured": true,
  "ready": true,
  "degraded_reason": null,
  "details": {
    "operating_mode": "fallback_only",
    "primary_url_configured": false,
    "fallback_url_configured": true,
    "timeout_ms": 1500,
    "max_retries": 1
  }
}
```

### `GET /internal/metrics/prometheus` em `monitoring-api`

- Uso: expor métricas agregadas de `monitoring` para scraping central do `Prometheus`
- Escopo:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - nao retorna watchlists, quotes ou alertas por organizacao
- Metricas relevantes:
  - `ontrack_monitoring_platform_watchlists_*`
  - `ontrack_monitoring_platform_watchlist_items_*`
  - `ontrack_monitoring_platform_alerts_*`
  - `ontrack_monitoring_platform_quotes_*`
  - `ontrack_monitoring_platform_operational_alert_status{code=...}`

### `GET /internal/metrics/prometheus` em `compliance-api`

- Uso: expor métricas agregadas de `compliance` para scraping central do `Prometheus`
- Escopo:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - nao retorna quotes, casos ou reports por organizacao
- Metricas relevantes:
  - `ontrack_compliance_platform_quotes_*`
  - `ontrack_compliance_platform_cases_*`
  - `ontrack_compliance_platform_reports_*`
  - `ontrack_compliance_platform_risk_checks_*`
  - `ontrack_compliance_platform_provider_*`
  - `ontrack_compliance_platform_operational_alert_status{code=...}`

### `GET /internal/provider-readiness` em `compliance-api`

- Uso: expor readiness/configuracao do provider AML/KYT para `staging tecnico`
- Escopo:
  - nao e endpoint publico
  - nao executa chamada externa ao provider
  - serve para distinguir provider suportado, habilitado, configurado e pronto
  - expõe `details.operating_mode` para diferenciar `live`, `disabled` e `misconfigured`
- Response exemplo:

```json
{
  "provider": "trm_labs",
  "provider_supported": true,
  "enabled": false,
  "configured": false,
  "ready": false,
  "degraded_reason": "provider_disabled",
  "details": {
    "operating_mode": "disabled",
    "screening_url_configured": false,
    "api_key_configured": false,
    "api_key_header": "Authorization",
    "api_key_prefix_configured": true,
    "timeout_ms": 1500,
    "max_retries": 1
  }
}
```

### `GET /internal/metrics/prometheus` em `report-api`

- Uso: expor métricas agregadas de `report` para scraping central do `Prometheus`
- Escopo:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - nao retorna downloads ou relatórios por organizacao
- Metricas relevantes:
  - `ontrack_report_platform_reports_*`
  - `ontrack_report_platform_downloads_*`
  - `ontrack_report_platform_orgs_with_downloads_last_24h_total`
  - `ontrack_report_platform_operational_alert_status{code=...}`

### `POST /internal/ops/alertmanager/webhook` em `monitoring-api`

- Uso: receiver interno do `Alertmanager` para persistir incidentes operacionais globais
- Restricao:
  - nao e endpoint publico
  - nao passa pelo `Traefik`
  - exige `Authorization: Bearer <token interno>`
- Request body relevante:

```json
{
  "receiver": "monitoring-webhook",
  "status": "firing",
  "groupKey": "{}:{alertname=\"OntrackPlatformWatchdog\"}",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "OntrackPlatformWatchdog",
        "severity": "info",
        "service": "platform"
      },
      "annotations": {
        "summary": "Watchdog da plataforma ativo"
      },
      "startsAt": "2026-06-26T18:00:00Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph",
      "fingerprint": "abc123"
    }
  ]
}
```

### `GET /api/v1/monitoring/admin/operational-alerts`

- Uso: listar incidentes operacionais globais recebidos do `Alertmanager`
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 monitoring_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint
- Query params:
  - `status`
  - `triage_status`
  - `service`
  - `receiver`
  - `severity`
  - `cursor`
  - `limit`
- Response relevante:

```json
{
  "status_filter": "firing",
  "triage_status_filter": "pending",
  "service_filter": "platform",
  "receiver_filter": "monitoring-webhook",
  "severity_filter": "warning",
  "cursor": null,
  "limit": 20,
  "total_count": 37,
  "count": 1,
  "has_more": false,
  "next_cursor": null,
  "data": [
    {
      "id": "uuid",
      "receiver": "monitoring-webhook",
      "status": "firing",
      "triage_status": "pending",
      "alertname": "OntrackPlatformWatchdog",
      "service": "platform",
      "severity": "info",
      "fingerprint": "abc123",
      "delivery_count": 3,
      "triaged_at": null,
      "triaged_by": null,
      "triage_note": null
    }
  ]
}
```

- `total_count` representa o total de incidentes que correspondem aos filtros ativos, independentemente da pagina atual do cursor.
- `severity` aceita os niveis operacionais atualmente emitidos pelas regras locais, como `info`, `warning` e `critical`.
- `receiver` permite separar a origem de entrega dos incidentes, como `monitoring-webhook` e `monitoring-test`.

### `GET /api/v1/monitoring/admin/operational-alerts/filter-options`

- Uso: listar valores distintos de `service` e `receiver` para popular filtros administrativos dinamicos na UI
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 monitoring_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint
- Response relevante:

```json
{
  "services": ["platform", "report-api", "dynamic-service-123"],
  "receivers": ["monitoring-webhook", "monitoring-test", "dynamic-receiver-123"],
  "generated_at": "2026-06-26T20:45:00+00:00"
}
```

- Comportamento:
  - retorna apenas valores nao nulos e nao vazios
  - ordena `services` e `receivers` alfabeticamente
  - serve como catalogo dinamico para os selects da UI `/monitoring`

### `POST /api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge`

- Uso: reconhecer manualmente um incidente global sem alterar o `status` tecnico do alerta
- Restricao:
  - exige `X-Role=ADMIN`
- Negacao RBAC:
  - `403 admin_role_required`
  - registra `authorization_denied` com `resource_type=operational_alerts`, `resource_id=<event_id>` e `request_id`
- Body:

```json
{
  "note": "ack_from_monitoring_ui",
  "triaged_by": "admin_ui"
}
```

- Response relevante:

```json
{
  "id": "uuid",
  "status": "firing",
  "triage_status": "acknowledged",
  "triaged_at": "2026-06-26T18:05:00+00:00",
  "triaged_by": "admin_ui",
  "triage_note": "ack_from_monitoring_ui"
}
```

### `POST /api/v1/monitoring/admin/operational-alerts/acknowledge-batch`

- Uso: reconhecer em lote todos os incidentes pendentes que correspondem ao recorte administrativo atual
- Restricao:
  - exige `X-Role=ADMIN`
- Negacao RBAC:
  - `403 admin_role_required`
  - registra `authorization_denied` com `resource_type=operational_alerts` e `request_id`
- Body:

```json
{
  "ids": ["uuid-1", "uuid-2"],
  "status": "firing",
  "triage_status": "pending",
  "service": "report-api",
  "receiver": "monitoring-webhook",
  "severity": "critical",
  "note": "ack_batch_from_monitoring_ui",
  "triaged_by": "admin_ui"
}
```

- Response relevante:

```json
{
  "updated_count": 2,
  "selected_count": 2,
  "status_filter": "firing",
  "triage_status_filter": "pending",
  "service_filter": "report-api",
  "receiver_filter": "monitoring-webhook",
  "severity_filter": "critical",
  "triage_status": "acknowledged"
}
```

- Comportamento:
  - atualiza apenas incidentes com `triage_status='pending'`
  - quando `ids` e enviado, restringe o lote aos incidentes explicitamente selecionados
  - respeita os filtros opcionais enviados no body
  - a UI pode acumular `ids` em multiplas paginas do mesmo recorte antes de enviar o lote
  - a UI persiste recorte e selecao acumulada em `sessionStorage` da aba atual para sobreviver a refresh da pagina
  - a UI tambem pode restaurar `cursor` e historico da paginação do mesmo recorte apos refresh

### `POST /api/v1/monitoring/admin/operational-alerts/export`

- Uso: exportar incidentes globais administrativos em `csv` ou `json`
- Restricao:
  - exige `X-Role=ADMIN`
- Negacao RBAC:
  - `403 admin_role_required`
  - registra `authorization_denied` com `resource_type=operational_alerts` e `request_id`
- Body:

```json
{
  "format": "csv",
  "scope": "filtered",
  "ids": [],
  "status": "firing",
  "triage_status": "pending",
  "service": "report-api",
  "receiver": "monitoring-webhook",
  "severity": "critical"
}
```

- Regras:
  - `format` aceita `csv|json`
  - `scope` aceita `filtered|selected`
  - `selected` exige `ids` nao vazio
  - reaplica os mesmos filtros administrativos do backlog
- Response:
  - `200 OK`
  - `content-disposition: attachment; filename="operational-alerts-<scope>-<timestamp>.<ext>"`
  - `content-type: text/csv` ou `application/json`
- Comportamento:
  - `filtered` exporta todo o recorte administrativo atual
  - `selected` exporta apenas os `ids` explicitamente escolhidos
  - `json` inclui metadados de geracao, filtros aplicados e `data`
  - `csv` inclui colunas operacionais, resumo/descricao e `labels/annotations` serializados
  - o backend exige contexto de organizacao valido para registrar a trilha auditavel do export
- Auditoria:
  - gera `operational_alerts_exported` quando ha contexto de organizacao
  - propaga `request_id` em `metadata.request_id`
  - registra `format`, `scope`, `selected_count`, `exported_count` e `filters`

### `POST /api/v1/monitoring/test/trigger-operational-alert`

- Uso: criar incidente sintetico deterministico para validacao de triagem operacional
- Observacao:
  - endpoint de teste, disponivel apenas quando `enable_test_endpoints=true`
- Body:

```json
{
  "alertname": "SyntheticPlatformAck-123",
  "service": "platform",
  "receiver": "monitoring-webhook",
  "severity": "warning",
  "summary": "Incidente sintetico para triagem",
  "description": "Fluxo de reconhecimento manual via UI"
}
```

### `GET /api/app/monitoring/operational-alerts` em `frontend`

- Uso: proxy autenticado para a UI administrativa `/monitoring`
- Comportamento:
  - exige cookie `otc_token`
  - valida o token diretamente no `auth-service` (`/validate`) para obter `X-Org-Id`, `X-User-Id` e a role efetiva da sessao
  - encaminha `X-Role` real da sessao (`ADMIN|AUDITOR|ANALYST`)
  - propaga `X-Org-Id`, `X-User-Id` e `X-Request-Id` para permitir negacao auditada no backend
  - repassa `status`, `triage_status`, `service`, `receiver`, `severity`, `cursor` e `limit`

### `POST /api/app/monitoring/operational-alerts/export` em `frontend`

- Uso: proxy autenticado do export administrativo dos incidentes globais
- Comportamento:
  - exige cookie `otc_token`
  - valida o token diretamente no `auth-service` (`/validate`) para obter `X-Org-Id`, `X-User-Id` e a role efetiva
  - usa `INTERNAL_AUTH_BASE_URL` quando configurado; no compose local o fallback e `http://auth-service:9000`
  - encaminha `X-Role` real da sessao
  - propaga `X-Request-Id`
  - preserva `content-type` e `content-disposition` do arquivo retornado

### `GET /api/app/audit/logs` em `frontend`

- Uso: proxy autenticado para a tela administrativa `/audit`
- Comportamento:
  - exige cookie `otc_token`
  - propaga `X-Request-Id`
  - encaminha os filtros `request_id`, `action`, `resource_type`, `report_id`, `resource_id` e `limit`
  - preserva a restricao de leitura privilegiada (`ADMIN|AUDITOR`) do backend

### `POST /api/v1/audit/evidence-export`

- Uso: exportar bundle auditado e filtravel de evidencias multi-dominio
- Roles permitidas: `ADMIN|AUDITOR`
- Body:

```json
{
  "format": "json",
  "request_id": "req_export_bundle_1",
  "action": "case_started",
  "resource_type": "case",
  "report_id": null,
  "resource_id": "11111111-1111-1111-1111-111111111111",
  "limit": 200,
  "include_audit_logs": true,
  "include_credit_ledger": true,
  "include_reports": true
}
```

- Response:
  - `application/json`
  - `content-disposition: attachment; filename="ontrackchain-evidence-bundle-<timestamp>.json"`
- Payload:
  - `generated_at`
  - `filters`
  - `sections.audit_logs.{included,count,data}`
  - `sections.credit_ledger.{included,count,data}`
  - `sections.reports.{included,count,data}`
- Auditoria:
  - gera `evidence_bundle_exported`
  - preserva `metadata.request_id`
  - registra filtros, formato e contagem por secao

### `POST /api/app/audit/evidence-export` em `frontend`

- Uso: proxy autenticado do export multi-dominio da tela `/audit`
- Comportamento:
  - exige cookie `otc_token`
  - valida o token via `auth-service` (`/validate`)
  - encaminha `X-Role`, `X-Org-Id`, `X-User-Id`, `X-Linked-User-Id` e `X-Request-Id`
  - preserva `content-type` e `content-disposition` do bundle retornado

### `GET /api/app/monitoring/operational-alert-filter-options` em `frontend`

- Uso: proxy autenticado do catalogo dinamico de `service` e `receiver`
- Comportamento:
  - exige cookie `otc_token`
  - valida o token diretamente no `auth-service` (`/validate`) para obter `X-Org-Id`, `X-User-Id` e a role efetiva da sessao
  - encaminha `X-Role` real da sessao
  - propaga `X-Org-Id`, `X-User-Id` e `X-Request-Id`
  - retorna as opcoes dinamicas usadas pelos selects da UI `/monitoring`

### `POST /api/app/monitoring/operational-alerts/{eventId}/acknowledge` em `frontend`

- Uso: proxy autenticado para a acao de triagem manual na UI `/monitoring`
- Comportamento:
  - exige cookie `otc_token`
  - valida o token diretamente no `auth-service` (`/validate`) para obter `X-Org-Id`, `X-User-Id` e a role efetiva da sessao
  - encaminha `X-Role` real da sessao
  - propaga `X-Org-Id`, `X-User-Id` e `X-Request-Id`
  - repassa o body com `note` e `triaged_by`

### `GET /api/v1/investigation/history`

- Uso: historico de cases

### `GET /api/v1/billing/balance`

- Uso: saldo de creditos da organizacao
- Response:

```json
{
  "credits_available": 100.0,
  "credits_reserved": 2.7,
  "credits_used_total": 20.4
}
```

### `GET /api/v1/audit/logs`

- Uso: listagem de auditoria
- Restricao:
  - exige `X-Role in {ADMIN, AUDITOR}`
- Negacao:
  - `403 privileged_read_role_required`
  - registra `authorization_denied` com `request_id`, `effective_role` e endpoint
- Query params:
  - `page`
  - `request_id`
  - `action`
  - `resource_type`
  - `report_id`
  - `resource_id`
  - `limit`
- Response relevante:

```json
{
  "data": [
    {
      "id": "uuid",
      "action": "report_generated",
      "resource_type": "case",
      "resource_id": "uuid",
      "request_id": "req-123",
      "report_id": "96a237996b3a9c8b",
      "file_hash_sha256": "sha256",
      "metadata": {
        "request_id": "req-123",
        "report_id": "96a237996b3a9c8b"
      },
      "created_at": "2026-06-26T12:00:00+00:00"
    }
  ],
  "page": 2,
  "count": 1,
  "limit": 50,
  "total": 73,
  "total_pages": 2,
  "has_more": false,
  "filters": {
    "action": "report_generated",
    "resource_type": "case",
    "request_id": "req-123",
    "report_id": "96a237996b3a9c8b",
    "resource_id": null
  }
}
```

### `POST /api/v1/investigation/{case_id}/internal/complete`

- Uso: finalizacao interna do case
- Fluxo de billing:
  - confirma custo
  - ou marca `billing_recalc_required`

### `POST /api/v1/investigation/{case_id}/internal/fail`

- Uso: falha interna com `REFUND`

### `DELETE /api/v1/investigation/{case_id}`

- Uso: remocao de case

## Compliance API

### `GET /api/v1/compliance/operations`

- Uso: catalogo de operacoes de compliance
- Comportamento:
  - combina disponibilidade comercial (`available`, `min_plan`) com capacidade operacional real por operacao
  - expõe `provider`, `provider_status`, `degraded_reason`, `capability_status`, `delivery_mode` e `capability_details`
  - evita que clientes precisem consultar `provider-readiness` separadamente para montar UX basica de homologacao
- Response exemplo:

```json
{
  "plan": "starter",
  "total": 4,
  "generated_at": "2026-06-28T12:00:00+00:00",
  "operations": [
    {
      "canonical": "kyc_wallet",
      "label": "KYC Wallet",
      "description": "Screening AML/KYT instantaneo de carteira",
      "cost_credits": 1,
      "available": true,
      "upgrade_required": null,
      "min_plan": "starter",
      "aliases_accepted": ["kyc", "wallet_kyc"],
      "deprecated_aliases": [],
      "chains_supported": ["ethereum", "polygon", "arbitrum", "base", "stellar"],
      "avg_duration_seconds": 45,
      "output_format": "json",
      "regulatory_reference": "AML/KYT",
      "tags": ["aml", "kyt", "wallet"],
      "provider": "trm_labs",
      "provider_status": "degraded",
      "degraded_reason": "provider_not_configured",
      "capability_status": "degraded",
      "delivery_mode": "risk_check_instant",
      "capability_details": {
        "operating_mode": "misconfigured",
        "screening_url_configured": false,
        "api_key_configured": false
      }
    }
  ],
  "note_deprecated": "aliases legados podem ser removidos em futuras versoes"
}
```

### `GET /api/v1/compliance/operations/{operation_identifier}`

- Uso: detalhe de operacao
- Comportamento:
  - retorna os mesmos campos comerciais e operacionais do catalogo
  - resolve aliases como `dd`, `sof` e `kyc`

### `POST /api/v1/compliance/estimate`

- Uso: cotacao de screening/compliance
- Request:

```json
{
  "address": "0x1111111111111111111111111111111111111111",
  "chain": "ethereum",
  "operation": "dd"
}
```

### `POST /api/v1/compliance/start`

- Uso: iniciar case de compliance
- Request:

```json
{
  "quote_id": "uuid",
  "confirmed": true
}
```

### `POST /api/v1/compliance/cases/{case_id}/report`

- Uso: gerar relatorio de compliance
- Request:

```json
{
  "report_type": "compliance_aml",
  "include_onchain_hash": true
}
```

- Response relevante:

```json
{
  "case_id": "uuid",
  "report_id": "96a237996b3a9c8b",
  "report_type_requested": "compliance_aml",
  "report_type_canonical": "compliance_aml",
  "created_at": "2026-06-26T12:00:00+00:00",
  "file_hash_sha256": "sha256",
  "onchain_hash": "pending",
  "content_type": "application/pdf"
}
```

### `POST /api/v1/compliance/kyc-wallet`

- Uso: screening direto de wallet com o mesmo provider/router do `risk-check`
- Comportamento:
  - usa o provider AML/KYT configurado e nunca inventa score quando o provider estiver degradado
  - retorna `provider`, `provider_status`, `degraded_reason` e `capability_status`
  - deriva `recommendation` apenas quando houver `risk_score` real em modo `live`
  - registra `compliance_kyc_wallet_checked` quando houver contexto organizacional
- Response:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "trm_labs",
  "provider_status": "degraded",
  "degraded_reason": "provider_not_configured",
  "capability_status": "degraded",
  "risk_score": null,
  "aml_flags": [],
  "recommendation": null,
  "report_id": null,
  "checked_at": "2026-06-28T12:00:00+00:00"
}
```

### `POST /api/v1/compliance/risk-check`

- Uso: risk check com provider primario configuravel, hoje com roteador explicito suportando `TRM Labs`
- Comportamento:
  - quando `COMPLIANCE_TRM_ENABLED=false` ou faltarem credenciais/URL, responde em modo `degraded`
  - quando `COMPLIANCE_RISK_PROVIDER` apontar para provider nao suportado, responde em modo `degraded` com `provider_unsupported`
  - nao inventa score quando o provider nao esta disponivel ou nao esta configurado
  - registra `compliance_risk_checked` com `provider`, `provider_status`, `degraded_reason`, `latency_ms` e `retries_used`
- Response:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "trm_labs",
  "provider_status": "degraded",
  "degraded_reason": "provider_not_configured",
  "risk_score": null,
  "dimensions": null,
  "checked_at": "2026-06-26T20:00:00+00:00"
}
```

- Resposta `live`:
  - `risk_score` vem preenchido quando o provider retorna score mapeavel
  - `dimensions` so vem preenchido se a resposta do provider trouxer estrutura compatível com o modelo 5D atual

### `POST /api/v1/compliance/due-diligence`

- Uso: consulta direta de capacidade de due diligence
- Comportamento:
  - nao retorna score de conforto ficticio
  - explicita `manual_review_required` ate existir integracao homologada
  - registra `compliance_due_diligence_checked` quando houver contexto organizacional
- Response:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "manual_review",
  "provider_status": "degraded",
  "degraded_reason": "manual_review_required",
  "capability_status": "degraded",
  "dd_score": null,
  "red_flags": [],
  "comfort_level": null,
  "checked_at": "2026-06-28T12:00:00+00:00"
}
```

### `POST /api/v1/compliance/source-of-funds`

- Uso: consulta direta de capacidade de origem de fundos
- Comportamento:
  - nao retorna percentuais ficticios de `clean_pct` ou `suspicious_pct`
  - responde com `origin_analysis.status=manual_review_pending` ate haver motor homologado
  - registra `compliance_source_of_funds_checked` quando houver contexto organizacional
- Response:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "manual_review",
  "provider_status": "degraded",
  "degraded_reason": "manual_review_required",
  "capability_status": "degraded",
  "origin_analysis": {
    "status": "manual_review_pending",
    "requires_human_review": true
  },
  "suspicious_pct": null,
  "clean_pct": null,
  "checked_at": "2026-06-28T12:00:00+00:00"
}
```

### `GET /api/v1/compliance/sanctions-check/{address}`

- Uso: consulta direta de capacidade de sanctions screening
- Comportamento:
  - nao retorna `hit=false` como falso negativo quando nao existe integracao homologada
  - explicita `sanctions_provider_not_integrated` e preserva a lista consultada
  - registra `compliance_sanctions_checked` quando houver contexto organizacional
- Response:

```json
{
  "address": "0x...",
  "chain": "ethereum",
  "provider": "sanctions_lists",
  "provider_status": "degraded",
  "degraded_reason": "sanctions_provider_not_integrated",
  "capability_status": "degraded",
  "lists": ["OFAC", "UN", "EU", "COAF"],
  "hit": null,
  "matched_lists": [],
  "entity_name": null,
  "designation_date": null,
  "checked_at": "2026-06-28T12:00:00+00:00"
}
```

## Monitoring API

### `GET /api/v1/monitoring/operations`

- Uso: catalogo de operacoes de monitoramento

### `GET /api/v1/monitoring/operations/{operation_identifier}`

- Uso: detalhe de operacao

### `POST /api/v1/monitoring/estimate`

- Uso: cotacao de monitoramento

### `POST /api/v1/monitoring/start`

- Uso: iniciar case/watchlist com quote confirmado

### `POST /api/v1/monitoring/watchlists`

- Uso: criar watchlist

### `GET /api/v1/monitoring/watchlists`

- Uso: listar watchlists

### `POST /api/v1/monitoring/watchlists/{watchlist_id}/items`

- Uso: adicionar item a watchlist

### `GET /api/v1/monitoring/alerts`

- Uso: listar alertas persistidos
- Query params:
  - `priority`
  - `watchlist_id`
  - `limit`

### `POST /api/v1/monitoring/test/trigger-alert`

- Uso: endpoint de teste para gerar alerta persistido

## Report API

### `POST /api/v1/reports/generate`

- Uso: gerar representacao deterministica de relatorio
- Request:

```json
{
  "case_id": "case-123",
  "report_type": "legal_report",
  "include_onchain_hash": false
}
```

### `GET /api/v1/reports/{report_id}`

- Uso: reservado; retorna `404 not_implemented`

### `GET /api/v1/reports/{report_id}/download`

- Uso: download do arquivo deterministico
- Query params obrigatorios:
  - `case_id`
  - `report_type`
  - `created_at`
- Regras para `legal_report`:
  - `X-Auth-Method=jwt`
  - `X-Role=ADMIN`
  - `X-2FA=ok`
- Auditoria:
  - gera `report_downloaded` quando ha contexto de organizacao

## Erros Relevantes

### Autenticacao/Autorizacao

- `401 missing_authorization`
- `401 invalid_token`
- `401 invalid_api_key`
- `403 admin_required`
- `403 legal_report_requires_jwt_auth`
- `403 legal_report_requires_admin_role`
- `403 2fa_required`

### Billing/Quote

- `404 quote_not_found`
- `409 quote_already_used`
- `410 quote_expired`
- `402 plan_downgraded_since_quote`
- `202 requote_required`
- `402 insufficient_credits`

### Catalogo/Entrada

- `422 invalid_report_type`
- `422 invalid_compliance_operation`
- `422 invalid_monitoring_operation`
- `422 unsupported_chain`

## Observacoes

- Alias recebido em API e sempre resolvido para valor canonico interno
- O contrato atual e o do scaffold executavel; antes de expor publicamente, o ideal e versionar formalmente como OpenAPI
