# Ownership do `.env.staging`

## Objetivo

Nomear owners explicitos para cada classe de placeholder `__FILL_*__` do arquivo privado de `staging`, reduzindo ambiguidade operacional antes dos preflights e da homologacao externa.

Este documento complementa:

- [`.env.staging.example`](../.env.staging.example)
- [Variaveis de Ambiente](environment-variables.md)
- [Deploy e Staging](deploy-and-staging.md)
- [Owners e SLAs Operacionais](operational-ownership-and-slas.md)
- [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md)
- [Folha de Preenchimento Manual da Janela `stg-2026-07-06-a`](governance-weekly/2026-07-06-staging-serious-window-manual-fill-sheet.md)

## Escopo Canonico

Use este documento para:

- atribuir ownership nominal aos placeholders e grupos de handoff do `.env.staging.private`
- registrar `Data` e `Status` humanos que bloqueiam ou liberam o preflight da janela
- cruzar owners do ambiente com os dominios operacionais executados no war room

Nao use este documento como fonte primaria para:

- coordenar war room, tracking ou decisao `go/no-go`: use os artefatos vivos em `docs/governance-weekly/`
Refira-se a [Governanca Semanal](governance-weekly/) para tracking do ciclo atual.
- preencher rapidamente contatos, canais e bridges da janela corrente: use a [Folha de Preenchimento Manual da Janela `stg-2026-07-06-a`](governance-weekly/2026-07-06-staging-serious-window-manual-fill-sheet.md)

## Regra Geral

- nenhum placeholder `__FILL_*__` pode permanecer no arquivo privado antes do `check_staging_env_placeholders.py`
- nenhum secret critico pode ser preenchido sem owner explicito
- itens de `OIDC/Auth` exigem owner de `Backend/Auth` com apoio de `Security`
- itens de `AML/KYT` exigem owner de `Compliance/Backend` com apoio de `Security`
- itens de `RPC/Infra` exigem owner de `Backend Core` com apoio de `Platform/DBA`
- qualquer conflito de preenchimento deve ser resolvido antes da janela e registrado no gate de release

## Matriz de Ownership

| Placeholder / grupo | Owner primario | Apoio | Evidencia esperada |
| --- | --- | --- | --- |
| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `Security` | secret provisionado no vault ou canal controlado |
| `__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__` | `Backend/Auth` | `Security` | credencial admin nao-dev validada e armazenada com controle |
| `__FILL_STAGING_KEYCLOAK_B2B_CLIENT_SECRET__` | `Backend/Auth` | `Security` | client secret do IdP registrado e testado |
| `__FILL_STAGING_JWT_HS256_SECRET__` | `Backend/Auth` | `Security` | secret HS256 nao-dev com rotacao planejada |
| `__FILL_STAGING_MFA_TOTP_SECRET__` | `Backend/Auth` | `Security` | secret TOTP nao-dev ou decisao formal de desuso no ambiente |
| `__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__` | `Backend/Auth` | `Security` | token OIDC administrativo temporario e controlado para evidenciar `legal_report` homologado |
| `__FILL_STAGING_RPC_PRIMARY_URL__` | `Backend Core` | `Platform/DBA` | endpoint RPC primario valido com owner e limite conhecido |
| `__FILL_STAGING_RPC_FALLBACK_URL__` | `Backend Core` | `Platform/DBA` | endpoint fallback distinto do primario e validado |
| `__FILL_STAGING_ALERTMANAGER_WEBHOOK_BEARER_TOKEN__` | `Platform/SRE` | `Security` | token configurado entre `Alertmanager` e `monitoring-api` |
| `__FILL_STAGING_TRM_SCREENING_URL__` | `Compliance/Backend` | `Security` | URL oficial do provider AML/KYT homologada para a janela |
| `__FILL_STAGING_TRM_API_KEY__` | `Compliance/Backend` | `Security` | API key do provider com trilha de provisionamento |
| `__FILL_STAGING_COMPLIANCE_EU_SANCTIONS_SOURCE_URL__` | `Compliance/Backend` | `Security` | URL XML tokenizada da lista da UE obtida no portal oficial e validada para a janela |
| `__FILL_STAGING_GRAFANA_ADMIN_PASSWORD__` | `Platform/SRE` | `Security` | senha admin nao-dev armazenada em secret manager |

