# Bridge Quick-Fill - `stg-2026-07-13-a`

## Objetivo

Folha minima para uso ao vivo na bridge da tentativa `stg-2026-07-13-a`.

Preencher primeiro aqui, depois refletir os dados finais em:

- [War Room da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-war-room.md)
- [Tracking ao Vivo da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-live-tracking.md)
- [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)

## Identificacao Rapida

- `window_id`: `stg-2026-07-13-a`
- `modo`: `dress_rehearsal_controlado`
- `data_utc`: `preencher`
- `hora_inicio_utc`: `preencher`
- `hora_limite_go_no_go_utc`: `preencher`
- `facilitador_online`: `preencher`
- `canal_principal`: `preencher`
- `bridge_principal`: `preencher`
- `decisao_corrente`: `pending_no_go | pending_go | pending_go_with_exception | approved`

## Contatos Criticos

| Frente | Papel sugerido | Owner online | Canal | Bridge/Escalacao | ETA atual |
| --- | --- | --- | --- | --- | --- |
| Gate agregado | `Release Manager Tecnico` | `preencher` | `preencher` | `preencher` | `preencher` |
| `P0-02` AML/KYT | `Compliance/Backend Lead` | `preencher` | `preencher` | `preencher` | `preencher` |
| `P0-03` Feed UE | `Compliance/Ops Lead` | `preencher` | `preencher` | `preencher` | `preencher` |
| `P0-04` consolidado | `Platform/SRE` | `preencher` | `preencher` | `preencher` | `preencher` |
| `P0-01` Auth/OIDC | `Backend/Auth` | `preencher` | `preencher` | `preencher` | `preencher` |

## T-30

- [ ] facilitador online confirmado
- [ ] canal principal confirmado
- [ ] bridge principal confirmada
- [ ] owners online registrados
- [ ] credencial AML/KYT disponivel para teste
- [ ] URL tokenizada UE disponivel para teste

Registrar:

- `status_t30`: `seguir | segurar | abortar`
- `maior_bloqueio_t30`: `preencher`
- `owner_escalado_t30`: `preencher`

## T-15

- [ ] `prepare_staging_window.py --validate --preflight` executado ou agendado
- [ ] `P0-02` apto a rodar checker com insumo real
- [ ] `P0-03` apto a rodar janela UE com insumo real
- [ ] `P0-01` risco residual explicitado

Registrar:

- `status_t15`: `seguir | segurar | abortar`
- `prepare_status`: `ok | failed | pending`
- `p0_02_pronto`: `sim | nao`
- `p0_03_pronto`: `sim | nao`
- `owner_escalado_t15`: `preencher`

## T+00

- [ ] `P0-02` disparado ou bloqueado explicitamente
- [ ] `P0-03` disparado ou bloqueado explicitamente
- [ ] ETA do bundle regulatorio recalculado
- [ ] proximo checkpoint combinado definido

Registrar:

- `status_t00`: `seguir | segurar | abortar`
- `p0_02_estado`: `pending | in_progress | blocked | ready_for_validation`
- `p0_03_estado`: `pending | in_progress | blocked | ready_for_validation`
- `eta_p0_04`: `preencher`
- `proximo_checkpoint_utc`: `preencher`

## Decisao Curta da Bridge

- `decisao_curta`: `pending_no_go | pending_go | pending_go_with_exception | approved`
- `motivo_curto`: `preencher`
- `owner_do_proximo_passo`: `preencher`
- `acao_imediata`: `preencher`
