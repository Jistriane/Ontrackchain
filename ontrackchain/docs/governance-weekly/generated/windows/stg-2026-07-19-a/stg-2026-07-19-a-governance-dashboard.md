# Governance Dashboard - stg-2026-07-19-a

## Leitura Executiva

- atualizado em: `2026-07-19T01:08:24.576591+00:00`
- status geral: `failed`
- semaforo executivo: `vermelho`
- leitura: regressao de bloqueios
- classificacao dominante: `operational_readiness_blocked`
- resumo do bloqueio dominante: 12 placeholder(s) e 8 campo(s) de handoff pendentes
- placeholders pendentes: `12`
- handoff pendente: `8`
- escopo regulatorio da tentativa: `none`
- `P0-04` readiness: `unknown`
- leitura regulatoria: sem escopo regulatorio material nesta tentativa
- RCA cross-domain: `not_available` | RCA(s) `0` | criticos `0` | pendentes `0`
- dominios RCA em destaque: `none`

## Status dos Steps

| Step | Status |
| --- | --- |
| prepare_staging_window | `failed` |
| run_staging_window | `failed` |
| validate_serious_window_artifact | `failed` |

## Artefatos de Referencia

- action plan: `docs/governance-weekly/generated/windows/stg-2026-07-19-a/stg-2026-07-19-a-war-room-action-plan.md`
- status snapshot (md): `docs/governance-weekly/generated/windows/stg-2026-07-19-a/stg-2026-07-19-a-status-snapshot.md`
- status delta (md): `docs/governance-weekly/generated/windows/stg-2026-07-19-a/stg-2026-07-19-a-status-snapshot-delta.md`
- snapshot atual (json): `artifacts/staging/checks/history/stg-2026-07-19-a-status-snapshot-20260719T010824Z.json`

## Comando Unico

- `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-19-a`
