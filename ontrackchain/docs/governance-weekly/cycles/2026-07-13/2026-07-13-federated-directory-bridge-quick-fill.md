# Bridge Quick-Fill - `stg-2026-07-13-federated-a`

## Objetivo

Folha minima para uso ao vivo na bridge da tentativa `stg-2026-07-13-federated-a`.

Preencher primeiro aqui, depois refletir os dados finais em:

- [War Room da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)
- [Tracking ao Vivo da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-live-tracking.md)
- [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

## Identificacao Rapida

- `window_id`: `stg-2026-07-13-federated-a`
- `modo`: `dress_rehearsal_controlado`
- `data_utc`: `preencher`
- `hora_inicio_utc`: `preencher`
- `hora_limite_go_no_go_utc`: `preencher`
- `facilitador_online`: `preencher`
- `canal_principal`: `preencher`
- `bridge_principal`: `preencher`
- `tenant_alvo`: `org-staging-e2e | preencher`
- `decisao_corrente`: `pending_no_go | pending_go | pending_go_with_exception | approved`

## Contatos Criticos

| Frente | Papel sugerido | Owner online | Canal | Bridge/Escalacao | ETA atual |
| --- | --- | --- | --- | --- | --- |
| Gate agregado federado | `Release Manager Tecnico` | `preencher` | `preencher` | `preencher` | `preencher` |
| `auth-service` / OIDC | `Backend/Auth` | `preencher` | `preencher` | `preencher` | `preencher` |
| `Team` / Frontend | `Frontend Lead` | `preencher` | `preencher` | `preencher` | `preencher` |
| `Audit` / observabilidade funcional | `Frontend Lead` | `preencher` | `preencher` | `preencher` | `preencher` |
| Banco / evidencias SQL | `Platform/SRE` | `preencher` | `preencher` | `preencher` | `preencher` |

## T-30

- [ ] facilitador online confirmado
- [ ] canal principal confirmado
- [ ] bridge principal confirmada
- [ ] owners online registrados
- [ ] tenant de teste confirmado
- [ ] operador `ADMIN` confirmado
- [ ] principal externo confirmado no `Keycloak`

Registrar:

- `status_t30`: `seguir | segurar | abortar`
- `maior_bloqueio_t30`: `preencher`
- `owner_escalado_t30`: `preencher`

## T-15

- [ ] client tecnico do `Keycloak` validado ou explicitamente bloqueado
- [ ] `auth-service` pronto para leitura do diretório
- [ ] `Team` apto a executar a busca assistida
- [ ] acesso ao `Audit` confirmado
- [ ] rota de evidencia SQL confirmada

Registrar:

- `status_t15`: `seguir | segurar | abortar`
- `runtime_status`: `ok | failed | pending`
- `team_pronto`: `sim | nao`
- `audit_pronto`: `sim | nao`
- `owner_escalado_t15`: `preencher`

## T+00

- [ ] busca assistida disparada ou bloqueada explicitamente
- [ ] sugestao de vinculo disparada ou bloqueada explicitamente
- [ ] `link` efetuado ou bloqueado explicitamente
- [ ] proximo checkpoint definido

Registrar:

- `status_t00`: `seguir | segurar | abortar`
- `search_estado`: `pending | in_progress | blocked | ready_for_validation`
- `link_estado`: `pending | in_progress | blocked | ready_for_validation`
- `audit_estado`: `pending | in_progress | blocked | ready_for_validation`
- `proximo_checkpoint_utc`: `preencher`

## Decisao Curta da Bridge

- `decisao_curta`: `pending_no_go | pending_go | pending_go_with_exception | approved`
- `motivo_curto`: `preencher`
- `owner_do_proximo_passo`: `preencher`
- `acao_imediata`: `preencher`
