# War Room da Janela Seria — `stg-2026-07-13-a`

## Contexto

- data: `2026-07-13`
- window_id: `stg-2026-07-13-a`
- mode: `dress_rehearsal_controlado`
- environment_name: `staging-serious`
- facilitador: `Release Manager Tecnico`
- objetivo da janela: executar a primeira tentativa combinada real de `P0-02 + P0-03` e converter a consolidacao `P0-04` em artefato revisavel
- baseline canonica: `93% / 79% / 89%`
- run sheet datada: [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)
- bridge quick-fill: [Bridge Quick-Fill `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-bridge-quick-fill.md)
- decision packet: [Go/No-Go Decision Packet `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-go-no-go-decision-packet.md)

## Leitura de Go/No-Go

- status atual: `pending_no_go`
- motivo principal: aguardando insumos reais de `P0-02` e `P0-03`, confirmacao dos owners online e checkpoint agregado verde
- risco residual: `P0-01` continua bloqueado por provider OIDC serio nao homologado; a janela combinada nao deve mascarar esse risco
- proximo checkpoint: validar owners online, confirmar credencial AML/KYT real e URL tokenizada do feed UE, depois rerodar o gate agregado
- hora do proximo checkpoint: `<preencher_HH:MMZ>`
- facilitador online: `<preencher_nome_facilitador_online>`
- canal principal do war room: `<preencher_canal_principal_war_room>`
- bridge de escalacao principal: `<preencher_bridge_go_no_go>`

## Preencher Primeiro

- prioridade 1: `<preencher_nome_facilitador_online>`, `<preencher_canal_principal_war_room>`, `<preencher_bridge_go_no_go>`, `<preencher_HH:MMZ>`
- prioridade 2: `<preencher_nome_owner_online_compliance_aml>`, `<preencher_nome_owner_backup_compliance_aml>`, `<preencher_nome_owner_escalacao_compliance_aml>`, `<preencher_slack_ou_teams_compliance_aml>`, `<preencher_bridge_compliance_aml>`
- prioridade 3: `<preencher_nome_owner_online_compliance_backend>`, `<preencher_nome_owner_backup_compliance_backend>`, `<preencher_nome_owner_escalacao_compliance_backend>`, `<preencher_slack_ou_teams_compliance_backend>`, `<preencher_bridge_compliance_backend>`
- prioridade 4: `<preencher_nome_owner_online_platform>`, `<preencher_nome_owner_backup_platform>`, `<preencher_nome_owner_escalacao_platform>`, `<preencher_slack_ou_teams_platform>`, `<preencher_bridge_platform>`
- prioridade 5: `<preencher_nome_owner_online_auth>`, `<preencher_nome_owner_backup_auth>`, `<preencher_nome_owner_escalacao_auth>`, `<preencher_slack_ou_teams_auth>`, `<preencher_bridge_auth>`
- criterio de saida do `pending_no_go`: owners online, gate agregado verde e insumos reais confirmados para `P0-02` e `P0-03`
- folha unica de apoio: [Run Sheet Datada `stg-2026-07-13-a`](./2026-07-13-first-combined-serious-window-run-sheet.md)

## Matriz Operacional Sugerida

| Frente | Papel sugerido | Dominio de origem | Ack minimo antes do `go/no-go` | Fonte de handoff |
| --- | --- | --- | --- | --- |
| Gate agregado | `Release Manager Tecnico` | `Arquitetura / Governanca` | checkpoint agregado registrado + bridge ativa + owners online confirmados | run sheet datada + war room |
| `P0-02` AML/KYT | `Compliance/Backend Lead` | `Compliance/AML` | credencial real validada + checker verde + `request_id` preenchido | `docs/staging-env-ownership.md` + homologacao externa |
| `P0-03` Feed UE | `Compliance/Ops Lead` | `Compliance/Backend` | URL tokenizada validada + JSONs da janela UE + correlator coerente | `docs/staging-env-ownership.md` + run sheet datada |
| `P0-04` consolidado | `Platform/SRE` | `Platform/Operations` | bundle regulatorio executado + validacao final do artifact `ok` | bundle regulatorio + dossier |
| `P0-01` Auth/OIDC | `Backend/Auth` | `Security/Auth` | bloqueio explicitado ou bundle OIDC revisavel | bundle OIDC + ownership OIDC |

