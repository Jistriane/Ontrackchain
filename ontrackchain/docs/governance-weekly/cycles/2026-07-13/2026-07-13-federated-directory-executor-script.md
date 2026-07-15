# Script Pratico do Executor - `stg-2026-07-13-federated-a`

## Objetivo

Dar ao executor humano uma sequencia curta, objetiva e verificavel para rodar a tentativa `stg-2026-07-13-federated-a` no `staging-serious`.

Use este script junto com:

- [Roteiro Minuto a Minuto `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-minute-by-minute-execution.md)
- [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)
- [Bridge Quick-Fill `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-bridge-quick-fill.md)
- [War Room `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)

## Antes de Comecar

Confirme apenas o minimo:

- [ ] voce esta autenticado como `ADMIN`
- [ ] o tenant alvo esta correto
- [ ] o `member_id` ou email local alvo esta confirmado
- [ ] o principal externo esperado existe no `Keycloak`
- [ ] o facilitador liberou a tentativa para execucao

Se qualquer item acima for `nao`, pare e marque `pending_no_go`.

## Dados Que Voce Precisa Ter em Maos

- `window_id`: `stg-2026-07-13-federated-a`
- `tenant_alvo`: `preencher`
- `member_id_alvo`: `preencher`
- `email_local_alvo`: `preencher`
- `external_subject_alvo`: `preencher`
- `query_usada`: `preencher`

## Passo 1 - Abrir `Team`

Acao:

1. acessar o ambiente `staging-serious`
2. entrar na tela `Team`
3. localizar o membro alvo pelo email ou pela roster table
4. selecionar o membro correto

Registrar:

- `team_opened=true`
- `selected_member_ok=true | false`

Stop/Go:

- seguir apenas se o membro selecionado for exatamente o esperado
- se houver duvida sobre o membro, parar e pedir confirmacao humana

## Passo 2 - Executar a Busca Assistida

Acao:

1. ir para a secao `Diretorio federado (assistido)`
2. preencher a busca com o email alvo ou query combinada
3. acionar a busca
4. revisar o primeiro candidato retornado

Voce precisa enxergar:

- email do candidato
- `org` do candidato
- `role_snapshot`
- `match_status`
- warnings, se existirem

Registrar:

- `candidate_email`
- `candidate_org`
- `candidate_role_snapshot`
- `candidate_match_status`
- `candidate_warnings`

Evidencia:

- capturar screenshot da busca assistida

Stop/Go:

- seguir se o candidato estiver coerente com o tenant e sem mismatch bloqueador
- parar se houver `candidate_org_mismatch`
- parar se o candidato parecer ambíguo

## Passo 3 - Validar e Vincular

Acao:

1. clicar em `Validar e vincular`
2. aguardar a resposta da sugestao
3. confirmar a mensagem de sucesso
4. confirmar que o roster/detalhe do membro mostra o vinculo persistido

Voce precisa enxergar:

- mensagem de sucesso
- `linked_identity_count` atualizado
- identidade marcada como vinculada

Registrar:

- `suggestion_status=done | failed`
- `link_status=done | failed`
- `match_reason`
- `linked_identity_count_after`

Evidencia:

- capturar screenshot da mensagem de sucesso e do membro vinculado

Stop/Go:

- seguir se `can_link` for aprovado e o `link` persistir
- parar se aparecer `team_external_identity_already_linked`
- parar se o `link` falhar sem mensagem rastreavel

## Passo 4 - Confirmar no `Audit`

Acao:

1. abrir o deep-link do preset `identity-federated`
2. filtrar pelo `member_id`, se necessario
3. localizar o evento `team_external_identity_linked`
4. abrir o detalhe do evento

Voce precisa enxergar:

- acao `team_external_identity_linked`
- `resource_type=team_user`
- `resource_id` do membro correto
- `provider` e `external_subject` coerentes

Registrar:

- `audit_link_event_found=true | false`
- `audit_event_timestamp`

Evidencia:

- capturar screenshot da lista e do detalhe do evento

Stop/Go:

- seguir se o evento estiver visivel e coerente
- parar se o evento nao aparecer apos o `link` confirmado no `Team`

## Passo 5 - Confirmar a Correlacao Tecnica

Acao:

1. pedir ao owner de `Platform/SRE` a execucao da SQL da run sheet
2. confirmar que os tres eventos do fluxo aparecem:
   - `team_federated_directory_searched`
   - `team_federated_directory_suggestion_validated`
   - `team_external_identity_linked`
3. anotar `request_id` ou timestamp equivalente

Registrar:

- `db_search_event_found=true | false`
- `db_suggestion_event_found=true | false`
- `db_link_event_found=true | false`
- `request_id_observado`

Evidencia:

- guardar screenshot ou output da SQL

Stop/Go:

- seguir se os tres eventos existirem e parecerem do mesmo fluxo
- parar se qualquer evento obrigatorio estiver ausente

## Passo 6 - Executar o `unlink`

Acao:

1. voltar para `Team`
2. localizar a identidade vinculada
3. clicar em `Desvincular`
4. confirmar a acao
5. validar que a identidade saiu do membro

Registrar:

- `unlink_status=done | failed`

Evidencia:

- capturar screenshot do `unlink` ou do estado final sem vinculo

Stop/Go:

- seguir para o `Audit` apenas se o `unlink` tiver sido realmente aplicado
- parar se o estado do membro continuar mostrando a identidade vinculada

## Passo 7 - Confirmar o `unlink` no `Audit`

Acao:

1. voltar para o preset `identity-federated`
2. localizar o evento `team_external_identity_unlinked`
3. conferir `member_id`, `provider` e `external_subject`

Registrar:

- `audit_unlink_event_found=true | false`

Evidencia:

- capturar screenshot do evento `unlink`

Stop/Go:

- concluir a tentativa apenas se o evento `unlink` estiver visivel
- marcar `pending` ou `no-go` se o `unlink` nao tiver trilha auditavel

## Fechamento do Executor

Antes de encerrar, garantir:

- [ ] screenshots anexadas ou com path registrado
- [ ] run sheet datada preenchida
- [ ] bridge quick-fill atualizada
- [ ] qualquer erro observado registrado literalmente
- [ ] facilitador avisado da leitura final

## Frase Curta de Handoff

Use esta frase, ajustando os campos:

`Execucao do window_id stg-2026-07-13-federated-a concluida com status <go|pending|no-go>; Team=<ok|falhou>, Audit=<ok|falhou>, SQL=<ok|falhou>, unlink=<ok|falhou>; maior bloqueio=<descrever>.`
