CREATE INDEX IF NOT EXISTS idx_audit_logs_org_action_created_at
ON audit_logs(organization_id, action, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_org_resource_type_created_at
ON audit_logs(organization_id, resource_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id
ON audit_logs ((metadata->>'request_id'))
WHERE metadata ? 'request_id';

CREATE INDEX IF NOT EXISTS idx_audit_logs_report_id
ON audit_logs ((metadata->>'report_id'))
WHERE metadata ? 'report_id';
