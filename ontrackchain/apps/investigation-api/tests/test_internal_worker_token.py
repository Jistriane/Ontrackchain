from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any

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
class InternalWorkerTokenTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeAuditPool]:
        state = {"audit_logs": []}
        return state, _FakeAuditPool(state)

    def test_internal_worker_token_allows_when_matches(self) -> None:
        _state, pool = self._build_state()
        main.settings.investigation_internal_worker_token = "expected-token"
        main._require_internal_worker_token_with_audit(
            pool,
            organization_id="org-1",
            request_id="req-1",
            token="expected-token",
            resource_id="case-1",
            endpoint="/api/v1/investigation/case-1/internal/complete",
            method="POST",
        )

    def test_internal_worker_token_denies_when_invalid_and_records_audit(self) -> None:
        state, pool = self._build_state()
        main.settings.investigation_internal_worker_token = "expected-token"
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_internal_worker_token_with_audit(
                pool,
                organization_id="org-1",
                request_id="req-2",
                token="wrong-token",
                resource_id="case-2",
                endpoint="/api/v1/investigation/case-2/internal/fail",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "invalid_internal_token")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        entry = state["audit_logs"][0]
        self.assertEqual(entry["action"], "authorization_denied")
        self.assertEqual(entry["resource_type"], "internal_worker")
        self.assertEqual(entry["resource_id"], "case-2")
        self.assertEqual(entry["metadata"]["detail"], "invalid_internal_token")


if __name__ == "__main__":
    unittest.main()
