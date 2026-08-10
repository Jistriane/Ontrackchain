"""
public_b2b_v2.py — Sprint 25 T2-12 enforcement B2B hourly quota integrado
SRP APIRouter prefix /api/v2/public/b2b. 2 rotas:
  POST /screening          → b2b_hourly_quota enforcement
  GET  /entity/{id}        → b2b_hourly_quota enforcement
"""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from investigation_api.billing_enforcement import BillingEnforcementResult, enforce_capability

router = APIRouter(
    prefix="/api/v2/public/b2b",
    tags=["Public API v2 B2B HMAC (ADR-019)"],
)


async def _enforce_b2b_hourly_quota(request: Request) -> BillingEnforcementResult:
    """Helper sync wrapper Depends (evita lambda em Depends = bug em algumas versões FastAPI)."""
    return await enforce_capability(request, "b2b_hourly_quota")


class B2BScreeningRequest(BaseModel):
    cpf_cnpj: str = Field(pattern=r"^\d{11}$|^\d{14}$", max_length=14)
    nome_completo: str | None = None
    data_nascimento: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class B2BScreeningResponse(BaseModel):
    request_id: str = "req-id-fake"
    risco_score: float = 18.4
    risco_nivel: Literal["baixo", "medio", "alto"] = "baixo"
    billing_enforcement_debug: dict


@router.post("/screening", response_model=B2BScreeningResponse)
async def b2b_screening_post(
    _enforce: Annotated[
        BillingEnforcementResult,
        Depends(_enforce_b2b_hourly_quota),
    ],
    payload: B2BScreeningRequest,
) -> B2BScreeningResponse:
    return B2BScreeningResponse(
        billing_enforcement_debug={
            "tier": _enforce.tier,
            "used": _enforce.used_after_incr,
            "remaining": _enforce.remaining,
            "engine": _enforce.counter_engine,
        }
    )


@router.get("/entity/{entity_id}", response_model=B2BScreeningResponse)
async def b2b_entity_get(
    _enforce: Annotated[
        BillingEnforcementResult,
        Depends(_enforce_b2b_hourly_quota),
    ],
    entity_id: str,
) -> B2BScreeningResponse:
    return B2BScreeningResponse(
        billing_enforcement_debug={
            "tier": _enforce.tier,
            "used": _enforce.used_after_incr,
            "remaining": _enforce.remaining,
            "engine": _enforce.counter_engine,
        }
    )
