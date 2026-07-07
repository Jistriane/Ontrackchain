# Run Sheet Operacional - `P0-01` OIDC + MFA serio

## Uso

Preencher e executar esta folha durante a janela real de `P0-01`. Ela existe para reduzir ambiguidade operacional, registrar o owner ativo, confirmar a configuracao seria sem expor segredos e listar os artefatos que precisam ser preservados.

Complementa o [Guia de Execucao Assistida de `P0-01` OIDC + MFA serio](./P0-01_OIDC_MFA_EXECUTION_GUIDE.md).

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `owner_ativo`: `Backend/Auth`
- `apoio`: `Platform/SRE`
- `facilitador`: `preencher`
- `bridge`: `preencher`
- `run_url`: `preencher`

## Checklist de Prontidao

- [ ] secrets reais de `OIDC` e `MFA` disponiveis fora do repositorio
- [ ] `AUTH_MODE=oidc`
- [ ] `DEV_AUTH_ENABLED=false`
- [ ] `NEXT_PUBLIC_AUTH_MODE=oidc`
- [ ] `NEXT_PUBLIC_DEV_AUTH_ENABLED=false`
- [ ] `OIDC_ISSUER_URL` preenchido com endpoint real
- [ ] `OIDC_JWKS_URL` preenchido com endpoint real
- [ ] `KEYCLOAK_B2B_CLIENT_SECRET` preenchido
- [ ] `docs/staging-env-ownership.md` com `Auth/OIDC.date` e `Auth/OIDC.status` fora de `pending`
- [ ] politica de `MFA` da janela definida

## Ordem de Execucao

### 1. Validar handoff e placeholders

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python3 scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Resultado esperado:

- `Auth/OIDC` sem `pending`
- nenhum placeholder critico remanescente para OIDC/MFA

### 2. Preflight OIDC serio

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_oidc_serious_env.py
```

Registrar:

- `preflight_status`: `preencher`
- observacao curta: `preencher`

### 3. Smoke auth serio

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/smoke_auth_oidc_mode.py
```

Registrar:

- `smoke_status`: `preencher`
- observacao curta: `preencher`

### 4. Gate critico do frontend

```bash
cd /home/jistriane/Ontrackchain/ontrackchain/apps/frontend
npm ci
npm run test:e2e:oidc-critical
```

Registrar:

- `frontend_gate_status`: `preencher`
- observacao curta: `preencher`

### 5. Bundle OIDC

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-oidc-readiness-bundle-local \
  WINDOW_ID=<window_id> \
  BASE_URL=http://localhost:8080
```

Registrar:

- `bundle_json`: `preencher`
- `bundle_md`: `preencher`

### 6. Homologacao externa quando aplicavel

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/homologation_external_evidence.py --mode both --include-oidc-legal-report
```

Registrar somente se aplicavel:

- `homologation_status`: `preencher`
- `homologation_json`: `preencher`
- `homologation_manifest`: `preencher`

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

- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- `artifacts/homologation/<arquivo>.json`, quando aplicavel
- `artifacts/homologation/<arquivo>.manifest.json`, quando aplicavel
- relatorio do `oidc-critical`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-war-room-action-plan.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot-delta.md`
- `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Gate de Saida

Marcar a trilha como pronta para validacao somente se todos estiverem verdadeiros:

- [ ] preflight OIDC serio verde
- [ ] smoke auth serio verde
- [ ] gate critico do frontend executado
- [ ] bundle OIDC preservado
- [ ] governanca reprocessada
- [ ] owner humano revisou a evidencia

## Resultado da Janela

- decisao sugerida: `preencher`
- motivo resumido: `preencher`
- proximo passo: `preencher`
- accountable: `preencher`
