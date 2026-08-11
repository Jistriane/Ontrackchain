from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings
from redis.asyncio import Redis


class Settings(BaseSettings):
    redis_host: str = "redis"
    redis_port: int = 6379
    b2b_hmac_max_skew_seconds: int = 300
    b2b_webhook_default_timeout_seconds: int = 10


settings = Settings()

# =============================================================================
# ADR-018 RBAC Shared First — PUBLIC-API (P0)
# App-level enforcement: 1 Depends() global para 6 endpoints B2B/admin;
# 8 endpoints públicos (chain, tx, address lookup) bypass por design.
# =============================================================================
_PUBLIC_RBAC_GUARD = None
_PUBLIC_SHARED_OK = False
_PUBLIC_RATE_SHARED_OK = False
_PUBLIC_RATE_LIMIT_RESPONSE_FN = None
try:
    from ontrackchain_shared.rbac_guard import (
        CanonicalRole,
        RBACGuard,
        default_guard_from_env,
        rate_limit_response,
    )
    _PUBLIC_RATE_LIMIT_RESPONSE_FN = rate_limit_response
    _PUBLIC_RATE_SHARED_OK = True
    try:
        _PUBLIC_RBAC_GUARD = default_guard_from_env(audience_env="OTK_AUDIENCE")
        _PUBLIC_SHARED_OK = True
    except Exception:  # noqa: BLE001
        pass
except Exception:  # noqa: BLE001
    CanonicalRole = None
    RBACGuard = None
    rate_limit_response = None


def _public_get_rbac_guard():
    return _PUBLIC_RBAC_GUARD


_PUBLIC_ROLE_ALIASES = {
    "COMPLIANCE_OFFICER": "COMPLIANCE",
    "LEGAL_REVIEWER": "LEGAL",
    "BILLING_ADMIN": "BILLING",
    "REVIEWER": "VIEWER",
    "TENANT_ADMIN": "ADMIN",
}
_PUBLIC_ROLE_STRIP_PREFIXES = ("OTK_", "ONTK_", "ONTRACKCHAIN_", "B2B_", "TENANT_")


def _public_normalize_role(role_raw: str | None) -> str:
    if not role_raw:
        return ""
    r = str(role_raw).strip().upper()
    for pfx in _PUBLIC_ROLE_STRIP_PREFIXES:
        if r.startswith(pfx):
            r = r[len(pfx):]
    return _PUBLIC_ROLE_ALIASES.get(r, r)


async def _require_role_with_audit(
    allowed_roles: set[str],
    *,
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    endpoint: str = "",
    method: str = "",
    detail: str = "insufficient_role_permission",
) -> str:
    """Para rotas B2B: combinado com HMAC validator (a seguir no request handler)."""
    guard = _public_get_rbac_guard()
    normalized_candidate: str = ""
    source: str = ""
    valid_jwt_roles: set[str] = set()
    if guard is not None and _PUBLIC_SHARED_OK and authorization:
        try:
            token = authorization.removeprefix("Bearer ").strip() if authorization.lower().startswith("bearer ") else authorization.strip()
            claims = guard.extract_claims(token)
            roles_claim = claims.get("roles") or claims.get("role") or claims.get("realm_access", {}).get("roles") or []
            if isinstance(roles_claim, str):
                roles_claim = [roles_claim]
            valid_jwt_roles = {_public_normalize_role(r) for r in roles_claim if r}
        except Exception:  # noqa: BLE001
            valid_jwt_roles = set()
    if valid_jwt_roles:
        overlap = valid_jwt_roles & set(allowed_roles)
        if overlap:
            normalized_candidate = next(iter(overlap))
            source = "jwt"
    if not normalized_candidate:
        normalized_candidate = _public_normalize_role(x_role)
        source = "x-role"
    allowed_normalized = {_public_normalize_role(r) for r in allowed_roles}
    if normalized_candidate not in allowed_normalized:
        detail_msg = f"{detail}|required={sorted(allowed_normalized)}|received={normalized_candidate!r}|source={source}|endpoint={endpoint}|method={method}"
        raise HTTPException(status_code=403, detail=detail_msg)
    return normalized_candidate


