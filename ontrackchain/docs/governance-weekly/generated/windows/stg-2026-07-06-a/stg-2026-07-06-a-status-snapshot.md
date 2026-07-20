# Staging Window Status Snapshot - stg-2026-07-06-a

## Resumo

- window_id: `stg-2026-07-06-a`
- gerado em: `2026-07-19T23:56:48.822717+00:00`
- status geral: `failed`
- classificacao dominante: `technical_gate_blocked`
- resumo do bloqueio dominante: falha tecnica registrada em prepare, run, artifact_validation
- arquivo fonte: `artifacts/staging/checks/stg-2026-07-06-a-status-snapshot.json`

## Steps

| Step | Status | Exit Code | Generated At |
| --- | --- | --- | --- |
| prepare_staging_window | `failed` | `1` | `2026-07-19T23:56:48.665174+00:00` |
| run_staging_window | `failed` | `1` | `2026-07-19T23:56:48.722141+00:00` |
| validate_serious_window_artifact | `failed` | `1` | `n/a` |

## Bloqueios Consolidados

- placeholders pendentes: `0`
- campos handoff pendentes: `0`

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

- classificacao: `technical_gate_blocked`
- resumo: falha tecnica registrada em prepare, run, artifact_validation

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

- `none`

### Campos de handoff pendentes

- `none`

## Erros de Execucao

- run: `external_preflight: falhou`
- artifact: `Mandatory artifact missing: Release dossier (stg-2026-07-06-a-dossier.json)`
- artifact: `Scoped artifact missing for P0-01: OIDC bundle JSON (stg-2026-07-06-a-oidc-readiness-bundle.json)`
- artifact: `Scoped artifact missing for P0-01: OIDC bundle summary (stg-2026-07-06-a-oidc-readiness-bundle.md)`

## Proximo Passo

- investigar a falha tecnica dominante no gate agregado
- anexar RCA ou evidencia tecnica antes da proxima tentativa
- rerodar o snapshot apos a correcao para confirmar estabilizacao
