# Checklist Executivo - Primeira Janela Seria Combinada `P0-02 + P0-03`

## Objetivo

Dar ao facilitador e ao `Release Manager Tecnico` uma folha curta de comando para a primeira janela seria combinada real, com:

- owners nominais por frente
- checkpoints por horario
- criterio explicito de `go`, `go_with_exception`, `pending` e `no-go`
- regra de rerun e troca de `window_id`

Este documento complementa:

- [Run Sheet Preenchivel da Primeira Janela Combinada](./FIRST_COMBINED_SERIOUS_WINDOW_RUN_SHEET.md)
- [Pacote Final de Execucao - Janela Seria Integrada](./SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md)
- [Guia `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_EXECUTION_GUIDE.md)
- [Guia `P0-03` Feed UE real](./P0-03_EU_FEED_EXECUTION_GUIDE.md)
- [Guia `P0-04` Bundle Regulatorio Oficial](./P0-04_REGULATORY_BUNDLE_EXECUTION_GUIDE.md)
- [Matriz de Execucao por Owner para Janela Seria](../../staging-serious-window-war-room-matrix.md)

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `run_url`: `preencher`
- `facilitador`: `Release Manager Tecnico`
- `decisao inicial`: `pending`
- `modo`: `dress_rehearsal_controlado | go_no_go_formal`

## Matriz Executiva de Owners

| Frente | Owner primario | Backup / escalacao | Evidencia minima para seguir |
| --- | --- | --- | --- |
| Gate agregado | `Arquiteto/Responsavel Tecnico` | `Platform/SRE` | `prepare_staging_window --validate --preflight` com `status=ok` |
| `P0-02` AML/KYT | `Compliance/Backend` | `Security` | runtime AML/KYT verde + homologacao externa preservada + `request_id` |
| `P0-03` Feed UE | `Compliance/Backend` | `Security` | JSON `preflight` + JSON `sync` + `EU_CONSOLIDATED=ACTIVE/SUCCESS` + `request_id` |
| `P0-04` consolidado | `Release Manager Tecnico` | `Arquiteto/Responsavel Tecnico` | bundle regulatorio com `readiness.regulatory_bundle=ready_for_validation` |
| Governanca / sign-off | `Release Manager Tecnico` | `Tech Lead` | snapshot, delta, consolidated e sign-off coerentes |

## Gating por Horario

Use os horarios como janelas relativas a partir do inicio da sessao, nao como horario absoluto rigido.

### `T-30 min` - Warmup

- [ ] bridge, facilitador e canal principal confirmados
- [ ] owners nominais online ou com backup nomeado
- [ ] `.env.staging.private` revisado fora do repositorio
- [ ] war room inicial carregado com decisao `pending` ou `no-go`
- [ ] `window_id` unico reservado para esta tentativa

Saida esperada:

- autorizacao para iniciar o gate agregado

### `T-15 min` - Gate agregado

- [ ] `python3 scripts/prepare_staging_window.py --window-id "$WINDOW_ID" --mode baseline --private-env-file .env.staging.private --validate --preflight`
- [ ] `status=ok`
- [ ] nenhum placeholder critico remanescente
- [ ] nenhum handoff obrigatorio em `pending`

Se falhar:

- decisao imediata: `no-go`
- nao avancar para `P0-02` nem `P0-03`

### `T+00` - `P0-02`

- [ ] `preflight_external_integrations.py` verde
- [ ] `make check-compliance-provider-runtime` verde
- [ ] `python3 scripts/homologation_external_evidence.py --mode compliance` preservado
- [ ] `request_id` do compliance runtime registrado
- [ ] `request_id` do runtime comparavel com a homologacao

Se falhar:

- marcar `P0-02=blocked`
- manter a janela em `pending` ou `no-go`
- nao promover `P0-04`

### `T+20 min` - `P0-03`

- [ ] `make rerun-compliance-worker` executado no ambiente correto
- [ ] `make gate-p0-03-eu-live WINDOW_ID="$WINDOW_ID" REQUEST_ID="$REQUEST_ID"` executado
- [ ] `make check-eu-sanctions-window REQUEST_ID="$REQUEST_ID"` verde
- [ ] `EU_CONSOLIDATED.status=ACTIVE`
- [ ] `EU_CONSOLIDATED.last_sync_status=SUCCESS`
- [ ] `source_url_matches_expected=true`
- [ ] `request_id` da janela UE registrado

Se falhar:

- marcar `P0-03=blocked`
- manter a janela em `pending` ou `no-go`
- nao promover `P0-04`

### `T+35 min` - `P0-04`

- [ ] `make gate-p0-04-regulatory-bundle WINDOW_ID="$WINDOW_ID"`
- [ ] `readiness.compliance_runtime=ready_for_validation`
- [ ] `readiness.eu_window=ready_for_validation`
- [ ] `readiness.regulatory_bundle=ready_for_validation`
- [ ] correlators preservados nos steps do bundle

Se falhar:

- bundle oficial fica `blocked`
- proibir promocao manual
- decidir entre `rerun_controlado` e `encerramento_no_go`

### `T+45 min` - Reconciliacao e sign-off

- [ ] `python3 scripts/validate_serious_window_artifact.py --window-id "$WINDOW_ID" --checks-dir artifacts/staging/checks --dossiers-dir artifacts/staging/dossiers --scope P0-01,P0-02,P0-03`
- [ ] `make refresh-staging-war-room-governance-local WINDOW_ID="$WINDOW_ID"`
- [ ] `status-snapshot.md`, `consolidated.json` e `sign-off` com mesma leitura executiva
- [ ] owners humanos revisaram os artefatos criticos

## Decisao Executiva

### `go`

Usar somente quando todos forem verdadeiros:

- gate agregado verde
- `P0-02` verde com homologacao externa
- `P0-03` verde com feed UE coerente
- `P0-04` em `ready_for_validation`
- validador de artifact retorna `status=ok`
- sign-off e governanca sincronizados

### `go_with_exception`

Usar apenas se:

- a janela teve evidencia material valida
- a excecao nao invalida correlators nem bundle oficial
- existe owner, waiver e prazo curto formal

Exemplos aceitaveis:

- atraso administrativo de publicacao em governanca, apos artefatos tecnicos revisados

Exemplos nao aceitaveis:

- `request_id` ausente
- `source_url_matches_expected=false`
- homologacao externa ausente
- `readiness.regulatory_bundle != ready_for_validation`

### `pending`

Usar quando:

- houve progresso parcial real
- ainda existe trilha faltante ou evidência nao reconciliada
- a janela deve ser retomada com nova tentativa controlada

### `no-go`

Usar imediatamente se qualquer um ocorrer:

- gate agregado falhar
- `P0-02` sem homologacao externa ou sem `request_id`
- `P0-03` sem `ACTIVE/SUCCESS` ou sem convergencia de `source_url`
- `P0-04` bloqueado por correlacao
- sign-off divergente do snapshot/consolidado

## Regra de Rerun

- nao rerodar a mesma tentativa depois de alterar secrets, endpoints ou token UE sem registrar isso explicitamente
- se a falha exigir mudanca material de insumo, criar novo `window_id`
- se a falha for apenas de governanca/renderizacao sem mudar evidência tecnica, o mesmo `window_id` pode ser reaproveitado
- nunca sobrescrever artefato anterior sem manter trilha revisavel da tentativa anterior

## Politica de Troca de `window_id`

Trocar o `window_id` quando houver:

- nova credencial AML/KYT
- novo token ou URL do feed UE
- rerun depois de falha de correlator
- mudanca de decisao de `dress_rehearsal_controlado` para `go_no_go_formal`

Pode manter o `window_id` quando houver apenas:

- rerender de governanca
- ajuste de markdown/sign-off
- reconciliacao documental sem alterar a prova tecnica

## Registro Minimo no Encerramento

- decisao final: `go | go_with_exception | pending | no-go`
- motivo objetivo da decisao
- owners presentes
- `window_id`
- paths dos bundles e do dossier
- correlators finais:
  - `compliance request_id`
  - `eu request_id`
  - `source_url_matches_expected`
- criterio objetivo para proxima tentativa, se houver
