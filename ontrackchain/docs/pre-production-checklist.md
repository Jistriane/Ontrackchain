# Checklist Pre-Producao

## Objetivo

Consolidar um checklist objetivo para decidir quando o projeto deixa de ser apenas um scaffold validado e passa a ser elegivel para uma jornada seria de pre-producao.

Este checklist adapta o rigor de sistemas regulados ao estado atual do Ontrackchain.

## Como Usar

- marque cada item apenas com evidencia objetiva
- nao avance para producao com itens criticos abertos
- use este documento junto com:
  - [Readiness Regulatorio](regulatory-readiness.md)
  - [Validacao e Auditoria](validation-and-audit.md)
  - [Deploy e Staging](deploy-and-staging.md)
  - [Retention e Recovery](retention-and-recovery-policy.md)
  - [Owners e SLAs Operacionais](operational-ownership-and-slas.md)

## 1. Aplicacao e Runtime

- [ ] `docker compose up -d --build` sobe todos os servicos sem erro
- [ ] `scripts/smoke_runtime.py` passa no ambiente alvo
- [ ] `npm run test:e2e:oidc-critical` passa no ambiente alvo com `AUTH_MODE=oidc` e preflight explicito de `baseURL` + `/auth/config`
- [ ] `npm run test:e2e` passa no ambiente alvo com `AUTH_MODE=oidc`
- [ ] health checks de todos os servicos respondem
- [ ] rotas Traefik refletem todos os endpoints novos

## 2. Banco e Dados

- [ ] `python3 scripts/check_postgres_schema.py` passou e `init.sql` segue alinhado com `infra/postgres/migrations`
- [ ] `python3 scripts/check_security_baseline.py` passou sem placeholders/secrets fora da allowlist
- [ ] `RLS` esta ativo nas tabelas sensiveis
- [ ] acesso cross-tenant negativo foi validado
- [ ] backup do banco foi executado e testado
- [ ] estrategia de restore foi testada
- [ ] evidencia do `rto_seconds` do ultimo restore controlado foi registrada
- [ ] manifestos JSON de backup e restore do ultimo teste controlado foram anexados

## 3. Autenticacao e Autorizacao

- [ ] JWT de staging/producao nao reutiliza secrets dev
- [ ] `python3 scripts/preflight_oidc_serious_env.py` passa com `APP_ENV=staging|production`, `AUTH_MODE=oidc`, `DEV_AUTH_ENABLED=false`, `MFA_EXTERNAL_PROVIDER_HOMOLOGATED` coerente com a janela e secrets nao-dev
- [ ] `python3 scripts/smoke_auth_oidc_mode.py` passa no ambiente alvo com `effective_auth_mode=oidc` e `/auth/issue-dev-token` desabilitado
- [ ] MFA/2FA real substituiu o mock onde necessario
- [ ] quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, existe `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` controlado para prova funcional do `legal_report`
- [ ] matriz RBAC foi definida por dominio
- [ ] `audit_logs` continua restrito a `ADMIN`
- [ ] `legal_report` continua exigindo `JWT + ADMIN + 2FA`
- [ ] `playwright-dev-auth` e tratado apenas como regressao local do scaffold, exige `AUTH_MODE=dev` e nunca e usado como criterio de promocao

## 4. Billing e Financeiro

- [ ] fluxo `estimate -> start` continua obrigatorio
- [ ] `plan lock` continua validado
- [ ] `PRE_HOLD`, `CONFIRMED` e `REFUND` podem ser reconciliados
- [ ] limites de credito e saldo estao coerentes
- [ ] divergencias de billing geram trilha auditavel

## 5. Auditoria e Evidencia

- [ ] `audit_logs` contem `request_id`
- [ ] `report_generated` e `report_downloaded` continuam auditados
- [ ] `operational_alerts_exported` continua auditado quando operadores exportam backlog global
- [ ] tentativa negada de recurso sensivel possui trilha suficiente
- [ ] `file_hash_sha256` pode ser reproduzido a partir do download
- [ ] operadores conseguem localizar eventos por `request_id`, `case_id` e `report_id`
- [ ] operadores conseguem consultar `/audit` e correlacionar exports administrativos com o mesmo `request_id`

