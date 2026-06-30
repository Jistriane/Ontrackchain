# ADR-004 — Legal Report com Strong Auth e 2FA

## Contexto

`legal_report` e mais sensivel que relatorios tecnicos comuns. Expor este artefato para API Key ou sem fator adicional aumentaria risco de acesso indevido.

## Decisao

Exigir, para download de `legal_report`:

- `X-Auth-Method=jwt`
- `X-Role=ADMIN`
- `X-2FA=ok`

O enforcement ocorre no `report-api`, e nao apenas no frontend.

## Motivacao

- evitar bypass por chamada direta ao backend
- aplicar seguranca mais forte em recurso sensivel
- preparar base para politicas futuras de acesso juridico/regulatorio

## Alternativas Consideradas

### Opcao A — Validacao apenas no frontend

- Vantagem:
  - implementacao rapida
- Desvantagem:
  - bypass trivial

### Opcao B — Validacao apenas por JWT

- Vantagem:
  - fluxo simples
- Desvantagem:
  - nao diferencia criticidade do recurso

### Opcao C — JWT + role + 2FA no backend

- Vantagem:
  - defesa em profundidade
- Desvantagem:
  - mais estados de sessao

## Consequencias

- frontend precisa propagar estado de `2FA`
- smoke e Playwright precisam validar caminho negativo e positivo
- tentativas negadas devem ser consideradas em evolucao de auditoria futura

## Trade-offs Aceitos

- UX um pouco mais rigorosa em troca de seguranca adequada ao recurso

## Status

- Aceito e implementado