## Handoff Minimo Antes do Ack

- `Gate agregado`: preencher `facilitador online`, `canal principal`, `bridge principal` e `hora do proximo checkpoint`
- `P0-02`: preencher `compliance_request_id`, `homologation_request_id`, `request_id_match`, `runtime_output` e `homologation_json`
- `P0-03`: preencher `eu_request_id`, `eu_consolidated_status`, `last_sync_status`, `source_url_matches_expected` e paths dos JSONs
- `P0-04`: preencher `bundle_json`, `bundle_md`, `dossier_json` e `artifact_validation_status`
- `P0-01`: preencher owner online, status do bloqueio e, se houver avanço real, o path do bundle OIDC

## Status Permitidos

- trilha: `pending` | `in_progress` | `blocked` | `ready` | `ready_for_validation` | `done` | `waived`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- decisao final: `go` | `no-go` | `go_with_exception`

## Trilhas do War Room

- `P0-02 / Compliance AML-KYT`
  - owner primario: `<preencher_nome_owner_online_compliance_aml>`
  - backup/escalacao: `<preencher_nome_owner_backup_compliance_aml>`
  - canal de contato: `<preencher_slack_ou_teams_compliance_aml>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: credencial real do provider AML/KYT no ambiente alvo
  - comando: `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
  - evidencia minima: JSON do runtime verde + homologacao externa preservada + `request_id`
  - criterio de go/no-go: credencial real validada e correlator reconciliado com a homologacao
  - observacoes: candidato mais proximo a mover a baseline de `88%`
- `P0-03 / Feed UE`
  - owner primario: `<preencher_nome_owner_online_compliance_backend>`
  - backup/escalacao: `<preencher_nome_owner_backup_compliance_backend>`
  - canal de contato: `<preencher_slack_ou_teams_compliance_backend>`
  - status: `ready`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: URL tokenizada real e sincronizacao coerente da janela UE
  - comando: `make run-eu-sanctions-window-local WINDOW_ID=stg-2026-07-13-a` e `make check-eu-sanctions-window`
  - evidencia minima: JSONs de `preflight` e `sync` + `source_url_matches_expected=true` + `request_id`
  - criterio de go/no-go: feed real validado com correlator e prova persistida
  - observacoes: segunda metade obrigatoria para promover `P0-04`
- `P0-04 / Bundle Regulatorio`
  - owner primario: `<preencher_nome_owner_online_platform>`
  - backup/escalacao: `<preencher_nome_owner_backup_platform>`
  - canal de contato: `<preencher_slack_ou_teams_platform>`
  - status: `pending`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: `P0-02` e `P0-03` com prova revisavel na mesma janela
  - comando: `make run-regulatory-readiness-bundle-local WINDOW_ID=stg-2026-07-13-a`
  - evidencia minima: bundle oficial em `ready_for_validation` + validacao final do artifact `ok`
  - criterio de go/no-go: consolidacao sem incoerencia de correlator
  - observacoes: principal ponte documental para `90%+`
- `P0-01 / Auth OIDC`
  - owner primario: `<preencher_nome_owner_online_auth>`
  - backup/escalacao: `<preencher_nome_owner_backup_auth>`
  - canal de contato: `<preencher_slack_ou_teams_auth>`
  - status: `blocked`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: provider OIDC serio homologado e MFA institucional
  - comando: `make run-oidc-readiness-bundle-local WINDOW_ID=stg-2026-07-13-a BASE_URL=http://localhost:8080`
  - evidencia minima: bundle OIDC com `readiness_status=ready_for_validation`
  - criterio de go/no-go: nao bloquear a janela combinada, mas impedir promocao institucional completa
  - observacoes: risco residual permanece vermelho ate homologacao externa
