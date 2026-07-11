# Governança Semanal — 2026-07-13 (Rascunho)

## Objetivo

Servir como rascunho da proxima revisao semanal de governanca, derivado do estado consolidado em `2026-07-06`, do plano consolidado vigente e dos gatilhos legitimos de avanço definidos para `P0-01`, `P0-02`, `P0-03` e `RUN-STG-01`.

Este documento deve ser convertido em registro semanal final apenas quando houver evidencia nova revisavel ou confirmacao formal de que os bloqueios permanecem.

## Leitura do Ciclo

- baseline tecnica esperada de referencia: `92%`
- baseline regulatoria esperada de referencia: `79%`
- baseline consolidada esperada de referencia: `88%`
- foco da semana: decidir se houve prova material suficiente para mover algum `P0`, fechar `RUN-STG-01` ou manter a baseline oficialmente sem recalibracao

## Contexto da Revisao

- origem do snapshot anterior:
  - [Plano Consolidado ate 95%](../../../project-construction-plan-to-95-percent.md)
  - [Governança Semanal 2026-07-06](../2026-07-06/2026-07-06-weekly-governance.md)
- janela seria em observacao:
  - `window_id`: `stg-2026-07-13-a`
  - artefatos vivos do ciclo: `war room`, `tracking`, `run sheet`, `bridge quick-fill`, `sign-off` e `decision packet`
- criterio macro:
  - manter `92% / 79% / 88%` se nao houver artefato novo revisavel
  - recalibrar apenas se houver checker/bundle/dossie/sign-off com valor operacional real

## Perguntas-Chave do Encontro

1. `P0-02` recebeu credenciais reais e checker verde?
2. `P0-03` recebeu URL tokenizada valida e JSONs de preflight/sync?
3. `P0-01` saiu de `blocked` com provider real, bundle OIDC e validacao seria?
4. `RUN-STG-01` concluiu com `artifact`, `packet`, `dossie` e `sign-off` revisaveis?
5. ownership/SLA e retention/recovery receberam aceite formal novo?

## Evidencias Revisadas - Preencher no Encontro

- artifact principal da janela: `serious-staging-window-stg-2026-07-13-a: pending`
- overall status: `pending` na tentativa datada ainda em preparacao
- validation status: `pending`, aguardando payload consolidado real
- preflight status: `pending`, aguardando gate agregado da janela datada
- run status: `pending`, aguardando insumos reais e owners online
- window packet: `pending`
- dossier: `pending`
- homologation: `pendente de evidencia externa real`
- oidc bundle summary: `P0-01` segue `blocked` por provider serio nao homologado
- regulatory bundle summary: `P0-02/P0-03` preparados documentalmente, mas ainda sem prova material real na mesma janela
- decision packet: `pending_no_go`, aguardando owners online, credencial AML/KYT real e URL UE tokenizada

## Matriz Minima de Evidencia para Mover o KPI

| Frente | Owner primario | Evidencia minima obrigatoria | Estado que pode mover | Efeito executivo esperado |
| --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | `Compliance/AML` | `check-compliance-provider-runtime` verde com credencial real + JSON persistido + revisao em governanca | `ready_for_validation` | habilita discutir saida de `88%` para `89%` se a prova for revisavel |
| `P0-03` feed UE real | `Compliance/Backend` | URL tokenizada valida + `eu-sanctions-preflight.json` + `eu-sanctions-sync.json` + `check_sanctions_sync_status.py` coerente | `ready_for_validation` | habilita discutir saida de `88%` para `89%` se a prova for revisavel |
| `P0-01` `OIDC + MFA` serio | `Security/Auth` | `preflight_oidc_serious_env.py` verde + `smoke_auth_oidc_mode.py` verde + bundle OIDC + Playwright critico verde com provider real | `ready_for_validation` | reduz risco critico, mas sozinho nao justifica nova baseline sem o fechamento regulatorio correspondente |
| `P0-04` bundle regulatorio oficial | `Platform/SRE` | `<window>-regulatory-readiness-bundle.json/.md` consolidando `P0-02` e `P0-03` sem erro residual nao classificado | `done` | habilita discutir travessia legitima para `90%+` |
| `RUN-STG-01` primeira janela seria | `Platform/SRE + Governanca` | artifact oficial + packet + dossier + war room + sign-off formal | `done` | habilita recalibracao executiva mais forte e reduz dependencia de narrativa |

