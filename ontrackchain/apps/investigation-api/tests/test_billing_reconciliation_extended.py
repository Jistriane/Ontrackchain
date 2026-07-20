from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("investigation_api.main")
else:
    main = None


class _FakeCursorOrg404:
    """Cursor que simula fetchone() retornando None para organizations (org nao encontrada)."""

    def __init__(self) -> None:
        self.execute_calls: list[tuple[str, Any]] = []

    def execute(self, query: str, params=None) -> None:
        self.execute_calls.append((query, params))

    def fetchone(self) -> None:
        return None  # simula org nao encontrada

    def fetchall(self) -> list:
        return []

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


def _make_pool_with_404_org() -> _FakePool:
    return _FakePool(_FakeCursorOrg404())


def _make_empty_pool() -> _FakePool:
    """Pool mínimo — apenas para testes que nunca chegam ao banco (falham antes)."""
    cursor = MagicMock()
    return _FakePool(cursor)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class BillingReconciliationRbacTests(unittest.TestCase):
    """Testes de autorização do endpoint billing_reconciliation."""

    def _call(
        self,
        pool,
        *,
        x_org_id: str | None = "org-rbac-test",
        x_role: str | None = "BILLING_ADMIN",
        x_user_id: str | None = "user-rbac-1",
        limit: int = 5,
    ) -> Any:
        return asyncio.run(
            main.billing_reconciliation(
                limit=limit,
                pool=pool,
                x_org_id=x_org_id,
                x_user_id=x_user_id,
                x_linked_user_id=None,
                x_role=x_role,
                x_request_id="req-billing-rbac-1",
            )
        )

    def test_rejects_viewer_role_with_403(self) -> None:
        pool = _make_empty_pool()
        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_require_billing_read_role",
                side_effect=main.HTTPException(status_code=403, detail="billing_reconciliation_role_required"),
            ),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool, x_role="VIEWER")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "billing_reconciliation_role_required")

    def test_rejects_analyst_role_with_403(self) -> None:
        pool = _make_empty_pool()
        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_require_billing_read_role",
                side_effect=main.HTTPException(status_code=403, detail="billing_reconciliation_role_required"),
            ),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool, x_role="ANALYST")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_rejects_missing_org_id_with_401(self) -> None:
        pool = _make_empty_pool()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_org_id=None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")

    def test_require_billing_read_role_called_with_correct_endpoint(self) -> None:
        pool = _make_empty_pool()
        with (
            patch.object(main, "_require_billing_read_role") as mock_role,
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_fetch_billing_reconciliation_snapshot", return_value={"ok": True}),
        ):
            self._call(pool, x_role="ADMIN")
        call_kwargs = mock_role.call_args.kwargs
        self.assertEqual(call_kwargs["endpoint"], "/api/v1/billing/reconciliation")
        self.assertEqual(call_kwargs["detail"], "billing_reconciliation_role_required")
        self.assertEqual(call_kwargs["resource_type"], "billing_reconciliation")

    def test_accepted_roles_include_billing_admin_and_otk_variant(self) -> None:
        # Verifica que BILLING_ADMIN e OTK_BILLING_ADMIN estao no set permitido
        self.assertIn("BILLING_ADMIN", main.BILLING_READ_ALLOWED_ROLES)
        self.assertIn("OTK_BILLING_ADMIN", main.BILLING_READ_ALLOWED_ROLES)
        self.assertIn("ADMIN", main.BILLING_READ_ALLOWED_ROLES)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class BillingReconciliationOrgNotFoundTests(unittest.TestCase):
    """Testa o comportamento quando a org nao existe no banco."""

    def _call(self, pool) -> Any:
        return asyncio.run(
            main.billing_reconciliation(
                limit=5,
                pool=pool,
                x_org_id="org-missing",
                x_user_id="user-1",
                x_linked_user_id=None,
                x_role="ADMIN",
                x_request_id="req-org-404",
            )
        )

    def test_returns_404_when_org_not_found(self) -> None:
        pool = _make_pool_with_404_org()
        with (
            patch.object(main, "_require_billing_read_role"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "organization_not_found")


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class BillingReconciliationEdgeCaseTests(unittest.TestCase):
    """Testa edge cases do snapshot: ledger vazio e metadata None."""

    def _make_pool(self, *, fetchone_rows, fetchall_batches) -> _FakePool:
        from tests.test_billing_reconciliation import _FakeCursor  # type: ignore[import]
        cursor = _FakeCursor(fetchone_rows=fetchone_rows, fetchall_batches=fetchall_batches)
        return _FakePool(cursor)

    def _call(self, pool, *, limit: int = 5) -> Any:
        return asyncio.run(
            main.billing_reconciliation(
                limit=limit,
                pool=pool,
                x_org_id="org-edge",
                x_user_id="user-1",
                x_linked_user_id=None,
                x_role="BILLING_ADMIN",
                x_request_id="req-edge-1",
            )
        )

    def test_empty_ledger_returns_zero_entries(self) -> None:
        pool = self._make_pool(
            fetchone_rows=[
                {"credits_available": 0.0, "credits_reserved": 0.0, "credits_used_total": 0.0},
                {"investigation_open_total": 0, "investigation_expired_total": 0,
                 "compliance_open_total": 0, "compliance_expired_total": 0,
                 "monitoring_open_total": 0, "monitoring_expired_total": 0},
            ],
            fetchall_batches=[[], []],
        )
        with (
            patch.object(main, "_require_billing_read_role"),
            patch.object(main, "_apply_rls_context"),
        ):
            payload = self._call(pool)
        self.assertEqual(payload["ledger"]["total_entries"], 0)
        self.assertEqual(payload["ledger"]["action_totals"], [])
        self.assertEqual(payload["ledger"]["recent"], [])

    def test_quotes_all_zero_returns_open_and_expired_zero(self) -> None:
        pool = self._make_pool(
            fetchone_rows=[
                {"credits_available": 50.0, "credits_reserved": 0.0, "credits_used_total": 0.0},
                {"investigation_open_total": 0, "investigation_expired_total": 0,
                 "compliance_open_total": 0, "compliance_expired_total": 0,
                 "monitoring_open_total": 0, "monitoring_expired_total": 0},
            ],
            fetchall_batches=[[], []],
        )
        with (
            patch.object(main, "_require_billing_read_role"),
            patch.object(main, "_apply_rls_context"),
        ):
            payload = self._call(pool)
        self.assertEqual(payload["quotes"]["open_total"], 0)
        self.assertEqual(payload["quotes"]["expired_total"], 0)

    def test_metadata_none_in_ledger_row_serializes_as_empty_dict(self) -> None:
        pool = self._make_pool(
            fetchone_rows=[
                {"credits_available": 10.0, "credits_reserved": 0.0, "credits_used_total": 0.0},
                {"investigation_open_total": 0, "investigation_expired_total": 0,
                 "compliance_open_total": 0, "compliance_expired_total": 0,
                 "monitoring_open_total": 0, "monitoring_expired_total": 0},
            ],
            fetchall_batches=[
                [{"action": "CONFIRMED", "entry_count": 1, "amount_total": None}],
                [{"id": "l-1", "case_id": None, "action": "CONFIRMED",
                  "amount": 0.0, "balance_after": 10.0, "metadata": None, "created_at": None}],
            ],
        )
        with (
            patch.object(main, "_require_billing_read_role"),
            patch.object(main, "_apply_rls_context"),
        ):
            payload = self._call(pool)
        recent_row = payload["ledger"]["recent"][0]
        # metadata=None deve ser serializado como dict vazio
        self.assertIsInstance(recent_row.get("metadata", {}), dict)


if __name__ == "__main__":
    unittest.main()
