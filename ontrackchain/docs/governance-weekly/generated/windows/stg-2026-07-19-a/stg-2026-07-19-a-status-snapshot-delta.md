# Staging Window Status Delta - stg-2026-07-19-a

## Resumo

- `insufficient_history`: menos de 2 snapshots historicos disponiveis
- history_dir: `artifacts/staging/checks/history`

## Proximo Passo

- executar novamente `make run-staging-window-status-snapshot-local WINDOW_ID=<window_id>` para criar base de comparacao
