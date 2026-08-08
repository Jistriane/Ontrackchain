from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

RLS_STATUS_OK = "enabled+policy"
RLS_STATUS_NO_ORG_COLUMN = "no_org_column"
RLS_STATUS_RLS_DISABLED = "rls_disabled"
RLS_STATUS_NO_POLICY = "no_policy"
RLS_STATUS_NO_INDEX = "no_index_on_organization_id"


TABLES_EXPECTED_TO_HAVE_ORG_ID = frozenset(
    [
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
)


@dataclass
class RLSStatus:
    table_name: str
    has_org_column: bool = False
    rls_enabled: bool = False
    has_isolation_policy: bool = False
    has_org_index: bool = False
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.has_org_column
            and self.rls_enabled
            and self.has_isolation_policy
            and self.has_org_index
            and not self.issues
        )

    @property
    def summary(self) -> str:
        if self.ok:
            return RLS_STATUS_OK
        return ", ".join(self.issues) if self.issues else "unknown"


def list_tables_with_organization_id(
    conn,
    expected_tables: Iterable[str] = TABLES_EXPECTED_TO_HAVE_ORG_ID,
) -> list[str]:
    """Retorna tabelas (dentre esperadas) que TEM coluna organization_id."""
    found: list[str] = []
    expected = list(expected_tables)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
              FROM information_schema.columns
             WHERE column_name = 'organization_id'
               AND table_schema = 'public'
               AND table_name = ANY(%s)
            """,
            (expected,),
        )
        for row in cur.fetchall():
            found.append(row[0])
    return found


def check_table_rls_status(conn, table_name: str) -> RLSStatus:
    """Checa 4 pilares de RLS seguro para 1 tabela."""
    status = RLSStatus(table_name=table_name)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_schema='public' AND table_name=%s AND column_name='organization_id'
                """,
                (table_name,),
            )
            if cur.fetchone() is None:
                status.issues.append(RLS_STATUS_NO_ORG_COLUMN)
                return status
            status.has_org_column = True

            cur.execute(
                "SELECT relrowsecurity FROM pg_class WHERE relname = %s AND relnamespace = 'public'::regnamespace",
                (table_name,),
            )
            row = cur.fetchone()
            if row is None or not row[0]:
                status.issues.append(RLS_STATUS_RLS_DISABLED)
            else:
                status.rls_enabled = True

            cur.execute(
                """
                SELECT COUNT(*) FROM pg_policy
                 WHERE schemaname='public'
                   AND tablename=%s
                   AND polname LIKE '%%tenant_isolation%%'
                """,
                (table_name,),
            )
            count = cur.fetchone()[0]
            if count <= 0:
                status.issues.append(RLS_STATUS_NO_POLICY)
            else:
                status.has_isolation_policy = True

            cur.execute(
                """
                SELECT COUNT(*) FROM pg_indexes
                 WHERE schemaname='public'
                   AND tablename=%s
                   AND indexdef LIKE '%%organization_id%%'
                """,
                (table_name,),
            )
            idx_count = cur.fetchone()[0]
            if idx_count <= 0:
                status.issues.append(RLS_STATUS_NO_INDEX)
            else:
                status.has_org_index = True
    except Exception as exc:  # noqa: BLE001
        status.issues.append(f"error: {exc}")
    return status


def scan_all_rls_tables(
    conn,
    expected_tables: Iterable[str] = TABLES_EXPECTED_TO_HAVE_ORG_ID,
) -> list[RLSStatus]:
    """Executa check_table_rls_status em TODAS tabelas esperadas."""
    return [check_table_rls_status(conn, t) for t in expected_tables]


def assert_tables_have_rls(
    conn,
    expected_tables: Iterable[str] = TABLES_EXPECTED_TO_HAVE_ORG_ID,
) -> tuple[bool, list[RLSStatus]]:
    """Asserção central (usada em CI gate). Retorna (tudo_ok?, lista status)."""
    statuses = scan_all_rls_tables(conn, expected_tables)
    all_ok = all(s.ok for s in statuses)
    return all_ok, statuses
