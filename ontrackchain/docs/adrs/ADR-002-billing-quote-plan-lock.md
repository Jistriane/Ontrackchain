# ADR-002 — Billing por Quote com Plan Lock

## Contexto

Operacoes de investigation, compliance e monitoring consomem creditos. Sem uma etapa formal de cotacao, o sistema ficaria sujeito a disputa de preco, downgrade oportunista e inconsistencias de cobranca.

## Decisao

Adotar o fluxo obrigatorio:

```text
estimate -> quote_id (TTL) -> start -> PRE_HOLD -> CONFIRMED | REFUND
```

Com `plan lock` entre a cotacao e a execucao:

- downgrade desde o quote bloqueia com `402`
- upgrade desde o quote exige novo quote com `202 requote_required`

## Motivacao

- garantir previsibilidade financeira
- impedir arbitragem indevida de plano
- manter trilha auditavel de cobranca

## Alternativas Consideradas

### Opcao A — Debitar direto no `start`

- Vantagem:
  - UX mais simples
- Desvantagem:
  - pouca previsibilidade
  - dificil explicar cobranca

### Opcao B — Quote formal com reserva de credito

- Vantagem:
  - melhor governanca financeira
  - melhora rastreabilidade
- Desvantagem:
  - mais estados de negocio

## Consequencias

- necessidade de TTL para `quote`
- necessidade de ledger append-only
- necessidade de smoke/E2E cobrindo billing e plan lock

## Trade-offs Aceitos

- mais complexidade de negocio em troca de consistencia financeira

## Status

- Aceito e implementado
