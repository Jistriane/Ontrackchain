# Pacote Final de Execucao - Janela Seria Integrada

## Objetivo

Entregar um roteiro unico, objetivo e operacional para conduzir uma janela seria integrada cobrindo `P0-01`, `P0-02` e `P0-03`, com um `window_id` padrao, checklist final de ambiente, comandos em ordem exata, artefatos obrigatorios e criterio de sign-off.

## Quando Usar

- quando o design operacional das trilhas ja estiver aprovado
- quando a execucao real for acontecer em ambiente `staging`
- quando o facilitador precisar conduzir a janela sem alternar entre varios documentos

## Artefatos de Apoio

- [Guia Combinado da Janela Seria `P0-01 + P0-02 + P0-03`](./P0_COMBINED_SERIOUS_WINDOW_GUIDE.md)
- [Checklist de Fechamento Semanal da Governanca](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)
- [Checklist de Evidência Mínima da Primeira Janela Séria](../../first-serious-window-evidence-checklist.md)

## `window_id` Sugerido

Usar o padrao:

```text
stg-YYYY-MM-DD-serious-a
```

Exemplo:

```text
stg-2026-07-07-serious-a
```

## Checklist Final de Ambiente

Antes de rodar qualquer comando, confirmar:

- [ ] `.env.staging.private` existe fora do versionamento
- [ ] `docs/staging-env-ownership.md` esta sem pendencias obrigatorias para `Auth/OIDC` e `Compliance/AML`
- [ ] `AUTH_MODE=oidc`
- [ ] `DEV_AUTH_ENABLED=false`
- [ ] `NEXT_PUBLIC_AUTH_MODE=oidc`
- [ ] `NEXT_PUBLIC_DEV_AUTH_ENABLED=false`
- [ ] `OIDC_*` aponta para endpoints reais, nunca `localhost`
- [ ] `AML/KYT` live esta credenciado
- [ ] `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` usa `https` e contem `token=`
- [ ] war room da janela esta `go` ou `go_with_exception`

## Sequencia Exata de Comandos

Executar na ordem abaixo, sem pular validacoes.

### 1. Gate agregado inicial

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
export WINDOW_ID=stg-2026-07-07-serious-a
python3 scripts/prepare_staging_window.py \
  --window-id "$WINDOW_ID" \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

### 2. Validacoes de handoff e placeholders

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private
```

### 3. Execucao `P0-01`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_oidc_serious_env.py
python3 scripts/smoke_auth_oidc_mode.py

cd /home/jistriane/Ontrackchain/ontrackchain/apps/frontend
npm ci
npm run test:e2e:oidc-critical

cd /home/jistriane/Ontrackchain/ontrackchain
make run-oidc-readiness-bundle-local \
  WINDOW_ID="$WINDOW_ID" \
  BASE_URL=http://localhost:8080
```

### 4. Execucao `P0-02`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/smoke_runtime.py
python3 scripts/homologation_external_evidence.py --mode compliance
```

### 5. Execucao `P0-03`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make rerun-compliance-worker
make run-eu-sanctions-window-local WINDOW_ID="$WINDOW_ID"
make check-eu-sanctions-window
```

### 6. Consolidacao `P0-02 + P0-03`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID="$WINDOW_ID"
```

### 7. Reconciliacao final da governanca

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID="$WINDOW_ID"
```

## Artefatos Que Precisam Existir ao Final

### Pacote base da janela

- `artifacts/staging/window-packet-<window_id>.md`
- `artifacts/staging/checks/ownership-coverage-<window_id>.json`
- `artifacts/staging/checks/placeholders-<window_id>.json`
- `artifacts/staging/checks/handoff-<window_id>.json`

### `P0-01`

- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- relatorio ou evidência do `npm run test:e2e:oidc-critical`

### `P0-02`

- evidência do `make check-compliance-provider-runtime`
- artefato de homologacao externa em `artifacts/homologation/`

### `P0-03`

- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`

### `P0-02 + P0-03`

- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`

### Governanca final

- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-war-room-action-plan.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot-delta.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Criterio Objetivo de Sign-Off

Declarar a janela apta a `sign-off` somente quando todos forem verdadeiros:

- [ ] gate agregado inicial retornou `status=ok`
- [ ] `P0-01` sem fallback para `dev auth`
- [ ] bundle OIDC existe e esta revisavel
- [ ] `P0-02` tem evidência de provider pronto e homologacao externa preservada
- [ ] `P0-03` tem os dois JSONs da janela UE
- [ ] `EU_CONSOLIDATED` esta em `ACTIVE/SUCCESS`
- [ ] bundle regulatorio existe e esta revisavel
- [ ] a governanca foi reprocessada para o mesmo `window_id`
- [ ] nao existe bloqueador `WR-*` aberto sem waiver formal
- [ ] owner e accountable revisaram os artefatos

## No-Go Imediato

Encerrar a janela como `no-go` imediatamente se qualquer um ocorrer:

- fallback silencioso para `dev auth`
- ausencia do bundle OIDC
- ausencia do bundle regulatorio
- ausencia dos JSONs da janela UE
- ausencia de homologacao externa para o modo exercitado
- `EU_CONSOLIDATED` sem `ACTIVE/SUCCESS`
- `status` final inconsistente entre war room, snapshot e consolidado

## Resultado Esperado

Ao final desta execucao, a janela precisa deixar:

- evidência preservada para `P0-01`
- evidência preservada para `P0-02`
- evidência preservada para `P0-03`
- pacote suficiente para `go/no-go`
- base objetiva para promover maturidade com aprovacao formal
