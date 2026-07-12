CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
  CREATE ROLE db_owner NOLOGIN;
EXCEPTION
  WHEN duplicate_object THEN
    NULL;
END
$$;

CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  plan VARCHAR(50) NOT NULL DEFAULT 'free',
  credits_available NUMERIC(10,4) NOT NULL DEFAULT 0,
  credits_reserved NUMERIC(10,4) NOT NULL DEFAULT 0,
  credits_used_total NUMERIC(10,4) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

GRANT SELECT ON organizations TO db_owner;

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(255),
  role VARCHAR(50) NOT NULL DEFAULT 'ANALYST',
  status VARCHAR(20) NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'invited', 'disabled')),
  note TEXT,
  is_2fa_enabled BOOLEAN DEFAULT FALSE,
  totp_secret_encrypted TEXT,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS note TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'users_status_check'
  ) THEN
    ALTER TABLE users
      ADD CONSTRAINT users_status_check
      CHECK (status IN ('active', 'invited', 'disabled'));
  END IF;
END
$$;

CREATE TABLE IF NOT EXISTS external_identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  provider VARCHAR(50) NOT NULL,
  external_subject VARCHAR(255) NOT NULL,
  user_id UUID REFERENCES users(id),
  email_snapshot VARCHAR(255),
  role_snapshot VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_identities_provider_subject_org
  ON external_identities(provider, external_subject, organization_id);

CREATE INDEX IF NOT EXISTS idx_external_identities_user_id
  ON external_identities(user_id);

CREATE INDEX IF NOT EXISTS idx_external_identities_org_id
  ON external_identities(organization_id);

CREATE TABLE IF NOT EXISTS cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  user_id UUID REFERENCES users(id),
  title VARCHAR(500),
  case_type VARCHAR(50) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'queued',
  priority VARCHAR(20) DEFAULT 'normal',
  target_address VARCHAR(255),
  target_chain VARCHAR(50),
  depth INTEGER DEFAULT 3,
  context_narrative TEXT,
  credits_estimated NUMERIC(10,4) NOT NULL DEFAULT 0,
  credits_used NUMERIC(10,4) NOT NULL DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id),
  agent_name VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL,
  input JSONB,
  output JSONB,
  error_message TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  duration_ms INTEGER
);

CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID REFERENCES cases(id),
  organization_id UUID REFERENCES organizations(id),
  external_report_id VARCHAR(64),
  report_type_requested VARCHAR(50),
  report_type VARCHAR(50),
  content_type VARCHAR(100),
  file_path VARCHAR(500),
  file_hash VARCHAR(64),
  onchain_hash VARCHAR(255),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_coaf_ready BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS external_report_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS report_type_requested VARCHAR(50),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100),
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS watchlists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT 'normal',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watchlist_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
  address VARCHAR(255) NOT NULL,
  chain VARCHAR(50) NOT NULL,
  last_scanned_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
  item_id UUID REFERENCES watchlist_items(id) ON DELETE SET NULL,
  address VARCHAR(255) NOT NULL,
  chain VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL DEFAULT 'medium',
  title VARCHAR(255) NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS operational_alert_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receiver VARCHAR(120) NOT NULL,
  group_key TEXT,
  status VARCHAR(20) NOT NULL,
  triage_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  alertname VARCHAR(255) NOT NULL,
  service VARCHAR(120),
  severity VARCHAR(20),
  fingerprint VARCHAR(255) NOT NULL UNIQUE,
  labels JSONB NOT NULL DEFAULT '{}'::jsonb,
  annotations JSONB NOT NULL DEFAULT '{}'::jsonb,
  starts_at TIMESTAMPTZ,
  ends_at TIMESTAMPTZ,
  generator_url TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  first_received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  delivery_count INTEGER NOT NULL DEFAULT 1,
  resolved_at TIMESTAMPTZ,
  triaged_at TIMESTAMPTZ,
  triaged_by VARCHAR(120),
  triage_note TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID REFERENCES users(id),
  action VARCHAR(80) NOT NULL,
  resource_type VARCHAR(80) NOT NULL,
  resource_id UUID,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  created_by UUID NOT NULL REFERENCES users(id),
  key_hash VARCHAR(64) NOT NULL UNIQUE,
  key_prefix VARCHAR(24) NOT NULL,
  name VARCHAR(255),
  permission_scope VARCHAR(50) NOT NULL DEFAULT 'READ',
  rate_limit_rpm INTEGER NOT NULL DEFAULT 100,
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS investigation_quotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID REFERENCES users(id),
  plan VARCHAR(50) NOT NULL,
  plan_snapshot VARCHAR(50) NOT NULL,
  target_address VARCHAR(255) NOT NULL,
  chains TEXT[] NOT NULL,
  requested_depth INTEGER NOT NULL,
  applied_depth INTEGER NOT NULL,
  report_type_requested VARCHAR(50) NOT NULL,
  report_type VARCHAR(50) NOT NULL,
  addons TEXT[] NOT NULL DEFAULT ARRAY[]::text[],
  quote_breakdown JSONB NOT NULL,
  subtotal_credits NUMERIC(10,4) NOT NULL,
  plan_discount NUMERIC(10,4) NOT NULL,
  total_credits NUMERIC(10,4) NOT NULL,
  pricing_table_hash VARCHAR(64) NOT NULL,
  calculation_version VARCHAR(20) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  used_at TIMESTAMPTZ,
  used_for_case_id UUID REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS compliance_quotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID REFERENCES users(id),
  plan VARCHAR(50) NOT NULL,
  plan_snapshot VARCHAR(50) NOT NULL,
  operation_requested VARCHAR(50) NOT NULL,
  operation_canonical VARCHAR(50) NOT NULL,
  chain VARCHAR(50) NOT NULL,
  target_address VARCHAR(255) NOT NULL,
  quote_breakdown JSONB NOT NULL,
  subtotal_credits NUMERIC(10,4) NOT NULL,
  plan_discount NUMERIC(10,4) NOT NULL,
  total_credits NUMERIC(10,4) NOT NULL,
  pricing_table_hash VARCHAR(64) NOT NULL,
  calculation_version VARCHAR(20) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  used_at TIMESTAMPTZ,
  used_for_case_id UUID REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS monitoring_quotes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id UUID REFERENCES users(id),
  plan VARCHAR(50) NOT NULL,
  plan_snapshot VARCHAR(50) NOT NULL,
  operation_requested VARCHAR(50) NOT NULL,
  operation_canonical VARCHAR(50) NOT NULL,
  chain VARCHAR(50) NOT NULL,
  target_address VARCHAR(255) NOT NULL,
  watchlist_name VARCHAR(255) NOT NULL,
  priority VARCHAR(20) NOT NULL DEFAULT 'normal',
  quote_breakdown JSONB NOT NULL,
  subtotal_credits NUMERIC(10,4) NOT NULL,
  plan_discount NUMERIC(10,4) NOT NULL,
  total_credits NUMERIC(10,4) NOT NULL,
  pricing_table_hash VARCHAR(64) NOT NULL,
  calculation_version VARCHAR(20) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  used_at TIMESTAMPTZ,
  used_for_case_id UUID REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS credit_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id),
  case_id UUID REFERENCES cases(id),
  action VARCHAR(50) NOT NULL CHECK (action IN ('PRE_HOLD', 'CONFIRMED', 'REFUND')),
  amount NUMERIC(10,4) NOT NULL,
  balance_after NUMERIC(10,4) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS counterparties (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  created_by_user_id UUID NOT NULL REFERENCES users(id),
  counterparty_type VARCHAR(50) NOT NULL,
  legal_name VARCHAR(500) NOT NULL,
  trading_name VARCHAR(500),
  document_type VARCHAR(20) NOT NULL,
  document_number VARCHAR(50) NOT NULL,
  document_country CHAR(3) NOT NULL DEFAULT 'BRA',
  document_verified BOOLEAN NOT NULL DEFAULT FALSE,
  document_verified_at TIMESTAMPTZ,
  registration_data JSONB NOT NULL DEFAULT '{}',
  beneficial_owners JSONB NOT NULL DEFAULT '[]',
  wallet_addresses JSONB NOT NULL DEFAULT '[]',
  risk_level INTEGER NOT NULL DEFAULT 1 CHECK (risk_level BETWEEN 1 AND 4),
  risk_rationale TEXT,
  risk_classified_by UUID REFERENCES users(id),
  risk_classified_at TIMESTAMPTZ,
  onchain_risk_score INTEGER CHECK (onchain_risk_score BETWEEN 0 AND 100),
  onchain_analysis JSONB DEFAULT '{}',
  is_pep BOOLEAN NOT NULL DEFAULT FALSE,
  pep_detail JSONB DEFAULT '{}',
  sanctions_cleared BOOLEAN NOT NULL DEFAULT FALSE,
  sanctions_check_date TIMESTAMPTZ,
  sanctions_hits JSONB NOT NULL DEFAULT '[]',
  kyc_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
  kyc_reviewed_by UUID REFERENCES users(id),
  kyc_reviewed_at TIMESTAMPTZ,
  kyc_rejection_reason TEXT,
  enhanced_dd_required BOOLEAN NOT NULL DEFAULT FALSE,
  enhanced_dd_status VARCHAR(50),
  enhanced_dd_completed_by UUID REFERENCES users(id),
  enhanced_dd_completed_at TIMESTAMPTZ,
  enhanced_dd_findings TEXT,
  enhanced_dd_checklist JSONB DEFAULT '[]',
  next_review_date DATE,
  review_frequency_days INTEGER NOT NULL DEFAULT 365,
  last_reviewed_at TIMESTAMPTZ,
  last_reviewed_by UUID REFERENCES users(id),
  status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  status_changed_at TIMESTAMPTZ,
  status_changed_by UUID REFERENCES users(id),
  status_reason TEXT,
  evidence_hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  retain_until TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 years'),
  CONSTRAINT uq_counterparty_doc_org UNIQUE (organization_id, document_type, document_number)
);

