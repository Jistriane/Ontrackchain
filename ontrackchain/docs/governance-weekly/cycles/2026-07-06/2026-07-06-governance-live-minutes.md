# Ata ao Vivo da Governança — 2026-07-06

## Dados do Encontro

- data:
- horário:
- facilitador:
- participantes:

## Baseline de Entrada

- técnico: `91%`
- regulatório: `78%`
- consolidado: `87%`
- decisão vigente: `go` para validação séria controlada e `no-go` para produção regulada forte

## Evidências Novas Apresentadas

- `P0-02` `AML/KYT live`: bundle regulatorio local executado; sem credencial real homologada
- `P0-03` feed UE real: checks locais gerados; URL tokenizada real ainda pendente
- `P0-01` `OIDC + MFA`: bundle OIDC local executado; homologacao real ainda pendente
- owners/SLA: handoff ainda com campos obrigatorios pendentes por dominio
- retention/recovery: sem nova evidencia executada nesta rodada
- janela `stg-2026-07-06-a`: validacao agregada de artifact `status=ok`; execucao ponta a ponta `status=failed` por gates locais
- rerun factual em `2026-07-03T21:40Z`:
  - `prepare_staging_window.py --validate --preflight` com `status=failed` (`generated_at=2026-07-03T21:40:40Z`)
  - `run_staging_window.py` com `status=failed` (`generated_at=2026-07-03T21:40:45Z`)
  - pendencias mantidas: `12` placeholders e `8` campos obrigatorios de handoff
- rerun factual em `2026-07-03T23:04Z` (comando unico):
  - `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-06-a`
  - snapshot consolidado `status=failed` (`generated_at=2026-07-03T23:04:23Z`)
  - delta de snapshot com semaforo executivo `amarelo` e `delta +0` em placeholders/handoff
- rerun factual mais recente (comando unico):
  - `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-06-a`
  - snapshot consolidado mantido em `status=failed`
  - bloqueios mantidos: `12` placeholders e `8` campos de handoff

## Status Decidido no Encontro

- `P0-02`
  - status anterior: `ready`
  - status atual: `ready`
  - evidência: `stg-2026-07-06-a-regulatory-readiness-bundle.json`
  - observação: sem credencial real, bloqueio externo mantido
- `P0-03`
  - status anterior: `ready`
  - status atual: `ready`
  - evidência: `stg-2026-07-06-a-eu-sanctions-preflight.json`
  - observação: sem URL real tokenizada, bloqueio externo mantido
- `P0-01`
  - status anterior: `blocked`
  - status atual: `blocked`
  - evidência: `stg-2026-07-06-a-oidc-readiness-bundle.json`
  - observação: homologacao real ainda pendente
- owners/SLA
  - status anterior: `ready_for_approval`
  - status atual: `ready_for_approval`
  - evidência: `handoff-stg-2026-07-06-a.json`
  - observação: `date/status` pendentes nos 4 dominios obrigatorios
- retention/recovery
  - status anterior: `ready_for_approval`
  - status atual: `ready_for_approval`
  - evidência: sem nova evidencia
  - observação: manter em trilha de aceite formal
- janela séria
  - status anterior: `pre-serious-window`
  - status atual: `pre-serious-window`
  - evidência: `make validate-serious-window-artifact-local` (`status=ok`), `run_staging_window.py` (`status=failed`) e `stg-2026-07-06-a-status-snapshot-delta.md` (`semaforo=amarelo`)
  - observação: pronta para controle de artifact, nao pronta para execucao plena

## Decisões

-

## Bloqueios Mantidos

- placeholders obrigatorios em `.env.staging.private` ainda nao preenchidos (`12`)
- handoff com `date/status` pendentes em `Auth/OIDC`, `Compliance/AML`, `Investigation/RPC` e `Platform/Operations`

## Ações Imediatas

- nota editorial: na pipeline atual, o resumo curto de comunicacao pode aparecer como `*-comms-summary.md`; nesta janela historica, o papel equivalente ficou concentrado no `governance-dashboard` e no `war-room-action-plan`

- atualizar pacote de governanca local em comando unico:
  - `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-06-a`
  - checklist de desbloqueio: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-unblock-checklist.md`
  - resumo executivo curto: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-governance-dashboard.md`
- atualizar plano automatico por dominio:
  - `make render-staging-war-room-action-plan WINDOW_ID=stg-2026-07-06-a`
  - referencia: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-war-room-action-plan.md`
- preencher segredos reais em canal seguro para os dominios `P0-01`, `P0-02`, `P0-03`
- atualizar `docs/staging-env-ownership.md` com `date/status` por dominio
- rerodar `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`

## Decisão Final de Baseline

- manter baseline atual
- manter KPI atual (`91% / 78% / 87%`)
- revisar em reunião seguinte

## Observação

Nenhum item deve mudar de status sem evidência nova revisada no próprio encontro.
