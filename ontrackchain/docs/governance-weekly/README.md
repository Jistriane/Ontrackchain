# Registros Semanais de Governança

## Objetivo

Centralizar os registros gerados a partir do [Runbook de Governança Semanal](../project-weekly-governance-runbook.md).

## Escopo Canonico

Use esta pasta para:

- registrar snapshots semanais, war rooms, tracking ao vivo, sign-offs e evidencias fechadas por ciclo
- preservar historico operacional e executivo sem sobrescrever o estado de semanas anteriores
- anexar a trilha documental de uma janela seria especifica depois que ela existir de fato

Nao use esta pasta como fonte primaria para:

- descrever o fluxo tecnico canônico de deploy: use [Deploy e Staging](../deploy-and-staging.md)
- definir gates formais ou criterio executivo de promocao: use [Gates de Release para Staging Serio](../project-release-gates.md)
- manter checklists operacionais genericos sem contexto de ciclo: use os documentos canônicos em `docs/`

Cada arquivo desta pasta deve representar um ciclo semanal fechado, contendo:

- leitura do ciclo
- contexto da janela seria, quando aplicavel
- evidências revisadas
- itens atualizados
- itens `blocked`
- decisões
- ações da próxima semana

## Convenção de Nome

Formato recomendado:

- `YYYY-MM-DD-weekly-governance.md`

Exemplo:

- `2026-06-29-weekly-governance.md`

## Regras de Uso

1. criar um novo arquivo por semana
2. não sobrescrever o registro da semana anterior
3. registrar apenas evidências reais revisadas no ciclo
4. manter alinhamento entre este registro, a [Matriz Operacional de Execução para 95%](../project-operational-execution-board.md) e o [Board de Prioridades do Projeto](../project-priority-board.md)
5. quando houver janela séria via GitHub Actions, registrar `window_id`, `environment_name`, link do run e artifact `serious-staging-window-<janela>`

## Template

- [Template de Registro Semanal](_template-weekly-governance.md)
- [Template de Atualizacao de KPI](_template-kpi-scorecard-update.md)

## Registros Disponíveis

- [Governança Semanal 2026-06-29](2026-06-29-weekly-governance.md)
- [Governança Semanal 2026-06-30](2026-06-30-weekly-governance.md)
- [Atualização de KPI 2026-07-01](2026-07-01-kpi-scorecard-update.md)
- [Governança Semanal 2026-07-01](2026-07-01-weekly-governance.md)
- [Readiness Check da Janela Seria 2026-07-01](2026-07-01-staging-serious-window-readiness-check.md)
- [Template de War Room da Janela Seria](_template-staging-serious-window-war-room.md)
- [Template de Tracking ao Vivo da Janela Seria](_template-staging-serious-window-live-tracking.md)
- [Governança Semanal 2026-07-06](2026-07-06-weekly-governance.md)
- [War Room da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-war-room.md)
- [Tracking ao Vivo da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-live-tracking.md)
- [Folha de Preenchimento Manual `stg-2026-07-06-a`](2026-07-06-staging-serious-window-manual-fill-sheet.md)
- [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)
