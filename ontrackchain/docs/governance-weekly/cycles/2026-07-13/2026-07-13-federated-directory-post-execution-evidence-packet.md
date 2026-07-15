# Pacote de Evidencia Pos-Execucao - `stg-2026-07-13-federated-a`

## Objetivo

Concentrar, em um unico lugar, as evidencias finais da tentativa `stg-2026-07-13-federated-a` para reconciliacao de:

- `Team`
- `Audit`
- `audit_logs`
- `sign-off`
- decisao final de `go/pending/no-go`

Use este packet junto com:

- [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)
- [Script Pratico do Executor `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-executor-script.md)
- [Roteiro Minuto a Minuto `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-minute-by-minute-execution.md)
- [War Room `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)
- [Sign-Off `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-signoff.md)

## Identificacao

- `window_id`: `stg-2026-07-13-federated-a`
- `run_url`: `preencher`
- `data_utc`: `preencher`
- `facilitador`: `preencher`
- `executor`: `preencher`
- `tenant_alvo`: `preencher`
- `member_id_alvo`: `preencher`
- `email_local_alvo`: `preencher`
- `external_subject_alvo`: `preencher`

## Resultado Executivo Curto

- `decisao_preliminar`: `go | go_with_exception | pending | no-go`
- `maior_bloqueio_real`: `preencher`
- `principal_ganho_real`: `preencher`
- `owner_da_escalacao`: `preencher`
- `nova_tentativa_necessaria`: `sim | nao`

## Snapshot da Execucao

Preencher apenas com leitura material observada:

- `runtime_auth_service`: `healthy | degraded | failed`
- `keycloak_admin_client_scope`: `ok | insufficient | unknown`
- `team_search_status`: `done | failed | pending`
- `suggestion_status`: `done | failed | pending`
- `link_status`: `done | failed | pending`
- `audit_link_event_found`: `true | false`
- `db_search_event_found`: `true | false`
- `db_suggestion_event_found`: `true | false`
- `db_link_event_found`: `true | false`
- `unlink_status`: `done | failed | pending`
- `audit_unlink_event_found`: `true | false`

## Evidencias Obrigatorias

| Evidencia | Status | Path ou URL | Observacao curta |
| --- | --- | --- | --- |
| screenshot da busca assistida no `Team` | `pending` | `preencher` | `preencher` |
| screenshot do `link` persistido no `Team` | `pending` | `preencher` | `preencher` |
| screenshot do preset `identity-federated` no `Audit` | `pending` | `preencher` | `preencher` |
| screenshot do detalhe do evento `team_external_identity_linked` | `pending` | `preencher` | `preencher` |
| screenshot do evento `team_external_identity_unlinked` | `pending` | `preencher` | `preencher` |
| output ou screenshot da SQL de `audit_logs` | `pending` | `preencher` | `preencher` |

## Correlators

- `request_id_search`: `preencher`
- `request_id_suggestion`: `preencher`
- `request_id_link`: `preencher`
- `request_id_unlink`: `preencher`
- `audit_event_timestamp_link`: `preencher`
- `audit_event_timestamp_unlink`: `preencher`
- `db_timestamp_reference`: `preencher`

## Leitura do `Team`

- `selected_member_ok`: `true | false`
- `candidate_email`: `preencher`
- `candidate_org`: `preencher`
- `candidate_role_snapshot`: `preencher`
- `candidate_match_status`: `preencher`
- `candidate_warnings`: `preencher`
- `linked_identity_count_after`: `preencher`
- `mensagem_sucesso_link`: `preencher ou n/a`

## Leitura do `Audit`

- `preset_opened_ok`: `true | false`
- `audit_member_filter_ok`: `true | false`
- `link_event_action`: `preencher`
- `unlink_event_action`: `preencher`
- `link_event_resource_id`: `preencher`
- `unlink_event_resource_id`: `preencher`
- `provider_from_audit`: `preencher`
- `external_subject_from_audit`: `preencher`

## Leitura da SQL

Registrar somente o minimo necessario:

- `search_action_found`: `true | false`
- `suggestion_action_found`: `true | false`
- `link_action_found`: `true | false`
- `unlink_action_found`: `true | false`
- `resource_type_confirmed`: `preencher`
- `resource_id_confirmed`: `preencher`
- `sql_evidence_path`: `preencher`

## Divergencias Observadas

- divergencia 1: `preencher ou n/a`
- divergencia 2: `preencher ou n/a`
- divergencia 3: `preencher ou n/a`

## Texto Curto para o War Room

Preencher e colar no war room:

`window_id stg-2026-07-13-federated-a executado com decisao preliminar <go|pending|no-go>; runtime=<healthy|degraded|failed>; Team=<ok|falhou>; Audit=<ok|falhou>; SQL=<ok|falhou>; unlink=<ok|falhou>; maior bloqueio=<descrever>.`

## Texto Curto para o Sign-Off

Preencher e colar no sign-off:

`A tentativa stg-2026-07-13-federated-a <comprovou|nao comprovou> a trilha federada ponta a ponta em staging. O fluxo search -> suggestion -> link -> Audit -> audit_logs -> unlink ficou <coerente|incompleto> e a decisao recomendada e <go|pending|no-go>.`

## Criterio de Fechamento

Considerar o packet completo somente se:

- [ ] todas as evidencias obrigatorias tiverem path ou URL
- [ ] os correlators estiverem preenchidos
- [ ] `Team`, `Audit` e SQL convergirem para o mesmo fluxo
- [ ] o texto do war room e do sign-off estiver coerente com a decisao
- [ ] houver owner humano identificado para o proximo passo
