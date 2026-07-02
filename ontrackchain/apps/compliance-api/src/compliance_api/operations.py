from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from psycopg_pool import ConnectionPool

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])

QUEUE_STATUS_VALUES = (
    "UNDER_REVIEW",
    "ESCALATED",
    "READY",
    "APPROVED",
    "SUBMITTED",
    "CLOSED",
    "REJECTED",
)
TERMINAL_QUEUE_STATUSES = {"CLOSED", "REJECTED"}
PRIORITY_VALUES = ("critical", "high", "normal")
WRITABLE_ROLES = {"ADMIN", "ANALYST", "AUDITOR", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
READABLE_ROLES = WRITABLE_ROLES | {"VIEWER"}
MODULE_VALUES = (
    "alerts",
    "sanctions",
    "blocks",
    "reports",
    "ros_coaf",
    "counterparties",
    "evidence",
)
RESOURCE_TYPE_VALUES = (
    "operational_alert",
    "sanctions_screening",
    "preventive_block",
    "formal_report_case",
    "ros_record",
    "counterparty",
    "evidence_event",
)
ALLOWED_TRANSITIONS = {
    "UNDER_REVIEW": {"ESCALATED", "READY", "REJECTED", "CLOSED"},
    "ESCALATED": {"READY", "REJECTED", "CLOSED"},
    "READY": {"APPROVED", "REJECTED", "CLOSED"},
    "APPROVED": {"SUBMITTED", "CLOSED"},
    "SUBMITTED": {"CLOSED"},
    "CLOSED": set(),
    "REJECTED": set(),
}


class WorkItemResponse(BaseModel):
    id: UUID
    module: str
    resource_type: str
    resource_id: UUID
    case_id: Optional[UUID]
    report_external_id: Optional[str]
    owner_user_id: Optional[UUID]
    assigned_by_user_id: Optional[UUID]
    queue_status: str
    priority: str
    due_at: Optional[str]
    sla_breached: bool
    title: Optional[str]
    note: Optional[str]
    metadata: dict
    created_at: str
    updated_at: str
    last_activity_at: str


class WorkEventResponse(BaseModel):
    id: UUID
    event_type: str
    from_status: Optional[str]
    to_status: Optional[str]
    actor_user_id: Optional[UUID]
    payload: dict
    created_at: str


class WorkCommentResponse(BaseModel):
    id: UUID
    comment_type: str
    actor_user_id: Optional[UUID]
    body: str
    created_at: str


class WorkItemListResponse(BaseModel):
    data: list[WorkItemResponse]
    page: int
    limit: int
    total: int
    has_more: bool


class CreateWorkItemRequest(BaseModel):
    module: Literal["alerts", "sanctions", "blocks", "reports", "ros_coaf", "counterparties", "evidence"]
    resource_type: Literal[
        "operational_alert",
        "sanctions_screening",
        "preventive_block",
        "formal_report_case",
        "ros_record",
        "counterparty",
        "evidence_event",
    ]
    resource_id: UUID
    case_id: Optional[UUID] = None
    report_external_id: Optional[str] = Field(default=None, max_length=64)
    owner_user_id: Optional[UUID] = None
    priority: Literal["critical", "high", "normal"] = "normal"
    queue_status: Literal["UNDER_REVIEW", "ESCALATED", "READY", "APPROVED", "SUBMITTED", "CLOSED", "REJECTED"] = (
        "UNDER_REVIEW"
    )
    due_at: Optional[datetime] = None
    title: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class UpdateWorkItemRequest(BaseModel):
    owner_user_id: Optional[UUID] = None
    priority: Optional[Literal["critical", "high", "normal"]] = None
    queue_status: Optional[
        Literal["UNDER_REVIEW", "ESCALATED", "READY", "APPROVED", "SUBMITTED", "CLOSED", "REJECTED"]
    ] = None
    due_at: Optional[datetime] = None
    title: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = None
    metadata: Optional[dict] = None


class CreateCommentRequest(BaseModel):
    comment_type: Literal["note", "decision", "handoff"] = "note"
    body: str = Field(min_length=1)


class WorkItemTimelineResponse(BaseModel):
    item: WorkItemResponse
    events: list[WorkEventResponse]
    comments: list[WorkCommentResponse]


def _serialize_timestamp(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def _apply_rls_context(conn, org_id: Optional[str]) -> None:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, true)", (org_id,))


def _require_org_id(org_id: Optional[str]) -> str:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    return org_id


def _resolve_actor_ids(*, external_user_id: Optional[str], linked_user_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    effective_user_id = linked_user_id or external_user_id
    if linked_user_id and external_user_id and linked_user_id != external_user_id:
        return effective_user_id, external_user_id
    return effective_user_id, None


def _resolve_persisted_user_id(cur, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    try:
        candidate_user_id = str(UUID(str(user_id)))
    except (TypeError, ValueError):
        return None
    cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate_user_id,))
    if cur.fetchone():
        return candidate_user_id
    return None


def _record_audit_log(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    metadata: dict,
) -> None:
    normalized_metadata = dict(metadata)
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    if user_id and not persisted_user_id:
        normalized_metadata.setdefault("external_user_id", str(user_id))
    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, resource_id, json.dumps(normalized_metadata)),
    )


