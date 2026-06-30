CREATE INDEX IF NOT EXISTS idx_operational_alert_events_last_received_at_id_desc
  ON operational_alert_events(last_received_at DESC, id DESC);
