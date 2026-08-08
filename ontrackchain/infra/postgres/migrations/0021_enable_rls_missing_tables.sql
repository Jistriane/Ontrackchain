-- Migration 0021: Habilita ROW LEVEL SECURITY + Policies de Isolamento Multi-Tenant
-- em tabelas sensíveis que faltavam. Alinhado com ADR-001-rls-multi-tenant.md
-- Padrão seguido: NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
-- (igual a tabelas counterparties, evidence_trail, agent_* já existentes)

-- ============================================================
-- 1. TABELA cases (compartilhada case-management + investigation)
-- ============================================================
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cases_tenant_isolation ON cases;
CREATE POLICY cases_tenant_isolation ON cases
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_cases_organization_id ON cases(organization_id);

-- ============================================================
-- 2. TABELA users (usuários por organização)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);

-- ============================================================
-- 3. TABELA monitoring_alerts (SLA 24h, dados sensíveis do tenant)
-- ============================================================
ALTER TABLE IF EXISTS monitoring_alerts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS monitoring_alerts_tenant_isolation ON monitoring_alerts;
CREATE POLICY monitoring_alerts_tenant_isolation ON monitoring_alerts
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_organization_id ON monitoring_alerts(organization_id);

-- ============================================================
-- 4. TABELA audit_logs (todas ações do sistema por organização)
-- ============================================================
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);

-- ============================================================
-- 5. TABELA watchlists (listas de monitoramento por tenant)
-- ============================================================
ALTER TABLE IF EXISTS watchlists ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS watchlists_tenant_isolation ON watchlists;
CREATE POLICY watchlists_tenant_isolation ON watchlists
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_watchlists_organization_id ON watchlists(organization_id);

-- ============================================================
-- 6. TABELA regulatory_work_items (itens de obrigação regulatória)
-- ============================================================
ALTER TABLE IF EXISTS regulatory_work_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS regulatory_work_items_tenant_isolation ON regulatory_work_items;
CREATE POLICY regulatory_work_items_tenant_isolation ON regulatory_work_items
    FOR ALL
    USING (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID)
    WITH CHECK (organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID);

CREATE INDEX IF NOT EXISTS idx_regulatory_work_items_organization_id ON regulatory_work_items(organization_id);
