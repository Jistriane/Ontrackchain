# Catálogo de Eventos — evidence_trail

Este documento consolida os `event_type` usados em `evidence_trail` para auditoria e rastreabilidade regulatória. O objetivo é reduzir drift entre contratos de API, regras de negócio e validações.

## Princípios

- `evidence_trail` é append-only e encadeado; use apenas eventos que precisem de defensabilidade regulatória.
- Eventos puramente operacionais devem preferir `audit_logs`.
- Para eventos de IA, usar `retain_until` de 7 anos quando aplicável (ex.: decisões sensíveis e exports).

## Convenções de nomenclatura

- Use nomes em `SCREAMING_SNAKE_CASE`.
- Use famílias apenas quando houver muitas variantes e for útil filtrar por prefixo.
- Prefira instâncias explícitas (evento fixo) quando o conjunto de motivos for conhecido e finito.

### Família vs instância

- Família: `AI_DEGRADED_*` (para queries/filtros por prefixo)
- Instâncias recomendadas: `AI_DEGRADED_LLM_DOWN`, `AI_DEGRADED_LLM_429`, `AI_DEGRADED_RPC_PARTIAL`, `AI_DEGRADED_RPC_TIMEOUT`, `AI_DEGRADED_PROVIDER_DEGRADED`

Regra: quando o motivo estiver dentro do catálogo baseline, emitir a instância. Usar somente a família (`AI_DEGRADED_*`) para motivos novos/experimentais (e registrar o motivo em `event_payload.degradation_reason`).

## Compliance / Sanções

- `SANCTIONS_CHECKED`
- `SANCTIONS_HIT`

## Bloqueios

- `BLOCK_*`

## Contrapartes / KYC

- `COUNTERPARTY_ONBOARDED`

## ROS/COAF

- `COAF_ROS_GENERATED`
- `COAF_ROS_APPROVED`
- `COAF_ROS_REJECTED`
- `COAF_ROS_SUBMITTED_MANUAL`

## IA (Jobs, Human Gate e Degradação)

### Outputs gerados (baseline atual)

- `AI_EXPLAIN_GENERATED`
- `AI_CASE_INSIGHTS_GENERATED`
- `AI_LAW_ENFORCEMENT_EXPORT_GENERATED`
- `AI_THEMIS_CASE_INTELLIGENCE_GENERATED`

### Lifecycle de Job

- `AI_JOB_AWAITING_HUMAN_GATE`
- `AI_JOB_APPROVAL_RECORDED`
- `AI_JOB_DEGRADED`
- `AI_JOB_FAILED`

### Degradação (família)

- `AI_DEGRADED_*`

### Degradação (instâncias recomendadas)

- `AI_DEGRADED_LLM_DOWN`
- `AI_DEGRADED_LLM_429`
- `AI_DEGRADED_RPC_PARTIAL`
- `AI_DEGRADED_RPC_TIMEOUT`
- `AI_DEGRADED_PROVIDER_DEGRADED`
