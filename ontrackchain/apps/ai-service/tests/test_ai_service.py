import pytest
from fastapi.testclient import TestClient
from ai_service.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_explain_risk_score():
    response = client.post(
        "/api/v1/ai/explain",
        json={"case_id": "test-123", "decision_type": "risk_score"},
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "test-123"
    assert data["decision_type"] == "risk_score"
    assert "confidence_score" in data
    assert "reasoning_steps" in data
    assert "factors" in data
    assert "recommendation" in data


def test_explain_block_recommendation():
    response = client.post(
        "/api/v1/ai/explain",
        json={"case_id": "test-456", "decision_type": "block_recommendation"},
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision_type"] == "block_recommendation"
    assert "BLOCK" in data["recommendation"]


def test_graph_analysis():
    response = client.post(
        "/api/v1/ai/graph-analysis",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum"},
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"
    assert data["chain"] == "ethereum"
    assert "nodes" in data
    assert "edges" in data
    assert "clusters" in data
    assert "risk_indicators" in data


def test_case_insights():
    response = client.post(
        "/api/v1/ai/case-insights",
        json={"case_id": "test-789"},
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "test-789"
    assert "summary" in data
    assert "risk_level" in data
    assert "key_findings" in data
    assert "recommendations" in data
    assert "similar_cases" in data


def test_missing_org_id():
    response = client.post(
        "/api/v1/ai/explain",
        json={"case_id": "test-123", "decision_type": "risk_score"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Org-Id required"
