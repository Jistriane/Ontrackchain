# Validacao em Staging - Diretorio Federado

## Objetivo

Padronizar a validacao operacional da trilha de busca assistida e vinculo federado em `staging`, cobrindo:

- configuracao minima do `auth-service`
- execucao manual no cockpit `Team`
- confirmacao da trilha auditavel no backend e no cockpit `Audit`

Este guia existe para reduzir risco de drift entre:

- `Keycloak Admin API`
- `auth-service`
- tela `Team`
- preset `identity-federated` do cockpit `Audit`

## Quando Usar

- depois que o blueprint do Render ja estiver sincronizado
- depois que os segredos do `auth-service` ja tiverem sido preenchidos
- antes de promover a trilha federada como operacao homologada do tenant

## Pre-Requisitos

Confirme antes de abrir o browser:

- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- `NEXT_PUBLIC_AUTH_MODE=oidc`
- `OIDC_ISSUER_URL` aponta para o `Keycloak` hospedado
- `KEYCLOAK_ADMIN_BASE_URL` aponta para o host publico do `Keycloak`
- `KEYCLOAK_ADMIN_REALM=ontrackchain`
- `KEYCLOAK_ADMIN_CLIENT_ID` e `KEYCLOAK_ADMIN_CLIENT_SECRET` estao preenchidos
- `KEYCLOAK_ADMIN_ORG_ATTRIBUTE=organization_id`
- `KEYCLOAK_ADMIN_ROLE_ATTRIBUTE=otk_role`
- existe ao menos um operador `ADMIN` autenticavel no tenant de teste
- existe ao menos um usuario local em `users` na organizacao alvo
- existe ao menos um principal no `Keycloak` com `email`, `organization_id` e `otk_role` coerentes com o usuario local

## Cenario de Teste Recomendado

Use um caso simples e reversivel:

- tenant: `org-staging-e2e`
- usuario local em `users`: `analyst@tenant.example`
- role local: `ANALYST`
- principal externo no `Keycloak`:
  - `email=analyst@tenant.example`
  - `attributes.organization_id=<org_id do tenant>`
  - `attributes.otk_role=otk_analyst`
  - `enabled=true`
- o principal externo escolhido nao deve estar previamente vinculado a outro usuario local

## Fase 1 - Verificacao de Backend

### Checklist

- [ ] `ontrackchain-auth-service-staging` esta `healthy`
- [ ] o operador confirmou que os segredos novos do diretório federado estao preenchidos
- [ ] o client tecnico do `Keycloak` possui escopo minimo de leitura do diretório

### Evidencia minima

- screenshot ou anotacao da configuracao do service no Render
- nome do client tecnico exercitado

### Stop/Go

- `stop` se `KEYCLOAK_ADMIN_CLIENT_SECRET` estiver ausente
- `stop` se o client tecnico nao tiver permissao de leitura
- `go` apenas quando o owner de `Backend/Auth` confirmar o runtime configurado

## Fase 2 - Fluxo Manual no Team

### Passos

1. autenticar como operador `ADMIN` no tenant alvo
2. abrir `Team`
3. selecionar o membro local que deve receber o vinculo
4. na secao `Diretorio federado (assistido)`, buscar por email ou username do principal externo
5. confirmar que a tabela retornou o candidato esperado
6. revisar:
   - `external_subject`
   - `organization_id`
   - `role_snapshot`
   - `match_status`
   - `warnings`
7. acionar `Validar e vincular`
8. confirmar mensagem de sucesso
9. confirmar que a roster table passou a exibir identidade `vinculada`
10. confirmar que a secao de identidades persistidas mostra o `provider/external_subject` esperado

### Fase 2 - Criterios de aceite

- a busca retorna pelo menos um candidato coerente
- o candidato certo aparece com `match_status` compativel com `suggested` ou `linked`
- a validacao de sugestao nao retorna erro
- o vinculo final atualiza `linked_identity_count` do membro
- o deep-link para `Audit` continua disponivel na tela `Team`

### Fase 2 - Stop/Go

- `stop` se a busca falhar com `federated_directory_unavailable`
- `stop` se a busca falhar com `federated_directory_forbidden`
- `stop` se o candidato retornar `candidate_org_mismatch`
- `stop` se o candidato retornar `candidate_already_linked`
- `go` apenas quando o vinculo final for persistido com sucesso

