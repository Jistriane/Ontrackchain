from __future__ import annotations

import json
import os
import uuid

from psycopg.types.json import Jsonb

ORG_ID = "00000000-0000-0000-0000-000000000001"


def _dsn() -> str:
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    user = os.environ.get("POSTGRES_USER", "ontrackchain")
    password = os.environ.get("POSTGRES_PASSWORD", "ontrackchain")
    db = os.environ.get("POSTGRES_DB", "ontrackchain")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def seed_case(
    db_pool,
    *,
    case_id: str | None = None,
    title: str = "Seeded Case",
    context_narrative: str = "Seeded for pytest",
    case_type: str = "investigation",
    priority: str = "medium",
    status: str = "open",
    target_address: str = "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",
    target_chain: str = "ethereum",
    depth: int = 3,
    org_id: str = ORG_ID,
    extra_metadata: dict | None = None,
) -> str:
    cid = case_id or str(uuid.uuid4())
    metadata = Jsonb({**(extra_metadata or {})})
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, true)", (org_id,))
            cur.execute(
                """
                INSERT INTO cases (
                    id, organization_id, case_type, title, context_narrative,
                    status, priority, target_address, target_chain, depth, metadata,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    cid, org_id, case_type, title, context_narrative,
                    status, priority, target_address, target_chain, depth, metadata,
                ),
            )
        conn.commit()
    return cid
