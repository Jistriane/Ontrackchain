# ADR-006 — Identidade Federada e Users Locais

## Contexto

O fluxo `OIDC` ja propaga `sub`, `org`, `plan` e `role` do provedor de identidade para o gateway e para os servicos de dominio. Esse modelo passou a ser validado no runtime local com `Keycloak`.

Durante o endurecimento do `P0-03`, surgiram dois fatos arquiteturalmente relevantes:

- o `sub` do IdP nao pertence necessariamente a tabela local `users`
- varias tabelas historicas assumem `user_id UUID REFERENCES users(id)` como representacao universal de autoria

Esse acoplamento gerou falhas reais de persistencia:

- `audit_logs.user_id`
- `cases.user_id`
- `investigation_quotes.user_id`
- `monitoring_quotes.user_id`
- `compliance_quotes.user_id`

O workaround atual ja validado em runtime evita quebra de `FK`:

- persiste `user_id = null` quando o principal federado nao existe em `users`
- preserva `external_user_id` em `metadata` quando a rastreabilidade precisa ser mantida

Esse workaround resolve o incidente imediato, mas nao define o modelo alvo de identidade.

## Decisao

Adotar um modelo de identidade em duas camadas:

- `users` permanece como identidade local de aplicacao
- uma nova relacao federada passa a vincular principals externos do `OIDC` a usuarios locais quando esse vinculo existir

Recomendacao concreta:

- criar uma tabela dedicada, por exemplo `external_identities`
- vincular `provider`, `external_subject`, `organization_id` e `user_id`
- tratar o principal `OIDC` como identidade canonica de autenticacao
- tratar `users` como cadastro local complementar de aplicacao, nao como fonte universal obrigatoria de autenticacao

No curto prazo, o fallback validado continua aceito:

- se nao houver vinculo federado nem usuario local correspondente, o runtime pode persistir `user_id = null`
- a autoria externa deve ser preservada em campo dedicado ou `metadata.external_user_id`

## Motivacao

- desacoplar autenticacao federada de cadastro local legado
- eliminar novos `FK` quebrando em fluxos `OIDC`
- preservar rastreabilidade regulatoria sem depender de espelho automatico em `users`
- abrir caminho para onboarding, offboarding e vinculo multi-tenant mais claros
- evitar que o primeiro login `OIDC` crie usuarios locais sem governanca de ciclo de vida

## Alternativas Consideradas

### Opcao A — Manter apenas o workaround atual com `user_id = null`

- Vantagem:
  - menor custo imediato
  - nenhuma migracao estrutural agora
- Desvantagem:
  - autoria federada fica dispersa em `metadata`
  - dificulta queries consistentes por identidade externa
  - nao cria modelo claro para onboarding/offboarding

### Opcao B — Provisionar usuario local automaticamente no primeiro login `OIDC`

- Vantagem:
  - reduz `nulls` em `user_id`
  - reaproveita o schema atual com menos ajuste nos servicos
- Desvantagem:
  - acopla autenticacao a criacao de cadastro local
  - aumenta risco de usuarios locais zombie ou mal provisionados
  - exige regras de reconciliacao quando claims mudarem no IdP
  - torna mais opaca a governanca de identidade

### Opcao C — Introduzir tabela de identidades federadas vinculada a `users`

- Vantagem:
  - separa autenticacao externa de cadastro local
  - suporta principals federados com ou sem espelho local
  - melhora auditabilidade e trilha de autoria
  - reduz ambiguidade para multi-tenant e compliance
- Desvantagem:
  - exige migracao de schema e ajustes graduais nos servicos
  - introduz mais uma entidade no modelo

## Recomendacao

Escolher a `Opcao C`.

Ela oferece o melhor equilibrio entre:

- seguranca
- rastreabilidade
- governanca operacional
- evolucao progressiva do schema

Ela tambem preserva reversibilidade:

- o sistema pode continuar aceitando `user_id = null` durante a transicao
- novos pontos de persistencia podem migrar gradualmente para usar identidade federada vinculada

## Estrategia de Implementacao

### Fase 1 — Compatibilidade

- manter o fallback atual para `audit_logs`, `cases` e `quotes`
- padronizar `external_user_id` onde ainda for necessario
- evitar novas tabelas assumindo `users(id)` como identidade universal

### Fase 2 — Modelo Federado

- criar `external_identities`
- campos minimos sugeridos:
  - `id`
  - `organization_id`
  - `provider`
  - `external_subject`
  - `user_id` nullable
  - `email_snapshot`
  - `role_snapshot`
  - `created_at`
  - `last_seen_at`
- impor unicidade em `provider + external_subject + organization_id`

### Fase 3 — Consumo de Dominio

- adaptar `auth-service` ou camada de provisionamento para resolver o vinculo federado
- enriquecer contexto propagado pelo gateway com `linked_user_id` quando existir
- migrar consultas e trilhas mais sensiveis para usar identidade federada de forma explicita

## Consequencias

- `users` deixa de ser interpretada como fonte canonica obrigatoria para toda autenticacao
- o time precisa definir politicas de vinculo:
  - quem pode vincular identidade externa a usuario local
  - quando o vinculo e criado
  - como ocorre desligamento e revogacao
- futuros recursos de auditoria e billing podem consultar identidade federada sem depender de `metadata` solta

## Trade-offs Aceitos

- maior complexidade de modelo em troca de coerencia entre `OIDC`, multi-tenant e persistencia relacional
- periodo transitorio com coexistencia de `user_id` local e identidade externa

## Status

- Aceito para implementacao faseada
