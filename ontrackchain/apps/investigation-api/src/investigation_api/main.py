from __future__ import annotations

import base64
import json
import uuid
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from datetime import timedelta
from typing import Annotated, Any, Literal, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from redis.asyncio import Redis

from investigation_api.config.agent_concurrency import CONCURRENCY_LIMITS_MVP
from investigation_api.rpc_provider import RpcProviderConfig, describe_rpc_readiness
from ontrackchain_agents.evidence_integration import emit_evidence_event_sync

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"
    redis_host: str = "redis"
    redis_port: int = 6379
    credit_value_brl: float = 1.0
    investigation_ready_queue_key: str = "investigation:queue:ready"
    investigation_waiting_queue_key: str = "investigation:queue:waiting"
    investigation_retry_zset_key: str = "investigation:queue:retry"
    investigation_dispatch_lock_key: str = "investigation:dispatch:lock"
    investigation_worker_wake_queue_key: str = "investigation:worker:wake"
    investigation_worker_max_attempts: int = 3
    investigation_worker_timeout_seconds: int = 15
    investigation_alert_waiting_warn_threshold: int = 3
    investigation_alert_retry_due_warn_threshold: int = 1
    investigation_alert_dlq_failed_critical_threshold: int = 1
    investigation_alert_oldest_queued_warn_seconds: int = 120
    investigation_alert_oldest_dlq_warn_seconds: int = 300
    investigation_internal_metrics_enabled: bool = True
    investigation_rpc_provider: str = "evm_rpc"
    investigation_rpc_enabled: bool = False
    investigation_rpc_primary_url: str = ""
    investigation_rpc_fallback_url: str = ""
    investigation_rpc_timeout_ms: int = 1500
    investigation_rpc_max_retries: int = 1
    investigation_manual_seal_backend: str = "local_hs256"
    investigation_manual_seal_hs256_secret: str = ""
    investigation_manual_seal_key_id: str = "manual-package-local-hs256"
    investigation_manual_seal_certificate_bundle_ref: str = "local-hs256-trust-bundle"
    investigation_manual_seal_issuer: str = "ontrackchain-investigation-api"


settings = Settings()

app = FastAPI(title="OnTrackChain Investigation API")

SUPPORTED_EVM_CHAINS = {"ethereum", "polygon", "bsc", "arbitrum", "base"}
SUPPORTED_BASIC_CHAINS = SUPPORTED_EVM_CHAINS | {"bitcoin"}

PLAN_DEPTH_LIMITS = {
    "ethereum": {"free": 1, "starter": 3, "professional": 5, "enterprise": 8, "hard_max": 10},
    "polygon": {"free": 1, "starter": 3, "professional": 5, "enterprise": 8, "hard_max": 10},
    "bsc": {"free": 1, "starter": 3, "professional": 5, "enterprise": 8, "hard_max": 10},
    "arbitrum": {"free": 1, "starter": 3, "professional": 5, "enterprise": 8, "hard_max": 10},
    "base": {"free": 1, "starter": 3, "professional": 5, "enterprise": 8, "hard_max": 10},
    "bitcoin": {"free": 0, "starter": 2, "professional": 3, "enterprise": 3, "hard_max": 3},
}

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
    "simple_report": "technical_basic",
    "coaf_lite": "compliance_aml",
}

MANUAL_PACKAGE_EXPORT_AUDIT_ACTION = "evidence_manual_review_package_exported"
MANUAL_PACKAGE_SEAL_AUDIT_ACTIONS = frozenset(
    {
        "evidence_manual_review_package_signoff_requested",
        "evidence_manual_review_package_signoff_recorded",
        "evidence_manual_review_package_sealed",
        "evidence_manual_review_package_seal_revoked",
        "evidence_manual_review_package_seal_superseded",
    }
)
MANUAL_PACKAGE_AUDIT_ACTIONS = MANUAL_PACKAGE_SEAL_AUDIT_ACTIONS | {
    MANUAL_PACKAGE_EXPORT_AUDIT_ACTION
}
MANUAL_PACKAGE_REQUIRED_SIGNER_ROLES = ("compliance_owner", "ops_owner")
MANUAL_PACKAGE_ALLOWED_SIGNER_ROLES = MANUAL_PACKAGE_REQUIRED_SIGNER_ROLES + ("legal_owner_optional",)
MANUAL_PACKAGE_SIGNOFF_METHODS = ("platform_authenticated_2fa", "governance_ticket")
MANUAL_PACKAGE_SIGNOFF_DECISIONS = ("approved", "rejected")
MANUAL_PACKAGE_MFA_VIOLATION_ACTION = "evidence_manual_review_package_mfa_violation"
MANUAL_PACKAGE_READ_ALLOWED_ROLES = {"ADMIN", "AUDITOR", "COMPLIANCE_OFFICER", "LEGAL_REVIEWER", "REVIEWER", "OTK_REVIEWER"}
MANUAL_PACKAGE_ADMIN_MUTATION_ALLOWED_ROLES = {"ADMIN"}
MANUAL_PACKAGE_SIGNOFF_ALLOWED_ROLES = {
    "ADMIN",
    "COMPLIANCE_OFFICER",
    "OTK_COMPLIANCE_OFFICER",
    "LEGAL_REVIEWER",
    "OTK_LEGAL_REVIEWER",
    "REVIEWER",
    "OTK_REVIEWER",
}
MANUAL_PACKAGE_AUTH_ROLE_TO_SIGNER_ROLES = {
    "ADMIN": set(MANUAL_PACKAGE_ALLOWED_SIGNER_ROLES),
    "COMPLIANCE_OFFICER": {"compliance_owner"},
    "OTK_COMPLIANCE_OFFICER": {"compliance_owner"},
    "LEGAL_REVIEWER": {"legal_owner_optional"},
    "OTK_LEGAL_REVIEWER": {"legal_owner_optional"},
    "REVIEWER": {"legal_owner_optional"},
    "OTK_REVIEWER": {"legal_owner_optional"},
}
BILLING_READ_ALLOWED_ROLES = {"ADMIN", "BILLING_ADMIN", "OTK_BILLING_ADMIN"}
MANUAL_PACKAGE_SEAL_STATUSES = (
    "pending_signoff",
    "ready_to_seal",
    "sealed",
    "revoked",
    "superseded",
    "failed",
)
MANUAL_PACKAGE_SEAL_RESOURCE_TYPE = "evidence_package_seal"

PLAN_ORDER = ["free", "starter", "professional", "enterprise"]

REPORT_TYPE_CATALOG = {
    "risk_check_instant": {
        "label": "Risk Check Instantaneo",
        "description": "Score AML 5D sem geracao de PDF. Resposta em < 3s.",
        "min_plan": "starter",
        "aliases_accepted": ["risk", "instant", "quick_check"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 3,
        "output_format": "json",
        "regulatory_reference": None,
        "tags": ["fast", "screening"],
    },
    "technical_basic": {
        "label": "Relatorio Tecnico Basico",
        "description": "Analise on-chain com grafo e score. PDF exportavel.",
        "min_plan": "starter",
        "aliases_accepted": ["technical", "tech", "basic"],
        "deprecated_aliases": ["simple_report"],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 45,
        "output_format": "pdf+json",
        "regulatory_reference": None,
        "tags": ["pdf", "graph"],
    },
    "technical_full": {
        "label": "Relatorio Tecnico Completo",
        "description": "Analise profunda com BridgeTracer cross-chain.",
        "min_plan": "professional",
        "aliases_accepted": ["technical_full", "deep_technical"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 120,
        "output_format": "pdf+json",
        "regulatory_reference": None,
        "tags": ["pdf", "graph", "cross-chain"],
    },
    "compliance_aml": {
        "label": "Relatorio de Compliance AML/KYT",
        "description": "Analise de origem de fundos, score AML e due diligence.",
        "min_plan": "professional",
        "aliases_accepted": ["compliance", "aml", "kyt", "aml_kyt"],
        "deprecated_aliases": ["coaf_lite"],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 180,
        "output_format": "pdf+json",
        "regulatory_reference": "Res. BCB 520 Art. 44-47 | Lei 9.613/98",
        "tags": ["pdf", "compliance", "aml", "regulatorio"],
    },
    "legal_report": {
        "label": "Parecer Juridico-Regulatorio",
        "description": "Analise com enquadramento juridico brasileiro.",
        "min_plan": "professional",
        "aliases_accepted": ["legal", "juridico", "parecer"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 240,
        "output_format": "pdf+json",
        "regulatory_reference": "Lei 14.478/22 | BCB 520 | Lei 9.613/98",
        "tags": ["pdf", "juridico", "compliance"],
    },
    "coaf_ready_report": {
        "label": "Relatorio Pronto para COAF (ROS)",
        "description": "Formatado para submissao de Relatorio de Operacao Suspeita.",
        "min_plan": "enterprise",
        "aliases_accepted": ["coaf", "coaf_report", "ros"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 360,
        "output_format": "pdf+json+coaf_xml",
        "regulatory_reference": "IN BCB 739/26 | COAF Res. 36/21 | Lei 9.613/98",
        "tags": ["pdf", "coaf", "regulatorio", "ros", "enterprise"],
    },
    "full_investigation": {
        "label": "Investigacao Completa",
        "description": "Pipeline completo com multiplos agentes e consolidacao final.",
        "min_plan": "enterprise",
        "aliases_accepted": ["full", "investigation"],
        "deprecated_aliases": [],
        "chains_supported": sorted(SUPPORTED_BASIC_CHAINS),
        "avg_duration_seconds": 420,
        "output_format": "pdf+json",
        "regulatory_reference": None,
        "tags": ["pdf", "investigation", "enterprise"],
    },
}

PRICING_TABLE = {
    "chain_base_cost": {
        "ethereum": 1.0,
        "polygon": 0.8,
        "bsc": 0.8,
        "arbitrum": 0.9,
        "base": 0.8,
        "bitcoin": 1.8,
    },
    "depth_multiplier": {
        1: 1.0,
        2: 1.3,
        3: 1.7,
        4: 2.2,
        5: 3.0,
        6: 4.0,
        7: 5.5,
        8: 7.5,
        9: 10.0,
        10: 14.0,
    },
    "report_type_cost": {
        "risk_check_instant": 0.5,
        "technical_basic": 1.0,
        "technical_full": 2.0,
        "compliance_aml": 3.0,
        "legal_report": 5.0,
        "coaf_ready_report": 8.0,
        "full_investigation": 10.0,
    },
    "addons": {
        "cross_chain_bridge_trace": 2.0,
        "monitoring_30days": 3.0,
        "monitoring_90days": 7.0,
        "monitoring_365days": 20.0,
        "source_of_funds_analysis": 2.0,
        "pep_screening": 1.0,
        "onchain_evidence_registry": 1.0,
    },
}

CALCULATION_VERSION = "v1.0"
QUOTE_TTL_MINUTES = 15
MAX_VARIANCE_PCT = 0.10


def _dsn() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


@app.on_event("startup")
async def _startup() -> None:
    app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
    app.state.redis = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


@app.on_event("shutdown")
async def _shutdown() -> None:
    pool: ConnectionPool = app.state.pool
    pool.close()
    redis: Redis = app.state.redis
    await redis.aclose()


def get_pool() -> ConnectionPool:
    return app.state.pool


async def get_redis() -> Redis:
    return app.state.redis


def _get_rpc_provider_config() -> RpcProviderConfig:
    return RpcProviderConfig(
        enabled=settings.investigation_rpc_enabled,
        primary_url=settings.investigation_rpc_primary_url,
        fallback_url=settings.investigation_rpc_fallback_url,
        timeout_ms=settings.investigation_rpc_timeout_ms,
        max_retries=settings.investigation_rpc_max_retries,
    )


def _apply_rls_context(conn, org_id: Optional[str]) -> None:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, true)", (org_id,))


def _require_org_id(org_id: Optional[str]) -> str:
    if not org_id:
        raise HTTPException(status_code=401, detail="missing_org_context")
    return org_id


def _normalized_role(x_role: Optional[str]) -> str:
    return (x_role or "").strip().upper()


def _require_platform_authenticated_2fa(
    *,
    x_2fa: Optional[str],
    x_mfa_mode: Optional[str],
    x_mfa_provider_homologated: Optional[str],
) -> None:
    normalized_mfa_mode = (x_mfa_mode or "").lower()
    if normalized_mfa_mode == "external_provider":
        if (x_mfa_provider_homologated or "").lower() != "true":
            raise HTTPException(status_code=403, detail="mfa_not_homologated_for_oidc")
        if x_2fa not in {"managed_externally", "managed_externally_homologated", "ok"}:
            raise HTTPException(status_code=403, detail="2fa_required")
        return
    if x_2fa != "ok":
        raise HTTPException(status_code=403, detail="2fa_required")


def _require_role(x_role: Optional[str], *, allowed_roles: set[str], detail: str) -> str:
    role = _normalized_role(x_role)
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return role


def _require_admin_role(x_role: Optional[str]) -> str:
    return _require_role(x_role, allowed_roles={"ADMIN"}, detail="admin_required")


def _require_privileged_read_role(x_role: Optional[str]) -> str:
    return _require_role(x_role, allowed_roles={"ADMIN", "AUDITOR"}, detail="privileged_read_role_required")


def _normalize_chain(chain: str) -> str:
    return chain.strip().lower()


def _validate_chain(chain: str) -> str:
    normalized = _normalize_chain(chain)
    if normalized not in SUPPORTED_BASIC_CHAINS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_chain",
                "message": "Chain fora do escopo do MVP",
                "supported_chains": sorted(SUPPORTED_BASIC_CHAINS),
            },
        )
    return normalized


def _org_active_counter_key(org_id: str) -> str:
    return f"investigation:active:org:{org_id}"


def _global_active_counter_key() -> str:
    return "investigation:active:global"


async def _get_active_counts(redis: Redis, org_id: str) -> tuple[int, int]:
    org_active_raw, global_active_raw = await redis.mget(_org_active_counter_key(org_id), _global_active_counter_key())
    return int(org_active_raw or 0), int(global_active_raw or 0)


async def _increment_active_counters(redis: Redis, org_id: str) -> None:
    await redis.incr(_org_active_counter_key(org_id))
    await redis.incr(_global_active_counter_key())


async def _enqueue_worker_signal(redis: Redis, payload: dict) -> None:
    message = json.dumps(payload, sort_keys=True)
    await redis.rpush(settings.investigation_worker_wake_queue_key, message)


async def _enqueue_case_for_worker(redis: Redis, payload: dict, *, immediate: bool) -> None:
    queue_key = settings.investigation_ready_queue_key if immediate else settings.investigation_waiting_queue_key
    message = json.dumps(payload, sort_keys=True)
    await redis.rpush(queue_key, message)
    await _enqueue_worker_signal(redis, {"event": "case_enqueued", "case_id": payload["case_id"], "org_id": payload["org_id"]})


def _normalize_plan(plan: str) -> str:
    return plan.strip().lower()


def _plan_rank(plan: str) -> int:
    normalized = _normalize_plan(plan)
    if normalized not in PLAN_ORDER:
        return PLAN_ORDER.index("starter")
    return PLAN_ORDER.index(normalized)


def _is_report_type_available(report_type: str, plan: str) -> bool:
    canonical, _ = _resolve_report_type(report_type)
    min_plan = REPORT_TYPE_CATALOG[canonical]["min_plan"]
    return _plan_rank(plan) >= _plan_rank(min_plan)


def _required_plan_for_report_type(report_type: str) -> str:
    canonical, _ = _resolve_report_type(report_type)
    return str(REPORT_TYPE_CATALOG[canonical]["min_plan"])


def _resolve_report_type(raw_input: str) -> tuple[str, Optional[dict]]:
    normalized = raw_input.strip().lower().replace("-", "_")
    if normalized in PRICING_TABLE["report_type_cost"]:
        return normalized, None
    if normalized in REPORT_TYPE_ALIASES:
        canonical = REPORT_TYPE_ALIASES[normalized]
        return canonical, {
            "warning": "report_type_alias_resolved",
            "requested": raw_input,
            "canonical": canonical,
        }
    raise HTTPException(
        status_code=422,
        detail={
            "code": "invalid_report_type",
            "message": f"report_type '{raw_input}' nao reconhecido",
            "valid_report_types": sorted(PRICING_TABLE["report_type_cost"].keys()),
            "accepted_aliases": sorted(REPORT_TYPE_ALIASES.keys()),
        },
    )


def _suggest_next_plan(current_plan: str) -> str:
    current_rank = _plan_rank(current_plan)
    if current_rank >= len(PLAN_ORDER) - 1:
        return "enterprise"
    return PLAN_ORDER[current_rank + 1]


def _next_plan_cap(chain: str, current_plan: str) -> int:
    normalized_chain = _normalize_chain(chain)
    chain_limits = PLAN_DEPTH_LIMITS.get(normalized_chain, PLAN_DEPTH_LIMITS["ethereum"])
    order = ["free", "starter", "professional", "enterprise"]
    current = _normalize_plan(current_plan)
    idx = order.index(current) if current in order else order.index("professional")
    if idx >= len(order) - 1:
        return int(chain_limits["enterprise"])
    return int(chain_limits[order[idx + 1]])


def _get_depth_cap(chain: str, plan: str, requested_depth: int) -> tuple[int, Optional[dict]]:
    normalized_chain = _normalize_chain(chain)
    normalized_plan = _normalize_plan(plan)
    chain_limits = PLAN_DEPTH_LIMITS.get(normalized_chain, PLAN_DEPTH_LIMITS["ethereum"])
    plan_cap = int(chain_limits.get(normalized_plan, chain_limits["starter"]))
    hard_cap = int(chain_limits["hard_max"])

    if plan_cap <= 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "chain_not_available_for_plan",
                "chain": normalized_chain,
                "plan": normalized_plan,
            },
        )

    effective = min(requested_depth, plan_cap, hard_cap)
    warning: Optional[dict] = None

    if normalized_chain == "bitcoin" and requested_depth > effective:
        warning = {
            "warning": "bitcoin_depth_capped",
            "requested": requested_depth,
            "applied": effective,
            "reason": "Bitcoin MVP limit — BridgeTracer não disponível para análise cross-chain BTC",
            "upgrade_path": "Fase 2 (Q4 2026) incluirá rastreio BTC até 5 hops com cross-chain",
            "coverage_estimate": "~85% dos padrões AML detectáveis nesta profundidade",
            "plan": normalized_plan,
        }
    elif requested_depth > plan_cap:
        warning = {
            "warning": "plan_depth_capped",
            "chain": normalized_chain,
            "plan": normalized_plan,
            "requested": requested_depth,
            "applied": effective,
            "reason": (
                f"depth={requested_depth} excede o limite do plano {normalized_plan.upper()} "
                f"para {normalized_chain} (max={plan_cap})."
            ),
            "upgrade_path": (
                f"Upgrade para {_suggest_next_plan(normalized_plan).capitalize()} "
                f"para depth até {_next_plan_cap(normalized_chain, normalized_plan)}."
            ),
        }
    elif requested_depth > hard_cap:
        warning = {
            "warning": "hard_depth_capped",
            "chain": normalized_chain,
            "requested": requested_depth,
            "applied": effective,
            "reason": f"depth={requested_depth} excede o limite global do sistema (max={hard_cap}).",
        }

    return effective, warning


