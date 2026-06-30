#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = REPO_ROOT / ".env"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "homologation"
DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000002"
DEFAULT_PLAN = "professional"
DEFAULT_ROLE = "ADMIN"
RPC_EXPECTED_CHOICES = {"live", "fallback_only"}


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


DOTENV_VALUES = load_dotenv_values(DOTENV_PATH)


def env_value(name: str, default: str) -> str:
    return os.getenv(name) or DOTENV_VALUES.get(name) or default


def build_base_url() -> str:
    return os.getenv("ONTRACKCHAIN_BASE_URL") or env_value(
        "NEXT_PUBLIC_API_BASE_URL",
        f"http://localhost:{env_value('TRAEFIK_HTTP_PORT', '8080')}",
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def make_headers(
    *,
    api_key: str,
    org_id: str,
    user_id: str,
    plan: str,
    role: str,
    request_id: str | None = None,
) -> dict[str, str]:
    headers = {
        "content-type": "application/json",
        "X-API-Key": api_key,
        "X-Org-Id": org_id,
        "X-User-Id": user_id,
        "X-Plan": plan,
        "X-Role": role,
    }
    if request_id:
        headers["X-Request-Id"] = request_id
    return headers


def request_json(
    *,
    base_url: str,
    method: str,
    path: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    retries: int = 4,
) -> tuple[int, dict[str, Any], dict[str, str]]:
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return response.status, payload, dict(response.headers)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw}
            return exc.code, payload, dict(exc.headers)
        except urllib.error.URLError as exc:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            return 599, {"error": str(exc)}, {}
    return 599, {"error": "unexpected_retry_exit"}, {}


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture_preflight_summary() -> tuple[int, dict[str, Any]]:
    module = load_module("preflight_external_integrations", "scripts/preflight_external_integrations.py")
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = int(module.main())
    raw_output = stdout.getvalue().strip() or stderr.getvalue().strip()
    if not raw_output:
        return exit_code, {"status": "failed", "errors": ["preflight_external_integrations nao gerou JSON"]}
    return exit_code, json.loads(raw_output)


def find_operation(operations_payload: dict[str, Any], canonical: str) -> dict[str, Any] | None:
    operations = operations_payload.get("operations") or []
    for item in operations:
        if item.get("canonical") == canonical:
            return item
    return None


def wait_for_investigation_terminal_result(
    *,
    base_url: str,
    headers: dict[str, str],
    case_id: str,
    timeout_seconds: int,
    poll_seconds: float,
) -> tuple[int, dict[str, Any]]:
    deadline = time.time() + timeout_seconds
    last_status = 599
    last_payload: dict[str, Any] = {}
    while time.time() < deadline:
        status, payload, _ = request_json(
            base_url=base_url,
            method="GET",
            path=f"/api/v1/investigation/{case_id}/result",
            headers=headers,
        )
        last_status = status
        last_payload = payload
        if status == 200 and payload.get("status") in {"completed", "failed"}:
            return status, payload
        time.sleep(poll_seconds)
    return last_status, last_payload


