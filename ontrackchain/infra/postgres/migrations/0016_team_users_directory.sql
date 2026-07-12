ALTER TABLE users
  ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active',
  ADD COLUMN IF NOT EXISTS note TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'users_status_check'
  ) THEN
    ALTER TABLE users
      ADD CONSTRAINT users_status_check
      CHECK (status IN ('active', 'invited', 'disabled'));
  END IF;
END
$$;

UPDATE users
SET
  display_name = COALESCE(display_name, split_part(email, '@', 1)),
  status = COALESCE(status, 'active'),
  updated_at = COALESCE(updated_at, created_at, NOW())
WHERE TRUE;
