# Tracking do Dia 6 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: `counterparties` em transicao para cockpit compartilhado de revisao cadastral e risco
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- owner, review e handoff visiveis
- comments persistidos
- timeline coerente por contraparte
- `P1-06` pronto para validacao

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 6

### T1 — Confirmar precondicoes herdadas

- status: `ready`
- owner: `Frontend`
- resultado: precondicoes herdadas dos cockpits anteriores
- observacoes: reusar metadata e regra `server > local draft`

### T2 — Fechar correlacao operacional por contraparte

- status: `in_progress`
- owner: `Frontend`
- resultado: correlacao operacional por `counterparty_id` em fechamento
- observacoes: ligar risco, KYC e review ao `work-item`

### T3 — Expor timeline do `work-item`

- status: `pending`
- owner: `Frontend`
- resultado: timeline ainda precisa ficar visivel no cockpit
- observacoes: renderizar historico por contraparte

### T4 — Persistir comments por contraparte

- status: `pending`
- owner: `Frontend`
- resultado: comments persistidos aguardam round-trip final
- observacoes: usar comments para handoff e solicitacao documental

### T5 — Exibir owner, risco, KYC e proximo review

- status: `in_progress`
- owner: `Frontend`
- resultado: ownership, risco e proximo review mapeados
- observacoes: exibir `kyc_status` e `next_review_at` no mesmo contexto

### T6 — Atualizar `P1-06` e decidir passagem

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: passagem depende da leitura multiusuario legivel
- observacoes: nao liberar o Dia 7 sem trilha persistida

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-06`|`in_progress`|`no`|fechar timeline/comments e revisao|
|ownership e revisao|`in_progress`|`no`|mostrar owner, risco e KYC|
|timeline/comments|`pending`|`no`|persistir historico compartilhado|

## Bloqueadores Ativos

- ID: `S2D6-01`
  - item: `P1-06`
  - categoria: `review_hidden`
  - descricao: a leitura conjunta de owner, risco, KYC e review ainda precisa ficar visivel na UI
  - owner da escalacao: `Frontend`
  - status: `open`
  - proximo checkpoint: fechar cockpit da contraparte

## Evidencias Coletadas

- timeline do `work-item` exposta: `pending`
- comments persistidos: `pending`
- owner, handoff e revisao visiveis: `in_progress`
- decisao de passagem para o `Dia 7`: `pending`

## Decisao de Passagem

- decisao para o `Dia 7`: `nao`
- motivo principal: `counterparties` ainda precisa fechar handoff persistido e timeline visivel
- lacuna residual, se houver: finalizar cockpit operacional da contraparte

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o modulo saiu da memoria local, mas ainda precisa evidenciar ownership e historico completos
- owner do primeiro passo do proximo marco: `Frontend`
- artefato relacionado: [Runbook de Execucao do Dia 6 da Sprint 2](../../sprint-2-day-6-execution-runbook.md)
