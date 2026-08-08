import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from case_management.main import app

TEST_ORG_ID = "00000000-0000-0000-0000-000000000001"
TEST_ORG_NAME = "E2E Test Org"
TEST_ORG_PLAN = "professional"


@pytest.fixture(scope="session")
def db_pool() -> Iterator[ConnectionPool]:
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "ontrackchain")
    password = os.environ.get("POSTGRES_PASSWORD", "ontrackchain")
    dbname = os.environ.get("POSTGRES_DB", "ontrackchain")
    conninfo = (
        f"host={host} port={port} dbname={dbname} "
        f"user={user} password={password}"
    )
    pool = ConnectionPool(conninfo=conninfo, kwargs={"row_factory": dict_row}, open=True)
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO organizations (id, name, plan) VALUES (%s, %s, %s) "
                    "ON CONFLICT (id) DO NOTHING",
                    (TEST_ORG_ID, TEST_ORG_NAME, TEST_ORG_PLAN),
                )
            conn.commit()
        yield pool
    finally:
        pool.close()


@pytest.fixture(autouse=True)
def _seed_org_and_truncate(db_pool: ConnectionPool) -> Iterator[None]:
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (id, name, plan) VALUES (%s, %s, %s) "
                "ON CONFLICT (id) DO NOTHING",
                (TEST_ORG_ID, TEST_ORG_NAME, TEST_ORG_PLAN),
            )
            cur.execute("TRUNCATE TABLE case_management_timeline CASCADE")
            cur.execute("TRUNCATE TABLE case_management_cases CASCADE")
            cur.execute("TRUNCATE TABLE audit_logs CASCADE")
            cur.execute("TRUNCATE TABLE cases CASCADE")
        conn.commit()
    yield


@pytest.fixture()
def client(db_pool: ConnectionPool, monkeypatch) -> Iterator[TestClient]:
    shutdown_fn = getattr(app.router, "shutdown_routers", None)

    real_pool_close = ConnectionPool.close

    def _safe_pool_close(self, *args, **kwargs):
        try:
            is_shared = self is db_pool
        except Exception:  # noqa: BLE001
            is_shared = False
        if is_shared:
            return
        return real_pool_close(self, *args, **kwargs)

    monkeypatch.setattr(ConnectionPool, "close", _safe_pool_close)

    app.state.pool = db_pool
    with TestClient(app, backend_options={"use_uvloop": False}) as c:
        yield c
