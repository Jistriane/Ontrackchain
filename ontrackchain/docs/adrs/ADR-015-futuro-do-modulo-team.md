# ADR-015 — Futuro do Modulo Team

## Contexto

O modulo `team` ja implementa:

- Gestao de membros da organizacao (CRUD completo)
- Vinculo/desvinculo de identidades federadas (Keycloak)
- Busca e validacao assistida no diretorio federado
- RBAC por papel (ADMIN, ANALYST, AUDITOR, VIEWER, TESTER, COMPLIANCE_OFFICER, LEGAL_REVIEWER, REVIEWER, BILLING_ADMIN)
- Integracao com `auth-service` para resolucao de vinculos federados

O ADR-006 ja definiu o modelo de identidade em duas camadas (users + external_identities). O modulo team e o frontend desse modelo.

## Decisao

Manter o modulo team como cockpit unico de gestao de identidade e acesso, com as seguintes diretrizes:

### 1. Escopo Atual (Manter)

- CRUD de membros da organizacao
- Gestao de identidades federadas (link/unlink)
- Busca no diretorio federado (Keycloak)
- Visualizacao de audit trail por membro
- RBAC granular por operacao (create/update/disable/link/unlink/search)

### 2. Evolucao Planejada (Futuro)

- **Notificacoes**: alertar quando identidade federada e desvinculada ou quando papel e alterado
- **Historico de cambios**: timeline de alteracoes de papel e status por membro
- **Importacao em lote**: importar membros de planilha ou CSV
- **Integracao com SCIM**: provisionamento automatico via protocolo SCIM 2.0
- **Politicas de acesso**: regras automaticas baseadas em papel (ex: ANALYST nao pode acessar billing)
- **Dashboard de conformidade**: visao agregada de vinculos federados, papéis e status

### 3. Nao Implementar (Fora do Escopo)

- Provisionamento automatico de usuarios no primeiro login OIDC (ja decidido no ADR-006)
- Sincronizacao bidirecional com IdP (manter unidirecional por seguranca)
- Gestao de grupos/permissoes no Keycloak (manter no IdP, nao espelhar)

## Motivacao

- consolidar o modulo team como fonte unica de verdade para gestao de identidade
- evitar duplicacao de funcionalidades entre team e outros modulos
- manter separacao entre autenticacao (IdP) e autorizacao (backend)
- preservar reversibilidade e evolucao gradual

## Alternativas Consideradas

### Opcao A — Manter modulo team como esta

- Vantagem: menor esforco imediato
- Desvantagem: sem evolucao, funcionalidades limitadas

### Opcao B — Expandir modulo team com todas as funcionalidades planejadas

- Vantagem: modulo completo e robusto
- Desvantagem: alto esforco, pode atrasar outras frentes

### Opcao C — Evolucao incremental conforme necessidade

- Vantagem: foco no que e necessario agora, flexibilidade
- Desvantagem: pode gerar inconsistencias se nao houver planejamento

## Recomendacao

Escolher a **Opcao C** — evolucao incremental conforme necessidade.

## Consequencias

- modulo team continua sendo o cockpit unico de gestao de identidade
- novas funcionalidades sao implementadas sob demanda
- documentacao e testes sao atualizados junto com cada evolucao
- RBAC continua sendo enforcement fino por operacao

## Trade-offs Aceitos

- evolucao incremental pode gerar pequenas inconsistencias temporarias
- algumas funcionalidades podem ficar pendentes ate serem necessarias
- manter modulo unico facilita manutencao mas pode criar gargalo se muitas funcionalidades forem adicionadas

## Status

- Aceito para implementacao incremental
