# Matriz de Evidencias e Auditoria

## Objetivo

Relacionar os fluxos criticos do Ontrackchain com:

- eventos em `audit_logs`
- eventos em `evidence_trail`
- hashes e identificadores de correlacao
- artefatos operacionais e regulatorios
- validacao automatizada existente

## Estrutura da Evidencia

Toda evidencia relevante deve permitir correlacao entre:

- `request_id`
- `organization_id`
- ator (`user_id` ou `linked_user_id`)
- recurso afetado
- hash do artefato ou snapshot
- base regulatoria quando aplicavel

## Matriz Atual

Referência de `event_type` (fonte única):

- [Catálogo de Eventos — evidence_trail](./evidence-event-catalog.md)

| Fluxo | `audit_logs` | `evidence_trail` | Chaves | Artefato | Validacao |
| --- | --- | --- | --- | --- | --- |
| Investigation start | `case_started` | opcional por integracao | `request_id`, `case_id` | case | smoke |
| Investigation complete | `case_completed` | opcional por integracao | `request_id`, `case_id` | resultado final | smoke |
| Compliance risk check | `compliance_risk_checked` | nao obrigatoria | `request_id`, `address`, `chain` | payload do provider | smoke/tests |
| Sanctions check sem hit | `compliance_sanctions_checked` | `SANCTIONS_CHECKED` | `request_id`, `address`, `chain` | cache local | endpoint/testes |
| Sanctions check com hit | `compliance_sanctions_checked` | `SANCTIONS_HIT` | `request_id`, `address`, `chain`, `matched_lists` | hit cacheado | endpoint/testes |
| Due diligence manual | `compliance_due_diligence_checked` | nao obrigatoria | `request_id`, `address`, `chain`, `delivery_mode`, `counterparty_context` | contrato `manual_review_pending` + pacote regulatório DD no cockpit `/evidence` | endpoint/testes/UI |
| Source of funds manual | `compliance_source_of_funds_checked` | nao obrigatoria | `request_id`, `address`, `chain`, `delivery_mode`, `amount`, `purpose` | contrato `manual_review_pending` + pacote regulatório SoF no cockpit `/evidence` | endpoint/testes/UI |
| Export de pacote manual | `evidence_manual_review_package_exported` | `EVIDENCE_EXPORTED` | `request_id`, `report_id`, `scope_id`, `package_sha256`, `manual_review_action`, `filename` | manifesto canônico SHA-256 + checksum do bundle/workspace + `audit_logs` oficial | endpoint/testes/UI |
| Preventive block | `preventive_block_evaluated` | `BLOCK_*` conforme decisao | `request_id`, `block_id`, `evidence_hash` | `preventive_blocks` | testes/domain |
| Block lift | `preventive_block_lifted` | `BLOCK_LIFTED` | `block_id`, `lifted_at` | update controlado | endpoint |
| Counterparty onboarding | `counterparty_created` ou equivalente | `COUNTERPARTY_ONBOARDED` | `counterparty_id`, `document_number`, `evidence_hash` | `counterparties` | endpoint |
| ROS gerado | `coaf_report_generated` | `COAF_ROS_GENERATED` | `ros_id`, `report_id`, `file_hash_sha256` | `reports` + `ros_records` | endpoint/runtime |
| ROS aprovado | `coaf_report_approved` | `COAF_ROS_APPROVED` | `ros_id`, `status` | `ros_records` | endpoint/runtime |
| ROS rejeitado | `coaf_report_rejected` | `COAF_ROS_REJECTED` | `ros_id`, `rejection_reason` | `ros_records` | endpoint/runtime |
| ROS submetido manualmente | `coaf_report_submitted_manual` | `COAF_ROS_SUBMITTED_MANUAL` | `ros_id`, `coaf_protocol_number`, `coaf_receipt_hash` | `ros_records` | endpoint/runtime |
| Download de relatorio | `report_downloaded` | `REPORT_DOWNLOADED` quando integrado | `request_id`, `report_id`, `file_hash_sha256` | PDF | smoke/E2E |
| Export administrativo global | `operational_alerts_exported` | nao obrigatoria | `request_id`, `scope`, `format` | CSV/JSON | Playwright |
| Bundle de evidencia | `evidence_bundle_exported` | `EVIDENCE_EXPORTED` quando aplicavel | `request_id`, `report_id`, filtros | bundle JSON | UI/API |
| Negacao administrativa | `authorization_denied` | nao obrigatoria | `request_id`, `effective_role`, endpoint | tentativa negada | Playwright |

## IA (Jobs, Human Gate e Degradação)

| Fluxo | `audit_logs` | `evidence_trail` | Chaves | Artefato | Validacao |
| --- | --- | --- | --- | --- | --- |
| AI explain solicitado | `ai_explain_requested` (implementado) | `AI_EXPLAIN_GENERATED` | `request_id`, `case_id` | `ai_analysis_results` + evidência | testes |
| AI risk model avaliado | `ai_risk_model_assessed` (implementado) | (não obrigatório no baseline atual) | `request_id`, `address`, `chain` | `ai_analysis_results` | testes |
| AI confidence | `ai_confidence_generated` (implementado) | (não obrigatório no baseline atual) | `request_id`, `analysis_id` | `ai_analysis_results` | testes |
| AI graph analysis | `ai_graph_analysis_completed` (implementado) | (não obrigatório no baseline atual) | `request_id`, `address`, `chain` | `ai_analysis_results` | testes |
| AI graph narrator | `ai_graph_narrator_generated` (implementado) | (não obrigatório no baseline atual) | `request_id`, `address`, `chain` | `ai_analysis_results` | testes |
| AI case insights | `ai_case_insights_generated` (implementado) | `AI_CASE_INSIGHTS_GENERATED` | `request_id`, `case_id` | `ai_analysis_results` + evidência | testes |
| AI export autoridades | `ai_law_enforcement_export_generated` (implementado) | `AI_LAW_ENFORCEMENT_EXPORT_GENERATED` | `request_id`, `case_id`, `format` | `ai_analysis_results` + evidência | testes |
| AI THEMIS | `ai_themis_case_intelligence_generated` (implementado) | `AI_THEMIS_CASE_INTELLIGENCE_GENERATED` | `request_id`, `case_id` | `ai_analysis_results` + evidência | testes |