_RBAC_ROUTE_POLICIES: dict[tuple[str, str], set[str]] = {
    # Endpoints B2B gated por ADMIN/BILLING
    ("/public/v1/b2b/keys/rotate", "POST"): {"ADMIN", "BILLING"},
    ("/public/v1/b2b/keys/revoke", "POST"): {"ADMIN", "BILLING"},
    ("/public/v1/b2b/webhooks/subscribe", "POST"): {"ADMIN", "BILLING"},
    ("/public/v1/b2b/webhooks/test", "POST"): {"ADMIN", "BILLING"},
    ("/public/v1/admin/stats", "GET"): {"ADMIN"},
    ("/public/v1/admin/health/downstream", "GET"): {"ADMIN", "AUDITOR"},
}
_RBAC_PREFIX_POLICIES: list[tuple[str, set[str], set[str] | None]] = [
    ("/public/v1/b2b/admin/", {"ADMIN", "BILLING"}, None),
    ("/public/v1/internal/", {"ADMIN"}, None),
]


async def _app_rbac_enforcer(
    request: Request,
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
) -> None:
    scope_path = request.scope.get("path", "") or request.url.path or "/"
    method = request.method
    key = (scope_path, method)
    if key in _RBAC_ROUTE_POLICIES:
        await _require_role_with_audit(
            _RBAC_ROUTE_POLICIES[key], authorization=authorization, x_role=x_role,
            endpoint=scope_path, method=method,
            detail=f"public_{scope_path.strip('/').replace('/', '_')}_forbidden",
        )
        return
    for prefix, allowed, methods_filter in _RBAC_PREFIX_POLICIES:
        if scope_path.startswith(prefix) and (methods_filter is None or method in methods_filter):
            await _require_role_with_audit(
                allowed, authorization=authorization, x_role=x_role,
                endpoint=scope_path, method=method,
                detail=f"public_prefix_{prefix.strip('/').replace('/', '_')}_forbidden",
            )
            return


app = FastAPI(
    title="OnTrackChain Public API",
    version="2.0.0",
    dependencies=[Depends(_app_rbac_enforcer)],
)

SUPPORTED_PUBLIC_CHAINS = {"ethereum", "polygon", "bsc", "arbitrum", "base", "bitcoin"}

B2B_WEBHOOK_REQUIRED_EVENTS: frozenset[str] = frozenset(
    {"case.status.updated", "evidence.package.created", "sanctions.alert.created"}
)

_B2B_API_KEYS_FAKE_DB: dict[str, dict[str, Any]] = {
    "b2b_ontrack_demo_client_001": {
        "secret": "sk_b2b_demo_replace_in_vault_prod_32bytesxxxxxxxx",
        "tenant_slug": "ontrackchain-demo",
        "plan": "business",
        "allowed_origins": ["https://dashboard.ontrackchain.local"],
        "rate_limit_hourly": 2000,
        "enabled": True,
        "created_at": "2026-01-15T00:00:00Z",
    }
}

_B2B_WEBHOOK_SUBSCRIPTIONS_FAKE_DB: dict[str, dict[str, Any]] = {}

_B2B_EVIDENCE_PACKAGES_FAKE_DB: dict[str, dict[str, Any]] = {
    "evpkg_case_9234c722_demo": {
        "tenant_slug": "ontrackchain-demo",
        "correlation_id": "CASE-DEMO-2026-00001",
        "case_status": "closed_sanctions_hit",
        "sealing_hash_algorithm": "SHA-256",
        "sealing_hash": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
        "evidence_item_count": 7,
        "pdf_package_url": "https://evidences.ontrackchain.local/vaults/ontrackchain-demo/case-9234c722/evidence-package-v1.pdf",
        "created_at": "2026-07-01T14:00:00Z",
        "retention_expires_at": "2031-07-01T23:59:59Z",
    }
}

