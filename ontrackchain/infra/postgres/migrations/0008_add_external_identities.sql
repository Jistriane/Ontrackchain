CREATE TABLE IF NOT EXISTS external_identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  provider VARCHAR(50) NOT NULL,
  external_subject VARCHAR(255) NOT NULL,
  user_id UUID REFERENCES users(id),
  email_snapshot VARCHAR(255),
  role_snapshot VARCHAR(50),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_external_identities_provider_subject_org
  ON external_identities(provider, external_subject, organization_id);

CREATE INDEX IF NOT EXISTS idx_external_identities_user_id
  ON external_identities(user_id);

CREATE INDEX IF NOT EXISTS idx_external_identities_org_id
  ON external_identities(organization_id);
