# Tracking ao Vivo da Janela Seria — `stg-2026-07-06-a`

## Contexto Operacional

- data: `2026-07-06`
- window_id: `stg-2026-07-06-a`
- mode: `baseline`
- environment_name: `staging-serious`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `blocked`
- checkpoint atual: `refresh-staging-war-room-governance-local` executado; status mantido `blocked` por `placeholder_check` e `handoff_check`
- ultima atualizacao: `ultimo rerun local via comando unico`
- cadencia de atualizacao recomendada: `15 min`
- plano de acao de referencia: [Plano de Acao do War Room `stg-2026-07-06-a`](stg-2026-07-06-a-war-room-action-plan.md)

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao recomendada: `pending_no_go` | `pending_go_with_exception` | `pending_go` | `approved`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 3: `<preencher_nome_owner_online_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- prioridade 4: `<preencher_nome_owner_online_rpc>`, `<preencher_slack_ou_teams_rpc>`, `<preencher_bridge_rpc>`
- prioridade 5: `<preencher_nome_owner_online_compliance>`, `<preencher_slack_ou_teams_compliance>`, `<preencher_bridge_compliance>`
- criterio de saida do `blocked`: depois de preencher os placeholders acima, atualizar o tracking e rerodar `prepare_staging_window.py --validate --preflight`
- folha unica de apoio: [Folha de Preenchimento Manual `stg-2026-07-06-a`](2026-07-06-staging-serious-window-manual-fill-sheet.md)

## Painel de Trilhas

- `Platform/Operations`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_owner_online_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - ack do owner: `no`
  - ultima atualizacao: `ultimo rerun local via comando unico`
  - ultimo checkpoint: `placeholders.json` manteve `POSTGRES_PASSWORD`, `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`, `GRAFANA_ADMIN_PASSWORD`
  - proximo checkpoint: provisionar segredos base e atualizar handoff
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `30 min`
  - dependencia ativa: `POSTGRES_PASSWORD`, `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`, `GRAFANA_ADMIN_PASSWORD`
  - bridge de escalacao: `<preencher_bridge_platform>`
  - observacoes: base da stack ainda nao formalizada
- `Auth/OIDC`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_owner_online_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - ack do owner: `no`
  - ultima atualizacao: `ultimo rerun local via comando unico`
  - ultimo checkpoint: handoff de `Auth/OIDC` ainda sem `date/status`; placeholders OIDC mantidos
  - proximo checkpoint: provisionar secrets OIDC serio e rodar preflight OIDC
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `30 min`
  - dependencia ativa: `KEYCLOAK_ADMIN_PASSWORD`, `KEYCLOAK_B2B_CLIENT_SECRET`, `JWT_HS256_SECRET`, `MFA_TOTP_SECRET`
  - bridge de escalacao: `<preencher_bridge_auth>`
  - observacoes: depende de evidencia externa de identidade
- `Investigation/RPC`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_owner_online_rpc>`
  - canal de contato: `<preencher_slack_ou_teams_rpc>`
  - ack do owner: `no`
  - ultima atualizacao: `ultimo rerun local via comando unico`
  - ultimo checkpoint: endpoints RPC primario/fallback ainda em placeholder
  - proximo checkpoint: preencher RPC primario/fallback e rerodar preflight externo
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `30 min`
  - dependencia ativa: `INVESTIGATION_RPC_PRIMARY_URL`, `INVESTIGATION_RPC_FALLBACK_URL`
  - bridge de escalacao: `<preencher_bridge_rpc>`
  - observacoes: dependencia externa de conectividade
- `Compliance/AML`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_owner_online_compliance>`
  - canal de contato: `<preencher_slack_ou_teams_compliance>`
  - ack do owner: `no`
  - ultima atualizacao: `ultimo rerun local via comando unico`
  - ultimo checkpoint: provider AML/KYT e feed UE tokenizado continuam sem insumo real
  - proximo checkpoint: provisionar credenciais AML/KYT e URL UE tokenizada
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `60 min`
  - dependencia ativa: `COMPLIANCE_TRM_SCREENING_URL`, `COMPLIANCE_TRM_API_KEY`, `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
  - bridge de escalacao: `<preencher_bridge_compliance>`
  - observacoes: `P0-02` e `P0-03` ainda sem artefato real
