ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS external_report_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS report_type_requested VARCHAR(50),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);

CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_external_report_id
  ON reports(external_report_id)
  WHERE external_report_id IS NOT NULL;
