# Runbooks Operacionais

## Objetivo

Concentrar respostas operacionais iniciais para os incidentes mais provaveis do scaffold atual.

Este documento e intencionalmente pragmatica: ele serve para reduzir tempo de diagnostico em development e staging tecnico/regulatorio.

## Escopo Canonico

Use este documento para:

- diagnosticar incidentes e falhas operacionais apos um sintoma observavel
- orientar resposta inicial por severidade, sinais, verificacao e acao
- acelerar troubleshooting em `development`, `staging` tecnico e janelas regulatorias em curso

Nao use este documento como fonte primaria para:

- fluxo tecnico de deploy e promocao: use [Deploy e Staging](deploy-and-staging.md)
- decisao executiva de `go/no-go`: use [Gates de Release para Staging Serio](project-release-gates.md)
- governanca semanal e war room: use [Governanca Semanal](./governance-weekly/README.md)

## Severidades

| Severidade | Definicao | Acao Inicial |
| --- | --- | --- |
| `P0` | indisponibilidade geral ou risco de acesso indevido | interromper mudancas e abrir war room |
| `P1` | fluxo critico quebrado sem risco imediato de vazamento | diagnostico e hotfix priorizado |
| `P2` | falha degradada ou fluxo auxiliar | corrigir no ciclo planejado |

## Runbook 1 — Gateway indisponivel

### Runbook 1 — Gateway indisponivel — Sinais

- `http://localhost:8080` nao responde
- rotas do frontend e APIs retornam erro

### Runbook 1 — Gateway indisponivel — Verificacao

```bash
docker compose ps
docker compose logs -f traefik
curl -v http://localhost:8080/
```

### Runbook 1 — Gateway indisponivel — Causas Provaveis

- container `traefik` nao iniciou
- configuracao invalida em `dynamic.yml`
- servico alvo nao esta registrado/saudavel

### Runbook 1 — Gateway indisponivel — Acao

- corrigir config do Traefik
- rebuildar a stack
- validar novamente com smoke

## Runbook 2 — Erro de schema no banco

### Runbook 2 — Erro de schema no banco — Sinais

- mensagens de tabela/coluna ausente
- APIs falhando apos mudanca estrutural

### Runbook 2 — Erro de schema no banco — Verificacao

```bash
docker compose logs -f investigation-api
docker compose logs -f compliance-api
docker compose exec postgres psql -U ontrackchain -d ontrackchain
```

### Runbook 2 — Erro de schema no banco — Causas Provaveis

- volume antigo sem migrations aplicadas
- drift entre `init.sql` e migrations

### Runbook 2 — Erro de schema no banco — Acao

- aplicar migrations incrementais
- nao usar `down -v` como primeira resposta em staging
- rodar smoke apos corrigir

## Runbook 3 — Login/session start falhando

### Runbook 3 — Login/session start falhando — Sinais

- `/api/session/start` retorna `401`
- Playwright falha logo no login

### Runbook 3 — Login/session start falhando — Verificacao

- conferir `auth-service`
- conferir `INTERNAL_API_BASE_URL`
- conferir `APP_ENV`, `AUTH_MODE` e `DEV_AUTH_ENABLED`
- conferir emissao de dev token apenas quando o ambiente for local/teste

### Runbook 3 — Login/session start falhando — Acao

- garantir `INTERNAL_API_BASE_URL=http://traefik`
- se o ambiente for local/teste, validar `/auth/issue-dev-token`
- se o ambiente for serio, confirmar `AUTH_MODE=oidc` e `DEV_AUTH_ENABLED=false`
- rebuildar frontend se a env mudou

## Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Severidade sugerida

- `P0` se impedir login de operadores/admins em ambiente serio
- `P1` se houver degradacao parcial com alternativa operacional aprovada

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Sinais

- redirecionamento para o `Keycloak` falha ou entra em loop
- callback OIDC retorna erro repetido ou nao conclui sessao
- o provedor autentica, mas nao aplica o segundo fator esperado
- operadores tentam usar o `TOTP` local em ambiente `OIDC`

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Escopo da decisao

- em `AUTH_MODE=dev`, o segundo fator do scaffold e `TOTP` local
- em `effective_auth_mode=oidc`, o segundo fator deve ser imposto pelo provedor de identidade
- o `TOTP` local nao e fallback automatico para ambiente serio

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Verificacao

```bash
docker compose ps keycloak auth-service frontend traefik
docker compose logs --tail=200 keycloak auth-service frontend
curl -fsS http://auth.localhost:8080/realms/ontrackchain/.well-known/openid-configuration
curl -fsS http://localhost:8080/auth/config
```

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Evidencias a coletar

- horario inicial do incidente
- ambiente afetado (`local`, `test`, `staging`, `production`)
- `request_id` de tentativas falhas no callback ou no proxy
- resposta observada em `/auth/config`
- prova se o erro esta no IdP, no callback, no `token exchange` ou na politica de MFA do provedor

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Causas provaveis

