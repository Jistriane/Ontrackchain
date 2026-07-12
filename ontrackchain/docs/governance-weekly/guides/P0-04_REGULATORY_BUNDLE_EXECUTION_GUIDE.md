# Guia de Execucao Assistida - `P0-04` Bundle Regulatorio Oficial

## Objetivo

Consolidar em um unico artefato o gate oficial de `P0-04`, promovendo o bundle regulatorio apenas quando `P0-02` e `P0-03` estiverem simultaneamente no escopo, verdes e coerentes por correlacao auditavel.

## Quando Usar

- quando a janela seria combinar `AML/KYT live` e feed UE real na mesma execucao
- quando `P0-02` e `P0-03` ja tiverem artefatos anexaveis e owner nominal confirmado
- quando o bundle regulatorio for usado como evidencia executiva de promocao

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
- `steps.compliance_provider_runtime.request_id`
- `steps.compliance_provider_runtime.correlation.provider_converges_live=true`
- `steps.eu_sanctions_window.request_id`
- `steps.eu_sanctions_window.correlation.expected_source_url`
- `steps.eu_sanctions_window.correlation.observed_source_url`
- `steps.eu_sanctions_window.correlation.source_url_matches_expected=true`
- `steps.eu_sanctions_window.correlation.override_tokenized=true`
- `steps.eu_sanctions_window.correlation.persisted_status_active=true`
- `steps.eu_sanctions_window.correlation.last_sync_status_success=true`
- `steps.eu_sanctions_window.correlation.eu_window_converges_ready=true`

## Anti-Patterns

- nao promover `P0-04` so porque o `status` bruto do bundle ficou `ok`
- nao aceitar janela parcial como bundle oficial
- nao aceitar feed UE verde sem convergencia explicita de `source_url`
- nao aceitar `AML/KYT live` sem `request_id` preservado no step canônico

## Definicao de Pronto Operacional

`P0-04` esta pronto para validacao somente quando:

- `P0-02` e `P0-03` estiverem ambos no escopo da mesma janela
- o bundle regulatorio estiver em `readiness.regulatory_bundle=ready_for_validation`
- o dossier e a governanca semanal refletirem o mesmo estado executivo
- houver aceite humano formal sobre os artefatos consolidados
