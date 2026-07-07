# Execucao Local de Preflight da Janela Seria — 2026-07-03

## Objetivo

Registrar a execucao local dos gates da janela `stg-2026-07-06-a` para evidenciar estado real de prontidao e bloqueios ativos.

## Escopo Executado

- bundle regulatorio local
- bundle OIDC local
- gate agregado via `prepare_staging_window.py --validate --preflight`
- validacao de completude de artifact

## Resultado Consolidado

- status geral de prontidao: `failed`
- baseline tecnica: mantida
- bloqueios externos/operacionais: mantidos
- validacao agregada de artifact: `ok`
- execucao ponta a ponta (`run_staging_window.py`): `failed` por gate local

## Evidencias Geradas

- `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/stg-2026-07-06-a-regulatory-readiness-bundle.md`
- `artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/stg-2026-07-06-a-oidc-readiness-bundle.md`
- `artifacts/staging/checks/ownership-coverage-stg-2026-07-06-a.json`
- `artifacts/staging/checks/placeholders-stg-2026-07-06-a.json`
- `artifacts/staging/checks/handoff-stg-2026-07-06-a.json`
- `artifacts/staging/window-packet-stg-2026-07-06-a.md`
- `artifacts/staging/checks/stg-2026-07-06-a-external_preflight.json`
- `artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a_20260703T213335Z.json`
- `artifacts/staging/dossiers/staging_release_dossier_stg-2026-07-06-a_20260703T213335Z.json.manifest.json`

## Bloqueios Confirmados no Ciclo

### Placeholders pendentes no `.env.staging.private`

Total pendente na ultima execucao ponta a ponta: `12` placeholders obrigatorios.

- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`
- e demais segredos criticos ainda em placeholder

### Handoff com pendencias obrigatorias

Total pendente na ultima execucao ponta a ponta: `8` campos obrigatorios.

- `Auth/OIDC.date`
- `Auth/OIDC.status`
- `Compliance/AML.date`
- `Compliance/AML.status`
- `Investigation/RPC.date`
- `Investigation/RPC.status`
- `Platform/Operations.date`
- `Platform/Operations.status`

## Execucao Ponta a Ponta da Janela (registro)

- comando executado:
  - `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`
- resultado:
  - `status=failed`
  - erros: `placeholder_check: falhou`, `handoff_check: falhou`
  - passos `oidc_preflight`, `external_preflight`, `homologation` e `release_dossier` ficaram `skipped` por `local_gates_failed`

### Reexecucao de Confirmacao (2026-07-03T21:40Z)

- gate agregado executado:
  - `python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
  - `generated_at`: `2026-07-03T21:40:40.333232+00:00`
  - resultado: `status=failed`
  - preflight: `skipped` por `validation_failed`
- run ponta a ponta executado:
  - `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`
  - `generated_at`: `2026-07-03T21:40:45.834170+00:00`
  - resultado: `status=failed`
  - erros: `placeholder_check: falhou`, `handoff_check: falhou`

Resumo objetivo da reexecucao:

- placeholders obrigatorios pendentes: `12`
- campos obrigatorios de handoff pendentes: `8`
- estado operacional manteve `blocked`, sem mudanca de baseline

### Artifact validado no fechamento tecnico

- preflight OIDC reconhecido (`stg-2026-07-06-a-oidc-preflight.json`)
- preflight externo reconhecido (`stg-2026-07-06-a-external_preflight.json`)
- dossier versionado reconhecido (`staging_release_dossier_stg-2026-07-06-a_<timestamp>.json`)

## Ajuste Tecnico Aplicado no Repositorio

Foi corrigida a nomenclatura dos arquivos gerados por `prepare_staging_window.py` para alinhar com o validador agregado.

Tambem foi ajustado `validate_serious_window_artifact.py` para aceitar variacoes canonicas de naming dos checks e o formato real do dossier versionado por timestamp.

Ganho observado:

- antes do ajuste, o validador reportava como ausentes tambem `ownership`, `placeholders` e `handoff`
- apos os ajustes, a validacao agregada passou a reconhecer o conjunto completo de artifacts da janela

## Decisao Operacional

- manter `go` para validacao seria controlada
- manter `no-go` para producao regulada forte
- nao promover `P0-01`, `P0-02` ou `P0-03` sem evidência nova material

## Proxima Execucao Recomendata

1. preencher segredos reais em canal seguro
2. atualizar handoff em `docs/staging-env-ownership.md`
3. rerodar:
   - `python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
4. se gate agregado ficar verde, executar:
   - `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`
