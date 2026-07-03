# War Room da Janela Seria — `stg-2026-07-06-a`

## Contexto

- data: `2026-07-06`
- window_id: `stg-2026-07-06-a`
- mode: `baseline`
- environment_name: `staging-serious`
- facilitador: `Arquiteto/Responsavel Tecnico`
- objetivo da janela: validar a primeira janela seria com evidencias anexaveis de staging e readiness regulatorio quando aplicavel
- baseline canônica: `91% / 78% / 87%`

## Leitura de Go/No-Go

- status atual: `no-go`
- motivo principal: `handoff` ainda com `Data/Status` pendentes e `.env.staging.private` ainda com placeholders criticos
- risco residual: dependencias externas reais de `OIDC`, `AML/KYT`, `RPC` e feed UE ainda nao homologadas para esta janela
- proximo checkpoint: rerodar `prepare_staging_window.py --validate --preflight` depois do provisionamento por dominio
- hora do proximo checkpoint: `<preencher_HH:MMZ>`
- facilitador online: `<preencher_nome_facilitador_online>`
- canal principal do war room: `<preencher_canal_principal_war_room>`
- bridge de escalacao principal: `<preencher_bridge_go_no_go>`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_platform>`, `<preencher_nome_owner_backup_platform>`, `<preencher_nome_owner_escalacao_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 3: `<preencher_nome_owner_online_auth>`, `<preencher_nome_owner_backup_auth>`, `<preencher_nome_owner_escalacao_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- prioridade 4: `<preencher_nome_owner_online_rpc>`, `<preencher_nome_owner_backup_rpc>`, `<preencher_nome_owner_escalacao_rpc>`, `<preencher_slack_ou_teams_rpc>`, `<preencher_bridge_rpc>`
- prioridade 5: `<preencher_nome_owner_online_compliance>`, `<preencher_nome_owner_backup_compliance>`, `<preencher_nome_owner_escalacao_compliance>`, `<preencher_slack_ou_teams_compliance>`, `<preencher_bridge_compliance>`
- criterio de saida do `no-go`: depois de preencher os placeholders acima, rerodar o gate agregado e exigir `status=ok`
- folha unica de apoio: [Folha de Preenchimento Manual `stg-2026-07-06-a`](2026-07-06-staging-serious-window-manual-fill-sheet.md)

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao final: `go` | `no-go` | `go_with_exception`

## Trilhas do War Room

- `Platform/Operations`
  - owner primario: `<preencher_nome_owner_online_platform>`
  - backup/escalacao: `<preencher_nome_owner_backup_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-01T19:45:00Z`
  - dependencia critica: `POSTGRES_PASSWORD`, `ALERTMANAGER_WEBHOOK_BEARER_TOKEN` e `GRAFANA_ADMIN_PASSWORD` reais
  - comando: `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` e `python scripts/check_staging_env_placeholders.py --file .env.staging.private`
  - evidencia minima: handoff sem `pending` do dominio e placeholders resolvidos
  - criterio de go/no-go: segredos base provisionados e handoff formalizado
  - observacoes: base da stack ainda nao formalizada
- `Auth/OIDC`
  - owner primario: `<preencher_nome_owner_online_auth>`
  - backup/escalacao: `<preencher_nome_owner_backup_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-01T19:45:00Z`
  - dependencia critica: secrets OIDC nao-dev e handoff de `Auth/OIDC`
  - comando: `python scripts/preflight_oidc_serious_env.py`
  - evidencia minima: preflight OIDC verde
  - criterio de go/no-go: secrets reais e handoff `Auth/OIDC` fechados
  - observacoes: `P0-01` continua dependente de evidencia externa
- `Investigation/RPC`
  - owner primario: `<preencher_nome_owner_online_rpc>`
  - backup/escalacao: `<preencher_nome_owner_backup_rpc>`
  - canal de contato: `<preencher_slack_ou_teams_rpc>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-01T19:45:00Z`
  - dependencia critica: `INVESTIGATION_RPC_PRIMARY_URL` e `INVESTIGATION_RPC_FALLBACK_URL` reais
  - comando: `python scripts/preflight_external_integrations.py`
  - evidencia minima: output coerente com `ONTRACKCHAIN_EXPECT_RPC_MODE`
  - criterio de go/no-go: endpoints RPC reais e preflight externo coerente
  - observacoes: dependencia externa de conectividade ainda aberta
- `Compliance/AML`
  - owner primario: `<preencher_nome_owner_online_compliance>`
  - backup/escalacao: `<preencher_nome_owner_backup_compliance>`
  - canal de contato: `<preencher_slack_ou_teams_compliance>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-01T19:45:00Z`
  - dependencia critica: credenciais reais `AML/KYT` e `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada
  - comando: `python scripts/preflight_external_integrations.py` e `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
  - evidencia minima: runtime AML/KYT verde e, quando houver UE, JSONs da janela UE
  - criterio de go/no-go: provider live e feed UE com prova real da janela
  - observacoes: `P0-02` e `P0-03` seguem `ready`, mas sem prova real da janela
- `Gate Agregado da Janela`
  - owner primario: `<preencher_nome_facilitador_online>`
  - backup/escalacao: `<preencher_nome_owner_backup_go_no_go>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-01T19:45:00Z`
  - dependencia critica: todas as trilhas acima verdes ou waived formalmente
  - comando: `python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
  - evidencia minima: `status=ok` no gate agregado
  - criterio de go/no-go: rerun verde do gate agregado com owners online
  - observacoes: ainda nao elegivel para `make run-serious-window-local`

