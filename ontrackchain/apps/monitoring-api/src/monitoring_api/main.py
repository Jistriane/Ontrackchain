from __future__ import annotations

import base64
import binascii
import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from ontrackchain_shared import (
    is_available_for_plan,
    normalize_plan,
    normalize_slug,
    plan_rank,
    pricing_table_hash,
    resolve_canonical_identifier,
)
from pydantic import BaseModel
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
    enable_test_endpoints: bool = True
    monitoring_internal_metrics_enabled: bool = True
    monitoring_alerts_last_hour_warn_threshold: int = 5
    monitoring_critical_alerts_last_24h_critical_threshold: int = 1
    monitoring_expired_quotes_warn_threshold: int = 10
    monitoring_open_quotes_warn_threshold: int = 25
    alertmanager_webhook_bearer_token: str = "alertmanager-local-token"


settings = Settings()

app = FastAPI(title="OnTrackChain Monitoring API")
QUOTE_TTL_MINUTES = 15
CALCULATION_VERSION = "v1.0"
SUPPORTED_CHAINS = {"ethereum", "polygon", "bsc", "arbitrum", "base", "bitcoin"}
MONITORING_CORE_READ_ALLOWED_ROLES = {
    "ADMIN",
    "ANALYST",
    "OTK_ANALYST",
    "AUDITOR",
    "VIEWER",
    "OTK_VIEWER",
    "TESTER",
    "OTK_TESTER",
}
MONITORING_CORE_OPERATION_ALLOWED_ROLES = {"ADMIN", "ANALYST", "OTK_ANALYST"}

MONITORING_OPERATION_ALIASES = {
    "30d": "monitoring_30days",
    "monthly": "monitoring_30days",
    "90d": "monitoring_90days",
    "quarterly": "monitoring_90days",
    "365d": "monitoring_365days",
    "annual": "monitoring_365days",
}

MONITORING_OPERATION_CATALOG = {
    "monitoring_30days": {
        "label": "Monitoramento 30 Dias",
        "description": "Watchlist ativa por 30 dias com alerta de movimentacao.",
        "min_plan": "starter",
        "aliases_accepted": ["30d", "monthly"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 5,
        "output_format": "json+alerts",
        "regulatory_reference": "Res. BCB 520 Art. 45",
        "tags": ["watchlist", "alerts", "starter"],
    },
    "monitoring_90days": {
        "label": "Monitoramento 90 Dias",
        "description": "Watchlist ativa por 90 dias com retencao estendida.",
        "min_plan": "professional",
        "aliases_accepted": ["90d", "quarterly"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 5,
        "output_format": "json+alerts",
        "regulatory_reference": "Res. BCB 520 Art. 45",
        "tags": ["watchlist", "alerts", "professional"],
    },
    "monitoring_365days": {
        "label": "Monitoramento 365 Dias",
        "description": "Watchlist ativa por 365 dias com historico de longo prazo.",
        "min_plan": "enterprise",
        "aliases_accepted": ["365d", "annual"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 5,
        "output_format": "json+alerts",
        "regulatory_reference": "Res. BCB 520 Art. 45",
        "tags": ["watchlist", "alerts", "enterprise"],
    },
}

MONITORING_PRICING_TABLE = {
    "operation_cost": {
        "monitoring_30days": 3.0,
        "monitoring_90days": 7.0,
        "monitoring_365days": 20.0,
    },
    "chain_multiplier": {
        "ethereum": 1.0,
        "polygon": 0.8,
        "bsc": 0.8,
        "arbitrum": 0.9,
        "base": 0.8,
        "bitcoin": 1.5,
    },
    "plan_discount": {
        "starter": 0.0,
        "professional": 0.0,
        "enterprise": 0.10,
    },
}


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


def _apply_rls_context(conn, org_id: Optional[str]) -> None:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, true)", (org_id,))


def _require_org_id(org_id: Optional[str]) -> str:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    return org_id


def _validate_chain(chain: str) -> str:
    normalized = normalize_slug(chain)
    if normalized not in SUPPORTED_CHAINS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_chain",
                "message": "Chain fora do escopo do MVP",
                "supported_chains": sorted(SUPPORTED_CHAINS),
            },
        )
    return normalized


def _resolve_operation(raw_input: str) -> tuple[str, Optional[dict]]:
    try:
        canonical, was_alias = resolve_canonical_identifier(
            raw_input,
            canonical_values=list(MONITORING_OPERATION_CATALOG.keys()),
            aliases=MONITORING_OPERATION_ALIASES,
        )
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_monitoring_operation",
                "message": f"operation '{raw_input}' nao reconhecida",
                "valid_operations": sorted(MONITORING_OPERATION_CATALOG.keys()),
                "accepted_aliases": sorted(MONITORING_OPERATION_ALIASES.keys()),
            },
        ) from None
    if not was_alias:
        return canonical, None
    return canonical, {"warning": "operation_alias_resolved", "requested": raw_input, "canonical": canonical}


def _is_operation_available(operation: str, plan: str) -> bool:
    canonical, _ = _resolve_operation(operation)
    min_plan = MONITORING_OPERATION_CATALOG[canonical]["min_plan"]
    return is_available_for_plan(min_plan, plan)


def _required_plan_for_operation(operation: str) -> str:
    canonical, _ = _resolve_operation(operation)
    return str(MONITORING_OPERATION_CATALOG[canonical]["min_plan"])


def _build_operation_detail(canonical: str, current_plan: str, include_deprecated: bool) -> dict:
    meta = MONITORING_OPERATION_CATALOG[canonical]
    available = _is_operation_available(canonical, current_plan)
    return {
        "canonical": canonical,
        "label": meta["label"],
        "description": meta["description"],
        "cost_credits": float(MONITORING_PRICING_TABLE["operation_cost"][canonical]),
        "available": available,
        "upgrade_required": None if available else meta["min_plan"],
        "min_plan": meta["min_plan"],
        "aliases_accepted": list(meta["aliases_accepted"]),
        "deprecated_aliases": list(meta["deprecated_aliases"]) if include_deprecated else [],
        "chains_supported": meta["chains_supported"],
        "avg_duration_seconds": meta["avg_duration_seconds"],
        "output_format": meta["output_format"],
        "regulatory_reference": meta["regulatory_reference"],
        "tags": meta["tags"],
    }


def _calculate_quote_cost(operation: str, chain: str, plan: str) -> dict:
    operation_cost = float(MONITORING_PRICING_TABLE["operation_cost"][operation])
    chain_multiplier = float(MONITORING_PRICING_TABLE["chain_multiplier"].get(chain, 1.0))
    subtotal = operation_cost * chain_multiplier
    discount_pct = float(MONITORING_PRICING_TABLE["plan_discount"].get(plan, 0.0))
    discount = subtotal * discount_pct
    total = subtotal - discount
    return {
        "breakdown": [
            {
                "item": f"Operacao de monitoring: {operation}",
                "base_cost": operation_cost,
                "chain": chain,
                "chain_multiplier": chain_multiplier,
                "subtotal": round(subtotal, 4),
            }
        ],
        "subtotal_credits": round(subtotal, 4),
        "plan_discount": round(discount, 4),
        "total_credits": round(total, 4),
        "pricing_table_hash": pricing_table_hash(MONITORING_PRICING_TABLE),
        "calculation_version": CALCULATION_VERSION,
    }


def _build_monitoring_quote_payload(
    *,
    watchlist_name: str,
    priority: str,
    address: str,
    chain: str,
    operation_requested: str,
    plan: str,
) -> dict:
    warnings: list[dict] = []
    canonical_operation, alias_warning = _resolve_operation(operation_requested)
    if alias_warning:
        warnings.append(alias_warning)
    if not _is_operation_available(canonical_operation, plan):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "operation_not_available_on_plan",
                "operation": canonical_operation,
                "required_plan": _required_plan_for_operation(canonical_operation),
                "current_plan": plan,
            },
        )
    quote = _calculate_quote_cost(canonical_operation, chain, plan)
    quote_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=QUOTE_TTL_MINUTES)
    total_credits = float(quote["total_credits"])
    return {
        "quote_id": quote_id,
        "expires_at": expires_at,
        "watchlist_name": watchlist_name,
        "priority": priority,
        "address": address,
        "chain": chain,
        "operation_requested": operation_requested,
        "operation_canonical": canonical_operation,
        "breakdown": quote["breakdown"],
        "subtotal_credits": float(quote["subtotal_credits"]),
        "plan_discount": float(quote["plan_discount"]),
        "total_credits": total_credits,
        "pricing_table_hash": quote["pricing_table_hash"],
        "calculation_version": quote["calculation_version"],
        "plan": plan,
        "warnings": warnings,
    }


