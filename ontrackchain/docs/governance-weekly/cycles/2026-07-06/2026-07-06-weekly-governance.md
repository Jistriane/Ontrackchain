# Governança Semanal — 2026-07-06

## Leitura do Ciclo

- Baseline técnica: `91%`
- Readiness regulatório: `78%`
- KPI total consolidado: `87%`
- Foco da semana: executar a primeira janela séria com evidências anexáveis e dossier final

## Contexto da Janela Séria

- `window_id`: `stg-2026-07-06-a`
- `mode`: `baseline`
- `environment_name`: `staging-serious`
- run do GitHub Actions: `pending`
- status esperado: `RUN-STG-01` de `ready -> in_progress` ou `ready -> done` (apenas se dossier final estiver `ok`)
- checklist canônico:
  - [Checklist de Evidência Mínima da Primeira Janela Séria](../../../history/first-serious-window-evidence-checklist.md)
- runbook do primeiro disparo:
  - [Runbook do Primeiro Disparo Real](../../../history/first-serious-window-first-dispatch-runbook.md)
- template de sign-off:
  - [Template de Sign-Off da Janela Seria](../../../history/staging-serious-window-signoff-template.md)
- war room desta janela:
  - [War Room da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-war-room.md)
- tracking ao vivo desta janela:
  - [Tracking ao Vivo da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-live-tracking.md)
- sign-off desta janela:
  - [Sign-Off da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-signoff.md)
- folha de preenchimento manual desta janela:
  - [Folha de Preenchimento Manual `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-manual-fill-sheet.md)

## Evidências Revisadas

- artifact `serious-staging-window-stg-2026-07-06-a`: `pending`
- war room status: `no-go`
- tracking ao vivo status: `blocked`
- leitura operacional atual da janela: `pending_execucao` com `no-go` ativo ate preencher handoff, canais, bridges e secrets reais
- overall status: `pending`
- validation status: `pending`
- preflight status: `pending`
- run status: `pending`
- window packet: `pending`
- dossier: `pending`
- homologation: `pending`
- oidc bundle summary: `pending`
- regulatory bundle summary: `pending`

## KPI da Semana

- construção técnica: `91%`
- prontidão regulatória: `78%`
- KPI total consolidado: `87%`
- houve recalibração material?: `nao`
- template detalhado de KPI:
  - [Atualização de KPI 2026-07-01](../../archive/weekly/2026-07-01-kpi-scorecard-update.md)

## Itens Atualizados

- ID: `P0-01`
  - status anterior: `blocked`
  - status atual: `blocked`
  - owner nominal: `Tech Lead Auth`
  - artefato revisado: trilho serio de `OIDC/MFA` e critérios de aceite institucional
  - próxima evidência esperada: evidência externa homologada com `X-MFA-Mode=external_provider`

- ID: `P0-02`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Owner de Integracao AML`
  - artefato revisado: gate `make check-compliance-provider-runtime` e bundle de homologação `AML/KYT live`
  - próxima evidência esperada: execução verde com credenciais reais e bundle anexado

- ID: `P0-03`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Owner de Compliance/Sancoes`
  - artefato revisado: runner `make run-eu-sanctions-window-local` e checker `EU_CONSOLIDATED`
  - próxima evidência esperada: `source_url` tokenizada válida + JSONs `<janela>-eu-sanctions-*.json`

- ID: `RUN-STG-01`
  - status anterior: `ready`
  - status atual: `pending_execucao`
  - owner nominal: `Release Manager Tecnico`
  - artefato revisado: workflow `Staging Serious Window` + artifact `serious-staging-window-stg-2026-07-06-a`
  - próxima evidência esperada: sign-off preenchido com `overall status=ok`, `validation=ok`, `preflight=ok` e `run=ok`

## Itens Blocked

- ID: `P0-01`
  - motivo: homologação formal de identidade forte ainda depende de evidência externa e aceite institucional
  - dependência externa: provider de identidade e validação do fluxo sério com `external_provider`
  - owner da escalação: `Tech Lead Auth`

## Decisões

- a semana fica orientada a executar a primeira janela séria via GitHub Actions, usando `mode=baseline` salvo bloqueio regulatório específico
- enquanto o `no-go` permanecer ativo, a prioridade da semana e preencher a folha manual e rerodar o gate agregado antes de qualquer dispatch real
- antes de qualquer disparo, o war room desta janela precisa sair de `no-go` para `go` ou `go_with_exception`
- o artifact do workflow será tratado como evidência oficial de `RUN-STG-01`
- manter a baseline oficial `91% / 78% / 87%` até nova evidência material publicada na governança semanal
- não promover `P0-02` ou `P0-03` sem artefato real anexável e checker verde correspondente

## Ações da Próxima Semana

- preencher a [Folha de Preenchimento Manual `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-manual-fill-sheet.md) com owners online, canais, bridges e checkpoints reais
- atualizar o [War Room da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-war-room.md) com owners, desbloqueios e checkpoint de `go/no-go`
- executar o workflow `Staging Serious Window` para `stg-2026-07-06-a` apenas se o war room sair de `no-go`
- preencher o sign-off em [Sign-Off da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-signoff.md)
- atualizar este registro com links reais de artifact, dossier, homologation, oidc bundle summary e regulatory bundle summary

## Observações

- este registro deve capturar paths dos artefatos gerados na execução da janela, incluindo homologação e dossier
- se o run falhar, registrar explicitamente o ponto de falha (`validation`, `preflight` ou `run`) e o owner da escalacao
