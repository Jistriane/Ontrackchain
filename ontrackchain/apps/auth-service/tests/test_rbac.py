from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from auth_service.main import (
    app,
    _auth_normalize_role as normalize_role,
    _RBAC_ROUTE_POLICIES as ROUTE_POLICIES,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
COMPLIANCE_OFFICER_H = {HEADER_X_ROLE: "COMPLIANCE_OFFICER"}
OTK_ADMIN_H = {HEADER_X_ROLE: "OTK_ADMIN"}
ONTK_COMPLIANCE_H = {HEADER_X_ROLE: "ONTK_COMPLIANCE"}
B2B_ADMIN_H = {HEADER_X_ROLE: "B2B_ADMIN"}
ONTRACKCHAIN_AUDITOR_H = {HEADER_X_ROLE: "ONTRACKCHAIN_AUDITOR"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}
BILLING_ADMIN_H = {HEADER_X_ROLE: "BILLING_ADMIN"}


# =========================
# UNITÁRIOS (pure functions)
# =========================
def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("   ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_ADMIN") == "ADMIN"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_admin") == "ADMIN"
    assert normalize_role("ONTK_COMPLIANCE") == "COMPLIANCE"
    assert normalize_role("B2B_ADMIN") == "ADMIN"
    assert normalize_role("ONTRACKCHAIN_AUDITOR") == "AUDITOR"


def test_normalize_role_alias_LEGAL_REVIEWER_maps_LEGAL():
    assert normalize_role("LEGAL_REVIEWER") == "LEGAL"
    assert normalize_role("OTK_LEGAL_REVIEWER") == "LEGAL"


def test_normalize_role_alias_COMPLIANCE_OFFICER_maps_COMPLIANCE():
    assert normalize_role("COMPLIANCE_OFFICER") == "COMPLIANCE"
    assert normalize_role("ONTK_COMPLIANCE_OFFICER") == "COMPLIANCE"


def test_normalize_role_alias_REVIEWER_and_BILLING_ADMIN_expand():
    assert normalize_role("REVIEWER") == "VIEWER"
    assert normalize_role("BILLING_ADMIN") == "BILLING"


# =========================
# INTEGRACAO (TestClient app)
# =========================
@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False, backend_options={"use_uvloop": False})


def test_app_enforcer_bypass_public_endpoints_like_health_docs(client: TestClient):
    for path in ("/health", "/docs", "/openapi.json"):
        r = client.get(path)
        assert r.status_code in {200, 307, 404}, (
            f"public {path} não deve exigir role (recebeu {r.status_code})"
        )


def test_app_enforcer_admin_exact_route_403_without_any_header(client: TestClient):
    r = client.post("/auth/issue-dev-token", json={})
    assert r.status_code == 403, f"issue-dev-token sem headers deve ser 403, recebido {r.status_code}"
    detail = str(r.json().get("detail", ""))
    assert "insufficient_role_permission" in detail or "required=" in detail or "forbidden" in detail


def test_app_enforcer_x_role_ADMIN_passes_whoami_all_logged_allowed(client: TestClient):
    r = client.get("/auth/whoami", headers=ADMIN_H)
    assert r.status_code not in {403}, "whoami GET com X-Role ADMIN pertence a ALL_LOGGED allowed"


def test_app_enforcer_x_role_VIEWER_denied_on_issue_dev_token_with_403_detail(client: TestClient):
    r = client.post("/auth/issue-dev-token", json={}, headers=VIEWER_H)
    assert r.status_code == 403, "issue-dev-token requer ADMIN"
    detail = str(r.json().get("detail", ""))
    assert "required=" in detail or "forbidden" in detail or "insufficient" in detail


def test_app_enforcer_prefix_admin_403_without_header(client: TestClient):
    for prefix_cfg in PREFIX_POLICIES:
        prefix, _allowed, _mf = prefix_cfg
        if prefix.startswith("/auth/admin") and "admin" in prefix:
            r = client.get(f"{prefix.rstrip('/')}/anything")
            assert r.status_code == 403 or r.status_code in {404, 422}, (
                f"admin prefixo {prefix} sem header deve 403/404/422 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_admin_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix_cfg in PREFIX_POLICIES:
        prefix, allowed, _mf = prefix_cfg
        if prefix.startswith("/auth/admin") and "ADMIN" in {a.upper() for a in allowed}:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"admin prefixo {prefix} com X-Role=ADMIN NAO deve 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
