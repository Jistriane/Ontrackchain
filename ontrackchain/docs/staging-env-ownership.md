# Ownership do `.env.staging`

## Objetivo

Nomear owners explicitos para cada classe de placeholder `__FILL_*__` do arquivo privado de `staging`, reduzindo ambiguidade operacional antes dos preflights e da homologacao externa.

Este documento complementa:

- [`.env.staging.example`](../.env.staging.example)
- [Variaveis de Ambiente](environment-variables.md)
- [Deploy e Staging](deploy-and-staging.md)
- [Owners e SLAs Operacionais](operational-ownership-and-slas.md)
- [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md)
- [Governanca Semanal](./governance-weekly/README.md)

## Escopo Canonico

Use este documento para:

- atribuir ownership nominal aos placeholders e grupos de handoff do `.env.staging.private`
- registrar `Data` e `Status` humanos que bloqueiam ou liberam o preflight da janela
- cruzar owners do ambiente com os dominios operacionais executados no war room
- servir como base de handoff para a `run sheet`, `bridge quick-fill` e `decision packet` do ciclo ativo

Nao use este documento como fonte primaria para:

- coordenar war room, tracking ou decisao `go/no-go`: use os artefatos vivos em `docs/governance-weekly/`
- use o indice do ciclo ativo em [Governanca Semanal](./governance-weekly/README.md) para tracking e decisao corrente
- preencher rapidamente contatos, canais e bridges da janela corrente: use a `run sheet` datada e a `bridge quick-fill` do ciclo ativo

## Papel Especifico

Este documento nao redefine a taxonomia geral de ownership do projeto.

Ele especializa, para a janela de staging, a taxonomia canonica publicada em [Owners e SLAs Operacionais](./operational-ownership-and-slas.md), cobrindo apenas:

- `placeholder/grupo -> owner da janela`
- apoio e sign-off no escopo do `.env.staging.private`
- `Data` e `Status` humanos do handoff
- bloqueios que impedem `prepare`, `preflight` ou `run` da janela

Se houver conflito entre este arquivo e a taxonomia de dominios do documento canonico de ownership operacional, corrigir este arquivo e nao o contrario, exceto quando a mudanca for estrutural para todo o projeto.

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
| `__FILL_STAGING_KEYCLOAK_ADMIN_CLIENT_SECRET__` | `Backend/Auth` | `Security` | secret do client tecnico usado pelo `auth-service` para consultar a Admin API do Keycloak |
| `__FILL_STAGING_JWT_HS256_SECRET__` | `Backend/Auth` | `Security` | secret HS256 nao-dev com rotacao planejada |
| `__FILL_STAGING_MFA_TOTP_SECRET__` | `Backend/Auth` | `Security` | secret TOTP nao-dev ou decisao formal de desuso no ambiente |
| `__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__` | `Backend/Auth` | `Security` | token OIDC administrativo temporario e controlado para evidenciar `legal_report` homologado |
| `__FILL_STAGING_RPC_PRIMARY_URL__` | `Backend Core` | `Platform/DBA` | endpoint RPC primario valido com owner e limite conhecido |
| `__FILL_STAGING_RPC_FALLBACK_URL__` | `Backend Core` | `Platform/DBA` | endpoint fallback distinto do primario e validado |
| `__FILL_STAGING_ALERTMANAGER_WEBHOOK_BEARER_TOKEN__` | `Platform/SRE` | `Security` | token configurado entre `Alertmanager` e `monitoring-api` |
| `__FILL_STAGING_TRM_SCREENING_URL__` | `Compliance/Backend` | `Security` | URL oficial do provider AML/KYT homologada para a janela |
| `__FILL_STAGING_TRM_API_KEY__` | `Compliance/Backend` | `Security` | API key do provider com trilha de provisionamento |
| `__FILL_STAGING_OPENSANCTIONS_API_KEY__` | `Compliance/Backend` | `Security` | API key do OpenSanctions validada para sync enriquecido das listas |
| `__FILL_STAGING_COMPLIANCE_EU_SANCTIONS_SOURCE_URL__` | `Compliance/Backend` | `Security` | URL XML tokenizada da lista da UE obtida no portal oficial e validada para a janela |
| `__FILL_STAGING_GRAFANA_ADMIN_PASSWORD__` | `Platform/SRE` | `Security` | senha admin nao-dev armazenada em secret manager |

## Agrupamento por Dominio

### Auth/OIDC

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `KEYCLOAK_ADMIN_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN`

Owner principal herdado da taxonomia canonica:

- `Backend/Auth`

Sign-off recomendado na janela:

- `Security`