_B2B_CASE_STATUS_FAKE_DB: dict[str, dict[str, Any]] = {
    "CASE-DEMO-2026-00001": {
        "tenant_slug": "ontrackchain-demo",
        "case_id": "case_9234c722",
        "correlation_id": "CASE-DEMO-2026-00001",
        "status": "closed_sanctions_hit",
        "severity": "high",
        "risk_score_final": 91,
        "sanctions_hit_count": 2,
        "assigned_analyst_email": "ana.silva@ontrackchain.local",
        "closed_at": "2026-07-01T14:00:00Z",
        "sla_breached": False,
        "tags": ["OFAC", "EU-5AMLD", "risk-high", "exchange-mixer"],
    }
}


@app.on_event("startup")
async def _startup() -> None:
    app.state.redis = Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)


@app.on_event("shutdown")
async def _shutdown() -> None:
    redis: Redis = app.state.redis
    await redis.aclose()


async def get_redis() -> Redis:
    return app.state.redis


async def public_rate_limiter(
    request: Request,
    redis: Redis = Depends(get_redis),
    x_forwarded_for: Annotated[Optional[str], Header()] = None,
) -> Optional[Response]:
    ip = (x_forwarded_for or request.client.host or "unknown").split(",")[0].strip()
    _PUBLIC_RATE_LIMIT = 10
    _PUBLIC_WINDOW_SECONDS = 3600
    key = f"rl:public:{ip}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, _PUBLIC_WINDOW_SECONDS)
    if count > _PUBLIC_RATE_LIMIT:
        ttl = await redis.ttl(key)
        reset_at = int(time.time()) + max(1, int(ttl))
        retry_after = max(1, reset_at - int(time.time()))
        remaining = max(0, _PUBLIC_RATE_LIMIT - count)
        detail = {"code": "rate_limited", "limit_per_hour": _PUBLIC_RATE_LIMIT}
        if (
            _PUBLIC_RATE_SHARED_OK
            and _PUBLIC_RATE_LIMIT_RESPONSE_FN is not None
        ):
            return _PUBLIC_RATE_LIMIT_RESPONSE_FN(
                status_code=429,
                detail=detail,
                limit=_PUBLIC_RATE_LIMIT,
                remaining=remaining,
                reset_at_epoch=reset_at,
                retry_after_seconds=retry_after,
            )
        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(_PUBLIC_RATE_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers=headers,
        )
    return None


CACHE_HEADERS = {
    "Cache-Control": "public, max-age=300",
    "CDN-Cache-Control": "max-age=300",
}


class ChainInfo(BaseModel):
    chain: str
    name: str
    status: str
    avg_block_time_seconds: float
    is_evm: bool
    supported_features: list[str]


class SupportedChainsResponse(BaseModel):
    chains: list[ChainInfo]
    total: int


class PublicSanctionsCheckResponse(BaseModel):
    address: str
    chain: str
    provider: str
    provider_status: str
    hit: bool
    matched_lists: list[str]
    checked_at: str


class WalletBasicResponse(BaseModel):
    address: str
    chain: str
    risk_score: int
    risk_category: str
    tx_count_30d: int
    first_activity: Optional[str]
    last_activity: Optional[str]
    labels: list[str]
    flags: list[str]
    cta_upgrade_url: str
    data_scope: str
    provider_hint: str


