#!/usr/bin/env python3
# pyright: reportMissingImports=false

from __future__ import annotations

import os
import time
from pathlib import Path

import psycopg

ROOT_DIR = Path("/app")
INIT_SQL_PATH = ROOT_DIR / "infra/postgres/init.sql"
MIGRATIONS_DIR = ROOT_DIR / "infra/postgres/migrations"
LOCK_KEY = 441922170
WAIT_TIMEOUT_SECONDS = 180
WAIT_INTERVAL_SECONDS = 2


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"missing_required_env:{name}")
    return value


def _build_conninfo() -> str:
    host = _required_env("POSTGRES_HOST")
    port = _required_env("POSTGRES_PORT")
    user = _required_env("POSTGRES_USER")
    password = _required_env("POSTGRES_PASSWORD")
    database = _required_env("POSTGRES_DB")
    return f"host={host} port={port} user={user} password={password} dbname={database}"


def _wait_for_database(conninfo: str) -> None:
    deadline = time.time() + WAIT_TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with psycopg.connect(conninfo, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return
        except Exception as exc:  # pragma: no cover - network/bootstrap dependent
            last_error = exc
            time.sleep(WAIT_INTERVAL_SECONDS)

    raise RuntimeError("database_unavailable") from last_error


def _load_sanitized_init_sql(db_user: str) -> str:
    source = INIT_SQL_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    sanitized: list[str] = []
    skip_role_block = False

    for line in lines:
        stripped = line.strip()
        if stripped == "DO $$":
            skip_role_block = False
        if "CREATE ROLE db_owner NOLOGIN;" in stripped:
            skip_role_block = True
            continue
        if skip_role_block:
            if stripped == "$$;":
                skip_role_block = False
            continue
        if stripped in {
            "GRANT SELECT ON organizations TO db_owner;",
            "ALTER TABLE api_keys OWNER TO db_owner;",
            "ALTER FUNCTION validate_api_key_and_get_context(TEXT) OWNER TO db_owner;",
        }:
            continue
        if stripped == "GRANT EXECUTE ON FUNCTION validate_api_key_and_get_context(TEXT) TO ontrackchain;":
            sanitized.append(
                f"GRANT EXECUTE ON FUNCTION validate_api_key_and_get_context(TEXT) TO {db_user};"
            )
            continue
        sanitized.append(line)

    return "\n".join(sanitized) + "\n"


def _migration_files() -> list[Path]:
    return sorted(
        path
        for path in MIGRATIONS_DIR.iterdir()
        if path.is_file() and path.suffix == ".sql" and path.name != "README.md"
    )


def main() -> None:
    conninfo = _build_conninfo()
    db_user = _required_env("POSTGRES_USER")
    _wait_for_database(conninfo)

    with psycopg.connect(conninfo, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (LOCK_KEY,))
            try:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS render_schema_migrations (
                      filename TEXT PRIMARY KEY,
                      applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )

                cur.execute("SELECT to_regclass('public.organizations') IS NOT NULL")
                schema_exists = bool(cur.fetchone()[0])
                if not schema_exists:
                    cur.execute(_load_sanitized_init_sql(db_user))

                for migration_path in _migration_files():
                    cur.execute(
                        "SELECT 1 FROM render_schema_migrations WHERE filename = %s",
                        (migration_path.name,),
                    )
                    already_applied = cur.fetchone() is not None
                    if already_applied:
                        continue
                    cur.execute(migration_path.read_text(encoding="utf-8"))
                    cur.execute(
                        "INSERT INTO render_schema_migrations (filename) VALUES (%s)",
                        (migration_path.name,),
                    )

                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))


if __name__ == "__main__":
    main()
