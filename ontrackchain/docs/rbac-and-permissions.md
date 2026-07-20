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
- `monitoring` core:
  - leitura operacional com `ADMIN|ANALYST|AUDITOR|VIEWER` e excecao controlada de QA para `TESTER`
  - operacao humana com `ADMIN|ANALYST`
- `audit/logs`:
  - leitura privilegiada com `ADMIN|AUDITOR`
- `report download` para `legal_report`:
  - `ADMIN` + `JWT` + `2FA`

### Onde o controle ainda e predominantemente contextual

- `investigation` core (`estimate`, `start`, `status`, `result`, `history`)
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
- o mesmo padrao agora cobre a trilha administrativa de `users + external_identities`: `team_external_identity_linked` e `team_external_identity_unlinked` usam `linked_user_id` como ator preferencial em `audit_logs` e mantem o principal externo em `metadata.external_user_id` quando nao houver usuario local persistido correspondente
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
| `investigation/estimate` | JWT ou API Key | `ADMIN`, `ANALYST` e alias legado `OTK_ANALYST` | `investigation_operational_role_required` | contexto valido |
| `investigation/start` | JWT ou API Key | `ADMIN`, `ANALYST` e alias legado `OTK_ANALYST` | `investigation_operational_role_required` | `quote` valida + plan lock |
| `billing/balance` | JWT ou API Key | `ADMIN`, `BILLING_ADMIN` e alias legado `OTK_BILLING_ADMIN` | `partial_rbac_enforced` | leitura de saldo financeiro + negacao auditada |
| `billing/reconciliation` | JWT ou API Key | `ADMIN`, `BILLING_ADMIN` e alias legado `OTK_BILLING_ADMIN` | `partial_rbac_enforced` | snapshot reconciliavel de `quotes` + `credit_ledger` com negacao auditada |
| `monitoring` core (`watchlists`, `alerts`, `start`, `estimate`) | JWT ou API Key | leitura: `ADMIN`, `ANALYST`, `AUDITOR`, `VIEWER`, `TESTER` e aliases legados `OTK_ANALYST`, `OTK_VIEWER`, `OTK_TESTER`; operacao: `ADMIN`, `ANALYST` e alias legado `OTK_ANALYST` | `rbac_enforced` | leitura do cockpit e listagens sob gate `monitoring_read_role_required`; quote/start e mutacoes de watchlist sob `monitoring_operational_role_required`; `TESTER` permanece apenas na trilha de leitura/QA e no `trigger-alert` sintetico |
| `compliance/*` | JWT ou API Key | contexto misto; mutacoes criticas com `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | `estimate`, `start`, `kyc-wallet`, `risk-check`, `due-diligence`, `source-of-funds`, `counterparties`, `sanctions-check`, `blocks/evaluate`, `blocks/*/lift`, leitura de `preventive_block` em `operations/work-items*` e `counterparties/*/review` agora seguem gates formais dedicados |
| `monitoring/admin/operational-alerts` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `monitoring/admin/operational-alerts/filter-options` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `monitoring/admin/operational-alerts/export` | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | export sensivel + auditoria |
| `monitoring/admin/operational-alerts/ack*` | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | mutacao administrativa |
| `investigation/admin` (`operations`, `alerts`, `metrics`, `dlq`) | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | leitura privilegiada + negacao auditada |
| `investigation/admin/dlq/*` mutacoes | contexto autenticado via gateway | `ADMIN` | `rbac_enforced` | requeue e resolucao manual |
| `audit/logs` | contexto autenticado via gateway | `ADMIN` ou `AUDITOR` | `rbac_enforced` | acesso restrito de leitura |
| `report generate` | JWT ou API Key | `ADMIN` ou `ANALYST` | `partial_rbac_enforced` | negacao auditada na geracao basica |
| `compliance/cases/{case_id}/report` | JWT ou API Key | `ADMIN` ou `ANALYST` | `partial_rbac_enforced` | espelha o gate de `report generate` no ponto de entrada do `compliance-api`, com negacao auditada dedicada |
| `compliance/estimate` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `compliance_estimate_role_required` | quote operacional alinhado ao mesmo trilho humano de `compliance/start`, com negacao auditada dedicada |
| `compliance/counterparties` | JWT ou API Key | leitura operacional: `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER`, `REVIEWER` e aliases legados `OTK_COMPLIANCE_OFFICER`, `OTK_REVIEWER`; onboarding segue `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER`, `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | listagem operacional agora usa gate dedicado `counterparty_read_role_required`; onboarding segue `counterparty_create_role_required` e o frontend oculta formulario/listagem/workspace conforme o recorte |
| `compliance/kyc-wallet` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | screening AML/KYT com negacao auditada dedicada `kyc_wallet_role_required` |
| `compliance/risk-check` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | score de risco com negacao auditada dedicada `risk_check_role_required` |
| `compliance/due-diligence` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | screening manual assistido com negacao auditada dedicada `due_diligence_role_required` |
| `compliance/source-of-funds` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | analise de origem de fundos com negacao auditada dedicada `source_of_funds_role_required` |
| `compliance/sanctions-check/{address}` | JWT ou API Key | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | screening operacional com negacao auditada dedicada e cockpit ocultando `sanctions-check` para roles fora do recorte; a triagem formal local do resultado agora aceita tambem `REVIEWER` e `OTK_REVIEWER` sem abrir o screening |
| `reports` leitura/listagem e `ROS/COAF` leitura | JWT ou API Key | `ADMIN`, `AUDITOR`, `ANALYST`, `VIEWER` | `partial_rbac_enforced` | negacao auditada em listagem agora preservada pelo BFF/App Router (`report_read_role_required`) sem degradar para lista vazia; referencia `ros-coaf` e dossie regulatorio; `VIEWER` permanece no trilho de catalogo/metadado |
| `report detail` leitura operacional (`GET /reports/{report_id}`) | JWT ou API Key | `ADMIN`, `AUDITOR`, `ANALYST` | `rbac_enforced` | leitura detalhada agora usa gate semantico dedicado (`report_detail_role_required`) com BFF e UX degradando o painel para `VIEWER` |
| `reports/formal-dossier` export (`POST`) | JWT ou API Key | `ADMIN`, `AUDITOR` | `rbac_enforced` | endpoint composto no App Router com gate semantico dedicado (`report_formal_dossier_role_required`) e policy alinhada ao export sensivel |
| `reports/ros-coaf` aprovacao formal (`/approve`) | JWT ou API Key | `ADMIN`, `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER`, `REVIEWER` e aliases legados `OTK_*` correspondentes | `partial_rbac_enforced` | gate formal de revisao com MFA externo homologado + negacao auditada |
| `reports/ros-coaf` submissao manual (`/submitted`) | JWT ou API Key | `ADMIN`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER` | `partial_rbac_enforced` | segregacao entre revisao formal e submissao efetiva ao COAF |
| `report download` comum | JWT ou API Key | `ADMIN`, `AUDITOR`, `ANALYST` | `rbac_enforced` | download do artefato agora usa gate semantico dedicado (`report_download_role_required`) no `report-api`, com BFF e UX ocultando o CTA para `VIEWER` |
| `legal_report download` | JWT | `ADMIN` | `rbac_enforced` | `X-2FA=ok` |
| `team/users` criacao administrativa (`POST`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a criacao local de usuario agora usa gate semantico dedicado (`team_user_create_role_required`) com `detail` preservado pelo App Router |
| `team/users/{member_id}` edicao administrativa (`PATCH`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a edicao local agora usa gate semantico dedicado (`team_user_update_role_required`) com `detail` preservado pelo App Router |
| `team/users/{member_id}` desativacao administrativa (`PATCH status=disabled`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a desativacao local agora usa gate semantico dedicado (`team_user_disable_role_required`) com `detail` preservado pelo App Router |
| `team/users/{member_id}/external-identities` leitura detalhada (`GET`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a leitura administrativa dos vínculos persistidos agora usa gate semantico dedicado (`team_federated_identity_read_role_required`) com `detail` preservado pelo App Router |
| `team/users/{member_id}/external-identities` mutacao manual (`POST`, `DELETE`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | `link` e `unlink` agora usam gates semanticos dedicados (`team_federated_identity_link_role_required` e `team_federated_identity_unlink_role_required`) com `detail` preservado pelo App Router |
| `team/federated-directory/users` busca assistida (`GET`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a busca no IdP agora usa gate semantico dedicado (`team_federated_directory_search_role_required`) com `detail` preservado pelo App Router |
| `team/federated-directory/suggestions` validacao assistida (`POST`) | JWT ou API Key | `ADMIN` | `rbac_enforced` | a validacao tardia da sugestao federada agora usa gate semantico dedicado (`team_federated_directory_suggestion_role_required`) com `detail` preservado pelo App Router |
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
| `compliance/cases/{case_id}/report` | Sim | Nao | Sim | Nao | Nao | `ADMIN` e `ANALYST`; `COMPLIANCE_OFFICER` nao gera o relatório por esta superfície enquanto o `report-api` mantiver a mesma política |
| `compliance/counterparties` onboarding regulado | Sim | Nao | Sim | Nao | Nao | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias `OTK_COMPLIANCE_OFFICER`; `VIEWER` nao recebe o formulario no cockpit |
| `reports` leitura/listagem e `ROS/COAF` leitura | Sim | Sim | Sim | Nao | Sim | `partial_rbac_enforced` + negacao auditada; `VIEWER` permanece somente no trilho de catalogo/metadado |
| `report` detail read | Sim | Nao | Sim | Nao | Sim | `rbac_enforced`; `VIEWER` perde acesso ao detalhe operacional rico e recebe negacao auditada dedicada |
| `billing/balance` | Sim | Nao | Nao | Nao | Nao | `BILLING_ADMIN` e alias legado podem ler saldo financeiro; roles fora do dominio recebem negacao auditada |
| `billing/reconciliation` | Sim | Nao | Nao | Nao | Nao | `BILLING_ADMIN` e alias legado podem ler o snapshot reconciliavel de saldo, quotes e `credit_ledger`; roles fora do dominio recebem negacao auditada |
| `team` criacao/edicao/desativacao local de usuario | Sim | Nao | Nao | Nao | Nao | `ADMIN` opera `create/update/disable`; roles fora do recorte recebem negacao auditada semantica no backend e mensagem humanizada no cockpit |
| `team` leitura detalhada de vínculos federados persistidos | Sim | Nao | Nao | Nao | Nao | `ADMIN` lê o detalhe administrativo de `external-identities`; roles fora do recorte recebem negacao auditada semantica e mensagem humanizada no cockpit |
| `team` vínculo/desvínculo manual de identidade federada | Sim | Nao | Nao | Nao | Nao | `ADMIN` opera `link/unlink`; roles fora do recorte nao recebem o formulario manual nem o CTA de desvinculação no cockpit |
| `team` diretório federado assistido (`search` + `suggestion validate`) | Sim | Nao | Nao | Nao | Nao | `ADMIN` executa busca assistida e validacao tardia no IdP; roles fora do recorte nao recebem busca utilizavel no cockpit |
| `reports/ros-coaf` aprovacao formal (`/approve`) | Sim | Nao | Nao | Nao | Nao | `COMPLIANCE_OFFICER`, `LEGAL_REVIEWER` e `REVIEWER` aprovam/rejeitam com MFA externo homologado; aliases `OTK_*` equivalentes continuam aceitos |
| `reports/ros-coaf` submissao manual (`/submitted`) | Sim | Nao | Nao | Nao | Nao | permanece restrita a `COMPLIANCE_OFFICER` e alias legado para preservar segregacao regulatoria |
| `report` download comum | Sim | Nao | Sim | Nao | Sim | `rbac_enforced`; `VIEWER` perde acesso ao artefato baixável e recebe negacao auditada dedicada |
| `report` download de `legal_report` | Sim | Nao | Nao | Nao | Nao | `rbac_enforced` + `JWT` + `2FA` |
| `compliance` leitura core | Sim | Sim | Sim | Sim | Sim | leitura principal ainda guiada por contexto + `RLS` |
| `compliance` mutacao core prioritaria (`counterparties`) | Sim | Nao | Sim | Nao | Nao | `partial_rbac_enforced` + negacao auditada; `COMPLIANCE_OFFICER` e alias legado tambem autorizados |
| `compliance/estimate` quote operacional | Sim | Nao | Sim | Nao | Nao | mesmo recorte de `compliance/start`; `VIEWER` e perfis fora do trilho humano recebem `compliance_estimate_role_required` com auditoria |
| `compliance/start` abertura operacional de case | Sim | Nao | Sim | Nao | Nao | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias `OTK_COMPLIANCE_OFFICER`; negacao auditada com `compliance_start_role_required` |
| `blocks/evaluate` triagem preventiva operacional | Sim | Nao | Sim | Nao | Nao | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias `OTK_COMPLIANCE_OFFICER`; frontend oculta a superficie para roles fora do recorte |
| `blocks` leitura oficial (`GET /compliance/blocks`) e `operations/work-items`/`timeline` de `preventive_block` | Sim | Nao | Sim | Nao | Nao | `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias `OTK_COMPLIANCE_OFFICER`; `VIEWER` deixa de ler tanto o feed oficial quanto a fila compartilhada e recebe `preventive_block_read_role_required` |
| `blocks/*/lift` desbloqueio regulatorio | Sim | Nao | Nao | Nao | Nao | `ADMIN`, `COMPLIANCE_OFFICER` e alias `OTK_COMPLIANCE_OFFICER`; `ANALYST` nao executa lift |
| `counterparties/*/review` revisao formal de DD/SoF | Sim | Nao | Nao | Nao | Nao | `ADMIN`, `COMPLIANCE_OFFICER`, `REVIEWER` e aliases `OTK_*` correspondentes; `ANALYST` nao revisa formalmente |
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
- `investigation-api` agora expõe `billing/reconciliation/export` sob o mesmo gate `ADMIN|BILLING_ADMIN|OTK_BILLING_ADMIN`, preservando `content-disposition` e negacao auditada por papel no backend
- `monitoring-api` agora trata `monitoring/test/trigger-alert` como superficie de QA/admin (`ADMIN|TESTER|OTK_TESTER`), com `authorization_denied` auditado para roles fora desse recorte
- `monitoring-api` agora trata `monitoring/estimate`, `monitoring/start`, `monitoring/watchlists`, `monitoring/watchlists/{watchlist_id}/items` e `monitoring/alerts` como superficies core distintas, separando leitura operacional (`ADMIN|ANALYST|AUDITOR|VIEWER|TESTER` e aliases legados compatíveis) de operacao humana (`ADMIN|ANALYST|OTK_ANALYST`) com `authorization_denied` auditado por `monitoring_read_role_required` e `monitoring_operational_role_required`
- `investigation-api` agora trata `investigation/estimate` e `investigation/start` como superficies operacionais humanas (`ADMIN|ANALYST|OTK_ANALYST`), com `authorization_denied` auditado para roles fora desse recorte
- o cockpit `monitoring` agora degrada os paineis administrativos de `monitoring` e `investigation` para leitura privilegiada `ADMIN/AUDITOR`, ocultando mutacoes/exportacoes de incidentes globais e DLQ fora de `ADMIN` para evitar negacao tardia na UI
- o cockpit `monitoring` agora bloqueia preventivamente a carteira core de watchlists/alerts para roles fora do recorte de leitura compatível, evitando chamadas tardias ao BFF e preservando o fluxo de QA sintetico apenas para perfis `TESTER` elegíveis
- `compliance-api` agora trata `compliance/estimate` e `compliance/start` como um unico trilho operacional humano (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com `authorization_denied` auditado e `detail` dedicado ja na fase de quote
- `compliance-api` agora trata `compliance/start` como superficie operacional humana (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), separada do write generico e com `authorization_denied` auditado por `compliance_start_role_required`
- `compliance-api` agora trata `compliance/cases/{case_id}/report` como superficie operacional de emissão (`ADMIN|ANALYST`), espelhando explicitamente o gate já aplicado no `report-api` e registrando `compliance_case_report_role_required` no ponto de entrada
- `compliance-api` agora separa a leitura operacional de `compliance/counterparties` (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER|REVIEWER|OTK_REVIEWER`) do onboarding (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com `counterparty_read_role_required` para a carteira/workspace e `counterparty_create_role_required` para escrita
- `compliance-api` agora trata `compliance/kyc-wallet` como superficie operacional de screening AML/KYT (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com negacao auditada dedicada `kyc_wallet_role_required`
- `compliance-api` agora trata `compliance/risk-check` como superficie operacional de score AML/KYT (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com negacao auditada dedicada `risk_check_role_required`
- `compliance-api` agora trata `compliance/due-diligence` como superficie operacional de investigação manual assistida (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com negacao auditada dedicada `due_diligence_role_required`
- `compliance-api` agora trata `compliance/source-of-funds` como superficie operacional de análise de origem (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com negacao auditada dedicada `source_of_funds_role_required`
- `compliance-api` agora trata `compliance/sanctions-check/{address}` como superficie operacional de screening (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), com negacao auditada dedicada `sanctions_check_role_required` e preservacao do `detail` pelo App Router
- `compliance-api` agora trata `GET /api/v1/compliance/blocks` como feed oficial de leitura de `preventive_block`, usando o mesmo recorte operacional de `blocks/evaluate` e registrando `preventive_block_read_role_required` quando a role nao pertence ao trilho
- `compliance-api` agora trata a leitura de `preventive_block` em `GET /api/v1/operations/work-items` e `GET /api/v1/operations/work-items/{work_item_id}/timeline` como superficie operacional distinta (`ADMIN|ANALYST|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), removendo `VIEWER` da fila compartilhada de bloqueios e auditando `preventive_block_read_role_required`
- `compliance-api` agora trata `counterparties/*/review` como superficie formal de revisao (`ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER|REVIEWER|OTK_REVIEWER`), separada do write operacional generico de `counterparties`
- `compliance-api` agora trata `blocks/*/lift` como superficie operacional regulatoria (`ADMIN|COMPLIANCE_OFFICER|OTK_COMPLIANCE_OFFICER`), separada do `blocks/evaluate` que continua operacional
- `auth-service` agora trata `team/users/{member_id}/external-identities` `POST` e `DELETE` como superficies administrativas distintas, retornando `team_federated_identity_link_role_required` e `team_federated_identity_unlink_role_required` em vez do gate generico de escrita de `team`
- `auth-service` agora trata `team/federated-directory/users` e `team/federated-directory/suggestions` como superficies administrativas distintas, retornando `team_federated_directory_search_role_required` e `team_federated_directory_suggestion_role_required` em vez do gate generico de escrita de `team`
- `auth-service` agora trata `team/users` `POST` e `team/users/{member_id}` `PATCH` como superficies administrativas distintas para criacao, edicao e desativacao local, retornando `team_user_create_role_required`, `team_user_update_role_required` e `team_user_disable_role_required` em vez do gate generico de escrita de `team`
- `auth-service` agora trata `team/users/{member_id}/external-identities` `GET` como superficie administrativa distinta, retornando `team_federated_identity_read_role_required` em vez do gate generico de escrita de `team`
- o App Router de `reports/formal-dossier` agora trata a exportacao do dossie formal como superficie composta distinta, retornando `report_formal_dossier_role_required` em vez de depender apenas do gate herdado de `audit/evidence-export`
- `report-api` agora trata `GET /api/v1/reports/{report_id}/download` como superficie distinta de `list/get report`, retornando `report_download_role_required` e removendo `VIEWER` do artefato baixável comum
- `report-api` agora trata `GET /api/v1/reports/{report_id}` como superficie distinta da listagem/catalogo, retornando `report_detail_role_required` e removendo `VIEWER` do detalhe operacional rico
- o frontend agora degrada a UX de `billing` na navegacao lateral, nos quick actions do `/dashboard` e no acesso direto a `/billing`, escondendo CTAs e bloqueando o dashboard financeiro para roles sem permissao
- o frontend agora exibe o CTA de export financeiro apenas quando a role efetiva pode ler `billing`, mantendo o download do snapshot no mesmo trilho de autorizacao da reconciliacao
- o frontend agora oculta o deep-link de billing em `/team` quando a role efetiva nao pode ler o dominio financeiro
- o frontend agora remove a projeção lateral de `team/users` de `/billing`, mantendo o cockpit financeiro desacoplado do roster administrativo e delegando onboarding/status/identidade federada ao cockpit `/team`
- o frontend agora oculta o CTA de `trigger-alert` em `/monitoring` para roles que nao pertencem ao recorte de QA/admin
- o frontend agora oculta a superficie de DD/SoF formal em `/counterparties` para roles fora do recorte regulatorio de revisao
- o frontend agora oculta a superficie de `block lift` em `/blocks` para roles fora do recorte regulatorio operacional
- o frontend agora degrada honestamente o workspace compartilhado de `/blocks`, exibindo a restricao semantica `preventive_block_read_role_required` em vez de mascarar a negação como falha genérica de sincronizacao
- o frontend agora usa `GET /api/app/compliance/blocks` como fonte primária do histórico/workspace de `/blocks`, deixando `operations/work-items` apenas como enriquecimento operacional para owner, prazo e timeline
- o frontend agora oculta o vínculo manual e a desvinculação de identidade federada em `/team` para roles fora de `ADMIN`, mantendo mensagem explicita de restricao e o `detail` canonico do backend no trilho de erro
- o frontend agora humaniza negacoes tardias do diretório federado assistido em `/team`, traduzindo `team_federated_directory_search_role_required` e `team_federated_directory_suggestion_role_required` sem expor o `error code` cru ao operador
- o frontend agora humaniza negacoes tardias de criacao, edicao e desativacao de usuarios em `/team`, traduzindo `team_user_create_role_required`, `team_user_update_role_required` e `team_user_disable_role_required` sem expor o `error code` cru ao operador
- o frontend agora humaniza a negacao tardia da leitura detalhada de vínculos persistidos em `/team`, traduzindo `team_federated_identity_read_role_required` sem expor o `error code` cru ao operador
- o frontend agora humaniza a negacao tardia da exportacao do dossie formal em `/reports`, traduzindo `report_formal_dossier_role_required` sem expor o `error code` cru ao operador
- o frontend agora oculta o CTA de download comum em `/reports` para roles fora de `ADMIN`, `AUDITOR` e `ANALYST`, mantendo mensagem explicita de restricao e `detail` canônico `report_download_role_required` no trilho de erro
- o frontend agora degrada o painel de detalhe em `/reports` para roles fora de `ADMIN`, `AUDITOR` e `ANALYST`, ocultando o metadado rico e exibindo mensagem explicita de restricao com `detail` canônico `report_detail_role_required`
- o frontend agora degrada a UX de `ROS/COAF` entre aprovacao formal e submissao manual, ocultando a superficie de submissao para `REVIEWER`/`LEGAL_REVIEWER` e exibindo mensagem explicita de segregacao quando a role nao pode operar aquela etapa
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
  - pode operar o `trigger-alert` sintetico de `monitoring` quando o ambiente expuser endpoints de teste
- `VIEWER`
  - leitura segura e restrita, sem mutacao operacional
- `REVIEWER`
  - revisao/aprovacao de reports
- `BILLING_ADMIN`
  - saldo, conciliacao financeira e export financeiro do snapshot reconciliavel
- `AUDITOR`
  - leitura ampliada de trilhas sem capacidade operacional

## Criterio de Evolucao

A RBAC atual e suficiente para o scaffold e para os fluxos mais sensiveis ja protegidos, mas nao deve ser considerada completa para ambiente regulado mais maduro.
