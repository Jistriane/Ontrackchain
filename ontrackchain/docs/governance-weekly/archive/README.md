# Arquivo Historico da Governanca

## Objetivo

Concentrar materiais historicos que nao fazem mais parte da trilha ativa de ciclos, mas ainda preservam contexto de decisao, calibracao e execucao.

## Papel Nesta Taxonomia

Esta pasta preserva historico frio consolidado da governanca. Ela existe para consulta e rastreabilidade, nao para orientar operacao corrente.

Quando houver conflito, use esta precedencia:

1. `../../README.md` e os documentos canonicamente indexados nele
2. `../cycles/` para evidencia datada ainda navegavel por semana ou janela
3. `../generated/` para artefatos derivados por `window_id`
4. `archive/` apenas como historico preservado

## Taxonomia

- [Historico Semanal](./weekly/README.md): registros semanais fechados, atualizacoes de KPI e checks de readiness antigos
- [Tracking de Sprints](./sprint-tracking/README.md): referencia historica agregada de sprints antigas

## Quando Consultar

Consulte esta pasta quando precisar:

- revisar a linha do tempo de decisoes passadas
- recuperar contexto de calibracoes e readiness antigos
- investigar como uma sprint ou semana foi conduzida antes da taxonomia atual

Nao consulte esta pasta como fonte primaria para:

- baseline executiva atual
- boards operacionais vigentes
- runbooks ativos
- decisao corrente de `go/no-go`

## Regra de Precedencia

- trate `archive/` como historico frio consolidado
- quando houver divergencia entre um artefato arquivado e o estado atual, prevalecem `docs/`, `governance-weekly/cycles/` e os scorecards/boards vivos
- nao use esta pasta como fonte primaria para operacao atual, baseline executiva ou contrato canônico
- se um artefato arquivado voltar a ser necessario para decisao atual, consolide a parte viva na trilha canônica em vez de reativar o snapshot historico como fonte corrente
