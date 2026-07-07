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

## Workflow Alvo

Workflow canônico:

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

## Formato do Secret

O valor deve ser salvo no GitHub exatamente como seria escrito no arquivo:

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
COMPLIANCE_TRM_ENABLED=true
COMPLIANCE_TRM_SCREENING_URL=https://provider.example/screening
COMPLIANCE_TRM_API_KEY=__REAL_SECRET__
INVESTIGATION_RPC_ENABLED=true
INVESTIGATION_RPC_PRIMARY_URL=https://rpc-primary.example
INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example
ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live
ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only
```

Regras:

- não incluir aspas extras desnecessárias
- não incluir blocos markdown
- não incluir `export`
- não deixar placeholders `__FILL_*__`
- só manter `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` como placeholder quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false`

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

## Primeiro Disparo Recomendado

No GitHub Actions:

Antes de abrir `Actions`, validar o handoff e gerar o packet operacional com:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
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
