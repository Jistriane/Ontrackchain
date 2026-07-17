# GitHub Environment para Staging Serio

## Objetivo

Definir como configurar o `GitHub Environment` usado pelo workflow manual de janela seria, centralizando:

- approvals
- secret multi-linha `STAGING_WINDOW_PRIVATE_ENV`
- disciplina operacional para o primeiro disparo real

Este documento complementa:

- [CI/CD e Release](ci-cd-and-release.md)
- [Deploy e Staging](deploy-and-staging.md)
- [Gates de Release para Staging Sério](project-release-gates.md)
- [Checklist Pré-Produção](pre-production-checklist.md)
- [Governanca Semanal](./governance-weekly/README.md)

Observacao importante:

- este documento cobre o workflow manual `Staging Serious Window`
- o workflow separado [deploy-to-production.yml](../../.github/workflows/deploy-to-production.yml) usa hooks de deploy do Render e `healthz` hospedado; ele nao consome `STAGING_WINDOW_PRIVATE_ENV`

## Papel Canonico

Este documento e a fonte primaria para:

- configuracao do `GitHub Environment` da janela seria
- reviewers, approvals e disciplina operacional do disparo manual
- formato e geracao do secret `STAGING_WINDOW_PRIVATE_ENV`
- contrato do workflow `Staging Serious Window`

Nao use este documento para:

- substituir o fluxo tecnico da janela: use [Deploy e Staging](deploy-and-staging.md)
- decidir `go/no-go`: use [Gates de Release para Staging Serio](project-release-gates.md)
- descrever a topologia hospedada e os segredos `sync: false` do Render: use [Blueprint Render para Staging Full-Stack](render-staging-blueprint.md)

## Workflow Alvo

Workflow canônico:

- neste workspace, o arquivo do workflow fica no repositório agregador pai em `../.github/workflows/`
- [staging-serious-window.yml](../../.github/workflows/staging-serious-window.yml)

Nome do workflow no GitHub Actions:

- `Staging Serious Window`

## Nome Recomendado do Environment

Recomendação inicial:

- `staging-serious`

Pode haver mais de um environment, desde que cada um mantenha o mesmo contrato operacional:

- approvals coerentes
- secret `STAGING_WINDOW_PRIVATE_ENV`
- owners explicitamente definidos

## Controles Recomendados no GitHub Environment

Configurar no repositório GitHub:

1. `Settings -> Environments`
2. criar ou revisar o environment `staging-serious`
3. habilitar reviewers obrigatórios quando a janela tocar provider real
4. restringir quem pode aprovar o environment
5. registrar descrição operacional do environment

Reviewers mínimos recomendados:

- Platform/DevOps
- Backend/Auth
- Security/Compliance quando a janela for regulatória ou homologada

## Secret Obrigatório

Nome obrigatório:

- `STAGING_WINDOW_PRIVATE_ENV`

Esse secret deve conter o conteúdo completo do arquivo `.env.staging.private`, em formato multi-linha.

## Segredos e Variables do Workflow de Deploy Hospedado

Quando o objetivo for acionar o workflow [deploy-to-production.yml](../../.github/workflows/deploy-to-production.yml), configure adicionalmente:

### Secrets

- `RENDER_STAGING_DEPLOY_HOOK_URL`
- `RENDER_PRODUCTION_DEPLOY_HOOK_URL`

### Repository Variables

- `RENDER_STAGING_HEALTHCHECK_URL`
- `RENDER_PRODUCTION_HEALTHCHECK_URL`

### Repository Variables opcionais

- `RENDER_STAGING_EXPECTED_DEPLOYMENT_MODEL`
- `RENDER_PRODUCTION_EXPECTED_DEPLOYMENT_MODEL`
- `RENDER_STAGING_ALLOW_SHOWCASE_FALLBACK`
- `RENDER_PRODUCTION_ALLOW_SHOWCASE_FALLBACK`

Recomendacao:

- manter `RENDER_STAGING_ALLOW_SHOWCASE_FALLBACK=false`
- manter `RENDER_PRODUCTION_ALLOW_SHOWCASE_FALLBACK=false`
- usar `healthz` publico do frontend, por exemplo `https://<frontend>/api/healthz`

## Formato do Secret

Use o conteudo final do `.env.staging.private` como fonte da verdade. O bloco abaixo e um recorte representativo das chaves mais sensiveis e das integracoes que costumam bloquear a janela:

