"""
Case Management Service - PostgreSQL-backed with RBAC and Evidence Trail
OnTrackChain - Graph Intelligence 4.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)


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


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    _app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
    try:
        yield
    finally:
        pool: Optional[ConnectionPool] = getattr(_app.state, "pool", None)
        if pool is not None:
            pool.close()


app = FastAPI(
    title="OnTrackChain Case Management Service",
    description="Case Management with PostgreSQL persistence, RBAC, and Evidence Trail",
    version="2.0.0",
    lifespan=_lifespan,
)


# ==========================================================================
# RLS CONTEXT INJECTION MIDDLEWARE (Habilita isolamento multi-tenant)
# Fonte Única: packages/shared/src/ontrackchain_shared/middleware_rls.py
# Strategy: Shared Package First → Fallback Inline (compatível host antigo)
# ==========================================================================
try:  # SHARED PACKAGE FIRST
    from ontrackchain_shared.middleware_rls import register_rls_context_middleware as _register_rls_mw

    def _get_pool_for_rls(request: Request) -> ConnectionPool:
        return get_pool(request)

    _register_rls_mw(app, get_pool_sync_fn=_get_pool_for_rls)
    del _register_rls_mw, _get_pool_for_rls
except Exception as _mw_exc:  # noqa: BLE001 — FALLBACK INLINE (host sem shared package)
    import logging as _mw_log

    _mw_log.getLogger(__name__).warning(
        "case-management: RLS middleware shared package import failed (%s). Using inline fallback.",
        type(_mw_exc).__name__,
    )
    import re as _mw_re
    import uuid as _mw_uuid

    _MW_RLS_BYPASS = frozenset(
        {"/", "/health", "/healthz", "/ready", "/metrics", "/docs", "/docs/", "/openapi.json", "/redoc"}
    )
    _MW_RLS_BYPASS_PFX = ("/public/", "/health", "/docs", "/openapi", "/auth/", "/static/")
    _MW_UUID_RE = _mw_re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )

    def _mw_is_uuid(s: object) -> bool:
        if s is None:
            return False
        s2 = str(s).strip()
        if _MW_UUID_RE.match(s2):
            return True
        try:
            _mw_uuid.UUID(s2)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _mw_path_needs(p: str) -> bool:
        if p in _MW_RLS_BYPASS:
            return False
        return not any(p.startswith(x) for x in _MW_RLS_BYPASS_PFX)

    def _mw_extract(request: Request) -> "str | None":
        raw = request.headers.get("X-Organization-Id")
        if raw and _mw_is_uuid(raw):
            return str(_mw_uuid.UUID(str(raw).strip()))
        q = request.query_params.get("organization_id") or request.query_params.get("org_id")
        if q and _mw_is_uuid(q):
            return str(_mw_uuid.UUID(str(q).strip()))
        return None

    try:
        from starlette.middleware.base import BaseHTTPMiddleware as _MWBase

        class _RlsInlineMiddleware(_MWBase):
            async def dispatch(self, request: Request, call_next):  # type: ignore[override]
                path = request.url.path or request.scope.get("path", "/")
                if not _mw_path_needs(path):
                    return await call_next(request)
                org_id = _mw_extract(request)
                if not org_id:
                    raise HTTPException(
                        status_code=401,
                        detail="SECURITY-RLS-VIOLATION-NO-CONTEXT: missing X-Organization-Id header or org_id JWT claim",
                    )
                pool_obj = get_pool(request)
                try:
                    with pool_obj.connection() as _c:
                        with _c.cursor() as _cur:
                            _cur.execute(
                                "SELECT set_config('app.organization_id', %s, True)",
                                (str(_mw_uuid.UUID(org_id)),),
                            )
                except HTTPException:
                    raise
                except Exception as _x:  # noqa: BLE001
                    raise HTTPException(
                        status_code=500,
                        detail=f"SECURITY-RLS-CONTEXT-SET-FAILED: {type(_x).__name__}",
                    )
                try:
                    setattr(request.state, "current_organization_id", org_id)
                except Exception:  # noqa: BLE001
                    pass
                return await call_next(request)

        app.add_middleware(_RlsInlineMiddleware)
    except Exception as _fb_exc:  # noqa: BLE001
        _mw_log.getLogger(__name__).warning(
            "case-management: RLS inline fallback ALSO failed (%s). RLS NOT ACTIVE!", type(_fb_exc).__name__
        )
    del _mw_log, _mw_re, _mw_uuid


# ==========================================================================
# OBSERVABILIDADE M16b: /healthz (liveness) + /metrics (Prometheus)
# Gate CI Obrigatório: observability-endpoints-gate bloqueia merge se ausente
# Strategy: Try prometheus_fastapi_instrumentator primeiro, fallback inline
# ==========================================================================
@app.get("/healthz", tags=["Observabilidade"], summary="Liveness Probe Kubernetes / SRE")
async def healthz_liveness_probe():
    return {
        "status": "ok",
        "service": "case-management",
        "version": "2.0.0",
        "liveness": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

try:
    from prometheus_fastapi_instrumentator import Instrumentator as _PromInstrumentator
    _PromInstrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception:  # noqa: BLE001 - fallback inline sempre funciona, sem dependencia
    from fastapi.responses import PlainTextResponse as _FallbackPlainText

    _FALLBACK_METRICS_BASE = """# HELP fastapi_info Info about the running FastAPI service.
