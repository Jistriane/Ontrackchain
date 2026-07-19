# Run Sheet Datada - Primeira Janela Seria Combinada `stg-2026-07-13-a`

## Objetivo

Instanciar a primeira tentativa combinada real de `P0-02 + P0-03` no ciclo `2026-07-13`, com campos prontos para preenchimento humano durante o war room.

Use esta folha junto com:

- [Run Sheet Preenchivel da Primeira Janela Combinada](../../guides/FIRST_COMBINED_SERIOUS_WINDOW_RUN_SHEET.md)
- [Checklist Executivo da Primeira Janela Combinada `P0-02 + P0-03`](../../guides/FIRST_COMBINED_SERIOUS_WINDOW_EXECUTIVE_CHECKLIST.md)
- [Governança Semanal Operacional 2026-07-13](./2026-07-13-weekly-governance-operational.md)
- [Rascunho de Execucao por Evidencia 2026-07-13](./2026-07-13-maturity-evidence-execution-draft.md)
- [Bridge Quick-Fill `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-bridge-quick-fill.md)

## Identificacao da Tentativa

- `window_id`: `stg-2026-07-13-a`
- `modo`: `dress_rehearsal_controlado`
- `data_utc`: `preencher`
- `run_url`: `preencher`
- `facilitador`: `Release Manager Tecnico`
- `release_manager_tecnico`: `preencher`
- `canal_principal`: `preencher`
- `bridge_principal`: `preencher`
- `hora_inicio_utc`: `preencher`
- `hora_limite_go_no_go_utc`: `preencher`
- `data_alvo_operacional`: `2026-07-17`

## Owners Online

| Frente | Owner ativo | Backup/Escalacao | Canal | Online? |
| --- | --- | --- | --- | --- |
| Gate agregado | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-02` AML/KYT | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-03` Feed UE | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-04` consolidado | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| Governanca / sign-off | `preencher` | `preencher` | `preencher` | `sim ou nao` |

## Preenchimento Guiado por Papel

| Frente | Papel sugerido | O que precisa estar preenchido antes do ack | Origem esperada |
| --- | --- | --- | --- |
| Gate agregado | `Release Manager Tecnico` | `facilitador`, `canal_principal`, `bridge_principal`, `hora_inicio_utc`, `hora_limite_go_no_go_utc` | war room + tracking |
| `P0-02` AML/KYT | `Compliance/Backend Lead` | `preflight_status`, `runtime_status`, `homologation_status`, `compliance_request_id`, `homologation_request_id` | checker AML/KYT + homologacao |
| `P0-03` Feed UE | `Compliance/Ops Lead` | `runner_status`, `checker_status`, `eu_request_id`, `eu_consolidated_status`, `source_url_matches_expected` | janela UE + checker |
| `P0-04` consolidado | `Platform/SRE` | `compliance_readiness`, `eu_readiness`, `regulatory_bundle_readiness`, `artifact_validation_status` | bundle regulatorio + validador |
| Governanca / sign-off | `Arquitetura / Governanca` | `snapshot_md`, `consolidated_json`, `signoff_md`, `decisao_final`, `proximo_passo` | refresh do war room + sign-off |

## Handoff Minimo por Dominio

- `Compliance/AML`: confirmar credencial real, owner online, status do checker e correlator da homologacao
- `Compliance/Backend`: confirmar URL tokenizada real, owner online, status do runner/checker e correlator da janela UE
- `Platform/SRE`: confirmar bundle regulatorio, validacao final e readiness consolidado
- `Security/Auth`: registrar explicitamente se `P0-01` permanece apenas como risco residual ou se houve artefato novo revisavel
- `Governanca`: registrar a decisao da tentativa e o criterio objetivo para rerun ou promocao

## Warmup `T-30 min`

- [ ] `window_id` confirmado no war room
- [ ] bridge principal ativa
- [ ] owners online confirmados
- [ ] `.env.staging.private` revisado fora do repositorio
- [ ] `docs/staging-env-ownership.md` sem pendencias impeditivas do escopo

Registrar:

- decisao do warmup: `seguir | segurar | abortar`
- motivo curto: `preencher`

## Gate Agregado `T-15 min`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-05-serious-window \
  WINDOW_ID=stg-2026-07-13-a \
  MODE=baseline \
  PRIVATE_ENV_FILE=.env.staging.private \
  GOVERNANCE_WEEKLY_DIR=docs/governance-weekly
```

Registrar:

- `prepare_status`: `preencher`
- `ownership_check`: `ok | failed`
- `placeholder_check`: `ok | failed`
- `preflight_oidc`: `ok | failed`
- `preflight_external`: `ok | failed`
- `prepare_output_json`: `ci-artifacts/prepare-staging-window-output.json | preencher`

## Execucao `P0-02`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/homologation_external_evidence.py --mode compliance
```

Registrar:

- `p0_02_status`: `pending | blocked | ready_for_validation | done`
- `preflight_status`: `preencher`
- `runtime_status`: `preencher`
- `homologation_status`: `preencher`
- `compliance_request_id`: `preencher`
- `homologation_request_id`: `preencher`
- `request_id_match`: `true | false`
- `runtime_output`: `preencher`
- `homologation_json`: `preencher`
- `homologation_manifest`: `preencher`

## Execucao `P0-03`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make rerun-compliance-worker
export REQUEST_ID="stg-2026-07-13-a-eu-check"
make gate-p0-03-eu-live WINDOW_ID=stg-2026-07-13-a REQUEST_ID="$REQUEST_ID"
make check-eu-sanctions-window REQUEST_ID="$REQUEST_ID"
```

Registrar:

- `p0_03_status`: `pending | blocked | ready_for_validation | done`
- `worker_status`: `preencher`
- `runner_status`: `preencher`
- `checker_status`: `preencher`
- `eu_request_id`: `preencher`
- `eu_consolidated_status`: `preencher`
- `last_sync_status`: `preencher`
- `source_url_matches_expected`: `true | false`
- `eu_preflight_json`: `artifacts/staging/checks/stg-2026-07-13-a-eu-sanctions-preflight.json | preencher`
- `eu_sync_json`: `artifacts/staging/checks/stg-2026-07-13-a-eu-sanctions-sync.json | preencher`

## Consolidacao `P0-04`

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-04-regulatory-bundle \
  WINDOW_ID=stg-2026-07-13-a \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks \
  DOSSIERS_DIR=artifacts/staging/dossiers \
  COMPLIANCE_INTERNAL_BASE_URL=http://compliance-api:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/validate_serious_window_artifact.py \
  --window-id stg-2026-07-13-a \
  --checks-dir artifacts/staging/checks \
  --dossiers-dir artifacts/staging/dossiers \
  --scope P0-01,P0-02,P0-03
```

Registrar:

- `p0_04_status`: `pending | blocked | ready | ready_for_validation | done`
- `compliance_readiness`: `preencher`
- `eu_readiness`: `preencher`
- `regulatory_bundle_readiness`: `preencher`
- `artifact_validation_status`: `preencher`
- `bundle_json`: `artifacts/staging/checks/stg-2026-07-13-a-regulatory-readiness-bundle.json | preencher`
- `bundle_md`: `artifacts/staging/dossiers/stg-2026-07-13-a-regulatory-readiness-bundle.md | preencher`
- `dossier_json`: `artifacts/staging/dossiers/stg-2026-07-13-a-dossier.json | preencher`

## Reconciliacao Final

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-13-a
```

Registrar:

- `snapshot_md`: `preencher`
- `snapshot_delta_md`: `preencher`
- `consolidated_json`: `preencher`
- `signoff_md`: `preencher`
- `war_room_status`: `preencher`
- `tracking_status`: `preencher`
- `snapshot_vs_signoff_match`: `true | false`
- `consolidated_vs_snapshot_match`: `true | false`

## Decisao Final

- `decisao_final`: `go | go_with_exception | pending | no-go`
- `motivo_objetivo`: `preencher`
- `maior_bloqueio`: `preencher`
- `owner_da_escalacao`: `preencher`
- `proximo_passo`: `preencher`
- `prazo_para_nova_tentativa`: `preencher`

## Regra de Rerun

- [ ] mesma tentativa pode ser reaproveitada
- [ ] novo `window_id` obrigatorio

Motivo:

- `preencher`

## Correlators Finais

- `compliance_request_id`: `preencher`
- `homologation_request_id`: `preencher`
- `eu_request_id`: `preencher`
- `source_url_matches_expected`: `true | false`
- `artifact_validation_status`: `preencher`

## Artefatos Esperados Deste Ciclo

- [ ] `artifacts/staging/checks/stg-2026-07-13-a-regulatory-readiness-bundle.json`
- [ ] `artifacts/staging/dossiers/stg-2026-07-13-a-regulatory-readiness-bundle.md`
- [ ] `artifacts/staging/dossiers/stg-2026-07-13-a-dossier.json`
- [ ] `artifacts/staging/checks/stg-2026-07-13-a-eu-sanctions-preflight.json`
- [ ] `artifacts/staging/checks/stg-2026-07-13-a-eu-sanctions-sync.json`
- [ ] `docs/governance-weekly/generated/windows/stg-2026-07-13-a/stg-2026-07-13-a-status-snapshot.md`
- [ ] `docs/governance-weekly/generated/windows/stg-2026-07-13-a/stg-2026-07-13-a-status-snapshot-delta.md`
- [ ] `docs/governance-weekly/generated/windows/stg-2026-07-13-a/stg-2026-07-13-a-consolidated.json`