CREATE OR REPLACE FUNCTION update_counterparty_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS counterparty_updated_at ON counterparties;
CREATE TRIGGER counterparty_updated_at
  BEFORE UPDATE ON counterparties
  FOR EACH ROW EXECUTE FUNCTION update_counterparty_updated_at();

CREATE TABLE IF NOT EXISTS counterparty_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  counterparty_id UUID NOT NULL REFERENCES counterparties(id),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  changed_by_user_id UUID NOT NULL REFERENCES users(id),
  change_type VARCHAR(50) NOT NULL,
  field_changed VARCHAR(100),
  old_value TEXT,
  new_value TEXT,
  change_reason TEXT,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  evidence_hash VARCHAR(64) NOT NULL
);

ALTER TABLE counterparties ENABLE ROW LEVEL SECURITY;
ALTER TABLE counterparty_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS counterparties_tenant_isolation ON counterparties;
CREATE POLICY counterparties_tenant_isolation
  ON counterparties FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS counterparty_history_tenant_isolation ON counterparty_history;
CREATE POLICY counterparty_history_tenant_isolation
  ON counterparty_history FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

CREATE INDEX IF NOT EXISTS idx_counterparties_org
  ON counterparties(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_counterparties_kyc_status
  ON counterparties(organization_id, kyc_status)
  WHERE kyc_status != 'APPROVED';

CREATE INDEX IF NOT EXISTS idx_counterparties_risk_level
  ON counterparties(organization_id, risk_level)
  WHERE risk_level >= 3;

CREATE INDEX IF NOT EXISTS idx_counterparties_review_due
  ON counterparties(organization_id, next_review_date)
  WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_counterparties_pep
  ON counterparties(organization_id)
  WHERE is_pep = TRUE;

CREATE INDEX IF NOT EXISTS idx_counterparties_sanctions
  ON counterparties(organization_id)
  WHERE sanctions_cleared = FALSE;

CREATE INDEX IF NOT EXISTS idx_counterparty_history_cp
  ON counterparty_history(counterparty_id, changed_at DESC);

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

CREATE TABLE IF NOT EXISTS regulatory_work_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  module VARCHAR(50) NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  resource_id UUID NOT NULL,
  case_id UUID REFERENCES cases(id),
  report_external_id VARCHAR(64),
  owner_user_id UUID REFERENCES users(id),
  assigned_by_user_id UUID REFERENCES users(id),
  queue_status VARCHAR(40) NOT NULL DEFAULT 'UNDER_REVIEW',
  priority VARCHAR(20) NOT NULL DEFAULT 'normal',
  due_at TIMESTAMPTZ,
  sla_breached BOOLEAN NOT NULL DEFAULT FALSE,
  title VARCHAR(255),
  note TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_regulatory_work_items_resource
    UNIQUE (organization_id, resource_type, resource_id),
  CONSTRAINT ck_regulatory_work_items_module
    CHECK (module IN ('alerts', 'sanctions', 'blocks', 'reports', 'ros_coaf', 'counterparties', 'evidence')),
  CONSTRAINT ck_regulatory_work_items_resource_type
    CHECK (resource_type IN (
      'operational_alert',
      'sanctions_screening',
      'preventive_block',
      'formal_report_case',
      'ros_record',
      'counterparty',
      'evidence_event'
    )),
  CONSTRAINT ck_regulatory_work_items_module_resource_pair
    CHECK (regulatory_work_item_module_resource_pair_valid(module, resource_type)),
  CONSTRAINT ck_regulatory_work_items_queue_status
    CHECK (queue_status IN ('UNDER_REVIEW', 'ESCALATED', 'READY', 'APPROVED', 'SUBMITTED', 'CLOSED', 'REJECTED')),
  CONSTRAINT ck_regulatory_work_items_priority
    CHECK (priority IN ('critical', 'high', 'normal')),
  CONSTRAINT ck_regulatory_work_items_metadata_shape
    CHECK (regulatory_work_item_metadata_guard(resource_type, metadata))
);