def _build_report_type_detail(canonical: str, current_plan: str, include_deprecated: bool) -> dict:
    meta = REPORT_TYPE_CATALOG[canonical]
    available = _is_report_type_available(canonical, current_plan)
    aliases = list(meta["aliases_accepted"])
    deprecated_aliases = list(meta["deprecated_aliases"]) if include_deprecated else []
    return {
        "canonical": canonical,
        "label": meta["label"],
        "description": meta["description"],
        "cost_credits": float(PRICING_TABLE["report_type_cost"][canonical]),
        "available": available,
        "upgrade_required": None if available else meta["min_plan"],
        "min_plan": meta["min_plan"],
        "aliases_accepted": aliases,
        "deprecated_aliases": deprecated_aliases,
        "chains_supported": meta["chains_supported"],
        "avg_duration_seconds": meta["avg_duration_seconds"],
        "output_format": meta["output_format"],
        "regulatory_reference": meta["regulatory_reference"],
        "tags": meta["tags"],
    }


def _build_quote_payload(
    *,
    address: str,
    chains: list[str],
    requested_depth: int,
    report_type_requested: str,
    addons: list[str],
    plan: str,
) -> dict:
    warnings: list[dict] = []
    canonical_report_type, alias_warning = _resolve_report_type(report_type_requested)
    if alias_warning:
        warnings.append(alias_warning)

    if not _is_report_type_available(canonical_report_type, plan):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "report_type_not_available_on_plan",
                "report_type": canonical_report_type,
                "required_plan": _required_plan_for_report_type(canonical_report_type),
                "current_plan": plan,
            },
        )

    applied_depth = requested_depth
    normalized_addons = [a.strip() for a in addons if a.strip()]
    for chain in chains:
        depth_for_chain, warning = _get_depth_cap(chain, plan, requested_depth)
        if warning:
            warnings.append(warning)
        applied_depth = min(applied_depth, depth_for_chain)

    quote = _calculate_cost(
        chains=chains,
        depth=applied_depth,
        report_type=canonical_report_type,
        addons=normalized_addons,
        org_plan=plan,
    )
    quote_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=QUOTE_TTL_MINUTES)
    total_credits = float(quote["total_credits"])
    return {
        "quote_id": quote_id,
        "expires_at": expires_at,
        "report_type_requested": report_type_requested,
        "report_type_canonical": canonical_report_type,
        "breakdown": quote["breakdown"],
        "subtotal_credits": float(quote["subtotal_credits"]),
        "plan_discount": float(quote["plan_discount"]),
        "total_credits": total_credits,
        "total_brl_estimate": round(total_credits * float(settings.credit_value_brl), 2),
        "calculation_version": quote["calculation_version"],
        "pricing_table_hash": quote["pricing_table_hash"],
        "depth_requested": requested_depth,
        "depth_applied": applied_depth,
        "plan": plan,
        "warnings": warnings,
        "address": address,
        "chains": chains,
        "addons": normalized_addons,
    }


def _persist_quote(cur, *, org_id: str, user_id: Optional[str], quote_payload: dict) -> None:
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    cur.execute(
        """
        INSERT INTO investigation_quotes (
          id, organization_id, user_id, plan, plan_snapshot, target_address, chains,
          requested_depth, applied_depth, report_type_requested, report_type, addons,
          quote_breakdown, subtotal_credits, plan_discount, total_credits,
          pricing_table_hash, calculation_version, expires_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
        """,
        (
            quote_payload["quote_id"],
            org_id,
            persisted_user_id,
            quote_payload["plan"],
            quote_payload["plan"],
            quote_payload["address"],
            quote_payload["chains"],
            quote_payload["depth_requested"],
            quote_payload["depth_applied"],
            quote_payload["report_type_requested"],
            quote_payload["report_type_canonical"],
            quote_payload["addons"],
            json.dumps(quote_payload["breakdown"]),
            quote_payload["subtotal_credits"],
            quote_payload["plan_discount"],
            quote_payload["total_credits"],
            quote_payload["pricing_table_hash"],
            quote_payload["calculation_version"],
            quote_payload["expires_at"],
        ),
    )


def _pricing_table_hash() -> str:
    payload = json.dumps(PRICING_TABLE, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _calculate_cost(
    *,
    chains: list[str],
    depth: int,
    report_type: str,
    addons: list[str],
    org_plan: str,
) -> dict:
    breakdown: list[dict] = []
    total = 0.0

    for chain in chains:
        chain_cost = float(PRICING_TABLE["chain_base_cost"].get(chain, 1.5))
        depth_mult = float(PRICING_TABLE["depth_multiplier"].get(depth, 14.0))
        chain_total = chain_cost * depth_mult
        breakdown.append(
            {
                "item": f"Coleta on-chain: {chain}",
                "base_cost": chain_cost,
                "depth": depth,
                "depth_multiplier": depth_mult,
                "subtotal": round(chain_total, 4),
            }
        )
        total += chain_total

    report_cost = float(PRICING_TABLE["report_type_cost"].get(report_type, 2.0))
    breakdown.append({"item": f"Relatório: {report_type}", "subtotal": round(report_cost, 4)})
    total += report_cost

    for addon in addons:
        addon_cost = float(PRICING_TABLE["addons"].get(addon, 0.0))
        breakdown.append({"item": f"Add-on: {addon}", "subtotal": round(addon_cost, 4)})
        total += addon_cost

    plan_discounts = {"starter": 0.0, "professional": 0.0, "enterprise": 0.15}
    discount_pct = float(plan_discounts.get(org_plan, 0.0))
    discount = total * discount_pct
    total_final = total - discount

    return {
        "breakdown": breakdown,
        "subtotal_credits": round(total, 4),
        "plan_discount": round(discount, 4),
        "total_credits": round(total_final, 4),
        "calculation_version": CALCULATION_VERSION,
        "pricing_table_hash": _pricing_table_hash(),
    }


def _record_credit_ledger(
    cur,
    *,
    org_id: str,
    case_id: Optional[UUID],
    action: str,
    amount: float,
    balance_after: float,
    metadata: dict,
) -> None:
    cur.execute(
        """
        INSERT INTO credit_ledger (org_id, case_id, action, amount, balance_after, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (org_id, case_id, action, amount, balance_after, json.dumps(metadata)),
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


def _record_manual_package_audit_event(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str | UUID],
    request_id: Optional[str],
    report_id: Optional[str],
    metadata: dict[str, object],
    created_at: str,
    external_user_id: Optional[str],
) -> dict[str, object]:
    if action not in MANUAL_PACKAGE_AUDIT_ACTIONS:
        raise ValueError(f"unsupported_manual_package_audit_action: {action}")

    normalized_metadata: dict[str, object] = {
        **metadata,
        "request_id": request_id,
        "report_id": report_id,
        "created_at": created_at,
    }
    if external_user_id:
        normalized_metadata["external_user_id"] = external_user_id

    _record_audit_log(
        cur,
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=normalized_metadata,
    )
    return normalized_metadata


def _record_audit_log(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str | UUID],
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
        (
            organization_id,
            persisted_user_id,
            action,
            resource_type,
            str(resource_id) if resource_id else None,
            json.dumps(normalized_metadata),
        ),
    )

    # ─── EVIDENCE TRAIL: piggyback no audit_log existente ─────────────────────
    # Mapeia ações do audit_log para event_types da evidence_trail
    _AUDIT_TO_EVIDENCE: dict[str, str] = {
        "case_started":           "CASE_CREATED",
        "case_completed":         "INVESTIGATION_COMPLETED",
        "case_failed":            "CASE_UPDATED",
        "compliance_risk_checked":"SANCTIONS_CHECKED",
        "report_generated":       "REPORT_GENERATED",
        "report_downloaded":      "REPORT_DOWNLOADED",
        "operational_alerts_exported": "EVIDENCE_EXPORTED",
        "evidence_manual_review_package_exported": "EVIDENCE_EXPORTED",
    }
    evidence_event_type = _AUDIT_TO_EVIDENCE.get(action)
    if evidence_event_type:
        case_id_str = (
            str(resource_id)
            if resource_id and resource_type == "case"
            else normalized_metadata.get("case_id")
        )
        emit_evidence_event_sync(
            cur=cur,
            org_id=organization_id,
            event_type=evidence_event_type,
            event_payload={
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                **{k: v for k, v in normalized_metadata.items()
                   if k not in ("external_user_id",)},  # evita duplicação
            },
            actor_user_id=persisted_user_id,
            case_id=case_id_str,
            regulatory_basis=["BCB 520 Art. 43 — Registro de operação"],
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
        logger.exception("failed_to_record_authorization_denial")


def _record_manual_package_mfa_violation(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    seal_id: str | UUID,
    request_id: str,
    auth_role: str,
    signer_role: str,
    signoff_method: str,
    mfa_mode: Optional[str],
    mfa_provider_homologated: Optional[str],
    two_factor_status: Optional[str],
    detail: str,
) -> None:
    try:
        with pool.connection() as conn:
            _apply_rls_context(conn, organization_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur,
                    organization_id=organization_id,
                    user_id=user_id,
                    action=MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                    resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                    resource_id=seal_id,
                    metadata={
                        "request_id": request_id,
                        "auth_role": auth_role,
                        "asserted_signer_role": signer_role,
                        "signoff_method": signoff_method,
                        "mfa_mode": mfa_mode or "not_informed",
                        "mfa_provider_homologated": (mfa_provider_homologated or "").lower() == "true",
                        "two_factor_status": two_factor_status or "not_informed",
                        "detail": detail,
                        "external_user_id": external_user_id,
                    },
                )
            conn.commit()
    except Exception:
        logger.exception("failed_to_record_manual_package_mfa_violation")


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


def _record_agent_run(
    cur,
    *,
    case_id: UUID,
    request_id: str,
) -> None:
    cur.execute(
        """
        INSERT INTO agent_runs (case_id, agent_name, status, input)
        VALUES (%s, %s, %s, %s::jsonb)
        """,
        (
            case_id,
            "investigation_executor",
            "pending",
            json.dumps(
                {
                    "request_id": request_id,
                    "attempt_count": 0,
                    "max_attempts": settings.investigation_worker_max_attempts,
                    "timeout_seconds": settings.investigation_worker_timeout_seconds,
                    "mode": "redis_async_worker_v1",
                }
            ),
        ),
    )


def _serialize_audit_log_row(row: dict) -> dict:
    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    return {
        "id": str(row["id"]),
        "user_id": str(row["user_id"]) if row.get("user_id") else None,
        "action": row["action"],
        "resource_type": row["resource_type"],
        "resource_id": str(row["resource_id"]) if row.get("resource_id") else None,
        "request_id": metadata.get("request_id"),
        "report_id": metadata.get("report_id"),
        "file_hash_sha256": metadata.get("file_hash_sha256"),
        "metadata": metadata,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _required_manual_package_signer_roles(_signoff_mode: Optional[str]) -> tuple[str, ...]:
    # Baseline arquitetural aprovada: quorum minimo Compliance + Ops.
    return MANUAL_PACKAGE_REQUIRED_SIGNER_ROLES


def _require_manual_package_read_role(
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
        allowed_roles=MANUAL_PACKAGE_READ_ALLOWED_ROLES,
        detail="manual_package_read_role_required",
        resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_manual_package_admin_mutation_role(
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
        allowed_roles=MANUAL_PACKAGE_ADMIN_MUTATION_ALLOWED_ROLES,
        detail="manual_package_admin_role_required",
        resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_billing_read_role(
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
        allowed_roles=BILLING_READ_ALLOWED_ROLES,
        detail="billing_balance_role_required",
        resource_type="billing_balance",
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )


def _require_manual_package_signoff_role_binding(
    pool: ConnectionPool,
    *,
    organization_id: str,
    user_id: Optional[str],
    external_user_id: Optional[str],
    request_id: str,
    x_role: Optional[str],
    signer_role: str,
    resource_id: Optional[str | UUID],
    endpoint: str,
    method: str,
) -> str:
    auth_role = _require_role_with_audit(
        pool,
        organization_id=organization_id,
        user_id=user_id,
        external_user_id=external_user_id,
        request_id=request_id,
        x_role=x_role,
        allowed_roles=MANUAL_PACKAGE_SIGNOFF_ALLOWED_ROLES,
        detail="manual_package_signoff_role_required",
        resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
        resource_id=resource_id,
        endpoint=endpoint,
        method=method,
    )
    allowed_signer_roles = MANUAL_PACKAGE_AUTH_ROLE_TO_SIGNER_ROLES.get(auth_role, set())
    if signer_role not in allowed_signer_roles:
        _record_authorization_denial(
            pool,
            organization_id=organization_id,
            user_id=user_id,
            external_user_id=external_user_id,
            request_id=request_id,
            effective_role=auth_role,
            allowed_roles=set(allowed_signer_roles),
            detail="manual_package_signer_role_mismatch",
            resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
        )
        raise HTTPException(status_code=403, detail="manual_package_signer_role_mismatch")
    return auth_role


def _serialize_manual_package_signoff_row(row: dict) -> dict:
    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    return {
        "id": str(row["id"]),
        "seal_id": str(row["seal_id"]),
        "organization_id": str(row["organization_id"]),
        "signer_role": row["signer_role"],
        "signer_user_id": str(row["signer_user_id"]) if row.get("signer_user_id") else None,
        "signer_display_name": row["signer_display_name"],
        "decision": row["decision"],
        "signoff_method": row["signoff_method"],
        "ticket_ref": row.get("ticket_ref"),
        "notes": row.get("notes"),
        "signed_at": row["signed_at"].isoformat() if row.get("signed_at") else None,
        "metadata": metadata,
    }


def _serialize_manual_package_seal_row(row: dict, signoffs: list[dict]) -> dict:
    raw_envelope = row.get("seal_envelope")
    seal_envelope = raw_envelope if isinstance(raw_envelope, dict) else {}
    raw_verification_summary = row.get("verification_summary")
    verification_summary = raw_verification_summary if isinstance(raw_verification_summary, dict) else {}
    serialized_signoffs = [_serialize_manual_package_signoff_row(signoff_row) for signoff_row in signoffs]
    approved_roles = {
        signoff["signer_role"]
        for signoff in serialized_signoffs
        if signoff["decision"] == "approved"
    }
    required_signers = list(_required_manual_package_signer_roles(row.get("signoff_mode")))
    return {
        "seal_id": str(row["id"]),
        "organization_id": str(row["organization_id"]),
        "package_kind": row["package_kind"],
        "request_id": row["request_id"],
        "report_id": row.get("report_id"),
        "scope_id": row["scope_id"],
        "manual_review_action": row["manual_review_action"],
        "package_sha256": row["package_sha256"],
        "manifest_schema_version": row["manifest_schema_version"],
        "classification": row["classification"],
        "signoff_mode": row["signoff_mode"],
        "seal_status": row["seal_status"],
        "seal_format": row["seal_format"],
        "signature_algorithm": row.get("signature_algorithm"),
        "kms_key_ref": row.get("kms_key_ref"),
        "certificate_fingerprint_sha256": row.get("certificate_fingerprint_sha256"),
        "certificate_bundle_ref": row.get("certificate_bundle_ref"),
        "policy_version": row["policy_version"],
        "sealed_at": row["sealed_at"].isoformat() if row.get("sealed_at") else None,
        "sealed_by_user_id": str(row["sealed_by_user_id"]) if row.get("sealed_by_user_id") else None,
        "revoked_at": row["revoked_at"].isoformat() if row.get("revoked_at") else None,
        "superseded_by_seal_id": str(row["superseded_by_seal_id"]) if row.get("superseded_by_seal_id") else None,
        "required_signers": required_signers,
        "completed_signoffs": len(serialized_signoffs),
        "approved_required_signoffs": sum(1 for role in required_signers if role in approved_roles),
        "required_signoffs": len(required_signers),
        "signoffs": serialized_signoffs,
        "seal_envelope": seal_envelope,
        "verification_summary": verification_summary,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


def _load_manual_package_seal(cur, *, organization_id: str, seal_id: UUID) -> tuple[dict, list[dict]]:
    cur.execute(
        """
        SELECT
            id,
            organization_id,
            package_kind,
            request_id,
            report_id,
            scope_id,
            manual_review_action,
            package_sha256,
            manifest_schema_version,
            classification,
            signoff_mode,
            seal_status,
            seal_format,
            signature_algorithm,
            kms_key_ref,
            certificate_fingerprint_sha256,
            certificate_bundle_ref,
            policy_version,
            sealed_at,
            sealed_by_user_id,
            revoked_at,
            superseded_by_seal_id,
            seal_envelope,
            verification_summary,
            created_at,
            updated_at
        FROM evidence_package_seals
        WHERE organization_id = %s
          AND id = %s
        """,
        (organization_id, seal_id),
    )
    seal_row = cur.fetchone()
    if not seal_row:
        raise HTTPException(status_code=404, detail="manual_package_seal_not_found")

    cur.execute(
        """
        SELECT
            id,
            seal_id,
            organization_id,
            signer_role,
            signer_user_id,
            signer_display_name,
            decision,
            signoff_method,
            ticket_ref,
            notes,
            signed_at,
            metadata
        FROM evidence_package_signoffs
        WHERE organization_id = %s
          AND seal_id = %s
        ORDER BY signed_at ASC
        """,
        (organization_id, seal_id),
    )
    signoff_rows = cur.fetchall()
    return seal_row, signoff_rows


def _load_manual_package_seal_by_digest(
    cur,
    *,
    organization_id: str,
    package_sha256: str,
    policy_version: str,
) -> tuple[dict, list[dict]]:
    cur.execute(
        """
        SELECT id
        FROM evidence_package_seals
        WHERE organization_id = %s
          AND package_sha256 = %s
          AND policy_version = %s
        """,
        (organization_id, package_sha256, policy_version),
    )
    seal_row = cur.fetchone()
    if not seal_row:
        raise HTTPException(status_code=404, detail="manual_package_seal_not_found")
    return _load_manual_package_seal(cur, organization_id=organization_id, seal_id=seal_row["id"])


def _resolve_manual_package_seal_status(signoff_mode: str, signoffs: list[dict]) -> str:
    if any(signoff.get("decision") == "rejected" for signoff in signoffs):
        return "failed"

    approved_roles = {
        signoff.get("signer_role")
        for signoff in signoffs
        if signoff.get("decision") == "approved"
    }
    required_roles = set(_required_manual_package_signer_roles(signoff_mode))
    if required_roles.issubset(approved_roles):
        return "ready_to_seal"
    return "pending_signoff"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _build_manual_package_signing_payload(
    seal_row: dict,
    signoff_rows: list[dict],
    *,
    finalized_at: str,
    finalized_by_user_id: Optional[str],
    issuer: str,
    key_id: str,
    finalize_metadata: dict[str, object],
) -> dict[str, object]:
    serialized_signoffs = [_serialize_manual_package_signoff_row(row) for row in signoff_rows]
    return {
        "iss": issuer,
        "sub": str(seal_row["id"]),
        "iat": finalized_at,
        "jti": str(uuid.uuid4()),
        "seal_id": str(seal_row["id"]),
        "organization_id": str(seal_row["organization_id"]),
        "package_kind": seal_row["package_kind"],
        "request_id": seal_row["request_id"],
        "report_id": seal_row.get("report_id"),
        "scope_id": seal_row["scope_id"],
        "manual_review_action": seal_row["manual_review_action"],
        "package_sha256": seal_row["package_sha256"],
        "manifest_schema_version": seal_row["manifest_schema_version"],
        "classification": seal_row["classification"],
        "signoff_mode": seal_row["signoff_mode"],
        "policy_version": seal_row["policy_version"],
        "seal_format": "JWS JSON Flattened",
        "key_id": key_id,
        "finalized_at": finalized_at,
        "finalized_by_user_id": finalized_by_user_id,
        "required_signer_roles": list(_required_manual_package_signer_roles(seal_row["signoff_mode"])),
        "signoffs": serialized_signoffs,
        "finalize_metadata": finalize_metadata,
    }


def _verify_local_hs256_jws(
    *,
    envelope: dict[str, object],
    secret: str,
) -> tuple[bool, dict[str, object]]:
    protected = str(envelope.get("protected") or "")
    payload = str(envelope.get("payload") or "")
    signature = str(envelope.get("signature") or "")
    signing_input = f"{protected}.{payload}".encode("ascii")
    expected_signature = _base64url_encode(hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
    verified = hmac.compare_digest(signature, expected_signature)
    payload_dict = json.loads(_base64url_decode(payload).decode("utf-8"))
    return verified, payload_dict


def _seal_manual_package_with_local_hs256(
    *,
    seal_row: dict,
    signoff_rows: list[dict],
    finalized_at: str,
    finalized_by_user_id: Optional[str],
    finalize_metadata: dict[str, object],
) -> dict[str, object]:
    secret = settings.investigation_manual_seal_hs256_secret.strip()
    if not secret:
        raise HTTPException(
            status_code=424,
            detail={
                "code": "manual_seal_secret_missing",
                "message": "configure INVESTIGATION_MANUAL_SEAL_HS256_SECRET para habilitar a selagem local_hs256",
            },
        )

    protected_header = {
        "alg": "HS256",
        "typ": "JWS",
        "cty": "application/json",
        "kid": settings.investigation_manual_seal_key_id,
    }
    payload = _build_manual_package_signing_payload(
        seal_row,
        signoff_rows,
        finalized_at=finalized_at,
        finalized_by_user_id=finalized_by_user_id,
        issuer=settings.investigation_manual_seal_issuer,
        key_id=settings.investigation_manual_seal_key_id,
        finalize_metadata=finalize_metadata,
    )
    protected_b64 = _base64url_encode(_canonical_json_bytes(protected_header))
    payload_b64 = _base64url_encode(_canonical_json_bytes(payload))
    signing_input = f"{protected_b64}.{payload_b64}".encode("ascii")
    signature_b64 = _base64url_encode(hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest())
    envelope = {
        "protected": protected_b64,
        "payload": payload_b64,
        "signature": signature_b64,
        "header": {
            "kid": settings.investigation_manual_seal_key_id,
            "seal_backend": "local_hs256",
        },
    }
    verified, verified_payload = _verify_local_hs256_jws(envelope=envelope, secret=secret)
    verified_signoffs = verified_payload.get("signoffs")
    verified_signoff_count = len(verified_signoffs) if isinstance(verified_signoffs, list) else 0
    verification_summary = {
        "verified": verified,
        "verification_method": "local_hs256_self_check",
        "seal_backend": "local_hs256",
        "signature_algorithm": "HS256",
        "issuer": settings.investigation_manual_seal_issuer,
        "key_id": settings.investigation_manual_seal_key_id,
        "certificate_bundle_ref": settings.investigation_manual_seal_certificate_bundle_ref,
        "certificate_material_present": False,
        "package_sha256": verified_payload.get("package_sha256"),
        "payload_sha256": hashlib.sha256(_canonical_json_bytes(verified_payload)).hexdigest(),
        "signed_at": finalized_at,
        "required_signer_roles": verified_payload.get("required_signer_roles", []),
        "signoff_count": verified_signoff_count,
    }
    return {
        "seal_envelope": envelope,
        "verification_summary": verification_summary,
        "signature_algorithm": "HS256",
        "kms_key_ref": settings.investigation_manual_seal_key_id,
        "certificate_bundle_ref": settings.investigation_manual_seal_certificate_bundle_ref,
        "certificate_fingerprint_sha256": None,
    }


def _finalize_manual_package_with_institutional_seal_service(
    *,
    seal_row: dict,
    signoff_rows: list[dict],
    finalized_at: str,
    finalized_by_user_id: Optional[str],
    finalize_metadata: dict[str, object],
) -> dict[str, object]:
    backend = settings.investigation_manual_seal_backend.strip().lower()
    if backend == "local_hs256":
        return _seal_manual_package_with_local_hs256(
            seal_row=seal_row,
            signoff_rows=signoff_rows,
            finalized_at=finalized_at,
            finalized_by_user_id=finalized_by_user_id,
            finalize_metadata=finalize_metadata,
        )
    raise HTTPException(
        status_code=424,
        detail={
            "code": "institutional_seal_backend_unsupported",
            "message": f"backend de selagem nao suportado: {backend or 'vazio'}",
        },
    )


def _serialize_credit_ledger_row(row: dict) -> dict:
    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    return {
        "id": str(row["id"]),
        "case_id": str(row["case_id"]) if row.get("case_id") else None,
        "action": row["action"],
        "amount": float(row["amount"]) if row.get("amount") is not None else None,
        "balance_after": float(row["balance_after"]) if row.get("balance_after") is not None else None,
        "request_id": metadata.get("request_id"),
        "quote_id": metadata.get("quote_id"),
        "metadata": metadata,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _serialize_billing_action_total_row(row: dict) -> dict:
    return {
        "action": str(row["action"]),
        "entry_count": int(row["entry_count"] or 0),
        "amount_total": float(row["amount_total"] or 0),
    }


def _fetch_billing_balance_row(cur, org_id: str) -> dict:
    cur.execute(
        """
        SELECT credits_available, credits_reserved, credits_used_total
        FROM organizations
        WHERE id = %s
        """,
        (org_id,),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="organization_not_found")
    return row


def _build_billing_balance_payload(row: dict) -> dict[str, float]:
    return {
        "credits_available": float(row["credits_available"]),
        "credits_reserved": float(row["credits_reserved"]),
        "credits_used_total": float(row["credits_used_total"]),
    }


def _fetch_billing_reconciliation_snapshot(cur, *, org_id: str, limit: int) -> dict[str, object]:
    balance_row = _fetch_billing_balance_row(cur, org_id)
    balance = _build_billing_balance_payload(balance_row)

    cur.execute(
        """
        SELECT
          (SELECT COUNT(*) FROM investigation_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at > NOW()) AS investigation_open_total,
          (SELECT COUNT(*) FROM investigation_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at <= NOW()) AS investigation_expired_total,
          (SELECT COUNT(*) FROM compliance_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at > NOW()) AS compliance_open_total,
          (SELECT COUNT(*) FROM compliance_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at <= NOW()) AS compliance_expired_total,
          (SELECT COUNT(*) FROM monitoring_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at > NOW()) AS monitoring_open_total,
          (SELECT COUNT(*) FROM monitoring_quotes WHERE organization_id = %s AND used_at IS NULL AND expires_at <= NOW()) AS monitoring_expired_total
        """,
        (org_id, org_id, org_id, org_id, org_id, org_id),
    )
    quote_row = cur.fetchone() or {}
    quotes_by_domain = {
        "investigation": {
            "open_total": int(quote_row.get("investigation_open_total") or 0),
            "expired_total": int(quote_row.get("investigation_expired_total") or 0),
        },
        "compliance": {
            "open_total": int(quote_row.get("compliance_open_total") or 0),
            "expired_total": int(quote_row.get("compliance_expired_total") or 0),
        },
        "monitoring": {
            "open_total": int(quote_row.get("monitoring_open_total") or 0),
            "expired_total": int(quote_row.get("monitoring_expired_total") or 0),
        },
    }
    quotes_open_total = (
        quotes_by_domain["investigation"]["open_total"]
        + quotes_by_domain["compliance"]["open_total"]
        + quotes_by_domain["monitoring"]["open_total"]
    )
    quotes_expired_total = (
        quotes_by_domain["investigation"]["expired_total"]
        + quotes_by_domain["compliance"]["expired_total"]
        + quotes_by_domain["monitoring"]["expired_total"]
    )

    cur.execute(
        """
        SELECT action, COUNT(*) AS entry_count, COALESCE(SUM(amount), 0) AS amount_total
        FROM credit_ledger
        WHERE org_id = %s
        GROUP BY action
        ORDER BY action ASC
        """,
        (org_id,),
    )
    action_totals = [_serialize_billing_action_total_row(row) for row in cur.fetchall()]

    cur.execute(
        """
        SELECT id, case_id, action, amount, balance_after, metadata, created_at
        FROM credit_ledger
        WHERE org_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (org_id, limit),
    )
    recent = [_serialize_credit_ledger_row(row) for row in cur.fetchall()]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "balance": balance,
        "quotes": {
            "investigation": quotes_by_domain["investigation"],
            "compliance": quotes_by_domain["compliance"],
            "monitoring": quotes_by_domain["monitoring"],
            "open_total": quotes_open_total,
            "expired_total": quotes_expired_total,
        },
        "ledger": {
            "total_entries": sum(entry["entry_count"] for entry in action_totals),
            "action_totals": action_totals,
            "recent": recent,
        },
    }


