# Artefatos Gerados

## Objetivo

Concentrar saidas geradas automaticamente ou semi-automaticamente pela janela seria e pelos paineis de governanca.

Use esta pasta para:

- dashboards gerados
- snapshots e deltas em Markdown
- JSONs consolidados
- metricas e historico de gate
- checklists e planos de acao produzidos pelo fluxo da janela

Regra operacional:

- esta pasta guarda saidas geradas do refresh e dos paineis automatizados
- artefatos humanos do ciclo ativo permanecem em `docs/governance-weekly/cycles/<data>/`
- artefatos executivos derivados do payload consolidado, como `sign-off` e `decision packet`, sao publicados no ciclo datado, nao aqui

Nao use esta pasta para:

- templates
- runbooks canonicos
- atas ou registros semanais escritos manualmente

## Artefatos Disponiveis

- [Historico e Metricas de Gate](./gates/README.md)
- [Indice de Janelas Geradas](./windows/README.md)
- [Artefatos da Janela `stg-2026-07-06-a`](./windows/stg-2026-07-06-a/README.md)

## Ciclo Ativo

- ciclo humano corrente: `2026-07-13`
- janela datada corrente: `stg-2026-07-13-a`
- este indice deve ganhar um novo namespace em `windows/` somente quando o refresh gerado dessa janela produzir artefatos persistidos
