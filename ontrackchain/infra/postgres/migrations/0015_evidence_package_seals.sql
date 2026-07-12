-- ============================================================
-- Migration 0015: evidence_package_seals
-- Selagem institucional forte para pacotes manuais DD/SoF
-- Base regulatoria:
--   BCB 520 Art. 45 II (retencao auditavel)
--   IN BCB 739 Art. 1° VIII (registro e rastreabilidade)
-- ============================================================

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

ALTER TABLE evidence_package_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_package_signoffs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS evidence_package_seals_tenant_isolation ON evidence_package_seals;
CREATE POLICY evidence_package_seals_tenant_isolation
  ON evidence_package_seals FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS evidence_package_signoffs_tenant_isolation ON evidence_package_signoffs;
CREATE POLICY evidence_package_signoffs_tenant_isolation
  ON evidence_package_signoffs FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

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
