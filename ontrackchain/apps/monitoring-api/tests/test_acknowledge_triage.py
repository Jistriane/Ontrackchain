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

_VALID_ORG_ID = "org-test-triage"
_VALID_USER_ID = "22222222-2222-2222-2222-222222222222"
_VALID_EVENT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class _AcknowledgeCursor:
    """Fake cursor para o endpoint acknowledge-by-id.

    Suporta as queries emitidas por _require_role_with_audit e
    acknowledge_operational_alert:
      - set_config (para RLS)
      - SELECT 1 FROM users
      - INSERT INTO audit_logs
      - UPDATE operational_alert_events ... RETURNING
    """

    def __init__(self, state: dict[str, Any], *, event_exists: bool = True) -> None:
        self.state = state
        self.event_exists = event_exists
        self._fetchone_value: Any = None

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized.startswith("SELECT set_config("):
            self._fetchone_value = {"set_config": params_tuple[0] if params_tuple else None}
            return

        if normalized == "SELECT 1 FROM users WHERE id = %s":
            self._fetchone_value = (
                {"exists": 1} if str(params_tuple[0]) in self.state["users"] else None
            )
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
            self._fetchone_value = None
            return

        if normalized.startswith("UPDATE operational_alert_events"):
            if self.event_exists:
                now = datetime.now(timezone.utc)
                note = params_tuple[2] if len(params_tuple) > 2 else None
                triaged_by = params_tuple[1] if len(params_tuple) > 1 else "admin_ui"
                self._fetchone_value = {
                    "id": str(params_tuple[3]) if len(params_tuple) > 3 else str(_VALID_EVENT_ID),
                    "status": "firing",
                    "triage_status": "acknowledged",
                    "triaged_at": now.isoformat(),
                    "triaged_by": triaged_by,
                    "triage_note": note,
                }
                self.state["acknowledged"].append(self._fetchone_value)
            else:
                self._fetchone_value = None
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized}")

    def fetchone(self) -> Any:
        return self._fetchone_value

    def __enter__(self) -> "_AcknowledgeCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _AcknowledgeConnection:
    def __init__(self, state: dict[str, Any], *, event_exists: bool = True) -> None:
        self.state = state
        self.event_exists = event_exists
        self.commit_calls = 0

    def cursor(self) -> _AcknowledgeCursor:
        return _AcknowledgeCursor(self.state, event_exists=self.event_exists)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_AcknowledgeConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _AcknowledgePool:
    def __init__(self, state: dict[str, Any], *, event_exists: bool = True) -> None:
        self.state = state
        self._conn = _AcknowledgeConnection(state, event_exists=event_exists)

    def connection(self) -> _AcknowledgeConnection:
        return self._conn


def _build_state(*, with_user: bool = True) -> tuple[dict[str, Any], _AcknowledgePool]:
    state: dict[str, Any] = {
        "users": {_VALID_USER_ID} if with_user else set(),
        "audit_logs": [],
        "acknowledged": [],
    }
    return state, _AcknowledgePool(state)


def _build_state_missing_event() -> tuple[dict[str, Any], _AcknowledgePool]:
    state: dict[str, Any] = {
        "users": {_VALID_USER_ID},
        "audit_logs": [],
        "acknowledged": [],
    }
    return state, _AcknowledgePool(state, event_exists=False)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class AcknowledgeOperationalAlertTests(unittest.TestCase):
    """Testes do endpoint POST /api/v1/monitoring/admin/operational-alerts/{event_id}/acknowledge."""

    def _call(
        self,
        pool: _AcknowledgePool,
        *,
        event_id: UUID = _VALID_EVENT_ID,
        note: str | None = "Investigado e mitigado",
        triaged_by: str = "admin_ui",
        x_role: str = "ADMIN",
        x_org_id: str | None = _VALID_ORG_ID,
        x_user_id: str | None = _VALID_USER_ID,
    ) -> Any:
        body = main.AcknowledgeOperationalAlertRequest(note=note, triaged_by=triaged_by)
        return asyncio.run(
            main.acknowledge_operational_alert(
                event_id=event_id,
                body=body,
                pool=pool,
                x_org_id=x_org_id,
                x_user_id=x_user_id,
                x_linked_user_id=None,
                x_role=x_role,
                x_request_id="req-ack-test-1",
            )
        )

    def test_acknowledge_sets_triage_status_to_acknowledged(self) -> None:
        state, pool = _build_state()
        result = self._call(pool)
        self.assertEqual(result["triage_status"], "acknowledged")
        self.assertEqual(len(state["acknowledged"]), 1)

    def test_acknowledge_persists_note(self) -> None:
        state, pool = _build_state()
        self._call(pool, note="Falso positivo confirmado")
        self.assertEqual(state["acknowledged"][0]["triage_note"], "Falso positivo confirmado")

    def test_acknowledge_records_audit_log(self) -> None:
        state, pool = _build_state()
        self._call(pool)
        self.assertEqual(len(state["audit_logs"]), 1)
        log = state["audit_logs"][0]
        self.assertEqual(log["action"], "operational_alert_acknowledged")
        self.assertEqual(log["resource_type"], "operational_alerts")
        self.assertEqual(log["resource_id"], str(_VALID_EVENT_ID))

    def test_acknowledge_commits_transaction(self) -> None:
        _state, pool = _build_state()
        self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_acknowledge_rejects_non_admin_role(self) -> None:
        _state, pool = _build_state()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_role="VIEWER")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "admin_role_required")

    def test_acknowledge_rejects_missing_org_id(self) -> None:
        _state, pool = _build_state()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool, x_org_id=None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "missing_org_context")

    def test_acknowledge_returns_404_when_event_not_found(self) -> None:
        _state, pool = _build_state_missing_event()
        with self.assertRaises(main.HTTPException) as ctx:
            self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "operational_alert_not_found")

    def test_acknowledge_does_not_commit_on_404(self) -> None:
        _state, pool = _build_state_missing_event()
        with self.assertRaises(main.HTTPException):
            self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 0)

    def test_acknowledge_note_can_be_none(self) -> None:
        state, pool = _build_state()
        result = self._call(pool, note=None)
        self.assertEqual(result["triage_status"], "acknowledged")
        self.assertIsNone(state["acknowledged"][0]["triage_note"])

    def test_acknowledge_audit_log_contains_triaged_by(self) -> None:
        state, pool = _build_state()
        self._call(pool, triaged_by="admin_ui", x_user_id=_VALID_USER_ID)
        log = state["audit_logs"][0]
        # user_id do header tem precedencia sobre triaged_by do body
        self.assertIn("triaged_by", log["metadata"])
        self.assertEqual(log["metadata"]["triaged_by"], _VALID_USER_ID)


if __name__ == "__main__":
    unittest.main()
