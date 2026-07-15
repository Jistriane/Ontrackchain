#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path

BASE_REALM_PATH = Path("/opt/keycloak/data/import/realm-ontrackchain.base.json")
OUTPUT_REALM_PATH = Path("/opt/keycloak/data/import/realm-ontrackchain.json")


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"missing_required_env:{name}")
    return value


def _user_password_overrides() -> dict[str, str]:
    env_by_username = {
        "system@ontrackchain.com": "KEYCLOAK_SYSTEM_USER_PASSWORD",
        "kmd@ontrackchain.com": "KEYCLOAK_KMD_TESTER_PASSWORD",
        "jibso@ontrackchain.com": "KEYCLOAK_JIBSO_ADMIN_PASSWORD",
        "auditor@ontrackchain.com": "KEYCLOAK_AUDITOR_PASSWORD",
        "analyst@ontrackchain.com": "KEYCLOAK_ANALYST_PASSWORD",
        "viewer@ontrackchain.com": "KEYCLOAK_VIEWER_PASSWORD",
        "sem-org@ontrackchain.com": "KEYCLOAK_SEM_ORG_PASSWORD",
    }
    overrides: dict[str, str] = {}
    for username, env_name in env_by_username.items():
        value = os.getenv(env_name, "").strip()
        if value:
            overrides[username] = value
    return overrides


def main() -> None:
    public_url = _required_env("KEYCLOAK_PUBLIC_URL").rstrip("/")
    gateway_url = _required_env("ONTRACKCHAIN_PUBLIC_BASE_URL").rstrip("/")
    b2b_secret = _required_env("KEYCLOAK_B2B_CLIENT_SECRET")
    password_overrides = _user_password_overrides()

    realm = json.loads(BASE_REALM_PATH.read_text(encoding="utf-8"))

    for client in realm.get("clients", []):
        if client.get("clientId") == "ontrackchain-web":
            client["redirectUris"] = [f"{gateway_url}/*", f"{gateway_url}/oidc/callback"]
            client["webOrigins"] = [gateway_url]
        if client.get("clientId") == "ontrackchain-b2b":
            client["secret"] = b2b_secret

    for user in realm.get("users", []):
        username = user.get("username")
        new_password = password_overrides.get(username)
        if not new_password:
            continue
        credentials = user.get("credentials") or []
        if not credentials:
            user["credentials"] = [{"type": "password", "value": new_password, "temporary": False}]
            continue
        credentials[0]["value"] = new_password
        credentials[0]["temporary"] = False

    realm["sslRequired"] = "external"
    realm["attributes"] = realm.get("attributes", {})
    realm["attributes"]["frontendUrl"] = public_url

    OUTPUT_REALM_PATH.write_text(json.dumps(realm, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
