# Tracking do Dia 5 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: `reports` em transicao de catalogo formal para cockpit operacional por caso
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- relatorio formal com contexto operacional por caso
- timeline e comments persistidos
- owner, SLA e estado de geracao/download visiveis
- `P1-05` pronto para validacao

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 5

### T1 — Confirmar precondicoes herdadas

- status: `ready`
- owner: `Frontend`
- resultado: precondicoes herdadas dos modulos anteriores
- observacoes: manter consistencia de metadata e fallback

### T2 — Reforcar filtros por `case_id`, `report_type` e `report_id`

- status: `in_progress`
- owner: `Frontend`
- resultado: filtros por caso e relatorio em endurecimento
- observacoes: ligar `case_id`, `report_type` e `report_id`

### T3 — Expor timeline do `work-item`

- status: `pending`
- owner: `Frontend`
- resultado: timeline do `work-item` ainda precisa aparecer na UI
- observacoes: usar `work_item_id` persistido

### T4 — Persistir comments por caso

- status: `pending`
- owner: `Frontend`
- resultado: comments por caso aguardam persistencia final
- observacoes: registrar handoff de geracao e entrega

### T5 — Exibir owner, SLA e estado de geracao/download

- status: `in_progress`
- owner: `Frontend + Report API`
- resultado: estado de geracao/download mapeado
- observacoes: evitar relatorio parecer asset solto

### T6 — Atualizar `P1-05` e decidir passagem

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: passagem depende da leitura completa do caso
- observacoes: nao liberar Dia 6 sem contexto operacional visivel

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-05`|`in_progress`|`no`|fechar timeline/comments e correlacao por caso|
|correlacao por caso|`in_progress`|`no`|ligar fila e relatorio formal|
|geracao/download|`in_progress`|`no`|exibir estado legivel no cockpit|

## Bloqueadores Ativos

- ID: `S2D5-01`
  - item: `P1-05`
  - categoria: `case_correlation_gap`
  - descricao: a correlacao entre fila operacional e relatorio formal ainda precisa ser provada na UI
  - owner da escalacao: `Frontend + Report API`
  - status: `open`
  - proximo checkpoint: fechar leitura por `case_id` e `report_id`

## Evidencias Coletadas

- timeline do `work-item` exposta: `pending`
- comments persistidos: `pending`
- contexto operacional por caso visivel: `in_progress`
- decisao de passagem para o `Dia 6`: `pending`

## Decisao de Passagem

- decisao para o `Dia 6`: `nao`
- motivo principal: `reports` ainda precisa tornar visivel a leitura operacional por caso
- lacuna residual, se houver: finalizar timeline/comments e estado de download

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o cockpit de relatorios esta bem encaminhado, mas ainda precisa fechar o handoff por caso
- owner do primeiro passo do proximo marco: `Frontend + Report API`
- artefato relacionado (legado, alvo removido da trilha viva): `sprint-2-day-5-execution-runbook.md`
