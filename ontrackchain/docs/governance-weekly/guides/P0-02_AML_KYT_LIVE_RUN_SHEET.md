# Run Sheet Operacional - `P0-02` AML/KYT live

## Uso

Preencher e executar esta folha durante a janela real de `P0-02`. Ela existe para reduzir ambiguidade operacional, registrar o owner ativo, confirmar os segredos sem expor valores e listar os artefatos que precisam ser preservados.

Complementa o [Guia de Execucao Assistida de `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_EXECUTION_GUIDE.md).

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `owner_ativo`: `Compliance/Backend`
- `apoio`: `Security`
- `facilitador`: `preencher`
- `bridge`: `preencher`
- `run_url`: `preencher`

## Checklist de Prontidao

- [ ] credencial real do provider disponivel fora do repositorio
- [ ] `COMPLIANCE_TRM_ENABLED=true` aplicado no ambiente privado
- [ ] `COMPLIANCE_TRM_SCREENING_URL` preenchido
- [ ] `COMPLIANCE_TRM_API_KEY` preenchido
- [ ] `COMPLIANCE_TRM_API_KEY_HEADER` confirmado
- [ ] `COMPLIANCE_TRM_API_KEY_PREFIX` confirmado
- [ ] `COMPLIANCE_TRM_TIMEOUT_MS` confirmado
- [ ] `COMPLIANCE_TRM_MAX_RETRIES` confirmado
- [ ] `docs/staging-env-ownership.md` com `Compliance/AML.date` e `Compliance/AML.status` fora de `pending`
- [ ] `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live`
- [ ] `ONTRACKCHAIN_EXPECT_RPC_MODE=disabled`

## Ordem de Execucao

### 1. Validar handoff e placeholders

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Resultado esperado:

- `Compliance/AML` sem `pending`
- nenhum placeholder critico remanescente para TRM

### 2. Preflight externo

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_external_integrations.py
```

Registrar:

- `status`: `preencher`
- observacao curta: `preencher`

### 3. Runtime gate AML/KYT

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-02-aml-live \
  PRIVATE_ENV_FILE=.env.staging.private \
  COMPLIANCE_INTERNAL_BASE_URL=http://localhost:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Registrar:

- `provider_readiness`: `preencher`
- `operating_mode`: `preencher`
- `provider_status`: `preencher`
- `request_id` principal: `preencher`

Se a execucao for hospedada via GitHub Actions, preencher tambem:

- `workflow`: `P0-02 AML Live Gate`
- `run_url`: `preencher`
- `artifact_name`: `p0-02-aml-live-<window_id>`

### 4. Smoke funcional

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/smoke_runtime.py
```

Registrar:

- `smoke_status`: `preencher`
- observacao curta: `preencher`

### 5. Evidencia externa

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/homologation_external_evidence.py --mode compliance
```

Registrar:

- `homologation_status`: `preencher`
- `homologation_json`: `preencher`
- `homologation_manifest`: `preencher`

### 6. Bundle regulatorio se `P0-03` estiver junto

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

- `ci-artifacts/p0-02-aml-live-gate.log`, quando a execucao ocorrer via GitHub Actions
- `ci-artifacts/p0-02/p0-02-preflight.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-02/p0-02-compliance-runtime.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-02/p0-02-smoke-runtime.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-02/p0-02-gate-summary.json`, quando a execucao ocorrer via gate canônico novo
- `ci-artifacts/p0-02-homologation.log`, quando `run_homologation=true` no workflow hospedado
- `ci-artifacts/p0-02-docker-compose-ps.txt`, quando a execucao ocorrer via GitHub Actions
- `ci-artifacts/p0-02-docker-compose-logs.txt`, quando a execucao ocorrer via GitHub Actions
- `artifacts/homologation/<arquivo>.json`
- `artifacts/homologation/<arquivo>.manifest.json`
- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`, quando aplicavel
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`, quando aplicavel
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-war-room-action-plan.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot-delta.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Gate de Saida

Marcar a trilha como pronta para validacao somente se todos estiverem verdadeiros:

- [ ] preflight externo verde
- [ ] runtime gate verde
- [ ] homologacao externa preservada
- [ ] `request_id` correlacionavel
- [ ] governanca reprocessada
- [ ] owner humano revisou a evidencia

## Resultado da Janela

- decisao sugerida: `preencher`
- motivo resumido: `preencher`
- proximo passo: `preencher`
- accountable: `preencher`
