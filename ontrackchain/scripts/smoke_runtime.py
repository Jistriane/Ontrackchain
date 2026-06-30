#!/usr/bin/env python3
from __future__ import annotations

import base64
import hmac
import json
import hashlib
import http.cookiejar
import os
from pathlib import Path
import struct
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
import uuid


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv_values(file_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not file_path.exists():
        return values
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


DOTENV_VALUES = load_dotenv_values(REPO_ROOT / ".env")


def env_value(name: str, default: str) -> str:
    return os.getenv(name) or DOTENV_VALUES.get(name) or default


BASE_URL = os.getenv("ONTRACKCHAIN_BASE_URL") or env_value(
    "NEXT_PUBLIC_API_BASE_URL", f"http://localhost:{env_value('TRAEFIK_HTTP_PORT', '8080')}"
)
PROMETHEUS_URL = os.getenv("ONTRACKCHAIN_PROMETHEUS_URL") or f"http://localhost:{env_value('PROMETHEUS_PORT', '9091')}"
GRAFANA_URL = os.getenv("ONTRACKCHAIN_GRAFANA_URL") or f"http://localhost:{env_value('GRAFANA_PORT', '3002')}"
ALERTMANAGER_URL = os.getenv("ONTRACKCHAIN_ALERTMANAGER_URL") or f"http://localhost:{env_value('ALERTMANAGER_PORT', '9093')}"
GRAFANA_USER = os.getenv("ONTRACKCHAIN_GRAFANA_USER") or env_value("GRAFANA_ADMIN_USER", "admin")
GRAFANA_PASSWORD = os.getenv("ONTRACKCHAIN_GRAFANA_PASSWORD") or env_value("GRAFANA_ADMIN_PASSWORD", "admin")
API_KEY = os.getenv("ONTRACKCHAIN_API_KEY", "otc_live_demo_key")
ORG_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000002"
RUN_ID = os.getenv("ONTRACKCHAIN_SMOKE_RUN_ID") or uuid.uuid4().hex[:12]
MFA_TOTP_SECRET = os.getenv("MFA_TOTP_SECRET", "JBSWY3DPEHPK3PXP")


def generate_totp_code(secret: str = MFA_TOTP_SECRET, timestamp: float | None = None) -> str:
    normalized = secret.replace(" ", "").strip().upper()
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    key = base64.b32decode(f"{normalized}{padding}", casefold=True)
    counter = int((timestamp if timestamp is not None else time.time()) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(binary % 1_000_000).zfill(6)


def request(
    method: str, path: str, data: dict | None = None, headers: dict | None = None, request_id: str | None = None
) -> tuple[int, dict]:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request_headers = {"content-type": "application/json"}
    if headers:
        request_headers.update(headers)
    if request_id:
        request_headers["X-Request-Id"] = request_id
    if "X-Request-Id" not in request_headers and "x-request-id" not in request_headers:
        request_headers["X-Request-Id"] = f"smoke-{RUN_ID}-{uuid.uuid4().hex[:12]}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=request_headers, method=method)
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            payload = exc.read().decode("utf-8")
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = {"raw": payload}
            return exc.code, parsed
        except urllib.error.URLError as exc:
            if attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return 599, {"error": str(exc)}
    return 599, {"error": "unexpected_retry_exit"}


def request_json_at_base(
    base_url: str, method: str, path: str, *, headers: dict | None = None, request_id: str | None = None
) -> tuple[int, dict]:
    request_headers = {"content-type": "application/json"}
    if headers:
        request_headers.update(headers)
    if request_id:
        request_headers["X-Request-Id"] = request_id
    req = urllib.request.Request(f"{base_url}{path}", data=None, headers=request_headers, method=method)
    for attempt in range(15):
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8")
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = {"raw": payload}
            return exc.code, parsed
        except urllib.error.URLError as exc:
            if attempt < 14:
                time.sleep(1.0)
                continue
            return 599, {"error": str(exc)}
    return 599, {"error": "unexpected_retry_exit"}


def basic_auth_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def request_raw(method: str, path: str, *, headers: dict | None = None, request_id: str | None = None) -> tuple[int, bytes, dict]:
    request_headers: dict[str, str] = {}
    if headers:
        request_headers.update(headers)
    if request_id:
        request_headers["X-Request-Id"] = request_id
    if "X-Request-Id" not in request_headers and "x-request-id" not in request_headers:
        request_headers["X-Request-Id"] = f"smoke-{RUN_ID}-{uuid.uuid4().hex[:12]}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=None, headers=request_headers, method=method)
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return exc.code, exc.read(), dict(exc.headers)
        except urllib.error.URLError as exc:
            if attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return 599, str(exc).encode("utf-8"), {}
    return 599, b"unexpected_retry_exit", {}

def request_opener_json(
    opener,
    method: str,
    path: str,
    *,
    data: dict | None = None,
    headers: dict | None = None,
    request_id: str | None = None,
) -> tuple[int, dict]:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request_headers: dict[str, str] = {"content-type": "application/json"}
    if headers:
        request_headers.update(headers)
    if request_id:
        request_headers["X-Request-Id"] = request_id
    if "X-Request-Id" not in request_headers and "x-request-id" not in request_headers:
        request_headers["X-Request-Id"] = f"smoke-{RUN_ID}-{uuid.uuid4().hex[:12]}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=request_headers, method=method)
    for attempt in range(10):
        try:
            with opener.open(req) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            payload = exc.read().decode("utf-8")
            try:
                parsed = json.loads(payload)
            except json.JSONDecodeError:
                parsed = {"raw": payload}
            return exc.code, parsed
        except urllib.error.URLError as exc:
            if attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return 599, {"error": str(exc)}
    return 599, {"error": "unexpected_retry_exit"}


def request_opener_raw(
    opener, method: str, path: str, *, headers: dict | None = None, request_id: str | None = None
) -> tuple[int, bytes, dict]:
    request_headers: dict[str, str] = {}
    if headers:
        request_headers.update(headers)
    if request_id:
        request_headers["X-Request-Id"] = request_id
    if "X-Request-Id" not in request_headers and "x-request-id" not in request_headers:
        request_headers["X-Request-Id"] = f"smoke-{RUN_ID}-{uuid.uuid4().hex[:12]}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=None, headers=request_headers, method=method)
    for attempt in range(10):
        try:
            with opener.open(req) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (502, 503, 504) and attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return exc.code, exc.read(), dict(exc.headers)
        except urllib.error.URLError as exc:
            if attempt < 9:
                time.sleep(0.4 * (attempt + 1))
                continue
            return 599, str(exc).encode("utf-8"), {}
    return 599, b"unexpected_retry_exit", {}


def expect_status(name: str, actual: int, expected: int) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: esperado HTTP {expected}, recebido {actual}")


def call(name: str, method: str, path: str, data: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
    return request(method, path, data=data, headers=headers, request_id=f"smoke-{RUN_ID}-{name}")


def wait_for_prometheus_target_up(job_name: str, timeout_seconds: int = 45) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        status, payload = request_json_at_base(
            PROMETHEUS_URL,
            "GET",
            "/api/v1/targets",
            request_id=f"smoke-{RUN_ID}-prometheus_targets",
        )
        expect_status(f"prometheus_targets[{job_name}]", status, 200)
        last_payload = payload
        active_targets = ((payload.get("data") or {}).get("activeTargets") or [])
        for target in active_targets:
            labels = target.get("labels") or {}
            if labels.get("job") == job_name and target.get("health") == "up":
                return target
        time.sleep(1.0)
    raise AssertionError(f"prometheus_targets[{job_name}]: alvo nao ficou healthy, ultimo={last_payload}")


def wait_for_prometheus_rule_group(group_name: str, timeout_seconds: int = 30) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        status, payload = request_json_at_base(
            PROMETHEUS_URL,
            "GET",
            "/api/v1/rules",
            request_id=f"smoke-{RUN_ID}-prometheus_rules",
        )
        expect_status(f"prometheus_rules[{group_name}]", status, 200)
        last_payload = payload
        groups = ((payload.get("data") or {}).get("groups") or [])
        for group in groups:
            if group.get("name") == group_name:
                return group
        time.sleep(1.0)
    raise AssertionError(f"prometheus_rules[{group_name}]: grupo nao encontrado, ultimo={last_payload}")


def wait_for_grafana_dashboard(uid: str, timeout_seconds: int = 45) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    headers = basic_auth_header(GRAFANA_USER, GRAFANA_PASSWORD)
    while time.time() < deadline:
        health_status, health_payload = request_json_at_base(
            GRAFANA_URL,
            "GET",
            "/api/health",
            headers=headers,
            request_id=f"smoke-{RUN_ID}-grafana_health",
        )
        expect_status("grafana_health", health_status, 200)
        status, payload = request_json_at_base(
            GRAFANA_URL,
            "GET",
            f"/api/dashboards/uid/{uid}",
            headers=headers,
            request_id=f"smoke-{RUN_ID}-grafana_dashboard",
        )
        if status == 200:
            return {"health": health_payload, "dashboard": payload}
        last_payload = payload
        time.sleep(1.0)
    raise AssertionError(f"grafana_dashboard[{uid}]: dashboard nao encontrado, ultimo={last_payload}")


def wait_for_alertmanager_alert(alertname: str, timeout_seconds: int = 75) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: list[dict] | dict = []
    while time.time() < deadline:
        status, payload = request_json_at_base(
            ALERTMANAGER_URL,
            "GET",
            "/api/v2/alerts",
            request_id=f"smoke-{RUN_ID}-alertmanager_alerts",
        )
        expect_status(f"alertmanager_alerts[{alertname}]", status, 200)
        last_payload = payload
        if isinstance(payload, list):
            for alert in payload:
                labels = alert.get("labels") or {}
                state = ((alert.get("status") or {}).get("state")) or ""
                if labels.get("alertname") == alertname and state in {"active", "suppressed"}:
                    return alert
        time.sleep(2.0)
    raise AssertionError(f"alertmanager_alert[{alertname}]: alerta nao encontrado, ultimo={last_payload}")


def wait_for_operational_alert_event(alertname: str, headers: dict, timeout_seconds: int = 75) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        status, payload = request(
            "GET",
            "/api/v1/monitoring/admin/operational-alerts?limit=100",
            headers=headers,
            request_id=f"smoke-{RUN_ID}-operational_alert_events",
        )
        expect_status(f"operational_alert_events[{alertname}]", status, 200)
        last_payload = payload
        for row in payload.get("data") or []:
            if row.get("alertname") == alertname:
                return row
        time.sleep(2.0)
    raise AssertionError(f"operational_alert_event[{alertname}]: evento nao encontrado, ultimo={last_payload}")


def wait_for_operational_alert_fingerprint(
    fingerprint: str, headers: dict, *, triage_status: str | None = None, timeout_seconds: int = 45
) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        status, payload = request(
            "GET",
            "/api/v1/monitoring/admin/operational-alerts?limit=100",
            headers=headers,
            request_id=f"smoke-{RUN_ID}-operational_alert_fingerprint",
        )
        expect_status(f"operational_alert_fingerprint[{fingerprint}]", status, 200)
        last_payload = payload
        for row in payload.get("data") or []:
            if row.get("fingerprint") != fingerprint:
                continue
            if triage_status and row.get("triage_status") != triage_status:
                continue
            return row
        time.sleep(1.5)
    raise AssertionError(
        "operational_alert_fingerprint:"
        f" evento nao encontrado fingerprint={fingerprint} triage_status={triage_status} ultimo={last_payload}"
    )


def wait_for_case_terminal(case_id: str, headers: dict, timeout_seconds: int = 30) -> dict:
    deadline = time.time() + timeout_seconds
    last_payload: dict = {}
    while time.time() < deadline:
        status, payload = request(
            "GET",
            f"/api/v1/investigation/{case_id}/status",
            headers=headers,
            request_id=f"smoke-{RUN_ID}-investigation_status_{case_id}",
        )
        expect_status(f"investigation_status[{case_id}]", status, 200)
        last_payload = payload
        if payload.get("status") in {"completed", "failed", "billing_recalc_required"}:
            return payload
        time.sleep(1.0)
    raise AssertionError(f"investigation_status[{case_id}]: timeout aguardando estado terminal, ultimo={last_payload}")


def issue_dev_token(plan: str) -> str:
    status, payload = call(
        f"issue_dev_token_{plan}",
        "POST",
        "/auth/issue-dev-token",
        data={
            "org_id": ORG_ID,
            "user_id": USER_ID,
            "plan": plan,
            "role": "ADMIN",
            "expires_in_minutes": 60,
        },
    )
    expect_status(f"issue_dev_token[{plan}]", status, 200)
    token = payload.get("token")
    if not token:
        raise AssertionError(f"issue_dev_token[{plan}]: token ausente")
    return token


def main() -> int:
    results: list[dict] = []
    api_key_headers = {"X-API-Key": API_KEY}
    admin_api_key_headers = {"X-API-Key": API_KEY, "X-Role": "ADMIN"}

    target = wait_for_prometheus_target_up("investigation-api")
    rule_group = wait_for_prometheus_rule_group("ontrack-investigation-operational")
    grafana_dashboard = wait_for_grafana_dashboard("ontrack-investigation-operations")
    monitoring_target = wait_for_prometheus_target_up("monitoring-api")
    monitoring_rule_group = wait_for_prometheus_rule_group("ontrack-monitoring-operational")
    monitoring_grafana_dashboard = wait_for_grafana_dashboard("ontrack-monitoring-operations")
    compliance_target = wait_for_prometheus_target_up("compliance-api")
    compliance_rule_group = wait_for_prometheus_rule_group("ontrack-compliance-operational")
    compliance_grafana_dashboard = wait_for_grafana_dashboard("ontrack-compliance-operations")
    report_target = wait_for_prometheus_target_up("report-api")
    report_rule_group = wait_for_prometheus_rule_group("ontrack-report-operational")
    report_grafana_dashboard = wait_for_grafana_dashboard("ontrack-report-operations")
    platform_rule_group = wait_for_prometheus_rule_group("ontrack-platform-operational")
    platform_grafana_dashboard = wait_for_grafana_dashboard("ontrack-platform-alerting")
    alertmanager_watchdog = wait_for_alertmanager_alert("OntrackPlatformWatchdog")
    operational_watchdog = wait_for_operational_alert_event("OntrackPlatformWatchdog", admin_api_key_headers)
    rules = rule_group.get("rules") or []
    monitoring_rules = monitoring_rule_group.get("rules") or []
    compliance_rules = compliance_rule_group.get("rules") or []
    report_rules = report_rule_group.get("rules") or []
    platform_rules = platform_rule_group.get("rules") or []
    results.append(
        {
            "name": "prometheus_investigation_target",
            "status": 200,
            "summary": {"scrapeUrl": target.get("scrapeUrl"), "lastScrape": target.get("lastScrape")},
        }
    )
    results.append(
        {
            "name": "prometheus_investigation_rules",
            "status": 200,
            "summary": {"group": rule_group.get("name"), "rules": len(rules)},
        }
    )
    results.append(
        {
            "name": "grafana_investigation_dashboard",
            "status": 200,
            "summary": {
                "title": ((grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("title"),
                "uid": ((grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("uid"),
                "database": (grafana_dashboard.get("health") or {}).get("database"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_monitoring_target",
            "status": 200,
            "summary": {
                "scrapeUrl": monitoring_target.get("scrapeUrl"),
                "lastScrape": monitoring_target.get("lastScrape"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_monitoring_rules",
            "status": 200,
            "summary": {"group": monitoring_rule_group.get("name"), "rules": len(monitoring_rules)},
        }
    )
    results.append(
        {
            "name": "grafana_monitoring_dashboard",
            "status": 200,
            "summary": {
                "title": ((monitoring_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("title"),
                "uid": ((monitoring_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("uid"),
                "database": (monitoring_grafana_dashboard.get("health") or {}).get("database"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_compliance_target",
            "status": 200,
            "summary": {
                "scrapeUrl": compliance_target.get("scrapeUrl"),
                "lastScrape": compliance_target.get("lastScrape"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_compliance_rules",
            "status": 200,
            "summary": {"group": compliance_rule_group.get("name"), "rules": len(compliance_rules)},
        }
    )
    results.append(
        {
            "name": "grafana_compliance_dashboard",
            "status": 200,
            "summary": {
                "title": ((compliance_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("title"),
                "uid": ((compliance_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("uid"),
                "database": (compliance_grafana_dashboard.get("health") or {}).get("database"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_report_target",
            "status": 200,
            "summary": {
                "scrapeUrl": report_target.get("scrapeUrl"),
                "lastScrape": report_target.get("lastScrape"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_report_rules",
            "status": 200,
            "summary": {"group": report_rule_group.get("name"), "rules": len(report_rules)},
        }
    )
    results.append(
        {
            "name": "grafana_report_dashboard",
            "status": 200,
            "summary": {
                "title": ((report_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("title"),
                "uid": ((report_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("uid"),
                "database": (report_grafana_dashboard.get("health") or {}).get("database"),
            },
        }
    )
    results.append(
        {
            "name": "prometheus_platform_rules",
            "status": 200,
            "summary": {"group": platform_rule_group.get("name"), "rules": len(platform_rules)},
        }
    )
    results.append(
        {
            "name": "grafana_platform_alerting_dashboard",
            "status": 200,
            "summary": {
                "title": ((platform_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("title"),
                "uid": ((platform_grafana_dashboard.get("dashboard") or {}).get("dashboard") or {}).get("uid"),
                "database": (platform_grafana_dashboard.get("health") or {}).get("database"),
            },
        }
    )
    results.append(
        {
            "name": "alertmanager_watchdog",
            "status": 200,
            "summary": {
                "receiver": alertmanager_watchdog.get("receivers"),
                "state": ((alertmanager_watchdog.get("status") or {}).get("state")),
            },
        }
    )
    results.append(
        {
            "name": "operational_alert_event_watchdog",
            "status": 200,
            "summary": {
                "service": operational_watchdog.get("service"),
                "status": operational_watchdog.get("status"),
                "delivery_count": operational_watchdog.get("delivery_count"),
            },
        }
    )
    status, payload = call(
        "trigger_operational_alert_triage",
        "POST",
        "/api/v1/monitoring/test/trigger-operational-alert",
        data={
            "alertname": f"SmokeOperationalTriage-{RUN_ID}",
            "service": "platform",
            "severity": "warning",
            "summary": "Incidente sintetico do smoke runtime",
            "description": "Valida o fluxo pending -> acknowledged dos incidentes operacionais globais.",
        },
        headers=api_key_headers,
    )
    expect_status("trigger_operational_alert_triage", status, 200)
    triage_fingerprint = payload.get("fingerprint")
    if not triage_fingerprint:
        raise AssertionError("trigger_operational_alert_triage: fingerprint ausente")
    triage_pending = wait_for_operational_alert_fingerprint(
        triage_fingerprint, admin_api_key_headers, triage_status="pending"
    )
    results.append(
        {
            "name": "operational_alert_triage_pending",
            "status": 200,
            "summary": {
                "id": triage_pending.get("id"),
                "fingerprint": triage_pending.get("fingerprint"),
                "triage_status": triage_pending.get("triage_status"),
            },
        }
    )
    triage_event_id = triage_pending.get("id")
    if not triage_event_id:
        raise AssertionError("operational_alert_triage_pending: id ausente")
    status, payload = call(
        "acknowledge_operational_alert_triage",
        "POST",
        f"/api/v1/monitoring/admin/operational-alerts/{triage_event_id}/acknowledge",
        data={"note": "ack_from_smoke_runtime", "triaged_by": "smoke_runtime"},
        headers=admin_api_key_headers,
    )
    expect_status("acknowledge_operational_alert_triage", status, 200)
    if payload.get("triage_status") != "acknowledged":
        raise AssertionError(
            "acknowledge_operational_alert_triage: triage_status inesperado "
            f"recebido={payload.get('triage_status')}"
        )
    triage_acknowledged = wait_for_operational_alert_fingerprint(
        triage_fingerprint, admin_api_key_headers, triage_status="acknowledged"
    )
    results.append(
        {
            "name": "operational_alert_triage_acknowledged",
            "status": 200,
            "summary": {
                "id": triage_acknowledged.get("id"),
                "triage_status": triage_acknowledged.get("triage_status"),
                "triaged_by": triage_acknowledged.get("triaged_by"),
            },
        }
    )

    status, payload = call("monitoring_catalog", "GET", "/api/v1/monitoring/operations", headers=api_key_headers)
    expect_status("monitoring_catalog", status, 200)
    results.append({"name": "monitoring_catalog", "status": status, "summary": payload.get("total")})

    status, payload = call(
        "monitoring_estimate",
        "POST",
        "/api/v1/monitoring/estimate",
        data={
            "name": "Smoke Watchlist",
            "priority": "high",
            "address": "0x5555555555555555555555555555555555555555",
            "chain": "ethereum",
            "operation": "30d",
        },
        headers=api_key_headers,
    )
    expect_status("monitoring_estimate", status, 200)
    monitoring_quote_id = payload.get("quote_id")
    if not monitoring_quote_id:
        raise AssertionError("monitoring_estimate: quote_id ausente")
    results.append({"name": "monitoring_estimate", "status": status, "summary": monitoring_quote_id})

    status, payload = call(
        "monitoring_start",
        "POST",
        "/api/v1/monitoring/start",
        data={"quote_id": monitoring_quote_id, "confirmed": True},
        headers=api_key_headers,
    )
    expect_status("monitoring_start", status, 200)
    monitoring_case_id = payload.get("case_id")
    monitoring_watchlist_id = payload.get("watchlist_id")
    results.append({"name": "monitoring_start", "status": status, "summary": monitoring_case_id})
    if not monitoring_watchlist_id:
        raise AssertionError("monitoring_start: watchlist_id ausente")

    status, payload = call(
        "monitoring_trigger_alert",
        "POST",
        "/api/v1/monitoring/test/trigger-alert",
        data={
            "watchlist_id": monitoring_watchlist_id,
            "address": "0x5555555555555555555555555555555555555555",
            "chain": "ethereum",
            "severity": "critical",
            "title": "Smoke Monitoring Alert",
            "details": {"source": "smoke_runtime"},
        },
        headers=api_key_headers,
    )
    expect_status("monitoring_trigger_alert", status, 200)
    results.append({"name": "monitoring_trigger_alert", "status": status, "summary": payload.get("alert_id")})

    status, payload = call("compliance_catalog", "GET", "/api/v1/compliance/operations", headers=api_key_headers)
    expect_status("compliance_catalog", status, 200)
    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations:
        raise AssertionError("compliance_catalog: operations ausentes ou invalidas")
    operations_by_canonical = {
        item.get("canonical"): item for item in operations if isinstance(item, dict) and item.get("canonical")
    }
    kyc_wallet_catalog = operations_by_canonical.get("kyc_wallet")
    if not isinstance(kyc_wallet_catalog, dict):
        raise AssertionError("compliance_catalog: operacao kyc_wallet ausente")
    if kyc_wallet_catalog.get("provider") != "trm_labs":
        raise AssertionError(
            f"compliance_catalog: provider inesperado em kyc_wallet recebido={kyc_wallet_catalog.get('provider')}"
        )
    kyc_provider_status = kyc_wallet_catalog.get("provider_status")
    if kyc_provider_status not in {"live", "degraded"}:
        raise AssertionError(
            "compliance_catalog: provider_status invalido em kyc_wallet "
            f"recebido={kyc_provider_status}"
        )
    if kyc_wallet_catalog.get("capability_status") != kyc_provider_status:
        raise AssertionError(
            "compliance_catalog: capability_status de kyc_wallet deve espelhar provider_status "
            f"recebido={kyc_wallet_catalog.get('capability_status')}"
        )
    if kyc_wallet_catalog.get("delivery_mode") != "risk_check_instant":
        raise AssertionError(
            "compliance_catalog: delivery_mode inesperado em kyc_wallet "
            f"recebido={kyc_wallet_catalog.get('delivery_mode')}"
        )
    kyc_capability_details = kyc_wallet_catalog.get("capability_details")
    if not isinstance(kyc_capability_details, dict):
        raise AssertionError("compliance_catalog: capability_details ausente em kyc_wallet")

    dd_catalog = operations_by_canonical.get("due_diligence")
    if not isinstance(dd_catalog, dict):
        raise AssertionError("compliance_catalog: operacao due_diligence ausente")
    if dd_catalog.get("provider") != "manual_review":
        raise AssertionError(
            "compliance_catalog: provider inesperado em due_diligence "
            f"recebido={dd_catalog.get('provider')}"
        )
    if dd_catalog.get("provider_status") != "degraded":
        raise AssertionError(
            "compliance_catalog: provider_status inesperado em due_diligence "
            f"recebido={dd_catalog.get('provider_status')}"
        )
    if dd_catalog.get("degraded_reason") != "manual_review_required":
        raise AssertionError(
            "compliance_catalog: degraded_reason inesperado em due_diligence "
            f"recebido={dd_catalog.get('degraded_reason')}"
        )
    if dd_catalog.get("capability_status") != "degraded":
        raise AssertionError(
            "compliance_catalog: capability_status inesperado em due_diligence "
            f"recebido={dd_catalog.get('capability_status')}"
        )
    if dd_catalog.get("delivery_mode") != "manual_review_pending":
        raise AssertionError(
            "compliance_catalog: delivery_mode inesperado em due_diligence "
            f"recebido={dd_catalog.get('delivery_mode')}"
        )
    dd_capability_details = dd_catalog.get("capability_details")
    if not isinstance(dd_capability_details, dict) or not dd_capability_details.get("requires_human_review"):
        raise AssertionError("compliance_catalog: capability_details inconsistente em due_diligence")
    results.append(
        {
            "name": "compliance_catalog",
            "status": status,
            "summary": {
                "total": payload.get("total"),
                "kyc_wallet": {
                    "provider": kyc_wallet_catalog.get("provider"),
                    "provider_status": kyc_provider_status,
                    "capability_status": kyc_wallet_catalog.get("capability_status"),
                    "delivery_mode": kyc_wallet_catalog.get("delivery_mode"),
                },
                "due_diligence": {
                    "provider": dd_catalog.get("provider"),
                    "provider_status": dd_catalog.get("provider_status"),
                    "capability_status": dd_catalog.get("capability_status"),
                    "delivery_mode": dd_catalog.get("delivery_mode"),
                },
            },
        }
    )

    status, payload = call(
        "compliance_estimate",
        "POST",
        "/api/v1/compliance/estimate",
        data={
            "address": "0x6666666666666666666666666666666666666666",
            "chain": "ethereum",
            "operation": "dd",
        },
        headers=api_key_headers,
    )
    expect_status("compliance_estimate", status, 200)
    compliance_quote_id = payload.get("quote_id")
    if not compliance_quote_id:
        raise AssertionError("compliance_estimate: quote_id ausente")
    results.append({"name": "compliance_estimate", "status": status, "summary": compliance_quote_id})

    status, payload = call(
        "compliance_start",
        "POST",
        "/api/v1/compliance/start",
        data={"quote_id": compliance_quote_id, "confirmed": True},
        headers=api_key_headers,
    )
    expect_status("compliance_start", status, 200)
    compliance_case_id = payload.get("case_id")
    if not compliance_case_id:
        raise AssertionError("compliance_start: case_id ausente")
    results.append({"name": "compliance_start", "status": status, "summary": compliance_case_id})

    status, payload = call(
        "compliance_report",
        "POST",
        f"/api/v1/compliance/cases/{compliance_case_id}/report",
        data={"include_onchain_hash": True},
        headers=api_key_headers,
    )
    expect_status("compliance_report", status, 200)
    compliance_report_id = payload.get("report_id")
    if not compliance_report_id:
        raise AssertionError("compliance_report: report_id ausente")
    compliance_report_type = payload.get("report_type_canonical")
    if not compliance_report_type:
        raise AssertionError("compliance_report: report_type_canonical ausente")
    compliance_created_at = payload.get("created_at")
    if not compliance_created_at:
        raise AssertionError("compliance_report: created_at ausente")
    compliance_file_hash = payload.get("file_hash_sha256")
    if not compliance_file_hash:
        raise AssertionError("compliance_report: file_hash_sha256 ausente")
    results.append({"name": "compliance_report", "status": status, "summary": compliance_report_id})

    status, payload = call(
        "compliance_risk_check",
        "POST",
        "/api/v1/compliance/risk-check",
        data={
            "address": "0x6666666666666666666666666666666666666666",
            "chain": "ethereum",
            "entity_name": "Smoke Counterparty",
            "declared_source": "integration_test",
        },
        headers=api_key_headers,
    )
    expect_status("compliance_risk_check", status, 200)
    provider_status = payload.get("provider_status")
    if payload.get("provider") != "trm_labs":
        raise AssertionError(
            f"compliance_risk_check: provider inesperado recebido={payload.get('provider')}"
        )
    if provider_status not in {"live", "degraded"}:
        raise AssertionError(
            f"compliance_risk_check: provider_status inesperado recebido={provider_status}"
        )
    if provider_status == "live":
        if not isinstance(payload.get("risk_score"), int):
            raise AssertionError("compliance_risk_check: esperado risk_score inteiro quando provider_status=live")
    else:
        if not isinstance(payload.get("degraded_reason"), str) or not payload.get("degraded_reason"):
            raise AssertionError(
                "compliance_risk_check: esperado degraded_reason preenchido quando provider_status=degraded"
            )
        if payload.get("risk_score") is not None:
            raise AssertionError("compliance_risk_check: nao esperado risk_score quando provider_status=degraded")
    results.append(
        {
            "name": "compliance_risk_check",
            "status": status,
            "summary": {
                "provider": payload.get("provider"),
                "provider_status": provider_status,
                "risk_score": payload.get("risk_score"),
                "degraded_reason": payload.get("degraded_reason"),
            },
        }
    )

    starter_token = issue_dev_token("starter")
    enterprise_token = issue_dev_token("enterprise")
    starter_headers = {"Authorization": f"Bearer {starter_token}"}
    enterprise_headers = {"Authorization": f"Bearer {enterprise_token}"}

    status, payload = call(
        "legal_report_generate",
        "POST",
        "/api/v1/reports/generate",
        data={"case_id": "legal-smoke-case", "report_type": "legal_report", "include_onchain_hash": False},
        headers=api_key_headers,
    )
    expect_status("legal_report_generate", status, 200)
    legal_report_id = payload.get("report_id")
    if not legal_report_id:
        raise AssertionError("legal_report_generate: report_id ausente")
    legal_created_at = payload.get("created_at")
    if not legal_created_at:
        raise AssertionError("legal_report_generate: created_at ausente")
    legal_file_hash = payload.get("file_hash_sha256")
    if not legal_file_hash:
        raise AssertionError("legal_report_generate: file_hash_sha256 ausente")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    status, _ = request_opener_json(
        opener,
        "POST",
        "/api/session/start",
        data={"plan": "professional"},
        request_id=f"smoke-{RUN_ID}-legal_session_start",
    )
    expect_status("legal_session_start", status, 200)

    legal_query = urllib.parse.urlencode(
        {"report_id": legal_report_id, "case_id": "legal-smoke-case", "report_type": "legal_report", "created_at": legal_created_at}
    )
    status, _, _ = request_opener_raw(
        opener,
        "GET",
        f"/api/app/reports/download?{legal_query}",
        request_id=f"smoke-{RUN_ID}-legal_download_pre_2fa",
    )
    if status != 403:
        raise AssertionError(f"legal_download_pre_2fa: esperado HTTP 403, recebido {status}")
    results.append({"name": "legal_download_pre_2fa", "status": status, "summary": "2fa_required"})

    status, payload = call("audit_logs_early_fetch", "GET", "/api/v1/audit/logs?limit=50", headers=enterprise_headers)
    expect_status("audit_logs_early_fetch", status, 200)
    early_logs = payload.get("data") or []
    early_matches = []
    for entry in early_logs:
        if entry.get("action") != "report_downloaded":
            continue
        metadata = entry.get("metadata") or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw": metadata}
        if metadata.get("request_id") == f"smoke-{RUN_ID}-legal_download_pre_2fa":
            early_matches.append(entry)
    if early_matches:
        raise AssertionError("legal_download_pre_2fa: nao esperado report_downloaded em audit logs antes do 2FA")

    status, _ = request_opener_json(
        opener,
        "POST",
        "/api/session/verify-2fa",
        data={"code": generate_totp_code()},
        request_id=f"smoke-{RUN_ID}-legal_2fa_verify",
    )
    expect_status("legal_2fa_verify", status, 200)
    status, content, _ = request_opener_raw(
        opener,
        "GET",
        f"/api/app/reports/download?{legal_query}",
        request_id=f"smoke-{RUN_ID}-legal_download_post_2fa",
    )
    expect_status("legal_download_post_2fa", status, 200)
    computed = hashlib.sha256(content).hexdigest()
    if computed != legal_file_hash:
        raise AssertionError(f"legal_download_post_2fa: hash divergente expected={legal_file_hash} computed={computed}")
    results.append({"name": "legal_download_post_2fa", "status": status, "summary": "ok"})

    compliance_query = urllib.parse.urlencode(
        {
            "report_id": compliance_report_id,
            "case_id": compliance_case_id,
            "report_type": compliance_report_type,
            "created_at": compliance_created_at,
        }
    )
    status, compliance_content, _ = request_opener_raw(
        opener,
        "GET",
        f"/api/app/reports/download?{compliance_query}",
        request_id=f"smoke-{RUN_ID}-compliance_report_download",
    )
    expect_status("compliance_report_download", status, 200)
    computed = hashlib.sha256(compliance_content).hexdigest()
    if computed != compliance_file_hash:
        raise AssertionError(
            "compliance_report_download: hash divergente "
            f"expected={compliance_file_hash} computed={computed} report_id={compliance_report_id}"
        )

    status, payload = call(
        "monitoring_planlock_estimate",
        "POST",
        "/api/v1/monitoring/estimate",
        data={
            "name": "Plan Drift Watchlist",
            "priority": "normal",
            "address": "0x7777777777777777777777777777777777777777",
            "chain": "ethereum",
            "operation": "monthly",
        },
        headers=starter_headers,
    )
    expect_status("monitoring_planlock_estimate", status, 200)
    drift_quote_id = payload.get("quote_id")
    if not drift_quote_id:
        raise AssertionError("monitoring_planlock_estimate: quote_id ausente")

    status, payload = call(
        "monitoring_planlock_start",
        "POST",
        "/api/v1/monitoring/start",
        data={"quote_id": drift_quote_id, "confirmed": True},
        headers=enterprise_headers,
    )
    expect_status("monitoring_planlock_start", status, 202)
    if payload.get("status") != "requote_required":
        raise AssertionError("monitoring_planlock_start: status inesperado")
    results.append({"name": "monitoring_planlock_start", "status": status, "summary": payload.get("status")})

    investigation_start_statuses: list[int] = []
    investigation_case_ids: list[str] = []
    for i in range(6):
        status, payload = call(
            f"investigation_estimate_{i}",
            "POST",
            "/api/v1/investigation/estimate",
            data={
                "address": f"0x{i:040x}",
                "chains": ["ethereum"],
                "depth": 3,
                "report_type": "technical_basic",
                "addons": [],
            },
            headers=api_key_headers,
        )
        expect_status(f"investigation_estimate[{i}]", status, 200)
        quote_id = payload.get("quote_id")
        if not quote_id:
            raise AssertionError(f"investigation_estimate[{i}]: quote_id ausente")

        status, payload = call(
            f"investigation_start_{i}",
            "POST",
            "/api/v1/investigation/start",
            data={"quote_id": quote_id, "confirmed": True},
            headers=api_key_headers,
        )
        if status not in (200, 202):
            raise AssertionError(f"investigation_start[{i}]: esperado 200/202, recebido {status}")
        case_id = payload.get("case_id")
        if not case_id:
            raise AssertionError(f"investigation_start[{i}]: case_id ausente")
        investigation_case_ids.append(case_id)
        if status == 202 and payload.get("position_in_queue") is None:
            raise AssertionError(f"investigation_start[{i}]: esperado position_in_queue quando 202")
        if status == 202 and payload.get("concurrency_limited") is not True:
            raise AssertionError(f"investigation_start[{i}]: esperado concurrency_limited=true quando 202")
        if status == 200 and payload.get("concurrency_limited") is True:
            raise AssertionError(f"investigation_start[{i}]: nao esperado concurrency_limited=true quando 200")
        investigation_start_statuses.append(status)

    terminal_statuses: list[str] = []
    for case_id in investigation_case_ids:
        payload = wait_for_case_terminal(case_id, api_key_headers)
        terminal_statuses.append(str(payload.get("status")))
    results.append(
        {
            "name": "investigation_concurrency",
            "status": 200,
            "summary": {"starts": investigation_start_statuses, "terminal_statuses": terminal_statuses},
        }
    )

    result_case_id = investigation_case_ids[0]
    status, payload = call(
        "investigation_result",
        "GET",
        f"/api/v1/investigation/{result_case_id}/result",
        headers=api_key_headers,
    )
    expect_status("investigation_result", status, 200)
    rpc_summary = ((payload.get("kyw_summary") or {}).get("rpc")) or {}
    rpc_provider = rpc_summary.get("provider")
    rpc_provider_status = rpc_summary.get("provider_status")
    rpc_source = rpc_summary.get("rpc_source")
    if rpc_provider != "evm_rpc":
        raise AssertionError(f"investigation_result: provider RPC inesperado recebido={rpc_provider}")
    if rpc_provider_status not in {"live", "degraded"}:
        raise AssertionError(
            f"investigation_result: provider_status RPC inesperado recebido={rpc_provider_status}"
        )
    if not isinstance(rpc_source, str) or not rpc_source:
        raise AssertionError("investigation_result: rpc_source ausente no resultado final")
    if rpc_provider_status == "live":
        if not isinstance(rpc_summary.get("latest_block_number"), int):
            raise AssertionError("investigation_result: latest_block_number esperado quando provider_status=live")
    else:
        if not isinstance(rpc_summary.get("degraded_reason"), str) or not rpc_summary.get("degraded_reason"):
            raise AssertionError("investigation_result: degraded_reason esperado quando provider_status=degraded")
    results.append(
        {
            "name": "investigation_result",
            "status": status,
            "summary": {
                "case_id": payload.get("case_id"),
                "provider": rpc_provider,
                "provider_status": rpc_provider_status,
                "rpc_source": rpc_source,
                "degraded_reason": rpc_summary.get("degraded_reason"),
            },
        }
    )

    status, payload = call("audit_logs_fetch", "GET", "/api/v1/audit/logs?limit=200", headers=enterprise_headers)
    expect_status("audit_logs_fetch", status, 200)
    logs = payload.get("data") or []
    prefix = f"smoke-{RUN_ID}-"
    matching: list[dict] = []
    matching_actions: set[str] = set()
    actions_by_request_id: dict[str, set[str]] = {}
    for entry in logs:
        metadata = entry.get("metadata") or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw": metadata}
        entry["metadata"] = metadata
        request_id = metadata.get("request_id")
        if isinstance(request_id, str) and request_id.startswith(prefix):
            matching.append(entry)
            action = entry.get("action")
            if isinstance(action, str):
                matching_actions.add(action)
                actions_by_request_id.setdefault(request_id, set()).add(action)
    if not matching:
        raise AssertionError("audit_logs_fetch: nenhum audit log encontrado para o run_id atual")
    if "case_started" not in matching_actions:
        raise AssertionError("audit_logs_fetch: esperado action case_started no run_id atual")
    if "report_generated" not in matching_actions:
        raise AssertionError("audit_logs_fetch: esperado action report_generated no run_id atual")
    if "report_downloaded" not in matching_actions:
        raise AssertionError("audit_logs_fetch: esperado action report_downloaded no run_id atual")

    expected_pairs = {
        f"smoke-{RUN_ID}-monitoring_start": "case_started",
        f"smoke-{RUN_ID}-compliance_start": "case_started",
        f"smoke-{RUN_ID}-compliance_report": "report_generated",
        f"smoke-{RUN_ID}-compliance_risk_check": "compliance_risk_checked",
        f"smoke-{RUN_ID}-compliance_report_download": "report_downloaded",
        f"smoke-{RUN_ID}-legal_download_post_2fa": "report_downloaded",
    }
    for req_id, expected_action in expected_pairs.items():
        got = actions_by_request_id.get(req_id, set())
        if expected_action not in got:
            raise AssertionError(
                f"audit_logs_fetch: esperado action {expected_action} para request_id={req_id}, recebido={sorted(got)}"
            )

    expected_resources = {
        f"smoke-{RUN_ID}-monitoring_start": {
            "action": "case_started",
            "resource_type": "case",
            "resource_id": monitoring_case_id,
        },
        f"smoke-{RUN_ID}-compliance_start": {
            "action": "case_started",
            "resource_type": "case",
            "resource_id": compliance_case_id,
        },
        f"smoke-{RUN_ID}-compliance_report": {
            "action": "report_generated",
            "resource_type": "case",
            "resource_id": compliance_case_id,
        },
    }
    for req_id, expected in expected_resources.items():
        entries = [e for e in matching if (e.get("metadata") or {}).get("request_id") == req_id]
        ok = False
        for entry in entries:
            if entry.get("action") != expected["action"]:
                continue
            if entry.get("resource_type") != expected["resource_type"]:
                continue
            if str(entry.get("resource_id")) != str(expected["resource_id"]):
                continue
            ok = True
            break
        if not ok:
            raise AssertionError(
                "audit_logs_fetch: resource mismatch para "
                f"request_id={req_id} esperado={{action:{expected['action']},resource_type:{expected['resource_type']},resource_id:{expected['resource_id']}}}"
            )

    compliance_report_req_id = f"smoke-{RUN_ID}-compliance_report"
    compliance_report_entries = [e for e in matching if (e.get("metadata") or {}).get("request_id") == compliance_report_req_id]
    report_ids: set[str] = set()
    file_hashes: set[str] = set()
    for entry in compliance_report_entries:
        if entry.get("action") != "report_generated":
            continue
        metadata = entry.get("metadata") or {}
        rid = metadata.get("report_id")
        if isinstance(rid, str) and rid:
            report_ids.add(rid)
        fh = metadata.get("file_hash_sha256")
        if isinstance(fh, str) and fh:
            file_hashes.add(fh)
    if compliance_report_id not in report_ids:
        raise AssertionError(
            "audit_logs_fetch: esperado metadata.report_id="
            f"{compliance_report_id} em report_generated para request_id={compliance_report_req_id}, recebido={sorted(report_ids)}"
        )
    if compliance_file_hash not in file_hashes:
        raise AssertionError(
            "audit_logs_fetch: esperado metadata.file_hash_sha256="
            f"{compliance_file_hash} em report_generated para request_id={compliance_report_req_id}, recebido={sorted(file_hashes)}"
        )

    risk_check_req_id = f"smoke-{RUN_ID}-compliance_risk_check"
    risk_check_entries = [e for e in matching if (e.get("metadata") or {}).get("request_id") == risk_check_req_id]
    if not risk_check_entries:
        raise AssertionError(
            "audit_logs_fetch: esperado ao menos um compliance_risk_checked "
            f"para request_id={risk_check_req_id}"
        )
    risk_check_valid = False
    for entry in risk_check_entries:
        if entry.get("action") != "compliance_risk_checked":
            continue
        metadata = entry.get("metadata") or {}
        provider = metadata.get("provider")
        provider_status = metadata.get("provider_status")
        degraded_reason = metadata.get("degraded_reason")
        score = metadata.get("risk_score")
        if provider != "trm_labs":
            continue
        if provider_status == "live" and isinstance(score, int):
            risk_check_valid = True
            break
        if provider_status == "degraded" and isinstance(degraded_reason, str) and degraded_reason:
            if score is None:
                risk_check_valid = True
                break
    if not risk_check_valid:
        raise AssertionError(
            "audit_logs_fetch: esperado metadata consistente de compliance_risk_checked "
            f"com provider_status live|degraded para request_id={risk_check_req_id}"
        )

    download_actions = [e for e in matching if e.get("action") == "report_downloaded"]

    def _expect_download_event(*, request_id: str, report_id: str, expected_file_hash: str, expected_case_id: str) -> None:
        entries = [e for e in download_actions if (e.get("metadata") or {}).get("request_id") == request_id]
        report_ids: set[str] = set()
        file_hashes: set[str] = set()
        case_ids: set[str] = set()
        for entry in entries:
            metadata = entry.get("metadata") or {}
            rid = metadata.get("report_id")
            if isinstance(rid, str) and rid:
                report_ids.add(rid)
            fh = metadata.get("file_hash_sha256")
            if isinstance(fh, str) and fh:
                file_hashes.add(fh)
            cid = metadata.get("case_id")
            if isinstance(cid, str) and cid:
                case_ids.add(cid)
        if report_id not in report_ids:
            raise AssertionError(
                f"audit_logs_fetch: esperado report_downloaded.metadata.report_id={report_id} para request_id={request_id}, recebido={sorted(report_ids)}"
            )
        if expected_file_hash not in file_hashes:
            raise AssertionError(
                f"audit_logs_fetch: esperado report_downloaded.metadata.file_hash_sha256={expected_file_hash} para request_id={request_id}, recebido={sorted(file_hashes)}"
            )
        if expected_case_id not in case_ids:
            raise AssertionError(
                f"audit_logs_fetch: esperado report_downloaded.metadata.case_id={expected_case_id} para request_id={request_id}, recebido={sorted(case_ids)}"
            )

    _expect_download_event(
        request_id=f"smoke-{RUN_ID}-compliance_report_download",
        report_id=compliance_report_id,
        expected_file_hash=compliance_file_hash,
        expected_case_id=compliance_case_id,
    )
    _expect_download_event(
        request_id=f"smoke-{RUN_ID}-legal_download_post_2fa",
        report_id=legal_report_id,
        expected_file_hash=legal_file_hash,
        expected_case_id="legal-smoke-case",
    )

    results.append({"name": "audit_logs_fetch", "status": status, "summary": {"matched": len(matching), "actions": sorted(matching_actions)}})

    print(json.dumps({"base_url": BASE_URL, "results": results}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
