# Bloco Pronto de Comandos - Janela Seria Integrada

## Objetivo

Entregar um bloco unico de comandos, pronto para copiar e executar, para a janela seria integrada de `P0-01 + P0-02 + P0-03` assim que o `.env.staging.private` estiver preenchido e os owners tiverem concluido o handoff.

## Quando Usar

- quando o arquivo `.env.staging.private` ja estiver preenchido fora do versionamento
- quando `docs/staging-env-ownership.md` estiver sem `pending` nos grupos obrigatorios
- quando a janela estiver autorizada para execucao em `staging`

## `window_id` Recomendado

Use o padrao:

```text
stg-YYYY-MM-DD-serious-a
```

Exemplo desta rodada:

```text
stg-2026-07-07-serious-a
```

## Bloco Unico de Execucao

Copiar e executar somente depois do preenchimento real do ambiente:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain

export WINDOW_ID=stg-2026-07-07-serious-a
export APP_ENV=staging
export AUTH_MODE=oidc
export DEV_AUTH_ENABLED=false
export NEXT_PUBLIC_AUTH_MODE=oidc
export NEXT_PUBLIC_APP_ENV=staging
export NEXT_PUBLIC_DEV_AUTH_ENABLED=false
export ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live
export ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only

python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private

python3 scripts/prepare_staging_window.py \
  --window-id "$WINDOW_ID" \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight

python3 scripts/preflight_oidc_serious_env.py
python3 scripts/smoke_auth_oidc_mode.py

cd /home/jistriane/Ontrackchain/ontrackchain/apps/frontend
npm ci
npm run test:e2e:oidc-critical

cd /home/jistriane/Ontrackchain/ontrackchain
make run-oidc-readiness-bundle-local \
  WINDOW_ID="$WINDOW_ID" \
  BASE_URL=http://localhost:8080

python3 scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/smoke_runtime.py
python3 scripts/homologation_external_evidence.py --mode compliance

make rerun-compliance-worker
make run-eu-sanctions-window-local WINDOW_ID="$WINDOW_ID"
make check-eu-sanctions-window

make run-regulatory-readiness-bundle-local WINDOW_ID="$WINDOW_ID"
make refresh-staging-war-room-governance-local WINDOW_ID="$WINDOW_ID"
```

## Precondicoes Minimas

Antes do bloco acima, confirmar:

- `.env.staging.private` existe e nao sera commitado
- `Auth/OIDC.date` e `Auth/OIDC.status` estao preenchidos
- `Compliance/AML.date` e `Compliance/AML.status` estao preenchidos
- `Investigation/RPC.date` e `Investigation/RPC.status` estao preenchidos
- `Platform/Operations.date` e `Platform/Operations.status` estao preenchidos
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` usa `https` e contem `token=`
- `COMPLIANCE_TRM_SCREENING_URL` e `COMPLIANCE_TRM_API_KEY` sao reais
- endpoints `OIDC_*` nao apontam para `localhost`

## Resultado Esperado

Ao final do bloco, devem existir ao menos:

- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Falha Imediata

Interromper a janela imediatamente se ocorrer qualquer um dos pontos abaixo:

- `check_staging_env_handoff.py` retornar `failed`
- `check_staging_env_placeholders.py` retornar `failed`
- `preflight_oidc_serious_env.py` detectar fallback para `dev auth`
- `check-compliance-provider-runtime` nao ficar verde
- `check-eu-sanctions-window` nao confirmar `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`

## Referencias

- [Pacote Final de Execucao da Janela Seria Integrada](./SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md)
- [Guia Combinado da Janela Seria `P0-01 + P0-02 + P0-03`](./P0_COMBINED_SERIOUS_WINDOW_GUIDE.md)
- [Checklist de Evidência Mínima da Primeira Janela Séria](../../first-serious-window-evidence-checklist.md)
