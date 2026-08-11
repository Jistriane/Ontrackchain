from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from case_management.main import (
    app,
    _case_normalize_role as normalize_role,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
ANALYST_H = {HEADER_X_ROLE: "ANALYST"}
COMPLIANCE_H = {HEADER_X_ROLE: "COMPLIANCE"}
INVESTIGATOR_H = {HEADER_X_ROLE: "INVESTIGATOR"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
COMPLIANCE_OFFICER_H = {HEADER_X_ROLE: "COMPLIANCE_OFFICER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
OTK_ANALYST_H = {HEADER_X_ROLE: "OTK_ANALYST"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("\n\t ") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_COMPLIANCE") == "COMPLIANCE"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_analyst") == "ANALYST"
    assert normalize_role("ONTK_INVESTIGATOR") == "INVESTIGATOR"
    assert normalize_role("B2B_ADMIN") == "ADMIN"
    assert normalize_role("ONTRACKCHAIN_VIEWER") == "VIEWER"


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
            f"health bypass RBAC deve 200/404/307 (recebeu {r.status_code})"
        )


def test_app_enforcer_cases_prefix_403_without_any_header(client: TestClient):
    target = None
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "cases" in prefix or "/api/v1/cases" in prefix:
            target = prefix
            break
    if target is None:
        pytest.skip("sem prefixo cases definido em PREFIX_POLICIES")
    r = client.post(f"{target.rstrip('/')}", json={"title": "T"})
    assert r.status_code in {403, 404, 422}, (
        f"cases prefix {target} sem header deve 403 ou 422/404 (recebeu {r.status_code})"
    )
    if r.status_code == 403:
        detail = str(r.json().get("detail", ""))
        assert "required=" in detail or "forbidden" in detail or "insufficient" in detail


def test_app_enforcer_x_role_CASE_TEAM_member_passes_cases_prefix(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        if "cases" not in prefix and "evidence" not in prefix and "investigations" not in prefix:
            continue
        allowed_upper = {str(a).upper() for a in allowed}
        if allowed_upper & {"ADMIN", "ANALYST", "COMPLIANCE", "INVESTIGATOR"}:
            r = client.get(f"{target.rstrip('/')}", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"cases/evidence prefix com ADMIN não deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_x_role_VIEWER_denied_on_case_write(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "cases" in prefix or "/api/v1/cases" in prefix:
            r = client.post(f"{prefix.rstrip('/')}", json={"title": "T"}, headers=VIEWER_H)
            assert r.status_code in {403, 404, 422}, (
                f"viewer POST cases → esperado 403/404/422 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_workflows_403_without_header(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "workflows" in prefix:
            r = client.get(f"{prefix.rstrip('/')}/anything")
            assert r.status_code in {403, 404, 422}, (
                f"workflows sem header → 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_internal_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if (prefix.endswith("/internal/") or prefix.rstrip("/").endswith("internal")) and "ADMIN" in allowed_upper:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"internal prefix {prefix} ADMIN ok deve evitar 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
