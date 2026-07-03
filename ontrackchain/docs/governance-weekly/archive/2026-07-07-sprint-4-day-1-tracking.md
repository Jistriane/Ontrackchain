# Tracking do Dia 1 da Sprint 4 — `stg-2026-07-07-a`

## Contexto Operacional

- data: `2026-07-07`
- `window_id`: `stg-2026-07-07-a`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `in_progress`
- checkpoint atual: revisao do risco pos-janela preparada para impedir que a baseline oficial carregue fotografia antiga
- ultima atualizacao: `2026-07-07T00:00:00Z`

## Resultado Esperado do Dia

- `project-risk-register.md` revisado
- riscos reclassificados com justificativa
- `P1-08` pronto para validacao
- passagem limpa para a baseline oficial

## Status Permitidos

- item principal: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 1

### T1 — Revisar riscos ligados aos `P0` e `P1` do ciclo anterior

- status: `ready`
- owner: `Arquitetura/Governanca`
- resultado: riscos alvo identificados
- observacoes: usar artifact e sign-offs da sprint anterior como base

### T2 — Comparar baseline antiga com evidencias novas

- status: `in_progress`
- owner: `Arquitetura`
- resultado: comparacao entre baseline antiga e evidencias novas em andamento
- observacoes: evitar reclassificacao por intuicao

### T3 — Reclassificar probabilidade e impacto

- status: `pending`
- owner: `Arquitetura + Security`
- resultado: reclassificacao formal ainda depende da leitura final das evidencias
- observacoes: explicitar o que mudou de fato

### T4 — Sincronizar `P1-08` no board

- status: `pending`
- owner: `Arquitetura/Governanca`
- resultado: sincronizacao do board depende da revisao do risk register
- observacoes: nao mover `P1-08` sem justificativa

### T5 — Decidir passagem para o Dia 2

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: passagem para baseline depende do risco revisado
- observacoes: so abrir Dia 2 sem risco obsoleto

## Leitura Final do Escopo

|Item|Status|Evidencia minima existe?|Proximo passo|
|---|---|---|---|
|`P1-08`|`in_progress`|`no`|fechar reclassificacao do risk register|
|riscos P0|`in_progress`|`no`|reclassificar com base na janela|
|riscos P1|`pending`|`no`|fechar leitura de retention e operacao recorrente|

## Bloqueadores Ativos

- ID: `S4D1-01`
  - item: `P1-08`
  - categoria: `evidence_gap`
  - descricao: a reclassificacao final ainda depende da leitura consolidada das evidencias da Sprint 3
  - owner da escalacao: `Arquitetura/Governanca`
  - status: `open`
  - proximo checkpoint: fechar leitura das evidencias materiais

## Evidencias Coletadas

- `project-risk-register.md` revisado: `in_progress`
- justificativa por reclassificacao: `pending`
- decisao de passagem para o `Dia 2`: `pending`

## Decisao de Passagem

- decisao para o `Dia 2`: `nao`
- motivo principal: o Dia 2 so deve abrir depois da reclassificacao formal do risco
- risco que ainda precisa de prova, se houver: fechar `project-risk-register.md` com justificativas

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o risco alvo esta bem mapeado, mas ainda precisa da reclassificacao final para destravar a baseline oficial
- owner do primeiro passo do proximo marco: `Arquitetura/Governanca`
- artefato relacionado: [Runbook de Execucao do Dia 1 da Sprint 4](../sprint-4-day-1-execution-runbook.md)
