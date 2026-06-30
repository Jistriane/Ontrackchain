#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = os.getenv("ONTRACKCHAIN_BASE_URL", "http://localhost:8080").rstrip("/")
EXPECTED_AUTH_MODE = os.getenv("ONTRACKCHAIN_EXPECTED_AUTH_MODE", "oidc")
EXPECTED_EFFECTIVE_AUTH_MODE = os.getenv("ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE", "oidc")
EXPECTED_APP_ENV = os.getenv("ONTRACKCHAIN_EXPECTED_APP_ENV", "staging")
EXPECTED_DEV_AUTH_ENABLED = os.getenv("ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
EXPECTED_OIDC_PROVIDER = os.getenv("ONTRACKCHAIN_EXPECTED_OIDC_PROVIDER", "keycloak")
EXPECTED_ORG_CLAIM = os.getenv("ONTRACKCHAIN_EXPECTED_OIDC_ORG_CLAIM")
EXPECTED_PLAN_CLAIM = os.getenv("ONTRACKCHAIN_EXPECTED_OIDC_PLAN_CLAIM")
EXPECTED_ROLE_CLAIM = os.getenv("ONTRACKCHAIN_EXPECTED_OIDC_ROLE_CLAIM")


def _request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"content-type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request) as response:
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


def main() -> int:
    config_status, config_payload = _request("GET", "/auth/config")
    _assert(config_status == 200, f"auth_config: esperado HTTP 200, recebido={config_status} payload={config_payload}")
    _assert(
        config_payload.get("auth_mode") == EXPECTED_AUTH_MODE,
        f"auth_config: auth_mode esperado={EXPECTED_AUTH_MODE} recebido={config_payload}",
    )
    _assert(
        config_payload.get("effective_auth_mode") == EXPECTED_EFFECTIVE_AUTH_MODE,
        "auth_config: effective_auth_mode "
        f"esperado={EXPECTED_EFFECTIVE_AUTH_MODE} recebido={config_payload}",
    )
    _assert(
        config_payload.get("app_env") == EXPECTED_APP_ENV,
        f"auth_config: app_env esperado={EXPECTED_APP_ENV} recebido={config_payload}",
    )
    _assert(
        config_payload.get("dev_auth_enabled") is EXPECTED_DEV_AUTH_ENABLED,
        "auth_config: dev_auth_enabled "
        f"esperado={EXPECTED_DEV_AUTH_ENABLED} recebido={config_payload}",
    )

    oidc = config_payload.get("oidc") or {}
    _assert(oidc.get("enabled") is True, f"auth_config: oidc.enabled esperado=true recebido={config_payload}")
    _assert(
        oidc.get("provider") == EXPECTED_OIDC_PROVIDER,
        f"auth_config: oidc.provider esperado={EXPECTED_OIDC_PROVIDER} recebido={config_payload}",
    )
    for field in ("issuer_url", "client_id", "audience", "authorization_url", "token_url"):
        value = oidc.get(field)
        _assert(bool(isinstance(value, str) and value.strip()), f"auth_config: oidc.{field} ausente {config_payload}")

    mfa = config_payload.get("mfa") or {}
    _assert(mfa.get("enabled") is True, f"auth_config: mfa.enabled esperado=true recebido={config_payload}")
    _assert(
        mfa.get("method") == "external_provider",
        f"auth_config: mfa.method esperado=external_provider recebido={config_payload}",
    )
    _assert(
        mfa.get("managed_by") == "oidc_provider",
        f"auth_config: mfa.managed_by esperado=oidc_provider recebido={config_payload}",
    )
    _assert(
        mfa.get("provider_homologated") is False,
        f"auth_config: mfa.provider_homologated esperado=false recebido={config_payload}",
    )

    claims = oidc.get("claims") or {}
    for field_name, expected_value in (
        ("org", EXPECTED_ORG_CLAIM),
        ("plan", EXPECTED_PLAN_CLAIM),
        ("role", EXPECTED_ROLE_CLAIM),
    ):
        value = claims.get(field_name)
        _assert(
            bool(isinstance(value, str) and value.strip()),
            f"auth_config: oidc.claims.{field_name} ausente {config_payload}",
        )
        if expected_value:
            _assert(
                value == expected_value,
                f"auth_config: oidc.claims.{field_name} esperado={expected_value} recebido={config_payload}",
            )

    issue_status, issue_payload = _request(
        "POST",
        "/auth/issue-dev-token",
        {
            "org_id": "00000000-0000-0000-0000-000000000001",
            "user_id": "00000000-0000-0000-0000-000000000002",
            "plan": "enterprise",
            "role": "ADMIN",
            "expires_in_minutes": 5,
        },
    )
    _assert(
        issue_status == 404,
        f"issue_dev_token: esperado HTTP 404 para dev auth desabilitado, recebido={issue_status} payload={issue_payload}",
    )
    _assert(
        issue_payload.get("detail") == "dev_auth_disabled",
        f"issue_dev_token: detail inesperado {issue_payload}",
    )

    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "auth_config": config_payload,
                "issue_dev_token": {
                    "status": issue_status,
                    "payload": issue_payload,
                },
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