def _require_role(x_role: Optional[str], allowed_roles: set[str], detail: str) -> str:
    normalized_role = (x_role or "").upper()
    if normalized_role not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return normalized_role


def _validate_transition(current_status: str, next_status: str, note: Optional[str]) -> None:
    if current_status == next_status:
        return
    if next_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise HTTPException(status_code=409, detail="invalid_transition")
    if next_status == "REJECTED" and not (note or "").strip():
        raise HTTPException(status_code=422, detail="note_required_for_rejected")


def _resource_exists(cur, resource_type: str, resource_id: UUID, case_id: Optional[UUID]) -> bool:
    lookup_sql = {
        "operational_alert": ("SELECT 1 FROM operational_alert_events WHERE id = %s", (resource_id,)),
        "preventive_block": ("SELECT 1 FROM preventive_blocks WHERE id = %s", (resource_id,)),
        "ros_record": ("SELECT 1 FROM ros_records WHERE id = %s", (resource_id,)),
        "counterparty": ("SELECT 1 FROM counterparties WHERE id = %s", (resource_id,)),
        "formal_report_case": ("SELECT 1 FROM cases WHERE id = %s", (case_id or resource_id,)),
        # Ainda sem entidade dedicada persistida para a fase 1.
        "sanctions_screening": ("SELECT 1", ()),
        "evidence_event": ("SELECT 1", ()),
    }
    query_tuple = lookup_sql.get(resource_type)
    if not query_tuple:
        return False
    query, params = query_tuple
    cur.execute(query, params)
    return cur.fetchone() is not None


def _compute_sla_breached(queue_status: str, due_at: Optional[datetime]) -> bool:
    if not due_at or queue_status in TERMINAL_QUEUE_STATUSES:
        return False
    reference = due_at if due_at.tzinfo else due_at.replace(tzinfo=timezone.utc)
    return reference < datetime.now(timezone.utc)


def _serialize_work_item(row: dict) -> WorkItemResponse:
    return WorkItemResponse(
        id=row["id"],
        module=row["module"],
        resource_type=row["resource_type"],
        resource_id=row["resource_id"],
        case_id=row["case_id"],
        report_external_id=row["report_external_id"],
        owner_user_id=row["owner_user_id"],
        assigned_by_user_id=row["assigned_by_user_id"],
        queue_status=row["queue_status"],
        priority=row["priority"],
        due_at=_serialize_timestamp(row["due_at"]),
        sla_breached=bool(row["sla_breached"]),
        title=row["title"],
        note=row["note"],
        metadata=row["metadata"] or {},
        created_at=_serialize_timestamp(row["created_at"]) or "",
        updated_at=_serialize_timestamp(row["updated_at"]) or "",
        last_activity_at=_serialize_timestamp(row["last_activity_at"]) or "",
    )


def _serialize_work_event(row: dict) -> WorkEventResponse:
    return WorkEventResponse(
        id=row["id"],
        event_type=row["event_type"],
        from_status=row["from_status"],
        to_status=row["to_status"],
        actor_user_id=row["actor_user_id"],
        payload=row["payload"] or {},
        created_at=_serialize_timestamp(row["created_at"]) or "",
    )