- `issuer`, `jwks`, `authorization_url` ou `token_url` divergentes
- indisponibilidade do IdP ou do fator adicional configurado no provedor
- claims obrigatorias ausentes no token retornado
- regressao no callback OIDC ou no proxy server-side do frontend
- `INTERNAL_AUTH_BASE_URL` ou `INTERNAL_KEYCLOAK_BASE_URL` ausentes no frontend hospedado, fazendo o runtime cair em `hostedShowcaseFallback`

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Regra de fallback

- `local` e `test`: pode-se usar o fluxo `dev + TOTP` apenas para diagnostico local controlado
- `staging` e `production`: fallback para `dev` e proibido como resposta operacional padrao
- `staging` hospedado pode cair automaticamente em `hostedShowcaseFallback`; isso preserva a navegacao seeded, mas nao substitui o restabelecimento do `full-stack`
- qualquer excecao fora do local exige aprovacao explicita de `Arquitetura/Backend Auth` e registro do incidente

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Acao imediata

1. congelar promocoes e mudancas de auth enquanto o incidente estiver aberto
2. confirmar se o problema e:
   - indisponibilidade do IdP
   - erro de configuracao OIDC
   - regressao no callback/frontend
   - politica de MFA do provedor nao aplicada
   - frontend hospedado degradado para `hostedShowcaseFallback`
3. se `staging|production`, manter `DEV_AUTH_ENABLED=false` e tratar o caso como incidente de identidade
4. abrir/atualizar incidente operacional com owner de identidade
5. comunicar claramente que o `TOTP` local nao substitui o MFA corporativo no modo `OIDC`
6. consultar `/api/healthz` do frontend e registrar `deploymentModel`, `hostedShowcaseFallback` e `missingEnvKeys`

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Critério de excecao

Uma excecao temporaria so pode ser considerada quando:

- o ambiente nao for de producao regulada
- houver aprovacao explicita de owner tecnico responsavel
- o risco residual estiver documentado com prazo
- houver trilha de auditoria da decisao

### Runbook 4 — Indisponibilidade de OIDC ou MFA do provedor — Validacao final

- login OIDC volta a concluir sessao com sucesso
- o segundo fator do provedor volta a ser exigido conforme politica corporativa
- `AUTH_MODE=dev` nao reaparece silenciosamente no ambiente serio
- smoke/playwright de auth permanecem verdes apos a correcao

## Runbook 5 — `legal_report` retornando `403` indevido

### Runbook 5 — `legal_report` retornando `403` indevido — Sinais

- download falha mesmo apos login/2FA

### Runbook 5 — `legal_report` retornando `403` indevido — Verificacao

- checar se auth e `jwt` em ambiente serio ou `dev_jwt` apenas no scaffold local controlado
- checar se papel e `ADMIN`
- checar se `X-2FA=ok`
- checar cookies `otc_token` e `otc_2fa`

### Runbook 5 — `legal_report` retornando `403` indevido — Acao

- repetir fluxo de 2FA
- validar se o proxy do frontend esta propagando `X-2FA`
- validar no `report-api` se headers chegaram
- se o ambiente for serio, confirmar que nao houve regressao para `dev auth`

### Runbook 5 — `legal_report` retornando `403` indevido — Validacao final

- `legal_download_pre_2fa` deve falhar
- `legal_download_post_2fa` deve passar
- em ambiente serio, a liberacao deve ocorrer apenas com `OIDC` e MFA do provedor

## Runbook 6 — Auditoria nao aparece

### Runbook 6 — Auditoria nao aparece — Sinais

- `/api/v1/audit/logs` retorna vazio ou erro
- smoke falha em correlacao

### Runbook 6 — Auditoria nao aparece — Verificacao

- confirmar que a role do request e `ADMIN`
- checar `audit_logs` no banco
- checar `request_id` no fluxo

### Runbook 6 — Auditoria nao aparece — Acao

- repetir chamada com contexto `ADMIN`
- validar inserts em `audit_logs`
- validar se os proxies estao propagando `X-Request-Id`

## Runbook 7 — Falha no smoke runtime

### Runbook 7 — Falha no smoke runtime — Sinais

- `python3 scripts/smoke_runtime.py` retorna erro

### Runbook 7 — Falha no smoke runtime — Verificacao

```bash
python3 scripts/smoke_runtime.py
docker compose ps
docker compose logs --tail=200 investigation-api compliance-api monitoring-api report-api frontend auth-service
```

### Runbook 7 — Falha no smoke runtime — Acao

- identificar o primeiro passo que falhou
- isolar se o problema e:
  - gateway
  - auth
  - schema
  - proxy frontend
  - auditoria
- corrigir e rerodar smoke antes de avançar

## Runbook 8 — Falha no Playwright

### Runbook 8 — Falha no Playwright — Sinais

- `critical-path` ou `compliance-flows` vermelhos

### Runbook 8 — Falha no Playwright — Verificacao

