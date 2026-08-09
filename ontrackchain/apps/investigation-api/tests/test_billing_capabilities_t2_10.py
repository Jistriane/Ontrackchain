"""
T2-10 Billing Capabilities Matrix + Usage Meters por Tier (Sprint 23)
====================================================================
12 testes contrato. Verifica:
  - /matrix público retorna 3 tiers (startup, business, enterprise)
  - Cada capability monotônica (tier superior NÃO perde capabilities)
  - Quotas: startup 5 usuários, business ilimitado, enterprise ilimitado
  - SSO SAML habilitado enterprise APENAS
  - B2B HMAC webhooks = business/enterprise
  - /my/{org_id} respeita plano do skeleton subscription
  - rate-limit-headers demo tem campos X-RateLimit-Limit + X-Billing-Tier
"""
from __future__ import annotations

import uuid

import pytest

from investigation_api.billing_capabilities import (
    OTK_PLAN_CAPABILITIES,
    get_billing_capabilities_matrix,
    get_billing_capabilities_my_org,
    get_org_rate_limit_headers_demo,
)
from investigation_api.billing_stripe import (
    _ORG_SUBSCRIPTIONS_DB,
    _ensure_org_skeleton_subscription,
)


# ---------------------------- /matrix --------------------------------

class TestBillingCapabilitiesMatrixT210:
    @pytest.mark.asyncio
    async def test_matrix_retorna_3_tiers_exatamente(self):
        res = await get_billing_capabilities_matrix()
        tiers_nomes = [t.tier for t in res.tiers]
        assert tiers_nomes == ["startup", "business", "enterprise"]
        assert res.source_of_truth.startswith("OTK_PLAN_CAPABILITIES")

    @pytest.mark.asyncio
    async def test_monotonic_users_max_startup_5_only(self):
        res = await get_billing_capabilities_matrix()
        by_tier = {t.tier: t for t in res.tiers}
        assert by_tier["startup"].included_users_max == 5
        assert by_tier["business"].included_users_max is None  # ilimitado
        assert by_tier["enterprise"].included_users_max is None

    @pytest.mark.asyncio
    async def test_monotonic_ai_credits_cada_tier_maior_que_anterior(self):
        res = await get_billing_capabilities_matrix()
        by_tier = {t.tier: t for t in res.tiers}
        startup_ai = by_tier["startup"].included_ai_credits_per_month
        business_ai = by_tier["business"].included_ai_credits_per_month
        enterprise_ai = by_tier["enterprise"].included_ai_credits_per_month
        assert startup_ai < business_ai < enterprise_ai

    @pytest.mark.asyncio
    async def test_sso_saml_apenas_enterprise(self):
        res = await get_billing_capabilities_matrix()
        by_tier = {t.tier: t for t in res.tiers}
        assert by_tier["startup"].has_sso_saml_oidc_federation is False
        assert by_tier["business"].has_sso_saml_oidc_federation is False
        assert by_tier["enterprise"].has_sso_saml_oidc_federation is True

    @pytest.mark.asyncio
    async def test_b2b_hmac_webhooks_business_e_enterprise(self):
        res = await get_billing_capabilities_matrix()
        by_tier = {t.tier: t for t in res.tiers}
        assert by_tier["startup"].has_b2b_hmac_enterprise_webhooks is False
        assert by_tier["business"].has_b2b_hmac_enterprise_webhooks is True
        assert by_tier["enterprise"].has_b2b_hmac_enterprise_webhooks is True

    @pytest.mark.asyncio
    async def test_graph_layouts_6_business_enterprise_2_startup(self):
        res = await get_billing_capabilities_matrix()
        by_tier = {t.tier: t for t in res.tiers}
        assert len(by_tier["startup"].graph_intelligence_layouts_allowed) == 2
        assert len(by_tier["business"].graph_intelligence_layouts_allowed) == 6
        assert len(by_tier["enterprise"].graph_intelligence_layouts_allowed) == 6

    @pytest.mark.asyncio
    async def test_source_constant_matches_response(self):
        """Testa que OTK_PLAN_CAPABILITIES = resposta do endpoint (SSOT)."""
        for tier, raw in OTK_PLAN_CAPABILITIES.items():
            res = await get_billing_capabilities_matrix()
            t_data = next(t for t in res.tiers if t.tier == tier)
            # Verifica 4 campos fundamentais baterem 1:1
            assert t_data.uptime_sla_percent_target == raw["uptime_sla_percent_target"]
            assert t_data.b2b_api_calls_per_hour_quota == raw["b2b_api_calls_per_hour_quota"]
            assert t_data.case_storage_months_retention_months == raw["case_storage_months_retention_months"]
            assert set(t_data.evidence_export_formats) == set(raw["evidence_export_formats"])


# ---------------------------- /my/{org} + rate-limit -----------------

class TestBillingCapabilitiesMyOrgT210:
    @pytest.mark.asyncio
    async def test_my_org_unknown_returns_startup_default_skeleton(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000007")
        res = await get_billing_capabilities_my_org(org_id)
        assert res.subscription_plan == "startup"
        assert res.organization_id == str(org_id)
        assert res.capabilities.tier == "startup"
        assert res.capabilities.included_users_max == 5
        # Especificação headers em contrato:
        assert "X-RateLimit-Limit" in res.rate_limit_headers_spec

    @pytest.mark.asyncio
    async def test_my_org_business_returns_business_capabilities(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000008")
        _ensure_org_skeleton_subscription(str(org_id), plan="business", currency="USD")
        res = await get_billing_capabilities_my_org(org_id)
        assert res.subscription_plan == "business"
        assert res.capabilities.tier == "business"
        assert res.capabilities.included_users_max is None
        assert res.capabilities.has_uptime_sla_contract is True
        assert res.capabilities.b2b_api_calls_per_hour_quota == 2_000

    @pytest.mark.asyncio
    async def test_my_org_enterprise_returns_full_capabilities(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000009")
        _ensure_org_skeleton_subscription(str(org_id), plan="enterprise", currency="EUR")
        res = await get_billing_capabilities_my_org(org_id)
        assert res.subscription_plan == "enterprise"
        assert res.capabilities.has_sso_saml_oidc_federation is True
        assert res.capabilities.has_rbac_custom_roles is True
        assert res.capabilities.has_dedicated_csm_success_manager is True
        assert "xml_bacen_ros_coaf" in res.capabilities.evidence_export_formats

    @pytest.mark.asyncio
    async def test_rate_limit_headers_demo_contains_4_key_fields(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000010")
        res = await get_org_rate_limit_headers_demo(org_id)
        hd = res["headers_spec_demo"]
        assert "X-RateLimit-Limit" in hd
        assert "X-RateLimit-Remaining" in hd
        assert "X-RateLimit-Reset" in hd
        assert hd["X-Billing-Tier"] == "startup"

    @pytest.mark.asyncio
    async def test_rate_limit_quota_business_matches_matrix(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
        _ensure_org_skeleton_subscription(str(org_id), plan="business")
        res = await get_org_rate_limit_headers_demo(org_id)
        assert res["tier"] == "business"
        assert res["headers_spec_demo"]["X-RateLimit-Limit"] == 2_000
