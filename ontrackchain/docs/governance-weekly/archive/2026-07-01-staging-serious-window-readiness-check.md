# Readiness Check da Janela Seria — 2026-07-01

## Objetivo

Registrar o resultado da pre-validacao segura executada sobre `.env.staging.private` antes do disparo real da janela seria, sem expor secrets.

## Execucao

- comando executado:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-2026-07-06-precheck \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

- resultado geral: `failed`
- `validation.status`: `failed`
- `preflight.status`: `skipped`
- motivo do skip do preflight: `validation_failed`

## Leitura Executiva

- a janela ainda nao esta pronta para execucao local ou oficial
- o bloqueio atual nao esta no runtime da aplicacao, e sim na prontidao operacional do pacote de staging
- a leitura operacional correta deste snapshot e `pending_execucao` com `no-go` ativo
- existem dois grupos distintos de bloqueio:
  - handoff humano ainda nao formalizado
  - placeholders criticos ainda nao preenchidos no `.env.staging.private`

## Bloqueadores Atuais

### 1. Handoff operacional ainda pendente

O checker `check_staging_env_handoff.py` falhou porque os grupos obrigatorios ainda nao possuem `Data` e `Status` aprovados:

- `Auth/OIDC`
- `Compliance/AML`
- `Investigation/RPC`
- `Platform/Operations`

Observacao:

- o `owner` nominal foi scaffoldado em `docs/staging-env-ownership.md`
- a janela continua bloqueada ate cada grupo preencher `Data` e `Status` com `reviewed`, `approved` ou `waived`

### 2. Placeholders criticos ainda nao preenchidos

O checker `check_staging_env_placeholders.py` identificou placeholders ainda abertos nestes segredos/URLs:

- `POSTGRES_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `GRAFANA_ADMIN_PASSWORD`

## Classificacao por Dominio

### Auth/OIDC

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`

### Compliance/AML

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

### Investigation/RPC

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

### Platform/Operations

- `POSTGRES_PASSWORD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

## Artefatos Gerados

- `artifacts/staging/checks/stg-2026-07-06-precheck-handoff.json`
- `artifacts/staging/checks/stg-2026-07-06-precheck-placeholders.json`
- `artifacts/staging/window-packet-stg-2026-07-06-precheck.md`

## Decisao Recomendada

- manter a janela em `no-go` ate o handoff operacional sair de `pending`
- nao executar `run-serious-window-local` nem `run_staging_window.py` com finalidade oficial enquanto os placeholders acima existirem
- usar este snapshot como checklist objetivo de provisionamento fora do repositório

## Proximo Artefato Operacional

Para destravar a janela sem ambiguidade, usar o checklist canônico por owner:

- [Ownership do `.env.staging`](../staging-env-ownership.md)
- [Folha de Preenchimento Manual `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-manual-fill-sheet.md)
- [Checklist de Provisionamento por Owner para Janela Seria](../staging-serious-window-owner-provisioning-checklist.md)
- [Matriz de Execucao por Owner para Janela Seria](../staging-serious-window-war-room-matrix.md)
- [War Room da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-war-room.md)
- [Tracking ao Vivo da Janela `stg-2026-07-06-a`](./2026-07-06-staging-serious-window-live-tracking.md)

Ordem recomendada:

1. `Gate Agregado da Janela` e placeholders transversais
2. `Platform/Operations`
3. `Auth/OIDC`
4. `Investigation/RPC`
5. `Compliance/AML`
6. atualizar `Data/Status` e checkpoints nos artefatos vivos
7. rerodar `prepare_staging_window.py --validate --preflight`
8. seguir para `run_staging_window.py` ou `run-serious-window-local` apenas se o gate agregado retornar `status=ok`
