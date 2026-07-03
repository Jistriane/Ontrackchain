# Tracking do Dia 4 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: `evidence` em endurecimento para deixar de ser visor filtravel e virar cockpit compartilhado por evento
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- evento de evidencia abre contexto operacional completo
- timeline e comments persistidos por evento
- deep-links continuam coerentes
- `P1-04` pronto para validacao

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 4

### T1 — Confirmar precondicoes e deep-links existentes

- status: `ready`
- owner: `Frontend`
- resultado: precondicoes e mapa de deep-links herdados
- observacoes: preservar navegacao cruzada como parte do aceite

### T2 — Expor timeline por `evidence_event`

- status: `in_progress`
- owner: `Frontend`
- resultado: timeline por `evidence_event` em integracao
- observacoes: usar `work_item_id` compartilhado

### T3 — Persistir comments por evento

- status: `pending`
- owner: `Frontend`
- resultado: comments por evento aguardam round-trip final
- observacoes: registrar handoff e observacoes operacionais

### T4 — Explicitar `source=server/local`

- status: `in_progress`
- owner: `Frontend`
- resultado: `source=server/local` desenhado na UX
- observacoes: distinguir evento persistido de contexto local

### T5 — Validar preservacao de links para `audit`, `reports`, `blocks`, `counterparties` e `ros`

- status: `ready`
- owner: `Frontend`
- resultado: deep-links mapeados para validacao
- observacoes: nao quebrar navegacao para `audit` e `reports`

### T6 — Atualizar `P1-04` e decidir passagem

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: decisao depende da visibilidade da trilha operacional
- observacoes: so liberar o Dia 5 com evento compartilhado legivel

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-04`|`in_progress`|`no`|fechar contexto operacional por evento|
|evento operacional|`in_progress`|`no`|renderizar timeline/comments|
|deep-links|`ready`|`yes`|validar regressao cruzada|

## Bloqueadores Ativos

- ID: `S2D4-01`
  - item: `P1-04`
  - categoria: `event_context_missing`
  - descricao: a experiencia por evento ainda precisa mostrar contexto operacional completo
  - owner da escalacao: `Frontend`
  - status: `open`
  - proximo checkpoint: fechar timeline/comments por `evidence_event`

## Evidencias Coletadas

- evento de evidencia com contexto operacional: `pending`
- timeline e comments persistidos: `pending`
- deep-links preservados: `ready`
- decisao de passagem para o `Dia 5`: `pending`

## Decisao de Passagem

- decisao para o `Dia 5`: `nao`
- motivo principal: `evidence` ainda precisa comprovar contexto compartilhado completo
- lacuna residual, se houver: finalizar timeline/comments por evento

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o modulo preserva a navegacao cruzada, mas ainda precisa fechar a trilha persistida por evento
- owner do primeiro passo do proximo marco: `Frontend`
- artefato relacionado: [Runbook de Execucao do Dia 4 da Sprint 2](../sprint-2-day-4-execution-runbook.md)
