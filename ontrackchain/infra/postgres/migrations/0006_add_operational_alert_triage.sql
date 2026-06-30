ALTER TABLE operational_alert_events
  ADD COLUMN IF NOT EXISTS triage_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS triaged_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS triaged_by VARCHAR(120),
  ADD COLUMN IF NOT EXISTS triage_note TEXT;

CREATE INDEX IF NOT EXISTS idx_operational_alert_events_triage_status_last_received_at
  ON operational_alert_events(triage_status, last_received_at DESC);
