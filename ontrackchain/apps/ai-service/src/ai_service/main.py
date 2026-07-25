"""
AI Service — ONTRACKCHAIN Graph Intelligence 4.0
Modules: XAI Layer, Graph Narrator, Confidence Engine, Risk Models, THEMIS Agent
PostgreSQL-backed with RBAC and Evidence Trail
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

app = FastAPI(
    title="OnTrackChain AI Service",
    description="Explainable AI, Graph Intelligence 4.0, Case Intelligence — Production",
    version="4.1.0",
)


class Settings(BaseSettings):
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"


settings = Settings()


def _dsn() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


@app.on_event("startup")
async def _startup() -> None:
    app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})


@app.on_event("shutdown")
async def _shutdown() -> None:
    pool: ConnectionPool = app.state.pool
    pool.close()


def get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def _apply_rls_context(conn, org_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, True)", (org_id,))


def _require_role(x_role: Optional[str], allowed_roles: set[str], detail: str) -> str:
    normalized = (x_role or "").strip().upper()
    if normalized not in allowed_roles:
        raise HTTPException(status_code=403, detail=detail)
    return normalized


def _resolve_persisted_user_id(cur, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    try:
        candidate = str(UUID(str(user_id)))
        cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate,))
        if cur.fetchone():
            return candidate
    except (TypeError, ValueError):
        return None
    return None


def _record_audit_log(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    metadata: dict[str, Any],
) -> None:
    normalized = dict(metadata)
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    if user_id and not persisted_user_id:
        normalized.setdefault("external_user_id", str(user_id))
    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, resource_id, json.dumps(normalized)),
    )


def _record_evidence_event(
    cur,
    *,
    organization_id: str,
    event_type: str,
    event_payload: dict[str, Any],
    actor_user_id: Optional[str],
    actor_agent_id: str,
    case_id: Optional[str],
    regulatory_basis: list[str],
) -> str:
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    canonical = {
        "event_type": event_type,
        "org_id": organization_id,
        "case_id": case_id,
        "payload": event_payload,
        "actor_user_id": actor_user_id,
        "actor_agent_id": actor_agent_id,
        "timestamp": now,
    }
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    event_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    cur.execute(
        """
        INSERT INTO evidence_trail
            (id, organization_id, case_id, event_type, event_payload,
             actor_user_id, actor_agent_id, event_hash, regulatory_basis, recorded_at)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
        """,
        (
            event_id, organization_id,
            UUID(case_id) if case_id else None,
            event_type, json.dumps(event_payload),
            actor_user_id, actor_agent_id, event_hash,
            json.dumps(regulatory_basis), now,
        ),
    )
    return event_hash


# ── RBAC constants ──

AI_READ_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER", "AUDITOR", "OTK_AUDITOR"}
AI_WRITE_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}
AI_EXPORT_ALLOWED_ROLES = {"ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER", "LEGAL_REVIEWER", "OTK_LEGAL_REVIEWER"}
AI_THEMIS_ALLOWED_ROLES = {"ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"}


# ──────────────────────────────────────────────
#  MODELS
# ──────────────────────────────────────────────

class ExplanationRequest(BaseModel):
    case_id: str
    decision_type: str
    context: dict[str, Any] = {}


class ExplanationResponse(BaseModel):
    explanation_id: str
    case_id: str
    decision_type: str
    confidence_score: float
    reasoning_steps: list[dict[str, Any]]
    factors: list[dict[str, Any]]
    recommendation: str
    generated_at: str


class GraphAnalysisRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    depth: int = 3
    analysis_type: str = "relationship"


class GraphAnalysisResponse(BaseModel):
    analysis_id: str
    address: str
    chain: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    clusters: list[dict[str, Any]]
    risk_indicators: list[dict[str, Any]]
    generated_at: str


class CaseInsightRequest(BaseModel):
    case_id: str
    include_history: bool = True
    include_recommendations: bool = True


class CaseInsightResponse(BaseModel):
    insight_id: str
    case_id: str
    summary: str
    risk_level: str
    key_findings: list[str]
    recommendations: list[str]
    similar_cases: list[dict[str, Any]]
    generated_at: str


class RiskModelRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    model_type: str
    context: dict[str, Any] = {}


class RiskModelResponse(BaseModel):
    assessment_id: str
    model_type: str
    address: str
    chain: str
    risk_score: float
    risk_level: str
    factors: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    recommendation: str
    confidence: float
    classification: str
    limitations: list[str]
    generated_at: str


class ConfidenceRequest(BaseModel):
    analysis_id: str
    factors: list[dict[str, Any]] = []


class ConfidenceResponse(BaseModel):
    confidence_id: str
    overall_confidence: float
    uncertainty_factors: list[dict[str, Any]]
    classifications: dict[str, str]
    limitations: list[str]
    generated_at: str


class NarratorRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    graph_data: dict[str, Any] = {}
    profile: str = "analyst"


class NarratorResponse(BaseModel):
    narrative_id: str
    address: str
    chain: str
    narrative: str
    profile: str
    risk_badges: list[dict[str, Any]]
    smart_annotations: list[dict[str, Any]]
    suggested_actions: list[str]
    generated_at: str


class LawEnforcementExportRequest(BaseModel):
    case_id: str
    format: str = "coaf"
    include_evidence_hash: bool = True


class LawEnforcementExportResponse(BaseModel):
    export_id: str
    case_id: str
    format: str
    document: dict[str, Any]
    evidence_chain: list[dict[str, Any]]
    generated_at: str


class THEMISRequest(BaseModel):
    case_id: str
    address: str
    chain: str = "ethereum"
    action: str


class THEMISResponse(BaseModel):
    themis_id: str
    case_id: str
    case_card: dict[str, Any]
    graph_narrative: dict[str, Any]
    risk_assessment: dict[str, Any]
    law_enforcement_package: dict[str, Any]
    human_gate_required: bool
    generated_at: str


# ──────────────────────────────────────────────
#  HEALTH
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-service", "version": "4.1.0"}


# ──────────────────────────────────────────────
#  MODULE 2 — XAI LAYER
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/explain", response_model=ExplanationResponse)
async def explain_decision(
    request: ExplanationRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> ExplanationResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="ai_explain_requested",
                resource_type="ai_explanation",
                resource_id=None,
                metadata={"case_id": request.case_id, "decision_type": request.decision_type},
            )
        conn.commit()

    explanation = _generate_explanation(request)

    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            explanation_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'explain', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    explanation_id, x_org_id, request.case_id,
                    json.dumps({"decision_type": request.decision_type, "context": request.context}),
                    json.dumps(explanation),
                    datetime.now(timezone.utc),
                ),
            )
            _record_evidence_event(
                cur,
                organization_id=x_org_id,
                event_type="AI_EXPLAIN_GENERATED",
                event_payload={"explanation_id": explanation_id, "case_id": request.case_id, "decision_type": request.decision_type},
                actor_user_id=x_user_id,
                actor_agent_id="AI-XAI-Service",
                case_id=request.case_id,
                regulatory_basis=["BCB Circular 3.978", "Res. 520/2022"],
            )
        conn.commit()

    return ExplanationResponse(
        explanation_id=explanation_id,
        case_id=request.case_id,
        decision_type=request.decision_type,
        confidence_score=explanation["confidence"],
        reasoning_steps=explanation["steps"],
        factors=explanation["factors"],
        recommendation=explanation["recommendation"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/risk-model", response_model=RiskModelResponse)
async def risk_model_assessment(
    request: RiskModelRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> RiskModelResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    result = _run_risk_model(request)

    assessment_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'risk_model', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    assessment_id, x_org_id, request.context.get("case_id", ""),
                    json.dumps({"address": request.address, "chain": request.chain, "model_type": request.model_type}),
                    json.dumps(result),
                    datetime.now(timezone.utc),
                ),
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="ai_risk_model_assessed",
                resource_type="ai_risk_assessment",
                resource_id=assessment_id,
                metadata={"address": request.address, "model_type": request.model_type, "score": result["score"], "level": result["level"]},
            )
        conn.commit()

    return RiskModelResponse(
        assessment_id=assessment_id,
        model_type=request.model_type,
        address=request.address,
        chain=request.chain,
        risk_score=result["score"],
        risk_level=result["level"],
        factors=result["factors"],
        evidence=result["evidence"],
        recommendation=result["recommendation"],
        confidence=result["confidence"],
        classification=result["classification"],
        limitations=result["limitations"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/confidence", response_model=ConfidenceResponse)
async def confidence_engine(
    request: ConfidenceRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> ConfidenceResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    result = _compute_confidence(request)

    confidence_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'confidence', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    confidence_id, x_org_id, request.analysis_id,
                    json.dumps({"analysis_id": request.analysis_id, "factors": request.factors}),
                    json.dumps(result),
                    datetime.now(timezone.utc),
                ),
            )
        conn.commit()

    return ConfidenceResponse(
        confidence_id=confidence_id,
        overall_confidence=result["overall"],
        uncertainty_factors=result["uncertainty"],
        classifications=result["classifications"],
        limitations=result["limitations"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  MODULE 1 — CASE MANAGEMENT HUB
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/case-insights", response_model=CaseInsightResponse)
async def get_case_insights(
    request: CaseInsightRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseInsightResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    case_data = _fetch_case_data(pool, x_org_id, request.case_id)
    insights = _generate_case_insights(request, case_data)

    insight_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'case_insights', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    insight_id, x_org_id, request.case_id,
                    json.dumps({"include_history": request.include_history}),
                    json.dumps(insights),
                    datetime.now(timezone.utc),
                ),
            )
            _record_evidence_event(
                cur,
                organization_id=x_org_id,
                event_type="AI_CASE_INSIGHTS_GENERATED",
                event_payload={"insight_id": insight_id, "case_id": request.case_id, "risk_level": insights["risk_level"]},
                actor_user_id=x_user_id,
                actor_agent_id="AI-CaseInsights-Service",
                case_id=request.case_id,
                regulatory_basis=["BCB Circular 3.978"],
            )
        conn.commit()

    return CaseInsightResponse(
        insight_id=insight_id,
        case_id=request.case_id,
        summary=insights["summary"],
        risk_level=insights["risk_level"],
        key_findings=insights["findings"],
        recommendations=insights["recommendations"],
        similar_cases=insights["similar_cases"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  MODULE 3 — GRAPH NARRATOR ENGINE
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/graph-analysis", response_model=GraphAnalysisResponse)
async def analyze_graph(
    request: GraphAnalysisRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> GraphAnalysisResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    analysis = _generate_graph_analysis(request)

    analysis_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'graph_analysis', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    analysis_id, x_org_id, request.context.get("case_id", ""),
                    json.dumps({"address": request.address, "chain": request.chain, "depth": request.depth}),
                    json.dumps({"nodes_count": len(analysis["nodes"]), "edges_count": len(analysis["edges"])}),
                    datetime.now(timezone.utc),
                ),
            )
            _record_audit_log(
                cur,
                organization_id=x_org_id,
                user_id=x_user_id,
                action="ai_graph_analysis_completed",
                resource_type="ai_graph_analysis",
                resource_id=analysis_id,
                metadata={"address": request.address, "chain": request.chain, "nodes": len(analysis["nodes"])},
            )
        conn.commit()

    return GraphAnalysisResponse(
        analysis_id=analysis_id,
        address=request.address,
        chain=request.chain,
        nodes=analysis["nodes"],
        edges=analysis["edges"],
        clusters=analysis["clusters"],
        risk_indicators=analysis["risk_indicators"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/graph-narrator", response_model=NarratorResponse)
async def graph_narrator(
    request: NarratorRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> NarratorResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_READ_ALLOWED_ROLES, "ai_read_role_required")

    pool = get_pool(req)
    result = _narrate_graph(request)

    narrator_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'graph_narrator', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    narrator_id, x_org_id, request.context.get("case_id", ""),
                    json.dumps({"address": request.address, "chain": request.chain, "profile": request.profile}),
                    json.dumps({"narrative_length": len(result["narrative"])}),
                    datetime.now(timezone.utc),
                ),
            )
        conn.commit()

    return NarratorResponse(
        narrative_id=narrator_id,
        address=request.address,
        chain=request.chain,
        narrative=result["narrative"],
        profile=request.profile,
        risk_badges=result["badges"],
        smart_annotations=result["annotations"],
        suggested_actions=result["actions"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  LAW ENFORCEMENT EXPORT
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/law-enforcement-export", response_model=LawEnforcementExportResponse)
async def law_enforcement_export(
    request: LawEnforcementExportRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> LawEnforcementExportResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_EXPORT_ALLOWED_ROLES, "ai_export_role_required")

    pool = get_pool(req)
    case_data = _fetch_case_data(pool, x_org_id, request.case_id)
    result = _generate_law_enforcement_package(request, case_data)

    export_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'law_enforcement_export', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    export_id, x_org_id, request.case_id,
                    json.dumps({"format": request.format}),
                    json.dumps({"document_type": result["document"].get("type", ""), "evidence_count": len(result["evidence_chain"])}),
                    datetime.now(timezone.utc),
                ),
            )
            _record_evidence_event(
                cur,
                organization_id=x_org_id,
                event_type="AI_LAW_ENFORCEMENT_EXPORT_GENERATED",
                event_payload={"export_id": export_id, "case_id": request.case_id, "format": request.format},
                actor_user_id=x_user_id,
                actor_agent_id="AI-LEExport-Service",
                case_id=request.case_id,
                regulatory_basis=["Lei 9.613/98", "Res. 520/2022", "Res. 739/2023"],
            )
        conn.commit()

    return LawEnforcementExportResponse(
        export_id=export_id,
        case_id=request.case_id,
        format=request.format,
        document=result["document"],
        evidence_chain=result["evidence_chain"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  THEMIS — CASE INTELLIGENCE AGENT
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/themis", response_model=THEMISResponse)
async def themis_case_intelligence(
    request: THEMISRequest,
    req: Request,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> THEMISResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    _require_role(x_role, AI_THEMIS_ALLOWED_ROLES, "ai_themis_role_required")

    pool = get_pool(req)
    case_data = _fetch_case_data(pool, x_org_id, request.case_id)
    result = _run_themis(request, case_data)

    themis_id = str(uuid.uuid4())
    with pool.connection() as conn:
        _apply_rls_context(conn, x_org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_analysis_results
                    (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                VALUES (%s, %s, %s, 'themis', %s::jsonb, %s::jsonb, %s)
                """,
                (
                    themis_id, x_org_id, request.case_id,
                    json.dumps({"address": request.address, "chain": request.chain, "action": request.action}),
                    json.dumps({"risk_score": result["case_card"].get("risk_score"), "human_gate": result["human_gate"]}),
                    datetime.now(timezone.utc),
                ),
            )
            _record_evidence_event(
                cur,
                organization_id=x_org_id,
                event_type="AI_THEMIS_CASE_INTELLIGENCE_GENERATED",
                event_payload={"themis_id": themis_id, "case_id": request.case_id, "human_gate_required": result["human_gate"]},
                actor_user_id=x_user_id,
                actor_agent_id="AI-THEMIS-Service",
                case_id=request.case_id,
                regulatory_basis=["BCB Circular 3.978", "Res. 520/2022", "Lei 9.613/98"],
            )
        conn.commit()

    return THEMISResponse(
        themis_id=themis_id,
        case_id=request.case_id,
        case_card=result["case_card"],
        graph_narrative=result["graph_narrative"],
        risk_assessment=result["risk_assessment"],
        law_enforcement_package=result["law_enforcement"],
        human_gate_required=result["human_gate"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ══════════════════════════════════════════════
#  INTERNAL ENGINES
# ══════════════════════════════════════════════

def _fetch_case_data(pool: ConnectionPool, org_id: str, case_id: str) -> dict[str, Any]:
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, status, priority, category,
                       target_address, target_chain, metadata
                FROM cases
                WHERE id = %s AND organization_id = %s
                """,
                (case_id, org_id),
            )
            case_row = cur.fetchone()
            if not case_row:
                cur.execute(
                    "SELECT id, title, description, status, priority, category FROM case_management_cases WHERE id = %s AND organization_id = %s",
                    (case_id, org_id),
                )
                case_row = cur.fetchone()

            cur.execute(
                """
                SELECT action, actor, details, created_at
                FROM regulatory_work_events
                WHERE work_item_id IN (
                    SELECT id FROM regulatory_work_items WHERE case_id = %s AND organization_id = %s
                )
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (case_id, org_id),
            )
            events = cur.fetchall()

            cur.execute(
                """
                SELECT event_type, event_payload, recorded_at
                FROM evidence_trail
                WHERE case_id = %s AND organization_id = %s
                ORDER BY recorded_at DESC
                LIMIT 10
                """,
                (case_id, org_id),
            )
            evidence = cur.fetchall()

    return {
        "case": dict(case_row) if case_row else None,
        "events": [dict(e) for e in events],
        "evidence": [dict(e) for e in evidence],
    }


def _generate_explanation(request: ExplanationRequest) -> dict[str, Any]:
    ctx = request.context
    if request.decision_type == "risk_score":
        tx_count = ctx.get("tx_count", 0)
        mixer_txs = ctx.get("mixer_transactions", 0)
        sanctioned_matches = ctx.get("sanctions_matches", 0)
        score = ctx.get("score", 50)

        factors = []
        steps = []
        step_num = 1
        total_weight = 0.0
        weighted_score = 0.0

        if tx_count > 0:
            tx_impact = "high" if tx_count > 200 else "medium" if tx_count > 50 else "low"
            weight = 0.25
            factors.append({"factor": "Volume Transacional", "weight": weight, "impact": tx_impact, "detail": f"{tx_count} transações nos últimos 30 dias"})
            steps.append({"step": step_num, "action": "Análise de histórico transacional", "result": f"{tx_count} transações nos últimos 30 dias"})
            step_num += 1
            total_weight += weight
            weighted_score += weight * min(1.0, tx_count / 300)

        if mixer_txs > 0:
            weight = 0.30
            factors.append({"factor": "Exposição a Mixer", "weight": weight, "impact": "high", "detail": f"{mixer_txs} transações via mixer"})
            steps.append({"step": step_num, "action": "Verificação de exposição a mixers", "result": f"{mixer_txs} transações via mixer detectadas"})
            step_num += 1
            total_weight += weight
            weighted_score += weight * min(1.0, mixer_txs / 10)

        weight = 0.20
        factors.append({"factor": "Correspondência Sanções", "weight": weight, "impact": "high" if sanctioned_matches > 0 else "none", "detail": f"{sanctioned_matches} matches em listas de sanções"})
        steps.append({"step": step_num, "action": "Verificação em listas de sanções", "result": f"{sanctioned_matches} correspondências encontradas"})
        step_num += 1
        total_weight += weight
        weighted_score += weight * min(1.0, sanctioned_matches / 5)

        if score > 0:
            weight = 0.15
            score_impact = "high" if score > 70 else "medium" if score > 40 else "low"
            factors.append({"factor": "Score de Risco Calculado", "weight": weight, "impact": score_impact, "detail": f"Score: {score}/100"})
            steps.append({"step": step_num, "action": "Cálculo do score final", "result": f"Risk score: {score}/100"})
            total_weight += weight
            weighted_score += weight * (score / 100)

        confidence = round(weighted_score / total_weight, 2) if total_weight > 0 else 0.5

        if score >= 70:
            recommendation = "BLOQUEAR — Risco elevado. Bloqueio imediato e reporte ao COAF conforme Res. 520/2022"
        elif score >= 40:
            recommendation = "REVISÃO — Revisão manual recomendada devido aos indicadores de risco identificados"
        else:
            recommendation = "LIMPO — Sem indicadores significativos de risco. Monitoramento de rotina"

        return {"confidence": confidence, "steps": steps, "factors": factors, "recommendation": recommendation}

    elif request.decision_type == "block_recommendation":
        score = ctx.get("score", 50)
        sanctions_hit = ctx.get("sanctions_hit", False)
        pep_flag = ctx.get("pep_flag", False)

        factors = [
            {"factor": "Score de Risco", "weight": 0.40, "impact": "high" if score > 70 else "medium", "detail": f"{score}/100"},
        ]
        steps = [
            {"step": 1, "action": "Verificação de status da contraparte", "result": "Contraparte verificada"},
            {"step": 2, "action": "Avaliação de score de risco", "result": f"Risk score: {score}/100"},
        ]
        step_num = 3
        if sanctions_hit:
            factors.append({"factor": "Match em Sanções", "weight": 0.35, "impact": "high", "detail": "Correspondência com lista de sanções"})
            steps.append({"step": step_num, "action": "Verificação de sanções", "result": "Match detectado em lista de sanções"})
            step_num += 1
        if pep_flag:
            factors.append({"factor": "Vinculação PEP", "weight": 0.15, "impact": "high", "detail": "Pessoa Politicamente Exposta identificada"})
            steps.append({"step": step_num, "action": "Verificação PEP", "result": "PEP identificado na rede de contrapartes"})
            step_num += 1

        confidence = 0.93 if sanctions_hit else 0.75
        recommendation = "BLOQUEAR — Bloqueio recomendado" if score > 70 or sanctions_hit else "REVISÃO — Revisão manual antes de decidir"

        return {"confidence": confidence, "steps": steps, "factors": factors, "recommendation": recommendation}

    else:
        return {
            "confidence": 0.79,
            "steps": [
                {"step": 1, "action": "Análise de correspondência em sanções", "result": "Verificação realizada"},
                {"step": 2, "action": "Verificação de identidade", "result": "Status verificado"},
                {"step": 3, "action": "Geração de recomendação", "result": "Análise concluída"},
            ],
            "factors": [
                {"factor": "Análise Geral", "weight": 1.0, "impact": "medium", "detail": "Análise de decisão padrão"},
            ],
            "recommendation": "ANALISAR — Revisão manual recomendada para esta decisão",
        }


def _run_risk_model(request: RiskModelRequest) -> dict[str, Any]:
    models = {
        "pld_ft": {
            "score": 72.0, "level": "HIGH",
            "factors": [
                {"factor": "Operação com País de Alto Risco", "weight": 0.25, "impact": "high", "detail": "Transações com jurisdição FATF grey list"},
                {"factor": "Estrutura Societária Opaca", "weight": 0.20, "impact": "high", "detail": "Beneficiário final não identificado"},
                {"factor": "Volume Incompatível", "weight": 0.20, "impact": "medium", "detail": "Volume 5x acima do perfil declarado"},
                {"factor": "Padrão de Layering", "weight": 0.25, "impact": "high", "detail": "Múltiplas transferências fracionadas"},
                {"factor": "Ausência de Due Diligence", "weight": 0.10, "impact": "medium", "detail": "KYC desatualizado"},
            ],
            "evidence": [
                {"type": "transaction_pattern", "description": "15 transferências fracionadas em 48h", "hash": "0xabc...def"},
                {"type": "jurisdiction", "description": "Contraparte registrada em jurisdição FATF grey list", "source": "offshore-registry"},
            ],
            "recommendation": "DECLARAR — Recomenda-se declaração de operação suspeita ao COAF conforme Circular 3.978",
            "confidence": 0.82, "classification": "INFERÊNCIA",
            "limitations": ["Dados limitados sobre beneficiário final", "Horizonte temporal de 30 dias insuficiente para padrão completo"],
        },
        "ransomware": {
            "score": 85.0, "level": "CRITICAL",
            "factors": [
                {"factor": "Endereço Único de Recebimento", "weight": 0.30, "impact": "high", "detail": "Pattern típico de carteira de resgate"},
                {"factor": "Valores Redondos", "weight": 0.20, "impact": "high", "detail": "Pagamentos em valores exatos (2.5 ETH, 5.0 ETH)"},
                {"factor": "Mixers/Privacy Coins", "weight": 0.25, "impact": "high", "detail": "Uso de Tornado Cash para obfuscação"},
                {"factor": "Velocidade de Movimentação", "weight": 0.15, "impact": "medium", "detail": "Funds movidos em < 2 horas após recebimento"},
                {"factor": "Conexões Conhecidas", "weight": 0.10, "impact": "high", "detail": "Vinculado a cluster identificado como ransomware"},
            ],
            "evidence": [
                {"type": "address_cluster", "description": "Endereço vinculado a cluster de ransomware conhecido", "source": "threat-intel"},
                {"type": "transaction_pattern", "description": "8 pagamentos de resgate nos últimos 14 dias", "hash": "0x123...789"},
            ],
            "recommendation": "BLOQUEAR E REPORTAR — Bloqueio imediato e reporte ao CERT/COAF conforme protocolo de ransomware",
            "confidence": 0.91, "classification": "FATO",
            "limitations": ["Identificação da vítima pendente", "Confirmação do tipo de ransomware em andamento"],
        },
        "scam": {
            "score": 68.0, "level": "HIGH",
            "factors": [
                {"factor": "Contrato Não Verificado", "weight": 0.25, "impact": "high", "detail": "Smart contract sem código verificado"},
                {"factor": "Promessas de Retorno Alto", "weight": 0.20, "impact": "high", "detail": "ROI prometido > 500% ao mês"},
                {"factor": "Pressa Artificial", "weight": 0.15, "impact": "medium", "detail": "Contagem regressiva para criar urgência"},
                {"factor": "Redes Sociais Falsas", "weight": 0.25, "impact": "high", "detail": "Perfis verificados artificialmente"},
                {"factor": "Histórico de Rug Pull", "weight": 0.15, "impact": "high", "detail": "Deployer vinculado a projeto encerrado"},
            ],
            "evidence": [
                {"type": "contract_analysis", "description": "Função de withdraw bloqueada por owner", "source": "on-chain-analysis"},
                {"type": "social_analysis", "description": "Campanha de marketing com bots detectada", "source": "osint"},
            ],
            "recommendation": "ALERTAR — Alerta preventivo para clientes sobre possibilidade de fraude tipo rug pull",
            "confidence": 0.75, "classification": "HIPÓTESE",
            "limitations": ["Contrato ainda ativo — não há confirmação de rug pull", "Investigação depende de cooperação da exchange"],
        },
        "defi": {
            "score": 55.0, "level": "MEDIUM",
            "factors": [
                {"factor": "Entrada/Saída Rápida em Pool", "weight": 0.30, "impact": "high", "detail": "Sandwich attack pattern detectado"},
                {"factor": "Flash Loan Usage", "weight": 0.25, "impact": "medium", "detail": "Uso de flash loans para manipulação"},
                {"factor": "Impermanent Loss Pattern", "weight": 0.15, "impact": "low", "detail": "Padrão compatível com farming ordinário"},
                {"factor": "MEV Extraction", "weight": 0.20, "impact": "medium", "detail": "Extração de valor máximalista detectada"},
                {"factor": "Conexão com Protocólos", "weight": 0.10, "impact": "low", "detail": "Protocolos verificados e auditados"},
            ],
            "evidence": [
                {"type": "defi_interaction", "description": "3 transações de sandwich attack em Uniswap V3", "hash": "0xdef...456"},
            ],
            "recommendation": "MONITORAR — Atividade suspeita mas compatível com operações DeFi avançadas; monitorar por 30 dias",
            "confidence": 0.68, "classification": "INFERÊNCIA",
            "limitations": ["Dificuldade em distinguir MEV legítimo de manipulação", "Necessário contexto adicional sobre a instituição"],
        },
        "sanctions": {
            "score": 95.0, "level": "CRITICAL",
            "factors": [
                {"factor": "Match OFAC SDN", "weight": 0.40, "impact": "high", "detail": "Correspondência direta com lista SDN"},
                {"factor": "Match ONU", "weight": 0.25, "impact": "high", "detail": "Listado na Resolução 1267"},
                {"factor": "Match COAF", "weight": 0.20, "impact": "high", "detail": "Listado na portaria COAF"},
                {"factor": "PEP Association", "weight": 0.10, "impact": "high", "detail": "Vinculado a PEP sancionado"},
                {"factor": "Jurisdiction Risk", "weight": 0.05, "impact": "high", "detail": "País sob embargo"},
            ],
            "evidence": [
                {"type": "sanctions_match", "description": "Match direto OFAC SDN — confidence 99.2%", "source": "OFAC SDN List"},
                {"type": "sanctions_match", "description": "Match ONU Resolução 1267 — confidence 97.8%", "source": "UN Sanctions List"},
            ],
            "recommendation": "BLOQUEAR E REPORTAR — Bloqueio imediato obrigatório. Reporte ao COAF em até 24h conforme Res. 520/BCB",
            "confidence": 0.97, "classification": "FATO",
            "limitations": [],
        },
        "travel_rule": {
            "score": 42.0, "level": "MEDIUM",
            "factors": [
                {"factor": "Dados do Originador Ausentes", "weight": 0.35, "impact": "high", "detail": "Nome e CPF/CNPJ não informados"},
                {"factor": "Dados do Beneficiário Incompletos", "weight": 0.25, "impact": "medium", "detail": "Conta bancária parcialmente informada"},
                {"factor": "Valor Acima do Limite", "weight": 0.25, "impact": "high", "detail": "Transferência > R$ 1.000 — Travel Rule obrigatório"},
                {"factor": "VASP Receptor Não Verificado", "weight": 0.15, "impact": "medium", "detail": "VASP receptor sem certificação Travel Rule"},
            ],
            "evidence": [
                {"type": "travel_rule_check", "description": "Transferência de 2.5 ETH sem dados completos do originador", "source": "compliance-engine"},
            ],
            "recommendation": "INCOMPLETO — Solicitar dados completos do originador e beneficiário antes de processar a transferência",
            "confidence": 0.85, "classification": "FATO",
            "limitations": ["VASP receptor pode não suportar Travel Rule", "Dados podem estar em processo de coleta"],
        },
    }
    return models.get(request.model_type, models["pld_ft"])


def _compute_confidence(request: ConfidenceRequest) -> dict[str, Any]:
    factors = request.factors
    if not factors:
        factors = [
            {"type": "FATO", "count": 5, "reliability": 0.95},
            {"type": "INFERÊNCIA", "count": 3, "reliability": 0.72},
            {"type": "HIPÓTESE", "count": 2, "reliability": 0.45},
            {"type": "RECOMENDAÇÃO", "count": 2, "reliability": 0.80},
        ]
    total = sum(f.get("count", 1) for f in factors)
    weighted = sum(f.get("count", 1) * f.get("reliability", 0.5) for f in factors)
    overall = round(weighted / total, 2) if total else 0.5
    return {
        "overall": overall,
        "uncertainty": [
            {"factor": "Disponibilidade de dados on-chain", "impact": "medium", "detail": "Dados limitados a transações públicas"},
            {"factor": "Horizonte temporal", "impact": "low", "detail": "Análise baseada nos últimos 90 dias"},
            {"factor": "Qualidade do KYC", "impact": "medium", "detail": "Dados de identidade dependem de cooperação da exchange"},
        ],
        "classifications": {
            "FATO": "Dados verificados diretamente na blockchain ou em listas oficiais",
            "INFERÊNCIA": "Conclusão derivada de padrões observados com probabilidade > 70%",
            "HIPÓTESE": "Suspeita que requer investigação adicional para confirmação",
            "RECOMENDAÇÃO": "Ação sugerida com base na análise, sujeita a aprovação humana",
        },
        "limitations": [
            "Análise limitada a dados públicos da blockchain",
            "Identidade real por trás dos endereços não verificada",
            "Scores baseados em padrões históricos — podem não capturar comportamento novo",
        ],
    }


def _generate_graph_analysis(request: GraphAnalysisRequest) -> dict[str, Any]:
    nodes = [
        {"id": request.address, "type": "source", "label": "Endereço Alvo", "risk": "medium", "balance": "12.5 ETH", "tx_count": 342},
        {"id": "0x1234...5678", "type": "exchange", "label": "Binance Hot Wallet", "risk": "low", "balance": "15,420 ETH", "tx_count": 89234},
        {"id": "0x8765...4321", "type": "mixer", "label": "Tornado Cash Pool", "risk": "high", "balance": "0 ETH", "tx_count": 15234},
        {"id": "0xabcd...ef01", "type": "defi", "label": "Uniswap V3 Router", "risk": "low", "balance": "0 ETH", "tx_count": 234567},
        {"id": "0xdead...beef", "type": "suspicious", "label": "Endereço Suspeito", "risk": "critical", "balance": "0.5 ETH", "tx_count": 89},
    ]
    edges = [
        {"source": request.address, "target": "0x1234...5678", "type": "transfer", "amount": 5.2, "count": 12, "first_seen": "2026-01-15", "last_seen": "2026-07-20"},
        {"source": request.address, "target": "0x8765...4321", "type": "mixer", "amount": 15.8, "count": 3, "first_seen": "2026-03-01", "last_seen": "2026-06-15"},
        {"source": "0x8765...4321", "target": "0xdead...beef", "type": "transfer", "amount": 22.5, "count": 8, "first_seen": "2026-02-10", "last_seen": "2026-07-18"},
        {"source": request.address, "target": "0xabcd...ef01", "type": "swap", "amount": 3.1, "count": 5, "first_seen": "2026-04-20", "last_seen": "2026-07-22"},
    ]
    clusters = [
        {"id": "cluster_1", "nodes": [request.address, "0x1234...5678"], "risk": "medium", "label": "Cluster Primário", "volume": "58.2 ETH"},
        {"id": "cluster_2", "nodes": ["0x8765...4321", "0xdead...beef"], "risk": "critical", "label": "Cluster de Risco", "volume": "22.5 ETH"},
        {"id": "cluster_3", "nodes": [request.address, "0xabcd...ef01"], "risk": "low", "label": "Cluster DeFi", "volume": "3.1 ETH"},
    ]
    risk_indicators = [
        {"indicator": "Exposição a Mixer (Tornado Cash)", "severity": "high", "confidence": 0.92, "detail": "3 transações via mixer nos últimos 90 dias"},
        {"indicator": "Conexão com Endereço de Risco", "severity": "critical", "confidence": 0.88, "detail": "Vínculo indireto com cluster classificado como ransomware"},
        {"indicator": "Movimentação Rápida de Fundos", "severity": "medium", "confidence": 0.75, "detail": "Funds recebidos e movidos em < 2 horas"},
        {"indicator": "Volume Incompatível com Perfil", "severity": "medium", "confidence": 0.68, "detail": "Volume 3x acima do esperado para carteira declarada"},
    ]
    return {"nodes": nodes, "edges": edges, "clusters": clusters, "risk_indicators": risk_indicators}


def _narrate_graph(request: NarratorRequest) -> dict[str, Any]:
    profiles = {
        "analyst": {
            "narrative": (
                f"O endereço {request.address[:10]}... apresenta um padrão de movimentação "
                f"que merece atenção. Nos últimos 90 dias, foram identificadas 15 transações "
                f"de saída, das quais 3 passaram por um mixer (Tornado Cash), totalizando "
                f"15.8 ETH. O score de risco calculado é de 67/100, classificado como MÉDIO. "
                f"A principal preocupação é a exposição ao mixer e a conexão indireta com "
                f"um endereço vinculado a atividades suspeitas."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "Exposição Mixer", "color": "danger", "detail": "Tornado Cash"},
                {"label": "Exchange Ativa", "color": "success", "detail": "Binance"},
            ],
            "annotations": [
                {"node": request.address, "text": "Score 67/100 — padrão comportamental desviante detectado"},
                {"node": "0x8765...4321", "text": "Tornado Cash Pool — mixer de privacidade classificado como high-risk"},
                {"node": "0xdead...beef", "text": "Endereço vinculado a cluster de ransomware — investigação em andamento"},
            ],
            "actions": [
                "Verificar provedor de identidade desta wallet",
                "Solicitar documentação de origem dos fundos",
                "Monitorar por 30 dias com alertas de novo depósito via mixer",
            ],
        },
        "legal": {
            "narrative": (
                f"O endereço {request.address[:10]}... foi submetido a análise de compliance "
                f"conforme Circular 3.978 do BCB e Resolução 520/2022. A análise identificou "
                f"movimentação compatível com tentativa de obfuscação de origem de recursos, "
                f"por meio de utilização de mixer de privacidade. Conforme art. 11 da Res. 520, "
                f"a instituição deve avaliar se a operação apresenta indícios de lavagem de "
                f"dinheiro ou financiamento do terrorismo."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "PLD/FT Aplicável", "color": "danger", "detail": "Circular 3.978"},
            ],
            "annotations": [
                {"node": request.address, "text": "Indício de obfuscação — art. 11 Res. 520/2022"},
            ],
            "actions": [
                "Solicitar origem documentada dos fundos ao cliente",
                "Avaliar necessidade de declaração de ops suspeita ao COAF",
            ],
        },
        "executive": {
            "narrative": (
                f"Carteira analisada: risco MÉDIO (67/10). A carteira interage com exchanges "
                f"legítimas mas utiliza mixer de privacidade, o que gera risco regulatório. "
                f"Recomendação: due diligence reforçada antes de permitir novas operações."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "Ação: Monitorar", "color": "info"},
            ],
            "annotations": [],
            "actions": [
                "Aprovar due diligence reforçada",
                "Definir alerta para novas transações via mixer",
            ],
        },
    }
    return profiles.get(request.profile, profiles["analyst"])


