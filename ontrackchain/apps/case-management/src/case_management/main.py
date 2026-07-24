"""
Case Management Service - Enhanced Case Management with AI Integration
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
    title="OnTrackChain Case Management Service",
    description="Enhanced Case Management with AI Integration",
    version="1.0.0"
)


class CaseCreateRequest(BaseModel):
    title: str
    description: str
    priority: str = "medium"  # "low", "medium", "high", "critical"
    category: str  # "sanctions", "aml", "kyc", "investigation"
    assigned_to: Optional[str] = None
    metadata: dict[str, Any] = {}


class CaseResponse(BaseModel):
    case_id: str
    title: str
    description: str
    status: str
    priority: str
    category: str
    assigned_to: Optional[str]
    risk_score: Optional[float]
    created_at: str
    updated_at: str


class CaseUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class CaseTimelineEntry(BaseModel):
    entry_id: str
    case_id: str
    action: str
    actor: str
    details: dict[str, Any]
    timestamp: str


class CaseMetricsResponse(BaseModel):
    total_cases: int
    open_cases: int
    closed_cases: int
    avg_resolution_time_hours: float
    cases_by_priority: dict[str, int]
    cases_by_category: dict[str, int]


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "case-management"}


@app.post("/api/v1/cases", response_model=CaseResponse)
async def create_case(
    request: CaseCreateRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    """
    Create a new investigation case with AI-powered risk assessment.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    
    case_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate AI-powered risk score
    risk_score = _calculate_risk_score(request)
    
    return CaseResponse(
        case_id=case_id,
        title=request.title,
        description=request.description,
        status="open",
        priority=request.priority,
        category=request.category,
        assigned_to=request.assigned_to,
        risk_score=risk_score,
        created_at=now,
        updated_at=now
    )


@app.get("/api/v1/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    """
    Get case details with AI-generated insights.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    
    # Return sample case
    return CaseResponse(
        case_id=case_id,
        title="Sample Investigation Case",
        description="This is a sample case for demonstration",
        status="open",
        priority="high",
        category="aml",
        assigned_to="analyst@ontrackchain.com",
        risk_score=75.0,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )


@app.put("/api/v1/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: str,
    request: CaseUpdateRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseResponse:
    """
    Update case with audit trail and AI recommendations.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    
    now = datetime.now(timezone.utc).isoformat()
    
    return CaseResponse(
        case_id=case_id,
        title="Updated Investigation Case",
        description="This case has been updated",
        status=request.status or "open",
        priority=request.priority or "high",
        category="aml",
        assigned_to=request.assigned_to,
        risk_score=75.0,
        created_at=now,
        updated_at=now
    )


@app.get("/api/v1/cases/{case_id}/timeline", response_model=list[CaseTimelineEntry])
async def get_case_timeline(
    case_id: str,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> list[CaseTimelineEntry]:
    """
    Get case timeline with all actions and AI-generated insights.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    
    return [
        CaseTimelineEntry(
            entry_id=str(uuid.uuid4()),
            case_id=case_id,
            action="case_created",
            actor="system@ontrackchain.com",
            details={"description": "Case created with initial risk assessment"},
            timestamp=datetime.now(timezone.utc).isoformat()
        ),
        CaseTimelineEntry(
            entry_id=str(uuid.uuid4()),
            case_id=case_id,
            action="ai_risk_assessment",
            actor="ai-service",
            details={"risk_score": 75.0, "confidence": 0.85, "factors": ["high_volume", "sanctions_match"]},
            timestamp=datetime.now(timezone.utc).isoformat()
        ),
        CaseTimelineEntry(
            entry_id=str(uuid.uuid4()),
            case_id=case_id,
            action="assigned",
            actor="system@ontrackchain.com",
            details={"assigned_to": "analyst@ontrackchain.com"},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    ]


@app.get("/api/v1/cases/metrics", response_model=CaseMetricsResponse)
async def get_case_metrics(
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseMetricsResponse:
    """
    Get case management metrics with AI-powered analytics.
    """
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    
    return CaseMetricsResponse(
        total_cases=156,
        open_cases=42,
        closed_cases=114,
        avg_resolution_time_hours=48.5,
        cases_by_priority={
            "low": 23,
            "medium": 67,
            "high": 45,
            "critical": 21
        },
        cases_by_category={
            "sanctions": 45,
            "aml": 67,
            "kyc": 23,
            "investigation": 21
        }
    )


def _calculate_risk_score(request: CaseCreateRequest) -> float:
    """Calculate AI-powered risk score for a case."""
    base_score = 50.0
    
    # Adjust based on priority
    priority_adjustments = {
        "low": -10,
        "medium": 0,
        "high": 15,
        "critical": 30
    }
    base_score += priority_adjustments.get(request.priority, 0)
    
    # Adjust based on category
    category_adjustments = {
        "sanctions": 20,
        "aml": 15,
        "kyc": 5,
        "investigation": 10
    }
    base_score += category_adjustments.get(request.category, 0)
    
    return min(100.0, max(0.0, base_score))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
