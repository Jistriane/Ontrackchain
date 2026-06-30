# Template de Execucao de Janela Seria

## Janela

- `window_id`:
- `ambiente`:
- `objetivo`:

## Owners

- `Backend/Auth`:
- `Compliance/Backend`:
- `Backend Core`:
- `Platform/SRE`:
- `Platform/DBA`:
- `Security/Compliance`:

## Entradas

- [ ] `.env.staging.private` criado a partir de `.env.staging.example`
- [ ] placeholders preenchidos sem `__FILL_*__`
- [ ] handoff atualizado em `docs/staging-env-ownership.md`
- [ ] janela registrada na governanca semanal

## Execucao (recomendada)

```bash
python scripts/run_staging_window.py \
  --window-id <window_id> \
  --private-env-file .env.staging.private
```

## Artefatos Esperados

- [ ] `artifacts/staging/checks/ownership-coverage-<window_id>.json`
- [ ] `artifacts/staging/window-packet-<window_id>.md`
- [ ] `artifacts/staging/checks/placeholders-<window_id>.json`
- [ ] `artifacts/staging/checks/handoff-<window_id>.json`
- [ ] `artifacts/homologation/<artefato>.json`
- [ ] `artifacts/homologation/<artefato>.json.manifest.json`
- [ ] `artifacts/staging/dossiers/<dossier>.json`
- [ ] `artifacts/staging/dossiers/<dossier>.manifest.json`

## Evidencias por Item

### `P0-01` (OIDC serio)

- [ ] preflight `OIDC` `ok`
- [ ] smoke `effective_auth_mode=oidc`
- [ ] evidência de login real (sem depender de `dev auth`)

### `P0-05` (AML/KYT `live`)

- [ ] preflight integrações externas `ok`
- [ ] homologacao externa `compliance` (ou `both`)
- [ ] evidência correlacionada por `request_id`

### `P0-06` (RPC primario + fallback)

- [ ] preflight integrações externas `ok`
- [ ] homologacao externa `rpc` (ou `both`)
- [ ] evidência correlacionada por `request_id`

### `RUN-STG-01` (janela completa)

- [ ] dossier final gerado
- [ ] `status=ok` no dossier final apenas quando tudo estiver `ok`

## Go/No-Go

- [ ] checklist aplicado:
  - [Checklist de Evidencia Minima da Primeira Janela Seria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md)

## Registro Semanal

- [ ] novo registro criado em:
  - [Registros Semanais de Governanca](file:///home/jistriane/Ontracktchain/ontrackchain/docs/governance-weekly/README.md)

## Observacoes

- 
