# Historico e Metricas de Gate

## Objetivo

Concentrar o historico agregado de gates, dashboards e metricas usadas para leitura executiva de bloqueio ou liberacao de operacoes.

Use esta pasta para:

- dashboards consolidados de gate
- metricas em Markdown
- metricas em JSON

## Artefatos Disponiveis

- [Dashboard de Historico de Gate](./gate-history-dashboard.md)
- [Metricas de Gate em Markdown](./gate-history-metrics.md)
- [Metricas de Gate em JSON](./gate-history-metrics.json)

## Nota Operacional

Este namespace continua ativo no baseline atual.

- `make track-governance-history` gera `gate-history-metrics.json`
- `make render-governance-gate-history-dashboard` gera `gate-history-dashboard.md`
- `make update-governance-metrics` atualiza o conjunto completo

Por isso, estes arquivos nao devem ser deletados nesta rodada; o ajuste correto foi alinhar scripts e documentacao ao caminho real em `docs/governance-weekly/generated/gates/`.
