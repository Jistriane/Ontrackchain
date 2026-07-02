#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlparse


SERIOUS_ENVS = {"staging", "production"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "keycloak"}
PLACEHOLDER_VALUES = {"", "change-me", "change-me-b2b-secret"}
EXPECTED_COMPLIANCE_MODES = {"disabled", "live"}
EXPECTED_RPC_MODES = {"disabled", "live", "fallback_only"}


def _env(name: str, default: str | None = None) -> str:
    return os.getenv(name, default or "").strip()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_positive_int(name: str, value: str, *, min_value: int, errors: list[str]) -> int | None:
    if not value:
        errors.append(f"{name}: variavel obrigatoria ausente")
        return None
    try:
        parsed = int(value)
    except ValueError:
        errors.append(f"{name}: esperado inteiro, recebido={value}")
        return None
    if parsed < min_value:
        errors.append(f"{name}: esperado valor >= {min_value}, recebido={parsed}")
        return None
    return parsed


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


def _validate_compliance(
    *,
    expect_mode: str,
    allow_insecure_urls: bool,
    allow_localhost_urls: bool,
    errors: list[str],
) -> dict:
    enabled = _as_bool(_env("COMPLIANCE_TRM_ENABLED", "false"))
    provider = _env("COMPLIANCE_RISK_PROVIDER", "trm_labs")
    screening_url = _env("COMPLIANCE_TRM_SCREENING_URL")
    api_key = _env("COMPLIANCE_TRM_API_KEY")
    ofac_source_url = _env("COMPLIANCE_OFAC_SDN_SOURCE_URL")
    eu_sanctions_source_url = _env("COMPLIANCE_EU_SANCTIONS_SOURCE_URL")
    timeout_ms = _parse_positive_int(
        "COMPLIANCE_TRM_TIMEOUT_MS",
        _env("COMPLIANCE_TRM_TIMEOUT_MS"),
        min_value=1,
        errors=errors,
    )
    max_retries = _parse_positive_int(
        "COMPLIANCE_TRM_MAX_RETRIES",
        _env("COMPLIANCE_TRM_MAX_RETRIES"),
        min_value=0,
        errors=errors,
    )

    if expect_mode == "disabled":
        if enabled:
            errors.append("COMPLIANCE_TRM_ENABLED: esperado=false quando ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=disabled")
    elif expect_mode == "live":
        if provider != "trm_labs":
            errors.append(f"COMPLIANCE_RISK_PROVIDER: esperado=trm_labs recebido={provider or '<vazio>'}")
        if not enabled:
            errors.append("COMPLIANCE_TRM_ENABLED: esperado=true para homologacao live")
        _validate_url(
            name="COMPLIANCE_TRM_SCREENING_URL",
            value=screening_url,
            require_https=not allow_insecure_urls,
            forbid_localhost=not allow_localhost_urls,
            errors=errors,
        )
        if api_key in PLACEHOLDER_VALUES:
            errors.append("COMPLIANCE_TRM_API_KEY: credencial ausente ou placeholder detectado")

    if ofac_source_url:
        _validate_url(
            name="COMPLIANCE_OFAC_SDN_SOURCE_URL",
            value=ofac_source_url,
            require_https=not allow_insecure_urls,
            forbid_localhost=not allow_localhost_urls,
            errors=errors,
        )

    if eu_sanctions_source_url:
        _validate_url(
            name="COMPLIANCE_EU_SANCTIONS_SOURCE_URL",
            value=eu_sanctions_source_url,
            require_https=not allow_insecure_urls,
            forbid_localhost=not allow_localhost_urls,
            errors=errors,
        )

    return {
        "expect_mode": expect_mode,
        "provider": provider,
        "enabled": enabled,
        "screening_url_present": bool(screening_url),
        "api_key_present": bool(api_key),
        "timeout_ms": timeout_ms,
        "max_retries": max_retries,
        "sanctions_source_overrides": {
            "ofac_present": bool(ofac_source_url),
            "eu_present": bool(eu_sanctions_source_url),
            "eu_tokenized": "token=" in eu_sanctions_source_url.lower(),
        },
    }


