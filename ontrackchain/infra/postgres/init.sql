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
  role VARCHAR(50) NOT NULL DEFAULT 'ANALYST',
  is_2fa_enabled BOOLEAN DEFAULT FALSE,
  totp_secret_encrypted TEXT,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_cases_org_id ON cases(organization_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_case_id ON agent_runs(case_id);
CREATE INDEX IF NOT EXISTS idx_reports_case_id ON reports(case_id);
DROP INDEX IF EXISTS uq_reports_external_report_id;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uq_reports_external_report_id'
      AND conrelid = 'reports'::regclass
  ) THEN
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

INSERT INTO users (id, organization_id, email, password_hash, role)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000001',
  'demo@ontrackchain.local',
  'not-a-real-hash',
  'ADMIN'
)
ON CONFLICT (id) DO NOTHING;

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
