from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
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


def _require_coaf_report_approval_auth(
    *,
    x_role: Optional[str],
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
    x_2fa: Optional[str],
) -> None:
    normalized_role = (x_role or "").upper()
    if normalized_role not in {"ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}:
        raise HTTPException(status_code=403, detail="coaf_report_requires_compliance_officer")
    if (x_mfa_mode or "").lower() != "external_provider":
        raise HTTPException(status_code=403, detail="coaf_report_requires_external_provider_mfa")
    if (x_mfa_provider_homologated or "").lower() != "true":
        raise HTTPException(status_code=403, detail="coaf_report_requires_homologated_provider")
    if x_2fa not in {"managed_externally", "managed_externally_homologated", "ok"}:
        raise HTTPException(status_code=403, detail="2fa_required")


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

    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, resource_id, json.dumps(normalized_metadata)),
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
async def generate_report(body: GenerateReportRequest) -> GenerateReportResponse:
    created_at = datetime.now(timezone.utc).isoformat()
    canonical_report_type, requested_alias = resolve_report_type(body.report_type)

    content = _build_pdf_bytes(case_id=body.case_id, report_type=canonical_report_type, created_at=created_at)
    file_hash = hashlib.sha256(content).hexdigest()
    onchain_hash = "pending" if body.include_onchain_hash else None
    report_id = _compute_report_id(body.case_id, canonical_report_type)

    return GenerateReportResponse(
        report_id=report_id,
        case_id=body.case_id,
        report_type_requested=requested_alias or canonical_report_type,
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
    _require_coaf_report_approval_auth(
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_coaf_report")

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
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (external_report_id)
                DO UPDATE SET
                    file_hash = EXCLUDED.file_hash,
                    content_type = EXCLUDED.content_type,
                    metadata = EXCLUDED.metadata
                """,
                (
                    x_org_id,
                    str(ros["case_id"]) if ros["case_id"] else None,
                    report_id,
                    "coaf_ready_report",
                    "coaf_ready_report",
                    draft.content_type,
                    draft.file_hash_sha256,
                    None,
                    json.dumps(
                        {
                            "ros_id": str(ros["id"]),
                            "generated_at": draft.generated_at,
                            "title": draft.title,
                            "request_id": x_request_id,
                        }
                    ),
                ),
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
    _require_coaf_report_approval_auth(
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )
    if not body.approved and not body.rejection_reason:
        raise HTTPException(status_code=422, detail="rejection_reason_required")

    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    reviewed_at = datetime.now(timezone.utc).isoformat()
    next_status = "APPROVED" if body.approved else "REJECTED"

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_coaf_report")

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
    _require_coaf_report_approval_auth(
        x_role=x_role,
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
        x_2fa=x_2fa,
    )
    if not body.coaf_protocol_number.strip():
        raise HTTPException(status_code=422, detail="coaf_protocol_number_required")

    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
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
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_coaf_report")

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


@app.get("/api/v1/reports/{report_id}", response_model=GenerateReportResponse)
async def get_report(
    report_id: str,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_auth_method: Optional[str] = Header(default=None, alias="X-Auth-Method"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
    x_2fa: Optional[str] = Header(default=None, alias="X-2FA"),
    x_mfa_mode: Optional[str] = Header(default=None, alias="X-MFA-Mode"),
    x_mfa_provider_homologated: Optional[str] = Header(default=None, alias="X-MFA-Provider-Homologated"),
) -> GenerateReportResponse:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")

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
                  created_at
                FROM reports
                WHERE external_report_id = %s
                """,
                (report_id,),
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

    case_id = row.get("case_id")
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


@app.get("/api/v1/reports/{report_id}/download")
async def download_report(
    report_id: str,
    case_id: str = Query(...),
    report_type: str = Query(...),
    created_at: str = Query(...),
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
    canonical_report_type, _ = resolve_report_type(report_type)
    expected_report_id = _compute_report_id(case_id, canonical_report_type)
    if expected_report_id != report_id:
        raise HTTPException(status_code=404, detail="report_not_found")
    if canonical_report_type == "legal_report":
        _require_strong_auth_for_legal_report(
            x_auth_method=x_auth_method,
            x_role=x_role,
            x_2fa=x_2fa,
            x_mfa_mode=x_mfa_mode,
            x_mfa_provider_homologated=x_mfa_provider_homologated,
        )
    content = _build_pdf_bytes(case_id=case_id, report_type=canonical_report_type, created_at=created_at)
    file_hash_sha256 = hashlib.sha256(content).hexdigest()
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )

    if x_org_id:
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
                        "case_id": case_id,
                        "report_type": canonical_report_type,
                        "created_at": created_at,
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
