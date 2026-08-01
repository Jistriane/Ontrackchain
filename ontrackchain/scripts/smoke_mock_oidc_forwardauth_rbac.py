#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_OIDC_HOST = "oidc.localhost"
DEFAULT_PROTECTED_PATH = "/api/v1/investigation/admin/operations"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict | None = None,
) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return exc.code, parsed


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _token_fingerprint(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return digest[:12]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke forwardAuth + RBAC via mock-oidc")
    parser.add_argument("--base-url", default=os.getenv("ONTRACKCHAIN_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--oidc-host", default=os.getenv("ONTRACKCHAIN_OIDC_HOST", DEFAULT_OIDC_HOST))
    parser.add_argument("--protected-path", default=os.getenv("ONTRACKCHAIN_PROTECTED_PATH", DEFAULT_PROTECTED_PATH))
    parser.add_argument("--output-file", default=os.getenv("ONTRACKCHAIN_SMOKE_OUTPUT_FILE", ""))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.strip().rstrip("/")
    oidc_host = args.oidc_host.strip()
    protected_path = args.protected_path.strip()

    _assert(bool(base_url), "base_url_ausente")
    _assert(bool(oidc_host), "oidc_host_ausente")
    _assert(bool(protected_path.startswith("/")), "protected_path_invalido")

    token_url = f"{base_url}/mock/token"
    protected_url = f"{base_url}{protected_path}"

    results: dict[str, Any] = {
        "kind": "smoke_mock_oidc_forwardauth_rbac",
        "generated_at": _utc_now(),
        "base_url": base_url,
        "oidc_host": oidc_host,
        "protected_path": protected_path,
        "checks": [],
    }

    def mint(role: str) -> str:
        status, payload = _request(
            method="POST",
            url=token_url,
            headers={"content-type": "application/json", "host": oidc_host},
            payload={"role": role},
        )
        _assert(status == 200, f"mint_token: role={role} esperado=200 recebido={status} payload={payload}")
        token = (payload.get("access_token") or "").strip()
        _assert(bool(token), f"mint_token: role={role} access_token_ausente payload={payload}")
        return token

    def call_protected(token: str) -> tuple[int, dict]:
        return _request(
            method="GET",
            url=protected_url,
            headers={
                "authorization": f"Bearer {token}",
                "x-request-id": f"smoke-{_token_fingerprint(token)}",
            },
            payload=None,
        )

    admin_token = mint("ADMIN")
    admin_status, admin_payload = call_protected(admin_token)
    results["checks"].append(
        {
            "name": "admin_can_access",
            "expected_status": 200,
            "received_status": admin_status,
            "token_fingerprint": _token_fingerprint(admin_token),
        }
    )
    _assert(
        admin_status == 200,
        f"admin_can_access: esperado=200 recebido={admin_status} payload={admin_payload}",
    )

    analyst_token = mint("ANALYST")
    analyst_status, analyst_payload = call_protected(analyst_token)
    results["checks"].append(
        {
            "name": "analyst_is_blocked",
            "expected_status": 403,
            "received_status": analyst_status,
            "token_fingerprint": _token_fingerprint(analyst_token),
            "received_detail": analyst_payload.get("detail"),
        }
    )
    _assert(
        analyst_status == 403,
        f"analyst_is_blocked: esperado=403 recebido={analyst_status} payload={analyst_payload}",
    )
    _assert(
        analyst_payload.get("detail") == "privileged_read_role_required",
        f"analyst_is_blocked: detail inesperado payload={analyst_payload}",
    )

    results["status"] = "ok"

    output_file = (args.output_file or "").strip()
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as file_obj:
            json.dump(results, file_obj, ensure_ascii=True, indent=2)

    sys.stdout.write(json.dumps(results, ensure_ascii=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from exc
