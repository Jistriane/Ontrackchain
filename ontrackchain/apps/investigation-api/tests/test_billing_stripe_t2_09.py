"""
T2-09 Billing Stripe Multi-tenant BRL USD EUR - Testes Contrato (Sprint 22)
==========================================================================
DUAL MODE - não quebra CI:
  1) pip install investigation-api[stripe]  → SDK oficial stripe >=9
  2) SEM stripe extra                       → Fake Stripe Fallback módulo

Contrato API idêntico, portanto testes são mode-agnostic.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import pytest

from investigation_api.billing_stripe import (
    PLAN_FEATURES,
    PLAN_PRICE_UNIT_CENTS,
    PRICE_IDS,
    _ORG_SUBSCRIPTIONS_DB,
    _WEBHOOK_EVENTS_LOG,
    FAKE_STRIPE_WHSEC,
    get_pricing_catalog,
    create_checkout_session,
    create_customer_portal_session,
    get_organization_subscription,
    _ensure_org_skeleton_subscription,
)
from investigation_api.billing_stripe import (
    CheckoutSessionRequest,
    CustomerPortalRequest,
)


class TestBillingCatalogT209:
    """Catálogo: 3 tiers × 3 currencies = 9 entradas, source-of-truth único."""

    @pytest.mark.asyncio
    async def test_catalog_total_9_entries(self):
        res = await get_pricing_catalog()
        assert len(res.plans) == 9

    @pytest.mark.asyncio
    async def test_catalog_every_tier_and_currency_present(self):
        res = await get_pricing_catalog()
        for tier in ("startup", "business", "enterprise"):
            for curr in ("BRL", "USD", "EUR"):
                matches = [p for p in res.plans if p.plan == tier and p.currency == curr]
                assert len(matches) == 1, f"Faltou {tier}/{curr}"
                assert matches[0].price_id == PRICE_IDS[tier][curr]
                assert matches[0].price_unit_cents == PLAN_PRICE_UNIT_CENTS[tier][curr]

    @pytest.mark.asyncio
    async def test_catalog_enterprise_requires_sales(self):
        res = await get_pricing_catalog()
        for p in res.plans:
            assert p.requires_sales_touch is (p.plan == "enterprise")

    @pytest.mark.asyncio
    async def test_catalog_features_source_of_truth(self):
        res = await get_pricing_catalog()
        for p in res.plans:
            assert len(p.features) == len(PLAN_FEATURES[p.plan])
            for ft in PLAN_FEATURES[p.plan]:
                assert ft in p.features


class TestBillingCheckoutAndPortalT209:
    """Checkout Session (201 Created), Customer Portal, subscription org link."""

    @pytest.mark.asyncio
    async def test_checkout_startup_brl_returns_session_and_url(self):
        req = CheckoutSessionRequest(
            organization_id=uuid.UUID("00000000-0000-0000-0000-000000000100"),
            plan="startup",
            currency="BRL",
            success_url="https://cliente.exemplo.com/billing/ok",
            cancel_url="https://cliente.exemplo.com/billing/cancelar",
            customer_email="financeiro@cliente.exemplo.com",
        )
        res = await create_checkout_session(req)
        assert res.plan == "startup" and res.currency == "BRL"
        assert res.price_id == PRICE_IDS["startup"]["BRL"]
        assert res.session_id.startswith("cs_")
        assert "http" in res.checkout_url.lower()
        assert res.provider_mode in ("stripe-official", "fake-stripe-fallback")

    @pytest.mark.asyncio
    async def test_checkout_business_usd_creates_skeleton_subscription(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.uuid4()
        req = CheckoutSessionRequest(
            organization_id=org_id,
            plan="business",
            currency="USD",
            success_url="https://app.foo.com/billing/done",
            cancel_url="https://app.foo.com/billing/cancel",
            customer_email="owner@foo.com",
        )
        await create_checkout_session(req)
        sub = await get_organization_subscription(org_id)
        assert sub.plan == "business"
        assert sub.currency == "USD"
        assert sub.stripe_customer_id is not None
        assert sub.status in ("incomplete", "active")

    @pytest.mark.asyncio
    async def test_customer_portal_returns_url_locale_and_session_id(self):
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000222")
        _ensure_org_skeleton_subscription(str(org_id))
        req = CustomerPortalRequest(
            organization_id=org_id,
            return_url="https://app.foo.com/settings/billing",
            locale="pt-BR",
        )
        res = await create_customer_portal_session(req)
        assert res.portal_session_id.startswith("bps_")
        assert res.locale == "pt-BR"
        assert res.organization_id == str(org_id)
        assert "http" in res.portal_url.lower()


class TestBillingSubscriptionWebhookT209:
    """Skeleton default, webhook side-effects assinatura HMAC, idempotência."""

    @pytest.mark.asyncio
    async def test_unknown_org_returns_skeleton_startup_brl_incomplete(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000999")
        sub = await get_organization_subscription(org_id)
        assert sub.plan == "startup"
        assert sub.currency == "BRL"
        assert sub.status == "incomplete"
        assert sub.cancel_at_period_end is False

    @pytest.mark.asyncio
    async def test_side_effect_invoice_paid_activates_30d_period(self):
        _ORG_SUBSCRIPTIONS_DB.clear()
        _WEBHOOK_EVENTS_LOG.clear()
        org_id = uuid.UUID("00000000-0000-0000-0000-000000000777")
        _ensure_org_skeleton_subscription(str(org_id), plan="business", currency="USD")
        from investigation_api.billing_stripe import (
            _APPLY_SIDE_EFFECTS_BY_EVENT as SE,
        )
        assert "invoice.paid" in SE
        metadata = {"organization_id": str(org_id)}
        side_effects_applied: list[str] = []
        for fn in SE["invoice.paid"]:
            r = fn(metadata, "inv_001", None)
            if isinstance(r, list):
                side_effects_applied.extend(r)
        assert any("period_renewed_30d" in x for x in side_effects_applied)
        sub = await get_organization_subscription(org_id)
        assert sub.status == "active"
        period_sec = (sub.current_period_end - sub.current_period_start).total_seconds()
        assert 86_400 * 29 <= period_sec <= 86_400 * 31

    @pytest.mark.asyncio
    async def test_webhook_hmac_signature_mismatch_returns_401(self):
        from investigation_api.billing_stripe import _verify_stripe_webhook_signature
        bad_sig = f"t={int(time.time())},v1=0000000000000000000000000000000000000000000000000000000000000000"
        body = b'{"id":"evt_x","type":"invoice.paid"}'
        with pytest.raises(Exception):  # HTTPException 401 ou ValueError
            _verify_stripe_webhook_signature(body, bad_sig, FAKE_STRIPE_WHSEC)

    @pytest.mark.asyncio
    async def test_webhook_hmac_signature_valid_accepts(self):
        from investigation_api.billing_stripe import _verify_stripe_webhook_signature
        body = b'{"id":"evt_ok","type":"invoice.paid"}'
        ts = str(int(time.time()))
        signed = f"{ts}.{body.decode()}".encode()
        sig = hmac.new(FAKE_STRIPE_WHSEC.encode(), signed, hashlib.sha256).hexdigest()
        # Não deve lançar:
        _verify_stripe_webhook_signature(body, f"t={ts},v1={sig}", FAKE_STRIPE_WHSEC)

    @pytest.mark.asyncio
    async def test_event_idempotency_duplicate_event_not_propagated(self):
        _WEBHOOK_EVENTS_LOG.clear()
        evt_id_dup = "evt_duplicado_001"
        from investigation_api.billing_stripe import _register_and_check_event_idempotent
        first = _register_and_check_event_idempotent(evt_id_dup)
        second = _register_and_check_event_idempotent(evt_id_dup)
        assert first is False
        assert second is True