## 6. Compliance e Seguranca

- [ ] controles de acesso sensiveis estao documentados
- [ ] retention minima de `audit_logs` foi definida
- [ ] owners de retention e recovery foram formalizados
- [ ] sign-off de `Security` e `Compliance` em [Retention e Recovery](retention-and-recovery-policy.md) foi registrado
- [ ] secrets nao estao em repositório nem em `.env` indevido
- [ ] `npm audit --omit=dev --audit-level=critical --prefix apps/frontend` passou
- [ ] alertas de seguranca/operacao foram configurados
- [ ] existe runbook de incidente para falhas criticas
- [ ] owners e SLA base por dominio foram formalizados
- [ ] aceite operacional em [Owners e SLAs Operacionais](operational-ownership-and-slas.md) foi registrado

## 7. Observabilidade

- [ ] logs centralizados estao ativos
- [ ] correlation IDs sao preservados
- [ ] dashboards minimos existem para erro, latencia e disponibilidade
- [ ] alertas existem para indisponibilidade de servico e falhas de auth
- [ ] downloads sensiveis possuem monitoramento
- [ ] `/monitoring` preserva triagem/export administrativo sem regressao

## 8. Operacao e Deploy

- [ ] staging tecnico foi validado
- [ ] staging regulatorio foi validado
- [ ] workflow manual [staging-serious-window.yml](../../.github/workflows/staging-serious-window.yml) foi executado para a janela alvo
- [ ] o `GitHub Environment` da janela possui approvals coerentes e secret `STAGING_WINDOW_PRIVATE_ENV`
- [ ] o artifact `serious-staging-window-<janela>` foi anexado ao sign-off da promocao
- [ ] bundle OIDC foi gerado quando P0-01 estava no escopo: `make run-oidc-readiness-bundle-local WINDOW_ID=<janela> BASE_URL=<url>` produziu `<janela>-oidc-readiness-bundle.json` e `<janela>-oidc-readiness-bundle.md`
- [ ] bundle regulatorio foi gerado quando P0-02/P0-03 estavam no escopo: `make run-regulatory-readiness-bundle-local WINDOW_ID=<janela>` produziu `<janela>-regulatory-readiness-bundle.json` e `<janela>-regulatory-readiness-bundle.md`
- [ ] completude do artifact foi validada: `make validate-serious-window-artifact-local WINDOW_ID=<janela>` passou com status `ok`
- [ ] rollback de aplicacao foi testado
- [ ] rollback/restore de banco foi testado
- [ ] owners de deploy, seguranca e banco estao definidos

## 9. Integracoes Externas

