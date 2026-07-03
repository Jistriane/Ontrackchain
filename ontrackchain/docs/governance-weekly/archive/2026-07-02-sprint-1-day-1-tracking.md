# Tracking do Dia 1 da Sprint 1 — `stg-2026-07-02-a`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-a`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `blocked`
- checkpoint atual: leitura inicial do `Dia 1` preparada; aguardando confirmacao de owners e insumos reais dos `P0`
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- `WINDOW_ID` definido
- owners nominais confirmados
- outputs dos tres checkers base coletados
- bloqueadores externos classificados
- decisao explicita sobre passagem para o `Dia 2`

## Status Permitidos

- item P0: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 1

### T1 — Definir contexto da sprint

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: `window_id` proposto como `stg-2026-07-02-a`
- observacoes: confirmar se este `window_id` sera o identificador oficial dos artefatos da sprint

### T2 — Confirmar owners nominais

- status: `in_progress`
- owner: `Arquitetura/Governanca`
- resultado: leitura inicial sugere owners por trilha, mas ainda falta confirmacao nominal final
- observacoes: `P0-01` continua mais sensivel por depender de owner IdP/MFA serio

### T3 — Revisar `.env.staging.private`

- status: `pending`
- owner: `Platform/SRE`
- resultado: aguardando leitura real do arquivo e classificacao dos placeholders criticos
- observacoes: sem esta leitura nao ha base honesta para liberar `P0-02` e `P0-03`

### T4 — Rodar checks base

- status: `pending`
- owner: `Platform/SRE`
- comando 1: `python scripts/check_staging_env_placeholders.py`
- comando 2: `python scripts/check_staging_env_handoff.py`
- comando 3: `python scripts/check_staging_env_ownership_coverage.py`
- resultado: aguardando execucao real
- observacoes: estes tres outputs definem se o dia fica em destravamento ou avanca para liberacao do `Dia 2`

### T5 — Classificar bloqueadores externos

- status: `in_progress`
- owner: `Arquitetura/Governanca`
- resultado: bloqueadores iniciais ja conhecidos foram mapeados, mas ainda faltam owners nominais e ETA
- observacoes: usar este arquivo como fonte unica para consolidar bloqueios do dia

### T6 — Atualizar status operacional dos P0

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: leitura inicial sugerida preparada no board
- observacoes: atualizar so depois da leitura real de owners, secrets e URLs

### T7 — Decidir passagem para o Dia 2

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: dependera de `T2`, `T3` e `T4`
- observacoes: nao liberar `Dia 2` se `P0-02` continuar sem credencial real disponivel

## Leitura dos P0 ao Fim do Dia

|Item|Status|Owner confirmado?|Insumo real disponivel?|Proximo passo|
|---|---|---|---|---|
|`P0-01`|`blocked`|`no`|`no`|confirmar owner IdP/MFA serio e trilho de validacao externa|
|`P0-02`|`ready`|`yes`|`no`|confirmar credencial real AML/KYT antes de mover para `in_progress`|
|`P0-03`|`ready`|`yes`|`no`|confirmar URL tokenizada UE antes de mover para `in_progress`|
|`P0-04`|`todo`|`yes`|`no`|aguardar artefatos reais de `P0-02` e `P0-03`|

## Bloqueadores Ativos

- ID: `D1-01`
  - item: `P0-01`
  - categoria: `owner_missing`
  - descricao: trilha `OIDC + MFA serio` ainda sem confirmacao nominal final do owner institucional
  - owner da escalacao: `Arquitetura/Governanca`
  - status: `open`
  - proximo checkpoint: confirmar owner e canal de escalacao do IdP
- ID: `D1-02`
  - item: `P0-02`
  - categoria: `secret_missing`
  - descricao: credencial real do provider `AML/KYT` ainda nao confirmada no ambiente de sprint
  - owner da escalacao: `Compliance/Backend`
  - status: `open`
  - proximo checkpoint: validar disponibilidade real de `COMPLIANCE_TRM_*`
- ID: `D1-03`
  - item: `P0-03`
  - categoria: `url_missing`
  - descricao: URL tokenizada da UE ainda nao confirmada para a sprint
  - owner da escalacao: `Compliance/Backend`
  - status: `open`
  - proximo checkpoint: validar `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- ID: `D1-04`
  - item: `Dia 1`
  - categoria: `env_incomplete`
  - descricao: leitura de placeholders, handoff e ownership coverage ainda nao executada
  - owner da escalacao: `Platform/SRE`
  - status: `open`
  - proximo checkpoint: rodar os tres checkers base do dia

## Evidencias Coletadas

- `check_staging_env_placeholders.py`: `pending`
- `check_staging_env_handoff.py`: `pending`
- `check_staging_env_ownership_coverage.py`: `pending`
- print da leitura de `.env.staging.private`: `pending`
- lista consolidada de bloqueadores: `in_progress`

## Decisao de Passagem

- decisao para o `Dia 2`: `nao`
- motivo principal: ainda faltam outputs dos checkers base e confirmacao real de owners/secrets/URLs
- condicao que falta para liberar, se houver: executar `T3` e `T4` e reduzir `D1-02` ou classifica-lo com ETA real

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: dia preparado com status iniciais coerentes, mas ainda sem evidencias materiais para liberar homologacao real
- owner do primeiro passo do `Dia 2`: `a definir apos leitura real do Dia 1`
- artefato relacionado: [Runbook de Execucao do Dia 1 da Sprint 1](../sprint-1-day-1-execution-runbook.md)
