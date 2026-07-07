# Preparação da Governança — 2026-07-06

## Objetivo

Servir como pauta inicial e folha de preparação para a próxima reunião de governança, usando a baseline validada em 2026-07-03.

## Leitura Base Obrigatória

- [Avaliacao Consolidada de Status do Projeto](../../../assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- [Checklist Operacional para 95%](../../../EXECUTION_CHECKLIST_TO_95_PERCENT.md)
- [Tracker Semanal de Owners para 95%](../../../history/WEEKLY_OWNERS_TRACKER_TO_95_PERCENT.md)
- [Governança Semanal 2026-07-03](../../archive/weekly/2026-07-03-weekly-governance.md)
- [Execucao Local de Preflight da Janela Seria 2026-07-03](../2026-07-03/2026-07-03-staging-serious-window-local-preflight.md)
- [Plano de Acao do War Room `stg-2026-07-06-a`](../../generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-war-room-action-plan.md)
- [Status Snapshot `stg-2026-07-06-a`](../../generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-status-snapshot.md)
- [Governance Dashboard `stg-2026-07-06-a`](../../generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-governance-dashboard.md)

## Leitura Inicial do Encontro

- baseline técnica: `91%`
- baseline regulatória: `78%`
- baseline consolidada: `87%`
- decisão atual: `go` para validação séria controlada e `no-go` para produção regulada forte

## Objetivo do Encontro

- confirmar se houve evidência nova real desde 2026-07-03
- checar o estado dos owners `P0`
- decidir se algum item pode sair de `blocked` ou `ready`
- confirmar readiness da janela `stg-2026-07-06-a`

## Snapshot Pré-Preenchido em 2026-07-03

| Bloco | Estado conhecido em 2026-07-03 | Próximo gatilho legítimo |
| --- | --- | --- |
| `P0-02` `AML/KYT live` | `ready`, sem credencial real anexada | credencial real + checker verde + JSON |
| `P0-03` feed UE real | `ready`, sem URL tokenizada real anexada | URL real + preflight/sync JSON |
| `P0-01` `OIDC + MFA` | `blocked`, trilho local existe mas sem homologação real | provider confirmado + preflight/smoke/E2E |
| owners/SLA | `ready_for_approval` | aceite formal registrado |
| retention/recovery | `ready_for_approval` | restore evidenciado + aceite |
| janela `stg-2026-07-06-a` | `pre-serious-window` | gate agregado verde + artefato anexável |

## Leituras de Entrada já Confirmadas

- baseline mantida em `91% / 78% / 87%`
- suíte principal Python revisada com `127 passed`
- preflight local da janela executado com bloqueios objetivos registrados
- validacao agregada de artifact da janela executada com `status=ok`
- nenhum item `P0` promovido artificialmente desde 2026-07-03
- decisão vigente permanece `go` para validação séria controlada e `no-go` para produção regulada forte

## Perguntas de Decisão

### `P0-02` `AML/KYT live`

- houve credencial real recebida?
- o checker foi executado?
- existe JSON persistido anexável?

### `P0-03` feed UE real

- houve URL tokenizada válida recebida?
- a janela UE local foi executada?
- os JSONs de preflight e sync existem e foram revisados?

### `P0-01` `OIDC + MFA`

- o provider foi confirmado?
- credenciais reais foram entregues?
- preflight, smoke e E2E foram executados?

### Governança

- houve aceite novo de owners/SLA?
- houve teste novo de retention/recovery?
- a janela séria tem insumos mínimos para sair de `no-go`?

## Ações Esperadas por Owner

| Bloco | Owner nominal | Resultado esperado no encontro |
| --- | --- | --- |
| `P0-02` | `Compliance/Backend` | evidência real ou bloqueio explicitamente mantido |
| `P0-03` | `Compliance/Backend` | evidência real ou bloqueio explicitamente mantido |
| `P0-01` | `Backend/Auth` | evidência real ou bloqueio explicitamente mantido |
| owners/SLA | `Platform/SRE` e `Security` | status de aceite atualizado |
| retention/recovery | `Platform/DBA`, `Security`, `Compliance` | status do restore e aceites atualizado |

## Checklist de Execução no Encontro (Prático)

### `Backend/Auth` (`P0-01`)

- confirmar entrega de credenciais/claims reais
- rodar `python scripts/preflight_oidc_serious_env.py`
- rodar `python scripts/smoke_auth_oidc_mode.py`
- anexar JSONs de saída no pacote da janela

### `Compliance/Backend` (`P0-02` e `P0-03`)

- confirmar `COMPLIANCE_TRM_API_KEY` e `COMPLIANCE_TRM_SCREENING_URL`
- rodar `make check-compliance-provider-runtime`
- confirmar `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada
- rodar `make run-eu-sanctions-window-local WINDOW_ID=stg-2026-07-06-a`

### `Backend Core` e `Platform/DBA` (`Investigation/RPC`)

- confirmar RPC primário/fallback fora de placeholder
- rodar `python scripts/preflight_external_integrations.py`

### `Platform/SRE` (`Owners/SLA` e operação)

- completar `date/status` de todos os grupos em `docs/staging-env-ownership.md`
- rodar `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md`
- rodar gate agregado:
  - `python scripts/prepare_staging_window.py --window-id stg-2026-07-06-a --mode baseline --private-env-file .env.staging.private --validate --preflight`

Se o gate agregado ficar verde:

- executar `python scripts/run_staging_window.py --window-id stg-2026-07-06-a --private-env-file .env.staging.private`

## Critério de Saída do Encontro

- nenhum item sobe de status sem evidência nova
- qualquer bloqueio externo continua marcado como bloqueio externo
- qualquer mudança de baseline exige atualização formal do KPI
- qualquer decisão de `go/no-go` deve referenciar os artefatos vigentes

## Comando de Atualizacao Rapida

Antes da reuniao (ou no inicio do war room), atualizar o plano automatico com:

- `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-06-a`
- `make render-staging-war-room-action-plan WINDOW_ID=stg-2026-07-06-a`
- `make run-staging-window-status-snapshot-local WINDOW_ID=stg-2026-07-06-a`
- `make render-staging-window-status-snapshot-delta WINDOW_ID=stg-2026-07-06-a`
- artefato esperado: `artifacts/staging/checks/stg-2026-07-06-a-status-snapshot.json`
- artefato esperado: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-status-snapshot-delta.md`
- artefato esperado: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-governance-dashboard.md`
- leitura executiva recomendada: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-governance-dashboard.md`
- leitura operacional recomendada: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-unblock-checklist.md`
- leitura executiva curta recomendada: `docs/governance-weekly/generated/windows/stg-2026-07-06-a/stg-2026-07-06-a-governance-dashboard.md`

## Observação

Este documento é de preparação de reunião. Ele não substitui o registro semanal fechado nem deve ser tratado como evidência de execução realizada.

Se não houver evidência nova real até a data da reunião, a saída esperada do encontro é manter baseline e bloqueios explicitamente.
