from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from ontrackchain_agents.coaf_report_agent import CoafReportAgent
from ontrackchain_agents.evidence_integration import emit_evidence_event_sync
from ontrackchain_shared import resolve_canonical_identifier
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


app = FastAPI(title="OnTrackChain Report API")

class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"
    report_internal_metrics_enabled: bool = True
    report_downloads_last_24h_warn_threshold: int = 10
    report_pending_onchain_warn_threshold: int = 3
    report_legal_download_security_violation_threshold: int = 1
    report_persisted_without_download_warn_threshold: int = 3


settings = Settings()
logger = logging.getLogger("report_api")

REPORT_TYPE_ALIASES = {
    "technical": "technical_basic",
    "tech": "technical_basic",
    "basic": "technical_basic",
    "technical_full": "technical_full",
    "deep_technical": "technical_full",
    "coaf": "coaf_ready_report",
    "coaf_report": "coaf_ready_report",
    "ros": "coaf_ready_report",
    "compliance": "compliance_aml",
    "aml": "compliance_aml",
    "kyt": "compliance_aml",
    "aml_kyt": "compliance_aml",
    "legal": "legal_report",
    "juridico": "legal_report",
    "parecer": "legal_report",
    "full": "full_investigation",
    "investigation": "full_investigation",
    "risk": "risk_check_instant",
    "instant": "risk_check_instant",
    "quick_check": "risk_check_instant",
}

REPORT_TYPES = {
    "risk_check_instant",
    "technical_basic",
    "technical_full",
    "compliance_aml",
    "legal_report",
    "coaf_ready_report",
    "full_investigation",
}

REPORT_READ_ALLOWED_ROLES = {"ADMIN", "AUDITOR", "ANALYST", "VIEWER"}
REPORT_DETAIL_ALLOWED_ROLES = {"ADMIN", "AUDITOR", "ANALYST"}
REPORT_DOWNLOAD_ALLOWED_ROLES = {"ADMIN", "AUDITOR", "ANALYST"}
REPORT_WRITE_ALLOWED_ROLES = {"ADMIN", "ANALYST"}


def resolve_report_type(raw_input: str) -> tuple[str, Optional[str]]:
    try:
        canonical, was_alias = resolve_canonical_identifier(
            raw_input,
            canonical_values=list(REPORT_TYPES),
            aliases=REPORT_TYPE_ALIASES,
        )
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_report_type",
                "message": f"report_type '{raw_input}' nao reconhecido",
                "valid_report_types": sorted(REPORT_TYPES),
                "accepted_aliases": sorted(REPORT_TYPE_ALIASES.keys()),
            },
        ) from None
    return canonical, raw_input if was_alias else None


class GenerateReportRequest(BaseModel):
    case_id: str
    report_type: str = "technical"
    include_onchain_hash: bool = False


class GenerateReportResponse(BaseModel):
    report_id: str
    case_id: str
    report_type_requested: str
    report_type: str
    created_at: str
    file_hash_sha256: str
    onchain_hash: Optional[str]
    content_type: str


class ReportListItem(BaseModel):
    report_id: str
    case_id: Optional[str]
    report_type_requested: str
    report_type: str
    content_type: str
    file_hash_sha256: Optional[str]
    onchain_hash: Optional[str]
    created_at: str
    has_download_audit: bool


class ReportListResponse(BaseModel):
    data: list[ReportListItem]
    page: int
    limit: int
    total: int
    has_more: bool


class GenerateRosCoafRequest(BaseModel):
    ros_id: str


class GenerateRosCoafResponse(BaseModel):
    ros_id: str
    report_id: str
    report_type: str
    status: str
    created_at: str
    file_hash_sha256: str
    content_type: str


class ReportRosCoafRefResponse(BaseModel):
    report_id: str
    ros_id: Optional[str] = None


class ApproveRosCoafRequest(BaseModel):
    approved: bool = True
    rejection_reason: Optional[str] = None


class ApproveRosCoafResponse(BaseModel):
    ros_id: str
    status: str
    approved_at: str
    approval_2fa_verified: bool


class SubmitRosCoafRequest(BaseModel):
    coaf_protocol_number: str
    coaf_receipt_hash: Optional[str] = None


class SubmitRosCoafResponse(BaseModel):
    ros_id: str
    status: str
    submitted_at: str
    coaf_protocol_number: str
    coaf_receipt_hash: str


class RosCoafListItem(BaseModel):
    ros_id: str
    case_id: Optional[str] = None
    status: str
    report_id: str = ""
    created_at: str
    approved_at: Optional[str] = None
    submitted_at: Optional[str] = None
    coaf_protocol_number: str = ""
    coaf_receipt_hash: str = ""
    rejection_reason: str = ""
    approval_2fa_verified: bool = False
    submission_deadline: Optional[str] = None
    deadline_breached: bool = False
    last_activity_at: str


class RosCoafListResponse(BaseModel):
    data: list[RosCoafListItem]
    page: int
    limit: int
    total: int
    has_more: bool


class RosCoafAuditEntry(BaseModel):
    id: UUID
    action: str
    user_id: Optional[UUID] = None
    created_at: str
    metadata: dict = {}


class RosCoafDetailResponse(BaseModel):
    ros_id: str
    case_id: Optional[str] = None
    report_id: str = ""
    status: str
    tipologia_code: str
    tipologia_description: str
    trigger_reason: str
    suspected_amount_brl: Optional[float] = None
    suspected_address: str = ""
    suspected_chain: str = ""
    pdf_hash: str = ""
    pdf_path: str = ""
    generated_at: Optional[str] = None
    approved_at: Optional[str] = None
    submitted_at: Optional[str] = None
    approval_2fa_verified: bool = False
    rejection_reason: str = ""
    submission_deadline: Optional[str] = None
    deadline_breached: bool = False
    coaf_protocol_number: str = ""
    coaf_receipt_hash: str = ""
    evidence_hash: str = ""
    evidence_trail_ref: str = ""
    created_at: str
    updated_at: str
    retain_until: str
    audit: list[RosCoafAuditEntry] = []


class RosCoafWorkItemSnapshot(BaseModel):
    id: UUID
    module: str
    resource_type: str
    resource_id: UUID
    case_id: Optional[UUID] = None
    report_external_id: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    assigned_by_user_id: Optional[UUID] = None
    queue_status: str
    priority: str
    due_at: Optional[str] = None
    sla_breached: bool = False
    title: Optional[str] = None
    note: Optional[str] = None
    metadata: dict = {}
    created_at: str
    updated_at: str
    last_activity_at: str


class RosCoafWorkEventEntry(BaseModel):
    id: UUID
    event_type: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    actor_user_id: Optional[UUID] = None
    payload: dict = {}
    created_at: str


class RosCoafWorkCommentEntry(BaseModel):
    id: UUID
    comment_type: str
    actor_user_id: Optional[UUID] = None
    body: str
    created_at: str


class RosCoafRegulatoryTimelineEntry(BaseModel):
    id: str
    source: Literal["domain_audit", "work_event", "work_comment"]
    label: str
    detail: Optional[str] = None
    actor: Optional[str] = None
    created_at: str


class RosCoafRegulatoryDossierResponse(BaseModel):
    version: str = "v1"
    generated_at: str
    dossier_sha256: str = ""
    ros_record: RosCoafDetailResponse
    work_item: Optional[RosCoafWorkItemSnapshot] = None
    work_events: list[RosCoafWorkEventEntry] = []
    work_comments: list[RosCoafWorkCommentEntry] = []
    unified_timeline: list[RosCoafRegulatoryTimelineEntry] = []


def _build_ros_coaf_regulatory_dossier_filename(ros_id: str) -> str:
    normalized_ros_id = ros_id.strip() or "selection"
    return f"ontrackchain-ros-coaf-regulatory-dossier-{normalized_ros_id}.json"


def _compute_report_id(case_id: str, report_type: str) -> str:
    return hashlib.sha256(f"{case_id}:{report_type}".encode("utf-8")).hexdigest()[:16]


def _require_strong_auth_for_legal_report(
    *,
    x_auth_method: Optional[str],
    x_role: Optional[str],
    x_2fa: Optional[str],
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
) -> None:
    if (x_auth_method or "").lower() not in {"jwt", "dev_jwt"}:
        raise HTTPException(status_code=403, detail="legal_report_requires_jwt_auth")
    if (x_role or "").upper() not in {"ADMIN"}:
        raise HTTPException(status_code=403, detail="legal_report_requires_admin_role")
    normalized_mfa_mode = (x_mfa_mode or "").lower()
    if normalized_mfa_mode == "external_provider":
        if (x_mfa_provider_homologated or "").lower() != "true":
            raise HTTPException(status_code=403, detail="mfa_not_homologated_for_oidc")
        if x_2fa not in {"managed_externally", "managed_externally_homologated", "ok"}:
            raise HTTPException(status_code=403, detail="2fa_required")
        return
    if x_2fa != "ok":
        raise HTTPException(status_code=403, detail="2fa_required")


