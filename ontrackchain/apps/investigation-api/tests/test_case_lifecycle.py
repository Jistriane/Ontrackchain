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
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("investigation_api.main")
else:
    main = None

_CASE_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_ORG_ID = "org-case-ops-test"
_USER_ID = "22222222-2222-2222-2222-222222222222"


class _SpyCursor:
    """Cursor generico que captura queries e permite configurar fetchone/fetchall."""

    def __init__(self, *, fetchone_sequence: list[dict | None] | None = None) -> None:
        self._fetchone_seq = list(fetchone_sequence or [])
        self.execute_calls: list[tuple[str, Any]] = []
        self.rowcount: int = 1

    def execute(self, query: str, params: tuple | list = ()) -> None:
        self.execute_calls.append((query, tuple(params)))

    def fetchone(self) -> dict | None:
        if not self._fetchone_seq:
            return None
        return self._fetchone_seq.pop(0)

    def __enter__(self) -> "_SpyCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _SpyConnection:
    def __init__(self, cursor: _SpyCursor) -> None:
        self._cursor = cursor
        self.commit_calls = 0

    def cursor(self) -> _SpyCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_SpyConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _SpyPool:
    def __init__(self, cursor: _SpyCursor) -> None:
        self._conn = _SpyConnection(cursor)

    def connection(self) -> _SpyConnection:
        return self._conn


# ---------------------------------------------------------------------------
# complete_case
# ---------------------------------------------------------------------------

@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class CompleteCaseTests(unittest.TestCase):
    """POST /api/v1/investigation/{case_id}/internal/complete"""

    def _call(self, pool, *, credits_used: float | None = 1.0) -> Any:
        body = main.FinalizeCaseRequest(credits_used=credits_used)
        return asyncio.run(
            main.complete_case(
                case_id=_CASE_ID,
                body=body,
                pool=pool,
                x_org_id=_ORG_ID,
                x_request_id="req-complete-1",
                x_internal_token=main.settings.investigation_internal_worker_token,
            )
        )

    def _pool_with_normal_completion(self) -> _SpyPool:
        cursor = _SpyCursor(fetchone_sequence=[
            # SELECT cases
            {"id": str(_CASE_ID), "organization_id": _ORG_ID, "status": "processing", "credits_estimated": 1.0},
            # SELECT organizations (for billing)
            {"credits_available": 100.0, "credits_reserved": 10.0, "credits_used_total": 50.0},
        ])
        return _SpyPool(cursor)

    def test_complete_returns_completed_status(self) -> None:
        pool = self._pool_with_normal_completion()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            result = self._call(pool, credits_used=1.0)
        self.assertEqual(result["case_id"], str(_CASE_ID))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["credits_used"], 1.0)

    def test_complete_commits_transaction(self) -> None:
        pool = self._pool_with_normal_completion()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            self._call(pool, credits_used=1.0)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_complete_returns_404_when_case_not_found(self) -> None:
        cursor = _SpyCursor(fetchone_sequence=[None])
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "case_not_found")

    def test_complete_returns_409_when_already_completed(self) -> None:
        cursor = _SpyCursor(fetchone_sequence=[
            {"id": str(_CASE_ID), "organization_id": _ORG_ID, "status": "completed", "credits_estimated": 1.0},
        ])
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "case_already_completed")

    def test_complete_rejects_missing_org(self) -> None:
        pool = _SpyPool(_SpyCursor())
        with self.assertRaises(main.HTTPException) as ctx:
            body = main.FinalizeCaseRequest(credits_used=1.0)
            asyncio.run(
                main.complete_case(
                    case_id=_CASE_ID,
                    body=body,
                    pool=pool,
                    x_org_id=None,
                    x_request_id="req-1",
                    x_internal_token="token",
                )
            )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")

    def test_complete_with_high_variance_flags_recalc(self) -> None:
        cursor = _SpyCursor(fetchone_sequence=[
            # SELECT cases — estimated 10.0
            {"id": str(_CASE_ID), "organization_id": _ORG_ID, "status": "processing", "credits_estimated": 10.0},
            # SELECT organizations (for refund)
            {"credits_available": 100.0, "credits_reserved": 20.0},
        ])
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            # credits_used=0.5 vs estimated=10.0 -> variance = 95% > 10%
            result = self._call(pool, credits_used=0.5)
        self.assertEqual(result["status"], "billing_recalc_required")
        self.assertEqual(result["refunded_amount"], 10.0)
        self.assertEqual(result["actual_cost"], 0.5)


# ---------------------------------------------------------------------------
# fail_case
# ---------------------------------------------------------------------------