```bash
cd apps/frontend
npm run test:e2e:oidc-critical
```

Para regressao apenas do scaffold local em `AUTH_MODE=dev`, use:

```bash
cd apps/frontend
npm run test:e2e:dev-auth
```

### Runbook 8 — Falha no Playwright — Causas Provaveis

- regressao UI/proxy
- auth/session quebrada
- fluxo de 2FA alterado
- API retornando contrato diferente

### Runbook 8 — Falha no Playwright — Acao

- identificar teste/step exato
- correlacionar com `audit_logs`
- validar manualmente o endpoint correspondente

## Runbook 9 — Concurrency/queue de investigation degradada

### Runbook 9 — Concurrency/queue de investigation degradada — Sinais

- excesso de `202 queued`
- cases nao saem da fila logica

### Runbook 9 — Concurrency/queue de investigation degradada — Verificacao

- checar quantidade de cases `processing/queued`
- checar finalizacoes internas
- checar limites do MVP

### Runbook 9 — Concurrency/queue de investigation degradada — Acao

- confirmar que a fila leve nao foi saturada por testes anteriores
- finalizar cases pendentes quando apropriado
- considerar limpeza controlada do ambiente de teste

## Runbook 10 — `report_downloaded` ausente

### Runbook 10 — `report_downloaded` ausente — Sinais

- download ocorreu, mas auditoria nao mostra `report_downloaded`

### Runbook 10 — `report_downloaded` ausente — Verificacao

- confirmar que o acesso realmente alcancou o `report-api`
- confirmar que `X-Org-Id` estava presente
- confirmar `request_id` usado no teste

### Runbook 10 — `report_downloaded` ausente — Acao

- repetir download via proxy correto
- checar logs do `report-api`
- validar tabela `audit_logs`

## Runbook 11 — Antes de fechar incidente

- rodar smoke runtime
- rodar Playwright relevante
- verificar `audit_logs` do run
- verificar `Prometheus` em `http://localhost:9090/api/v1/targets` e `.../rules`
- verificar `Grafana` em `http://localhost:3001/api/health` e dashboard provisionado
- registrar causa raiz usando `docs/cross-domain-incident-rca-playbook.md` quando houver impacto cross-domain
- registrar se houve gap de documentacao/teste

## Runbook 12 — Case em DLQ de investigation

### Runbook 12 — Case em DLQ de investigation — Sinais

- `case` termina em `failed`
- `Monitoring` mostra entrada na DLQ
- operacao precisa decidir entre requeue ou investigacao manual

### Runbook 12 — Case em DLQ de investigation — Verificacao

- confirmar `failure_reason` e `attempt_count/max_attempts`
- confirmar saldo para novo `PRE_HOLD`
- confirmar se o `report_type` ainda e permitido no plano atual

### Runbook 12 — Case em DLQ de investigation — Acao

- usar `Monitoring` ou `POST /api/v1/investigation/admin/dlq/{case_id}/requeue`
- validar `case_requeued_from_dlq` e novo `PRE_HOLD`
- acompanhar ate estado terminal em `/status`
- se nao houver acao de requeue, marcar como `acknowledged` ou `discarded`
- usar filtros de `state` e `target_chain` para revisar backlog aberto vs resolvido
- consultar `GET /api/v1/investigation/admin/alerts` para priorizar incidentes abertos
- validar `GET /api/v1/investigation/admin/metrics` para scraping e troubleshooting rapido

## Runbook 13 — Scraping/alertas de investigation indisponiveis

### Runbook 13 — Scraping/alertas de investigation indisponiveis — Sinais

- `http://localhost:9090/api/v1/targets` mostra `investigation-api` como `down`
- `http://localhost:9090/api/v1/rules` nao lista `ontrack-investigation-operational`
- dashboard operacional da UI continua funcional, mas nao ha coleta central

### Runbook 13 — Scraping/alertas de investigation indisponiveis — Verificacao

```bash
docker compose ps prometheus investigation-api
docker compose logs --tail=200 prometheus investigation-api
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS http://localhost:9090/api/v1/rules
docker compose exec investigation-api python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8001/internal/metrics/prometheus').read().decode())"
```

### Runbook 13 — Scraping/alertas de investigation indisponiveis — Causas Provaveis

- `prometheus` nao subiu ou iniciou sem os arquivos de config
- endpoint interno desabilitado por `INVESTIGATION_INTERNAL_METRICS_ENABLED=false`
- regressao de serializacao nas metricas agregadas

### Runbook 13 — Scraping/alertas de investigation indisponiveis — Acao

- revalidar `infra/observability/prometheus.yml` e `infra/observability/investigation.rules.yml`
- rebuildar `investigation-api` e `prometheus`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar target e regras

## Runbook 14 — Dashboard Grafana ausente ou vazio

### Runbook 14 — Dashboard Grafana ausente ou vazio — Sinais