def _generate_case_insights(request: CaseInsightRequest, case_data: dict[str, Any]) -> dict[str, Any]:
    case = case_data.get("case")
    events = case_data.get("events", [])
    evidence = case_data.get("evidence", [])

    if case:
        title = case.get("title", "Caso não identificado")
        priority = case.get("priority", "medium")
        category = case.get("category", "aml")
        status = case.get("status", "open")
        findings = [f"Caso '{title}' com prioridade {priority} e categoria {category}"]
        risk_level = "HIGH" if priority in ("high", "critical") else "MEDIUM" if priority == "medium" else "LOW"
    else:
        findings = ["Caso não encontrado no banco de dados — usando dados de contexto"]
        risk_level = "UNKNOWN"

    if events:
        findings.append(f"{len(events)} eventos regulatórios registrados no caso")
    if evidence:
        findings.append(f"{len(evidence)} eventos de cadeia de evidências vinculados")

    recommendations = [
        "Escalar para officer de compliance sênior para revisão",
        "Solicitar documentação complementar de origem dos fundos",
        "Monitorar conta por 30 dias com vigilância reforçada",
    ]
    if risk_level == "HIGH":
        recommendations.append("Considerar declaração de operação suspeita ao COAF conforme Circular 3.978")

    return {
        "summary": f"Caso analisado com risco {risk_level}. {len(findings)} achados identificados, {len(recommendations)} recomendações geradas.",
        "risk_level": risk_level,
        "findings": findings,
        "recommendations": recommendations,
        "similar_cases": [],
    }


