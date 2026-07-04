# Staging Window Status Snapshot - stg-2026-07-06-a

## Resumo

- window_id: `stg-2026-07-06-a`
- gerado em: `2026-07-04T01:16:32.746097+00:00`
- status geral: `failed`
- arquivo fonte: `artifacts/staging/checks/stg-2026-07-06-a-status-snapshot.json`

## Steps

| Step | Status | Exit Code | Generated At |
| --- | --- | --- | --- |
| prepare_staging_window | `failed` | `1` | `2026-07-04T01:16:32.623997+00:00` |
| run_staging_window | `failed` | `1` | `2026-07-04T01:16:32.682849+00:00` |
| validate_serious_window_artifact | `ok` | `0` | `n/a` |

## Bloqueios Consolidados

- placeholders pendentes: `12`
- campos handoff pendentes: `8`

### Placeholders pendentes

- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_TRM_SCREENING_URL`
- `GRAFANA_ADMIN_PASSWORD`
- `INVESTIGATION_RPC_FALLBACK_URL`
- `INVESTIGATION_RPC_PRIMARY_URL`
- `JWT_HS256_SECRET`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `MFA_TOTP_SECRET`
- `POSTGRES_PASSWORD`

### Campos de handoff pendentes

- `Auth/OIDC.date`
- `Auth/OIDC.status`
- `Compliance/AML.date`
- `Compliance/AML.status`
- `Investigation/RPC.date`
- `Investigation/RPC.status`
- `Platform/Operations.date`
- `Platform/Operations.status`

## Erros de Execucao

- run: `placeholder_check: falhou`
- run: `handoff_check: falhou`
- artifact: `none`

## Proximo Passo

- preencher segredos reais no `.env.staging.private`
- atualizar `docs/staging-env-ownership.md` com `date/status` por dominio
- rerodar o snapshot para confirmar reducao de bloqueios
