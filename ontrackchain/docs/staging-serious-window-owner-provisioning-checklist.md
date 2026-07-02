# Checklist de Provisionamento por Owner para Janela Seria

## Objetivo

Transformar os placeholders e handoffs pendentes da janela seria em um plano operacional executavel por dominio, sem expor secrets no repositório.

## Escopo Canonico

Use este documento para:

- provisionar owners, handoffs, placeholders e validacoes minimas por dominio
- destravar a janela do ponto de vista de responsabilidade operacional
- preparar o ambiente antes do gate agregado da janela

Nao use este documento como fonte primaria para:

- comandos completos de deploy e do runner consolidado: use [Deploy e Staging](deploy-and-staging.md)
- criterio formal de `go/no-go`: use [Gates de Release para Staging Serio](project-release-gates.md)
- coordenacao do primeiro rito com war room e sign-off: use [Primeiro Disparo Real da Janela Seria](first-serious-window-first-dispatch-runbook.md)

Use este checklist junto com:

- [Ownership do `.env.staging`](staging-env-ownership.md)
- [Deploy e Staging](deploy-and-staging.md)
- [Checklist Pre-Producao](pre-production-checklist.md)
- [Readiness Regulatorio](regulatory-readiness.md)

## Regras de Uso

- preencher valores reais apenas em canal seguro ou vault
- nunca colar secrets em issues, PRs, docs versionadas ou logs de CI
- so marcar um dominio como concluido quando:
  - os placeholders do dominio tiverem sido provisionados
  - `Data` e `Status` do dominio tiverem saído de `pending` no handoff
  - o comando de validacao do dominio tiver sido executado com evidencia anexavel

## Ordem Recomendada

1. `Platform/Operations`
2. `Auth/OIDC`
3. `Investigation/RPC`
4. `Compliance/AML`
5. rerodar o gate agregado da janela

Racional:

- `Platform/Operations` desbloqueia segredos-base da stack
- `Auth/OIDC` e prerequisito do trilho serio de identidade
- `Investigation/RPC` e `Compliance/AML` dependem de URLs/credenciais externas e podem exigir coordenacao com terceiros

## Dominios e Entregas

### 1. Platform/Operations

Owner nominal:

- `Platform/SRE`

Placeholders a provisionar:

- `POSTGRES_PASSWORD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Entregas esperadas:

- `.env.staging.private` atualizado em canal seguro
- `docs/staging-env-ownership.md` com `Data` preenchida
- `docs/staging-env-ownership.md` com `Status=reviewed|approved|waived`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
```

Evidencia anexavel:

- JSON do handoff sem `pending` para `Platform/Operations`
- JSON de placeholders sem ocorrencias desse dominio

### 2. Auth/OIDC

Owner nominal:

- `Backend/Auth`

Placeholders a provisionar:

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`

Condicional:

- `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` apenas quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`

Entregas esperadas:

- secrets OIDC nao-dev provisionados
- claims/issuer coerentes com o ambiente serio
- handoff de `Auth/OIDC` com `Data` e `Status` fora de `pending`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_oidc_serious_env.py
```

Evidencia anexavel:

- JSON do handoff sem `pending` para `Auth/OIDC`
- output verde do `preflight_oidc_serious_env.py`

### 3. Investigation/RPC

Owner nominal:

- `Backend Core`

Placeholders a provisionar:

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

Entregas esperadas:

- endpoints primario e fallback distintos e roteaveis
- modo esperado de RPC definido para a janela
- handoff de `Investigation/RPC` com `Data` e `Status` fora de `pending`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_external_integrations.py
```

Evidencia anexavel:

- JSON do handoff sem `pending` para `Investigation/RPC`
- output do preflight externo coerente com `ONTRACKCHAIN_EXPECT_RPC_MODE`

### 4. Compliance/AML

Owner nominal:

- `Compliance/Backend`

Placeholders a provisionar:

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Entregas esperadas:

- provider AML/KYT com credencial real e endpoint homologavel
- URL tokenizada da UE, quando `EU_CONSOLIDATED` estiver no escopo
- handoff de `Compliance/AML` com `Data` e `Status` fora de `pending`

Validacao minima:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
python scripts/check_staging_env_placeholders.py --file .env.staging.private
python scripts/preflight_external_integrations.py
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
```

Validacao adicional quando houver feed UE:

```bash
make run-eu-sanctions-window-local WINDOW_ID=stg-YYYY-MM-DD-a
```

Evidencia anexavel:

- JSON do handoff sem `pending` para `Compliance/AML`
- output verde do preflight externo
- output verde do runtime AML/KYT
- JSONs `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` quando a UE estiver no escopo

## Gate Final da Janela

Depois de todos os dominios acima:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

Se o resultado for `status=ok`, a janela fica elegivel para:

```bash
make run-serious-window-local WINDOW_ID=stg-YYYY-MM-DD-a MODE=baseline
```

## Criterio de No-Go

Nao seguir para `run-serious-window-local` quando qualquer um dos pontos abaixo continuar aberto:

- `docs/staging-env-ownership.md` com `Data` ou `Status` em `pending`
- `.env.staging.private` com qualquer `__FILL_*__` critico
- `preflight_oidc_serious_env.py` falhando
- `preflight_external_integrations.py` falhando
- `check-compliance-provider-runtime` falhando quando `AML/KYT live` estiver no escopo
- JSONs da janela UE ausentes quando `EU_CONSOLIDATED` estiver no escopo