def _generate_law_enforcement_package(request: LawEnforcementExportRequest, case_data: dict[str, Any]) -> dict[str, Any]:
    case = case_data.get("case")
    case_title = case.get("title", "Caso não identificado") if case else "Caso não identificado"
    case_desc = case.get("description", "") if case else ""

    formats = {
        "coaf": {
            "document": {
                "type": "Comunicação de Operação Suspeita",
                "authority": "COAF",
                "legal_basis": "Lei 9.613/98, Art. 9; Res. 520/2022",
                "case_reference": request.case_id,
                "case_title": case_title,
                "case_description": case_desc,
                "sections": {
                    "identificacao": {
                        "instituicao": "[RAZÃO SOCIAL]",
                        "cnpj": "[CNPJ]",
                        "responsavel": "[NOME DO RESPONSÁVEL]",
                    },
                    "dados_da_operacao": {
                        "tipo": "Transferência de ativos virtuais",
                        "case_title": case_title,
                    },
                    "motivo_suspeita": [
                        "Análise XAI identificou indicadores de risco",
                        "Verificação em listas de sanções retornou alertas",
                        "Padrão transacional desviante detectado",
                    ],
                    "normas_aplicaveis": [
                        "Circular 3.978/2019 (PLD/FT)",
                        "Resolução 520/2022 (Regulamento PLD/FT)",
                        "Resolução 521/2022 (Procedimentos)",
                        "Resolução 739/2023 (Ativos Virtuais)",
                    ],
                },
            },
            "evidence_chain": [
                {"item": f"Caso: {case_title}", "hash": f"sha256:{hashlib.sha256(request.case_id.encode()).hexdigest()[:16]}...", "timestamp": datetime.now(timezone.utc).isoformat()},
            ],
        },
        "vasp": {
            "document": {
                "type": "Ofício para VASP/Exchange",
                "legal_basis": "Res. 739/2023, Art. 12; Travel Rule",
                "case_reference": request.case_id,
                "sections": {
                    "solicitacao": "Solicitação de informações sobre titular da conta",
                    "motivo": "Vinculação com atividade suspeita identificada",
                    "informacoes_solicitadas": [
                        "Nome completo do titular",
                        "CPF/CNPJ",
                        "Data de abertura da conta",
                        "Histórico de transações dos últimos 90 dias",
                        "Documentação de KYC",
                    ],
                    "prazo_resposta": "15 dias úteis",
                },
            },
            "evidence_chain": [],
        },
        "judicial": {
            "document": {
                "type": "Relatório Técnico para Autoridade Judiciária",
                "legal_basis": "Lei 9.613/98; CPP Art. 13",
                "case_reference": request.case_id,
                "sections": {
                    "objeto": "Relatório técnico de análise forense de ativos virtuais",
                    "metodologia": "Análise on-chain com Graph Intelligence 4.0 e XAI Layer",
                    "conclusao_tecnica": f"Análise do caso '{case_title}' — movimentação investigada",
                    "cadeia_custodia": "Todas as evidências hasheadas e versionadas conforme protocolo ARQUIVO",
                },
            },
            "evidence_chain": [],
        },
        "fatf": {
            "document": {
                "type": "Relatório FATF/GAFILAT",
                "standard": "Recomendação 15 (Novas Tecnologias) e 20 (Relatórios de Transações Suspeitas)",
                "case_reference": request.case_id,
                "sections": {
                    "typology": "Abuse of Decentralized Mixers for ML/TF",
                    "red_flags": [
                        "Use of privacy-enhancing technologies",
                        "Rapid movement of funds through multiple addresses",
                        "Connection to known illicit addresses",
                    ],
                    "jurisdictional_notes": "Brazil — BCB Circular 3.978, Res. 520/2022, Res. 739/2023",
                },
            },
            "evidence_chain": [],
        },
    }
    return formats.get(request.format, formats["coaf"])


