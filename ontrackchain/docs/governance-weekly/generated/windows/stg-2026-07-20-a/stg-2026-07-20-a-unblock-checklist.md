# Checklist de Desbloqueio - stg-2026-07-20-a

## Resumo

- gerado em: `2026-07-20T19:02:37.980335+00:00`
- snapshot fonte: `artifacts/staging/checks/stg-2026-07-20-a-status-snapshot.json`
- status geral: `failed`
- classificacao dominante: `technical_gate_blocked`
- resumo do bloqueio dominante: falha tecnica registrada em prepare, run, artifact_validation
- placeholders pendentes: `0`
- handoff pendente: `0`
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
  - [x] nenhum placeholder pendente
- handoff:
  - [x] nenhum campo de handoff pendente
- comandos de validacao:
  - `python scripts/preflight_oidc_serious_env.py`
  - `python scripts/smoke_auth_oidc_mode.py`

## Compliance/AML

- objetivo: reduzir bloqueios da trilha `Compliance/AML`
- placeholders:
- contexto regulatorio: escopo atual `none` com `P0-04=unknown`
- classificacao dominante atual: `technical_gate_blocked`
  - [x] nenhum placeholder pendente
- handoff:
  - [x] nenhum campo de handoff pendente
- comandos de validacao:
  - `make check-compliance-provider-runtime`
  - `make run-eu-sanctions-window-local WINDOW_ID=<window_id>`

## Investigation/RPC

- objetivo: reduzir bloqueios da trilha `Investigation/RPC`
- placeholders:
  - [x] nenhum placeholder pendente
- handoff:
  - [x] nenhum campo de handoff pendente
- comandos de validacao:
  - `python scripts/preflight_external_integrations.py`

## Platform/Operations

- objetivo: reduzir bloqueios da trilha `Platform/Operations`
- placeholders:
  - [x] nenhum placeholder pendente
- handoff:
  - [x] nenhum campo de handoff pendente
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
