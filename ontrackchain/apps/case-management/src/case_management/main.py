"""
Case Management Service - PostgreSQL-backed with RBAC and Evidence Trail
OnTrackChain - Graph Intelligence 4.0
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

app = FastAPI(
    title="OnTrackChain Case Management Service",
    description="Case Management with PostgreSQL persistence, RBAC, and Evidence Trail",
    version="2.0.0",
)


class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"


settings = Settings()


def _dsn() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


@app.on_event("startup")
async def _startup() -> None:
    app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})


@app.on_event("shutdown")
async def _shutdown() -> None:
    pool: ConnectionPool = app.state.pool
    pool.close()


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def _apply_rls_context(conn, org_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, True)", (org_id,))


def _require_role(x_role: Optional[str], allowed_roles: set[str], detail: str) -> str:
    normalized = (x_role or "").strip().upper()
    if normalized not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return normalized


def _resolve_persisted_user_id(cur, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    try:
        candidate = str(UUID(str(user_id)))
        cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate,))
        if cur.fetchone():
            return candidate
    except (TypeError, ValueError):
        return None
    return None


def _record_audit_log(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    metadata: dict[str, Any],
) -> None:
    normalized = dict(metadata)
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    if user_id and not persisted_user_id:
        normalized.setdefault("external_user_id", str(user_id))
    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, resource_id, json.dumps(normalized)),
    )


# ── RBAC constants ──

CASE_READ_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER", "AUDITOR", "OTK_AUDITOR", "VIEWER", "OTK_VIEWER"}
CASE_WRITE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
CASE_ADMIN_ALLOWED_ROLES = {"ADMIN"}


# ──────────────────────────────────────────────
#  MODELS
# ──────────────────────────────────────────────


class CaseCreateRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    category: str
    assigned_to: Optional[str] = None
    metadata: dict[str, Any] = {}


class CaseResponse(BaseModel):
    case_id: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    assigned_to: Optional[str]
    risk_score: Optional[float]
    created_at: str
    updated_at: str


class CaseUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CaseTimelineEntry(BaseModel):
    entry_id: str
    case_id: str
    action: str
    actor: str
    details: dict[str, Any]
    timestamp: str


class CaseMetricsResponse(BaseModel):
    total_cases: int
    open_cases: int
    closed_cases: int
    avg_resolution_time_hours: float
    cases_by_priority: dict[str, int]
    cases_by_category: dict[str, int]


class CaseListResponse(BaseModel):
    data: list[CaseResponse]
    total: int


# ──────────────────────────────────────────────
#  HEALTH
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "case-management", "version": "2.0.0"}


# ──────────────────────────────────────────────
#  LIST CASES
# ──────────────────────────────────────────────

@app.get("/api/v1/cases", response_model=CaseListResponse)
async def list_cases(
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseListResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_READ_ALLOWED_ROLES, "case_read_role_required")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, status, priority, category,
                       assigned_to, risk_score, created_at, updated_at
                FROM case_management_cases
                WHERE organization_id = %s
                ORDER BY created_at DESC
                """,
                (x_org_id,),
            )
            rows = cur.fetchall()

    cases = [
        CaseResponse(
            case_id=str(r["id"]),
            title=r["title"],
            description=r["description"],
            status=r["status"],
            priority=r["priority"],
            category=r["category"],
            assigned_to=r.get("assigned_to"),
            risk_score=r.get("risk_score"),
            created_at=r["created_at"].isoformat() if r["created_at"] else "",
            updated_at=r["updated_at"].isoformat() if r["updated_at"] else "",
        )
        for r in rows
    ]
    return CaseListResponse(data=cases, total=len(cases))


# ──────────────────────────────────────────────
#  CREATE CASE
# ──────────────────────────────────────────────

@app.post("/api/v1/cases", response_model=CaseResponse)
async def create_case(
    request_body: CaseCreateRequest,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_WRITE_ALLOWED_ROLES, "case_write_role_required")

    pool = get_pool(request)
    case_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    risk_score = _calculate_risk_score(request_body)

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO case_management_cases
                    (id, organization_id, title, description, status, priority, category,
                     assigned_to, risk_score, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                (
                    case_id, x_org_id, request_body.title, request_body.description,
                    "open", request_body.priority, request_body.category,
                    request_body.assigned_to, risk_score,
                    json.dumps(request_body.metadata), now, now,
                ),
            )

            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="case_created",
                resource_type="case_management_case",
                resource_id=case_id,
                metadata={"case_id": case_id, "title": request_body.title, "category": request_body.category},
            )
        conn.commit()

    return CaseResponse(
        case_id=case_id,
        title=request_body.title,
        description=request_body.description,
        status="open",
        priority=request_body.priority,
        category=request_body.category,
        assigned_to=request_body.assigned_to,
        risk_score=risk_score,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )


# ──────────────────────────────────────────────
#  GET CASE
# ──────────────────────────────────────────────

