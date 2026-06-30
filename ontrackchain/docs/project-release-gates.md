# Gates de Release para Staging Serio

## Objetivo

Definir criterios minimos de promocao para staging serio, reduzindo o risco de promover o Ontrackchain com falsa percepcao de prontidao.

Este documento complementa:

- [Avaliacao de Maturidade do Projeto](project-maturity-assessment.md)
- [Plano de Execucao para 90%](project-execution-plan-to-90.md)
- [Board de Prioridades do Projeto](project-priority-board.md)
- [Checklist Pre-Producao](pre-production-checklist.md)
- [Runbooks Operacionais](runbooks.md)
- [Checklist de Evidencia Minima da Primeira Janela Seria](first-serious-window-evidence-checklist.md)

## Meta de Promocao

Uma promocao para staging serio so deve acontecer quando:

- os fluxos core estiverem validados de ponta a ponta
- os controles minimos de identidade, autorizacao e auditoria estiverem ativos
- a operacao conseguir detectar, diagnosticar e recuperar incidentes provaveis
- o time tiver evidencias objetivas da promocao

## Regra Geral

Promocao permitida:

- apenas quando todos os gates `obrigatorios` estiverem verdes

Promocao condicionada:

- somente para gaps classificados como `aceitaveis temporariamente`, com owner nomeado, prazo e risco documentado

Promocao bloqueada:

- quando algum gate critico de seguranca, auth, auditoria, dados ou restore estiver incompleto

## Classificacao dos Gates

### Obrigatorio

- sem esse gate, a promocao deve ser bloqueada

### Condicional

- pode haver excecao temporaria, desde que aprovada e documentada

### Informativo

- nao bloqueia sozinho, mas sinaliza reducao de maturidade

## Gates por Dominio

### 1. Auth e Identidade

Classificacao:

- `Obrigatorio`

Gate:

- auth operacional sem dependencia do caminho dev em ambiente serio
- tokens e secrets nao-dev configurados
- preflight serio de `OIDC` sem defaults locais e sem endpoints publicos em `localhost`
- validacao de contexto (`X-Org-Id`, `X-User-Id`, `X-Role`) funcionando

Evidencias:

- login real funcional em ambiente alvo
- teste de protecao de rotas administrativas
- prova de propagacao de headers de contexto
- `python scripts/preflight_oidc_serious_env.py` validando matriz seria de `OIDC`, `DEV_AUTH_ENABLED=false`, `MFA_EXTERNAL_PROVIDER_HOMOLOGATED`, secrets nao-dev e URLs publicas nao-locais
- `python scripts/smoke_auth_oidc_mode.py` validando `effective_auth_mode=oidc` e `dev_auth_disabled`
- gate `playwright` com `test:e2e:oidc-critical` verde

Bloqueadores tipicos:

- `AUTH_MODE=dev` como caminho principal
- `effective_auth_mode=dev` reaparecendo silenciosamente em `staging`/`production`
- segredo compartilhado nao controlado
- `OIDC_ISSUER_URL` ou `OIDC_AUTHORIZATION_URL` ainda apontando para `localhost`
- falta de identidade organizacional consistente

### 2. MFA / 2FA

Classificacao:

- `Obrigatorio`

Gate:

- MFA real protegendo fluxos sensiveis
- fluxo de excecao documentado para indisponibilidade do provedor

Evidencias:

- prova de MFA em download de `legal_report`
- tentativa negativa registrada em auditoria
- runbook para falha do segundo fator, incluindo politica de fallback e escalacao do IdP
- job `playwright-dev-auth` verde apenas para regressao local do scaffold, sem substituir o gate serio de `OIDC`

Bloqueadores tipicos:

- 2FA mockado
- 2FA apenas cosmetico na UI
- ausencia de trilha para negacao sensivel
- fallback silencioso de `OIDC` para `dev`
- uso do job `dev auth` como justificativa para promover ambiente serio

### Evidencia Minima de Pipeline

Classificacao:

- `Obrigatorio`

Gate:

- `playwright` em `AUTH_MODE=oidc` precisa validar o gate `OIDC` critico e a regressao completa
- `playwright-dev-auth` existe apenas como regressao controlada do scaffold local

Evidencias:

- workflow [e2e-tests.yml](../.github/workflows/e2e-tests.yml) executando:
  - `npm run test:e2e:oidc-critical`
  - `npm run test:e2e`
  - `npm run test:e2e:dev-auth`
- artefatos HTML e `test-results` publicados para ambos os trilhos
- interpretacao explicita de que apenas o trilho `oidc` bloqueia promocao de ambiente serio

Bloqueadores tipicos:

- pipeline sem separacao entre `OIDC` e `dev auth`
- ambiente serio aprovado apenas por testes do scaffold local
- falta de artefatos para diagnostico de falha em auth ou federacao

### 3. RBAC e Autorizacao

Classificacao:

- `Obrigatorio`

Gate:

- papeis principais definidos por dominio
- enforcement de autorizacao nos endpoints administrativos e sensiveis
- negacoes relevantes auditadas

Evidencias:

- matriz RBAC validada
- teste negativo por papel
- eventos de negacao com `request_id`

Bloqueadores tipicos:

- papel `ADMIN` excessivamente amplo
- autorizacao implícita por front-end
- ausencia de rastreabilidade de negacao

### 4. Investigation e Billing

Classificacao:

- `Obrigatorio`

Gate:

- `quote -> start -> worker -> report` funcional
- reserva e fechamento de credito corretos
- DLQ e retry testados em falha controlada

Evidencias:

- smoke runtime verde
- testes E2E de critical path
- caso de falha com reprocessamento ou descarte administrativo

Bloqueadores tipicos:

- inconsistencia de creditos
- worker sem recuperacao previsivel
- fluxo core quebrado apos deploy

### 5. Compliance

Classificacao:

- `Obrigatorio`

Gate:

- endpoints core sem dependencia de stub para o ambiente-alvo
- provider AML/KYT com timeout, retry e fallback quando aplicavel

Evidencias:

- chamadas reais ou controladas ao provider
- `python scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md` validando que cada placeholder `__FILL_*__` possui owner, apoio e evidencia explicitos na matriz
- `python scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md` gerando um pacote redigido da janela com baseline, handoff atual e sequencia operacional
- `python scripts/check_staging_env_placeholders.py --file .env.staging.private` validando ausencia de placeholders `__FILL_*__`, ausencias e vazios em chaves criticas do ambiente serio
- matriz de handoff em [Ownership do `.env.staging`](staging-env-ownership.md) preenchida ou revisada pelos owners da janela
- `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` validando grupos obrigatorios, owner, data e status permitidos (`approved|reviewed|waived`)
- `python scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` orquestrando a janela, persistindo JSONs de checks/preflights e bloqueando continuidade em caso de falha
- `python scripts/preflight_external_integrations.py` validando `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live` ou `ONTRACKCHAIN_EXPECT_RPC_MODE=live|fallback_only` conforme a janela
- `python scripts/homologation_external_evidence.py --mode compliance|rpc|both` gerando artefato anexavel com manifest e `request_id` correlacionado
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, o artefato de `homologation_external_evidence.py` deve incluir prova de `legal_report` via OIDC com download `200` e `report_downloaded` correlacionado
- `python scripts/build_staging_release_dossier.py` consolidando `window packet`, JSONs dos checkers e homologacao em um dossier unico anexavel para sign-off
- `provider-readiness` em modo `live`
- catalogo `/api/v1/compliance/operations` expondo `kyc_wallet.capability_status=live`
- observabilidade de falha/degradacao por provider
- `risk-check` executado com `request_id` rastreavel e trilha auditavel correspondente
- `rpc-readiness` com `ready=true` e `details.operating_mode=live|fallback_only`
- resultado final de investigation preservando `analysis_version=rpc_provider_v1`, `provider_status` e `rpc_source`
- bundle de evidencias exportado de `/audit` anexado para homologacao RPC
- bundle de evidencias exportado de `/audit` anexado ao gate
- resposta coerente para cenarios de indisponibilidade
- providers AML/KYT e RPC validados com integracoes reais e evidencias auditaveis

Bloqueadores tipicos:

- retorno stub em fluxo sensivel
- ausencia de estrategia de degradação controlada
- falha silenciosa em integrações externas

### 6. Reports e Evidencias

Classificacao:

- `Obrigatorio`

Gate:

- geracao de relatorio com `report_id` e `file_hash_sha256`
- downloads auditados
- exportacoes sensiveis com trilha de auditoria

Evidencias:

- evento `report_generated`
- evento `report_downloaded`
- evento de export auditado com `request_id`

Bloqueadores tipicos:

- ausencia de hash
- trilha incompleta de download/exportacao
- vazamento de relatorio sem controle de acesso

### 7. Observabilidade e Alerting

Classificacao:

- `Obrigatorio`

Gate:

- Prometheus, Grafana e Alertmanager ativos
- incidentes globais chegando ao `monitoring-api`
- `/monitoring` operacional para triagem

Evidencias:

- scraping funcional
- alerta sintetico persistido em `operational_alert_events`
- triagem manual e export validos

Bloqueadores tipicos:

- sem alerta operacional ponta a ponta
- sem persistencia de incidente global
- sem visibilidade minima do ambiente

### 8. CI/CD e Validacao

Classificacao:

- `Obrigatorio`

Gate:

- `build`, `smoke` e `playwright` verdes
- artefatos de falha publicados
- workflow `quality-gates` verde com `security-baseline`, `frontend-audit`, `postgres-schema`, `frontend-typecheck` e `python-quality`
- workflow manual [staging-serious-window.yml](../.github/workflows/staging-serious-window.yml) executado para a janela regulatoria com `window_id`, `mode` e `environment_name` aprovados
- validacao pos-deploy orientada a `OIDC` e integracoes reais, sem dependencias de fixture

Evidencias:

- pipeline verde no commit candidato
- logs e artefatos acessiveis
- evidencias de validacao pos-deploy quando aplicavel
- artifact `serious-staging-window-<janela>` anexado ou referenciado no sign-off
- prova de que o `GitHub Environment` da janela continha `STAGING_WINDOW_PRIVATE_ENV` e approvals coerentes com o rito serio

Bloqueadores tipicos:

- promocao sem validacao pos-deploy aderente ao ambiente real
- deploy sem E2E minimo
- pipeline sem criterio confiavel de falha
- ausencia de evidencia consolidada do smoke pos-deploy tecnico
- execucao manual fora do workflow oficial sem pacote anexavel equivalente

### 9. Dados, Retention e Restore

Classificacao:

- `Obrigatorio`

Gate:

- retention minima definida
- backup realizado
- restore pelo menos uma vez testado em ambiente controlado

Evidencias:

- politica de retention aprovada
- log de backup
- evidencia de restore com tempo de recuperacao

Bloqueadores tipicos:

- sem backup testado
- sem estrategia de retention
- evidencia sem cadeia de custodia minima

### 10. Operacao e Runbooks

Classificacao:

- `Condicional`

Gate:

- runbooks principais publicados
- owners operacionais nomeados
- caminho de escalacao minimamente definido

Evidencias:

- runbook de incidente
- runbook de restore
- owner por dominio
- registro de aceite em `retention-and-recovery-policy.md`
- registro de aceite em `operational-ownership-and-slas.md`

Bloqueadores tipicos:

- ambiente promovido sem dono
- falha sem caminho claro de resposta

## Evidencias Minimas para Aprovacao

Antes de promover, anexar ou referenciar:

- pipeline `build + smoke + playwright` verde
- resultado recente do `smoke_runtime.py`
- evidencias recentes de validacao pos-deploy aderentes ao ambiente alvo
- evidencias de:
  - `case_started`
  - `report_generated`
  - `report_downloaded`
- prova de enforcement de `legal_report`
- prova de alerta sintetico chegando ao backlog operacional
- prova de export auditado em `/monitoring`
- prova de restore ou evidencia do ultimo teste de restore
- lista de excecoes abertas com owner e prazo
- artifact `serious-staging-window-<janela>` do workflow manual com `checks`, `dossier`, `window packet` e `homologation`
- sign-off preenchido usando [Template de Sign-Off da Janela Seria](staging-serious-window-signoff-template.md)

## Checklist de Aprovacao

| Item | Obrigatorio | Status |
| --- | --- | --- |
| Auth forte fora do caminho dev | Sim | `pending` |
| MFA real nos fluxos sensiveis | Sim | `pending` |
| RBAC minimo aplicado | Sim | `pending` |
| Investigation + billing validados ponta a ponta | Sim | `pending` |
| Compliance core sem stub relevante | Sim | `pending` |
| Reports e downloads auditados | Sim | `pending` |
| Alerting e triagem globais operacionais | Sim | `pending` |
| Pipeline verde com smoke e E2E | Sim | `pending` |
| Workflow `staging-serious-window` executado e anexado | Sim | `pending` |
| Backup + restore comprovados | Sim | `pending` |
| Runbooks e owners minimos | Nao, mas recomendado | `ready_for_approval` |

## Excecoes Aceitaveis Temporariamente

Podem ser aceitas apenas se:

- nao afetarem seguranca critica
- nao afetarem identidade e autorizacao
- nao afetarem integridade de dados e restore
- tiverem owner, prazo e mitigacao

Exemplos de excecao aceitavel:

- ausencia temporaria de um gate informativo adicional de qualidade, desde que `build + smoke + playwright` estejam verdes

Exemplos de excecao nao aceitavel:

- MFA mockado em fluxo sensivel
- compliance core ainda dependente de stub
- restore nunca testado

## Critério de Rollback

Rollback deve ser imediatamente considerado quando houver:

- quebra do fluxo `quote -> start -> report`
- erro de billing ou reserva de credito inconsistente
- falha de auth em rotas sensiveis
- falha de auditoria em geracao/download/exportacao de evidencia
- ausencia de alertas operacionais em ambiente promovido
- regressao em controles de `legal_report`

## Procedimento Minimo de Rollback

1. congelar novas promocoes
2. registrar `request_id`, build e horario do incidente
3. reverter para a ultima versao validada
4. executar smoke minimo pos-rollback
5. confirmar saude de:
   - auth
   - investigation
   - report
   - monitoring
6. abrir incidente com owner e causa presumida

## Aprovadores Recomendados

- Arquitetura/Tech Lead
- Responsavel por Backend/Auth
- Responsavel por Platform/SRE
- Responsavel por Compliance/Security quando houver impacto regulatorio

## Decisao Recomendada

Uma promocao para staging serio deve exigir:

- todos os gates obrigatorios verdes
- nenhuma excecao aberta em auth, compliance core, auditoria ou restore
- evidencias anexadas ou referenciadas na aprovacao

## Suposicoes

- o projeto continuara com viés regulatorio e auditavel
- staging serio exige mais do que apenas ambiente “funcionando”
- o time aceita bloquear promocao quando a prova operacional for insuficiente