```env
APP_ENV=staging
AUTH_MODE=oidc
DEV_AUTH_ENABLED=false
NEXT_PUBLIC_AUTH_MODE=oidc
NEXT_PUBLIC_APP_ENV=staging
NEXT_PUBLIC_DEV_AUTH_ENABLED=false
OIDC_PROVIDER=keycloak
OIDC_ISSUER_URL=https://auth.staging.example.com/realms/ontrackchain
OIDC_AUTHORIZATION_URL=https://auth.staging.example.com/realms/ontrackchain/protocol/openid-connect/auth
OIDC_JWKS_URL=https://auth.staging.example.com/realms/ontrackchain/protocol/openid-connect/certs
OIDC_CLIENT_ID=ontrackchain-web
OIDC_AUDIENCE=ontrackchain-api
OIDC_ORG_CLAIM=org
OIDC_PLAN_CLAIM=plan
OIDC_ROLE_CLAIM=otk_role
JWT_HS256_SECRET=__REAL_SECRET__
KEYCLOAK_ADMIN_PASSWORD=__REAL_SECRET__
KEYCLOAK_B2B_CLIENT_SECRET=__REAL_SECRET__
MFA_TOTP_SECRET=__REAL_SECRET__
MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false
ALERTMANAGER_WEBHOOK_BEARER_TOKEN=__REAL_SECRET__
COMPLIANCE_TRM_ENABLED=true
COMPLIANCE_TRM_SCREENING_URL=https://provider.example/screening
COMPLIANCE_TRM_API_KEY=__REAL_SECRET__
OPENSANCTIONS_API_KEY=__REAL_SECRET__
COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://example.com/eu-sanctions.xml?token=__REAL_SECRET__
INVESTIGATION_RPC_ENABLED=true
# manter vazio quando ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only
INVESTIGATION_RPC_PRIMARY_URL=
INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example
GRAFANA_ADMIN_PASSWORD=__REAL_SECRET__
ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live
ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only
```

Regras:

- não incluir aspas extras desnecessárias
- não incluir blocos markdown
- não incluir `export`
- não deixar placeholders `__FILL_*__`
- só manter `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` como placeholder quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false`
- quando `ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only`, manter `INVESTIGATION_RPC_PRIMARY_URL` vazio e preencher apenas `INVESTIGATION_RPC_FALLBACK_URL`
- incluir tambem as demais chaves presentes em [`.env.staging.example`](../.env.staging.example), mesmo quando nao aparecam no recorte acima

## Como Gerar o Conteúdo do Secret

Fluxo recomendado:

1. rodar localmente:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --mode baseline
```

1. preencher `.env.staging.private` em canal seguro
1. validar localmente:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --mode baseline \
  --validate
```

1. copiar o conteúdo final do `.env.staging.private`
1. colar esse conteúdo em `STAGING_WINDOW_PRIVATE_ENV`

Para a trilha de `Render full-stack`, alinhe em paralelo os segredos `sync: false` do painel com [render-staging-blueprint.md](render-staging-blueprint.md). O `GitHub Environment` governa a janela séria via workflow; o painel do Render governa o runtime hospedado.

## Primeiro Disparo Recomendado

No GitHub Actions:

Antes de abrir `Actions`, validar o handoff e gerar o packet operacional com:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-YYYY-MM-DD-a"
```

1. abrir `Actions`
2. escolher `Staging Serious Window`
3. clicar em `Run workflow`
4. informar:
   - `window_id`: `stg-YYYY-MM-DD-a`
   - `mode`: `baseline` ou `homologated`
   - `environment_name`: `staging-serious`

Resultado esperado:

- artifact `serious-staging-window-<janela>`
- `GITHUB_STEP_SUMMARY` com status geral, status de `validation`, `preflight` e `run`
- `checks`, `dossier`, `window packet`, `homologation` e, quando aplicável, os resumos do `oidc-readiness-bundle` e do `regulatory-readiness-bundle` anexados

Depois de baixar o artifact do workflow, sincronizar a camada executiva com:

```bash
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

Saida adicional esperada do pós-processamento:

- sign-off versionado em `docs/governance-weekly/cycles/<data>/`
- `go/no-go decision packet` versionado em `docs/governance-weekly/cycles/<data>/`
- sincronizacao do registro semanal e do board operacional global

## Critérios de Go/No-Go

Go:

- `status=ok` no payload consolidado
- `validation.status=ok`
- `preflight.status=ok`
- `run.status=ok`
- artifact `serious-staging-window-<janela>` preservado

No-Go:

- secret ausente
- payload JSON inválido
- qualquer status `failed`
- artifact ausente ou incompleto

## Falhas Comuns

### Secret vazio ou ausente

Sintoma:

- o workflow falha antes de materializar `.env.staging.private`

Ação:

- revisar o environment selecionado
- confirmar se o secret foi cadastrado naquele environment, e não apenas em nível de repositório

### Placeholder remanescente

Sintoma:

- `validation.status=failed`

Ação:

- regenerar ou revisar `.env.staging.private`
- rodar `prepare_staging_window.py --validate` localmente antes do próximo disparo

### Provider não homologado

Sintoma:

- `preflight.status=failed` ou `run.status=failed`

Ação:

- corrigir credenciais, URLs ou modo esperado
- não reexecutar em loop sem registrar a causa

## Evidência para Governança

Na governança semanal, registrar:

- nome do environment usado
- `window_id`
- artifact `serious-staging-window-<janela>`
- paths do `window packet`, `checks`, `homologation`, `dossier`, do `oidc-readiness-bundle.md` quando o escopo incluir `P0-01` e do `regulatory-readiness-bundle.md` quando o escopo incluir `P0-02/P0-03`
- bloqueios externos encontrados

## Suposicoes

- o repositório usará `staging-serious` como environment inicial
- o secret `STAGING_WINDOW_PRIVATE_ENV` continuará sendo o contrato oficial do workflow
- o time prefere approvals no `GitHub Environment` em vez de secrets dispersos por job