def _persist_monitoring_quote(cur, *, org_id: str, user_id: Optional[str], quote_payload: dict) -> None:
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    cur.execute(
        """
        INSERT INTO monitoring_quotes (
          id, organization_id, user_id, plan, plan_snapshot, operation_requested, operation_canonical,
          chain, target_address, watchlist_name, priority, quote_breakdown, subtotal_credits,
          plan_discount, total_credits, pricing_table_hash, calculation_version, expires_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
        """,
        (
            quote_payload["quote_id"],
            org_id,
            persisted_user_id,
            quote_payload["plan"],
            quote_payload["plan"],
            quote_payload["operation_requested"],
            quote_payload["operation_canonical"],
            quote_payload["chain"],
            quote_payload["address"],
            quote_payload["watchlist_name"],
            quote_payload["priority"],
            json.dumps(quote_payload["breakdown"]),
            quote_payload["subtotal_credits"],
            quote_payload["plan_discount"],
            quote_payload["total_credits"],
            quote_payload["pricing_table_hash"],
            quote_payload["calculation_version"],
            quote_payload["expires_at"],
        ),
    )


def _record_credit_ledger(cur, *, org_id: str, case_id: str, amount: float, balance_after: float, metadata: dict) -> None:
    cur.execute(
        """
        INSERT INTO credit_ledger (org_id, case_id, action, amount, balance_after, metadata)
        VALUES (%s, %s, 'PRE_HOLD', %s, %s, %s::jsonb)
        """,
        (org_id, case_id, amount, balance_after, json.dumps(metadata)),
    )


def _resolve_persisted_user_id(cur, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    try:
        candidate_user_id = str(UUID(str(user_id)))
        cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate_user_id,))
        if cur.fetchone():
            return candidate_user_id
    except (TypeError, ValueError):
        return None
    return None


def _resolve_actor_ids(
    *,
    external_user_id: Optional[str],
    linked_user_id: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    effective_user_id = linked_user_id or external_user_id
    if linked_user_id and external_user_id and linked_user_id != external_user_id:
        return effective_user_id, external_user_id
    return effective_user_id, None


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
    resource_id: Optional[str],
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
                    resource_id=resource_id,
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
        logger.exception("failed_to_record_authorization_denied")


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
    resource_id: Optional[str],
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


def _normalized_role(x_role: Optional[str]) -> str:
    return (x_role or "").strip().upper()


def _require_role(x_role: Optional[str], *, allowed_roles: set[str], detail: str) -> str:
    role = _normalized_role(x_role)
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return role


def _require_admin_role(x_role: Optional[str]) -> str:
    return _require_role(x_role, allowed_roles={"ADMIN"}, detail="admin_role_required")


def _require_operational_read_role(x_role: Optional[str]) -> str:
    return _require_role(x_role, allowed_roles={"ADMIN", "AUDITOR"}, detail="monitoring_read_role_required")


def _require_test_trigger_role_with_audit(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
    resource_id: Optional[str],
    endpoint: str,
    method: str,
) -> str:
    return _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "TESTER", "OTK_TESTER"},
        detail="monitoring_test_trigger_role_required",
        resource_type="monitoring_test_alert",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_monitoring_core_read_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
    resource_type: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> str:
    return _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles=MONITORING_CORE_READ_ALLOWED_ROLES,
        detail="monitoring_read_role_required",
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        endpoint=endpoint,
        method=method,
    )


def _require_monitoring_operational_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
    resource_type: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> str:
    return _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles=MONITORING_CORE_OPERATION_ALLOWED_ROLES,
        detail="monitoring_operational_role_required",
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        endpoint=endpoint,
        method=method,
    )


def _require_internal_bearer_token(authorization: Optional[str]) -> None:
    expected = f"Bearer {settings.alertmanager_webhook_bearer_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid_internal_token")


