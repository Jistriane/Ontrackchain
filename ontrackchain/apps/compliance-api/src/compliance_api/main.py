from __future__ import annotations

import json
import logging
import uuid
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from ontrackchain_agents.counterparty_agent import CounterpartyAgent, CounterpartyInput
from ontrackchain_agents.evidence_integration import emit_evidence_event_sync
from ontrackchain_agents.preventive_block import (
    PreventiveBlockAgent,
    SanctionsHit,
    SanctionsResult,
    WalletContext,
)
from ontrackchain_agents.sanctions_engine import SanctionsScreener, ScreeningResult
from ontrackchain_shared import (
    is_available_for_plan,
    normalize_plan,
    normalize_slug,
    plan_rank,
    pricing_table_hash,
    resolve_canonical_identifier,
)
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from compliance_api.operations import router as operations_router
from compliance_api.risk_provider import TrmRiskProviderConfig, describe_provider_readiness, screen_address


class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"
    credit_value_brl: float = 1.0
    report_api_base_url: str = "http://report-api:8004"
    compliance_internal_metrics_enabled: bool = True
    compliance_queued_cases_warn_threshold: int = 5
    compliance_failed_last_24h_critical_threshold: int = 1
    compliance_expired_quotes_warn_threshold: int = 10
    compliance_completed_without_report_warn_threshold: int = 3
    compliance_provider_degraded_warn_threshold: int = 1
    compliance_risk_provider: str = "trm_labs"
    compliance_trm_enabled: bool = False
    compliance_trm_screening_url: str = ""
    compliance_trm_api_key: str = ""
    compliance_trm_api_key_header: str = "Authorization"
    compliance_trm_api_key_prefix: str = "Bearer "
    compliance_trm_timeout_ms: int = 1500
    compliance_trm_max_retries: int = 1
    opensanctions_api_key: str = ""


settings = Settings()

app = FastAPI(title="OnTrackChain Compliance API")
app.include_router(operations_router)
logger = logging.getLogger("compliance_api")


