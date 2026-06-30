CREATE TABLE IF NOT EXISTS operational_alert_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receiver VARCHAR(120) NOT NULL,
  group_key TEXT,
  status VARCHAR(20) NOT NULL,
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
  resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_operational_alert_events_status_last_received_at
  ON operational_alert_events(status, last_received_at DESC);

CREATE INDEX IF NOT EXISTS idx_operational_alert_events_service_last_received_at
  ON operational_alert_events(service, last_received_at DESC);
