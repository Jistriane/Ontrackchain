# Checklist de Desbloqueio - stg-2026-07-19-a

## Resumo

- gerado em: `2026-07-19T01:08:24.576591+00:00`
- snapshot fonte: `artifacts/staging/checks/stg-2026-07-19-a-status-snapshot.json`
- status geral: `failed`
- classificacao dominante: `operational_readiness_blocked`
- resumo do bloqueio dominante: 12 placeholder(s) e 8 campo(s) de handoff pendentes
- placeholders pendentes: `12`
- handoff pendente: `8`
- escopo regulatorio da tentativa: `none`
- scope validado no gate final: `P0-01,P0-02,P0-03`
- `P0-04` readiness: `unknown`
- leitura regulatoria: sem escopo regulatorio material nesta tentativa

## Sequencia Segura (Sem Expor Segredos)

1. Preencher segredos reais apenas em `.env.staging.private` local e nunca em documentos versionados.
2. Atualizar `docs/staging-env-ownership.md` somente com `date` e `status` por trilha.
3. Executar os comandos sugeridos por trilha e anexar evidencias em `artifacts/staging/checks` e `artifacts/staging/dossiers`.
4. Reexecutar o pacote completo com `make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>`.
5. Confirmar reducao objetiva de bloqueios no delta e no dashboard executivo.

## Auth/OIDC

- objetivo: reduzir bloqueios da trilha `Auth/OIDC`
- placeholders:
  - [ ] JWT_HS256_SECRET
  - [ ] KEYCLOAK_ADMIN_PASSWORD
  - [ ] KEYCLOAK_B2B_CLIENT_SECRET
  - [ ] MFA_TOTP_SECRET
- handoff:
  - [ ] Auth/OIDC.date
  - [ ] Auth/OIDC.status
- comandos de validacao:
  - `python scripts/preflight_oidc_serious_env.py`
  - `python scripts/smoke_auth_oidc_mode.py`

## Compliance/AML

- objetivo: reduzir bloqueios da trilha `Compliance/AML`
- placeholders:
- contexto regulatorio: escopo atual `none` com `P0-04=unknown`
- classificacao dominante atual: `operational_readiness_blocked`
  - [ ] COMPLIANCE_EU_SANCTIONS_SOURCE_URL
  - [ ] COMPLIANCE_TRM_API_KEY
  - [ ] COMPLIANCE_TRM_SCREENING_URL
- handoff:
  - [ ] Compliance/AML.date
  - [ ] Compliance/AML.status
- comandos de validacao:
  - `make check-compliance-provider-runtime`
  - `make run-eu-sanctions-window-local WINDOW_ID=<window_id>`

## Investigation/RPC

- objetivo: reduzir bloqueios da trilha `Investigation/RPC`
- placeholders:
  - [ ] INVESTIGATION_RPC_FALLBACK_URL
- handoff:
  - [ ] Investigation/RPC.date
  - [ ] Investigation/RPC.status
- comandos de validacao:
  - `python scripts/preflight_external_integrations.py`

## Platform/Operations

- objetivo: reduzir bloqueios da trilha `Platform/Operations`
- placeholders:
  - [ ] ALERTMANAGER_WEBHOOK_BEARER_TOKEN
  - [ ] GRAFANA_ADMIN_PASSWORD
  - [ ] OPENSANCTIONS_API_KEY
  - [ ] POSTGRES_PASSWORD
- handoff:
  - [ ] Platform/Operations.date
  - [ ] Platform/Operations.status
- comandos de validacao:
  - `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md`
  - `python scripts/check_staging_env_placeholders.py --file .env.staging.private`

## Criterio de Saida

- `prepare_staging_window`: `ok`
- `run_staging_window`: `ok`
- `validate_serious_window_artifact`: `ok`
- placeholders pendentes: `0`
- handoff pendente: `0`
- se o escopo regulatorio for parcial, nao marcar `P0-04` como fechado
- so considerar promocao oficial de `P0-04` quando `P0-02` e `P0-03` convergirem na mesma trilha revisavel
