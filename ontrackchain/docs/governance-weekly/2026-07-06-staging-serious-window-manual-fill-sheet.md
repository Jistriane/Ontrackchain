# Folha de Preenchimento Manual — `stg-2026-07-06-a`

## Objetivo

Concentrar, em uma unica folha, todos os placeholders operacionais que precisam ser substituidos para a janela `stg-2026-07-06-a` sair de `no-go`, sem obrigar o time a navegar entre varios artefatos antes do primeiro rerun.

Use esta folha junto com:

- [War Room da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-war-room.md)
- [Tracking ao Vivo da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-live-tracking.md)
- [Runbook do Primeiro Disparo](../first-serious-window-first-dispatch-runbook.md)
- [Checklist de Provisionamento por Owner](../staging-serious-window-owner-provisioning-checklist.md)

## Regra de Uso

- preencher nomes, canais e bridges diretamente nos artefatos versionados
- provisionar secrets e URLs reais apenas em vault, GitHub Environment ou canal seguro
- marcar um owner como concluido apenas quando:
  - os placeholders operacionais do owner tiverem sido substituidos
  - os placeholders reais do dominio tiverem saído do `.env.staging.private`
  - a validacao minima do dominio estiver verde

## Ordem de Execucao

1. `Gate Agregado da Janela` e placeholders transversais
2. `Platform/Operations`
3. `Auth/OIDC`
4. `Investigation/RPC`
5. `Compliance/AML`
6. rerun do gate agregado

## 1. Gate Agregado da Janela

Owner de preenchimento:

- `Arquiteto/Responsavel Tecnico`

Placeholders a substituir nos artefatos vivos:

- `<preencher_nome_facilitador_online>`
- `<preencher_canal_principal_war_room>`
- `<preencher_bridge_go_no_go>`
- `<preencher_HH:MMZ>`
- `<preencher_nome_owner_backup_go_no_go>`

Arquivos onde substituir primeiro:

- `docs/governance-weekly/2026-07-06-staging-serious-window-war-room.md`
- `docs/governance-weekly/2026-07-06-staging-serious-window-live-tracking.md`

Checklist rapido:

- [ ] facilitador online definido
- [ ] canal principal do war room definido
- [ ] bridge principal de escalacao definida
- [ ] hora do proximo checkpoint definida
- [ ] backup do gate agregado definido

Evidencia minima:

- `war room` e `tracking` sem placeholders transversais

## 2. Platform/Operations

Owner de preenchimento:

- `Platform/SRE`

Placeholders operacionais a substituir:

- `<preencher_nome_owner_online_platform>`
- `<preencher_nome_owner_backup_platform>`
- `<preencher_nome_owner_escalacao_platform>`
- `<preencher_slack_ou_teams_platform>`
- `<preencher_bridge_platform>`

Placeholders reais do dominio:

- `POSTGRES_PASSWORD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Arquivos e campos que devem refletir o owner:

- `war room`: owner primario, backup/escalacao, canal de contato, bloqueador `WR-01`
- `tracking`: responsavel online, canal de contato, bridge de escalacao
- `docs/staging-env-ownership.md`: `Data` e `Status`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Evidencia minima:

- JSON do handoff sem `pending` para `Platform/Operations`
- JSON de placeholders sem ocorrencias do dominio

Checklist rapido:

- [ ] owner online informado
- [ ] backup informado
- [ ] bridge informada
- [ ] segredos base provisionados
- [ ] handoff fora de `pending`

## 3. Auth/OIDC

Owner de preenchimento:

- `Backend/Auth`

Placeholders operacionais a substituir:

- `<preencher_nome_owner_online_auth>`
- `<preencher_nome_owner_backup_auth>`
- `<preencher_nome_owner_escalacao_auth>`
- `<preencher_slack_ou_teams_auth>`
- `<preencher_bridge_auth>`

Placeholders reais do dominio:

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`

Condicional:

- `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` apenas se `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`

Arquivos e campos que devem refletir o owner:

- `war room`: owner primario, backup/escalacao, canal de contato, bloqueador `WR-02`
- `tracking`: responsavel online, canal de contato, bridge de escalacao
- `docs/staging-env-ownership.md`: `Data` e `Status`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_oidc_serious_env.py
```

Evidencia minima:

- JSON do handoff sem `pending` para `Auth/OIDC`
- output verde do `preflight_oidc_serious_env.py`

Checklist rapido:

- [ ] owner online informado
- [ ] backup informado
- [ ] bridge informada
- [ ] secrets OIDC provisionados
- [ ] handoff fora de `pending`
- [ ] preflight OIDC verde

## 4. Investigation/RPC

Owner de preenchimento:

- `Backend Core`

Placeholders operacionais a substituir:

- `<preencher_nome_owner_online_rpc>`
- `<preencher_nome_owner_backup_rpc>`
- `<preencher_nome_owner_escalacao_rpc>`
- `<preencher_slack_ou_teams_rpc>`
- `<preencher_bridge_rpc>`

Placeholders reais do dominio:

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

Arquivos e campos que devem refletir o owner:

- `war room`: owner primario, backup/escalacao, canal de contato, bloqueador `WR-03`
- `tracking`: responsavel online, canal de contato, bridge de escalacao
- `docs/staging-env-ownership.md`: `Data` e `Status`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_external_integrations.py
```

Evidencia minima:

- JSON do handoff sem `pending` para `Investigation/RPC`
- output do preflight externo coerente com `ONTRACKCHAIN_EXPECT_RPC_MODE`

Checklist rapido:

- [ ] owner online informado
- [ ] backup informado
- [ ] bridge informada
- [ ] endpoints RPC provisionados
- [ ] handoff fora de `pending`
- [ ] preflight externo coerente

## 5. Compliance/AML

Owner de preenchimento:

- `Compliance/Backend`

Placeholders operacionais a substituir:

- `<preencher_nome_owner_online_compliance>`
- `<preencher_nome_owner_backup_compliance>`
- `<preencher_nome_owner_escalacao_compliance>`
- `<preencher_slack_ou_teams_compliance>`
- `<preencher_bridge_compliance>`

Placeholders reais do dominio:

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Arquivos e campos que devem refletir o owner:

- `war room`: owner primario, backup/escalacao, canal de contato, bloqueador `WR-04`
- `tracking`: responsavel online, canal de contato, bridge de escalacao
- `docs/staging-env-ownership.md`: `Data` e `Status`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
```

Validacao adicional quando `EU_CONSOLIDATED` estiver no escopo:

```bash
make run-eu-sanctions-window-local WINDOW_ID=stg-2026-07-06-a
```

Evidencia minima:

- JSON do handoff sem `pending` para `Compliance/AML`
- output verde do preflight externo
- output verde do runtime AML/KYT
- JSONs `stg-2026-07-06-a-eu-sanctions-preflight.json` e `stg-2026-07-06-a-eu-sanctions-sync.json`, quando aplicavel

Checklist rapido:

- [ ] owner online informado
- [ ] backup informado
- [ ] bridge informada
- [ ] credenciais AML/KYT provisionadas
- [ ] URL tokenizada da UE provisionada, quando aplicavel
- [ ] handoff fora de `pending`
- [ ] runtime AML/KYT verde

## Gate Final

Quando todos os grupos acima estiverem preenchidos:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-2026-07-06-a \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

Seguir apenas se o resultado for:

- `status=ok`

Se o gate agregado ficar verde, a janela passa a ser elegivel para:

```bash
make run-serious-window-local WINDOW_ID=stg-2026-07-06-a MODE=baseline
```
