# Run Sheet Datada - Diretorio Federado `stg-2026-07-13-federated-a`

## Objetivo

Instanciar uma tentativa controlada da trilha de diretório federado no ciclo `2026-07-13`, com campos prontos para preenchimento humano durante a validacao em `staging`.

Use esta folha junto com:

- [Run Sheet Operacional - Diretorio Federado em Staging](../../guides/FEDERATED_DIRECTORY_STAGING_RUN_SHEET.md)
- [Validacao em Staging - Diretorio Federado](../../../federated-directory-staging-validation.md)
- [Pacote Final de Execucao - Janela Seria Integrada](../../guides/SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md)
- [Governanca Semanal Operacional 2026-07-13](./2026-07-13-weekly-governance-operational.md)

## Identificacao da Tentativa

- `window_id`: `stg-2026-07-13-federated-a`
- `modo`: `dress_rehearsal_controlado`
- `data_utc`: `preencher`
- `run_url`: `preencher`
- `facilitador`: `Release Manager Tecnico`
- `owner_ativo`: `Backend/Auth`
- `apoio`: `Frontend` / `Platform/SRE`
- `bridge_principal`: `preencher`
- `tenant_alvo`: `org-staging-e2e`
- `member_id_alvo`: `preencher`
- `email_local_alvo`: `analyst@tenant.example`
- `external_subject_alvo`: `preencher`

## Owners Online

| Frente | Owner ativo | Backup/Escalacao | Canal | Online? |
| --- | --- | --- | --- | --- |
| `auth-service` / OIDC | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `Team` / Frontend | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `Audit` / observabilidade funcional | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| `Platform/SRE` | `preencher` | `preencher` | `preencher` | `sim ou nao` |
| Governanca / sign-off | `preencher` | `preencher` | `preencher` | `sim ou nao` |

## Warmup `T-30 min`

- [ ] `window_id` confirmado no war room
- [ ] owners online confirmados
- [ ] `docs/staging-env-ownership.md` sem pendencia obrigatoria de `Auth/OIDC`
- [ ] `KEYCLOAK_ADMIN_CLIENT_SECRET` confirmado fora do repositório
- [ ] principal externo coerente no `Keycloak`
- [ ] membro local existente em `users`

Registrar:

- decisao do warmup: `seguir | segurar | abortar`
- motivo curto: `preencher`

## Gate Inicial `T-15 min`

Registrar:

- `runtime_auth_service`: `healthy | degraded | failed`
- `keycloak_admin_client_scope`: `ok | insufficient | unknown`
- `oidc_runtime_status`: `ok | failed | unknown`
- `observacao_curta`: `preencher`

Decisao:

- [ ] seguir para o `Team`
- [ ] abortar a janela como `no-go`

## Execucao no `Team`

### Busca assistida

Passos resumidos:

1. autenticar como `ADMIN`
2. abrir `Team`
3. selecionar o membro alvo
4. buscar o principal externo na secao `Diretorio federado (assistido)`

Registrar:

- `team_search_status`: `pending | failed | done`
- `query_usada`: `analyst@tenant.example | preencher`
- `candidate_email`: `preencher`
- `candidate_org`: `preencher`
- `candidate_role_snapshot`: `preencher`
- `candidate_match_status`: `preencher`
- `candidate_warnings`: `preencher`
- `screenshot_team_search`: `preencher`

Gate:

- [ ] busca retornou o candidato certo
- [ ] `candidate_org` coerente com o tenant
- [ ] warnings nao bloquearam a operacao

### Sugestao e `link`

Passos resumidos:

1. acionar `Validar e vincular`
2. confirmar mensagem de sucesso
3. validar roster e detalhes persistidos

Registrar:

- `suggestion_status`: `pending | failed | done`
- `link_status`: `pending | failed | done`
- `match_reason`: `preencher`
- `linked_identity_count_after`: `preencher`
- `screenshot_team_link`: `preencher`
- `erro_observado`: `preencher ou n/a`

Gate:

- [ ] sugestao aprovada
- [ ] `link` persistido
- [ ] `linked_identity_count` atualizado

## Confirmacao no `Audit`

Passos resumidos:

1. abrir o deep-link `identity-federated`
2. validar filtro por `member_id`
3. localizar o evento `team_external_identity_linked`

Registrar:

- `audit_preset_status`: `pending | failed | done`
- `audit_member_filter_ok`: `true | false`
- `audit_link_event_found`: `true | false`
- `audit_event_timestamp`: `preencher`
- `screenshot_audit_link_event`: `preencher`

Gate:

- [ ] preset abriu corretamente
- [ ] evento de `link` encontrado
- [ ] payload coerente com a acao do `Team`

## Confirmacao Tecnica no Banco

SQL sugerido:

```sql
SELECT
  action,
  resource_type,
  resource_id,
  metadata,
  created_at
FROM audit_logs
WHERE action IN (
  'team_federated_directory_searched',
  'team_federated_directory_suggestion_validated',
  'team_external_identity_linked'
)
ORDER BY created_at DESC
LIMIT 20;
```

Registrar:

- `db_search_event_found`: `true | false`
- `db_suggestion_event_found`: `true | false`
- `db_link_event_found`: `true | false`
- `request_id_observado`: `preencher`
- `sql_evidence_path`: `preencher`

Gate:

- [ ] tres eventos encontrados
- [ ] eventos coerentes com o mesmo fluxo

## Reversao Controlada

Passos resumidos:

1. voltar ao `Team`
2. executar `Desvincular`
3. confirmar sucesso
4. verificar `team_external_identity_unlinked` no `Audit`

Registrar:

- `unlink_status`: `pending | failed | done`
- `audit_unlink_event_found`: `true | false`
- `screenshot_team_unlink`: `preencher`
- `screenshot_audit_unlink_event`: `preencher`

Gate:

- [ ] `unlink` exigiu confirmacao
- [ ] identidade saiu do membro
- [ ] evento de `unlink` encontrado

## Correlators Finais

- `request_id_search`: `preencher`
- `request_id_suggestion`: `preencher`
- `request_id_link`: `preencher`
- `request_id_unlink`: `preencher`
- `member_id_alvo`: `preencher`
- `external_subject_alvo`: `preencher`

## Artefatos Esperados Deste Ciclo

- [ ] screenshot da busca assistida no `Team`
- [ ] screenshot do `link` persistido no `Team`
- [ ] screenshot do preset `identity-federated` no `Audit`
- [ ] screenshot do evento `team_external_identity_unlinked`
- [ ] output ou screenshot da consulta SQL em `audit_logs`
- [ ] anotacao final do `request_id`

## Decisao Final

- `decisao_final`: `go | go_with_exception | pending | no-go`
- `motivo_objetivo`: `preencher`
- `maior_bloqueio`: `preencher`
- `owner_da_escalacao`: `preencher`
- `proximo_passo`: `preencher`
- `prazo_para_nova_tentativa`: `preencher`
