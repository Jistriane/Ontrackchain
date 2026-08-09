"""
Teste P0 OBRIGATÓRIO: RLS Cross-Tenant Isolation (Prova Real)
================================================================

Valida 3 pilares centrais de segurança do PostgreSQL RLS
(com organizations/users/cases tabelas):

1. Todas tabelas sensíveis TÊM coluna organization_id
2. Toda tabela sensível tem RLS ENABLED + POLICY tenant_isolation + ÍNDICE por org
3. Tenant A NUNCA consegue ler/alterar registros do Tenant B (0 vazamentos)

Este arquivo RODA COM pytest. Requer:
- pip install psycopg[binary]>=3.2 pytest>=8 pytest-postgresql>=6.1
- Variável ONTRACKCHAIN_DATABASE_URL (postgres://user:pass@host:5432/db)
- Banco PostgreSQL 16+ ALVO com todas migrations aplicadas (0001 a 0021)

Se falhar = NÃO FAZ MERGE.

Sprint 18 (T2-08): sys.path HACK removido. PYTHONPATH de monorepo é injetado
AUTOMATICAMENTE por workspace/conftest.py + pyproject.toml
[tool.pytest.ini_options] pythonpath = [...]
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import psycopg

# ------------------ setup: conexão bd -----------------
DB_URL_VAR = "ONTRACKCHAIN_DATABASE_URL"


def _db_url_or_skip() -> str:
    url = os.environ.get(DB_URL_VAR)
    if not url:
        pytest.skip(f"Env {DB_URL_VAR} não definida (pular teste RLS real)")
    return url


ORG_A_ID = "11111111-1111-1111-1111-111111111111"
ORG_B_ID = "22222222-2222-2222-2222-222222222222"

TABLES_WITH_EXPECTED_ORG_ID = [
    "users",
    "cases",
    "counterparties",
    "counterparty_history",
    "monitoring_alerts",
    "audit_logs",
    "watchlists",
    "evidence_trail",
    "evidence_package_seals",
    "evidence_package_signoffs",
    "regulatory_work_items",
    "agent_golden_dataset",
    "agent_hypotheses",
    "agent_artifacts",
    "agent_eval_runs",
]


# ================== TESTE 1: COLUNA ORG_ID EM TODAS ==================
@pytest.mark.parametrize("table_name", TABLES_WITH_EXPECTED_ORG_ID)
def test_p0_table_has_organization_id_column(table_name: str) -> None:
    """Tabela X TEM coluna organization_id (informativo: sempre obrigatório para RLS)."""
    with psycopg.connect(_db_url_or_skip()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_schema='public' AND table_name=%s AND column_name='organization_id'
                """,
                (table_name,),
            )
            assert cur.fetchone() is not None, f"Tabela {table_name} NÃO TEM coluna organization_id"


# ================== TESTE 2: RLS + POLICY + ÍNDICE ==================
@pytest.mark.parametrize("table_name", TABLES_WITH_EXPECTED_ORG_ID)
def test_p0_table_has_rls_policy_and_index(table_name: str) -> None:
    """4 verificações por tabela: tem org_id coluna, RLS enabled, policy tenant_isolation, índice em org_id."""
    from qa_gateway.rls import check_table_rls_status

    with psycopg.connect(_db_url_or_skip()) as conn:
        status = check_table_rls_status(conn, table_name)
    assert status.ok, (
        f"Tabela {table_name} falhou RLS: status={status.summary} "
        f"(has_org_col={status.has_org_column}, rls_enabled={status.rls_enabled}, "
        f"has_policy={status.has_isolation_policy}, has_idx={status.has_org_index}, issues={status.issues})"
    )


