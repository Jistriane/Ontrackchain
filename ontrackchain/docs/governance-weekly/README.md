# Registros Semanais de Governança

## Objetivo

Centralizar os registros gerados a partir do [Runbook de Governança Semanal](../project-weekly-governance-runbook.md).

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

## Registros Disponíveis

- [Governança Semanal 2026-06-29](2026-06-29-weekly-governance.md)
- [Governança Semanal 2026-06-30](2026-06-30-weekly-governance.md)
- [Governança Semanal 2026-07-06](2026-07-06-weekly-governance.md)
- [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)
