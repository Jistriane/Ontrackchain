import pytest
from fastapi.testclient import TestClient
from ai_service.main import app

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
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "coaf"
    assert data["document"]["type"] == "Comunicação de Operação Suspeita"
    assert data["document"]["authority"] == "COAF"
    assert len(data["evidence_chain"]) > 0


def test_law_enforcement_export_vasp():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "vasp"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document"]["type"] == "Ofício para VASP/Exchange"


def test_law_enforcement_export_judicial():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "judicial"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document"]["type"] == "Relatório Técnico para Autoridade Judiciária"


def test_law_enforcement_export_fatf():
    response = client.post(
        "/api/v1/ai/law-enforcement-export",
        json={"case_id": "test-case", "format": "fatf"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["document"]["type"] == "Relatório FATF/GAFILAT"


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
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "test-case"
    assert "case_card" in data
    assert "graph_narrative" in data
    assert "risk_assessment" in data
    assert "law_enforcement_package" in data
    assert "human_gate_required" in data
    assert isinstance(data["human_gate_required"], bool)


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
    assert response.status_code == 200


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