CREATE TABLE IF NOT EXISTS regulatory_work_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_item_id UUID NOT NULL REFERENCES regulatory_work_items(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id),
  actor_user_id UUID REFERENCES users(id),
  event_type VARCHAR(50) NOT NULL,
  from_status VARCHAR(40),
  to_status VARCHAR(40),
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS regulatory_work_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  work_item_id UUID NOT NULL REFERENCES regulatory_work_items(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id),
  actor_user_id UUID REFERENCES users(id),
  comment_type VARCHAR(30) NOT NULL DEFAULT 'note',
  body TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ck_regulatory_work_comments_type
    CHECK (comment_type IN ('note', 'decision', 'handoff'))
);

CREATE TABLE IF NOT EXISTS evidence_package_seals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  package_kind VARCHAR(50) NOT NULL DEFAULT 'manual_review_package',
  request_id VARCHAR(120) NOT NULL,
  report_id VARCHAR(64),
  scope_id VARCHAR(120) NOT NULL,
  manual_review_action VARCHAR(80) NOT NULL,
  package_sha256 VARCHAR(64) NOT NULL,
  manifest_schema_version VARCHAR(80) NOT NULL,
  classification VARCHAR(80) NOT NULL,
  signoff_mode VARCHAR(80) NOT NULL,
  seal_status VARCHAR(40) NOT NULL DEFAULT 'pending_signoff',
  seal_format VARCHAR(40) NOT NULL DEFAULT 'jws_json_flattened',
  signature_algorithm VARCHAR(40),
  kms_key_ref VARCHAR(255),
  certificate_fingerprint_sha256 VARCHAR(64),
  certificate_bundle_ref VARCHAR(255),
  policy_version VARCHAR(80) NOT NULL DEFAULT 'manual_package_sealing/v1',
  sealed_at TIMESTAMPTZ,
  sealed_by_user_id UUID REFERENCES users(id),
  revoked_at TIMESTAMPTZ,
  superseded_by_seal_id UUID REFERENCES evidence_package_seals(id),
  seal_envelope JSONB NOT NULL DEFAULT '{}'::jsonb,
  verification_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_evidence_package_seals_org_digest_policy
    UNIQUE (organization_id, package_sha256, policy_version),
  CONSTRAINT ck_evidence_package_seals_kind
    CHECK (package_kind IN ('manual_review_package')),
  CONSTRAINT ck_evidence_package_seals_manual_action
    CHECK (manual_review_action IN (
      'compliance_due_diligence_checked',
      'compliance_source_of_funds_checked'
    )),
  CONSTRAINT ck_evidence_package_seals_status
    CHECK (seal_status IN (
      'pending_signoff',
      'ready_to_seal',
      'sealed',
      'revoked',
      'superseded',
      'failed'
    )),
  CONSTRAINT ck_evidence_package_seals_format
    CHECK (seal_format IN ('jws_json_flattened'))
);

CREATE TABLE IF NOT EXISTS evidence_package_signoffs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seal_id UUID NOT NULL REFERENCES evidence_package_seals(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id),
  signer_role VARCHAR(40) NOT NULL,
  signer_user_id UUID REFERENCES users(id),
  signer_display_name VARCHAR(255) NOT NULL,
  decision VARCHAR(20) NOT NULL,
  signoff_method VARCHAR(40) NOT NULL,
  ticket_ref VARCHAR(120),
  notes TEXT,
  signed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_evidence_package_signoffs_role
    UNIQUE (seal_id, signer_role),
  CONSTRAINT ck_evidence_package_signoffs_role
    CHECK (signer_role IN (
      'compliance_owner',
      'ops_owner',
      'legal_owner_optional'
    )),
  CONSTRAINT ck_evidence_package_signoffs_decision
    CHECK (decision IN ('approved', 'rejected')),
  CONSTRAINT ck_evidence_package_signoffs_method
    CHECK (signoff_method IN (
      'platform_authenticated_2fa',
      'governance_ticket'
    ))
);

