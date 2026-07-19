# Run Sheet Operacional - `P0-03` Feed UE real

## Uso

Preencher e executar esta folha durante a janela real de `P0-03`. Ela existe para reduzir ambiguidade operacional, registrar o owner ativo, confirmar o override do feed sem expor o valor e listar os artefatos que precisam ser preservados.

Complementa o [Guia de Execucao Assistida de `P0-03` Feed UE real](./P0-03_EU_FEED_EXECUTION_GUIDE.md).

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `owner_ativo`: `Compliance/Backend`
- `apoio`: `Security`
- `facilitador`: `preencher`
- `bridge`: `preencher`
- `run_url`: `preencher`

## Checklist de Prontidao

- [ ] URL XML tokenizada oficial da UE disponivel fora do repositorio
- [ ] `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` aplicado no ambiente privado
- [ ] `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` usa `https`
- [ ] `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` contem `token=`
- [ ] `DATABASE_URL` aponta para o banco do ambiente-alvo
- [ ] `docs/staging-env-ownership.md` com `Compliance/AML.date` e `Compliance/AML.status` fora de `pending`
- [ ] observabilidade do `compliance-worker` disponivel

## Ordem de Execucao

### 1. Validar handoff e placeholders

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Resultado esperado:

- `Compliance/AML` sem `pending`
- nenhum placeholder critico remanescente para feed UE

### 2. Preflight externo

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_external_integrations.py
```

Registrar:

- `status`: `preencher`
- observacao curta: `preencher`

### 3. Reexecutar worker

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make rerun-compliance-worker
```

Registrar:

- `worker_status`: `preencher`
- observacao curta: `preencher`

### 4. Runner da janela UE

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-03-eu-live \
  WINDOW_ID=<window_id> \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks
```

Registrar:

- `runner_status`: `preencher`
- `eu_preflight_json`: `preencher`
- `eu_sync_json`: `preencher`
- `eu_request_id`: `preencher`

### 5. Checker pos-sync

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make check-eu-sanctions-window REQUEST_ID=<eu_request_id>
```

Registrar:

- `checker_status`: `preencher`
- `eu_consolidated_status`: `preencher`
- `last_sync_status`: `preencher`
- `source_url_match`: `preencher`

Se a execucao for hospedada via GitHub Actions, preencher tambem:

- `workflow`: `P0-03 EU Live Gate`
- `run_url`: `preencher`
- `artifact_name`: `p0-03-eu-live-<window_id>`

### 6. Bundle regulatorio se `P0-02` estiver junto

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-04-regulatory-bundle \
  WINDOW_ID=<window_id> \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks \
  DOSSIERS_DIR=artifacts/staging/dossiers \
  COMPLIANCE_INTERNAL_BASE_URL=http://compliance-api:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Registrar somente se aplicavel:

- `bundle_json`: `preencher`
- `bundle_md`: `preencher`

### 7. Reconciliar governanca

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Registrar:

- `snapshot_status`: `preencher`
- `delta_status`: `preencher`
- `consolidated_json`: `preencher`

## Artefatos a Preservar

- `ci-artifacts/p0-03-eu-live-gate.log`, quando a execucao ocorrer via GitHub Actions
- `ci-artifacts/p0-03/p0-03-preflight.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-03/p0-03-eu-window.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-03/p0-03-eu-checker.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-03/p0-03-gate-summary.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-03-docker-compose-ps.txt`, quando a execucao ocorrer via GitHub Actions
- `ci-artifacts/p0-03-docker-compose-logs.txt`, quando a execucao ocorrer via GitHub Actions
- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`, quando aplicavel
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`, quando aplicavel
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-war-room-action-plan.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot-delta.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Gate de Saida

Marcar a trilha como pronta para validacao somente se todos estiverem verdadeiros:

- [ ] preflight externo verde
- [ ] worker reexecutado com a env correta
- [ ] `eu-sanctions-preflight.json` preservado
- [ ] `eu-sanctions-sync.json` preservado
- [ ] checker pos-sync verde
- [ ] `source_url` persistido igual ao override
- [ ] governanca reprocessada
- [ ] owner humano revisou a evidencia

## Resultado da Janela

- decisao sugerida: `preencher`
- motivo resumido: `preencher`
- proximo passo: `preencher`
- accountable: `preencher`
