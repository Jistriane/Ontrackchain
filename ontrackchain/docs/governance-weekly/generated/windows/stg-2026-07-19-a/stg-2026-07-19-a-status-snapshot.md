# Staging Window Status Snapshot - stg-2026-07-19-a

## Resumo

- window_id: `stg-2026-07-19-a`
- gerado em: `2026-07-19T01:08:24.576591+00:00`
- status geral: `failed`
- classificacao dominante: `operational_readiness_blocked`
- resumo do bloqueio dominante: 12 placeholder(s) e 8 campo(s) de handoff pendentes
- arquivo fonte: `artifacts/staging/checks/stg-2026-07-19-a-status-snapshot.json`

## Steps

| Step | Status | Exit Code | Generated At |
| --- | --- | --- | --- |
| prepare_staging_window | `failed` | `1` | `2026-07-19T01:08:24.422608+00:00` |
| run_staging_window | `failed` | `1` | `2026-07-19T01:08:24.497652+00:00` |
| validate_serious_window_artifact | `failed` | `1` | `n/a` |

## Bloqueios Consolidados

- placeholders pendentes: `12`
- campos handoff pendentes: `8`

## Escopo Regulatorio

- escopo regulatorio da tentativa: `none`
- scope validado pelo gate final: `P0-01,P0-02,P0-03`
- AML/KYT runtime gate: `unknown`
- AML/KYT runtime readiness: `unknown`
- feed UE tokenizado: `unknown`
- feed UE readiness: `unknown`
- bundle regulatorio (`P0-04`) readiness: `unknown`
- leitura de promocao: sem escopo regulatorio material nesta tentativa

## Classificacao Dominante

- classificacao: `operational_readiness_blocked`
- resumo: 12 placeholder(s) e 8 campo(s) de handoff pendentes

## Incidentes Operacionais e RCA

- status do resumo RCA: `not_available`
- exportados no resumo: `0`
- work-items rastreados: `0`
- RCAs anexadas: `0`
- causas confirmadas: `0`
- incidentes `firing`: `0`
- incidentes criticos abertos: `0`
- fila `READY`: `0`
- triagem pendente: `0`
- triagem acknowledged: `0`
- dominios RCA em destaque: `none`
- dominios afetados em destaque: `none`

### Placeholders pendentes

- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_TRM_SCREENING_URL`
- `GRAFANA_ADMIN_PASSWORD`
- `INVESTIGATION_RPC_FALLBACK_URL`
- `JWT_HS256_SECRET`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `MFA_TOTP_SECRET`
- `OPENSANCTIONS_API_KEY`
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

- run: `ownership_coverage: falhou`
- run: `placeholder_check: falhou`
- run: `handoff_check: falhou`
- artifact: `Mandatory artifact missing: OIDC preflight (oidc-preflight-stg-2026-07-19-a.json)`
- artifact: `Mandatory artifact missing: External preflight (external-preflight-stg-2026-07-19-a.json)`
- artifact: `Mandatory artifact missing: Release dossier (stg-2026-07-19-a-dossier.json)`
- artifact: `Scoped artifact missing for P0-01: OIDC bundle JSON (stg-2026-07-19-a-oidc-readiness-bundle.json)`
- artifact: `Scoped artifact missing for P0-01: OIDC bundle summary (stg-2026-07-19-a-oidc-readiness-bundle.md)`

## Proximo Passo

- preencher segredos reais no `.env.staging.private`
- atualizar `docs/staging-env-ownership.md` com `date/status` por dominio
- rerodar o snapshot para confirmar reducao de bloqueios