def _serialize_work_comment(row: dict) -> WorkCommentResponse:
    return WorkCommentResponse(
        id=row["id"],
        comment_type=row["comment_type"],
        actor_user_id=row["actor_user_id"],
        body=row["body"],
        created_at=_serialize_timestamp(row["created_at"]) or "",
    )


@router.post("/work-items", response_model=WorkItemResponse, status_code=201)
async def create_work_item(
    body: CreateWorkItemRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> WorkItemResponse:
    org_id = _require_org_id(x_org_id)
    _require_role(x_role, WRITABLE_ROLES, "privileged_write_role_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required")
            if not _resource_exists(cur, body.resource_type, body.resource_id, body.case_id):
                raise HTTPException(status_code=404, detail="resource_not_found")
            owner_user_id = str(body.owner_user_id) if body.owner_user_id else None
            if owner_user_id and not _resolve_persisted_user_id(cur, owner_user_id):
                raise HTTPException(status_code=422, detail="owner_user_not_found")
            sla_breached = _compute_sla_breached(body.queue_status, body.due_at)
            cur.execute(
                """
                INSERT INTO regulatory_work_items (
                    organization_id, module, resource_type, resource_id,
                    case_id, report_external_id, owner_user_id, assigned_by_user_id,
                    queue_status, priority, due_at, sla_breached,
                    title, note, metadata, created_at, updated_at, last_activity_at
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s::jsonb, NOW(), NOW(), NOW()
                )
                ON CONFLICT (organization_id, resource_type, resource_id)
                DO UPDATE SET
                    module = EXCLUDED.module,
                    case_id = COALESCE(EXCLUDED.case_id, regulatory_work_items.case_id),
                    report_external_id = COALESCE(EXCLUDED.report_external_id, regulatory_work_items.report_external_id),
                    owner_user_id = COALESCE(EXCLUDED.owner_user_id, regulatory_work_items.owner_user_id),
                    assigned_by_user_id = CASE
                        WHEN EXCLUDED.owner_user_id IS NOT NULL THEN EXCLUDED.assigned_by_user_id
                        ELSE regulatory_work_items.assigned_by_user_id
                    END,
                    queue_status = EXCLUDED.queue_status,
                    priority = EXCLUDED.priority,
                    due_at = EXCLUDED.due_at,
                    sla_breached = EXCLUDED.sla_breached,
                    title = COALESCE(EXCLUDED.title, regulatory_work_items.title),
                    note = COALESCE(EXCLUDED.note, regulatory_work_items.note),
                    metadata = regulatory_work_items.metadata || EXCLUDED.metadata,
                    updated_at = NOW(),
                    last_activity_at = NOW()
                RETURNING *
                """,
                (
                    org_id,
                    body.module,
                    body.resource_type,
                    body.resource_id,
                    body.case_id,
                    body.report_external_id,
                    owner_user_id,
                    persisted_user_id if owner_user_id else None,
                    body.queue_status,
                    body.priority,
                    body.due_at,
                    sla_breached,
                    body.title,
                    body.note,
                    json.dumps(body.metadata),
                ),
            )
            work_item = cur.fetchone()
            cur.execute(
                """
                INSERT INTO regulatory_work_events (
                    work_item_id, organization_id, actor_user_id,
                    event_type, from_status, to_status, payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    work_item["id"],
                    org_id,
                    persisted_user_id,
                    "WORK_ITEM_UPSERTED",
                    None,
                    body.queue_status,
                    json.dumps(
                        {
                            "module": body.module,
                            "request_id": x_request_id,
                            "external_user_id": external_actor_user_id,
                        }
                    ),
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="regulatory_work_item_upserted",
                resource_type="regulatory_work_item",
                resource_id=str(work_item["id"]),
                metadata={
                    "request_id": x_request_id,
                    "module": body.module,
                    "resource_type": body.resource_type,
                    "resource_id": str(body.resource_id),
                    "queue_status": body.queue_status,
                    "priority": body.priority,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return _serialize_work_item(work_item)


@router.get("/work-items", response_model=WorkItemListResponse)
async def list_work_items(
    module: Optional[str] = Query(default=None),
    queue_status: Optional[str] = Query(default=None),
    owner_user_id: Optional[UUID] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    case_id: Optional[UUID] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    due_before: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
) -> WorkItemListResponse:
    org_id = _require_org_id(x_org_id)
    _require_role(x_role, READABLE_ROLES, "privileged_read_role_required")
    if module and module not in MODULE_VALUES:
        raise HTTPException(status_code=422, detail="invalid_module")
    if queue_status and queue_status not in QUEUE_STATUS_VALUES:
        raise HTTPException(status_code=422, detail="invalid_queue_status")
    if priority and priority not in PRIORITY_VALUES:
        raise HTTPException(status_code=422, detail="invalid_priority")
    if resource_type and resource_type not in RESOURCE_TYPE_VALUES:
        raise HTTPException(status_code=422, detail="invalid_resource_type")
    offset = (page - 1) * limit
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            base_query = """
                FROM regulatory_work_items
                WHERE organization_id = %s
            """
            params: list[object] = [org_id]
            if module:
                base_query += " AND module = %s"
                params.append(module)
            if queue_status:
                base_query += " AND queue_status = %s"
                params.append(queue_status)
            if owner_user_id:
                base_query += " AND owner_user_id = %s"
                params.append(owner_user_id)
            if priority:
                base_query += " AND priority = %s"
                params.append(priority)
            if case_id:
                base_query += " AND case_id = %s"
                params.append(case_id)
            if resource_type:
                base_query += " AND resource_type = %s"
                params.append(resource_type)
            if due_before:
                base_query += " AND due_at IS NOT NULL AND due_at <= %s"
                params.append(due_before)

            cur.execute("SELECT COUNT(*) AS total " + base_query, params)
            total = int((cur.fetchone() or {}).get("total") or 0)

            cur.execute(
                """
                SELECT *
                """
                + base_query
                + """
                ORDER BY
                    sla_breached DESC,
                    due_at NULLS LAST,
                    last_activity_at DESC,
                    id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, limit, offset],
            )
            rows = cur.fetchall()
    return WorkItemListResponse(
        data=[_serialize_work_item(row) for row in rows],
        page=page,
        limit=limit,
        total=total,
        has_more=offset + len(rows) < total,
    )


