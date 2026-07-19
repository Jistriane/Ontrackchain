# Guia de Execucao Assistida - `P0-02` AML/KYT live

## Objetivo

Concentrar em um unico artefato o rito minimo para mover `P0-02` de `blocked` para `in_progress`, executando antes o readiness check canônico, depois a homologacao `AML/KYT live` com evidencia preservada e devolvendo a trilha para a governanca semanal sem drift.

## Quando Usar

- quando a credencial real do provider AML/KYT ja estiver disponivel fora do repositório
- quando a janela seria incluir `P0-02` isolado ou combinado com `P0-03`
- quando o owner `Compliance/Backend` estiver nominalmente confirmado em `docs/staging-env-ownership.md`

## Fontes Canonicas

- [Runbook 16A](../../runbooks.md)
- [Project Release Gates](../../project-release-gates.md)
- [Project Operational Execution Board](../../project-operational-execution-board.md)
- [Staging Env Ownership](../../staging-env-ownership.md)
- [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md)

## Artefato Complementar

- [Run Sheet Operacional de `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_RUN_SHEET.md)

## Estado Inicial Esperado

- `P0-02` esta `blocked` no estado local atual ate o readiness check ficar verde
- o baseline local continua com `COMPLIANCE_TRM_ENABLED=false`
- nenhuma credencial real aparece em arquivo versionado
- a janela nao pode promover maturidade sem checker verde e artefato anexavel
- a execucao real local de `2026-07-19` confirmou o bloqueio atual por `.env.staging.private` ausente e `Compliance/AML.date/status` pendentes

## Requisitos Minimos

### Owner e Handoff

- grupo: `Compliance/AML`
- owner esperado: `Compliance/Backend`
- apoio: `Security`
- atualizar somente `date` e `status` em `docs/staging-env-ownership.md`

### Segredos Obrigatorios

Preencher apenas em `.env.staging.private` local ou no ambiente serio equivalente:

- `COMPLIANCE_TRM_ENABLED=true`
- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_TRM_API_KEY_HEADER`
- `COMPLIANCE_TRM_API_KEY_PREFIX`
- `COMPLIANCE_TRM_TIMEOUT_MS`
- `COMPLIANCE_TRM_MAX_RETRIES`

### Variaveis de Shell Recomendadas

```bash
export ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live
export ONTRACKCHAIN_EXPECT_RPC_MODE=disabled
```

## Sequencia de Execucao Segura

### Gate Canônico Recomendado

Antes do gate, validar se handoff + secrets minimos da trilha estao prontos:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make check-regulatory-window-readiness \
  REGULATORY_SCOPE=p0-02 \
  PRIVATE_ENV_FILE=.env.staging.private \
  OWNERSHIP_FILE=docs/staging-env-ownership.md
```

Esperado:

- `readiness.readiness_status=ready_for_execution`
- grupo `Compliance/AML` sem `pending`
- `COMPLIANCE_TRM_ENABLED=true` e credenciais TRM sem placeholder

Para a execucao local coordenada de preflight + checker AML/KYT + smoke, preferir:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-02-aml-live \
  PRIVATE_ENV_FILE=.env.staging.private \
  COMPLIANCE_INTERNAL_BASE_URL=http://localhost:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Esse alvo preserva um `request_id` unico entre o gate AML/KYT e a trilha subsequente de homologacao, reduzindo drift de correlacao no dossier.

### Workflow Hospedado Recomendado

Quando houver GitHub Environment aprovado com `STAGING_WINDOW_PRIVATE_ENV`, preferir a execucao hospedada:

```text
GitHub -> Actions -> P0-02 AML Live Gate -> Run workflow
  window_id: <window_id>
  environment_name: staging-serious
  internal_base_url: http://localhost:8002
  public_base_url: http://localhost:8080
  run_homologation: true
```

Esperado:

- materializacao efemera de `.env.staging.private`
- reset explicito da stack residual de compliance no runner antes do gate
- execucao de `make gate-p0-02-aml-live` com `request_id` correlacionavel
- opcionalmente, execucao de `homologation_external_evidence.py --mode compliance`
- coleta de `docker compose ps/logs` em `ci-artifacts/`
- upload de `ci-artifacts/` e `artifacts/homologation/`
- `run_url` registravel no run sheet operacional

### 1. Preflight Externo

Executar antes de qualquer chamada real de homologacao:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/preflight_external_integrations.py
```

Esperado:

- `status=ok`
- `kind=external_integrations_preflight`
- `readiness.readiness_status=prepared`
- modo de compliance coerente com `live`
- URL e credencial reconhecidas como presentes no ambiente privado

### 2. Gate Leve do Provider

Executar o gate canonico de runtime:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
export REQUEST_ID=<compliance_request_id>
make gate-p0-02-aml-live \
  REQUEST_ID=$REQUEST_ID \
  PRIVATE_ENV_FILE=.env.staging.private \
  COMPLIANCE_INTERNAL_BASE_URL=http://compliance-api:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Esperado:

- readiness interna `ready=true`
- `details.operating_mode=live`
- catalogo publico coerente com `kyc_wallet.provider=trm_labs`
- correlacao estruturada do checker com `provider_converges_live=true`
- artefatos em `ci-artifacts/p0-02/` ou `OUTPUT_DIR` equivalente, incluindo `p0-02-compliance-runtime.json` e `p0-02-gate-summary.json`
- o JSON principal deve expor `kind=compliance_provider_runtime_check`
- o JSON principal deve expor `request_id`, `correlation.provider_converges_live=true` e `readiness.readiness_status=prepared_for_homologation`
- preservar o `request_id` do checker para correlacao posterior com homologacao externa, bundle regulatorio e dossier

### 3. Smoke Runtime

Executar uma verificacao funcional curta:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/smoke_runtime.py
```

Esperado:

- checks de compliance relevantes verdes
- nenhuma degradacao silenciosa nao documentada

### 4. Evidencia Externa de Homologacao

Executar a coleta formal da trilha de homologacao:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
python3 scripts/homologation_external_evidence.py --mode compliance
```

Esperado:

- JSON em `artifacts/homologation/`
- manifesto correspondente `.manifest.json`
- `request_id` correlacionavel entre readiness, catalogo, `risk-check` e bundle `/audit`
- sempre que possivel, reutilizar ou registrar explicitamente o mesmo `request_id` do checker AML/KYT para facilitar reconciliacao no dossier

### 5. Bundle Regulatório Quando `P0-03` Tambem Estiver no Escopo

Se a mesma janela incluir feed UE real, preferir consolidar:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-04-regulatory-bundle \
  WINDOW_ID=<window_id> \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks \
  DOSSIERS_DIR=artifacts/staging/dossiers \
  COMPLIANCE_INTERNAL_BASE_URL=http://compliance-api:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

Esperado:

- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- o JSON do bundle deve explicitar `readiness.compliance_runtime.readiness_status` e `readiness.regulatory_bundle.readiness_status`
- o markdown do bundle deve refletir readiness executivo, bloqueadores e `next_action` coerentes com a trilha `P0-02`

### 6. Reconciliar Governanca Semanal

Depois que os artefatos existirem, sincronizar a janela:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Esperado:

- reducao objetiva de bloqueios no snapshot e delta
- artefatos da janela em `docs/governance-weekly/generated/windows/<window_id>/`
- consolidado pronto para gate, Slack e trilha executiva

## Artefatos Minimos Exigidos

- saida verde do `preflight_external_integrations.py`
- gate verde de `make check-compliance-provider-runtime`
- `steps.compliance_provider_runtime.correlation.provider_converges_live=true`
- diagnosticos do runner (`docker compose ps/logs`) preservados quando a execucao ocorrer via GitHub Actions
- artefato JSON de homologacao em `artifacts/homologation/`
- bundle `/audit` correlacionado pelo mesmo `request_id`
- bundle regulatorio preservando `steps.compliance_provider_runtime.request_id`
- quando aplicavel, `regulatory-readiness-bundle.json` e resumo `.md`
- snapshot/governance atualizados apos `refresh-staging-war-room-governance-local`

## Criterio de Promocao de Status

Mover `P0-02` de `blocked` para `in_progress` somente quando:

- o gate `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-02 ...` estiver verde
- a credencial real do provider estiver disponivel
- o owner `Compliance/AML` estiver confirmado
- a janela de homologacao estiver reservada

Mover `P0-02` para `ready_for_validation` somente quando:

- o gate `check-compliance-provider-runtime` estiver verde
- a homologacao externa tiver gerado artefato anexavel
- os artefatos estiverem preservados em `artifacts/`
- a governanca semanal tiver sido reprocessada com os paths reais

Considerar `P0-02` fechado somente quando:

- readiness interna e catalogo publico convergirem em `live`
- a evidencia for revisada por humano
- o accountable aceitar formalmente a janela

## Falhas Aceitaveis

- indisponibilidade controlada do provider durante a janela
- `provider_status=degraded` com motivo explicito
- falha auditada com `request_id`

Nesses casos:

- marcar a homologacao como nao concluida
- nao promover maturidade
- preservar artefatos para reexecucao

## Anti-Patterns

- nao preencher segredos em documentos versionados
- nao promover `P0-02` apenas porque o codigo e o checker existem
- nao registrar `done` sem artefato anexavel
- nao atualizar scorecard antes de revisao humana e aceite formal

## Definicao de Pronto Operacional

`P0-02` esta pronto para aprovacao somente se houver:

- credencial real validada no ambiente correto
- checker verde
- homologacao externa preservada
- governanca sincronizada
- aceite humano formal
