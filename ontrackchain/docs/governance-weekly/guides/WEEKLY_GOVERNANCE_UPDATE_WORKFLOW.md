# Workflow de Atualizacao Semanal da Governanca

## Objetivo

Padronizar o fluxo semanal de atualizacao da governanca para evitar drift entre:

- plano consolidado vigente
- versao operacional curta da reuniao
- rascunho completo da semana
- registro semanal fechado
- artefatos da janela seria

Este workflow existe para responder duas perguntas de forma consistente:

1. quando atualizar apenas o operacional e o rascunho
2. quando promover um ciclo para `YYYY-MM-DD-weekly-governance.md` fechado

Checklist de apoio para o fechamento:

- [Checklist de Fechamento Semanal da Governanca](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)
- [Roteiro de Facilitacao da Governanca Semanal](./WEEKLY_GOVERNANCE_FACILITATION_SCRIPT.md)
- [Guia de Uso dos Artefatos da Governanca Semanal](./WEEKLY_GOVERNANCE_ARTIFACT_SELECTION_GUIDE.md)

## Artefatos de Entrada

Usar como fontes oficiais, nesta ordem:

1. [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md)
2. [Governança Semanal mais recente](../cycles/2026-07-06/2026-07-06-weekly-governance.md) ou outro registro semanal fechado vigente
3. [Versao Operacional da Semana](../cycles/2026-07-13/2026-07-13-weekly-governance-operational.md) ou equivalente
4. [Rascunho Completo da Semana](../cycles/2026-07-13/2026-07-13-weekly-governance-draft.md) ou equivalente
5. war room, sign-off, tracking, snapshot, delta e JSON consolidado da janela seria ativa

## Regra de Ouro

Nao promover status, KPI ou baseline por:

- expectativa
- promessa verbal
- preparacao de reuniao
- artifact local sem revisao
- evidência `dev` usada como substituto de fluxo serio

Promover apenas quando houver evidência nova revisavel no proprio ciclo.

## Fluxo Recomendado

### Passo 1 - Atualizar a base factual da janela seria

Quando houver janela seria ativa, atualizar primeiro o pacote operacional gerado:

```bash
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Revisar pelo menos:

- `stg-<...>-governance-dashboard.md`
- `stg-<...>-status-snapshot.md`
- `stg-<...>-status-snapshot-delta.md`
- `stg-<...>-consolidated.json`

Se existir payload consolidado da janela (`prepare-staging-window-output.json`), executar em seguida o pós-processamento executivo:

```bash
make postprocess-serious-window RUN_URL=https://github.com/<org>/<repo>/actions/runs/<run_id>
```

Revisar pelo menos:

- `2026-..-staging-serious-window-signoff.md`
- `2026-..-staging-serious-window-go-no-go-decision-packet.md`
- sincronizacao do registro semanal correspondente

### Passo 2 - Atualizar a versao operacional curta

Preencher ou revisar:

- baseline da semana
- decisao executiva rapida
- snapshot dos itens criticos
- escalacoes necessarias
- proxima revisao

Objetivo:

- permitir leitura rapida em reuniao
- deixar claro o bloqueio atual e a proxima acao verificavel

### Passo 3 - Atualizar o rascunho completo

Sincronizar no rascunho:

- evidências revisadas
- status de `P0-01`, `P0-02`, `P0-03` e `RUN-STG-01`
- itens `blocked`
- decisoes esperadas ou confirmadas
- açoes da semana seguinte

Objetivo:

- preparar o material que podera virar o registro semanal fechado

### Passo 4 - Decidir se o ciclo pode ser fechado

Criar ou atualizar `YYYY-MM-DD-weekly-governance.md` apenas quando pelo menos uma destas condicoes for verdadeira:

- houve evidência nova material revisada no encontro
- houve decisao formal de manter baseline e bloqueios com base em evidencia revisada no encontro
- a janela seria teve artifact, sign-off, packet ou dossie que precisou ser formalmente registrado

Se nenhuma dessas condicoes ocorrer, manter apenas:

- versao operacional da semana
- rascunho da semana

## Regra de Promocao de Documento

### Manter como operacional + rascunho

Usar quando:

- a reuniao ainda nao aconteceu
- os dados ainda estao incompletos
- existe expectativa de nova evidência antes do fechamento da semana

### Promover para registro semanal fechado

Usar quando:

- a reuniao da semana terminou
- as evidências do encontro foram revisadas
- a decisao semanal ficou registrada
- os itens `blocked` e as acoes seguintes ficaram claros

O arquivo fechado deve usar o formato:

- `YYYY-MM-DD-weekly-governance.md`

E conter, no minimo:

- leitura do ciclo
- contexto da janela seria
- evidências revisadas
- KPI da semana
- itens atualizados
- itens `blocked`
- decisoes
- acoes da proxima semana

## Regra de Sincronizacao

Ao fechar a semana, sincronizar pelo menos estes pontos:

1. versao operacional curta
2. rascunho completo
3. registro semanal fechado
4. [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md), quando houver mudanca material de baseline, status ou gatilho
5. [Matriz Operacional de Execucao para 95%](../../project-operational-execution-board.md), quando houver mudanca de prioridade ou owner

## Perguntas de Controle Antes do Fechamento

- houve checker, bundle, artifact, dossie ou sign-off novo revisavel?
- o `go/no-go decision packet` ficou coerente com war room, sign-off e snapshot consolidado?
- a baseline mudou de forma defensavel?
- algum `P0` mudou de status por evidencia real?
- a janela seria saiu de `no-go`, permaneceu em `no-go` ou voltou para `pending` com justificativa clara?
- os paths dos artefatos relevantes ficaram registrados?

## Resultado Esperado

Ao final do ciclo semanal, o time deve conseguir responder sem ambiguidade:

- qual e a baseline oficial vigente
- quais itens continuam `blocked`
- qual item esta mais proximo de fechar
- qual evidência falta para o proximo avanço legitimo
- se a semana terminou em `go`, `go_with_exception`, `pending` ou `no-go`