- `http://localhost:3001/api/health` responde, mas o dashboard nao aparece
- `GET /api/dashboards/uid/ontrack-investigation-operations` retorna `404`
- Prometheus esta `up`, mas os operadores nao conseguem visualizar o painel pronto

### Runbook 14 — Dashboard Grafana ausente ou vazio — Verificacao

```bash
docker compose ps grafana prometheus
docker compose logs --tail=200 grafana
curl -u admin:admin http://localhost:3001/api/health
curl -u admin:admin http://localhost:3001/api/dashboards/uid/ontrack-investigation-operations
```

### Runbook 14 — Dashboard Grafana ausente ou vazio — Causas Provaveis

- arquivos de provisioning nao foram montados corretamente
- datasource `Prometheus` nao foi provisionado
- dashboard JSON invalido ou com `uid` de datasource divergente

### Runbook 14 — Dashboard Grafana ausente ou vazio — Acao

- revalidar `infra/observability/grafana/provisioning`
- revalidar `infra/observability/grafana/dashboards/investigation-operations.json`
- rebuildar/subir `grafana`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar health e dashboard

## Runbook 15 — Observabilidade de monitoring indisponivel

### Runbook 15 — Observabilidade de monitoring indisponivel — Sinais

- `http://localhost:9090/api/v1/targets` mostra `monitoring-api` como `down`
- `http://localhost:9090/api/v1/rules` nao lista `ontrack-monitoring-operational`
- dashboard `ontrack-monitoring-operations` nao aparece no `Grafana`

### Runbook 15 — Observabilidade de monitoring indisponivel — Verificacao

```bash
docker compose ps monitoring-api prometheus grafana
docker compose logs --tail=200 monitoring-api prometheus grafana
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS http://localhost:9090/api/v1/rules
curl -u admin:admin http://localhost:3001/api/dashboards/uid/ontrack-monitoring-operations
```

### Runbook 15 — Observabilidade de monitoring indisponivel — Causas Provaveis

- endpoint interno desabilitado por `MONITORING_INTERNAL_METRICS_ENABLED=false`
- regressao na serializacao agregada de watchlists/alerts/quotes
- regra ou dashboard de monitoring nao montado corretamente

### Runbook 15 — Observabilidade de monitoring indisponivel — Acao

- revalidar `infra/observability/prometheus.yml` e `infra/observability/monitoring.rules.yml`
- revalidar `infra/observability/grafana/dashboards/monitoring-operations.json`
- rebuildar `monitoring-api`, `prometheus` e `grafana`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar target, regras e dashboard

## Runbook 16 — Observabilidade de compliance indisponivel

### Runbook 16 — Observabilidade de compliance indisponivel — Sinais

- `http://localhost:9090/api/v1/targets` mostra `compliance-api` como `down`
- `http://localhost:9090/api/v1/rules` nao lista `ontrack-compliance-operational`
- dashboard `ontrack-compliance-operations` nao aparece no `Grafana`

### Runbook 16 — Observabilidade de compliance indisponivel — Verificacao

```bash
docker compose ps compliance-api prometheus grafana
docker compose logs --tail=200 compliance-api prometheus grafana
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS http://localhost:9090/api/v1/rules
curl -u admin:admin http://localhost:3001/api/dashboards/uid/ontrack-compliance-operations
```

### Runbook 16 — Observabilidade de compliance indisponivel — Causas Provaveis

- endpoint interno desabilitado por `COMPLIANCE_INTERNAL_METRICS_ENABLED=false`
- regressao na serializacao agregada de quotes/cases/reports
- regra ou dashboard de compliance nao montado corretamente

### Runbook 16 — Observabilidade de compliance indisponivel — Acao

- revalidar `infra/observability/prometheus.yml` e `infra/observability/compliance.rules.yml`
- revalidar `infra/observability/grafana/dashboards/compliance-operations.json`
- rebuildar `compliance-api`, `prometheus` e `grafana`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar target, regras e dashboard

## Runbook 16A — Homologacao AML/KYT live controlada

### Runbook 16A — Homologacao AML/KYT live controlada — Preparacao

- habilitar `COMPLIANCE_TRM_ENABLED=true`
- preencher `COMPLIANCE_TRM_SCREENING_URL`, `COMPLIANCE_TRM_API_KEY`, `COMPLIANCE_TRM_API_KEY_HEADER` e `COMPLIANCE_TRM_API_KEY_PREFIX`
- confirmar com o fornecedor o payload/endpoint esperado para screening
- confirmar timeout e retries homologados em `COMPLIANCE_TRM_TIMEOUT_MS` e `COMPLIANCE_TRM_MAX_RETRIES`
- executar `python3 scripts/preflight_external_integrations.py` com `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live` e `ONTRACKCHAIN_EXPECT_RPC_MODE=disabled` para validar URL, credencial e parametros antes da janela
- definir `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live` no shell da janela para que o artefato automatizado capture o mesmo preflight da homologacao
- validar que o endpoint `GET /api/v1/compliance/operations` expoe capability operacional para `kyc_wallet`
- executar `make check-compliance-provider-runtime INTERNAL_BASE_URL=<url-interna> PUBLIC_BASE_URL=<url-publica>` como gate leve antes da homologacao pesada
- reservar janela curta de homologacao com owner de Compliance/Backend e observabilidade ativa

