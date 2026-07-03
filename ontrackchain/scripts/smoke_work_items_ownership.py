#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone


BASE_URL = os.getenv("ONTRACKCHAIN_BASE_URL", "http://localhost:8080").rstrip("/")
API_PREFIX = os.getenv("ONTRACKCHAIN_SMOKE_API_PREFIX", "/api/app").rstrip("/")
ORG_ID = os.getenv("ONTRACKCHAIN_SMOKE_ORG_ID", "00000000-0000-0000-0000-000000000001")
USER_ID = os.getenv("ONTRACKCHAIN_SMOKE_USER_ID", "00000000-0000-0000-0000-000000000002")
LINKED_USER_ID = os.getenv("ONTRACKCHAIN_SMOKE_LINKED_USER_ID", USER_ID)
ROLE = os.getenv("ONTRACKCHAIN_SMOKE_ROLE", "ADMIN")
API_KEY = os.getenv("ONTRACKCHAIN_API_KEY")
AUTH_TOKEN = os.getenv("ONTRACKCHAIN_SMOKE_TOKEN") or os.getenv("OTC_TOKEN")


def _issue_dev_token() -> str:
    status, payload = _request(
        "POST",
        "/auth/issue-dev-token",
        {
            "org_id": ORG_ID,
            "user_id": USER_ID,
            "role": ROLE,
            "plan": "enterprise",
            "expires_in_minutes": 15,
        },
        include_cookie=False,
    )
    if status != 200:
        raise AssertionError(
            "issue_dev_token: falhou para obter token de sessao dev; "
            f"status={status}, payload={payload}. "
            "Defina ONTRACKCHAIN_SMOKE_TOKEN para ambiente OIDC/serio."
        )

    token = payload.get("token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise AssertionError(f"issue_dev_token: token ausente payload={payload}")
    return token


def _request(method: str, path: str, payload: dict | None = None, *, include_cookie: bool = True) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-request-id": f"smoke-owner-{uuid.uuid4().hex[:12]}",
        "x-org-id": ORG_ID,
        "x-user-id": USER_ID,
        "x-linked-user-id": LINKED_USER_ID,
        "x-role": ROLE,
    }
    if API_KEY:
        headers["x-api-key"] = API_KEY
    if include_cookie and AUTH_TOKEN:
        headers["Cookie"] = f"otc_token={AUTH_TOKEN}"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return exc.code, parsed
    except urllib.error.URLError as exc:
        return 599, {"error": str(exc)}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    global AUTH_TOKEN
    if API_PREFIX.startswith("/api/app") and not AUTH_TOKEN:
        AUTH_TOKEN = _issue_dev_token()

    resource_id = str(uuid.uuid4())
    owner_user_id = LINKED_USER_ID
    due_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    create_status, create_payload = _request(
        "POST",
        f"{API_PREFIX}/operations/work-items",
        {
            "module": "sanctions",
            "resource_type": "sanctions_screening",
            "resource_id": resource_id,
            "owner_user_id": owner_user_id,
            "priority": "high",
            "queue_status": "UNDER_REVIEW",
            "due_at": due_at,
            "title": f"Smoke ownership {resource_id}",
            "note": "create_from_smoke_work_items_ownership",
            "metadata": {
                "owner_label": owner_user_id,
                "smoke_scope": "work_items_ownership",
                "smoke_resource": resource_id,
            },
        },
    )
    _assert(create_status == 201, f"create_work_item: esperado 201, recebido={create_status}, payload={create_payload}")

    work_item_id = str(create_payload.get("id") or "")
    _assert(bool(work_item_id), f"create_work_item: id ausente payload={create_payload}")
    _assert(
        str(create_payload.get("owner_user_id") or "") == owner_user_id,
        f"create_work_item: owner_user_id inesperado payload={create_payload}",
    )

    patch_status, patch_payload = _request(
        "PATCH",
        f"{API_PREFIX}/operations/work-items/{urllib.parse.quote(work_item_id)}",
        {
            "owner_user_id": owner_user_id,
            "queue_status": "ESCALATED",
            "note": "patch_from_smoke_work_items_ownership",
            "metadata": {
                "smoke_patch": True,
                "smoke_scope": "work_items_ownership",
            },
        },
    )
    _assert(patch_status == 200, f"patch_work_item: esperado 200, recebido={patch_status}, payload={patch_payload}")
    _assert(
        str(patch_payload.get("owner_user_id") or "") == owner_user_id,
        f"patch_work_item: owner_user_id inesperado payload={patch_payload}",
    )
    _assert(
        patch_payload.get("queue_status") == "ESCALATED",
        f"patch_work_item: queue_status inesperado payload={patch_payload}",
    )

    list_status, list_payload = _request(
        "GET",
        f"{API_PREFIX}/operations/work-items?module=sanctions&owner_user_id={urllib.parse.quote(owner_user_id)}&limit=100",
    )
    _assert(list_status == 200, f"list_work_items: esperado 200, recebido={list_status}, payload={list_payload}")
    rows = list_payload.get("data") if isinstance(list_payload, dict) else None
    _assert(isinstance(rows, list), f"list_work_items: data invalido payload={list_payload}")
    by_id = {str(row.get("id")): row for row in rows if isinstance(row, dict)}
    _assert(work_item_id in by_id, f"list_work_items: item nao encontrado id={work_item_id}")
    selected = by_id[work_item_id]
    _assert(
        str(selected.get("owner_user_id") or "") == owner_user_id,
        f"list_work_items: owner_user_id inesperado row={selected}",
    )

    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "work_item_id": work_item_id,
                "resource_id": resource_id,
                "owner_user_id": owner_user_id,
                "api_prefix": API_PREFIX,
                "create_status": create_status,
                "patch_status": patch_status,
                "list_status": list_status,
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from exc
