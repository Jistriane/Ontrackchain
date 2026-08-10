"""
Sprint 24 T2-11 - Testes Contrato Billing Enforcement Middleware
=================================================================
ADR-027: Fail-Closed 402 + DUAL MODE Redis/InMemory + 5 headers globais.

Classes de testes:
  1. TestInMemoryCounter (4) — monotonicidade INCR, reset, TTL, get None.
  2. TestEnforceCapabilityDepends (7) — sucesso 200, 429 TooMany B2B hora,
     402 AI credits esgotados, 402 max users, fail-closed RedisConnectionError,
     org_id None gera warning log, counter engine correta.
  3. TestHeadersBillingGlobal (4) — X-RateLimit, X-Billing-Tier,
     X-Billing-AI-Credits-Remaining, X-RateLimit-Reset em responses de sucesso e erro 402.
Total: 15 testes contrato (100% ADR-027 DoD 027.4).
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from investigation_api.billing_capabilities import OTK_PLAN_CAPABILITIES
from investigation_api.billing_enforcement import (
    BillingEnforcementResult,
    InMemoryBillingCounter,
    add_billing_headers_middleware,
    build_billing_counter_from_env,
    enforce_capability,
    get_default_billing_counter,
)


# ---------------------------------------------------------------------------
# Helpers: montar Request.state.* conforme Auth middleware upstream
# ---------------------------------------------------------------------------
def _build_request_with_org(
    org_id: uuid.UUID | None = None,
    tier: str = "startup",
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/fake",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
    }
    req = Request(scope)
    if org_id is None:
        org_id = uuid.uuid4()
    req.state.current_organization_id = org_id
    req.state.current_org_tier = tier
    req.state.request_id = str(uuid.uuid4())
    return req


# ---------------------------------------------------------------------------
# 1. Suite TestInMemoryCounter (4)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInMemoryCounter:
    @pytest.mark.asyncio
    async def test_inmemory_incr_monotonic_and_ttl(self) -> None:
        c = InMemoryBillingCounter()
        key = "test_incr_monotonic"
        for i in range(1, 6):
            v = await c.incr(key, ttl_seconds=3600)
            assert v == i, f"InMemory NÃO é monotônico, esperado {i} obtido {v}"

    @pytest.mark.asyncio
    async def test_inmemory_get_apos_incr(self) -> None:
        c = InMemoryBillingCounter()
        key = "test_get"
        await c.incr(key, ttl_seconds=3600, amount=13)
        assert await c.get(key) == 13

    @pytest.mark.asyncio
    async def test_inmemory_reset_zera_contador(self) -> None:
        c = InMemoryBillingCounter()
        key = "test_reset"
        await c.incr(key, ttl_seconds=3600, amount=77)
        await c.reset(key)
        assert await c.get(key) is None

    @pytest.mark.asyncio
    async def test_inmemory_ttl_expira_auto(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        c = InMemoryBillingCounter()
        key = "test_ttl"
        await c.incr(key, ttl_seconds=1, amount=5)
        assert await c.get(key) == 5
        # Monkey-patch time.monotonic() para avançar 2 segundos (passou TTL)
        future_time = time.monotonic() + 2
        monkeypatch.setattr(time, "monotonic", lambda: future_time)
        assert await c.get(key) is None, "TTL expirou mas valor ainda está presente"


# ---------------------------------------------------------------------------
# 2. Suite TestEnforceCapabilityDepends (7)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEnforceCapabilityDepends:
    @pytest.mark.asyncio
    async def test_enforce_b2b_quota_sucesso_dentro_limite(self) -> None:
        org_id = uuid.uuid4()
        counter = InMemoryBillingCounter()
        request = _build_request_with_org(org_id=org_id, tier="business")
        # Business tem b2b_api_calls_per_hour_quota=2000. Consome 1.
        result: BillingEnforcementResult = await enforce_capability(
            request, "b2b_hourly_quota", counter=counter
        )
        assert result.limit == 2_000
        assert result.used_after_incr == 1
        assert result.remaining == 1_999
        assert result.organization_id == org_id
        assert result.tier == "business"
        assert result.counter_engine == "in_memory"

    @pytest.mark.asyncio
    async def test_enforce_b2b_quota_excedida_429(self) -> None:
        org_id = uuid.uuid4()
        counter = InMemoryBillingCounter()
        request = _build_request_with_org(org_id=org_id, tier="startup")
        # Startup = 200. Consome 200 antes, depois o 201 deve dar 429.
        for _ in range(200):
            await enforce_capability(request, "b2b_hourly_quota", counter=counter)
        with pytest.raises(HTTPException) as exc_info:
            await enforce_capability(request, "b2b_hourly_quota", counter=counter)
        assert exc_info.value.status_code == 429
        detail = exc_info.value.detail or {}
        assert isinstance(detail, dict)
        assert detail["code"] == "B2B_HOURLY_QUOTA_EXCEEDED"
        assert detail["limit"] == 200

    @pytest.mark.asyncio
    async def test_enforce_ai_credits_esgotados_402(self) -> None:
        org_id = uuid.uuid4()
        counter = InMemoryBillingCounter()
        request = _build_request_with_org(org_id=org_id, tier="enterprise")
        # Enterprise = 1.000.000 AI. Consome 999.999 + 1 = 1.000.001 (>limite)
        await enforce_capability(
            request, "ai_credits", counter=counter, amount=999_999
        )
        with pytest.raises(HTTPException) as exc_info:
            await enforce_capability(request, "ai_credits", counter=counter, amount=2)
        assert exc_info.value.status_code == 402
        detail = exc_info.value.detail or {}
        assert isinstance(detail, dict)
        assert detail["code"] == "AI_CREDITS_EXHAUSTED"
        assert detail["limit"] == 1_000_000

    @pytest.mark.asyncio
    async def test_enforce_max_users_startup_402(self) -> None:
        org_id = uuid.uuid4()
        counter = InMemoryBillingCounter()
        request = _build_request_with_org(org_id=org_id, tier="startup")
        for _ in range(5):
            await enforce_capability(request, "max_users_per_org", counter=counter)
        with pytest.raises(HTTPException) as exc_info:
            await enforce_capability(request, "max_users_per_org", counter=counter)
        assert exc_info.value.status_code == 402
        detail = exc_info.value.detail or {}
        assert isinstance(detail, dict)
        assert detail["code"] == "MAX_USERS_PER_ORG_EXCEEDED"

    @pytest.mark.asyncio
    async def test_enforce_fail_closed_counter_exception_402(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        class FailingCounter:
            async def incr(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                raise ConnectionError("redis connection refused - simulate down")

            async def get(self, key):  # type: ignore[no-untyped-def]
                return None

            async def reset(self, key):  # type: ignore[no-untyped-def]
                return None

        request = _build_request_with_org(tier="startup")
        with caplog.at_level(logging.CRITICAL):
            with pytest.raises(HTTPException) as exc_info:
                await enforce_capability(
                    request, "b2b_hourly_quota", counter=FailingCounter()  # type: ignore[arg-type]
                )
        assert exc_info.value.status_code == 402
        assert any("[BILLING-FAILCLOSED]" in rec.message for rec in caplog.records)
        detail = exc_info.value.detail or {}
        assert isinstance(detail, dict)
        assert detail["code"] == "BILLING_COUNTER_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_enforce_org_none_warning_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        scope = {"type": "http", "method": "GET", "path": "/", "query_string": b"", "headers": [], "server": ("t", 80)}
        request = Request(scope)
        counter = InMemoryBillingCounter()
        with caplog.at_level(logging.WARNING):
            result = await enforce_capability(request, "ai_credits", counter=counter)
        assert result.counter_engine == "in_memory"
        assert any(
            "current_organization_id NÃO definido" in rec.message
            for rec in caplog.records
        )

    @pytest.mark.asyncio
    async def test_counter_factory_noredis_env_cai_inmemory(self, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        monkeypatch.delenv("OTK_REDIS_URL", raising=False)
        counter = build_billing_counter_from_env()
        assert isinstance(counter, InMemoryBillingCounter)


# ---------------------------------------------------------------------------
# 3. Suite TestHeadersBillingGlobal (4)
# ---------------------------------------------------------------------------
@pytest.mark.integration
class TestHeadersBillingGlobal:
    @pytest.fixture()
    def app_with_billing(self) -> FastAPI:  # type: ignore[return-value]
        app = FastAPI(title="test-billing-headers")
        add_billing_headers_middleware(app)

        @app.get("/healthz")
        async def healthz(request: Request):  # type: ignore[no-untyped-def]
            # Simula auth upstream setando org/tier
            request.state.current_organization_id = uuid.UUID(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            )
            request.state.current_org_tier = "business"
            return {"status": "ok"}

        @app.get("/ai/force-exceed")
        async def force_exceed(request: Request):  # type: ignore[no-untyped-def]
            request.state.current_organization_id = uuid.UUID(
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
            )
            request.state.current_org_tier = "startup"
            # Consome 2.501 AI (Startup = 2500) → HTTPException 402
            result = await enforce_capability(
                request, "ai_credits", counter=InMemoryBillingCounter(), amount=2_501
            )
            return {"unreachable": result}

        return app

    def test_healthz_resposta_possui_5_headers_billing(self, app_with_billing: FastAPI) -> None:
        with TestClient(app_with_billing) as cli:
            r = cli.get("/healthz")
            assert r.status_code == 200
            h = r.headers
            assert "X-RateLimit-Limit" in h
            assert "X-RateLimit-Remaining" in h
            assert "X-RateLimit-Reset" in h
            assert "X-Billing-Tier" in h and h["X-Billing-Tier"] == "business"
            assert "X-Billing-AI-Credits-Remaining" in h

    def test_402_ai_excedido_ainda_tem_headers_billing(self, app_with_billing: FastAPI) -> None:
        with TestClient(app_with_billing) as cli:
            r = cli.get("/ai/force-exceed")
            assert r.status_code == 402
            h = r.headers
            assert "X-Billing-Tier" in h, "Mesmo 402 deve retornar X-Billing-Tier"
            assert "X-Billing-AI-Credits-Remaining" in h
            assert "X-Response-Time-Ms" in h, "Middleware NÃO injetou ResponseTimeMs"

    def test_billing_ai_remaining_e_2500_apos_incr_0_startup(self, app_with_billing: FastAPI) -> None:
        """Startup 2500 AI: 0 usados -> remaining = 2500."""
        with TestClient(app_with_billing) as cli:
            # Cria org nova (UUID random) para evitar cache global InMemory
            @app_with_billing.get("/ai/new-org")
            async def new_org(request: Request):  # type: ignore[no-untyped-def]
                request.state.current_organization_id = uuid.uuid4()
                request.state.current_org_tier = "startup"
                return {"ok": True}

            r = cli.get("/ai/new-org")
            remaining = int(r.headers["X-Billing-AI-Credits-Remaining"])
            assert remaining == OTK_PLAN_CAPABILITIES["startup"]["included_ai_credits_per_month"]

    def test_x_ratelimit_reset_e_unix_future(self, app_with_billing: FastAPI) -> None:
        with TestClient(app_with_billing) as cli:
            r = cli.get("/healthz")
            reset_epoch = int(r.headers["X-RateLimit-Reset"])
            assert reset_epoch > int(time.time()), "Reset deve ser no futuro (UTC unix epoch)"


# ---------------------------------------------------------------------------
# 4. Teste de regressão: InMemory não compartilha chaves entre orgs
# ---------------------------------------------------------------------------
@pytest.mark.unit
def test_duas_orgs_nao_compartilham_contadores_inmemory() -> None:
    async def _runner() -> None:
        c = InMemoryBillingCounter()
        org_a = uuid.UUID("11111111-1111-1111-1111-111111111111")
        org_b = uuid.UUID("22222222-2222-2222-2222-222222222222")
        req_a = _build_request_with_org(org_id=org_a, tier="startup")
        req_b = _build_request_with_org(org_id=org_b, tier="startup")
        # Startup tier b2b_hourly_quota = 200. Org A: 199 + 1 = 200 (cheio, remaining 0). Org B: 1 (isolado).
        await enforce_capability(req_a, "b2b_hourly_quota", counter=c, amount=199)
        a = await enforce_capability(req_a, "b2b_hourly_quota", counter=c)
        b = await enforce_capability(req_b, "b2b_hourly_quota", counter=c)
        assert a.remaining == 0, f"Esperado 0 (200-200), recebeu {a.remaining}"
        assert a.used_after_incr == 200
        assert b.used_after_incr == 1, "Org B contador começa em 1, NÃO em 201 (isolamento por org_id)."
    asyncio.run(_runner())