### Runbook 16A — Homologacao AML/KYT live controlada — Execucao

1. Confirmar readiness sem chamada externa:
   - preferencialmente via `make check-compliance-provider-runtime`
   - ou, manualmente, `GET /internal/provider-readiness`
   - esperado: `ready=true` e `details.operating_mode=live`
2. Confirmar capability publica do catalogo:
   - `GET /api/v1/compliance/operations`
   - esperado: `kyc_wallet.provider=trm_labs`
   - esperado: `kyc_wallet.provider_status=live`
   - esperado: `kyc_wallet.capability_status=live`
   - esperado: `kyc_wallet.delivery_mode=risk_check_instant`
3. Executar `risk-check` real controlado:
   - `POST /api/v1/compliance/risk-check`
   - usar `X-Request-Id` dedicado para facilitar correlacao
   - esperado: `provider_status=live`
   - esperado: `score_source=provider_live` na trilha auditada
4. Executar `python3 scripts/smoke_runtime.py`
   - esperado: `compliance_catalog` e `compliance_risk_check` verdes
5. Exportar evidencias:
   - observacao: no baseline `local` do repositório, `COMPLIANCE_TRM_ENABLED=false`; portanto um artefato `status=ok` exige overrides serios de ambiente e provider real
   - executar `python3 scripts/homologation_external_evidence.py --mode compliance`
   - esperado: artefato JSON em `artifacts/homologation/` com `preflight`, `provider-readiness`, catalogo, `risk-check` e bundle `/audit` correlacionado pelo mesmo `request_id`
   - anexar o `.json` e o `.manifest.json` gerados ao gate de release

### Runbook 16A — Homologacao AML/KYT live controlada — Evidencias Minimas

- resposta de `provider-readiness` com `details.operating_mode=live`
- resultado `status=ok` de `python3 scripts/preflight_external_integrations.py` para `COMPLIANCE_MODE=live`
- resposta do catalogo de compliance com capability `live` para `kyc_wallet`
- resposta de `risk-check` com `provider_status=live` ou degradacao controlada explicitamente documentada
- `audit_logs` com `action=compliance_risk_checked`, `request_id`, `provider`, `provider_status`, `score_source`, `latency_ms` e `retries_used`
- resultado recente de `python3 scripts/smoke_runtime.py`
- artefato de `python3 scripts/homologation_external_evidence.py --mode compliance` com `status=ok`
- bundle de evidencias exportado de `/audit` anexado ao gate de release

### Runbook 16A — Homologacao AML/KYT live controlada — Falhas Aceitaveis

- indisponibilidade controlada do provider durante a janela, desde que:
  - `provider_status=degraded`
  - `degraded_reason` esteja preenchido
  - a falha esteja auditada com `request_id`
  - a homologacao seja marcada como `nao concluida`, nunca como `aprovada`

### Runbook 16A — Homologacao AML/KYT live controlada — Resultado Esperado

- `provider-readiness` retorna `details.operating_mode=live`
- `GET /api/v1/compliance/operations` retorna `kyc_wallet.capability_status=live`
- `risk-check` retorna `provider_status=live` ou, se houver indisponibilidade controlada, o erro fica auditado e explicito
- `audit_logs` registra `score_source=provider_live`
- a evidência do run fica disponível para anexar ao gate de release

## Runbook 16B — Homologacao RPC live controlada

### Runbook 16B — Homologacao RPC live controlada — Preparacao

- habilitar `INVESTIGATION_RPC_ENABLED=true`
- preencher `INVESTIGATION_RPC_PRIMARY_URL`
- preencher `INVESTIGATION_RPC_FALLBACK_URL` quando houver segundo provider
- confirmar timeout e retries homologados em `INVESTIGATION_RPC_TIMEOUT_MS` e `INVESTIGATION_RPC_MAX_RETRIES`
- executar `python3 scripts/preflight_external_integrations.py` com `ONTRACKCHAIN_EXPECT_RPC_MODE=live|fallback_only` e `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=disabled` para validar URLs e parametros antes da janela
- definir `ONTRACKCHAIN_EXPECT_RPC_MODE=live|fallback_only` no shell da janela para que o artefato automatizado capture o preflight coerente com a aprovacao esperada
- confirmar qual resultado e aceitavel para a janela: `live` ou `fallback_only`
- reservar janela curta de homologacao com owner de Backend Core e observabilidade ativa

### Runbook 16B — Homologacao RPC live controlada — Execucao

1. Confirmar readiness sem chamada externa:
   - `GET /internal/rpc-readiness`
   - esperado: `ready=true`
   - esperado: `details.operating_mode=live` ou `fallback_only`
