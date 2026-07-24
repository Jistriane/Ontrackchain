import pytest
from fastapi.testclient import TestClient
from case_management.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_case():
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "Test Case",
            "description": "This is a test case",
            "priority": "high",
            "category": "aml"
        },
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-User-Id": "test-user", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Case"
    assert data["description"] == "This is a test case"
    assert data["priority"] == "high"
    assert data["category"] == "aml"
    assert data["status"] == "open"
    assert "case_id" in data
    assert "risk_score" in data


def test_get_case():
    # First create a case
    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Test Case",
            "description": "This is a test case",
            "priority": "medium",
            "category": "sanctions"
        },
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-User-Id": "test-user", "X-Role": "ADMIN"}
    )
    case_id = create_response.json()["case_id"]
    
    # Then get the case
    response = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id


def test_update_case():
    # First create a case
    create_response = client.post(
        "/api/v1/cases",
        json={
            "title": "Test Case",
            "description": "This is a test case",
            "priority": "low",
            "category": "kyc"
        },
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-User-Id": "test-user", "X-Role": "ADMIN"}
    )
    case_id = create_response.json()["case_id"]
    
    # Then update the case
    response = client.put(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress", "priority": "high"},
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-User-Id": "test-user", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_get_case_timeline():
    response = client.get(
        "/api/v1/cases/test-case/timeline",
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "action" in data[0]
    assert "timestamp" in data[0]


def test_get_case_metrics():
    response = client.get(
        "/api/v1/cases/metrics",
        headers={"X-Org-Id": "00000000-0000-0000-0000-000000000001", "X-Role": "ADMIN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "open_cases" in data
    assert "closed_cases" in data
    assert "avg_resolution_time_hours" in data
    assert "cases_by_priority" in data
    assert "cases_by_category" in data


def test_missing_org_id():
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "Test Case",
            "description": "This is a test case",
            "priority": "medium",
            "category": "aml"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Org-Id required"
