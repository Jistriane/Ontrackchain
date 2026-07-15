from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("investigation_api.main")
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
class BillingRbacTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeAuditPool]:
        user_id = "11111111-1111-1111-1111-111111111111"
        state = {
            "users": {user_id},
            "audit_logs": [],
        }
        return state, _FakeAuditPool(state)

    def test_require_billing_read_role_allows_billing_admin(self) -> None:
        state, pool = self._build_state()

        normalized_role = main._require_billing_read_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-billing-admin-1",
            x_role="BILLING_ADMIN",
            resource_id="org-1",
            endpoint="/api/v1/billing/balance",
            method="GET",
        )

        self.assertEqual(normalized_role, "BILLING_ADMIN")
        self.assertEqual(state["audit_logs"], [])

    def test_require_billing_read_role_rejects_analyst_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_billing_read_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-billing-analyst-1",
                x_role="ANALYST",
                resource_id="org-1",
                endpoint="/api/v1/billing/balance",
                method="GET",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "billing_balance_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "billing_balance")
        self.assertEqual(log_entry["resource_id"], "org-1")
        self.assertEqual(log_entry["metadata"]["effective_role"], "ANALYST")
        self.assertEqual(log_entry["metadata"]["detail"], "billing_balance_role_required")

    def test_billing_reconciliation_export_returns_attachment_for_billing_admin(self) -> None:
        _state, pool = self._build_state()
        expected_payload = {
            "generated_at": "2026-07-15T00:00:00+00:00",
            "balance": {
                "credits_available": 100.0,
                "credits_reserved": 10.0,
                "credits_used_total": 45.0,
            },
            "quotes": {
                "investigation": {"open_total": 2, "expired_total": 1},
                "compliance": {"open_total": 1, "expired_total": 0},
                "monitoring": {"open_total": 3, "expired_total": 2},
                "open_total": 6,
                "expired_total": 3,
            },
            "ledger": {
                "total_entries": 2,
                "action_totals": [{"action": "CONFIRMED", "entry_count": 2, "amount_total": 7.5}],
                "recent": [],
            },
        }

        with (
            patch.object(main, "_require_billing_read_role", return_value="BILLING_ADMIN"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_fetch_billing_reconciliation_snapshot", return_value=expected_payload),
            patch.object(main, "_format_billing_reconciliation_export_filename", return_value="billing-export.json"),
        ):
            response = asyncio.run(
                main.billing_reconciliation_export(
                    limit=25,
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="BILLING_ADMIN",
                    x_request_id="req-billing-export-1",
                )
            )

        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="billing-export.json"')
        self.assertEqual(response.media_type, "application/json; charset=utf-8")
        self.assertEqual(json.loads(response.body.decode("utf-8")), expected_payload)


if __name__ == "__main__":
    unittest.main()
