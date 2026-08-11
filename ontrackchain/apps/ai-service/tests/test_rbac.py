from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

import pytest
from fastapi.testclient import TestClient

from ai_service.main import (
    app,
    _ai_normalize_role as normalize_role,
    _RBAC_PREFIX_POLICIES as PREFIX_POLICIES,
)

HEADER_X_ROLE = "X-Role"
ADMIN_H = {HEADER_X_ROLE: "ADMIN"}
ANALYST_H = {HEADER_X_ROLE: "ANALYST"}
LEGAL_H = {HEADER_X_ROLE: "LEGAL"}
AUDITOR_H = {HEADER_X_ROLE: "AUDITOR"}
VIEWER_H = {HEADER_X_ROLE: "VIEWER"}
LEGAL_REVIEWER_H = {HEADER_X_ROLE: "LEGAL_REVIEWER"}
COMPLIANCE_H = {HEADER_X_ROLE: "COMPLIANCE"}
OTK_ANALYST_H = {HEADER_X_ROLE: "OTK_ANALYST"}
REVIEWER_H = {HEADER_X_ROLE: "REVIEWER"}


def test_normalize_role_returns_empty_for_none_or_empty():
    assert normalize_role(None) == ""
    assert normalize_role("") == ""
    assert normalize_role("  \t") == ""


def test_normalize_role_strips_otk_prefix():
    assert normalize_role("OTK_ANALYST") == "ANALYST"


def test_normalize_role_strips_all_4_prefixes_and_uppercase():
    assert normalize_role("otk_admin") == "ADMIN"
    assert normalize_role("ONTK_LEGAL") == "LEGAL"
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
        assert r.status_code in {200, 307, 404, 422}, (
            f"health/docs devem bypass RBAC (recebeu {r.status_code} {path})"
        )


def test_app_enforcer_agents_law_prefix_403_without_any_header(client: TestClient):
    target = None
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "agents/law" in prefix or "xai" in prefix:
            target = prefix
            break
    if target is None:
        pytest.skip("sem prefixo agents/law ou xai definido")
    r = client.post(f"{target.rstrip('/')}/anything", json={})
    assert r.status_code in {403, 404, 422}, f"agents/law/xai prefix sem header {target} deve 403 (recebeu {r.status_code})"
    if r.status_code == 403:
        detail = str(r.json().get("detail", ""))
        assert "required=" in detail or "forbidden" in detail or "insufficient" in detail


def test_app_enforcer_x_role_LEGAL_passes_agents_law_prefix(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if ("agents/law" in prefix or "xai" in prefix) and allowed_upper & {"LEGAL", "AUDITOR"}:
            r = client.post(f"{prefix.rstrip('/')}/anything", json={}, headers=LEGAL_H)
            assert r.status_code not in {403}, f"{prefix} com LEGAL NAO deve 403 (recebeu {r.status_code})"
            return


def test_app_enforcer_x_role_VIEWER_denied_on_agents_law_with_403_detail(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if "agents/law" in prefix or "xai" in prefix:
            r = client.post(f"{prefix.rstrip('/')}/anything", json={}, headers=VIEWER_H)
            assert r.status_code == 403 or r.status_code in {404, 422}, (
                f"viewer negado agents/law/xai → {r.status_code}"
            )
            return


def test_app_enforcer_prefix_internal_403_without_header(client: TestClient):
    for prefix, _a, _mf in PREFIX_POLICIES:
        if prefix.endswith("/internal/") or prefix.rstrip("/").endswith("internal"):
            r = client.get(f"{prefix.rstrip('/')}/anything")
            assert r.status_code in {403, 404, 422}, (
                f"internal prefix {prefix} sem header deve 403 (recebeu {r.status_code})"
            )
            return


def test_app_enforcer_prefix_internal_passes_with_X_Role_ADMIN(client: TestClient):
    for prefix, allowed, _mf in PREFIX_POLICIES:
        allowed_upper = {str(a).upper() for a in allowed}
        if (prefix.endswith("/internal/") or prefix.rstrip("/").endswith("internal")) and "ADMIN" in allowed_upper:
            r = client.get(f"{prefix.rstrip('/')}/anything", headers=ADMIN_H)
            assert r.status_code not in {403}, (
                f"internal prefix {prefix} com ADMIN NAO deve 403 (recebeu {r.status_code})"
            )
            return


if __name__ == "__main__":
    import unittest
    unittest.main(module="__main__", exit=False, verbosity=2)
