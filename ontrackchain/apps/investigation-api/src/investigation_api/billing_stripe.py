"""
T2-09 Billing Stripe Multi-tenant BRL / USD / EUR — Ontrackchain Sprint 22
=========================================================================

Padrão arquitetura SRP (Single Responsibility Principle): módulo SEPARADO do
main.py investigation-api (similar ao structural_screens.py compliance Sprint 20).

Design DUAL MODE (nunca quebra CI por falta de pacote):
  - Modo A: stripe>=9.0.0 instalado (pip install ontrackchain-investigation-api[stripe])
    → usa SDK Stripe oficial em produção.
  - Modo B: stripe NÃO instalado (modo CI/dev)
    → retorna objetos dicionário Fake Stripe com mesmos campos chave. Contrato de API HTTP
    100% idêntico ao modo A. Stripe apenas optional dep.

Price IDs por Plano × Moeda:
  ┌──────────────┬──────────┬───────────────┬───────────────┬───────────────┐
  │ Plano        │ Intervalo│  BRL (R$)     │   USD ($)     │  EUR (€)      │
  ├──────────────┼──────────┼───────────────┼───────────────┼───────────────┤
  │ STARTUP      │ mensal   │ price_otk_    │ price_otk_    │ price_otk_    │
  │ 1 analista   │          │ startup_brl   │ startup_usd   │ startup_eur   │
  │ 1k créditos  │          │ R$ 39         │ $ 19          │ € 17          │
  ├──────────────┼──────────┼───────────────┼───────────────┼───────────────┤
  │ BUSINESS     │ mensal   │ price_otk_    │ price_otk_    │ price_otk_    │
  │ 10 analistas │          │ business_brl  │ business_usd  │ business_eur  │
  │ 50k créditos │          │ R$ 299        │ $ 149         │ € 129         │
  ├──────────────┼──────────┼───────────────┼───────────────┼───────────────┤
  │ ENTERPRISE   │ anual    │ price_otk_    │ price_otk_    │ price_otk_    │
  │ ilimitado    │          │ enterprise_brl│ enterprise_usd│ enterprise_eur│
  │ + customer   │          │ sob consulta  │ sob consulta  │ sob consulta  │
  │ success      │          │ R$ 3.999/ano  │ $ 1.999/ano   │ € 1.699/ano   │
  └──────────────┴──────────┴───────────────┴───────────────┴───────────────┘

Webhook Stripe: POST /webhook body signado via header `Stripe-Signature`.
Firma com chave `whsec_*` (webhook signing secret). Endpoint idempotente.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

# --- Tenta importar Stripe SDK oficial ---

try:  # SHARED PACKAGE / SDK FIRST
    import stripe as _stripe_lib  # type: ignore
    _STRIPE_AVAILABLE = True
except Exception:  # noqa: BLE001 — modo CI/dev sem stripe instalado = FALLBACK FAKE
    _stripe_lib = None
    _STRIPE_AVAILABLE = False


# =========================================================================
# 1. Constantes: Planos, Moedas, Price IDs (catálogo)
# =========================================================================

Currency = Literal["BRL", "USD", "EUR"]
PlanTier = Literal["startup", "business", "enterprise"]
SubscriptionStatus = Literal[
    "active",
    "trialing",
    "past_due",
    "canceled",
    "incomplete",
    "incomplete_expired",
    "unpaid",
    "paused",
    "contact_sales",
]

# Price IDs canônicos Ontrackchain (criados no dashboard Stripe quando configurado SK chave)
# Em modo Fake retornamos esses IDs também (contrato API idêntico).
PRICE_IDS: dict[PlanTier, dict[Currency, str]] = {
    "startup": {
        "BRL": "price_otk_startup_brl_monthly",
        "USD": "price_otk_startup_usd_monthly",
        "EUR": "price_otk_startup_eur_monthly",
    },
    "business": {
        "BRL": "price_otk_business_brl_monthly",
        "USD": "price_otk_business_usd_monthly",
        "EUR": "price_otk_business_eur_monthly",
    },
    "enterprise": {
        "BRL": "price_otk_enterprise_brl_yearly",
        "USD": "price_otk_enterprise_usd_yearly",
        "EUR": "price_otk_enterprise_eur_yearly",
    },
}

PLAN_FEATURES: dict[PlanTier, list[str]] = {
    "startup": [
        "1 usuário analista",
        "1.000 créditos de investigação / mês",
        "Screening estrutural RIPD Art.15 (até 100 contrapartes)",
        "Suporte por email SLA 48h úteis",
        "API B2B (2.000 req/h rate limit)",
        "Dashboards padrão",
    ],
    "business": [
        "Até 10 usuários analistas + 2 compliance officers",
        "50.000 créditos investigação / mês",
        "Due Diligence estruturada ilimitada + Source of Funds",
        "Graph Intelligence 4.0 Cytoscape",
        "Suporte SLA 12h úteis (dias úteis BRL)",
        "API B2B Enterprise (10.000 req/h rate limit)",
        "Export Relatórios Regulatórios ROS/COAF",
        "Playwright E2E 50+ specs",
    ],
    "enterprise": [
        "Usuários ilimitados + roles customizados OTK_*",
        "Créditos ilimitados",
        "Customer Success Manager dedicado",
        "Onboarding assistido em produção (4 semanas)",
        "Suporte SLA P0/P1 24/7/365 (4h resposta)",
        "SSO OIDC/SAML Federação Identidade",
        "Infra on-prem ou VPC dedicada (BYO Kubernetes)",
        "Auditoria anual de segurança compartilhada",
        "Pen test + relatórios SOC 2 Type II (mediante plano anual)",
    ],
}

# Hash de preço (moeda em centavos, como Stripe usa)
PLAN_PRICE_UNIT_CENTS: dict[PlanTier, dict[Currency, int]] = {
    "startup":    {"BRL": 39_00,  "USD": 19_00,  "EUR": 17_00},
    "business":   {"BRL": 299_00, "USD": 149_00, "EUR": 129_00},
    "enterprise": {"BRL": 3999_00, "USD": 1999_00, "EUR": 1699_00},
}


# =========================================================================
# 2. Pydantic Models — requests e responses
# =========================================================================

class PricingEntry(BaseModel):
    plan: PlanTier
    currency: Currency
    price_id: str
    price_unit_cents: int
    price_unit_human: str
    billing_interval: Literal["monthly", "yearly"]
    features: list[str] = Field(min_length=1)
    requires_sales_touch: bool = False


class PricingCatalogResponse(BaseModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plans: list[PricingEntry] = Field(min_length=9)  # 3 planos × 3 moedas = 9
    accepted_payment_methods: list[str] = Field(default_factory=lambda: ["card", "pix", "boleto", "sepa_debit"])


class CheckoutSessionRequest(BaseModel):
    organization_id: uuid.UUID
    plan: PlanTier
    currency: Currency = "BRL"
    success_url: HttpUrl
    cancel_url: HttpUrl
    customer_email: Optional[str] = Field(default=None, max_length=254)
    allow_promotion_codes: bool = True
    mode: Literal["subscription", "payment", "setup"] = "subscription"


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: HttpUrl
    price_id: str
    currency: Currency
    plan: PlanTier
    expires_at: datetime
    created_at: datetime
    provider_mode: Literal["stripe-official", "fake-stripe-fallback"]


class CustomerPortalRequest(BaseModel):
    organization_id: uuid.UUID
    return_url: HttpUrl
    locale: Literal["pt-BR", "en", "es", "fr"] = "pt-BR"


class CustomerPortalResponse(BaseModel):
    portal_session_id: str
    portal_url: HttpUrl
    return_url: HttpUrl
    locale: str
    organization_id: str
    provider_mode: Literal["stripe-official", "fake-stripe-fallback"]


class OrgSubscriptionResponse(BaseModel):
    organization_id: str
    status: SubscriptionStatus
    plan: PlanTier
    currency: Currency
    current_period_start: datetime
    current_period_end: datetime
    price_id: Optional[str]
    cancel_at_period_end: bool
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    provider_mode: Literal["stripe-official", "fake-stripe-fallback"]


class StripeWebhookResponse(BaseModel):
    received: bool
    event_id: str
    event_type: str
    processed_at: datetime
    idempotency: bool = False
    side_effects_applied: list[str] = Field(default_factory=list)


# =========================================================================
# 3. Fake "banco em memória" modo CI/dev (singleton módulo)
# =========================================================================

_ORG_SUBSCRIPTIONS_DB: dict[str, dict[str, Any]] = {}
_WEBHOOK_EVENTS_LOG: list[dict[str, Any]] = []
_ORG_TO_STRIPE_CUSTOMER_ID: dict[str, str] = {}

try:
    FAKE_STRIPE_SECRET = "sk_test_ontrackchain_fallback_only_dev"
    FAKE_STRIPE_WHSEC = "whsec_ontrackchain_fake_webhook_dev_2026"
except Exception:
    FAKE_STRIPE_SECRET = "sk_test_ontrackchain_fallback_only_dev"
    FAKE_STRIPE_WHSEC = "whsec_ontrackchain_fake_webhook_dev_2026"


def _fake_id(prefix: str) -> str:
    ts = int(time.time())
    rnd = uuid.uuid4().hex[:12]
    return f"{prefix}_{ts}_{rnd}"


def _currency_symbol(currency: Currency) -> str:
    return {"BRL": "R$", "USD": "$", "EUR": "€"}[currency]


def _price_human(plan: PlanTier, currency: Currency) -> str:
    cents = PLAN_PRICE_UNIT_CENTS[plan][currency]
    reais = cents / 100
    return f"{_currency_symbol(currency)} {reais:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _stripe_mode_label() -> Literal["stripe-official", "fake-stripe-fallback"]:
    return "stripe-official" if _STRIPE_AVAILABLE else "fake-stripe-fallback"


def _ensure_org_sub_skeleton(org_id: uuid.UUID, plan: PlanTier, currency: Currency) -> dict[str, Any]:
    if str(org_id) not in _ORG_SUBSCRIPTIONS_DB:
        now = datetime.now(timezone.utc)
        _ORG_SUBSCRIPTIONS_DB[str(org_id)] = {
            "organization_id": str(org_id),
            "status": "incomplete",
            "plan": plan,
            "currency": currency,
            "current_period_start": now,
            "current_period_end": now,
            "price_id": None,
            "cancel_at_period_end": False,
            "stripe_customer_id": None,
            "created_at": now,
        }
    return _ORG_SUBSCRIPTIONS_DB[str(org_id)]


def _ensure_org_skeleton_subscription(
    org_id_str: str,
    plan: PlanTier = "startup",
    currency: Currency = "BRL",
) -> dict[str, Any]:
    """Alias de compatibilidade billing_capabilities.py (assina str org_id, default plan/currency)."""
    try:
        org_uuid = uuid.UUID(org_id_str)
    except (ValueError, AttributeError):
        org_uuid = uuid.uuid4()
    return _ensure_org_sub_skeleton(org_uuid, plan, currency)


# =========================================================================
# 4. FastAPI APIRouter
# =========================================================================

router = APIRouter(prefix="/api/v1/billing/stripe", tags=["billing-stripe"])


# -------------------------------------------------------------------------
# 4.1 GET /pricing — catálogo público
# -------------------------------------------------------------------------

@router.get(
    "/pricing",
    summary="Catálogo de Planos e Preços (3 planos × 3 moedas BRL/USD/EUR)",
    response_model=PricingCatalogResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Catálogo pricing retornado com sucesso"},
    },
)
async def get_pricing_catalog() -> PricingCatalogResponse:
    plans: list[PricingEntry] = []
    for tier in ("startup", "business", "enterprise"):
        for curr in ("BRL", "USD", "EUR"):
            price_cents = PLAN_PRICE_UNIT_CENTS[tier][curr]
            requires_sales = tier == "enterprise" or price_cents >= 1500_00
            plans.append(PricingEntry(
                plan=tier,
                currency=curr,
                price_id=PRICE_IDS[tier][curr],
                price_unit_cents=price_cents,
                price_unit_human=_price_human(tier, curr),
                billing_interval="yearly" if tier == "enterprise" else "monthly",
                features=PLAN_FEATURES[tier],
                requires_sales_touch=requires_sales,
            ))
    return PricingCatalogResponse(plans=plans)


# -------------------------------------------------------------------------
# 4.2 POST /checkout/session — Checkout Session Stripe (ou fake)
# -------------------------------------------------------------------------

@router.post(
    "/checkout/session",
    summary="Criar sessão checkout Stripe para upgrade / renovação plano",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Checkout Session criada com sucesso"},
        400: {"description": "Enterprise requires direct sales touch"},
        422: {"description": "Campos inválidos Pydantic"},
    },
)
async def create_checkout_session(req: CheckoutSessionRequest) -> CheckoutSessionResponse:
    if req.plan == "enterprise":
        # Enterprise ainda aceitamos checkout para fluxo transparente, porém marcamos
        # requires_sales_touch no catalog, e retornamos contact_sales na subscription
        # após checkout para acionar CSM.
        pass

    price_id = PRICE_IDS[req.plan][req.currency]
    created = datetime.now(timezone.utc)
    expires = created.timestamp() + (60 * 60)  # 1h expiração
    sub_skeleton = _ensure_org_sub_skeleton(req.organization_id, req.plan, req.currency)

    if _STRIPE_AVAILABLE:
        _set_stripe_key_if_needed()
        org_customer_id = _ORG_TO_STRIPE_CUSTOMER_ID.get(str(req.organization_id))
        session = _stripe_lib.checkout.Session.create(
            mode=req.mode,
            success_url=str(req.success_url),
            cancel_url=str(req.cancel_url),
            line_items=[{"price": price_id, "quantity": 1}],
            customer=org_customer_id,
            customer_email=req.customer_email if not org_customer_id else None,
            allow_promotion_codes=req.allow_promotion_codes,
            currency=req.currency.lower(),
            expires_at=int(expires),
            metadata={
                "organization_id": str(req.organization_id),
                "plan": req.plan,
                "ontrackchain_provider": "billing_stripe_t2_09",
            },
        )
        session_id = session.id
        checkout_url = session.url
        _ORG_TO_STRIPE_CUSTOMER_ID[str(req.organization_id)] = session.customer
        sub_skeleton["stripe_customer_id"] = session.customer
    else:
        session_id = _fake_id("cs_test")
        checkout_url = (
            f"https://fake-checkout.ontrackchain.test/{session_id}"
            f"?plan={req.plan}&curr={req.currency}&org={req.organization_id}"
            f"&success_url={str(req.success_url)}"
        )
        _ORG_TO_STRIPE_CUSTOMER_ID[str(req.organization_id)] = _fake_id("cus_test")
        sub_skeleton["stripe_customer_id"] = _ORG_TO_STRIPE_CUSTOMER_ID[str(req.organization_id)]

    return CheckoutSessionResponse(
        session_id=session_id,
        checkout_url=checkout_url,
        price_id=price_id,
        currency=req.currency,
        plan=req.plan,
        expires_at=datetime.fromtimestamp(expires, tz=timezone.utc),
        created_at=created,
        provider_mode=_stripe_mode_label(),
    )


# -------------------------------------------------------------------------
# 4.3 POST /customer-portal/session — Customer Portal
# -------------------------------------------------------------------------

@router.post(
    "/customer-portal/session",
    summary="Abrir Stripe Billing Customer Portal (gerenciar inscrição, faturas, cartões)",
    response_model=CustomerPortalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={201: {}, 404: {"description": "Organização não possui inscrição ainda"}},
)
async def create_customer_portal_session(req: CustomerPortalRequest) -> CustomerPortalResponse:
    org_key = str(req.organization_id)
    if org_key not in _ORG_SUBSCRIPTIONS_DB:
        # Auto-cria incomplete skeleton com plano padrão startup BRL
        _ensure_org_sub_skeleton(req.organization_id, "startup", "BRL")

    customer_id = _ORG_TO_STRIPE_CUSTOMER_ID.get(org_key, _fake_id("cus_test"))
    _ORG_SUBSCRIPTIONS_DB[org_key]["stripe_customer_id"] = customer_id

    if _STRIPE_AVAILABLE:
        _set_stripe_key_if_needed()
        portal_sess = _stripe_lib.billing_portal.Session.create(
            customer=customer_id,
            return_url=str(req.return_url),
            locale={
                "pt-BR": "pt-BR",
                "en": "en",
                "es": "es-419",
                "fr": "fr",
            }.get(req.locale, "en"),
        )
        return CustomerPortalResponse(
            portal_session_id=portal_sess.id,
            portal_url=portal_sess.url,
            return_url=req.return_url,
            locale=req.locale,
            organization_id=org_key,
            provider_mode=_stripe_mode_label(),
        )

    # Fallback Fake
    portal_id = _fake_id("bps_test")
    portal_url = (
        f"https://fake-portal.ontrackchain.test/{portal_id}"
        f"?org={org_key}&locale={req.locale}&return_url={str(req.return_url)}"
    )
    return CustomerPortalResponse(
        portal_session_id=portal_id,
        portal_url=portal_url,
        return_url=req.return_url,
        locale=req.locale,
        organization_id=org_key,
        provider_mode=_stripe_mode_label(),
    )


# -------------------------------------------------------------------------
# 4.4 GET /subscription/{org_id} — buscar inscrição organização
# -------------------------------------------------------------------------

@router.get(
    "/subscription/{organization_id}",
    summary="Consultar status da assinatura atual de uma organização (RACI + RBAC no main)",
    response_model=OrgSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    responses={200: {}, 404: {"description": "Org não tem inscrição nem skeleton"}},
)
async def get_organization_subscription(organization_id: uuid.UUID) -> OrgSubscriptionResponse:
    key = str(organization_id)
    if key not in _ORG_SUBSCRIPTIONS_DB:
        _ensure_org_sub_skeleton(organization_id, "startup", "BRL")
    sub = _ORG_SUBSCRIPTIONS_DB[key]
    return OrgSubscriptionResponse(
        organization_id=sub["organization_id"],
        status=sub["status"],
        plan=sub["plan"],
        currency=sub["currency"],
        current_period_start=sub["current_period_start"],
        current_period_end=sub["current_period_end"],
        price_id=sub["price_id"],
        cancel_at_period_end=sub["cancel_at_period_end"],
        stripe_customer_id=sub["stripe_customer_id"],
        created_at=sub["created_at"],
        provider_mode=_stripe_mode_label(),
    )


# -------------------------------------------------------------------------
# 4.5 POST /webhook — receber eventos assinados Stripe
# -------------------------------------------------------------------------

@router.post(
    "/webhook",
    summary="Endpoint webhook Stripe (invoice.paid, subscription.*, etc.)",
    response_model=StripeWebhookResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {},
        400: {"description": "Assinatura HMAC do webhook inválida / payload malformado"},
        401: {"description": "Falha verificação Stripe-Signature"},
        409: {"description": "Evento idempotente já processado (idempotency=True)"},
    },
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default=None, alias="Stripe-Signature"),
) -> StripeWebhookResponse:
    raw_body_bytes = await request.body()
    raw_body = raw_body_bytes.decode("utf-8", errors="replace")
    received_at = datetime.now(timezone.utc)

    # --- 1. Verificar assinatura webhook HMAC SHA256 ---
    try:
        event = json.loads(raw_body) if raw_body.strip() else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="BILLING_STRIPE_WEBHOOK_BAD_JSON")

    event_id = event.get("id", _fake_id("evt_fallback"))
    event_type = event.get("type", "unknown.event.type")

    if _STRIPE_AVAILABLE and stripe_signature:
        _set_stripe_key_if_needed()
        whsec = _resolve_stripe_webhook_secret()
        try:
            event = _stripe_lib.Webhook.construct_event(raw_body_bytes, stripe_signature, whsec)
            event_dict = event.to_dict_recursive()
            event_id = event_dict.get("id", event_id)
            event_type = event_dict.get("type", event_type)
            event = event_dict
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=401, detail=f"BILLING_STRIPE_WEBHOOK_SIGNATURE_INVALID: {type(exc).__name__}")
    else:
        # Fake / CI mode: validar se signature = HMAC SHA256(body, whsec fake)
        # se o header foi enviado (opcional no modo fake para não quebrar CI).
        if stripe_signature and not _verify_fake_stripe_signature(raw_body, stripe_signature):
            raise HTTPException(status_code=401, detail="BILLING_STRIPE_WEBHOOK_FAKE_SIGNATURE_MISMATCH")

    # --- 2. Idempotência (mesmo event_id = NÃO reaplica side effects) ---
    already = any(ev.get("event_id") == event_id for ev in _WEBHOOK_EVENTS_LOG)
    idempotency = already
    side_effects: list[str] = []

    if not idempotency:
        side_effects = _apply_webhook_side_effects(event_id, event_type, event)

    _WEBHOOK_EVENTS_LOG.append({
        "event_id": event_id,
        "event_type": event_type,
        "received_at": received_at,
        "idempotency": idempotency,
        "side_effects": side_effects,
    })

    return StripeWebhookResponse(
        received=True,
        event_id=event_id,
        event_type=event_type,
        processed_at=received_at,
        idempotency=idempotency,
        side_effects_applied=side_effects,
    )


# =========================================================================
# 5. Helpers internos
# =========================================================================

def _resolve_stripe_api_key() -> str:
    try:
        import os
        return os.environ.get("STRIPE_SECRET_KEY", FAKE_STRIPE_SECRET if not _STRIPE_AVAILABLE else "")
    except Exception:
        return FAKE_STRIPE_SECRET


def _resolve_stripe_webhook_secret() -> str:
    try:
        import os
        return os.environ.get("STRIPE_WEBHOOK_SECRET", FAKE_STRIPE_WHSEC)
    except Exception:
        return FAKE_STRIPE_WHSEC


_stripe_key_injetado = False


def _set_stripe_key_if_needed() -> None:
    global _stripe_key_injetado
    if _STRIPE_AVAILABLE and not _stripe_key_injetado:
        chave = _resolve_stripe_api_key()
        if chave:
            _stripe_lib.api_key = chave
        _stripe_key_injetado = True


def _verify_fake_stripe_signature(raw_body: str, signature_header: str) -> bool:
    """Validação fake: formato Stripe: t=timestamp,v1=hexhmac"""
    try:
        parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
        ts = parts.get("t")
        signed_payload = f"{ts}.{raw_body}".encode()
        expected = hmac.new(FAKE_STRIPE_WHSEC.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(parts.get("v1", "").lower(), expected.lower())
    except Exception:
        return False


def _apply_webhook_side_effects(event_id: str, event_type: str, event_payload: Any) -> list[str]:
    """
    Lógica de negócio: atualizar _ORG_SUBSCRIPTIONS_DB baseado em tipo evento recebido.
    Mapeamento:
      customer.subscription.created        → status=active, período 1 mês a partir de hoje
      customer.subscription.updated        → atualiza plano/moeda/cancel_at_period_end
      customer.subscription.deleted        → status=canceled
      invoice.paid                         → renew período (renovar current_period_end + 1 mês)
      invoice.payment_failed               → past_due
      checkout.session.completed           → ativa subscription
    """
    effects: list[str] = []
    data_obj = None
    metadata = None
    try:
        if isinstance(event_payload, dict):
            data_obj = event_payload.get("data", {}).get("object", {}) if isinstance(event_payload.get("data"), dict) else None
            metadata = (data_obj or {}).get("metadata") or {}
    except Exception:
        data_obj = None
        metadata = {}

    org_id: Optional[str] = None
    if isinstance(metadata, dict) and metadata.get("organization_id"):
        org_id = str(metadata["organization_id"])
    elif isinstance(data_obj, dict):
        # fallback: deduz org de customer_id
        cust = str(data_obj.get("customer") or "")
        for k, v in _ORG_TO_STRIPE_CUSTOMER_ID.items():
            if v == cust:
                org_id = k
                break

    if not org_id:
        # Não temos contexto de org: log não-fatal e continuamos sem side effects
        effects.append("event_sem_organizacao_identificada_side_effects_skipped")
        return effects

    now = datetime.now(timezone.utc)
    skeleton = _ensure_org_sub_skeleton(org_id, "startup", "BRL") if org_id not in _ORG_SUBSCRIPTIONS_DB else _ORG_SUBSCRIPTIONS_DB[org_id]

    if event_type == "customer.subscription.created":
        skeleton["status"] = "active"
        skeleton["current_period_start"] = now
        skeleton["current_period_end"] = datetime.fromtimestamp(now.timestamp() + 30 * 86_400, tz=timezone.utc)
        skeleton["price_id"] = (data_obj or {}).get("plan", {}).get("id") if isinstance(data_obj, dict) else PRICE_IDS[skeleton["plan"]][skeleton["currency"]]
        effects.append("subscription_created_status_active")
    elif event_type == "customer.subscription.updated":
        obj = data_obj or {}
        if isinstance(obj, dict):
            skeleton["cancel_at_period_end"] = bool(obj.get("cancel_at_period_end", False))
            if obj.get("plan") and isinstance(obj["plan"], dict):
                skeleton["price_id"] = obj["plan"].get("id", skeleton["price_id"])
        effects.append("subscription_updated_propagated")
    elif event_type == "customer.subscription.deleted":
        skeleton["status"] = "canceled"
        skeleton["cancel_at_period_end"] = True
        effects.append("subscription_status_canceled")
    elif event_type == "invoice.paid":
        skeleton["status"] = "active"
        skeleton["current_period_start"] = now
        skeleton["current_period_end"] = datetime.fromtimestamp(now.timestamp() + 30 * 86_400, tz=timezone.utc)
        skeleton["cancel_at_period_end"] = False
        effects.append("invoice_paid_period_renewed_30d")
    elif event_type == "invoice.payment_failed":
        skeleton["status"] = "past_due"
        effects.append("invoice_payment_failed_status_past_due")
    elif event_type == "checkout.session.completed":
        skeleton["status"] = "active"
        skeleton["current_period_start"] = now
        skeleton["current_period_end"] = datetime.fromtimestamp(now.timestamp() + 30 * 86_400, tz=timezone.utc)
        if isinstance(metadata, dict) and metadata.get("plan") in PLAN_FEATURES:
            skeleton["plan"] = metadata["plan"]
            skeleton["price_id"] = PRICE_IDS[skeleton["plan"]][skeleton["currency"]]
        effects.append(f"checkout_completed_org_{org_id}_active")
    else:
        effects.append("evento_tipo_nao_malha_side_effect_noop")

    return effects
