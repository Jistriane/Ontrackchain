# Governança Semanal — 2026-07-13 (Rascunho)

## Objetivo

Servir como rascunho da proxima revisao semanal de governanca, derivado do estado consolidado em `2026-07-06`, do plano de continuidade e dos gatilhos legitimos de avanço definidos para `P0-01`, `P0-02`, `P0-03` e `RUN-STG-01`.

Este documento deve ser convertido em registro semanal final apenas quando houver evidencia nova revisavel ou confirmacao formal de que os bloqueios permanecem.

## Leitura do Ciclo

- baseline tecnica esperada de referencia: `91%`
- baseline regulatoria esperada de referencia: `78%`
- baseline consolidada esperada de referencia: `87%`
- foco da semana: decidir se houve prova material suficiente para mover algum `P0`, fechar `RUN-STG-01` ou manter a baseline oficialmente sem recalibracao

## Contexto da Revisao

- origem do snapshot anterior:
  - [Plano Consolidado de Continuidade e Execucao](../../../history/CONTINUATION_EXECUTION_PLAN_2026_07.md)
  - [Governança Semanal 2026-07-06](../2026-07-06/2026-07-06-weekly-governance.md)
- janela seria em observacao:
  - `window_id`: `stg-2026-07-06-a`
- criterio macro:
  - manter `91% / 78% / 87%` se nao houver artefato novo revisavel
  - recalibrar apenas se houver checker/bundle/dossie/sign-off com valor operacional real

## Perguntas-Chave do Encontro

1. `P0-02` recebeu credenciais reais e checker verde?
2. `P0-03` recebeu URL tokenizada valida e JSONs de preflight/sync?
3. `P0-01` saiu de `blocked` com provider real, bundle OIDC e validacao seria?
4. `RUN-STG-01` concluiu com `artifact`, `packet`, `dossie` e `sign-off` revisaveis?
5. ownership/SLA e retention/recovery receberam aceite formal novo?

## Evidencias Revisadas - Preencher no Encontro

- artifact principal da janela: `serious-staging-window-stg-2026-07-06-a: pending`
- overall status: `failed` no snapshot consolidado mais recente
- validation status: `ok` em `validate_serious_window_artifact`
- preflight status: `failed` no rerun factual mais recente
- run status: `failed` por `placeholder_check` e `handoff_check`
- window packet: `pending`
- dossier: `pending`
- homologation: `pendente de evidencia externa real`
- oidc bundle summary: `stg-2026-07-06-a-oidc-readiness-bundle.json`, sem homologacao real
- regulatory bundle summary: `stg-2026-07-06-a-regulatory-readiness-bundle.json`, sem credencial real homologada

## KPI da Semana - Decisao Esperada

### Cenario A - Sem evidencia material nova

- construcao tecnica: `91%`
- prontidao regulatoria: `78%`
- KPI total consolidado: `87%`
- houve recalibracao material?: `nao`

### Cenario B - Avanco real em `P0-02` e/ou `P0-03`

- construcao tecnica: `91-93%`
- prontidao regulatoria: `82-84%`
- KPI total consolidado: `88-89%`
- houve recalibracao material?: `sim`, se houver bundle/artefato revisavel

### Cenario C - Fechamento de `RUN-STG-01` com dossie aceito

- construcao tecnica: `93-95%`
- prontidao regulatoria: `85-88%`
- KPI total consolidado: `91%`
- houve recalibracao material?: `sim`

## Itens para Revisao

### `P0-02` `AML/KYT live`

- status anterior esperado: `ready`
- gatilho legitimo de avanço:
  - `check-compliance-provider-runtime` verde com credencial real
- decisao de passagem:
  - se houver checker + JSON: `ready_for_validation`
  - se houver checker + bundle consolidado revisado: `done`
  - se nao houver credencial real: manter `ready`

### `P0-03` feed UE real

- status anterior esperado: `ready`
- gatilho legitimo de avanço:
  - `source_url` tokenizada valida + JSONs de preflight/sync