@router.patch("/work-items/{work_item_id}", response_model=WorkItemResponse)
async def update_work_item(
    work_item_id: UUID,
    body: UpdateWorkItemRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> WorkItemResponse:
    org_id = _require_org_id(x_org_id)
    _require_role(x_role, WRITABLE_ROLES, "privileged_write_role_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required")
            cur.execute(
                "SELECT * FROM regulatory_work_items WHERE id = %s AND organization_id = %s",
                (work_item_id, org_id),
            )
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="work_item_not_found")
            next_status = body.queue_status or current["queue_status"]
            _validate_transition(current["queue_status"], next_status, body.note)
            owner_user_id = str(body.owner_user_id) if body.owner_user_id else current["owner_user_id"]
            if owner_user_id and not _resolve_persisted_user_id(cur, owner_user_id):
                raise HTTPException(status_code=422, detail="owner_user_not_found")
            merged_metadata = dict(current["metadata"] or {})
            if body.metadata:
                merged_metadata.update(body.metadata)
            due_at = body.due_at if body.due_at is not None else current["due_at"]
            sla_breached = _compute_sla_breached(next_status, due_at)
            cur.execute(
                """
                UPDATE regulatory_work_items
                   SET owner_user_id = %s,
                       assigned_by_user_id = CASE
                           WHEN %s IS DISTINCT FROM owner_user_id THEN %s
                           ELSE assigned_by_user_id
                       END,
                       priority = COALESCE(%s, priority),
                       queue_status = %s,
                       due_at = %s,
                       sla_breached = %s,
                       title = COALESCE(%s, title),
                       note = COALESCE(%s, note),
                       metadata = %s::jsonb,
                       updated_at = NOW(),
                       last_activity_at = NOW()
                 WHERE id = %s
                   AND organization_id = %s
                 RETURNING *
                """,
                (
                    owner_user_id,
                    owner_user_id,
                    persisted_user_id,
                    body.priority,
                    next_status,
                    due_at,
                    sla_breached,
                    body.title,
                    body.note,
                    json.dumps(merged_metadata),
                    work_item_id,
                    org_id,
                ),
            )
            updated = cur.fetchone()
            cur.execute(
                """
                INSERT INTO regulatory_work_events (
                    work_item_id, organization_id, actor_user_id,
                    event_type, from_status, to_status, payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    work_item_id,
                    org_id,
                    persisted_user_id,
                    "STATUS_CHANGED" if current["queue_status"] != next_status else "WORK_ITEM_UPDATED",
                    current["queue_status"],
                    next_status,
                    json.dumps(
                        {
                            "request_id": x_request_id,
                            "priority": body.priority,
                            "owner_user_id": owner_user_id,
                            "external_user_id": external_actor_user_id,
                        }
                    ),
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="regulatory_work_item_updated",
                resource_type="regulatory_work_item",
                resource_id=str(work_item_id),
                metadata={
                    "request_id": x_request_id,
                    "from_status": current["queue_status"],
                    "to_status": next_status,
                    "priority": body.priority or current["priority"],
                    "owner_user_id": owner_user_id,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return _serialize_work_item(updated)


@router.get("/work-items/{work_item_id}/timeline", response_model=WorkItemTimelineResponse)
async def get_work_item_timeline(
    work_item_id: UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
) -> WorkItemTimelineResponse:
    org_id = _require_org_id(x_org_id)
    _require_role(x_role, READABLE_ROLES, "privileged_read_role_required")
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM regulatory_work_items WHERE id = %s AND organization_id = %s",
                (work_item_id, org_id),
            )
            item = cur.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="work_item_not_found")
            cur.execute(
                """
                SELECT *
                  FROM regulatory_work_events
                 WHERE work_item_id = %s
                   AND organization_id = %s
                 ORDER BY created_at DESC, id DESC
                """,
                (work_item_id, org_id),
            )
            events = cur.fetchall()
            cur.execute(
                """
                SELECT *
                  FROM regulatory_work_comments
                 WHERE work_item_id = %s
                   AND organization_id = %s
                 ORDER BY created_at DESC, id DESC
                """,
                (work_item_id, org_id),
            )
            comments = cur.fetchall()
    return WorkItemTimelineResponse(
        item=_serialize_work_item(item),
        events=[_serialize_work_event(row) for row in events],
        comments=[_serialize_work_comment(row) for row in comments],
    )


@router.post("/work-items/{work_item_id}/comments", response_model=WorkCommentResponse, status_code=201)
async def create_work_item_comment(
    work_item_id: UUID,
    body: CreateCommentRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> WorkCommentResponse:
    org_id = _require_org_id(x_org_id)
    _require_role(x_role, WRITABLE_ROLES, "privileged_write_role_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required")
            cur.execute(
                "SELECT queue_status FROM regulatory_work_items WHERE id = %s AND organization_id = %s",
                (work_item_id, org_id),
            )
            item = cur.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="work_item_not_found")
            cur.execute(
                """
                INSERT INTO regulatory_work_comments (
                    work_item_id, organization_id, actor_user_id, comment_type, body
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (work_item_id, org_id, persisted_user_id, body.comment_type, body.body.strip()),
            )
            comment = cur.fetchone()
            cur.execute(
                """
                INSERT INTO regulatory_work_events (
                    work_item_id, organization_id, actor_user_id,
                    event_type, from_status, to_status, payload
                )
                VALUES (%s, %s, %s, 'COMMENT_ADDED', %s, %s, %s::jsonb)
                """,
                (
                    work_item_id,
                    org_id,
                    persisted_user_id,
                    item["queue_status"],
                    item["queue_status"],
                    json.dumps({"comment_type": body.comment_type}),
                ),
            )
            cur.execute(
                """
                UPDATE regulatory_work_items
                   SET updated_at = NOW(),
                       last_activity_at = NOW()
                 WHERE id = %s
                   AND organization_id = %s
                """,
                (work_item_id, org_id),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="regulatory_work_comment_added",
                resource_type="regulatory_work_item",
                resource_id=str(work_item_id),
                metadata={
                    "request_id": x_request_id,
                    "comment_type": body.comment_type,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return _serialize_work_comment(comment)
