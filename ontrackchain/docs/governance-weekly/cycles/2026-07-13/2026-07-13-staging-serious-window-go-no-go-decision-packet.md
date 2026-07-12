# Go/No-Go Decision Packet - `stg-2026-07-13-a`

## Objetivo

Dar uma leitura executiva unica da tentativa `stg-2026-07-13-a`, com:

- decisao atual
- bloqueadores ativos
- evidencias minimas faltantes
- criterio objetivo para promocao

Use este packet junto com:

- [Bridge Quick-Fill `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-bridge-quick-fill.md)
- [War Room da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-war-room.md)
- [Sign-Off da Janela `stg-2026-07-13-a`](./2026-07-13-staging-serious-window-signoff.md)

## Decisao Atual

- `window_id`: `stg-2026-07-13-a`
- `modo`: `dress_rehearsal_controlado`
- `decisao_atual`: `pending_no_go`
- `motivo_principal`: aguardando insumos reais de `P0-02` e `P0-03`, owners online confirmados e `prepare_staging_window --validate --preflight` verde
- `owner_da_decisao`: `Release Manager Tecnico`
- `proximo_checkpoint`: `<preencher_HH:MMZ>`

## Leitura Curta por Frente

| Frente | Estado atual | O que falta | Saida honesta hoje |
| --- | --- | --- | --- |
| `P0-02` AML/KYT | `ready` | credencial real + checker verde + homologacao com `request_id` | `ready_for_validation` |
| `P0-03` Feed UE | `ready` | URL tokenizada real + JSONs de preflight/sync + `source_url_matches_expected=true` | `ready_for_validation` |
| `P0-04` Bundle Regulatorio | `pending` | `P0-02` e `P0-03` verdes na mesma janela + validacao final do artifact `ok` | `ready_for_validation` |
| `P0-01` Auth/OIDC | `blocked` | provider serio homologado + bundle OIDC revisavel | `blocked` |
| `RUN-STG-01` | `pending_execucao` | gate agregado `ok` + pacote de execucao gerado | `pending` |

## Bloqueadores Ativos

- `WR-01`: credencial real do provider AML/KYT ainda nao confirmada neste ciclo
- `WR-02`: URL tokenizada real do feed UE ainda nao confirmada neste ciclo
- `WR-03`: provider OIDC serio e homologacao institucional de MFA seguem pendentes
- `WR-04`: owners online, bridge e checkpoint agregado ainda nao registrados para a tentativa datada

## Evidencias Minimas Faltantes

- `P0-02`
  - JSON do `check-compliance-provider-runtime`
  - homologacao externa preservada
  - `compliance_request_id`
  - `homologation_request_id`
- `P0-03`
  - `stg-2026-07-13-a-eu-sanctions-preflight.json`
  - `stg-2026-07-13-a-eu-sanctions-sync.json`
  - `eu_request_id`
  - `source_url_matches_expected=true`
- `P0-04`
  - `stg-2026-07-13-a-regulatory-readiness-bundle.json`
  - `stg-2026-07-13-a-regulatory-readiness-bundle.md`
  - `artifact_validation_status=ok`
- `Gate agregado`
  - owners online confirmados
  - bridge principal preenchida
  - `prepare_staging_window.py --validate --preflight` com `status=ok`

## Critero Objetivo de Promocao

Promover de `pending_no_go` para `pending_go` somente se todos forem verdadeiros:

- owners online confirmados na bridge
- `P0-02` apto a rodar com insumo real
- `P0-03` apto a rodar com insumo real
- gate agregado executavel sem bloqueio humano imediato

Promover de `pending_go` para `go_with_exception` somente se:

- `P0-02` e `P0-03` tiverem prova material valida
- `P0-04` estiver coerente ou a excecao nao afetar a integridade do bundle
- waiver formal existir e estiver documentado

Promover para `approved` somente se:

- `overall`, `validation`, `preflight` e `run` estiverem `ok`
- `P0-02` em `ready_for_validation` ou `done`
- `P0-03` em `ready_for_validation` ou `done`
- `P0-04` em `ready_for_validation` ou `done`
- sign-off, war room, tracking e run sheet estiverem coerentes

## No-Go Imediato

- credencial AML/KYT indisponivel no momento da execucao
- URL tokenizada UE indisponivel ou incoerente
- `prepare_staging_window --validate --preflight` falhar
- correlator obrigatorio faltar em `P0-02` ou `P0-03`
- `P0-04` bloquear por inconsistência entre as trilhas

## Proximo Passo Executivo

- acao: preencher owners/canais, validar insumos reais de `P0-02` e `P0-03`, e rerodar o gate agregado
- owner: `Release Manager Tecnico`
- destino esperado apos o checkpoint: `pending_go` ou `no-go`
