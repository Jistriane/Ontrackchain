# ADR-001 — Isolamento Multi-tenant com RLS

## Contexto

O projeto lida com dados sensiveis de investigacao, compliance, billing e auditoria. Um erro de filtro por organizacao na aplicacao teria impacto critico.

## Decisao

Adotar `PostgreSQL Row Level Security` como barreira obrigatoria de isolamento multi-tenant nas tabelas sensiveis, com contexto de organizacao injetado na sessao.

## Motivacao

- reduzir risco de vazamento cross-tenant
- impedir dependencia exclusiva de filtros na aplicacao
- tornar o banco a ultima linha de defesa

## Alternativas Consideradas

### Opcao A — Isolamento apenas na aplicacao

- Vantagem:
  - menor complexidade inicial
- Desvantagem:
  - risco alto em regressao de query

### Opcao B — Banco separado por tenant

- Vantagem:
  - isolamento forte
- Desvantagem:
  - custo operacional alto para o MVP
  - complexidade desnecessaria cedo demais

### Opcao C — Schema compartilhado com `RLS`

- Vantagem:
  - equilibrio entre seguranca e custo
- Desvantagem:
  - exige disciplina maior em bootstrap e debugging

## Consequencias

- `RLS` precisa estar refletido tanto em `init.sql` quanto em migrations
- acessos administrativos e funcoes especiais precisam ser desenhados com cuidado
- testes de regressao devem cobrir comportamento com contexto de organizacao

## Trade-offs Aceitos

- maior rigor operacional em troca de seguranca estrutural

## Status

- Aceito e implementado