- decisao de passagem:
  - se houver JSONs validos: `ready_for_validation`
  - se houver bundle regulatorio final revisado: `done`
  - se nao houver URL valida: manter `ready`

### `P0-01` `OIDC + MFA` serio

- status anterior esperado: `blocked`
- gatilho legitimo de avanço:
  - preflight + smoke + bundle OIDC com provider real
- decisao de passagem:
  - se houver execucao parcial seria: `in_progress`
  - se houver bundle valido aguardando revisao final: `ready_for_validation`
  - se nao houver provider real: manter `blocked`

### `RUN-STG-01` primeira janela seria

- status anterior esperado: `pending_execucao`
- gatilho legitimo de avanço:
  - workflow concluido com artifact oficial, packet, dossie e sign-off
- decisao de passagem:
  - se workflow rodou, mas a revisao final ainda nao terminou: `ready_for_validation`
  - se `overall status=ok` e docs sincronizadas: `done`
  - se o war room seguir `no-go`: manter `pending_execucao`

### `P1-03` ownership/SLA

- status anterior esperado: `in_progress`
- gatilho legitimo de avanço:
  - aceite escrito + drill documentado
- decisao de passagem:
  - `ready_for_validation` ou `done`, conforme o aceite coletado

### `P2-01` retention/recovery

- status anterior esperado: `in_progress`
- gatilho legitimo de avanço:
  - restore revisado + RTO/RPO + sign-offs
- decisao de passagem:
  - `ready_for_validation` ou `done`

## Itens Blocked - Preencher se Persistirem

- ID: `P0-01`
  - motivo: homologacao real de `OIDC + MFA` segue pendente; bundle local nao equivale a prova seria homologada
  - dependencia externa: provider de identidade, segredos reais e aceite institucional do trilho serio
  - owner da escalacao: `Security/Auth`

- ID: `P0-02`
  - motivo: credencial AML/KYT real ainda nao foi anexada ao checker operacional
  - dependencia externa: provider AML/KYT
  - owner da escalacao: `Compliance/AML`

- ID: `P0-03`
  - motivo: URL tokenizada real do feed UE ainda nao foi confirmada com JSONs de preflight/sync validos
  - dependencia externa: provider do feed UE
  - owner da escalacao: `Compliance/Backend`

- ID: `RUN-STG-01`
  - motivo: janela continua em `no-go`, com `12` placeholders e `8` handoffs pendentes
  - dependencia externa: provisao de secrets/URLs reais e fechamento de `date/status` por dominio
  - owner da escalacao: `Release Manager Tecnico`

## Decisoes Esperadas do Encontro

- manter baseline, se nao houver prova nova revisavel
- nao promover `P0-01`, `P0-02` ou `P0-03` sem checker, bundle ou artefato oficial correspondente
- nao promover `RUN-STG-01` sem `artifact` e `dossie` revisaveis
- explicitar por escrito qualquer excecao usada no war room

### Posicao Base Esperada na Ausencia de Novas Evidencias

- decisao executiva: `manter baseline`
- KPI oficial: `91% / 78% / 87%`
- leitura da janela: `pre-serious-window` com `no-go` operacional mantido
- proximo melhor candidato a avanço: `P0-02` ou `P0-03`, dependendo da primeira credencial externa valida disponivel
- principal escalacao da semana: `P0-01`, por depender de provider OIDC serio e aceite institucional

## Acoes Esperadas para a Semana Seguinte

- concluir o primeiro `P0` que tiver insumo real disponivel
- executar a primeira janela seria apenas se o `no-go` sair de bloqueio
- colher aceite formal de ownership/SLA e retention/recovery quando houver evidencia suficiente
- publicar novo scorecard apenas se a governanca registrar prova material

## Observacoes

- este rascunho existe para acelerar a proxima reuniao semanal
- se nao houver evidencia nova real, a saida correta continua sendo confirmar bloqueios e manter a baseline
- este documento nao substitui o registro final da semana; ele serve como base de preenchimento
