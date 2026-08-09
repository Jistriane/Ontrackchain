"""
T2-10 Billing Capabilities Matrix + Usage Meters por Tier (Sprint 23)
===================================================================
Fonte Única da Verdade de capabilities por plano: OTK_PLAN_CAPABILITIES.

NÃO duplicar estes valores em frontend nem qa-gateway. Frontend deve consumir
o endpoint /capabilities/matrix ou /capabilities/my. qa-gateway deve consumir
esta constante importando diretamente `from investigation_api.billing_capabilities
import OTK_PLAN_CAPABILITIES`.

3 tiers — mesmos nomes canônicos de billing_stripe.py:
  startup    → pequenos clientes, 5 usuários, B2B básico
  business   → média empresa, usuários ilimitados básicos, AI credits padrão
  enterprise → cliente grande, AI credits full, SSO SAML, SLA contratual, backup dedicado
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from investigation_api.billing_stripe import _ensure_org_skeleton_subscription

Tier = Literal["startup", "business", "enterprise"]
Currency = Literal["BRL", "USD", "EUR"]

router = APIRouter(
    prefix="/api/v1/billing/capabilities",
    tags=["billing-capabilities", "T2-10"],
)


# ---------------------------------------------------------------------------
# 1. FONTE ÚNICA DA VERDADE — NÃO DUPLICAR ESTES VALORES EM LUGAR NENHUM
# ---------------------------------------------------------------------------

OTK_PLAN_CAPABILITIES: dict[Tier, dict[str, Any]] = {
    "startup": {
        "tier": "startup",
        "display_name": "Startup",
        "included_users_max": 5,
        "included_ai_credits_per_month": 2_500,
        "b2b_api_calls_per_hour_quota": 200,
        "screening_counterparties_per_month": 500,
        "cases_per_month_quota": 50,
        "case_storage_months_retention_months": 12,
        "evidence_export_formats": ["pdf", "json"],
        "role_family_allowed": ["OTK_VIEWER", "OTK_ANALYST"],
        "has_audit_log_download_csv": False,
        "has_rbac_custom_roles": False,
        "has_sso_saml_oidc_federation": False,
        "has_dedicated_csm_success_manager": False,
        "has_uptime_sla_contract": False,
        "uptime_sla_percent_target": 99.5,
        "has_custom_backup_retention": False,
        "has_b2b_hmac_enterprise_webhooks": False,
        "max_custom_graph_dashboards": 1,
        "max_risk_rules_custom": 5,
        "graph_intelligence_enabled": True,
        "graph_intelligence_layouts_allowed": ["cose", "grid"],
    },
    "business": {
        "tier": "business",
        "display_name": "Business",
        "included_users_max": None,  # None = ilimitado
        "included_ai_credits_per_month": 50_000,
        "b2b_api_calls_per_hour_quota": 2_000,
        "screening_counterparties_per_month": 20_000,
        "cases_per_month_quota": 5_000,
        "case_storage_months_retention_months": 60,
        "evidence_export_formats": ["pdf", "json", "csv", "zip_sha256_sealed_package"],
        "role_family_allowed": [
            "OTK_VIEWER", "OTK_ANALYST", "OTK_COMPLIANCE_OFFICER", "OTK_AUDITOR",
        ],
        "has_audit_log_download_csv": True,
        "has_rbac_custom_roles": False,
        "has_sso_saml_oidc_federation": False,
        "has_dedicated_csm_success_manager": False,
        "has_uptime_sla_contract": True,
        "uptime_sla_percent_target": 99.9,
        "has_custom_backup_retention": False,
        "has_b2b_hmac_enterprise_webhooks": True,
        "max_custom_graph_dashboards": 10,
        "max_risk_rules_custom": 50,
        "graph_intelligence_enabled": True,
        "graph_intelligence_layouts_allowed": [
            "cose", "cola", "forceatlas2", "grid", "breadthfirst", "concentric",
        ],
    },
    "enterprise": {
        "tier": "enterprise",
        "display_name": "Enterprise",
        "included_users_max": None,
        "included_ai_credits_per_month": 1_000_000,
        "b2b_api_calls_per_hour_quota": 10_000,
        "screening_counterparties_per_month": 500_000,
        "cases_per_month_quota": 100_000,
        "case_storage_months_retention_months": 120,  # 10 anos LGPD Art.15
        "evidence_export_formats": [
            "pdf", "json", "csv", "xml_bacen_ros_coaf", "zip_sha256_sealed_package",
        ],
        "role_family_allowed": [
            "OTK_VIEWER", "OTK_ANALYST", "OTK_COMPLIANCE_OFFICER", "OTK_AUDITOR",
            "OTK_ADMIN", "custom_rbac_enabled",
        ],
        "has_audit_log_download_csv": True,
        "has_rbac_custom_roles": True,
        "has_sso_saml_oidc_federation": True,
        "has_dedicated_csm_success_manager": True,
        "has_uptime_sla_contract": True,
        "uptime_sla_percent_target": 99.95,
        "has_custom_backup_retention": True,
        "has_b2b_hmac_enterprise_webhooks": True,
        "max_custom_graph_dashboards": None,  # ilimitado
        "max_risk_rules_custom": None,
        "graph_intelligence_enabled": True,
        "graph_intelligence_layouts_allowed": [
            "cose", "cola", "forceatlas2", "grid", "breadthfirst", "concentric",
        ],
    },
}


# ---------------------------------------------------------------------------
# 2. Pydantic models públicos de resposta
# ---------------------------------------------------------------------------

class BillingCapabilityTierEntry(BaseModel):
    tier: Tier
    display_name: str
    included_users_max: int | None = Field(
        None, description="Número máximo de contas de usuário por organização. None = ilimitado."
    )
    included_ai_credits_per_month: int
    b2b_api_calls_per_hour_quota: int
    screening_counterparties_per_month: int
    cases_per_month_quota: int
    case_storage_months_retention_months: int
    evidence_export_formats: list[str]
    role_family_allowed: list[str]
    has_audit_log_download_csv: bool
    has_rbac_custom_roles: bool
    has_sso_saml_oidc_federation: bool
    has_dedicated_csm_success_manager: bool
    has_uptime_sla_contract: bool
    uptime_sla_percent_target: float
    has_custom_backup_retention: bool
    has_b2b_hmac_enterprise_webhooks: bool
    max_custom_graph_dashboards: int | None
    max_risk_rules_custom: int | None
    graph_intelligence_enabled: bool
    graph_intelligence_layouts_allowed: list[str]


class BillingCapabilitiesMatrixResponse(BaseModel):
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_of_truth: str = "OTK_PLAN_CAPABILITIES investigation_api.billing_capabilities (T2-10)"
    tiers: list[BillingCapabilityTierEntry]


class BillingCapabilitiesMyResponse(BaseModel):
    organization_id: str
    subscription_plan: Tier
    subscription_status: str
    capabilities: BillingCapabilityTierEntry
    rate_limit_headers_spec: dict[str, str] = Field(
        default_factory=lambda: {
            "X-RateLimit-Limit": "Cota total por janela (hora)",
            "X-RateLimit-Remaining": "Restante na janela atual",
            "X-RateLimit-Reset": "Timestamp UTC reset janela",
            "X-Billing-Tier": "Tier nome canônico: startup | business | enterprise",
            "X-Billing-AI-Credits-Remaining": "AI créditos restantes no mês",
        }
    )
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# 3. Helpers internos
# ---------------------------------------------------------------------------

def _tier_capability_entry(tier: Tier) -> BillingCapabilityTierEntry:
    raw = OTK_PLAN_CAPABILITIES[tier]
    return BillingCapabilityTierEntry(**raw)


def _enrich_with_rate_limit_headers_demo(
    tier: Tier,
) -> dict[str, int | float | str]:
    cap = OTK_PLAN_CAPABILITIES[tier]
    now = datetime.now(timezone.utc)
    next_reset_unix = int(now.timestamp()) + 3_600  # +1 hora
    # Demo / resposta statica do header spec.
    return {
        "X-RateLimit-Limit": cap["b2b_api_calls_per_hour_quota"],
        "X-RateLimit-Remaining": max(0, int(cap["b2b_api_calls_per_hour_quota"] * 0.78)),
        "X-RateLimit-Reset": next_reset_unix,
        "X-Billing-Tier": tier,
        "X-Billing-AI-Credits-Remaining": int(cap["included_ai_credits_per_month"] * 0.62),
    }


# ---------------------------------------------------------------------------
# 4. Endpoints públicos
# ---------------------------------------------------------------------------

@router.get(
    "/matrix",
    response_model=BillingCapabilitiesMatrixResponse,
    summary="T2-10: Matrix de capabilities dos 3 tiers (Startup × Business × Enterprise)",
    description="Endpoint público, SEM autenticação. Útil para tela de preços / comparativo / documentação.",
)
async def get_billing_capabilities_matrix(
    include_deprecated: bool = Query(False, description="Se true, retorna também campos de compatibilidade (não usados hoje)."),
) -> BillingCapabilitiesMatrixResponse:
    entries = [
        _tier_capability_entry("startup"),
        _tier_capability_entry("business"),
        _tier_capability_entry("enterprise"),
    ]
    return BillingCapabilitiesMatrixResponse(tiers=entries)


@router.get(
    "/my/{organization_id}",
    response_model=BillingCapabilitiesMyResponse,
    summary="T2-10: Capabilities efetivas aplicadas para UMA organização (considera inscrição + overage).",
    description="Autenticação recomendada em produção; hoje usa skeleton subscription do billing_stripe.py.",
)
async def get_billing_capabilities_my_org(
    organization_id: uuid.UUID,
) -> BillingCapabilitiesMyResponse:
    org_id_str = str(organization_id)
    _ensure_org_skeleton_subscription(org_id_str)
    from investigation_api.billing_stripe import _ORG_SUBSCRIPTIONS_DB  # singleton do billing_stripe

    sub = _ORG_SUBSCRIPTIONS_DB.get(org_id_str, {})
    tier_raw = sub.get("plan", "startup")
    if tier_raw not in OTK_PLAN_CAPABILITIES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "BILLING-CAP-T210-001",
                "message": f"Plano {tier_raw} desconhecido em OTK_PLAN_CAPABILITIES",
            },
        )
    tier: Tier = tier_raw  # type: ignore[assignment]
    cap_entry = _tier_capability_entry(tier)

    # Injetar headers demonstrativos (middleware em prod vai adicionar REAL em cada request).
    return BillingCapabilitiesMyResponse(
        organization_id=org_id_str,
        subscription_plan=tier,
        subscription_status=str(sub.get("status", "incomplete")),
        capabilities=cap_entry,
    )


# ---------------------------------------------------------------------------
# 5. Ação secundária: demo de rate-limit header spec (apenas exposto)
#    NÃO IMPLEMENTAMOS enforcement neste endpoint; T2-10 é só a matriz + contrato.
# ---------------------------------------------------------------------------

@router.get(
    "/my/{organization_id}/rate-limit-headers",
    summary="T2-10 aux: Exemplo de headers de rate limit que o middleware vai inserir em toda chamada B2B.",
)
async def get_org_rate_limit_headers_demo(organization_id: uuid.UUID):
    org_id_str = str(organization_id)
    _ensure_org_skeleton_subscription(org_id_str)
    from investigation_api.billing_stripe import _ORG_SUBSCRIPTIONS_DB
    tier_raw: Tier = _ORG_SUBSCRIPTIONS_DB.get(org_id_str, {}).get("plan", "startup")  # type: ignore[assignment]
    if tier_raw not in OTK_PLAN_CAPABILITIES:
        tier_raw = "startup"
    return {
        "organization_id": org_id_str,
        "tier": tier_raw,
        "headers_spec_demo": _enrich_with_rate_limit_headers_demo(tier_raw),
        "note": "Esses valores são DEMO. Middleware real em API Gateway deve calcular com Redis Janela Hora.",
    }
