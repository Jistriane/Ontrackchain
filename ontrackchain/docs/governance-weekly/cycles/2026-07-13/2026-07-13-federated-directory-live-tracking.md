# Tracking ao Vivo da Trilha Federada — `stg-2026-07-13-federated-a`

## Contexto Operacional

- data: `2026-07-13`
- window_id: `stg-2026-07-13-federated-a`
- mode: `dress_rehearsal_controlado`
- environment_name: `staging-serious`
- facilitador: `Release Manager Tecnico`
- status global: `pending`
- checkpoint atual: `aguardando owners online, runtime do auth-service confirmado e operador ADMIN disponivel`
- ultima atualizacao: `pre-run do ciclo 2026-07-13`
- cadencia de atualizacao recomendada: `15 min`
- run sheet de referencia: [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `ready_for_validation` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao recomendada: `pending_no_go` | `pending_go_with_exception` | `pending_go` | `approved`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- prioridade 3: `<preencher_nome_owner_online_frontend>`, `<preencher_slack_ou_teams_frontend>`, `<preencher_bridge_frontend>`
- prioridade 4: `<preencher_nome_owner_online_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 5: `<preencher_nome_operador_admin_tenant>`, `<preencher_tenant_de_teste>`, `<preencher_external_subject_alvo>`
- criterio de saida do `pending`: owners confirmados, operador/tenant prontos e runtime confirmado
- folha unica de apoio: [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

## Painel de Trilhas

- `auth-service / Diretorio Federado`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: backend, blueprint e segredos modelados; falta validar escopo real do client tecnico
  - proximo checkpoint: confirmar client tecnico e disponibilidade do runtime
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-13`
  - dependencia ativa: `KEYCLOAK_ADMIN_CLIENT_SECRET` real + leitura do diretório
  - bridge de escalacao: `<preencher_bridge_auth>`
  - observacoes: principal risco tecnico da tentativa
- `Team / Busca Assistida`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_frontend>`
  - canal de contato: `<preencher_slack_ou_teams_frontend>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: UI pronta com busca, validacao e link; falta execucao real no tenant
  - proximo checkpoint: executar `search -> suggestion -> link`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-13`
  - dependencia ativa: operador `ADMIN` e principal externo coerente
  - bridge de escalacao: `<preencher_bridge_frontend>`
  - observacoes: ponto de prova funcional mais visivel
- `Audit / Preset identity-federated`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_frontend>`
  - canal de contato: `<preencher_slack_ou_teams_frontend>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: preset e deep-link modelados; falta evento real
  - proximo checkpoint: validar evento `team_external_identity_linked`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-13`
  - dependencia ativa: evento real de `link` no backend
  - bridge de escalacao: `<preencher_bridge_frontend>`
  - observacoes: evidencia visual de governanca operacional
- `Banco / audit_logs`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: SQL e criterios ja preparados; falta correlacao real
  - proximo checkpoint: verificar `search + suggestion + link`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-13`
  - dependencia ativa: acesso operacional ao banco ou evidence path equivalente
  - bridge de escalacao: `<preencher_bridge_platform>`
  - observacoes: prova tecnica final da tentativa
- `Gate Agregado Federado`
  - status atual: `pending`
  - responsavel online: `<preencher_nome_facilitador_online>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - ack do owner: `yes`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: run sheet, guide e packet datados criados
  - proximo checkpoint: confirmar owners e disparar a validacao manual
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-13`
  - dependencia ativa: disponibilidade humana e runtime real
  - bridge de escalacao: `<preencher_bridge_go_no_go>`
  - observacoes: nao declarar `approved` sem evidencias capturadas

## Linha do Tempo

- `T-30`:
  - trilha: `Gate Agregado Federado`
  - evento: owners, tenant e tentativa datada confirmados
  - impacto: habilita o checkpoint inicial
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`
- `T-15`:
  - trilha: `auth-service / Diretorio Federado`
  - evento: client tecnico validado ou recusado
  - impacto: define se a janela pode seguir
  - owner: `<preencher_nome_owner_online_auth>`
  - canal: `<preencher_slack_ou_teams_auth>`
- `T+00`:
  - trilha: `Team / Busca Assistida`
  - evento: busca e sugestao executadas
  - impacto: define se o vinculo pode ser efetivado
  - owner: `<preencher_nome_owner_online_frontend>`
  - canal: `<preencher_slack_ou_teams_frontend>`
- `T+15`:
  - trilha: `Audit / Preset identity-federated`
  - evento: evento de `link` validado
  - impacto: transforma acao funcional em prova de cockpit
  - owner: `<preencher_nome_owner_online_frontend>`
  - canal: `<preencher_slack_ou_teams_frontend>`
- `T+25`:
  - trilha: `Banco / audit_logs`
  - evento: SQL confirma os eventos obrigatorios
  - impacto: fecha a prova tecnica
  - owner: `<preencher_nome_owner_online_platform>`
  - canal: `<preencher_slack_ou_teams_platform>`
- `T+35`:
  - trilha: `Gate Agregado Federado`
  - evento: reconciliacao final e decisao `go/no-go`
  - impacto: define se a tentativa sobe para homologada
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`

## Bloqueadores em Curso

- ID: `FD-01`
  - trilha: `auth-service / Diretorio Federado`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - ETA: `2026-07-13`
  - observacao: sem escopo minimo do client tecnico, a tentativa nao deve comecar
- ID: `FD-02`
  - trilha: `Team / Busca Assistida`
  - status: `watching`
  - owner da escalacao: `<preencher_nome_owner_escalacao_frontend>`
  - canal da escalacao: `<preencher_bridge_frontend>`
  - ETA: `2026-07-13`
  - observacao: depende de tenant, operador e principal externo coerentes
- ID: `FD-03`
  - trilha: `Banco / audit_logs`
  - status: `watching`
  - owner da escalacao: `<preencher_nome_owner_escalacao_platform>`
  - canal da escalacao: `<preencher_bridge_platform>`
  - ETA: `2026-07-13`
  - observacao: sem evidencias SQL, a prova tecnica fica incompleta

## Decisoes Operacionais

- manter `status global=pending` ate confirmacao material do runtime, busca, link e reversao
- atualizar este tracking em cada checkpoint material
- nao mover o sign-off para `approved` enquanto `Team`, `Audit` e `audit_logs` nao convergirem

## Hand-off para Sign-Off

- war room: [War Room da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)
- sign-off: [Sign-Off da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-signoff.md)
- run sheet datada: [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)
- decision packet: [Go/No-Go Decision Packet `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-go-no-go-decision-packet.md)
- decisao recomendada: `pending_no_go`