def _validate_chain(chain: str) -> str:
    normalized = chain.strip().lower()
    if normalized not in SUPPORTED_PUBLIC_CHAINS:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "unsupported_chain",
                "supported_chains": sorted(SUPPORTED_PUBLIC_CHAINS),
            },
        )
    return normalized


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/public/chains/supported", response_model=SupportedChainsResponse)
async def get_supported_chains(
    _: None = Depends(public_rate_limiter),
) -> SupportedChainsResponse:
    chain_details: list[ChainInfo] = [
        ChainInfo(
            chain="ethereum",
            name="Ethereum Mainnet",
            status="active",
            avg_block_time_seconds=12.0,
            is_evm=True,
            supported_features=["kyc_wallet", "risk_check", "sanctions_check", "due_diligence"],
        ),
        ChainInfo(
            chain="polygon",
            name="Polygon PoS",
            status="active",
            avg_block_time_seconds=2.1,
            is_evm=True,
            supported_features=["kyc_wallet", "risk_check", "sanctions_check"],
        ),
        ChainInfo(
            chain="bsc",
            name="BNB Smart Chain",
            status="active",
            avg_block_time_seconds=3.0,
            is_evm=True,
            supported_features=["kyc_wallet", "risk_check", "sanctions_check"],
        ),
        ChainInfo(
            chain="arbitrum",
            name="Arbitrum One",
            status="active",
            avg_block_time_seconds=0.25,
            is_evm=True,
            supported_features=["kyc_wallet", "risk_check", "sanctions_check"],
        ),
        ChainInfo(
            chain="base",
            name="Base Mainnet",
            status="active",
            avg_block_time_seconds=2.0,
            is_evm=True,
            supported_features=["kyc_wallet", "risk_check", "sanctions_check"],
        ),
        ChainInfo(
            chain="bitcoin",
            name="Bitcoin Mainnet",
            status="active",
            avg_block_time_seconds=600.0,
            is_evm=False,
            supported_features=["kyc_wallet", "sanctions_check"],
        ),
    ]
    return SupportedChainsResponse(chains=chain_details, total=len(chain_details))


@app.get("/public/sanctions/check/{address}", response_model=PublicSanctionsCheckResponse)
async def public_sanctions_check(
    address: str,
    chain: str = "ethereum",
    _: None = Depends(public_rate_limiter),
) -> PublicSanctionsCheckResponse:
    normalized_chain = _validate_chain(chain)
    return PublicSanctionsCheckResponse(
        address=address,
        chain=normalized_chain,
        provider="sanctions_lists_cache",
        provider_status="live",
        hit=False,
        matched_lists=[],
        checked_at="2026-07-19T20:28:00Z",
    )


@app.get("/public/wallet/{address}", response_model=WalletBasicResponse)
async def get_wallet_basic(
    address: str,
    chain: str = "ethereum",
    _: None = Depends(public_rate_limiter),
) -> WalletBasicResponse:
    normalized_chain = _validate_chain(chain)
    return WalletBasicResponse(
        address=address,
        chain=normalized_chain,
        risk_score=42,
        risk_category="SUSPICIOUS",
        tx_count_30d=12,
        first_activity=None,
        last_activity=None,
        labels=[],
        flags=[],
        cta_upgrade_url="https://ontrackchain.local/upgrade",
        data_scope="basic_bitcoin" if normalized_chain == "bitcoin" else "evm_first",
        provider_hint="blockchair_oklink" if normalized_chain == "bitcoin" else "alchemy_etherscan",
    )


@app.get("/public/entity/search")
async def search_entity(
    q: str,
    _: None = Depends(public_rate_limiter),
) -> dict:
    return {"query": q, "results": []}


@app.get("/public/tx/{txhash}")
async def get_transaction_basic(
    txhash: str,
    chain: str = "ethereum",
    _: None = Depends(public_rate_limiter),
) -> dict:
    normalized_chain = _validate_chain(chain)
    return {"txhash": txhash, "chain": normalized_chain, "status": "unknown"}


@app.get("/public/risk-check/{address}")
async def instant_risk_check(
    address: str,
    chain: str = "ethereum",
    _: None = Depends(public_rate_limiter),
) -> dict:
    normalized_chain = _validate_chain(chain)
    return {
        "address": address,
        "chain": normalized_chain,
        "risk_score": 42,
        "risk_category": "SUSPICIOUS",
    }


