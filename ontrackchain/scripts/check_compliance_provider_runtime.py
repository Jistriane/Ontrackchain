#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_dotenv_values(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


DOTENV_VALUES = load_dotenv_values(DOTENV_PATH)


def env_value(name: str, default: str = "") -> str:
    return (os.getenv(name) or DOTENV_VALUES.get(name) or default).strip()


def build_internal_base_url() -> str:
    explicit = env_value("ONTRACKCHAIN_COMPLIANCE_INTERNAL_BASE_URL")
    if explicit:
        return explicit.rstrip("/")

    port = env_value("COMPLIANCE_API_PORT", "8002")
    return f"http://localhost:{port}".rstrip("/")


def build_public_base_url(internal_base_url: str) -> str:
    return (
        env_value("ONTRACKCHAIN_COMPLIANCE_PUBLIC_BASE_URL")
        or env_value("ONTRACKCHAIN_BASE_URL")
        or env_value("NEXT_PUBLIC_API_BASE_URL")
        or internal_base_url
    ).rstrip("/")


def request_json(
    *,
    base_url: str,
    path: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    request_headers = dict(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        request_headers.setdefault("content-type", "application/json")

    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            if not isinstance(payload, dict):
                payload = {"raw_response": payload}
            return response.status, payload, dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        if not isinstance(payload, dict):
            payload = {"raw_response": payload}
        return exc.code, payload, dict(exc.headers)
    except urllib.error.URLError as exc:
        return 599, {"error": str(exc)}, {}


def build_headers(
    *,
    bearer_token: str,
    api_key: str,
    plan: str,
    request_id: str,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "accept": "application/json",
        "X-Plan": plan,
        "X-Request-Id": request_id,
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    elif api_key:
        headers["X-API-Key"] = api_key
    return headers


def build_payload(
    *,
    internal_base_url: str,
    public_base_url: str,
    expected_provider: str,
    plan: str,
    sample_address: str,
    sample_chain: str,
    bearer_token: str,
    api_key: str,
    timeout_seconds: float,
    request_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    headers = build_headers(
        bearer_token=bearer_token,
        api_key=api_key,
        plan=plan,
        request_id=request_id,
    )

    internal_status, internal_payload, _ = request_json(
        base_url=internal_base_url,
        path="/internal/provider-readiness",
        headers={"accept": "application/json", "X-Request-Id": request_id},
        timeout_seconds=timeout_seconds,
    )
    internal_ok = True
    if internal_status != 200:
        internal_ok = False
        errors.append(
            f"internal/provider-readiness: esperado_http=200 recebido={internal_status}"
        )
    elif internal_payload.get("provider") != expected_provider:
        internal_ok = False
        errors.append(
            f"internal/provider-readiness: provider esperado={expected_provider} recebido={internal_payload.get('provider')}"
        )
    elif not internal_payload.get("ready"):
        internal_ok = False
        errors.append(
            "internal/provider-readiness: ready esperado=true "
            f"recebido={internal_payload.get('ready')} degraded_reason={internal_payload.get('degraded_reason')}"
        )
    elif internal_payload.get("details", {}).get("operating_mode") != "live":
        internal_ok = False
        errors.append(
            "internal/provider-readiness: operating_mode esperado=live "
            f"recebido={internal_payload.get('details', {}).get('operating_mode')}"
        )

    checks.append(
        {
            "name": "internal_provider_readiness",
            "status": "ok" if internal_ok else "failed",
            "http_status": internal_status,
            "details": internal_payload,
        }
    )

    catalog_status, catalog_payload, _ = request_json(
        base_url=public_base_url,
        path="/api/v1/compliance/operations/kyc_wallet",
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    catalog_ok = True
    if catalog_status != 200:
        catalog_ok = False
        errors.append(
            f"operations/kyc_wallet: esperado_http=200 recebido={catalog_status}"
        )
    elif catalog_payload.get("provider") != expected_provider:
        catalog_ok = False
        errors.append(
            f"operations/kyc_wallet: provider esperado={expected_provider} recebido={catalog_payload.get('provider')}"
        )
    elif catalog_payload.get("provider_status") != "live":
        catalog_ok = False
        errors.append(
            "operations/kyc_wallet: provider_status esperado=live "
            f"recebido={catalog_payload.get('provider_status')}"
        )
    elif catalog_payload.get("capability_status") != "live":
        catalog_ok = False
        errors.append(
            "operations/kyc_wallet: capability_status esperado=live "
            f"recebido={catalog_payload.get('capability_status')}"
        )

    checks.append(
        {
            "name": "catalog_kyc_wallet",
            "status": "ok" if catalog_ok else "failed",
            "http_status": catalog_status,
            "details": catalog_payload,
        }
    )

    kyc_status, kyc_payload, _ = request_json(
        base_url=public_base_url,
        path="/api/v1/compliance/kyc-wallet",
        method="POST",
        headers=headers,
        data={
            "address": sample_address,
            "chain": sample_chain,
        },
        timeout_seconds=timeout_seconds,
    )
    kyc_ok = True
    if kyc_status != 200:
        kyc_ok = False
        errors.append(
            f"kyc-wallet: esperado_http=200 recebido={kyc_status}"
        )
    elif kyc_payload.get("provider") != expected_provider:
        kyc_ok = False
        errors.append(
            f"kyc-wallet: provider esperado={expected_provider} recebido={kyc_payload.get('provider')}"
        )
    elif kyc_payload.get("provider_status") != "live":
        kyc_ok = False
        errors.append(
            "kyc-wallet: provider_status esperado=live "
            f"recebido={kyc_payload.get('provider_status')} degraded_reason={kyc_payload.get('degraded_reason')}"
        )
    elif kyc_payload.get("capability_status") != "live":
        kyc_ok = False
        errors.append(
            "kyc-wallet: capability_status esperado=live "
            f"recebido={kyc_payload.get('capability_status')}"
        )

    checks.append(
        {
            "name": "runtime_kyc_wallet",
            "status": "ok" if kyc_ok else "failed",
            "http_status": kyc_status,
            "details": kyc_payload,
        }
    )

    correlation = {
        "internal_provider": internal_payload.get("provider"),
        "internal_ready": internal_payload.get("ready"),
        "internal_operating_mode": (internal_payload.get("details") or {}).get("operating_mode"),
        "catalog_provider": catalog_payload.get("provider"),
        "catalog_provider_status": catalog_payload.get("provider_status"),
        "catalog_capability_status": catalog_payload.get("capability_status"),
        "catalog_delivery_mode": catalog_payload.get("delivery_mode"),
        "runtime_provider": kyc_payload.get("provider"),
        "runtime_provider_status": kyc_payload.get("provider_status"),
        "runtime_capability_status": kyc_payload.get("capability_status"),
        "runtime_delivery_mode": kyc_payload.get("delivery_mode"),
        "provider_converges_live": (
            internal_payload.get("provider") == expected_provider
            and catalog_payload.get("provider") == expected_provider
            and kyc_payload.get("provider") == expected_provider
            and internal_payload.get("ready") is True
            and (internal_payload.get("details") or {}).get("operating_mode") == "live"
            and catalog_payload.get("provider_status") == "live"
            and catalog_payload.get("capability_status") == "live"
            and kyc_payload.get("provider_status") == "live"
            and kyc_payload.get("capability_status") == "live"
        ),
    }

    return {
        "status": "failed" if errors else "ok",
        "request_id": request_id,
        "internal_base_url": internal_base_url,
        "public_base_url": public_base_url,
        "expected_provider": expected_provider,
        "plan": plan,
        "sample_address": sample_address,
        "sample_chain": sample_chain,
        "checks": checks,
        "correlation": correlation,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    internal_base = build_internal_base_url()
    public_base = build_public_base_url(internal_base)

    parser = argparse.ArgumentParser(
        description="Valida runtime real do provider AML/KYT no compliance-api."
    )
    parser.add_argument("--internal-base-url", default=internal_base)
    parser.add_argument("--public-base-url", default=public_base)
    parser.add_argument("--expected-provider", default=env_value("COMPLIANCE_RISK_PROVIDER", "trm_labs"))
    parser.add_argument("--plan", default=env_value("ONTRACKCHAIN_EXPECTED_PLAN", "professional"))
    parser.add_argument(
        "--sample-address",
        default=env_value("ONTRACKCHAIN_COMPLIANCE_SAMPLE_ADDRESS", "0x000000000000000000000000000000000000dEaD"),
    )
    parser.add_argument("--sample-chain", default=env_value("ONTRACKCHAIN_COMPLIANCE_SAMPLE_CHAIN", "ethereum"))
    parser.add_argument("--bearer-token", default=env_value("ONTRACKCHAIN_BEARER_TOKEN"))
    parser.add_argument("--api-key", default=env_value("ONTRACKCHAIN_API_KEY"))
    parser.add_argument("--timeout-seconds", type=float, default=float(env_value("ONTRACKCHAIN_HTTP_TIMEOUT_SECONDS", "10")))
    parser.add_argument(
        "--request-id",
        default=env_value("ONTRACKCHAIN_REGULATORY_COMPLIANCE_REQUEST_ID", f"compliance-runtime-{uuid.uuid4().hex[:12]}"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        internal_base_url=args.internal_base_url.rstrip("/"),
        public_base_url=args.public_base_url.rstrip("/"),
        expected_provider=args.expected_provider,
        plan=args.plan,
        sample_address=args.sample_address,
        sample_chain=args.sample_chain,
        bearer_token=args.bearer_token,
        api_key=args.api_key,
        timeout_seconds=args.timeout_seconds,
        request_id=args.request_id,
    )
    output = sys.stdout if payload["status"] == "ok" else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