# TYPE fastapi_info gauge
fastapi_info{service="case-management",version="2.0.0"} 1.0
# HELP http_requests_total Total HTTP requests (fallback inline, sem middleware).
# TYPE http_requests_total counter
http_requests_total{service="case-management",endpoint="/healthz",method="GET",status_code="200"} 0
# HELP up Liveness probe (1 = UP).
# TYPE up gauge
up{service="case-management"} 1.0
"""

    @app.get("/metrics", include_in_schema=False, response_class=_FallbackPlainText)
    async def fallback_metrics_prometheus_text_format():
        import time as _fb_time
        now_unix = _fb_time.time()
        body = _FALLBACK_METRICS_BASE + f"# HELP metrics_scrape_timestamp_seconds Unix UTC scrape timestamp.\n# TYPE metrics_scrape_timestamp_seconds gauge\nmetrics_scrape_timestamp_seconds{{service=\"case-management\"}} {now_unix}\n"
        return body.rstrip() + "\n"


def get_pool(request: Request) -> ConnectionPool:
    pool: Optional[ConnectionPool] = getattr(request.app.state, "pool", None)
    if pool is None:
        pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
        request.app.state.pool = pool
    return pool


def _apply_rls_context(conn, org_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, True)", (org_id,))


try:
    from ontrackchain_shared.auth import canonicalize_role as _canonicalize_role
except Exception:  # noqa: BLE001 - fallback inline for host / old environments
    def _canonicalize_role(raw_role: object) -> str:
        if raw_role is None:
            return ""
        role = str(raw_role).strip()
        if not role:
            return ""
        mapping = {
            "OTK_ADMIN": "ADMIN",
            "OTK_ANALYST": "ANALYST",
            "OTK_AUDITOR": "AUDITOR",
            "OTK_VIEWER": "VIEWER",
            "OTK_COMPLIANCE_OFFICER": "COMPLIANCE_OFFICER",
            "OTK_LEGAL_REVIEWER": "LEGAL_REVIEWER",
            "OTK_TESTER": "TESTER",
            "OTK_REVIEWER": "REVIEWER",
            "OTK_BILLING_ADMIN": "BILLING_ADMIN",
        }
        if role in mapping:
            return mapping[role]
        if role.upper() in mapping:
            return mapping[role.upper()]
        return role.upper()


def _require_role(x_role: Optional[str], allowed_roles: set[str], detail: str) -> str:
    normalized = _canonicalize_role(x_role)
    if normalized not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return normalized


def _record_authorization_denial(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    effective_role: str,
    allowed_roles: set[str],
    detail: str,
    resource_type: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> None:
    try:
        with pool.connection() as conn:
            _apply_rls_context(conn, organization_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur,
                    organization_id=organization_id,
                    user_id=user_id,
                    action="authorization_denied",
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id is not None else None,
                    metadata={
                        "request_id": request_id,
                        "auth_role": effective_role,
                        "allowed_roles": sorted(allowed_roles),
                        "detail": detail,
                        "endpoint": endpoint,
                        "method": method,
                        "external_user_id": external_user_id,
                    },
                )
            conn.commit()
    except Exception:
        logger.exception("failed_to_record_authorization_denial")


def _require_role_with_audit(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
    allowed_roles: set[str],
    detail: str,
    resource_type: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> str:
    normalized = _canonicalize_role(x_role)
    if normalized not in {_canonicalize_role(r) for r in allowed_roles}:
        _record_authorization_denial(
            pool,
            organization_id=organization_id,
            user_id=user_id,
            external_user_id=external_user_id,
            request_id=request_id,
            effective_role=normalized,
            allowed_roles=allowed_roles,
            detail=detail,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
        )
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

CASE_READ_ALLOWED_ROLES = {
    "ADMIN", "OTK_ADMIN",
    "ANALYST", "OTK_ANALYST",
    "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER",
    "AUDITOR", "OTK_AUDITOR",
    "VIEWER", "OTK_VIEWER",
    "LEGAL_REVIEWER", "OTK_LEGAL_REVIEWER",
    "REVIEWER", "OTK_REVIEWER",
}
CASE_WRITE_ALLOWED_ROLES = {
    "ADMIN", "OTK_ADMIN",
    "ANALYST", "OTK_ANALYST",
    "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER",
}
CASE_ADMIN_ALLOWED_ROLES = {"ADMIN", "OTK_ADMIN"}
CASE_EXPORT_ALLOWED_ROLES = {
    "ADMIN", "OTK_ADMIN",
    "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER",
    "LEGAL_REVIEWER", "OTK_LEGAL_REVIEWER",
}
CASE_DLQ_ADMIN_ALLOWED_ROLES = {
    "ADMIN", "OTK_ADMIN",
    "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER",
    "AUDITOR", "OTK_AUDITOR",
}


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


class DlqInvestigationItem(BaseModel):
    case_id: str
    status: str
    dlq_state: str
    created_at: str
    completed_at: Optional[str]
    metadata: dict[str, Any]


class DlqListResponse(BaseModel):
    data: list[DlqInvestigationItem]
    total: int
    state: str


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
    pool = get_pool(request)
    _request_id = str(uuid.uuid4())
    canonical_role = _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=x_user_id,
        external_user_id=None,
        request_id=_request_id,
        x_role=x_role,
        allowed_roles=CASE_WRITE_ALLOWED_ROLES,
        detail="case_write_role_required",
        resource_type="case_management_case",
        resource_id=None,
        endpoint="/api/v1/cases",
        method="POST",
    )
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

    asyncio.create_task(
        _async_generate_case_insights(
            case_id=case_id,
            org_id=x_org_id,
            user_id=x_user_id,
            role=canonical_role,
        )
    )

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
#  CASE METRICS (must be declared before /api/v1/cases/{case_id} to avoid UUID param capture)
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
#  CASE TIMELINE (must be declared before /api/v1/cases/{case_id} to avoid UUID param capture)
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
#  DLQ INVESTIGATION ADMIN (declared before /{case_id} to avoid UUID param capture)
# ──────────────────────────────────────────────

@app.get("/api/v1/cases/investigation-dlq", response_model=DlqListResponse)
async def list_investigation_dlq(
    request: Request,
    state: str = "failed_permanent",
    limit: int = 50,
    offset: int = 0,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> DlqListResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, CASE_DLQ_ADMIN_ALLOWED_ROLES, "dlq_admin_role_required")

    valid_states = {"failed_permanent", "acknowledged", "discarded"}
    if state not in valid_states:
        raise HTTPException(status_code=400, detail=f"invalid_state_expected_one_of_{sorted(valid_states)}")

    pool = get_pool(request)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM cases
                WHERE organization_id = %s
                  AND case_type = 'investigation'
                  AND metadata->>'dlq_state' = %s
                """,
                (x_org_id, state),
            )
            total = cur.fetchone()["total"]

            cur.execute(
                """
                SELECT id, status, metadata, created_at, completed_at
                FROM cases
                WHERE organization_id = %s
                  AND case_type = 'investigation'
                  AND metadata->>'dlq_state' = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (x_org_id, state, limit, offset),
            )
            rows = cur.fetchall()

    items = [
        DlqInvestigationItem(
            case_id=str(r["id"]),
            status=r["status"] or "",
            dlq_state=(r["metadata"] or {}).get("dlq_state", state) if isinstance(r["metadata"], dict) else state,
            created_at=r["created_at"].isoformat() if r["created_at"] else "",
            completed_at=r["completed_at"].isoformat() if r["completed_at"] else None,
            metadata=r["metadata"] if isinstance(r["metadata"], dict) else {},
        )
        for r in rows
    ]
    return DlqListResponse(data=items, total=total, state=state)


@app.post("/api/v1/cases/investigation-dlq/{case_id}/requeue")
async def requeue_investigation_dlq(
    case_id: str,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> dict[str, Any]:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    pool = get_pool(request)
    _request_id = str(uuid.uuid4())
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=x_user_id,
        external_user_id=None,
        request_id=_request_id,
        x_role=x_role,
        allowed_roles=CASE_DLQ_ADMIN_ALLOWED_ROLES,
        detail="dlq_admin_role_required",
        resource_type="investigation_case",
        resource_id=case_id,
        endpoint="/api/v1/cases/investigation-dlq/{case_id}/requeue",
        method="POST",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, metadata
                FROM cases
                WHERE id = %s AND organization_id = %s AND case_type = 'investigation'
                """,
                (case_id, x_org_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="investigation_case_not_found")

            metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
            if metadata.get("dlq_state") not in {"failed_permanent", "acknowledged"}:
                raise HTTPException(status_code=409, detail="dlq_case_not_in_requeueable_state")

            requeue_count = int(metadata.get("dlq_requeue_count", 0) or 0) + 1
            metadata["dlq_requeue_count"] = requeue_count
            metadata["dlq_state"] = "requeued"
            metadata["dlq_last_requeued_at"] = datetime.now(timezone.utc).isoformat()
            if x_user_id:
                metadata["dlq_last_requeued_by"] = str(x_user_id)

            cur.execute(
                """
                UPDATE cases
                SET status = 'queued',
                    metadata = %s::jsonb,
                    completed_at = NULL
                WHERE id = %s AND organization_id = %s
                """,
                (json.dumps(metadata), case_id, x_org_id),
            )

            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="investigation_dlq_requeued",
                resource_type="investigation_case",
                resource_id=case_id,
                metadata={"case_id": case_id, "requeue_count": requeue_count},
            )
        conn.commit()

    return {"status": "requeued", "case_id": case_id, "requeue_count": requeue_count}