- `Gate Agregado da Janela`
  - owner primario: `<preencher_nome_facilitador_online>`
  - backup/escalacao: `<preencher_nome_owner_backup_go_no_go>`
  - canal de contato: `<preencher_canal_principal_war_room>`
  - status: `pending`
  - ultima atualizacao: `2026-07-13T00:00:00Z`
  - dependencia critica: `P0-02` e `P0-03` com insumos reais + owners online + gate agregado verde
  - comando: `python3 scripts/prepare_staging_window.py --window-id stg-2026-07-13-a --mode baseline --private-env-file .env.staging.private --validate --preflight`
  - evidencia minima: `status=ok` no gate agregado antes do disparo de execucao real
  - criterio de go/no-go: somente seguir para workflow oficial com `go` ou `go_with_exception` formal
  - observacoes: janela planejada para `2026-07-17`, mas pode antecipar se os insumos chegarem

## Bloqueadores Ativos

- ID: `WR-01`
  - trilha: `P0-02 / Compliance AML-KYT`
  - descricao: credencial real do provider AML/KYT ainda nao confirmada neste ciclo
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance_aml>`
  - canal da escalacao: `<preencher_bridge_compliance_aml>`
  - tempo alvo: `2026-07-14`
  - status: `open`
- ID: `WR-02`
  - trilha: `P0-03 / Feed UE`
  - descricao: URL tokenizada real do feed UE ainda nao confirmada neste ciclo
  - owner da escalacao: `<preencher_nome_owner_escalacao_compliance_backend>`
  - canal da escalacao: `<preencher_bridge_compliance_backend>`
  - tempo alvo: `2026-07-14`
  - status: `open`
- ID: `WR-03`
  - trilha: `P0-01 / Auth OIDC`
  - descricao: provider OIDC serio e homologacao institucional de MFA seguem pendentes
  - owner da escalacao: `<preencher_nome_owner_escalacao_auth>`
  - canal da escalacao: `<preencher_bridge_auth>`
  - tempo alvo: `2026-07-15`
  - status: `open`
- ID: `WR-04`
  - trilha: `Gate Agregado da Janela`
  - descricao: owners online, bridge e checkpoint agregado ainda nao registrados para a tentativa datada
  - owner da escalacao: `<preencher_nome_owner_escalacao_platform>`
  - canal da escalacao: `<preencher_bridge_platform>`
  - tempo alvo: `2026-07-17`
  - status: `watching`

## Evidencias Revisadas

- `run sheet datada`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-first-combined-serious-window-run-sheet.md`
- `governanca semanal operacional`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-weekly-governance-operational.md`
- `execucao por evidencia`: `docs/governance-weekly/cycles/2026-07-13/2026-07-13-maturity-evidence-execution-draft.md`
- `artifacts/staging/checks/stg-2026-07-13-a-oidc-readiness-bundle.json`: `pending`
- `artifacts/staging/checks/stg-2026-07-13-a-regulatory-readiness-bundle.json`: `pending`
- `artifacts/staging/dossiers/stg-2026-07-13-a-regulatory-readiness-bundle.md`: `pending`
- `artifacts/staging/dossiers/stg-2026-07-13-a-dossier.json`: `pending`

## Decisoes

- manter a tentativa `stg-2026-07-13-a` em `pending_no_go` ate confirmacao dos insumos reais e owners online
- tratar esta tentativa como `dress_rehearsal_controlado` ate decisao explicita de promover para `go_no_go_formal`
- nao promover `P0-04` nem `RUN-STG-01` sem prova combinada de `P0-02` e `P0-03`

## Proximo Passo Autorizado

- acao: preencher owners e bridges, confirmar credencial AML/KYT e URL UE tokenizada, depois rerodar o gate agregado
- owner: `Release Manager Tecnico` com coordenacao de `Compliance/AML`, `Compliance/Backend`, `Platform/SRE` e `Security/Auth`
- canal: `<preencher_canal_principal_war_room>`
- criterio para seguir: gate agregado `ok` + `P0-02` e `P0-03` aptos a gerar artefatos revisaveis

## Resultado Final do War Room

- decisao final: `pending_no_go`
- justificativa: a tentativa esta operacionalmente preparada, mas ainda nao possui insumos reais nem owners confirmados para o disparo
- artefato de sign-off relacionado: [Sign-Off da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-signoff.md)
- tracking ao vivo relacionado: [Tracking ao Vivo da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-live-tracking.md)