## Bloqueadores Ativos

- ID: `WR-01`
  - trilha: `Platform/Operations`
  - descricao: placeholders criticos de base ainda abertos no `.env.staging.private`
  - owner da escalacao: `<preencher_nome_owner_escalacao_platform>`
  - canal da escalacao: `<preencher_bridge_platform>`
  - tempo alvo: `30 min`
  - status: `open`
- ID: `WR-02`
  - trilha: `Auth/OIDC`
  - descricao: handoff de `Auth/OIDC` ainda sem `Data/Status` reais e secrets OIDC serio nao comprovados
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - tempo alvo: `30 min`
  - status: `open`
- ID: `WR-03`
  - trilha: `Investigation/RPC`
  - descricao: endpoints RPC primario/fallback ainda em placeholder
  - owner da escalacao: `<preencher_nome_owner_escalacao_rpc>`
  - canal da escalacao: `<preencher_bridge_rpc>`
  - tempo alvo: `30 min`
  - status: `open`
- ID: `WR-04`
  - trilha: `Compliance/AML`
  - descricao: provider `AML/KYT live` e URL tokenizada da UE ainda nao homologados para a janela
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance>`
  - canal da escalacao: `<preencher_bridge_compliance>`
  - tempo alvo: `60 min`
  - status: `open`

## Evidencias Revisadas

- `handoff.json`: `artifacts/staging/checks/stg-2026-07-06-precheck2-handoff.json`
- `placeholders.json`: `artifacts/staging/checks/stg-2026-07-06-precheck2-placeholders.json`
- `preflight_oidc_serious_env.py`: `pending`
- `oidc-readiness-bundle.json`: `pending`
- `oidc-readiness-bundle.md`: `pending`
- `preflight_external_integrations.py`: `pending`
- `check-compliance-provider-runtime`: `pending`
- `<janela>-eu-sanctions-preflight.json`: `pending`
- `<janela>-eu-sanctions-sync.json`: `pending`
- `regulatory-readiness-bundle.json`: `pending`
- `regulatory-readiness-bundle.md`: `pending`
- `prepare-staging-window-output.json`: `pending`

## Decisoes

- manter a janela em `no-go` ate os owners resolverem handoff e placeholders por dominio
- nao disparar `run-serious-window-local` nem workflow oficial antes do gate agregado ficar verde
- usar o checklist por owner e a matriz de war room como artefatos oficiais da coordenacao desta janela

## Proximo Passo Autorizado

- acao: provisionar secrets/URLs reais por dominio e preencher `Data/Status` no handoff
- owner: `owners nominais por trilha com coordenacao do facilitador/Release Manager Tecnico`
- canal: `<preencher_canal_principal_war_room>`
- criterio para seguir: rerun de `prepare_staging_window.py --validate --preflight` com `status=ok`

## Resultado Final do War Room

- decisao final: `no-go`
- justificativa: a janela ainda nao possui prontidao operacional minima para producao de evidencias reais
- artefato de sign-off relacionado: [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)
- tracking ao vivo relacionado: [Tracking ao Vivo da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-live-tracking.md)