def _parse_optional_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _encode_operational_alert_cursor(*, last_received_at: datetime, event_id: UUID | str) -> str:
    payload = json.dumps(
        {"last_received_at": last_received_at.isoformat(), "id": str(event_id)},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def _decode_operational_alert_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        last_received_at = _parse_optional_timestamp(payload.get("last_received_at"))
        event_id = UUID(str(payload.get("id")))
    except (ValueError, TypeError, json.JSONDecodeError, binascii.Error):
        raise HTTPException(status_code=422, detail="invalid_operational_alert_cursor") from None

    if not last_received_at:
        raise HTTPException(status_code=422, detail="invalid_operational_alert_cursor")
    return last_received_at, event_id


def _persist_operational_alert_event(
    cur,
    *,
    receiver: str,
    group_key: Optional[str],
    alert_status: str,
    alertname: str,
    service: Optional[str],
    severity: Optional[str],
    fingerprint: str,
    labels: dict,
    annotations: dict,
    starts_at: Optional[datetime],
    ends_at: Optional[datetime],
    generator_url: Optional[str],
    payload: dict,
) -> None:
    now = datetime.now(timezone.utc)
    resolved_at = ends_at or now if alert_status == "resolved" else None
    cur.execute(
        """
        INSERT INTO operational_alert_events (
          receiver, group_key, status, triage_status, alertname, service, severity, fingerprint,
          labels, annotations, starts_at, ends_at, generator_url, payload,
          first_received_at, last_received_at, delivery_count, resolved_at
        )
        VALUES (%s, %s, %s, 'pending', %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s::jsonb, %s, %s, 1, %s)
        ON CONFLICT (fingerprint) DO UPDATE SET
          receiver = EXCLUDED.receiver,
          group_key = EXCLUDED.group_key,
          status = EXCLUDED.status,
          alertname = EXCLUDED.alertname,
          service = EXCLUDED.service,
          severity = EXCLUDED.severity,
          labels = EXCLUDED.labels,
          annotations = EXCLUDED.annotations,
          starts_at = COALESCE(operational_alert_events.starts_at, EXCLUDED.starts_at),
          ends_at = EXCLUDED.ends_at,
          generator_url = EXCLUDED.generator_url,
          payload = EXCLUDED.payload,
          last_received_at = EXCLUDED.last_received_at,
          delivery_count = operational_alert_events.delivery_count + 1,
          resolved_at = CASE
            WHEN EXCLUDED.status = 'resolved' THEN COALESCE(EXCLUDED.ends_at, EXCLUDED.last_received_at)
            ELSE NULL
          END,
          triage_status = CASE
            WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN 'pending'
            ELSE operational_alert_events.triage_status
          END,
          triaged_at = CASE
            WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN NULL
            ELSE operational_alert_events.triaged_at
          END,
          triaged_by = CASE
            WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN NULL
            ELSE operational_alert_events.triaged_by
          END,
          triage_note = CASE
            WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN NULL
            ELSE operational_alert_events.triage_note
          END
        """,
        (
            receiver,
            group_key,
            alert_status,
            alertname,
            service,
            severity,
            fingerprint,
            json.dumps(labels),
            json.dumps(annotations),
            starts_at,
            ends_at,
            generator_url,
            json.dumps(payload),
            now,
            now,
            resolved_at,
        ),
    )


def _build_monitoring_platform_snapshot(*, pool: ConnectionPool) -> dict:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (SELECT COUNT(*) FROM watchlists) AS watchlists_total,
                  (SELECT COUNT(*) FROM watchlists WHERE created_at >= NOW() - INTERVAL '24 hour') AS watchlists_created_last_24h,
                  (SELECT COUNT(*) FROM watchlist_items) AS watchlist_items_total,
                  (SELECT COUNT(*) FROM watchlist_items WHERE created_at >= NOW() - INTERVAL '24 hour') AS watchlist_items_created_last_24h,
                  (SELECT COUNT(*) FROM monitoring_alerts) AS alerts_total,
                  (SELECT COUNT(*) FROM monitoring_alerts WHERE created_at >= NOW() - INTERVAL '1 hour') AS alerts_last_hour,
                  (SELECT COUNT(*) FROM monitoring_alerts WHERE created_at >= NOW() - INTERVAL '24 hour') AS alerts_last_24h,
                  (SELECT COUNT(*) FROM monitoring_alerts WHERE severity = 'critical' AND created_at >= NOW() - INTERVAL '24 hour') AS critical_alerts_last_24h,
                  (SELECT COUNT(DISTINCT organization_id) FROM monitoring_alerts WHERE created_at >= NOW() - INTERVAL '24 hour') AS orgs_with_alerts_last_24h,
                  (SELECT COUNT(*) FROM monitoring_quotes WHERE used_at IS NULL AND expires_at > NOW()) AS open_quotes_total,
                  (SELECT COUNT(*) FROM monitoring_quotes WHERE used_at IS NULL AND expires_at <= NOW()) AS expired_quotes_total,
                  (SELECT COUNT(*) FROM operational_alert_events) AS operational_incidents_total,
                  (SELECT COUNT(*) FROM operational_alert_events WHERE status = 'firing') AS operational_incidents_firing_total,
                  (SELECT COUNT(*) FROM operational_alert_events WHERE status = 'resolved') AS operational_incidents_resolved_total,
                  (SELECT COUNT(*) FROM operational_alert_events WHERE triage_status = 'pending') AS operational_incidents_pending_triage_total,
                  (SELECT COUNT(*) FROM operational_alert_events WHERE triage_status = 'acknowledged') AS operational_incidents_acknowledged_total,
                  (SELECT COUNT(*) FROM operational_alert_events WHERE last_received_at >= NOW() - INTERVAL '1 hour') AS operational_deliveries_last_hour
                """
            )
            summary = cur.fetchone() or {}

            cur.execute(
                """
                SELECT severity, COUNT(*) AS total
                FROM monitoring_alerts
                WHERE created_at >= NOW() - INTERVAL '24 hour'
                GROUP BY severity
                """
            )
            severity_rows = cur.fetchall()

    severity_counts = {str(row["severity"]): int(row["total"]) for row in severity_rows}
    return {
        "catalog": {
            "operations_total": len(MONITORING_OPERATION_CATALOG),
        },
        "watchlists": {
            "total": int(summary.get("watchlists_total") or 0),
            "created_last_24h": int(summary.get("watchlists_created_last_24h") or 0),
        },
        "items": {
            "total": int(summary.get("watchlist_items_total") or 0),
            "created_last_24h": int(summary.get("watchlist_items_created_last_24h") or 0),
        },
        "alerts": {
            "total": int(summary.get("alerts_total") or 0),
            "last_hour": int(summary.get("alerts_last_hour") or 0),
            "last_24h": int(summary.get("alerts_last_24h") or 0),
            "critical_last_24h": int(summary.get("critical_alerts_last_24h") or 0),
            "orgs_with_alerts_last_24h": int(summary.get("orgs_with_alerts_last_24h") or 0),
            "severity_last_24h": severity_counts,
        },
        "quotes": {
            "open_total": int(summary.get("open_quotes_total") or 0),
            "expired_total": int(summary.get("expired_quotes_total") or 0),
        },
        "operational_incidents": {
            "total": int(summary.get("operational_incidents_total") or 0),
            "firing_total": int(summary.get("operational_incidents_firing_total") or 0),
            "resolved_total": int(summary.get("operational_incidents_resolved_total") or 0),
            "pending_triage_total": int(summary.get("operational_incidents_pending_triage_total") or 0),
            "acknowledged_total": int(summary.get("operational_incidents_acknowledged_total") or 0),
            "deliveries_last_hour": int(summary.get("operational_deliveries_last_hour") or 0),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_monitoring_platform_alerts(snapshot: dict) -> list[dict]:
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

    alerts_last_hour = snapshot["alerts"]["last_hour"]
    critical_alerts_last_24h = snapshot["alerts"]["critical_last_24h"]
    expired_quotes_total = snapshot["quotes"]["expired_total"]
    open_quotes_total = snapshot["quotes"]["open_total"]

    append_alert(
        code="monitoring_alert_spike",
        severity="warning",
        status="open" if alerts_last_hour >= settings.monitoring_alerts_last_hour_warn_threshold else "closed",
        metric="alerts.last_hour",
        value=float(alerts_last_hour),
        threshold=float(settings.monitoring_alerts_last_hour_warn_threshold),
        title="Pico recente de alertas",
        message="O volume de alertas emitidos na ultima hora excedeu o limiar operacional.",
        recommended_action="Revisar watchlists sensiveis, chains afetadas e possiveis eventos anormais.",
    )
    append_alert(
        code="monitoring_critical_alert_volume",
        severity="critical",
        status="open"
        if critical_alerts_last_24h >= settings.monitoring_critical_alerts_last_24h_critical_threshold
        else "closed",
        metric="alerts.critical_last_24h",
        value=float(critical_alerts_last_24h),
        threshold=float(settings.monitoring_critical_alerts_last_24h_critical_threshold),
        title="Alertas criticos recentes",
        message="Existem alertas criticos emitidos nas ultimas 24 horas.",
        recommended_action="Priorizar triagem operacional e correlacao com investigacoes ou compliance.",
    )
    append_alert(
        code="monitoring_expired_quotes_backlog",
        severity="warning",
        status="open" if expired_quotes_total >= settings.monitoring_expired_quotes_warn_threshold else "closed",
        metric="quotes.expired_total",
        value=float(expired_quotes_total),
        threshold=float(settings.monitoring_expired_quotes_warn_threshold),
        title="Quotes expirados acumulados",
        message="Existe acúmulo de quotes de monitoring expirados e nao consumidos.",
        recommended_action="Revisar UX/comercial do fluxo quote -> start e possivel limpeza operacional.",
    )
    append_alert(
        code="monitoring_open_quotes_backlog",
        severity="warning",
        status="open" if open_quotes_total >= settings.monitoring_open_quotes_warn_threshold else "closed",
        metric="quotes.open_total",
        value=float(open_quotes_total),
        threshold=float(settings.monitoring_open_quotes_warn_threshold),
        title="Quotes abertos acumulados",
        message="O volume de quotes ainda abertos ultrapassou o limiar operacional.",
        recommended_action="Verificar abandono de fluxo, expiração e aderencia do tier ao catalogo atual.",
    )
    return alerts


def _render_monitoring_platform_prometheus_metrics(snapshot: dict, alerts: list[dict]) -> str:
    alert_open_total = sum(1 for alert in alerts if alert["status"] == "open")
    critical_open_total = sum(1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical")
    lines = [
        "# HELP ontrack_monitoring_platform_catalog_operations_total Operacoes canonicas do catalogo de monitoring.",
        "# TYPE ontrack_monitoring_platform_catalog_operations_total gauge",
        f"ontrack_monitoring_platform_catalog_operations_total {snapshot['catalog']['operations_total']}",
        "# HELP ontrack_monitoring_platform_watchlists_total Watchlists totais.",
        "# TYPE ontrack_monitoring_platform_watchlists_total gauge",
        f"ontrack_monitoring_platform_watchlists_total {snapshot['watchlists']['total']}",
        "# HELP ontrack_monitoring_platform_watchlists_created_last_24h Watchlists criadas nas ultimas 24 horas.",
        "# TYPE ontrack_monitoring_platform_watchlists_created_last_24h gauge",
        f"ontrack_monitoring_platform_watchlists_created_last_24h {snapshot['watchlists']['created_last_24h']}",
        "# HELP ontrack_monitoring_platform_watchlist_items_total Itens totais nas watchlists.",
        "# TYPE ontrack_monitoring_platform_watchlist_items_total gauge",
        f"ontrack_monitoring_platform_watchlist_items_total {snapshot['items']['total']}",
        "# HELP ontrack_monitoring_platform_watchlist_items_created_last_24h Itens criados nas ultimas 24 horas.",
        "# TYPE ontrack_monitoring_platform_watchlist_items_created_last_24h gauge",
        f"ontrack_monitoring_platform_watchlist_items_created_last_24h {snapshot['items']['created_last_24h']}",
        "# HELP ontrack_monitoring_platform_alerts_total Alertas totais persistidos.",
        "# TYPE ontrack_monitoring_platform_alerts_total gauge",
        f"ontrack_monitoring_platform_alerts_total {snapshot['alerts']['total']}",
        "# HELP ontrack_monitoring_platform_alerts_last_hour Alertas emitidos na ultima hora.",
        "# TYPE ontrack_monitoring_platform_alerts_last_hour gauge",
        f"ontrack_monitoring_platform_alerts_last_hour {snapshot['alerts']['last_hour']}",
        "# HELP ontrack_monitoring_platform_alerts_last_24h Alertas emitidos nas ultimas 24 horas.",
        "# TYPE ontrack_monitoring_platform_alerts_last_24h gauge",
        f"ontrack_monitoring_platform_alerts_last_24h {snapshot['alerts']['last_24h']}",
        "# HELP ontrack_monitoring_platform_alerts_critical_last_24h Alertas criticos emitidos nas ultimas 24 horas.",
        "# TYPE ontrack_monitoring_platform_alerts_critical_last_24h gauge",
        f"ontrack_monitoring_platform_alerts_critical_last_24h {snapshot['alerts']['critical_last_24h']}",
        "# HELP ontrack_monitoring_platform_orgs_with_alerts_last_24h_total Organizacoes com ao menos um alerta nas ultimas 24 horas.",
        "# TYPE ontrack_monitoring_platform_orgs_with_alerts_last_24h_total gauge",
        f"ontrack_monitoring_platform_orgs_with_alerts_last_24h_total {snapshot['alerts']['orgs_with_alerts_last_24h']}",
        "# HELP ontrack_monitoring_platform_quotes_open_total Quotes em aberto e ainda validos.",
        "# TYPE ontrack_monitoring_platform_quotes_open_total gauge",
        f"ontrack_monitoring_platform_quotes_open_total {snapshot['quotes']['open_total']}",
        "# HELP ontrack_monitoring_platform_quotes_expired_unused_total Quotes expirados e nao consumidos.",
        "# TYPE ontrack_monitoring_platform_quotes_expired_unused_total gauge",
        f"ontrack_monitoring_platform_quotes_expired_unused_total {snapshot['quotes']['expired_total']}",
        "# HELP ontrack_monitoring_platform_operational_incidents_total Incidentes operacionais recebidos pelo Alertmanager.",
        "# TYPE ontrack_monitoring_platform_operational_incidents_total gauge",
        f"ontrack_monitoring_platform_operational_incidents_total {snapshot['operational_incidents']['total']}",
        "# HELP ontrack_monitoring_platform_operational_incidents_firing_total Incidentes operacionais em estado firing.",
        "# TYPE ontrack_monitoring_platform_operational_incidents_firing_total gauge",
        f"ontrack_monitoring_platform_operational_incidents_firing_total {snapshot['operational_incidents']['firing_total']}",
        "# HELP ontrack_monitoring_platform_operational_incidents_resolved_total Incidentes operacionais resolvidos.",
        "# TYPE ontrack_monitoring_platform_operational_incidents_resolved_total gauge",
        f"ontrack_monitoring_platform_operational_incidents_resolved_total {snapshot['operational_incidents']['resolved_total']}",
        "# HELP ontrack_monitoring_platform_operational_incidents_pending_triage_total Incidentes operacionais aguardando triagem manual.",
        "# TYPE ontrack_monitoring_platform_operational_incidents_pending_triage_total gauge",
        f"ontrack_monitoring_platform_operational_incidents_pending_triage_total {snapshot['operational_incidents']['pending_triage_total']}",
        "# HELP ontrack_monitoring_platform_operational_incidents_acknowledged_total Incidentes operacionais ja reconhecidos manualmente.",
        "# TYPE ontrack_monitoring_platform_operational_incidents_acknowledged_total gauge",
        f"ontrack_monitoring_platform_operational_incidents_acknowledged_total {snapshot['operational_incidents']['acknowledged_total']}",
        "# HELP ontrack_monitoring_platform_operational_incident_deliveries_last_hour Entregas de webhooks operacionais na ultima hora.",
        "# TYPE ontrack_monitoring_platform_operational_incident_deliveries_last_hour gauge",
        f"ontrack_monitoring_platform_operational_incident_deliveries_last_hour {snapshot['operational_incidents']['deliveries_last_hour']}",
        "# HELP ontrack_monitoring_platform_operational_alerts_open_total Total de alertas operacionais abertos.",
        "# TYPE ontrack_monitoring_platform_operational_alerts_open_total gauge",
        f"ontrack_monitoring_platform_operational_alerts_open_total {alert_open_total}",
        "# HELP ontrack_monitoring_platform_operational_alerts_critical_open_total Total de alertas operacionais criticos abertos.",
        "# TYPE ontrack_monitoring_platform_operational_alerts_critical_open_total gauge",
        f"ontrack_monitoring_platform_operational_alerts_critical_open_total {critical_open_total}",
    ]
    for severity in sorted(snapshot["alerts"]["severity_last_24h"].keys()):
        lines.extend(
            [
                "# HELP ontrack_monitoring_platform_alerts_severity_last_24h Alertas nas ultimas 24 horas por severidade.",
                "# TYPE ontrack_monitoring_platform_alerts_severity_last_24h gauge",
                (
                    "ontrack_monitoring_platform_alerts_severity_last_24h"
                    f'{{severity="{severity}"}} {snapshot["alerts"]["severity_last_24h"][severity]}'
                ),
            ]
        )
    lines.extend(
        [
            "# HELP ontrack_monitoring_platform_operational_alert_status Estado do alerta operacional avaliado pela aplicacao.",
            "# TYPE ontrack_monitoring_platform_operational_alert_status gauge",
        ]
    )
    for alert in alerts:
        alert_status = 1 if alert["status"] == "open" else 0
        lines.append(
            "ontrack_monitoring_platform_operational_alert_status"
            f'{{code="{alert["code"]}",severity="{alert["severity"]}",metric="{alert["metric"]}"}} {alert_status}'
        )
    return "\n".join(lines) + "\n"


class CreateWatchlistRequest(BaseModel):
    name: str
    priority: str = "normal"


class AddWatchlistItemRequest(BaseModel):
    address: str
    chain: str = "ethereum"


class TriggerAlertRequest(BaseModel):
    watchlist_id: UUID
    address: str
    chain: str = "ethereum"
    severity: str = "medium"
    title: str = "Movimentacao detectada"
    details: dict = {}


class AlertmanagerWebhookRequest(BaseModel):
    receiver: str
    status: str
    groupKey: Optional[str] = None
    commonLabels: dict = {}
    commonAnnotations: dict = {}
    alerts: list[dict]


class AcknowledgeOperationalAlertRequest(BaseModel):
    note: Optional[str] = None
    triaged_by: str = "admin_ui"


class AcknowledgeOperationalAlertsBatchRequest(BaseModel):
    note: Optional[str] = None
    triaged_by: str = "admin_ui"
    ids: list[UUID] = []
    status: Optional[str] = None
    triage_status: Optional[str] = None
    service: Optional[str] = None
    receiver: Optional[str] = None
    severity: Optional[str] = None


class ExportOperationalAlertsRequest(BaseModel):
    format: Literal["json", "csv"] = "json"
    scope: Literal["filtered", "selected"] = "filtered"
    ids: list[UUID] = []
    status: Optional[str] = None
    triage_status: Optional[str] = None
    service: Optional[str] = None
    receiver: Optional[str] = None
    severity: Optional[str] = None


class TriggerOperationalAlertRequest(BaseModel):
    alertname: str = "OntrackSyntheticOperationalAlert"
    service: str = "platform"
    receiver: str = "monitoring-webhook"
    severity: str = "warning"
    summary: str = "Incidente sintetico de teste"
    description: str = "Incidente sintetico criado para validar a triagem operacional."
    fingerprint: Optional[str] = None


class MonitoringCatalogItem(BaseModel):
    canonical: str
    label: str
    description: str
    cost_credits: float
    available: bool
    upgrade_required: Optional[str]
    min_plan: str
    aliases_accepted: list[str]
    deprecated_aliases: list[str]
    chains_supported: list[str]
    avg_duration_seconds: int
    output_format: str
    regulatory_reference: Optional[str]
    tags: list[str]


class MonitoringCatalogResponse(BaseModel):
    plan: str
    total: int
    generated_at: str
    operations: list[MonitoringCatalogItem]
    note_deprecated: str


class OperationalAlertFilterOptionsResponse(BaseModel):
    services: list[str]
    receivers: list[str]
    generated_at: str


def _format_operational_alert_export_filename(*, export_scope: str, export_format: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"operational-alerts-{export_scope}-{stamp}.{export_format}"


def _serialize_operational_alert_rows_csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "receiver",
            "status",
            "triage_status",
            "alertname",
            "service",
            "severity",
            "fingerprint",
            "delivery_count",
            "first_received_at",
            "last_received_at",
            "resolved_at",
            "triaged_at",
            "triaged_by",
            "triage_note",
            "summary",
            "description",
            "labels_json",
            "annotations_json",
            "work_item_id",
            "work_item_queue_status",
            "work_item_priority",
            "work_item_owner_user_id",
            "work_item_due_at",
            "work_item_sla_breached",
            "work_item_last_activity_at",
            "rca_domain",
            "rca_containment_status",
            "rca_incident_commander",
            "rca_affected_domains_json",
            "rca_impact_summary",
            "rca_suspected_root_cause",
            "rca_confirmed_root_cause",
            "rca_corrective_actions_json",
            "rca_evidence_refs_json",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["id"],
                row["receiver"],
                row["status"],
                row["triage_status"],
                row["alertname"],
                row["service"],
                row["severity"],
                row["fingerprint"],
                row["delivery_count"],
                row["first_received_at"],
                row["last_received_at"],
                row["resolved_at"],
                row["triaged_at"],
                row["triaged_by"],
                row["triage_note"],
                row.get("annotations", {}).get("summary"),
                row.get("annotations", {}).get("description"),
                json.dumps(row["labels"], separators=(",", ":"), ensure_ascii=False),
                json.dumps(row["annotations"], separators=(",", ":"), ensure_ascii=False),
                row.get("work_item_id"),
                row.get("work_item_queue_status"),
                row.get("work_item_priority"),
                row.get("work_item_owner_user_id"),
                row.get("work_item_due_at"),
                row.get("work_item_sla_breached"),
                row.get("work_item_last_activity_at"),
                row.get("rca_domain"),
                row.get("rca_containment_status"),
                row.get("rca_incident_commander"),
                json.dumps(row.get("rca_affected_domains") or [], separators=(",", ":"), ensure_ascii=False),
                row.get("rca_impact_summary"),
                row.get("rca_suspected_root_cause"),
                row.get("rca_confirmed_root_cause"),
                json.dumps(row.get("rca_corrective_actions") or [], separators=(",", ":"), ensure_ascii=False),
                json.dumps(row.get("rca_evidence_refs") or [], separators=(",", ":"), ensure_ascii=False),
            ]
        )
    return buffer.getvalue()


def _enrich_operational_alert_export_rows_with_work_items(
    *,
    cur,
    organization_id: str,
    rows: list[dict],
) -> list[dict]:
    if not rows:
        return rows

    resource_ids = [str(row["id"]) for row in rows]
    cur.execute(
        """
        SELECT
          resource_id,
          id AS work_item_id,
          queue_status,
          priority,
          owner_user_id,
          due_at,
          sla_breached,
          last_activity_at,
          metadata
        FROM regulatory_work_items
        WHERE organization_id = %s
          AND resource_type = 'operational_alert'
          AND resource_id = ANY(%s::uuid[])
        """,
        (organization_id, resource_ids),
    )
    work_item_rows = cur.fetchall()
    work_items_by_resource_id = {str(row["resource_id"]): row for row in work_item_rows}
    enriched_rows: list[dict] = []
    for row in rows:
        enriched_row = dict(row)
        work_item = work_items_by_resource_id.get(str(row["id"]))
        metadata = work_item.get("metadata") if work_item else None
        metadata = metadata if isinstance(metadata, dict) else {}
        affected_domains = metadata.get("affected_domains")
        corrective_actions = metadata.get("corrective_actions")
        evidence_refs = metadata.get("evidence_refs")

        enriched_row["work_item_id"] = str(work_item["work_item_id"]) if work_item and work_item.get("work_item_id") else None
        enriched_row["work_item_queue_status"] = work_item.get("queue_status") if work_item else None
        enriched_row["work_item_priority"] = work_item.get("priority") if work_item else None
        enriched_row["work_item_owner_user_id"] = (
            str(work_item["owner_user_id"]) if work_item and work_item.get("owner_user_id") else None
        )
        enriched_row["work_item_due_at"] = work_item["due_at"].isoformat() if work_item and work_item.get("due_at") else None
        enriched_row["work_item_sla_breached"] = bool(work_item.get("sla_breached")) if work_item else None
        enriched_row["work_item_last_activity_at"] = (
            work_item["last_activity_at"].isoformat() if work_item and work_item.get("last_activity_at") else None
        )
        enriched_row["rca_domain"] = metadata.get("domain")
        enriched_row["rca_containment_status"] = metadata.get("containment_status")
        enriched_row["rca_incident_commander"] = metadata.get("incident_commander")
        enriched_row["rca_affected_domains"] = (
            [str(value) for value in affected_domains if isinstance(value, str)] if isinstance(affected_domains, list) else []
        )
        enriched_row["rca_impact_summary"] = metadata.get("impact_summary")
        enriched_row["rca_suspected_root_cause"] = metadata.get("suspected_root_cause")
        enriched_row["rca_confirmed_root_cause"] = metadata.get("confirmed_root_cause")
        enriched_row["rca_corrective_actions"] = (
            [str(value) for value in corrective_actions if isinstance(value, str)] if isinstance(corrective_actions, list) else []
        )
        enriched_row["rca_evidence_refs"] = (
            [str(value) for value in evidence_refs if isinstance(value, str)] if isinstance(evidence_refs, list) else []
        )
        enriched_rows.append(enriched_row)
    return enriched_rows


class EstimateMonitoringRequest(BaseModel):
    name: str
    priority: str = "normal"
    address: str
    chain: str = "ethereum"
    operation: str = "monitoring_30days"


class EstimateMonitoringResponse(BaseModel):
    quote_id: uuid.UUID
    expires_at: str
    operation_requested: str
    operation_canonical: str
    breakdown: list[dict]
    subtotal_credits: float
    plan_discount: float
    total_credits: float
    credits_available: float
    can_proceed: bool
    calculation_version: str
    pricing_table_hash: str
    plan: str
    chain: str
    warnings: list[dict]


class StartMonitoringRequest(BaseModel):
    quote_id: uuid.UUID
    confirmed: bool = False


class StartMonitoringResponse(BaseModel):
    case_id: uuid.UUID
    watchlist_id: uuid.UUID
    item_id: uuid.UUID
    status: str
    operation_requested: str
    operation_canonical: str
    credits_required: float
    billing_action: str
    plan: str
    chain: str
    warnings: list[dict]


class RequoteMonitoringResponse(BaseModel):
    status: str
    message: str
    original_quote: dict
    new_quote: dict
    action_required: str
    note: str


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/internal/metrics/prometheus")
async def internal_monitoring_prometheus_metrics(pool: ConnectionPool = Depends(get_pool)) -> Response:
    if not settings.monitoring_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    snapshot = _build_monitoring_platform_snapshot(pool=pool)
    alerts = _build_monitoring_platform_alerts(snapshot)
    return Response(
        content=_render_monitoring_platform_prometheus_metrics(snapshot, alerts),
        media_type="text/plain; version=0.0.4",
    )


@app.post("/internal/ops/alertmanager/webhook")
async def receive_alertmanager_webhook(
    body: AlertmanagerWebhookRequest,
    pool: ConnectionPool = Depends(get_pool),
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
) -> dict:
    _require_internal_bearer_token(authorization)
    received = 0
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for alert in body.alerts:
                alert_payload = alert if isinstance(alert, dict) else {"raw": alert}
                raw_labels = alert_payload.get("labels")
                raw_annotations = alert_payload.get("annotations")
                labels = raw_labels if isinstance(raw_labels, dict) else {}
                annotations = raw_annotations if isinstance(raw_annotations, dict) else {}
                alert_status = str(alert_payload.get("status") or body.status or "firing")
                alertname = str(labels.get("alertname") or body.commonLabels.get("alertname") or "unknown_alert")
                service = labels.get("service") or body.commonLabels.get("service")
                severity = labels.get("severity") or body.commonLabels.get("severity")
                fingerprint = str(alert_payload.get("fingerprint") or f"{alertname}:{service}:{severity}")
                _persist_operational_alert_event(
                    cur,
                    receiver=body.receiver,
                    group_key=body.groupKey,
                    alert_status=alert_status,
                    alertname=alertname,
                    service=str(service) if service else None,
                    severity=str(severity) if severity else None,
                    fingerprint=fingerprint,
                    labels=labels,
                    annotations=annotations,
                    starts_at=_parse_optional_timestamp(alert_payload.get("startsAt")),
                    ends_at=_parse_optional_timestamp(alert_payload.get("endsAt")),
                    generator_url=alert_payload.get("generatorURL"),
                    payload=alert_payload,
                )
                received += 1
        conn.commit()
    return {"status": "accepted", "received": received}


@app.get("/api/v1/monitoring/admin/operational-alerts")
async def list_operational_alerts(
    status: Optional[str] = Query(default=None),
    triage_status: Optional[str] = Query(default=None),
    service: Optional[str] = Query(default=None),
    receiver: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="monitoring_read_role_required",
        resource_type="operational_alerts",
        resource_id=None,
        endpoint="/api/v1/monitoring/admin/operational-alerts",
        method="GET",
    )
    cursor_values: tuple[datetime, UUID] | None = _decode_operational_alert_cursor(cursor) if cursor else None
    with pool.connection() as conn:
        with conn.cursor() as cur:
            filters_query = """
                FROM operational_alert_events
                WHERE 1 = 1
            """
            filter_params: list = []
            if status:
                filters_query += " AND status = %s"
                filter_params.append(status)
            if triage_status:
                filters_query += " AND triage_status = %s"
                filter_params.append(triage_status)
            if service:
                filters_query += " AND service = %s"
                filter_params.append(service)
            if receiver:
                filters_query += " AND receiver = %s"
                filter_params.append(receiver)
            if severity:
                filters_query += " AND severity = %s"
                filter_params.append(severity)
            cur.execute(f"SELECT COUNT(*) AS total_count {filters_query}", filter_params)
            total_count = int(cur.fetchone()["total_count"])
            query = f"""
                SELECT
                  id, receiver, status, alertname, service, severity, fingerprint,
                  triage_status, labels, annotations, first_received_at, last_received_at, delivery_count,
                  resolved_at, triaged_at, triaged_by, triage_note
                {filters_query}
            """
            params = list(filter_params)
            if cursor_values:
                query += " AND (last_received_at, id) < (%s, %s)"
                params.extend(cursor_values)
            query += " ORDER BY last_received_at DESC, id DESC LIMIT %s"
            params.append(limit + 1)
            cur.execute(query, params)
            rows = cur.fetchall()
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = None
    if has_more and page_rows:
        last_row = page_rows[-1]
        next_cursor = _encode_operational_alert_cursor(
            last_received_at=last_row["last_received_at"],
            event_id=last_row["id"],
        )
    return {
        "status_filter": status,
        "triage_status_filter": triage_status,
        "service_filter": service,
        "receiver_filter": receiver,
        "severity_filter": severity,
        "cursor": cursor,
        "limit": limit,
        "total_count": total_count,
        "count": len(page_rows),
        "has_more": has_more,
        "next_cursor": next_cursor,
        "data": page_rows,
    }


@app.get(
    "/api/v1/monitoring/admin/operational-alerts/filter-options",
    response_model=OperationalAlertFilterOptionsResponse,
)
async def get_operational_alert_filter_options(
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> OperationalAlertFilterOptionsResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="monitoring_read_role_required",
        resource_type="operational_alerts",
        resource_id=None,
        endpoint="/api/v1/monitoring/admin/operational-alerts/filter-options",
        method="GET",
    )
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT service
                FROM operational_alert_events
                WHERE service IS NOT NULL AND service <> ''
                ORDER BY service ASC
                """
            )
            service_rows = cur.fetchall()
            cur.execute(
                """
                SELECT DISTINCT receiver
                FROM operational_alert_events
                WHERE receiver IS NOT NULL AND receiver <> ''
                ORDER BY receiver ASC
                """
            )
            receiver_rows = cur.fetchall()
    return OperationalAlertFilterOptionsResponse(
        services=[str(row["service"]) for row in service_rows],
        receivers=[str(row["receiver"]) for row in receiver_rows],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/monitoring/admin/operational-alerts/export")
async def export_operational_alerts(
    body: ExportOperationalAlertsRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> Response:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN"},
        detail="admin_role_required",
        resource_type="operational_alerts",
        resource_id=None,
        endpoint="/api/v1/monitoring/admin/operational-alerts/export",
        method="POST",
    )
    if body.scope == "selected" and not body.ids:
        raise HTTPException(status_code=422, detail="selected_operational_alert_ids_required")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id,
                       receiver,
                       status,
                       triage_status,
                       alertname,
                       service,
                       severity,
                       fingerprint,
                       labels,
                       annotations,
                       first_received_at,
                       last_received_at,
                       delivery_count,
                       resolved_at,
                       triaged_at,
                       triaged_by,
                       triage_note
                FROM operational_alert_events
                WHERE 1=1
            """
            params: list = []
            if body.scope == "selected":
                query += " AND id = ANY(%s::uuid[])"
                params.append([str(event_id) for event_id in body.ids])
            if body.status:
                query += " AND status = %s"
                params.append(body.status)
            if body.triage_status:
                query += " AND triage_status = %s"
                params.append(body.triage_status)
            if body.service:
                query += " AND service = %s"
                params.append(body.service)
            if body.receiver:
                query += " AND receiver = %s"
                params.append(body.receiver)
            if body.severity:
                query += " AND severity = %s"
                params.append(body.severity)
            query += " ORDER BY last_received_at DESC, id DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            rows = _enrich_operational_alert_export_rows_with_work_items(
                cur=cur,
                organization_id=org_id,
                rows=rows,
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="operational_alerts_exported",
                resource_type="operational_alerts",
                resource_id=None,
                metadata={
                    "request_id": request_id,
                    "format": body.format,
                    "scope": body.scope,
                    "selected_count": len(body.ids),
                    "exported_count": len(rows),
                    "filters": {
                        "status": body.status,
                        "triage_status": body.triage_status,
                        "service": body.service,
                        "receiver": body.receiver,
                        "severity": body.severity,
                    },
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    filename = _format_operational_alert_export_filename(export_scope=body.scope, export_format=body.format)
    if body.format == "csv":
        return Response(
            content=_serialize_operational_alert_rows_csv(rows),
            media_type="text/csv; charset=utf-8",
            headers={"content-disposition": f'attachment; filename="{filename}"'},
        )

    payload = json.dumps(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "scope": body.scope,
            "format": body.format,
            "count": len(rows),
            "filters": {
                "status": body.status,
                "triage_status": body.triage_status,
                "service": body.service,
                "receiver": body.receiver,
                "severity": body.severity,
            },
            "selected_count": len(body.ids),
            "data": rows,
        },
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return Response(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/v1/monitoring/admin/operational-alerts/acknowledge-batch")
async def acknowledge_operational_alerts_batch(
    body: AcknowledgeOperationalAlertsBatchRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    triaged_by = effective_user_id or body.triaged_by
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN"},
        detail="admin_role_required",
        resource_type="operational_alerts",
        resource_id=None,
        endpoint="/api/v1/monitoring/admin/operational-alerts/acknowledge-batch",
        method="POST",
    )
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            query = """
                UPDATE operational_alert_events
                SET triage_status = 'acknowledged',
                    triaged_at = %s,
                    triaged_by = %s,
                    triage_note = %s
                WHERE triage_status = 'pending'
            """
            params: list = [now, triaged_by, body.note]
            if body.ids:
                query += " AND id = ANY(%s::uuid[])"
                params.append([str(event_id) for event_id in body.ids])
            if body.status:
                query += " AND status = %s"
                params.append(body.status)
            if body.triage_status:
                query += " AND triage_status = %s"
                params.append(body.triage_status)
            if body.service:
                query += " AND service = %s"
                params.append(body.service)
            if body.receiver:
                query += " AND receiver = %s"
                params.append(body.receiver)
            if body.severity:
                query += " AND severity = %s"
                params.append(body.severity)
            query += " RETURNING id"
            cur.execute(query, params)
            updated_count = len(cur.fetchall())
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="operational_alerts_acknowledged_batch",
                resource_type="operational_alerts",
                resource_id=None,
                metadata={
                    "request_id": request_id,
                    "updated_count": updated_count,
                    "selected_count": len(body.ids),
                    "triaged_by": triaged_by,
                    "requested_triaged_by": body.triaged_by,
                    "filters": {
                        "status": body.status,
                        "triage_status": body.triage_status,
                        "service": body.service,
                        "receiver": body.receiver,
                        "severity": body.severity,
                    },
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return {
        "updated_count": updated_count,
        "selected_count": len(body.ids),
        "status_filter": body.status,
        "triage_status_filter": body.triage_status,
        "service_filter": body.service,
        "receiver_filter": body.receiver,
        "severity_filter": body.severity,
        "triage_status": "acknowledged",
    }


@app.post("/api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge")
async def acknowledge_operational_alert(
    event_id: UUID,
    body: AcknowledgeOperationalAlertRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    triaged_by = effective_user_id or body.triaged_by
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles={"ADMIN"},
        detail="admin_role_required",
        resource_type="operational_alerts",
        resource_id=str(event_id),
        endpoint="/api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge",
        method="POST",
    )
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE operational_alert_events
                SET triage_status = 'acknowledged',
                    triaged_at = %s,
                    triaged_by = %s,
                    triage_note = %s
                WHERE id = %s
                RETURNING id, status, triage_status, triaged_at, triaged_by, triage_note
                """,
                (now, triaged_by, body.note, event_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="operational_alert_not_found")
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="operational_alert_acknowledged",
                resource_type="operational_alerts",
                resource_id=str(event_id),
                metadata={
                    "request_id": request_id,
                    "triaged_by": triaged_by,
                    "requested_triaged_by": body.triaged_by,
                    "note": body.note,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return row


@app.post("/api/v1/monitoring/test/trigger-operational-alert")
async def trigger_operational_alert(
    body: TriggerOperationalAlertRequest,
    pool: ConnectionPool = Depends(get_pool),
) -> dict:
    if not settings.enable_test_endpoints:
        raise HTTPException(status_code=404, detail="not_found")

    fingerprint = body.fingerprint or f"synthetic:{body.alertname}:{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            _persist_operational_alert_event(
                cur,
                receiver=body.receiver,
                group_key=f"synthetic:{body.service}",
                alert_status="firing",
                alertname=body.alertname,
                service=body.service,
                severity=body.severity,
                fingerprint=fingerprint,
                labels={
                    "alertname": body.alertname,
                    "service": body.service,
                    "severity": body.severity,
                    "source": "synthetic_test",
                },
                annotations={
                    "summary": body.summary,
                    "description": body.description,
                },
                starts_at=now,
                ends_at=None,
                generator_url="synthetic://monitoring-api/test-trigger",
                payload={
                    "status": "firing",
                    "labels": {
                        "alertname": body.alertname,
                        "service": body.service,
                        "severity": body.severity,
                        "source": "synthetic_test",
                    },
                    "annotations": {
                        "summary": body.summary,
                        "description": body.description,
                    },
                    "startsAt": now.isoformat(),
                    "fingerprint": fingerprint,
                    "generatorURL": "synthetic://monitoring-api/test-trigger",
                },
            )
        conn.commit()
    return {"status": "created", "fingerprint": fingerprint}


@app.get("/api/v1/monitoring/operations", response_model=MonitoringCatalogResponse)
async def get_monitoring_catalog(
    include_deprecated: bool = Query(default=False),
    include_unavailable: bool = Query(default=False),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> MonitoringCatalogResponse:
    plan = normalize_plan(x_plan or "professional")
    catalog = [
        _build_operation_detail(canonical, plan, include_deprecated)
        for canonical in MONITORING_OPERATION_CATALOG.keys()
    ]
    if not include_unavailable:
        catalog = [item for item in catalog if item["available"]]
    return MonitoringCatalogResponse(
        plan=plan,
        total=len(catalog),
        generated_at=datetime.now(timezone.utc).isoformat(),
        operations=[MonitoringCatalogItem(**item) for item in catalog],
        note_deprecated=(
            "aliases_accepted sao aceitos para compatibilidade retroativa. "
            "deprecated_aliases serao removidos em v2 (Jan/2027). Migre para os canonicos."
        ),
    )


@app.get("/api/v1/monitoring/operations/{operation_identifier}", response_model=MonitoringCatalogItem)
async def get_monitoring_operation_detail(
    operation_identifier: str,
    include_deprecated: bool = Query(default=True),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> MonitoringCatalogItem:
    plan = normalize_plan(x_plan or "professional")
    canonical, _ = _resolve_operation(operation_identifier)
    return MonitoringCatalogItem(**_build_operation_detail(canonical, plan, include_deprecated))


@app.post("/api/v1/monitoring/estimate", response_model=EstimateMonitoringResponse)
async def estimate_monitoring(
    body: EstimateMonitoringRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> EstimateMonitoringResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    plan = normalize_plan(x_plan or "professional")
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_operational_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_quote",
        resource_id=None,
        endpoint="/api/v1/monitoring/estimate",
        method="POST",
    )
    chain = _validate_chain(body.chain)
    quote_payload = _build_monitoring_quote_payload(
        watchlist_name=body.name,
        priority=body.priority,
        address=body.address,
        chain=chain,
        operation_requested=body.operation,
        plan=plan,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("SELECT credits_available FROM organizations WHERE id = %s", (org_id,))
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")
            available = float(org["credits_available"])
            _persist_monitoring_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=quote_payload)
        conn.commit()
    return EstimateMonitoringResponse(
        quote_id=quote_payload["quote_id"],
        expires_at=quote_payload["expires_at"].isoformat(),
        operation_requested=quote_payload["operation_requested"],
        operation_canonical=quote_payload["operation_canonical"],
        breakdown=quote_payload["breakdown"],
        subtotal_credits=quote_payload["subtotal_credits"],
        plan_discount=quote_payload["plan_discount"],
        total_credits=quote_payload["total_credits"],
        credits_available=available,
        can_proceed=available >= quote_payload["total_credits"],
        calculation_version=quote_payload["calculation_version"],
        pricing_table_hash=quote_payload["pricing_table_hash"],
        plan=plan,
        chain=chain,
        warnings=quote_payload["warnings"],
    )


@app.post("/api/v1/monitoring/watchlists")
async def create_watchlist(
    body: CreateWatchlistRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_operational_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_watchlist",
        resource_id=None,
        endpoint="/api/v1/monitoring/watchlists",
        method="POST",
    )
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO watchlists (organization_id, name, priority, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (org_id, body.name, body.priority, now),
            )
            row = cur.fetchone()
        conn.commit()
    return {"watchlist_id": str(row["id"]), "status": "created"}


@app.get("/api/v1/monitoring/watchlists")
async def list_watchlists(
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_core_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_watchlist",
        resource_id=None,
        endpoint="/api/v1/monitoring/watchlists",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, priority, created_at FROM watchlists ORDER BY created_at DESC")
            rows = cur.fetchall()
    return {"data": rows}


@app.post("/api/v1/monitoring/start", response_model=StartMonitoringResponse)
async def start_monitoring(
    body: StartMonitoringRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> StartMonitoringResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_operational_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_case",
        resource_id=None,
        endpoint="/api/v1/monitoring/start",
        method="POST",
    )
    if not body.confirmed:
        raise HTTPException(status_code=412, detail="quote_confirmation_required")
    plan = normalize_plan(x_plan or "professional")
    now = datetime.now(timezone.utc)
    warnings: list[dict] = []

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM monitoring_quotes WHERE id = %s AND organization_id = %s",
                (body.quote_id, org_id),
            )
            quote_row = cur.fetchone()
            if not quote_row:
                raise HTTPException(status_code=404, detail={"error": "quote_not_found"})
            if quote_row["used_at"] is not None:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "quote_already_used",
                        "case_id": str(quote_row["used_for_case_id"]) if quote_row["used_for_case_id"] else None,
                    },
                )
            if quote_row["expires_at"] <= now:
                raise HTTPException(status_code=410, detail={"error": "quote_expired", "ttl_minutes": QUOTE_TTL_MINUTES})

            quote_plan = normalize_plan(str(quote_row["plan_snapshot"]))
            estimated_cost = float(quote_row["total_credits"])
            if str(quote_row["operation_requested"]) != str(quote_row["operation_canonical"]):
                warnings.append(
                    {
                        "warning": "operation_alias_resolved",
                        "requested": str(quote_row["operation_requested"]),
                        "canonical": str(quote_row["operation_canonical"]),
                    }
                )
            if plan != quote_plan:
                if plan_rank(plan) < plan_rank(quote_plan):
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "plan_downgraded_since_quote",
                            "quote_plan": quote_plan,
                            "current_plan": plan,
                            "operation": str(quote_row["operation_canonical"]),
                        },
                    )
                new_quote_payload = _build_monitoring_quote_payload(
                    watchlist_name=str(quote_row["watchlist_name"]),
                    priority=str(quote_row["priority"]),
                    address=str(quote_row["target_address"]),
                    chain=str(quote_row["chain"]),
                    operation_requested=str(quote_row["operation_requested"]),
                    plan=plan,
                )
                _persist_monitoring_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=new_quote_payload)
                conn.commit()
                return JSONResponse(
                    status_code=202,
                    content=RequoteMonitoringResponse(
                        status="requote_required",
                        message=f"Seu plano foi atualizado para {plan.upper()} desde a emissao do quote.",
                        original_quote={
                            "quote_id": str(quote_row["id"]),
                            "plan_snapshot": quote_plan,
                            "operation_requested": str(quote_row["operation_requested"]),
                            "operation_canonical": str(quote_row["operation_canonical"]),
                            "total_credits": estimated_cost,
                            "expires_at": quote_row["expires_at"].isoformat(),
                        },
                        new_quote={
                            "quote_id": str(new_quote_payload["quote_id"]),
                            "plan_snapshot": new_quote_payload["plan"],
                            "operation_requested": new_quote_payload["operation_requested"],
                            "operation_canonical": new_quote_payload["operation_canonical"],
                            "total_credits": new_quote_payload["total_credits"],
                            "expires_at": new_quote_payload["expires_at"].isoformat(),
                        },
                        action_required="Confirme o novo quote via POST /api/v1/monitoring/start",
                        note="O preco pode ter mudado conforme a tabela do novo plano.",
                    ).model_dump(),
                )
            if not _is_operation_available(str(quote_row["operation_canonical"]), plan):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "operation_not_available_on_plan",
                        "operation": str(quote_row["operation_canonical"]),
                        "required_plan": _required_plan_for_operation(str(quote_row["operation_canonical"])),
                        "current_plan": plan,
                    },
                )
            cur.execute("SELECT id, credits_available, credits_reserved FROM organizations WHERE id = %s", (org_id,))
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")
            if float(org["credits_available"]) < estimated_cost:
                raise HTTPException(status_code=402, detail={"error": "insufficient_credits"})
            new_available = round(float(org["credits_available"]) - estimated_cost, 4)
            new_reserved = round(float(org["credits_reserved"]) + estimated_cost, 4)
            cur.execute(
                "UPDATE organizations SET credits_available = %s, credits_reserved = %s, updated_at = NOW() WHERE id = %s",
                (new_available, new_reserved, org_id),
            )
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            cur.execute(
                """
                INSERT INTO cases (
                  organization_id, user_id, title, case_type, status, target_address, target_chain,
                  context_narrative, credits_estimated, created_at, metadata
                )
                VALUES (%s, %s, %s, %s, 'queued', %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    org_id,
                    persisted_user_id,
                    f"Monitoring {quote_row['operation_canonical']} {quote_row['target_address']}",
                    "monitoring",
                    quote_row["target_address"],
                    quote_row["chain"],
                    None,
                    estimated_cost,
                    now,
                    json.dumps(
                        {
                            "quote_id": str(body.quote_id),
                            "operation_requested": str(quote_row["operation_requested"]),
                            "operation_canonical": str(quote_row["operation_canonical"]),
                            "external_user_id": (
                                external_actor_user_id
                                if external_actor_user_id
                                else (effective_user_id if effective_user_id and not persisted_user_id else None)
                            ),
                        }
                    ),
                ),
            )
            case_row = cur.fetchone()
            cur.execute(
                """
                INSERT INTO watchlists (organization_id, name, priority, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (org_id, quote_row["watchlist_name"], quote_row["priority"], now),
            )
            watchlist_row = cur.fetchone()
            cur.execute(
                """
                INSERT INTO watchlist_items (watchlist_id, address, chain, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (watchlist_row["id"], quote_row["target_address"], quote_row["chain"], now),
            )
            item_row = cur.fetchone()
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="case_started",
                resource_type="case",
                resource_id=str(case_row["id"]) if case_row else None,
                metadata={
                    "request_id": request_id,
                    "case_type": "monitoring",
                    "status": "queued",
                    "credits_estimated": estimated_cost,
                    "quote_id": str(body.quote_id),
                    "operation_requested": str(quote_row["operation_requested"]),
                    "operation_canonical": str(quote_row["operation_canonical"]),
                    "watchlist_id": str(watchlist_row["id"]) if watchlist_row else None,
                    "external_user_id": external_actor_user_id,
                },
            )
            _record_credit_ledger(
                cur,
                org_id=org_id,
                case_id=str(case_row["id"]),
                amount=estimated_cost,
                balance_after=new_available,
                metadata={
                    "request_id": request_id,
                    "quote_id": str(body.quote_id),
                    "watchlist_id": str(watchlist_row["id"]),
                    "operation_canonical": str(quote_row["operation_canonical"]),
                    "chain": str(quote_row["chain"]),
                },
            )
            cur.execute(
                "UPDATE monitoring_quotes SET used_at = NOW(), used_for_case_id = %s WHERE id = %s",
                (case_row["id"], body.quote_id),
            )
        conn.commit()
    return StartMonitoringResponse(
        case_id=case_row["id"],
        watchlist_id=watchlist_row["id"],
        item_id=item_row["id"],
        status="queued",
        operation_requested=str(quote_row["operation_requested"]),
        operation_canonical=str(quote_row["operation_canonical"]),
        credits_required=estimated_cost,
        billing_action="PRE_HOLD",
        plan=plan,
        chain=str(quote_row["chain"]),
        warnings=warnings,
    )


@app.post("/api/v1/monitoring/watchlists/{watchlist_id}/items")
async def add_watchlist_item(
    watchlist_id: UUID,
    body: AddWatchlistItemRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_operational_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_watchlist_item",
        resource_id=str(watchlist_id),
        endpoint="/api/v1/monitoring/watchlists/{watchlist_id}/items",
        method="POST",
    )
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM watchlists WHERE id = %s", (watchlist_id,))
            wl = cur.fetchone()
            if not wl:
                raise HTTPException(status_code=404, detail="watchlist_not_found")

            cur.execute(
                """
                INSERT INTO watchlist_items (watchlist_id, address, chain, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (watchlist_id, body.address, _validate_chain(body.chain), now),
            )
            row = cur.fetchone()
        conn.commit()

    return {"item_id": str(row["id"]), "status": "created"}


@app.get("/api/v1/monitoring/watchlists/{watchlist_id}/items")
async def list_watchlist_items(
    watchlist_id: UUID,
    limit: int = Query(default=20, ge=1, le=200),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_core_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_watchlist_item",
        resource_id=str(watchlist_id),
        endpoint="/api/v1/monitoring/watchlists/{watchlist_id}/items",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM watchlists
                WHERE id = %s
                """,
                (watchlist_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="watchlist_not_found")

            cur.execute(
                """
                SELECT id, watchlist_id, address, chain, created_at
                FROM watchlist_items
                WHERE watchlist_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (watchlist_id, limit),
            )
            rows = cur.fetchall()

    return {"watchlist_id": str(watchlist_id), "data": rows, "limit": limit}


@app.get("/api/v1/monitoring/alerts")
async def list_alerts(
    priority: Optional[str] = Query(default=None),
    watchlist_id: Optional[UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_monitoring_core_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_type="monitoring_alert",
        resource_id=str(watchlist_id) if watchlist_id else None,
        endpoint="/api/v1/monitoring/alerts",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            query = """
                SELECT id, watchlist_id, address, chain, severity, title, details, created_at
                FROM monitoring_alerts
                WHERE organization_id = %s
            """
            params: list = [org_id]
            if priority:
                query += " AND severity = %s"
                params.append(priority)
            if watchlist_id:
                query += " AND watchlist_id = %s"
                params.append(watchlist_id)
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(query, params)
            rows = cur.fetchall()
    return {"priority": priority, "data": rows}


@app.post("/api/v1/monitoring/test/trigger-alert")
async def trigger_alert(
    body: TriggerAlertRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    if not settings.enable_test_endpoints:
        raise HTTPException(status_code=404, detail="not_found")
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_test_trigger_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=str(body.watchlist_id),
        endpoint="/api/v1/monitoring/test/trigger-alert",
        method="POST",
    )
    now = datetime.now(timezone.utc)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM watchlists WHERE id = %s", (body.watchlist_id,))
            wl = cur.fetchone()
            if not wl:
                raise HTTPException(status_code=404, detail="watchlist_not_found")
            cur.execute(
                """
                INSERT INTO monitoring_alerts (
                  organization_id, watchlist_id, address, chain, severity, title, details, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                RETURNING id
                """,
                (
                    org_id,
                    body.watchlist_id,
                    body.address,
                    _validate_chain(body.chain),
                    body.severity,
                    body.title,
                    json.dumps(body.details),
                    now,
                ),
            )
            row = cur.fetchone()
        conn.commit()
    return {"alert_id": str(row["id"]), "status": "created"}
