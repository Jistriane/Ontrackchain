from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("monitoring_api.main")
else:
    main = None

_VALID_ORG_ID = "org-test-batch"
_VALID_USER_ID = "33333333-3333-3333-3333-333333333333"

_ID_1 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_ID_2 = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_ID_3 = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


class _BatchCursor:
    """Fake cursor para o endpoint acknowledge-batch.

    Captura a query UPDATE completa (com todos os filtros dinâmicos) e
    devolve um fetchall() simulando N rows atualizadas com base em
    quantos IDs foram passados no filtro ids (ou num_rows fixo).
    """

    def __init__(
        self,
        state: dict[str, Any],
        *,
        num_rows_returned: int = 1,
    ) -> None:
        self.state = state
        self.num_rows_returned = num_rows_returned
        self._fetchall_value: list[Any] = []
        self.last_query: str = ""
        self.last_params: tuple[Any, ...] = ()

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized.startswith("SELECT set_config("):
            return

        if normalized == "SELECT 1 FROM users WHERE id = %s":
            return

        if normalized.startswith("INSERT INTO audit_logs"):
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
            return

        if normalized.startswith("UPDATE operational_alert_events"):
            self.last_query = normalized
            self.last_params = params_tuple
            now = datetime.now(timezone.utc)
            # Devolve N rows simulando N updates (id é suficiente)
            self._fetchall_value = [
                {"id": str(_ID_1)} for _ in range(self.num_rows_returned)
            ]
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized}")

    def fetchall(self) -> list[Any]:
        return self._fetchall_value

    def fetchone(self) -> Any:
        return None

    def __enter__(self) -> "_BatchCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _BatchConnection:
    def __init__(self, state: dict[str, Any], *, num_rows_returned: int = 1) -> None:
        self.state = state
        self.num_rows_returned = num_rows_returned
        self.commit_calls = 0
        self._cursor = _BatchCursor(state, num_rows_returned=num_rows_returned)

    def cursor(self) -> _BatchCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_BatchConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _BatchPool:
    def __init__(self, state: dict[str, Any], *, num_rows_returned: int = 1) -> None:
        self.state = state
        self._conn = _BatchConnection(state, num_rows_returned=num_rows_returned)

    def connection(self) -> _BatchConnection:
        return self._conn


def _build_state(*, num_rows_returned: int = 1) -> tuple[dict[str, Any], _BatchPool]:
    state: dict[str, Any] = {
        "users": {_VALID_USER_ID},
        "audit_logs": [],
    }
    return state, _BatchPool(state, num_rows_returned=num_rows_returned)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class AcknowledgeBatchTests(unittest.TestCase):
    """Testes do endpoint POST /api/v1/monitoring/admin/operational-alerts/acknowledge-batch."""

    def _call(
        self,
        pool: _BatchPool,
        *,
        ids: list[UUID] | None = None,
        note: str | None = None,
        triaged_by: str = "admin_ui",
        status: str | None = None,
        triage_status: str | None = None,
        service: str | None = None,
        receiver: str | None = None,
        severity: str | None = None,
        x_role: str = "ADMIN",
        x_org_id: str | None = _VALID_ORG_ID,
        x_user_id: str | None = _VALID_USER_ID,
    ) -> Any:
        body = main.AcknowledgeOperationalAlertsBatchRequest(
            ids=ids or [],
            note=note,
            triaged_by=triaged_by,
            status=status,
            triage_status=triage_status,
            service=service,
            receiver=receiver,
            severity=severity,
        )
        return asyncio.run(
            main.acknowledge_operational_alerts_batch(
                body=body,
                pool=pool,
                x_org_id=x_org_id,
                x_user_id=x_user_id,
                x_linked_user_id=None,
                x_role=x_role,
                x_request_id="req-batch-test-1",
            )
        )

    def test_batch_returns_updated_count(self) -> None:
        _state, pool = _build_state(num_rows_returned=3)
        result = self._call(pool)
        self.assertEqual(result["updated_count"], 3)
        self.assertEqual(result["triage_status"], "acknowledged")

    def test_batch_selected_count_matches_ids_passed(self) -> None:
        _state, pool = _build_state(num_rows_returned=2)
        result = self._call(pool, ids=[_ID_1, _ID_2])
        self.assertEqual(result["selected_count"], 2)

    def test_batch_with_no_ids_has_selected_count_zero(self) -> None:
        _state, pool = _build_state(num_rows_returned=1)
        result = self._call(pool, ids=[])
        self.assertEqual(result["selected_count"], 0)

    def test_batch_query_contains_ids_filter_when_ids_provided(self) -> None:
        _state, pool = _build_state()
        self._call(pool, ids=[_ID_1, _ID_2, _ID_3])
        cur = pool._conn._cursor
        self.assertIn("AND id = ANY(%s::uuid[])", cur.last_query)

    def test_batch_query_does_not_contain_ids_filter_when_empty(self) -> None:
        _state, pool = _build_state()
        self._call(pool, ids=[])
        cur = pool._conn._cursor
        self.assertNotIn("ANY", cur.last_query)

    def test_batch_query_contains_severity_filter(self) -> None:
        _state, pool = _build_state()
        self._call(pool, severity="critical")
        cur = pool._conn._cursor
        self.assertIn("AND severity = %s", cur.last_query)
        self.assertIn("critical", cur.last_params)

    def test_batch_query_contains_service_filter(self) -> None:
        _state, pool = _build_state()
        self._call(pool, service="aml-monitor")
        cur = pool._conn._cursor
        self.assertIn("AND service = %s", cur.last_query)
        self.assertIn("aml-monitor", cur.last_params)

    def test_batch_query_always_filters_pending_triage_status(self) -> None:
        _state, pool = _build_state()
        self._call(pool)
        cur = pool._conn._cursor
        self.assertIn("WHERE triage_status = 'pending'", cur.last_query)

    def test_batch_records_audit_log_with_updated_count(self) -> None:
        state, pool = _build_state(num_rows_returned=5)
        self._call(pool)
        self.assertEqual(len(state["audit_logs"]), 1)
        log = state["audit_logs"][0]
        self.assertEqual(log["action"], "operational_alerts_acknowledged_batch")
        self.assertEqual(log["metadata"]["updated_count"], 5)

    def test_batch_audit_log_contains_filters(self) -> None:
        state, pool = _build_state()
        self._call(pool, severity="critical", service="aml-monitor")
        log = state["audit_logs"][0]
        self.assertEqual(log["metadata"]["filters"]["severity"], "critical")
        self.assertEqual(log["metadata"]["filters"]["service"], "aml-monitor")
        self.assertIsNone(log["metadata"]["filters"]["status"])

    def test_batch_commits_transaction(self) -> None:
        _state, pool = _build_state()
        self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_batch_rejects_non_admin_role(self) -> None:
        _state, pool = _build_state()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_role="VIEWER")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "admin_role_required")

    def test_batch_rejects_missing_org_id(self) -> None:
        _state, pool = _build_state()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_org_id=None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")

    def test_batch_returns_zero_updated_count_without_error_when_no_rows(self) -> None:
        _state, pool = _build_state(num_rows_returned=0)
        result = self._call(pool)
        self.assertEqual(result["updated_count"], 0)
        self.assertEqual(result["triage_status"], "acknowledged")

    def test_batch_result_contains_filter_echo(self) -> None:
        _state, pool = _build_state()
        result = self._call(pool, severity="warning", service="compliance-api")
        self.assertEqual(result["severity_filter"], "warning")
        self.assertEqual(result["service_filter"], "compliance-api")
        self.assertIsNone(result["status_filter"])


if __name__ == "__main__":
    unittest.main()
