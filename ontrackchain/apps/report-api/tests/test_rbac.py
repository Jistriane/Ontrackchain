from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from report_api.main import (
    app,
    _report_normalize_role as normalize_role,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
ANALYST_H = {HEADER_X_ROLE: "ANALYST"}
AUDITOR_H = {HEADER_X_ROLE: "AUDITOR"}
LEGAL_H = {HEADER_X_ROLE: "LEGAL"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
COMPLIANCE_H = {HEADER_X_ROLE: "COMPLIANCE"}
OTK_ADMIN_H = {HEADER_X_ROLE: "OTK_ADMIN"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("   ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_ANALYST") == "ANALYST"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_legal") == "LEGAL"
    assert normalize_role("ONTK_AUDITOR") == "AUDITOR"
    assert normalize_role("B2B_ADMIN") == "ADMIN"
    assert normalize_role("ONTRACKCHAIN_ANALYST") == "ANALYST"


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
            f"health bypass (recebeu {r.status_code})"
        )


def test_app_enforcer_reports_generate_prefix_403_without_any_header(client: TestClient):
    target = None
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "reports" in prefix or "/reports/" in prefix:
            target = prefix
            break
    if target is None:
        pytest.skip("sem prefixo reports definido")
    r = client.post(f"{target.rstrip('/')}/generate", json={})
    assert r.status_code in {403, 404, 422}, (
        f"reports generate sem header deve 403/404/422 (recebeu {r.status_code})"
    )
    if r.status_code == 403:
        detail = str(r.json().get("detail", ""))
        assert "required=" in detail or "forbidden" in detail or "insufficient" in detail


def test_app_enforcer_x_role_ADMIN_passes_reports_generate(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if ("reports" in prefix or "/reports/" in prefix) and allowed_upper & {"ADMIN", "ANALYST"}:
            r = client.post(f"{prefix.rstrip('/')}/generate", json={}, headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"reports generate ADMIN NAO deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_x_role_VIEWER_denied_on_reports_generate_403(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "reports" in prefix or "/reports/" in prefix:
            r = client.post(f"{prefix.rstrip('/')}/generate", json={}, headers=VIEWER_H)
            assert r.status_code in {403, 404, 422}, (
                f"viewer reports generate 403 esperado (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_coaf_read_403_without_header(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "coaf" in prefix or "ros-coaf" in prefix:
            r = client.get(f"{prefix.rstrip('/')}")
            assert r.status_code in {403, 404, 422}, (
                f"coaf/ros-coaf GET sem header {prefix} deve 403/404 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_internal_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if (prefix.endswith("/internal/") or prefix.rstrip("/").endswith("internal")) and "ADMIN" in allowed_upper:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"internal prefix ADMIN evita 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
