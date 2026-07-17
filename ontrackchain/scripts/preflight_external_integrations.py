#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


SERIOUS_ENVS = {"staging", "production"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "keycloak"}
PLACEHOLDER_VALUES = {"", "change-me", "change-me-b2b-secret"}
EXPECTED_COMPLIANCE_MODES = {"disabled", "live"}
EXPECTED_RPC_MODES = {"disabled", "live", "fallback_only"}
EXPECTED_FRONTEND_DEPLOYMENT_MODELS = {"render-full-stack-staging", "render-frontend-standalone-showcase"}


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


def _resolve_frontend_healthz_base_url() -> str:
    return (
        _env("ONTRACKCHAIN_FRONTEND_HEALTHCHECK_BASE_URL")
        or _env("ONTRACKCHAIN_BASE_URL")
        or _env("NEXT_PUBLIC_API_BASE_URL")
    )


def _validate_frontend_runtime(
    *,
    app_env: str,
    errors: list[str],
) -> dict:
    expected_deployment_model = _env("ONTRACKCHAIN_EXPECT_FRONTEND_DEPLOYMENT_MODEL", "render-full-stack-staging")
    allow_showcase_fallback = _as_bool(_env("ONTRACKCHAIN_ALLOW_FRONTEND_SHOWCASE_FALLBACK", "false"))
    base_url = _resolve_frontend_healthz_base_url()
    summary = {
        "expected_deployment_model": expected_deployment_model,
        "allow_showcase_fallback": allow_showcase_fallback,
        "base_url": base_url,
        "healthz_url": "",
        "reachable": False,
        "http_status": None,
        "deployment_model": "",
        "hosted_showcase_fallback": None,
        "standalone_showcase_mode": None,
        "missing_env_keys": [],
    }

    if app_env not in SERIOUS_ENVS:
        return summary

    if expected_deployment_model not in EXPECTED_FRONTEND_DEPLOYMENT_MODELS:
        errors.append(
            "ONTRACKCHAIN_EXPECT_FRONTEND_DEPLOYMENT_MODEL: "
            f"esperado um valor em {sorted(EXPECTED_FRONTEND_DEPLOYMENT_MODELS)}, "
            f"recebido={expected_deployment_model or '<vazio>'}"
        )
        return summary

    _validate_url(
        name="ONTRACKCHAIN_FRONTEND_HEALTHCHECK_BASE_URL",
        value=base_url,
        require_https=True,
        forbid_localhost=True,
        errors=errors,
    )
    if not base_url:
        return summary

    healthz_url = f"{base_url.rstrip('/')}/api/healthz"
    summary["healthz_url"] = healthz_url

    try:
        with urllib.request.urlopen(healthz_url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            summary["reachable"] = True
            summary["http_status"] = response.getcode()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        errors.append(f"frontend_healthz: HTTP {exc.code} em {healthz_url}")
        summary["http_status"] = exc.code
        if body:
            summary["response_body"] = body[:500]
        return summary
    except urllib.error.URLError as exc:
        errors.append(f"frontend_healthz: endpoint inacessivel em {healthz_url} ({exc.reason})")
        return summary
    except (OSError, TimeoutError) as exc:
        errors.append(f"frontend_healthz: falha de rede em {healthz_url} ({exc})")
        return summary
    except json.JSONDecodeError as exc:
        errors.append(f"frontend_healthz: resposta invalida de {healthz_url} ({exc})")
        return summary

    deployment_model = str(payload.get("deploymentModel") or "").strip()
    hosted_showcase_fallback = payload.get("hostedShowcaseFallback")
    standalone_showcase_mode = payload.get("standaloneShowcaseMode")
    missing_env_keys = payload.get("missingEnvKeys") or []

    summary["deployment_model"] = deployment_model
    summary["hosted_showcase_fallback"] = hosted_showcase_fallback
    summary["standalone_showcase_mode"] = standalone_showcase_mode
    summary["missing_env_keys"] = missing_env_keys if isinstance(missing_env_keys, list) else []

    if deployment_model != expected_deployment_model:
        errors.append(
            "frontend_healthz: "
            f"deploymentModel esperado={expected_deployment_model} recebido={deployment_model or '<vazio>'}"
        )

    if hosted_showcase_fallback and not allow_showcase_fallback:
        errors.append("frontend_healthz: hostedShowcaseFallback=true nao e permitido para janela seria")

    return summary


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
    frontend_summary = _validate_frontend_runtime(app_env=app_env, errors=errors)

    summary = {
        "app_env": app_env,
        "allow_insecure_urls": allow_insecure_urls,
        "allow_localhost_urls": allow_localhost_urls,
        "compliance": compliance_summary,
        "rpc": rpc_summary,
        "frontend": frontend_summary,
        "status": "ok" if not errors else "failed",
        "errors": errors,
    }

    output = sys.stdout if not errors else sys.stderr
    output.write(json.dumps(summary, ensure_ascii=True, indent=2) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