def _serialize_report_row(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "case_id": str(row["case_id"]) if row.get("case_id") else None,
        "report_id": row.get("external_report_id"),
        "report_type_requested": row.get("report_type_requested"),
        "report_type_canonical": row.get("report_type"),
        "content_type": row.get("content_type"),
        "file_path": row.get("file_path"),
        "file_hash_sha256": row.get("file_hash"),
        "onchain_hash": row.get("onchain_hash"),
        "is_coaf_ready": bool(row.get("is_coaf_ready")) if row.get("is_coaf_ready") is not None else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def _format_evidence_export_filename(export_format: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"ontrackchain-evidence-bundle-{timestamp}.{export_format}"


def _serialize_worker_case_row(row: dict) -> dict:
    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_agent_input = row.get("agent_input")
    agent_input = raw_agent_input if isinstance(raw_agent_input, dict) else {}
    return {
        "case_id": str(row["id"]),
        "status": row["status"],
        "target_address": row["target_address"],
        "target_chain": row["target_chain"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "queue_state": metadata.get("worker_queue_state"),
        "last_error": row.get("error_message") or metadata.get("worker_last_error") or metadata.get("failure_reason"),
        "attempt_count": int(agent_input.get("attempt_count", 0)),
        "report_type_canonical": metadata.get("report_type_canonical"),
        "charged_cost": metadata.get("charged_cost"),
        "duration_ms": int(row["duration_ms"]) if row.get("duration_ms") is not None else None,
    }


def _serialize_dlq_case_row(row: dict, *, credits_available: float) -> dict:
    raw_metadata = row.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_agent_input = row.get("agent_input")
    agent_input = raw_agent_input if isinstance(raw_agent_input, dict) else {}
    estimated_cost = float(row["credits_estimated"])
    return {
        "case_id": str(row["id"]),
        "status": row["status"],
        "target_address": row["target_address"],
        "target_chain": row["target_chain"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
        "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
        "report_type_canonical": metadata.get("report_type_canonical"),
        "failure_reason": metadata.get("failure_reason") or row.get("error_message") or metadata.get("worker_last_error"),
        "dlq_state": metadata.get("dlq_state"),
        "dlq_failed_at": metadata.get("dlq_failed_at") or (row["completed_at"].isoformat() if row.get("completed_at") else None),
        "dlq_requeue_count": int(metadata.get("dlq_requeue_count") or 0),
        "dlq_acknowledged_at": metadata.get("dlq_acknowledged_at"),
        "dlq_acknowledged_by": metadata.get("dlq_acknowledged_by"),
        "dlq_resolution_note": metadata.get("dlq_resolution_note"),
        "attempt_count": int(agent_input.get("attempt_count", 0)),
        "max_attempts": int(agent_input.get("max_attempts", settings.investigation_worker_max_attempts)),
        "credits_estimated": estimated_cost,
        "credits_available": credits_available,
        "can_requeue": credits_available >= estimated_cost,
    }


def _seconds_since(value: Optional[datetime]) -> int:
    if value is None:
        return 0
    delta = datetime.now(timezone.utc) - value
    return max(0, int(delta.total_seconds()))


async def _build_investigation_operations_snapshot(
    *,
    pool: ConnectionPool,
    redis: Redis,
    org_id: str,
    org_plan: str,
) -> dict:
    provider_readiness = describe_rpc_readiness(
        provider_name=settings.investigation_rpc_provider,
        config=_get_rpc_provider_config(),
    )
    org_limit = _concurrency_limit_for_plan(org_plan)
    global_limit = _global_concurrency_limit()
    org_active, global_active = await _get_active_counts(redis, org_id)
    ready_count = await redis.llen(settings.investigation_ready_queue_key)
    waiting_count = await redis.llen(settings.investigation_waiting_queue_key)
    retry_pending = await redis.zcard(settings.investigation_retry_zset_key)
    retry_due = await redis.zcount(
        settings.investigation_retry_zset_key,
        min="-inf",
        max=datetime.now(timezone.utc).timestamp(),
    )
    wake_signals = await redis.llen(settings.investigation_worker_wake_queue_key)

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE status = 'queued') AS queued,
                  COUNT(*) FILTER (WHERE status = 'processing') AS processing,
                  COUNT(*) FILTER (WHERE status = 'failed' AND COALESCE(metadata->>'dlq_state', '') = 'failed_permanent') AS dlq_failed,
                  COUNT(*) FILTER (WHERE status = 'failed' AND COALESCE(metadata->>'dlq_state', '') IN ('acknowledged', 'discarded')) AS dlq_resolved,
                  COUNT(*) FILTER (WHERE status = 'completed' AND completed_at >= NOW() - INTERVAL '1 hour') AS completed_last_hour,
                  COUNT(*) FILTER (WHERE status = 'failed' AND completed_at >= NOW() - INTERVAL '1 hour') AS failed_last_hour,
                  COUNT(*) FILTER (WHERE status = 'billing_recalc_required' AND completed_at >= NOW() - INTERVAL '1 hour') AS billing_recalc_last_hour,
                  MIN(created_at) FILTER (WHERE status = 'queued') AS oldest_queued_created_at,
                  MIN(completed_at) FILTER (
                    WHERE status = 'failed'
                      AND COALESCE(metadata->>'dlq_state', '') = 'failed_permanent'
                  ) AS oldest_dlq_failed_at
                FROM cases
                WHERE case_type = 'investigation'
                """,
            )
            summary = cur.fetchone() or {}

            cur.execute(
                """
                SELECT AVG(duration_ms)::numeric(10,2) AS avg_duration_ms
                FROM (
                  SELECT duration_ms
                  FROM agent_runs
                  WHERE agent_name = 'investigation_executor'
                    AND duration_ms IS NOT NULL
                  ORDER BY completed_at DESC NULLS LAST
                  LIMIT 20
                ) recent_runs
                """,
            )
            duration_row = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                  ) AS manual_package_mfa_violations_last_hour,
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                      AND COALESCE(metadata->>'detail', '') = '2fa_required'
                  ) AS manual_package_mfa_2fa_required_last_hour,
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                      AND COALESCE(metadata->>'detail', '') = 'mfa_not_homologated_for_oidc'
                  ) AS manual_package_mfa_provider_not_homologated_last_hour
                FROM audit_logs
                """,
                (
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                ),
            )
            security_row = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                  c.id,
                  c.status,
                  c.target_address,
                  c.target_chain,
                  c.created_at,
                  c.completed_at,
                  c.metadata,
                  ar.input AS agent_input,
                  ar.error_message,
                  ar.duration_ms
                FROM cases c
                LEFT JOIN agent_runs ar
                  ON ar.case_id = c.id
                 AND ar.agent_name = 'investigation_executor'
                WHERE c.case_type = 'investigation'
                ORDER BY c.created_at DESC, ar.started_at DESC NULLS FIRST, ar.id DESC
                LIMIT 10
                """,
            )
            recent_rows = cur.fetchall()

    return {
        "queue": {
            "ready": int(ready_count),
            "waiting": int(waiting_count),
            "retry_pending": int(retry_pending),
            "retry_due": int(retry_due),
            "wake_signals": int(wake_signals),
        },
        "concurrency": {
            "org_active": int(org_active),
            "org_limit": int(org_limit),
            "global_active": int(global_active),
            "global_limit": int(global_limit),
            "plan": org_plan,
        },
        "throughput": {
            "completed_last_hour": int(summary.get("completed_last_hour") or 0),
            "failed_last_hour": int(summary.get("failed_last_hour") or 0),
            "billing_recalc_last_hour": int(summary.get("billing_recalc_last_hour") or 0),
            "avg_duration_ms_last_20": float(duration_row.get("avg_duration_ms") or 0),
        },
        "states": {
            "queued": int(summary.get("queued") or 0),
            "processing": int(summary.get("processing") or 0),
            "dlq_failed": int(summary.get("dlq_failed") or 0),
            "dlq_resolved": int(summary.get("dlq_resolved") or 0),
        },
        "timing": {
            "oldest_queued_age_seconds": _seconds_since(summary.get("oldest_queued_created_at")),
            "oldest_dlq_age_seconds": _seconds_since(summary.get("oldest_dlq_failed_at")),
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
        "security": {
            "manual_package_mfa_violations_last_hour": int(
                security_row.get("manual_package_mfa_violations_last_hour") or 0
            ),
            "manual_package_mfa_2fa_required_last_hour": int(
                security_row.get("manual_package_mfa_2fa_required_last_hour") or 0
            ),
            "manual_package_mfa_provider_not_homologated_last_hour": int(
                security_row.get("manual_package_mfa_provider_not_homologated_last_hour") or 0
            ),
        },
        "recent_cases": [_serialize_worker_case_row(row) for row in recent_rows],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _build_investigation_platform_snapshot(
    *,
    pool: ConnectionPool,
    redis: Redis,
) -> dict:
    provider_readiness = describe_rpc_readiness(
        provider_name=settings.investigation_rpc_provider,
        config=_get_rpc_provider_config(),
    )
    global_limit = _global_concurrency_limit()
    ready_count = await redis.llen(settings.investigation_ready_queue_key)
    waiting_count = await redis.llen(settings.investigation_waiting_queue_key)
    retry_pending = await redis.zcard(settings.investigation_retry_zset_key)
    retry_due = await redis.zcount(
        settings.investigation_retry_zset_key,
        min="-inf",
        max=datetime.now(timezone.utc).timestamp(),
    )
    wake_signals = await redis.llen(settings.investigation_worker_wake_queue_key)
    global_active_raw = await redis.get(_global_active_counter_key())
    global_active = int(global_active_raw or 0)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (WHERE status = 'queued') AS queued,
                  COUNT(*) FILTER (WHERE status = 'processing') AS processing,
                  COUNT(*) FILTER (WHERE status = 'failed' AND COALESCE(metadata->>'dlq_state', '') = 'failed_permanent') AS dlq_failed,
                  COUNT(*) FILTER (WHERE status = 'failed' AND COALESCE(metadata->>'dlq_state', '') IN ('acknowledged', 'discarded')) AS dlq_resolved,
                  COUNT(*) FILTER (WHERE status = 'completed' AND completed_at >= NOW() - INTERVAL '1 hour') AS completed_last_hour,
                  COUNT(*) FILTER (WHERE status = 'failed' AND completed_at >= NOW() - INTERVAL '1 hour') AS failed_last_hour,
                  COUNT(DISTINCT organization_id) FILTER (
                    WHERE status = 'failed'
                      AND COALESCE(metadata->>'dlq_state', '') = 'failed_permanent'
                  ) AS orgs_with_open_dlq,
                  MIN(created_at) FILTER (WHERE status = 'queued') AS oldest_queued_created_at,
                  MIN(completed_at) FILTER (
                    WHERE status = 'failed'
                      AND COALESCE(metadata->>'dlq_state', '') = 'failed_permanent'
                  ) AS oldest_dlq_failed_at
                FROM cases
                WHERE case_type = 'investigation'
                """,
            )
            summary = cur.fetchone() or {}

            cur.execute(
                """
                SELECT AVG(duration_ms)::numeric(10,2) AS avg_duration_ms
                FROM (
                  SELECT duration_ms
                  FROM agent_runs
                  WHERE agent_name = 'investigation_executor'
                    AND duration_ms IS NOT NULL
                  ORDER BY completed_at DESC NULLS LAST
                  LIMIT 20
                ) recent_runs
                """,
            )
            duration_row = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                  ) AS manual_package_mfa_violations_last_hour,
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                      AND COALESCE(metadata->>'detail', '') = '2fa_required'
                  ) AS manual_package_mfa_2fa_required_last_hour,
                  COUNT(*) FILTER (
                    WHERE action = %s
                      AND created_at >= NOW() - INTERVAL '1 hour'
                      AND COALESCE(metadata->>'detail', '') = 'mfa_not_homologated_for_oidc'
                  ) AS manual_package_mfa_provider_not_homologated_last_hour
                FROM audit_logs
                """,
                (
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                    MANUAL_PACKAGE_MFA_VIOLATION_ACTION,
                ),
            )
            security_row = cur.fetchone() or {}

    return {
        "queue": {
            "ready": int(ready_count),
            "waiting": int(waiting_count),
            "retry_pending": int(retry_pending),
            "retry_due": int(retry_due),
            "wake_signals": int(wake_signals),
        },
        "concurrency": {
            "global_active": int(global_active),
            "global_limit": int(global_limit),
        },
        "throughput": {
            "completed_last_hour": int(summary.get("completed_last_hour") or 0),
            "failed_last_hour": int(summary.get("failed_last_hour") or 0),
            "avg_duration_ms_last_20": float(duration_row.get("avg_duration_ms") or 0),
        },
        "states": {
            "queued": int(summary.get("queued") or 0),
            "processing": int(summary.get("processing") or 0),
            "dlq_failed": int(summary.get("dlq_failed") or 0),
            "dlq_resolved": int(summary.get("dlq_resolved") or 0),
            "orgs_with_open_dlq": int(summary.get("orgs_with_open_dlq") or 0),
        },
        "timing": {
            "oldest_queued_age_seconds": _seconds_since(summary.get("oldest_queued_created_at")),
            "oldest_dlq_age_seconds": _seconds_since(summary.get("oldest_dlq_failed_at")),
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
        "security": {
            "manual_package_mfa_violations_last_hour": int(
                security_row.get("manual_package_mfa_violations_last_hour") or 0
            ),
            "manual_package_mfa_2fa_required_last_hour": int(
                security_row.get("manual_package_mfa_2fa_required_last_hour") or 0
            ),
            "manual_package_mfa_provider_not_homologated_last_hour": int(
                security_row.get("manual_package_mfa_provider_not_homologated_last_hour") or 0
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_investigation_operational_alerts(snapshot: dict) -> list[dict]:
    alerts: list[dict] = []

    def append_alert(*, code: str, severity: str, status: str, metric: str, value: float, threshold: float, title: str, message: str, recommended_action: str) -> None:
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

    waiting = snapshot["queue"]["waiting"]
    retry_due = snapshot["queue"]["retry_due"]
    dlq_failed = snapshot["states"]["dlq_failed"]
    oldest_queued_age = snapshot["timing"]["oldest_queued_age_seconds"]
    oldest_dlq_age = snapshot["timing"]["oldest_dlq_age_seconds"]
    org_active = snapshot["concurrency"]["org_active"]
    org_limit = snapshot["concurrency"]["org_limit"]
    global_active = snapshot["concurrency"]["global_active"]
    global_limit = snapshot["concurrency"]["global_limit"]
    provider_enabled = snapshot["provider"]["enabled"]
    provider_ready = snapshot["provider"]["ready"]
    manual_package_mfa_violations_last_hour = snapshot["security"]["manual_package_mfa_violations_last_hour"]

    append_alert(
        code="investigation_waiting_backlog",
        severity="warning",
        status="open" if waiting >= settings.investigation_alert_waiting_warn_threshold else "closed",
        metric="queue.waiting",
        value=float(waiting),
        threshold=float(settings.investigation_alert_waiting_warn_threshold),
        title="Backlog de waiting",
        message="Fila waiting acima do limiar operacional.",
        recommended_action="Verificar throughput do worker e pressão de concorrência por plano.",
    )
    append_alert(
        code="investigation_retry_due",
        severity="warning",
        status="open" if retry_due >= settings.investigation_alert_retry_due_warn_threshold else "closed",
        metric="queue.retry_due",
        value=float(retry_due),
        threshold=float(settings.investigation_alert_retry_due_warn_threshold),
        title="Retries vencidos",
        message="Existem retries prontos para processamento e ainda não consumidos.",
        recommended_action="Inspecionar worker, wake queue e possíveis falhas de dispatch.",
    )
    append_alert(
        code="investigation_dlq_open",
        severity="critical",
        status="open" if dlq_failed >= settings.investigation_alert_dlq_failed_critical_threshold else "closed",
        metric="states.dlq_failed",
        value=float(dlq_failed),
        threshold=float(settings.investigation_alert_dlq_failed_critical_threshold),
        title="Itens abertos em DLQ",
        message="Há cases em falha permanente aguardando intervenção operacional.",
        recommended_action="Reprocessar, arquivar ou descartar itens da DLQ conforme runbook.",
    )
    append_alert(
        code="investigation_queued_stale",
        severity="warning",
        status="open" if oldest_queued_age >= settings.investigation_alert_oldest_queued_warn_seconds else "closed",
        metric="timing.oldest_queued_age_seconds",
        value=float(oldest_queued_age),
        threshold=float(settings.investigation_alert_oldest_queued_warn_seconds),
        title="Queued envelhecido",
        message="O item mais antigo da fila queued excede o SLA operacional definido.",
        recommended_action="Verificar saturação, locks presos ou capacidade insuficiente do worker.",
    )
    append_alert(
        code="investigation_dlq_stale",
        severity="critical",
        status="open" if oldest_dlq_age >= settings.investigation_alert_oldest_dlq_warn_seconds else "closed",
        metric="timing.oldest_dlq_age_seconds",
        value=float(oldest_dlq_age),
        threshold=float(settings.investigation_alert_oldest_dlq_warn_seconds),
        title="DLQ envelhecida",
        message="Existe item em DLQ aberto há mais tempo do que o permitido operacionalmente.",
        recommended_action="Executar triagem da DLQ e registrar decisão administrativa.",
    )
    append_alert(
        code="investigation_concurrency_saturation",
        severity="warning",
        status="open" if org_active >= org_limit or global_active >= global_limit else "closed",
        metric="concurrency.active",
        value=float(max(org_active, global_active)),
        threshold=float(max(org_limit, global_limit)),
        title="Concorrência saturada",
        message="Os limites de concorrência estão no teto para a organização ou globalmente.",
        recommended_action="Acompanhar filas, revisar limites ou escalonar workers.",
    )
    append_alert(
        code="investigation_rpc_provider_not_ready",
        severity="warning",
        status="open" if provider_enabled and not provider_ready else "closed",
        metric="provider.ready",
        value=1.0 if provider_ready else 0.0,
        threshold=1.0,
        title="Provider RPC não pronto",
        message="O provider RPC habilitado não está pronto para atender o worker de investigação.",
        recommended_action="Validar primary/fallback, fixture mode ou credenciais do provider RPC.",
    )
    append_alert(
        code="investigation_manual_package_mfa_violations",
        severity="warning",
        status="open" if manual_package_mfa_violations_last_hour >= 1 else "closed",
        metric="security.manual_package_mfa_violations_last_hour",
        value=float(manual_package_mfa_violations_last_hour),
        threshold=1.0,
        title="Violações MFA em selagem manual",
        message="Houve violações recentes de MFA no fluxo institucional de manual-package.",
        recommended_action="Revisar a trilha de auditoria do selo e validar headers MFA/2FA no fluxo de signoff.",
    )
    return alerts


def _build_investigation_platform_alerts(snapshot: dict) -> list[dict]:
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

    waiting = snapshot["queue"]["waiting"]
    retry_due = snapshot["queue"]["retry_due"]
    dlq_failed = snapshot["states"]["dlq_failed"]
    oldest_queued_age = snapshot["timing"]["oldest_queued_age_seconds"]
    oldest_dlq_age = snapshot["timing"]["oldest_dlq_age_seconds"]
    global_active = snapshot["concurrency"]["global_active"]
    global_limit = snapshot["concurrency"]["global_limit"]
    provider_enabled = snapshot["provider"]["enabled"]
    provider_ready = snapshot["provider"]["ready"]
    manual_package_mfa_violations_last_hour = snapshot["security"]["manual_package_mfa_violations_last_hour"]

    append_alert(
        code="investigation_waiting_backlog",
        severity="warning",
        status="open" if waiting >= settings.investigation_alert_waiting_warn_threshold else "closed",
        metric="queue.waiting",
        value=float(waiting),
        threshold=float(settings.investigation_alert_waiting_warn_threshold),
        title="Backlog global de waiting",
        message="Fila global waiting acima do limiar operacional.",
        recommended_action="Verificar throughput do worker e pressão de concorrência global.",
    )
    append_alert(
        code="investigation_retry_due",
        severity="warning",
        status="open" if retry_due >= settings.investigation_alert_retry_due_warn_threshold else "closed",
        metric="queue.retry_due",
        value=float(retry_due),
        threshold=float(settings.investigation_alert_retry_due_warn_threshold),
        title="Retries globais vencidos",
        message="Existem retries globais prontos para processamento e ainda não consumidos.",
        recommended_action="Inspecionar worker, wake queue e possíveis falhas de dispatch.",
    )
    append_alert(
        code="investigation_dlq_open",
        severity="critical",
        status="open" if dlq_failed >= settings.investigation_alert_dlq_failed_critical_threshold else "closed",
        metric="states.dlq_failed",
        value=float(dlq_failed),
        threshold=float(settings.investigation_alert_dlq_failed_critical_threshold),
        title="DLQ global aberta",
        message="Há cases em falha permanente aguardando intervenção operacional.",
        recommended_action="Triar a DLQ, reenfileirar itens elegíveis ou encerrar administrativamente.",
    )
    append_alert(
        code="investigation_queued_stale",
        severity="warning",
        status="open" if oldest_queued_age >= settings.investigation_alert_oldest_queued_warn_seconds else "closed",
        metric="timing.oldest_queued_age_seconds",
        value=float(oldest_queued_age),
        threshold=float(settings.investigation_alert_oldest_queued_warn_seconds),
        title="Queued global envelhecido",
        message="O item mais antigo da fila queued excede o SLA operacional global.",
        recommended_action="Verificar saturação, locks presos ou capacidade insuficiente do worker.",
    )
    append_alert(
        code="investigation_dlq_stale",
        severity="critical",
        status="open" if oldest_dlq_age >= settings.investigation_alert_oldest_dlq_warn_seconds else "closed",
        metric="timing.oldest_dlq_age_seconds",
        value=float(oldest_dlq_age),
        threshold=float(settings.investigation_alert_oldest_dlq_warn_seconds),
        title="DLQ global envelhecida",
        message="Existe item em DLQ aberto há mais tempo do que o permitido operacionalmente.",
        recommended_action="Executar triagem da DLQ e registrar decisão administrativa.",
    )
    append_alert(
        code="investigation_concurrency_saturation",
        severity="warning",
        status="open" if global_active >= global_limit else "closed",
        metric="concurrency.global_active",
        value=float(global_active),
        threshold=float(global_limit),
        title="Concorrência global saturada",
        message="O limite global de concorrência do worker foi atingido.",
        recommended_action="Acompanhar filas, revisar limites ou escalar workers.",
    )
    append_alert(
        code="investigation_rpc_provider_not_ready",
        severity="warning",
        status="open" if provider_enabled and not provider_ready else "closed",
        metric="provider.ready",
        value=1.0 if provider_ready else 0.0,
        threshold=1.0,
        title="Provider RPC global não pronto",
        message="O provider RPC habilitado não está pronto na visão global da plataforma.",
        recommended_action="Validar URLs primária/secundária, fixture mode ou indisponibilidade do provider.",
    )
    append_alert(
        code="investigation_manual_package_mfa_violations",
        severity="warning",
        status="open" if manual_package_mfa_violations_last_hour >= 1 else "closed",
        metric="security.manual_package_mfa_violations_last_hour",
        value=float(manual_package_mfa_violations_last_hour),
        threshold=1.0,
        title="Violações globais de MFA em selagem manual",
        message="Houve violações recentes de MFA no fluxo institucional global de manual-package.",
        recommended_action="Revisar audit logs, confirmar homologação MFA/OIDC e validar tentativas recentes de signoff.",
    )
    return alerts


def _render_prometheus_metrics(snapshot: dict, alerts: list[dict]) -> str:
    alert_open_total = sum(1 for alert in alerts if alert["status"] == "open")
    critical_open_total = sum(1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical")
    lines = [
        "# HELP ontrack_investigation_queue_ready Jobs prontos para consumo imediato.",
        "# TYPE ontrack_investigation_queue_ready gauge",
        f"ontrack_investigation_queue_ready {snapshot['queue']['ready']}",
        "# HELP ontrack_investigation_queue_waiting Jobs aguardando promoção.",
        "# TYPE ontrack_investigation_queue_waiting gauge",
        f"ontrack_investigation_queue_waiting {snapshot['queue']['waiting']}",
        "# HELP ontrack_investigation_queue_retry_pending Jobs agendados para retry.",
        "# TYPE ontrack_investigation_queue_retry_pending gauge",
        f"ontrack_investigation_queue_retry_pending {snapshot['queue']['retry_pending']}",
        "# HELP ontrack_investigation_queue_retry_due Jobs com retry vencido.",
        "# TYPE ontrack_investigation_queue_retry_due gauge",
        f"ontrack_investigation_queue_retry_due {snapshot['queue']['retry_due']}",
        "# HELP ontrack_investigation_states_queued Cases em queued.",
        "# TYPE ontrack_investigation_states_queued gauge",
        f"ontrack_investigation_states_queued {snapshot['states']['queued']}",
        "# HELP ontrack_investigation_states_processing Cases em processing.",
        "# TYPE ontrack_investigation_states_processing gauge",
        f"ontrack_investigation_states_processing {snapshot['states']['processing']}",
        "# HELP ontrack_investigation_states_dlq_failed Cases em DLQ aberta.",
        "# TYPE ontrack_investigation_states_dlq_failed gauge",
        f"ontrack_investigation_states_dlq_failed {snapshot['states']['dlq_failed']}",
        "# HELP ontrack_investigation_states_dlq_resolved Cases resolvidos administrativamente na DLQ.",
        "# TYPE ontrack_investigation_states_dlq_resolved gauge",
        f"ontrack_investigation_states_dlq_resolved {snapshot['states']['dlq_resolved']}",
        "# HELP ontrack_investigation_oldest_queued_age_seconds Idade do item mais antigo em queued.",
        "# TYPE ontrack_investigation_oldest_queued_age_seconds gauge",
        f"ontrack_investigation_oldest_queued_age_seconds {snapshot['timing']['oldest_queued_age_seconds']}",
        "# HELP ontrack_investigation_oldest_dlq_age_seconds Idade do item mais antigo em DLQ aberta.",
        "# TYPE ontrack_investigation_oldest_dlq_age_seconds gauge",
        f"ontrack_investigation_oldest_dlq_age_seconds {snapshot['timing']['oldest_dlq_age_seconds']}",
        "# HELP ontrack_investigation_completed_last_hour Cases completed na ultima hora.",
        "# TYPE ontrack_investigation_completed_last_hour gauge",
        f"ontrack_investigation_completed_last_hour {snapshot['throughput']['completed_last_hour']}",
        "# HELP ontrack_investigation_failed_last_hour Cases failed na ultima hora.",
        "# TYPE ontrack_investigation_failed_last_hour gauge",
        f"ontrack_investigation_failed_last_hour {snapshot['throughput']['failed_last_hour']}",
        "# HELP ontrack_investigation_avg_duration_ms_last_20 Media de duracao dos ultimos 20 runs.",
        "# TYPE ontrack_investigation_avg_duration_ms_last_20 gauge",
        f"ontrack_investigation_avg_duration_ms_last_20 {snapshot['throughput']['avg_duration_ms_last_20']}",
        "# HELP ontrack_investigation_provider_supported Estado de suporte do provider RPC configurado.",
        "# TYPE ontrack_investigation_provider_supported gauge",
        f"ontrack_investigation_provider_supported {1 if snapshot['provider']['supported'] else 0}",
        "# HELP ontrack_investigation_provider_enabled Estado de habilitacao do provider RPC configurado.",
        "# TYPE ontrack_investigation_provider_enabled gauge",
        f"ontrack_investigation_provider_enabled {1 if snapshot['provider']['enabled'] else 0}",
        "# HELP ontrack_investigation_provider_configured Estado de configuracao do provider RPC configurado.",
        "# TYPE ontrack_investigation_provider_configured gauge",
        f"ontrack_investigation_provider_configured {1 if snapshot['provider']['configured'] else 0}",
        "# HELP ontrack_investigation_provider_ready Estado de prontidao do provider RPC configurado.",
        "# TYPE ontrack_investigation_provider_ready gauge",
        f"ontrack_investigation_provider_ready {1 if snapshot['provider']['ready'] else 0}",
        "# HELP ontrack_investigation_manual_package_mfa_violations_last_hour Violacoes de MFA em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_manual_package_mfa_violations_last_hour gauge",
        f"ontrack_investigation_manual_package_mfa_violations_last_hour {snapshot['security']['manual_package_mfa_violations_last_hour']}",
        "# HELP ontrack_investigation_manual_package_mfa_2fa_required_last_hour Violacoes por ausencia de 2FA valido em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_manual_package_mfa_2fa_required_last_hour gauge",
        f"ontrack_investigation_manual_package_mfa_2fa_required_last_hour {snapshot['security']['manual_package_mfa_2fa_required_last_hour']}",
        "# HELP ontrack_investigation_manual_package_mfa_provider_not_homologated_last_hour Violacoes por provedor MFA nao homologado em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_manual_package_mfa_provider_not_homologated_last_hour gauge",
        f"ontrack_investigation_manual_package_mfa_provider_not_homologated_last_hour {snapshot['security']['manual_package_mfa_provider_not_homologated_last_hour']}",
        "# HELP ontrack_investigation_operational_alerts_open_total Total de alertas operacionais abertos.",
        "# TYPE ontrack_investigation_operational_alerts_open_total gauge",
        f"ontrack_investigation_operational_alerts_open_total {alert_open_total}",
        "# HELP ontrack_investigation_operational_alerts_critical_open_total Total de alertas criticos abertos.",
        "# TYPE ontrack_investigation_operational_alerts_critical_open_total gauge",
        f"ontrack_investigation_operational_alerts_critical_open_total {critical_open_total}",
    ]
    return "\n".join(lines) + "\n"


def _render_platform_prometheus_metrics(snapshot: dict, alerts: list[dict]) -> str:
    alert_open_total = sum(1 for alert in alerts if alert["status"] == "open")
    critical_open_total = sum(1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical")
    lines = [
        "# HELP ontrack_investigation_platform_queue_ready Jobs prontos para consumo imediato.",
        "# TYPE ontrack_investigation_platform_queue_ready gauge",
        f"ontrack_investigation_platform_queue_ready {snapshot['queue']['ready']}",
        "# HELP ontrack_investigation_platform_queue_waiting Jobs aguardando promoção.",
        "# TYPE ontrack_investigation_platform_queue_waiting gauge",
        f"ontrack_investigation_platform_queue_waiting {snapshot['queue']['waiting']}",
        "# HELP ontrack_investigation_platform_queue_retry_pending Jobs agendados para retry.",
        "# TYPE ontrack_investigation_platform_queue_retry_pending gauge",
        f"ontrack_investigation_platform_queue_retry_pending {snapshot['queue']['retry_pending']}",
        "# HELP ontrack_investigation_platform_queue_retry_due Jobs com retry vencido.",
        "# TYPE ontrack_investigation_platform_queue_retry_due gauge",
        f"ontrack_investigation_platform_queue_retry_due {snapshot['queue']['retry_due']}",
        "# HELP ontrack_investigation_platform_concurrency_global_active Workers ativos globalmente.",
        "# TYPE ontrack_investigation_platform_concurrency_global_active gauge",
        f"ontrack_investigation_platform_concurrency_global_active {snapshot['concurrency']['global_active']}",
        "# HELP ontrack_investigation_platform_concurrency_global_limit Limite global de concorrencia.",
        "# TYPE ontrack_investigation_platform_concurrency_global_limit gauge",
        f"ontrack_investigation_platform_concurrency_global_limit {snapshot['concurrency']['global_limit']}",
        "# HELP ontrack_investigation_platform_states_queued Cases em queued.",
        "# TYPE ontrack_investigation_platform_states_queued gauge",
        f"ontrack_investigation_platform_states_queued {snapshot['states']['queued']}",
        "# HELP ontrack_investigation_platform_states_processing Cases em processing.",
        "# TYPE ontrack_investigation_platform_states_processing gauge",
        f"ontrack_investigation_platform_states_processing {snapshot['states']['processing']}",
        "# HELP ontrack_investigation_platform_states_dlq_failed Cases em DLQ aberta.",
        "# TYPE ontrack_investigation_platform_states_dlq_failed gauge",
        f"ontrack_investigation_platform_states_dlq_failed {snapshot['states']['dlq_failed']}",
        "# HELP ontrack_investigation_platform_states_dlq_resolved Cases resolvidos administrativamente na DLQ.",
        "# TYPE ontrack_investigation_platform_states_dlq_resolved gauge",
        f"ontrack_investigation_platform_states_dlq_resolved {snapshot['states']['dlq_resolved']}",
        "# HELP ontrack_investigation_platform_states_orgs_with_open_dlq_total Organizacoes com ao menos um item aberto em DLQ.",
        "# TYPE ontrack_investigation_platform_states_orgs_with_open_dlq_total gauge",
        f"ontrack_investigation_platform_states_orgs_with_open_dlq_total {snapshot['states']['orgs_with_open_dlq']}",
        "# HELP ontrack_investigation_platform_oldest_queued_age_seconds Idade do item mais antigo em queued.",
        "# TYPE ontrack_investigation_platform_oldest_queued_age_seconds gauge",
        f"ontrack_investigation_platform_oldest_queued_age_seconds {snapshot['timing']['oldest_queued_age_seconds']}",
        "# HELP ontrack_investigation_platform_oldest_dlq_age_seconds Idade do item mais antigo em DLQ aberta.",
        "# TYPE ontrack_investigation_platform_oldest_dlq_age_seconds gauge",
        f"ontrack_investigation_platform_oldest_dlq_age_seconds {snapshot['timing']['oldest_dlq_age_seconds']}",
        "# HELP ontrack_investigation_platform_completed_last_hour Cases completed na ultima hora.",
        "# TYPE ontrack_investigation_platform_completed_last_hour gauge",
        f"ontrack_investigation_platform_completed_last_hour {snapshot['throughput']['completed_last_hour']}",
        "# HELP ontrack_investigation_platform_failed_last_hour Cases failed na ultima hora.",
        "# TYPE ontrack_investigation_platform_failed_last_hour gauge",
        f"ontrack_investigation_platform_failed_last_hour {snapshot['throughput']['failed_last_hour']}",
        "# HELP ontrack_investigation_platform_avg_duration_ms_last_20 Media de duracao dos ultimos 20 runs.",
        "# TYPE ontrack_investigation_platform_avg_duration_ms_last_20 gauge",
        f"ontrack_investigation_platform_avg_duration_ms_last_20 {snapshot['throughput']['avg_duration_ms_last_20']}",
        "# HELP ontrack_investigation_platform_provider_supported Estado de suporte do provider RPC configurado.",
        "# TYPE ontrack_investigation_platform_provider_supported gauge",
        f"ontrack_investigation_platform_provider_supported {1 if snapshot['provider']['supported'] else 0}",
        "# HELP ontrack_investigation_platform_provider_enabled Estado de habilitacao do provider RPC configurado.",
        "# TYPE ontrack_investigation_platform_provider_enabled gauge",
        f"ontrack_investigation_platform_provider_enabled {1 if snapshot['provider']['enabled'] else 0}",
        "# HELP ontrack_investigation_platform_provider_configured Estado de configuracao do provider RPC configurado.",
        "# TYPE ontrack_investigation_platform_provider_configured gauge",
        f"ontrack_investigation_platform_provider_configured {1 if snapshot['provider']['configured'] else 0}",
        "# HELP ontrack_investigation_platform_provider_ready Estado de prontidao do provider RPC configurado.",
        "# TYPE ontrack_investigation_platform_provider_ready gauge",
        f"ontrack_investigation_platform_provider_ready {1 if snapshot['provider']['ready'] else 0}",
        "# HELP ontrack_investigation_platform_manual_package_mfa_violations_last_hour Violacoes globais de MFA em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_platform_manual_package_mfa_violations_last_hour gauge",
        f"ontrack_investigation_platform_manual_package_mfa_violations_last_hour {snapshot['security']['manual_package_mfa_violations_last_hour']}",
        "# HELP ontrack_investigation_platform_manual_package_mfa_2fa_required_last_hour Violacoes globais por ausencia de 2FA valido em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_platform_manual_package_mfa_2fa_required_last_hour gauge",
        f"ontrack_investigation_platform_manual_package_mfa_2fa_required_last_hour {snapshot['security']['manual_package_mfa_2fa_required_last_hour']}",
        "# HELP ontrack_investigation_platform_manual_package_mfa_provider_not_homologated_last_hour Violacoes globais por provedor MFA nao homologado em manual-package/signoffs na ultima hora.",
        "# TYPE ontrack_investigation_platform_manual_package_mfa_provider_not_homologated_last_hour gauge",
        f"ontrack_investigation_platform_manual_package_mfa_provider_not_homologated_last_hour {snapshot['security']['manual_package_mfa_provider_not_homologated_last_hour']}",
        "# HELP ontrack_investigation_platform_operational_alerts_open_total Total de alertas operacionais abertos.",
        "# TYPE ontrack_investigation_platform_operational_alerts_open_total gauge",
        f"ontrack_investigation_platform_operational_alerts_open_total {alert_open_total}",
        "# HELP ontrack_investigation_platform_operational_alerts_critical_open_total Total de alertas criticos abertos.",
        "# TYPE ontrack_investigation_platform_operational_alerts_critical_open_total gauge",
        f"ontrack_investigation_platform_operational_alerts_critical_open_total {critical_open_total}",
    ]
    lines.extend(
        [
            "# HELP ontrack_investigation_platform_operational_alert_status Estado do alerta operacional avaliado pela aplicacao.",
            "# TYPE ontrack_investigation_platform_operational_alert_status gauge",
        ]
    )
    for alert in alerts:
        alert_status = 1 if alert["status"] == "open" else 0
        lines.append(
            "ontrack_investigation_platform_operational_alert_status"
            f'{{code="{alert["code"]}",severity="{alert["severity"]}",metric="{alert["metric"]}"}} {alert_status}'
        )
    return "\n".join(lines) + "\n"


class StartInvestigationRequest(BaseModel):
    quote_id: UUID
    confirmed: bool = False


class StartInvestigationResponse(BaseModel):
    case_id: UUID
    status: str
    estimated_time_seconds: int
    position_in_queue: Optional[int] = None
    concurrency_limited: bool = False
    report_type_requested: str
    report_type_canonical: str
    credits_required: float
    billing_action: str
    supported_scope: list[str]
    depth_requested: int
    applied_depth: int
    plan: str
    warnings: list[dict]


class EvidenceExportRequest(BaseModel):
    format: Literal["json"] = "json"
    request_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    report_id: Optional[str] = None
    resource_id: Optional[UUID] = None
    limit: int = Field(default=200, ge=1, le=500)
    include_audit_logs: bool = True
    include_credit_ledger: bool = True
    include_reports: bool = False


class ManualPackageAuditRequest(BaseModel):
    action: Literal["evidence_manual_review_package_exported"] = MANUAL_PACKAGE_EXPORT_AUDIT_ACTION
    resource_type: str = "audit_log"
    resource_id: Optional[str] = None
    request_id: Optional[str] = None
    report_id: Optional[str] = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ManualPackageSignoffRequestCreate(BaseModel):
    request_id: str
    report_id: Optional[str] = None
    scope_id: str
    manual_review_action: Literal[
        "compliance_due_diligence_checked",
        "compliance_source_of_funds_checked",
    ]
    package_sha256: str = Field(min_length=64, max_length=64)
    manifest_schema_version: str = "manual_review_package/v2"
    classification: str = "restricted_regulatory"
    signoff_mode: str = "compliance_ops_signoff"
    package_kind: str = "manual_review_package"
    policy_version: str = "manual_package_sealing/v1"


class ManualPackageSignoffRecordRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    signer_role: Literal["compliance_owner", "ops_owner", "legal_owner_optional"]
    signoff_method: Literal["platform_authenticated_2fa", "governance_ticket"]
    ticket_ref: Optional[str] = None
    notes: Optional[str] = None
    signer_display_name: Optional[str] = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ManualPackageFinalizeRequest(BaseModel):
    metadata: dict[str, object] = Field(default_factory=dict)


class ManualPackageRevokeRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    ticket_ref: str = Field(min_length=3, max_length=120)
    metadata: dict[str, object] = Field(default_factory=dict)


class ManualPackageSupersedeRequest(BaseModel):
    superseded_by_seal_id: UUID
    reason: str = Field(min_length=3, max_length=500)
    ticket_ref: str = Field(min_length=3, max_length=120)
    metadata: dict[str, object] = Field(default_factory=dict)


class RequoteRequiredResponse(BaseModel):
    status: str
    message: str
    original_quote: dict
    new_quote: dict
    action_required: str
    note: str


class EstimateInvestigationRequest(BaseModel):
    address: str
    chains: list[str] = Field(default_factory=lambda: ["ethereum"])
    depth: int = Field(default=3, ge=1, le=10)
    report_type: str = "technical_basic"
    addons: list[str] = Field(default_factory=list)


class EstimateInvestigationResponse(BaseModel):
    quote_id: UUID
    expires_at: str
    report_type_requested: str
    report_type_canonical: str
    breakdown: list[dict]
    subtotal_credits: float
    plan_discount: float
    total_credits: float
    total_brl_estimate: float
    credits_available: float
    can_proceed: bool
    calculation_version: str
    pricing_table_hash: str
    depth_requested: int
    depth_applied: int
    plan: str
    warnings: list[dict]
    legal_notice: str


def _concurrency_limit_for_plan(plan: str) -> int:
    return int(CONCURRENCY_LIMITS_MVP.get(plan, 1))


def _global_concurrency_limit() -> int:
    return int(CONCURRENCY_LIMITS_MVP.get("global_max_concurrent_investigations", 10))


class ReportTypeCatalogItem(BaseModel):
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


class ReportTypeCatalogResponse(BaseModel):
    plan: str
    total: int
    generated_at: str
    types: list[ReportTypeCatalogItem]
    note_deprecated: str


class FinalizeCaseRequest(BaseModel):
    credits_used: Optional[float] = None
    reason: Optional[str] = None


class RequeueCaseRequest(BaseModel):
    reason: Optional[str] = None


class DlqResolutionRequest(BaseModel):
    action: Literal["acknowledged", "discarded"]
    note: Optional[str] = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/report-types", response_model=ReportTypeCatalogResponse)
async def get_report_types_catalog(
    include_deprecated: bool = Query(default=False),
    include_unavailable: bool = Query(default=False),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> ReportTypeCatalogResponse:
    plan = _normalize_plan(x_plan or "professional")
    catalog = [
        _build_report_type_detail(canonical, plan, include_deprecated)
        for canonical in PRICING_TABLE["report_type_cost"].keys()
    ]
    if not include_unavailable:
        catalog = [item for item in catalog if item["available"]]

    return ReportTypeCatalogResponse(
        plan=plan,
        total=len(catalog),
        generated_at=datetime.now(timezone.utc).isoformat(),
        types=[ReportTypeCatalogItem(**item) for item in catalog],
        note_deprecated=(
            "aliases_accepted sao aceitos para compatibilidade retroativa. "
            "deprecated_aliases serao removidos em v2 (Jan/2027). Migre para os canonicos."
        ),
    )


@app.get("/api/v1/report-types/{type_identifier}", response_model=ReportTypeCatalogItem)
async def get_report_type_detail(
    type_identifier: str,
    include_deprecated: bool = Query(default=True),
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> ReportTypeCatalogItem:
    plan = _normalize_plan(x_plan or "professional")
    canonical, _ = _resolve_report_type(type_identifier)
    return ReportTypeCatalogItem(**_build_report_type_detail(canonical, plan, include_deprecated))


@app.post("/api/v1/investigation/estimate", response_model=EstimateInvestigationResponse)
async def estimate_investigation(
    body: EstimateInvestigationRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
) -> EstimateInvestigationResponse:
    org_id = _require_org_id(x_org_id)
    plan = _normalize_plan(x_plan or "professional")
    effective_user_id, _ = _resolve_actor_ids(external_user_id=x_user_id, linked_user_id=x_linked_user_id)

    chains = [_validate_chain(c) for c in body.chains]
    if not chains:
        raise HTTPException(status_code=422, detail="no_chains_provided")
    quote_payload = _build_quote_payload(
        address=body.address,
        chains=chains,
        requested_depth=body.depth,
        report_type_requested=body.report_type,
        addons=body.addons,
        plan=plan,
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT credits_available FROM organizations WHERE id = %s",
                (org_id,),
            )
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")
            available = float(org["credits_available"])
            _persist_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=quote_payload)
        conn.commit()

    return EstimateInvestigationResponse(
        quote_id=quote_payload["quote_id"],
        expires_at=quote_payload["expires_at"].isoformat(),
        report_type_requested=quote_payload["report_type_requested"],
        report_type_canonical=quote_payload["report_type_canonical"],
        breakdown=quote_payload["breakdown"],
        subtotal_credits=quote_payload["subtotal_credits"],
        plan_discount=quote_payload["plan_discount"],
        total_credits=quote_payload["total_credits"],
        total_brl_estimate=quote_payload["total_brl_estimate"],
        credits_available=available,
        can_proceed=available >= quote_payload["total_credits"],
        calculation_version=quote_payload["calculation_version"],
        pricing_table_hash=quote_payload["pricing_table_hash"],
        depth_requested=quote_payload["depth_requested"],
        depth_applied=quote_payload["depth_applied"],
        plan=plan,
        warnings=quote_payload["warnings"],
        legal_notice=(
            "Valores baseados na tabela de pricing v1.0. O débito final pode variar ±10% por complexidade "
            "de execução (Art. 62 Res. 520 BCB)."
        ),
    )


@app.post("/api/v1/investigation/start", response_model=StartInvestigationResponse)
async def start_investigation(
    body: StartInvestigationRequest,
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> StartInvestigationResponse:
    org_id = _require_org_id(x_org_id)
    if not body.confirmed:
        raise HTTPException(status_code=412, detail="quote_confirmation_required")

    plan = _normalize_plan(x_plan or "professional")
    request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    now = datetime.now(timezone.utc)
    warnings: list[dict] = []
    worker_payload: Optional[dict] = None

    async with redis.lock(settings.investigation_dispatch_lock_key, timeout=10):
        org_active, global_active = await _get_active_counts(redis, org_id)
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM investigation_quotes
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
                            "action": "Solicite um novo quote via POST /api/v1/investigation/estimate",
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
                            "requote_url": "/api/v1/investigation/estimate",
                        },
                    )

                estimated_cost = float(quote_row["total_credits"])
                applied_depth = int(quote_row["applied_depth"])
                requested_depth = int(quote_row["requested_depth"])
                primary_chain = str(quote_row["chains"][0])
                quote_plan = _normalize_plan(str(quote_row["plan_snapshot"]))
                _, depth_warning = _get_depth_cap(primary_chain, quote_plan, requested_depth)
                if depth_warning:
                    warnings.append(depth_warning)
                alias_warning = None
                if str(quote_row["report_type_requested"]) != str(quote_row["report_type"]):
                    alias_warning = {
                        "warning": "report_type_alias_resolved",
                        "requested": str(quote_row["report_type_requested"]),
                        "canonical": str(quote_row["report_type"]),
                    }
                if alias_warning:
                    warnings.append(alias_warning)

                if plan != quote_plan:
                    if _plan_rank(plan) < _plan_rank(quote_plan):
                        raise HTTPException(
                            status_code=402,
                            detail={
                                "error": "plan_downgraded_since_quote",
                                "message": (
                                    f"O quote foi emitido no plano {quote_plan.upper()} mas o plano atual e "
                                    f"{plan.upper()}. Este tipo de relatorio nao esta disponivel no plano atual."
                                ),
                                "quote_plan": quote_plan,
                                "current_plan": plan,
                                "report_type": str(quote_row["report_type"]),
                                "action": (
                                    f"Opcoes: (1) Faca upgrade para {quote_plan.upper()} e tente novamente, "
                                    "(2) Solicite um novo quote compativel com o plano atual."
                                ),
                                "upgrade_url": "/billing/upgrade",
                                "requote_url": "/api/v1/investigation/estimate",
                            },
                        )

                    new_quote_payload = _build_quote_payload(
                        address=str(quote_row["target_address"]),
                        chains=list(quote_row["chains"]),
                        requested_depth=requested_depth,
                        report_type_requested=str(quote_row["report_type_requested"]),
                        addons=list(quote_row["addons"]),
                        plan=plan,
                    )
                    _persist_quote(cur, org_id=org_id, user_id=effective_user_id, quote_payload=new_quote_payload)
                    conn.commit()
                    return JSONResponse(
                        status_code=202,
                        content=RequoteRequiredResponse(
                            status="requote_required",
                            message=(
                                f"Seu plano foi atualizado para {plan.upper()} desde a emissao do quote. "
                                "Um novo quote foi calculado."
                            ),
                            original_quote={
                                "quote_id": str(quote_row["id"]),
                                "plan_snapshot": quote_plan,
                                "report_type_requested": str(quote_row["report_type_requested"]),
                                "report_type_canonical": str(quote_row["report_type"]),
                                "total_credits": estimated_cost,
                                "expires_at": quote_row["expires_at"].isoformat(),
                            },
                            new_quote={
                                "quote_id": str(new_quote_payload["quote_id"]),
                                "plan_snapshot": new_quote_payload["plan"],
                                "report_type_requested": new_quote_payload["report_type_requested"],
                                "report_type_canonical": new_quote_payload["report_type_canonical"],
                                "total_credits": new_quote_payload["total_credits"],
                                "expires_at": new_quote_payload["expires_at"].isoformat(),
                                "depth_requested": new_quote_payload["depth_requested"],
                                "depth_applied": new_quote_payload["depth_applied"],
                                "warnings": new_quote_payload["warnings"],
                            },
                            action_required="Confirme o novo quote via POST /api/v1/investigation/start",
                            note="O preco pode ter mudado conforme a tabela do novo plano.",
                        ).model_dump(),
                    )

                if not _is_report_type_available(str(quote_row["report_type"]), plan):
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "report_type_not_available_on_plan",
                            "report_type": str(quote_row["report_type"]),
                            "required_plan": _required_plan_for_report_type(str(quote_row["report_type"])),
                            "current_plan": plan,
                        },
                    )

                cur.execute(
                    """
                    SELECT id, credits_available, credits_reserved, credits_used_total
                    FROM organizations
                    WHERE id = %s
                    """,
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

                per_plan_limit = _concurrency_limit_for_plan(plan)
                global_limit = _global_concurrency_limit()
                concurrency_limited = org_active >= per_plan_limit or global_active >= global_limit
                queue_position = None
                case_status = "processing"
                if concurrency_limited:
                    case_status = "queued"
                    queued_len = await redis.llen(settings.investigation_waiting_queue_key)
                    queue_position = int(queued_len) + 1
                    warnings.append(
                        {
                            "warning": "concurrency_limited",
                            "org_active": org_active,
                            "org_limit": per_plan_limit,
                            "global_active": global_active,
                            "global_limit": global_limit,
                            "queue_position": queue_position,
                        }
                    )

                new_available = round(float(org["credits_available"]) - estimated_cost, 4)
                new_reserved = round(float(org["credits_reserved"]) + estimated_cost, 4)
                cur.execute(
                    """
                    UPDATE organizations
                    SET credits_available = %s, credits_reserved = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (new_available, new_reserved, org_id),
                )
                persisted_user_id = _resolve_persisted_user_id(cur, effective_user_id)
                cur.execute(
                    """
                    INSERT INTO cases (
                      organization_id, user_id, title, case_type, status,
                      target_address, target_chain, depth, context_narrative,
                      credits_estimated, created_at, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        org_id,
                        persisted_user_id,
                        f"Investigation {quote_row['target_address']}",
                        "investigation",
                        case_status,
                        quote_row["target_address"],
                        quote_row["chains"][0],
                        applied_depth,
                        None,
                        estimated_cost,
                        now,
                        json.dumps(
                            {
                                "quote_id": str(body.quote_id),
                                "pricing_table_hash": quote_row["pricing_table_hash"],
                                "calculation_version": quote_row["calculation_version"],
                                "requested_by_role": x_role or "UNKNOWN",
                                "external_user_id": (
                                    external_actor_user_id
                                    if external_actor_user_id
                                    else (effective_user_id if effective_user_id and not persisted_user_id else None)
                                ),
                                "billing_mode": "pre_hold_confirm_refund",
                                "org_plan": plan,
                                "report_type_requested": quote_row["report_type_requested"],
                                "report_type_canonical": quote_row["report_type"],
                                "processing_mode": "redis_async_worker_v1",
                                "worker_queue_state": case_status,
                            }
                        ),
                    ),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=500, detail="failed_to_create_case")
                _record_agent_run(cur, case_id=row["id"], request_id=request_id)
                _record_audit_log(
                    cur,
                    organization_id=org_id,
                    user_id=effective_user_id,
                    action="case_started",
                    resource_type="case",
                    resource_id=row["id"],
                    metadata={
                        "request_id": request_id,
                        "case_type": "investigation",
                        "status": case_status,
                        "concurrency_limited": concurrency_limited,
                        "queue_position": queue_position,
                        "credits_estimated": estimated_cost,
                        "quote_id": str(body.quote_id),
                        "report_type_requested": str(quote_row["report_type_requested"]),
                        "report_type_canonical": str(quote_row["report_type"]),
                        "processing_mode": "redis_async_worker_v1",
                        "external_user_id": external_actor_user_id,
                    },
                )
                _record_credit_ledger(
                    cur,
                    org_id=org_id,
                    case_id=row["id"],
                    action="PRE_HOLD",
                    amount=estimated_cost,
                    balance_after=new_available,
                    metadata={
                        "request_id": request_id,
                        "quote_id": str(body.quote_id),
                        "report_type_requested": str(quote_row["report_type_requested"]),
                        "report_type_canonical": str(quote_row["report_type"]),
                        "chains": quote_row["chains"],
                        "requested_depth": int(quote_row["requested_depth"]),
                        "applied_depth": applied_depth,
                        "auth_role": x_role,
                        "processing_mode": "redis_async_worker_v1",
                    },
                )
                cur.execute(
                    """
                    UPDATE investigation_quotes
                    SET used_at = NOW(), used_for_case_id = %s
                    WHERE id = %s
                    """,
                    (row["id"], body.quote_id),
                )
            conn.commit()

        worker_payload = {
            "case_id": str(row["id"]),
            "org_id": org_id,
            "request_id": request_id,
            "plan": plan,
            "status": case_status,
            "quote_id": str(body.quote_id),
        }
        if not concurrency_limited:
            await _increment_active_counters(redis, org_id)
        await _enqueue_case_for_worker(redis, worker_payload, immediate=not concurrency_limited)

    response = StartInvestigationResponse(
        case_id=row["id"],
        status=case_status,
        estimated_time_seconds=120,
        position_in_queue=queue_position,
        concurrency_limited=concurrency_limited,
        report_type_requested=str(quote_row["report_type_requested"]),
        report_type_canonical=str(quote_row["report_type"]),
        credits_required=estimated_cost,
        billing_action="PRE_HOLD",
        supported_scope=sorted(SUPPORTED_BASIC_CHAINS),
        depth_requested=requested_depth,
        applied_depth=applied_depth,
        plan=plan,
        warnings=warnings,
    )
    if concurrency_limited:
        return JSONResponse(status_code=202, content=response.model_dump(mode="json"))
    return response


@app.get("/api/v1/investigation/{case_id}/status")
async def get_status(
    case_id: UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT c.status, c.created_at, c.completed_at, c.metadata, ar.agent_name, ar.status AS agent_status, ar.input, ar.error_message
                FROM cases c
                LEFT JOIN agent_runs ar
                  ON ar.case_id = c.id
                 AND ar.agent_name = 'investigation_executor'
                WHERE c.id = %s
                ORDER BY ar.started_at DESC NULLS FIRST, ar.id DESC
                LIMIT 1
                """,
                (case_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="case_not_found")

    case_status = row["status"]
    agent_status = row.get("agent_status")
    metadata = row.get("metadata") or {}
    progress_by_status = {
        "queued": 10,
        "processing": 65 if agent_status == "running" else 35,
        "completed": 100,
        "failed": 100,
        "billing_recalc_required": 100,
    }
    agents_completed = []
    agents_pending = []
    current_agent = None
    if row.get("agent_name"):
        if agent_status == "completed":
            agents_completed = [row["agent_name"]]
        elif agent_status in {"pending", "running"}:
            agents_pending = [row["agent_name"]]
        if agent_status == "running":
            current_agent = row["agent_name"]

    return {
        "status": case_status,
        "progress_pct": progress_by_status.get(case_status, 0),
        "agents_completed": agents_completed,
        "agents_pending": agents_pending,
        "current_agent": current_agent,
        "queue_state": metadata.get("worker_queue_state"),
        "last_error": row.get("error_message"),
    }


@app.get("/api/v1/investigation/{case_id}/result")
async def get_result(
    case_id: UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  c.id,
                  c.status,
                  c.target_address,
                  c.target_chain,
                  c.credits_estimated,
                  c.credits_used,
                  c.created_at,
                  c.completed_at,
                  c.metadata,
                  ar.output AS agent_output
                FROM cases
                c
                LEFT JOIN agent_runs ar
                  ON ar.case_id = c.id
                 AND ar.agent_name = 'investigation_executor'
                WHERE c.id = %s
                ORDER BY ar.completed_at DESC NULLS LAST, ar.id DESC
                LIMIT 1
                """,
                (case_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="case_not_found")

    agent_output = row.get("agent_output") or {}
    metadata = row.get("metadata") or {}
    worker_result = metadata.get("worker_last_result") if isinstance(metadata, dict) else None
    result_payload = worker_result if isinstance(worker_result, dict) else agent_output

    return {
        "case_id": str(row["id"]),
        "status": row["status"],
        "risk_score": result_payload.get("risk_score"),
        "risk_level": result_payload.get("risk_level"),
        "patterns_detected": result_payload.get("patterns_detected", []),
        "kyw_summary": result_payload.get("kyw_summary", {}),
        "credits_estimated": float(row["credits_estimated"]),
        "credits_used": float(row["credits_used"]),
        "report_url": result_payload.get("report_url"),
        "report_hash": result_payload.get("report_hash"),
        "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
    }


@app.get("/api/v1/investigation/history")
async def history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    chain: Optional[str] = None,
    status: Optional[str] = None,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    offset = (page - 1) * limit
    where = []
    params: list[object] = []

    if chain:
        where.append("target_chain = %s")
        params.append(chain)
    if status:
        where.append("status = %s")
        params.append(status)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, status, target_address, target_chain, created_at, completed_at
                FROM cases
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, offset),
            )
            rows = cur.fetchall()

    return {"page": page, "limit": limit, "data": rows}


@app.get("/api/v1/billing/balance")
async def billing_balance(
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
    _require_billing_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=org_id,
        endpoint="/api/v1/billing/balance",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            row = _fetch_billing_balance_row(cur, org_id)
    return _build_billing_balance_payload(row)


@app.get("/api/v1/billing/reconciliation")
async def billing_reconciliation(
    limit: int = Query(default=10, ge=1, le=25),
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
    _require_billing_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=request_id,
        x_role=x_role,
        resource_id=org_id,
        endpoint="/api/v1/billing/reconciliation",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            return _fetch_billing_reconciliation_snapshot(cur, org_id=org_id, limit=limit)


@app.get("/api/v1/investigation/admin/operations")
async def investigation_operations(
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
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
        detail="privileged_read_role_required",
        resource_type="investigation_operations",
        resource_id=None,
        endpoint="/api/v1/investigation/admin/operations",
        method="GET",
    )

    org_plan = _normalize_plan(x_plan or "professional")
    return await _build_investigation_operations_snapshot(pool=pool, redis=redis, org_id=org_id, org_plan=org_plan)


@app.get("/api/v1/investigation/admin/alerts")
async def investigation_operational_alerts(
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
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
        detail="privileged_read_role_required",
        resource_type="investigation_alerts",
        resource_id=None,
        endpoint="/api/v1/investigation/admin/alerts",
        method="GET",
    )

    snapshot = await _build_investigation_operations_snapshot(
        pool=pool,
        redis=redis,
        org_id=org_id,
        org_plan=_normalize_plan(x_plan or "professional"),
    )
    alerts = _build_investigation_operational_alerts(snapshot)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "open_total": sum(1 for alert in alerts if alert["status"] == "open"),
        "critical_open_total": sum(
            1 for alert in alerts if alert["status"] == "open" and alert["severity"] == "critical"
        ),
        "alerts": alerts,
    }


@app.get("/api/v1/investigation/admin/metrics")
async def investigation_prometheus_metrics(
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
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
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="privileged_read_role_required",
        resource_type="investigation_metrics",
        resource_id=None,
        endpoint="/api/v1/investigation/admin/metrics",
        method="GET",
    )

    snapshot = await _build_investigation_operations_snapshot(
        pool=pool,
        redis=redis,
        org_id=org_id,
        org_plan=_normalize_plan(x_plan or "professional"),
    )
    alerts = _build_investigation_operational_alerts(snapshot)
    return Response(content=_render_prometheus_metrics(snapshot, alerts), media_type="text/plain; version=0.0.4")


@app.get("/internal/metrics/prometheus")
async def internal_investigation_prometheus_metrics(
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
) -> Response:
    if not settings.investigation_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    snapshot = await _build_investigation_platform_snapshot(pool=pool, redis=redis)
    alerts = _build_investigation_platform_alerts(snapshot)
    return Response(content=_render_platform_prometheus_metrics(snapshot, alerts), media_type="text/plain; version=0.0.4")


@app.get("/internal/rpc-readiness")
async def internal_investigation_rpc_readiness() -> dict:
    if not settings.investigation_internal_metrics_enabled:
        raise HTTPException(status_code=404, detail="internal_metrics_disabled")

    readiness = describe_rpc_readiness(
        provider_name=settings.investigation_rpc_provider,
        config=_get_rpc_provider_config(),
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


@app.get("/api/v1/investigation/admin/dlq")
async def investigation_dlq(
    state: str = Query(default="failed_permanent"),
    target_chain: Optional[str] = Query(default=None),
    can_requeue: Optional[bool] = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
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
        detail="privileged_read_role_required",
        resource_type="investigation_dlq",
        resource_id=None,
        endpoint="/api/v1/investigation/admin/dlq",
        method="GET",
    )
    normalized_state = (state or "failed_permanent").strip().lower()
    if normalized_state not in {"failed_permanent", "acknowledged", "discarded", "resolved", "all"}:
        raise HTTPException(status_code=422, detail="invalid_dlq_state_filter")

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT credits_available
                FROM organizations
                WHERE id = %s
                """,
                (org_id,),
            )
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")
            credits_available = float(org["credits_available"])

            cur.execute(
                """
                SELECT
                  c.id,
                  c.status,
                  c.target_address,
                  c.target_chain,
                  c.created_at,
                  c.completed_at,
                  c.credits_estimated,
                  c.metadata,
                  ar.input AS agent_input,
                  ar.error_message
                FROM cases c
                LEFT JOIN agent_runs ar
                  ON ar.case_id = c.id
                 AND ar.agent_name = 'investigation_executor'
                WHERE c.case_type = 'investigation'
                  AND c.status = 'failed'
                  AND COALESCE(c.metadata->>'dlq_state', '') <> ''
                ORDER BY c.completed_at DESC NULLS LAST, c.created_at DESC
                LIMIT 100
                """,
            )
            rows = cur.fetchall()

    serialized = [_serialize_dlq_case_row(row, credits_available=credits_available) for row in rows]
    if normalized_state == "resolved":
        serialized = [entry for entry in serialized if entry["dlq_state"] in {"acknowledged", "discarded"}]
    elif normalized_state != "all":
        serialized = [entry for entry in serialized if entry["dlq_state"] == normalized_state]
    if target_chain:
        normalized_chain = _normalize_chain(target_chain)
        serialized = [entry for entry in serialized if entry["target_chain"] == normalized_chain]
    if can_requeue is not None:
        serialized = [entry for entry in serialized if bool(entry["can_requeue"]) is can_requeue]
    serialized = serialized[:limit]

    return {
        "count": len(serialized),
        "credits_available": credits_available,
        "filters": {
            "state": normalized_state,
            "target_chain": _normalize_chain(target_chain) if target_chain else None,
            "can_requeue": can_requeue,
            "limit": limit,
        },
        "cases": serialized,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/investigation/admin/dlq/{case_id}/requeue")
async def requeue_dlq_case(
    case_id: UUID,
    body: RequeueCaseRequest,
    pool: ConnectionPool = Depends(get_pool),
    redis: Redis = Depends(get_redis),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_plan: Annotated[Optional[str], Header(alias="X-Plan")] = None,
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
        allowed_roles={"ADMIN"},
        detail="admin_required",
        resource_type="case",
        resource_id=case_id,
        endpoint="/api/v1/investigation/admin/dlq/{case_id}/requeue",
        method="POST",
    )
    plan = _normalize_plan(x_plan or "professional")

    async with redis.lock(settings.investigation_dispatch_lock_key, timeout=10):
        org_active, global_active = await _get_active_counts(redis, org_id)
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      c.id,
                      c.status,
                      c.case_type,
                      c.target_address,
                      c.target_chain,
                      c.credits_estimated,
                      c.metadata,
                      ar.input AS agent_input
                    FROM cases c
                    LEFT JOIN agent_runs ar
                      ON ar.case_id = c.id
                     AND ar.agent_name = 'investigation_executor'
                    WHERE c.id = %s
                    """,
                    (case_id,),
                )
                case_row = cur.fetchone()
                if not case_row:
                    raise HTTPException(status_code=404, detail="case_not_found")
                if case_row["case_type"] != "investigation":
                    raise HTTPException(status_code=409, detail="invalid_case_type_for_requeue")
                if case_row["status"] != "failed":
                    raise HTTPException(status_code=409, detail="case_not_in_dlq")

                raw_metadata = case_row.get("metadata")
                metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
                if metadata.get("dlq_state") != "failed_permanent":
                    raise HTTPException(status_code=409, detail="case_not_in_dlq")

                report_type_canonical = str(metadata.get("report_type_canonical") or "technical_basic")
                if not _is_report_type_available(report_type_canonical, plan):
                    raise HTTPException(
                        status_code=403,
                        detail={
                            "error": "report_type_not_available_on_plan",
                            "report_type": report_type_canonical,
                            "required_plan": _required_plan_for_report_type(report_type_canonical),
                            "current_plan": plan,
                        },
                    )

                cur.execute(
                    """
                    SELECT credits_available, credits_reserved
                    FROM organizations
                    WHERE id = %s
                    """,
                    (org_id,),
                )
                org = cur.fetchone()
                if not org:
                    raise HTTPException(status_code=404, detail="organization_not_found")

                estimated_cost = round(float(case_row["credits_estimated"]), 4)
                if float(org["credits_available"]) < estimated_cost:
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "insufficient_credits_for_requeue",
                            "credits_required": estimated_cost,
                            "credits_available": float(org["credits_available"]),
                        },
                    )

                per_plan_limit = _concurrency_limit_for_plan(plan)
                global_limit = _global_concurrency_limit()
                concurrency_limited = org_active >= per_plan_limit or global_active >= global_limit
                queue_position = None
                case_status = "processing"
                if concurrency_limited:
                    case_status = "queued"
                    queued_len = await redis.llen(settings.investigation_waiting_queue_key)
                    queue_position = int(queued_len) + 1

                new_available = round(float(org["credits_available"]) - estimated_cost, 4)
                new_reserved = round(float(org["credits_reserved"]) + estimated_cost, 4)
                cur.execute(
                    """
                    UPDATE organizations
                    SET credits_available = %s, credits_reserved = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (new_available, new_reserved, org_id),
                )

                requeue_count = int(metadata.get("dlq_requeue_count") or 0) + 1
                failure_reason = metadata.get("failure_reason") or "unknown_error"
                cur.execute(
                    """
                    UPDATE cases
                    SET status = %s,
                        completed_at = NULL,
                        credits_used = 0,
                        metadata = jsonb_strip_nulls(COALESCE(metadata, '{}'::jsonb) || %s::jsonb)
                    WHERE id = %s
                    """,
                    (
                        case_status,
                        json.dumps(
                            {
                                "worker_queue_state": case_status,
                                "worker_last_error": None,
                                "worker_next_retry_at": None,
                                "failure_reason": None,
                                "dlq_state": "requeued",
                                "dlq_last_failure_reason": failure_reason,
                                "dlq_requeue_count": requeue_count,
                                "dlq_requeued_at": datetime.now(timezone.utc).isoformat(),
                                "dlq_requeued_by": effective_user_id or "admin",
                                "dlq_requeued_external_user_id": external_actor_user_id,
                                "org_plan": plan,
                            }
                        ),
                        case_id,
                    ),
                )
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'pending',
                        started_at = NULL,
                        completed_at = NULL,
                        error_message = NULL,
                        output = NULL,
                        duration_ms = NULL,
                        input = jsonb_strip_nulls((COALESCE(input, '{}'::jsonb) - 'last_error') || %s::jsonb)
                    WHERE case_id = %s
                      AND agent_name = 'investigation_executor'
                    """,
                    (
                        json.dumps(
                            {
                                "attempt_count": 0,
                                "requeue_request_id": request_id,
                                "manual_requeue_reason": body.reason or "manual_dlq_requeue",
                            }
                        ),
                        case_id,
                    ),
                )
                _record_credit_ledger(
                    cur,
                    org_id=org_id,
                    case_id=case_id,
                    action="PRE_HOLD",
                    amount=estimated_cost,
                    balance_after=new_available,
                    metadata={
                        "request_id": request_id,
                        "reason": body.reason or "manual_dlq_requeue",
                        "requeue_count": requeue_count,
                        "report_type_canonical": report_type_canonical,
                    },
                )
                _record_audit_log(
                    cur,
                    organization_id=org_id,
                    user_id=effective_user_id,
                    action="case_requeued_from_dlq",
                    resource_type="case",
                    resource_id=case_id,
                    metadata={
                        "request_id": request_id,
                        "reason": body.reason or "manual_dlq_requeue",
                        "requeue_count": requeue_count,
                        "status": case_status,
                        "queue_position": queue_position,
                        "credits_estimated": estimated_cost,
                        "external_user_id": external_actor_user_id,
                    },
                )
            conn.commit()

        worker_payload = {
            "case_id": str(case_id),
            "org_id": org_id,
            "request_id": request_id,
            "plan": plan,
            "status": case_status,
            "quote_id": None,
        }
        if not concurrency_limited:
            await _increment_active_counters(redis, org_id)
        await _enqueue_case_for_worker(redis, worker_payload, immediate=not concurrency_limited)

    return {
        "case_id": str(case_id),
        "status": case_status,
        "position_in_queue": queue_position,
        "concurrency_limited": concurrency_limited,
        "billing_action": "PRE_HOLD",
    }


@app.post("/api/v1/investigation/admin/dlq/{case_id}/acknowledge")
async def acknowledge_dlq_case(
    case_id: UUID,
    body: DlqResolutionRequest,
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
        allowed_roles={"ADMIN"},
        detail="admin_required",
        resource_type="case",
        resource_id=case_id,
        endpoint="/api/v1/investigation/admin/dlq/{case_id}/acknowledge",
        method="POST",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, case_type, status, metadata
                FROM cases
                WHERE id = %s
                """,
                (case_id,),
            )
            case_row = cur.fetchone()
            if not case_row:
                raise HTTPException(status_code=404, detail="case_not_found")
            if case_row["case_type"] != "investigation":
                raise HTTPException(status_code=409, detail="invalid_case_type_for_dlq_resolution")
            if case_row["status"] != "failed":
                raise HTTPException(status_code=409, detail="case_not_failed")

            raw_metadata = case_row.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
            if metadata.get("dlq_state") != "failed_permanent":
                raise HTTPException(status_code=409, detail="case_not_open_in_dlq")

            resolved_state = body.action
            action_name = "case_dlq_acknowledged" if resolved_state == "acknowledged" else "case_dlq_discarded"
            cur.execute(
                """
                UPDATE cases
                SET metadata = jsonb_strip_nulls(COALESCE(metadata, '{}'::jsonb) || %s::jsonb)
                WHERE id = %s
                """,
                (
                    json.dumps(
                        {
                            "dlq_state": resolved_state,
                            "dlq_acknowledged_at": datetime.now(timezone.utc).isoformat(),
                            "dlq_acknowledged_by": effective_user_id or "admin",
                            "dlq_acknowledged_external_user_id": external_actor_user_id,
                            "dlq_resolution_note": body.note or None,
                        }
                    ),
                    case_id,
                ),
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action=action_name,
                resource_type="case",
                resource_id=case_id,
                metadata={
                    "request_id": request_id,
                    "resolution": resolved_state,
                    "note": body.note or "",
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()

    return {
        "case_id": str(case_id),
        "status": "failed",
        "dlq_state": body.action,
        "resolution_note": body.note or "",
    }


@app.get("/api/v1/audit/logs")
async def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    request_id: Optional[str] = None,
    report_id: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    offset = (page - 1) * limit
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="privileged_read_role_required",
        resource_type="audit_logs",
        resource_id=resource_id,
        endpoint="/api/v1/audit/logs",
        method="GET",
    )
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            base_query = """
                FROM audit_logs
                WHERE organization_id = %s
            """
            params: list[object] = [org_id]
            if action:
                base_query += " AND action = %s"
                params.append(action)
            if resource_type:
                base_query += " AND resource_type = %s"
                params.append(resource_type)
            if request_id:
                base_query += " AND metadata ->> 'request_id' = %s"
                params.append(request_id)
            if report_id:
                base_query += " AND metadata ->> 'report_id' = %s"
                params.append(report_id)
            if resource_id:
                base_query += " AND resource_id = %s"
                params.append(resource_id)

            count_query = "SELECT COUNT(*) AS total " + base_query
            cur.execute(count_query, params)
            total_row = cur.fetchone() or {}
            total = int(total_row.get("total") or 0)

            query = """
                SELECT id, user_id, action, resource_type, resource_id, metadata, created_at
                FROM audit_logs
                WHERE organization_id = %s
            """
            if action:
                query += " AND action = %s"
            if resource_type:
                query += " AND resource_type = %s"
            if request_id:
                query += " AND metadata ->> 'request_id' = %s"
            if report_id:
                query += " AND metadata ->> 'report_id' = %s"
            if resource_id:
                query += " AND resource_id = %s"
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cur.execute(query, [*params, limit, offset])
            rows = cur.fetchall()
    serialized_rows = [_serialize_audit_log_row(row) for row in rows]
    total_pages = max(1, (total + limit - 1) // limit) if total else 1
    return {
        "data": serialized_rows,
        "page": page,
        "limit": limit,
        "count": len(serialized_rows),
        "total": total,
        "total_pages": total_pages,
        "has_more": page < total_pages,
        "filters": {
            "action": action,
            "resource_type": resource_type,
            "request_id": request_id,
            "report_id": report_id,
            "resource_id": str(resource_id) if resource_id else None,
        },
    }


@app.post("/api/v1/audit/evidence-export")
async def export_evidence_bundle(
    body: EvidenceExportRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> Response:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="privileged_read_role_required",
        resource_type="evidence_bundle",
        resource_id=body.resource_id,
        endpoint="/api/v1/audit/evidence-export",
        method="POST",
    )
    if not body.include_audit_logs and not body.include_credit_ledger and not body.include_reports:
        raise HTTPException(status_code=422, detail="evidence_export_sections_required")

    audit_rows: list[dict] = []
    credit_rows: list[dict] = []
    report_rows: list[dict] = []
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            if body.include_audit_logs:
                audit_query = """
                    SELECT id, user_id, action, resource_type, resource_id, metadata, created_at
                    FROM audit_logs
                    WHERE organization_id = %s
                """
                audit_params: list[object] = [org_id]
                if body.action:
                    audit_query += " AND action = %s"
                    audit_params.append(body.action)
                if body.resource_type:
                    audit_query += " AND resource_type = %s"
                    audit_params.append(body.resource_type)
                if body.request_id:
                    audit_query += " AND metadata ->> 'request_id' = %s"
                    audit_params.append(body.request_id)
                if body.report_id:
                    audit_query += " AND metadata ->> 'report_id' = %s"
                    audit_params.append(body.report_id)
                if body.resource_id:
                    audit_query += " AND resource_id = %s"
                    audit_params.append(body.resource_id)
                audit_query += " ORDER BY created_at DESC LIMIT %s"
                audit_params.append(body.limit)
                cur.execute(audit_query, audit_params)
                audit_rows = [_serialize_audit_log_row(row) for row in cur.fetchall()]

            if body.include_credit_ledger:
                credit_query = """
                    SELECT id, case_id, action, amount, balance_after, metadata, created_at
                    FROM credit_ledger
                    WHERE org_id = %s
                """
                credit_params: list[object] = [org_id]
                if body.action:
                    credit_query += " AND action = %s"
                    credit_params.append(body.action)
                if body.request_id:
                    credit_query += " AND metadata ->> 'request_id' = %s"
                    credit_params.append(body.request_id)
                if body.resource_id:
                    credit_query += " AND case_id = %s"
                    credit_params.append(body.resource_id)
                credit_query += " ORDER BY created_at DESC LIMIT %s"
                credit_params.append(body.limit)
                cur.execute(credit_query, credit_params)
                credit_rows = [_serialize_credit_ledger_row(row) for row in cur.fetchall()]

            if body.include_reports:
                report_query = """
                    SELECT
                      id,
                      case_id,
                      external_report_id,
                      report_type_requested,
                      report_type,
                      content_type,
                      file_path,
                      file_hash,
                      onchain_hash,
                      is_coaf_ready,
                      created_at
                    FROM reports
                    WHERE organization_id = %s
                """
                report_params: list[object] = [org_id]
                if body.report_id:
                    report_query += " AND external_report_id = %s"
                    report_params.append(body.report_id)
                if body.resource_id:
                    report_query += " AND case_id = %s"
                    report_params.append(body.resource_id)
                if body.request_id or body.action or body.resource_type:
                    report_query += """
                        AND EXISTS (
                          SELECT 1
                          FROM audit_logs a
                          WHERE a.organization_id = %s
                            AND (
                              (reports.external_report_id IS NOT NULL AND a.metadata ->> 'report_id' = reports.external_report_id)
                              OR (reports.case_id IS NOT NULL AND a.resource_id = reports.case_id)
                            )
                    """
                    report_params.append(org_id)
                    if body.request_id:
                        report_query += " AND a.metadata ->> 'request_id' = %s"
                        report_params.append(body.request_id)
                    if body.action:
                        report_query += " AND a.action = %s"
                        report_params.append(body.action)
                    if body.resource_type:
                        report_query += " AND a.resource_type = %s"
                        report_params.append(body.resource_type)
                    report_query += ")"
                report_query += " ORDER BY created_at DESC LIMIT %s"
                report_params.append(body.limit)
                cur.execute(report_query, report_params)
                report_rows = [_serialize_report_row(row) for row in cur.fetchall()]

            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="evidence_bundle_exported",
                resource_type="evidence_bundle",
                resource_id=body.resource_id,
                metadata={
                    "request_id": effective_request_id,
                    "filters": {
                        "request_id": body.request_id,
                        "action": body.action,
                        "resource_type": body.resource_type,
                        "report_id": body.report_id,
                        "resource_id": str(body.resource_id) if body.resource_id else None,
                        "limit": body.limit,
                    },
                    "format": body.format,
                    "sections": {
                        "audit_logs": {
                            "included": body.include_audit_logs,
                            "count": len(audit_rows),
                        },
                        "credit_ledger": {
                            "included": body.include_credit_ledger,
                            "count": len(credit_rows),
                        },
                        "reports": {
                            "included": body.include_reports,
                            "count": len(report_rows),
                        },
                    },
                    "external_user_id": external_actor_user_id,
                },
            )
        conn.commit()

    payload = json.dumps(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "request_id": body.request_id,
                "action": body.action,
                "resource_type": body.resource_type,
                "report_id": body.report_id,
                "resource_id": str(body.resource_id) if body.resource_id else None,
                "limit": body.limit,
            },
            "sections": {
                "audit_logs": {
                    "included": body.include_audit_logs,
                    "count": len(audit_rows),
                    "data": audit_rows,
                },
                "credit_ledger": {
                    "included": body.include_credit_ledger,
                    "count": len(credit_rows),
                    "data": credit_rows,
                },
                "reports": {
                    "included": body.include_reports,
                    "count": len(report_rows),
                    "data": report_rows,
                },
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    filename = _format_evidence_export_filename(body.format)
    return Response(
        content=payload,
        media_type="application/json; charset=utf-8",
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/v1/audit/manual-package-export")
async def record_manual_package_export(
    body: ManualPackageAuditRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_role_with_audit(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        allowed_roles={"ADMIN", "AUDITOR"},
        detail="privileged_read_role_required",
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        endpoint="/api/v1/audit/manual-package-export",
        method="POST",
    )

    created_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            metadata = _record_manual_package_audit_event(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action=body.action,
                resource_type=body.resource_type,
                resource_id=body.resource_id,
                request_id=body.request_id,
                report_id=body.report_id,
                metadata=body.metadata,
                created_at=created_at,
                external_user_id=external_actor_user_id,
            )
        conn.commit()

    return {
        "action": body.action,
        "resource_type": body.resource_type,
        "resource_id": body.resource_id,
        "request_id": body.request_id,
        "report_id": body.report_id,
        "created_at": created_at,
        "metadata": metadata,
    }


@app.post("/api/v1/evidence/manual-package/signoff-requests")
async def create_manual_package_signoff_request(
    body: ManualPackageSignoffRequestCreate,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_admin_mutation_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=None,
        endpoint="/api/v1/evidence/manual-package/signoff-requests",
        method="POST",
    )

    created_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM evidence_package_seals
                WHERE organization_id = %s
                  AND package_sha256 = %s
                  AND policy_version = %s
                """,
                (org_id, body.package_sha256, body.policy_version),
            )
            existing_row = cur.fetchone()
            if existing_row:
                seal_id = existing_row["id"]
            else:
                cur.execute(
                    """
                    INSERT INTO evidence_package_seals (
                        organization_id,
                        package_kind,
                        request_id,
                        report_id,
                        scope_id,
                        manual_review_action,
                        package_sha256,
                        manifest_schema_version,
                        classification,
                        signoff_mode,
                        seal_status,
                        seal_format,
                        policy_version
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        org_id,
                        body.package_kind,
                        body.request_id,
                        body.report_id,
                        body.scope_id,
                        body.manual_review_action,
                        body.package_sha256,
                        body.manifest_schema_version,
                        body.classification,
                        body.signoff_mode,
                        "pending_signoff",
                        "jws_json_flattened",
                        body.policy_version,
                    ),
                )
                inserted = cur.fetchone()
                if not inserted:
                    raise HTTPException(status_code=500, detail="manual_package_seal_not_created")
                seal_id = inserted["id"]
                _record_manual_package_audit_event(
                    cur,
                    organization_id=org_id,
                    user_id=effective_user_id,
                    action="evidence_manual_review_package_signoff_requested",
                    resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                    resource_id=seal_id,
                    request_id=body.request_id,
                    report_id=body.report_id,
                    metadata={
                        "seal_id": str(seal_id),
                        "scope_id": body.scope_id,
                        "manual_review_action": body.manual_review_action,
                        "package_sha256": body.package_sha256,
                        "policy_version": body.policy_version,
                        "required_signers": list(_required_manual_package_signer_roles(body.signoff_mode)),
                    },
                    created_at=created_at,
                    external_user_id=external_actor_user_id,
                )

            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
        conn.commit()

    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.post("/api/v1/evidence/manual-package/seals/{seal_id}/signoffs")
async def record_manual_package_signoff(
    seal_id: UUID,
    body: ManualPackageSignoffRecordRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
    x_2fa: Annotated[Optional[str], Header(alias="X-2FA")] = None,
    x_mfa_mode: Annotated[Optional[str], Header(alias="X-MFA-Mode")] = None,
    x_mfa_provider_homologated: Annotated[Optional[str], Header(alias="X-MFA-Provider-Homologated")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    auth_role = _require_manual_package_signoff_role_binding(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        signer_role=body.signer_role,
        resource_id=seal_id,
        endpoint="/api/v1/evidence/manual-package/seals/{seal_id}/signoffs",
        method="POST",
    )
    if body.signoff_method == "platform_authenticated_2fa":
        try:
            _require_platform_authenticated_2fa(
                x_2fa=x_2fa,
                x_mfa_mode=x_mfa_mode,
                x_mfa_provider_homologated=x_mfa_provider_homologated,
            )
        except HTTPException as exc:
            if exc.status_code == 403 and exc.detail in {"2fa_required", "mfa_not_homologated_for_oidc"}:
                _record_manual_package_mfa_violation(
                    pool,
                    organization_id=org_id,
                    user_id=effective_user_id,
                    external_user_id=external_actor_user_id,
                    seal_id=seal_id,
                    request_id=effective_request_id,
                    auth_role=auth_role,
                    signer_role=body.signer_role,
                    signoff_method=body.signoff_method,
                    mfa_mode=x_mfa_mode,
                    mfa_provider_homologated=x_mfa_provider_homologated,
                    two_factor_status=x_2fa,
                    detail=str(exc.detail),
                )
            raise

    signed_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            if seal_row["seal_status"] in {"sealed", "revoked", "superseded"}:
                raise HTTPException(status_code=409, detail="manual_package_seal_locked")

            if any(signoff["signer_role"] == body.signer_role for signoff in signoff_rows):
                raise HTTPException(status_code=409, detail="manual_package_signoff_role_already_recorded")

            signer_display_name = (
                body.signer_display_name
                or effective_user_id
                or external_actor_user_id
                or body.signer_role
            )
            signer_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            signoff_metadata = dict(body.metadata)
            signoff_metadata.update(
                {
                    "auth_role": auth_role,
                    "asserted_signer_role": body.signer_role,
                    "request_id": effective_request_id,
                    "signer_binding_enforced": True,
                    "mfa_mode": x_mfa_mode or "not_informed",
                    "mfa_provider_homologated": (x_mfa_provider_homologated or "").lower() == "true",
                    "two_factor_status": x_2fa or "not_informed",
                }
            )
            if external_actor_user_id:
                signoff_metadata.setdefault("external_user_id", external_actor_user_id)

            cur.execute(
                """
                INSERT INTO evidence_package_signoffs (
                    seal_id,
                    organization_id,
                    signer_role,
                    signer_user_id,
                    signer_display_name,
                    decision,
                    signoff_method,
                    ticket_ref,
                    notes,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
                """,
                (
                    seal_id,
                    org_id,
                    body.signer_role,
                    signer_user_id,
                    str(signer_display_name),
                    body.decision,
                    body.signoff_method,
                    body.ticket_ref,
                    body.notes,
                    json.dumps(signoff_metadata),
                ),
            )
            inserted_signoff = cur.fetchone()
            if not inserted_signoff:
                raise HTTPException(status_code=500, detail="manual_package_signoff_not_recorded")

            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            next_status = _resolve_manual_package_seal_status(seal_row["signoff_mode"], signoff_rows)
            cur.execute(
                """
                UPDATE evidence_package_seals
                SET seal_status = %s
                WHERE id = %s
                """,
                (next_status, seal_id),
            )
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)

            _record_manual_package_audit_event(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="evidence_manual_review_package_signoff_recorded",
                resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                resource_id=seal_id,
                request_id=seal_row["request_id"],
                report_id=seal_row.get("report_id"),
                metadata={
                    "seal_id": str(seal_id),
                    "scope_id": seal_row["scope_id"],
                    "manual_review_action": seal_row["manual_review_action"],
                    "package_sha256": seal_row["package_sha256"],
                    "signer_role": body.signer_role,
                    "auth_role": auth_role,
                    "decision": body.decision,
                    "signoff_method": body.signoff_method,
                    "ticket_ref": body.ticket_ref,
                    "seal_status": next_status,
                },
                created_at=signed_at,
                external_user_id=external_actor_user_id,
            )
        conn.commit()

    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.post("/api/v1/evidence/manual-package/seals/{seal_id}/finalize")
async def finalize_manual_package_seal(
    seal_id: UUID,
    body: ManualPackageFinalizeRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_admin_mutation_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=seal_id,
        endpoint="/api/v1/evidence/manual-package/seals/{seal_id}/finalize",
        method="POST",
    )

    finalized_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            if seal_row["seal_status"] != "ready_to_seal":
                raise HTTPException(status_code=409, detail="manual_package_seal_not_ready")

            approved_roles = {
                signoff["signer_role"]
                for signoff in signoff_rows
                if signoff.get("decision") == "approved"
            }
            missing_roles = [
                role
                for role in _required_manual_package_signer_roles(seal_row["signoff_mode"])
                if role not in approved_roles
            ]
            if missing_roles:
                raise HTTPException(status_code=409, detail="manual_package_signoff_incomplete")
            finalized_by_user_id = _resolve_persisted_user_id(cur, effective_user_id)
            seal_result = _finalize_manual_package_with_institutional_seal_service(
                seal_row=seal_row,
                signoff_rows=signoff_rows,
                finalized_at=finalized_at,
                finalized_by_user_id=str(finalized_by_user_id) if finalized_by_user_id else None,
                finalize_metadata=body.metadata,
            )
            raw_verification_summary = seal_result["verification_summary"]
            verification_summary = (
                raw_verification_summary if isinstance(raw_verification_summary, dict) else {}
            )
            cur.execute(
                """
                UPDATE evidence_package_seals
                SET
                    seal_status = %s,
                    signature_algorithm = %s,
                    kms_key_ref = %s,
                    certificate_fingerprint_sha256 = %s,
                    certificate_bundle_ref = %s,
                    sealed_at = %s,
                    sealed_by_user_id = %s,
                    seal_envelope = %s::jsonb,
                    verification_summary = %s::jsonb
                WHERE id = %s
                """,
                (
                    "sealed",
                    seal_result["signature_algorithm"],
                    seal_result["kms_key_ref"],
                    seal_result["certificate_fingerprint_sha256"],
                    seal_result["certificate_bundle_ref"],
                    finalized_at,
                    finalized_by_user_id,
                    json.dumps(seal_result["seal_envelope"]),
                    json.dumps(seal_result["verification_summary"]),
                    seal_id,
                ),
            )
            _record_manual_package_audit_event(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="evidence_manual_review_package_sealed",
                resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                resource_id=seal_id,
                request_id=seal_row["request_id"],
                report_id=seal_row.get("report_id"),
                metadata={
                    "seal_id": str(seal_id),
                    "scope_id": seal_row["scope_id"],
                    "manual_review_action": seal_row["manual_review_action"],
                    "package_sha256": seal_row["package_sha256"],
                    "seal_backend": verification_summary["seal_backend"],
                    "signature_algorithm": seal_result["signature_algorithm"],
                    "certificate_bundle_ref": seal_result["certificate_bundle_ref"],
                    "verification_summary": verification_summary,
                },
                created_at=finalized_at,
                external_user_id=external_actor_user_id,
            )
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
        conn.commit()
    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.post("/api/v1/evidence/manual-package/seals/{seal_id}/revoke")
async def revoke_manual_package_seal(
    seal_id: UUID,
    body: ManualPackageRevokeRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_admin_mutation_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=seal_id,
        endpoint="/api/v1/evidence/manual-package/seals/{seal_id}/revoke",
        method="POST",
    )

    revoked_at = datetime.now(timezone.utc).isoformat()
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            previous_status = seal_row["seal_status"]
            if seal_row["seal_status"] == "revoked":
                raise HTTPException(status_code=409, detail="manual_package_seal_already_revoked")
            if seal_row["seal_status"] == "superseded":
                raise HTTPException(status_code=409, detail="manual_package_seal_already_superseded")

            cur.execute(
                """
                UPDATE evidence_package_seals
                SET
                    seal_status = %s,
                    revoked_at = %s,
                    superseded_by_seal_id = NULL,
                    updated_at = NOW()
                WHERE id = %s
                """,
                ("revoked", revoked_at, seal_id),
            )
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            _record_manual_package_audit_event(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="evidence_manual_review_package_seal_revoked",
                resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                resource_id=seal_id,
                request_id=seal_row["request_id"],
                report_id=seal_row.get("report_id"),
                metadata={
                    "seal_id": str(seal_id),
                    "scope_id": seal_row["scope_id"],
                    "manual_review_action": seal_row["manual_review_action"],
                    "package_sha256": seal_row["package_sha256"],
                    "previous_seal_status": previous_status,
                    "reason": body.reason,
                    "ticket_ref": body.ticket_ref,
                    "metadata": body.metadata,
                },
                created_at=revoked_at,
                external_user_id=external_actor_user_id,
            )
        conn.commit()
    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.post("/api/v1/evidence/manual-package/seals/{seal_id}/supersede")
async def supersede_manual_package_seal(
    seal_id: UUID,
    body: ManualPackageSupersedeRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_admin_mutation_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=seal_id,
        endpoint="/api/v1/evidence/manual-package/seals/{seal_id}/supersede",
        method="POST",
    )

    superseded_at = datetime.now(timezone.utc).isoformat()
    if body.superseded_by_seal_id == seal_id:
        raise HTTPException(status_code=422, detail="manual_package_supersede_target_invalid")
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            if seal_row["seal_status"] == "revoked":
                raise HTTPException(status_code=409, detail="manual_package_seal_revoked")
            if seal_row["seal_status"] == "superseded":
                raise HTTPException(status_code=409, detail="manual_package_seal_already_superseded")

            replacement_seal_row, replacement_signoffs = _load_manual_package_seal(
                cur, organization_id=org_id, seal_id=body.superseded_by_seal_id
            )
            if replacement_seal_row["seal_status"] != "sealed":
                raise HTTPException(status_code=409, detail="manual_package_supersede_target_not_sealed")
            if replacement_seal_row.get("revoked_at"):
                raise HTTPException(status_code=409, detail="manual_package_supersede_target_revoked")
            if replacement_seal_row.get("superseded_by_seal_id"):
                raise HTTPException(status_code=409, detail="manual_package_supersede_target_superseded")

            cur.execute(
                """
                UPDATE evidence_package_seals
                SET
                    seal_status = %s,
                    superseded_by_seal_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                ("superseded", body.superseded_by_seal_id, seal_id),
            )
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
            _record_manual_package_audit_event(
                cur,
                organization_id=org_id,
                user_id=effective_user_id,
                action="evidence_manual_review_package_seal_superseded",
                resource_type=MANUAL_PACKAGE_SEAL_RESOURCE_TYPE,
                resource_id=seal_id,
                request_id=seal_row["request_id"],
                report_id=seal_row.get("report_id"),
                metadata={
                    "seal_id": str(seal_id),
                    "superseded_by_seal_id": str(body.superseded_by_seal_id),
                    "scope_id": seal_row["scope_id"],
                    "manual_review_action": seal_row["manual_review_action"],
                    "package_sha256": seal_row["package_sha256"],
                    "replacement_package_sha256": replacement_seal_row.get("package_sha256"),
                    "replacement_policy_version": replacement_seal_row.get("policy_version"),
                    "reason": body.reason,
                    "ticket_ref": body.ticket_ref,
                    "metadata": body.metadata,
                },
                created_at=superseded_at,
                external_user_id=external_actor_user_id,
            )
        conn.commit()
    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.get("/api/v1/evidence/manual-package/seals/{seal_id}")
async def get_manual_package_seal(
    seal_id: UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=seal_id,
        endpoint="/api/v1/evidence/manual-package/seals/{seal_id}",
        method="GET",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal(cur, organization_id=org_id, seal_id=seal_id)
    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.get("/api/v1/evidence/manual-package/seals/by-digest")
async def get_manual_package_seal_by_digest(
    package_sha256: Annotated[str, Query(min_length=64, max_length=64)],
    policy_version: Annotated[str, Query(min_length=1)] = "manual_package_sealing/v1",
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_linked_user_id: Annotated[Optional[str], Header(alias="X-Linked-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    effective_request_id = x_request_id or str(uuid.uuid4())
    effective_user_id, external_actor_user_id = _resolve_actor_ids(
        external_user_id=x_user_id,
        linked_user_id=x_linked_user_id,
    )
    _require_manual_package_read_role(
        pool,
        organization_id=org_id,
        user_id=effective_user_id,
        external_user_id=external_actor_user_id,
        request_id=effective_request_id,
        x_role=x_role,
        resource_id=package_sha256,
        endpoint="/api/v1/evidence/manual-package/seals/by-digest",
        method="GET",
    )

    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            seal_row, signoff_rows = _load_manual_package_seal_by_digest(
                cur,
                organization_id=org_id,
                package_sha256=package_sha256,
                policy_version=policy_version,
            )
    return _serialize_manual_package_seal_row(seal_row, signoff_rows)


@app.post("/api/v1/investigation/{case_id}/internal/complete")
async def complete_case(
    case_id: UUID,
    body: FinalizeCaseRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, organization_id, status, credits_estimated
                FROM cases
                WHERE id = %s
                """,
                (case_id,),
            )
            case_row = cur.fetchone()
            if not case_row:
                raise HTTPException(status_code=404, detail="case_not_found")
            if case_row["status"] == "completed":
                raise HTTPException(status_code=409, detail="case_already_completed")

            estimated_cost = round(float(case_row["credits_estimated"]), 4)
            actual_cost = round(float(body.credits_used), 4) if body.credits_used is not None else None
            if actual_cost is not None and estimated_cost > 0:
                variance = abs(actual_cost - estimated_cost) / estimated_cost
                if variance > MAX_VARIANCE_PCT:
                    cur.execute(
                        """
                        SELECT credits_available, credits_reserved
                        FROM organizations
                        WHERE id = %s
                        """,
                        (org_id,),
                    )
                    org_for_refund = cur.fetchone()
                    if not org_for_refund:
                        raise HTTPException(status_code=404, detail="organization_not_found")

                    new_available_refund = round(float(org_for_refund["credits_available"]) + estimated_cost, 4)
                    new_reserved_refund = round(float(org_for_refund["credits_reserved"]) - estimated_cost, 4)
                    cur.execute(
                        """
                        UPDATE organizations
                        SET credits_available = %s, credits_reserved = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        (new_available_refund, new_reserved_refund, org_id),
                    )
                    cur.execute(
                        """
                        UPDATE cases
                        SET status = 'billing_recalc_required',
                            completed_at = NOW(),
                            metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                        WHERE id = %s
                        """,
                        (
                            json.dumps(
                                {
                                    "billing_variance_pct": round(variance, 4),
                                    "estimated_cost": estimated_cost,
                                    "actual_cost": actual_cost,
                                }
                            ),
                            case_id,
                        ),
                    )
                    _record_credit_ledger(
                        cur,
                        org_id=org_id,
                        case_id=case_id,
                        action="REFUND",
                        amount=estimated_cost,
                        balance_after=new_available_refund,
                        metadata={
                            "request_id": request_id,
                            "reason": "variance_above_threshold",
                            "estimated_cost": estimated_cost,
                            "actual_cost": actual_cost,
                            "max_variance_pct": MAX_VARIANCE_PCT,
                        },
                    )
                    _record_audit_log(
                        cur,
                        organization_id=org_id,
                        user_id=None,
                        action="case_flagged_billing_recalc_required",
                        resource_type="case",
                        resource_id=case_id,
                        metadata={
                            "request_id": request_id,
                            "case_type": "investigation",
                            "estimated_cost": estimated_cost,
                            "actual_cost": actual_cost,
                            "billing_variance_pct": round(variance, 4),
                            "max_variance_pct": MAX_VARIANCE_PCT,
                        },
                    )
                    conn.commit()
                    return {
                        "case_id": str(case_id),
                        "status": "billing_recalc_required",
                        "refunded_amount": estimated_cost,
                        "estimated_cost": estimated_cost,
                        "actual_cost": actual_cost,
                        "max_variance_pct": MAX_VARIANCE_PCT,
                    }

            charged_cost = estimated_cost
            cur.execute(
                """
                SELECT credits_available, credits_reserved, credits_used_total
                FROM organizations
                WHERE id = %s
                """,
                (org_id,),
            )
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")

            new_reserved = round(float(org["credits_reserved"]) - estimated_cost, 4)
            new_available = round(float(org["credits_available"]), 4)
            new_used_total = round(float(org["credits_used_total"]) + charged_cost, 4)
            cur.execute(
                """
                UPDATE organizations
                SET credits_available = %s, credits_reserved = %s, credits_used_total = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (new_available, new_reserved, new_used_total, org_id),
            )
            cur.execute(
                """
                UPDATE cases
                SET status = 'completed', credits_used = %s, completed_at = NOW(),
                    metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
                """,
                (
                    charged_cost,
                    json.dumps(
                        {
                            "actual_cost_observed": actual_cost,
                            "charged_cost": charged_cost,
                            "max_variance_pct": MAX_VARIANCE_PCT,
                        }
                    ),
                    case_id,
                ),
            )
            _record_credit_ledger(
                cur,
                org_id=org_id,
                case_id=case_id,
                action="CONFIRMED",
                amount=charged_cost,
                balance_after=new_available,
                metadata={
                    "request_id": request_id,
                    "estimated_cost": estimated_cost,
                    "actual_cost_observed": actual_cost,
                    "charged_cost": charged_cost,
                },
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=None,
                action="case_completed",
                resource_type="case",
                resource_id=case_id,
                metadata={"request_id": request_id, "case_type": "investigation", "charged_cost": charged_cost, "estimated_cost": estimated_cost},
            )
        conn.commit()
    return {"case_id": str(case_id), "status": "completed", "credits_used": charged_cost}


@app.post("/api/v1/investigation/{case_id}/internal/fail")
async def fail_case(
    case_id: UUID,
    body: FinalizeCaseRequest,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    request_id = x_request_id or str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, credits_estimated
                FROM cases
                WHERE id = %s
                """,
                (case_id,),
            )
            case_row = cur.fetchone()
            if not case_row:
                raise HTTPException(status_code=404, detail="case_not_found")
            estimated_cost = round(float(case_row["credits_estimated"]), 4)

            cur.execute(
                """
                SELECT credits_available, credits_reserved
                FROM organizations
                WHERE id = %s
                """,
                (org_id,),
            )
            org = cur.fetchone()
            if not org:
                raise HTTPException(status_code=404, detail="organization_not_found")

            new_available = round(float(org["credits_available"]) + estimated_cost, 4)
            new_reserved = round(float(org["credits_reserved"]) - estimated_cost, 4)
            cur.execute(
                """
                UPDATE organizations
                SET credits_available = %s, credits_reserved = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (new_available, new_reserved, org_id),
            )
            cur.execute(
                """
                UPDATE cases
                SET status = 'failed', completed_at = NOW(), metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                WHERE id = %s
                """,
                (
                    json.dumps(
                        {
                            "failure_reason": body.reason or "unknown_error",
                            "worker_queue_state": "dlq",
                            "dlq_state": "failed_permanent",
                            "dlq_failed_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    case_id,
                ),
            )
            _record_credit_ledger(
                cur,
                org_id=org_id,
                case_id=case_id,
                action="REFUND",
                amount=estimated_cost,
                balance_after=new_available,
                metadata={"request_id": request_id, "reason": body.reason or "unknown_error"},
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=None,
                action="case_failed",
                resource_type="case",
                resource_id=case_id,
                metadata={
                    "request_id": request_id,
                    "case_type": "investigation",
                    "reason": body.reason or "unknown_error",
                    "refunded_amount": estimated_cost,
                },
            )
            _record_audit_log(
                cur,
                organization_id=org_id,
                user_id=None,
                action="case_sent_to_dlq",
                resource_type="case",
                resource_id=case_id,
                metadata={
                    "request_id": request_id,
                    "case_type": "investigation",
                    "reason": body.reason or "unknown_error",
                },
            )
        conn.commit()
    return {"case_id": str(case_id), "status": "failed", "refund_amount": estimated_cost}


@app.delete("/api/v1/investigation/{case_id}")
async def delete_case(
    case_id: UUID,
    pool: ConnectionPool = Depends(get_pool),
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
) -> dict:
    org_id = _require_org_id(x_org_id)
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM cases WHERE id = %s", (case_id,))
            deleted = cur.rowcount
            conn.commit()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="case_not_found")

    return {"status": "deleted", "case_id": str(case_id)}
