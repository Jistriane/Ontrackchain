ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS external_report_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS report_type_requested VARCHAR(50),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);

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
