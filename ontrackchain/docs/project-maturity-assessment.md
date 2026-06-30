# Avaliacao de Maturidade do Projeto

## Objetivo

Consolidar uma leitura executiva e tecnica do estado atual do Ontrackchain, transformando a analise de maturidade em um artefato reutilizavel para:

- priorizacao de roadmap
- handoff tecnico
- alinhamento entre produto, engenharia, seguranca e operacao
- decisao sobre entrada em staging tecnico ou regulado

## Resumo Executivo

Leituras oficiais recomendadas:

- `89%` de construcao como plataforma tecnica funcional
- `76%` de prontidao para producao regulada

Interpretacao:

- o projeto ja passou da fase de scaffold avancado e opera com identidade federada, RBAC administrativo e trilhas auditaveis comprovadas
- a maior parte do core tecnico ja existe, e agora tambem possui evidencia automatizada mais forte em CI, gates por componente e orquestracao seria de `staging`
- os pontos restantes estao concentrados em maturidade pesada:
  - homologacao de identidade forte fora do ambiente local
  - integracoes reais AML/KYT/RPC
  - retention, backup/restore e exportacao segura de evidencias
  - gates adicionais de qualidade, schema e seguranca
  - operacao de producao com owners, SLOs e segredos nao-dev

## Regua Utilizada

Esta avaliacao usa duas reguas distintas:

### 1. Construcao Tecnica do Produto

Mede o quanto o sistema ja esta efetivamente construido como plataforma funcional:

- servicos
- contratos
- fluxo operacional
- trilha auditavel
- testes
- observabilidade

Resultado atual:

- `89%`

### 2. Prontidao para Producao Regulada

Mede o quanto o projeto esta pronto para um contexto forte de operacao regulada:

- identidade e MFA reais
- retention e cadeia de custodia
- backup e restore
- RBAC formal
- integracoes reais
- operacao e governanca

Resultado atual:

- `76%`

## Evidencias Utilizadas

Principais artefatos considerados:

