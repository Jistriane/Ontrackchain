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
    main: Any = importlib.import_module("monitoring_api.main")
else:
    main = None


class _TriggerCursor:
    """Fake cursor para o endpoint trigger-operational-alert.

    Suporta apenas INSERT INTO operational_alert_events gerado por
    _persist_operational_alert_event.
    """

    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized.startswith("INSERT INTO operational_alert_events"):
            self.state["persisted"].append(
                {
                    "receiver": params_tuple[0],
                    "group_key": params_tuple[1],
                    "status": params_tuple[2],
                    "alertname": params_tuple[3],
                    "service": params_tuple[4],
                    "severity": params_tuple[5],
                    "fingerprint": params_tuple[6],
                    "labels": json.loads(params_tuple[7]),
                    "annotations": json.loads(params_tuple[8]),
                    "generator_url": params_tuple[11],
                    "payload": json.loads(params_tuple[12]),
                }
            )
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized}")

    def __enter__(self) -> "_TriggerCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _TriggerConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.commit_calls = 0

    def cursor(self) -> _TriggerCursor:
        return _TriggerCursor(self.state)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_TriggerConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _TriggerPool:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._conn = _TriggerConnection(state)

    def connection(self) -> _TriggerConnection:
        return self._conn


def _build_state() -> tuple[dict[str, Any], _TriggerPool]:
    state: dict[str, Any] = {"persisted": []}
    return state, _TriggerPool(state)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class TriggerOperationalAlertTests(unittest.TestCase):
    """Testes do endpoint POST /api/v1/monitoring/test/trigger-operational-alert."""

    def _call(
        self,
        pool: _TriggerPool,
        *,
        alertname: str = "OntrackSyntheticOperationalAlert",
        service: str = "platform",
        receiver: str = "monitoring-webhook",
        severity: str = "warning",
        summary: str = "Incidente sintetico de teste",
        description: str = "Incidente sintetico criado para validar a triagem operacional.",
        fingerprint: str | None = None,
    ) -> Any:
        body = main.TriggerOperationalAlertRequest(
            alertname=alertname,
            service=service,
            receiver=receiver,
            severity=severity,
            summary=summary,
            description=description,
            fingerprint=fingerprint,
        )
        return asyncio.run(
            main.trigger_operational_alert(body=body, pool=pool)
        )

    def test_trigger_returns_status_created(self) -> None:
        _state, pool = _build_state()
        result = self._call(pool)
        self.assertEqual(result["status"], "created")

    def test_trigger_persists_one_event(self) -> None:
        state, pool = _build_state()
        self._call(pool)
        self.assertEqual(len(state["persisted"]), 1)

    def test_trigger_persists_correct_alertname_and_service(self) -> None:
        state, pool = _build_state()
        self._call(pool, alertname="QueueLagCritical", service="aml-monitor")
        row = state["persisted"][0]
        self.assertEqual(row["alertname"], "QueueLagCritical")
        self.assertEqual(row["service"], "aml-monitor")

    def test_trigger_persists_status_firing(self) -> None:
        state, pool = _build_state()
        self._call(pool)
        self.assertEqual(state["persisted"][0]["status"], "firing")

    def test_trigger_uses_provided_fingerprint(self) -> None:
        state, pool = _build_state()
        self._call(pool, fingerprint="fp-synthetic-explicit")
        result_fp = state["persisted"][0]["fingerprint"]
        self.assertEqual(result_fp, "fp-synthetic-explicit")

    def test_trigger_generates_fingerprint_when_not_provided(self) -> None:
        state, pool = _build_state()
        result = self._call(pool, fingerprint=None)
        fp = result["fingerprint"]
        self.assertTrue(fp.startswith("synthetic:"))
        self.assertEqual(state["persisted"][0]["fingerprint"], fp)

    def test_trigger_fingerprint_in_response_matches_persisted(self) -> None:
        state, pool = _build_state()
        result = self._call(pool)
        self.assertEqual(result["fingerprint"], state["persisted"][0]["fingerprint"])

    def test_trigger_group_key_contains_service(self) -> None:
        state, pool = _build_state()
        self._call(pool, service="compliance-api")
        self.assertIn("compliance-api", state["persisted"][0]["group_key"])

    def test_trigger_labels_contain_source_synthetic_test(self) -> None:
        state, pool = _build_state()
        self._call(pool)
        labels = state["persisted"][0]["labels"]
        self.assertEqual(labels.get("source"), "synthetic_test")

    def test_trigger_annotations_contain_summary_and_description(self) -> None:
        state, pool = _build_state()
        self._call(pool, summary="Latencia alta", description="Latencia acima de 500ms")
        annotations = state["persisted"][0]["annotations"]
        self.assertEqual(annotations["summary"], "Latencia alta")
        self.assertEqual(annotations["description"], "Latencia acima de 500ms")

    def test_trigger_commits_transaction(self) -> None:
        _state, pool = _build_state()
        self._call(pool)
        self.assertEqual(pool._conn.commit_calls, 1)

    def test_trigger_returns_404_when_test_endpoints_disabled(self) -> None:
        _state, pool = _build_state()
        with patch.object(main.settings, "enable_test_endpoints", False):
            with self.assertRaises(main.HTTPException) as ctx:
                self._call(pool)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "not_found")

    def test_trigger_does_not_persist_when_test_endpoints_disabled(self) -> None:
        state, pool = _build_state()
        with patch.object(main.settings, "enable_test_endpoints", False):
            with self.assertRaises(main.HTTPException):
                self._call(pool)
        self.assertEqual(len(state["persisted"]), 0)
        self.assertEqual(pool._conn.commit_calls, 0)

    def test_trigger_payload_contains_fingerprint(self) -> None:
        state, pool = _build_state()
        result = self._call(pool, fingerprint="fp-payload-check")
        payload = state["persisted"][0]["payload"]
        self.assertEqual(payload["fingerprint"], "fp-payload-check")

    def test_trigger_generator_url_is_synthetic(self) -> None:
        state, pool = _build_state()
        self._call(pool)
        self.assertEqual(
            state["persisted"][0]["generator_url"],
            "synthetic://monitoring-api/test-trigger",
        )


if __name__ == "__main__":
    unittest.main()