### Compliance/AML

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `OPENSANCTIONS_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Owner principal herdado da taxonomia canonica:

- `Compliance/Backend`

Sign-off recomendado na janela:

- `Security`

Observacao:

- `OPENSANCTIONS_API_KEY` passa a ser obrigatoria quando o escopo incluir o worker de sancoes com enriquecimento via OpenSanctions ou quando o blueprint `full-stack` do Render for usado como baseline serio de compliance

### Investigation/RPC

- `INVESTIGATION_RPC_PRIMARY_URL` quando `ONTRACKCHAIN_EXPECT_RPC_MODE=live`
- `INVESTIGATION_RPC_FALLBACK_URL`

Owner principal herdado da taxonomia canonica:

- `Backend Core`

Sign-off recomendado na janela:

- `Platform/DBA`

Observacao:

- quando a janela for aprovada em modo `fallback_only`, o owner de `Backend Core` deve preencher apenas `INVESTIGATION_RPC_FALLBACK_URL` e manter `INVESTIGATION_RPC_PRIMARY_URL` vazio

### Platform/Operations

- `POSTGRES_PASSWORD`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Owner principal herdado da taxonomia canonica:

- `Platform/SRE` ou `Platform/DBA` conforme o item

Sign-off recomendado na janela:

- `Security`

## Sequencia Recomendada de Desbloqueio

Estado real mais recente, em `2026-07-19`:

- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-02` falhou
- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-03` falhou
- `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-04` falhou
- o bloqueio dominante atual foi a combinacao de `.env.staging.private` ausente com `Compliance/AML.date/status` ainda em `pending`

1. preencher o `Gate Agregado da Janela` e os placeholders transversais na folha manual e nos artefatos vivos
2. destravar `Platform/Operations`
3. destravar `Auth/OIDC`
4. destravar `Investigation/RPC`
5. destravar `Compliance/AML`
6. rerodar o gate agregado da janela

Sequencia tecnica correspondente:

1. copiar [`.env.staging.example`](../.env.staging.example) para `.env.staging.private`
2. distribuir os placeholders por owner desta matriz
3. executar `python3 scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md`
4. gerar um pacote redigido da janela com `python3 scripts/render_staging_window_packet.py --window-id <janela> --output-file artifacts/staging/window-packet-<janela>.md`
5. preencher os valores reais em canal seguro
6. executar `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-02 PRIVATE_ENV_FILE=.env.staging.private OWNERSHIP_FILE=docs/staging-env-ownership.md` quando houver `AML/KYT live`
7. executar `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-03 PRIVATE_ENV_FILE=.env.staging.private OWNERSHIP_FILE=docs/staging-env-ownership.md` quando houver feed UE real
8. executar `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-04 PRIVATE_ENV_FILE=.env.staging.private OWNERSHIP_FILE=docs/staging-env-ownership.md` quando a janela quiser consolidar o bundle regulatorio
9. rerodar o gate agregado com `make gate-p0-05-serious-window WINDOW_ID=<janela> MODE=baseline PRIVATE_ENV_FILE=.env.staging.private GOVERNANCE_WEEKLY_DIR=docs/governance-weekly`
10. seguir para `python3 scripts/run_staging_window.py --window-id <janela> --private-env-file .env.staging.private` apenas se o gate agregado retornar `status=ok`
11. anexar o `window packet`, os JSONs em `artifacts/staging/checks/`, a homologacao, o dossier final e, quando houver `P0-01`, o resumo `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md`, alem do resumo `artifacts/staging/dossiers/<janela>-regulatory-readiness-bundle.md` quando houver `P0-02/P0-03`, ao sign-off da janela

Atalho recomendado para o gate agregado:

```bash
make gate-p0-05-serious-window \
  WINDOW_ID=stg-YYYY-MM-DD-a \
  MODE=baseline \
  PRIVATE_ENV_FILE=.env.staging.private \
  GOVERNANCE_WEEKLY_DIR=docs/governance-weekly
```

Atalho recomendado para execucao ponta a ponta, somente depois do gate agregado verde:

```bash
python3 scripts/run_staging_window.py \
  --window-id stg-YYYY-MM-DD-a \
  --private-env-file .env.staging.private
```

O gate agregado acima deve ser a ultima verificacao antes da execucao ponta a ponta.

O runner acima encapsula, em ordem, os gates de `ownership coverage`, `window packet`, placeholders, handoff, checks regulatórios aplicáveis (`p0-02`, `p0-03`, `p0-04` quando o `.env` privado já sinalizar escopo real), `preflight_oidc_serious_env.py`, `preflight_external_integrations.py`, `run_oidc_readiness_bundle.py`, o resumo markdown do bundle OIDC, `run_regulatory_readiness_bundle.py`, o resumo markdown do bundle regulatório, `homologation_external_evidence.py` e `build_staging_release_dossier.py`.

Na pratica, os checks regulatórios acima devem ser tratados como precondicao humana e tecnica do restante da janela. Se qualquer um deles falhar por `.env.staging.private` ausente ou por `Compliance/AML` ainda em `pending`, a execucao deve parar antes do runtime real.

## Registro de Handoff

Use o checker abaixo antes dos preflights:

```bash
python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md
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
| Compliance/AML | `Compliance/Backend` | `pending` | `pending` | confirmar URL, credencial TRM, `OPENSANCTIONS_API_KEY` e, se necessario, a URL XML tokenizada da UE para a janela |
| Investigation/RPC | `Backend Core` | `pending` | `pending` | confirmar primario/fallback e limites |
| Platform/Operations | `Platform/SRE` | `pending` | `pending` | confirmar senha DB, Grafana e webhook |
