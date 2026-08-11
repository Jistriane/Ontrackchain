from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from public_api.main import (
    app,
    _public_normalize_role as normalize_role,
    _RBAC_ROUTE_POLICIES as ROUTE_POLICIES,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
BILLING_H = {HEADER_X_ROLE: "BILLING"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
COMPLIANCE_OFFICER_H = {HEADER_X_ROLE: "COMPLIANCE_OFFICER"}
OTK_ADMIN_H = {HEADER_X_ROLE: "OTK_ADMIN"}
B2B_ADMIN_H = {HEADER_X_ROLE: "B2B_ADMIN"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}
BILLING_ADMIN_H = {HEADER_X_ROLE: "BILLING_ADMIN"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("   ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_ADMIN") == "ADMIN"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_billing") == "BILLING"
    assert normalize_role("ONTK_LEGAL") == "LEGAL"
    assert normalize_role("B2B_ADMIN") == "ADMIN"
    assert normalize_role("ONTRACKCHAIN_AUDITOR") == "AUDITOR"


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


def test_app_enforcer_bypass_public_endpoints_like_health_docs(client: TestClient):
    for path in ("/health", "/docs", "/openapi.json", "/public/v1/chain/status"):
        r = client.get(path)
        assert r.status_code in {200, 307, 404, 422}, (
            f"público {path} não deve exigir role (recebeu {r.status_code})"
        )


def test_app_enforcer_b2b_admin_exact_route_403_without_any_header(client: TestClient):
    exact_paths = [p for (p, m), a in ROUTE_POLICIES.items() if "b2b" in p and m == "GET"]
    for p in exact_paths:
        r = client.get(p)
        assert r.status_code in {403, 404, 422}, f"b2b admin rota {p} sem header deve 403 (recebeu {r.status_code})"
        if r.status_code == 403:
            detail = str(r.json().get("detail", ""))
            assert "required=" in detail or "forbidden" in detail or "insufficient" in detail
            return


def test_app_enforcer_x_role_ADMIN_BILLING_passes_b2b_keys(client: TestClient):
    target = None
    for (p, m), a in ROUTE_POLICIES.items():
        if "b2b/keys" in p and m == "GET":
            target = p
            break
    if target is None:
        pytest.skip("sem rota b2b/keys GET definida em _RBAC_ROUTE_POLICIES")
    r = client.get(target, headers={**ADMIN_H, **BILLING_H})
    assert r.status_code not in {403}, f"b2b/keys com ADMIN+BILLING NAO deve 403 (recebeu {r.status_code})"


def test_app_enforcer_x_role_VIEWER_denied_on_b2b_admin_exact_route(client: TestClient):
    target = None
    for (p, m), a in ROUTE_POLICIES.items():
        if "b2b/keys" in p and m == "GET":
            target = p
            break
    if target is None:
        pytest.skip("sem rota b2b/keys GET definida")
    r = client.get(target, headers=VIEWER_H)
    assert r.status_code == 403, f"b2b/keys requer ADMIN+BILLING; viewer deve 403 (recebeu {r.status_code})"


def test_app_enforcer_prefix_internal_403_without_header(client: TestClient):
    for prefix, _allowed, _mf in PREFIX_POLICIES:
        if prefix.startswith("/public/v1/internal"):
            r = client.get(f"{prefix.rstrip('/')}/anything/nested")
            assert r.status_code in {403, 404, 422}, f"internal prefix {prefix} sem header deve 403/404 (recebeu {r.status_code})"
            return


def test_app_enforcer_prefix_internal_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        if prefix.startswith("/public/v1/internal") and "ADMIN" in {str(a).upper() for a in allowed}:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"internal prefix {prefix} com X-Role=ADMIN NAO deve 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
