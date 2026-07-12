# Checklist de Fechamento Semanal da Governanca

## Objetivo

Servir como lista curta e objetiva para fechar um ciclo semanal sem inflar progresso e sem deixar drift entre:

- versao operacional da semana
- rascunho completo
- registro semanal fechado
- artefatos da janela seria
- baseline executiva

## Checklist de Fechamento

- [ ] atualizar o pacote operacional da janela seria ativa, quando aplicavel
- [ ] revisar `dashboard`, `status snapshot`, `delta`, `sign-off` e `JSON consolidado`
- [ ] confirmar se houve evidência nova material revisavel no proprio ciclo
- [ ] registrar a decisao da semana: `manter baseline`, `recalibrar`, `pending`, `no-go` ou `go_with_exception`
- [ ] validar se algum `P0`, `P1` ou `P2` mudou de status por evidência real
- [ ] confirmar quais itens permanecem `blocked`
- [ ] registrar a proxima evidencia esperada por item critico
- [ ] preencher ou revisar a versao operacional da semana
- [ ] sincronizar o rascunho completo da semana
- [ ] decidir se a semana deve ser promovida para `YYYY-MM-DD-weekly-governance.md`
- [ ] se houve mudanca material, sincronizar o [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md)
- [ ] se houve mudanca de KPI, sincronizar scorecard e avaliacao consolidada
- [ ] registrar paths dos artefatos revisados no fechamento

## Criterios Minimos para Promocao da Semana

Promover para registro semanal fechado apenas quando:

- a reuniao semanal realmente aconteceu
- as evidências do encontro foram revisadas
- a decisao executiva da semana ficou registrada
- os itens `blocked` e as acoes seguintes ficaram claros

## Anti-Padroes

Nao fechar a semana como se houvesse avanço quando existir apenas:

- promessa verbal de provider
- preparacao de reuniao sem artifact
- bundle local sem revisao formal
- expectativa de credencial "chegando"
- rerun sem delta real em placeholders, handoff ou sign-off

## Saida Esperada

Ao final do fechamento, deve estar claro:

- qual e a baseline oficial da semana
- quais itens continuam `blocked`
- qual item esta mais proximo de fechar
- qual artefato legitima o proximo avanço
- se a semana terminou em `go`, `go_with_exception`, `pending` ou `no-go`
