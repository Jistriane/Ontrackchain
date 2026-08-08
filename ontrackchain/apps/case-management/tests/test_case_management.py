import json
import uuid

import pytest
from fastapi.testclient import TestClient
from psycopg_pool import ConnectionPool

from case_management.main import app

ORG_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000002", "X-Role": "ADMIN"}
ANALYST_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000004", "X-Role": "ANALYST"}
VIEWER_HEADERS = {"X-Org-Id": ORG_ID, "X-User-Id": "00000000-0000-0000-0000-000000000007", "X-Role": "VIEWER"}
OTK_COMPLIANCE_OFFICER_HEADERS = {
    "X-Org-Id": ORG_ID,
    "X-User-Id": "00000000-0000-0000-0000-000000000009",
    "X-Role": "OTK_COMPLIANCE_OFFICER",
}
OTK_AUDITOR_HEADERS = {
    "X-Org-Id": ORG_ID,
    "X-User-Id": "00000000-0000-0000-0000-000000000010",
    "X-Role": "OTK_AUDITOR",
}
FAKE_AI_ANALYSIS_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "case-management"
    assert data["version"] == "2.0.0"


def test_missing_org_id(client: TestClient):
    response = client.post(
        "/api/v1/cases",
        json={"title": "Test", "description": "Desc", "priority": "medium", "category": "aml"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "X-Org-Id required"


def test_rbac_viewer_cannot_create(client: TestClient):
    response = client.post(
        "/api/v1/cases",
        json={"title": "Test", "description": "Desc", "priority": "medium", "category": "aml"},
        headers=VIEWER_HEADERS,
    )
    assert response.status_code == 403
    assert "case_write_role_required" in response.json()["detail"]


def test_rbac_viewer_can_list(client: TestClient):
    response = client.get("/api/v1/cases", headers=VIEWER_HEADERS)
    assert response.status_code == 200


def test_create_case(client: TestClient):
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


def test_create_case_analyst(client: TestClient):
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


def test_list_cases(client: TestClient):
    response = client.get("/api/v1/cases", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert isinstance(data["data"], list)


def test_get_case(client: TestClient):
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


def test_get_case_not_found(client: TestClient):
    response = client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404


def test_update_case(client: TestClient):
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


def test_update_case_no_updates(client: TestClient):
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


def test_get_case_timeline(client: TestClient):
    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "Timeline Test", "description": "Test", "priority": "low", "category": "aml"},
        headers=ADMIN_HEADERS,
    )
    case_id = create_resp.json()["case_id"]
    response = client.get(
        f"/api/v1/cases/{case_id}/timeline",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_case_metrics(client: TestClient):
    response = client.get("/api/v1/cases/metrics", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "open_cases" in data
    assert "closed_cases" in data
    assert "avg_resolution_time_hours" in data
    assert "cases_by_priority" in data
    assert "cases_by_category" in data


def test_case_category_sanctions_risk(client: TestClient):
    response = client.post(
        "/api/v1/cases",
        json={"title": "Sanctions Case", "description": "Test", "priority": "critical", "category": "sanctions"},
        headers=ADMIN_HEADERS,
    )
    data = response.json()
    assert data["risk_score"] == 100.0


def test_case_category_kyc_low_risk(client: TestClient):
    response = client.post(
        "/api/v1/cases",
        json={"title": "KYC Case", "description": "Test", "priority": "low", "category": "kyc"},
        headers=ADMIN_HEADERS,
    )
    data = response.json()
    assert data["risk_score"] == 45.0


# ──────────────────────────────────────────────
#  BLOCO B TESTS — OTK_* Roles Federation
# ──────────────────────────────────────────────


def test_otk_compliance_officer_can_create_case(client: TestClient):
    response = client.post(
        "/api/v1/cases",
        json={
            "title": "OTK Compliance Case",
            "description": "Created by federated role",
            "priority": "high",
            "category": "aml",
        },
        headers=OTK_COMPLIANCE_OFFICER_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert data["risk_score"] >= 75.0


def test_otk_auditor_can_read_but_not_write(client: TestClient):
    list_resp = client.get("/api/v1/cases", headers=OTK_AUDITOR_HEADERS)
    assert list_resp.status_code == 200

    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "Auditor Try Create", "description": "x", "priority": "low", "category": "kyc"},
        headers=OTK_AUDITOR_HEADERS,
    )
    assert create_resp.status_code == 403
    assert "case_write_role_required" in create_resp.json()["detail"]


# ──────────────────────────────────────────────
#  BLOCO A TEST — AI Async Fire-and-Forget
# ──────────────────────────────────────────────


def test_create_case_ai_analysis_field_in_metadata(client: TestClient, db_pool: ConnectionPool, monkeypatch):
    captured: list[dict] = []

    class _FakeResponse:
        status_code = 200
        _body = {
            "insight_id": FAKE_AI_ANALYSIS_ID,
            "summary": "test",
            "risk_level": "low",
            "key_findings": [],
            "recommendations": [],
            "similar_cases": [],
        }

        def json(self):
            return self._body

        @property
        def text(self):
            return json.dumps(self._body)

    class _FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def post(self, url, headers=None, json=None):
            captured.append({"url": url, "headers": headers or {}, "json": json or {}})
            return _FakeResponse()

    import case_management.main as cm_main
    import httpx as _httpx_mod

    monkeypatch.setattr(
        cm_main,
        "httpx",
        type("M", (), {"AsyncClient": _FakeAsyncClient, "ConnectError": _httpx_mod.ConnectError})(),
    )

    create_resp = client.post(
        "/api/v1/cases",
        json={"title": "AI Test Case", "description": "trigger AI", "priority": "medium", "category": "investigation"},
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 200
    case_id = create_resp.json()["case_id"]

    client.app.state.pool = db_pool
    import asyncio

    asyncio.run(
        cm_main._async_generate_case_insights(
            case_id=case_id,
            org_id=ORG_ID,
            user_id=ADMIN_HEADERS["X-User-Id"],
            role="ADMIN",
        )
    )

    assert len(captured) >= 1
    assert captured[-1]["json"]["case_id"] == case_id
    assert "/api/v1/ai/case-insights" in captured[-1]["url"]

    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, True)", (ORG_ID,))
            cur.execute(
                "SELECT metadata FROM case_management_cases WHERE id = %s AND organization_id = %s",
                (case_id, ORG_ID),
            )
            row = cur.fetchone()

    metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
    assert metadata.get("ai_analysis_id") == FAKE_AI_ANALYSIS_ID


# ──────────────────────────────────────────────
#  BLOCO C TESTS — DLQ Investigation Admin
# ──────────────────────────────────────────────


def _seed_dlq_case(db_pool: ConnectionPool, *, state: str = "failed_permanent", case_id: str | None = None) -> str:
    cid = case_id or str(uuid.uuid4())
    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, True)", (ORG_ID,))
            cur.execute(
                """
                INSERT INTO cases (id, organization_id, case_type, status, metadata, created_at)
                VALUES (%s, %s, 'investigation', 'failed', %s::jsonb, NOW())
                """,
                (cid, ORG_ID, json.dumps({"dlq_state": state, "error": "worker_timeout"})),
            )
        conn.commit()
    return cid


def test_list_investigation_dlq_state_filter_and_total(client: TestClient, db_pool: ConnectionPool):
    _seed_dlq_case(db_pool, state="failed_permanent")
    _seed_dlq_case(db_pool, state="failed_permanent")
    _seed_dlq_case(db_pool, state="acknowledged")

    list_resp = client.get(
        "/api/v1/cases/investigation-dlq?state=failed_permanent&limit=10",
        headers=ADMIN_HEADERS,
    )
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 2
    assert body["state"] == "failed_permanent"
    assert len(body["data"]) == 2
    for item in body["data"]:
        assert item["dlq_state"] == "failed_permanent"
        assert item["case_id"]


def test_list_investigation_dlq_invalid_state(client: TestClient):
    resp = client.get(
        "/api/v1/cases/investigation-dlq?state=bogus",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 400
    assert "invalid_state" in resp.json()["detail"]


def test_dlq_otk_auditor_can_list_but_viewer_cannot(client: TestClient, db_pool: ConnectionPool):
    _seed_dlq_case(db_pool, state="failed_permanent")

    auditor_resp = client.get("/api/v1/cases/investigation-dlq", headers=OTK_AUDITOR_HEADERS)
    assert auditor_resp.status_code == 200

    viewer_resp = client.get("/api/v1/cases/investigation-dlq", headers=VIEWER_HEADERS)
    assert viewer_resp.status_code == 403
    assert "dlq_admin_role_required" in viewer_resp.json()["detail"]


def test_dlq_requeue_increments_count_and_resets_status(client: TestClient, db_pool: ConnectionPool):
    case_id = _seed_dlq_case(db_pool, state="failed_permanent")

    requeue_resp = client.post(
        f"/api/v1/cases/investigation-dlq/{case_id}/requeue",
        headers=ADMIN_HEADERS,
    )
    assert requeue_resp.status_code == 200
    body = requeue_resp.json()
    assert body["status"] == "requeued"
    assert body["requeue_count"] == 1

    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, True)", (ORG_ID,))
            cur.execute(
                "SELECT status, metadata FROM cases WHERE id = %s AND organization_id = %s",
                (case_id, ORG_ID),
            )
            row = cur.fetchone()
    assert row["status"] == "queued"
    md = row["metadata"] if isinstance(row["metadata"], dict) else {}
    assert md["dlq_state"] == "requeued"
    assert md["dlq_requeue_count"] == 1


def test_dlq_acknowledge_sets_state(client: TestClient, db_pool: ConnectionPool):
    case_id = _seed_dlq_case(db_pool, state="failed_permanent")

    ack_resp = client.post(
        f"/api/v1/cases/investigation-dlq/{case_id}/acknowledge",
        headers=OTK_AUDITOR_HEADERS,
    )
    assert ack_resp.status_code == 200
    body = ack_resp.json()
    assert body["status"] == "acknowledged"

    with db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.organization_id', %s, True)", (ORG_ID,))
            cur.execute(
                "SELECT status, metadata FROM cases WHERE id = %s AND organization_id = %s",
                (case_id, ORG_ID),
            )
            row = cur.fetchone()
    md = row["metadata"] if isinstance(row["metadata"], dict) else {}
    assert md["dlq_state"] == "acknowledged"
    assert "dlq_acknowledged_at" in md


def test_dlq_requeue_conflict_if_already_requeued(client: TestClient, db_pool: ConnectionPool):
    case_id = _seed_dlq_case(db_pool, state="requeued")

    resp = client.post(
        f"/api/v1/cases/investigation-dlq/{case_id}/requeue",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409
    assert "not_in_requeueable_state" in resp.json()["detail"]