2. Executar investigacao controlada:
   - `POST /api/v1/investigation/estimate`
   - `POST /api/v1/investigation/start`
   - aguardar status terminal real
3. Confirmar resultado final:
   - `GET /api/v1/investigation/{case_id}/result`
   - esperado: `analysis_version=rpc_provider_v1`
   - esperado: `kyw_summary.rpc.provider_status=live|degraded`
   - esperado: `kyw_summary.rpc.rpc_source=provider_primary|provider_fallback`
4. Executar `python3 scripts/smoke_runtime.py`
   - esperado: `investigation_result` verde preservando `provider_status` e `rpc_source`
5. Exportar evidencias:
   - observacao: no baseline `local` do repositório, `INVESTIGATION_RPC_ENABLED=false`; portanto um artefato `status=ok` exige URLs reais e overrides serios de ambiente
   - executar `python3 scripts/homologation_external_evidence.py --mode rpc --rpc-expected-mode live|fallback_only`
   - esperado: artefato JSON em `artifacts/homologation/` com `preflight`, `rpc-readiness`, `estimate`, `start`, `result` e bundle `/audit` correlacionado pelo mesmo `request_id`
   - anexar o `.json` e o `.manifest.json` gerados ao gate de release

### Runbook 16B — Homologacao RPC live controlada — Evidencias Minimas

- resposta de `rpc-readiness` com `ready=true`
- resultado `status=ok` de `python3 scripts/preflight_external_integrations.py` para o modo RPC esperado
- `details.operating_mode=live` ou `fallback_only`, conforme a janela aprovada
- resultado final da investigation com `analysis_version=rpc_provider_v1`
- `kyw_summary.rpc.provider_status` preenchido
- `kyw_summary.rpc.rpc_source` igual a `provider_primary` ou `provider_fallback`
- resultado recente de `python3 scripts/smoke_runtime.py`
- artefato de `python3 scripts/homologation_external_evidence.py --mode rpc` com `status=ok`
- bundle de evidencias exportado de `/audit` anexado ao gate de release

### Runbook 16B — Homologacao RPC live controlada — Falhas Aceitaveis

- fallback controlado para provider secundario durante a janela, desde que:
  - `details.operating_mode=fallback_only` ou `kyw_summary.rpc.rpc_source=provider_fallback`
  - a investigacao termine com trilha consistente
  - a homologacao registre explicitamente que o primario nao foi validado como `live`
- falha total do primario sem fallback funcional:
  - a homologacao deve ser marcada como `nao concluida`, nunca como `aprovada`

### Runbook 16B — Homologacao RPC live controlada — Resultado Esperado

- `rpc-readiness` retorna `details.operating_mode=live` ou `fallback_only`
- o resultado final da investigation preserva `analysis_version=rpc_provider_v1`
- `kyw_summary.rpc.rpc_source` identifica `provider_primary` ou `provider_fallback`
- a evidência do run fica disponível para anexar ao gate de release

## Runbook 16C — Homologacao do feed UE tokenizado

### Runbook 16C — Homologacao do feed UE tokenizado — Preparacao

- obter a URL XML tokenizada oficial do feed da UE
- preencher `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` no `.env.staging.private`
- confirmar que `DATABASE_URL` aponta para o banco do ambiente-alvo
- executar `python3 scripts/preflight_external_integrations.py` para validar `https` e bloquear URLs locais
- rebuildar ou reexecutar o `compliance-worker` com a env atualizada
- reservar janela curta com owner de Compliance/Backend e observabilidade do worker ativa

### Runbook 16C — Homologacao do feed UE tokenizado — Execucao

1. Confirmar precondicao de override:
   - `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` presente
   - esperado: URL XML tokenizada com `token=`
2. Reexecutar o worker de compliance:
   - esperado: tentativa real de sync de `EU_CONSOLIDATED`
   - esperado: override persistido antes do sync
3. Executar o gate canônico da janela UE:
   - preferencialmente `make run-eu-sanctions-window WINDOW_ID=<janela>`
   - ou, de forma pontual, `make check-eu-sanctions-window REQUEST_ID=<eu_request_id>`
   - esperado: `EU_CONSOLIDATED` em `status=ACTIVE`
   - esperado: `EU_CONSOLIDATED.last_sync_status=SUCCESS`
   - esperado: `sanctions_lists_meta.source_url` igual ao override configurado
4. Revisar os artefatos persistidos em `artifacts/staging/checks/`:
   - `<janela>-eu-sanctions-preflight.json`
   - `<janela>-eu-sanctions-sync.json`
5. Anexar os artefatos do runner ao sign-off da janela

### Runbook 16C — Homologacao do feed UE tokenizado — Comandos Exatos

```bash
export WINDOW_ID=stg-$(date +%F)-eu
export REQUEST_ID=${WINDOW_ID}-eu-check
make gate-p0-03-eu-live WINDOW_ID=$WINDOW_ID REQUEST_ID=$REQUEST_ID
make check-eu-sanctions-window REQUEST_ID=$REQUEST_ID
```

