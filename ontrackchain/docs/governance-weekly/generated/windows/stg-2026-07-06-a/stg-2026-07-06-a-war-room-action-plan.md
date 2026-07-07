# Plano de Acao do War Room - stg-2026-07-06-a

- gerado em: `2026-07-04T01:16:32.512455+00:00`
- checks_dir: `artifacts/staging/checks`
- fonte placeholders: `artifacts/staging/checks/placeholders-stg-2026-07-06-a.json`
- fonte handoff: `artifacts/staging/checks/handoff-stg-2026-07-06-a.json`

## Auth/OIDC

- placeholders pendentes:
  - `JWT_HS256_SECRET`
  - `KEYCLOAK_ADMIN_PASSWORD`
  - `KEYCLOAK_B2B_CLIENT_SECRET`
  - `MFA_TOTP_SECRET`
- handoff pendente:
  - `date`
  - `status`
- comandos sugeridos:
  - `python scripts/preflight_oidc_serious_env.py`
  - `python scripts/smoke_auth_oidc_mode.py`

## Compliance/AML

- placeholders pendentes:
  - `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
  - `COMPLIANCE_TRM_API_KEY`
  - `COMPLIANCE_TRM_SCREENING_URL`
- handoff pendente:
  - `date`
  - `status`
- comandos sugeridos:
  - `make check-compliance-provider-runtime`
  - `make run-eu-sanctions-window-local WINDOW_ID=<window_id>`

## Investigation/RPC

- placeholders pendentes:
  - `INVESTIGATION_RPC_FALLBACK_URL`
  - `INVESTIGATION_RPC_PRIMARY_URL`
- handoff pendente:
  - `date`
  - `status`
- comandos sugeridos:
  - `python scripts/preflight_external_integrations.py`

## Platform/Operations

- placeholders pendentes:
  - `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
  - `GRAFANA_ADMIN_PASSWORD`
  - `POSTGRES_PASSWORD`
- handoff pendente:
  - `date`
  - `status`
- comandos sugeridos:
  - `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md`
  - `python scripts/check_staging_env_placeholders.py --file .env.staging.private`

## Fechamento

- atualizar `docs/staging-env-ownership.md` com `date` e `status` nos 4 grupos
- rerodar `python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
- se verde, executar `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`