def run_compliance_homologation(
    *,
    base_url: str,
    api_key: str,
    org_id: str,
    user_id: str,
    plan: str,
    role: str,
    address: str,
    chain: str,
) -> dict[str, Any]:
    errors: list[str] = []
    request_id = os.getenv("ONTRACKCHAIN_HOMOLOGATION_COMPLIANCE_REQUEST_ID") or f"homologation-compliance-{uuid.uuid4().hex[:12]}"
    headers = make_headers(
        api_key=api_key,
        org_id=org_id,
        user_id=user_id,
        plan=plan,
        role=role,
        request_id=request_id,
    )

    readiness_status, readiness_payload, _ = request_json(
        base_url=base_url,
        method="GET",
        path="/internal/provider-readiness",
        headers=headers,
    )
    catalog_status, catalog_payload, _ = request_json(
        base_url=base_url,
        method="GET",
        path="/api/v1/compliance/operations?include_unavailable=true",
        headers=headers,
    )
    risk_check_status, risk_check_payload, _ = request_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/compliance/risk-check",
        headers=headers,
        data={"address": address, "chain": chain},
    )
    evidence_status, evidence_payload, _ = request_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/audit/evidence-export",
        headers=headers,
        data={
            "request_id": request_id,
            "resource_type": "address",
            "limit": 100,
            "include_audit_logs": True,
            "include_credit_ledger": False,
            "include_reports": True,
        },
    )

    kyc_operation = find_operation(catalog_payload, "kyc_wallet")
    readiness_mode = ((readiness_payload.get("details") or {}).get("operating_mode")) if isinstance(readiness_payload, dict) else None
    evidence_audit_count = (((evidence_payload.get("sections") or {}).get("audit_logs") or {}).get("count")) if isinstance(evidence_payload, dict) else None

    if readiness_status != 200:
        errors.append(f"provider-readiness: esperado HTTP 200, recebido {readiness_status}")
    if not readiness_payload.get("ready"):
        errors.append("provider-readiness: esperado ready=true")
    if readiness_mode != "live":
        errors.append(f"provider-readiness: esperado details.operating_mode=live, recebido={readiness_mode}")
    if catalog_status != 200:
        errors.append(f"compliance-operations: esperado HTTP 200, recebido {catalog_status}")
    if not kyc_operation:
        errors.append("compliance-operations: operacao canonical=kyc_wallet nao encontrada")
    else:
        if kyc_operation.get("provider") != "trm_labs":
            errors.append(f"compliance-operations: esperado provider=trm_labs, recebido={kyc_operation.get('provider')}")
        if kyc_operation.get("provider_status") != "live":
            errors.append(
                f"compliance-operations: esperado provider_status=live, recebido={kyc_operation.get('provider_status')}"
            )
        if kyc_operation.get("capability_status") != "live":
            errors.append(
                f"compliance-operations: esperado capability_status=live, recebido={kyc_operation.get('capability_status')}"
            )
        if kyc_operation.get("delivery_mode") != "risk_check_instant":
            errors.append(
                f"compliance-operations: esperado delivery_mode=risk_check_instant, recebido={kyc_operation.get('delivery_mode')}"
            )
    if risk_check_status != 200:
        errors.append(f"compliance-risk-check: esperado HTTP 200, recebido {risk_check_status}")
    if risk_check_payload.get("provider_status") != "live":
        errors.append(
            f"compliance-risk-check: esperado provider_status=live, recebido={risk_check_payload.get('provider_status')}"
        )
    if evidence_status != 200:
        errors.append(f"evidence-export: esperado HTTP 200, recebido {evidence_status}")
    if not evidence_audit_count:
        errors.append("evidence-export: esperado pelo menos um audit_log correlacionado pelo request_id")

    return {
        "mode": "compliance",
        "request_id": request_id,
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "inputs": {"address": address, "chain": chain},
        "checks": {
            "provider_readiness": {"http_status": readiness_status, "payload": readiness_payload},
            "operations_catalog": {"http_status": catalog_status, "payload": catalog_payload},
            "risk_check": {"http_status": risk_check_status, "payload": risk_check_payload},
            "evidence_export": {"http_status": evidence_status, "payload": evidence_payload},
        },
    }


