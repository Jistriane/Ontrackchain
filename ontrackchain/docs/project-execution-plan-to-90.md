# Plano de Execucao para 90% de Maturidade

## Objetivo

Transformar a avaliacao de maturidade do projeto em um plano executivo acionavel para levar o Ontrackchain de:

- `89%` de construcao tecnica

para:

- `90%+` de maturidade como plataforma pronta para staging serio

Este documento complementa:

- [Avaliacao de Maturidade do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-maturity-assessment.md)
- [Board de Prioridades do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md)
- [Readiness Regulatorio](file:///home/jistriane/Ontracktchain/ontrackchain/docs/regulatory-readiness.md)

## Meta Executiva

Leitura alvo:

- `90%+` de maturidade tecnica

Condicoes para considerar a meta atingida:

- auth forte sem dependencia do fluxo dev
- RBAC por dominio para fluxos principais homologado em ambiente serio
- integracoes reais AML/KYT e RPC com fallback
- retention, backup/restore e exportacao segura de evidencias definidos e testados
- pipeline com gates adicionais de qualidade, schema e seguranca
- operacao com runbooks e capacidade de diagnostico mais madura

## Estrategia de Execucao

O plano esta dividido em quatro ondas.

Cada onda:

- fecha um conjunto coeso de riscos
- aumenta a nota global do projeto
- prepara a proxima etapa sem reabrir decisoes arquiteturais centrais

## Ondas de Execucao

### Onda 1 — Identidade e Acesso

Objetivo:

- remover o maior gap de seguranca e staging forte

Entregas:

- IdP real
- MFA/2FA real fora do contexto apenas local
- secrets nao-dev para auth
- homologacao seria do RBAC por dominio ja implementado
- consolidacao das negacoes sensiveis ja auditadas no core

Ganho estimado:

- `+1.5 a +2.5 pontos`

### Onda 2 — Realismo do Dominio

Objetivo:

- reduzir dependencia de stubs e aumentar aderencia de produto

Entregas:

- provider real AML/KYT
- provider RPC primario + fallback
- remocao dos stubs criticos de compliance
- metricas de disponibilidade e degradacao por provider

Ganho estimado:

- `+2 a +2.5 pontos`

### Onda 3 — Governanca e Evidencias

Objetivo:

- fechar cadeia de custodia e controles operacionais

Entregas:

- retention minima definida
- backup e restore testados
- exportacao segura de evidencias multi-dominio
- ownership operacional e runbooks mais fortes

Ganho estimado:

- `+1.5 a +2 pontos`

### Onda 4 — Gating e Promocao

Objetivo:

- endurecer o caminho de promocao para staging

Entregas:

- lint e typecheck por app
- gates de schema e migrations
- checks de seguranca
- fluxo simples de promocao para staging

Ganho estimado:

- `+1 a +1.5 ponto`

## Backlog Prioritario

| ID | Iniciativa | Dominio | Prioridade | Esforco | Owner Sugerido | Dependencias | Ganho Estimado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | Implementar IdP real e despriorizar modo dev fora de local | Auth | P0 | Alto | Backend/Auth | infra de identidade, configuracao de secrets | +1.5 |
| P0-02 | Expandir MFA real para contexto serio e runbooks de indisponibilidade | Auth | P0 | Medio | Backend/Auth + Frontend | P0-01 | +1.0 |
| P0-03 | Fechar RBAC por dominio de ponta a ponta | Seguranca | P0 | Medio | Arquiteto + Backend | P0-01 | ganho principal ja capturado |
| P0-04 | Expandir persistencia de eventos negativos sensiveis de autorizacao | Seguranca | P0 | Medio | Backend | P0-03 | ganho principal ja capturado |
| P0-05 | Integrar provider real AML/KYT em modo live | Compliance | P0 | Alto | Compliance/Backend | contrato de provider e credenciais | +1.0 |
| P0-06 | Integrar RPC primario e fallback | Investigation/Monitoring | P0 | Alto | Backend Core | P0-05 opcional | +1.0 |
| P0-07 | Remover stubs criticos de compliance | Compliance | P0 | Alto | Compliance/Backend | P0-05 | +1.0 |
| P1-01 | Definir retention policy de auditoria e evidencias | Governanca | P1 | Medio | Security/Platform | decisao de compliance | +0.5 |
| P1-02 | Implementar backup e restore testados | Operacao | P1 | Alto | Platform/DBA | P1-01 | +0.75 |
| P1-03 | Criar exportacao segura multi-dominio de evidencias | Auditoria | P1 | Alto | Backend + Frontend | P1-01 | +0.75 |
| P1-04 | Expandir `/audit` com paginação/exportacao operacional | Frontend/Ops | P1 | Medio | Frontend | P1-03 | +0.5 |
| P1-05 | Adicionar lint e typecheck dedicados por app | CI/CD | P1 | Medio | DevOps | nenhuma | +0.5 |
| P1-06 | Adicionar gates de schema/migrations | CI/CD | P1 | Medio | DevOps + Backend | P1-05 | +0.5 |
| P1-07 | Adicionar checks de seguranca na pipeline | CI/CD | P1 | Medio | DevOps/Security | P1-05 | +0.5 |
| P2-01 | Estruturar staging tecnico com smoke pos-deploy | Release | P2 | Medio | DevOps/Platform | P1-05, P1-06 | +0.5 |
| P2-02 | Formalizar owners, SLAs e runbooks de incidente | Operacao | P2 | Medio | Platform/SRE | P1-01 | +0.5 |

## Sequencia Recomendada

### Sprint 1

Foco:

- identidade forte

Entregas:

- `P0-01`
- `P0-02`

Resultado esperado:

- remover dependencia do fluxo dev nos cenarios serios

### Sprint 2

Foco:

- autorizacao e seguranca de acesso

Entregas:

- `P0-03`
- `P0-04`

Resultado esperado:

- reduzir superficie de acesso excessivo e ampliar rastreabilidade

Status atual:

- ganho tecnico principal desta sprint ja foi capturado no runtime local, nos E2Es e no CI
- o remanescente de autenticacao forte migrou para homologacao seria de `P0-01` e `P0-02`

### Sprint 3

Foco:

- realismo de produto

Entregas:

- `P0-05`
- `P0-06`
- `P0-07`

Resultado esperado:

- reduzir mocks e aumentar aderencia do dominio

### Sprint 4

Foco:

- governanca e cadeia de custodia

Entregas:

- `P1-01`
- `P1-02`
- `P1-03`
- `P1-04`

Resultado esperado:

- elevar a capacidade de auditoria e operacao controlada

### Sprint 5

Foco:

- release hardening

Entregas:

- `P1-05`
- `P1-06`
- `P1-07`
- `P2-01`
- `P2-02`

Resultado esperado:

- preparar caminho serio para staging tecnico/regulado

## Snapshot Atual do Plano

### Ganhos Ja Capturados

- `OIDC + Keycloak + PKCE` validados no runtime local
- `external_identities` e `linked_user_id` propagados no core endurecido
- `RBAC` administrativo principal fechado com trilha auditavel
- `authorization_denied` persistido no core administrativo e nos fluxos federados relevantes
- `test:e2e:oidc-critical`, regressao completa e `test:e2e:dev-auth` institucionalizados no CI

### Gaps que Ainda Seguram o 90%

- homologacao de `OIDC` e MFA serio com segredos nao-dev
- provider real AML/KYT
- RPC primario com fallback
- remocao dos stubs criticos de compliance
- retention, backup/restore e exportacao segura de evidencias

## Plano Tatico por Sprint

### Premissas de Planejamento

- squad de referencia: `1 backend`, `1 frontend`, `0.5 platform/devops`, `0.25 arquitetura/security`
- sprint de referencia: `8 a 10 dias uteis`
- estimativas em horas uteis efetivas, sem inflar com cerimonias
- faixas de risco:
  - `baixo`: baixa dependencia externa e baixa chance de retrabalho arquitetural
  - `medio`: depende de integracao moderada ou ajuste transversal
  - `alto`: depende de provider externo, infraestrutura externa ou hardening de alto impacto

### Sprint 1 — Identidade Forte

Objetivo:

- sair do conforto do fluxo local e validar caminho serio de autenticacao

| Item | WP/P | Esforco Estimado | Risco | Dependencias | Entrega de Saida |
| --- | --- | ---: | --- | --- | --- |
| Configurar `AUTH_MODE=oidc`, segredos nao-dev e docs operacionais | `WP-01` / `P0-01` | 20 a 28h | alto | credenciais e configuracao do IdP | login OIDC funcional fora do modo dev |
| Validar propagacao ponta a ponta de `X-Org-Id`, `X-User-Id`, `X-Role` | `WP-01` / `P0-01` | 8 a 12h | medio | OIDC funcional | rotas protegidas com contexto consistente |
| Expandir MFA real para contexto serio e documentar indisponibilidade | `WP-02` / `P0-02` | 12 a 18h | medio | `P0-01` | segundo fator operacional e runbook inicial |
| Testes positivos/negativos de login e fluxo sensivel | `WP-01`, `WP-02` | 8 a 12h | medio | itens acima | evidencias automatizadas da sprint |

Esforco total sugerido:

- `48 a 70h`

Risco dominante:

- dependencia externa do IdP e segredos

#### Sprint 1 — Backlog Tecnico Imediato

Leitura do estado atual:

- `auth-service` ja suporta `AUTH_MODE=dev|oidc`, validacao via `JWKS` e `effective_auth_mode`
- o frontend ja alterna entre login dev e fluxo `OIDC` por `Redirect Web`, com `PKCE` e callback em `/oidc/callback`
- o `2FA` atual ja e `TOTP` real no fluxo local, mas ainda nao esta integrado como experiencia de autenticacao forte em ambiente serio
- o maior gap da sprint nao e algoritmo, e sim operacionalizacao de IdP, claims, secrets e UX de entrada segura
- decisao arquitetural desta sprint: `Keycloak` como IdP e `Redirect Web` como primeiro corte de login serio
- a trilha local do `WP-01` ja possui evidencia automatizada positiva e negativa, incluindo `invalid_claims`

##### Faixa A — Auth Service

| Tarefa | Arquivo/Servico Principal | Resultado Esperado | Aceite Tecnico |
| --- | --- | --- | --- |
| Parametrizar `OIDC_PROVIDER=keycloak` com claims, audience e issuer coerentes | `apps/auth-service/src/auth_service/main.py` | preset oficial da sprint alinhado ao Keycloak | `/auth/config` expõe `provider=keycloak` e claims corretos |
| Endurecer validacao de configuracao OIDC em ambiente `staging` ou `production` | `apps/auth-service/src/auth_service/main.py` | falha rapida quando `OIDC_*` obrigatorio estiver ausente | health/config denunciam configuracao invalida sem fallback silencioso |
| Documentar modo de transicao entre `dev` e `oidc` sem ambiguidade | `apps/auth-service`, `docs/` e `.env.example` | rollout incremental previsivel | operadores sabem quando `dev` deixa de ser permitido |
| Preparar endpoint/configuracao para login serio por redirecionamento web | `apps/auth-service` | URL e metadados suficientes para iniciar o fluxo externo | discovery/authorization URL validos e documentados para o frontend |

##### Faixa B — Frontend

| Tarefa | Arquivo/Servico Principal | Resultado Esperado | Aceite Tecnico |
| --- | --- | --- | --- |
| Melhorar a UX de login OIDC para ambiente serio via redirecionamento | `apps/frontend/app/login/page.tsx` | instrucoes, erros e estados coerentes para `oidc` | usuario entende que o login inicia no Keycloak, nao por token colado |
| Diferenciar com clareza `dev_auth_disabled`, `missing_oidc_token`, `login_failed` e sessao expirada | `apps/frontend/app/login/page.tsx`, rotas `/api/session/*` | erros acionaveis e nao genericos | mensagens guiando troubleshooting sem ambiguidade |
| Preparar fluxo de `2FA` para coexistir com OIDC sem pressuposto incorreto | `apps/frontend/app/api/session/start/route.ts`, `verify-2fa/route.ts` | sem UX inconsistente entre `OIDC` e `JWT dev` | `oidc_2fa_managed_externally` tratado de forma explicita na UI |

##### Faixa C — Configuracao e Ambiente

| Tarefa | Arquivo/Servico Principal | Resultado Esperado | Aceite Tecnico |
| --- | --- | --- | --- |
| Versionar template de ambiente OIDC serio | `.env.example`, `docker-compose.yml` | variaveis obrigatorias e opcionais claramente separadas | ambiente sobe com OIDC configuravel sem inferencias ocultas |
| Definir combinacoes validas de `APP_ENV`, `AUTH_MODE` e `DEV_AUTH_ENABLED` | `.env.example`, docs operacionais | matriz de operacao previsivel | `local/test` e `staging/production` tem comportamento documentado |
| Registrar prerequisitos externos do IdP | `docs/` | onboarding do provider sem depender de memoria oral | checklist de issuer, client_id, audience, jwks e claims publicado |

##### Faixa D — Testes e Evidencias

| Tarefa | Arquivo/Servico Principal | Resultado Esperado | Aceite Tecnico |
| --- | --- | --- | --- |
| Adicionar smoke de `effective_auth_mode=oidc` fora de local | `scripts/` e/ou E2E | bloqueio de regressao no gate de auth | fluxo dev nao reaparece silenciosamente em staging |
| Cobrir login OIDC bem-sucedido e falhas principais | `apps/frontend/tests/e2e/` | evidencia automatizada da trilha seria | casos positivo/negativo do OIDC, inclusive `invalid_claims`, passam em CI |
| Cobrir expiracao de sessao e erro de 2FA com UX clara | `apps/frontend/tests/e2e/` | estabilidade de autenticacao visivel ao operador | erro retorna mensagem correta sem estado preso |

##### Sequencia Recomendada Dentro da Sprint 1

1. fechar matriz de ambiente e provider OIDC
2. endurecer configuracao do `auth-service`
3. ajustar UX do frontend para modo `oidc`
4. validar `TOTP`/sessao/erros no fluxo combinado
5. automatizar evidencias da sprint em smoke e E2E

##### Estado Atual do WP-01

- `Keycloak` local com realm importado, clients e mapeamento de `org`, `plan` e `otk_role`
- fluxo real `login -> Keycloak -> /oidc/callback -> sessao local -> /dashboard` validado
- usuario negativo `sem-org@ontrackchain.com` seedado para provar `401 invalid_claims`
- suite Playwright do OIDC cobrindo casos positivo, logout, callback invalido, contrato negativo e mensagem visual deterministica
- gap restante da sprint: consolidar ambiente serio com segredos nao-dev, homologacao fora do local e integracao final com MFA operacional

##### Parametros Minimos do Keycloak

1. `realm` dedicado para o ambiente do Ontrackchain
2. `client_id` do frontend web
3. `issuer URL` do realm
4. `jwks URL` do realm
5. `authorization URL` do fluxo web
6. `redirect URI` do frontend apos autenticacao
7. mapeamento das claims de `org`, `plan` e `role`

Template operacional:

- ver [keycloak-oidc-template.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/keycloak-oidc-template.md) para checklist de realm, client, claims, redirects e variaveis de ambiente prontas para preenchimento

##### Bloqueadores Externos da Sprint 1

1. `realm`, `client_id`, `issuer URL`, `jwks URL` e `authorization URL` reais do Keycloak
2. `redirect URIs` e `web origins` liberados no client do Keycloak
3. mapeamento real das claims de `org`, `plan` e `role`
4. secrets nao-dev para o ambiente serio

### Sprint 2 — RBAC de Ponta a Ponta

Objetivo:

- fechar o gap entre enforcement principal e governanca real de autorizacao

| Item | WP/P | Esforco Estimado | Risco | Dependencias | Entrega de Saida |
| --- | --- | ---: | --- | --- | --- |
| Formalizar matriz RBAC por dominio e recursos sensiveis | `WP-03` / `P0-03` | 10 a 14h | medio | `P0-01` | matriz versionada e revisada |
| Aplicar enforcement faltante nos endpoints core | `WP-03` / `P0-03` | 16 a 24h | medio | matriz RBAC | autorizacao coerente nos dominios principais |
| Expandir `authorization_denied` para todo o core administrativo | `WP-03` / `P0-04` | 10 a 16h | medio | regras de negacao definidas | trilha negativa auditavel ampliada |
| Testes negativos por papel e regressao documental | `WP-03` / `P0-03`, `P0-04` | 8 a 12h | baixo | itens acima | suite negativa cobrindo papeis criticos |

Esforco total sugerido:

- `44 a 66h`

Risco dominante:

- retrabalho de contrato entre frontend/proxies/backends ao endurecer papeis

### Sprint 3 — Compliance Real

Objetivo:

- reduzir drasticamente a dependencia de stub no dominio regulatorio

| Item | WP/P | Esforco Estimado | Risco | Dependencias | Entrega de Saida |
| --- | --- | ---: | --- | --- | --- |
| Validar provider AML/KYT em modo `live` com payload real | `WP-04` / `P0-05` | 16 a 24h | alto | credenciais do provider | `risk-check` live com fallback auditado |
| Ajustar parser/contrato e observabilidade por provider | `WP-04` / `P0-05` | 8 a 14h | medio | resposta real do provider | telemetria confiavel de degradacao |
| Remover stubs criticos restantes de compliance | `WP-06` / `P0-07` | 18 a 28h | alto | `P0-05` | endpoints core sem retorno stub |
| Atualizar contratos, smoke e regressao E2E | `WP-04`, `WP-06` | 10 a 16h | medio | itens acima | evidencias de nao-regressao |

Esforco total sugerido:

- `52 a 82h`

Risco dominante:

- payload/latencia do provider e descoberta tardia de requisitos do parceiro externo

### Sprint 4 — Resiliencia e Cadeia de Custodia

Objetivo:

- reduzir risco sistemico operacional e preparar a governanca minima exigivel

| Item | WP/P | Esforco Estimado | Risco | Dependencias | Entrega de Saida |
| --- | --- | ---: | --- | --- | --- |
| Integrar RPC primario com fallback e metricas | `WP-05` / `P0-06` | 18 a 28h | alto | providers aceitos | resiliencia de investigation/monitoring |
| Definir retention policy e owner de evidencias | `WP-07` / `P1-01` | 6 a 10h | medio | alinhamento compliance/security | politica aprovada e publicada |
| Implementar backup minimo e testar restore | `WP-08` / `P1-02` | 16 a 24h | alto | `P1-01` | restore evidenciado com RTO observado |
| Expandir exportacao segura multi-dominio | `WP-09` / `P1-03` | 16 a 24h | medio | `P1-01` | export auditado alem de monitoring |

Esforco total sugerido:

- `56 a 86h`

Risco dominante:

- restore e fallback introduzirem variacao ambiental e custo de estabilizacao

### Sprint 5 — Release Hardening

Objetivo:

- transformar evolucao tecnica em promocao repetivel e auditavel

| Item | WP/P | Esforco Estimado | Risco | Dependencias | Entrega de Saida |
| --- | --- | ---: | --- | --- | --- |
| Adicionar lint e typecheck por app | `WP-10` / `P1-05` | 10 a 16h | medio | nenhuma | pipeline com qualidade basica forte |
| Adicionar gates de schema/migration | `WP-11` / `P1-06` | 8 a 14h | medio | `P1-05` | alteracoes de dados validadas automaticamente |
| Adicionar checks de seguranca com criterio de bloqueio | `WP-11` / `P1-07` | 8 a 14h | medio | `P1-05` | pipeline com sinal de seguranca acionavel |
| Estruturar smoke pos-deploy, aprovacao e rollback | `WP-12` / `P2-01`, `P2-02` | 12 a 18h | medio | `P1-06`, `P1-07` | promocao para staging tecnico auditavel |

Esforco total sugerido:

- `38 a 62h`

Risco dominante:

- aumento do tempo de feedback da pipeline e necessidade de separar gates obrigatorios de informativos

## Trilhas Paralelas Recomendadas

### Trilha A — Produto/Core

- `Sprint 1`: `P0-01`, `P0-02`
- `Sprint 2`: `P0-03`, `P0-04`
- `Sprint 3`: `P0-05`, `P0-07`
- `Sprint 4`: `P0-06`, `P1-03`

### Trilha B — Platform/Governanca

- `Sprint 1`: preparar segredos, ambientes e prerequisitos do IdP
- `Sprint 2`: consolidar matriz de acesso e observabilidade de negacoes
- `Sprint 3`: preparar requisitos de provider e ambientes de homologacao
- `Sprint 4`: `P1-01`, `P1-02`
- `Sprint 5`: `P1-05`, `P1-06`, `P1-07`, `P2-01`, `P2-02`

## Criterio Tatico de Go/No-Go por Sprint

| Sprint | Go | No-Go |
| --- | --- | --- |
| 1 | login serio funcional e MFA validado | IdP ainda bloqueando o fluxo principal |
| 2 | RBAC documentado, aplicado e auditado | papeis ainda ambiguos ou negacoes sem trilha |
| 3 | compliance core sem stub relevante | provider ainda sem validacao real ou contrato instavel |
| 4 | restore e fallback provados com evidencia | resiliencia so teorica, sem execucao documentada |
| 5 | pipeline endurecida e promocao repetivel | staging ainda depende de validacao manual ad hoc |

## Matriz de Dependencias

| Iniciativa | Bloqueia | Motivo |
| --- | --- | --- |
| `P0-01` IdP real | `P0-02`, `P0-03` | auth forte precisa estar definida antes do enforcement fino |
| `P0-03` RBAC por dominio | `P0-04` | eventos negativos dependem de regras explicitas de negacao |
| `P0-05` Provider AML/KYT real | `P0-07` | remover stubs sem provider aumentaria risco de regressao |
| `P1-01` Retention policy | `P1-02`, `P1-03`, `P2-02` | governanca de evidencias precisa de base formal |
| `P1-05` Lint/typecheck | `P1-06`, `P1-07`, `P2-01` | pipeline precisa primeiro cobrir qualidade basica |

## Critérios de Aceitação por Onda

### Onda 1

- auth forte operacional fora do modo dev
- MFA real testado
- RBAC minimo documentado e aplicado
- eventos de negacao sensivel persistidos

### Onda 2

- endpoints de compliance mais relevantes nao dependerem mais de stub
- fallback de provider validado
- disponibilidade por provider observavel

### Onda 3

- retention definida
- backup e restore provados
- exportacao segura de evidencias disponivel para operadores autorizados

### Onda 4

- pipeline com lint/typecheck
- gates de schema ativos
- checks de seguranca ativos
- staging com smoke pos-deploy

## Riscos Principais

### 1. Complexidade de Auth

Risco:

- auth forte atrasar por dependencias externas

Mitigacao:

- usar rollout incremental
- manter `AUTH_MODE=dev|oidc` temporariamente como estrategia de transicao

### 2. Integradores Externos

Risco:

- providers AML/KYT e RPC introduzirem flakiness

Mitigacao:

- adaptar com retries, timeout, fallback e telemetria por provider

### 3. Governanca Sem Owner

Risco:

- retention, backup e evidencias virarem backlog eterno

Mitigacao:

- atribuir owner explicito por iniciativa antes do inicio da onda 3

### 4. Pipeline Mais Lenta

Risco:

- CI endurecida aumentar tempo de feedback

Mitigacao:

- paralelizar jobs
- usar cache
- separar gates obrigatorios e gates informativos

## Indicadores de Sucesso

### Tecnicos

- smoke runtime verde apos cada onda
- Playwright critical/compliance verde apos cada onda
- nenhuma regressao em:
  - `plan lock`
  - `report_generated`
  - `report_downloaded`
  - `legal_report`
  - investigation assíncrona

### Operacionais

- operadores conseguem diagnosticar fluxos sensiveis por `request_id`
- auditoria consegue exportar evidencias seguras
- staging responde com runbooks e rollback claros

### Estrategicos

- reduzir dependencia de mock
- elevar a confianca para `90%+`
- preparar entrada em staging serio

## Decisao Recomendada

Recomendacao:

- executar primeiro `Onda 1` e `Onda 2` sem abrir novas frentes grandes de UX ou features adjacentes

Justificativa:

- essas ondas compram a maior parte do ganho percentual
- elas reduzem o maior risco estrutural do projeto
- evitam que o projeto aparente maturidade maior do que realmente possui

## Suposicoes

- a meta principal continua sendo staging serio com viés regulatorio
- o time consegue executar auth, integracoes e governanca em paralelo parcial
- nao surgirao mudancas de escopo maiores que invalidem a referencia atual de `89%`
