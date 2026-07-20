# Plano de Acao do War Room - stg-2026-07-20-a

- gerado em: `2026-07-20T19:02:37.458764+00:00`
- checks_dir: `artifacts/staging/checks`
- fonte placeholders: `artifacts/staging/checks/placeholders-stg-2026-07-20-a.json`
- fonte handoff: `artifacts/staging/checks/handoff-stg-2026-07-20-a.json`
- fonte snapshot: `pending`

## Contexto Regulatorio

- escopo regulatorio da tentativa: `none`
- `P0-04` readiness: `unknown`
- leitura regulatoria: indisponivel
- classificacao dominante: `unknown`
- resumo do bloqueio dominante: indisponivel

## Auth/OIDC

- placeholders pendentes:
  - `none`
- handoff pendente:
  - `none`
- comandos sugeridos:
  - `python scripts/preflight_oidc_serious_env.py`
  - `python scripts/smoke_auth_oidc_mode.py`

## Compliance/AML

- placeholders pendentes:
  - `none`
- handoff pendente:
  - `none`
- comandos sugeridos:
  - `make check-compliance-provider-runtime`
  - `make run-eu-sanctions-window-local WINDOW_ID=<window_id>`
- observacao regulatoria:
  - sem escopo regulatorio material no snapshot atual

## Investigation/RPC

- placeholders pendentes:
  - `none`
- handoff pendente:
  - `none`
- comandos sugeridos:
  - `python scripts/preflight_external_integrations.py`

## Platform/Operations

- placeholders pendentes:
  - `none`
- handoff pendente:
  - `none`
- comandos sugeridos:
  - `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md`
  - `python scripts/check_staging_env_placeholders.py --file .env.staging.private`

## Fechamento

- atualizar `docs/staging-env-ownership.md` com `date` e `status` nos 4 grupos
- rerodar `python scripts/prepare_staging_window.py --window-id stg-2026-07-20-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
- se verde, executar `python scripts/run_staging_window.py --window-id stg-2026-07-20-a --private-env-file .env.staging.private`