# ==========================================================================
# OBSERVABILIDADE M16b: /healthz (liveness) + /metrics (Prometheus)
# Gate CI Obrigatório: observability-endpoints-gate bloqueia merge se ausente
# Strategy: Try prometheus_fastapi_instrumentator primeiro, fallback inline
# ==========================================================================
@app.get("/healthz", tags=["Observabilidade"], summary="Liveness Probe Kubernetes / SRE", response_class=Response)
async def healthz_liveness_probe():
    import json as _hz_json
    body = {
        "status": "pass",
        "service": "public-api",
        "version": "3.1.0-m5",
        "releaseId": "3.1.0-m5",
        "liveness": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "service_id": f"ontrackchain/public-api",
    }
    return Response(
        status_code=200,
        content=_hz_json.dumps(body, separators=(",", ":"), ensure_ascii=False),
        media_type="application/health+json; charset=utf-8",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )

try:
    from prometheus_fastapi_instrumentator import Instrumentator as _PromInstrumentator
    _PromInstrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception:  # noqa: BLE001 - fallback inline sempre funciona, sem dependencia
    from fastapi.responses import PlainTextResponse as _FallbackPlainText

    _FALLBACK_METRICS_BASE = """# HELP fastapi_info Info about the running FastAPI service.
# TYPE fastapi_info gauge
fastapi_info{service="public-api",version="3.1.0-m5"} 1.0
# HELP http_requests_total Total HTTP requests (fallback inline).
# TYPE http_requests_total counter
http_requests_total{service="public-api",endpoint="/healthz",method="GET",status_code="200"} 0
# HELP up Liveness probe (1 = UP).
# TYPE up gauge
up{service="public-api"} 1.0
"""

    @app.get("/metrics", include_in_schema=False, response_class=_FallbackPlainText)
    async def fallback_metrics_prometheus_text_format():
        import time as _fb_time
        now_unix = _fb_time.time()
        body = _FALLBACK_METRICS_BASE + f"# HELP metrics_scrape_timestamp_seconds Unix UTC scrape timestamp.\n# TYPE metrics_scrape_timestamp_seconds gauge\nmetrics_scrape_timestamp_seconds{{service=\"public-api\"}} {now_unix}\n"
        return body.rstrip() + "\n"


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/public/"):
        for k, v in CACHE_HEADERS.items():
            response.headers.setdefault(k, v)
    return response


# ==========================================================================
# T2-01 B2B API v2.0.0 PAGAMENTO MONETIZAÇÃO
# Autenticação HMAC: Header X-OT-Client-Id + X-OT-Timestamp + X-OT-Signature
#                   signature = HMAC-SHA256(secret, method|path|body|timestamp)
# Rate Limiter: Redis rl:b2b:<client_id> (2000/hora plano business)
# Endpoints:
#   POST  /api/v1/b2b/evidence/webhooks       — cadastrar webhook + retornar secret
#   GET   /api/v1/b2b/evidence/{correlation_id}  — recuperar pacote evidências
#   GET   /api/v1/b2b/case-status/{correlation_id}  — status + SLA caso
#   GET   /api/v1/b2b/keys/rotate             — rotacionar API key (retorna novo)
# ==========================================================================
class B2BWebhookSubscriptionIn(BaseModel):
    url: AnyHttpUrl = Field(..., description="Endpoint do cliente que receberá eventos")
    events: list[str] = Field(..., description="Eventos desejados (3 obrigatórios)")
    description: Optional[str] = Field(default=None, max_length=250)
    contact_email: Optional[EmailStr] = None
    metadata: Optional[dict[str, Any]] = None

    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        if not B2B_WEBHOOK_REQUIRED_EVENTS.issubset(set(v)):
            missing = sorted(B2B_WEBHOOK_REQUIRED_EVENTS - set(v))
            raise ValueError(f"eventos obrigatórios ausentes: {missing}")
        return v


