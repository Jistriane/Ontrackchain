# Tracking Historico de Sprints

## Objetivo

Preservar uma referencia historica agregada das sprints antigas, sem manter acompanhamentos diarios como trilha navegavel ativa.

## Faixas Disponiveis

- Sprint 1: dias 1 a 5 em `2026-07-02`
- Sprint 2: dias 1 a 7 em `2026-07-02`
- Sprint 3: dias 1 a 5 em `2026-07-06`
- Sprint 4: dias 1 a 5 em `2026-07-07`

## Status

- os arquivos diarios foram removidos para reduzir ruido e falso drift na navegacao
- este README permanece como ponte historica para referenciar o contexto das sprints
- a politica de retencao de `archive/` e aplicada por automacao e nao deve reintroduzir arquivos diarios nesta pasta

## Observacao

Historicamente, os acompanhamentos diarios desta pasta referenciavam runbooks antigos que ja nao estao presentes na trilha viva atual. Esses links devem ser lidos apenas como contexto historico e nao como caminho operacional ativo.

Em especial, referencias no formato `../../sprint-<n>-day-<m>-execution-runbook.md` representam a trilha de execucao usada durante o acompanhamento diario original da sprint. Esses runbooks nao existem mais na estrutura canonica atual e sua ausencia nao indica erro operacional da documentacao viva.

## Leitura Correta dos Links Legados

- tratar links para `*-execution-runbook.md` como evidencia de contexto do acompanhamento historico, nao como documento que precisa ser restaurado
- usar [Historico de Apoio](../../../history/README.md) quando a necessidade for consultar planos e runbooks datados ainda relevantes
- usar [Registros Semanais de Governança](../../README.md) quando a necessidade for navegar pela trilha viva de governanca
- usar [Documentacao Canonica](../../../README.md) quando a necessidade for localizar a fonte primaria atual
