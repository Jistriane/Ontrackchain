# Planos, Limites e Catalogos

## Objetivo

Consolidar as regras atuais de plano, limites operacionais e catalogos autoritativos do scaffold.

Este documento existe para responder rapidamente:

- o que cada plano pode fazer
- quais limites operacionais existem no MVP
- quais tipos de relatorio e operacoes estao disponiveis

## Ordem de Planos

Ordem de capacidade observada no backend:

```text
free -> starter -> professional -> enterprise
```

Essa ordem impacta:

- elegibilidade de catalogos
- profundidade maxima por chain
- concorrencia de investigacao
- acesso a operacoes premium

## Principios de Enforcement

- catalogos sao filtrados por plano
- `quote` e `start` respeitam `plan lock`
- downgrade desde o quote bloqueia execucao
- upgrade desde o quote exige novo quote

## Investigacao — Limites por Chain

Fonte: [main.py](../apps/investigation-api/src/investigation_api/main.py)

### EVM (`ethereum`, `polygon`, `bsc`, `arbitrum`, `base`)

| Plano | Profundidade |
|---|---:|
| `free` | 1 |
| `starter` | 3 |
| `professional` | 5 |
| `enterprise` | 8 |
| `hard_max` | 10 |

### Bitcoin

| Plano | Profundidade |
|---|---:|
| `free` | 0 |
| `starter` | 2 |
| `professional` | 3 |
| `enterprise` | 3 |
| `hard_max` | 3 |

Observacao:

- Bitcoin continua intencionalmente capado em `3 hops` no MVP

## Investigacao — Concorrencia MVP

Fonte: [agent_concurrency.py](../apps/investigation-api/src/investigation_api/config/agent_concurrency.py)

| Plano | Max investigacoes concorrentes |
|---|---:|
| `free` | 0 |
| `starter` | 1 |
| `professional` | 2 |
| `enterprise` | 5 |

Limites globais:

- `global_max_concurrent_investigations = 10`
- `investigation_timeout_seconds = 300`
- `celery_workers = 4`
- `celery_concurrency_per_worker = 2`

Comportamento esperado:

- dentro do limite: `200` com `processing`
- acima do limite: `202` com `queued` e `position_in_queue`

## Catalogo de Report Types

Fonte: [main.py](../apps/investigation-api/src/investigation_api/main.py)

| Canonico | Min Plan | Formato | Observacao |
|---|---|---|---|
| `risk_check_instant` | `starter` | `json` | score AML 5D sem PDF |
| `technical_basic` | `starter` | `pdf` | relatorio tecnico basico |
| `technical_full` | `professional` | `pdf` | analise aprofundada |
| `compliance_aml` | `starter` | `pdf` | compliance/AML/KYT |
| `coaf_ready_report` | `professional` | `pdf` | baseline regulatorio |
| `legal_report` | `enterprise` | `pdf` | exige strong auth no download |
| `full_investigation` | `enterprise` | `pdf` | pacote mais completo |

### Aliases Relevantes

- `technical`, `tech`, `basic` -> `technical_basic`
- `coaf`, `coaf_report`, `ros` -> `coaf_ready_report`
- `aml`, `kyt`, `compliance` -> `compliance_aml`
- `legal`, `juridico`, `parecer` -> `legal_report`
- `full`, `investigation` -> `full_investigation`
- `risk`, `instant`, `quick_check` -> `risk_check_instant`

## Compliance — Operacoes

Fonte: [main.py](../apps/compliance-api/src/compliance_api/main.py)

| Canonico | Min Plan | Formato | Referencia |
|---|---|---|---|
| `kyc_wallet` | `starter` | `json` | Lei 9.613/98, Res. BCB 520 |
| `due_diligence` | `professional` | `json+pdf` | Res. BCB 520 Art. 44-47 |
| `source_of_funds` | `professional` | `json+pdf` | Res. BCB 520 |
| `sanctions_check` | `starter` | `json` | screening sancoes |

### Aliases Relevantes

- `kyc`, `wallet_kyc` -> `kyc_wallet`
- `dd`, `due_diligence` -> `due_diligence`
- `sof`, `source_of_funds` -> `source_of_funds`
- `sanctions`, `sanctions_check` -> `sanctions_check`

## Monitoring — Operacoes

Fonte: [main.py](../apps/monitoring-api/src/monitoring_api/main.py)

| Canonico | Min Plan | Duracao | Formato |
|---|---|---|---|
| `monitoring_30days` | `starter` | 30 dias | `json+alerts` |
| `monitoring_90days` | `professional` | 90 dias | `json+alerts` |
| `monitoring_365days` | `enterprise` | 365 dias | `json+alerts` |

### Aliases Relevantes

- `30d`, `monthly` -> `monitoring_30days`
- `90d`, `quarterly` -> `monitoring_90days`
- `365d`, `annual` -> `monitoring_365days`

## Regras de Produto Importantes

### 1. Catalogo Autoritativo

O frontend e os consumidores devem preferir os endpoints de catalogo:

- `/api/v1/report-types`
- `/api/v1/compliance/operations`
- `/api/v1/monitoring/operations`

Esses endpoints sao a fonte de verdade para:

- disponibilidade por plano
- aliases aceitos
- chains suportadas
- formato de saida

### 2. Alias Nunca e Persistencia Final

Aliases sao aceitos por UX/API, mas sempre resolvidos para nome canonico antes de:

- billing
- persistencia
- auditoria
- report generation

### 3. Plan Lock

O plano considerado no `quote` precisa permanecer valido no `start`.

## Gaps Atuais

- nao ha ainda uma doc separada por preco/creditos reais de cada operacao
- a matriz de planos ainda e tecnicamente distribuida por dominio
- nao ha feature flags formais para beta/rollout de catalogos

## Recomendacoes

- usar este documento junto com [api-contracts.md](api-contracts.md)
- manter atualizacao sincronizada sempre que houver mudanca em catalogo ou limites
- no futuro, centralizar esse conhecimento em endpoint/versionamento de produto
