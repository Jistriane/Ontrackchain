# Guia de Uso dos Artefatos da Governanca Semanal

## Objetivo

Explicar qual documento usar em cada momento do ciclo semanal, evitando duplicacao, drift e duvida operacional.

## Regra Simples

Se a pergunta for:

- "qual e o estado geral e a estrategia?" -> usar o plano consolidado
- "como conduzir a reuniao?" -> usar o roteiro de facilitacao
- "o que preencher rapidamente no encontro?" -> usar a versao operacional da semana
- "onde registrar a leitura completa da semana?" -> usar o rascunho completo ou o registro fechado
- "quando posso promover para documento fechado?" -> usar o workflow + checklist de fechamento

## Qual Documento Usar

### 1. Estado geral e baseline oficial

Usar:

- [Plano Consolidado de Continuidade e Execucao](../../history/CONTINUATION_EXECUTION_PLAN_2026_07.md)

Quando usar:

- para entender baseline oficial
- para revisar caminho critico
- para consultar owners, datas-alvo, gatilhos e matriz de status

### 2. Conducao da reuniao semanal

Usar:

- [Roteiro de Facilitacao da Governanca Semanal](./WEEKLY_GOVERNANCE_FACILITATION_SCRIPT.md)

Quando usar:

- no inicio da reuniao
- durante a conducao pelo facilitador
- para manter foco nos itens criticos e na decisao executiva

### 3. Preenchimento rapido no encontro

Usar:

- [Template de Governança Semanal Operacional](../templates/_template-weekly-governance-operational.md)
- ou a versao ja aberta da semana, como [Governança Semanal Operacional 2026-07-13](../cycles/2026-07-13/2026-07-13-weekly-governance-operational.md)

Quando usar:

- para registrar status curto
- para capturar bloqueios, semaforo, escalacoes e proxima acao verificavel

### 4. Registro detalhado da semana

Usar:

- [Template de Governança Semanal Completa](../templates/_template-weekly-governance.md)
- ou o rascunho completo da semana, como [Governança Semanal 2026-07-13 (Rascunho)](../cycles/2026-07-13/2026-07-13-weekly-governance-draft.md)

Quando usar:

- para consolidar a leitura completa do ciclo
- para preparar o documento que pode virar registro semanal fechado

### 5. Decidir se a semana pode ser fechada

Usar:

- [Workflow de Atualizacao Semanal da Governanca](./WEEKLY_GOVERNANCE_UPDATE_WORKFLOW.md)
- [Checklist de Fechamento Semanal da Governanca](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)

Quando usar:

- apos a reuniao
- no fechamento da semana
- sempre que houver duvida se a semana vira apenas `operational + draft` ou registro fechado

### 6. Janela seria ativa

Usar:

- war room
- sign-off
- status snapshot
- status delta
- dashboard
- JSON consolidado

Quando usar:

- quando a semana tiver dependencia de `RUN-STG-01`
- quando for necessario decidir `go`, `go_with_exception`, `pending` ou `no-go`

## Fluxo Recomendado de Uso

1. abrir o [Plano Consolidado de Continuidade e Execucao](../../history/CONTINUATION_EXECUTION_PLAN_2026_07.md)
2. conduzir a reuniao com o [Roteiro de Facilitacao](./WEEKLY_GOVERNANCE_FACILITATION_SCRIPT.md)
3. preencher a versao operacional da semana
4. sincronizar o rascunho completo
5. aplicar o [Workflow de Atualizacao](./WEEKLY_GOVERNANCE_UPDATE_WORKFLOW.md)
6. validar a [Checklist de Fechamento](./WEEKLY_GOVERNANCE_CLOSEOUT_CHECKLIST.md)
7. promover ou nao para `YYYY-MM-DD-weekly-governance.md`

## Anti-Padroes

Evitar:

- atualizar varios documentos ao mesmo tempo sem definir qual e a fonte de verdade do encontro
- usar o rascunho como se ja fosse registro fechado
- usar a versao operacional como substituto do registro semanal final
- mudar baseline no plano consolidado antes da revisao formal da semana
- usar a janela seria como prova de avanço sem artifact, sign-off ou delta real

## Resultado Esperado

O time deve conseguir responder com rapidez:

- qual documento abrir primeiro
- qual documento preencher durante a reuniao
- qual documento fecha a semana
- qual documento governa a decisao de promocao
