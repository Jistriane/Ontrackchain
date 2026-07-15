# Run Sheet Operacional - Diretorio Federado em Staging

## Uso

Preencher e executar esta folha durante a validacao real da trilha de diretório federado em `staging`.

Ela existe para:

- registrar owner ativo, janela e canal de execucao
- reduzir ambiguidade entre `auth-service`, `Team` e `Audit`
- concentrar checkpoints curtos e objetivos para `go/no-go`
- preservar evidencias minimas da busca, sugestao, `link` e `unlink`

Complementa:

- [Validacao em Staging - Diretorio Federado](../../federated-directory-staging-validation.md)
- [Pacote Final de Execucao - Janela Seria Integrada](./SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md)
- exemplo datado do ciclo atual: [Run Sheet Datada - Diretorio Federado `stg-2026-07-13-federated-a`](../cycles/2026-07-13/2026-07-13-federated-directory-staging-run-sheet.md)

## Identificacao da Janela

- `window_id`: `preencher`
- `data_utc`: `preencher`
- `owner_ativo`: `Backend/Auth`
- `apoio`: `Frontend` / `Platform/SRE`
- `facilitador`: `preencher`
- `bridge`: `preencher`
- `run_url`: `preencher`
- `tenant_alvo`: `preencher`
- `member_id_alvo`: `preencher`
- `email_local_alvo`: `preencher`
- `external_subject_alvo`: `preencher`

## Checklist de Prontidao

- [ ] `AUTH_MODE=oidc`
- [ ] `DEV_AUTH_ENABLED=false`
- [ ] `NEXT_PUBLIC_AUTH_MODE=oidc`
- [ ] `OIDC_ISSUER_URL` aponta para host real do `Keycloak`
- [ ] `KEYCLOAK_ADMIN_BASE_URL` aponta para host real do `Keycloak`
- [ ] `KEYCLOAK_ADMIN_CLIENT_ID` preenchido
- [ ] `KEYCLOAK_ADMIN_CLIENT_SECRET` preenchido
- [ ] `KEYCLOAK_ADMIN_ORG_ATTRIBUTE=organization_id`
- [ ] `KEYCLOAK_ADMIN_ROLE_ATTRIBUTE=otk_role`
- [ ] operador `ADMIN` do tenant disponivel
- [ ] usuario local em `users` previamente criado
- [ ] principal externo coerente no `Keycloak`
- [ ] `docs/staging-env-ownership.md` sem pendencia obrigatoria de `Auth/OIDC`

## Ordem de Execucao

### 1. Verificacao inicial do ambiente

Registrar:

- `runtime_auth_service`: `healthy | degraded | failed`
- `keycloak_admin_client_scope`: `ok | insufficient | unknown`
- `observacao_curta`: `preencher`

Decisao:

- [ ] seguir para o `Team`
- [ ] abortar a janela como `no-go`

### 2. Busca assistida no `Team`

Passos resumidos:

1. autenticar como `ADMIN`
2. abrir `Team`
3. selecionar o membro alvo
4. buscar o principal externo na secao `Diretorio federado (assistido)`

Registrar:

- `team_search_status`: `pending | failed | done`
- `query_usada`: `preencher`
- `candidate_email`: `preencher`
- `candidate_org`: `preencher`
- `candidate_role_snapshot`: `preencher`
- `candidate_match_status`: `preencher`
- `candidate_warnings`: `preencher`
- `screenshot_team_search`: `preencher`

Gate de saida:

- [ ] busca retornou o candidato correto
- [ ] `candidate_org` coerente com o tenant
- [ ] nenhum warning bloqueador

### 3. Validacao da sugestao e `link`

Passos resumidos:

1. acionar `Validar e vincular`
2. confirmar mensagem de sucesso
3. confirmar roster e detalhes persistidos

Registrar:

- `suggestion_status`: `pending | failed | done`
- `link_status`: `pending | failed | done`
- `match_reason`: `preencher`
- `linked_identity_count_after`: `preencher`
- `screenshot_team_link`: `preencher`
- `erro_observado`: `preencher ou n/a`

Gate de saida:

- [ ] sugestao aprovada
- [ ] `link` persistido
- [ ] `linked_identity_count` atualizado

### 4. Confirmacao no `Audit`

Passos resumidos:

1. abrir deep-link `identity-federated`
2. confirmar filtro por `member_id`
3. localizar o evento `team_external_identity_linked`

Registrar:

- `audit_preset_status`: `pending | failed | done`
- `audit_member_filter_ok`: `true | false`
- `audit_link_event_found`: `true | false`
- `audit_event_timestamp`: `preencher`
- `screenshot_audit_link_event`: `preencher`

Gate de saida:

- [ ] preset abriu corretamente
- [ ] evento de `link` encontrado
- [ ] payload do evento coerente com a acao executada

### 5. Confirmacao tecnica em `audit_logs`

SQL recomendado:

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

Gate de saida:

- [ ] os tres eventos existem
- [ ] os tres eventos sao coerentes com o mesmo fluxo

### 6. Reversao controlada (`unlink`)

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

Gate de saida:

- [ ] `unlink` exigiu confirmacao
- [ ] identidade saiu do membro
- [ ] evento de `unlink` encontrado no `Audit`

## Artefatos a Preservar

- screenshot da busca assistida no `Team`
- screenshot do `link` persistido no `Team`
- screenshot do preset `identity-federated` no `Audit`
- screenshot do evento `team_external_identity_unlinked`
- output ou screenshot da consulta SQL em `audit_logs`
- anotacao do `request_id` ou timestamp correlacionavel

## Gate de Saida Final

Marcar a trilha como pronta para validacao homologada somente se todos estiverem verdadeiros:

- [ ] runtime do `auth-service` confirmado
- [ ] busca assistida funcionando
- [ ] sugestao validada com sucesso
- [ ] `link` persistido
- [ ] `Audit` exibindo `team_external_identity_linked`
- [ ] consulta SQL exibindo `search + suggestion + link`
- [ ] `unlink` reversivel validado
- [ ] owner humano revisou a evidencia

## Resultado da Janela

- `decisao_sugerida`: `go | go_with_exception | pending | no-go`
- `motivo_resumido`: `preencher`
- `maior_bloqueio`: `preencher`
- `owner_da_escalacao`: `preencher`
- `proximo_passo`: `preencher`
- `prazo_para_nova_tentativa`: `preencher`