Se o arquivo privado nao estiver no caminho padrao ou se voce quiser isolar a saida:

```bash
export WINDOW_ID=stg-$(date +%F)-eu
make rerun-compliance-worker
make run-eu-sanctions-window \
  WINDOW_ID=$WINDOW_ID \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks
```

### Runbook 16C — Homologacao do feed UE tokenizado — Evidencias Minimas

- `python3 scripts/preflight_external_integrations.py` com `status=ok`
- `make check-eu-sanctions-window REQUEST_ID=<eu_request_id>` com `status=ok`
- `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`
- `source_url` persistido igual ao valor de `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` contendo `token=`
- log operacional ou evidência do `compliance-worker` anexado ao pacote da janela

### Runbook 16C — Homologacao do feed UE tokenizado — Falhas Aceitaveis

- `403` da UE antes do provisionamento da URL tokenizada:
  - a janela deve ser marcada como `nao concluida`
  - o erro deve aparecer explicitamente no checker ou no `status_reason`
- divergencia entre override configurado e `source_url` persistido:
  - a janela deve falhar
  - nunca tratar como sucesso parcial

### Runbook 16C — Homologacao do feed UE tokenizado — Resultado Esperado

- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` valido e tokenizado
- `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`
- `source_url` persistido convergente com o override
- checker pos-sync verde e anexavel ao gate de release

## Runbook 17 — Observabilidade de report indisponivel

### Runbook 17 — Observabilidade de report indisponivel — Sinais

- `http://localhost:9090/api/v1/targets` mostra `report-api` como `down`
- `http://localhost:9090/api/v1/rules` nao lista `ontrack-report-operational`
- dashboard `ontrack-report-operations` nao aparece no `Grafana`

### Runbook 17 — Observabilidade de report indisponivel — Verificacao

```bash
docker compose ps report-api prometheus grafana
docker compose logs --tail=200 report-api prometheus grafana
curl -fsS http://localhost:9090/api/v1/targets
curl -fsS http://localhost:9090/api/v1/rules
curl -u admin:admin http://localhost:3001/api/dashboards/uid/ontrack-report-operations
```

### Runbook 17 — Observabilidade de report indisponivel — Causas Provaveis

- endpoint interno desabilitado por `REPORT_INTERNAL_METRICS_ENABLED=false`
- regressao na serializacao agregada de `reports` ou `audit_logs`
- regra ou dashboard de `report` nao montado corretamente

### Runbook 17 — Observabilidade de report indisponivel — Acao

- revalidar `infra/observability/prometheus.yml` e `infra/observability/report.rules.yml`
- revalidar `infra/observability/grafana/dashboards/report-operations.json`
- rebuildar `report-api`, `prometheus` e `grafana`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar target, regras e dashboard

## Runbook 18 — Alertmanager ou receiver interno indisponivel

### Runbook 18 — Alertmanager ou receiver interno indisponivel — Sinais

- `http://localhost:9093/-/ready` falha
- `http://localhost:9093/api/v2/alerts` nao mostra `OntrackPlatformWatchdog`
- `GET /api/v1/monitoring/admin/operational-alerts` nao lista incidentes recentes

### Runbook 18 — Alertmanager ou receiver interno indisponivel — Verificacao

```bash
docker compose ps alertmanager prometheus monitoring-api
docker compose logs --tail=200 alertmanager prometheus monitoring-api
curl -fsS http://localhost:9093/-/ready
curl -fsS http://localhost:9093/api/v2/alerts
curl -H 'X-API-Key: otc_live_demo_key' -H 'X-Role: ADMIN' http://localhost:8080/api/v1/monitoring/admin/operational-alerts?limit=20
```

### Runbook 18 — Alertmanager ou receiver interno indisponivel — Causas Provaveis

- `prometheus.yml` sem `alerting.alertmanagers`
- `alertmanager.yml` com receiver invalido ou token divergente
- `monitoring-api` sem tabela `operational_alert_events`
- webhook interno bloqueado por token incorreto

### Runbook 18 — Alertmanager ou receiver interno indisponivel — Acao

- aplicar `infra/postgres/migrations/0005_add_operational_alert_events.sql` se houver volume antigo
- revalidar `infra/observability/alertmanager.yml` e `infra/observability/platform.rules.yml`
- rebuildar `monitoring-api`, `prometheus` e `alertmanager`
- rerodar `python3 scripts/smoke_runtime.py` para confirmar watchdog, roteamento e persistencia

## Runbook 19 — Triagem manual de incidente global nao persiste

### Runbook 19 — Triagem manual de incidente global nao persiste — Sinais

- a UI `/monitoring` exibe incidente, mas o botao `Reconhecer` falha
- `GET /api/v1/monitoring/admin/operational-alerts` nao retorna `triage_status`
- o incidente continua como `pending` mesmo apos acknowledge

