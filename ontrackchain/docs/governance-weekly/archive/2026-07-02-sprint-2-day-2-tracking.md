# Tracking do Dia 2 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: `blocks` em endurecimento para sair de experiencia mono-usuario e assumir handoff persistido
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- timeline do `work-item` exposta
- comments persistidos
- origem `server/local` explicita
- `P1-02` pronto para validacao

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 2

### T1 — Confirmar precondicoes de `P1-01`

- status: `ready`
- owner: `Frontend`
- resultado: precondicoes de `P1-01` herdadas do Dia 1
- observacoes: nao abrir timeline se o contrato ainda estiver inconsistente

### T2 — Expor timeline do `work-item`

- status: `in_progress`
- owner: `Frontend`
- resultado: integração da timeline em andamento
- observacoes: usar `work_item_id` persistido como chave principal

### T3 — Persistir comments operacionais

- status: `pending`
- owner: `Frontend`
- resultado: comments ainda dependem de round-trip completo com backend
- observacoes: evitar fallback silencioso local

### T4 — Exibir owner, prioridade, deadline e status

- status: `pending`
- owner: `Frontend`
- resultado: ownership e SLA aguardando leitura final da UI
- observacoes: explicitar `queue_status`

### T5 — Distinguir rascunho local de bloco persistido

- status: `in_progress`
- owner: `Arquitetura/Frontend`
- resultado: criterio `server/local` mapeado
- observacoes: nao confundir rascunho com item persistido

### T6 — Atualizar `P1-02` e decidir passagem

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: decisao depende do historico aparecer na UI
- observacoes: so liberar o Dia 3 com `P1-02` legivel

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-02`|`in_progress`|`no`|fechar timeline/comments e ownership|
|timeline|`in_progress`|`no`|renderizar via API|
|comments|`pending`|`no`|persistir no backend|

## Bloqueadores Ativos

- ID: `S2D2-01`
  - item: `P1-02`
  - categoria: `timeline_missing`
  - descricao: ainda falta confirmar visibilidade da timeline no cockpit
  - owner da escalacao: `Frontend`
  - status: `open`
  - proximo checkpoint: fechar integracao de timeline

## Evidencias Coletadas

- timeline renderizada via API: `pending`
- comments persistidos: `pending`
- `source=server/local` visivel: `in_progress`
- decisao de passagem para o `Dia 3`: `pending`

## Decisao de Passagem

- decisao para o `Dia 3`: `nao`
- motivo principal: `blocks` ainda precisa fechar timeline/comments de forma visivel
- lacuna residual, se houver: finalizar historico compartilhado

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o modulo avanca para multiusuario, mas ainda sem todos os sinais de persistencia fechados
- owner do primeiro passo do proximo marco: `Frontend`
- artefato relacionado: [Runbook de Execucao do Dia 2 da Sprint 2](../sprint-2-day-2-execution-runbook.md)