@app.get("/api/v1/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_READ_ALLOWED_ROLES, "case_read_role_required")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, status, priority, category,
                       assigned_to, risk_score, created_at, updated_at
                FROM case_management_cases
                WHERE id = %s AND organization_id = %s
                """,
                (case_id, x_org_id),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="case_not_found")

    return CaseResponse(
        case_id=str(row["id"]),
        title=row["title"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        category=row["category"],
        assigned_to=row.get("assigned_to"),
        risk_score=row.get("risk_score"),
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        updated_at=row["updated_at"].isoformat() if row["updated_at"] else "",
    )


# ──────────────────────────────────────────────
#  UPDATE CASE
# ──────────────────────────────────────────────

@app.put("/api/v1/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    request_body: CaseUpdateRequest,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_WRITE_ALLOWED_ROLES, "case_write_role_required")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM case_management_cases WHERE id = %s AND organization_id = %s",
                (case_id, x_org_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="case_not_found")

            updates = []
            params: list[Any] = []
            if request_body.status is not None:
                updates.append("status = %s")
                params.append(request_body.status)
            if request_body.priority is not None:
                updates.append("priority = %s")
                params.append(request_body.priority)
            if request_body.assigned_to is not None:
                updates.append("assigned_to = %s")
                params.append(request_body.assigned_to)
            if request_body.resolution is not None:
                updates.append("resolution = %s")
                params.append(request_body.resolution)
            if request_body.metadata is not None:
                updates.append("metadata = %s::jsonb")
                params.append(json.dumps(request_body.metadata))

            if not updates:
                raise HTTPException(status_code=400, detail="no_updates_provided")

            updates.append("updated_at = %s")
            params.append(datetime.now(timezone.utc))
            params.extend([case_id, x_org_id])

            cur.execute(
                f"UPDATE case_management_cases SET {', '.join(updates)} WHERE id = %s AND organization_id = %s",
                params,
            )

            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="case_updated",
                resource_type="case_management_case",
                resource_id=case_id,
                metadata={
                    "case_id": case_id,
                    "updated_fields": [k for k in ["status", "priority", "assigned_to", "resolution", "metadata"] if getattr(request_body, k) is not None],
                },
            )
        conn.commit()

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, status, priority, category,
                       assigned_to, risk_score, created_at, updated_at
                FROM case_management_cases
                WHERE id = %s AND organization_id = %s
                """,
                (case_id, x_org_id),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="case_not_found")

    return CaseResponse(
        case_id=str(row["id"]),
        title=row["title"],
        description=row["description"],
        status=row["status"],
        priority=row["priority"],
        category=row["category"],
        assigned_to=row.get("assigned_to"),
        risk_score=row.get("risk_score"),
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        updated_at=row["updated_at"].isoformat() if row["updated_at"] else "",
    )


# ──────────────────────────────────────────────
#  CASE TIMELINE
# ──────────────────────────────────────────────

@app.get("/api/v1/cases/{case_id}/timeline", response_model=list[CaseTimelineEntry])
async def get_case_timeline(
    case_id: str,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> list[CaseTimelineEntry]:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_READ_ALLOWED_ROLES, "case_read_role_required")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, case_id, action, actor, details, created_at
                FROM case_management_timeline
                WHERE case_id = %s AND organization_id = %s
                ORDER BY created_at ASC
                """,
                (case_id, x_org_id),
            )
            rows = cur.fetchall()

    return [
        CaseTimelineEntry(
            entry_id=str(r["id"]),
            case_id=str(r["case_id"]),
            action=r["action"],
            actor=r["actor"],
            details=r["details"] if isinstance(r["details"], dict) else json.loads(r["details"]) if r["details"] else {},
            timestamp=r["created_at"].isoformat() if r["created_at"] else "",
        )
        for r in rows
    ]


# ──────────────────────────────────────────────
#  CASE METRICS
# ──────────────────────────────────────────────

@app.get("/api/v1/cases/metrics", response_model=CaseMetricsResponse)
async def get_case_metrics(
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseMetricsResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_READ_ALLOWED_ROLES, "case_read_role_required")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM case_management_cases WHERE organization_id = %s",
                (x_org_id,),
            )
            total = cur.fetchone()["total"]

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM case_management_cases WHERE organization_id = %s AND status = 'open'",
                (x_org_id,),
            )
            open_cases = cur.fetchone()["cnt"]

            cur.execute(
                "SELECT COUNT(*) AS cnt FROM case_management_cases WHERE organization_id = %s AND status = 'closed'",
                (x_org_id,),
            )
            closed_cases = cur.fetchone()["cnt"]

            cur.execute(
                """
                SELECT COALESCE(
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 3600), 0
                ) AS avg_hours
                FROM case_management_cases
                WHERE organization_id = %s AND status = 'closed'
                """,
                (x_org_id,),
            )
            avg_hours = cur.fetchone()["avg_hours"] or 0.0

            cur.execute(
                """
                SELECT priority, COUNT(*) AS cnt
                FROM case_management_cases WHERE organization_id = %s
                GROUP BY priority
                """,
                (x_org_id,),
            )
            by_priority = {r["priority"]: r["cnt"] for r in cur.fetchall()}

            cur.execute(
                """
                SELECT category, COUNT(*) AS cnt
                FROM case_management_cases WHERE organization_id = %s
                GROUP BY category
                """,
                (x_org_id,),
            )
            by_category = {r["category"]: r["cnt"] for r in cur.fetchall()}

    return CaseMetricsResponse(
        total_cases=total,
        open_cases=open_cases,
        closed_cases=closed_cases,
        avg_resolution_time_hours=float(avg_hours),
        cases_by_priority=by_priority,
        cases_by_category=by_category,
    )


# ──────────────────────────────────────────────
#  INTERNAL HELPERS
# ──────────────────────────────────────────────

def _calculate_risk_score(request: CaseCreateRequest) -> float:
    base_score = 50.0
    priority_adj = {"low": -10, "medium": 0, "high": 15, "critical": 30}
    base_score += priority_adj.get(request.priority, 0)
    category_adj = {"sanctions": 20, "aml": 15, "kyc": 5, "investigation": 10}
    base_score += category_adj.get(request.category, 0)
    return min(100.0, max(0.0, base_score))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
