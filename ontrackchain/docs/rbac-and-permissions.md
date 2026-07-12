# RBAC e Matriz de Permissoes

## Objetivo

Documentar o modelo atual de papeis e restricoes do scaffold, destacando:

- o que hoje e explicitamente restringido
- o que ainda depende de evolucao na Fase 2
- quais fluxos sensiveis exigem papel privilegiado

## Contexto Atual

O contexto de autorizacao e propagado pelo `auth-service` atraves do gateway, usando principalmente:

- `X-Role`
- `X-Auth-Method`
- `X-Org-Id`
- `X-User-Id`
- `X-Plan`
- `X-Linked-User-Id`

Esse contexto pode nascer de:

- `JWT` validado pelo `auth-service`
- `API Key` validada pelo `auth-service`, caso em que o papel efetivo passa a refletir o `permission_scope` da chave

Semantica atual dos identificadores:

- `X-User-Id` representa o principal autenticado no provedor ou na credencial apresentada
- `X-Linked-User-Id` representa o usuario local vinculado, quando houver relacao federada resolvida

No estado atual, o scaffold nao implementa uma matriz RBAC completa para todos os recursos. Ele possui um modelo misto:

- `RLS` + contexto organizacional para a maior parte dos fluxos core
- papeis privilegiados para leituras e mutacoes administrativas
- autenticacao forte adicional em recursos mais sensiveis, como `legal_report`

Leitura arquitetural atual:

- o corte mais maduro do RBAC esta nos dominios administrativos de `investigation`, `monitoring` e `audit`
- o fluxo de reports endurece um recurso sensivel especifico (`legal_report`)
- os fluxos core de negocio ainda nao diferenciam de forma fina `ANALYST`, `TESTER` e `VIEWER`

## Papeis Observados

### `ADMIN`

- papel privilegiado do scaffold atual
- pode acessar auditoria (`/api/v1/audit/logs`)
- pode operar triagem administrativa global em `/monitoring`, incluindo acknowledge e export
- pode operar mutacoes administrativas da DLQ de investigation, incluindo `requeue` e resolucao manual
- pode baixar `legal_report` desde que tambem cumpra os demais requisitos

### `AUDITOR`

- papel de leitura privilegiada introduzido no `WP-03`
- pode consultar auditoria (`/api/v1/audit/logs`)
- pode acessar leituras administrativas de monitoring e investigation
- nao pode executar mutacoes administrativas, export sensivel ou download juridico privilegiado

### `ANALYST`

- aparece como papel canonico no `auth-service` e nos proxies do frontend
- no estado atual, nao possui enforcement dedicado para leitura administrativa nem para mutacoes privilegiadas
- continua apto aos fluxos core da propria organizacao que dependem de autenticacao valida + `RLS` + plano

### `TESTER`

- aparece como papel canonico no `auth-service` e no realm local do `Keycloak`
- hoje nao possui privilegios administrativos dedicados no backend
- serve mais como papel de identidade/seed do ambiente do que como role de autorizacao fina aplicada por dominio

### `VIEWER`

- aparece como papel canonico no `auth-service`
- hoje nao possui matriz especifica de leitura-only por dominio no backend
- na pratica, herda o mesmo limite dos papeis nao privilegiados: sem acesso administrativo, mas ainda sem segmentacao fina nos fluxos core

### `COMPLIANCE_OFFICER`

- papel especializado ja consumido pelo fluxo `ROS/COAF`
- agora passa a ser canonizavel no `auth-service`, reduzindo drift entre `frontend`, `report-api` e claims do IdP
- continua reservado a aprovacoes/submissoes reguladas e nao substitui automaticamente `ANALYST` no restante dos dominios

### `LEGAL_REVIEWER`

- papel observado no frontend e no catalogo de equipe
- agora passa a ser canonizavel no `auth-service`
- ainda nao possui enforcement backend dedicado nesta rodada

### `UNKNOWN`

- valor usado em alguns metadados quando o papel nao esta presente
- nao deve ser tratado como papel de acesso

## Estado Real do Enforcement

### Onde ja existe enforcement fino

- `investigation` administrativo:
  - leitura privilegiada com `ADMIN|AUDITOR`
  - mutacao administrativa com `ADMIN`
- `monitoring` administrativo:
  - leitura privilegiada com `ADMIN|AUDITOR`
  - acknowledge/export com `ADMIN`
