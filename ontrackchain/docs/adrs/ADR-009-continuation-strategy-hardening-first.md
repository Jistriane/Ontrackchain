# ADR-009: Continuidade — Hardening First e Modularização Guiada

## Contexto

O Ontrackchain ja ultrapassou o estagio de scaffold basico e opera com:

- gateway com `ForwardAuth`
- `PostgreSQL RLS` como ultima linha de defesa multi-tenant
- trilha auditavel `append-only` por `request_id`
- worker assíncrono real para investigation e fila/DLQ
- observabilidade central via `Prometheus -> Alertmanager -> monitoring-api` com triagem e export auditado
- CI com smoke + E2E Playwright e quality gates por componente

Apesar disso, a credibilidade para `staging` serio e operacao regulada permanece limitada por concentracao de gaps em:

- homologacao de identidade e MFA fora do contexto local
- integracoes reais AML/KYT e RPC com fallback em ambiente serio
- fechamento de partes do dominio de compliance ainda em modo `degraded`/manual
- consolidacao do aceite operacional (owners, SLA, runbooks) e evidencias recorrentes

## Decisao

Adotar uma estrategia de continuidade baseada em:

1. `Hardening First` para atravessar o corte de `90%+` com credibilidade operacional.
2. `Modularizacao Guiada` apenas nos hotspots tocados por hardening, para reduzir custo de manutencao sem abrir uma frente de replatform.

Esta decisao orienta a ordem de execucao e prioriza confianca e segurança sobre expansao de features.

## Consequencias

### Positivas

- reduz o risco estrutural de `staging` serio (identidade, providers e governanca)
- evita que o produto aparente maturidade regulatoria maior do que possui
- diminui flakiness e aumenta repetibilidade operacional
- cria base real para evolucao de compliance sem depender de stubs/degradacao

### Negativas

- reduz a velocidade de entrega de features novas no curto prazo
- exige coordenacao com stakeholders externos (IdP, Security, Compliance, provider AML/KYT)
- pode expor gaps de contrato e UX ao endurecer auth e RBAC

## Trade-offs

- foi priorizada homologacao e governanca formal antes de “completar” o dominio de compliance por inteiro
- modularizacao ocorre apenas onde ha continuidade imediata (evita refatoracao cosmética)
- a pipeline atual e tomada como fonte de verdade para nao regressao; expansoes exigem evidencia automatizada correspondente

## Critérios de Aceitação

- `OIDC` funcionando fora de `local|test` com segredos nao-dev e claims coerentes
- `MFA serio` homologado (federado pelo IdP ou equivalente operacional) para fluxos sensiveis
- provider AML/KYT em modo `live` com readiness, timeout, retry e degradacao honesta
- RPC primario + fallback homologados com evidencias de degradacao e preservacao de metadados no resultado
- pelo menos uma janela seria executada ponta a ponta com dossier anexavel e go/no-go coerente

