CREATE TABLE IF NOT EXISTS ai_service_jobs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     UUID NOT NULL REFERENCES organizations(id),
  case_id             VARCHAR(255),
  analysis_type       VARCHAR(100) NOT NULL
    CHECK (analysis_type IN ('explain', 'risk_model', 'confidence', 'case_insights', 'graph_analysis', 'graph_narrator', 'law_enforcement_export', 'themis')),
  status              VARCHAR(50) NOT NULL
    CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'degraded', 'awaiting_human_gate', 'cancelled')),
  queue_reason        VARCHAR(50)
    CHECK (queue_reason IN ('ORG_RATE_LIMIT', 'LLM_429', 'LONG_RUNNING_OPERATION')),
  request_id          UUID,
  request_payload_hash VARCHAR(128),
  input_data          JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_analysis_id  UUID REFERENCES ai_analysis_results(id),
  degradation_reason  VARCHAR(50),
  error_data          JSONB NOT NULL DEFAULT '{}'::jsonb,
  human_gate_required BOOLEAN NOT NULL DEFAULT FALSE,
  required_approvals  INTEGER NOT NULL DEFAULT 1
    CHECK (required_approvals IN (1, 2)),
  approvals           JSONB NOT NULL DEFAULT '[]'::jsonb,
  approved_by         VARCHAR(255),
  approved_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ai_service_jobs IS
  'Jobs assíncronos do ai-service: fila, execução longa, aprovação humana e degradação evidenciada.';

COMMENT ON COLUMN ai_service_jobs.error_data IS
  'Payload de erro estruturado. Recomenda-se incluir code=MISSING_PREREQUISITES e missing_prerequisites[] quando aplicável.';

ALTER TABLE ai_service_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ai_service_jobs_tenant_isolation ON ai_service_jobs;
CREATE POLICY ai_service_jobs_tenant_isolation
  ON ai_service_jobs FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

CREATE INDEX IF NOT EXISTS idx_ai_service_jobs_org_created
  ON ai_service_jobs(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_service_jobs_org_status
  ON ai_service_jobs(organization_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_service_jobs_org_type
  ON ai_service_jobs(organization_id, analysis_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_service_jobs_request_id
  ON ai_service_jobs(request_id)
  WHERE request_id IS NOT NULL;

CREATE OR REPLACE FUNCTION update_ai_service_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ai_service_jobs_updated_at ON ai_service_jobs;
CREATE TRIGGER ai_service_jobs_updated_at
  BEFORE UPDATE ON ai_service_jobs
  FOR EACH ROW EXECUTE FUNCTION update_ai_service_jobs_updated_at();
