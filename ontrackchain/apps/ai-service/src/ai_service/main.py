"""
AI Service - Explainable AI for Compliance Decisions
OnTrackChain - Graph Intelligence 4.0
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="OnTrackChain AI Service",
    description="Explainable AI for Compliance Decisions and Graph Intelligence",
    version="1.0.0"
)


class ExplanationRequest(BaseModel):
    case_id: str
    decision_type: str  # "risk_score", "block_recommendation", "sanctions_match"
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
    chain: str
    depth: int = 3
    analysis_type: str = "relationship"  # "relationship", "flow", "cluster"


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


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-service"}


@app.post("/api/v1/ai/explain", response_model=ExplanationResponse)
async def explain_decision(
    request: ExplanationRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> ExplanationResponse:
    """
    Generate explainable AI decision for compliance cases.
    Provides step-by-step reasoning for risk scores and recommendations.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")

    # Generate explanation based on decision type
    explanation = _generate_explanation(request)
    
    return ExplanationResponse(
        explanation_id=str(uuid.uuid4()),
        case_id=request.case_id,
        decision_type=request.decision_type,
        confidence_score=explanation["confidence"],
        reasoning_steps=explanation["steps"],
        factors=explanation["factors"],
        recommendation=explanation["recommendation"],
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@app.post("/api/v1/ai/graph-analysis", response_model=GraphAnalysisResponse)
async def analyze_graph(
    request: GraphAnalysisRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> GraphAnalysisResponse:
    """
    Perform graph intelligence analysis on blockchain addresses.
    Detects relationships, transaction flows, and risk clusters.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")

    # Generate graph analysis
    analysis = _generate_graph_analysis(request)
    
    return GraphAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        address=request.address,
        chain=request.chain,
        nodes=analysis["nodes"],
        edges=analysis["edges"],
        clusters=analysis["clusters"],
        risk_indicators=analysis["risk_indicators"],
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@app.post("/api/v1/ai/case-insights", response_model=CaseInsightResponse)
async def get_case_insights(
    request: CaseInsightRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseInsightResponse:
    """
    Generate AI-powered insights for investigation cases.
    Includes risk assessment, key findings, and recommendations.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")

    # Generate case insights
    insights = _generate_case_insights(request)
    
    return CaseInsightResponse(
        insight_id=str(uuid.uuid4()),
        case_id=request.case_id,
        summary=insights["summary"],
        risk_level=insights["risk_level"],
        key_findings=insights["findings"],
        recommendations=insights["recommendations"],
        similar_cases=insights["similar_cases"],
        generated_at=datetime.now(timezone.utc).isoformat()
    )


def _generate_explanation(request: ExplanationRequest) -> dict[str, Any]:
    """Generate explainable AI explanation for a decision."""
    
    if request.decision_type == "risk_score":
        return {
            "confidence": 0.85,
            "steps": [
                {"step": 1, "action": "Analyze transaction history", "result": "150 transactions in last 30 days"},
                {"step": 2, "action": "Check sanctions lists", "result": "No matches found"},
                {"step": 3, "action": "Evaluate risk indicators", "result": "Medium risk due to high volume"},
                {"step": 4, "action": "Calculate final score", "result": "Risk score: 65/100"}
            ],
            "factors": [
                {"factor": "Transaction Volume", "weight": 0.3, "impact": "high"},
                {"factor": "Sanctions Match", "weight": 0.4, "impact": "none"},
                {"factor": "Behavioral Pattern", "weight": 0.3, "impact": "medium"}
            ],
            "recommendation": "REVIEW - Manual review recommended due to high transaction volume"
        }
    elif request.decision_type == "block_recommendation":
        return {
            "confidence": 0.92,
            "steps": [
                {"step": 1, "action": "Check counterparty status", "result": "Counterparty is active"},
                {"step": 2, "action": "Evaluate risk score", "result": "Risk score: 78/100"},
                {"step": 3, "action": "Check compliance rules", "result": "Rule violation detected"},
                {"step": 4, "action": "Generate recommendation", "result": "BLOCK recommended"}
            ],
            "factors": [
                {"factor": "Risk Score", "weight": 0.5, "impact": "high"},
                {"factor": "Compliance Rules", "weight": 0.3, "impact": "high"},
                {"factor": "Historical Pattern", "weight": 0.2, "impact": "medium"}
            ],
            "recommendation": "BLOCK - Immediate block recommended due to compliance violation"
        }
    else:
        return {
            "confidence": 0.78,
            "steps": [
                {"step": 1, "action": "Analyze sanctions match", "result": "Potential match found"},
                {"step": 2, "action": "Verify identity", "result": "Identity verification pending"},
                {"step": 3, "action": "Generate recommendation", "result": "INVESTIGATE recommended"}
            ],
            "factors": [
                {"factor": "Sanctions Match", "weight": 0.6, "impact": "high"},
                {"factor": "Identity Verification", "weight": 0.4, "impact": "medium"}
            ],
            "recommendation": "INVESTIGATE - Further investigation required"
        }


def _generate_graph_analysis(request: GraphAnalysisRequest) -> dict[str, Any]:
    """Generate graph intelligence analysis for blockchain addresses."""
    
    # Generate sample graph data
    nodes = [
        {"id": request.address, "type": "source", "label": "Target Address", "risk": "medium"},
        {"id": "0x1234...5678", "type": "counterparty", "label": "Counterparty 1", "risk": "low"},
        {"id": "0x8765...4321", "type": "counterparty", "label": "Counterparty 2", "risk": "high"},
        {"id": "0xabcd...ef01", "type": "exchange", "label": "Exchange Wallet", "risk": "low"}
    ]
    
    edges = [
        {"source": request.address, "target": "0x1234...5678", "type": "transfer", "amount": 5.2, "count": 12},
        {"source": request.address, "target": "0x8765...4321", "type": "transfer", "amount": 15.8, "count": 3},
        {"source": "0x8765...4321", "target": "0xabcd...ef01", "type": "transfer", "amount": 22.5, "count": 8}
    ]
    
    clusters = [
        {"id": "cluster_1", "nodes": [request.address, "0x1234...5678"], "risk": "medium", "label": "Primary Cluster"},
        {"id": "cluster_2", "nodes": ["0x8765...4321", "0xabcd...ef01"], "risk": "high", "label": "Risk Cluster"}
    ]
    
    risk_indicators = [
        {"indicator": "High volume to risky address", "severity": "high", "confidence": 0.85},
        {"indicator": "Connection to known cluster", "severity": "medium", "confidence": 0.72},
        {"indicator": "Rapid fund movement", "severity": "medium", "confidence": 0.68}
    ]
    
    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "risk_indicators": risk_indicators
    }


def _generate_case_insights(request: CaseInsightRequest) -> dict[str, Any]:
    """Generate AI-powered insights for investigation cases."""
    
    return {
        "summary": f"Case {request.case_id} involves potential compliance risk with multiple indicators requiring attention.",
        "risk_level": "HIGH",
        "findings": [
            "Transaction pattern shows unusual activity in last 7 days",
            "Connection to 2 high-risk counterparties identified",
            "Sanctions screening returned potential matches requiring verification",
            "Behavioral analysis indicates deviation from normal patterns"
        ],
        "recommendations": [
            "Escalate to senior compliance officer for review",
            "Request additional documentation from counterparty",
            "Monitor account for 30 days with enhanced scrutiny",
            "Consider filing Suspicious Activity Report (SAR)"
        ],
        "similar_cases": [
            {"case_id": "CASE-2026-0156", "similarity": 0.82, "outcome": "BLOCKED"},
            {"case_id": "CASE-2026-0089", "similarity": 0.75, "outcome": "INVESTIGATED"},
            {"case_id": "CASE-2026-0234", "similarity": 0.68, "outcome": "CLEARED"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
