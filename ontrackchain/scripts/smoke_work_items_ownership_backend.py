#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone


import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
ORG_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000002"

HEADERS = {
    "content-type": "application/json",
    "x-org-id": ORG_ID,
    "x-user-id": USER_ID,
    "x-linked-user-id": USER_ID,
    "x-role": "ADMIN",
    "x-request-id": f"smoke-owner-{uuid.uuid4().hex[:12]}",
}


def request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw or "{}")
        except Exception:
            parsed = {"raw": raw}
        return exc.code, parsed


def get_auth_token() -> str | None:
    token_req = urllib.request.Request(
        f"{BASE_URL}/auth/issue-dev-token",
        data=json.dumps({
            "org_id": ORG_ID,
            "user_id": USER_ID,
            "role": "ADMIN",
            "plan": "enterprise",
            "expires_in_minutes": 60,
        }).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(token_req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("token")
    except Exception:
        return None

token = get_auth_token()
if token:
    HEADERS["authorization"] = f"Bearer {token}"


def main() -> int:
    resource_id = str(uuid.uuid4())
    owner_user_id = USER_ID
    due_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    create_status, create_payload = request(
        "POST",
        "/api/v1/operations/work-items",
        {
            "module": "sanctions",
            "resource_type": "sanctions_screening",
            "resource_id": resource_id,
            "owner_user_id": owner_user_id,
            "priority": "high",
            "queue_status": "UNDER_REVIEW",
            "due_at": due_at,
            "title": f"Smoke ownership {resource_id}",
            "note": "create_internal_smoke",
            "metadata": {
                "owner_label": owner_user_id,
                "smoke_scope": "internal_backend",
            },
        },
    )
    if create_status != 201:
        print(json.dumps({"step": "create", "status": create_status, "payload": create_payload}, ensure_ascii=True))
        return 1

    work_item_id = create_payload["id"]

    patch_status, patch_payload = request(
        "PATCH",
        f"/api/v1/operations/work-items/{urllib.parse.quote(work_item_id)}",
        {
            "owner_user_id": owner_user_id,
            "queue_status": "ESCALATED",
            "note": "patch_internal_smoke",
            "metadata": {"smoke_patch": True},
        },
    )
    if patch_status != 200:
        print(json.dumps({"step": "patch", "status": patch_status, "payload": patch_payload}, ensure_ascii=True))
        return 1

    list_status, list_payload = request(
        "GET",
        f"/api/v1/operations/work-items?module=sanctions&owner_user_id={urllib.parse.quote(owner_user_id)}&limit=100",
    )
    if list_status != 200:
        print(json.dumps({"step": "list", "status": list_status, "payload": list_payload}, ensure_ascii=True))
        return 1

    rows = list_payload.get("data", [])
    selected = next((row for row in rows if row.get("id") == work_item_id), None)
    if not selected:
        print(json.dumps({"step": "assert_exists", "work_item_id": work_item_id, "total": len(rows)}, ensure_ascii=True))
        return 1
    if str(selected.get("owner_user_id") or "") != owner_user_id:
        print(
            json.dumps(
                {"step": "assert_owner", "expected": owner_user_id, "selected": selected},
                ensure_ascii=True,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "work_item_id": work_item_id,
                "resource_id": resource_id,
                "owner_user_id": owner_user_id,
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
    raise SystemExit(main())