### IA (Job assíncrono — proposto)

| Fluxo | `audit_logs` | `evidence_trail` | Chaves | Artefato | Validacao |
| --- | --- | --- | --- | --- | --- |
| AI job enfileirado | `ai_job_queued` (implementado) | opcional | `request_id`, `job_id`, `analysis_type` | job | testes |
| AI job aguardando gate | `ai_job_awaiting_human_gate` (sugerido) | `AI_JOB_AWAITING_HUMAN_GATE` | `request_id`, `job_id`, `analysis_type`, `case_id` | job + referência `ai_analysis_results` | testes |
| Aprovação registrada | `ai_job_approval_recorded` (sugerido) | `AI_JOB_APPROVAL_RECORDED` | `job_id`, `role`, `approved_by` | job | testes |
| Job degradado | `ai_job_degraded` (sugerido) | `AI_JOB_DEGRADED` + `AI_DEGRADED_*` quando aplicável | `job_id`, `degradation_reason`, `result_analysis_id` | resultado parcial | testes |
| Job falhou | `ai_job_failed` (sugerido) | `AI_JOB_FAILED` quando impactar decisão sensível | `job_id`, `error.code`, `request_id` | erro estruturado | testes |

## Evidencias por Dominio

### Sancoes e Compliance

Fontes:

- `sanctions_lists_meta`
- `sanctions_hits_cache`
- `audit_logs`
- `evidence_trail`
- `artifacts/homologation/`

Chaves relevantes:

- `list_name`
- `source_url`
- `last_sync_hash`
- `address`
- `matched_lists`
- `request_id`

### Bloqueios Preventivos

Fontes:

- `preventive_blocks`
- `audit_logs`
- `evidence_trail`

Chaves relevantes:

- `block_id`
- `evidence_hash`
- `evidence_trail_event_hash`
- `coaf_ros_required`

### Contrapartes

Fontes:

- `counterparties`
- `counterparty_history`
- `evidence_trail`

Chaves relevantes:

- `counterparty_id`
- `document_type`
- `document_number`
- `risk_level`
- `next_review_date`

### ROS/COAF

Fontes:

- `ros_records`
- `reports`
- `audit_logs`
- `evidence_trail`

Chaves relevantes:

- `ros_id`
- `report_id`
- `pdf_hash`
- `coaf_protocol_number`
- `coaf_receipt_hash`
- `submission_deadline`

### Reports formais

Fontes:

- `reports`
- `audit_logs`
- `evidence_trail`
- bundles exportados via `evidence-export`
- cockpit `/evidence` com foco contextual e export da cadeia selecionada

Chaves relevantes:

- `report_id`
- `case_id`
- `report_type`
- `file_hash_sha256`
- `request_id`

## Evidencias Operacionais de Staging

Artefatos relevantes:

- `artifacts/staging/checks/*.json`
- `artifacts/staging/checks/*-oidc-readiness-bundle.json`
- `artifacts/staging/checks/*-eu-sanctions-preflight.json`
- `artifacts/staging/checks/*-eu-sanctions-sync.json`
- `artifacts/staging/checks/*-regulatory-readiness-bundle.json`
- `artifacts/staging/window-packet-*.md`
- `artifacts/staging/dossiers/*.json`
- `artifacts/staging/dossiers/*-oidc-readiness-bundle.md`
- `artifacts/staging/dossiers/*-regulatory-readiness-bundle.md`
- `artifacts/homologation/*.json`
- `*.manifest.json`

Scripts canonicos:

- `prepare_staging_window.py`
- `run_staging_window.py`
- `run_oidc_readiness_bundle.py`
- `preflight_external_integrations.py`
- `check_compliance_provider_runtime.py`
- `run_eu_sanctions_window.py`
- `check_sanctions_sync_status.py`
- `build_staging_release_dossier.py`

## Gaps Residuais da Matriz

- nem todo evento negativo sensivel possui espelho em `evidence_trail`; parte continua apenas em `audit_logs`
- janelas `AML/KYT live` e UE ainda dependem de evidencia institucional recorrente, apesar dos guardrails tecnicos estarem prontos
- `P0-01` agora possui bundle OIDC próprio, mas a homologação institucional de MFA/`external_provider` ainda depende de execução recorrente em janela séria
- artefatos de manual review para `due_diligence` e `source_of_funds` agora possuem pacote regulatório operacional no cockpit `/evidence`, com selagem institucional forte funcional, governança pós-selagem e correlação auditável por `package_sha256`
- os gaps residuais dessa trilha agora se concentram em homologação do provider institucional definitivo, trust bundle versionado e aceite recorrente em janela séria
- o contrato HTTP canônico dessa superfície está em `./api-contracts.md`, com visão arquitetural complementar em `./evidence-manual-package-strong-sealing-architecture.md`

## Uso Recomendado

Consultar esta matriz quando:

- um fluxo sensivel for alterado
- houver incidente regulatorio ou operacional
- for necessario anexar prova tecnica a uma janela seria
- um novo endpoint passar a gerar hash, evidencia ou export controlado

Para a trilha manual DD/SoF, complementar a revisao com:

- `./evidence-manual-package-rollout-checklist.md`