- `audit/logs`:
  - leitura privilegiada com `ADMIN|AUDITOR`
- `report download` para `legal_report`:
  - `ADMIN` + `JWT` + `2FA`

### Onde o controle ainda e predominantemente contextual

- `investigation` core (`estimate`, `start`, `status`, `result`, `history`)
- `monitoring` core (`watchlists`, `alerts`, `start`, `estimate`)
- `compliance/*`
- `billing/balance`

Nesses casos, o controle real hoje depende mais de:

- autenticacao valida
- `X-Org-Id`
- `RLS`
- `X-Plan`

Do que de um papel de dominio fino.

## Regras Efetivamente Implementadas

### 1. Audit Logs

Endpoint:

- `/api/v1/audit/logs`

Restricao:

- exige `X-Role` privilegiado (`ADMIN` ou `AUDITOR`) vindo do gateway
- quando a chamada entra por `API Key`, o valor efetivo de `X-Role` passa a refletir o `permission_scope` resolvido no `auth-service`

Objetivo:

- permitir leitura auditavel para perfis de revisao sem abrir permissao de mutacao administrativa
- quando o papel nao atende a regra, o backend registra `authorization_denied` com `request_id`, `effective_role`, `allowed_roles` e endpoint
- quando o principal autenticado vem do `OIDC` sem correspondencia na tabela local `users`, a trilha persiste `external_user_id` no `metadata` e grava `user_id = null` para nao quebrar o `FK`
- o mesmo principio de compatibilidade agora vale para criacao de `cases` e `quotes`: o runtime nao falha por `FK` quando o principal vem do IdP sem espelho local
- quando `X-Linked-User-Id` esta presente, os fluxos core de `investigation`, `monitoring` e `compliance` passam a preferir esse identificador para persistencia relacional, preservando o principal externo em `metadata.external_user_id`
- a decisao arquitetural alvo para evoluir esse ponto foi registrada em [ADR-006](adrs/ADR-006-identidade-federada-e-users-locais.md)

### 2. Legal Report

Endpoint:

- `/api/v1/reports/{report_id}/download`

Restricoes para `legal_report`:

- `X-Auth-Method=jwt`
- `X-Role=ADMIN`
- `X-2FA=ok`

Objetivo:

- restringir o recurso mais sensivel a autenticacao forte

### 3. Operacao Administrativa de Monitoring

Endpoints:

- `/api/v1/monitoring/admin/operational-alerts`
- `/api/v1/monitoring/admin/operational-alerts/filter-options`
- `/api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge`
- `/api/v1/monitoring/admin/operational-alerts/acknowledge-batch`
- `/api/v1/monitoring/admin/operational-alerts/export`

Restricao:

- leitura privilegiada:
  - `/api/v1/monitoring/admin/operational-alerts`
  - `/api/v1/monitoring/admin/operational-alerts/filter-options`
  - exige `X-Role in {ADMIN, AUDITOR}`
- mutacao administrativa:
  - `/api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge`
  - `/api/v1/monitoring/admin/operational-alerts/acknowledge-batch`
  - `/api/v1/monitoring/admin/operational-alerts/export`
  - exige `X-Role=ADMIN`

Objetivo:

- separar leitura privilegiada de triagem/exportacao administrativa sensivel
- negar mutacoes ou leituras privilegiadas fora do papel esperado com trilha persistida em `audit_logs`

### 4. Operacao Administrativa de Investigation

Endpoints:

- `/api/v1/investigation/admin/operations`
- `/api/v1/investigation/admin/alerts`
- `/api/v1/investigation/admin/metrics`
- `/api/v1/investigation/admin/dlq`
- `/api/v1/investigation/admin/dlq/{case_id}/requeue`
- `/api/v1/investigation/admin/dlq/{case_id}/acknowledge`

Restricao:

- leitura privilegiada:
  - `operations`, `alerts`, `metrics`, `dlq`
  - exige `X-Role in {ADMIN, AUDITOR}`
- mutacao administrativa:
  - `requeue`, `acknowledge`
  - exige `X-Role=ADMIN`

Objetivo:

- permitir observabilidade e revisao operacional para auditoria sem delegar capacidade de alterar fila, billing ou estado da DLQ
- registrar tentativas negadas de leitura privilegiada ou mutacao administrativa via `authorization_denied`

