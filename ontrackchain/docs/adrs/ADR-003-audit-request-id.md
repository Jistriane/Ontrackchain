# ADR-003 — Auditoria Correlacionada por Request ID

## Contexto

O projeto precisa trilhar eventos de investigacao, compliance, billing e download de relatorios de forma forense. Apenas registrar a acao sem correlacao entre camadas dificultaria debug, auditoria e reconstrucao de fluxo.

## Decisao

Padronizar `X-Request-Id` nos fluxos criticos e persisti-lo em `audit_logs.metadata` e, quando aplicavel, em `credit_ledger.metadata`.

## Motivacao

- correlacao ponta a ponta
- suporte a troubleshooting
- auditabilidade regulatoria mais forte

## Estrategia

- frontend proxies propagam ou geram `X-Request-Id`
- APIs geram fallback quando necessario
- smoke runtime usa IDs deterministas por etapa
- eventos de auditoria guardam:
  - `request_id`
  - `resource_type`
  - `resource_id`
  - `report_id`
  - `file_hash_sha256`

## Alternativas Consideradas

### Opcao A — Correlation ID apenas em logs de aplicacao

- Vantagem:
  - mais simples
- Desvantagem:
  - fora do escopo do banco/auditoria

### Opcao B — Persistencia em `audit_logs`

- Vantagem:
  - trilha consultavel e consistente
- Desvantagem:
  - aumenta volume e necessidade futura de retention

## Consequencias

- filtros por `request_id` se tornam parte importante da operacao
- integracoes futuras devem preservar este header
- smoke e Playwright passam a validar correlacao, nao so status HTTP

## Trade-offs Aceitos

- maior volume de metadata em troca de rastreabilidade operacional e regulatoria

## Status

- Aceito e implementado
