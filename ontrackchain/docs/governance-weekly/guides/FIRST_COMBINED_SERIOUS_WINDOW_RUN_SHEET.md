# Run Sheet Preenchivel - Primeira Janela Seria Combinada `P0-02 + P0-03`

## Uso

Preencher esta folha durante a primeira execucao combinada real de `P0-02` e `P0-03`.

Ela existe para:

- registrar owners presentes e canais ativos
- manter checkpoints curtos sem reabrir varios documentos
- concentrar decisao, correlators e paths dos artefatos
- reduzir erro operacional durante `go/no-go`

Use esta folha junto com:

- [Checklist Executivo da Primeira Janela Combinada `P0-02 + P0-03`](./FIRST_COMBINED_SERIOUS_WINDOW_EXECUTIVE_CHECKLIST.md)
- [Pacote Final de Execucao - Janela Seria Integrada](./SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md)
- [Guia `P0-04` Bundle Regulatorio Oficial](./P0-04_REGULATORY_BUNDLE_EXECUTION_GUIDE.md)

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `modo`: `dress_rehearsal_controlado | go_no_go_formal`
- `run_url`: `preencher`
- `facilitador`: `preencher`
- `release_manager_tecnico`: `preencher`
- `canal_principal`: `preencher`
- `bridge_principal`: `preencher`
- `hora_inicio_utc`: `preencher`
- `hora_limite_go_no_go_utc`: `preencher`

## Owners Online

| Frente | Owner ativo | Backup/Escalacao | Canal | Online? |
| --- | --- | --- | --- | --- |
| Gate agregado | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-02` AML/KYT | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-03` Feed UE | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `P0-04` consolidado | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| Governanca / sign-off | `preencher` | `preencher` | `preencher` | `sim ou nao` |

## Checkpoint `T-30 min`

- [ ] `window_id` reservado para esta tentativa
- [ ] bridge principal confirmada
- [ ] owners online confirmados
- [ ] `.env.staging.private` revisado fora do repositorio
- [ ] war room carregado com estado inicial

Registrar:

- decisao do checkpoint: `seguir | segurar | abortar`
- motivo curto: `preencher`

## Checkpoint `T-15 min` - Gate Agregado

Comando:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/prepare_staging_window.py \
  --window-id "$WINDOW_ID" \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

Registrar:

- `prepare_status`: `preencher`
- `ownership_check`: `ok | failed`
- `placeholder_check`: `ok | failed`
- `preflight_oidc`: `ok | failed`
- `preflight_external`: `ok | failed`
- `output_json`: `preencher`

Decisao:

- [ ] seguir para `P0-02`
- [ ] abortar a janela como `no-go`

## `P0-02` AML/KYT

### Execucao `P0-02`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
python3 scripts/homologation_external_evidence.py --mode compliance
```

### Registro `P0-02`

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
- `observacao_curta`: `preencher`

### Gate de Saida `P0-02`

- [ ] runtime AML/KYT verde
- [ ] homologacao externa preservada
- [ ] `request_id` presente
- [ ] `request_id` comparavel com a homologacao

## `P0-03` Feed UE

### Execucao `P0-03`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make rerun-compliance-worker
make run-eu-sanctions-window-local WINDOW_ID="$WINDOW_ID"
make check-eu-sanctions-window
```

### Registro `P0-03`

- `p0_03_status`: `pending | blocked | ready_for_validation | done`
- `worker_status`: `preencher`
- `runner_status`: `preencher`
- `checker_status`: `preencher`
- `eu_request_id`: `preencher`
- `eu_consolidated_status`: `preencher`
- `last_sync_status`: `preencher`
- `source_url_matches_expected`: `true | false`
- `eu_preflight_json`: `preencher`
- `eu_sync_json`: `preencher`
- `checker_output`: `preencher`
- `observacao_curta`: `preencher`

### Gate de Saida `P0-03`

- [ ] `EU_CONSOLIDATED=ACTIVE`
- [ ] `last_sync_status=SUCCESS`
- [ ] `request_id` presente
- [ ] `source_url_matches_expected=true`

## `P0-04` Bundle Regulatorio Oficial

### Execucao `P0-04`

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID="$WINDOW_ID"
python3 scripts/validate_serious_window_artifact.py \
  --window-id "$WINDOW_ID" \
  --checks-dir artifacts/staging/checks \
  --dossiers-dir artifacts/staging/dossiers \
  --scope P0-01,P0-02,P0-03
```

### Registro `P0-04`

- `p0_04_status`: `pending | blocked | ready | ready_for_validation | done`
- `compliance_readiness`: `preencher`
- `eu_readiness`: `preencher`
- `regulatory_bundle_readiness`: `preencher`
- `artifact_validation_status`: `preencher`
- `bundle_json`: `preencher`
- `bundle_md`: `preencher`
- `dossier_json`: `preencher`
- `validation_output`: `preencher`
- `observacao_curta`: `preencher`

### Gate de Saida `P0-04`

- [ ] `readiness.compliance_runtime=ready_for_validation`
- [ ] `readiness.eu_window=ready_for_validation`
- [ ] `readiness.regulatory_bundle=ready_for_validation`
- [ ] validador de artifact com `status=ok`

## Reconciliacao Final

Comando:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID="$WINDOW_ID"
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

## Artefatos Finais Confirmados

- [ ] `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- [ ] `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- [ ] `artifacts/staging/dossiers/<window_id>-dossier.json`
- [ ] `artifacts/homologation/<arquivo>.json`
- [ ] `artifacts/homologation/<arquivo>.manifest.json`
- [ ] `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- [ ] `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- [ ] `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot.md`
- [ ] `docs/governance-weekly/generated/windows/<window_id>/<window_id>-status-snapshot-delta.md`
- [ ] `docs/governance-weekly/generated/windows/<window_id>/<window_id>-consolidated.json`

## Correlators Finais

- `compliance_request_id`: `preencher`
- `homologation_request_id`: `preencher`
- `eu_request_id`: `preencher`
- `source_url_matches_expected`: `true | false`
- `artifact_validation_status`: `preencher`

## Assinatura Operacional

- `facilitador`: `preencher`
- `owner_p0_02`: `preencher`
- `owner_p0_03`: `preencher`
- `release_manager_tecnico`: `preencher`
- `horario_encerramento_utc`: `preencher`
