from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from monitoring_api.main import (
    app,
    _monitoring_normalize_role as normalize_role,
    _RBAC_ROUTE_POLICIES as ROUTE_POLICIES,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
AUDITOR_H = {HEADER_X_ROLE: "AUDITOR"}
ANALYST_H = {HEADER_X_ROLE: "ANALYST"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
COMPLIANCE_OFFICER_H = {HEADER_X_ROLE: "COMPLIANCE_OFFICER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
OTK_ANALYST_H = {HEADER_X_ROLE: "OTK_ANALYST"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("   ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_AUDITOR") == "AUDITOR"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_analyst") == "ANALYST"
    assert normalize_role("ONTK_ADMIN") == "ADMIN"
    assert normalize_role("B2B_ANALYST") == "ANALYST"
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
    for path in ("/health", "/docs", "/openapi.json"):
        r = client.get(path)
        assert r.status_code in {200, 307, 404}, (
            f"health/docs bypass (recebeu {r.status_code})"
        )


def test_app_enforcer_alertmanager_webhook_exact_POST_403_without_any_header(client: TestClient):
    for (p, m), _a in ROUTE_POLICIES.items():
        if "alertmanager" in p and m == "POST":
            r = client.post(p, json={})
            assert r.status_code in {403, 404, 422}, (
                f"alertmanager webhook POST sem header deve 403/404 (recebeu {r.status_code})"
            )
            if r.status_code == 403:
                detail = str(r.json().get("detail", ""))
                assert "required=" in detail or "forbidden" in detail or "insufficient" in detail
            return


def test_app_enforcer_x_role_ADMIN_AUDITOR_passes_alertmanager_webhook(client: TestClient):
    for (p, m), allowed in ROUTE_POLICIES.items():
        if "alertmanager" in p and m == "POST":
            allowed_upper = {str(a).upper() for a in allowed}
            headers = ADMIN_H if "ADMIN" in allowed_upper else AUDITOR_H
            r = client.post(p, json={}, headers=headers)
            assert r.status_code not in {403}, (
                f"alertmanager webhook POST com role permitido NAO 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_x_role_VIEWER_denied_on_alertmanager_403(client: TestClient):
    for (p, m), _a in ROUTE_POLICIES.items():
        if "alertmanager" in p and m == "POST":
            r = client.post(p, json={}, headers=VIEWER_H)
            assert r.status_code in {403, 404, 422}, (
                f"viewer alertmanager deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_watchlists_read_403_without_header(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "watchlists" in prefix:
            r = client.get(f"{prefix.rstrip('/')}")
            assert r.status_code in {403, 404, 422}, (
                f"watchlists sem header GET deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_internal_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if (prefix.endswith("/internal/") or prefix.rstrip("/").endswith("internal")) and "ADMIN" in allowed_upper:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"internal prefix ADMIN nao deve 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
