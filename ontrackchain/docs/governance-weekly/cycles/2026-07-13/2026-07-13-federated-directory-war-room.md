# War Room da Trilha Federada — `stg-2026-07-13-federated-a`

## Contexto

- data: `2026-07-13`
- window_id: `stg-2026-07-13-federated-a`
- mode: `dress_rehearsal_controlado`
- environment_name: `staging-serious`
- facilitador: `Release Manager Tecnico`
- objetivo da janela: validar ponta a ponta a trilha `Keycloak Admin API -> Team -> Audit -> audit_logs`, incluindo reversao controlada
- baseline canonica: `96%`
- run sheet datada: [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)
- bridge quick-fill: [Bridge Quick-Fill `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-bridge-quick-fill.md)
- decision packet: [Go/No-Go Decision Packet `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-go-no-go-decision-packet.md)

## Leitura de Go/No-Go

- status atual: `pending_no_go`
- motivo principal: aguardando validacao material do runtime, operador `ADMIN` do tenant e evidencias reais de `Team`, `Audit` e `audit_logs`
- risco residual: o desenho esta pronto, mas sem execucao real a trilha ainda nao conta como homologada
- proximo checkpoint: confirmar owners online, validar client tecnico do `Keycloak` e executar a busca assistida
- hora do proximo checkpoint: `<preencher_HH:MMZ>`
- facilitador online: `<preencher_nome_facilitador_online>`
- canal principal do war room: `<preencher_canal_principal_war_room>`
- bridge de escalacao principal: `<preencher_bridge_go_no_go>`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_auth>`, `<preencher_nome_owner_backup_auth>`, `<preencher_nome_owner_escalacao_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- prioridade 3: `<preencher_nome_owner_online_frontend>`, `<preencher_nome_owner_backup_frontend>`, `<preencher_nome_owner_escalacao_frontend>`, `<preencher_slack_ou_teams_frontend>`, `<preencher_bridge_frontend>`
- prioridade 4: `<preencher_nome_owner_online_platform>`, `<preencher_nome_owner_backup_platform>`, `<preencher_nome_owner_escalacao_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 5: `<preencher_nome_operador_admin_tenant>`, `<preencher_tenant_de_teste>`, `<preencher_member_id_alvo>`, `<preencher_external_subject_alvo>`
- criterio de saida do `pending_no_go`: runtime validado, operador/tenant prontos, busca assistida executavel e evidencia prevista mapeada
- folha unica de apoio: [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

## Matriz Operacional Sugerida

| Frente | Papel sugerido | Dominio de origem | Ack minimo antes do `go/no-go` | Fonte de handoff |
| --- | --- | --- | --- | --- |
| Gate agregado federado | `Release Manager Tecnico` | `Arquitetura / Governanca` | checkpoint inicial registrado + bridge ativa + owners online | run sheet datada + war room |
| `auth-service` / Diretorio Federado | `Backend/Auth` | `Security/Auth` | client tecnico validado + runtime confirmado | render blueprint + ownership + auth-service |
| `Team` / Busca Assistida | `Frontend Lead` | `Frontend` | busca retorna candidato correto + sugestao validada | cockpit `Team` + run sheet |
| `Audit` / preset `identity-federated` | `Frontend Lead` | `Frontend` | evento `link` visivel e coerente | cockpit `Audit` + run sheet |
| Banco / `audit_logs` | `Platform/SRE` | `Platform/Operations` | SQL confirma `search + suggestion + link` | evidence SQL + run sheet |

## Handoff Minimo Antes do Ack

- `Gate agregado`: preencher `facilitador online`, `canal principal`, `bridge principal` e `hora do proximo checkpoint`
- `auth-service`: preencher `runtime_auth_service`, `keycloak_admin_client_scope` e owner online
- `Team`: preencher `query_usada`, `candidate_email`, `candidate_org`, `candidate_match_status`
- `Audit`: preencher `audit_member_filter_ok`, `audit_link_event_found`, `audit_event_timestamp`
- `Banco`: preencher `db_search_event_found`, `db_suggestion_event_found`, `db_link_event_found`, `request_id_observado`

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `ready_for_validation` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao final: `go` | `no-go` | `go_with_exception`

## Trilhas do War Room

- `auth-service / Diretorio Federado`
  - owner primario: `<preencher_nome_owner_online_auth>`
  - backup/escalacao: `<preencher_nome_owner_backup_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: client tecnico do `Keycloak` com escopo minimo de leitura
  - evidencia minima: runtime confirmado + leitura real do diretório sem `forbidden`
  - criterio de go/no-go: sem isso, a janela deve abortar
  - observacoes: principal gate tecnico