@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class FailCaseTests(unittest.TestCase):
    """POST /api/v1/investigation/{case_id}/internal/fail"""

    def _call(self, pool, *, reason: str | None = "worker_timeout") -> Any:
        body = main.FinalizeCaseRequest(reason=reason)
        return asyncio.run(
            main.fail_case(
                case_id=_CASE_ID,
                body=body,
                pool=pool,
                x_org_id=_ORG_ID,
                x_request_id="req-fail-1",
                x_internal_token=main.settings.investigation_internal_worker_token,
            )
        )

    def _pool_with_case(self) -> _SpyPool:
        cursor = _SpyCursor(fetchone_sequence=[
            # SELECT cases
            {"id": str(_CASE_ID), "status": "processing", "credits_estimated": 5.0},
            # SELECT organizations
            {"credits_available": 80.0, "credits_reserved": 15.0},
        ])
        return _SpyPool(cursor)

    def test_fail_returns_failed_status_and_refund(self) -> None:
        pool = self._pool_with_case()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            result = self._call(pool)
        self.assertEqual(result["case_id"], str(_CASE_ID))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["refund_amount"], 5.0)

    def test_fail_commits_transaction(self) -> None:
        pool = self._pool_with_case()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_fail_records_two_audit_logs(self) -> None:
        pool = self._pool_with_case()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log") as mock_audit,
        ):
            self._call(pool, reason="rpc_timeout")
        # fail_case grava 2 audit logs: case_failed + case_sent_to_dlq
        self.assertEqual(mock_audit.call_count, 2)
        actions = [call.kwargs["action"] for call in mock_audit.call_args_list]
        self.assertIn("case_failed", actions)
        self.assertIn("case_sent_to_dlq", actions)

    def test_fail_returns_404_when_case_not_found(self) -> None:
        cursor = _SpyCursor(fetchone_sequence=[None])
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "case_not_found")

    def test_fail_uses_unknown_error_when_reason_is_none(self) -> None:
        pool = self._pool_with_case()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger") as mock_ledger,
            patch.object(main, "_record_audit_log"),
        ):
            self._call(pool, reason=None)
        ledger_meta = mock_ledger.call_args.kwargs["metadata"]
        self.assertEqual(ledger_meta["reason"], "unknown_error")

    def test_fail_metadata_includes_dlq_state(self) -> None:
        pool = self._pool_with_case()
        with (
            patch.object(main, "_require_internal_worker_token_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_credit_ledger"),
            patch.object(main, "_record_audit_log"),
        ):
            self._call(pool)
        # O UPDATE cases recebe metadata com dlq_state
        update_calls = [
            c for c in pool._conn._cursor.execute_calls
            if "UPDATE cases" in c[0]
        ]
        self.assertTrue(len(update_calls) >= 1)
        metadata_json = update_calls[0][1][0]
        metadata = json.loads(metadata_json)
        self.assertEqual(metadata["dlq_state"], "failed_permanent")
        self.assertEqual(metadata["worker_queue_state"], "dlq")


# ---------------------------------------------------------------------------
# delete_case
# ---------------------------------------------------------------------------

@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class DeleteCaseTests(unittest.TestCase):
    """DELETE /api/v1/investigation/{case_id}"""

    def _call(self, pool, *, x_role: str = "ADMIN", x_org_id: str | None = _ORG_ID) -> Any:
        return asyncio.run(
            main.delete_case(
                case_id=_CASE_ID,
                pool=pool,
                x_org_id=x_org_id,
                x_user_id=_USER_ID,
                x_linked_user_id=None,
                x_role=x_role,
                x_request_id="req-delete-1",
            )
        )

    def test_delete_returns_deleted_status(self) -> None:
        cursor = _SpyCursor()
        cursor.rowcount = 1
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log"),
        ):
            result = self._call(pool)
        self.assertEqual(result["status"], "deleted")
        self.assertEqual(result["case_id"], str(_CASE_ID))

    def test_delete_commits_transaction(self) -> None:
        cursor = _SpyCursor()
        cursor.rowcount = 1
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log"),
        ):
            self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_delete_records_audit_log(self) -> None:
        cursor = _SpyCursor()
        cursor.rowcount = 1
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log") as mock_audit,
        ):
            self._call(pool)
        mock_audit.assert_called_once()
        self.assertEqual(mock_audit.call_args.kwargs["action"], "case_deleted")

    def test_delete_returns_404_when_no_row_deleted(self) -> None:
        cursor = _SpyCursor()
        cursor.rowcount = 0
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "case_not_found")

    def test_delete_does_not_record_audit_when_no_row(self) -> None:
        cursor = _SpyCursor()
        cursor.rowcount = 0
        pool = _SpyPool(cursor)
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log") as mock_audit,
        ):
            with self.assertRaises(main.HTTPException):
                self._call(pool)
        mock_audit.assert_not_called()

    def test_delete_rejects_non_admin_role(self) -> None:
        pool = _SpyPool(_SpyCursor())
        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_require_role_with_audit",
                side_effect=main.HTTPException(status_code=403, detail="admin_required"),
            ),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool, x_role="VIEWER")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_delete_rejects_missing_org(self) -> None:
        pool = _SpyPool(_SpyCursor())
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_org_id=None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")


if __name__ == "__main__":
    unittest.main()
