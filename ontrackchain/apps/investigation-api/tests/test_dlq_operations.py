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

_CASE_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_VALID_ORG = "org-dlq-test"
_VALID_USER = "44444444-4444-4444-4444-444444444444"


class _AckCursor:
    """Cursor para acknowledge_dlq_case.

    Suporta SELECT cases, UPDATE cases e INSERT INTO audit_logs.
    Configurável via case_row para simular cenários diferentes.
    """

    def __init__(self, state: dict[str, Any], *, case_row: dict | None) -> None:
        self.state = state
        self._case_row = case_row
        self._fetchone_value: Any = None

    def execute(self, query: str, params: tuple | list = ()) -> None:
        normalized = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized.startswith("SELECT set_config("):
            return

        if normalized == "SELECT 1 FROM users WHERE id = %s":
            self._fetchone_value = (
                {"exists": 1} if str(params_tuple[0]) in self.state["users"] else None
            )
            return

        if normalized.startswith("SELECT id, case_type, status, metadata FROM cases"):
            self._fetchone_value = self._case_row
            return

        if normalized.startswith("UPDATE cases"):
            self.state["updated"] = True
            return

        if normalized.startswith("INSERT INTO audit_logs"):
            organization_id, user_id, action, resource_type, resource_id, metadata_json = params_tuple
            self.state["audit_logs"].append(
                {
                    "organization_id": str(organization_id),
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "metadata": json.loads(metadata_json),
                }
            )
            self._fetchone_value = None
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized}")

    def fetchone(self) -> Any:
        return self._fetchone_value

    def __enter__(self) -> "_AckCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _AckConnection:
    def __init__(self, state: dict[str, Any], *, case_row: dict | None) -> None:
        self.state = state
        self.case_row = case_row
        self.commit_calls = 0

    def cursor(self) -> _AckCursor:
        return _AckCursor(self.state, case_row=self.case_row)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_AckConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _AckPool:
    def __init__(self, state: dict[str, Any], *, case_row: dict | None) -> None:
        self.state = state
        self._conn = _AckConnection(state, case_row=case_row)

    def connection(self) -> _AckConnection:
        return self._conn


def _make_pool(*, case_row: dict | None) -> _AckPool:
    state: dict[str, Any] = {
        "users": {_VALID_USER},
        "audit_logs": [],
        "updated": False,
    }
    return _AckPool(state, case_row=case_row)


