#!/usr/bin/env bash
set -euo pipefail

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
KEYCLOAK_DB_NAME="${KEYCLOAK_DB_NAME:-keycloak}"
KEYCLOAK_DB_USER="${KEYCLOAK_DB_USER:-keycloak}"
KEYCLOAK_DB_PASSWORD="${KEYCLOAK_DB_PASSWORD:-keycloak_password}"
AUTH_DB_NAME="${AUTH_DB_NAME:-auth_service}"
AUTH_DB_USER="${AUTH_DB_USER:-auth_service}"
AUTH_DB_PASSWORD="${AUTH_DB_PASSWORD:-auth_service_password}"
CASE_DB_NAME="${CASE_DB_NAME:-case_management}"
CASE_DB_USER="${CASE_DB_USER:-case_management}"
CASE_DB_PASSWORD="${CASE_DB_PASSWORD:-case_management_password}"
INV_DB_NAME="${INV_DB_NAME:-investigation_service}"
INV_DB_USER="${INV_DB_USER:-investigation_service}"
INV_DB_PASSWORD="${INV_DB_PASSWORD:-investigation_service_password}"
BILLING_DB_NAME="${BILLING_DB_NAME:-billing_service}"
BILLING_DB_USER="${BILLING_DB_USER:-billing_service}"
BILLING_DB_PASSWORD="${BILLING_DB_PASSWORD:-billing_service_password}"
COMPLIANCE_DB_NAME="${COMPLIANCE_DB_NAME:-compliance_service}"
COMPLIANCE_DB_USER="${COMPLIANCE_DB_USER:-compliance_service}"
COMPLIANCE_DB_PASSWORD="${COMPLIANCE_DB_PASSWORD:-compliance_service_password}"
COUNTERPARTY_DB_NAME="${COUNTERPARTY_DB_NAME:-counterparty_service}"
COUNTERPARTY_DB_USER="${COUNTERPARTY_DB_USER:-counterparty_service}"
COUNTERPARTY_DB_PASSWORD="${COUNTERPARTY_DB_PASSWORD:-counterparty_service_password}"
NOTIFICATION_DB_NAME="${NOTIFICATION_DB_NAME:-notification_service}"
NOTIFICATION_DB_USER="${NOTIFICATION_DB_USER:-notification_service}"
NOTIFICATION_DB_PASSWORD="${NOTIFICATION_DB_PASSWORD:-notification_service_password}"
AUDIT_DB_NAME="${AUDIT_DB_NAME:-audit_service}"
AUDIT_DB_USER="${AUDIT_DB_USER:-audit_service}"
AUDIT_DB_PASSWORD="${AUDIT_DB_PASSWORD:-audit_service_password}"
ENTERPRISE_DB_NAME="${ENTERPRISE_DB_NAME:-enterprise_service}"
ENTERPRISE_DB_USER="${ENTERPRISE_DB_USER:-enterprise_service}"
ENTERPRISE_DB_PASSWORD="${ENTERPRISE_DB_PASSWORD:-enterprise_service_password}"
SANCTIONS_DB_NAME="${SANCTIONS_DB_NAME:-sanctions_service}"
SANCTIONS_DB_USER="${SANCTIONS_DB_USER:-sanctions_service}"
SANCTIONS_DB_PASSWORD="${SANCTIONS_DB_PASSWORD:-sanctions_service_password}"
RISK_DB_NAME="${RISK_DB_NAME:-risk_service}"
RISK_DB_USER="${RISK_DB_USER:-risk_service}"
RISK_DB_PASSWORD="${RISK_DB_PASSWORD:-risk_service_password}"
AI_DB_NAME="${AI_DB_NAME:-ai_service}"
AI_DB_USER="${AI_DB_USER:-ai_service}"
AI_DB_PASSWORD="${AI_DB_PASSWORD:-ai_service_password}"
REPORTING_DB_NAME="${REPORTING_DB_NAME:-reporting_service}"
REPORTING_DB_USER="${REPORTING_DB_USER:-reporting_service}"
REPORTING_DB_PASSWORD="${REPORTING_DB_PASSWORD:-reporting_service_password}"
EVENT_DB_NAME="${EVENT_DB_NAME:-event_service}"
EVENT_DB_USER="${EVENT_DB_USER:-event_service}"
EVENT_DB_PASSWORD="${EVENT_DB_PASSWORD:-event_service_password}"
TEAM_DB_NAME="${TEAM_DB_NAME:-team_service}"
TEAM_DB_USER="${TEAM_DB_USER:-team_service}"
TEAM_DB_PASSWORD="${TEAM_DB_PASSWORD:-team_service_password}"
EVIDENCE_DB_NAME="${EVIDENCE_DB_NAME:-evidence_service}"
EVIDENCE_DB_USER="${EVIDENCE_DB_USER:-evidence_service}"
EVIDENCE_DB_PASSWORD="${EVIDENCE_DB_PASSWORD:-evidence_service_password}"
BLOCKCHAIN_DB_NAME="${BLOCKCHAIN_DB_NAME:-blockchain_service}"
BLOCKCHAIN_DB_USER="${BLOCKCHAIN_DB_USER:-blockchain_service}"
BLOCKCHAIN_DB_PASSWORD="${BLOCKCHAIN_DB_PASSWORD:-blockchain_service_password}"

