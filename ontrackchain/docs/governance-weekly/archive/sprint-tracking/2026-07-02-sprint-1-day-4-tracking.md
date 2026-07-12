# Tracking do Dia 4 da Sprint 1 — `stg-2026-07-02-a`

## Contexto Operacional

- data: `2026-07-02`
- `window_id`: `stg-2026-07-02-a`
- facilitador: `Arquiteto/Responsavel Tecnico`
- status global: `blocked`
- checkpoint atual: leitura inicial do `Dia 4` preparada; aguardando owner do trilho serio de identidade, preflight OIDC e evidência de MFA homologado
- ultima atualizacao: `2026-07-02T00:00:00Z`

## Resultado Esperado do Dia

- preflight OIDC serio verde
- smoke auth OIDC verde
- trilho critico de frontend verde ou bloqueio reproduzivel documentado
- enforcement validado para `legal_report`, `ROS/COAF` e `block lift`
- decisao explicita sobre passagem para o `Dia 5`

## Status Permitidos

- item P0: `todo` | `ready` | `in_progress` | `blocked` | `ready_for_validation` | `done`
- bloqueador: `open` | `watching` | `mitigated` | `closed`
- fechamento do dia: `aceitavel` | `parcial` | `nao_aceitavel`

## Tarefas do Dia 4

### T1 — Validar precondicoes do Dia 4

- status: `ready`
- owner: `Facilitador/Arquitetura`
- resultado: precondicoes mapeadas, mas ainda dependentes do fechamento minimamente aceitavel dos `Dias 2` e `3`
- observacoes: nao abrir validacao seria de identidade sem ambiente, owner e status honesto do MFA

### T2 — Confirmar variaveis e URLs do trilho serio

- status: `blocked`
- owner: `Backend/Auth`
- resultado: trilho serio ainda sem confirmacao nominal final de owner e sem leitura real das variaveis no snapshot
- observacoes: `AUTH_MODE=oidc` e `DEV_AUTH_ENABLED=false` precisam ser comprovados, nao assumidos

### T3 — Rodar o preflight OIDC serio

- status: `pending`
- owner: `Backend/Auth`
- comando 1: `python scripts/preflight_oidc_serious_env.py`
- resultado: aguardando execucao real
- observacoes: valida URLs, claims obrigatorias e fechamento do caminho dev

### T4 — Rodar o smoke de auth OIDC

- status: `pending`
- owner: `Backend/Auth`
- comando 1: `python scripts/smoke_auth_oidc_mode.py`
- resultado: aguardando execucao real
- observacoes: precisa confirmar `effective_auth_mode=oidc` e `dev_auth_disabled`

### T5 — Rodar o trilho critico de frontend

- status: `pending`
- owner: `Frontend`
- comando 1: `npm run test:e2e:oidc-critical`
- resultado: aguardando execucao real
- observacoes: falha so e aceitavel se for reproduzivel e nao central ao auth/MFA

### T6 — Validar enforcement nos fluxos sensiveis

- status: `pending`
- owner: `Arquitetura/Auth`
- resultado: aguardando leitura real de headers, contexto e comportamento observado
- observacoes: conferir `legal_report`, `ROS/COAF` e `block lift`

### T7 — Atualizar `P0-01` e decidir passagem para o Dia 5

- status: `pending`
- owner: `Facilitador/Arquitetura`
- resultado: dependera de `T2` a `T6`
- observacoes: nao liberar bundle final se `P0-01` permanecer ambiguo entre configurado e homologado

## Leitura dos P0 ao Fim do Dia

|Item|Status|Owner confirmado?|Insumo real disponivel?|Proximo passo|
|---|---|---|---|---|
|`P0-01`|`blocked`|`no`|`no`|confirmar owner IdP/MFA, rodar preflight e validar enforcement serio|
|`P0-02`|`blocked`|`yes`|`no`|obter checker AML/KYT antes do bundle|
|`P0-03`|`blocked`|`yes`|`no`|obter runner UE e convergencia de `EU_CONSOLIDATED`|
|`P0-04`|`todo`|`yes`|`no`|aguardar `P0-02` e `P0-03` prontos e classificar `P0-01` com honestidade|

## Bloqueadores Ativos

- ID: `D4-01`
  - item: `P0-01`
  - categoria: `owner_missing`
  - descricao: a trilha `OIDC + MFA serio` ainda nao possui owner institucional nominalmente confirmado
  - owner da escalacao: `Arquitetura/Governanca`
  - status: `open`
  - proximo checkpoint: confirmar owner do IdP e do aceite de MFA
- ID: `D4-02`
  - item: `P0-01`
  - categoria: `mfa_not_homologated`
  - descricao: a homologacao operacional do MFA externo ainda nao esta comprovada neste snapshot
  - owner da escalacao: `Backend/Auth`
  - status: `open`
  - proximo checkpoint: validar `MFA_EXTERNAL_PROVIDER_HOMOLOGATED` e comportamento dos fluxos sensiveis

## Evidencias Coletadas

- `preflight_oidc_serious_env.py`: `pending`
- `smoke_auth_oidc_mode.py`: `pending`
- `npm run test:e2e:oidc-critical`: `pending`
- leitura dos fluxos sensiveis: `pending`
- confirmacao de `mfa.provider_homologated`: `pending`

## Decisao de Passagem

- decisao para o `Dia 5`: `nao`
- motivo principal: ainda nao existe evidência real do trilho `OIDC + MFA serio` ponta a ponta
- condicao que falta para liberar, se houver: confirmar owner, rodar preflight/smoke, validar Playwright critico e comprovar enforcement nos fluxos sensiveis

## Fechamento do Dia

- classificacao: `parcial`
- resumo executivo: o `Dia 4` esta pronto como trilha de validacao de identidade forte, mas segue bloqueado por dependencia institucional e ausencia de evidência operacional do MFA homologado
- owner do primeiro passo do `Dia 5`: `a definir apos fechamento real do Dia 4`
- artefato relacionado (legado, alvo removido da trilha viva): `sprint-1-day-4-execution-runbook.md`