- [`README.md`](file:///home/jistriane/Ontracktchain/ontrackchain/README.md)
- [`docs/README.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/README.md)
- [`docs/architecture.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/architecture.md)
- [`docs/regulatory-readiness.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/regulatory-readiness.md)
- [`docs/compliance-and-security-controls.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/compliance-and-security-controls.md)
- [`docs/validation-and-audit.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/validation-and-audit.md)
- [`docs/ci-cd-and-release.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/ci-cd-and-release.md)
- [`docs/pre-production-checklist.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/pre-production-checklist.md)
- [`docs/project-release-gates.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-release-gates.md)
- [`docs/project-priority-board.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md)
- [`docs/project-execution-plan-to-90.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-execution-plan-to-90.md)
- [`docs/rbac-and-permissions.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/rbac-and-permissions.md)
- [`docs/adrs/ADR-006-identidade-federada-e-users-locais.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/adrs/ADR-006-identidade-federada-e-users-locais.md)
- [`docs/adrs/ADR-007-validacao-por-modo-de-autenticacao.md`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/adrs/ADR-007-validacao-por-modo-de-autenticacao.md)
- [`apps/auth-service/src/auth_service/main.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/auth-service/src/auth_service/main.py)
- [`apps/investigation-api/src/investigation_api/main.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/investigation-api/src/investigation_api/main.py)
- [`apps/investigation-api/src/investigation_api/worker.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/investigation-api/src/investigation_api/worker.py)
- [`apps/compliance-api/src/compliance_api/main.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/compliance-api/src/compliance_api/main.py)
- [`apps/compliance-api/src/compliance_api/risk_provider.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/compliance-api/src/compliance_api/risk_provider.py)
- [`apps/compliance-api/tests/test_risk_provider.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/compliance-api/tests/test_risk_provider.py)
- [`apps/monitoring-api/src/monitoring_api/main.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/monitoring-api/src/monitoring_api/main.py)
- [`apps/report-api/src/report_api/main.py`](file:///home/jistriane/Ontracktchain/ontrackchain/apps/report-api/src/report_api/main.py)
- [`.github/workflows/e2e-tests.yml`](file:///home/jistriane/Ontracktchain/ontrackchain/.github/workflows/e2e-tests.yml)
- [`.github/workflows/quality-gates.yml`](file:///home/jistriane/Ontracktchain/ontrackchain/.github/workflows/quality-gates.yml)
- [`scripts/smoke_runtime.py`](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/smoke_runtime.py)
- [`scripts/run_staging_window.py`](file:///home/jistriane/Ontracktchain/ontrackchain/scripts/run_staging_window.py)

## Matriz de Maturidade

| Dominio | Maturidade | Peso | Contribuicao | Owner Sugerido |
| --- | ---: | ---: | ---: | --- |
| Arquitetura e Runtime | 93% | 12% | 11.16 | Arquiteto / Platform |
| Auth e Identidade | 88% | 14% | 12.32 | Backend / Auth |
| Investigation + Billing | 90% | 16% | 14.40 | Backend Core |
| Compliance | 78% | 12% | 9.36 | Compliance / Backend |
| Monitoring Operacional | 91% | 10% | 9.10 | Backend + Frontend |
| Reports e Evidencias | 90% | 10% | 9.00 | Backend / Compliance |
| Frontend Operacional | 89% | 8% | 7.12 | Frontend |
| Observabilidade e Alerting | 87% | 8% | 6.96 | Platform / SRE |
| Testes e CI/CD | 94% | 5% | 4.70 | DevOps |
| Seguranca e Governanca | 88% | 5% | 4.40 | Security / Platform |
| Documentacao e Handoff | 93% | 0% | fora da conta principal | Arquitetura / Engenharia |

Resultado ponderado:

- `89%`

Observacao:

- `Documentacao e Handoff` foi avaliada, mas ficou fora da conta principal para evitar inflar artificialmente o percentual do produto

## Leitura por Dominio

### Arquitetura e Runtime — 93%

Pontos fortes:

- stack multi-servico consistente
- `docker compose` executavel
- gateway central com `Traefik`
- `RLS` e migrations versionadas
- pacotes compartilhados e separacao por dominio

Gaps:

- automacao de promocao para ambientes superiores
- hardening operacional de producao

### Auth e Identidade — 88%

Pontos fortes:

- `ForwardAuth`
- suporte `dev|oidc`
- validacao de JWT e API key
- `TOTP` real integrado ao `auth-service`
- fluxo `OIDC` local exercitado com `Keycloak`, `Redirect Web`, `PKCE` e callback dedicado em `/oidc/callback`
- suite E2E cobrindo login OIDC bem-sucedido, logout, callback invalido e `invalid_claims`
- bloqueio de `dev auth` fora de ambientes locais
- preflight serio de `OIDC` para bloquear `localhost`, defaults inseguros e combinacoes invalidas fora de `local|test`
- propagacao de contexto (`X-Org-Id`, `X-User-Id`, `X-Role`, `X-Plan`)
- resolucao aditiva de `linked_user_id` com `external_identities`
- sem fallback silencioso de `OIDC` para auth local em ambiente serio
- gate E2E especifico para `OIDC` e identidade federada

Gaps:

- OIDC/IdP ja foi exercitado como caminho principal no runtime local e no CI, mas ainda nao foi homologado em ambiente serio com segredos nao-dev
- faltam ciclo de identidade operacional e onboarding/offboarding
- faltam segredos de producao e politica forte de identidade

### Investigation + Billing — 90%

Pontos fortes:

- catalogo e precificacao bem definidos
- `quote -> start`
- `plan lock`
- reserva e fechamento de creditos
- worker real com Redis
- retry/backoff, limites por plano e DLQ
- RPC com `primary_url + fallback_url`, `rpc-readiness` e preservacao de metadados do provider no resultado final

Gaps:

- mais idempotencia
- restore operacional e hardening do worker
- observabilidade mais profunda sobre falhas e tempos de fila

### Compliance — 78%

Pontos fortes:

- catalogo coerente de operacoes
- baseline regulatorio
- `risk-check` provider-aware com estados `live|degraded`
- telemetria e auditoria de degradacao por provider
- acoplamento com reports
- preflight e homologacao externa com evidencias anexaveis por `request_id`
- baseline serio de `staging` para AML/KYT com ownership, handoff e coverage executavel

Gaps:

- parte das operacoes ainda e stub/parcial
- provider AML/KYT ainda nao foi validado com credenciais reais
- falta schema regulatorio mais forte e versionamento formal

### Monitoring Operacional — 91%

Pontos fortes:

- watchlists e alertas
- integracao com `Alertmanager`
- backlog administrativo global
- filtros dinamicos
- paginação cursor-based
- ack unitario e em lote
- export auditado `CSV|JSON`

Gaps:

- deduplicacao, escalonamento e politicas de operacao mais sofisticadas
- refinamentos adicionais de UX operacional

### Reports e Evidencias — 90%

Pontos fortes:

- `report_id` deterministico
- `file_hash_sha256`
- enforcement forte em `legal_report`
- trilha auditavel de geracao e download
- prova positiva e negativa de acesso apos `2FA`
- suporte coerente de sessao forte local controlada (`dev_jwt`) sem abrir bypass por `API Key`
- bundle multi-dominio e dossier de janela para anexacao operacional

Gaps:

- versionamento formal de templates
- exportacao multi-dominio de evidencias
- assinatura/selagem externa para contexto regulado forte

### Frontend Operacional — 89%

Pontos fortes:

- UI administrativa e operacional bem distribuida
- proxies autenticados
- `/audit` e `/monitoring` funcionais
- persistencia de selecao e cursor na triagem global
- login com `TOTP` real e rotas principais testadas em E2E

Gaps:

- paginação/exportacao mais ricas em auditoria
- maior profundidade de UX para operacao e troubleshooting

### Observabilidade e Alerting — 87%

Pontos fortes:

- Prometheus
- Grafana
- Alertmanager
- dashboards e regras por dominio
- persistencia de incidentes globais
- alertas de degradacao recente do provider AML/KYT
- owners operacionais, runbooks e SLA base ja publicados

Gaps:

- security monitoring mais forte
- SLAs/SLOs e owners formais
- correlacao operacional mais rica entre dominios

### Testes e CI/CD — 94%

Pontos fortes:

- smoke runtime
- Playwright E2E
- pipeline com `build`, `smoke` e `playwright`
- artefatos de diagnostico
- testes unitarios do adapter de risk provider
- gate `OIDC` critico explicito antes da regressao completa
- job separado de `dev auth` para preservar o scaffold local sem contaminar o gate serio
- suite E2E ampliada cobrindo identidade federada, `authorization_denied` e `legal_report`
- `frontend-typecheck`, `python-quality`, `postgres-schema`, `security-baseline` e regressao de preflights/homologacao na pipeline

Gaps:

- reducao de duplicacao entre runners e melhoria de tempo de feedback
- execucao real do runner de janela em ambiente serio com segredos e providers homologados
- promocao automatizada completa para ambientes superiores

### Seguranca e Governanca — 88%

Pontos fortes:

- `RLS`
- trilha auditavel
- enforcement forte em fluxo sensivel
- contexto autenticado propagado
- eventos `authorization_denied` persistidos nos dominios administrativos principais
- ADR formal para identidade federada
- ADR formal para validacao por modo de autenticacao
- checklist pre-producao e gates de release alinhados aos trilhos `oidc` e `dev auth`
- baseline de retention/recovery publicada com owners e restore evidenciado
- baseline de ownership operacional e SLA publicada por dominio

Gaps:

- RBAC ainda nao foi homologado em ambiente serio com secrets nao-dev e governanca operacional completa
- negacoes sensiveis ainda nao cobrem literalmente todo o ecossistema, apesar de o core administrativo ja estar fechado
- faltam sign-offs formais de Security/Compliance/Platform para transformar baseline em controle aceito
- vault e incident response ainda nao estao maduros como operacao de producao

## O Que Segura o Projeto Abaixo de 90%

Os principais bloqueadores estruturais sao:

1. identidade forte com IdP externo ainda nao foi homologada fora do contexto local com segredos nao-dev
2. operacoes de compliance ainda dependem parcialmente de stubs
3. providers reais AML/KYT/RPC com fallback ainda nao estao consolidados em producao-like
4. retention, ownership e recovery ja possuem baseline tecnica, mas ainda aguardam aceite formal e execucao em ambiente serio
5. a pipeline ficou forte tecnicamente, mas a promocao ainda nao foi exercitada com segredos nao-dev e homologacao externa real

## Plano para Sair de 89% para 90%+

### Onda 1 — Identidade e Acesso

Objetivo:

- fechar o maior gap estrutural de seguranca e staging forte

Entregas:

- IdP real
- MFA real
- fluxo de autenticacao forte sem dependencia do modo dev
- RBAC minimo por dominio

Ganho estimado:

- `+4 a +5 pontos`

### Onda 2 — Realismo do Dominio

Objetivo:

- reduzir dependencia de stubs e aumentar credibilidade funcional

Entregas:

- providers reais AML/KYT
- RPC primario + fallback
- substituicao dos stubs criticos de compliance

Ganho estimado:

- `+2 a +2.5 pontos`

### Onda 3 — Governanca e Evidencias

Objetivo:

- fechar a cadeia de custodia operacional

Entregas:

- retention minima
- backup e restore testados
- exportacao segura de evidencias multi-dominio
- runbooks e owners mais formais

Ganho estimado:

- `+1.5 a +2 pontos`

### Onda 4 — Gating e Promocao

Objetivo:

- endurecer o caminho para staging e producao

Entregas:

- lint e typecheck por app
- gates de schema
- checks de seguranca
- smoke pos-deploy e fluxo simples de promocao

Ganho estimado:

- `+1 a +1.5 ponto`

## Plano Resumido por Sprint

| Sprint | Foco | Entregas-Chave | Resultado Esperado |
| --- | --- | --- | --- |
| 1 | Auth forte | IdP real, MFA real, secrets nao-dev | remover dependencia do fluxo dev |
| 2 | RBAC | matriz por dominio e enforcement principal | reduzir superficie de acesso excessivo |
| 3 | Integracoes reais | AML/KYT e RPC com fallback | reduzir stubs e mocks criticos |
| 4 | Governanca | retention, backup/restore, export seguro | elevar prontidao regulatoria |
| 5 | Release hardening | lint, typecheck, schema, security gates | preparar staging serio |

## Matriz dos 11% Restantes para 100%

Leitura:

- os `11%` restantes nao estao concentrados em um unico bloco
- o maior peso residual esta em `Auth`, `Compliance` e `Investigation + Billing`
- parte relevante do restante nao e feature nova, e sim hardening operacional, governanca e integracoes reais

| Dominio | Atual | Alvo | Delta Bruto | Impacto Ponderado Aprox. | Principais WPs | Principal Bloqueador |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Arquitetura e Runtime | 93% | 100% | 7 | 0.84 | `WP-08`, `WP-12` | promocao e operacao de ambiente superior |
| Auth e Identidade | 88% | 100% | 12 | 1.68 | `WP-01`, `WP-02` | rollout serio do IdP fora do local, secrets nao-dev e ciclo operacional de identidade |
| Investigation + Billing | 90% | 100% | 10 | 1.60 | `WP-05`, `WP-08` | RPC resiliente, restore e hardening do worker |
| Compliance | 78% | 100% | 22 | 2.64 | `WP-04`, `WP-06` | credenciais/provider real e remocao dos stubs core |
| Monitoring Operacional | 91% | 100% | 9 | 0.90 | `WP-09`, `WP-12` | exportacao segura multi-dominio e rito de operacao |
| Reports e Evidencias | 90% | 100% | 10 | 1.00 | `WP-07`, `WP-09` | cadeia de custodia e exportacao controlada |
| Frontend Operacional | 89% | 100% | 11 | 0.88 | `WP-09`, `WP-12` | UX de evidencias, exportacao e fluxos de operacao seria |
| Observabilidade e Alerting | 87% | 100% | 13 | 1.04 | `WP-05`, `WP-12` | SLOs, correlacao cross-domain e smoke pos-deploy |
| Testes e CI/CD | 94% | 100% | 6 | 0.30 | `WP-10`, `WP-11` | execucao seria da promocao e consolidacao de tempos/caches |
| Seguranca e Governanca | 88% | 100% | 12 | 0.60 | `WP-03`, `WP-07`, `WP-08`, `WP-11` | sign-off formal, vault e incident response |

Observacao:

- a soma ponderada aproximada fecha os `11%` residuais da regua atual, com pequena variacao por arredondamento

### Leitura Executiva dos Maiores Gaps

1. `Compliance` ainda responde por cerca de `3 pontos` do gap total, porque ainda ha stub parcial e provider real nao validado em modo `live`
2. `Auth e Identidade` ainda responde por cerca de `1.7 ponto`, puxado por homologacao seria, secrets nao-dev e ciclo operacional de identidade
3. `Investigation + Billing` ainda carrega delta importante por dependencia de RPC resiliente e restore
4. o restante esta espalhado entre governanca, evidencias, observabilidade e sign-off operacional

### Ordem Recomendada para Consumir os 11%

1. consumir primeiro os pontos de maior densidade estrutural: `WP-01`, `WP-04`, `WP-06`
2. depois fechar o risco sistemico de operacao: `WP-05`, `WP-08`, `WP-11`
3. por fim consolidar governanca e promocao: `WP-07`, `WP-09`, `WP-10`, `WP-12`

## Matriz Executiva Ate 95%

### Faixa 1 — 89% para 90%+

Objetivo:

- atravessar o corte de plataforma tecnicamente pronta para `staging` serio

Principais alavancas:

- `P0-01`
- `P0-05`
- `P0-06`

Ganho estimado:

- `+1 a +2 pontos`

### Faixa 2 — 90%+ para 93%

Objetivo:

- converter baseline forte em operacao seria repetivel

Principais alavancas:

- `P0-02`
- `P1-01`
- `P2-02`
- execucao real do `run_staging_window.py` com dossier anexado

Ganho estimado:

- `+2 a +3 pontos`

### Faixa 3 — 93% para 95%

Objetivo:

- aproximar o projeto de prontidao quase plena, com menor dependencia de validacao manual dispersa

Principais alavancas:

- provider AML/KYT e RPC operando em janela seria recorrente
- sign-offs formais de retention/recovery/ownership
- incident response e vault de producao
- promocao mais automatizada para ambiente superior

Ganho estimado:

- `+2 pontos`

### Leitura Executiva

1. sair de `89%` para `90%+` depende mais de homologacao seria do que de novas features
2. sair de `90%+` para `93%` depende mais de governanca formal e operacao recorrente do que de codigo puro
3. sair de `93%` para `95%` depende de confiabilidade institucionalizada, segredos de producao e cadeia de custodia forte

## Decisao Recomendada

### Se a meta for Staging Tecnico

Leitura recomendada:

- o projeto esta suficientemente avancado para continuar evoluindo como base seria de staging tecnico

### Se a meta for Producao Regulada

Leitura recomendada:

- ainda nao deve ser tratado como pronto
- usar a referencia de `76%` de prontidao regulatoria

## Suposicoes

- a porcentagem principal mede maturidade tecnica do produto
- a documentacao atual foi recalibrada para refletir tambem `P1-05`, `P1-06`, `P1-07`, `P2-01` e a trilha executavel de janela seria
- o objetivo do projeto continua sendo evoluir para um staging serio com viés regulatorio

## Como Reavaliar

Recalcular esta matriz sempre que houver mudancas relevantes em:

- autenticacao e 2FA
- RBAC
- integracoes reais AML/KYT/RPC
- backup/restore e retention
- pipeline de CI/CD
- trilha auditavel multi-dominio

Frequencia recomendada:

- ao final de cada sprint relevante
- antes de promover para staging regulado
