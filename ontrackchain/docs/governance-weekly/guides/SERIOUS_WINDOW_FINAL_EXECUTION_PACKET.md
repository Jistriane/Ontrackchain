# Pacote Final de Execucao - Janela Seria Integrada

## Objetivo

Entregar um roteiro unico, objetivo e operacional para conduzir uma janela seria integrada cobrindo `P0-01`, `P0-02` e `P0-03`, com um `window_id` padrao, checklist final de ambiente, comandos em ordem exata, artefatos obrigatorios e criterio de sign-off.

## Quando Usar

- quando o design operacional das trilhas ja estiver aprovado
- quando a execucao real for acontecer em ambiente `staging`
- quando o facilitador precisar conduzir a janela sem alternar entre varios documentos

## Artefatos de Apoio

- [Checklist de Fechamento Semanal da Governanca](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)
- [Checklist de Evidência Mínima da Primeira Janela Séria](../../history/first-serious-window-evidence-checklist.md) - apoio historico complementar; a sequencia viva desta janela esta neste proprio pacote
- [Checklist Executivo da Primeira Janela Combinada `P0-02 + P0-03`](./FIRST_COMBINED_SERIOUS_WINDOW_EXECUTIVE_CHECKLIST.md)
- [Run Sheet Preenchivel da Primeira Janela Combinada](./FIRST_COMBINED_SERIOUS_WINDOW_RUN_SHEET.md)
- [Workflow de Atualizacao Semanal da Governanca](./WEEKLY_GOVERNANCE_UPDATE_WORKFLOW.md)
- [Guia `P0-01` OIDC + MFA serio](./P0-01_OIDC_MFA_EXECUTION_GUIDE.md)
- [Guia `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_EXECUTION_GUIDE.md)
- [Guia `P0-03` Feed UE real](./P0-03_EU_FEED_EXECUTION_GUIDE.md)
- [Validacao em Staging - Diretorio Federado](../../federated-directory-staging-validation.md)
- [Run Sheet Operacional - Diretorio Federado em Staging](./FEDERATED_DIRECTORY_STAGING_RUN_SHEET.md)

Este documento e a fonte canônica unica para a execucao integrada da janela seria. Evite duplicar a sequencia de comandos em outros guias da mesma pasta.

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

## Matriz Integrada por Frente

| Frente | Owner primario | Gate tecnico minimo | Evidencia minima | Nao promover se |
| --- | --- | --- | --- | --- |
| `P0-01` | `Backend/Auth` | `preflight_oidc_serious_env.py`, `smoke_auth_oidc_mode.py`, `npm run test:e2e:oidc-critical` | bundle OIDC JSON/MD + gate E2E | houver fallback silencioso para `dev auth` |
| `P0-02` | `Compliance/Backend` | `preflight_external_integrations.py`, `make check-compliance-provider-runtime`, `python3 scripts/homologation_external_evidence.py --mode compliance` | checker verde + JSON de homologacao | a credencial real nao estiver exercitada ou faltar artefato revisavel |
| `P0-03` | `Compliance/Backend` | `make rerun-compliance-worker`, `make gate-p0-03-eu-live WINDOW_ID="$WINDOW_ID" REQUEST_ID="$REQUEST_ID"`, `make check-eu-sanctions-window REQUEST_ID="$REQUEST_ID"` | JSON preflight + JSON sync + checker verde | `EU_CONSOLIDATED` nao ficar em `ACTIVE/SUCCESS` |

## Regra de Proveniencia de Secrets

- usar apenas `.env.staging.private`, `GitHub Environment` aprovado ou secret manager/canal controlado
- nunca copiar segredo real para documento versionado, output colado em issue ou artefato publico
- se algum valor ainda estiver em placeholder, a frente correspondente permanece `blocked` ou `ready`, nunca `in_progress`
- registrar somente a existencia da prova e o path do artefato; nunca o segredo em si

## Sequencia Exata de Comandos

Executar na ordem abaixo, sem pular validacoes.

### 1. Gate agregado inicial

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
export WINDOW_ID=stg-YYYY-MM-DD-serious-a
make gate-p0-05-serious-window \
  WINDOW_ID="$WINDOW_ID" \
  MODE=baseline \
  PRIVATE_ENV_FILE=.env.staging.private \
  GOVERNANCE_WEEKLY_DIR=docs/governance-weekly
```

Esse gate canônico encapsula `prepare_staging_window.py --run` e o `postprocess` da janela, preservando payload, sign-off, decision packet, war room e live tracking de forma coerente.

### 2. Validacoes de handoff e placeholders

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private
```

### 3. Execucao `P0-01`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_oidc_serious_env.py
python3 scripts/smoke_auth_oidc_mode.py

cd /home/jistriane/Ontrackchain/github_main/ontrackchain/apps/frontend
npm ci
npm run test:e2e:oidc-critical

cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make run-oidc-readiness-bundle-local \
  WINDOW_ID="$WINDOW_ID" \
  BASE_URL=http://localhost:8080
```

### 4. Execucao `P0-02`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/smoke_runtime.py
python3 scripts/homologation_external_evidence.py --mode compliance
```

### 5. Execucao `P0-03`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make rerun-compliance-worker
export REQUEST_ID="${WINDOW_ID}-eu-check"
make gate-p0-03-eu-live WINDOW_ID="$WINDOW_ID" REQUEST_ID="$REQUEST_ID"
make check-eu-sanctions-window REQUEST_ID="$REQUEST_ID"
```

Esperado ao fim da etapa:

- `EU_CONSOLIDATED.status=ACTIVE`
- `EU_CONSOLIDATED.last_sync_status=SUCCESS`
- `source_url` persistido coerente com o override serio exercitado

### 6. Consolidacao `P0-02 + P0-03`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-04-regulatory-bundle \
  WINDOW_ID="$WINDOW_ID" \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks \
  DOSSIERS_DIR=artifacts/staging/dossiers \
  COMPLIANCE_INTERNAL_BASE_URL=http://localhost:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Esperado ao fim da etapa:

- `readiness.compliance_runtime=ready_for_validation`
- `readiness.eu_window=ready_for_validation`
- `readiness.regulatory_bundle=ready_for_validation`
- `steps.compliance_provider_runtime.request_id` presente
- `steps.compliance_provider_runtime.output_file.kind=compliance_provider_runtime_check`
- `steps.eu_sanctions_window.request_id` presente
- `steps.eu_sanctions_window.output_file.kind=eu_sanctions_window_run`
- `steps.eu_sanctions_window.correlation.source_url_matches_expected=true`

### 6.1 Validacao objetiva do pacote combinado

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/validate_serious_window_artifact.py \
  --window-id "$WINDOW_ID" \
  --checks-dir artifacts/staging/checks \
  --dossiers-dir artifacts/staging/dossiers \
  --scope P0-01,P0-02,P0-03
```

Esperado:

- `status=ok`
- sem erro de `request_id ausente`
- sem erro de `source_url_matches_expected != true`
- sem erro de `readiness.regulatory_bundle.readiness_status`

### 7. Reconciliacao final da governanca

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID="$WINDOW_ID"
```

Se a janela tiver payload consolidado (`ci-artifacts/prepare-staging-window-output.json`), sincronizar a camada executiva com:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Quando a execucao ocorrer pelo workflow hospedado `Staging Serious Window`, essa reconciliacao ja e disparada pelo proprio gate `P0-05`; o comando acima fica como fallback/manual.

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
- `docs/governance-weekly/cycles/<data>/<data>-staging-serious-window-signoff.md`
- `docs/governance-weekly/cycles/<data>/<data>-staging-serious-window-go-no-go-decision-packet.md`

## Reconciliacao Final Obrigatoria

Antes do `go/no-go`, revisar explicitamente:

- `oidc-readiness-bundle.json`: `readiness.readiness_status`, `blockers`, `next_action`
- `regulatory-readiness-bundle.json`: `readiness.regulatory_bundle.readiness_status`
- `regulatory-readiness-bundle.json`: `steps.compliance_provider_runtime.request_id`
- `regulatory-readiness-bundle.json`: `steps.eu_sanctions_window.request_id`
- `regulatory-readiness-bundle.json`: `steps.eu_sanctions_window.correlation.source_url_matches_expected`
- `staging_release_dossier_*.json`: `summaries.regulatory_readiness_bundle.correlation`
- `staging-serious-window-signoff.md`: status executivo coerente com os bundles
- `go-no-go-decision-packet.md`: decisao atual, bloqueadores e criterio de promocao coerentes com os bundles
- `status-snapshot.md` e `consolidated.json`: mesma leitura final da janela

Nao aceitar reconciliacao apenas visual. Os campos acima devem ser comparaveis por valor.

## Rollback Operacional

Se a janela combinada falhar depois de iniciar `P0-02` ou `P0-03`, executar:

1. marcar a janela como `no-go` ou `pending` com bloqueador explicito
2. preservar os artefatos ja gerados, sem sobrescrever o `window_id`
3. nao rerodar a mesma janela com novos secrets sem registrar nova tentativa ou novo `window_id`
4. manter `P0-04` em `ready` ou `blocked`, nunca promover manualmente
5. registrar no snapshot:
   - ultimo step valido
   - correlator invalido ou ausente
   - owner da correcao
   - criterio objetivo para nova tentativa

Rollback especifico:

- se `P0-02` falhar: preservar `request_id` do compliance runtime e homologacao, sem descartar o artifact
- se `P0-03` falhar: preservar `request_id` da janela UE e os JSONs `preflight/sync`
- se `P0-04` falhar por correlacao: corrigir correlators e rerodar o bundle, nao reclassificar manualmente o status

## Criterio Objetivo de Sign-Off

Declarar a janela apta a `sign-off` somente quando todos forem verdadeiros:

- [ ] gate agregado inicial retornou `status=ok`
- [ ] `P0-01` sem fallback para `dev auth`
- [ ] bundle OIDC existe e esta revisavel
- [ ] `P0-02` tem evidência de provider pronto e homologacao externa preservada
- [ ] `P0-03` tem os dois JSONs da janela UE
- [ ] `EU_CONSOLIDATED` esta em `ACTIVE/SUCCESS`
- [ ] bundle regulatorio existe e esta revisavel
- [ ] bundle regulatorio oficial esta em `readiness.regulatory_bundle=ready_for_validation`
- [ ] `request_id` de `P0-02` e `P0-03` estao preservados nos artefatos executivos
- [ ] `source_url_matches_expected=true` para a janela UE
- [ ] a governanca foi reprocessada para o mesmo `window_id`
- [ ] nao existe bloqueador `WR-*` aberto sem waiver formal
- [ ] owner e accountable revisaram os artefatos

## Evidencia Minima a Registrar na Governanca

- `window_id`
- owners nominais das tres trilhas
- paths reais de cada JSON/MD gerado
- resultado objetivo dos gates (`ok`, `failed`, `blocked`)
- decisao final `go`, `go_with_exception` ou `no-go`
- bloqueadores residuais com owner e data alvo

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
