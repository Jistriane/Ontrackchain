# Runbook do Primeiro Disparo Real

## Objetivo

Executar a primeira janela séria de staging com disciplina operacional suficiente para produzir evidências anexáveis e um `go/no-go` defensável.

## Entradas Obrigatórias

- `window_id` definido
- `.env.staging.private` provisionado para o escopo da janela
- war room criado e owners online identificados
- artifact target do workflow ou execução local definido

## Sequência Recomendada

1. Validar ownership, placeholders e handoff.
2. Rodar o gate agregado com `prepare_staging_window.py --validate --preflight`.
3. Se `P0-01` estiver no escopo, gerar o bundle OIDC.
4. Se `P0-02/P0-03` estiverem no escopo, gerar o bundle regulatório.
5. Executar `run_staging_window.py` para consolidar checks, homologação e dossier.
6. Atualizar live tracking, war room e sign-off com os paths finais.

## Comandos Canônicos

```bash
python scripts/prepare_staging_window.py --window-id <janela> --mode baseline --private-env-file .env.staging.private --validate --preflight
python scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private
```

Para `P0-01`:

```bash
make run-oidc-readiness-bundle-local WINDOW_ID=<janela> BASE_URL=http://localhost:8080
```

Para `P0-02/P0-03`:

```bash
make run-regulatory-readiness-bundle-local WINDOW_ID=<janela> INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080
```

## Saídas Esperadas

- `window packet`
- JSONs de checks/preflights em `artifacts/staging/checks/`
- homologação em `artifacts/homologation/`
- dossier e manifestos em `artifacts/staging/dossiers/`
- `oidc-readiness-bundle.md` quando `P0-01` estiver no escopo
- `regulatory-readiness-bundle.md` quando `P0-02/P0-03` estiverem no escopo

## Critério de Encerramento

- war room atualizado com decisão final
- sign-off preenchido com artifact real
- checklist de evidência mínima revisado
- exceções registradas explicitamente, se existirem