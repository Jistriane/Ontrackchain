from __future__ import annotations

import asyncio
import importlib
import importlib.util
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


class _FakeCursorOrg404:
    def __init__(self) -> None:
        self.execute_calls: list[tuple[str, Any]] = []

    def execute(self, query: str, params=None) -> None:
        self.execute_calls.append((query, params))

    def fetchone(self) -> None:
        return None

    def __enter__(self) -> "_FakeCursorOrg404":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeConnection:
    def __init__(self, cursor) -> None:
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakePool:
    def __init__(self, cursor) -> None:
        self._cursor = cursor

    def connection(self) -> _FakeConnection:
        return _FakeConnection(self._cursor)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class BillingBalanceTests(unittest.TestCase):
    def test_billing_balance_returns_payload_and_queries_organization(self) -> None:
        from tests.test_billing_reconciliation import _FakeCursor, _FakePool  # type: ignore[import]

        cursor = _FakeCursor(
            fetchone_rows=[
                {
                    "credits_available": 120,
                    "credits_reserved": 15.5,
                    "credits_used_total": 420.75,
                }
            ]
        )
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_billing_read_role") as require_role,
            patch.object(main, "_apply_rls_context") as apply_rls_context,
        ):
            payload = asyncio.run(
                main.billing_balance(
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="external-user-1",
                    x_linked_user_id="linked-user-1",
                    x_role="BILLING_ADMIN",
                    x_request_id="req-balance-1",
                )
            )

        require_role.assert_called_once()
        self.assertEqual(require_role.call_args.kwargs["endpoint"], "/api/v1/billing/balance")
        self.assertEqual(payload["credits_available"], 120.0)
        self.assertEqual(payload["credits_reserved"], 15.5)
        self.assertEqual(payload["credits_used_total"], 420.75)
        apply_rls_context.assert_called_once()
        self.assertEqual(len(cursor.execute_calls), 1)
        query, params = cursor.execute_calls[0]
        self.assertIn("FROM organizations", query)
        self.assertEqual(params, ("org-1",))

    def test_billing_balance_rejects_missing_org_id_with_401(self) -> None:
        pool = _FakePool(_FakeCursorOrg404())

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.billing_balance(
                    pool=pool,
                    x_org_id=None,
                    x_user_id="external-user-1",
                    x_linked_user_id=None,
                    x_role="BILLING_ADMIN",
                    x_request_id="req-balance-missing-org",
                )
            )

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")

    def test_billing_balance_returns_404_when_org_not_found(self) -> None:
        pool = _FakePool(_FakeCursorOrg404())

        with (
            patch.object(main, "_require_billing_read_role"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                asyncio.run(
                    main.billing_balance(
                        pool=pool,
                        x_org_id="org-missing",
                        x_user_id="external-user-1",
                        x_linked_user_id=None,
                        x_role="ADMIN",
                        x_request_id="req-balance-org-404",
                    )
                )

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "organization_not_found")

    def test_build_billing_balance_payload_coerces_numeric_types_to_float(self) -> None:
        payload = main._build_billing_balance_payload(
            {
                "credits_available": 10,
                "credits_reserved": "2.5",
                "credits_used_total": 0,
            }
        )

        self.assertEqual(
            payload,
            {
                "credits_available": 10.0,
                "credits_reserved": 2.5,
                "credits_used_total": 0.0,
            },
        )

    def test_format_billing_reconciliation_export_filename_uses_expected_pattern(self) -> None:
        filename = main._format_billing_reconciliation_export_filename("json")

        self.assertRegex(
            filename,
            r"^ontrackchain-billing-reconciliation-\d{8}T\d{6}Z\.json$",
        )
        self.assertTrue(filename.endswith(".json"))


if __name__ == "__main__":
    unittest.main()