- `Team / Busca Assistida`
  - owner primario: `<preencher_nome_owner_online_frontend>`
  - backup/escalacao: `<preencher_nome_owner_backup_frontend>`
  - canal de contato: `<preencher_slack_ou_teams_frontend>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: operador `ADMIN`, tenant valido e principal externo coerente
  - evidencia minima: screenshot da busca assistida + screenshot do link
  - criterio de go/no-go: busca, sugestao e `link` precisam convergir
  - observacoes: prova funcional principal
- `Audit / Preset identity-federated`
  - owner primario: `<preencher_nome_owner_online_frontend>`
  - backup/escalacao: `<preencher_nome_owner_backup_frontend>`
  - canal de contato: `<preencher_slack_ou_teams_frontend>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: evento real de `link`
  - evidencia minima: screenshot do preset e do detalhe do evento
  - criterio de go/no-go: sem evento visivel, nao homologar
  - observacoes: prova operacional de governanca
- `Banco / audit_logs`
  - owner primario: `<preencher_nome_owner_online_platform>`
  - backup/escalacao: `<preencher_nome_owner_backup_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: acesso operacional ao evidence path
  - evidencia minima: SQL com `search + suggestion + link`
  - criterio de go/no-go: sem correlacao tecnica, a prova fica incompleta
  - observacoes: valida a rastreabilidade do backend
- `Gate Agregado Federado`
  - owner primario: `<preencher_nome_facilitador_online>`
  - backup/escalacao: `<preencher_nome_owner_backup_go_no_go>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - status: `pending`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: owners online, runtime validado e evidencias capturadas
  - evidencia minima: run sheet atualizado + decision packet coerente + handoff para sign-off
  - criterio de go/no-go: apenas aprovar se as quatro frentes anteriores convergirem
  - observacoes: fecha a tentativa como prova homologada ou `no-go`

## Bloqueadores Ativos

- ID: `FD-01`
  - trilha: `auth-service / Diretorio Federado`
  - descricao: client tecnico do `Keycloak` ainda nao exercitado nesta janela
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - tempo alvo: `2026-07-13`
  - status: `open`
- ID: `FD-02`
  - trilha: `Team / Busca Assistida`
  - descricao: tenant, operador ou principal externo ainda nao confirmados
  - owner da escalacao: `<preencher_nome_owner_escalacao_frontend>`
  - canal da escalacao: `<preencher_bridge_frontend>`
  - tempo alvo: `2026-07-13`
  - status: `watching`
- ID: `FD-03`
  - trilha: `Banco / audit_logs`
  - descricao: evidence SQL ainda nao preparada ou sem acesso operacional confirmado
  - owner da escalacao: `<preencher_nome_owner_escalacao_platform>`
  - canal da escalacao: `<preencher_bridge_platform>`
  - tempo alvo: `2026-07-13`
  - status: `watching`

## Evidencias Revisadas

- `run sheet datada`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-federated-directory-staging-run-sheet.md`
- `decision packet`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-federated-directory-go-no-go-decision-packet.md`
- `tracking ao vivo`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-federated-directory-live-tracking.md`
- `bridge quick-fill`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-federated-directory-bridge-quick-fill.md`
- screenshot da busca assistida: `pending`
- screenshot do link persistido: `pending`
- screenshot do Audit: `pending`
- evidence SQL: `pending`

## Decisoes

- manter a tentativa `stg-2026-07-13-federated-a` em `pending_no_go` ate confirmacao material do runtime e das evidencias
- tratar esta tentativa como `dress_rehearsal_controlado` ate a primeira captura real
- nao declarar a trilha federada homologada sem `unlink` reversivel confirmado

## Proximo Passo Autorizado

- acao: preencher owners e bridge, confirmar runtime do `auth-service`, executar busca assistida e capturar as evidencias
- owner: `Release Manager Tecnico` com coordenacao de `Backend/Auth`, `Frontend` e `Platform/SRE`
- canal: `<preencher_canal_principal_war_room>`
- criterio para seguir: runtime `ok` + operador/tenant prontos + tentativa iniciada

## Resultado Final do War Room

- decisao final: `pending_no_go`
- justificativa: a tentativa esta completamente preparada em termos de processo, mas ainda sem prova material do ambiente
- artefato de sign-off relacionado: [Sign-Off da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-signoff.md)
- tracking ao vivo relacionado: [Tracking ao Vivo da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-live-tracking.md)
