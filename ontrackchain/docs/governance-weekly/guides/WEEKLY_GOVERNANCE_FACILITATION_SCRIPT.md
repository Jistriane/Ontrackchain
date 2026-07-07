# Roteiro de Facilitacao da Governanca Semanal

## Objetivo

Guiar a reuniao semanal de governanca de forma curta, objetiva e orientada a evidencia.

Este roteiro deve ser usado junto com:

- [Workflow de Atualizacao Semanal da Governanca](./WEEKLY_GOVERNANCE_UPDATE_WORKFLOW.md)
- [Checklist de Fechamento Semanal da Governanca](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)
- versao operacional da semana
- rascunho completo da semana

## Duracao Recomendada

- `20-30 min` para semana sem mudanca material
- `30-45 min` para semana com janela seria, artifact novo ou decisao de `go/no-go`

## Preparacao Minima Antes da Reuniao

- atualizar a versao operacional da semana
- atualizar o rascunho completo da semana
- revisar war room, sign-off, snapshot, delta e JSON consolidado da janela seria ativa
- deixar visivel a baseline oficial vigente

## Agenda Recomendada

### 1. Abertura e baseline (`3 min`)

Confirmar:

- baseline tecnica vigente
- baseline regulatoria vigente
- KPI consolidado vigente
- decisao vigente: `go`, `go_with_exception`, `pending` ou `no-go`

Pergunta do facilitador:

- "Houve evidencia nova material desde o ultimo fechamento?"

### 2. Revisao dos itens criticos (`10-15 min`)

Revisar, nesta ordem:

1. `P0-02`
2. `P0-03`
3. `P0-01`
4. `RUN-STG-01`
5. ownership/SLA
6. retention/recovery

Para cada item, perguntar:

- qual foi a ultima evidencia revisada?
- houve delta real desde a ultima semana?
- o item continua `blocked`, `ready`, `in_progress`, `ready_for_validation` ou `done`?
- qual e a proxima acao verificavel?

## 3. Janela seria e gates (`5-10 min`)

Se houver janela seria ativa, confirmar:

- status do `dashboard`
- status do `snapshot`
- status do `delta`
- status do `sign-off`
- existencia ou ausencia de artifact, packet e dossie

Perguntas obrigatorias:

- o war room saiu de `no-go`?
- houve reducao real de placeholders ou handoff pendente?
- o workflow pode ser tratado como evidência oficial ou ainda nao?

## 4. Decisao executiva da semana (`3-5 min`)

O facilitador deve registrar uma decisao objetiva:

- `manter baseline`
- `recalibrar`
- `pending`
- `no-go`
- `go_with_exception`

Perguntas de controle:

- algum KPI mudou de forma defensavel?
- algum item mudou de status por evidência real?
- algum bloqueio externo precisa de escalacao formal nesta semana?

## 5. Fechamento (`3-5 min`)

Registrar:

- principal ganho da semana
- principal bloqueio da semana
- item mais proximo de fechamento
- owner da principal escalacao
- proxima evidencia esperada

## Saidas Obrigatorias da Reuniao

Ao final da reuniao, deve existir:

- decisao semanal registrada
- itens `blocked` explicitamente marcados
- paths dos artefatos relevantes, quando existirem
- proxima acao verificavel por item critico
- decisao se a semana vira apenas `operational + draft` ou registro semanal fechado

## Frases-Guia do Facilitador

Usar perguntas curtas e objetivas:

- "Qual e a evidencia nova?"
- "Isso muda status ou apenas confirma bloqueio?"
- "Qual artefato legitima essa mudanca?"
- "Sem esse artefato, o status permanece qual?"
- "Qual owner fica responsavel pelo proximo gate?"

## Anti-Padroes de Conducao

Evitar:

- discutir roadmap longo antes dos itens criticos da semana
- mudar KPI por percepcao
- aceitar readiness documental como substituto de evidência real
- encerrar a reuniao sem owner de escalacao
- tratar rerun sem delta como progresso material

## Encerramento Recomendado

Fechar sempre com uma sintese curta:

- baseline final da semana
- decisao executiva final
- maior bloqueio mantido
- proxima evidencia esperada
- data da proxima revisao
