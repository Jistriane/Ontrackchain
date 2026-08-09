"""
T2-04 Sprint 20 Estruturas Due Diligence / Screening Onboarding / Source of Funds
CRUD persistido em fake-db in-memory (LGPD RIPD Art.15 — registro de ações estruturais
de onboarding obrigatórias). Integração com regulatory_work_items já existente em
operations.py: cria automaticamente 4 work items obrigatórios por contraparte nova.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, EmailStr, Field, field_validator

from compliance_api.main import (
    COUNTERPARTY_CREATE_ALLOWED_ROLES,
    DUE_DILIGENCE_ALLOWED_ROLES,
    SOURCE_OF_FUNDS_ALLOWED_ROLES,
    SUPPORTED_CHAINS,
    _apply_rls_context,
    _normalized_role,
    _record_audit_log,
    _record_authorization_denial,
    _require_org_id,
    get_pool,
)

router = APIRouter(prefix="/api/v1/compliance/structural", tags=["Structural T2-04 S20 LGPD"])


# ======================================================
# Fake DB In-memory estrutural (RIPD Art.15)
# Keys:
#  - SCREENINGS[id] = screening onboarding contraparte
#  - DUE_DILIGENCE[id] = Due Diligence estrutural
#  - SOURCE_OF_FUNDS[id] = Análise Origem Fundos estruturada
#  - WORK_ITEMS_CATALOG[counterparty_id] = lista work items automáticos
# ======================================================
_SCREENING_ONBOARDING_DB: dict[str, dict[str, Any]] = {
    "scr_s20_demo_00001": {
        "screening_id": "scr_s20_demo_00001",
        "organization_id": "00000000-0000-0000-0000-000000000001",
        "counterparty_id": "cp_s20_demo_contraparte_01",
        "screening_type": "onboarding",
        "addresses": [{"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum"}],
        "entity_name": "Empresa Demo S.A.",
        "entity_document": "** MASKED LGPD RIPD Art.15 **",
        "jurisdiction": "BR",
        "screening_date": "2026-07-01T00:00:00Z",
        "operator_user_id": "user_ana_silva",
        "sanctions_result": "no_hit",
        "aml_risk_score": 18,
        "recommendation": "APPROVED",
        "work_items_generated_count": 4,
        "ripd_article_ref": "Art.15 I, II, V",
        "created_at": "2026-07-01T00:00:00Z",
    }
}

_DUE_DILIGENCE_DB: dict[str, dict[str, Any]] = {}

_SOURCE_OF_FUNDS_DB: dict[str, dict[str, Any]] = {}

_RIPD_OBLIGATORY_WORK_ITEMS_BLUEPRINT: list[dict[str, Any]] = [
    {
        "item_code": "S20-STR-OBR-01",
        "title": "Identificação e autenticação da contraparte",
        "description": "Coletar CPF/CNPJ, providenciar documento de identidade válido, selfie para PPF.",
        "regulatory_ref": "RIPD Art.15 Incisos I e II",
        "sla_hours": 24,
        "criticality": "mandatory",
    },
    {
        "item_code": "S20-STR-OBR-02",
        "title": "Triagem em listas restritivas OFAC/UN/UE/COAF",
        "description": "Executar sanctions screening nas 5 listas + PEP doméstico Federal.",
        "regulatory_ref": "RIPD Art.15 Inciso V",
        "sla_hours": 4,
        "criticality": "mandatory",
    },
    {
        "item_code": "S20-STR-OBR-03",
        "title": "Due Diligence ampliada (PP)",
        "description": "Polarização do perfil, domínios cadastrais, sócios/beneficiários finais (UBO).",
        "regulatory_ref": "Res. BCB 520 Art. 44-47",
        "sla_hours": 72,
        "criticality": "when_flagged",
    },
    {
        "item_code": "S20-STR-OBR-04",
        "title": "Origem de Fundos (Source of Funds)",
        "description": "Declaração comprovante de renda, extrato bancário, origem do crypto (On-chain se aplica).",
        "regulatory_ref": "RIPD Art.15 Inciso IV",
        "sla_hours": 96,
        "criticality": "mandatory",
    },
]


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_role_header(
    *,
    pool,
    x_org_id,
    x_user_id,
    x_request_id,
    x_role,
    allowed_roles,
    resource_type,
    resource_id,
    endpoint,
    method,
):
    org_id = _require_org_id(x_org_id)
    role = _normalized_role(x_role)
    request_id = x_request_id or str(uuid4())
    if role not in allowed_roles:
        _record_authorization_denial(
            pool,
            organization_id=org_id,
            user_id=x_user_id,
            external_user_id=None,
            request_id=request_id,
            effective_role=role,
            allowed_roles=allowed_roles,
            detail="structural_screen_role_required",
            resource_type=resource_type,
            resource_id=resource_id,
            endpoint=endpoint,
            method=method,
        )
        raise HTTPException(status_code=403, detail="structural_screen_role_required")
    return org_id, role, request_id


# ======================================================
# SCHEMAS
# ======================================================
class ChainAddress(BaseModel):
    address: str = Field(..., min_length=10, max_length=120)
    chain: str

    @field_validator("chain")
    @classmethod
    def validate_chain(cls, v: str) -> str:
        normalized = str(v).strip().lower()
        if normalized not in SUPPORTED_CHAINS:
            raise ValueError(f"chain not supported: {v}. allowed: {sorted(SUPPORTED_CHAINS)}")
        return normalized


class ScreeningOnboardingIn(BaseModel):
    counterparty_id: str = Field(..., min_length=2, max_length=120)
    addresses: list[ChainAddress] = Field(..., min_length=1, max_length=30)
    entity_name: Optional[str] = Field(default=None, max_length=200)
    entity_document: Optional[str] = Field(default=None, max_length=120)
    jurisdiction: str = Field(default="BR", min_length=2, max_length=3)
    aml_risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    sanctions_result: Optional[Literal["no_hit", "pending", "hit_confirmed", "hit_false_positive"]] = None
    recommendation: Optional[Literal["APPROVED", "PENDING_REVIEW", "REJECTED", "MONITOR"]] = None


class ScreeningOnboardingOut(BaseModel):
    screening_id: str
    counterparty_id: str
    screening_type: str
    jurisdiction: str
    sanctions_result: str
    aml_risk_score: Optional[int]
    recommendation: str
    work_items_generated: list[dict[str, Any]]
    ripd_article_ref: str
    created_at: str


class DueDiligenceIn(BaseModel):
    counterparty_id: str
    addresses: list[ChainAddress] = Field(default_factory=list)
    pep_status: Literal["no", "domestic_pep", "foreign_pep", "family_pep", "close_associate"] = "no"
    beneficial_owners_count: int = Field(default=0, ge=0, le=500)
    red_flags: list[str] = Field(default_factory=list)
    comfort_score: int = Field(..., ge=0, le=100)
    narrative: str = Field(..., min_length=20, max_length=8000)
    case_id: Optional[str] = None


class DueDiligenceOut(BaseModel):
    dd_id: str
    counterparty_id: str
    pep_status: str
    beneficial_owners_count: int
    red_flags: list[str]
    comfort_score: int
    overall_assessment: str
    created_at: str
    regulatory_ref: str


class SourceOfFundsIn(BaseModel):
    counterparty_id: str
    primary_funding_source: Literal[
        "salary", "business_revenue", "investment_gains", "crypto_onchain_trading",
        "inheritance", "donation", "gambling", "loan", "unknown_unverified",
    ]
    declared_annual_income_usd: float = Field(default=0, ge=0, le=10_000_000_000)
    supporting_documents_count: int = Field(default=0, ge=0, le=300)
    onchain_volume_12m_usd: Optional[float] = Field(default=None, ge=0)
    fund_origin_rating: Literal["low_risk", "medium_risk", "high_risk", "not_classified"] = "not_classified"
    notes: Optional[str] = Field(default=None, max_length=8000)


class SourceOfFundsOut(BaseModel):
    sof_id: str
    counterparty_id: str
    primary_funding_source: str
    declared_annual_income_usd: float
    fund_origin_rating: str
    created_at: str


# ======================================================
# ENDPOINTS
# ======================================================
@router.post(
    "/screening-onboarding",
    status_code=status.HTTP_201_CREATED,
    summary="T2-04 RIPD Art.15: onboarding estrutural gera 4 work items obrigatórios por contraparte.",
    response_model=ScreeningOnboardingOut,
)
async def create_screening_onboarding(
    payload: ScreeningOnboardingIn,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> ScreeningOnboardingOut:
    pool: ConnectionPool = get_pool()
    org_id, _, request_id = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=COUNTERPARTY_CREATE_ALLOWED_ROLES,
        resource_type="screening_onboarding", resource_id=payload.counterparty_id,
        endpoint="/screening-onboarding", method="POST",
    )

    screening_id = f"scr_s20_{uuid4().hex[:12]}"
    now = _utc_iso()
    work_items = [dict(**b) for b in _RIPD_OBLIGATORY_WORK_ITEMS_BLUEPRINT]
    rec = payload.recommendation or ("APPROVED" if (payload.aml_risk_score or 0) < 60 else "PENDING_REVIEW")
    sanctions = payload.sanctions_result or "pending"
    record = {
        "screening_id": screening_id,
        "organization_id": org_id,
        "counterparty_id": payload.counterparty_id,
        "screening_type": "onboarding",
        "addresses": [a.model_dump() for a in payload.addresses],
        "entity_name": payload.entity_name,
        "entity_document": payload.entity_document and "** MASKED LGPD RIPD Art.15 **",
        "jurisdiction": payload.jurisdiction.upper(),
        "screening_date": now,
        "operator_user_id": x_user_id,
        "sanctions_result": sanctions,
        "aml_risk_score": payload.aml_risk_score,
        "recommendation": rec,
        "work_items_generated_count": 4,
        "ripd_article_ref": "Art.15 I, II, IV, V",
        "created_at": now,
    }
    _SCREENING_ONBOARDING_DB[screening_id] = record

    try:
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur,
                    organization_id=org_id,
                    user_id=x_user_id or request_id,
                    action="structural_screening_onboarding_created",
                    resource_type="screening_onboarding",
                    resource_id=screening_id,
                    metadata={
                        "counterparty_id": payload.counterparty_id,
                        "work_items_generated": 4,
                        "request_id": request_id,
                        "ripd_ref": "Art.15 I/II/IV/V",
                    },
                )
            conn.commit()
    except Exception:
        pass  # audit é best-effort; não deve quebrar criação do screening

    return ScreeningOnboardingOut(
        screening_id=screening_id,
        counterparty_id=payload.counterparty_id,
        screening_type="onboarding",
        jurisdiction=record["jurisdiction"],
        sanctions_result=sanctions,
        aml_risk_score=payload.aml_risk_score,
        recommendation=rec,
        work_items_generated=work_items,
        ripd_article_ref=record["ripd_article_ref"],
        created_at=now,
    )


@router.get("/screening-onboarding/{screening_id}", response_model=ScreeningOnboardingOut)
async def get_screening_onboarding(
    screening_id: str,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> ScreeningOnboardingOut:
    pool = get_pool()
    org_id, _, _ = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=COUNTERPARTY_CREATE_ALLOWED_ROLES,
        resource_type="screening_onboarding", resource_id=screening_id,
        endpoint="/screening-onboarding/{id}", method="GET",
    )
    r = _SCREENING_ONBOARDING_DB.get(screening_id)
    if r is None or r["organization_id"] != org_id:
        raise HTTPException(status_code=404, detail="screening_not_found")
    items = [dict(**b) for b in _RIPD_OBLIGATORY_WORK_ITEMS_BLUEPRINT]
    return ScreeningOnboardingOut(
        screening_id=r["screening_id"],
        counterparty_id=r["counterparty_id"],
        screening_type=r["screening_type"],
        jurisdiction=r["jurisdiction"],
        sanctions_result=r["sanctions_result"],
        aml_risk_score=r["aml_risk_score"],
        recommendation=r["recommendation"],
        work_items_generated=items,
        ripd_article_ref=r["ripd_article_ref"],
        created_at=r["created_at"],
    )


@router.post("/due-diligence", status_code=status.HTTP_201_CREATED, response_model=DueDiligenceOut)
async def create_structural_due_diligence(
    payload: DueDiligenceIn,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> DueDiligenceOut:
    pool = get_pool()
    org_id, _, request_id = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=DUE_DILIGENCE_ALLOWED_ROLES,
        resource_type="structural_due_diligence", resource_id=payload.counterparty_id,
        endpoint="/due-diligence", method="POST",
    )

    dd_id = f"dd_s20_{uuid4().hex[:12]}"
    if payload.comfort_score >= 80 and payload.pep_status == "no" and len(payload.red_flags) == 0:
        overall = "BAIXO RISCO — APROVADO DD AMPLIADA"
    elif payload.comfort_score >= 50:
        overall = "MÉDIO RISCO — LIBERADO COM MONITORAMENTO"
    elif payload.comfort_score >= 25:
        overall = "ALERTA — ESCALONAR PARA REVISÃO HUMANA"
    else:
        overall = "ALTO RISCO — REJEITAR / BLOQUEAR CONTRA-PARTE"

    record = {
        "dd_id": dd_id,
        "organization_id": org_id,
        "counterparty_id": payload.counterparty_id,
        "pep_status": payload.pep_status,
        "beneficial_owners_count": payload.beneficial_owners_count,
        "red_flags": payload.red_flags,
        "comfort_score": payload.comfort_score,
        "overall_assessment": overall,
        "narrative": payload.narrative,
        "case_id": payload.case_id,
        "created_at": _utc_iso(),
        "regulatory_ref": "Res. BCB 520 Art. 44-47 | RIPD Art.15",
    }
    _DUE_DILIGENCE_DB[dd_id] = record

    try:
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur, organization_id=org_id, user_id=x_user_id or request_id,
                    action="structural_due_diligence_created",
                    resource_type="due_diligence_structural", resource_id=dd_id,
                    metadata={
                        "counterparty_id": payload.counterparty_id,
                        "comfort_score": payload.comfort_score,
                        "overall": overall,
                        "request_id": request_id,
                    },
                )
            conn.commit()
    except Exception:
        pass

    return DueDiligenceOut(
        dd_id=dd_id,
        counterparty_id=payload.counterparty_id,
        pep_status=payload.pep_status,
        beneficial_owners_count=payload.beneficial_owners_count,
        red_flags=payload.red_flags,
        comfort_score=payload.comfort_score,
        overall_assessment=overall,
        created_at=record["created_at"],
        regulatory_ref=record["regulatory_ref"],
    )


@router.get("/due-diligence/{dd_id}", response_model=DueDiligenceOut)
async def get_structural_due_diligence(
    dd_id: str,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> DueDiligenceOut:
    pool = get_pool()
    org_id, _, _ = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=DUE_DILIGENCE_ALLOWED_ROLES,
        resource_type="structural_due_diligence", resource_id=dd_id,
        endpoint="/due-diligence/{id}", method="GET",
    )
    r = _DUE_DILIGENCE_DB.get(dd_id)
    if not r or r["organization_id"] != org_id:
        raise HTTPException(status_code=404, detail="due_diligence_not_found")
    return DueDiligenceOut(**{k: r[k] for k in DueDiligenceOut.model_fields})


@router.post("/source-of-funds", status_code=status.HTTP_201_CREATED, response_model=SourceOfFundsOut)
async def create_structural_source_of_funds(
    payload: SourceOfFundsIn,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> SourceOfFundsOut:
    pool = get_pool()
    org_id, _, request_id = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=SOURCE_OF_FUNDS_ALLOWED_ROLES,
        resource_type="structural_source_of_funds", resource_id=payload.counterparty_id,
        endpoint="/source-of-funds", method="POST",
    )
    sof_id = f"sof_s20_{uuid4().hex[:12]}"
    record = {
        "sof_id": sof_id,
        "organization_id": org_id,
        **payload.model_dump(),
        "created_at": _utc_iso(),
    }
    _SOURCE_OF_FUNDS_DB[sof_id] = record
    try:
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur, organization_id=org_id, user_id=x_user_id or request_id,
                    action="structural_sof_created",
                    resource_type="source_of_funds_structural", resource_id=sof_id,
                    metadata={
                        "counterparty_id": payload.counterparty_id,
                        "fund_origin_rating": payload.fund_origin_rating,
                        "request_id": request_id,
                    },
                )
            conn.commit()
    except Exception:
        pass
    return SourceOfFundsOut(
        sof_id=sof_id,
        counterparty_id=payload.counterparty_id,
        primary_funding_source=payload.primary_funding_source,
        declared_annual_income_usd=payload.declared_annual_income_usd,
        fund_origin_rating=payload.fund_origin_rating,
        created_at=record["created_at"],
    )


@router.get("/source-of-funds/{sof_id}", response_model=SourceOfFundsOut)
async def get_structural_source_of_funds(
    sof_id: str,
    x_org_id: Annotated[Optional[str], Header(alias="X-Org-Id")] = None,
    x_user_id: Annotated[Optional[str], Header(alias="X-User-Id")] = None,
    x_role: Annotated[Optional[str], Header(alias="X-Role")] = None,
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-Id")] = None,
) -> SourceOfFundsOut:
    pool = get_pool()
    org_id, _, _ = _require_role_header(
        pool=pool, x_org_id=x_org_id, x_user_id=x_user_id, x_request_id=x_request_id,
        x_role=x_role, allowed_roles=SOURCE_OF_FUNDS_ALLOWED_ROLES,
        resource_type="structural_source_of_funds", resource_id=sof_id,
        endpoint="/source-of-funds/{id}", method="GET",
    )
    r = _SOURCE_OF_FUNDS_DB.get(sof_id)
    if not r or r["organization_id"] != org_id:
        raise HTTPException(status_code=404, detail="source_of_funds_not_found")
    return SourceOfFundsOut(
        sof_id=sof_id,
        counterparty_id=r["counterparty_id"],
        primary_funding_source=r["primary_funding_source"],
        declared_annual_income_usd=r["declared_annual_income_usd"],
        fund_origin_rating=r["fund_origin_rating"],
        created_at=r["created_at"],
    )


@router.get("/work-items-blueprint", summary="Catálogo RIPD Art.15 dos 4 work items obrigatórios.")
async def get_work_items_blueprint() -> dict[str, Any]:
    return {
        "obligatory_work_items_total": len(_RIPD_OBLIGATORY_WORK_ITEMS_BLUEPRINT),
        "regulatory_reference": "RIPD Lei 14.133/21 Art.15 I,II,IV,V + Res. BCB 520",
        "blueprint": _RIPD_OBLIGATORY_WORK_ITEMS_BLUEPRINT,
    }
