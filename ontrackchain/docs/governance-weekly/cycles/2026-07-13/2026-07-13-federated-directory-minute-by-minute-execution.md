# Roteiro Minuto a Minuto - `stg-2026-07-13-federated-a`

## Objetivo

Dar ao facilitador e aos owners da tentativa `stg-2026-07-13-federated-a` um roteiro operacional minuto a minuto para conduzir a validacao em `staging` sem ambiguidade.

Use este roteiro junto com:

- [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)
- [Script Pratico do Executor `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-executor-script.md)
- [Bridge Quick-Fill `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-bridge-quick-fill.md)
- [Tracking ao Vivo `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-live-tracking.md)
- [War Room `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)
- [Go/No-Go Decision Packet `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-go-no-go-decision-packet.md)

## Premissas

- `window_id`: `stg-2026-07-13-federated-a`
- `mode`: `dress_rehearsal_controlado`
- a tentativa so deve comecar com owners online e runtime do `auth-service` confirmado
- readiness documental nao substitui evidencia material de `Team`, `Audit` e `audit_logs`

## Linha do Tempo Executiva

| Marco | Objetivo | Owner primario | Gate de saida |
| --- | --- | --- | --- |
| `T-30` | confirmar bridge, owners e tenant | `Release Manager Tecnico` | janela autorizada para warmup |
| `T-15` | validar runtime e client tecnico | `Backend/Auth` | leitura do diretório possivel ou `no-go` |
| `T+00` | executar busca assistida | `Frontend` | candidato correto encontrado |
| `T+10` | validar sugestao e efetivar `link` | `Frontend` + `Backend/Auth` | vinculo persistido |
| `T+20` | confirmar evento no `Audit` | `Frontend` | evento `link` visivel |
| `T+30` | confirmar correlacao no banco | `Platform/SRE` | `search + suggestion + link` visiveis |
| `T+40` | validar `unlink` reversivel | `Frontend` + `Backend/Auth` | evento `unlink` visivel |
| `T+50` | reconciliar evidencias e decidir | `Release Manager Tecnico` | `go / pending / no-go` |

## `T-30 min` - Warmup da Janela

### Script do Facilitador - `T-30`

- "Confirmem bridge principal, owner ativo por frente e backup nomeado."
- "Precisamos sair deste ponto com tenant, operador `ADMIN` e principal externo confirmados."
- "Sem estes insumos, a decisao correta ainda e `pending_no_go`."

### Checklist - `T-30`

- [ ] facilitador online
- [ ] canal principal do war room confirmado
- [ ] bridge principal confirmada
- [ ] owner `Backend/Auth` online
- [ ] owner `Frontend` online
- [ ] owner `Platform/SRE` online
- [ ] operador `ADMIN` do tenant confirmado
- [ ] `member_id` alvo confirmado
- [ ] principal externo coerente no `Keycloak`

### Evidencia Minima - `T-30`

- preencher [Bridge Quick-Fill `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-bridge-quick-fill.md)
- atualizar `owners online` na [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

### Stop/Go - `T-30`

- `go para T-15`: owners + operador + tenant + principal externo confirmados
- `segurar`: falta owner ou falta principal externo coerente
- `no-go`: nao existe owner responsavel por uma frente critica

## `T-15 min` - Gate Tecnico do `auth-service`

### Script do Facilitador - `T-15`

- "Backend/Auth, confirmem agora se o client tecnico do `Keycloak` esta apto a ler o diretório."
- "Se tivermos `forbidden`, `unavailable` ou escopo insuficiente, a tentativa nao deve seguir."

### Checklist - `T-15`

- [ ] `auth-service` saudavel
- [ ] `KEYCLOAK_ADMIN_CLIENT_ID` preenchido
- [ ] `KEYCLOAK_ADMIN_CLIENT_SECRET` preenchido fora do repositorio
- [ ] escopo minimo do client tecnico confirmado
- [ ] nenhuma pendencia critica em `Auth/OIDC`

### Evidencia Minima - `T-15`

- `runtime_auth_service=healthy`
- `keycloak_admin_client_scope=ok`
- nota curta de runtime preenchida na run sheet

### Stop/Go - `T-15`

- `go para T+00`: runtime `healthy` e escopo `ok`
- `segurar`: escopo `unknown`
- `no-go`: `federated_directory_forbidden` ou `federated_directory_unavailable`

## `T+00` - Busca Assistida no `Team`

### Script do Facilitador - `T+00`

- "Frontend, executem a busca assistida com o email alvo ou query equivalente."
- "Precisamos confirmar candidato correto, `org` coerente e ausencia de warning bloqueador."

### Checklist - `T+00`

- [ ] login como `ADMIN`
- [ ] tela `Team` aberta
- [ ] membro alvo selecionado
- [ ] query executada
- [ ] candidato correto visivel
- [ ] `candidate_org` coerente com o tenant

### Evidencia Minima - `T+00`

- screenshot da busca assistida
- `query_usada`
- `candidate_email`
- `candidate_org`
- `candidate_match_status`

### Stop/Go - `T+00`

- `go para T+10`: candidato correto e sem mismatch bloqueador
- `segurar`: warning nao conclusivo que exige revisao humana
- `no-go`: `candidate_org_mismatch` ou candidato ambíguo sem resolucao segura

## `T+10` - Sugestao e `link`

### Script do Facilitador - `T+10`

- "Executem `Validar e vincular` apenas se o candidato estiver coerente."
- "Backend/Auth acompanha qualquer erro canônico para decidir se é bloqueio definitivo ou apenas retomada."

### Checklist - `T+10`

- [ ] sugestao disparada
- [ ] `can_link=true`
- [ ] `match_reason` registrado
- [ ] mensagem de sucesso exibida
- [ ] `linked_identity_count` atualizado

### Evidencia Minima - `T+10`

- screenshot do `link` persistido
- `suggestion_status=done`
- `link_status=done`
- `linked_identity_count_after`

### Stop/Go - `T+10`

- `go para T+20`: sugestao aprovada e `link` persistido
- `segurar`: timeout intermitente com candidato coerente
- `no-go`: `team_external_identity_already_linked` ou falha sem explicacao rastreavel

## `T+20` - Confirmacao no `Audit`

### Script do Facilitador - `T+20`

- "Abram o preset `identity-federated` e filtrem pelo `member_id`."
- "A tentativa nao deve ser promovida sem evento de `link` visivel e coerente."

### Checklist - `T+20`

- [ ] preset abriu corretamente
- [ ] filtro por `member_id` aplicado
- [ ] evento `team_external_identity_linked` localizado
- [ ] timestamp do evento registrado

### Evidencia Minima - `T+20`

- screenshot do preset no `Audit`
- screenshot do evento de `link`
- `audit_link_event_found=true`

### Stop/Go - `T+20`

- `go para T+30`: evento visivel e coerente
- `segurar`: UI do `Audit` abriu mas o evento ainda nao apareceu
- `no-go`: evento ausente apos confirmacao do `link` no `Team`

## `T+30` - Confirmacao Tecnica em `audit_logs`

### Script do Facilitador - `T+30`

- "Platform/SRE, precisamos provar agora a correlacao tecnica do fluxo completo."
- "Sem `search + suggestion + link`, a trilha continua incompleta, mesmo com cockpit verde."

### Checklist - `T+30`

- [ ] consulta SQL executada
- [ ] `team_federated_directory_searched` encontrado
- [ ] `team_federated_directory_suggestion_validated` encontrado
- [ ] `team_external_identity_linked` encontrado
- [ ] correlator (`request_id` ou timestamp) anotado

### Evidencia Minima - `T+30`

- output ou screenshot da SQL
- `db_search_event_found=true`
- `db_suggestion_event_found=true`
- `db_link_event_found=true`

### Stop/Go - `T+30`

- `go para T+40`: tres eventos encontrados e coerentes
- `segurar`: acesso ao banco pendente mas evidence path alternativo existe
- `no-go`: qualquer evento obrigatorio ausente

## `T+40` - Reversao Controlada com `unlink`

### Script do Facilitador - `T+40`

- "Executem `Desvincular` para provar reversibilidade operacional."
- "Sem `unlink` reversivel, a trilha nao sobe como homologada."

### Checklist - `T+40`

- [ ] confirmacao humana do `unlink`
- [ ] identidade removida do membro
- [ ] evento `team_external_identity_unlinked` localizado no `Audit`

### Evidencia Minima - `T+40`

- screenshot do `unlink` no `Team`
- screenshot do evento `unlink` no `Audit`
- `unlink_status=done`
- `audit_unlink_event_found=true`

### Stop/Go - `T+40`

- `go para T+50`: `unlink` concluido e auditado
- `segurar`: `unlink` feito mas evento ainda nao refletiu
- `no-go`: `unlink` falhou ou nao ficou auditado

## `T+50` - Reconciliacao Final e Decisao

### Script do Facilitador - `T+50`

- "Vamos responder objetivamente: temos runtime, busca, sugestao, `link`, `Audit`, SQL e `unlink` convergindo?"
- "Se a resposta for nao ou incerta em qualquer frente critica, a decisao correta nao e `go`."

### Checklist - `T+50`

- [ ] run sheet datada atualizada
- [ ] bridge quick-fill reconciliada
- [ ] tracking ao vivo atualizado
- [ ] war room com mesma leitura executiva
- [ ] sign-off coerente com as evidencias

### Resultado Possivel

- `go`: todos os gates materiais passaram
- `go_with_exception`: evidência material valida + excecao formal pequena e nao destrutiva
- `pending`: progresso real com evidência parcial e nova tentativa controlada necessaria
- `no-go`: falha de runtime, correlacao ou reversibilidade

## Regra de Rerun

- manter o mesmo `window_id` somente se a tentativa parar por reconciliacao documental ou atraso de publicacao
- criar novo `window_id` se houver mudanca material de secret, escopo do client tecnico, tenant, principal externo ou runtime

## Encerramento Recomendado

Fechar a bridge sempre com esta sintese:

- decisao final
- maior bloqueio real
- owner da escalacao
- proxima evidência esperada
- prazo da nova tentativa, se houver
