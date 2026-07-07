# Tracking do Dia 3 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: `ros-coaf` em transicao para fluxo auditavel de aprovacao, rejeicao e submissao manual
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- historico operacional completo do ROS visivel
- comments persistidos para handoff e decisao
- estado regulatorio e operacional lado a lado
- `P1-03` pronto para validacao

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 3

### T1 — Confirmar precondicoes de `P1-01`

- status: `ready`
- owner: `Frontend`
- resultado: precondicoes herdadas do contrato comum
- observacoes: reusar padrao de metadata da sprint

### T2 — Expor timeline do `ros_record`

- status: `in_progress`
- owner: `Frontend`
- resultado: timeline do ROS em integracao
- observacoes: usar `work_item_id` persistido

### T3 — Persistir comments de handoff e decisao

- status: `pending`
- owner: `Frontend`
- resultado: comments de handoff aguardam persistencia final
- observacoes: registrar decisao de aprovacao/rejeicao

### T4 — Mostrar estados regulatorios e operacionais em conjunto

- status: `in_progress`
- owner: `Frontend + Report API`
- resultado: estados regulatorios e operacionais mapeados
- observacoes: exibir `queue_status` sem esconder `PENDING_APPROVAL`

### T5 — Exibir owner e SLA do item

- status: `pending`
- owner: `Frontend`
- resultado: owner e SLA ainda aguardam renderizacao final
- observacoes: legibilidade e auditoria na mesma tela

### T6 — Atualizar `P1-03` e decidir passagem

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: passagem depende da leitura completa do ROS
- observacoes: nao liberar o Dia 4 sem comments persistidos

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-03`|`in_progress`|`no`|fechar timeline e comments|
|timeline|`in_progress`|`no`|renderizar historico completo|
|estado regulatorio|`in_progress`|`no`|alinhar com SLA e ownership|

## Bloqueadores Ativos

- ID: `S2D3-01`
  - item: `P1-03`
  - categoria: `state_mismatch`
  - descricao: a leitura conjunta do estado regulatorio e operacional ainda precisa ser validada
  - owner da escalacao: `Frontend + Report API`
  - status: `open`
  - proximo checkpoint: fechar painel de estados lado a lado

## Evidencias Coletadas

- historico completo do ROS na UI: `pending`
- comments persistidos: `pending`
- estados regulatorios coerentes: `in_progress`
- decisao de passagem para o `Dia 4`: `pending`

## Decisao de Passagem

- decisao para o `Dia 4`: `nao`
- motivo principal: o fluxo ROS ainda precisa fechar comments persistidos e leitura final dos estados
- lacuna residual, se houver: finalizar painel regulatorio/operacional

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o cockpit ROS avancou, mas ainda sem comprovacao completa de auditabilidade na UI
- owner do primeiro passo do proximo marco: `Frontend + Report API`
- artefato relacionado: [Runbook de Execucao do Dia 3 da Sprint 2](../../sprint-2-day-3-execution-runbook.md)