def run_rpc_homologation(
    *,
    base_url: str,
    api_key: str,
    org_id: str,
    user_id: str,
    plan: str,
    role: str,
    address: str,
    chain: str,
    expected_mode: str,
    timeout_seconds: int,
    poll_seconds: float,
) -> dict[str, Any]:
    errors: list[str] = []
    request_id = os.getenv("ONTRACKCHAIN_HOMOLOGATION_RPC_REQUEST_ID") or f"homologation-rpc-{uuid.uuid4().hex[:12]}"
    headers = make_headers(
        api_key=api_key,
        org_id=org_id,
        user_id=user_id,
        plan=plan,
        role=role,
        request_id=request_id,
    )

    readiness_status, readiness_payload, _ = request_json(
        base_url=base_url,
        method="GET",
        path="/internal/rpc-readiness",
        headers=headers,
    )
    estimate_status, estimate_payload, _ = request_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/investigation/estimate",
        headers=headers,
        data={
            "address": address,
            "chains": [chain],
            "depth": 3,
            "report_type": "technical_basic",
            "addons": [],
        },
    )
    quote_id = estimate_payload.get("quote_id")
    start_status = None
    start_payload: dict[str, Any] = {}
    result_status = None
    result_payload: dict[str, Any] = {}
    case_id = None
    if quote_id:
        start_status, start_payload, _ = request_json(
            base_url=base_url,
            method="POST",
            path="/api/v1/investigation/start",
            headers=headers,
            data={"quote_id": quote_id, "confirmed": True},
        )
        case_id = start_payload.get("case_id")
        if case_id:
            result_status, result_payload = wait_for_investigation_terminal_result(
                base_url=base_url,
                headers=headers,
                case_id=case_id,
                timeout_seconds=timeout_seconds,
                poll_seconds=poll_seconds,
            )

    evidence_status, evidence_payload, _ = request_json(
        base_url=base_url,
        method="POST",
        path="/api/v1/audit/evidence-export",
        headers=headers,
        data={
            "request_id": request_id,
            "resource_id": case_id,
            "limit": 150,
            "include_audit_logs": True,
            "include_credit_ledger": True,
            "include_reports": True,
        },
    )

    readiness_mode = ((readiness_payload.get("details") or {}).get("operating_mode")) if isinstance(readiness_payload, dict) else None
    kyw_summary = (result_payload.get("kyw_summary") or {}) if isinstance(result_payload, dict) else {}
    rpc_summary = (kyw_summary.get("rpc") or {}) if isinstance(kyw_summary, dict) else {}
    analysis_version = kyw_summary.get("analysis_version")
    rpc_source = rpc_summary.get("rpc_source")
    provider_status = rpc_summary.get("provider_status")
    evidence_audit_count = (((evidence_payload.get("sections") or {}).get("audit_logs") or {}).get("count")) if isinstance(evidence_payload, dict) else None

    if readiness_status != 200:
        errors.append(f"rpc-readiness: esperado HTTP 200, recebido {readiness_status}")
    if not readiness_payload.get("ready"):
        errors.append("rpc-readiness: esperado ready=true")
    if readiness_mode != expected_mode:
        errors.append(f"rpc-readiness: esperado details.operating_mode={expected_mode}, recebido={readiness_mode}")
    if estimate_status != 200:
        errors.append(f"investigation-estimate: esperado HTTP 200, recebido {estimate_status}")
    if not quote_id:
        errors.append("investigation-estimate: quote_id ausente")
    if start_status not in {200, 202}:
        errors.append(f"investigation-start: esperado HTTP 200/202, recebido {start_status}")
    if not case_id:
        errors.append("investigation-start: case_id ausente")
    if result_status != 200:
        errors.append(f"investigation-result: esperado HTTP 200, recebido {result_status}")
    if result_payload.get("status") != "completed":
        errors.append(f"investigation-result: esperado status=completed, recebido={result_payload.get('status')}")
    if analysis_version != "rpc_provider_v1":
        errors.append(f"investigation-result: esperado analysis_version=rpc_provider_v1, recebido={analysis_version}")
    if provider_status not in {"live", "degraded"}:
        errors.append(f"investigation-result: provider_status invalido={provider_status}")
    if rpc_source not in {"provider_primary", "provider_fallback"}:
        errors.append(f"investigation-result: rpc_source invalido={rpc_source}")
    if expected_mode == "live" and rpc_source != "provider_primary":
        errors.append(f"investigation-result: esperado rpc_source=provider_primary em modo live, recebido={rpc_source}")
    if expected_mode == "fallback_only" and rpc_source != "provider_fallback":
        errors.append(
            f"investigation-result: esperado rpc_source=provider_fallback em modo fallback_only, recebido={rpc_source}"
        )
    if evidence_status != 200:
        errors.append(f"evidence-export: esperado HTTP 200, recebido {evidence_status}")
    if not evidence_audit_count:
        errors.append("evidence-export: esperado pelo menos um audit_log correlacionado pelo request_id")

    return {
        "mode": "rpc",
        "request_id": request_id,
        "case_id": case_id,
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "inputs": {
            "address": address,
            "chain": chain,
            "expected_mode": expected_mode,
            "timeout_seconds": timeout_seconds,
            "poll_seconds": poll_seconds,
        },
        "checks": {
            "rpc_readiness": {"http_status": readiness_status, "payload": readiness_payload},
            "estimate": {"http_status": estimate_status, "payload": estimate_payload},
            "start": {"http_status": start_status, "payload": start_payload},
            "result": {"http_status": result_status, "payload": result_payload},
            "evidence_export": {"http_status": evidence_status, "payload": evidence_payload},
        },
    }


