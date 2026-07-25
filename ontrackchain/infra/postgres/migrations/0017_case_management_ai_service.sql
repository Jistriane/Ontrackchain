-- ============================================================
-- Migration 0017: case_management + ai_service
-- Tabelas para Case Management persistido e Análises AI
-- Base regulatória: BCB Circular 3.978 / Res. 520/2022 / Res. 739/2023
-- ============================================================

-- ─── CASE MANAGEMENT CASES ──────────────────────────────────
CREATE TABLE IF NOT EXISTS case_management_cases (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     UUID NOT NULL REFERENCES organizations(id),
  title               VARCHAR(500) NOT NULL,
  description         TEXT NOT NULL DEFAULT '',
  status              VARCHAR(50) NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'in_progress', 'under_review', 'escalated', 'closed', 'archived')),
  priority            VARCHAR(20) NOT NULL DEFAULT 'medium'
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
  category            VARCHAR(50) NOT NULL
    CHECK (category IN ('sanctions', 'aml', 'kyc', 'investigation', 'fraud', 'ransomware', 'defi')),
  assigned_to         VARCHAR(255),
  risk_score          NUMERIC(5,2) CHECK (risk_score >= 0 AND risk_score <= 100),
  resolution          TEXT,
  metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── CASE MANAGEMENT TIMELINE ───────────────────────────────
CREATE TABLE IF NOT EXISTS case_management_timeline (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             UUID NOT NULL REFERENCES case_management_cases(id) ON DELETE CASCADE,
  organization_id     UUID NOT NULL REFERENCES organizations(id),
  action              VARCHAR(100) NOT NULL,
  actor               VARCHAR(255) NOT NULL,
  details             JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── AI ANALYSIS RESULTS ────────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_analysis_results (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     UUID NOT NULL REFERENCES organizations(id),
  case_id             VARCHAR(255),
  analysis_type       VARCHAR(100) NOT NULL
    CHECK (analysis_type IN ('explain', 'risk_model', 'confidence', 'case_insights', 'graph_analysis', 'graph_narrator', 'law_enforcement_export', 'themis')),
  input_data          JSONB NOT NULL DEFAULT '{}'::jsonb,
  result_data         JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── RLS ────────────────────────────────────────────────────
ALTER TABLE case_management_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_management_timeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis_results ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS case_management_cases_tenant_isolation ON case_management_cases;
CREATE POLICY case_management_cases_tenant_isolation
  ON case_management_cases FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS case_management_timeline_tenant_isolation ON case_management_timeline;
CREATE POLICY case_management_timeline_tenant_isolation
  ON case_management_timeline FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS ai_analysis_results_tenant_isolation ON ai_analysis_results;
CREATE POLICY ai_analysis_results_tenant_isolation
  ON ai_analysis_results FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

-- ─── ÍNDICES ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_case_management_cases_org_created
  ON case_management_cases(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_case_management_cases_org_status
  ON case_management_cases(organization_id, status);

CREATE INDEX IF NOT EXISTS idx_case_management_cases_org_priority
  ON case_management_cases(organization_id, priority);

CREATE INDEX IF NOT EXISTS idx_case_management_cases_org_category
  ON case_management_cases(organization_id, category);

CREATE INDEX IF NOT EXISTS idx_case_management_timeline_case
  ON case_management_timeline(case_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_case_management_timeline_org
  ON case_management_timeline(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_org_type
  ON ai_analysis_results(organization_id, analysis_type, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_case
  ON ai_analysis_results(case_id)
  WHERE case_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ai_analysis_results_org_generated
  ON ai_analysis_results(organization_id, generated_at DESC);

-- ─── TRIGGER: updated_at automático ─────────────────────────
CREATE OR REPLACE FUNCTION update_case_management_cases_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS case_management_cases_updated_at ON case_management_cases;
CREATE TRIGGER case_management_cases_updated_at
  BEFORE UPDATE ON case_management_cases
  FOR EACH ROW EXECUTE FUNCTION update_case_management_cases_updated_at();

-- ─── COMENTÁRIOS ────────────────────────────────────────────
COMMENT ON TABLE case_management_cases IS
  'Casos de investigação e compliance persistidos no PostgreSQL. '
  'Substitui o mock anterior com dados reais, RBAC e audit trail.';

COMMENT ON TABLE case_management_timeline IS
  'Timeline de eventos dos casos de investigação. '
  'Cada ação (criação, atualização, escalação) é registrada.';

COMMENT ON TABLE ai_analysis_results IS
  'Resultados persistidos das análises de IA (XAI, Risk Models, Confidence, '
  'Graph Analysis, Narrator, Case Insights, Law Enforcement Export, THEMIS). '
  'Cada análise é registrada com input, output e timestamp para auditoria.';

COMMENT ON COLUMN case_management_cases.risk_score IS
  'Score de risco calculado (0-100). Atualizado pela AI Service na criação.';

COMMENT ON COLUMN ai_analysis_results.analysis_type IS
  'Tipo de análise AI: explain, risk_model, confidence, case_insights, '
  'graph_analysis, graph_narrator, law_enforcement_export, themis.';