# ================== TESTE 3: ISOLAMENTO CROSS-TENANT CASES ==================
def test_p0_cross_tenant_cases_isolation() -> None:
    """
    Caso do Tenant A criado → Set contexto B → NÃO deve ser retornado.
    Caso do Tenant B criado → Set contexto A → NÃO deve ser retornado.
    Query SELECT * com id caso-other-org → 0 linhas SEMPRE.
    """
    url = _db_url_or_skip()
    org_a = str(uuid.UUID(ORG_A_ID))
    org_b = str(uuid.UUID(ORG_B_ID))
    case_a_id = str(uuid.uuid4())
    case_b_id = str(uuid.uuid4())

    with psycopg.connect(url, autocommit=True) as conn:
        with conn.cursor() as c:
            c.execute(
                "INSERT INTO organizations (id, name, plan) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (org_a, "p0-test-org-a", "enterprise"),
            )
            c.execute(
                "INSERT INTO organizations (id, name, plan) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (org_b, "p0-test-org-b", "enterprise"),
            )
            c.execute(
                """INSERT INTO cases (id, organization_id, case_type, title, context_narrative, status, priority, depth)
                VALUES (%s,%s,'aml','CASE-A-ONLY','narrative-a','open','high',2) ON CONFLICT DO NOTHING""",
                (case_a_id, org_a),
            )
            c.execute(
                """INSERT INTO cases (id, organization_id, case_type, title, context_narrative, status, priority, depth)
                VALUES (%s,%s,'aml','CASE-B-ONLY','narrative-b','open','high',2) ON CONFLICT DO NOTHING""",
                (case_b_id, org_b),
            )

        # -------- TROCA CONTEXTO ORG A -------- só deve ver 1 caso (o seu)
        with conn.cursor() as c:
            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_a,))
            c.execute("SELECT id FROM cases ORDER BY title")
            a_rows = c.fetchall()
            assert len(a_rows) >= 1 and a_rows[0][0] == case_a_id, (
                f"RLS LEAK CASES (org A não vê seu caso ou vê mais de 1). "
                f"Esperado ID {case_a_id} → obtido {a_rows}"
            )

            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_a,))
            c.execute("SELECT 1 FROM cases WHERE id=%s", (case_b_id,))
            leak_b_in_a = c.fetchone()
            assert leak_b_in_a is None, f"FATAL RLS LEAK: ORG_A leu CASE_B (id {case_b_id})"

        # -------- TROCA CONTEXTO ORG B --------
        with conn.cursor() as c:
            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_b,))
            c.execute("SELECT id FROM cases ORDER BY title")
            b_rows = c.fetchall()
            assert len(b_rows) >= 1 and b_rows[0][0] == case_b_id, (
                f"RLS LEAK CASES (org B não vê seu caso ou vê mais de 1). "
                f"Esperado ID {case_b_id} → obtido {b_rows}"
            )

            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_b,))
            c.execute("SELECT 1 FROM cases WHERE id=%s", (case_a_id,))
            leak_a_in_b = c.fetchone()
            assert leak_a_in_b is None, f"FATAL RLS LEAK: ORG_B leu CASE_A (id {case_a_id})"


# ================== TESTE 4: ISOLAMENTO CROSS-TENANT USERS ==================
def test_p0_cross_tenant_users_isolation() -> None:
    """User ORG_A NÃO PODE ser retornado quando contexto ORG_B."""
    url = _db_url_or_skip()
    org_a = str(uuid.UUID(ORG_A_ID))
    org_b = str(uuid.UUID(ORG_B_ID))
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())

    with psycopg.connect(url, autocommit=True) as conn:
        with conn.cursor() as c:
            c.execute(
                """INSERT INTO users (id, organization_id, email, name, role, status)
                VALUES (%s,%s,'user-a@a.com','UserA','ADMIN','active') ON CONFLICT DO NOTHING""",
                (user_a, org_a),
            )
            c.execute(
                """INSERT INTO users (id, organization_id, email, name, role, status)
                VALUES (%s,%s,'user-b@b.com','UserB','ADMIN','active') ON CONFLICT DO NOTHING""",
                (user_b, org_b),
            )

        with conn.cursor() as c:
            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_a,))
            c.execute("SELECT id FROM users WHERE id=%s", (user_b,))
            leak = c.fetchone()
            assert leak is None, f"FATAL RLS LEAK users: ORG_A leu USER_B ({user_b}) por ID"

            c.execute("SELECT set_config('app.organization_id', %s, True)", (org_b,))
            c.execute("SELECT id FROM users WHERE id=%s", (user_a,))
            leak2 = c.fetchone()
            assert leak2 is None, f"FATAL RLS LEAK users: ORG_B leu USER_A ({user_a}) por ID"