echo "[render-pgvector-initdb] Creating extensions in template1/postgres"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-'EOSQL'
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS btree_gin;
    CREATE EXTENSION IF NOT EXISTS btree_gist;
    CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
    CREATE EXTENSION IF NOT EXISTS unaccent;
    CREATE EXTENSION IF NOT EXISTS hstore;
    CREATE EXTENSION IF NOT EXISTS citext;
EOSQL

declare -A DATABASES=(
    ["$KEYCLOAK_DB_NAME"]="$KEYCLOAK_DB_USER:$KEYCLOAK_DB_PASSWORD"
    ["$AUTH_DB_NAME"]="$AUTH_DB_USER:$AUTH_DB_PASSWORD"
    ["$CASE_DB_NAME"]="$CASE_DB_USER:$CASE_DB_PASSWORD"
    ["$INV_DB_NAME"]="$INV_DB_USER:$INV_DB_PASSWORD"
    ["$BILLING_DB_NAME"]="$BILLING_DB_USER:$BILLING_DB_PASSWORD"
    ["$COMPLIANCE_DB_NAME"]="$COMPLIANCE_DB_USER:$COMPLIANCE_DB_PASSWORD"
    ["$COUNTERPARTY_DB_NAME"]="$COUNTERPARTY_DB_USER:$COUNTERPARTY_DB_PASSWORD"
    ["$NOTIFICATION_DB_NAME"]="$NOTIFICATION_DB_USER:$NOTIFICATION_DB_PASSWORD"
    ["$AUDIT_DB_NAME"]="$AUDIT_DB_USER:$AUDIT_DB_PASSWORD"
    ["$ENTERPRISE_DB_NAME"]="$ENTERPRISE_DB_USER:$ENTERPRISE_DB_PASSWORD"
    ["$SANCTIONS_DB_NAME"]="$SANCTIONS_DB_USER:$SANCTIONS_DB_PASSWORD"
    ["$RISK_DB_NAME"]="$RISK_DB_USER:$RISK_DB_PASSWORD"
    ["$AI_DB_NAME"]="$AI_DB_USER:$AI_DB_PASSWORD"
    ["$REPORTING_DB_NAME"]="$REPORTING_DB_USER:$REPORTING_DB_PASSWORD"
    ["$EVENT_DB_NAME"]="$EVENT_DB_USER:$EVENT_DB_PASSWORD"
    ["$TEAM_DB_NAME"]="$TEAM_DB_USER:$TEAM_DB_PASSWORD"
    ["$EVIDENCE_DB_NAME"]="$EVIDENCE_DB_USER:$EVIDENCE_DB_PASSWORD"
    ["$BLOCKCHAIN_DB_NAME"]="$BLOCKCHAIN_DB_USER:$BLOCKCHAIN_DB_PASSWORD"
)

for db in "${!DATABASES[@]}"; do
    user_pass="${DATABASES[$db]}"
    user="${user_pass%%:*}"
    pass="${user_pass#*:}"
    echo "[render-pgvector-initdb] Role '$user' / Database '$db'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
        DO \$\$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${user}') THEN
                CREATE ROLE ${user} WITH LOGIN PASSWORD '${pass}';
            ELSE
                ALTER ROLE ${user} WITH PASSWORD '${pass}';
            END IF;
        END \$\$;
EOSQL
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
        SELECT 'CREATE DATABASE ${db} OWNER ${user}' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${db}')\gexec
EOSQL
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<-EOSQL
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE EXTENSION IF NOT EXISTS btree_gin;
        CREATE EXTENSION IF NOT EXISTS btree_gist;
        CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
        CREATE EXTENSION IF NOT EXISTS unaccent;
        CREATE EXTENSION IF NOT EXISTS hstore;
        CREATE EXTENSION IF NOT EXISTS citext;
        REVOKE ALL ON DATABASE ${db} FROM PUBLIC;
        GRANT ALL PRIVILEGES ON DATABASE ${db} TO ${user};
        GRANT ALL ON SCHEMA public TO ${user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${user};
EOSQL
done

echo "[render-pgvector-initdb] DONE."
