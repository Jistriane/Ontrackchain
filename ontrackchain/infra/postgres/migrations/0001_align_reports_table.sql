ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS external_report_id VARCHAR(64),
  ADD COLUMN IF NOT EXISTS report_type_requested VARCHAR(50),
  ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);

DO $$
DECLARE
  orphan_index_exists BOOLEAN;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uq_reports_external_report_id'
      AND conrelid = 'reports'::regclass
  ) THEN
    SELECT EXISTS (
      SELECT 1
      FROM pg_class idx
      JOIN pg_index i ON i.indexrelid = idx.oid
      WHERE idx.relname = 'uq_reports_external_report_id'
        AND i.indrelid = 'reports'::regclass
        AND NOT EXISTS (
          SELECT 1
          FROM pg_constraint c
          WHERE c.conindid = idx.oid
        )
    )
    INTO orphan_index_exists;

    IF orphan_index_exists THEN
      EXECUTE 'DROP INDEX IF EXISTS uq_reports_external_report_id';
    END IF;

    ALTER TABLE reports
      ADD CONSTRAINT uq_reports_external_report_id UNIQUE (external_report_id);
  END IF;
END
$$;