- `Gate Agregado da Janela`
  - status atual: `blocked`
  - responsavel online: `<preencher_nome_facilitador_online>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - ack do owner: `yes`
  - ultima atualizacao: `ultimo rerun local via comando unico`
  - ultimo checkpoint: `prepare_staging_window` e `run_staging_window` com `status=failed`; delta com semaforo `amarelo`
  - proximo checkpoint: executar `prepare_staging_window.py --validate --preflight`
  - hora do proximo checkpoint: `<preencher_HH:MMZ>`
  - ETA desbloqueio: `15 min`
  - dependencia ativa: todas as trilhas anteriores precisam sair de `blocked`
  - bridge de escalacao: `<preencher_bridge_go_no_go>`
  - observacoes: ainda nao elegivel para `run-serious-window-local`

## Linha do Tempo

- `T-00`:
  - trilha: `Gate Agregado da Janela`
  - evento: janela marcada como `no-go` no war room inicial
  - impacto: bloqueia disparo local e workflow oficial
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`
- `T+05`:
  - trilha: `Platform/Operations`
  - evento: confirmado que secrets base ainda estao em placeholder
  - impacto: impede progresso das demais trilhas
  - owner: `<preencher_nome_owner_online_platform>`
  - canal: `<preencher_slack_ou_teams_platform>`
- `T+10`:
  - trilha: `Compliance/AML`
  - evento: confirmado que provider live e feed UE ainda nao possuem prova real da janela
  - impacto: impede qualquer leitura honesta de `go_with_exception`
  - owner: `<preencher_nome_owner_online_compliance>`
  - canal: `<preencher_slack_ou_teams_compliance>`
- `T+15`:
  - trilha: `Gate Agregado da Janela`
  - evento: rerun do gate agregado e run ponta a ponta executados sem mudanca de status
  - impacto: `no-go` mantido por `placeholder_check` e `handoff_check`
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`
- `T+20`:
  - trilha: `Gate Agregado da Janela`
  - evento: comando unico `refresh-staging-war-room-governance-local` executado com snapshot e delta atualizados
  - impacto: sem progresso material (`delta +0`), semaforo executivo `amarelo`, `no-go` mantido
  - owner: `<preencher_nome_facilitador_online>`
  - canal: `<preencher_canal_principal_war_room>`

## Bloqueadores em Curso

- ID: `WR-01`
  - trilha: `Platform/Operations`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_platform>`
  - canal da escalacao: `<preencher_bridge_platform>`
  - ETA: `30 min`
  - observacao: resolver segredos base primeiro reduz risco de retrabalho
- ID: `WR-02`
  - trilha: `Auth/OIDC`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - ETA: `30 min`
  - observacao: depende de handoff e preflight OIDC verde
- ID: `WR-03`
  - trilha: `Investigation/RPC`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_rpc>`
  - canal da escalacao: `<preencher_bridge_rpc>`
  - ETA: `30 min`
  - observacao: precisa de endpoints reais antes do preflight externo
- ID: `WR-04`
  - trilha: `Compliance/AML`
  - status: `open`
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance>`
  - canal da escalacao: `<preencher_bridge_compliance>`
  - ETA: `60 min`
  - observacao: depende de credenciais AML/KYT e URL UE tokenizada

## Decisoes Operacionais

- manter `status global=blocked` ate o gate agregado ser rerodado com insumos reais
- atualizar este tracking em cada checkpoint material do war room
- nao mover o sign-off para `approved` nem `approved_with_exception` enquanto qualquer `WR-*` estiver aberto

## Hand-off para Sign-Off

- war room: [War Room da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-war-room.md)
- sign-off: [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)
- artefato OIDC esperado para `P0-01`: `artifacts/staging/checks/stg-2026-07-06-a-oidc-readiness-bundle.json` e `artifacts/staging/dossiers/stg-2026-07-06-a-oidc-readiness-bundle.md`
- artefato regulatório esperado para `P0-02/P0-03`: `artifacts/staging/checks/stg-2026-07-06-a-regulatory-readiness-bundle.json` e `artifacts/staging/dossiers/stg-2026-07-06-a-regulatory-readiness-bundle.md`
- snapshot consolidado esperado: `artifacts/staging/checks/stg-2026-07-06-a-status-snapshot.json`
- dashboard executivo esperado: `docs/governance-weekly/stg-2026-07-06-a-governance-dashboard.md`
- checklist de desbloqueio esperado: `docs/governance-weekly/stg-2026-07-06-a-unblock-checklist.md`
- resumo de comunicacao esperado: `docs/governance-weekly/stg-2026-07-06-a-war-room-action-plan.md`
- comando unico recomendado: `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-06-a`
- delta esperado: `docs/governance-weekly/stg-2026-07-06-a-status-snapshot-delta.md`
- decisao recomendada: `pending_no_go`
- owner do proximo passo: `owners nominais por trilha com coordenacao do facilitador/Release Manager Tecnico`
- canal do proximo passo: `<preencher_canal_principal_war_room>`