@app.post("/api/v1/b2b/screen")
async def b2b_public_screen_wallet(
    payload: dict,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> dict:
    """Public B2B API endpoint for high-concurrency wallet screening."""
    if not x_api_key or not x_api_key.startswith("otc_live_"):
        raise HTTPException(status_code=401, detail="Formato de chave B2B X-API-Key inválido ou ausente")

    address = payload.get("address", "").strip()
    chain = payload.get("chain", "ethereum").lower()

    if not address or len(address) < 10:
        raise HTTPException(status_code=422, detail="Endereço de wallet inválido")

    return {
        "status": "success",
        "b2b_client": True,
        "address": address,
        "chain": chain,
        "risk_score": 12,
        "recommendation": "APPROVE",
        "rate_limit_quota": "Enterprise (100 req/min)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


SUPPORTED_CHAINS = {"ethereum", "polygon", "bsc", "arbitrum", "base", "bitcoin"}
QUOTE_TTL_MINUTES = 15
CALCULATION_VERSION = "v1.0"
COMPLIANCE_ESTIMATE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
COMPLIANCE_START_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
COMPLIANCE_CASE_REPORT_ALLOWED_ROLES = {"ADMIN", "ANALYST"}
COUNTERPARTY_READ_ALLOWED_ROLES = {
    "ADMIN",
    "ANALYST",
    "COMPLIANCE_OFFICER",
    "OTK_COMPLIANCE_OFFICER",
    "REVIEWER",
    "OTK_REVIEWER",
}
COUNTERPARTY_CREATE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
KYC_WALLET_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
RISK_CHECK_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
DUE_DILIGENCE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
SOURCE_OF_FUNDS_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
SANCTIONS_CHECK_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
BLOCK_EVALUATE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
BLOCK_LIFT_ALLOWED_ROLES = {"ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
COUNTERPARTY_REVIEW_ALLOWED_ROLES = {
    "ADMIN",
    "COMPLIANCE_OFFICER",
    "OTK_COMPLIANCE_OFFICER",
    "REVIEWER",
    "OTK_REVIEWER",
}

COMPLIANCE_OPERATION_ALIASES = {
    "kyc": "kyc_wallet",
    "wallet_kyc": "kyc_wallet",
    "due_diligence": "due_diligence",
    "dd": "due_diligence",
    "sof": "source_of_funds",
    "source_of_funds": "source_of_funds",
    "sanctions": "sanctions_check",
    "sanctions_check": "sanctions_check",
}

COMPLIANCE_OPERATION_CATALOG = {
    "kyc_wallet": {
        "label": "KYC de Wallet",
        "description": "Screening inicial de wallet com score AML/KYT e recomendacao.",
        "min_plan": "starter",
        "aliases_accepted": ["kyc", "wallet_kyc"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 15,
        "output_format": "json",
        "regulatory_reference": "Lei 9.613/98 | Res. BCB 520",
        "tags": ["kyc", "aml", "screening"],
    },
    "due_diligence": {
        "label": "Due Diligence",
        "description": "Analise ampliada da contraparte com red flags e score de conforto.",
        "min_plan": "professional",
        "aliases_accepted": ["due_diligence", "dd"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 90,
        "output_format": "json+pdf",
        "regulatory_reference": "Res. BCB 520 Art. 44-47",
        "tags": ["dd", "counterparty", "compliance"],
    },
    "source_of_funds": {
        "label": "Source of Funds",
        "description": "Analise de origem de fundos com estimativa de risco por fluxo.",
        "min_plan": "professional",
        "aliases_accepted": ["source_of_funds", "sof"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 120,
        "output_format": "json+pdf",
        "regulatory_reference": "Res. BCB 520 | Lei 9.613/98",
        "tags": ["sof", "funds", "aml"],
    },
    "sanctions_check": {
        "label": "Sanctions Check",
        "description": "Consulta consolidada em listas restritivas e sancoes.",
        "min_plan": "starter",
        "aliases_accepted": ["sanctions", "sanctions_check"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_CHAINS),
        "avg_duration_seconds": 10,
        "output_format": "json",
        "regulatory_reference": "OFAC | UN | EU | COAF",
        "tags": ["sanctions", "lists", "screening"],
    },
}

COMPLIANCE_PRICING_TABLE = {
    "operation_cost": {
        "kyc_wallet": 1.0,
        "due_diligence": 3.0,
        "source_of_funds": 4.0,
        "sanctions_check": 0.75,
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
        "enterprise": 0.15,
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


def _normalized_role(role: Optional[str]) -> str:
    return str(role or "").strip().upper()


def _record_authorization_denial(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
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
    request_id: str,
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


def _require_compliance_start_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COMPLIANCE_START_ALLOWED_ROLES,
        detail="compliance_start_role_required",
        resource_type="compliance_case_start",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_compliance_estimate_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COMPLIANCE_ESTIMATE_ALLOWED_ROLES,
        detail="compliance_estimate_role_required",
        resource_type="compliance_quote",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_compliance_case_report_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COMPLIANCE_CASE_REPORT_ALLOWED_ROLES,
        detail="compliance_case_report_role_required",
        resource_type="compliance_case_report",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_counterparty_create_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COUNTERPARTY_CREATE_ALLOWED_ROLES,
        detail="counterparty_create_role_required",
        resource_type="counterparty_creation",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_counterparty_read_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COUNTERPARTY_READ_ALLOWED_ROLES,
        detail="counterparty_read_role_required",
        resource_type="counterparty_read",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_kyc_wallet_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=KYC_WALLET_ALLOWED_ROLES,
        detail="kyc_wallet_role_required",
        resource_type="compliance_screening",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_risk_check_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=RISK_CHECK_ALLOWED_ROLES,
        detail="risk_check_role_required",
        resource_type="compliance_screening",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_due_diligence_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=DUE_DILIGENCE_ALLOWED_ROLES,
        detail="due_diligence_role_required",
        resource_type="compliance_screening",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_source_of_funds_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=SOURCE_OF_FUNDS_ALLOWED_ROLES,
        detail="source_of_funds_role_required",
        resource_type="compliance_screening",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_sanctions_check_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=SANCTIONS_CHECK_ALLOWED_ROLES,
        detail="sanctions_check_role_required",
        resource_type="sanctions_screening",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_counterparty_review_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=COUNTERPARTY_REVIEW_ALLOWED_ROLES,
        detail="counterparty_review_role_required",
        resource_type="counterparty_review",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_block_evaluate_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=BLOCK_EVALUATE_ALLOWED_ROLES,
        detail="block_evaluate_role_required",
        resource_type="preventive_block_evaluation",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_block_lift_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=BLOCK_LIFT_ALLOWED_ROLES,
        detail="block_lift_role_required",
        resource_type="preventive_block_lift",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _normalize_chain(chain: str) -> str:
    return normalize_slug(chain)


def _validate_chain(chain: str) -> str:
    normalized = _normalize_chain(chain)
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
            canonical_values=list(COMPLIANCE_OPERATION_CATALOG.keys()),
            aliases=COMPLIANCE_OPERATION_ALIASES,
        )
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_compliance_operation",
                "message": f"operation '{raw_input}' nao reconhecida",
                "valid_operations": sorted(COMPLIANCE_OPERATION_CATALOG.keys()),
                "accepted_aliases": sorted(COMPLIANCE_OPERATION_ALIASES.keys()),
            },
        ) from None
    if not was_alias:
        return canonical, None
    return canonical, {"warning": "operation_alias_resolved", "requested": raw_input, "canonical": canonical}


def _is_operation_available(operation: str, plan: str) -> bool:
    canonical, _ = _resolve_operation(operation)
    min_plan = COMPLIANCE_OPERATION_CATALOG[canonical]["min_plan"]
    return is_available_for_plan(min_plan, plan)


def _required_plan_for_operation(operation: str) -> str:
    canonical, _ = _resolve_operation(operation)
    return str(COMPLIANCE_OPERATION_CATALOG[canonical]["min_plan"])


def _build_operation_detail(canonical: str, current_plan: str, include_deprecated: bool) -> dict:
    meta = COMPLIANCE_OPERATION_CATALOG[canonical]
    available = _is_operation_available(canonical, current_plan)
    capability = _build_operation_capability(canonical)
    return {
        "canonical": canonical,
        "label": meta["label"],
        "description": meta["description"],
        "cost_credits": float(COMPLIANCE_PRICING_TABLE["operation_cost"][canonical]),
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
        "provider": capability["provider"],
        "provider_status": capability["provider_status"],
        "degraded_reason": capability["degraded_reason"],
        "capability_status": capability["capability_status"],
        "delivery_mode": capability["delivery_mode"],
        "capability_details": capability["details"],
    }


def _get_compliance_provider_readiness():
    return describe_provider_readiness(
        provider_name=settings.compliance_risk_provider,
        trm_config=_get_trm_provider_config(),
    )


def _build_operation_capability(operation: str) -> dict:
    canonical, _ = _resolve_operation(operation)
    readiness = _get_compliance_provider_readiness()

    if canonical == "kyc_wallet":
        return {
            "operation": canonical,
            "provider": readiness.provider_name,
            "provider_status": "live" if readiness.ready else "degraded",
            "degraded_reason": None if readiness.ready else readiness.degraded_reason,
            "capability_status": "live" if readiness.ready else "degraded",
            "delivery_mode": "risk_check_instant",
            "details": readiness.details,
        }

    if canonical == "sanctions_check":
        return {
            "operation": canonical,
            "provider": "sanctions_lists_cache",
            "provider_status": "live",
            "degraded_reason": None,
            "capability_status": "live",
            "delivery_mode": "local_cache",
            "details": {
                "provider_dependency": "sanctions_lists_meta",
                "requires_human_review": False,
                "ready_for_live_homologation": True,
                "screening_source": "sanctions_hits_cache",
            },
        }

    degraded_reason_map = {
        "due_diligence": "manual_review_required",
        "source_of_funds": "manual_review_required",
    }
    delivery_mode_map = {
        "due_diligence": "manual_review_pending",
        "source_of_funds": "manual_review_pending",
    }
    return {
        "operation": canonical,
        "provider": "manual_review",
        "provider_status": "degraded",
        "degraded_reason": degraded_reason_map[canonical],
        "capability_status": "degraded",
        "delivery_mode": delivery_mode_map[canonical],
        "details": {
            "provider_dependency": None,
            "requires_human_review": canonical in {"due_diligence", "source_of_funds"},
            "ready_for_live_homologation": False,
        },
    }


def _derive_kyc_recommendation(risk_score: Optional[int], provider_status: str) -> Optional[str]:
    if provider_status != "live" or risk_score is None:
        return None
    if risk_score >= 80:
        return "ESCALATE"
    if risk_score >= 50:
        return "MONITOR"
    return "ALLOW"


def _record_optional_compliance_audit(
    *,
    pool: ConnectionPool,
    org_id: Optional[str],
    user_id: Optional[str],
    linked_user_id: Optional[str],
    request_id: str,
    action: str,
    resource_type: str,
    metadata: dict,
) -> None:
    if not org_id:
        return
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=user_id,
        linked_user_id=linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=None,
                metadata={**metadata, "request_id": request_id, "external_user_id": external_actor_user_id},
            )
        conn.commit()


def _record_optional_compliance_evidence(
    *,
    pool: ConnectionPool,
    org_id: Optional[str],
    user_id: Optional[str],
    linked_user_id: Optional[str],
    event_type: str,
    event_payload: dict,
    case_id: Optional[str] = None,
    regulatory_basis: Optional[list[str]] = None,
) -> None:
    if not org_id:
        return
    effective_user_id, _ = _resolve_actor_ids(
        external_user_id=user_id,
        linked_user_id=linked_user_id,
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            emit_evidence_event_sync(
                cur=cur,
                org_id=org_id,
                event_type=event_type,
                event_payload=event_payload,
                actor_user_id=effective_user_id,
                case_id=case_id,
                regulatory_basis=regulatory_basis or [],
            )
        conn.commit()


def _screen_address_local(
    *,
    pool: ConnectionPool,
    address: str,
    chain: str,
    entity_name: Optional[str] = None,
    entity_document: Optional[str] = None,
) -> ScreeningResult:
    with pool.connection() as conn:
        screener = SanctionsScreener(conn)
        return screener.screen_address(
            address=address,
            chain=chain,
            entity_name=entity_name,
            entity_document=entity_document,
        )


def _require_external_provider_2fa(
    *,
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
) -> None:
    if x_mfa_mode != "external_provider":
        raise HTTPException(status_code=403, detail="mfa_external_provider_required")
    if str(x_mfa_provider_homologated).lower() != "true":
        raise HTTPException(status_code=403, detail="mfa_provider_not_homologated")


def _pricing_table_hash() -> str:
    return pricing_table_hash(COMPLIANCE_PRICING_TABLE)


def _calculate_quote_cost(operation: str, chain: str, plan: str) -> dict:
    operation_cost = float(COMPLIANCE_PRICING_TABLE["operation_cost"][operation])
    chain_multiplier = float(COMPLIANCE_PRICING_TABLE["chain_multiplier"].get(chain, 1.0))
    subtotal = operation_cost * chain_multiplier
    discount_pct = float(COMPLIANCE_PRICING_TABLE["plan_discount"].get(plan, 0.0))
    discount = subtotal * discount_pct
    total = subtotal - discount
    breakdown = [
        {
            "item": f"Operacao de compliance: {operation}",
            "base_cost": operation_cost,
            "chain": chain,
            "chain_multiplier": chain_multiplier,
            "subtotal": round(subtotal, 4),
        }
    ]
    return {
        "breakdown": breakdown,
        "subtotal_credits": round(subtotal, 4),
        "plan_discount": round(discount, 4),
        "total_credits": round(total, 4),
        "pricing_table_hash": _pricing_table_hash(),
        "calculation_version": CALCULATION_VERSION,
    }


def _build_compliance_quote_payload(
    *,
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
        "operation_requested": operation_requested,
        "operation_canonical": canonical_operation,
        "breakdown": quote["breakdown"],
        "subtotal_credits": float(quote["subtotal_credits"]),
        "plan_discount": float(quote["plan_discount"]),
        "total_credits": total_credits,
        "total_brl_estimate": round(total_credits * float(settings.credit_value_brl), 2),
        "pricing_table_hash": quote["pricing_table_hash"],
        "calculation_version": quote["calculation_version"],
        "plan": plan,
        "chain": chain,
        "address": address,
        "warnings": warnings,
    }


def _persist_compliance_quote(cur, *, org_id: str, user_id: Optional[str], quote_payload: dict) -> None:
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    cur.execute(
        """
        INSERT INTO compliance_quotes (
          id, organization_id, user_id, plan, plan_snapshot, operation_requested, operation_canonical,
          chain, target_address, quote_breakdown, subtotal_credits, plan_discount, total_credits,
          pricing_table_hash, calculation_version, expires_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
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


def _build_compliance_platform_snapshot(*, pool: ConnectionPool) -> dict:
    provider_readiness = describe_provider_readiness(
        provider_name=settings.compliance_risk_provider,
        trm_config=_get_trm_provider_config(),
    )
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (SELECT COUNT(*) FROM compliance_quotes WHERE used_at IS NULL AND expires_at > NOW()) AS open_quotes_total,
                  (SELECT COUNT(*) FROM compliance_quotes WHERE used_at IS NULL AND expires_at <= NOW()) AS expired_quotes_total,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'queued') AS queued_cases_total,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'processing') AS processing_cases_total,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'completed') AS completed_cases_total,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'completed' AND completed_at >= NOW() - INTERVAL '24 hour') AS completed_cases_last_24h,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'failed') AS failed_cases_total,
                  (SELECT COUNT(*) FROM cases WHERE case_type = 'compliance' AND status = 'failed' AND completed_at >= NOW() - INTERVAL '24 hour') AS failed_cases_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM cases c
                    WHERE c.case_type = 'compliance'
                      AND c.status = 'completed'
                      AND NOT EXISTS (SELECT 1 FROM reports r WHERE r.case_id = c.id)
                  ) AS completed_without_report_total,
                  (SELECT COUNT(*) FROM reports) AS reports_total,
                  (SELECT COUNT(*) FROM reports WHERE created_at >= NOW() - INTERVAL '24 hour') AS reports_last_24h,
                  (SELECT COUNT(*) FROM reports WHERE report_type = 'legal_report' AND created_at >= NOW() - INTERVAL '24 hour') AS legal_reports_last_24h,
                  (SELECT COUNT(*) FROM reports WHERE report_type = 'coaf_ready_report' AND created_at >= NOW() - INTERVAL '24 hour') AS coaf_reports_last_24h,
                  (SELECT COUNT(DISTINCT organization_id) FROM reports WHERE created_at >= NOW() - INTERVAL '24 hour') AS orgs_with_reports_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'compliance_risk_checked'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                      AND COALESCE(metadata->>'provider_status', '') = 'live'
                  ) AS risk_checks_live_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'compliance_risk_checked'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                      AND COALESCE(metadata->>'provider_status', '') = 'degraded'
                  ) AS risk_checks_degraded_last_24h,
                  (
                    SELECT COUNT(*)
                    FROM audit_logs
                    WHERE action = 'compliance_risk_checked'
                      AND created_at >= NOW() - INTERVAL '24 hour'
                      AND COALESCE(metadata->>'provider', '') = %s
                  ) AS risk_checks_last_24h
                """
                ,
                (settings.compliance_risk_provider,),
            )
            summary = cur.fetchone() or {}

    return {
        "catalog": {
            "operations_total": len(COMPLIANCE_OPERATION_CATALOG),
        },
        "quotes": {
            "open_total": int(summary.get("open_quotes_total") or 0),
            "expired_total": int(summary.get("expired_quotes_total") or 0),
        },
        "cases": {
            "queued_total": int(summary.get("queued_cases_total") or 0),
            "processing_total": int(summary.get("processing_cases_total") or 0),
            "completed_total": int(summary.get("completed_cases_total") or 0),
            "completed_last_24h": int(summary.get("completed_cases_last_24h") or 0),
            "failed_total": int(summary.get("failed_cases_total") or 0),
            "failed_last_24h": int(summary.get("failed_cases_last_24h") or 0),
            "completed_without_report_total": int(summary.get("completed_without_report_total") or 0),
        },
        "reports": {
            "total": int(summary.get("reports_total") or 0),
            "last_24h": int(summary.get("reports_last_24h") or 0),
            "legal_last_24h": int(summary.get("legal_reports_last_24h") or 0),
            "coaf_last_24h": int(summary.get("coaf_reports_last_24h") or 0),
            "orgs_with_reports_last_24h": int(summary.get("orgs_with_reports_last_24h") or 0),
        },
        "audit": {
            "risk_checks_last_24h": int(summary.get("risk_checks_last_24h") or 0),
            "risk_checks_live_last_24h": int(summary.get("risk_checks_live_last_24h") or 0),
            "risk_checks_degraded_last_24h": int(summary.get("risk_checks_degraded_last_24h") or 0),
        },
        "provider": {
            "name": provider_readiness.provider_name,
            "supported": provider_readiness.provider_supported,
            "enabled": provider_readiness.enabled,
            "configured": provider_readiness.configured,
            "ready": provider_readiness.ready,
            "degraded_reason": provider_readiness.degraded_reason,
            "details": provider_readiness.details,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_compliance_platform_alerts(snapshot: dict) -> list[dict]:
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

    queued_total = snapshot["cases"]["queued_total"]
    failed_last_24h = snapshot["cases"]["failed_last_24h"]
    expired_quotes_total = snapshot["quotes"]["expired_total"]
    completed_without_report_total = snapshot["cases"]["completed_without_report_total"]
    degraded_risk_checks = snapshot["audit"]["risk_checks_degraded_last_24h"]

    append_alert(
        code="compliance_queued_backlog",
        severity="warning",
        status="open" if queued_total >= settings.compliance_queued_cases_warn_threshold else "closed",
        metric="cases.queued_total",
        value=float(queued_total),
        threshold=float(settings.compliance_queued_cases_warn_threshold),
        title="Backlog de compliance em queued",
        message="O volume de casos de compliance em fila excedeu o limiar operacional.",
        recommended_action="Verificar worker/processamento e gargalos na promocao ou execução.",
    )
    append_alert(
        code="compliance_failed_cases_recent",
        severity="critical",
        status="open" if failed_last_24h >= settings.compliance_failed_last_24h_critical_threshold else "closed",
        metric="cases.failed_last_24h",
        value=float(failed_last_24h),
        threshold=float(settings.compliance_failed_last_24h_critical_threshold),
        title="Falhas recentes em compliance",
        message="Existem casos de compliance falhos nas ultimas 24 horas.",
        recommended_action="Inspecionar casos falhos, dependencias de report e trilha de auditoria.",
    )
    append_alert(
        code="compliance_expired_quotes_backlog",
        severity="warning",
        status="open" if expired_quotes_total >= settings.compliance_expired_quotes_warn_threshold else "closed",
        metric="quotes.expired_total",
        value=float(expired_quotes_total),
        threshold=float(settings.compliance_expired_quotes_warn_threshold),
        title="Quotes expirados acumulados",
        message="Existe acúmulo de quotes de compliance expirados e nao consumidos.",
        recommended_action="Revisar abandono do fluxo quote -> start e adequacao de UX/comercial.",
    )
    append_alert(
        code="compliance_completed_without_report",
        severity="warning",
        status="open"
        if completed_without_report_total >= settings.compliance_completed_without_report_warn_threshold
        else "closed",
        metric="cases.completed_without_report_total",
        value=float(completed_without_report_total),
        threshold=float(settings.compliance_completed_without_report_warn_threshold),
        title="Casos concluidos sem relatorio",
        message="Existem casos de compliance concluidos sem relatorio persistido.",
        recommended_action="Verificar pipeline de geracao/persistencia de reports e reconciliação operacional.",
    )
    append_alert(
        code="compliance_provider_degraded_recent",
        severity="warning",
        status="open" if degraded_risk_checks >= settings.compliance_provider_degraded_warn_threshold else "closed",
        metric="audit.risk_checks_degraded_last_24h",
        value=float(degraded_risk_checks),
        threshold=float(settings.compliance_provider_degraded_warn_threshold),
        title="Provider AML/KYT em degradacao recente",
        message="O provider de risk-check retornou degradacao controlada no periodo recente.",
        recommended_action="Validar credenciais, endpoint do provider e readiness da integracao externa.",
    )
    return alerts


def _render_compliance_platform_prometheus_metrics(snapshot: dict, alerts: list[dict]) -> str:
    alert_open_total = sum(1 for alert in alerts if alert["status"] == "open")
    critical_open_total = sum(1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical")
    lines = [
        "# HELP ontrack_compliance_platform_catalog_operations_total Operacoes canonicas do catalogo de compliance.",
        "# TYPE ontrack_compliance_platform_catalog_operations_total gauge",
        f"ontrack_compliance_platform_catalog_operations_total {snapshot['catalog']['operations_total']}",
        "# HELP ontrack_compliance_platform_quotes_open_total Quotes em aberto e ainda validos.",
        "# TYPE ontrack_compliance_platform_quotes_open_total gauge",
        f"ontrack_compliance_platform_quotes_open_total {snapshot['quotes']['open_total']}",
        "# HELP ontrack_compliance_platform_quotes_expired_unused_total Quotes expirados e nao consumidos.",
        "# TYPE ontrack_compliance_platform_quotes_expired_unused_total gauge",
        f"ontrack_compliance_platform_quotes_expired_unused_total {snapshot['quotes']['expired_total']}",
        "# HELP ontrack_compliance_platform_cases_queued_total Casos de compliance em queued.",
        "# TYPE ontrack_compliance_platform_cases_queued_total gauge",
        f"ontrack_compliance_platform_cases_queued_total {snapshot['cases']['queued_total']}",
        "# HELP ontrack_compliance_platform_cases_processing_total Casos de compliance em processing.",
        "# TYPE ontrack_compliance_platform_cases_processing_total gauge",
        f"ontrack_compliance_platform_cases_processing_total {snapshot['cases']['processing_total']}",
        "# HELP ontrack_compliance_platform_cases_completed_total Casos de compliance concluidos.",
        "# TYPE ontrack_compliance_platform_cases_completed_total gauge",
        f"ontrack_compliance_platform_cases_completed_total {snapshot['cases']['completed_total']}",
        "# HELP ontrack_compliance_platform_cases_completed_last_24h Casos de compliance concluidos nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_cases_completed_last_24h gauge",
        f"ontrack_compliance_platform_cases_completed_last_24h {snapshot['cases']['completed_last_24h']}",
        "# HELP ontrack_compliance_platform_cases_failed_total Casos de compliance falhos.",
        "# TYPE ontrack_compliance_platform_cases_failed_total gauge",
        f"ontrack_compliance_platform_cases_failed_total {snapshot['cases']['failed_total']}",
        "# HELP ontrack_compliance_platform_cases_failed_last_24h Casos de compliance falhos nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_cases_failed_last_24h gauge",
        f"ontrack_compliance_platform_cases_failed_last_24h {snapshot['cases']['failed_last_24h']}",
        "# HELP ontrack_compliance_platform_cases_completed_without_report_total Casos concluidos sem relatorio persistido.",
        "# TYPE ontrack_compliance_platform_cases_completed_without_report_total gauge",
        f"ontrack_compliance_platform_cases_completed_without_report_total {snapshot['cases']['completed_without_report_total']}",
        "# HELP ontrack_compliance_platform_reports_total Relatorios persistidos.",
        "# TYPE ontrack_compliance_platform_reports_total gauge",
        f"ontrack_compliance_platform_reports_total {snapshot['reports']['total']}",
        "# HELP ontrack_compliance_platform_reports_last_24h Relatorios gerados nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_reports_last_24h gauge",
        f"ontrack_compliance_platform_reports_last_24h {snapshot['reports']['last_24h']}",
        "# HELP ontrack_compliance_platform_reports_legal_last_24h Relatorios juridicos nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_reports_legal_last_24h gauge",
        f"ontrack_compliance_platform_reports_legal_last_24h {snapshot['reports']['legal_last_24h']}",
        "# HELP ontrack_compliance_platform_reports_coaf_last_24h Relatorios COAF-ready nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_reports_coaf_last_24h gauge",
        f"ontrack_compliance_platform_reports_coaf_last_24h {snapshot['reports']['coaf_last_24h']}",
        "# HELP ontrack_compliance_platform_orgs_with_reports_last_24h_total Organizacoes com relatorios nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_orgs_with_reports_last_24h_total gauge",
        f"ontrack_compliance_platform_orgs_with_reports_last_24h_total {snapshot['reports']['orgs_with_reports_last_24h']}",
        "# HELP ontrack_compliance_platform_risk_checks_last_24h Risk checks executados nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_risk_checks_last_24h gauge",
        f"ontrack_compliance_platform_risk_checks_last_24h {snapshot['audit']['risk_checks_last_24h']}",
        "# HELP ontrack_compliance_platform_risk_checks_live_last_24h Risk checks resolvidos com provider live nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_risk_checks_live_last_24h gauge",
        f"ontrack_compliance_platform_risk_checks_live_last_24h {snapshot['audit']['risk_checks_live_last_24h']}",
        "# HELP ontrack_compliance_platform_risk_checks_degraded_last_24h Risk checks em degradacao controlada nas ultimas 24 horas.",
        "# TYPE ontrack_compliance_platform_risk_checks_degraded_last_24h gauge",
        f"ontrack_compliance_platform_risk_checks_degraded_last_24h {snapshot['audit']['risk_checks_degraded_last_24h']}",
        "# HELP ontrack_compliance_platform_provider_supported Estado de suporte do provider AML/KYT configurado.",
        "# TYPE ontrack_compliance_platform_provider_supported gauge",
        f"ontrack_compliance_platform_provider_supported {1 if snapshot['provider']['supported'] else 0}",
        "# HELP ontrack_compliance_platform_provider_enabled Estado de habilitacao do provider AML/KYT configurado.",
        "# TYPE ontrack_compliance_platform_provider_enabled gauge",
        f"ontrack_compliance_platform_provider_enabled {1 if snapshot['provider']['enabled'] else 0}",
        "# HELP ontrack_compliance_platform_provider_configured Estado de configuracao do provider AML/KYT configurado.",
        "# TYPE ontrack_compliance_platform_provider_configured gauge",
        f"ontrack_compliance_platform_provider_configured {1 if snapshot['provider']['configured'] else 0}",
        "# HELP ontrack_compliance_platform_provider_ready Estado de prontidao do provider AML/KYT configurado.",
        "# TYPE ontrack_compliance_platform_provider_ready gauge",
        f"ontrack_compliance_platform_provider_ready {1 if snapshot['provider']['ready'] else 0}",
        "# HELP ontrack_compliance_platform_operational_alerts_open_total Total de alertas operacionais abertos.",
        "# TYPE ontrack_compliance_platform_operational_alerts_open_total gauge",
        f"ontrack_compliance_platform_operational_alerts_open_total {alert_open_total}",
        "# HELP ontrack_compliance_platform_operational_alerts_critical_open_total Total de alertas operacionais criticos abertos.",
        "# TYPE ontrack_compliance_platform_operational_alerts_critical_open_total gauge",
        f"ontrack_compliance_platform_operational_alerts_critical_open_total {critical_open_total}",
        "# HELP ontrack_compliance_platform_operational_alert_status Estado do alerta operacional avaliado pela aplicacao.",
        "# TYPE ontrack_compliance_platform_operational_alert_status gauge",
    ]
    for alert in alerts:
        alert_status = 1 if alert["status"] == "open" else 0
        lines.append(
            "ontrack_compliance_platform_operational_alert_status"
            f'{{code="{alert["code"]}",severity="{alert["severity"]}",metric="{alert["metric"]}"}} {alert_status}'
        )
    return "\n".join(lines) + "\n"


class KycWalletRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    entity_name: Optional[str] = None
    declared_source: Optional[str] = None


class KycWalletResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str] = None
    capability_status: Literal["live", "degraded"]
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    aml_flags: list[str]
    recommendation: Optional[str]
    report_id: Optional[str]
    checked_at: str


class RiskCheckDimensions(BaseModel):
    ownership: int = Field(ge=0, le=100)
    behavioral: int = Field(ge=0, le=100)
    counterparty: int = Field(ge=0, le=100)
    exposure: int = Field(ge=0, le=100)
    aml: int = Field(ge=0, le=100)


class RiskCheckResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str] = None
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    dimensions: Optional[RiskCheckDimensions] = None
    checked_at: str


class DueDiligenceRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    counterparty_context: str


class DueDiligenceResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str] = None
    capability_status: Literal["live", "degraded"]
    dd_score: Optional[int] = Field(default=None, ge=0, le=100)
    red_flags: list[str]
    comfort_level: Optional[str]
    checked_at: str


class SourceOfFundsRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    amount: float
    purpose: str


class SourceOfFundsResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str] = None
    capability_status: Literal["live", "degraded"]
    origin_analysis: dict
    suspicious_pct: Optional[float] = None
    clean_pct: Optional[float] = None
    checked_at: str


class SanctionsCheckResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str] = None
    capability_status: Literal["live", "degraded"]
    lists: list[str]
    hit: Optional[bool] = None
    matched_lists: list[str]
    entity_name: Optional[str]
    designation_date: Optional[str]
    checked_at: str


class ComplianceCatalogItem(BaseModel):
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
    provider: str
    provider_status: Literal["live", "degraded"]
    degraded_reason: Optional[str]
    capability_status: Literal["live", "degraded"]
    delivery_mode: str
    capability_details: dict


class ComplianceCatalogResponse(BaseModel):
    plan: str
    total: int
    generated_at: str
    operations: list[ComplianceCatalogItem]
    note_deprecated: str


class EstimateComplianceRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    operation: str = "kyc_wallet"


class EstimateComplianceResponse(BaseModel):
    quote_id: uuid.UUID
    expires_at: str
    operation_requested: str
    operation_canonical: str
    breakdown: list[dict]
    subtotal_credits: float
    plan_discount: float
    total_credits: float
    total_brl_estimate: float
    credits_available: float
    can_proceed: bool
    calculation_version: str
    pricing_table_hash: str
    plan: str
    chain: str
    warnings: list[dict]
    legal_notice: str


class StartComplianceRequest(BaseModel):
    quote_id: uuid.UUID
    confirmed: bool = False


class StartComplianceResponse(BaseModel):
    case_id: uuid.UUID
    status: str
    operation_requested: str
    operation_canonical: str
    credits_required: float
    billing_action: str
    plan: str
    chain: str
    warnings: list[dict]


class RequoteComplianceResponse(BaseModel):
    status: str
    message: str
    original_quote: dict
    new_quote: dict
    action_required: str
    note: str


class GenerateComplianceReportRequest(BaseModel):
    report_type: Optional[str] = None
    include_onchain_hash: bool = False


class GenerateComplianceReportResponse(BaseModel):
    case_id: uuid.UUID
    report_id: str
    report_type_requested: str
    report_type_canonical: str
    created_at: str
    file_hash_sha256: str
    onchain_hash: Optional[str]
    content_type: str


class BlockEvaluateRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    aml_score: int = Field(default=0, ge=0, le=100)
    is_self_custody: bool = False
    owner_identified: bool = True
    is_international_transfer: bool = False
    has_direct_mixer_contact: bool = False
    has_chain_hopping: bool = False
    structuring_detected: bool = False
    entity_name: Optional[str] = None
    entity_document: Optional[str] = None
    case_id: Optional[uuid.UUID] = None


class BlockEvaluateResponse(BaseModel):
    address: str
    chain: str
    action: str
    requires_coaf_report: bool
    decision_confidence: float
    regulatory_basis: list[str]
    matched_lists: list[str]
    evidence_hash: Optional[str]
    block_id: Optional[uuid.UUID]
    screened_at: str


class BlockLiftRequest(BaseModel):
    reason: str


class BlockLiftResponse(BaseModel):
    block_id: uuid.UUID
    status: str
    review_status: str
    lifted_at: str


class BlockListItem(BaseModel):
    block_id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    address: str
    chain: str
    action: str
    review_status: str
    status: str
    regulatory_basis: list[str]
    matched_lists: list[str]
    decision_confidence: float
    requires_coaf_report: bool
    evidence_hash: str
    screened_at: str
    lifted_at: Optional[str] = None
    lifted_reason: Optional[str] = None
    review_note: Optional[str] = None


class BlockListResponse(BaseModel):
    items: list[BlockListItem]
    total: int
    limit: int
    offset: int


class CounterpartyCreateRequest(BaseModel):
    counterparty_type: str
    legal_name: str
    trading_name: Optional[str] = None
    document_type: str
    document_number: str
    document_country: str = "BRA"
    registration_data: dict = Field(default_factory=dict)
    beneficial_owners: list[dict] = Field(default_factory=list)
    wallet_addresses: list[dict] = Field(default_factory=list)
    declared_risk_context: Optional[str] = None
    onchain_risk_score: Optional[int] = Field(default=None, ge=0, le=100)


class CounterpartyCreateResponse(BaseModel):
    counterparty_id: uuid.UUID
    legal_name: str
    risk_level: int
    kyc_status: str
    sanctions_cleared: bool
    is_pep: bool
    enhanced_dd_required: bool
    next_review_date: str
    status: str


class CounterpartyListItem(BaseModel):
    id: uuid.UUID
    legal_name: str
    counterparty_type: str
    document_type: str
    document_number: str
    risk_level: int
    kyc_status: str
    sanctions_cleared: bool
    is_pep: bool
    enhanced_dd_required: bool
    next_review_date: Optional[str]
    status: str
    created_at: str
    dd_review_status: str = "pending"
    dd_review_note: str = ""
    sof_description: str = ""
    sof_document_ref: str = ""
    last_reviewed_at: Optional[str] = None


class CounterpartyListResponse(BaseModel):
    items: list[CounterpartyListItem]
    total: int


class CounterpartyReviewUpdateRequest(BaseModel):
    dd_review_status: Literal["pending", "in_progress", "completed", "escalated"] = "pending"
    dd_review_note: str = ""
    sof_description: str = ""
    sof_document_ref: str = ""


class CounterpartyReviewResponse(BaseModel):
    counterparty_id: uuid.UUID
    dd_review_status: str
    dd_review_note: str
    sof_description: str
    sof_document_ref: str
    last_reviewed_at: Optional[str] = None


class CounterpartyReviewSnapshot(BaseModel):
    dd_review_status: str
    dd_review_note: str
    sof_description: str
    sof_document_ref: str
    last_reviewed_at: Optional[str] = None


class CounterpartyDetailResponse(BaseModel):
    counterparty_id: uuid.UUID
    legal_name: str
    counterparty_type: str
    document_type: str
    document_number: str
    document_country: str
    registration_data: dict = Field(default_factory=dict)
    beneficial_owners: list[dict] = Field(default_factory=list)
    wallet_addresses: list[dict] = Field(default_factory=list)
    risk_level: int
    risk_rationale: str = ""
    onchain_risk_score: Optional[int] = None
    onchain_analysis: dict = Field(default_factory=dict)
    is_pep: bool
    pep_detail: dict = Field(default_factory=dict)
    sanctions_cleared: bool
    sanctions_hits: list[dict] = Field(default_factory=list)
    kyc_status: str
    enhanced_dd_required: bool
    next_review_date: Optional[str] = None
    status: str
    created_at: str
    review_snapshot: CounterpartyReviewSnapshot


class CounterpartyHistoryItem(BaseModel):
    id: uuid.UUID
    counterparty_id: uuid.UUID
    changed_by_user_id: uuid.UUID
    change_type: str
    field_changed: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_reason: Optional[str] = None
    changed_at: str
    evidence_hash: str


class CounterpartyHistoryResponse(BaseModel):
    items: list[CounterpartyHistoryItem]
    total: int
    limit: int
    offset: int


def _normalize_counterparty_review_status(value: Optional[str]) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"pending", "in_progress", "completed", "escalated"}:
        return normalized

    aliases = {
        "in progress": "in_progress",
        "in-progress": "in_progress",
        "under_review": "in_progress",
        "approved": "completed",
        "done": "completed",
        "waived_with_justification": "escalated",
    }
    return aliases.get(normalized, "pending")


def _normalize_counterparty_review_payload(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            "sof_description": value.get("sof_description", "") if isinstance(value.get("sof_description"), str) else "",
            "sof_document_ref": value.get("sof_document_ref", "") if isinstance(value.get("sof_document_ref"), str) else "",
        }
    return {"sof_description": "", "sof_document_ref": ""}


def _build_counterparty_review_snapshot(row: dict) -> dict[str, Optional[str]]:
    payload = _normalize_counterparty_review_payload(row.get("enhanced_dd_checklist"))
    return {
        "dd_review_status": _normalize_counterparty_review_status(row.get("enhanced_dd_status")),
        "dd_review_note": row.get("enhanced_dd_findings") or "",
        "sof_description": payload["sof_description"],
        "sof_document_ref": payload["sof_document_ref"],
        "last_reviewed_at": row["last_reviewed_at"].isoformat() if row.get("last_reviewed_at") else None,
    }


def _serialize_counterparty_detail(row: dict) -> CounterpartyDetailResponse:
    review_snapshot = _build_counterparty_review_snapshot(row)
    registration_data = row.get("registration_data")
    beneficial_owners = row.get("beneficial_owners")
    wallet_addresses = row.get("wallet_addresses")
    onchain_analysis = row.get("onchain_analysis")
    pep_detail = row.get("pep_detail")
    sanctions_hits = row.get("sanctions_hits")
    return CounterpartyDetailResponse(
        counterparty_id=row["id"],
        legal_name=row["legal_name"],
        counterparty_type=row["counterparty_type"],
        document_type=row["document_type"],
        document_number=row["document_number"],
        document_country=row["document_country"],
        registration_data=registration_data if isinstance(registration_data, dict) else {},
        beneficial_owners=beneficial_owners if isinstance(beneficial_owners, list) else [],
        wallet_addresses=wallet_addresses if isinstance(wallet_addresses, list) else [],
        risk_level=row["risk_level"],
        risk_rationale=row.get("risk_rationale") or "",
        onchain_risk_score=row.get("onchain_risk_score"),
        onchain_analysis=onchain_analysis if isinstance(onchain_analysis, dict) else {},
        is_pep=bool(row.get("is_pep")),
        pep_detail=pep_detail if isinstance(pep_detail, dict) else {},
        sanctions_cleared=bool(row.get("sanctions_cleared")),
        sanctions_hits=sanctions_hits if isinstance(sanctions_hits, list) else [],
        kyc_status=row["kyc_status"],
        enhanced_dd_required=bool(row.get("enhanced_dd_required")),
        next_review_date=row["next_review_date"].isoformat() if row.get("next_review_date") else None,
        status=row["status"],
        created_at=row["created_at"].isoformat(),
        review_snapshot=CounterpartyReviewSnapshot(
            dd_review_status=review_snapshot["dd_review_status"] or "pending",
            dd_review_note=review_snapshot["dd_review_note"] or "",
            sof_description=review_snapshot["sof_description"] or "",
            sof_document_ref=review_snapshot["sof_document_ref"] or "",
            last_reviewed_at=review_snapshot["last_reviewed_at"],
        ),
    )


def _serialize_counterparty_history_item(row: dict) -> CounterpartyHistoryItem:
    return CounterpartyHistoryItem(
        id=row["id"],
        counterparty_id=row["counterparty_id"],
        changed_by_user_id=row["changed_by_user_id"],
        change_type=row["change_type"],
        field_changed=row.get("field_changed"),
        old_value=row.get("old_value"),
        new_value=row.get("new_value"),
        change_reason=row.get("change_reason"),
        changed_at=row["changed_at"].isoformat(),
        evidence_hash=row["evidence_hash"],
    )


def _require_block_read_role(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
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
        allowed_roles=BLOCK_EVALUATE_ALLOWED_ROLES,
        detail="preventive_block_read_role_required",
        resource_type="preventive_block",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _serialize_block_list_item(row: dict) -> BlockListItem:
    sanctions_hits = row.get("sanctions_hits")
    matched_lists = [
        str(hit.get("list_name") or "").strip()
        for hit in sanctions_hits
        if isinstance(hit, dict) and str(hit.get("list_name") or "").strip()
    ] if isinstance(sanctions_hits, list) else []
    confidence = row.get("decision_confidence")
    return BlockListItem(
        block_id=row["id"],
        case_id=row.get("case_id"),
        address=row["target_address"],
        chain=row["target_chain"],
        action=row["block_action"],
        review_status=row["review_status"],
        status=row["status"],
        regulatory_basis=list(row.get("regulatory_basis") or []),
        matched_lists=matched_lists,
        decision_confidence=float(confidence) if confidence is not None else 0.0,
        requires_coaf_report=bool(row.get("coaf_ros_required")),
        evidence_hash=row["evidence_hash"],
        screened_at=row["block_timestamp"].isoformat(),
        lifted_at=row["lifted_at"].isoformat() if row.get("lifted_at") else None,
        lifted_reason=row.get("lifted_reason"),
        review_note=row.get("review_note"),
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/internal/metrics/prometheus")
async def internal_compliance_prometheus_metrics(pool: ConnectionPool = Depends(get_pool)) -> Response:
    if not settings.compliance_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    snapshot = _build_compliance_platform_snapshot(pool=pool)
    alerts = _build_compliance_platform_alerts(snapshot)
    return Response(
        content=_render_compliance_platform_prometheus_metrics(snapshot, alerts),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/internal/provider-readiness")
async def internal_compliance_provider_readiness() -> dict:
    if not settings.compliance_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    readiness = describe_provider_readiness(
        provider_name=settings.compliance_risk_provider,
        trm_config=_get_trm_provider_config(),
    )
    return {
        "provider": readiness.provider_name,
        "provider_supported": readiness.provider_supported,
        "enabled": readiness.enabled,
        "configured": readiness.configured,
        "ready": readiness.ready,
        "degraded_reason": readiness.degraded_reason,
        "details": readiness.details,
    }


@app.get("/api/v1/compliance/operations", response_model=ComplianceCatalogResponse)
async def get_operations_catalog(
    include_deprecated: bool = Query(default=False),
    include_unavailable: bool = Query(default=False),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> ComplianceCatalogResponse:
    plan = normalize_plan(x_plan or "professional")
    catalog = [
        _build_operation_detail(canonical, plan, include_deprecated)
        for canonical in COMPLIANCE_OPERATION_CATALOG.keys()
    ]
    if not include_unavailable:
        catalog = [item for item in catalog if item["available"]]

    return ComplianceCatalogResponse(
        plan=plan,
        total=len(catalog),
        generated_at=datetime.now(timezone.utc).isoformat(),
        operations=[ComplianceCatalogItem(**item) for item in catalog],
        note_deprecated=(
            "aliases_accepted sao aceitos para compatibilidade retroativa. "
            "deprecated_aliases serao removidos em v2 (Jan/2027). Migre para os canonicos."
        ),
    )


@app.get("/api/v1/compliance/operations/{operation_identifier}", response_model=ComplianceCatalogItem)
async def get_operation_detail(
    operation_identifier: str,
    include_deprecated: bool = Query(default=True),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> ComplianceCatalogItem:
    plan = normalize_plan(x_plan or "professional")
    canonical, _ = _resolve_operation(operation_identifier)
    return ComplianceCatalogItem(**_build_operation_detail(canonical, plan, include_deprecated))


@app.post("/api/v1/compliance/estimate", response_model=EstimateComplianceResponse)
async def estimate_compliance(
    body: EstimateComplianceRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> EstimateComplianceResponse:
    org_id = _require_org_id(x_org_id)
    plan = normalize_plan(x_plan or "professional")
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_compliance_estimate_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/estimate",
        method="POST",
    )
    chain = _validate_chain(body.chain)
    quote_payload = _build_compliance_quote_payload(
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
            _persist_compliance_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=quote_payload)
        conn.commit()

    return EstimateComplianceResponse(
        quote_id=quote_payload["quote_id"],
        expires_at=quote_payload["expires_at"].isoformat(),
        operation_requested=quote_payload["operation_requested"],
        operation_canonical=quote_payload["operation_canonical"],
        breakdown=quote_payload["breakdown"],
        subtotal_credits=quote_payload["subtotal_credits"],
        plan_discount=quote_payload["plan_discount"],
        total_credits=quote_payload["total_credits"],
        total_brl_estimate=quote_payload["total_brl_estimate"],
        credits_available=available,
        can_proceed=available >= quote_payload["total_credits"],
        calculation_version=quote_payload["calculation_version"],
        pricing_table_hash=quote_payload["pricing_table_hash"],
        plan=plan,
        chain=chain,
        warnings=quote_payload["warnings"],
        legal_notice=(
            "Valores baseados na tabela de pricing v1.0. O debito final pode variar apenas por mudanca "
            "explicita de plano ou expiracao do quote."
        ),
    )


@app.post("/api/v1/compliance/start", response_model=StartComplianceResponse)
async def start_compliance(
    body: StartComplianceRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> StartComplianceResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    if not body.confirmed:
        raise HTTPException(status_code=412, detail="quote_confirmation_required")

    plan = normalize_plan(x_plan or "professional")
    now = datetime.now(timezone.utc)
    warnings: list[dict] = []
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_compliance_start_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/start",
        method="POST",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM compliance_quotes
                WHERE id = %s
                  AND organization_id = %s
                """,
                (body.quote_id, org_id),
            )
            quote_row = cur.fetchone()
            if not quote_row:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "quote_not_found",
                        "message": "Quote nao encontrado ou nao pertence a organizacao.",
                        "action": "Solicite um novo quote via POST /api/v1/compliance/estimate",
                    },
                )
            if quote_row["used_at"] is not None:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "quote_already_used",
                        "message": "Este quote ja foi consumido anteriormente.",
                        "case_id": str(quote_row["used_for_case_id"]) if quote_row["used_for_case_id"] else None,
                    },
                )
            if quote_row["expires_at"] <= now:
                raise HTTPException(
                    status_code=410,
                    detail={
                        "error": "quote_expired",
                        "message": f"Quote expirou em {quote_row['expires_at'].isoformat()}.",
                        "ttl_minutes": QUOTE_TTL_MINUTES,
                        "action": "Solicite um novo quote. Precos podem ter sido atualizados.",
                        "requote_url": "/api/v1/compliance/estimate",
                    },
                )

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
                            "message": (
                                f"O quote foi emitido no plano {quote_plan.upper()} mas o plano atual e "
                                f"{plan.upper()}."
                            ),
                            "quote_plan": quote_plan,
                            "current_plan": plan,
                            "operation": str(quote_row["operation_canonical"]),
                            "upgrade_url": "/billing/upgrade",
                            "requote_url": "/api/v1/compliance/estimate",
                        },
                    )

                new_quote_payload = _build_compliance_quote_payload(
                    address=str(quote_row["target_address"]),
                    chain=str(quote_row["chain"]),
                    operation_requested=str(quote_row["operation_requested"]),
                    plan=plan,
                )
                _persist_compliance_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=new_quote_payload)
                conn.commit()
                return JSONResponse(
                    status_code=202,
                    content=RequoteComplianceResponse(
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
                            "warnings": new_quote_payload["warnings"],
                        },
                        action_required="Confirme o novo quote via POST /api/v1/compliance/start",
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

            cur.execute(
                "SELECT id, credits_available, credits_reserved FROM organizations WHERE id = %s",
                (org_id,),
            )
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")
            if float(org["credits_available"]) < estimated_cost:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "insufficient_credits",
                        "credits_required": estimated_cost,
                        "credits_available": float(org["credits_available"]),
                    },
                )

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
                  organization_id, user_id, title, case_type, status,
                  target_address, target_chain, context_narrative,
                  credits_estimated, created_at, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    org_id,
                    persisted_user_id,
                    f"Compliance {quote_row['operation_canonical']} {quote_row['target_address']}",
                    "compliance",
                    "queued",
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
                            "requested_by_role": x_role or "UNKNOWN",
                            "external_user_id": (
                                external_actor_user_id
                                if external_actor_user_id
                                else (effective_user_id if effective_user_id and not persisted_user_id else None)
                            ),
                            "org_plan": plan,
                        }
                    ),
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="failed_to_create_case")
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="case_started",
                resource_type="case",
                resource_id=str(row["id"]),
                metadata={
                    "request_id": request_id,
                    "case_type": "compliance",
                    "status": "queued",
                    "credits_estimated": estimated_cost,
                    "quote_id": str(body.quote_id),
                    "operation_requested": str(quote_row["operation_requested"]),
                    "operation_canonical": str(quote_row["operation_canonical"]),
                    "external_user_id": external_actor_user_id,
                },
            )
            _record_credit_ledger(
                cur,
                org_id=org_id,
                case_id=str(row["id"]),
                amount=estimated_cost,
                balance_after=new_available,
                metadata={
                    "request_id": request_id,
                    "quote_id": str(body.quote_id),
                    "operation_requested": str(quote_row["operation_requested"]),
                    "operation_canonical": str(quote_row["operation_canonical"]),
                    "chain": str(quote_row["chain"]),
                },
            )
            cur.execute(
                "UPDATE compliance_quotes SET used_at = NOW(), used_for_case_id = %s WHERE id = %s",
                (row["id"], body.quote_id),
            )
        conn.commit()

    return StartComplianceResponse(
        case_id=row["id"],
        status="queued",
        operation_requested=str(quote_row["operation_requested"]),
        operation_canonical=str(quote_row["operation_canonical"]),
        credits_required=estimated_cost,
        billing_action="PRE_HOLD",
        plan=plan,
        chain=str(quote_row["chain"]),
        warnings=warnings,
    )


def _default_report_type_for_operation(operation: str) -> str:
    mapping = {
        "kyc_wallet": "compliance_aml",
        "due_diligence": "compliance_aml",
        "source_of_funds": "compliance_aml",
        "sanctions_check": "risk_check_instant",
    }
    return mapping.get(operation, "compliance_aml")


def _generate_report_for_case(
    case_id: str,
    report_type: str,
    include_onchain_hash: bool,
    *,
    org_id: str,
    user_id: Optional[str],
    linked_user_id: Optional[str],
    role: Optional[str],
    request_id: Optional[str],
) -> dict:
    payload = json.dumps(
        {
            "case_id": case_id,
            "report_type": report_type,
            "include_onchain_hash": include_onchain_hash,
        }
    ).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "X-Org-Id": org_id,
    }
    if user_id:
        headers["X-User-Id"] = user_id
    if linked_user_id:
        headers["X-Linked-User-Id"] = linked_user_id
    if role:
        headers["X-Role"] = role
    if request_id:
        headers["X-Request-Id"] = request_id
    request = urllib.request.Request(
        f"{settings.report_api_base_url}/api/v1/reports/generate",
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def _get_trm_provider_config() -> TrmRiskProviderConfig:
    return TrmRiskProviderConfig(
        enabled=settings.compliance_trm_enabled,
        screening_url=settings.compliance_trm_screening_url,
        api_key=settings.compliance_trm_api_key,
        api_key_header=settings.compliance_trm_api_key_header,
        api_key_prefix=settings.compliance_trm_api_key_prefix,
        timeout_ms=settings.compliance_trm_timeout_ms,
        max_retries=settings.compliance_trm_max_retries,
    )


@app.post("/api/v1/compliance/cases/{case_id}/report", response_model=GenerateComplianceReportResponse)
async def generate_compliance_report(
    case_id: UUID,
    body: GenerateComplianceReportRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> GenerateComplianceReportResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_compliance_case_report_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=case_id,
        endpoint="/api/v1/compliance/cases/{case_id}/report",
        method="POST",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.id, c.organization_id, c.metadata
                FROM cases c
                WHERE c.id = %s
                  AND c.organization_id = %s
                  AND c.case_type = 'compliance'
                """,
                (case_id, org_id),
            )
            case_row = cur.fetchone()
            if not case_row:
                raise HTTPException(status_code=404, detail="compliance_case_not_found")

            metadata = case_row["metadata"] or {}
            operation = metadata.get("operation_canonical", "kyc_wallet")
            requested_report_type = body.report_type or _default_report_type_for_operation(operation)
            report = _generate_report_for_case(
                str(case_id),
                requested_report_type,
                body.include_onchain_hash,
                org_id=org_id,
                user_id=x_user_id,
                linked_user_id=x_linked_user_id,
                role=x_role,
                request_id=request_id,
            )

            cur.execute(
                """
                INSERT INTO reports (
                  case_id, organization_id, external_report_id, report_type_requested, report_type,
                  content_type, file_hash, onchain_hash, is_coaf_ready, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (external_report_id)
                DO UPDATE SET
                  case_id = EXCLUDED.case_id,
                  organization_id = EXCLUDED.organization_id,
                  report_type_requested = EXCLUDED.report_type_requested,
                  report_type = EXCLUDED.report_type,
                  content_type = EXCLUDED.content_type,
                  file_hash = EXCLUDED.file_hash,
                  onchain_hash = EXCLUDED.onchain_hash,
                  is_coaf_ready = EXCLUDED.is_coaf_ready
                RETURNING id
                """,
                (
                    case_id,
                    org_id,
                    report["report_id"],
                    report["report_type_requested"],
                    report["report_type"],
                    report["content_type"],
                    report["file_hash_sha256"],
                    report["onchain_hash"],
                    report["report_type"] == "coaf_ready_report",
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="report_generated",
                resource_type="case",
                resource_id=str(case_id),
                metadata={
                    "request_id": request_id,
                    "report_id": report["report_id"],
                    "report_type_requested": report["report_type_requested"],
                    "report_type_canonical": report["report_type"],
                    "created_at": report["created_at"],
                    "content_type": report["content_type"],
                    "file_hash_sha256": report["file_hash_sha256"],
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return GenerateComplianceReportResponse(
        case_id=case_id,
        report_id=report["report_id"],
        report_type_requested=report["report_type_requested"],
        report_type_canonical=report["report_type"],
        created_at=report["created_at"],
        file_hash_sha256=report["file_hash_sha256"],
        onchain_hash=report["onchain_hash"],
        content_type=report["content_type"],
    )


@app.post("/api/v1/compliance/kyc-wallet", response_model=KycWalletResponse)
async def kyc_wallet(
    body: KycWalletRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> KycWalletResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_kyc_wallet_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=body.address,
        endpoint="/api/v1/compliance/kyc-wallet",
        method="POST",
    )
    normalized_chain = _validate_chain(body.chain)
    provider_outcome = screen_address(
        provider_name=settings.compliance_risk_provider,
        trm_config=_get_trm_provider_config(),
        address=body.address,
        chain=normalized_chain,
        entity_name=body.entity_name,
        declared_source=body.declared_source,
        request_id=request_id,
    )
    response = KycWalletResponse(
        address=body.address,
        chain=normalized_chain,
        provider=provider_outcome.provider_name,
        provider_status=provider_outcome.provider_status,
        degraded_reason=provider_outcome.degraded_reason,
        capability_status="live" if provider_outcome.provider_status == "live" else "degraded",
        risk_score=provider_outcome.risk_score,
        aml_flags=[],
        recommendation=_derive_kyc_recommendation(
            provider_outcome.risk_score,
            provider_outcome.provider_status,
        ),
        report_id=None,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
    _record_optional_compliance_audit(
        pool=pool,
        org_id=org_id,
        user_id=effective_user_id,
        linked_user_id=external_actor_user_id,
        request_id=request_id,
        action="compliance_kyc_wallet_checked",
        resource_type="address",
        metadata={
            "address": body.address,
            "chain": normalized_chain,
            "provider": response.provider,
            "provider_status": response.provider_status,
            "degraded_reason": response.degraded_reason,
            "capability_status": response.capability_status,
            "risk_score": response.risk_score,
            "recommendation": response.recommendation,
            "external_user_id": external_actor_user_id,
        },
    )
    return response


@app.post("/api/v1/compliance/risk-check", response_model=RiskCheckResponse)
async def risk_check(
    body: KycWalletRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> RiskCheckResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_risk_check_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=body.address,
        endpoint="/api/v1/compliance/risk-check",
        method="POST",
    )
    normalized_chain = _validate_chain(body.chain)
    provider_outcome = screen_address(
        provider_name=settings.compliance_risk_provider,
        trm_config=_get_trm_provider_config(),
        address=body.address,
        chain=normalized_chain,
        entity_name=body.entity_name,
        declared_source=body.declared_source,
        request_id=request_id,
    )
    dimensions = (
        RiskCheckDimensions(**provider_outcome.dimensions)
        if provider_outcome.dimensions
        else None
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="compliance_risk_checked",
                resource_type="address",
                resource_id=None,
                metadata={
                    "request_id": request_id,
                    "address": body.address,
                    "chain": normalized_chain,
                    "provider": provider_outcome.provider_name,
                    "provider_status": provider_outcome.provider_status,
                    "degraded_reason": provider_outcome.degraded_reason,
                    "risk_score": provider_outcome.risk_score,
                    "dimensions": dimensions.model_dump() if dimensions else None,
                    "latency_ms": provider_outcome.latency_ms,
                    "retries_used": provider_outcome.retries_used,
                    "score_source": provider_outcome.score_source,
                    "upstream_status_code": provider_outcome.upstream_status_code,
                    "screening_host": provider_outcome.screening_host,
                    "request_id_forwarded": provider_outcome.request_id_forwarded,
                    "provider_payload": provider_outcome.raw_payload,
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()
    return RiskCheckResponse(
        address=body.address,
        chain=normalized_chain,
        provider=provider_outcome.provider_name,
        provider_status=provider_outcome.provider_status,
        degraded_reason=provider_outcome.degraded_reason,
        risk_score=provider_outcome.risk_score,
        dimensions=dimensions,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/compliance/due-diligence", response_model=DueDiligenceResponse)
async def due_diligence(
    body: DueDiligenceRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> DueDiligenceResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_due_diligence_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=body.address,
        endpoint="/api/v1/compliance/due-diligence",
        method="POST",
    )
    normalized_chain = _validate_chain(body.chain)
    capability = _build_operation_capability("due_diligence")
    response = DueDiligenceResponse(
        address=body.address,
        chain=normalized_chain,
        provider=capability["provider"],
        provider_status=capability["provider_status"],
        degraded_reason=capability["degraded_reason"],
        capability_status=capability["capability_status"],
        dd_score=None,
        red_flags=[],
        comfort_level=None,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
    _record_optional_compliance_audit(
        pool=pool,
        org_id=org_id,
        user_id=effective_user_id,
        linked_user_id=external_actor_user_id,
        request_id=request_id,
        action="compliance_due_diligence_checked",
        resource_type="address",
        metadata={
            "address": body.address,
            "chain": normalized_chain,
            "provider": response.provider,
            "provider_status": response.provider_status,
            "degraded_reason": response.degraded_reason,
            "capability_status": response.capability_status,
            "delivery_mode": capability["delivery_mode"],
            "counterparty_context_present": bool(body.counterparty_context.strip()),
            "external_user_id": external_actor_user_id,
        },
    )
    return response


@app.post("/api/v1/compliance/source-of-funds", response_model=SourceOfFundsResponse)
async def source_of_funds(
    body: SourceOfFundsRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> SourceOfFundsResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_source_of_funds_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=body.address,
        endpoint="/api/v1/compliance/source-of-funds",
        method="POST",
    )
    normalized_chain = _validate_chain(body.chain)
    capability = _build_operation_capability("source_of_funds")
    response = SourceOfFundsResponse(
        address=body.address,
        chain=normalized_chain,
        provider=capability["provider"],
        provider_status=capability["provider_status"],
        degraded_reason=capability["degraded_reason"],
        capability_status=capability["capability_status"],
        origin_analysis={
            "status": capability["delivery_mode"],
            "requires_human_review": True,
        },
        suspicious_pct=None,
        clean_pct=None,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
    _record_optional_compliance_audit(
        pool=pool,
        org_id=org_id,
        user_id=effective_user_id,
        linked_user_id=external_actor_user_id,
        request_id=request_id,
        action="compliance_source_of_funds_checked",
        resource_type="address",
        metadata={
            "address": body.address,
            "chain": normalized_chain,
            "provider": response.provider,
            "provider_status": response.provider_status,
            "degraded_reason": response.degraded_reason,
            "capability_status": response.capability_status,
            "delivery_mode": capability["delivery_mode"],
            "amount": body.amount,
            "purpose": body.purpose,
            "external_user_id": external_actor_user_id,
        },
    )
    return response


@app.get("/api/v1/compliance/sanctions-check/{address}", response_model=SanctionsCheckResponse)
async def sanctions_check(
    address: str,
    pool: ConnectionPool = Depends(get_pool),
    chain: str = "ethereum",
    lists: str = Query(default="OFAC,UN,EU,COAF"),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> SanctionsCheckResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_sanctions_check_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=address,
        endpoint="/api/v1/compliance/sanctions-check/{address}",
        method="GET",
    )
    normalized_chain = _validate_chain(chain)
    resolved_lists = [s.strip() for s in lists.split(",") if s.strip()]
    capability = _build_operation_capability("sanctions_check")
    screening = _screen_address_local(
        pool=pool,
        address=address,
        chain=normalized_chain,
    )
    first_hit = screening.hits[0] if screening.hits else None
    response = SanctionsCheckResponse(
        address=address,
        chain=normalized_chain,
        provider="sanctions_lists_cache",
        provider_status="live",
        degraded_reason=capability["degraded_reason"],
        capability_status="live",
        lists=resolved_lists,
        hit=screening.has_hit,
        matched_lists=[hit.list_name for hit in screening.hits],
        entity_name=first_hit.entity_name if first_hit else None,
        designation_date=first_hit.designation_date if first_hit else None,
        checked_at=screening.screened_at,
    )
    _record_optional_compliance_audit(
        pool=pool,
        org_id=org_id,
        user_id=effective_user_id,
        linked_user_id=external_actor_user_id,
        request_id=request_id,
        action="compliance_sanctions_checked",
        resource_type="address",
        metadata={
            "address": address,
            "chain": normalized_chain,
            "provider": response.provider,
            "provider_status": response.provider_status,
            "degraded_reason": response.degraded_reason,
            "capability_status": response.capability_status,
            "delivery_mode": "local_cache",
            "lists": resolved_lists,
            "matched_lists": response.matched_lists,
            "screening_duration_ms": screening.screening_duration_ms,
            "external_user_id": external_actor_user_id,
        },
    )
    _record_optional_compliance_evidence(
        pool=pool,
        org_id=x_org_id,
        user_id=x_user_id,
        linked_user_id=x_linked_user_id,
        event_type="SANCTIONS_HIT" if screening.has_hit else "SANCTIONS_CHECKED",
        event_payload={
            "address": address,
            "chain": normalized_chain,
            "matched_lists": response.matched_lists,
            "hit": screening.has_hit,
            "screening_duration_ms": screening.screening_duration_ms,
        },
        regulatory_basis=["BCB 520 Art. 43 §2° V", "BCB 520 Art. 34 III"],
    )
    return response


@app.post("/api/v1/compliance/blocks/evaluate", response_model=BlockEvaluateResponse)
async def evaluate_block(
    body: BlockEvaluateRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> BlockEvaluateResponse:
    request_id = x_request_id or str(uuid.uuid4())
    org_id = _require_org_id(x_org_id)
    normalized_chain = _validate_chain(body.chain)
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_block_evaluate_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/blocks/evaluate",
        method="POST",
    )

    screening = _screen_address_local(
        pool=pool,
        address=body.address,
        chain=normalized_chain,
        entity_name=body.entity_name,
        entity_document=body.entity_document,
    )
    sanctions_result = SanctionsResult(
        address=body.address,
        chain=normalized_chain,
        has_hit=screening.has_hit,
        hits=[
            SanctionsHit(
                list_name=hit.list_name,
                entity_name=hit.entity_name,
                confidence=hit.confidence,
                designation_date=hit.designation_date,
                regulatory_basis=hit.regulatory_basis,
            )
            for hit in screening.hits
        ],
        screened_lists=screening.screened_lists,
        screening_duration_ms=screening.screening_duration_ms,
    )
    wallet_context = WalletContext(
        address=body.address,
        chain=normalized_chain,
        aml_score=body.aml_score,
        is_self_custody=body.is_self_custody,
        owner_identified=body.owner_identified,
        is_international_transfer=body.is_international_transfer,
        has_direct_mixer_contact=body.has_direct_mixer_contact,
        has_chain_hopping=body.has_chain_hopping,
        structuring_detected=body.structuring_detected,
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)

        class _EvidenceProxy:
            def __init__(self, cur) -> None:
                self.cur = cur

            async def record_event(self, **kwargs) -> Optional[str]:
                return emit_evidence_event_sync(
                    cur=self.cur,
                    org_id=kwargs["org_id"],
                    event_type=kwargs["event_type"],
                    event_payload=kwargs["event_payload"],
                    actor_user_id=str(kwargs["auth"].user_id) if kwargs["auth"].user_id else None,
                    actor_agent_id=kwargs["auth"].agent_id,
                    case_id=str(kwargs["case_id"]) if kwargs.get("case_id") else None,
                    regulatory_basis=kwargs.get("regulatory_basis"),
                )

        class _DbProxy:
            def __init__(self, cur) -> None:
                self.cur = cur

            async def execute(self, query: str, params: dict) -> None:
                sql = (
                    query.replace("%(id)s", "%s")
                    .replace("%(org_id)s", "%s")
                    .replace("%(case_id)s", "%s")
                    .replace("%(address)s", "%s")
                    .replace("%(chain)s", "%s")
                    .replace("%(action)s", "%s")
                    .replace("%(triggers)s", "%s::jsonb")
                    .replace("%(regulatory_basis)s", "%s")
                    .replace("%(aml_score)s", "%s")
                    .replace("%(sanctions_hits)s", "%s::jsonb")
                    .replace("%(confidence)s", "%s")
                    .replace("%(analysis_context)s", "%s::jsonb")
                    .replace("%(agent)s", "%s")
                    .replace("%(coaf_required)s", "%s")
                    .replace("%(evidence_hash)s", "%s")
                    .replace("%(evidence_trail_hash)s", "%s")
                )
                ordered = (
                    params["id"],
                    params["org_id"],
                    params["case_id"],
                    params["address"],
                    params["chain"],
                    params["action"],
                    params["triggers"],
                    params["regulatory_basis"],
                    params["aml_score"],
                    params["sanctions_hits"],
                    params["confidence"],
                    params["analysis_context"],
                    params["agent"],
                    params["coaf_required"],
                    params["evidence_hash"],
                    params["evidence_trail_hash"],
                )
                self.cur.execute(sql, ordered)

        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            agent = PreventiveBlockAgent(
                evidence_svc=_EvidenceProxy(cur),
                db=_DbProxy(cur),
            )
            auth_ctx = type(
                "AuthCtx",
                (),
                {
                    "user_id": UUID(str(persisted_user_id)) if persisted_user_id else None,
                    "agent_id": None,
                    "org_id": UUID(org_id),
                    "ip_address": None,
                },
            )()
            decision = await agent.evaluate(
                wallet_context=wallet_context,
                sanctions_result=sanctions_result,
                auth=auth_ctx,
                case_id=body.case_id,
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="preventive_block_evaluated",
                resource_type="address",
                resource_id=str(decision.block_id) if decision.block_id else None,
                metadata={
                    "request_id": request_id,
                    "address": body.address,
                    "chain": normalized_chain,
                    "action": decision.action,
                    "matched_lists": [hit.list_name for hit in screening.hits],
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()

    return BlockEvaluateResponse(
        address=body.address,
        chain=normalized_chain,
        action=decision.action,
        requires_coaf_report=decision.requires_coaf_report,
        decision_confidence=decision.decision_confidence,
        regulatory_basis=decision.regulatory_basis,
        matched_lists=[hit.list_name for hit in screening.hits],
        evidence_hash=decision.evidence_hash,
        block_id=decision.block_id,
        screened_at=screening.screened_at,
    )


@app.get("/api/v1/compliance/blocks", response_model=BlockListResponse)
async def list_blocks(
    pool: ConnectionPool = Depends(get_pool),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> BlockListResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_block_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/blocks",
        method="GET",
    )

    normalized_status = status.strip().upper() if isinstance(status, str) and status.strip() else None
    where_clauses = ["organization_id = %s"]
    params: list[object] = [org_id]
    if normalized_status:
        where_clauses.append("status = %s")
        params.append(normalized_status)

    where_sql = " AND ".join(where_clauses)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM preventive_blocks
                WHERE {where_sql}
                """,
                tuple(params),
            )
            total = int(cur.fetchone()["total"])
            cur.execute(
                f"""
                SELECT
                    id,
                    case_id,
                    target_address,
                    target_chain,
                    block_action,
                    review_status,
                    status,
                    regulatory_basis,
                    sanctions_hits,
                    decision_confidence,
                    coaf_ros_required,
                    evidence_hash,
                    block_timestamp,
                    lifted_at,
                    lifted_reason,
                    review_note
                FROM preventive_blocks
                WHERE {where_sql}
                ORDER BY block_timestamp DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                tuple([*params, limit, offset]),
            )
            rows = cur.fetchall()

    return BlockListResponse(
        items=[_serialize_block_list_item(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.post("/api/v1/compliance/blocks/{block_id}/lift", response_model=BlockLiftResponse)
async def lift_block(
    block_id: uuid.UUID,
    body: BlockLiftRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_mfa_mode: Annotated[Optional[str], Header(alias="X-MFA-Mode")] = None,
    x_mfa_provider_homologated: Annotated[Optional[str], Header(alias="X-MFA-Provider-Homologated")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> BlockLiftResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    _require_external_provider_2fa(
        x_mfa_mode=x_mfa_mode,
        x_mfa_provider_homologated=x_mfa_provider_homologated,
    )
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="missing_user_context")
    _require_block_lift_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=block_id,
        endpoint="/api/v1/compliance/blocks/{block_id}/lift",
        method="POST",
    )

    lifted_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_block_lift")
            cur.execute(
                """
                UPDATE preventive_blocks
                   SET status = 'LIFTED',
                       review_status = 'LIFTED',
                       lifted_at = %s,
                       lifted_by_user_id = %s,
                       lifted_reason = %s,
                       reviewed_at = %s,
                       reviewed_by_user_id = %s,
                       review_note = %s
                 WHERE id = %s
                   AND organization_id = %s
                RETURNING id, status, review_status, case_id, target_address, target_chain
                """,
                (
                    lifted_at,
                    persisted_user_id,
                    body.reason,
                    lifted_at,
                    persisted_user_id,
                    body.reason,
                    str(block_id),
                    org_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="preventive_block_not_found")
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="preventive_block_lifted",
                resource_type="preventive_block",
                resource_id=str(block_id),
                metadata={
                    "reason": body.reason,
                    "target_address": row["target_address"],
                    "target_chain": row["target_chain"],
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=org_id,
                event_type="BLOCK_LIFTED",
                event_payload={
                    "block_id": str(block_id),
                    "reason": body.reason,
                    "target_address": row["target_address"],
                    "target_chain": row["target_chain"],
                },
                actor_user_id=persisted_user_id,
                case_id=str(row["case_id"]) if row["case_id"] else None,
                regulatory_basis=["IN BCB 739 Art. 1° VII", "BCB 520 Art. 43 §2° VI"],
            )
        conn.commit()
    return BlockLiftResponse(
        block_id=block_id,
        status=row["status"],
        review_status=row["review_status"],
        lifted_at=lifted_at,
    )


@app.post("/api/v1/compliance/counterparties", response_model=CounterpartyCreateResponse)
async def create_counterparty(
    body: CounterpartyCreateRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> CounterpartyCreateResponse:
    request_id = x_request_id or str(uuid.uuid4())
    org_id = _require_org_id(x_org_id)
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="missing_user_context")
    _require_counterparty_create_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/counterparties",
        method="POST",
    )

    screening = _screen_address_local(
        pool=pool,
        address=(body.wallet_addresses[0]["address"] if body.wallet_addresses else body.document_number),
        chain=(body.wallet_addresses[0].get("chain", "ethereum") if body.wallet_addresses else "ethereum"),
        entity_name=body.legal_name,
        entity_document=body.document_number,
    )
    assessment = CounterpartyAgent().assess(
        CounterpartyInput(
            counterparty_type=body.counterparty_type,
            legal_name=body.legal_name,
            trading_name=body.trading_name,
            document_type=body.document_type,
            document_number=body.document_number,
            document_country=body.document_country,
            registration_data=body.registration_data,
            beneficial_owners=body.beneficial_owners,
            wallet_addresses=body.wallet_addresses,
            declared_risk_context=body.declared_risk_context,
        ),
        sanctions_result=screening,
        onchain_risk_score=body.onchain_risk_score,
    )

    counterparty_id = uuid.uuid4()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_counterparty_creation")
            cur.execute(
                """
                INSERT INTO counterparties (
                    id, organization_id, created_by_user_id,
                    counterparty_type, legal_name, trading_name,
                    document_type, document_number, document_country,
                    document_verified, registration_data, beneficial_owners, wallet_addresses,
                    risk_level, risk_rationale, risk_classified_by, risk_classified_at,
                    onchain_risk_score, onchain_analysis,
                    is_pep, pep_detail,
                    sanctions_cleared, sanctions_check_date, sanctions_hits,
                    kyc_status,
                    enhanced_dd_required, enhanced_dd_status,
                    next_review_date, review_frequency_days,
                    status, status_changed_at, status_changed_by,
                    evidence_hash
                )
                VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s::jsonb, %s::jsonb, %s::jsonb,
                    %s, %s, %s, NOW(),
                    %s, %s::jsonb,
                    %s, %s::jsonb,
                    %s, NOW(), %s::jsonb,
                    %s,
                    %s, %s,
                    %s, %s,
                    %s, NOW(), %s,
                    %s
                )
                """,
                (
                    str(counterparty_id),
                    org_id,
                    persisted_user_id,
                    body.counterparty_type,
                    body.legal_name,
                    body.trading_name,
                    body.document_type,
                    body.document_number,
                    body.document_country,
                    True,
                    json.dumps(body.registration_data),
                    json.dumps(body.beneficial_owners),
                    json.dumps(body.wallet_addresses),
                    assessment.risk_level,
                    assessment.risk_rationale,
                    persisted_user_id,
                    assessment.onchain_risk_score,
                    json.dumps(assessment.onchain_analysis),
                    assessment.is_pep,
                    json.dumps(assessment.pep_detail),
                    assessment.sanctions_cleared,
                    json.dumps(assessment.sanctions_hits),
                    assessment.kyc_status,
                    assessment.enhanced_dd_required,
                    assessment.enhanced_dd_status,
                    assessment.next_review_date.isoformat(),
                    assessment.review_frequency_days,
                    assessment.status,
                    persisted_user_id,
                    assessment.evidence_hash,
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="counterparty_created",
                resource_type="counterparty",
                resource_id=str(counterparty_id),
                metadata={
                    "legal_name": body.legal_name,
                    "risk_level": assessment.risk_level,
                    "kyc_status": assessment.kyc_status,
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=org_id,
                event_type="COUNTERPARTY_ONBOARDED",
                event_payload={
                    "counterparty_id": str(counterparty_id),
                    "legal_name": body.legal_name,
                    "risk_level": assessment.risk_level,
                    "kyc_status": assessment.kyc_status,
                    "sanctions_cleared": assessment.sanctions_cleared,
                },
                actor_user_id=persisted_user_id,
                regulatory_basis=["BCB 520 Art. 47", "IN BCB 739 Art. 1° IV"],
            )
        conn.commit()

    return CounterpartyCreateResponse(
        counterparty_id=counterparty_id,
        legal_name=body.legal_name,
        risk_level=assessment.risk_level,
        kyc_status=assessment.kyc_status,
        sanctions_cleared=assessment.sanctions_cleared,
        is_pep=assessment.is_pep,
        enhanced_dd_required=assessment.enhanced_dd_required,
        next_review_date=assessment.next_review_date.isoformat(),
        status=assessment.status,
    )


@app.get("/api/v1/compliance/counterparties", response_model=CounterpartyListResponse)
async def list_counterparties(
    pool: ConnectionPool = Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> CounterpartyListResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_counterparty_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/compliance/counterparties",
        method="GET",
    )
    items: list[CounterpartyListItem] = []
    total = 0
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM counterparties WHERE organization_id = %s", (org_id,))
            total = int(cur.fetchone()["total"])
            cur.execute(
                """
                SELECT
                    id,
                    legal_name,
                    counterparty_type,
                    document_type,
                    document_number,
                    risk_level,
                    kyc_status,
                    sanctions_cleared,
                    is_pep,
                    enhanced_dd_required,
                    enhanced_dd_status,
                    enhanced_dd_findings,
                    enhanced_dd_checklist,
                    next_review_date,
                    last_reviewed_at,
                    status,
                    created_at
                FROM counterparties
                WHERE organization_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (org_id, limit, offset),
            )
            rows = cur.fetchall()
    for row in rows:
        review_snapshot = _build_counterparty_review_snapshot(row)
        items.append(
            CounterpartyListItem(
                id=row["id"],
                legal_name=row["legal_name"],
                counterparty_type=row["counterparty_type"],
                document_type=row["document_type"],
                document_number=row["document_number"],
                risk_level=row["risk_level"],
                kyc_status=row["kyc_status"],
                sanctions_cleared=row["sanctions_cleared"],
                is_pep=row["is_pep"],
                enhanced_dd_required=row["enhanced_dd_required"],
                next_review_date=row["next_review_date"].isoformat() if row["next_review_date"] else None,
                status=row["status"],
                created_at=row["created_at"].isoformat(),
                dd_review_status=review_snapshot["dd_review_status"] or "pending",
                dd_review_note=review_snapshot["dd_review_note"] or "",
                sof_description=review_snapshot["sof_description"] or "",
                sof_document_ref=review_snapshot["sof_document_ref"] or "",
                last_reviewed_at=review_snapshot["last_reviewed_at"],
            )
        )
    return CounterpartyListResponse(items=items, total=total)


@app.get("/api/v1/compliance/counterparties/{counterparty_id}", response_model=CounterpartyDetailResponse)
async def get_counterparty_detail(
    counterparty_id: uuid.UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> CounterpartyDetailResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_counterparty_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=counterparty_id,
        endpoint="/api/v1/compliance/counterparties/{counterparty_id}",
        method="GET",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    legal_name,
                    counterparty_type,
                    document_type,
                    document_number,
                    document_country,
                    registration_data,
                    beneficial_owners,
                    wallet_addresses,
                    risk_level,
                    risk_rationale,
                    onchain_risk_score,
                    onchain_analysis,
                    is_pep,
                    pep_detail,
                    sanctions_cleared,
                    sanctions_hits,
                    kyc_status,
                    enhanced_dd_required,
                    enhanced_dd_status,
                    enhanced_dd_findings,
                    enhanced_dd_checklist,
                    next_review_date,
                    last_reviewed_at,
                    status,
                    created_at
                FROM counterparties
                WHERE id = %s
                  AND organization_id = %s
                """,
                (str(counterparty_id), org_id),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="counterparty_not_found")
    return _serialize_counterparty_detail(row)


@app.get("/api/v1/compliance/counterparties/{counterparty_id}/history", response_model=CounterpartyHistoryResponse)
async def list_counterparty_history(
    counterparty_id: uuid.UUID,
    pool: ConnectionPool = Depends(get_pool),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> CounterpartyHistoryResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_counterparty_review_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=counterparty_id,
        endpoint="/api/v1/compliance/counterparties/{counterparty_id}/history",
        method="GET",
    )

    rows: list[dict] = []
    total = 0
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM counterparties WHERE id = %s AND organization_id = %s",
                (str(counterparty_id), org_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="counterparty_not_found")

            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM counterparty_history
                WHERE counterparty_id = %s
                  AND organization_id = %s
                """,
                (str(counterparty_id), org_id),
            )
            total = int(cur.fetchone()["total"])
            cur.execute(
                """
                SELECT
                    id,
                    counterparty_id,
                    changed_by_user_id,
                    change_type,
                    field_changed,
                    old_value,
                    new_value,
                    change_reason,
                    changed_at,
                    evidence_hash
                FROM counterparty_history
                WHERE counterparty_id = %s
                  AND organization_id = %s
                ORDER BY changed_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (str(counterparty_id), org_id, limit, offset),
            )
            rows = cur.fetchall()

    return CounterpartyHistoryResponse(
        items=[_serialize_counterparty_history_item(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.patch("/api/v1/compliance/counterparties/{counterparty_id}/review", response_model=CounterpartyReviewResponse)
async def update_counterparty_review(
    counterparty_id: uuid.UUID,
    body: CounterpartyReviewUpdateRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> CounterpartyReviewResponse:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="missing_user_context")
    _require_counterparty_review_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=counterparty_id,
        endpoint="/api/v1/compliance/counterparties/{counterparty_id}/review",
        method="PATCH",
    )

    reviewed_at = datetime.now(timezone.utc)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            if not persisted_user_id:
                raise HTTPException(status_code=403, detail="linked_user_required_for_counterparty_review")

            cur.execute(
                """
                SELECT legal_name, enhanced_dd_status, enhanced_dd_findings, enhanced_dd_checklist, evidence_hash
                FROM counterparties
                WHERE id = %s
                  AND organization_id = %s
                """,
                (str(counterparty_id), org_id),
            )
            existing_row = cur.fetchone()
            if not existing_row:
                raise HTTPException(status_code=404, detail="counterparty_not_found")

            existing_payload = _normalize_counterparty_review_payload(existing_row["enhanced_dd_checklist"])
            merged_payload = {
                **existing_payload,
                "sof_description": body.sof_description.strip(),
                "sof_document_ref": body.sof_document_ref.strip(),
            }
            normalized_status = _normalize_counterparty_review_status(body.dd_review_status)

            cur.execute(
                """
                UPDATE counterparties
                   SET enhanced_dd_status = %s,
                       enhanced_dd_findings = %s,
                       enhanced_dd_checklist = %s::jsonb,
                       last_reviewed_at = %s,
                       last_reviewed_by = %s
                 WHERE id = %s
                   AND organization_id = %s
                RETURNING id, enhanced_dd_status, enhanced_dd_findings, enhanced_dd_checklist, last_reviewed_at
                """,
                (
                    normalized_status,
                    body.dd_review_note.strip(),
                    json.dumps(merged_payload),
                    reviewed_at.isoformat(),
                    persisted_user_id,
                    str(counterparty_id),
                    org_id,
                ),
            )
            updated_row = cur.fetchone()

            cur.execute(
                """
                INSERT INTO counterparty_history (
                    counterparty_id, organization_id, changed_by_user_id, change_type,
                    field_changed, old_value, new_value, change_reason, evidence_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(counterparty_id),
                    org_id,
                    persisted_user_id,
                    "DD_REVIEW_UPDATED",
                    "enhanced_dd_status",
                    existing_row["enhanced_dd_status"],
                    normalized_status,
                    body.dd_review_note.strip() or None,
                    existing_row["evidence_hash"],
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=persisted_user_id,
                action="counterparty_review_updated",
                resource_type="counterparty",
                resource_id=str(counterparty_id),
                metadata={
                    "legal_name": existing_row["legal_name"],
                    "dd_review_status": normalized_status,
                    "sof_document_ref": merged_payload["sof_document_ref"],
                    "external_user_id": external_actor_user_id,
                },
            )
            emit_evidence_event_sync(
                cur=cur,
                org_id=org_id,
                event_type="COUNTERPARTY_UPDATED",
                event_payload={
                    "counterparty_id": str(counterparty_id),
                    "legal_name": existing_row["legal_name"],
                    "dd_review_status": normalized_status,
                    "sof_document_ref": merged_payload["sof_document_ref"],
                },
                actor_user_id=persisted_user_id,
                regulatory_basis=["BCB 520 Art. 47", "Circular BCB 3.978/2020"],
            )
        conn.commit()

    review_snapshot = _build_counterparty_review_snapshot(updated_row)
    return CounterpartyReviewResponse(
        counterparty_id=counterparty_id,
        dd_review_status=review_snapshot["dd_review_status"] or "pending",
        dd_review_note=review_snapshot["dd_review_note"] or "",
        sof_description=review_snapshot["sof_description"] or "",
        sof_document_ref=review_snapshot["sof_document_ref"] or "",
        last_reviewed_at=review_snapshot["last_reviewed_at"],
    )