### 5. Demais Fluxos de Negocio

Hoje dependem mais de:

- autenticacao valida
- contexto de organizacao
- plano contratado
- RLS no banco

Do que de uma matriz RBAC fina por papel.

## Matriz Atual

| Recurso/Acao | Auth Necessaria | Papel | Status | Condicoes Extras |
| --- | --- | --- | --- | --- |
| Catalogos protegidos | JWT ou API Key | qualquer autenticado | `enforced_by_context` | plano e filtros aplicam |
| `investigation/estimate` | JWT ou API Key | qualquer autenticado | `enforced_by_context` | contexto valido |
| `investigation/start` | JWT ou API Key | qualquer autenticado | `enforced_by_context` | `quote` valida + plan lock |
| `billing/balance` | JWT ou API Key | `ADMIN`, `BILLING_ADMIN` e alias legado `OTK_BILLING_ADMIN` | `partial_rbac_enforced` | leitura de saldo financeiro + negacao auditada |
| `billing/reconciliation` | JWT ou API Key | `ADMIN`, `BILLING_ADMIN` e alias legado `OTK_BILLING_ADMIN` | `partial_rbac_enforced` | snapshot reconciliavel de `quotes` + `credit_ledger` com negacao auditada |
| `monitoring` core (`watchlists`, `alerts`, `start`, `estimate`) | JWT ou API Key | qualquer autenticado | `enforced_by_context` | contexto valido |
| `compliance/*` | JWT ou API Key | contexto misto; mutacoes criticas com `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | escrita prioritaria endurecida em `start`, `blocks/evaluate`, `blocks/*/lift`, `counterparties` e `counterparties/*/review` |
| `monitoring/admin/operational-alerts` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `monitoring/admin/operational-alerts/filter-options` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `monitoring/admin/operational-alerts/export` | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | export sensivel + auditoria |
| `monitoring/admin/operational-alerts/ack*` | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | mutacao administrativa |
| `investigation/admin` (`operations`, `alerts`, `metrics`, `dlq`) | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `investigation/admin/dlq/*` mutacoes | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | requeue e resolucao manual |
| `audit/logs` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | acesso restrito de leitura |
| `report generate` | JWT ou API Key | `ADMIN` ou `ANALYST` | `partial_rbac_enforced` | negacao auditada na geracao basica |
| `reports` leitura/listagem e `ROS/COAF` leitura | JWT ou API Key | `ADMIN`, `AUDITOR`, `ANALYST`, `VIEWER` | `partial_rbac_enforced` | negacao auditada em listagem, detalhe, dossie e downloads nao-juridicos |
| `reports/ros-coaf` aprovacao formal (`/approve`) | JWT ou API Key | `ADMIN`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER`, `REVIEWER` e aliases legados `OTK_*` correspondentes | `partial_rbac_enforced` | gate formal de revisao com MFA externo homologado + negacao auditada |
| `reports/ros-coaf` submissao manual (`/submitted`) | JWT ou API Key | `ADMIN`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | segregacao entre revisao formal e submissao efetiva ao COAF |
| `report download` comum | JWT ou API Key | `ADMIN`, `AUDITOR`, `ANALYST`, `VIEWER` | `partial_rbac_enforced` | query params corretos + negacao auditada |
| `legal_report download` | JWT | `ADMIN` | `rbac_enforced` | `X-2FA=ok` |
| `evidence/manual-package` leitura (`seal` e `by-digest`) | JWT ou API Key | `ADMIN`, `AUDITOR`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER`, `REVIEWER` | `partial_rbac_enforced` | leitura institucional + negacao auditada |
| `evidence/manual-package` `signoffs` | JWT ou API Key | `ADMIN`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER`, `REVIEWER` | `partial_rbac_enforced` | vinculo obrigatorio entre `X-Role` e `signer_role` |
| `evidence/manual-package` `signoff-requests/finalize/revoke/supersede` | JWT ou API Key | `ADMIN` | `rbac_enforced` | `AUDITOR` permanece somente leitura |

## Matriz por Papel e Dominio

| Dominio / Acao | ADMIN | AUDITOR | ANALYST | TESTER | VIEWER | Leitura Atual |
| --- | --- | --- | --- | --- | --- | --- |
| `investigation` core da propria org | Sim | Sim | Sim | Sim | Sim | controle principal via `RLS` + plano |
| `investigation` leitura administrativa (`operations`, `alerts`, `metrics`, `dlq`) | Sim | Sim | Nao | Nao | Nao | `rbac_enforced` |
| `investigation` mutacao administrativa (`requeue`, `acknowledge`) | Sim | Nao | Nao | Nao | Nao | `rbac_enforced` |
| `monitoring` core da propria org | Sim | Sim | Sim | Sim | Sim | controle principal via `RLS` + plano |
| `monitoring` leitura administrativa (`operational-alerts`, filtros) | Sim | Sim | Nao | Nao | Nao | `rbac_enforced` |
| `monitoring` mutacao/export administrativo | Sim | Nao | Nao | Nao | Nao | `rbac_enforced` |
| `audit/logs` leitura privilegiada | Sim | Sim | Nao | Nao | Nao | `rbac_enforced` |
| `report generate` | Sim | Nao | Sim | Nao | Nao | `partial_rbac_enforced` + negacao auditada |
| `reports` leitura/listagem e `ROS/COAF` leitura | Sim | Sim | Sim | Nao | Sim | `partial_rbac_enforced` + negacao auditada |
| `billing/balance` | Sim | Nao | Nao | Nao | Nao | `BILLING_ADMIN` e alias legado podem ler saldo financeiro; roles fora do dominio recebem negacao auditada |
| `billing/reconciliation` | Sim | Nao | Nao | Nao | Nao | `BILLING_ADMIN` e alias legado podem ler o snapshot reconciliavel de saldo, quotes e `credit_ledger`; roles fora do dominio recebem negacao auditada |
| `reports/ros-coaf` aprovacao formal (`/approve`) | Sim | Nao | Nao | Nao | Nao | `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER` aprovam/rejeitam com MFA externo homologado; aliases `OTK_*` equivalentes continuam aceitos |
| `reports/ros-coaf` submissao manual (`/submitted`) | Sim | Nao | Nao | Nao | Nao | permanece restrita a `COMPLIANCE_OFFICER` e alias legado para preservar segregacao regulatoria |
| `report` download comum | Sim | Sim | Sim | Nao | Sim | `partial_rbac_enforced` + negacao auditada |
| `report` download de `legal_report` | Sim | Nao | Nao | Nao | Nao | `rbac_enforced` + `JWT` + `2FA` |
| `compliance` leitura core | Sim | Sim | Sim | Sim | Sim | leitura principal ainda guiada por contexto + `RLS` |
| `compliance` mutacao core prioritaria (`start`, `blocks/evaluate`, `blocks/*/lift`, `counterparties`, `counterparties/*/review`) | Sim | Nao | Sim | Nao | Nao | `partial_rbac_enforced` + negacao auditada; `COMPLIANCE_OFFICER` e alias legado tambem autorizados |
| `evidence/manual-package` leitura institucional | Sim | Sim | Nao | Nao | Nao | `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER` tambem leem para signoff dirigido |
| `evidence/manual-package` `signoffs` | Sim | Nao | Nao | Nao | Nao | `COMPLIANCE_OFFICER -> compliance_owner`, `LEGAL_REVIEWER -> legal_owner_optional`, `REVIEWER -> legal_owner_optional` |
| `evidence/manual-package` `finalize/revoke/supersede/signoff-request` | Sim | Nao | Nao | Nao | Nao | `rbac_enforced`; `AUDITOR` saiu da mutacao |

Observacao importante:

- `Sim` nos fluxos core nao significa privilégio fino por papel; significa apenas que o backend atual nao diferencia esses papeis quando o acesso ja esta autenticado dentro da organizacao correta
- por isso, `ANALYST`, `TESTER` e `VIEWER` ainda nao podem ser tratados como papeis plenamente definidos do ponto de vista regulatorio
- em rotas atras do gateway, o cliente nao deve ser tratado como fonte de verdade para `X-Role`; o valor efetivo e derivado pelo `auth-service` a partir do `JWT` ou do `permission_scope` da `API Key`
- quando houver vinculo federado resolvido, o gateway tambem pode propagar `X-Linked-User-Id` sem alterar o significado de `X-User-Id`

## Evidencias Ja Confirmadas

- `auth-service` canoniza hoje: `ADMIN`, `ANALYST`, `TESTER`, `AUDITOR`, `VIEWER`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER`, `REVIEWER` e `BILLING_ADMIN`
- `investigation-api` e `monitoring-api` persistem `authorization_denied` nas rotas administrativas endurecidas
- `compliance-api` agora persiste `authorization_denied` na primeira fatia de mutacoes sensiveis do dominio
- `report-api` agora persiste `authorization_denied` na leitura sensivel de `reports` e `ROS/COAF`, inclusive dossie regulatorio e download nao-juridico
- `investigation-api` agora aplica `BILLING_ADMIN` tambem em `billing/reconciliation`, protegendo o snapshot reconciliavel de saldo, quotes e `credit_ledger`
- no fluxo `OIDC`, a trilha de negacao agora preserva o `sub` externo em `metadata.external_user_id` quando nao ha usuario local correspondente
- no fluxo `OIDC`, novos `cases` core preservam `metadata.external_user_id`; `quotes` passam a gravar `user_id = null` quando o principal nao existe em `users`
- a suite Playwright ja cobre negacao de `AUDITOR` tentando:
  - acknowledge administrativo em `monitoring`
  - `requeue` administrativo em `investigation`
- a suite Playwright tambem cobre `OIDC` com:
  - negacao de `ANALYST` e `VIEWER` em superficies administrativas e `legal_report`
  - leitura privilegiada de `AUDITOR` com mutacoes administrativas negadas e `authorization_denied` consultavel
- os proxies do frontend preservam a role efetiva da sessao; nao devem inventar `X-Role`

## Relacao entre RBAC e Outros Controles

O controle real de acesso hoje e combinado:

- autenticacao
- papel (`X-Role`)
- metodo de autenticacao (`X-Auth-Method`)
- `2FA` para recurso sensivel
- `RLS` por `organization_id`
- plano (`X-Plan`) para limites e catalogos

Em outras palavras: o scaffold atual usa um modelo misto de autorizacao, e nao RBAC puro.

## Gaps Atuais

### 1. Matriz de Papeis Incompleta

- falta definir claramente:
  - diferenca operacional entre `ANALYST`, `TESTER` e `VIEWER`
  - se `TESTER` continuara apenas como papel de QA/scaffold ou ganhara semantica real
  - como expandir `REVIEWER` e `BILLING_ADMIN` para mais superficies alem das fatias ja endurecidas

### 2. Falta de Granularidade

- a maior parte das APIs protegidas ainda aceita qualquer contexto autenticado valido dentro da organizacao
- `compliance` saiu do estado totalmente indiferenciado, mas ainda falta separar leitura, operacao e aprovacao para o dominio inteiro
- `monitoring` core e `investigation` core ainda nao separam leitura, operacao e aprovacao por papel fora dos cortes ja endurecidos

### 3. Cobertura Parcial de Negacao Auditada por Papel

- `WP-03` agora persiste `authorization_denied` nas rotas administrativas centrais de `monitoring`, `investigation` e `audit/logs`
- os eventos carregam `request_id`, `effective_role`, `allowed_roles`, `detail` e endpoint
- proxies do frontend nao devem sobrescrever `X-Role`; a role efetiva precisa vir do gateway/auth-service
- o mesmo padrao ainda precisa ser expandido para `compliance` restante; em `evidence/manual-package`, o `signoff_method=platform_authenticated_2fa` ja exige MFA real no backend

## Recomendacao para Fase 2

Definir uma matriz de permissoes por dominio:

- `ADMIN`
  - auditoria
  - configuracoes sensiveis
  - downloads juridicos
- `ANALYST`
  - investigation/compliance/monitoring operacionais
- `TESTER`
  - apenas ambientes de QA e fluxos de validacao, sem privilegio administrativo por default
- `VIEWER`
  - leitura segura e restrita, sem mutacao operacional
- `REVIEWER`
  - revisao/aprovacao de reports
- `BILLING_ADMIN`
  - saldo e conciliacao financeira; export financeiro permanece como proxima superficie natural
- `AUDITOR`
  - leitura ampliada de trilhas sem capacidade operacional

## Criterio de Evolucao

A RBAC atual e suficiente para o scaffold e para os fluxos mais sensiveis ja protegidos, mas nao deve ser considerada completa para ambiente regulado mais maduro.
