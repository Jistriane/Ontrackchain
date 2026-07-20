# Governance Dashboard - stg-2026-07-20-a

## Leitura Executiva

- atualizado em: `2026-07-20T19:02:37.980335+00:00`
- status geral: `failed`
- semaforo executivo: `amarelo`
- leitura: progresso regulatorio material com bloqueios remanescentes
- classificacao dominante: `technical_gate_blocked`
- resumo do bloqueio dominante: falha tecnica registrada em prepare, run, artifact_validation
- placeholders pendentes: `0`
- handoff pendente: `0`
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

- action plan: `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-war-room-action-plan.md`
- status snapshot (md): `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-status-snapshot.md`
- status delta (md): `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-status-snapshot-delta.md`
- snapshot atual (json): `artifacts/staging/checks/history/stg-2026-07-20-a-status-snapshot-20260720T190237Z.json`

## Comando Unico

- `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-20-a`