def _valid_case_row() -> dict:
    return {
        "id": str(_CASE_ID),
        "case_type": "investigation",
        "status": "failed",
        "metadata": {"dlq_state": "failed_permanent"},
    }


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class AcknowledgeDlqCaseTests(unittest.TestCase):
    """Testa POST /api/v1/investigation/admin/dlq/{case_id}/acknowledge."""

    def _call(
        self,
        pool: _AckPool,
        *,
        action: str = "acknowledged",
        note: str | None = "revisado manualmente",
        x_role: str = "ADMIN",
        x_org_id: str | None = _VALID_ORG,
        x_user_id: str | None = _VALID_USER,
    ) -> Any:
        body = main.DlqResolutionRequest(action=action, note=note)
        return asyncio.run(
            main.acknowledge_dlq_case(
                case_id=_CASE_ID,
                body=body,
                pool=pool,
                x_org_id=x_org_id,
                x_user_id=x_user_id,
                x_linked_user_id=None,
                x_role=x_role,
                x_request_id="req-dlq-ack-1",
            )
        )

    def test_acknowledge_returns_case_id_and_dlq_state(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            result = self._call(pool)
        self.assertEqual(result["case_id"], str(_CASE_ID))
        self.assertEqual(result["dlq_state"], "acknowledged")

    def test_discard_returns_discarded_state(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            result = self._call(pool, action="discarded")
        self.assertEqual(result["dlq_state"], "discarded")

    def test_resolution_note_echoed_in_response(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            result = self._call(pool, note="falso positivo confirmado")
        self.assertEqual(result["resolution_note"], "falso positivo confirmado")

    def test_note_none_returns_empty_string(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            result = self._call(pool, note=None)
        self.assertEqual(result["resolution_note"], "")

    def test_commits_transaction(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_records_audit_log_with_action(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            self._call(pool, action="acknowledged")
        logs = pool.state["audit_logs"]
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "case_dlq_acknowledged")

    def test_discard_records_audit_log_discarded(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with patch.object(main, "_apply_rls_context"):
            self._call(pool, action="discarded")
        self.assertEqual(pool.state["audit_logs"][0]["action"], "case_dlq_discarded")

    def test_returns_404_when_case_not_found(self) -> None:
        pool = _make_pool(case_row=None)
        with patch.object(main, "_apply_rls_context"):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "case_not_found")

    def test_returns_409_when_case_type_is_not_investigation(self) -> None:
        row = _valid_case_row()
        row["case_type"] = "compliance"
        pool = _make_pool(case_row=row)
        with patch.object(main, "_apply_rls_context"):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "invalid_case_type_for_dlq_resolution")

    def test_returns_409_when_case_status_is_not_failed(self) -> None:
        row = _valid_case_row()
        row["status"] = "completed"
        pool = _make_pool(case_row=row)
        with patch.object(main, "_apply_rls_context"):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "case_not_failed")

    def test_returns_409_when_dlq_state_is_not_failed_permanent(self) -> None:
        row = _valid_case_row()
        row["metadata"] = {"dlq_state": "acknowledged"}
        pool = _make_pool(case_row=row)
        with patch.object(main, "_apply_rls_context"):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "case_not_open_in_dlq")

    def test_returns_409_when_metadata_is_none(self) -> None:
        row = _valid_case_row()
        row["metadata"] = None
        pool = _make_pool(case_row=row)
        with patch.object(main, "_apply_rls_context"):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertEqual(ctx.exception.detail, "case_not_open_in_dlq")

    def test_rejects_non_admin_with_403(self) -> None:
        pool = _make_pool(case_row=_valid_case_row())
        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_require_role_with_audit",
                side_effect=main.HTTPException(status_code=403, detail="admin_required"),
            ),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool, x_role="AUDITOR")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "admin_required")

    def test_rejects_missing_org_id_with_401(self) -> None:
        pool = _make_pool(case_row=None)
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_org_id=None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class InvestigationDlqStateFilterTests(unittest.TestCase):
    """Testa a validacao do parametro state no endpoint GET /api/v1/investigation/admin/dlq."""

    def _call_dlq(self, pool, *, state: str = "failed_permanent") -> Any:
        return asyncio.run(
            main.investigation_dlq(
                state=state,
                target_chain=None,
                can_requeue=None,
                limit=10,
                pool=pool,
                x_org_id=_VALID_ORG,
                x_user_id=_VALID_USER,
                x_linked_user_id=None,
                x_role="ADMIN",
                x_request_id="req-dlq-list-1",
            )
        )

    def test_rejects_invalid_state_with_422(self) -> None:
        from unittest.mock import MagicMock
        pool = MagicMock()
        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call_dlq(pool, state="invalid_state")
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "invalid_dlq_state_filter")

    def test_accepts_all_valid_states(self) -> None:
        from unittest.mock import MagicMock

        valid_states = ["failed_permanent", "acknowledged", "discarded", "resolved", "all"]
        for state in valid_states:
            with self.subTest(state=state):
                # Cursor que retorna org + lista vazia de DLQ
                cursor = MagicMock()
                cursor.__enter__ = lambda s: s
                cursor.__exit__ = MagicMock(return_value=None)
                cursor.fetchone.return_value = {"credits_available": 100.0}
                cursor.fetchall.return_value = []
                conn = MagicMock()
                conn.__enter__ = lambda s: s
                conn.__exit__ = MagicMock(return_value=None)
                conn.cursor.return_value = cursor
                pool = MagicMock()
                pool.connection.return_value = conn

                with (
                    patch.object(main, "_require_role_with_audit"),
                    patch.object(main, "_apply_rls_context"),
                ):
                    result = self._call_dlq(pool, state=state)
                self.assertIn("cases", result)


if __name__ == "__main__":
    unittest.main()
