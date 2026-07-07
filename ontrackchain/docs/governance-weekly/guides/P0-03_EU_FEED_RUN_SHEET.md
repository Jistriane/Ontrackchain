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
cd /home/jistriane/Ontrackchain/ontrackchain
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Resultado esperado:

- `Compliance/AML` sem `pending`
- nenhum placeholder critico remanescente para feed UE

### 2. Preflight externo

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python scripts/preflight_external_integrations.py
```

Registrar:

- `status`: `preencher`
- observacao curta: `preencher`

### 3. Reexecutar worker

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make rerun-compliance-worker
```

Registrar:

- `worker_status`: `preencher`
- observacao curta: `preencher`

### 4. Runner da janela UE

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-eu-sanctions-window-local WINDOW_ID=<window_id>
```

Registrar:

- `runner_status`: `preencher`
- `eu_preflight_json`: `preencher`
- `eu_sync_json`: `preencher`

### 5. Checker pos-sync

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make check-eu-sanctions-window
```

Registrar:

- `checker_status`: `preencher`
- `eu_consolidated_status`: `preencher`
- `last_sync_status`: `preencher`
- `source_url_match`: `preencher`

### 6. Bundle regulatorio se `P0-02` estiver junto

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID=<window_id>
```

Registrar somente se aplicavel:

- `bundle_json`: `preencher`
- `bundle_md`: `preencher`

### 7. Reconciliar governanca

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Registrar:

- `snapshot_status`: `preencher`
- `delta_status`: `preencher`
- `consolidated_json`: `preencher`

## Artefatos a Preservar

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
