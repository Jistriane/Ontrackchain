"""
ai_service.py — Sprint 25 T2-12 enforcement AI credits integrado
SRP APIRouter prefix /api/v1/ai. 2 rotas:
  POST /analyze         → ai_credits enforcement (1 AI credit por request)
  POST /summarize-docs  → ai_credits enforcement (3 AI credits por request — sumarização é mais custosa)
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Literal

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field

from investigation_api.billing_enforcement import BillingEnforcementResult, enforce_capability

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["Serviços de AI / LLMs"],
)


# ---------------------------------------------------------------------------
# 1. Schemas
# ---------------------------------------------------------------------------
class AIAnalyzeRequest(BaseModel):
    case_id: uuid.UUID = Field(description="ID do caso investigativo.")
    prompt_personalizado: str | None = Field(default=None, max_length=8000)
    include_documentos_ids: List[uuid.UUID] = Field(default_factory=list)


class AIAnalyzeResponse(BaseModel):
    status: Literal["completed", "queued"] = "completed"
    entidades_extraidas: int = 42
    resumo_curto: str = "Resumo AI modelo gerado (placebo enforcement ativo)."
    billing_enforcement_debug: dict = Field(description="Info do enforcement middleware.")


class AISummarizeDocsRequest(BaseModel):
    document_ids: List[uuid.UUID]
    comprimento_maximo_palavras: int = Field(default=500, ge=100, le=5000)


class AISummarizeResponse(BaseModel):
    status: Literal["completed"] = "completed"
    numero_documentos_sumarizados: int
    resumo_geral: str = "Resumo multi-documentos."
    billing_enforcement_debug: dict


# ---------------------------------------------------------------------------
# 2. Rotas com enforcement de AI credits
# ---------------------------------------------------------------------------
@router.post("/analyze", response_model=AIAnalyzeResponse)
async def ai_analyze(
    _enforce: Annotated[
        BillingEnforcementResult,
        Depends(lambda r: enforce_capability(r, "ai_credits", amount=1)),
    ],
    payload: AIAnalyzeRequest = Body(...),
) -> AIAnalyzeResponse:
    # LLM real aqui em S27 quando handoff. Por enquanto resposta placebo.
    return AIAnalyzeResponse(
        entidades_extraidas=42,
        billing_enforcement_debug={
            "tier": _enforce.tier,
            "used": _enforce.used_after_incr,
            "remaining": _enforce.remaining,
            "engine": _enforce.counter_engine,
        },
    )


@router.post("/summarize-docs", response_model=AISummarizeResponse)
async def ai_summarize_docs(
    _enforce: Annotated[
        BillingEnforcementResult,
        Depends(lambda r: enforce_capability(r, "ai_credits", amount=3)),
    ],
    payload: AISummarizeDocsRequest = Body(...),
) -> AISummarizeResponse:
    # Placeholder real em S27. Sumarização = 3x mais cara (3 AI credits).
    return AISummarizeResponse(
        numero_documentos_sumarizados=len(payload.document_ids),
        billing_enforcement_debug={
            "tier": _enforce.tier,
            "used": _enforce.used_after_incr,
            "remaining": _enforce.remaining,
            "engine": _enforce.counter_engine,
        },
    )
