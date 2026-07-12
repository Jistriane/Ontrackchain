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


class _FakeCursor:
    def __init__(self, *, fetchone_rows: list[dict] | None = None, fetchall_batches: list[list[dict]] | None = None):
        self.fetchone_rows = list(fetchone_rows or [])
        self.fetchall_batches = list(fetchall_batches or [])
        self.execute_calls: list[tuple[str, tuple[object, ...] | list[object] | None]] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def execute(self, query: str, params=None) -> None:
        self.execute_calls.append((query, params))

    def fetchone(self) -> dict:
        if not self.fetchone_rows:
            raise AssertionError("fetchone called more times than expected")
        return self.fetchone_rows.pop(0)

    def fetchall(self) -> list[dict]:
        if not self.fetchall_batches:
            raise AssertionError("fetchall called more times than expected")
        return self.fetchall_batches.pop(0)


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return self._cursor


class _FakePool:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def connection(self) -> _FakeConnection:
        return _FakeConnection(self._cursor)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class BillingReconciliationTests(unittest.TestCase):
    def test_billing_reconciliation_returns_snapshot(self) -> None:
        cursor = _FakeCursor(
            fetchone_rows=[
                {
                    "credits_available": 120.0,
                    "credits_reserved": 15.5,
                    "credits_used_total": 420.75,
                },
                {
                    "investigation_open_total": 2,
                    "investigation_expired_total": 1,
                    "compliance_open_total": 1,
                    "compliance_expired_total": 0,
                    "monitoring_open_total": 3,
                    "monitoring_expired_total": 2,
                },
            ],
            fetchall_batches=[
                [
                    {"action": "CONFIRMED", "entry_count": 2, "amount_total": 7.5},
                    {"action": "PRE_HOLD", "entry_count": 1, "amount_total": 3.0},
                ],
                [
                    {
                        "id": "ledger-1",
                        "case_id": "case-1",
                        "action": "CONFIRMED",
                        "amount": 4.5,
                        "balance_after": 120.0,
                        "metadata": {"request_id": "req-1", "quote_id": "quote-1"},
                        "created_at": None,
                    }
                ],
            ],
        )
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_billing_read_role") as require_role,
            patch.object(main, "_apply_rls_context"),
        ):
            payload = asyncio.run(
                main.billing_reconciliation(
                    limit=5,
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="external-user-1",
                    x_linked_user_id="linked-user-1",
                    x_role="BILLING_ADMIN",
                    x_request_id="req-billing-recon-1",
                )
            )

        require_role.assert_called_once()
        self.assertEqual(require_role.call_args.kwargs["endpoint"], "/api/v1/billing/reconciliation")
        self.assertEqual(payload["balance"]["credits_available"], 120.0)
        self.assertEqual(payload["quotes"]["open_total"], 6)
        self.assertEqual(payload["quotes"]["expired_total"], 3)
        self.assertEqual(payload["quotes"]["monitoring"]["expired_total"], 2)
        self.assertEqual(payload["ledger"]["total_entries"], 3)
        self.assertEqual(payload["ledger"]["action_totals"][0]["action"], "CONFIRMED")
        self.assertEqual(payload["ledger"]["recent"][0]["quote_id"], "quote-1")
        self.assertEqual(len(cursor.execute_calls), 4)
        balance_query, balance_params = cursor.execute_calls[0]
        quotes_query, quotes_params = cursor.execute_calls[1]
        totals_query, totals_params = cursor.execute_calls[2]
        recent_query, recent_params = cursor.execute_calls[3]
        self.assertIn("FROM organizations", balance_query)
        self.assertEqual(balance_params, ("org-1",))
        self.assertIn("FROM investigation_quotes", quotes_query)
        self.assertEqual(quotes_params, ("org-1", "org-1", "org-1", "org-1", "org-1", "org-1"))
        self.assertIn("FROM credit_ledger", totals_query)
        self.assertEqual(totals_params, ("org-1",))
        self.assertIn("LIMIT %s", recent_query)
        self.assertEqual(recent_params, ("org-1", 5))


if __name__ == "__main__":
    unittest.main()
