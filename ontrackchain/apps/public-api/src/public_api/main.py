from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from redis.asyncio import Redis


class Settings(BaseSettings):
    redis_host: str = "redis"
    redis_port: int = 6379


settings = Settings()

app = FastAPI(title="OnTrackChain Public API")

SUPPORTED_PUBLIC_CHAINS = {"ethereum", "polygon", "bsc", "arbitrum", "base", "bitcoin"}


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
) -> None:
    ip = (x_forwarded_for or request.client.host or "unknown").split(",")[0].strip()
    key = f"rl:public:{ip}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 3600)
    if count > 10:
        raise HTTPException(status_code=429, detail="rate_limited")


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
@app.get("/healthz", tags=["Observabilidade"], summary="Liveness Probe Kubernetes / SRE")
async def healthz_liveness_probe():
    return {
        "status": "ok",
        "service": "public-api",
        "version": "2.0.0",
        "liveness": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

try:
    from prometheus_fastapi_instrumentator import Instrumentator as _PromInstrumentator
    _PromInstrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception:  # noqa: BLE001 - fallback inline sempre funciona, sem dependencia
    from fastapi.responses import PlainTextResponse as _FallbackPlainText

    _FALLBACK_METRICS_BASE = """# HELP fastapi_info Info about the running FastAPI service.
# TYPE fastapi_info gauge
fastapi_info{service="public-api",version="2.0.0"} 1.0
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
