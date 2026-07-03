# Tracking do Dia 2 da Sprint 1 — `stg-2026-07-02-a`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-a`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `blocked`
- checkpoint atual: leitura inicial do `Dia 2` preparada; aguardando credencial real AML/KYT e outputs do preflight externo
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- credencial real AML/KYT confirmada ou bloqueio formalizado
- preflight externo coerente com modo `live`
- checker de runtime anexavel
- convergencia entre readiness interno, catalogo e runtime
- decisao explicita sobre passagem para o `Dia 3`

## Status Permitidos

- item P0: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 2

### T1 — Validar precondicoes do Dia 2

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: precondicoes mapeadas, mas ainda dependentes da leitura real do `Dia 1` e da credencial AML/KYT
- observacoes: nao abrir homologacao do provider sem owner nominal e secret real

### T2 — Confirmar readiness de secrets AML/KYT

- status: `blocked`
- owner: `Compliance/Backend`
- resultado: credencial real `COMPLIANCE_TRM_*` ainda nao confirmada neste snapshot
- observacoes: este e o bloqueio principal do `Dia 2`

### T3 — Rodar preflight externo

- status: `pending`
- owner: `Platform/SRE`
- comando 1: `python scripts/preflight_external_integrations.py`
- comando 2: `python -m unittest tests.test_preflight_guards`
- resultado: aguardando execucao real
- observacoes: so rodar depois de confirmar secrets e escopo do dia

### T4 — Rodar o checker de runtime do provider

- status: `pending`
- owner: `Compliance/Backend`
- comando 1: `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- comando 2: `python -m unittest tests.test_check_compliance_provider_runtime`
- resultado: aguardando execucao real
- observacoes: depende da liberacao de `T2`

### T5 — Validar convergencia das tres camadas

- status: `pending`
- owner: `Arquitetura/Compliance`
- resultado: aguardando outputs de `T3` e `T4`
- observacoes: precisa comparar readiness interno, catalogo e runtime publico

### T6 — Registrar degradacoes e falhas reais

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: categorias de degradacao ja definidas para o dia
- observacoes: registrar timeout, contract drift ou indisponibilidade do provider sem suavizar a leitura

### T7 — Atualizar `P0-02` e decidir passagem para o Dia 3

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: dependera de `T2` a `T5`
- observacoes: nao liberar `Dia 3` se `P0-02` seguir sem evidência operacional anexavel

## Leitura dos P0 ao Fim do Dia

|Item|Status|Owner confirmado?|Insumo real disponivel?|Proximo passo|
|---|---|---|---|---|
|`P0-01`|`blocked`|`no`|`no`|confirmar owner IdP/MFA e manter fora do bundle ate leitura honesta|
|`P0-02`|`blocked`|`yes`|`no`|confirmar credencial real AML/KYT e executar preflight/checker|
|`P0-03`|`ready`|`yes`|`no`|aguardar validacao da URL tokenizada UE no `Dia 3`|
|`P0-04`|`todo`|`yes`|`no`|aguardar artefatos reais de `P0-02` e `P0-03`|

## Bloqueadores Ativos

- ID: `D2-01`
  - item: `P0-02`
  - categoria: `secret_missing`
  - descricao: credencial real AML/KYT ainda nao confirmada para o ambiente serio da sprint
  - owner da escalacao: `Compliance/Backend`
  - status: `open`
  - proximo checkpoint: validar disponibilidade de `COMPLIANCE_TRM_*`
- ID: `D2-02`
  - item: `Dia 2`
  - categoria: `institutional_pending`
  - descricao: a homologacao nao deve ser iniciada sem leitura final de owners e insumos do `Dia 1`
  - owner da escalacao: `Arquitetura/Governanca`
  - status: `open`
  - proximo checkpoint: fechar rastreabilidade minima do `Dia 1`

## Evidencias Coletadas

- `preflight_external_integrations.py`: `pending`
- `tests.test_preflight_guards`: `pending`
- `check-compliance-provider-runtime`: `pending`
- `tests.test_check_compliance_provider_runtime`: `pending`
- leitura de convergencia das tres camadas: `pending`

## Decisao de Passagem

- decisao para o `Dia 3`: `nao`
- motivo principal: ainda nao existe evidência real do provider AML/KYT em modo `live`
- condicao que falta para liberar, se houver: confirmar secret real, executar preflight e obter checker anexavel sem divergencia entre as tres camadas

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o `Dia 2` esta preparado como trilha de homologacao AML/KYT, mas permanece bloqueado ate a liberacao de credencial real e outputs dos checkers
- owner do primeiro passo do `Dia 3`: `a definir apos fechamento real do Dia 2`
- artefato relacionado: [Runbook de Execucao do Dia 2 da Sprint 1](../sprint-1-day-2-execution-runbook.md)
