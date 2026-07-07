# Guia Combinado - Janela Seria `P0-01 + P0-02 + P0-03`

## Objetivo

Concentrar a ordem recomendada para executar uma janela seria combinada cobrindo `OIDC + MFA`, `AML/KYT live` e feed UE real, com artefatos suficientes para `go/no-go`, bundle regulatorio e revisao formal.

## Quando Usar

- quando as tres trilhas tiverem owners nominais confirmados
- quando os segredos reais de `P0-01`, `P0-02` e `P0-03` estiverem disponiveis fora do repositorio
- quando a janela exigir um pacote executivo unificado para sign-off

## Guias de Apoio

- [Guia de Execucao Assistida de `P0-01` OIDC + MFA serio](./P0-01_OIDC_MFA_EXECUTION_GUIDE.md)
- [Guia de Execucao Assistida de `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_EXECUTION_GUIDE.md)
- [Guia de Execucao Assistida de `P0-03` Feed UE real](./P0-03_EU_FEED_EXECUTION_GUIDE.md)

## Precondicoes

- `docs/staging-env-ownership.md` sem owners obrigatorios pendentes para `Auth/OIDC` e `Compliance/AML`
- `.env.staging.private` sem placeholders criticos do escopo da janela
- war room da janela em `go` ou `go_with_exception`
- facilitador e bridge da janela preenchidos

## Ordem Recomendada de Execucao

### 1. Gate agregado inicial

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/prepare_staging_window.py \
  --window-id <window_id> \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

Esperado:

- `status=ok`
- owners e placeholders coerentes com o escopo

### 2. Executar `P0-01`

Executar em ordem:

- `python3 scripts/preflight_oidc_serious_env.py`
- `python3 scripts/smoke_auth_oidc_mode.py`
- `cd apps/frontend && npm ci && npm run test:e2e:oidc-critical`
- `make run-oidc-readiness-bundle-local WINDOW_ID=<window_id> BASE_URL=http://localhost:8080`

Saidas esperadas:

- `<window_id>-oidc-readiness-bundle.json`
- `<window_id>-oidc-readiness-bundle.md`

### 3. Executar `P0-02`

Executar em ordem:

- `python3 scripts/preflight_external_integrations.py`
- `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- `python3 scripts/smoke_runtime.py`
- `python3 scripts/homologation_external_evidence.py --mode compliance`

Saidas esperadas:

- gate AML/KYT verde
- artefato de homologacao em `artifacts/homologation/`

### 4. Executar `P0-03`

Executar em ordem:

- `make rerun-compliance-worker`
- `make run-eu-sanctions-window-local WINDOW_ID=<window_id>`
- `make check-eu-sanctions-window`

Saidas esperadas:

- `<window_id>-eu-sanctions-preflight.json`
- `<window_id>-eu-sanctions-sync.json`
- `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`

### 5. Consolidar `P0-02 + P0-03`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID=<window_id>
```

Saidas esperadas:

- `<window_id>-regulatory-readiness-bundle.json`
- `<window_id>-regulatory-readiness-bundle.md`

### 6. Reconciliar governanca semanal

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Saidas esperadas:

- snapshot e delta atualizados
- artefatos em `docs/governance-weekly/generated/windows/<window_id>/`
- consolidado pronto para gate, Slack, dashboard e sign-off

## Artefatos Minimos da Janela

- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- artefato de homologacao externa em `artifacts/homologation/`
- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Criterio de Go

Considerar `go` somente quando:

- `P0-01` estiver ao menos em `ready_for_validation`
- `P0-02` estiver ao menos em `ready_for_validation`
- `P0-03` estiver ao menos em `ready_for_validation`
- bundles OIDC e regulatorio existirem
- nenhum bloqueador `WR-*` permanecer aberto sem waiver formal

## No-Go Imediato

- fallback silencioso para `dev auth`
- ausencia do bundle OIDC quando `P0-01` estiver no escopo
- ausencia dos JSONs da janela UE quando `P0-03` estiver no escopo
- ausencia do bundle regulatorio quando `P0-02/P0-03` estiverem no escopo
- homologacao externa ausente para o modo exercitado

## Resultado Esperado

- trilhas `P0-01`, `P0-02` e `P0-03` com evidencia preservada
- pacote unico suficiente para sign-off
- decisao formal `go/no-go` documentada na governanca semanal