COAF_REPORT_REVIEW_ALLOWED_ROLES = {
    "ADMIN",
    "COMPLIANCE_OFFICER",
    "OTK_COMPLIANCE_OFFICER",
    "LEGAL_REVIEWER",
    "OTK_LEGAL_REVIEWER",
    "REVIEWER",
    "OTK_REVIEWER",
}
COAF_REPORT_SUBMISSION_ALLOWED_ROLES = {"ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}


def _require_coaf_report_review_auth(
    *,
    pool: ConnectionPool,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: Optional[str],
    ros_id: Optional[str],
    x_role: Optional[str],
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
    x_2fa: Optional[str],
) -> str:
    normalized_role = _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles=COAF_REPORT_REVIEW_ALLOWED_ROLES,
        detail="coaf_report_review_role_required",
        resource_type="ros_record",
        resource_id=ros_id,
        endpoint="/api/v1/reports/ros-coaf/{ros_id}/approve",
        method="POST",
    )
    if (x_mfa_mode or "").lower() != "external_provider":
        raise HTTPException(status_code=403, detail="coaf_report_requires_external_provider_mfa")
    if (x_mfa_provider_homologated or "").lower() != "true":
        raise HTTPException(status_code=403, detail="coaf_report_requires_homologated_provider")
    if x_2fa not in {"managed_externally", "managed_externally_homologated", "ok"}:
        raise HTTPException(status_code=403, detail="2fa_required")
    return normalized_role


def _require_coaf_report_submission_auth(
    *,
    pool: ConnectionPool,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: Optional[str],
    ros_id: Optional[str],
    x_role: Optional[str],
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
    x_2fa: Optional[str],
) -> str:
    normalized_role = _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles=COAF_REPORT_SUBMISSION_ALLOWED_ROLES,
        detail="coaf_report_submission_role_required",
        resource_type="ros_record",
        resource_id=ros_id,
        endpoint="/api/v1/reports/ros-coaf/{ros_id}/submitted",
        method="POST",
    )
    if (x_mfa_mode or "").lower() != "external_provider":
        raise HTTPException(status_code=403, detail="coaf_report_requires_external_provider_mfa")
    if (x_mfa_provider_homologated or "").lower() != "true":
        raise HTTPException(status_code=403, detail="coaf_report_requires_homologated_provider")
    if x_2fa not in {"managed_externally", "managed_externally_homologated", "ok"}:
        raise HTTPException(status_code=403, detail="2fa_required")
    return normalized_role


def _normalized_role(role: Optional[str]) -> str:
    return str(role or "").strip().upper()


def _resolve_persisted_user_id(cur, effective_user_id: Optional[str]) -> Optional[str]:
    if not effective_user_id:
        return None
    try:
        candidate_user_id = str(UUID(str(effective_user_id)))
    except (TypeError, ValueError):
        return None
    cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate_user_id,))
    if cur.fetchone():
        return candidate_user_id
    return None


def _require_persisted_actor_user_id(
    cur,
    effective_user_id: Optional[str],
    *,
    detail: str = "linked_user_required_for_coaf_report",
) -> str:
    persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
    if not persisted_user_id:
        raise HTTPException(status_code=403, detail=detail)
    return persisted_user_id


def _build_pdf_bytes(*, case_id: str, report_type: str, created_at: str) -> bytes:
    extra_lines = ""
    if report_type == "coaf_ready_report":
        extra_lines = (
            "%%coaf_cliente:DEMO\n"
            "%%coaf_data:" + created_at + "\n"
            "%%coaf_valor_brl:0\n"
            "%%coaf_finalidade:DEMO\n"
            "%%coaf_comunicacao:DEMO\n"
        )
    payload = (
        "%PDF-1.4\n"
        "%OnTrackChain\n"
        "1 0 obj\n"
        "<< /Type /Catalog >>\n"
        "endobj\n"
        f"%%case_id:{case_id}\n"
        f"%%report_type:{report_type}\n"
        f"%%created_at:{created_at}\n"
        f"{extra_lines}"
        "%%EOF\n"
    )
    return payload.encode("utf-8")


def _normalize_reports_pagination(page: int, limit: int) -> tuple[int, int, int]:
    safe_page = page if page > 0 else 1
    safe_limit = limit if 1 <= limit <= 100 else 20
    offset = (safe_page - 1) * safe_limit
    return safe_page, safe_limit, offset


def _normalize_report_filter_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _summarize_metadata_fields(record: Optional[dict], preferred_keys: list[str]) -> Optional[str]:
    if not record:
        return None
    parts: list[str] = []
    for key in preferred_keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(f"{key}: {value.strip()}")
        elif isinstance(value, (int, float, bool)):
            parts.append(f"{key}: {value}")
        if len(parts) >= 3:
            break
    return " | ".join(parts) if parts else None


def _format_work_event_label(event_type: str, from_status: Optional[str], to_status: Optional[str]) -> str:
    if from_status and to_status and from_status != to_status:
        return f"{event_type}: {from_status} -> {to_status}"
    return event_type


def _serialize_report_list_row(row: dict) -> ReportListItem:
    created_at = row.get("created_at")
    if isinstance(created_at, datetime):
        created_at_value = created_at.astimezone(timezone.utc).isoformat()
    else:
        created_at_value = str(created_at) if created_at else ""

    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    case_id = row.get("case_id") or metadata.get("case_reference_id")
    report_id = row.get("external_report_id")

    return ReportListItem(
        report_id=str(report_id),
        case_id=str(case_id) if case_id else None,
        report_type_requested=row.get("report_type_requested") or row.get("report_type") or "unknown",
        report_type=row.get("report_type") or row.get("report_type_requested") or "unknown",
        content_type=row.get("content_type") or "application/pdf",
        file_hash_sha256=row.get("file_hash"),
        onchain_hash=row.get("onchain_hash"),
        created_at=created_at_value,
        has_download_audit=bool(row.get("has_download_audit")),
    )


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


def get_pool() -> ConnectionPool:
    return app.state.pool


def _apply_rls_context(conn, org_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, true)", (org_id,))


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
    persisted_user_id: Optional[str] = None
    persisted_resource_id: Optional[str] = None

    if user_id:
        try:
            candidate_user_id = str(UUID(str(user_id)))
            cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate_user_id,))
            if cur.fetchone():
                persisted_user_id = candidate_user_id
            else:
                normalized_metadata.setdefault("external_user_id", candidate_user_id)
        except (TypeError, ValueError):
            normalized_metadata.setdefault("external_user_id", str(user_id))

    if resource_id:
        try:
            persisted_resource_id = str(UUID(str(resource_id)))
        except (TypeError, ValueError):
            normalized_metadata.setdefault("resource_reference_id", str(resource_id))

    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, persisted_resource_id, json.dumps(normalized_metadata)),
    )


def _upsert_report_record(
    cur,
    *,
    organization_id: str,
    case_id: Optional[str],
    report_id: str,
    report_type_requested: str,
    report_type: str,
    content_type: str,
    file_hash_sha256: str,
    onchain_hash: Optional[str],
    created_at: str,
    metadata: dict,
) -> None:
    cur.execute(
        """
        INSERT INTO reports (
            organization_id,
            case_id,
            external_report_id,
            report_type_requested,
            report_type,
            content_type,
            file_hash,
            onchain_hash,
            created_at,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (external_report_id)
        DO UPDATE SET
            case_id = EXCLUDED.case_id,
            report_type_requested = EXCLUDED.report_type_requested,
            report_type = EXCLUDED.report_type,
            content_type = EXCLUDED.content_type,
            file_hash = EXCLUDED.file_hash,
            onchain_hash = EXCLUDED.onchain_hash,
            created_at = EXCLUDED.created_at,
            metadata = EXCLUDED.metadata
        """,
        (
            organization_id,
            case_id,
            report_id,
            report_type_requested,
            report_type,
            content_type,
            file_hash_sha256,
            onchain_hash,
            created_at,
            json.dumps(metadata),
        ),
    )