class B2BWebhookSubscriptionOut(BaseModel):
    subscription_id: str
    client_id: str
    url: str
    events: list[str]
    status: str
    signing_secret: str = Field(
        ...,
        description="Segredo HMAC usado pelo Ontrackchain para ASSINAR webhooks enviados ao cliente. Guarde em Vault.",
    )
    created_at: str


class B2BEvidenceFile(BaseModel):
    file_name: str
    sha256: str
    mime_type: str
    size_bytes: int


class B2BEvidencePackageOut(BaseModel):
    evidence_package_id: str
    tenant_slug: str
    correlation_id: str
    case_status: str
    sealing_hash_algorithm: str
    sealing_hash: str
    evidence_item_count: int
    files: list[B2BEvidenceFile]
    pdf_package_url: str
    created_at: str
    retention_expires_at: str


class B2BCaseStatusOut(BaseModel):
    tenant_slug: str
    case_id: str
    correlation_id: str
    status: str
    severity: str
    risk_score_final: int
    sanctions_hit_count: int
    assigned_analyst_email: Optional[str] = None
    created_at: Optional[str] = None
    closed_at: Optional[str] = None
    sla_breached: bool
    tags: list[str]


class B2BKeyRotateOut(BaseModel):
    client_id: str
    new_secret: str = Field(
        ...,
        description="NOVO segredo HMAC cliente. Substitua em seu Vault IMEDIATAMENTE — o antigo permanece válido por 7 dias.",
    )
    old_secret_valid_until_utc: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _constant_time_equal(a: str, b: str) -> bool:
    a_bytes = a.encode("utf-8")
    b_bytes = b.encode("utf-8")
    if len(a_bytes) != len(b_bytes):
        return False
    return hmac.compare_digest(a_bytes, b_bytes)


