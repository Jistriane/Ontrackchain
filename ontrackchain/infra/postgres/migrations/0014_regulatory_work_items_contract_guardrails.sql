-- ============================================================
-- Migration 0014: regulatory_work_items contract guardrails
-- Endurece o contrato entre module/resource_type e metadata
-- sem quebrar compatibilidade com aliases legados.
-- ============================================================

CREATE OR REPLACE FUNCTION jsonb_is_string_or_null(value JSONB)
RETURNS BOOLEAN AS $$
  SELECT value IS NULL OR jsonb_typeof(value) IN ('string', 'null');
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION jsonb_is_bool_or_null(value JSONB)
RETURNS BOOLEAN AS $$
  SELECT value IS NULL OR jsonb_typeof(value) IN ('boolean', 'null');
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION jsonb_is_number_or_null(value JSONB)
RETURNS BOOLEAN AS $$
  SELECT value IS NULL OR jsonb_typeof(value) IN ('number', 'null');
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION jsonb_is_string_array_or_null(value JSONB)
RETURNS BOOLEAN AS $$
  SELECT
    value IS NULL
    OR jsonb_typeof(value) = 'null'
    OR (
      jsonb_typeof(value) = 'array'
      AND NOT EXISTS (
        SELECT 1
        FROM jsonb_array_elements(value) AS entry
        WHERE jsonb_typeof(entry) <> 'string'
      )
    );
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION regulatory_work_item_module_resource_pair_valid(
  module_value TEXT,
  resource_type_value TEXT
)
RETURNS BOOLEAN AS $$
  SELECT CASE module_value
    WHEN 'alerts' THEN resource_type_value = 'operational_alert'
    WHEN 'sanctions' THEN resource_type_value = 'sanctions_screening'
    WHEN 'blocks' THEN resource_type_value = 'preventive_block'
    WHEN 'reports' THEN resource_type_value = 'formal_report_case'
    WHEN 'ros_coaf' THEN resource_type_value = 'ros_record'
    WHEN 'counterparties' THEN resource_type_value = 'counterparty'
    WHEN 'evidence' THEN resource_type_value = 'evidence_event'
    ELSE FALSE
  END;
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION regulatory_work_item_metadata_guard(
  resource_type_value TEXT,
  metadata_value JSONB
)
RETURNS BOOLEAN AS $$
  SELECT
    metadata_value IS NOT NULL
    AND jsonb_typeof(metadata_value) = 'object'
    AND jsonb_is_string_or_null(metadata_value -> 'case_id')
    AND jsonb_is_string_or_null(metadata_value -> 'local_case_id')
    AND jsonb_is_string_or_null(metadata_value -> 'owner_user_id')
    AND jsonb_is_string_or_null(metadata_value -> 'owner_label')
    AND jsonb_is_string_or_null(metadata_value -> 'workspace_status')
    AND jsonb_is_string_or_null(metadata_value -> 'local_workspace_status')
    AND jsonb_is_string_or_null(metadata_value -> 'note')
    AND CASE resource_type_value
      WHEN 'operational_alert' THEN
        jsonb_is_string_or_null(metadata_value -> 'alertname')
        AND jsonb_is_string_or_null(metadata_value -> 'receiver')
        AND jsonb_is_string_or_null(metadata_value -> 'service')
        AND jsonb_is_string_or_null(metadata_value -> 'severity')
        AND jsonb_is_string_or_null(metadata_value -> 'fingerprint')
        AND jsonb_is_string_or_null(metadata_value -> 'first_received_at')
        AND jsonb_is_string_or_null(metadata_value -> 'last_received_at')
        AND jsonb_is_number_or_null(metadata_value -> 'delivery_count')
        AND jsonb_is_string_or_null(metadata_value -> 'triage_status')
        AND jsonb_is_string_or_null(metadata_value -> 'triaged_at')
        AND jsonb_is_string_or_null(metadata_value -> 'triaged_by')
        AND jsonb_is_string_or_null(metadata_value -> 'triage_note')
        AND jsonb_is_string_or_null(metadata_value -> 'address')
        AND jsonb_is_string_or_null(metadata_value -> 'report_id')
      WHEN 'sanctions_screening' THEN
        jsonb_is_string_or_null(metadata_value -> 'workspace_id')
        AND jsonb_is_string_or_null(metadata_value -> 'address')
        AND jsonb_is_string_or_null(metadata_value -> 'chain')
        AND jsonb_is_string_array_or_null(metadata_value -> 'lists')
        AND jsonb_is_string_or_null(metadata_value -> 'provider')
        AND jsonb_is_string_or_null(metadata_value -> 'provider_status')
        AND jsonb_is_string_or_null(metadata_value -> 'capability_status')
        AND jsonb_is_string_or_null(metadata_value -> 'degraded_reason')
        AND jsonb_is_string_array_or_null(metadata_value -> 'matched_lists')
        AND jsonb_is_bool_or_null(metadata_value -> 'hit')
        AND jsonb_is_string_or_null(metadata_value -> 'entity_name')
        AND jsonb_is_string_or_null(metadata_value -> 'designation_date')
        AND jsonb_is_string_or_null(metadata_value -> 'checked_at')
        AND jsonb_is_string_or_null(metadata_value -> 'triage_note')
      WHEN 'preventive_block' THEN
        jsonb_is_string_or_null(metadata_value -> 'workspace_id')
        AND jsonb_is_string_or_null(metadata_value -> 'local_block_status')
        AND jsonb_is_string_or_null(metadata_value -> 'address')
        AND jsonb_is_string_or_null(metadata_value -> 'chain')
        AND jsonb_is_string_or_null(metadata_value -> 'entity_name')
        AND jsonb_is_string_or_null(metadata_value -> 'entity_document')
        AND jsonb_is_string_or_null(metadata_value -> 'action')
        AND jsonb_is_bool_or_null(metadata_value -> 'requires_coaf_report')
        AND jsonb_is_number_or_null(metadata_value -> 'decision_confidence')
        AND jsonb_is_string_array_or_null(metadata_value -> 'regulatory_basis')
        AND jsonb_is_string_array_or_null(metadata_value -> 'matched_lists')
        AND jsonb_is_string_or_null(metadata_value -> 'evidence_hash')
        AND jsonb_is_string_or_null(metadata_value -> 'block_id')
        AND jsonb_is_string_or_null(metadata_value -> 'screened_at')
        AND jsonb_is_string_or_null(metadata_value -> 'lifted_at')
        AND jsonb_is_string_or_null(metadata_value -> 'lift_reason')
      WHEN 'formal_report_case' THEN
        jsonb_is_string_or_null(metadata_value -> 'target_address')
        AND jsonb_is_string_or_null(metadata_value -> 'target_chain')
        AND jsonb_is_string_or_null(metadata_value -> 'report_type')
      WHEN 'ros_record' THEN
        jsonb_is_string_or_null(metadata_value -> 'ros_id')
        AND jsonb_is_string_or_null(metadata_value -> 'ros_status')
        AND jsonb_is_string_or_null(metadata_value -> 'report_id')
        AND jsonb_is_string_or_null(metadata_value -> 'created_at')
        AND jsonb_is_string_or_null(metadata_value -> 'approved_at')
        AND jsonb_is_string_or_null(metadata_value -> 'submitted_at')
        AND jsonb_is_string_or_null(metadata_value -> 'coaf_protocol_number')
        AND jsonb_is_string_or_null(metadata_value -> 'coaf_receipt_hash')
      WHEN 'counterparty' THEN
        jsonb_is_string_or_null(metadata_value -> 'counterparty_id')
        AND jsonb_is_string_or_null(metadata_value -> 'legal_name')
        AND jsonb_is_string_or_null(metadata_value -> 'counterparty_type')
        AND jsonb_is_string_or_null(metadata_value -> 'document_type')
        AND jsonb_is_string_or_null(metadata_value -> 'document_number')
        AND jsonb_is_string_or_null(metadata_value -> 'wallet_chain')
        AND jsonb_is_string_or_null(metadata_value -> 'wallet_address')
        AND jsonb_is_string_or_null(metadata_value -> 'wallet_label')
        AND jsonb_is_number_or_null(metadata_value -> 'risk_level')
        AND jsonb_is_string_or_null(metadata_value -> 'kyc_status')
        AND jsonb_is_bool_or_null(metadata_value -> 'sanctions_cleared')
        AND jsonb_is_bool_or_null(metadata_value -> 'is_pep')
        AND jsonb_is_bool_or_null(metadata_value -> 'enhanced_dd_required')
        AND jsonb_is_string_or_null(metadata_value -> 'next_review_date')
        AND jsonb_is_string_or_null(metadata_value -> 'status')
        AND jsonb_is_string_or_null(metadata_value -> 'created_at')
        AND jsonb_is_string_or_null(metadata_value -> 'dd_review_status')
        AND jsonb_is_string_or_null(metadata_value -> 'dd_review_note')
        AND jsonb_is_string_or_null(metadata_value -> 'sof_description')
        AND jsonb_is_string_or_null(metadata_value -> 'sof_document_ref')
      WHEN 'evidence_event' THEN
        jsonb_is_string_or_null(metadata_value -> 'event_id')
        AND jsonb_is_string_or_null(metadata_value -> 'audit_action')
        AND jsonb_is_string_or_null(metadata_value -> 'audit_resource_type')
        AND jsonb_is_string_or_null(metadata_value -> 'audit_resource_id')
        AND jsonb_is_string_or_null(metadata_value -> 'request_id')
        AND jsonb_is_string_or_null(metadata_value -> 'report_id')
        AND jsonb_is_string_or_null(metadata_value -> 'file_hash_sha256')
      ELSE FALSE
    END;