## Fase 3 - Confirmacao no Audit

### Fase 3 - Passos

1. a partir da tela `Team`, abrir o deep-link do preset `identity-federated`
2. confirmar que o cockpit `Audit` abre com o `member_id` correto no filtro
3. validar que existe ao menos um evento `team_external_identity_linked`
4. confirmar no detalhe do evento:
   - `provider`
   - `external_subject`
   - `actor_user_id`
   - `linked_user_id`
   - `auth_method`
   - `tenant_role`

### Fase 3 - Criterios de aceite

- o preset `identity-federated` abre sem erro
- o `member_id` filtrado corresponde ao membro testado
- o evento de `link` esta presente e coerente com a acao executada no `Team`

### Observacao

Nesta fase, o cockpit `Audit` cobre operacionalmente `link/unlink`. Os eventos de busca e sugestao do diretório federado sao persistidos no backend, mas ainda sao validados abaixo por consulta tecnica.

## Fase 4 - Confirmacao Tecnica no Backend

### SQL recomendado

```sql
SELECT
  action,
  resource_type,
  resource_id,
  metadata,
  created_at
FROM audit_logs
WHERE action IN (
  'team_federated_directory_searched',
  'team_federated_directory_suggestion_validated',
  'team_external_identity_linked'
)
ORDER BY created_at DESC
LIMIT 20;
```

### O que confirmar em `metadata`

- `request_id`
- `provider`
- `external_subject`
- `candidate_email`
- `candidate_org`
- `role_snapshot`
- `match_reason`
- `warnings`

### Fase 4 - Criterios de aceite

- existe ao menos um `team_federated_directory_searched`
- existe ao menos um `team_federated_directory_suggestion_validated`
- existe ao menos um `team_external_identity_linked`
- os tres eventos sao coerentes com o mesmo fluxo manual

## Fase 5 - Teste de Reversao Controlada

### Fase 5 - Passos

1. voltar para `Team`
2. abrir a identidade persistida do membro
3. executar `Desvincular`
4. confirmar a mensagem de sucesso
5. validar no `Audit` a presenca de `team_external_identity_unlinked`

### Fase 5 - Criterios de aceite

- o `unlink` exige confirmacao explicita
- o membro volta a estado sem identidade vinculada
- o evento `team_external_identity_unlinked` aparece no cockpit `Audit`

## Resultado Esperado

A validacao em `staging` deve terminar com:

- `Team` conseguindo buscar no `Keycloak`
- sugestao de vinculo aprovada por `email + org + role`
- vinculo persistido em `external_identities`
- trilha de `link/unlink` visivel no cockpit `Audit`
- trilha de `search/suggestion/link` presente em `audit_logs`

## Falhas Mais Provaveis

### `federated_directory_unavailable`

- `KEYCLOAK_ADMIN_BASE_URL` incorreto
- timeout do `Keycloak`
- endpoint administrativo indisponivel

### `federated_directory_forbidden`

- client tecnico sem permissao minima
- client/secret incorretos

### `candidate_org_mismatch`

- `attributes.organization_id` no `Keycloak` diverge do tenant atual

### `candidate_role_missing` ou `candidate_role_unknown`

- atributo `otk_role` ausente
- valor de role nao canonizado para o app

### `team_external_identity_already_linked`

- o principal externo ja foi vinculado a outro usuario local

## Evidencia Minima para Sign-Off

- screenshot da busca assistida no `Team`
- screenshot do vinculo persistido no `Team`
- screenshot do preset `identity-federated` no `Audit`
- output ou screenshot da consulta `audit_logs`
- anotacao do `request_id` ou timestamp aproximado da execucao

## Referencias

- [Run Sheet Operacional - Diretorio Federado em Staging](governance-weekly/guides/FEDERATED_DIRECTORY_STAGING_RUN_SHEET.md)
- [Deploy e Staging](deploy-and-staging.md)
- [Blueprint Render para Staging Full-Stack](render-staging-blueprint.md)
- [Ownership do ambiente de staging](staging-env-ownership.md)
- [Validacao e Auditoria](validation-and-audit.md)
- [ADR-006 - identidade federada e users locais](adrs/ADR-006-identidade-federada-e-users-locais.md)
