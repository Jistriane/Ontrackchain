# Tracking ao Vivo da Janela Seria — `stg-2026-07-13-a`

## Contexto Operacional

- data: `2026-07-13`
- window_id: `stg-2026-07-13-a`
- mode: `dress_rehearsal_controlado`
- environment_name: `staging-serious`
- facilitador: `Release Manager Tecnico`
- status global: `pending`
- checkpoint atual: `aguardando owners online e validacao dos insumos reais de P0-02/P0-03`
- ultima atualizacao: `pre-run do ciclo 2026-07-13`
- cadencia de atualizacao recomendada: `15 min`
- run sheet de referencia: [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `ready_for_validation` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao recomendada: `pending_no_go` | `pending_go_with_exception` | `pending_go` | `approved`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_compliance_aml>`, `<preencher_slack_ou_teams_compliance_aml>`, `<preencher_bridge_compliance_aml>`
- prioridade 3: `<preencher_nome_owner_online_compliance_backend>`, `<preencher_slack_ou_teams_compliance_backend>`, `<preencher_bridge_compliance_backend>`
- prioridade 4: `<preencher_nome_owner_online_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 5: `<preencher_nome_owner_online_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- criterio de saida do `pending`: owners confirmados, insumos reais validados e gate agregado verde
- folha unica de apoio: [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)

## Painel de Trilhas

- `P0-02 / Compliance AML-KYT`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_compliance_aml>`
  - canal de contato: `<preencher_slack_ou_teams_compliance_aml>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: checker e correlacao documental preparados; credencial real ainda ausente
  - proximo checkpoint: validar credencial real e executar `check-compliance-provider-runtime`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-14`
  - dependencia ativa: credencial AML/KYT real
  - bridge de escalacao: `<preencher_bridge_compliance_aml>`
  - observacoes: primeiro item com maior potencial de mudar a baseline
- `P0-03 / Feed UE`
  - status atual: `ready`
  - responsavel online: `<preencher_nome_owner_online_compliance_backend>`
  - canal de contato: `<preencher_slack_ou_teams_compliance_backend>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: runner, checker e correlator preparados; URL tokenizada real ainda ausente
  - proximo checkpoint: validar URL UE tokenizada e executar a janela `stg-2026-07-13-a`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-14`
  - dependencia ativa: `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` real
  - bridge de escalacao: `<preencher_bridge_compliance_backend>`
  - observacoes: precisa convergir com `P0-02` para destravar `P0-04`
- `P0-04 / Bundle Regulatorio`
  - status atual: `pending`
  - responsavel online: `<preencher_nome_owner_online_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: sem execucao real ainda, aguardando provas de `P0-02` e `P0-03`
  - proximo checkpoint: executar o bundle regulatorio e validar o artifact final
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-17`
  - dependencia ativa: `P0-02` e `P0-03` em `ready_for_validation`
  - bridge de escalacao: `<preencher_bridge_platform>`
  - observacoes: ponte obrigatoria para discutir `90%+`
- `P0-01 / Auth OIDC`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_owner_online_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - ack do owner: `no`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: bundle e readiness modelados, mas provider serio continua ausente
  - proximo checkpoint: homologar provider serio e rerodar o bundle OIDC
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-15`
  - dependencia ativa: provider OIDC serio e MFA homologado
  - bridge de escalacao: `<preencher_bridge_auth>`
  - observacoes: risco institucional ainda vermelho
- `Gate Agregado da Janela`
  - status atual: `pending`
  - responsavel online: `<preencher_nome_facilitador_online>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - ack do owner: `yes`
  - ultima atualizacao: `pre-run do ciclo 2026-07-13`
  - ultimo checkpoint: tentativa datada criada com run sheet, war room e tracking
  - proximo checkpoint: `prepare_staging_window.py --validate --preflight`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `2026-07-17`
  - dependencia ativa: owners online e insumos reais disponiveis
  - bridge de escalacao: `<preencher_bridge_go_no_go>`
  - observacoes: nao disparar execucao final sem `go` formal

## Linha do Tempo

- `T-30`:
  - trilha: `Gate Agregado da Janela`
  - evento: owners, bridge e janela datada confirmados
  - impacto: habilita o checkpoint agregado inicial
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`
- `T-15`:
  - trilha: `P0-02 / Compliance AML-KYT`
  - evento: credencial real AML/KYT validada ou recusada para o ciclo
  - impacto: define se a janela pode perseguir `89%`
  - owner: `<preencher_nome_owner_online_compliance_aml>`
  - canal: `<preencher_slack_ou_teams_compliance_aml>`
- `T+00`:
  - trilha: `P0-03 / Feed UE`
  - evento: URL tokenizada do feed UE validada ou recusada para o ciclo
  - impacto: define se `P0-04` podera ser promovido honestamente
  - owner: `<preencher_nome_owner_online_compliance_backend>`
  - canal: `<preencher_slack_ou_teams_compliance_backend>`
- `T+20`:
  - trilha: `P0-04 / Bundle Regulatorio`
  - evento: bundle consolidado executado, se `P0-02` e `P0-03` estiverem verdes
  - impacto: transforma readiness em prova revisavel
  - owner: `<preencher_nome_owner_online_platform>`
  - canal: `<preencher_slack_ou_teams_platform>`
- `T+45`:
  - trilha: `Gate Agregado da Janela`
  - evento: reconciliacao final e decisao `go/no-go`
  - impacto: define se a janela segue para formalizacao ou novo rerun controlado
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`

## Bloqueadores em Curso

- ID: `WR-01`
  - trilha: `P0-02 / Compliance AML-KYT`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance_aml>`
  - canal da escalacao: `<preencher_bridge_compliance_aml>`
  - ETA: `2026-07-14`
  - observacao: sem credencial real, o ciclo continua apenas documental
- ID: `WR-02`
  - trilha: `P0-03 / Feed UE`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance_backend>`
  - canal da escalacao: `<preencher_bridge_compliance_backend>`
  - ETA: `2026-07-14`
  - observacao: sem URL tokenizada, o correlator do feed nao pode ser validado
- ID: `WR-03`
  - trilha: `P0-01 / Auth OIDC`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - ETA: `2026-07-15`
  - observacao: nao impede o dress rehearsal combinado, mas impede o fechamento institucional completo

## Decisoes Operacionais

- manter `status global=pending` ate confirmacao material de `P0-02` e `P0-03`
- atualizar este tracking em cada checkpoint material do war room
- nao mover o sign-off para `approved` ou `approved_with_exception` enquanto `P0-04` nao estiver ao menos em `ready_for_validation`

## Hand-off para Sign-Off

- war room: [War Room da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-war-room.md)
- sign-off: [Sign-Off da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-signoff.md)
- run sheet datada: [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)
- artefato OIDC esperado para `P0-01`: `artifacts/staging/checks/stg-2026-07-13-a-oidc-readiness-bundle.json`
- artefato regulatorio esperado para `P0-02/P0-03`: `artifacts/staging/checks/stg-2026-07-13-a-regulatory-readiness-bundle.json`
- dossie executivo esperado: `artifacts/staging/dossiers/stg-2026-07-13-a-dossier.json`
- snapshot consolidado esperado: `docs/governance-weekly/generated/windows/stg-2026-07-13-a/stg-2026-07-13-a-consolidated.json`
- comando unico recomendado: `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-13-a`
- decisao recomendada: `pending_no_go`