## Agrupamento por Dominio

### Auth/OIDC

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN`

Owner principal:

- `Backend/Auth`

Sign-off recomendado:

- `Security`

### Compliance/AML

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Owner principal:

- `Compliance/Backend`

Sign-off recomendado:

- `Security`

### Investigation/RPC

- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

Owner principal:

- `Backend Core`

Sign-off recomendado:

- `Platform/DBA`

### Platform/Operations

- `POSTGRES_PASSWORD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Owner principal:

- `Platform/SRE` ou `Platform/DBA` conforme o item

Sign-off recomendado:

- `Security`

## Sequencia Recomendada de Desbloqueio

1. preencher o `Gate Agregado da Janela` e os placeholders transversais na folha manual e nos artefatos vivos
2. destravar `Platform/Operations`
3. destravar `Auth/OIDC`
4. destravar `Investigation/RPC`
5. destravar `Compliance/AML`
6. rerodar o gate agregado da janela

Sequencia tecnica correspondente:

1. copiar [`.env.staging.example`](../.env.staging.example) para `.env.staging.private`
2. distribuir os placeholders por owner desta matriz
3. executar `python scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md`
4. gerar um pacote redigido da janela com `python scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md`
5. preencher os valores reais em canal seguro
6. rerodar o gate agregado com `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline --private-env-file .env.staging.private --validate --preflight`
7. seguir para `python scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` apenas se o gate agregado retornar `status=ok`
8. anexar o `window packet`, os JSONs em `artifacts/staging/checks/`, a homologacao e o dossier final ao sign-off da janela

Atalho recomendado para o gate agregado:

```bash
python scripts/prepare_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --mode baseline \
  --private-env-file .env.staging.private \
  --validate \
  --preflight
```

Atalho recomendado para execucao ponta a ponta, somente depois do gate agregado verde:

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

O gate agregado acima deve ser a ultima verificacao antes da execucao ponta a ponta.

O runner acima encapsula, em ordem, os gates de `ownership coverage`, `window packet`, placeholders, handoff, `preflight_oidc_serious_env.py`, `preflight_external_integrations.py`, `homologation_external_evidence.py` e `build_staging_release_dossier.py`.

## Registro de Handoff

Use o checker abaixo antes dos preflights:

```bash
python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
```

Status aceitos:

- `approved`: owner preencheu ou confirmou os valores da janela
- `reviewed`: owner revisou a janela e manteve o valor/integração vigente
- `waived`: excecao documentada; exige observacao nao-pendente

Enquanto qualquer linha permanecer com `pending`, o checker deve falhar e a janela nao deve seguir para `preflight_oidc_serious_env.py`, `preflight_external_integrations.py` ou `homologation_external_evidence.py`.

Scaffold controlado atual:

- a coluna `Owner` pode ser pre-preenchida com o responsavel nominal do dominio
- as colunas `Data` e `Status` continuam bloqueadoras ate confirmacao humana da janela
- nao promover `reviewed`, `approved` ou `waived` sem evidencias reais do owner correspondente
- preencher primeiro facilitador, canal principal, bridge principal e checkpoint na folha manual antes de avancar nos dominios
- usar a [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md) durante o war room da janela para coordenar dependencias, comandos e escalacoes

| Grupo | Owner | Data | Status | Observacoes |
| --- | --- | --- | --- | --- |
| Auth/OIDC | `Backend/Auth` | `pending` | `pending` | preencher secrets, claims finais e token OIDC de homologacao quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true` |
| Compliance/AML | `Compliance/Backend` | `pending` | `pending` | confirmar URL, credencial TRM e, se necessario, a URL XML tokenizada da UE para a janela |
| Investigation/RPC | `Backend Core` | `pending` | `pending` | confirmar primario/fallback e limites |
| Platform/Operations | `Platform/SRE` | `pending` | `pending` | confirmar senha DB, Grafana e webhook |
