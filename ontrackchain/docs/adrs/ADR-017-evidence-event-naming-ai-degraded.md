# ADR-017 — Nomeação de Eventos de Evidência para IA (AI_DEGRADED)

## Contexto

O `evidence_trail` registra eventos regulatórios append-only e encadeados. Para fluxos de IA, precisamos registrar degradações de forma:

- filtrável (por prefixo)
- auditável (motivo explícito)
- estável (conjunto de eventos controlado)

## Decisão

- Manter a família `AI_DEGRADED_*` como convenção para filtros e buscas.
- Emitir instâncias explícitas para os motivos baseline:
  - `AI_DEGRADED_LLM_DOWN`
  - `AI_DEGRADED_LLM_429`
  - `AI_DEGRADED_RPC_PARTIAL`
  - `AI_DEGRADED_RPC_TIMEOUT`
  - `AI_DEGRADED_PROVIDER_DEGRADED`
- Para motivos novos/experimentais, permitir `AI_DEGRADED_*` e registrar o motivo em `event_payload.degradation_reason`.

## Consequências

- Prós: padronização, filtros consistentes e melhor auditoria.
- Contras: exige manutenção do catálogo baseline quando novos motivos forem adicionados.

