from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from mock_oidc.main import (
    app,
    _mock_oidc_normalize_role as normalize_role,
    _RBAC_ROUTE_POLICIES as ROUTE_POLICIES,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
TESTER_H = {HEADER_X_ROLE: "TESTER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
COMPLIANCE_OFFICER_H = {HEADER_X_ROLE: "COMPLIANCE_OFFICER"}
OTK_ADMIN_H = {HEADER_X_ROLE: "OTK_ADMIN"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("   ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_ADMIN") == "ADMIN"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_admin") == "ADMIN"
    assert normalize_role("ONTK_VIEWER") == "VIEWER"
    assert normalize_role("B2B_ADMIN") == "ADMIN"
    assert normalize_role("ONTRACKCHAIN_TESTER") == "TESTER"


def test_normalize_role_alias_LEGAL_REVIEWER_maps_LEGAL():
    assert normalize_role("LEGAL_REVIEWER") == "LEGAL"


def test_normalize_role_alias_COMPLIANCE_OFFICER_maps_COMPLIANCE():
    assert normalize_role("COMPLIANCE_OFFICER") == "COMPLIANCE"


def test_normalize_role_alias_REVIEWER_and_BILLING_ADMIN_expand():
    assert normalize_role("REVIEWER") == "VIEWER"
    assert normalize_role("BILLING_ADMIN") == "BILLING"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False, backend_options={"use_uvloop": False})


def test_app_enforcer_bypass_public_endpoints_like_health_openid(client: TestClient):
    for path in ("/health", "/.well-known/openid-configuration", "/jwks", "/docs", "/openapi.json"):
        r = client.get(path)
        assert r.status_code in {200, 307, 404}, (
            f"IdP público {path} não deve exigir role (recebeu {r.status_code})"
        )


def test_app_enforcer_admin_token_route_403_without_any_header(client: TestClient):
    for (p, m), _a in ROUTE_POLICIES.items():
        if "admin" in p.lower() or "/token" in p or "/clients" in p:
            method = m.lower()
            fn = getattr(client, method, client.get)
            r = fn(p)
            assert r.status_code in {403, 404, 405, 422}, (
                f"admin/token rota exata {m} {p} sem header deve 403 (recebeu {r.status_code})"
            )
            if r.status_code == 403:
                detail = str(r.json().get("detail", ""))
                assert "required=" in detail or "forbidden" in detail or "insufficient" in detail
            return


def test_app_enforcer_x_role_ADMIN_passes_admin_exact_route(client: TestClient):
    for (p, m), allowed in ROUTE_POLICIES.items():
        allowed_upper = {str(a).upper() for a in allowed}
        if "ADMIN" in allowed_upper:
            method = m.lower()
            fn = getattr(client, method, client.get)
            r = fn(p, headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"rota exata {m} {p} com ADMIN NAO deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_x_role_VIEWER_denied_on_admin_exact_route_403(client: TestClient):
    for (p, m), allowed in ROUTE_POLICIES.items():
        allowed_upper = {str(a).upper() for a in allowed}
        if "ADMIN" in allowed_upper and "VIEWER" not in allowed_upper:
            method = m.lower()
            fn = getattr(client, method, client.get)
            r = fn(p, headers=VIEWER_H)
            assert r.status_code in {403, 404, 405, 422}, (
                f"viewer admin rota exata → 403 esperado (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_admin_403_without_header(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if prefix.startswith("/admin"):
            r = client.get(f"{prefix.rstrip('/')}/any/resource")
            assert r.status_code in {403, 404, 422}, (
                f"admin prefixo {prefix} sem header → 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_admin_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if prefix.startswith("/admin") and "ADMIN" in allowed_upper:
            r = client.get(f"{prefix.rstrip('/')}/any/resource", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"admin prefixo ADMIN ok deve evitar 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
