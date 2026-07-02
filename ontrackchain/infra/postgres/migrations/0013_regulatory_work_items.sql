-- ============================================================
-- Migration 0013: regulatory_work_items
-- Camada operacional multiusuario persistida para modulos regulatorios
-- Base regulatoria:
--   BCB 520 Art. 45 II (retencao auditavel)
--   BCB 520 Art. 47 (supervisao de contrapartes)
--   IN BCB 739 Art. 1° IV, V, VII e VIII
-- ============================================================

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
    CHECK (module IN (
      'alerts',
      'sanctions',
      'blocks',
      'reports',
      'ros_coaf',
      'counterparties',
      'evidence'
    )),

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

  CONSTRAINT ck_regulatory_work_items_queue_status
    CHECK (queue_status IN (
      'UNDER_REVIEW',
      'ESCALATED',
      'READY',
      'APPROVED',
      'SUBMITTED',
      'CLOSED',
      'REJECTED'
    )),

  CONSTRAINT ck_regulatory_work_items_priority
    CHECK (priority IN ('critical', 'high', 'normal'))
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

ALTER TABLE regulatory_work_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_work_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulatory_work_comments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS regulatory_work_items_tenant_isolation ON regulatory_work_items;
CREATE POLICY regulatory_work_items_tenant_isolation
  ON regulatory_work_items FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS regulatory_work_events_tenant_isolation ON regulatory_work_events;
CREATE POLICY regulatory_work_events_tenant_isolation
  ON regulatory_work_events FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS regulatory_work_comments_tenant_isolation ON regulatory_work_comments;
CREATE POLICY regulatory_work_comments_tenant_isolation
  ON regulatory_work_comments FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

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

COMMENT ON TABLE regulatory_work_items IS
  'Fila operacional multiusuario persistida por tenant para modulos regulatorios. '
  'Base: BCB 520 Art. 45 II · IN BCB 739.';

COMMENT ON TABLE regulatory_work_events IS
  'Timeline operacional auditavel de transicoes e eventos de fila regulatoria.';

COMMENT ON TABLE regulatory_work_comments IS
  'Comentarios operacionais compartilhados por tenant para handoff e decisoes.';
