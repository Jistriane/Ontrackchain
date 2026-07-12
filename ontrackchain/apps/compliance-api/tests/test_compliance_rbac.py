from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "agents" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "shared" / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("compliance_api.main")
else:
    main = None


class _FakeAuditCursor:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._fetchone: dict[str, Any] | None = None

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized_query.startswith("SELECT set_config("):
            self._fetchone = {"set_config": params_tuple[0] if params_tuple else None}
            return

        if normalized_query == "SELECT 1 FROM users WHERE id = %s":
            self._fetchone = {"exists": 1} if str(params_tuple[0]) in self.state["users"] else None
            return

        if normalized_query.startswith("INSERT INTO audit_logs"):
            organization_id, user_id, action, resource_type, resource_id, metadata_json = params_tuple
            self.state["audit_logs"].append(
                {
                    "organization_id": str(organization_id),
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "metadata": json.loads(metadata_json),
                }
            )
            self._fetchone = None
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def fetchone(self) -> dict[str, Any] | None:
        return self._fetchone

    def __enter__(self) -> "_FakeAuditCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeAuditConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.commit_calls = 0

    def cursor(self) -> _FakeAuditCursor:
        return _FakeAuditCursor(self.state)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_FakeAuditConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeAuditPool:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._connection = _FakeAuditConnection(state)

    def connection(self) -> _FakeAuditConnection:
        return self._connection


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class ComplianceRbacTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeAuditPool]:
        user_id = "11111111-1111-1111-1111-111111111111"
        state = {
            "users": {user_id},
            "audit_logs": [],
        }
        return state, _FakeAuditPool(state)

    def test_record_authorization_denial_persists_audit_log(self) -> None:
        state, pool = self._build_state()

        main._record_authorization_denial(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id="external-actor-1",
            request_id="req-rbac-1",
            effective_role="VIEWER",
            allowed_roles={"ADMIN", "ANALYST"},
            detail="compliance_write_role_required",
            resource_type="counterparty",
            resource_id="counterparty-1",
            endpoint="/api/v1/compliance/counterparties",
            method="POST",
        )

        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty")
        self.assertEqual(log_entry["resource_id"], "counterparty-1")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/counterparties")

    def test_create_counterparty_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.create_counterparty(
                    main.CounterpartyCreateRequest(
                        counterparty_type="individual",
                        legal_name="Counterparty QA",
                        document_type="cpf",
                        document_number="12345678900",
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="VIEWER",
                    x_request_id="req-counterparty-viewer",
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "compliance_write_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty")
        self.assertEqual(log_entry["metadata"]["request_id"], "req-counterparty-viewer")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")

    def test_compliance_write_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_compliance_write_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-co-role",
            x_role="COMPLIANCE_OFFICER",
            resource_type="counterparty",
            resource_id="counterparty-1",
            endpoint="/api/v1/compliance/counterparties",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_compliance_write_role_accepts_legacy_otk_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_compliance_write_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-legacy-co-role",
            x_role="OTK_COMPLIANCE_OFFICER",
            resource_type="preventive_block",
            resource_id="block-1",
            endpoint="/api/v1/compliance/blocks/evaluate",
            method="POST",
        )

        self.assertEqual(normalized_role, "OTK_COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)


if __name__ == "__main__":
    unittest.main()