CREATE OR REPLACE FUNCTION update_regulatory_work_items_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  NEW.last_activity_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS regulatory_work_items_updated_at ON regulatory_work_items;
CREATE TRIGGER regulatory_work_items_updated_at
  BEFORE UPDATE ON regulatory_work_items
  FOR EACH ROW EXECUTE FUNCTION update_regulatory_work_items_updated_at();

CREATE OR REPLACE FUNCTION update_evidence_package_seals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS evidence_package_seals_updated_at ON evidence_package_seals;
CREATE TRIGGER evidence_package_seals_updated_at
  BEFORE UPDATE ON evidence_package_seals
  FOR EACH ROW EXECUTE FUNCTION update_evidence_package_seals_updated_at();

CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_cases_org_id ON cases(organization_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_case_id ON agent_runs(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_case_id ON reports(case_id);
DO $$
DECLARE
  orphan_index_exists BOOLEAN;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uq_reports_external_report_id'
      AND conrelid = 'reports'::regclass
  ) THEN
    SELECT EXISTS (
      SELECT 1
      FROM pg_class idx
      JOIN pg_index i ON i.indexrelid = idx.oid
      WHERE idx.relname = 'uq_reports_external_report_id'
        AND i.indrelid = 'reports'::regclass
        AND NOT EXISTS (
          SELECT 1
          FROM pg_constraint c
          WHERE c.conindid = idx.oid
        )
    )
    INTO orphan_index_exists;

    IF orphan_index_exists THEN
      EXECUTE 'DROP INDEX IF EXISTS uq_reports_external_report_id';
    END IF;

    ALTER TABLE reports
      ADD CONSTRAINT uq_reports_external_report_id UNIQUE (external_report_id);
  END IF;
END
$$;
CREATE INDEX IF NOT EXISTS idx_watchlists_org_id ON watchlists(organization_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_watchlist_id ON watchlist_items(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_org_id ON monitoring_alerts(organization_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_watchlist_id ON monitoring_alerts(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_created_at ON monitoring_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_operational_alert_events_status_last_received_at
  ON operational_alert_events(status, last_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_operational_alert_events_service_last_received_at
  ON operational_alert_events(service, last_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_operational_alert_events_triage_status_last_received_at
  ON operational_alert_events(triage_status, last_received_at DESC);
CREATE INDEX IF NOT EXISTS idx_operational_alert_events_last_received_at_id_desc
  ON operational_alert_events(last_received_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_action_created_at ON audit_logs(organization_id, action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_resource_type_created_at ON audit_logs(organization_id, resource_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs ((metadata->>'request_id')) WHERE metadata ? 'request_id';
CREATE INDEX IF NOT EXISTS idx_audit_logs_report_id ON audit_logs ((metadata->>'report_id')) WHERE metadata ? 'report_id';
CREATE INDEX IF NOT EXISTS idx_api_keys_org_id ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_quotes_org_id ON investigation_quotes(organization_id);
CREATE INDEX IF NOT EXISTS idx_quotes_expires_at ON investigation_quotes(expires_at);
CREATE INDEX IF NOT EXISTS idx_quotes_plan_drift ON investigation_quotes(plan_snapshot, organization_id, used_at) WHERE used_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_compliance_quotes_org_id ON compliance_quotes(organization_id);
CREATE INDEX IF NOT EXISTS idx_compliance_quotes_expires_at ON compliance_quotes(expires_at);
CREATE INDEX IF NOT EXISTS idx_compliance_quotes_plan_drift ON compliance_quotes(plan_snapshot, organization_id, used_at) WHERE used_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_monitoring_quotes_org_id ON monitoring_quotes(organization_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_quotes_expires_at ON monitoring_quotes(expires_at);
CREATE INDEX IF NOT EXISTS idx_monitoring_quotes_plan_drift ON monitoring_quotes(plan_snapshot, organization_id, used_at) WHERE used_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_credit_ledger_org_id ON credit_ledger(org_id);
CREATE INDEX IF NOT EXISTS idx_credit_ledger_case_id ON credit_ledger(case_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_org_module_status_due
  ON regulatory_work_items(organization_id, module, queue_status, due_at);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_org_owner_status_due
  ON regulatory_work_items(organization_id, owner_user_id, queue_status, due_at);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_org_case
  ON regulatory_work_items(organization_id, case_id)
  WHERE case_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_org_activity
  ON regulatory_work_items(organization_id, last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_org_resource
  ON regulatory_work_items(organization_id, resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_events_work_item
  ON regulatory_work_events(work_item_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_regulatory_work_comments_work_item
  ON regulatory_work_comments(work_item_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_package_seals_org_request_action_created
  ON evidence_package_seals(organization_id, request_id, manual_review_action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_package_seals_org_package_sha
  ON evidence_package_seals(organization_id, package_sha256);
CREATE INDEX IF NOT EXISTS idx_evidence_package_seals_org_status_created
  ON evidence_package_seals(organization_id, seal_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_package_signoffs_org_signed_at
  ON evidence_package_signoffs(organization_id, signed_at DESC);

COMMENT ON TABLE evidence_package_seals IS
  'Estado persistido da selagem institucional de pacotes manuais DD/SoF por tenant. '
  'Preserva package_sha256, signoff_mode, seal_status e envelope assinado sem quebrar o contrato atual.';

COMMENT ON TABLE evidence_package_signoffs IS
  'Decisoes institucionais por papel para selagem forte de pacotes manuais DD/SoF.';

INSERT INTO organizations (id, name, plan, credits_available, credits_reserved, credits_used_total)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Demo Organization',
  'enterprise',
  1000.0000,
  0,
  0
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, organization_id, email, password_hash, display_name, role, status, note, updated_at)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',
  'demo@ontrackchain.local',
  'not-a-real-hash',
  'Demo Admin',
  'ADMIN',
  'active',
  'Conta bootstrap local para desenvolvimento.',
  NOW()
)
ON CONFLICT (id) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  role = EXCLUDED.role,
  status = EXCLUDED.status,
  note = EXCLUDED.note,
  updated_at = NOW();

INSERT INTO api_keys (
  id,
  organization_id,
  created_by,
  key_hash,
  key_prefix,
  name,
  permission_scope,
  rate_limit_rpm,
  is_active
)
VALUES (
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002',
  encode(digest('otc_live_demo_key', 'sha256'), 'hex'),
  'otc_live_',
  'Demo Integration',
  'ADMIN',
  600,
  TRUE
)
ON CONFLICT (id) DO NOTHING;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigation_quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_work_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_work_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_work_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_package_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_package_signoffs ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION check_rls_context()
RETURNS BOOLEAN AS $$
BEGIN
  IF current_setting('app.organization_id', true) IS NULL
     OR current_setting('app.organization_id', true) = '' THEN
    RAISE EXCEPTION 'RLS context not set — access denied'
      USING ERRCODE = '42501';
  END IF;
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP POLICY IF EXISTS users_isolation ON users;
CREATE POLICY users_isolation ON users
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS cases_isolation ON cases;
CREATE POLICY cases_isolation ON cases
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS reports_isolation ON reports;
CREATE POLICY reports_isolation ON reports
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS watchlists_isolation ON watchlists;
CREATE POLICY watchlists_isolation ON watchlists
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS monitoring_alerts_isolation ON monitoring_alerts;
CREATE POLICY monitoring_alerts_isolation ON monitoring_alerts
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS audit_logs_isolation ON audit_logs;
CREATE POLICY audit_logs_isolation ON audit_logs
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS agent_runs_isolation ON agent_runs;
CREATE POLICY agent_runs_isolation ON agent_runs
  USING (
    check_rls_context()
    AND
    EXISTS (
      SELECT 1
      FROM cases
      WHERE cases.id = agent_runs.case_id
        AND cases.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
  )
  WITH CHECK (
    check_rls_context()
    AND
    EXISTS (
      SELECT 1
      FROM cases
      WHERE cases.id = agent_runs.case_id
        AND cases.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
  );

DROP POLICY IF EXISTS watchlist_items_isolation ON watchlist_items;
CREATE POLICY watchlist_items_isolation ON watchlist_items
  USING (
    check_rls_context()
    AND
    EXISTS (
      SELECT 1
      FROM watchlists
      WHERE watchlists.id = watchlist_items.watchlist_id
        AND watchlists.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
  )
  WITH CHECK (
    check_rls_context()
    AND
    EXISTS (
      SELECT 1
      FROM watchlists
      WHERE watchlists.id = watchlist_items.watchlist_id
        AND watchlists.organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    )
  );

DROP POLICY IF EXISTS api_keys_isolation ON api_keys;
CREATE POLICY api_keys_isolation ON api_keys
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS investigation_quotes_isolation ON investigation_quotes;
CREATE POLICY investigation_quotes_isolation ON investigation_quotes
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS compliance_quotes_isolation ON compliance_quotes;
CREATE POLICY compliance_quotes_isolation ON compliance_quotes
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS monitoring_quotes_isolation ON monitoring_quotes;
CREATE POLICY monitoring_quotes_isolation ON monitoring_quotes
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS credit_ledger_isolation ON credit_ledger;
CREATE POLICY credit_ledger_isolation ON credit_ledger
  USING (
    check_rls_context()
    AND org_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND org_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS regulatory_work_items_tenant_isolation ON regulatory_work_items;
CREATE POLICY regulatory_work_items_tenant_isolation ON regulatory_work_items
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS regulatory_work_events_tenant_isolation ON regulatory_work_events;
CREATE POLICY regulatory_work_events_tenant_isolation ON regulatory_work_events
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS regulatory_work_comments_tenant_isolation ON regulatory_work_comments;
CREATE POLICY regulatory_work_comments_tenant_isolation ON regulatory_work_comments
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS evidence_package_seals_tenant_isolation ON evidence_package_seals;
CREATE POLICY evidence_package_seals_tenant_isolation ON evidence_package_seals
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

DROP POLICY IF EXISTS evidence_package_signoffs_tenant_isolation ON evidence_package_signoffs;
CREATE POLICY evidence_package_signoffs_tenant_isolation ON evidence_package_signoffs
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
  );

CREATE OR REPLACE FUNCTION validate_api_key_and_get_context(
  p_key_hash TEXT
)
RETURNS TABLE (
  org_id UUID,
  user_id UUID,
  plan VARCHAR(50),
  permission_scope VARCHAR(50),
  rate_limit_rpm INTEGER,
  is_valid BOOLEAN,
  error_code TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
SET row_security = off
VOLATILE
AS $$
DECLARE
  v_api_key api_keys%ROWTYPE;
  v_plan VARCHAR(50);
BEGIN
  SELECT *
  INTO v_api_key
  FROM api_keys
  WHERE key_hash = p_key_hash
    AND is_active = TRUE
    AND (expires_at IS NULL OR expires_at > NOW())
  LIMIT 1;

  IF NOT FOUND THEN
    RETURN QUERY SELECT NULL::UUID, NULL::UUID, NULL::VARCHAR, NULL::VARCHAR, 0, FALSE, 'INVALID_KEY';
    RETURN;
  END IF;

  SELECT organizations.plan
  INTO v_plan
  FROM organizations
  WHERE organizations.id = v_api_key.organization_id;

  UPDATE api_keys
  SET last_used_at = NOW()
  WHERE id = v_api_key.id;

  RETURN QUERY SELECT
    v_api_key.organization_id,
    v_api_key.created_by,
    v_plan,
    v_api_key.permission_scope,
    v_api_key.rate_limit_rpm,
    TRUE,
    NULL::TEXT;
END;
$$;

ALTER TABLE api_keys OWNER TO db_owner;
ALTER FUNCTION validate_api_key_and_get_context(TEXT) OWNER TO db_owner;
REVOKE ALL ON api_keys FROM PUBLIC;
GRANT EXECUTE ON FUNCTION validate_api_key_and_get_context(TEXT) TO ontrackchain;

CREATE OR REPLACE FUNCTION prevent_credit_ledger_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'credit_ledger is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_credit_ledger_no_update ON credit_ledger;
CREATE TRIGGER trg_credit_ledger_no_update
BEFORE UPDATE ON credit_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_credit_ledger_mutation();

DROP TRIGGER IF EXISTS trg_credit_ledger_no_delete ON credit_ledger;
CREATE TRIGGER trg_credit_ledger_no_delete
BEFORE DELETE ON credit_ledger
FOR EACH ROW EXECUTE FUNCTION prevent_credit_ledger_mutation();
