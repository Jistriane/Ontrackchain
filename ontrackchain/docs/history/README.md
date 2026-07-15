# Historico de Apoio

## Objetivo

Concentrar artefatos datados que continuam uteis para consulta, mas que nao devem mais competir com a documentacao viva e canonica da raiz de `docs/`.

## Papel Nesta Taxonomia

Esta pasta existe para preservar contexto datado fora da trilha viva. Ela nao substitui:

- `../README.md` como indice canonico
- `../project-kpi-scorecard.md` e `../project-maturity-assessment.md` como baseline viva
- `../governance-weekly/` como trilha oficial de ciclos, janelas e artefatos gerados

Quando houver conflito, use esta precedencia:

1. `../README.md` e documentos canonicamente indexados
2. `../governance-weekly/` para evidencia datada ainda operacional
3. `history/` apenas como contexto historico de apoio

Use esta pasta para:

- planos datados de um ciclo especifico
- runbooks ligados a uma janela especifica
- trackers semanais que perderam centralidade
- roteiros taticos supersedidos por boards e kits canonicos

Nao use esta pasta como fonte primaria para:

- baseline oficial
- scorecard atual
- board operacional vigente
- rito semanal atual de governanca

## Fonte Primaria Atual

Comece por estes documentos:

- [Resumo Executivo de Readiness](../project-executive-readiness-brief.md)
- [Kit de Execucao por Evidencia](../project-maturity-evidence-execution-kit.md)
- [Scorecard Oficial do Projeto](../project-kpi-scorecard.md)
- [Board Operacional Unico](../project-operational-execution-board.md)
- [Runbook de Governança Semanal](../project-weekly-governance-runbook.md)

## Regra de Leitura

- trate os arquivos desta pasta como registros congelados de apoio
- se um fluxo ainda estiver ativo por semana, janela ou `window_id`, prefira `../governance-weekly/`
- se um documento desta pasta voltar a governar decisao atual, ele deve ser promovido para a trilha canônica ou consolidado nela
- artefatos supersedidos devem permanecer aqui apenas quando ainda preservarem valor de auditoria, trilha ou contexto

## Artefatos Movidos

- [Plano Consolidado de Continuidade e Execucao](./CONTINUATION_EXECUTION_PLAN_2026_07.md)
- [Plano Tatico Sprint 7-9: Escalacao Controlada para 95%](./TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md)
- [Tracker Semanal de Owners para 95%](./WEEKLY_OWNERS_TRACKER_TO_95_PERCENT.md)
- [Checklist de Evidencia Minima da Primeira Janela Seria](./first-serious-window-evidence-checklist.md)
- [Runbook do Primeiro Disparo Real](./first-serious-window-first-dispatch-runbook.md)
- [Template de Sign-Off da Janela Seria](./staging-serious-window-signoff-template.md)
- [Auditoria de `.publish_repo` - 2026-07-11](./PUBLISH_REPO_AUDIT_2026_07_11.md)

## Notas de Consolidacao

- o roteiro operacional datado da janela `stg-2026-07-06-a` foi absorvido pelos artefatos do ciclo em `../governance-weekly/cycles/2026-07-06/`
- use `../project-construction-plan-to-95-percent.md` e `../project-operational-execution-board.md` como referencias vivas; os arquivos desta pasta permanecem apenas como registro frio