### Runbook 19 — Triagem manual de incidente global nao persiste — Verificacao

```bash
docker compose ps monitoring-api postgres frontend
docker compose logs --tail=200 monitoring-api frontend
curl -H 'X-API-Key: otc_live_demo_key' -H 'X-Role: ADMIN' \
  http://localhost:8080/api/v1/monitoring/admin/operational-alerts?status=firing\&triage_status=pending\&limit=20
docker compose exec -T postgres psql -U ontrackchain -d ontrackchain < infra/postgres/migrations/0006_add_operational_alert_triage.sql
```

### Runbook 19 — Triagem manual de incidente global nao persiste — Causas Provaveis

- volume antigo sem a migration `0006_add_operational_alert_triage.sql`
- proxy do frontend nao encaminha `X-Role=ADMIN`
- regressao no endpoint `POST /api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge`

### Runbook 19 — Triagem manual de incidente global nao persiste — Acao

- aplicar a migration `0006_add_operational_alert_triage.sql` em ambientes com volume persistido
- rebuildar `monitoring-api` e `frontend`
- disparar um incidente sintetico via `POST /api/v1/monitoring/test/trigger-operational-alert`
- validar o ciclo `pending -> acknowledged` por API e pela UI

## Runbook 20 — Export de incidentes globais falha ou nao gera auditoria

### Runbook 20 — Export de incidentes globais falha ou nao gera auditoria — Sinais

- a UI `/monitoring` mostra `Falha ao exportar incidentes operacionais`
- o browser nao inicia download de `CSV|JSON`
- `POST /api/app/monitoring/operational-alerts/export` retorna `401`
- `audit_logs` nao mostra `operational_alerts_exported` para o `request_id`

### Runbook 20 — Export de incidentes globais falha ou nao gera auditoria — Verificacao

```bash
docker compose ps frontend auth-service monitoring-api
docker compose logs --tail=200 frontend auth-service monitoring-api
cd apps/frontend
npx playwright test tests/e2e/compliance-flows.spec.ts -g "monitoring registra auditoria do export administrativo por request_id|monitoring exporta incidentes selecionados em json pela UI|monitoring admin operational alerts exporta recorte filtrado em csv"
```

### Runbook 20 — Export de incidentes globais falha ou nao gera auditoria — Causas Provaveis

- proxy server-side do frontend sem acesso ao `auth-service`
- override incorreto de `INTERNAL_AUTH_BASE_URL`
- regressao no encaminhamento de `X-Org-Id`, `X-User-Id` ou `X-Request-Id`
- token/cookie `otc_token` ausente ou invalido

### Runbook 20 — Export de incidentes globais falha ou nao gera auditoria — Acao

- confirmar que o proxy de export valida o token diretamente em `http://auth-service:9000/validate` ou no override configurado
- rebuildar `frontend` apos qualquer ajuste em proxy/env
- repetir o export pela UI e pela rota `/api/app/monitoring/operational-alerts/export`
- consultar `/api/app/audit/logs?request_id=<id>&action=operational_alerts_exported`
- somente fechar o incidente quando download e auditoria estiverem presentes no mesmo run

## Evolucao Recomendada

- transformar estes runbooks em procedimentos com owner
- ligar cada runbook a alertas observaveis
- criar runbooks especificos para:
  - backup/restore
  - falha de provider externo
  - incidente de seguranca

## Runbook 21 — Backup ou restore do PostgreSQL falhou

### Runbook 21 — Backup ou restore do PostgreSQL falhou — Sinais

- `bash scripts/backup_postgres.sh` termina com erro
- `bash scripts/restore_postgres.sh <arquivo.dump>` falha antes de concluir
- o `rto_seconds` nao e emitido
- o banco de restore nao contem as tabelas esperadas
- o manifesto `.manifest.json` nao e gerado

### Runbook 21 — Backup ou restore do PostgreSQL falhou — Verificacao

```bash
docker compose ps postgres
docker compose logs --tail=200 postgres
ls -lh artifacts/backups
bash scripts/backup_postgres.sh
RESTORE_TARGET_DB=ontrackchain_restore_check bash scripts/restore_postgres.sh artifacts/backups/<arquivo>.dump
```

### Runbook 21 — Backup ou restore do PostgreSQL falhou — Causas Provaveis

- container `postgres` indisponivel ou sem volume saudavel
- credenciais divergentes entre `.env` e container
- dump corrompido ou truncado
- tentativa de restore no banco principal sem confirmacao explicita

### Runbook 21 — Backup ou restore do PostgreSQL falhou — Acao

- gerar novo dump com `bash scripts/backup_postgres.sh`
- repetir o restore em banco isolado com `RESTORE_TARGET_DB`
- validar contagem minima de tabelas restauradas, `rto_seconds` e presenca dos manifestos JSON
- se o incidente afetar evidencias, auditoria ou retention, envolver `Platform/DBA` e `Security`