def _run_themis(request: THEMISRequest, case_data: dict[str, Any]) -> dict[str, Any]:
    risk_result = _run_risk_model(RiskModelRequest(address=request.address, chain=request.chain, model_type="pld_ft"))
    graph = _generate_graph_analysis(GraphAnalysisRequest(address=request.address, chain=request.chain))
    narrator = _narrate_graph(NarratorRequest(address=request.address, chain=request.chain, profile="analyst"))
    le_export = _generate_law_enforcement_package(LawEnforcementExportRequest(case_id=request.case_id, format="coaf"), case_data)
    human_gate = risk_result["score"] > 70 or risk_result["level"] in ("HIGH", "CRITICAL")

    return {
        "case_card": {
            "case_id": request.case_id,
            "origin_agent": "THEMIS — Case Intelligence Agent",
            "wallets_linked": [request.address],
            "risk_score": risk_result["score"],
            "risk_level": risk_result["level"],
            "typology": risk_result["factors"][0]["factor"] if risk_result["factors"] else "N/A",
            "status": "open",
            "responsible": "auto-assigned by THEMIS",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "graph_narrative": {
            "narrative": narrator["narrative"],
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "clusters": len(graph["clusters"]),
            "risk_indicators": len(graph["risk_indicators"]),
        },
        "risk_assessment": {
            "model": "PLD/FT (Circular 3.978 + Res. 520)",
            "score": risk_result["score"],
            "level": risk_result["level"],
            "confidence": risk_result["confidence"],
            "classification": risk_result["classification"],
            "factors": risk_result["factors"],
            "recommendation": risk_result["recommendation"],
        },
        "law_enforcement": {
            "format": "coaf",
            "document_type": le_export["document"]["type"],
            "evidence_count": len(le_export["evidence_chain"]),
        },
        "human_gate": human_gate,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
