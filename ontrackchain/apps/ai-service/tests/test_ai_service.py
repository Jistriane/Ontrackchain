import json
import uuid

import pytest
from fastapi.testclient import TestClient
from ai_service.main import app
from ai_service.worker import process_next_job

client = TestClient(app)

ORG_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000002", "X-Role": "ADMIN"}
ANALYST_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000004", "X-Role": "ANALYST"}
VIEWER_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000007", "X-Role": "VIEWER"}
COMPLIANCE_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000010", "X-Role": "COMPLIANCE_OFFICER"}
LEGAL_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000011", "X-Role": "LEGAL_REVIEWER"}


def _create_job(*, analysis_type: str = "themis", status: str = "awaiting_human_gate", required_approvals: int = 1) -> str:
    pool = app.state.pool
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, True)", (ORG_ID,))
            request_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO ai_service_jobs(
                  organization_id, analysis_type, status, queue_reason, request_id, request_payload_hash,
                  input_data, human_gate_required, required_approvals
                ) VALUES (
                  %s, %s, %s, 'LONG_RUNNING_OPERATION', %s, 'test',
                  %s::jsonb, true, %s
                ) RETURNING id
                """,
                (ORG_ID, analysis_type, status, request_id, json.dumps({}), required_approvals),
            )
            job_id = cur.fetchone()["id"]
        conn.commit()
    return str(job_id)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"
    assert data["version"] == "4.1.0"


def test_missing_org_id():
    response = client.post(
        "/api/v1/ai/explain",
        json={"case_id": "test-123", "decision_type": "risk_score"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Org-Id required"


def test_rbac_viewer_cannot_explain():
    response = client.post(
        "/api/v1/ai/explain",
        json={"case_id": "test-123", "decision_type": "risk_score"},
        headers=VIEWER_HEADERS,
    )
    assert response.status_code == 403
    assert "ai_read_role_required" in response.json()["detail"]


def test_explain_risk_score():
    response = client.post(
        "/api/v1/ai/explain",
        json={
            "case_id": "test-123",
            "decision_type": "risk_score",
            "context": {"tx_count": 150, "mixer_transactions": 3, "sanctions_matches": 0, "score": 67},
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "test-123"
    assert data["decision_type"] == "risk_score"
    assert "confidence_score" in data
    assert "reasoning_steps" in data
    assert "factors" in data
    assert "recommendation" in data
    assert data["explanation_id"]


def test_explain_block_recommendation():
    response = client.post(
        "/api/v1/ai/explain",
        json={
            "case_id": "test-456",
            "decision_type": "block_recommendation",
            "context": {"score": 78, "sanctions_hit": True, "pep_flag": False},
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision_type"] == "block_recommendation"
    assert "BLOQUEAR" in data["recommendation"]


def test_risk_model_pld_ft():
    response = client.post(
        "/api/v1/ai/risk-model",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum", "model_type": "pld_ft"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_type"] == "pld_ft"
    assert data["risk_score"] == 72.0
    assert data["risk_level"] == "HIGH"
    assert data["classification"] == "INFERÊNCIA"
    assert len(data["factors"]) > 0
    assert len(data["evidence"]) > 0
    assert data["assessment_id"]


def test_risk_model_sanctions():
    response = client.post(
        "/api/v1/ai/risk-model",
        json={"address": "0x123", "chain": "ethereum", "model_type": "sanctions"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 95.0
    assert data["risk_level"] == "CRITICAL"
    assert data["classification"] == "FATO"


def test_risk_model_ransomware():
    response = client.post(
        "/api/v1/ai/risk-model",
        json={"address": "0x456", "chain": "ethereum", "model_type": "ransomware"},
        headers=ANALYST_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] == 85.0
    assert data["risk_level"] == "CRITICAL"


def test_confidence_engine():
    response = client.post(
        "/api/v1/ai/confidence",
        json={
            "analysis_id": "analysis-001",
            "factors": [
                {"type": "FATO", "count": 5, "reliability": 0.95},
                {"type": "INFERÊNCIA", "count": 3, "reliability": 0.72},
            ],
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overall_confidence"] > 0
    assert data["overall_confidence"] <= 1.0
    assert "classifications" in data
    assert "FATO" in data["classifications"]


def test_graph_analysis():
    response = client.post(
        "/api/v1/ai/graph-analysis",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae"
    assert data["chain"] == "ethereum"
    assert len(data["nodes"]) == 5
    assert len(data["edges"]) == 4
    assert len(data["clusters"]) == 3
    assert len(data["risk_indicators"]) == 4


def test_graph_narrator():
    response = client.post(
        "/api/v1/ai/graph-narrator",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum", "profile": "analyst"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "analyst"
    assert len(data["narrative"]) > 0
    assert len(data["risk_badges"]) > 0


def test_graph_narrator_legal():
    response = client.post(
        "/api/v1/ai/graph-narrator",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum", "profile": "legal"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "legal"
    assert "Circular 3.978" in data["narrative"] or "compliance" in data["narrative"].lower()


def test_graph_narrator_executive():
    response = client.post(
        "/api/v1/ai/graph-narrator",
        json={"address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae", "chain": "ethereum", "profile": "executive"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "executive"


def test_law_enforcement_export_coaf():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "coaf"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    assert process_next_job(app.state.pool, ORG_ID) is not None
    status = client.get(f"/api/v1/ai/jobs/{job_id}", headers=ADMIN_HEADERS).json()
    assert status["status"] == "awaiting_human_gate"
    assert status["required_approvals"] == 2

    status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS).json()
    assert status["status"] == "awaiting_human_gate"

    status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=LEGAL_HEADERS).json()
    assert status["status"] == "completed"


def test_law_enforcement_export_vasp():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "vasp"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert process_next_job(app.state.pool, ORG_ID) is not None
    status = client.get(f"/api/v1/ai/jobs/{job_id}", headers=ADMIN_HEADERS).json()
    assert status["status"] == "awaiting_human_gate"
    client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS)
    status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=LEGAL_HEADERS).json()
    assert status["status"] == "completed"


def test_law_enforcement_export_judicial():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "judicial"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert process_next_job(app.state.pool, ORG_ID) is not None
    status = client.get(f"/api/v1/ai/jobs/{job_id}", headers=ADMIN_HEADERS).json()
    assert status["status"] == "awaiting_human_gate"
    client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS)
    status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=LEGAL_HEADERS).json()
    assert status["status"] == "completed"


def test_law_enforcement_export_fatf():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "fatf"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    assert process_next_job(app.state.pool, ORG_ID) is not None
    status = client.get(f"/api/v1/ai/jobs/{job_id}", headers=ADMIN_HEADERS).json()
    assert status["status"] == "awaiting_human_gate"
    client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS)
    status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=LEGAL_HEADERS).json()
    assert status["status"] == "completed"


def test_law_enforcement_rbac_viewer():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "coaf"},
        headers=VIEWER_HEADERS,
    )
    assert response.status_code == 403


def test_themis_case_intelligence():
    response = client.post(
        "/api/v1/ai/themis",
        json={
            "case_id": "test-case",
            "address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",
            "chain": "ethereum",
            "action": "full",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    assert process_next_job(app.state.pool, ORG_ID) is not None
    status = client.get(f"/api/v1/ai/jobs/{job_id}", headers=ADMIN_HEADERS).json()
    assert status["analysis_type"] == "themis"
    assert status["status"] in ("awaiting_human_gate", "completed")
    if status["status"] == "awaiting_human_gate":
        status = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS).json()
        assert status["status"] == "completed"


def test_job_approve_missing_x_user_id_returns_400():
    job_id = _create_job()
    response = client.post(
        f"/api/v1/ai/jobs/{job_id}/approve",
        json={},
        headers={"X-Org-Id": ORG_ID, "X-Role": "COMPLIANCE_OFFICER"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "missing_x_user_id"


def test_job_approve_idempotent_after_completion():
    job_id = _create_job()
    first = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS)
    assert first.status_code == 200
    assert first.json()["status"] == "completed"

    second = client.post(f"/api/v1/ai/jobs/{job_id}/approve", json={}, headers=COMPLIANCE_HEADERS)
    assert second.status_code == 200
    assert second.json()["status"] == "completed"
    assert second.json()["approvals_received"] == 1
    assert second.json()["required_approvals"] == 1


def test_themis_rbac_analyst():
    response = client.post(
        "/api/v1/ai/themis",
        json={
            "case_id": "test-case",
            "address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",
            "chain": "ethereum",
            "action": "full",
        },
        headers=ANALYST_HEADERS,
    )
    assert response.status_code == 202


def test_themis_rbac_viewer_forbidden():
    response = client.post(
        "/api/v1/ai/themis",
        json={
            "case_id": "test-case",
            "address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",
            "chain": "ethereum",
            "action": "full",
        },
        headers=VIEWER_HEADERS,
    )
    assert response.status_code == 403


def test_case_insights():
    response = client.post(
        "/api/v1/ai/case-insights",
        json={"case_id": "test-789"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "test-789"
    assert "summary" in data
    assert "risk_level" in data
    assert "key_findings" in data
    assert "recommendations" in data
    assert "similar_cases" in data
