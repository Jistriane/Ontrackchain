# Tracking do Dia 1 da Sprint 2 — `stg-2026-07-02-b`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-b`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: contrato de `metadata` em consolidacao; foco em impedir drift antes da abertura dos cockpits multiusuario
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- contrato comum de `metadata` definido
- campos minimos por modulo alinhados
- regra de merge parcial documentada
- passagem objetiva para `blocks` e `ros-coaf`

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 1

### T1 — Validar contrato minimo de `metadata`

- status: `ready`
- owner: `Backend/Compliance + Frontend`
- resultado: escopo do contrato minimo identificado
- observacoes: precisa fechar chaves obrigatorias e merge parcial

### T2 — Alinhar leitura e escrita entre frontend e backend

- status: `in_progress`
- owner: `Backend/Compliance`
- resultado: leitura das operacoes de `work-items` em andamento
- observacoes: garantir alinhamento com a API existente

### T3 — Confirmar campos minimos por dominio

- status: `in_progress`
- owner: `Arquitetura/Frontend`
- resultado: campos alvo por modulo mapeados
- observacoes: nao abrir excecoes ad hoc sem justificativa

### T4 — Documentar merge parcial e ownership de metadata

- status: `ready`
- owner: `Arquitetura`
- resultado: regra de merge parcial preparada
- observacoes: registrar precedencia e preservacao de metadata existente

### T5 — Atualizar leitura de `P1-01` e liberar o Dia 2

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: dependente das tarefas anteriores
- observacoes: liberar Dia 2 apenas sem drift conceitual

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-01`|`in_progress`|`no`|fechar contrato e mover para validacao|
|`blocks`|`ready`|`no`|abrir Dia 2 com contrato comum|
|`ros-coaf`|`ready`|`no`|aguardar contrato comum final|

## Bloqueadores Ativos

- ID: `S2D1-01`
  - item: `P1-01`
  - categoria: `contract_drift`
  - descricao: ainda falta fixar a lista final de chaves compartilhadas
  - owner da escalacao: `Arquitetura/Backend`
  - status: `open`
  - proximo checkpoint: fechar contrato minimo de metadata

## Evidencias Coletadas

- contrato comum de `metadata`: `in_progress`
- lista de campos obrigatorios por modulo: `pending`
- regra de merge parcial registrada: `pending`
- decisao de passagem para o `Dia 2`: `pending`

## Decisao de Passagem

- decisao para o `Dia 2`: `nao`
- motivo principal: o contrato de `metadata` ainda precisa ser fechado sem ambiguidade
- condicao que falta para liberar, se houver: concluir contrato comum e regra de merge parcial

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o dia avanca com direcao correta, mas ainda sem contrato comum fechado
- owner do primeiro passo do proximo marco: `Backend/Compliance + Frontend`
- artefato relacionado (legado, alvo removido da trilha viva): `sprint-2-day-1-execution-runbook.md`
