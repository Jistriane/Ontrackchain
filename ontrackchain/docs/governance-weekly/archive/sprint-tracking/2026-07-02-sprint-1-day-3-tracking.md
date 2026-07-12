# Tracking do Dia 3 da Sprint 1 — `stg-2026-07-02-a`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-a`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `blocked`
- checkpoint atual: leitura inicial do `Dia 3` preparada; aguardando URL tokenizada valida da UE e execucao real da janela dedicada
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- URL tokenizada da UE confirmada
- runner da janela UE executado com JSONs persistidos
- checker pos-sync verde
- convergencia de `EU_CONSOLIDATED` em `sanctions_lists_meta`
- decisao explicita sobre passagem para o `Dia 4`

## Status Permitidos

- item P0: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 3

### T1 — Validar precondicoes do Dia 3

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: precondicoes desenhadas, mas ainda dependentes do fechamento aceitavel do `Dia 2`
- observacoes: nao tratar a trilha UE como pronta enquanto `P0-03` nao tiver URL real e owner responsavel confirmados

### T2 — Confirmar URL tokenizada e readiness do feed UE

- status: `blocked`
- owner: `Compliance/Backend`
- resultado: `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` ainda nao confirmada neste snapshot
- observacoes: este e o bloqueio central do `Dia 3`

### T3 — Rodar preflight externo

- status: `pending`
- owner: `Platform/SRE`
- comando 1: `python scripts/preflight_external_integrations.py`
- comando 2: `python -m unittest tests.test_preflight_guards`
- resultado: aguardando execucao real
- observacoes: precisa validar a elegibilidade da URL antes do runner

### T4 — Executar a janela UE dedicada

- status: `pending`
- owner: `Compliance/Backend`
- comando 1: `make run-eu-sanctions-window-local WINDOW_ID=stg-YYYY-MM-DD-a`
- resultado: aguardando execucao real
- observacoes: somente valido se gerar JSONs persistidos

### T5 — Rodar o checker pos-sync de sancoes

- status: `pending`
- owner: `Compliance/Backend`
- comando 1: `python scripts/check_sanctions_sync_status.py --eu-window`
- comando 2: `python -m unittest tests.test_check_sanctions_sync_status`
- resultado: aguardando execucao real
- observacoes: depende de `T4`

### T6 — Validar convergencia em `sanctions_lists_meta`

- status: `pending`
- owner: `Arquitetura/Compliance`
- resultado: aguardando outputs do runner e do checker
- observacoes: conferir `status`, `last_sync_status` e `source_url`

### T7 — Atualizar `P0-03` e decidir passagem para o Dia 4

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: dependera de `T2` a `T6`
- observacoes: nao liberar `Dia 4` se `P0-03` seguir sem JSONs e sem convergencia real

## Leitura dos P0 ao Fim do Dia

|Item|Status|Owner confirmado?|Insumo real disponivel?|Proximo passo|
|---|---|---|---|---|
|`P0-01`|`blocked`|`no`|`no`|manter em trilha de identidade ate confirmacao institucional do MFA|
|`P0-02`|`blocked`|`yes`|`no`|encerrar homologacao AML/KYT antes de consolidar bundle|
|`P0-03`|`blocked`|`yes`|`no`|confirmar URL tokenizada, rodar janela UE e validar convergencia|
|`P0-04`|`todo`|`yes`|`no`|aguardar artefatos materiais de `P0-02` e `P0-03`|

## Bloqueadores Ativos

- ID: `D3-01`
  - item: `P0-03`
  - categoria: `url_missing`
  - descricao: URL tokenizada da UE ainda nao confirmada para a sprint
  - owner da escalacao: `Compliance/Backend`
  - status: `open`
  - proximo checkpoint: validar `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- ID: `D3-02`
  - item: `Dia 3`
  - categoria: `institutional_pending`
  - descricao: a janela UE nao deve ser executada enquanto `Dia 2` permanecer sem homologacao real de compliance runtime
  - owner da escalacao: `Arquitetura/Governanca`
  - status: `open`
  - proximo checkpoint: obter leitura final aceitavel do `Dia 2`

## Evidencias Coletadas

- `preflight_external_integrations.py`: `pending`
- `<janela>-eu-sanctions-preflight.json`: `pending`
- `<janela>-eu-sanctions-sync.json`: `pending`
- `check_sanctions_sync_status.py --eu-window`: `pending`
- `tests.test_check_sanctions_sync_status`: `pending`
- leitura de `EU_CONSOLIDATED`: `pending`

## Decisao de Passagem

- decisao para o `Dia 4`: `nao`
- motivo principal: ainda nao existe evidência real do feed UE com JSONs persistidos e convergencia em banco
- condicao que falta para liberar, se houver: validar URL tokenizada, executar a janela UE e obter checker pos-sync verde com `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o `Dia 3` esta pronto como trilha de homologacao do feed UE, mas permanece bloqueado ate a confirmacao da URL tokenizada e da execucao real do runner
- owner do primeiro passo do `Dia 4`: `a definir apos fechamento real do Dia 3`
- artefato relacionado (legado, alvo removido da trilha viva): `sprint-1-day-3-execution-runbook.md`
