import pytest
from fastapi.testclient import TestClient
from case_management.main import app

client = TestClient(app)

ORG_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000002", "X-Role": "ADMIN"}
ANALYST_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000004", "X-Role": "ANALYST"}
VIEWER_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000007", "X-Role": "VIEWER"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "case-management"
    assert data["version"] == "2.0.0"


def test_missing_org_id():
    response = client.post(
        "/api/v1/cases",
        json={"title": "Test", "description": "Desc", "priority": "medium", "category": "aml"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Org-Id required"


def test_rbac_viewer_cannot_create():
    response = client.post(
        "/api/v1/cases",
        json={"title": "Test", "description": "Desc", "priority": "medium", "category": "aml"},
        headers=VIEWER_HEADERS,
    )
    assert response.status_code == 403
    assert "case_write_role_required" in response.json()["detail"]


def test_rbac_viewer_can_list():
    response = client.get("/api/v1/cases", headers=VIEWER_HEADERS)
    assert response.status_code == 200


def test_create_case():
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "Suspicious Transaction Pattern",
            "description": "High volume transactions to sanctioned address",
            "priority": "high",
            "category": "aml",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Suspicious Transaction Pattern"
    assert data["description"] == "High volume transactions to sanctioned address"
    assert data["priority"] == "high"
    assert data["category"] == "aml"
    assert data["status"] == "open"
    assert data["case_id"]
    assert data["risk_score"] is not None
    assert data["risk_score"] >= 60.0


def test_create_case_analyst():
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "KYC Verification",
            "description": "Pending KYC review",
            "priority": "medium",
            "category": "kyc",
        },
        headers=ANALYST_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 55.0


def test_list_cases():
    response = client.get("/api/v1/cases", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)


def test_get_case():
    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "Get Test", "description": "Test", "priority": "low", "category": "sanctions"},
        headers=ADMIN_HEADERS,
    )
    case_id = create_resp.json()["case_id"]

    response = client.get(f"/api/v1/cases/{case_id}", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["title"] == "Get Test"


def test_get_case_not_found():
    response = client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404


def test_update_case():
    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "Update Test", "description": "Test", "priority": "low", "category": "investigation"},
        headers=ADMIN_HEADERS,
    )
    case_id = create_resp.json()["case_id"]

    response = client.put(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress", "priority": "high"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_update_case_no_updates():
    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "No Update Test", "description": "Test", "priority": "low", "category": "aml"},
        headers=ADMIN_HEADERS,
    )
    case_id = create_resp.json()["case_id"]

    response = client.put(
        f"/api/v1/cases/{case_id}",
        json={},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 400


def test_get_case_timeline():
    response = client.get(
        "/api/v1/cases/test-case/timeline",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_case_metrics():
    response = client.get("/api/v1/cases/metrics", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "open_cases" in data
    assert "closed_cases" in data
    assert "avg_resolution_time_hours" in data
    assert "cases_by_priority" in data
    assert "cases_by_category" in data


def test_case_category_sanctions_risk():
    response = client.post(
        "/api/v1/cases",
        json={"title": "Sanctions Case", "description": "Test", "priority": "critical", "category": "sanctions"},
        headers=ADMIN_HEADERS,
    )
    data = response.json()
    assert data["risk_score"] == 100.0


def test_case_category_kyc_low_risk():
    response = client.post(
        "/api/v1/cases",
        json={"title": "KYC Case", "description": "Test", "priority": "low", "category": "kyc"},
        headers=ADMIN_HEADERS,
    )
    data = response.json()
    assert data["risk_score"] == 45.0