def _resolve_actor_ids(
    *,
    external_user_id: Optional[str],
    linked_user_id: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    effective_user_id = linked_user_id or external_user_id
    if linked_user_id and external_user_id and linked_user_id != external_user_id:
        return effective_user_id, external_user_id
    return effective_user_id, None


def _record_authorization_denial(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: Optional[str],
    effective_role: Optional[str],
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
                        "effective_role": effective_role or "UNSPECIFIED",
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
    request_id: Optional[str],
    x_role: Optional[str],
    allowed_roles: set[str],
    detail: str,
    resource_type: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> str:
    role = _normalized_role(x_role)
    if role not in allowed_roles:
        _record_authorization_denial(
            pool,
            organization_id=organization_id,
            user_id=user_id,
            external_user_id=external_user_id,
            request_id=request_id,
            effective_role=role,
            allowed_roles=allowed_roles,
            detail=detail,
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
        )
        raise HTTPException(status_code=403, detail=detail)
    return role


def _build_report_platform_snapshot(*, pool: ConnectionPool) -> dict:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (SELECT COUNT(*) FROM reports) AS reports_total,
                  (SELECT COUNT(*) FROM reports WHERE created_at >= NOW() - INTERVAL '24 hour') AS reports_last_24h,
                  (SELECT COUNT(*) FROM reports WHERE report_type = 'legal_report' AND created_at >= NOW() - INTERVAL '24 hour') AS legal_reports_last_24h,
                  (SELECT COUNT(*) FROM reports WHERE report_type = 'coaf_ready_report' AND created_at >= NOW() - INTERVAL '24 hour') AS coaf_reports_last_24h,
                  (SELECT COUNT(*) FROM reports WHERE onchain_hash = 'pending') AS pending_onchain_total,
                  (
                    SELECT COUNT(*)
                    FROM reports r
                    WHERE NOT EXISTS (
                      SELECT 1
                      FROM audit_logs a
                      WHERE a.action = 'report_downloaded'
                        AND a.metadata->>'report_id' = COALESCE(r.external_report_id, '')
                    )
                  ) AS reports_without_download_total,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS downloads_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND metadata->>'report_type' = 'legal_report'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS legal_downloads_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND metadata->>'report_type' = 'legal_report'
                      AND metadata->>'two_fa' = 'ok'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS legal_downloads_2fa_ok_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND metadata->>'report_type' = 'legal_report'
                      AND COALESCE(metadata->>'two_fa', '') <> 'ok'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS legal_downloads_without_2fa_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND metadata->>'auth_method' = 'jwt'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS jwt_downloads_last_24h,
                  (
                    SELECT COUNT(DISTINCT organization_id)
                    FROM audit_logs
                    WHERE action = 'report_downloaded'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                  ) AS orgs_with_downloads_last_24h
                """
            )
            summary = cur.fetchone() or {}

    return {
        "catalog": {
            "report_types_total": len(REPORT_TYPES),
        },
        "reports": {
            "total": int(summary.get("reports_total") or 0),
            "last_24h": int(summary.get("reports_last_24h") or 0),
            "legal_last_24h": int(summary.get("legal_reports_last_24h") or 0),
            "coaf_last_24h": int(summary.get("coaf_reports_last_24h") or 0),
            "pending_onchain_total": int(summary.get("pending_onchain_total") or 0),
            "without_download_total": int(summary.get("reports_without_download_total") or 0),
        },
        "downloads": {
            "last_24h": int(summary.get("downloads_last_24h") or 0),
            "legal_last_24h": int(summary.get("legal_downloads_last_24h") or 0),
            "legal_2fa_ok_last_24h": int(summary.get("legal_downloads_2fa_ok_last_24h") or 0),
            "legal_without_2fa_last_24h": int(summary.get("legal_downloads_without_2fa_last_24h") or 0),
            "jwt_last_24h": int(summary.get("jwt_downloads_last_24h") or 0),
            "orgs_with_downloads_last_24h": int(summary.get("orgs_with_downloads_last_24h") or 0),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_report_platform_alerts(snapshot: dict) -> list[dict]:
    alerts: list[dict] = []

    def append_alert(
        *,
        code: str,
        severity: str,
        status: str,
        metric: str,
        value: float,
        threshold: float,
        title: str,
        message: str,
        recommended_action: str,
    ) -> None:
        alerts.append(
            {
                "code": code,
                "severity": severity,
                "status": status,
                "metric": metric,
                "value": value,
                "threshold": threshold,
                "title": title,
                "message": message,
                "recommended_action": recommended_action,
            }
        )

    downloads_last_24h = snapshot["downloads"]["last_24h"]
    pending_onchain_total = snapshot["reports"]["pending_onchain_total"]
    legal_without_2fa_last_24h = snapshot["downloads"]["legal_without_2fa_last_24h"]
    reports_without_download_total = snapshot["reports"]["without_download_total"]

    append_alert(
        code="report_download_volume",
        severity="warning",
        status="open" if downloads_last_24h >= settings.report_downloads_last_24h_warn_threshold else "closed",
        metric="downloads.last_24h",
        value=float(downloads_last_24h),
        threshold=float(settings.report_downloads_last_24h_warn_threshold),
        title="Volume alto de downloads",
        message="O volume de downloads de relatorio nas ultimas 24 horas excedeu o limiar operacional.",
        recommended_action="Correlacionar picos com clientes, campanhas ou comportamento anomalo.",
    )
    append_alert(
        code="report_pending_onchain_backlog",
        severity="warning",
        status="open" if pending_onchain_total >= settings.report_pending_onchain_warn_threshold else "closed",
        metric="reports.pending_onchain_total",
        value=float(pending_onchain_total),
        threshold=float(settings.report_pending_onchain_warn_threshold),
        title="Backlog de hash on-chain pendente",
        message="Existem relatorios persistidos com hash on-chain ainda pendente.",
        recommended_action="Verificar pipeline de ancoragem/hash e reconciliação de evidencias.",
    )
    append_alert(
        code="report_legal_download_security_violation",
        severity="critical",
        status="open"
        if legal_without_2fa_last_24h >= settings.report_legal_download_security_violation_threshold
        else "closed",
        metric="downloads.legal_without_2fa_last_24h",
        value=float(legal_without_2fa_last_24h),
        threshold=float(settings.report_legal_download_security_violation_threshold),
        title="Violacao de 2FA em download juridico",
        message="Foi detectado download auditado de legal_report sem 2FA valido.",
        recommended_action="Investigar imediatamente proxy, headers e bypass de autenticacao forte.",
    )
    append_alert(
        code="report_persisted_without_download_backlog",
        severity="warning",
        status="open"
        if reports_without_download_total >= settings.report_persisted_without_download_warn_threshold
        else "closed",
        metric="reports.without_download_total",
        value=float(reports_without_download_total),
        threshold=float(settings.report_persisted_without_download_warn_threshold),
        title="Relatorios persistidos sem download",
        message="Existe backlog de relatorios persistidos ainda sem download auditado.",
        recommended_action="Verificar abandono do fluxo de entrega ou clientes aguardando processamento manual.",
    )
    return alerts


def _normalize_report_case_reference(case_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if case_id is None:
        return None, None

    normalized_case_id = str(case_id).strip()
    if not normalized_case_id:
        return None, None

    try:
        return str(UUID(normalized_case_id)), None
    except ValueError:
        return None, normalized_case_id


def _render_report_platform_prometheus_metrics(snapshot: dict, alerts: list[dict]) -> str:
    alert_open_total = sum(1 for alert in alerts if alert["status"] == "open")
    critical_open_total = sum(1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical")
    lines = [
        "# HELP ontrack_report_platform_catalog_report_types_total Tipos canonicos de relatorio suportados.",
        "# TYPE ontrack_report_platform_catalog_report_types_total gauge",
        f"ontrack_report_platform_catalog_report_types_total {snapshot['catalog']['report_types_total']}",
        "# HELP ontrack_report_platform_reports_total Relatorios persistidos.",
        "# TYPE ontrack_report_platform_reports_total gauge",
        f"ontrack_report_platform_reports_total {snapshot['reports']['total']}",
        "# HELP ontrack_report_platform_reports_last_24h Relatorios persistidos nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_reports_last_24h gauge",
        f"ontrack_report_platform_reports_last_24h {snapshot['reports']['last_24h']}",
        "# HELP ontrack_report_platform_reports_legal_last_24h Relatorios juridicos nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_reports_legal_last_24h gauge",
        f"ontrack_report_platform_reports_legal_last_24h {snapshot['reports']['legal_last_24h']}",
        "# HELP ontrack_report_platform_reports_coaf_last_24h Relatorios COAF-ready nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_reports_coaf_last_24h gauge",
        f"ontrack_report_platform_reports_coaf_last_24h {snapshot['reports']['coaf_last_24h']}",
        "# HELP ontrack_report_platform_reports_pending_onchain_total Relatorios com hash on-chain pendente.",
        "# TYPE ontrack_report_platform_reports_pending_onchain_total gauge",
        f"ontrack_report_platform_reports_pending_onchain_total {snapshot['reports']['pending_onchain_total']}",
        "# HELP ontrack_report_platform_reports_without_download_total Relatorios persistidos ainda sem download auditado.",
        "# TYPE ontrack_report_platform_reports_without_download_total gauge",
        f"ontrack_report_platform_reports_without_download_total {snapshot['reports']['without_download_total']}",
        "# HELP ontrack_report_platform_downloads_last_24h Downloads de relatorio nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_downloads_last_24h gauge",
        f"ontrack_report_platform_downloads_last_24h {snapshot['downloads']['last_24h']}",
        "# HELP ontrack_report_platform_downloads_legal_last_24h Downloads de legal_report nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_downloads_legal_last_24h gauge",
        f"ontrack_report_platform_downloads_legal_last_24h {snapshot['downloads']['legal_last_24h']}",
        "# HELP ontrack_report_platform_downloads_legal_2fa_ok_last_24h Downloads juridicos com 2FA valido nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_downloads_legal_2fa_ok_last_24h gauge",
        f"ontrack_report_platform_downloads_legal_2fa_ok_last_24h {snapshot['downloads']['legal_2fa_ok_last_24h']}",
        "# HELP ontrack_report_platform_downloads_legal_without_2fa_last_24h Downloads juridicos sem 2FA valido nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_downloads_legal_without_2fa_last_24h gauge",
        f"ontrack_report_platform_downloads_legal_without_2fa_last_24h {snapshot['downloads']['legal_without_2fa_last_24h']}",
        "# HELP ontrack_report_platform_downloads_jwt_last_24h Downloads com autenticacao JWT nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_downloads_jwt_last_24h gauge",
        f"ontrack_report_platform_downloads_jwt_last_24h {snapshot['downloads']['jwt_last_24h']}",
        "# HELP ontrack_report_platform_orgs_with_downloads_last_24h_total Organizacoes com downloads nas ultimas 24 horas.",
        "# TYPE ontrack_report_platform_orgs_with_downloads_last_24h_total gauge",
        f"ontrack_report_platform_orgs_with_downloads_last_24h_total {snapshot['downloads']['orgs_with_downloads_last_24h']}",
        "# HELP ontrack_report_platform_operational_alerts_open_total Total de alertas operacionais abertos.",
        "# TYPE ontrack_report_platform_operational_alerts_open_total gauge",
        f"ontrack_report_platform_operational_alerts_open_total {alert_open_total}",
        "# HELP ontrack_report_platform_operational_alerts_critical_open_total Total de alertas operacionais criticos abertos.",
        "# TYPE ontrack_report_platform_operational_alerts_critical_open_total gauge",
        f"ontrack_report_platform_operational_alerts_critical_open_total {critical_open_total}",
        "# HELP ontrack_report_platform_operational_alert_status Estado do alerta operacional avaliado pela aplicacao.",
        "# TYPE ontrack_report_platform_operational_alert_status gauge",
    ]
    for alert in alerts:
        alert_status = 1 if alert["status"] == "open" else 0
        lines.append(
            "ontrack_report_platform_operational_alert_status"
            f'{{code="{alert["code"]}",severity="{alert["severity"]}",metric="{alert["metric"]}"}} {alert_status}'
        )
    return "\n".join(lines) + "\n"


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/internal/metrics/prometheus")
async def internal_report_prometheus_metrics(pool: ConnectionPool = Depends(get_pool)) -> Response:
    if not settings.report_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    snapshot = _build_report_platform_snapshot(pool=pool)
    alerts = _build_report_platform_alerts(snapshot)
    return Response(
        content=_render_report_platform_prometheus_metrics(snapshot, alerts),
        media_type="text/plain; version=0.0.4",
    )


@app.post("/api/v1/reports/generate", response_model=GenerateReportResponse)
async def generate_report(
    body: GenerateReportRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> GenerateReportResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_WRITE_ALLOWED_ROLES,
        detail="report_write_role_required",
        resource_type="report",
        resource_id=body.case_id,
        endpoint="/api/v1/reports/generate",
        method="POST",
    )
    created_at = datetime.now(timezone.utc).isoformat()
    canonical_report_type, requested_alias = resolve_report_type(body.report_type)
    report_type_requested = requested_alias or canonical_report_type

    content = _build_pdf_bytes(case_id=body.case_id, report_type=canonical_report_type, created_at=created_at)
    file_hash = hashlib.sha256(content).hexdigest()
    onchain_hash = "pending" if body.include_onchain_hash else None
    report_id = _compute_report_id(body.case_id, canonical_report_type)
    persisted_case_id, case_reference_id = _normalize_report_case_reference(body.case_id)
    metadata = {
        "generated_at": created_at,
        "request_id": x_request_id,
        "generated_via": "report_api.generate_report",
    }
    if case_reference_id:
        metadata["case_reference_id"] = case_reference_id

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            _upsert_report_record(
                cur,
                organization_id=x_org_id,
                case_id=persisted_case_id,
                report_id=report_id,
                report_type_requested=report_type_requested,
                report_type=canonical_report_type,
                content_type="application/pdf",
                file_hash_sha256=file_hash,
                onchain_hash=onchain_hash,
                created_at=created_at,
                metadata=metadata,
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=effective_user_id,
                action="report_generated",
                resource_type="case",
                resource_id=body.case_id,
                metadata={
                    "request_id": x_request_id,
                    "report_id": report_id,
                    "report_type_requested": report_type_requested,
                    "report_type_canonical": canonical_report_type,
                    "created_at": created_at,
                    "content_type": "application/pdf",
                    "file_hash_sha256": file_hash,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()

    return GenerateReportResponse(
        report_id=report_id,
        case_id=body.case_id,
        report_type_requested=report_type_requested,
        report_type=canonical_report_type,
        created_at=created_at,
        file_hash_sha256=file_hash,
        onchain_hash=onchain_hash,
        content_type="application/pdf",
    )


@app.post("/api/v1/reports/ros-coaf", response_model=GenerateRosCoafResponse)
async def generate_ros_coaf_report(
    body: GenerateRosCoafRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> GenerateRosCoafResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_coaf_report_submission_auth(
        pool=pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        ros_id=body.ros_id,
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _require_persisted_actor_user_id(cur, effective_user_id)

            cur.execute(
                """
                SELECT
                  id,
                  case_id,
                  tipologia_code,
                  trigger_reason,
                  suspected_amount_brl,
                  suspected_address,
                  suspected_chain,
                  status
                FROM ros_records
                WHERE id = %s
                  AND organization_id = %s
                """,
                (body.ros_id, x_org_id),
            )
            ros = cur.fetchone()
            if not ros:
                raise HTTPException(status_code=404, detail="ros_record_not_found")

            draft = CoafReportAgent().generate(
                ros_id=str(ros["id"]),
                case_id=str(ros["case_id"]) if ros["case_id"] else None,
                trigger_reason=ros["trigger_reason"],
                tipologia_code=ros["tipologia_code"],
                suspected_amount_brl=float(ros["suspected_amount_brl"]) if ros["suspected_amount_brl"] is not None else None,
                suspected_address=ros["suspected_address"],
                suspected_chain=ros["suspected_chain"],
            )
            report_id = _compute_report_id(str(ros["case_id"] or ros["id"]), "coaf_ready_report")

            _upsert_report_record(
                cur,
                organization_id=x_org_id,
                case_id=str(ros["case_id"]) if ros["case_id"] else None,
                report_id=report_id,
                report_type_requested="coaf_ready_report",
                report_type="coaf_ready_report",
                content_type=draft.content_type,
                file_hash_sha256=draft.file_hash_sha256,
                onchain_hash=None,
                created_at=draft.generated_at,
                metadata={
                    "ros_id": str(ros["id"]),
                    "generated_at": draft.generated_at,
                    "title": draft.title,
                    "request_id": x_request_id,
                },
            )
            cur.execute(
                """
                UPDATE ros_records
                   SET status = 'PENDING_APPROVAL',
                       generated_by_user_id = %s,
                       generated_at = %s,
                       pdf_hash = %s,
                       pdf_path = %s
                 WHERE id = %s
                """,
                (
                    persisted_user_id,
                    draft.generated_at,
                    draft.file_hash_sha256,
                    f"reports/{report_id}.pdf",
                    body.ros_id,
                ),
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=persisted_user_id,
                action="coaf_report_generated",
                resource_type="ros_record",
                resource_id=body.ros_id,
                metadata={
                    "request_id": x_request_id,
                    "report_id": report_id,
                    "file_hash_sha256": draft.file_hash_sha256,
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=x_org_id,
                event_type="COAF_ROS_GENERATED",
                event_payload={
                    "ros_id": body.ros_id,
                    "report_id": report_id,
                    "file_hash_sha256": draft.file_hash_sha256,
                },
                actor_user_id=persisted_user_id,
                case_id=str(ros["case_id"]) if ros["case_id"] else None,
                regulatory_basis=["Lei 9.613/98 Art. 11", "IN BCB 739 Art. 1° V"],
            )
        conn.commit()

    return GenerateRosCoafResponse(
        ros_id=body.ros_id,
        report_id=report_id,
        report_type="coaf_ready_report",
        status="PENDING_APPROVAL",
        created_at=draft.generated_at,
        file_hash_sha256=draft.file_hash_sha256,
        content_type=draft.content_type,
    )


@app.get("/api/v1/reports/ros-coaf", response_model=RosCoafListResponse)
async def list_ros_coaf_reports(
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    ros_id: Optional[str] = Query(default=None),
    case_id: Optional[str] = Query(default=None),
    report_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> RosCoafListResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")

    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    normalized_ros_id = ros_id.strip() if ros_id else None
    normalized_case_id = case_id.strip() if case_id else None
    normalized_report_id = report_id.strip() if report_id else None
    normalized_status = status.strip().upper() if status else None
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_READ_ALLOWED_ROLES,
        detail="report_read_role_required",
        resource_type="ros_record",
        resource_id=normalized_ros_id or normalized_report_id,
        endpoint="/api/v1/reports/ros-coaf",
        method="GET",
    )
    offset = (page - 1) * limit

    base_from = """
        FROM ros_records ros
        LEFT JOIN LATERAL (
            SELECT external_report_id, created_at
            FROM reports rep
            WHERE rep.organization_id = ros.organization_id
              AND rep.report_type = 'coaf_ready_report'
              AND rep.metadata->>'ros_id' = ros.id::text
            ORDER BY rep.created_at DESC, rep.id DESC
            LIMIT 1
        ) report_ref ON TRUE
        WHERE ros.organization_id = %s
    """
    params: list[object] = [x_org_id]
    if normalized_ros_id:
        base_from += " AND ros.id::text = %s"
        params.append(normalized_ros_id)
    if normalized_case_id:
        base_from += " AND ros.case_id::text = %s"
        params.append(normalized_case_id)
    if normalized_report_id:
        base_from += " AND report_ref.external_report_id = %s"
        params.append(normalized_report_id)
    if normalized_status:
        base_from += " AND ros.status = %s"
        params.append(normalized_status)

    total = 0
    rows: list[dict] = []
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS total {base_from}", params)
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT
                    ros.id::text AS ros_id,
                    ros.case_id::text AS case_id,
                    ros.status,
                    COALESCE(report_ref.external_report_id, '') AS report_id,
                    COALESCE(report_ref.created_at, ros.generated_at, ros.created_at) AS created_at,
                    ros.approved_at,
                    ros.submitted_at,
                    ros.coaf_protocol_number,
                    ros.coaf_receipt_hash,
                    ros.rejection_reason,
                    ros.approval_2fa_verified,
                    ros.submission_deadline,
                    (
                        ros.deadline_breached
                        OR (
                            ros.status NOT IN ('SUBMITTED_MANUAL', 'REJECTED')
                            AND ros.submission_deadline < NOW()
                        )
                    ) AS deadline_breached,
                    GREATEST(
                        COALESCE(ros.updated_at, ros.created_at),
                        COALESCE(ros.submitted_at, ros.created_at),
                        COALESCE(ros.approved_at, ros.created_at),
                        COALESCE(ros.generated_at, ros.created_at),
                        COALESCE(report_ref.created_at, ros.created_at)
                    ) AS last_activity_at
                {base_from}
                ORDER BY last_activity_at DESC, ros.id DESC
                LIMIT %s OFFSET %s
                """,
                [*params, limit, offset],
            )
            rows = cur.fetchall()

    data = [
        RosCoafListItem(
            ros_id=row["ros_id"],
            case_id=row["case_id"],
            status=row["status"],
            report_id=row["report_id"] or "",
            created_at=row["created_at"].isoformat(),
            approved_at=row["approved_at"].isoformat() if row["approved_at"] else None,
            submitted_at=row["submitted_at"].isoformat() if row["submitted_at"] else None,
            coaf_protocol_number=row["coaf_protocol_number"] or "",
            coaf_receipt_hash=row["coaf_receipt_hash"] or "",
            rejection_reason=row["rejection_reason"] or "",
            approval_2fa_verified=bool(row["approval_2fa_verified"]),
            submission_deadline=row["submission_deadline"].isoformat() if row["submission_deadline"] else None,
            deadline_breached=bool(row["deadline_breached"]),
            last_activity_at=row["last_activity_at"].isoformat(),
        )
        for row in rows
    ]
    return RosCoafListResponse(
        data=data,
        page=page,
        limit=limit,
        total=total,
        has_more=offset + len(data) < total,
    )


@app.get("/api/v1/reports/ros-coaf/{ros_id}", response_model=RosCoafDetailResponse)
async def get_ros_coaf_report(
    ros_id: str,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> RosCoafDetailResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")

    normalized_ros_id = ros_id.strip()
    if not normalized_ros_id:
        raise HTTPException(status_code=422, detail="ros_id_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_READ_ALLOWED_ROLES,
        detail="report_read_role_required",
        resource_type="ros_record",
        resource_id=normalized_ros_id,
        endpoint="/api/v1/reports/ros-coaf/{ros_id}",
        method="GET",
    )

    ros_row: Optional[dict] = None
    audit_rows: list[dict] = []
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _require_persisted_actor_user_id(cur, effective_user_id)
            cur.execute(
                """
                SELECT
                    ros.id,
                    ros.id::text AS ros_id,
                    ros.case_id::text AS case_id,
                    ros.status,
                    COALESCE(report_ref.external_report_id, '') AS report_id,
                    ros.tipologia_code,
                    ros.tipologia_description,
                    ros.trigger_reason,
                    ros.suspected_amount_brl,
                    ros.suspected_address,
                    ros.suspected_chain,
                    ros.pdf_hash,
                    ros.pdf_path,
                    ros.generated_at,
                    ros.approved_at,
                    ros.submitted_at,
                    ros.approval_2fa_verified,
                    ros.rejection_reason,
                    ros.submission_deadline,
                    (
                        ros.deadline_breached
                        OR (
                            ros.status NOT IN ('SUBMITTED_MANUAL', 'REJECTED')
                            AND ros.submission_deadline < NOW()
                        )
                    ) AS deadline_breached,
                    ros.coaf_protocol_number,
                    ros.coaf_receipt_hash,
                    ros.evidence_hash,
                    ros.evidence_trail_ref,
                    ros.created_at,
                    ros.updated_at,
                    ros.retain_until
                FROM ros_records ros
                LEFT JOIN LATERAL (
                    SELECT external_report_id, created_at
                    FROM reports rep
                    WHERE rep.organization_id = ros.organization_id
                      AND rep.report_type = 'coaf_ready_report'
                      AND rep.metadata->>'ros_id' = ros.id::text
                    ORDER BY rep.created_at DESC, rep.id DESC
                    LIMIT 1
                ) report_ref ON TRUE
                WHERE ros.organization_id = %s
                  AND ros.id::text = %s
                """,
                (x_org_id, normalized_ros_id),
            )
            ros_row = cur.fetchone()
            if not ros_row:
                raise HTTPException(status_code=404, detail="ros_record_not_found")

            cur.execute(
                """
                SELECT id, user_id, action, metadata, created_at
                FROM audit_logs
                WHERE organization_id = %s
                  AND resource_type = 'ros_record'
                  AND resource_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (x_org_id, ros_row["id"]),
            )
            audit_rows = cur.fetchall()

    audit = [
        RosCoafAuditEntry(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            created_at=row["created_at"].isoformat(),
            metadata=row["metadata"] or {},
        )
        for row in audit_rows
    ]
    return RosCoafDetailResponse(
        ros_id=ros_row["ros_id"],
        case_id=ros_row["case_id"],
        report_id=ros_row["report_id"] or "",
        status=ros_row["status"],
        tipologia_code=ros_row["tipologia_code"],
        tipologia_description=ros_row["tipologia_description"],
        trigger_reason=ros_row["trigger_reason"],
        suspected_amount_brl=float(ros_row["suspected_amount_brl"]) if ros_row["suspected_amount_brl"] is not None else None,
        suspected_address=ros_row["suspected_address"] or "",
        suspected_chain=ros_row["suspected_chain"] or "",
        pdf_hash=ros_row["pdf_hash"] or "",
        pdf_path=ros_row["pdf_path"] or "",
        generated_at=ros_row["generated_at"].isoformat() if ros_row["generated_at"] else None,
        approved_at=ros_row["approved_at"].isoformat() if ros_row["approved_at"] else None,
        submitted_at=ros_row["submitted_at"].isoformat() if ros_row["submitted_at"] else None,
        approval_2fa_verified=bool(ros_row["approval_2fa_verified"]),
        rejection_reason=ros_row["rejection_reason"] or "",
        submission_deadline=ros_row["submission_deadline"].isoformat() if ros_row["submission_deadline"] else None,
        deadline_breached=bool(ros_row["deadline_breached"]),
        coaf_protocol_number=ros_row["coaf_protocol_number"] or "",
        coaf_receipt_hash=ros_row["coaf_receipt_hash"] or "",
        evidence_hash=ros_row["evidence_hash"] or "",
        evidence_trail_ref=ros_row["evidence_trail_ref"] or "",
        created_at=ros_row["created_at"].isoformat(),
        updated_at=ros_row["updated_at"].isoformat(),
        retain_until=ros_row["retain_until"].isoformat(),
        audit=audit,
    )


@app.get("/api/v1/reports/ros-coaf/{ros_id}/regulatory-dossier")
async def get_ros_coaf_regulatory_dossier(
    ros_id: str,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    x_auth_method: Optional[str] = Header(default=None, alias="X-Auth-Method"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    limit: int = Query(default=50, ge=1, le=200),
) -> Response:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")

    normalized_ros_id = ros_id.strip()
    if not normalized_ros_id:
        raise HTTPException(status_code=422, detail="ros_id_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_READ_ALLOWED_ROLES,
        detail="report_read_role_required",
        resource_type="ros_record",
        resource_id=normalized_ros_id,
        endpoint="/api/v1/reports/ros-coaf/{ros_id}/regulatory-dossier",
        method="GET",
    )

    ros_row: Optional[dict] = None
    audit_rows: list[dict] = []
    work_item_row: Optional[dict] = None
    event_rows: list[dict] = []
    comment_rows: list[dict] = []
    persisted_user_id: Optional[str] = None

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _require_persisted_actor_user_id(cur, effective_user_id)
            cur.execute(
                """
                SELECT
                    ros.id,
                    ros.id::text AS ros_id,
                    ros.case_id::text AS case_id,
                    ros.status,
                    COALESCE(report_ref.external_report_id, '') AS report_id,
                    ros.tipologia_code,
                    ros.tipologia_description,
                    ros.trigger_reason,
                    ros.suspected_amount_brl,
                    ros.suspected_address,
                    ros.suspected_chain,
                    ros.pdf_hash,
                    ros.pdf_path,
                    ros.generated_at,
                    ros.approved_at,
                    ros.submitted_at,
                    ros.approval_2fa_verified,
                    ros.rejection_reason,
                    ros.submission_deadline,
                    (
                        ros.deadline_breached
                        OR (
                            ros.status NOT IN ('SUBMITTED_MANUAL', 'REJECTED')
                            AND ros.submission_deadline < NOW()
                        )
                    ) AS deadline_breached,
                    ros.coaf_protocol_number,
                    ros.coaf_receipt_hash,
                    ros.evidence_hash,
                    ros.evidence_trail_ref,
                    ros.created_at,
                    ros.updated_at,
                    ros.retain_until
                FROM ros_records ros
                LEFT JOIN LATERAL (
                    SELECT external_report_id, created_at
                    FROM reports rep
                    WHERE rep.organization_id = ros.organization_id
                      AND rep.report_type = 'coaf_ready_report'
                      AND rep.metadata->>'ros_id' = ros.id::text
                    ORDER BY rep.created_at DESC, rep.id DESC
                    LIMIT 1
                ) report_ref ON TRUE
                WHERE ros.organization_id = %s
                  AND ros.id::text = %s
                """,
                (x_org_id, normalized_ros_id),
            )
            ros_row = cur.fetchone()
            if not ros_row:
                raise HTTPException(status_code=404, detail="ros_record_not_found")

            cur.execute(
                """
                SELECT id, user_id, action, metadata, created_at
                FROM audit_logs
                WHERE organization_id = %s
                  AND resource_type = 'ros_record'
                  AND resource_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (x_org_id, ros_row["id"], limit),
            )
            audit_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id,
                    module,
                    resource_type,
                    resource_id,
                    case_id,
                    report_external_id,
                    owner_user_id,
                    assigned_by_user_id,
                    queue_status,
                    priority,
                    due_at,
                    sla_breached,
                    title,
                    note,
                    metadata,
                    created_at,
                    updated_at,
                    last_activity_at
                FROM regulatory_work_items
                WHERE organization_id = %s
                  AND module = 'ros_coaf'
                  AND resource_type = 'ros_record'
                  AND resource_id = %s
                LIMIT 1
                """,
                (x_org_id, ros_row["id"]),
            )
            work_item_row = cur.fetchone()

            if work_item_row:
                cur.execute(
                    """
                    SELECT id, event_type, from_status, to_status, actor_user_id, payload, created_at
                    FROM regulatory_work_events
                    WHERE work_item_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (work_item_row["id"], limit),
                )
                event_rows = cur.fetchall()

                cur.execute(
                    """
                    SELECT id, comment_type, actor_user_id, body, created_at
                    FROM regulatory_work_comments
                    WHERE work_item_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (work_item_row["id"], limit),
                )
                comment_rows = cur.fetchall()

    audit = [
        RosCoafAuditEntry(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            created_at=row["created_at"].isoformat(),
            metadata=row["metadata"] or {},
        )
        for row in audit_rows
    ]
    ros_record = RosCoafDetailResponse(
        ros_id=ros_row["ros_id"],
        case_id=ros_row["case_id"],
        report_id=ros_row["report_id"] or "",
        status=ros_row["status"],
        tipologia_code=ros_row["tipologia_code"],
        tipologia_description=ros_row["tipologia_description"],
        trigger_reason=ros_row["trigger_reason"],
        suspected_amount_brl=float(ros_row["suspected_amount_brl"]) if ros_row["suspected_amount_brl"] is not None else None,
        suspected_address=ros_row["suspected_address"] or "",
        suspected_chain=ros_row["suspected_chain"] or "",
        pdf_hash=ros_row["pdf_hash"] or "",
        pdf_path=ros_row["pdf_path"] or "",
        generated_at=_isoformat(ros_row.get("generated_at")),
        approved_at=_isoformat(ros_row.get("approved_at")),
        submitted_at=_isoformat(ros_row.get("submitted_at")),
        approval_2fa_verified=bool(ros_row["approval_2fa_verified"]),
        rejection_reason=ros_row["rejection_reason"] or "",
        submission_deadline=_isoformat(ros_row.get("submission_deadline")),
        deadline_breached=bool(ros_row["deadline_breached"]),
        coaf_protocol_number=ros_row["coaf_protocol_number"] or "",
        coaf_receipt_hash=ros_row["coaf_receipt_hash"] or "",
        evidence_hash=ros_row["evidence_hash"] or "",
        evidence_trail_ref=ros_row["evidence_trail_ref"] or "",
        created_at=ros_row["created_at"].isoformat(),
        updated_at=ros_row["updated_at"].isoformat(),
        retain_until=ros_row["retain_until"].isoformat(),
        audit=audit,
    )

    work_item = None
    if work_item_row:
        work_item = RosCoafWorkItemSnapshot(
            id=work_item_row["id"],
            module=work_item_row["module"],
            resource_type=work_item_row["resource_type"],
            resource_id=work_item_row["resource_id"],
            case_id=work_item_row["case_id"],
            report_external_id=work_item_row.get("report_external_id"),
            owner_user_id=work_item_row.get("owner_user_id"),
            assigned_by_user_id=work_item_row.get("assigned_by_user_id"),
            queue_status=work_item_row["queue_status"],
            priority=work_item_row["priority"],
            due_at=_isoformat(work_item_row.get("due_at")),
            sla_breached=bool(work_item_row.get("sla_breached")),
            title=work_item_row.get("title"),
            note=work_item_row.get("note"),
            metadata=work_item_row.get("metadata") or {},
            created_at=work_item_row["created_at"].isoformat(),
            updated_at=work_item_row["updated_at"].isoformat(),
            last_activity_at=work_item_row["last_activity_at"].isoformat(),
        )

    work_events = [
        RosCoafWorkEventEntry(
            id=row["id"],
            event_type=row["event_type"],
            from_status=row.get("from_status"),
            to_status=row.get("to_status"),
            actor_user_id=row.get("actor_user_id"),
            payload=row.get("payload") or {},
            created_at=row["created_at"].isoformat(),
        )
        for row in event_rows
    ]
    work_comments = [
        RosCoafWorkCommentEntry(
            id=row["id"],
            comment_type=row["comment_type"],
            actor_user_id=row.get("actor_user_id"),
            body=row.get("body") or "",
            created_at=row["created_at"].isoformat(),
        )
        for row in comment_rows
    ]

    timeline: list[tuple[datetime, RosCoafRegulatoryTimelineEntry]] = []
    for entry in audit:
        created_at_dt = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
        timeline.append(
            (
                created_at_dt,
                RosCoafRegulatoryTimelineEntry(
                    id=f"audit-{entry.id}",
                    source="domain_audit",
                    label=entry.action,
                    detail=_summarize_metadata_fields(
                        entry.metadata if isinstance(entry.metadata, dict) else None,
                        ["request_id", "report_id", "filename", "dossier_sha256", "external_user_id", "file_hash_sha256"],
                    ),
                    actor=str(entry.user_id) if entry.user_id else None,
                    created_at=entry.created_at,
                ),
            )
        )

    for entry in work_events:
        created_at_dt = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
        timeline.append(
            (
                created_at_dt,
                RosCoafRegulatoryTimelineEntry(
                    id=f"event-{entry.id}",
                    source="work_event",
                    label=_format_work_event_label(entry.event_type, entry.from_status, entry.to_status),
                    detail=_summarize_metadata_fields(
                        entry.payload if isinstance(entry.payload, dict) else None,
                        ["ros_id", "report_id", "request_id", "coaf_protocol_number", "coaf_receipt_hash"],
                    ),
                    actor=str(entry.actor_user_id) if entry.actor_user_id else None,
                    created_at=entry.created_at,
                ),
            )
        )

    for entry in work_comments:
        created_at_dt = datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
        timeline.append(
            (
                created_at_dt,
                RosCoafRegulatoryTimelineEntry(
                    id=f"comment-{entry.id}",
                    source="work_comment",
                    label=entry.comment_type,
                    detail=entry.body.strip() or None,
                    actor=str(entry.actor_user_id) if entry.actor_user_id else None,
                    created_at=entry.created_at,
                ),
            )
        )

    unified_timeline = [entry for _, entry in sorted(timeline, key=lambda item: item[0], reverse=True)]

    dossier = RosCoafRegulatoryDossierResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        ros_record=ros_record,
        work_item=work_item,
        work_events=work_events,
        work_comments=work_comments,
        unified_timeline=unified_timeline,
    )
    serialized_without_hash = dossier.model_dump_json(indent=2)
    dossier_sha256 = hashlib.sha256(serialized_without_hash.encode("utf-8")).hexdigest()
    dossier.dossier_sha256 = dossier_sha256
    serialized_with_hash = dossier.model_dump_json(indent=2)
    dossier_filename = _build_ros_coaf_regulatory_dossier_filename(ros_record.ros_id)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=persisted_user_id,
                action="coaf_regulatory_dossier_downloaded",
                resource_type="ros_record",
                resource_id=ros_row["id"],
                metadata={
                    "request_id": x_request_id,
                    "ros_id": ros_record.ros_id,
                    "report_id": ros_record.report_id,
                    "filename": dossier_filename,
                    "content_type": "application/json",
                    "dossier_sha256": dossier_sha256,
                    "auth_method": x_auth_method,
                    "role": x_role,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return Response(
        content=serialized_with_hash,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{dossier_filename}"',
            "X-Ontrack-Dossier-SHA256": dossier_sha256,
        },
    )


@app.post("/api/v1/reports/ros-coaf/{ros_id}/approve", response_model=ApproveRosCoafResponse)
async def approve_ros_coaf_report(
    ros_id: str,
    body: ApproveRosCoafRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> ApproveRosCoafResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_coaf_report_review_auth(
        pool=pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        ros_id=ros_id,
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )
    if not body.approved and not body.rejection_reason:
        raise HTTPException(status_code=422, detail="rejection_reason_required")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    next_status = "APPROVED" if body.approved else "REJECTED"

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _require_persisted_actor_user_id(cur, effective_user_id)

            cur.execute(
                """
                SELECT id, case_id, status, pdf_hash
                FROM ros_records
                WHERE id = %s
                  AND organization_id = %s
                """,
                (ros_id, x_org_id),
            )
            ros = cur.fetchone()
            if not ros:
                raise HTTPException(status_code=404, detail="ros_record_not_found")
            if ros["status"] != "PENDING_APPROVAL":
                raise HTTPException(status_code=409, detail="ros_record_not_pending_approval")

            cur.execute(
                """
                UPDATE ros_records
                   SET status = %s,
                       approved_by_user_id = %s,
                       approved_at = %s,
                       approval_2fa_verified = %s,
                       rejection_reason = %s,
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (
                    next_status,
                    persisted_user_id,
                    reviewed_at,
                    body.approved,
                    None if body.approved else body.rejection_reason,
                    ros_id,
                ),
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=persisted_user_id,
                action="coaf_report_approved" if body.approved else "coaf_report_rejected",
                resource_type="ros_record",
                resource_id=ros_id,
                metadata={
                    "request_id": x_request_id,
                    "status": next_status,
                    "rejection_reason": body.rejection_reason,
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=x_org_id,
                event_type="COAF_ROS_APPROVED" if body.approved else "COAF_ROS_REJECTED",
                event_payload={
                    "ros_id": ros_id,
                    "status": next_status,
                    "pdf_hash": ros["pdf_hash"],
                    "rejection_reason": body.rejection_reason,
                },
                actor_user_id=persisted_user_id,
                case_id=str(ros["case_id"]) if ros["case_id"] else None,
                regulatory_basis=["Lei 9.613/98 Art. 11", "IN BCB 739 Art. 1° V"],
            )
        conn.commit()

    return ApproveRosCoafResponse(
        ros_id=ros_id,
        status=next_status,
        approved_at=reviewed_at,
        approval_2fa_verified=body.approved,
    )


@app.post("/api/v1/reports/ros-coaf/{ros_id}/submitted", response_model=SubmitRosCoafResponse)
async def mark_ros_coaf_submitted(
    ros_id: str,
    body: SubmitRosCoafRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> SubmitRosCoafResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_coaf_report_submission_auth(
        pool=pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        ros_id=ros_id,
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )
    if not body.coaf_protocol_number.strip():
        raise HTTPException(status_code=422, detail="coaf_protocol_number_required")
    submitted_at = datetime.now(timezone.utc).isoformat()
    receipt_hash = (
        body.coaf_receipt_hash.lower().strip()
        if body.coaf_receipt_hash
        else hashlib.sha256(f"{ros_id}:{body.coaf_protocol_number}:{submitted_at}".encode("utf-8")).hexdigest()
    )
    if len(receipt_hash) != 64:
        raise HTTPException(status_code=422, detail="coaf_receipt_hash_must_be_sha256")

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _require_persisted_actor_user_id(cur, effective_user_id)

            cur.execute(
                """
                SELECT id, case_id, status, pdf_hash, submission_deadline
                FROM ros_records
                WHERE id = %s
                  AND organization_id = %s
                """,
                (ros_id, x_org_id),
            )
            ros = cur.fetchone()
            if not ros:
                raise HTTPException(status_code=404, detail="ros_record_not_found")
            if ros["status"] != "APPROVED":
                raise HTTPException(status_code=409, detail="ros_record_not_approved")

            cur.execute(
                """
                UPDATE ros_records
                   SET status = 'SUBMITTED_MANUAL',
                       submitted_by_user_id = %s,
                       submitted_at = %s,
                       coaf_protocol_number = %s,
                       coaf_receipt_hash = %s,
                       updated_at = NOW()
                 WHERE id = %s
                """,
                (
                    persisted_user_id,
                    submitted_at,
                    body.coaf_protocol_number.strip(),
                    receipt_hash,
                    ros_id,
                ),
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=persisted_user_id,
                action="coaf_report_submitted_manual",
                resource_type="ros_record",
                resource_id=ros_id,
                metadata={
                    "request_id": x_request_id,
                    "coaf_protocol_number": body.coaf_protocol_number.strip(),
                    "coaf_receipt_hash": receipt_hash,
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=x_org_id,
                event_type="COAF_ROS_SUBMITTED_MANUAL",
                event_payload={
                    "ros_id": ros_id,
                    "coaf_protocol_number": body.coaf_protocol_number.strip(),
                    "coaf_receipt_hash": receipt_hash,
                    "pdf_hash": ros["pdf_hash"],
                    "deadline_breached": bool(
                        ros["submission_deadline"] and ros["submission_deadline"] < datetime.now(timezone.utc)
                    ),
                },
                actor_user_id=persisted_user_id,
                case_id=str(ros["case_id"]) if ros["case_id"] else None,
                regulatory_basis=["Lei 9.613/98 Art. 11-B", "IN BCB 739 Art. 1° V"],
            )
        conn.commit()

    return SubmitRosCoafResponse(
        ros_id=ros_id,
        status="SUBMITTED_MANUAL",
        submitted_at=submitted_at,
        coaf_protocol_number=body.coaf_protocol_number.strip(),
        coaf_receipt_hash=receipt_hash,
    )


@app.get("/api/v1/reports", response_model=ReportListResponse)
async def list_reports(
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    page: int = Query(default=1),
    limit: int = Query(default=20),
    report_id: Optional[str] = Query(default=None),
    case_id: Optional[str] = Query(default=None),
    report_type: Optional[str] = Query(default=None),
    created_from: Optional[datetime] = Query(default=None),
    created_to: Optional[datetime] = Query(default=None),
) -> ReportListResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )

    canonical_report_type: Optional[str] = None
    if report_type:
        canonical_report_type, _ = resolve_report_type(report_type)
    normalized_report_id = report_id.strip() if report_id else None

    safe_page, safe_limit, offset = _normalize_reports_pagination(page=page, limit=limit)
    normalized_created_from = _normalize_report_filter_datetime(created_from)
    normalized_created_to = _normalize_report_filter_datetime(created_to)

    if normalized_created_from and normalized_created_to and normalized_created_from > normalized_created_to:
        raise HTTPException(status_code=422, detail="invalid_created_range")

    if case_id:
        try:
            case_id = str(UUID(case_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="invalid_case_id") from None
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_READ_ALLOWED_ROLES,
        detail="report_read_role_required",
        resource_type="report",
        resource_id=normalized_report_id or case_id,
        endpoint="/api/v1/reports",
        method="GET",
    )

    query_filters = ["r.organization_id = %s"]
    query_params: list = [x_org_id]

    if normalized_report_id:
        query_filters.append("r.external_report_id = %s")
        query_params.append(normalized_report_id)
    if case_id:
        query_filters.append("r.case_id = %s")
        query_params.append(case_id)
    if canonical_report_type:
        query_filters.append("r.report_type = %s")
        query_params.append(canonical_report_type)
    if normalized_created_from:
        query_filters.append("r.created_at >= %s")
        query_params.append(normalized_created_from)
    if normalized_created_to:
        query_filters.append("r.created_at <= %s")
        query_params.append(normalized_created_to)

    where_clause = " AND ".join(query_filters)

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM reports r
                WHERE {where_clause}
                """,
                tuple(query_params),
            )
            count_row = cur.fetchone() or {}
            total = int(count_row.get("total") or 0)

            cur.execute(
                f"""
                SELECT
                  r.external_report_id,
                  r.case_id,
                  r.report_type_requested,
                  r.report_type,
                  r.content_type,
                  r.file_hash,
                  r.onchain_hash,
                  r.created_at,
                  r.metadata,
                  EXISTS (
                    SELECT 1
                    FROM audit_logs a
                    WHERE a.action = 'report_downloaded'
                      AND a.organization_id = r.organization_id
                      AND a.metadata->>'report_id' = COALESCE(r.external_report_id, '')
                  ) AS has_download_audit
                FROM reports r
                WHERE {where_clause}
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT %s OFFSET %s
                """,
                tuple([*query_params, safe_limit, offset]),
            )
            rows = cur.fetchall() or []

    items = [
        _serialize_report_list_row(row)
        for row in rows
        if row.get("external_report_id")
    ]

    return ReportListResponse(
        data=items,
        page=safe_page,
        limit=safe_limit,
        total=total,
        has_more=(offset + safe_limit) < total,
    )


@app.get("/api/v1/reports/{report_id}", response_model=GenerateReportResponse)
async def get_report(
    report_id: str,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    x_auth_method: Optional[str] = Header(default=None, alias="X-Auth-Method"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
) -> GenerateReportResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    normalized_report_id = report_id.strip()
    if not normalized_report_id:
        raise HTTPException(status_code=422, detail="report_id_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_DETAIL_ALLOWED_ROLES,
        detail="report_detail_role_required",
        resource_type="report",
        resource_id=normalized_report_id,
        endpoint="/api/v1/reports/{report_id}",
        method="GET",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  external_report_id,
                  case_id,
                  report_type_requested,
                  report_type,
                  content_type,
                  file_hash,
                  onchain_hash,
                  created_at,
                  metadata
                FROM reports
                WHERE external_report_id = %s
                """,
                (normalized_report_id,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="report_not_found")

    report_type = row.get("report_type") or row.get("report_type_requested")
    if not report_type:
        raise HTTPException(status_code=409, detail="report_missing_type")

    if report_type == "legal_report":
        _require_strong_auth_for_legal_report(
            x_auth_method=x_auth_method,
            x_role=x_role,
            x_2fa=x_2fa,
            x_mfa_mode=x_mfa_mode,
            x_mfa_provider_homologated=x_mfa_provider_homologated,
        )

    created_at = row.get("created_at")
    if isinstance(created_at, datetime):
        created_at_value = created_at.astimezone(timezone.utc).isoformat()
    else:
        created_at_value = str(created_at) if created_at else ""

    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    case_id = row.get("case_id") or metadata.get("case_reference_id")
    if not case_id:
        raise HTTPException(status_code=409, detail="report_missing_case_id")

    file_hash = row.get("file_hash")
    if not file_hash:
        raise HTTPException(status_code=409, detail="report_missing_hash")

    content_type = row.get("content_type") or "application/pdf"

    return GenerateReportResponse(
        report_id=row.get("external_report_id") or report_id,
        case_id=str(case_id),
        report_type_requested=row.get("report_type_requested") or report_type,
        report_type=report_type,
        created_at=created_at_value,
        file_hash_sha256=file_hash,
        onchain_hash=row.get("onchain_hash"),
        content_type=content_type,
    )


@app.get("/api/v1/reports/{report_id}/ros-coaf-ref", response_model=ReportRosCoafRefResponse)
async def get_report_ros_coaf_ref(
    report_id: str,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> ReportRosCoafRefResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")

    normalized_report_id = report_id.strip()
    if not normalized_report_id:
        raise HTTPException(status_code=422, detail="report_id_required")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=x_org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=x_request_id,
        x_role=x_role,
        allowed_roles=REPORT_READ_ALLOWED_ROLES,
        detail="report_read_role_required",
        resource_type="report",
        resource_id=normalized_report_id,
        endpoint="/api/v1/reports/{report_id}/ros-coaf-ref",
        method="GET",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT external_report_id, metadata
                FROM reports
                WHERE external_report_id = %s
                """,
                (normalized_report_id,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="report_not_found")

    metadata = row.get("metadata") or {}
    ros_id = metadata.get("ros_id") if isinstance(metadata, dict) else None
    ros_id_value = ros_id.strip() if isinstance(ros_id, str) and ros_id.strip() else None
    return ReportRosCoafRefResponse(
        report_id=row.get("external_report_id") or normalized_report_id,
        ros_id=ros_id_value,
    )


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(
    report_id: str,
    case_id: Optional[str] = Query(default=None),
    report_type: Optional[str] = Query(default=None),
    created_at: Optional[str] = Query(default=None),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_linked_user_id: Optional[str] = Header(default=None, alias="X-Linked-User-Id"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
    x_auth_method: Optional[str] = Header(default=None, alias="X-Auth-Method"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
) -> Response:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT case_id, external_report_id, report_type, report_type_requested, content_type, created_at, metadata
                FROM reports
                WHERE external_report_id = %s
                """,
                (report_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="report_not_found")

            metadata = row.get("metadata") or {}
            effective_case_id = (
                str(row["case_id"])
                if row.get("case_id")
                else str(metadata.get("case_reference_id") or metadata.get("ros_id") or case_id or "").strip() or None
            )
            persisted_report_type = str(row.get("report_type") or report_type or "").strip()
            if not effective_case_id or not persisted_report_type:
                raise HTTPException(status_code=404, detail="report_download_source_not_found")

            canonical_report_type, _ = resolve_report_type(persisted_report_type)
            expected_report_id = _compute_report_id(effective_case_id, canonical_report_type)
            if expected_report_id != report_id:
                raise HTTPException(status_code=404, detail="report_not_found")

            persisted_created_at_raw = row.get("created_at")
            persisted_created_at = (
                persisted_created_at_raw.isoformat()
                if isinstance(persisted_created_at_raw, datetime)
                else str(persisted_created_at_raw or created_at or "")
            )
            if not persisted_created_at:
                raise HTTPException(status_code=404, detail="report_created_at_not_found")

    if canonical_report_type == "legal_report":
        _require_strong_auth_for_legal_report(
            x_auth_method=x_auth_method,
            x_role=x_role,
            x_2fa=x_2fa,
            x_mfa_mode=x_mfa_mode,
            x_mfa_provider_homologated=x_mfa_provider_homologated,
        )
    else:
        _require_role_with_audit(
            pool,
            organization_id=x_org_id,
            user_id=effective_user_id,
            external_user_id=external_actor_user_id,
            request_id=x_request_id,
            x_role=x_role,
            allowed_roles=REPORT_DOWNLOAD_ALLOWED_ROLES,
            detail="report_download_role_required",
            resource_type="report",
            resource_id=report_id,
            endpoint="/api/v1/reports/{report_id}/download",
            method="GET",
        )
    content = _build_pdf_bytes(case_id=effective_case_id, report_type=canonical_report_type, created_at=persisted_created_at)
    file_hash_sha256 = hashlib.sha256(content).hexdigest()
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=effective_user_id,
                action="report_downloaded",
                resource_type="report",
                resource_id=None,
                metadata={
                    "request_id": x_request_id,
                    "report_id": report_id,
                    "case_id": effective_case_id,
                    "report_type": canonical_report_type,
                    "created_at": persisted_created_at,
                    "content_type": "application/pdf",
                    "file_hash_sha256": file_hash_sha256,
                    "auth_method": x_auth_method,
                    "role": x_role,
                    "two_fa": x_2fa,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return Response(content=content, media_type="application/pdf", headers={"content-disposition": f'attachment; filename=\"report-{report_id}.pdf\"'})
