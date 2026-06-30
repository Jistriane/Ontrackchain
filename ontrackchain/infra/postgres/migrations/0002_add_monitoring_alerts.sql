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

ALTER TABLE monitoring_alerts ENABLE ROW LEVEL SECURITY;

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

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_org_id ON monitoring_alerts(organization_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_watchlist_id ON monitoring_alerts(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_created_at ON monitoring_alerts(created_at);
