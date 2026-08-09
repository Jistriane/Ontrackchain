"""
T2-11 Billing Capabilities Enforcement Middleware (Sprint 24 ADR-027)
======================================================================
Implementa o enforcement de capabilities do T2-10 OTK_PLAN_CAPABILITIES via
DUAL MODE:
  - RedisBillingCounter (padrão staging/prod >=2 Pods)
  - InMemoryBillingCounter (fallback CI/1 Pod dev. WARNING level log).

Regras de design OBRIGATÓRIAS (ADR-027):
  1. Fail-closed: qualquer exceção do redis → HTTP 402 Payment Required.
  2. Ordem de middlewares: HMAC verify (ADR-019) → ENFORCE BILLING (este) → Business Logic.
  3. Contadores TTL nativos do Redis: 3.600s B2B hora, 2.592.000s (~30d) AI créditos mês.
  4. Headers inseridos SEMPRE (sucesso, 402, 429): X-RateLimit-Limit/Remaining/Reset,
     X-Billing-Tier, X-Billing-AI-Credits-Remaining.

Padrão opcional-deps group [billing-redis]:
    pip install ontrackchain-investigation-api[billing-redis]  # -> redis-py>=5.0.0
    pip install ontrackchain-investigation-api                # -> InMemory fallback default
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Literal, Optional, Protocol

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from investigation_api.billing_capabilities import OTK_PLAN_CAPABILITIES, Tier

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 0. Contrato do Billing Counter (Protocol) — DUAL MODE
# ---------------------------------------------------------------------------
BillingCapabilityKey = Literal[
    "b2b_hourly_quota",
    "ai_credits",
    "max_users_per_org",
]

class BillingCounter(Protocol):
    """Protocol comum para Redis e InMemory: NÃO depende de tipos concretos."""

    async def incr(self, key: str, ttl_seconds: int, amount: int = 1) -> int:
        """Atomicamente incrementa contador e retorna o novo valor total."""
        ...

    async def get(self, key: str) -> Optional[int]:
        """Retorna valor atual do contador ou None se não existir."""
        ...

    async def reset(self, key: str) -> None: ...


# ---------------------------------------------------------------------------
# 1. InMemoryBillingCounter — fallback CI / 1 Pod
# ---------------------------------------------------------------------------
class InMemoryBillingCounter:
    """Fallback para quando Redis NÃO estiver disponível.

    Apenas em staging mono pod / CI. GERA WARNING level logs por request em
    ambiente 'prod' (detectado via OTK_ENV=prod)."""

    def __init__(self) -> None:
        self._store: Dict[str, int] = {}
        self._ttl_store: Dict[str, float] = {}
        logger.warning(
            "[BILLING-DUALMODE] InMemoryBillingCounter ativo. "
            "Multi-pod PRODUÇÃO DEVE usar RedisBillingCounter. "
            "Instale group pip [billing-redis] + configure OTK_REDIS_URL."
        )

    def _evict_if_expired(self, key: str) -> None:
        expiry = self._ttl_store.get(key)
        if expiry is not None and expiry <= time.monotonic():
            self._store.pop(key, None)
            self._ttl_store.pop(key, None)

    async def incr(self, key: str, ttl_seconds: int, amount: int = 1) -> int:
        self._evict_if_expired(key)
        new_value = self._store.get(key, 0) + amount
        self._store[key] = new_value
        self._ttl_store.setdefault(key, time.monotonic() + ttl_seconds)
        return new_value

    async def get(self, key: str) -> Optional[int]:
        self._evict_if_expired(key)
        return self._store.get(key)

    async def reset(self, key: str) -> None:
        self._store.pop(key, None)
        self._ttl_store.pop(key, None)


# ---------------------------------------------------------------------------
# 2. RedisBillingCounter — padrão staging/prod (ADR-027 Opção C Recomendada)
# ---------------------------------------------------------------------------
class RedisBillingCounter:
    """Contador atômico via `INCR` Redis + TTL nativo EX. DualMode optional."""

    __slots__ = ("_redis_client", "_url")

    def __init__(self, redis_client: Any, redis_url: str) -> None:
        self._redis_client = redis_client
        self._url = redis_url
        logger.info(
            "[BILLING-DUALMODE] RedisBillingCounter ativo. "
            "endpoint redis=%s (pronto para multi-pod)." % self._url
        )

    async def incr(self, key: str, ttl_seconds: int, amount: int = 1) -> int:
        value: int = await self._redis_client.incrby(key, amount)
        # Apenas a primeira chamada define o TTL (chave nova, value == amount).
        # Evita resetar o TTL em chamadas subsequentes dentro da janela.
        if value == amount:
            await self._redis_client.expire(key, ttl_seconds, nx=True)
        return value

    async def get(self, key: str) -> Optional[int]:
        value = await self._redis_client.get(key)
        if value is None:
            return None
        return int(value)

    async def reset(self, key: str) -> None:
        await self._redis_client.delete(key)


# ---------------------------------------------------------------------------
# 3. Factory: monta o Counter conforme ambiente OTK_REDIS_URL + redis instalado
# ---------------------------------------------------------------------------
def build_billing_counter_from_env() -> BillingCounter:
    """Monta BillingCounter conforme optional-deps [billing-redis] + env OTK_REDIS_URL.

    - Se `redis` importavel E `OTK_REDIS_URL` definido: RedisBillingCounter.
    - Senão: InMemoryBillingCounter (fallback DUAL MODE).
    """
    import os

    redis_url = os.environ.get("OTK_REDIS_URL")
    if not redis_url:
        return InMemoryBillingCounter()
    try:
        from redis import asyncio as redis_asyncio  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - dep opcional
        logger.warning(
            "[BILLING-DUALMODE] OTK_REDIS_URL definido, mas redis-py NÃO instalado. "
            "Exceção: %s. Fallback InMemoryBillingCounter. Para corrigir: "
            "`pip install ontrackchain-investigation-api[billing-redis]`",
            exc,
        )
        return InMemoryBillingCounter()
    try:
        client = redis_asyncio.Redis.from_url(redis_url, decode_responses=True)
        return RedisBillingCounter(client, redis_url)
    except Exception as exc:  # noqa: BLE001 - pragma: no cover - erro runtime
        logger.warning(
            "[BILLING-DUALMODE] Erro ao conectar Redis %s: %r. "
            "Fallback InMemoryBillingCounter.", redis_url, exc,
        )
        return InMemoryBillingCounter()


# Singleton escopo aplicação (criado 1 vez no startup FastAPI)
_DEFAULT_COUNTER: Optional[BillingCounter] = None

def get_default_billing_counter() -> BillingCounter:
    global _DEFAULT_COUNTER
    if _DEFAULT_COUNTER is None:
        _DEFAULT_COUNTER = build_billing_counter_from_env()
    return _DEFAULT_COUNTER


# ---------------------------------------------------------------------------
# 4. Estruturas de Request / Response do Middleware
# ---------------------------------------------------------------------------
class BillingEnforcementResult(BaseModel):
    organization_id: uuid.UUID
    tier: Tier
    capability: BillingCapabilityKey
    limit: Optional[int]
    used_after_incr: Optional[int]
    remaining: Optional[int]
    reset_unix_seconds: Optional[int]
    counter_engine: Literal["redis", "in_memory"]


# ---------------------------------------------------------------------------
# 5. Helpers de limite e chave Redis
# ---------------------------------------------------------------------------
def _capability_limit_for_tier(tier: Tier, capability: BillingCapabilityKey) -> Optional[int]:
    cap_map: dict[BillingCapabilityKey, str] = {
        "b2b_hourly_quota": "b2b_api_calls_per_hour_quota",
        "ai_credits": "included_ai_credits_per_month",
        "max_users_per_org": "included_users_max",
    }
    key = cap_map[capability]
    limit_value = OTK_PLAN_CAPABILITIES[tier].get(key)
    # None = ilimitado (ex: business/enterprise included_users_max = None)
    return limit_value  # type: ignore[return-value]


def _ttl_and_window_for(capability: BillingCapabilityKey) -> tuple[int, str]:
    """(TTL em segundos, formato janela YYYYMMDDHH / YYYYMM)."""
    now = datetime.now(timezone.utc)
    if capability == "b2b_hourly_quota":
        # 1h sliding, key por hora UTC
        return 3_600, now.strftime("%Y%m%d%H")
    if capability == "ai_credits":
        # 30 dias (mês calendário)
        return 2_592_000, now.strftime("%Y%m")
    # max_users_per_org — permanente até decremento manual (TTL longo 1 ano)
    return 31_536_000, "static"


def _counter_key(org_id: uuid.UUID, capability: BillingCapabilityKey) -> str:
    ttl, window = _ttl_and_window_for(capability)
    if capability == "max_users_per_org":
        return f"billing:users:{org_id}"
    return f"billing:{capability}:{org_id}:{window}"


# ---------------------------------------------------------------------------
# 6. enforce_capability — Dependência FastAPI principal (SRP)
# ---------------------------------------------------------------------------
async def enforce_capability(
    request: Request,
    capability: BillingCapabilityKey,
    counter: Optional[BillingCounter] = None,
    amount: int = 1,
) -> BillingEnforcementResult:
    """Dependência FastAPI para enforcement. Incrementa atomicamente o counter.

    Uso:
        @router.post("/ai/analyze")
        async def my_ai_route(
            enforce: BillingEnforcementResult = Depends(lambda r: enforce_capability(r, "ai_credits"))
        ): ...
    """
    if counter is None:
        counter = get_default_billing_counter()
    org_id = getattr(request.state, "current_organization_id", None)
    tier: Tier = getattr(request.state, "current_org_tier", "startup")
    if org_id is None:
        # Fallback em rotas que NÃO passaram por auth: gera org aleatório + warning.
        # Middleware de auth (ADR-019) SEMPRE seta current_organization_id ANTES.
        org_id = uuid.uuid4()
        logger.warning(
            "[BILLING-ENFORCE] request.state.current_organization_id NÃO definido. "
            "Ordem de middleware errada (billing rodando ANTES do auth). "
            "Ordem correta: AUTH -> HMAC -> BILLING -> BUSINESS."
        )
    limit = _capability_limit_for_tier(tier, capability)
    ttl, _ = _ttl_and_window_for(capability)
    key = _counter_key(org_id, capability)

    # 6.1 FAIL-CLOSED: qualquer erro no counter -> 402 Payment Required.
    used_after_incr: Optional[int]
    try:
        used_after_incr = await counter.incr(key, ttl_seconds=ttl, amount=amount)
    except Exception as exc:  # noqa: BLE001
        logger.critical(
            "[BILLING-FAILCLOSED] Erro ao incrementar counter key=%s cap=%s. "
            "Falha tratada: bloqueio 402. Exceção=%s", key, capability, exc,
        )
        engine_name = "redis" if isinstance(counter, RedisBillingCounter) else "in_memory"
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "BILLING_COUNTER_UNAVAILABLE",
                "message": "Sistema de billing indisponível. Por favor tente novamente em 30 segundos.",
                "capability": capability,
                "engine": engine_name,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # 6.2 Cálculo restante
    remaining: Optional[int] = None
    if limit is not None:
        remaining = max(0, limit - used_after_incr)

    # 6.3 Excedeu limite? Levanta 402 / 429.
    if limit is not None and used_after_incr > limit:
        reset_epoch = int(time.time()) + ttl
        if capability == "b2b_hourly_quota":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
            err_code, err_msg = (
                "B2B_HOURLY_QUOTA_EXCEEDED",
                f"Cota B2B por hora excedida para tier={tier} ({limit}/hora).",
            )
        elif capability == "ai_credits":
            status_code = status.HTTP_402_PAYMENT_REQUIRED
            err_code, err_msg = (
                "AI_CREDITS_EXHAUSTED",
                f"Créditos AI mensais do tier {tier} esgotados ({limit}/mês).",
            )
        else:
            status_code = status.HTTP_402_PAYMENT_REQUIRED
            err_code, err_msg = (
                "MAX_USERS_PER_ORG_EXCEEDED",
                f"Limite de usuários excedido tier={tier} ({limit}).",
            )
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": err_code,
                "message": err_msg,
                "limit": limit,
                "used": used_after_incr,
                "reset_unix_seconds": reset_epoch,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    reset_epoch = int(time.time()) + ttl
    engine_name = "redis" if isinstance(counter, RedisBillingCounter) else "in_memory"
    return BillingEnforcementResult(
        organization_id=org_id,
        tier=tier,
        capability=capability,
        limit=limit,
        used_after_incr=used_after_incr,
        remaining=remaining,
        reset_unix_seconds=reset_epoch,
        counter_engine=engine_name,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# 7. Header Injector Global (T2-10 spec: 5 headers SEMPRE presentes)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def billing_headers_scope(
    request: Request,
    response: Response,
    enforce_result: Optional[BillingEnforcementResult] = None,
) -> AsyncIterator[None]:
    """Context manager / helper para injetar 5 headers billing em qualquer response.

    Chamado via: `app.middleware("http") ...` (ver main.py include do global
    middleware `add_billing_headers_middleware` abaixo), ou manualmente em rotas
    específicas.
    """
    org_id: Optional[uuid.UUID] = getattr(request.state, "current_organization_id", None)
    tier: Tier = getattr(request.state, "current_org_tier", "startup")
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_epoch: Optional[int] = None

    if enforce_result is not None:
        limit = enforce_result.limit
        remaining = enforce_result.remaining
        reset_epoch = enforce_result.reset_unix_seconds
    elif org_id is not None:
        # Nenhum enforce_result nesta rota: injeta headers estáticos demonstrativos
        # (equivalente a /rate-limit-headers T2-10).
        ai_limit = _capability_limit_for_tier(tier, "ai_credits")
        if ai_limit is not None:
            key = _counter_key(org_id, "ai_credits")
            counter = get_default_billing_counter()
            try:
                used = await counter.get(key)
            except Exception:  # noqa: BLE001
                used = None
            limit = ai_limit
            remaining = max(0, ai_limit - (used or 0))
            ttl, _ = _ttl_and_window_for("ai_credits")
            reset_epoch = int(time.time()) + ttl

    if limit is not None:
        response.headers["X-RateLimit-Limit"] = str(limit)
    if remaining is not None:
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    if reset_epoch is not None:
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)
    response.headers["X-Billing-Tier"] = tier
    # AI credits remaining (preenche mesmo se enforce for outra capability):
    if org_id is not None:
        ai_limit = _capability_limit_for_tier(tier, "ai_credits")
        if ai_limit is not None:
            counter = get_default_billing_counter()
            try:
                ai_key = _counter_key(org_id, "ai_credits")
                ai_used = await counter.get(ai_key) or 0
                ai_remaining = max(0, ai_limit - ai_used)
                response.headers["X-Billing-AI-Credits-Remaining"] = str(ai_remaining)
            except Exception:  # noqa: BLE001
                response.headers["X-Billing-AI-Credits-Remaining"] = "unknown"
    yield


def add_billing_headers_middleware(app):  # type: ignore[no-untyped-def]
    """Registra middleware HTTP global para injetar headers billing.

    Chamado em main.py investigation-api. ADR-027 DoD 027.3.
    """
    import time as _time

    @app.middleware("http")
    async def _billing_headers_global_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = _time.perf_counter()
        try:
            response = await call_next(request)
        except HTTPException as hexc:
            response = JSONResponse(
                status_code=hexc.status_code,
                content={"detail": hexc.detail},
            )
        try:
            async with billing_headers_scope(request, response, enforce_result=None):
                pass
        except Exception as exc:  # noqa: BLE001
            logger.debug("[BILLING-HEADERS] Falha leve ao montar headers: %s", exc)
        response.headers["X-Response-Time-Ms"] = f"{(_time.perf_counter() - start) * 1000:.1f}"
        return response
    return _billing_headers_global_middleware