def _validate_rpc(
    *,
    expect_mode: str,
    allow_insecure_urls: bool,
    allow_localhost_urls: bool,
    errors: list[str],
) -> dict:
    enabled = _as_bool(_env("INVESTIGATION_RPC_ENABLED", "false"))
    provider = _env("INVESTIGATION_RPC_PROVIDER", "evm_rpc")
    primary_url = _env("INVESTIGATION_RPC_PRIMARY_URL")
    fallback_url = _env("INVESTIGATION_RPC_FALLBACK_URL")
    timeout_ms = _parse_positive_int(
        "INVESTIGATION_RPC_TIMEOUT_MS",
        _env("INVESTIGATION_RPC_TIMEOUT_MS"),
        min_value=1,
        errors=errors,
    )
    max_retries = _parse_positive_int(
        "INVESTIGATION_RPC_MAX_RETRIES",
        _env("INVESTIGATION_RPC_MAX_RETRIES"),
        min_value=0,
        errors=errors,
    )

    if provider != "evm_rpc":
        errors.append(f"INVESTIGATION_RPC_PROVIDER: esperado=evm_rpc recebido={provider or '<vazio>'}")

    if expect_mode == "disabled":
        if enabled:
            errors.append("INVESTIGATION_RPC_ENABLED: esperado=false quando ONTRACKCHAIN_EXPECT_RPC_MODE=disabled")
    elif expect_mode == "live":
        if not enabled:
            errors.append("INVESTIGATION_RPC_ENABLED: esperado=true para homologacao RPC")
        _validate_url(
            name="INVESTIGATION_RPC_PRIMARY_URL",
            value=primary_url,
            require_https=not allow_insecure_urls,
            forbid_localhost=not allow_localhost_urls,
            errors=errors,
        )
        if fallback_url:
            _validate_url(
                name="INVESTIGATION_RPC_FALLBACK_URL",
                value=fallback_url,
                require_https=not allow_insecure_urls,
                forbid_localhost=not allow_localhost_urls,
                errors=errors,
            )
        if primary_url and fallback_url and primary_url == fallback_url:
            errors.append("INVESTIGATION_RPC_FALLBACK_URL: deve diferir da URL primaria quando configurada")
    elif expect_mode == "fallback_only":
        if not enabled:
            errors.append("INVESTIGATION_RPC_ENABLED: esperado=true para fallback_only")
        if primary_url:
            errors.append("INVESTIGATION_RPC_PRIMARY_URL: esperado vazio quando ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only")
        _validate_url(
            name="INVESTIGATION_RPC_FALLBACK_URL",
            value=fallback_url,
            require_https=not allow_insecure_urls,
            forbid_localhost=not allow_localhost_urls,
            errors=errors,
        )

    return {
        "expect_mode": expect_mode,
        "provider": provider,
        "enabled": enabled,
        "primary_url_present": bool(primary_url),
        "fallback_url_present": bool(fallback_url),
        "timeout_ms": timeout_ms,
        "max_retries": max_retries,
    }


def main() -> int:
    app_env = _env("APP_ENV")
    expect_compliance_mode = _env("ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE", "disabled")
    expect_rpc_mode = _env("ONTRACKCHAIN_EXPECT_RPC_MODE", "disabled")
    allow_insecure_urls = _as_bool(_env("ONTRACKCHAIN_ALLOW_INSECURE_PROVIDER_URLS", "false"))
    allow_localhost_urls = _as_bool(_env("ONTRACKCHAIN_ALLOW_LOCAL_PROVIDER_URLS", "false"))

    errors: list[str] = []
    if app_env not in SERIOUS_ENVS:
        errors.append(f"APP_ENV: esperado um ambiente serio em {sorted(SERIOUS_ENVS)}, recebido={app_env or '<vazio>'}")
    if expect_compliance_mode not in EXPECTED_COMPLIANCE_MODES:
        errors.append(
            f"ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE: esperado um valor em {sorted(EXPECTED_COMPLIANCE_MODES)}, recebido={expect_compliance_mode or '<vazio>'}"
        )
    if expect_rpc_mode not in EXPECTED_RPC_MODES:
        errors.append(
            f"ONTRACKCHAIN_EXPECT_RPC_MODE: esperado um valor em {sorted(EXPECTED_RPC_MODES)}, recebido={expect_rpc_mode or '<vazio>'}"
        )

    compliance_summary = _validate_compliance(
        expect_mode=expect_compliance_mode,
        allow_insecure_urls=allow_insecure_urls,
        allow_localhost_urls=allow_localhost_urls,
        errors=errors,
    )
    rpc_summary = _validate_rpc(
        expect_mode=expect_rpc_mode,
        allow_insecure_urls=allow_insecure_urls,
        allow_localhost_urls=allow_localhost_urls,
        errors=errors,
    )

    summary = {
        "app_env": app_env,
        "allow_insecure_urls": allow_insecure_urls,
        "allow_localhost_urls": allow_localhost_urls,
        "compliance": compliance_summary,
        "rpc": rpc_summary,
        "status": "ok" if not errors else "failed",
        "errors": errors,
    }

    output = sys.stdout if not errors else sys.stderr
    output.write(json.dumps(summary, ensure_ascii=True, indent=2) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
