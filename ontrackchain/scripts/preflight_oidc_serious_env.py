#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlparse


SERIOUS_ENVS = {"staging", "production"}
ALLOWED_OIDC_PROVIDERS = {"generic", "keycloak", "auth0", "entra"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "auth.localhost", "keycloak"}


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default or "")
    return value.strip()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_url(
    *,
    name: str,
    value: str,
    require_https: bool,
    forbid_localhost: bool,
    errors: list[str],
) -> None:
    if not value:
        errors.append(f"{name}: variavel obrigatoria ausente")
        return

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        errors.append(f"{name}: URL invalida ({value})")
        return

    host = (parsed.hostname or "").strip().lower()
    if require_https and parsed.scheme.lower() != "https":
        errors.append(f"{name}: em ambiente serio deve usar https ({value})")

    if forbid_localhost and host in LOCAL_HOSTS:
        errors.append(f"{name}: endpoint local nao e permitido em ambiente serio ({value})")


def main() -> int:
    app_env = _env("APP_ENV")
    auth_mode = _env("AUTH_MODE")
    dev_auth_enabled = _as_bool(_env("DEV_AUTH_ENABLED", "false"))
    next_public_auth_mode = _env("NEXT_PUBLIC_AUTH_MODE")
    next_public_app_env = _env("NEXT_PUBLIC_APP_ENV")
    next_public_dev_auth_enabled = _as_bool(_env("NEXT_PUBLIC_DEV_AUTH_ENABLED", "false"))
    oidc_provider = _env("OIDC_PROVIDER")
    mfa_external_provider_homologated = _as_bool(_env("MFA_EXTERNAL_PROVIDER_HOMOLOGATED", "false"))

    allow_insecure_public_urls = _as_bool(_env("ONTRACKCHAIN_ALLOW_INSECURE_OIDC_URLS", "false"))
    allow_localhost_urls = _as_bool(_env("ONTRACKCHAIN_ALLOW_LOCALHOST_OIDC_URLS", "false"))

    errors: list[str] = []

    if app_env not in SERIOUS_ENVS:
        errors.append(f"APP_ENV: esperado um ambiente serio em {sorted(SERIOUS_ENVS)}, recebido={app_env or '<vazio>'}")

    if auth_mode != "oidc":
        errors.append(f"AUTH_MODE: esperado=oidc recebido={auth_mode or '<vazio>'}")

    if dev_auth_enabled:
        errors.append("DEV_AUTH_ENABLED: esperado=false em ambiente serio")

    if next_public_auth_mode != "oidc":
        errors.append(f"NEXT_PUBLIC_AUTH_MODE: esperado=oidc recebido={next_public_auth_mode or '<vazio>'}")

    if next_public_app_env and next_public_app_env != app_env:
        errors.append(
            f"NEXT_PUBLIC_APP_ENV: esperado alinhar com APP_ENV ({app_env}), recebido={next_public_app_env}"
        )

    if next_public_dev_auth_enabled:
        errors.append("NEXT_PUBLIC_DEV_AUTH_ENABLED: esperado=false em ambiente serio")

    if oidc_provider not in ALLOWED_OIDC_PROVIDERS:
        errors.append(
            f"OIDC_PROVIDER: esperado um preset valido em {sorted(ALLOWED_OIDC_PROVIDERS)}, recebido={oidc_provider or '<vazio>'}"
        )
    elif mfa_external_provider_homologated and oidc_provider == "generic":
        errors.append("MFA_EXTERNAL_PROVIDER_HOMOLOGATED: nao e permitido com OIDC_PROVIDER=generic em ambiente serio")

    required_strings = {
        "OIDC_AUDIENCE": _env("OIDC_AUDIENCE"),
        "OIDC_CLIENT_ID": _env("OIDC_CLIENT_ID"),
        "OIDC_ORG_CLAIM": _env("OIDC_ORG_CLAIM"),
        "OIDC_PLAN_CLAIM": _env("OIDC_PLAN_CLAIM"),
        "OIDC_ROLE_CLAIM": _env("OIDC_ROLE_CLAIM"),
    }
    for name, value in required_strings.items():
        if not value:
            errors.append(f"{name}: variavel obrigatoria ausente")

    _validate_url(
        name="OIDC_ISSUER_URL",
        value=_env("OIDC_ISSUER_URL"),
        require_https=not allow_insecure_public_urls,
        forbid_localhost=not allow_localhost_urls,
        errors=errors,
    )
    _validate_url(
        name="OIDC_AUTHORIZATION_URL",
        value=_env("OIDC_AUTHORIZATION_URL"),
        require_https=not allow_insecure_public_urls,
        forbid_localhost=not allow_localhost_urls,
        errors=errors,
    )
    _validate_url(
        name="OIDC_JWKS_URL",
        value=_env("OIDC_JWKS_URL"),
        require_https=False,
        forbid_localhost=not allow_localhost_urls,
        errors=errors,
    )

    disallowed_defaults = {
        "JWT_HS256_SECRET": {"", "change-me"},
        "MFA_TOTP_SECRET": {"", "JBSWY3DPEHPK3PXP"},
        "KEYCLOAK_ADMIN_PASSWORD": {"", "admin"},
        "KEYCLOAK_B2B_CLIENT_SECRET": {"", "change-me-b2b-secret"},
    }
    for name, forbidden_values in disallowed_defaults.items():
        value = _env(name)
        if value in forbidden_values:
            errors.append(f"{name}: valor padrao/local detectado; configurar secret nao-dev")

    summary = {
        "app_env": app_env,
        "auth_mode": auth_mode,
        "dev_auth_enabled": dev_auth_enabled,
        "next_public_auth_mode": next_public_auth_mode,
        "next_public_app_env": next_public_app_env,
        "next_public_dev_auth_enabled": next_public_dev_auth_enabled,
        "oidc_provider": oidc_provider,
        "mfa_external_provider_homologated": mfa_external_provider_homologated,
        "allow_insecure_public_urls": allow_insecure_public_urls,
        "allow_localhost_urls": allow_localhost_urls,
        "status": "ok" if not errors else "failed",
        "errors": errors,
    }

    output = sys.stdout if not errors else sys.stderr
    output.write(json.dumps(summary, ensure_ascii=True, indent=2) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
