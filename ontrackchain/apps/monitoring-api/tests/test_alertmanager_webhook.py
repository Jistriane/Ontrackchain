from __future__ import annotations

import asyncio
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
    main: Any = importlib.import_module("monitoring_api.main")
else:
    main = None


class _FakeOperationalAlertsCursor:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized_query.startswith("INSERT INTO operational_alert_events"):
            self.state["operational_alert_events"].append(
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

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def __enter__(self) -> "_FakeOperationalAlertsCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeOperationalAlertsConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.commit_calls = 0
        self.cursor_calls = 0

    def cursor(self) -> _FakeOperationalAlertsCursor:
        self.cursor_calls += 1
        return _FakeOperationalAlertsCursor(self.state)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_FakeOperationalAlertsConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeOperationalAlertsPool:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.connection_calls = 0
        self._connection = _FakeOperationalAlertsConnection(state)

    def connection(self) -> _FakeOperationalAlertsConnection:
        self.connection_calls += 1
        return self._connection


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class AlertmanagerWebhookTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeOperationalAlertsPool]:
        state = {"operational_alert_events": []}
        return state, _FakeOperationalAlertsPool(state)

    def _build_request(self) -> Any:
        return main.AlertmanagerWebhookRequest(
            receiver="monitoring-webhook",
            status="firing",
            groupKey="group-1",
            commonLabels={"service": "aml-monitor", "severity": "critical"},
            alerts=[
                {
                    "status": "firing",
                    "fingerprint": "fp-alertmanager-1",
                    "labels": {
                        "alertname": "QueueLagCritical",
                        "service": "aml-monitor",
                        "severity": "critical",
                    },
                    "annotations": {
                        "summary": "Queue lag critical",
                        "description": "Queue lag above threshold",
                    },
                    "generatorURL": "http://prometheus.local/graph?g0.expr=queue_lag",
                }
            ],
        )

    def test_receive_alertmanager_webhook_rejects_invalid_token_without_persisting(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.receive_alertmanager_webhook(
                    body=self._build_request(),
                    pool=pool,
                    authorization="Bearer invalid-token",
                )
            )

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "invalid_internal_token")
        self.assertEqual(pool.connection_calls, 0)
        self.assertEqual(pool._connection.cursor_calls, 0)
        self.assertEqual(pool._connection.commit_calls, 0)
        self.assertEqual(state["operational_alert_events"], [])

    def test_receive_alertmanager_webhook_accepts_valid_token_and_persists_alert(self) -> None:
        state, pool = self._build_state()

        response = asyncio.run(
            main.receive_alertmanager_webhook(
                body=self._build_request(),
                pool=pool,
                authorization=f"Bearer {main.settings.alertmanager_webhook_bearer_token}",
            )
        )

        self.assertEqual(response, {"status": "accepted", "received": 1})
        self.assertEqual(pool.connection_calls, 1)
        self.assertEqual(pool._connection.cursor_calls, 1)
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["operational_alert_events"]), 1)
        persisted_event = state["operational_alert_events"][0]
        self.assertEqual(persisted_event["receiver"], "monitoring-webhook")
        self.assertEqual(persisted_event["group_key"], "group-1")
        self.assertEqual(persisted_event["status"], "firing")
        self.assertEqual(persisted_event["alertname"], "QueueLagCritical")
        self.assertEqual(persisted_event["service"], "aml-monitor")
        self.assertEqual(persisted_event["severity"], "critical")
        self.assertEqual(persisted_event["fingerprint"], "fp-alertmanager-1")
        self.assertEqual(persisted_event["annotations"]["summary"], "Queue lag critical")


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class PersistOperationalAlertEventTests(unittest.TestCase):
    """
    Testa _persist_operational_alert_event diretamente, verificando o SQL gerado
    e os parâmetros posicionais — especialmente o comportamento do CASE WHEN para
    o ciclo resolved->firing que reseta triage_status, triaged_at, triaged_by e triage_note.
    """

    def _make_spy_cursor(self) -> "_SpyCursor":
        return _SpyCursor()

    def _call_persist(self, cur: "_SpyCursor", *, alert_status: str = "firing") -> None:
        main._persist_operational_alert_event(
            cur,
            receiver="alertmanager-main",
            group_key="grp-test-1",
            alert_status=alert_status,
            alertname="HighMemoryUsage",
            service="compliance-api",
            severity="warning",
            fingerprint="fp-persist-test-1",
            labels={"alertname": "HighMemoryUsage", "service": "compliance-api"},
            annotations={"summary": "Memory above threshold"},
            starts_at=None,
            ends_at=None,
            generator_url="http://prom.local/graph",
            payload={"status": alert_status},
        )

    def test_persist_firing_inserts_pending_triage_status_in_sql(self) -> None:
        cur = self._make_spy_cursor()
        self._call_persist(cur, alert_status="firing")

        self.assertEqual(len(cur.calls), 1)
        query, params = cur.calls[0]
        # O INSERT inicial define triage_status = 'pending' explicitamente
        self.assertIn("'pending'", query)
        # O status enviado deve ser 'firing' (3º parâmetro posicional)
        self.assertEqual(params[2], "firing")
        # O fingerprint deve estar presente (7º parâmetro posicional)
        self.assertEqual(params[6], "fp-persist-test-1")

    def test_persist_resolved_sets_resolved_status_in_params(self) -> None:
        cur = self._make_spy_cursor()
        self._call_persist(cur, alert_status="resolved")

        self.assertEqual(len(cur.calls), 1)
        _, params = cur.calls[0]
        self.assertEqual(params[2], "resolved")

    def test_persist_sql_contains_resolved_to_firing_triage_reset_case(self) -> None:
        """
        Verifica que o SQL emitido contém o CASE WHEN para reset de triage_status
        quando o status anterior era 'resolved' e o novo é 'firing'.
        Essa prova documenta que a lógica está no SQL e protege contra remoção acidental.
        """
        cur = self._make_spy_cursor()
        self._call_persist(cur, alert_status="firing")

        query, _ = cur.calls[0]
        normalized = " ".join(query.split())
        # O CASE WHEN de reset de triage_status deve estar presente
        self.assertIn("WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN 'pending'", normalized)
        # O mesmo padrão para triaged_at
        self.assertIn("WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN NULL", normalized)

    def test_persist_firing_after_resolved_params_contain_correct_status(self) -> None:
        """
        Simula dois ciclos de persistência (firing -> resolved -> firing) via
        duas chamadas diretas a _persist_operational_alert_event e verifica que
        os parâmetros de status passados ao banco são os esperados em cada ciclo.
        """
        cur = self._make_spy_cursor()

        # Ciclo 1: alerta firing
        self._call_persist(cur, alert_status="firing")
        self.assertEqual(cur.calls[0][1][2], "firing")

        # Ciclo 2: alerta resolved
        self._call_persist(cur, alert_status="resolved")
        self.assertEqual(cur.calls[1][1][2], "resolved")

        # Ciclo 3: alerta reabre (firing)
        self._call_persist(cur, alert_status="firing")
        self.assertEqual(cur.calls[2][1][2], "firing")

        # Garante que a query do ciclo 3 ainda contém o CASE WHEN de reset
        normalized = " ".join(cur.calls[2][0].split())
        self.assertIn("WHEN operational_alert_events.status = 'resolved' AND EXCLUDED.status = 'firing' THEN 'pending'", normalized)


class _SpyCursor:
    """Cursor spy que captura todas as queries e parâmetros passados via execute()."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, query: str, params: tuple = ()) -> None:
        self.calls.append((query, tuple(params)))

    def __enter__(self) -> "_SpyCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


if __name__ == "__main__":
    unittest.main()