- [ ] providers AML/KYT reais foram validados com `make check-compliance-provider-runtime` verde e homologacao externa anexada
- [ ] `python3 scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md` passa sem placeholders sem owner, mappings obsoletos ou linhas incompletas na matriz
- [ ] `python3 scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md` gerou pacote redigido anexavel para a janela
- [ ] `python3 scripts/check_staging_env_placeholders.py --file .env.staging.private` passa sem placeholders `__FILL_*__`, variaveis criticas ausentes ou vazias
- [ ] handoff de placeholders em [Ownership do `.env.staging`](staging-env-ownership.md) foi preenchido ou explicitamente revisado para a janela
- [ ] `python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` passa sem grupos ausentes, campos `pending`, datas invalidas ou status fora da politica
- [ ] `python3 scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` executou a janela ponta a ponta com persistencia dos JSONs de checks/preflights
- [ ] `python3 scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated --run` foi exercitado como gate unico canonico, localmente ou via CI controlado
- [ ] quando `P0-01` estiver no escopo, `make run-oidc-readiness-bundle-local WINDOW_ID=<janela> BASE_URL=<url>` gera `<janela>-oidc-readiness-bundle.json` e `<janela>-oidc-readiness-bundle.md`
- [ ] `python3 scripts/preflight_external_integrations.py` passa com `ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live` antes da janela AML/KYT
- [ ] `make check-compliance-provider-runtime` fica verde com runtime convergente para `live`
- [ ] `python3 scripts/homologation_external_evidence.py --mode compliance` gera artefato `status=ok` anexavel ao gate
- [ ] quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, `python3 scripts/homologation_external_evidence.py --mode both --include-oidc-legal-report` gera artefato `status=ok` com download auditado de `legal_report`
- [ ] `python3 scripts/build_staging_release_dossier.py ...` gerou dossier consolidado com status final `ok`
- [ ] `GET /internal/provider-readiness` retorna `ready=true` e `details.operating_mode=live`
- [ ] `GET /api/v1/compliance/operations` retorna `kyc_wallet.capability_status=live`
- [ ] `POST /api/v1/compliance/risk-check` foi executado com `X-Request-Id` dedicado e evidência auditável
- [ ] bundle exportado de `/audit` foi anexado para a homologacao AML/KYT live
- [ ] quando houver feed UE no escopo, `make run-eu-sanctions-window-local WINDOW_ID=<janela>` gera `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json`
- [ ] quando houver feed UE no escopo, `EU_CONSOLIDATED` converge para `ACTIVE/SUCCESS` com `source_url` persistido coerente com o override
- [ ] RPC primario e fallback foram validados
- [ ] `python3 scripts/preflight_external_integrations.py` passa com `ONTRACKCHAIN_EXPECT_RPC_MODE=live|fallback_only` antes da janela RPC
- [ ] `python3 scripts/homologation_external_evidence.py --mode rpc --rpc-expected-mode live|fallback_only` gera artefato `status=ok` anexavel ao gate
- [ ] `GET /internal/rpc-readiness` retorna `ready=true`
- [ ] `details.operating_mode` do RPC foi validado como `live` ou `fallback_only`
- [ ] resultado final de investigation preserva `kyw_summary.rpc.provider_status` e `rpc_source`
- [ ] bundle exportado de `/audit` foi anexado para a homologacao RPC
- [ ] falhas de provider possuem estrategia de retry/fallback
- [ ] rate limiting de terceiros foi considerado
- [ ] dependencias externas criticas possuem monitoramento

## 10. Documentacao

- [ ] README principal reflete o estado real do sistema
- [ ] contratos de API estao atualizados
- [ ] ADRs cobrem as decisoes irreversiveis relevantes
- [ ] roadmap da Fase 2 esta coerente com os gaps atuais
- [ ] documentacao regulatoria e de evidencia esta atualizada

## Itens Criticos de Bloqueio

Nao avancar para pre-producao real se qualquer item abaixo estiver aberto:

- [ ] `RLS` inconsistente
- [ ] auth/2FA ainda dependente de mock no ambiente alvo
- [ ] smoke ou Playwright falhando
- [ ] gate `oidc-critical` ausente ou vermelho no ambiente alvo
- [ ] ausencia de backup/restore testado
- [ ] ausencia de trilha auditavel para fluxos sensiveis
- [ ] `legal_report` acessivel sem `JWT + ADMIN + 2FA`
- [ ] promocao baseada apenas em validacao de `dev auth`

## Criterio de Go/No-Go

### Go

- todos os itens criticos fechados
- backlog residual e conhecido
- operacao consegue diagnosticar incidentes

### No-Go

- controles criticos ainda sao apenas dev-like
- nao ha evidencia auditavel suficiente
- rollback nao foi provado

## Evidencias Minimas para Aprovar

- output do smoke runtime
- output de `npm run test:e2e:oidc-critical` com preflight bem-sucedido do ambiente serio
- output de `npm run test:e2e`
- confirmacao de backup e restore
- consulta de `audit_logs` com eventos do run atual
- prova de bloqueio e liberacao correta do `legal_report`
- artifact `serious-staging-window-<janela>` ou pacote equivalente contendo `checks`, `window packet`, `homologation` e `dossier`
- quando `P0-01` estiver no escopo, `<janela>-oidc-readiness-bundle.json` e `<janela>-oidc-readiness-bundle.md` anexados ao pacote
- quando houver `AML/KYT live`, resultado de `make check-compliance-provider-runtime` anexado ao pacote
- quando houver feed UE, `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` anexados ao pacote
- se houver mudanca no scaffold local, output de `npm run test:e2e:dev-auth` como evidencia auxiliar em `AUTH_MODE=dev`