Regras sinteticas:

- uma unica prova isolada de `P0-02` ou `P0-03` pode sustentar debate de `89%`, mas nao de `90%+`
- `90%+` exige prova combinada e revisavel de readiness regulatoria, preferencialmente fechando `P0-04`
- `P0-01` reduz risco institucional, mas deve ser lido como multiplicador de confianca, nao como gatilho unico de score

## KPI da Semana - Decisao Esperada

### Cenario A - Sem evidencia material nova

- construcao tecnica: `92%`
- prontidao regulatoria: `79%`
- KPI total consolidado: `88%`
- houve recalibracao material?: `nao`

### Cenario B - Avanco real em `P0-02` e/ou `P0-03`

- construcao tecnica: `92-93%`
- prontidao regulatoria: `82-84%`
- KPI total consolidado: `89-90%`
- houve recalibracao material?: `sim`, se houver bundle/artefato revisavel

### Cenario C - Fechamento de `RUN-STG-01` com dossie aceito

- construcao tecnica: `93-95%`
- prontidao regulatoria: `85-88%`
- KPI total consolidado: `92%`
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
- impacto minimo no KPI:
  - isoladamente, pode sustentar debate de `89%` quando a prova for revisavel
  - combinado com `P0-03` e `P0-04`, pode sustentar discussao de `90%+`

### `P0-03` feed UE real

- status anterior esperado: `ready`
- gatilho legitimo de avanço:
  - `source_url` tokenizada valida + JSONs de preflight/sync
- decisao de passagem:
  - se houver JSONs validos: `ready_for_validation`
  - se houver bundle regulatorio final revisado: `done`
  - se nao houver URL valida: manter `ready`
- impacto minimo no KPI:
  - isoladamente, pode sustentar debate de `89%` quando a prova for revisavel
  - combinado com `P0-02` e `P0-04`, pode sustentar discussao de `90%+`

### `P0-01` `OIDC + MFA` serio

- status anterior esperado: `blocked`
- gatilho legitimo de avanço:
  - preflight + smoke + bundle OIDC com provider real
- decisao de passagem:
  - se houver execucao parcial seria: `in_progress`
  - se houver bundle valido aguardando revisao final: `ready_for_validation`
  - se nao houver provider real: manter `blocked`
- impacto minimo no KPI:
  - reduz risco critico e fortalece `go/no-go`
  - nao deve mover baseline sozinho sem fechamento regulatorio correspondente

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
  - motivo: janela `stg-2026-07-13-a` segue em `pending_no_go`, aguardando owners online, credencial AML/KYT real e URL UE tokenizada
  - dependencia externa: provisao de secrets/URLs reais e checkpoint agregado verde para a tentativa datada
  - owner da escalacao: `Release Manager Tecnico`

## Decisoes Esperadas do Encontro

- manter baseline, se nao houver prova nova revisavel
- nao promover `P0-01`, `P0-02` ou `P0-03` sem checker, bundle ou artefato oficial correspondente
- nao promover `RUN-STG-01` sem `artifact` e `dossie` revisaveis
- explicitar por escrito qualquer excecao usada no war room

### Posicao Base Esperada na Ausencia de Novas Evidencias

- decisao executiva: `manter baseline`
- KPI oficial: `92% / 79% / 88%`
- leitura da janela: `dress_rehearsal_controlado` com `pending_no_go` operacional mantido
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