@app.post("/api/v1/cases/investigation-dlq/{case_id}/acknowledge")
async def acknowledge_investigation_dlq(
    case_id: str,
    request: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> dict[str, Any]:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    pool = get_pool(request)
    _request_id = str(uuid.uuid4())
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=x_user_id,
        external_user_id=None,
        request_id=_request_id,
        x_role=x_role,
        allowed_roles=CASE_DLQ_ADMIN_ALLOWED_ROLES,
        detail="dlq_admin_role_required",
        resource_type="investigation_case",
        resource_id=case_id,
        endpoint="/api/v1/cases/investigation-dlq/{case_id}/acknowledge",
        method="POST",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, metadata
                FROM cases
                WHERE id = %s AND organization_id = %s AND case_type = 'investigation'
                """,
                (case_id, x_org_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="investigation_case_not_found")

            metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
            if metadata.get("dlq_state") != "failed_permanent":
                raise HTTPException(status_code=409, detail="dlq_case_not_in_failed_permanent_state")

            metadata["dlq_state"] = "acknowledged"
            metadata["dlq_acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            if x_user_id:
                metadata["dlq_acknowledged_by"] = str(x_user_id)

            cur.execute(
                """
                UPDATE cases
                SET status = 'acknowledged',
                    metadata = %s::jsonb
                WHERE id = %s AND organization_id = %s
                """,
                (json.dumps(metadata), case_id, x_org_id),
            )

            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="investigation_dlq_acknowledged",
                resource_type="investigation_case",
                resource_id=case_id,
                metadata={"case_id": case_id},
            )
        conn.commit()

    return {"status": "acknowledged", "case_id": case_id}


# ──────────────────────────────────────────────
#  GET CASE (catch-all UUID route, declared last)
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
    pool = get_pool(request)
    _request_id = str(uuid.uuid4())
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=x_user_id,
        external_user_id=None,
        request_id=_request_id,
        x_role=x_role,
        allowed_roles=CASE_WRITE_ALLOWED_ROLES,
        detail="case_write_role_required",
        resource_type="case_management_case",
        resource_id=case_id,
        endpoint="/api/v1/cases/{case_id}",
        method="PUT",
    )
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
#  INTERNAL HELPERS
# ──────────────────────────────────────────────

def _calculate_risk_score(request: CaseCreateRequest) -> float:
    base_score = 50.0
    priority_adj = {"low": -10, "medium": 0, "high": 15, "critical": 30}
    base_score += priority_adj.get(request.priority, 0)
    category_adj = {"sanctions": 20, "aml": 15, "kyc": 5, "investigation": 10}
    base_score += category_adj.get(request.category, 0)
    return min(100.0, max(0.0, base_score))


async def _async_generate_case_insights(
    *,
    case_id: str,
    org_id: str,
    user_id: Optional[str],
    role: str,
) -> None:
    try:
        import os
        ai_service_url = os.environ.get("AI_SERVICE_URL", "http://ai-service:8005")

        pool: Optional[ConnectionPool] = getattr(app.state, "pool", None)
        if pool is None:
            pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
            app.state.pool = pool

        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT title, description, category FROM case_management_cases WHERE id = %s AND organization_id = %s",
                    (case_id, org_id),
                )
                row = cur.fetchone()
                if not row:
                    logger.warning("case-insights: case %s not found for org %s", case_id, org_id)
                    return

                case_title = row["title"]
                case_description = row["description"]
                case_category = row["category"]

        headers = {
            "X-Org-Id": org_id,
            "X-User-Id": user_id or "",
            "X-Role": role or "ADMIN",
            "Content-Type": "application/json",
        }
        payload = {
            "case_id": case_id,
            "title": case_title,
            "description": case_description,
            "category": case_category,
        }

        logger.info("case-insights: calling ai-service for case %s", case_id)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{ai_service_url}/api/v1/ai/case-insights",
                headers=headers,
                json=payload,
            )

        if resp.status_code != 200:
            logger.warning(
                "case-insights: ai-service returned %s for case %s: %s",
                resp.status_code, case_id, resp.text[:200],
            )
            return

        data = resp.json()
        insight_id = data.get("insight_id") or data.get("analysis_id")
        if not insight_id:
            logger.warning("case-insights: no insight_id in ai-service response for case %s", case_id)
            return

        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE case_management_cases
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{ai_analysis_id}',
                        to_jsonb(%s::text)
                    ),
                    updated_at = %s
                    WHERE id = %s AND organization_id = %s
                    """,
                    (str(insight_id), datetime.now(timezone.utc), case_id, org_id),
                )
                _record_audit_log(
                    cur,
                    organization_id=org_id,
                    user_id=user_id,
                    action="case_ai_analysis_scheduled",
                    resource_type="case_management_case",
                    resource_id=case_id,
                    metadata={"case_id": case_id, "ai_analysis_id": str(insight_id)},
                )
            conn.commit()

        logger.info("case-insights: stored ai_analysis_id=%s for case %s", insight_id, case_id)

    except httpx.ConnectError as exc:
        logger.warning("case-insights: ai-service unreachable for case %s: %s", case_id, exc)
    except Exception as exc:  # noqa: BLE001 - fire-and-forget task must never raise
        logger.exception("case-insights: unexpected error for case %s: %s", case_id, exc)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
