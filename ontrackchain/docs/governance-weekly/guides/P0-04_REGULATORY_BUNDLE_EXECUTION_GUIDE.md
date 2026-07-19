# Guia de Execucao Assistida - `P0-04` Bundle Regulatorio Oficial

## Objetivo

Consolidar em um unico artefato o gate oficial de `P0-04`, promovendo o bundle regulatorio apenas quando `P0-02` e `P0-03` estiverem simultaneamente no escopo, verdes e coerentes por correlacao auditavel.

## Quando Usar

- quando a janela seria combinar `AML/KYT live` e feed UE real na mesma execucao
- quando `P0-02` e `P0-03` ja tiverem artefatos anexaveis e owner nominal confirmado
- quando o bundle regulatorio for usado como evidencia executiva de promocao

Estado local atual:

- `P0-04` esta `blocked`
- a execucao real local de `2026-07-19` confirmou que o bloqueio dominante atual ainda e anterior ao bundle: `.env.staging.private` ausente e `Compliance/AML.date/status` pendentes

## Contrato Canonico

- `readiness.compliance_runtime.readiness_status` deve refletir a trilha `P0-02`
- `readiness.eu_window.readiness_status` deve refletir a trilha `P0-03`
- `readiness.regulatory_bundle.readiness_status` so pode ser `ready_for_validation` se:
  - `P0-02` estiver `ready_for_validation`
  - `P0-03` estiver `ready_for_validation`
  - `steps.compliance_provider_runtime.request_id` estiver presente
  - `steps.compliance_provider_runtime.correlation.provider_converges_live` for `true`
  - `steps.eu_sanctions_window.request_id` estiver presente
  - `steps.eu_sanctions_window.correlation.eu_window_converges_ready` for `true`

## Regras de Promocao

- se qualquer trilha estiver `blocked`, o bundle oficial deve ficar `blocked`
- se apenas uma das trilhas estiver no escopo, o bundle oficial deve ficar `ready`, nunca `ready_for_validation`
- se as duas trilhas estiverem no escopo, mas houver incoerencia de correlacao, o bundle deve ficar `blocked`
- promover `ready_for_validation` somente quando a janela combinada provar as duas trilhas na mesma execucao

## Evidencias Minimas

- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- `steps.compliance_provider_runtime.output_file` referenciando um payload com `kind=compliance_provider_runtime_check`
- `steps.compliance_provider_runtime.output_file` referenciando um payload com `readiness.readiness_status=prepared_for_homologation`
- `steps.compliance_provider_runtime.request_id`
- `steps.compliance_provider_runtime.correlation.provider_converges_live=true`
- `steps.eu_sanctions_window.output_file` referenciando um payload com `kind=eu_sanctions_window_run`
- `steps.eu_sanctions_window.output_file` referenciando um payload com `readiness.readiness_status=ready_for_validation`
- `steps.eu_sanctions_window.request_id`
- `steps.eu_sanctions_window.correlation.expected_source_url`
- `steps.eu_sanctions_window.correlation.observed_source_url`
- `steps.eu_sanctions_window.correlation.source_url_matches_expected=true`
- `steps.eu_sanctions_window.correlation.override_tokenized=true`
- `steps.eu_sanctions_window.correlation.persisted_status_active=true`
- `steps.eu_sanctions_window.correlation.last_sync_status_success=true`
- `steps.eu_sanctions_window.correlation.eu_window_converges_ready=true`

## Gate Canônico Recomendado

Antes do gate, validar se a mesma janela ja pode sustentar `P0-02 + P0-03`:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make check-regulatory-window-readiness \
  REGULATORY_SCOPE=p0-04 \
  PRIVATE_ENV_FILE=.env.staging.private \
  OWNERSHIP_FILE=docs/staging-env-ownership.md
```

Esperado:

- `readiness.readiness_status=ready_for_execution`
- grupo `Compliance/AML` sem `pending`
- segredos TRM preenchidos
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada

Para a execucao local coordenada de preflight + bundle JSON + resumo markdown, preferir:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make gate-p0-04-regulatory-bundle \
  WINDOW_ID=<window_id> \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks \
  DOSSIERS_DIR=artifacts/staging/dossiers \
  COMPLIANCE_INTERNAL_BASE_URL=http://localhost:8002 \
  COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080
```

## Workflow Hospedado Recomendado

Quando houver GitHub Environment aprovado com `STAGING_WINDOW_PRIVATE_ENV`, preferir a execucao hospedada:

```text
GitHub -> Actions -> P0-04 Regulatory Bundle Gate -> Run workflow
  window_id: <window_id>
  environment_name: staging-serious
  checks_dir: artifacts/staging/checks
  dossiers_dir: artifacts/staging/dossiers
  internal_base_url: http://localhost:8002
  public_base_url: http://localhost:8080
```

Esperado:

- materializacao efemera de `.env.staging.private`
- correlacao explicita de `request_id` para as trilhas `P0-02` e `P0-03` dentro da mesma run hospedada
- execucao de `make gate-p0-04-regulatory-bundle`
- upload do JSON e do resumo markdown do bundle regulatorio
- `run_url` registravel na trilha executiva/war room

## Anti-Patterns

- nao promover `P0-04` so porque o `status` bruto do bundle ficou `ok`
- nao aceitar `preflight` verde sem `kind=external_integrations_preflight` e `readiness.readiness_status=prepared`
- nao aceitar janela parcial como bundle oficial
- nao aceitar feed UE verde sem convergencia explicita de `source_url`
- nao aceitar `AML/KYT live` sem `request_id` preservado no step canônico

## Definicao de Pronto Operacional

`P0-04` esta pronto para validacao somente quando:

- `P0-02` e `P0-03` estiverem ambos no escopo da mesma janela
- o bundle regulatorio estiver em `readiness.regulatory_bundle=ready_for_validation`
- o dossier e a governanca semanal refletirem o mesmo estado executivo
- houver aceite humano formal sobre os artefatos consolidados

Quando o gate for executado com `OUTPUT_DIR`, preserve tambem `p0-04-gate-summary.json` como marcador explicito de que o bundle foi gerado para revisao manual e nao equivale, por si so, a readiness oficial.