def write_artifacts(*, payload: dict[str, Any], mode: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    artifact_path = output_dir / f"external_homologation_{mode}_{stamp}.json"
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifact_path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    size_bytes = artifact_path.stat().st_size

    manifest_payload = {
        "kind": "external_homologation_evidence",
        "status": payload.get("status"),
        "generated_at_utc": payload.get("generated_at"),
        "mode": mode,
        "artifact_file": str(artifact_path),
        "artifact_file_size_bytes": size_bytes,
        "artifact_file_sha256": digest,
        "runs": {
            "compliance_request_id": ((payload.get("runs") or {}).get("compliance") or {}).get("request_id"),
            "rpc_request_id": ((payload.get("runs") or {}).get("rpc") or {}).get("request_id"),
            "rpc_case_id": ((payload.get("runs") or {}).get("rpc") or {}).get("case_id"),
        },
    }
    manifest_path = output_dir / f"{artifact_path.name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact_path, manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa homologacao controlada de AML/KYT e RPC e gera artefato anexavel ao gate."
    )
    parser.add_argument("--mode", choices=["compliance", "rpc", "both"], default="both")
    parser.add_argument("--base-url", default=build_base_url())
    parser.add_argument("--api-key", default=os.getenv("ONTRACKCHAIN_API_KEY", "otc_live_demo_key"))
    parser.add_argument("--org-id", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_ORG_ID", DEFAULT_ORG_ID))
    parser.add_argument("--user-id", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_USER_ID", DEFAULT_USER_ID))
    parser.add_argument("--plan", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_PLAN", DEFAULT_PLAN))
    parser.add_argument("--role", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_ROLE", DEFAULT_ROLE))
    parser.add_argument(
        "--compliance-address",
        default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_COMPLIANCE_ADDRESS", "0x00000000000000000000000000000000000000c1"),
    )
    parser.add_argument("--compliance-chain", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_COMPLIANCE_CHAIN", "ethereum"))
    parser.add_argument(
        "--rpc-address",
        default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_RPC_ADDRESS", "0x0000000000000000000000000000000000000a11"),
    )
    parser.add_argument("--rpc-chain", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_RPC_CHAIN", "ethereum"))
    parser.add_argument(
        "--rpc-expected-mode",
        choices=["live", "fallback_only"],
        default=(
            os.getenv("ONTRACKCHAIN_EXPECT_RPC_MODE")
            if os.getenv("ONTRACKCHAIN_EXPECT_RPC_MODE") in RPC_EXPECTED_CHOICES
            else "live"
        ),
    )
    parser.add_argument("--timeout-seconds", type=int, default=int(os.getenv("ONTRACKCHAIN_HOMOLOGATION_TIMEOUT_SECONDS", "45")))
    parser.add_argument("--poll-seconds", type=float, default=float(os.getenv("ONTRACKCHAIN_HOMOLOGATION_POLL_SECONDS", "1.5")))
    parser.add_argument("--output-dir", default=os.getenv("ONTRACKCHAIN_HOMOLOGATION_OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR)))
    parser.add_argument("--skip-preflight", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = utc_now().isoformat()
    payload: dict[str, Any] = {
        "kind": "external_homologation_evidence",
        "generated_at": started_at,
        "base_url": args.base_url,
        "mode": args.mode,
        "status": "ok",
        "errors": [],
        "preflight": None,
        "runs": {},
    }

    try:
        if not args.skip_preflight:
            preflight_exit_code, preflight_payload = capture_preflight_summary()
            payload["preflight"] = {
                "exit_code": preflight_exit_code,
                "payload": preflight_payload,
            }
            if preflight_exit_code != 0:
                payload["errors"].append("preflight_external_integrations: falhou para o ambiente atual")

        if args.mode in {"compliance", "both"}:
            payload["runs"]["compliance"] = run_compliance_homologation(
                base_url=args.base_url,
                api_key=args.api_key,
                org_id=args.org_id,
                user_id=args.user_id,
                plan=args.plan,
                role=args.role,
                address=args.compliance_address,
                chain=args.compliance_chain,
            )
            payload["errors"].extend(payload["runs"]["compliance"]["errors"])

        if args.mode in {"rpc", "both"}:
            payload["runs"]["rpc"] = run_rpc_homologation(
                base_url=args.base_url,
                api_key=args.api_key,
                org_id=args.org_id,
                user_id=args.user_id,
                plan=args.plan,
                role=args.role,
                address=args.rpc_address,
                chain=args.rpc_chain,
                expected_mode=args.rpc_expected_mode,
                timeout_seconds=args.timeout_seconds,
                poll_seconds=args.poll_seconds,
            )
            payload["errors"].extend(payload["runs"]["rpc"]["errors"])
    except Exception as exc:  # noqa: BLE001
        payload["errors"].append(f"execucao_inesperada: {exc}")

    payload["status"] = "ok" if not payload["errors"] else "failed"
    payload["finished_at"] = utc_now().isoformat()
    artifact_path, manifest_path = write_artifacts(
        payload=payload,
        mode=args.mode,
        output_dir=Path(args.output_dir),
    )
    payload["artifact_file"] = str(artifact_path)
    payload["manifest_file"] = str(manifest_path)

    output = sys.stdout if payload["status"] == "ok" else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
