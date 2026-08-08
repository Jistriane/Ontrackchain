from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ai_service.main import app

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from _helpers import ORG_ID, _dsn  # noqa: E402


@pytest.fixture(scope="session")
def db_pool() -> Iterator[ConnectionPool]:
    pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
    try:
        yield pool
    finally:
        pool.close()


@pytest.fixture(autouse=True)
def _seed_org_and_truncate(db_pool: ConnectionPool) -> Iterator[None]:
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO organizations (id, name, created_at, updated_at)
                VALUES (%s::uuid, 'seeded-org-test', NOW(), NOW())
                ON CONFLICT (id) DO NOTHING
                """,
                (ORG_ID,),
            )
            cur.execute("TRUNCATE TABLE ai_service_jobs CASCADE")
            cur.execute("TRUNCATE TABLE ai_analysis_results CASCADE")
            cur.execute("TRUNCATE TABLE cases CASCADE")
            cur.execute("TRUNCATE TABLE audit_logs CASCADE")
        conn.commit()
    yield


@pytest.fixture()
def client(db_pool: ConnectionPool, monkeypatch) -> Iterator[TestClient]:
    real_pool_close = ConnectionPool.close

    def _safe_pool_close(self, *args, **kwargs):
        try:
            shared = self is db_pool
        except Exception:  # noqa: BLE001
            shared = False
        if shared:
            return
        return real_pool_close(self, *args, **kwargs)

    monkeypatch.setattr(ConnectionPool, "close", _safe_pool_close)

    app.state.pool = db_pool
    with TestClient(app) as c:
        yield c