$$ LANGUAGE sql IMMUTABLE;

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{workspace_status}', to_jsonb(metadata ->> 'local_workspace_status'), true)
WHERE NOT (metadata ? 'workspace_status')
  AND metadata ? 'local_workspace_status'
  AND jsonb_typeof(metadata -> 'local_workspace_status') = 'string';

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{workspace_status}', to_jsonb(metadata ->> 'local_block_status'), true)
WHERE resource_type = 'preventive_block'
  AND NOT (metadata ? 'workspace_status')
  AND metadata ? 'local_block_status'
  AND jsonb_typeof(metadata -> 'local_block_status') = 'string';

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{workspace_status}', to_jsonb(metadata ->> 'ros_status'), true)
WHERE resource_type = 'ros_record'
  AND NOT (metadata ? 'workspace_status')
  AND metadata ? 'ros_status'
  AND jsonb_typeof(metadata -> 'ros_status') = 'string';

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{local_workspace_status}', to_jsonb(metadata ->> 'workspace_status'), true)
WHERE resource_type IN ('sanctions_screening', 'formal_report_case', 'counterparty', 'evidence_event')
  AND metadata ? 'workspace_status'
  AND NOT (metadata ? 'local_workspace_status')
  AND jsonb_typeof(metadata -> 'workspace_status') = 'string';

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{local_block_status}', to_jsonb(metadata ->> 'workspace_status'), true)
WHERE resource_type = 'preventive_block'
  AND metadata ? 'workspace_status'
  AND NOT (metadata ? 'local_block_status')
  AND jsonb_typeof(metadata -> 'workspace_status') = 'string';

UPDATE regulatory_work_items
SET metadata = jsonb_set(metadata, '{ros_status}', to_jsonb(metadata ->> 'workspace_status'), true)
WHERE resource_type = 'ros_record'
  AND metadata ? 'workspace_status'
  AND NOT (metadata ? 'ros_status')
  AND jsonb_typeof(metadata -> 'workspace_status') = 'string';

ALTER TABLE regulatory_work_items
  DROP CONSTRAINT IF EXISTS ck_regulatory_work_items_module_resource_pair;

ALTER TABLE regulatory_work_items
  ADD CONSTRAINT ck_regulatory_work_items_module_resource_pair
  CHECK (regulatory_work_item_module_resource_pair_valid(module, resource_type));

ALTER TABLE regulatory_work_items
  DROP CONSTRAINT IF EXISTS ck_regulatory_work_items_metadata_shape;

ALTER TABLE regulatory_work_items
  ADD CONSTRAINT ck_regulatory_work_items_metadata_shape
  CHECK (regulatory_work_item_metadata_guard(resource_type, metadata));