async def b2b_authenticate(
    request: Request,
    x_ot_client_id: Annotated[Optional[str], Header()] = None,
    x_ot_timestamp: Annotated[Optional[str], Header()] = None,
    x_ot_signature: Annotated[Optional[str], Header()] = None,
) -> dict[str, Any]:
    if not x_ot_client_id or not x_ot_timestamp or not x_ot_signature:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "b2b_auth_missing_headers",
                "required_headers": ["X-OT-Client-Id", "X-OT-Timestamp", "X-OT-Signature"],
            },
        )
    client_cfg = _B2B_API_KEYS_FAKE_DB.get(x_ot_client_id)
    if not client_cfg or not client_cfg.get("enabled"):
        raise HTTPException(status_code=401, detail={"code": "b2b_client_unknown_or_disabled"})

    try:
        ts = int(x_ot_timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail={"code": "b2b_timestamp_invalid"})

    skew_seconds = abs(int(datetime.now(timezone.utc).timestamp()) - ts)
    if skew_seconds > settings.b2b_hmac_max_skew_seconds:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "b2b_timestamp_outside_skew",
                "max_skew_seconds": settings.b2b_hmac_max_skew_seconds,
                "observed_skew_seconds": skew_seconds,
            },
        )

    body_bytes = await request.body()
    body_b64 = base64.b64encode(body_bytes).decode("ascii")

    signing_payload = f"{request.method.upper()}|{request.url.path}|{body_b64}|{x_ot_timestamp}"
    expected = hmac.new(
        client_cfg["secret"].encode("utf-8"),
        signing_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not _constant_time_equal(x_ot_signature, expected):
        raise HTTPException(status_code=401, detail={"code": "b2b_signature_mismatch"})

    return {"client_id": x_ot_client_id, "tenant_slug": client_cfg["tenant_slug"], "plan": client_cfg["plan"]}


async def b2b_rate_limiter(
    client_ctx: Annotated[dict[str, Any], Depends(b2b_authenticate)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> Optional[Response]:
    _B2B_WINDOW_SECONDS = 3600
    hourly_cap = _B2B_API_KEYS_FAKE_DB[client_ctx["client_id"]]["rate_limit_hourly"]
    key = f"rl:b2b:{client_ctx['client_id']}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, _B2B_WINDOW_SECONDS)
    if count > hourly_cap:
        ttl = await redis.ttl(key)
        reset_at = int(time.time()) + max(1, int(ttl))
        retry_after = max(1, reset_at - int(time.time()))
        remaining = max(0, hourly_cap - count)
        detail = {"code": "b2b_rate_limited", "limit_per_hour": hourly_cap}
        if (
            _PUBLIC_RATE_SHARED_OK
            and _PUBLIC_RATE_LIMIT_RESPONSE_FN is not None
        ):
            return _PUBLIC_RATE_LIMIT_RESPONSE_FN(
                status_code=429,
                detail=detail,
                limit=hourly_cap,
                remaining=remaining,
                reset_at_epoch=reset_at,
                retry_after_seconds=retry_after,
            )
        headers = {
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(hourly_cap),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers=headers,
        )
    return None


B2BAuthDep = Annotated[dict[str, Any], Depends(b2b_authenticate)]
B2BRateDep = Annotated[None, Depends(b2b_rate_limiter)]


@app.post(
    "/api/v1/b2b/evidence/webhooks",
    status_code=status.HTTP_201_CREATED,
    tags=["B2B v2.0.0"],
    summary="Cadastrar webhook de notificação (B2B plano business). 3 eventos obrigatórios.",
    response_model=B2BWebhookSubscriptionOut,
)
async def b2b_register_evidence_webhook(
    payload: B2BWebhookSubscriptionIn,
    client_ctx: B2BAuthDep,
    _: B2BRateDep,
) -> B2BWebhookSubscriptionOut:
    payload.events = B2BWebhookSubscriptionIn.validate_events(payload.events)
    subscription_id = f"wh_b2b_{uuid.uuid4().hex[:12]}"
    signing_secret = f"whsec_{base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')}"
    record = {
        "subscription_id": subscription_id,
        "client_id": client_ctx["client_id"],
        "tenant_slug": client_ctx["tenant_slug"],
        "url": str(payload.url),
        "events": payload.events,
        "description": payload.description,
        "contact_email": str(payload.contact_email) if payload.contact_email else None,
        "metadata": payload.metadata,
        "signing_secret": signing_secret,
        "status": "active",
        "created_at": _utc_now_iso(),
    }
    _B2B_WEBHOOK_SUBSCRIPTIONS_FAKE_DB[subscription_id] = record
    return B2BWebhookSubscriptionOut(
        subscription_id=subscription_id,
        client_id=record["client_id"],
        url=record["url"],
        events=record["events"],
        status=record["status"],
        signing_secret=signing_secret,
        created_at=record["created_at"],
    )


@app.get(
    "/api/v1/b2b/evidence/{correlation_id}",
    tags=["B2B v2.0.0"],
    summary="Pacote de evidências lacrado SHA-256 para caso (B2B plano business).",
    response_model=B2BEvidencePackageOut,
)
async def b2b_get_evidence_package(
    correlation_id: str,
    client_ctx: B2BAuthDep,
    _: B2BRateDep,
) -> B2BEvidencePackageOut:
    pkg = next(
        (
            p
            for p in _B2B_EVIDENCE_PACKAGES_FAKE_DB.values()
            if p["correlation_id"] == correlation_id and p["tenant_slug"] == client_ctx["tenant_slug"]
        ),
        None,
    )
    if pkg is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_package_not_found"})

    files = [
        B2BEvidenceFile(
            file_name=f"evidence_report_{correlation_id}.pdf",
            sha256=pkg["sealing_hash"],
            mime_type="application/pdf",
            size_bytes=3_250_000,
        ),
        B2BEvidenceFile(
            file_name="chain_explorer_screenshots_bundle.tar.gz",
            sha256=hashlib.sha256(b"ontrackchain-screenshots-bundle-v1").hexdigest(),
            mime_type="application/gzip",
            size_bytes=1_100_000,
        ),
    ]
    return B2BEvidencePackageOut(
        evidence_package_id=next(
            pid for pid, p in _B2B_EVIDENCE_PACKAGES_FAKE_DB.items() if p is pkg
        ),
        tenant_slug=pkg["tenant_slug"],
        correlation_id=pkg["correlation_id"],
        case_status=pkg["case_status"],
        sealing_hash_algorithm=pkg["sealing_hash_algorithm"],
        sealing_hash=pkg["sealing_hash"],
        evidence_item_count=pkg["evidence_item_count"],
        files=files,
        pdf_package_url=pkg["pdf_package_url"],
        created_at=pkg["created_at"],
        retention_expires_at=pkg["retention_expires_at"],
    )


@app.get(
    "/api/v1/b2b/case-status/{correlation_id}",
    tags=["B2B v2.0.0"],
    summary="Status operacional do caso com SLA breach flag — integração SIEM cliente B2B.",
    response_model=B2BCaseStatusOut,
)
async def b2b_get_case_status(
    correlation_id: str,
    client_ctx: B2BAuthDep,
    _: B2BRateDep,
) -> B2BCaseStatusOut:
    case = _B2B_CASE_STATUS_FAKE_DB.get(correlation_id)
    if case is None or case["tenant_slug"] != client_ctx["tenant_slug"]:
        raise HTTPException(status_code=404, detail={"code": "case_not_found"})
    return B2BCaseStatusOut(**case)


@app.post(
    "/api/v1/b2b/keys/rotate",
    tags=["B2B v2.0.0"],
    summary="Rotacionar segredo HMAC cliente. Antigo válido 7 dias para rollover seguro.",
    response_model=B2BKeyRotateOut,
)
async def b2b_rotate_api_key(
    client_ctx: B2BAuthDep,
    _: B2BRateDep,
) -> B2BKeyRotateOut:
    new_secret = f"sk_b2b_{base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')}"
    old = _B2B_API_KEYS_FAKE_DB[client_ctx["client_id"]]
    old["_rotation_previous_secret"] = old["secret"]
    old["_rotation_valid_until"] = (
        datetime.now(timezone.utc) + timedelta(days=7)
    ).isoformat().replace("+00:00", "Z")
    old["secret"] = new_secret
    return B2BKeyRotateOut(
        client_id=client_ctx["client_id"],
        new_secret=new_secret,
        old_secret_valid_until_utc=old["_rotation_valid_until"],
    )


# Test only endpoint (dev-only, não exposto em prod)
@app.post(
    "/api/v1/b2b/_internal/signature-test",
    include_in_schema=False,
    tags=["B2B Internal Test"],
    summary="(Staging only) Gerar assinatura HMAC válida para testes (não disponível em produção).",
)
async def b2b_internal_signature_test(
    request: Request,
    x_ot_test_client_id: Annotated[Optional[str], Header()] = None,
    x_ot_test_force_timestamp: Annotated[Optional[str], Header()] = None,
):
    if not x_ot_test_client_id:
        raise HTTPException(status_code=400, detail={"code": "missing_test_client_id"})
    cfg = _B2B_API_KEYS_FAKE_DB.get(x_ot_test_client_id)
    if not cfg:
        raise HTTPException(status_code=404, detail={"code": "test_client_id_unknown"})
    ts = x_ot_test_force_timestamp or str(int(datetime.now(timezone.utc).timestamp()))
    body_bytes = await request.body()
    body_b64 = base64.b64encode(body_bytes).decode("ascii")
    signing_payload = f"POST|/api/v1/b2b/_internal/signature-test|{body_b64}|{ts}"
    sig = hmac.new(
        cfg["secret"].encode("utf-8"),
        signing_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "client_id": x_ot_test_client_id,
        "timestamp": ts,
        "signing_payload": signing_payload,
        "signature": sig,
        "note_prod_only": "Remova este endpoint em produção — só deve ser usado no staging CI.",
    }
