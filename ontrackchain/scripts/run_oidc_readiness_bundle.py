#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRIVATE_ENV_FILE = REPO_ROOT / ".env.staging.private"
DEFAULT_CHECKS_DIR = REPO_ROOT / "artifacts" / "staging" / "checks"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_env_values(file_path: Path) -> dict[str, str]:
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


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_module_capture(relative_path: str, argv: list[str], module_name: str) -> tuple[int, dict[str, Any]]:
    module = load_module(module_name, relative_path)
    stdout = io.StringIO()
    stderr = io.StringIO()
    previous_argv = sys.argv[:]
    try:
        sys.argv = argv
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = module.main()
    except Exception as exc:  # noqa: BLE001
        raw_output = stdout.getvalue().strip() or stderr.getvalue().strip()
        errors = [raw_output] if raw_output else []
        errors.append(str(exc))
        return 1, {
            "status": "failed",
            "errors": errors,
        }
    finally:
        sys.argv = previous_argv

    exit_code = int(result or 0)
    std_output = stdout.getvalue().strip()
    err_output = stderr.getvalue().strip()
    raw_output = std_output or err_output
    if not raw_output:
        return exit_code, {
            "status": "failed",
            "errors": [f"{relative_path}: execucao sem payload"],
        }

    try:
        return exit_code, json.loads(raw_output)
    except json.JSONDecodeError:
        status = "ok" if exit_code == 0 else "failed"
        return exit_code, {
            "status": status,
            "errors": [] if exit_code == 0 else [raw_output],
            "raw_output": raw_output,
        }


@contextmanager
def temporary_environ(overrides: dict[str, str]) -> Iterator[None]:
    previous: dict[str, str | None] = {}
    for key, value in overrides.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_output_file(window_id: str, step_name: str, checks_dir: Path) -> Path:
    return checks_dir / f"{window_id}-{step_name}.json"


def build_step(
    *,
    status: str,
    enabled: bool,
    exit_code: int | None = None,
    output_file: Path | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "enabled": enabled,
        "status": status,
    }
    if exit_code is not None:
        payload["exit_code"] = exit_code
    if output_file is not None:
        payload["output_file"] = str(output_file)
    if errors is not None:
        payload["errors"] = errors
    return payload


def build_readiness_summary(payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps") or {}
    preflight = steps.get("oidc_preflight") or {}
    smoke = steps.get("smoke_auth_oidc_mode") or {}
    playwright = steps.get("oidc_playwright_critical") or {}
    scope = payload.get("scope") or {}
    require_playwright_critical = scope.get("require_playwright_critical") is True

    blockers: list[str] = []
    if preflight.get("status") != "ok":
        blockers.append("preflight_oidc_serious_env ainda nao esta verde")
    if smoke.get("status") != "ok":
        blockers.append("smoke_auth_oidc_mode ainda nao esta verde")
    if require_playwright_critical and playwright.get("status") != "ok":
        blockers.append("oidc_playwright_critical ainda nao esta verde")

    mfa_homologated = str(scope.get("mfa_external_provider_homologated", "false")).strip().lower() == "true"
    if not mfa_homologated:
        blockers.append("provider MFA/OIDC ainda nao esta homologado para trilho serio")

    if preflight.get("status") != "ok" or smoke.get("status") != "ok" or (
        require_playwright_critical and playwright.get("status") != "ok"
    ):
        readiness_status = "blocked"
        next_action = "Corrigir preflight/smoke OIDC e rerodar o bundle antes de qualquer promocao."
    elif not mfa_homologated:
        readiness_status = "ready"
        next_action = "Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais."
    else:
        readiness_status = "ready_for_validation"
        next_action = "Anexar bundle ao war room/sign-off e executar validacao formal com fluxo critico OIDC."

    return {
        "readiness_status": readiness_status,
        "blockers": blockers,
        "next_action": next_action,
    }


def run_bundle(
    *,
    window_id: str,
    private_env_file: Path,
    checks_dir: Path,
    base_url: str,
    include_playwright_critical: bool,
    require_playwright_critical: bool,
    playwright_base_url: str,
    frontend_dir: Path,
    expected_oidc_provider: str,
    expected_mfa_provider_homologated: str | None,
    expected_org_claim: str,
    expected_plan_claim: str,
    expected_role_claim: str,
) -> tuple[int, dict[str, Any]]:
    env_values = load_env_values(private_env_file)
    checks_dir.mkdir(parents=True, exist_ok=True)

    smoke_env: dict[str, str] = {}
    if base_url:
        smoke_env["ONTRACKCHAIN_BASE_URL"] = base_url
    if expected_oidc_provider:
        smoke_env["ONTRACKCHAIN_EXPECTED_OIDC_PROVIDER"] = expected_oidc_provider
    if expected_mfa_provider_homologated is not None:
        smoke_env["ONTRACKCHAIN_EXPECTED_MFA_PROVIDER_HOMOLOGATED"] = expected_mfa_provider_homologated
    if expected_org_claim:
        smoke_env["ONTRACKCHAIN_EXPECTED_OIDC_ORG_CLAIM"] = expected_org_claim
    if expected_plan_claim:
        smoke_env["ONTRACKCHAIN_EXPECTED_OIDC_PLAN_CLAIM"] = expected_plan_claim
    if expected_role_claim:
        smoke_env["ONTRACKCHAIN_EXPECTED_OIDC_ROLE_CLAIM"] = expected_role_claim

    payload: dict[str, Any] = {
        "kind": "oidc_readiness_bundle",
        "window_id": window_id,
        "generated_at": utc_now().isoformat(),
        "status": "ok",
        "errors": [],
        "files": {
            "private_env_file": str(private_env_file),
            "checks_dir": str(checks_dir),
        },
        "scope": {
            "mfa_external_provider_homologated": env_values.get("MFA_EXTERNAL_PROVIDER_HOMOLOGATED", "false"),
            "expected_oidc_provider": expected_oidc_provider,
            "include_playwright_critical": include_playwright_critical,
            "require_playwright_critical": require_playwright_critical,
        },
        "steps": {},
    }

    preflight_output_file = build_output_file(window_id, "oidc-preflight", checks_dir)
    with temporary_environ(env_values):
        preflight_exit_code, preflight_payload = run_module_capture(
            "scripts/preflight_oidc_serious_env.py",
            ["preflight_oidc_serious_env.py"],
            f"oidc_readiness_preflight_{window_id}",
        )
    write_json_file(preflight_output_file, preflight_payload)
    payload["steps"]["oidc_preflight"] = build_step(
        status=preflight_payload.get("status", "failed"),
        enabled=True,
        exit_code=preflight_exit_code,
        output_file=preflight_output_file,
        errors=preflight_payload.get("errors", []),
    )
    if preflight_exit_code != 0:
        payload["errors"].append("oidc_preflight: falhou")

    smoke_output_file = build_output_file(window_id, "oidc-smoke-auth", checks_dir)
    with temporary_environ({**env_values, **smoke_env}):
        smoke_exit_code, smoke_payload = run_module_capture(
            "scripts/smoke_auth_oidc_mode.py",
            ["smoke_auth_oidc_mode.py"],
            f"oidc_readiness_smoke_{window_id}",
        )
    write_json_file(smoke_output_file, smoke_payload)
    payload["steps"]["smoke_auth_oidc_mode"] = build_step(
        status=smoke_payload.get("status", "failed"),
        enabled=True,
        exit_code=smoke_exit_code,
        output_file=smoke_output_file,
        errors=smoke_payload.get("errors", []),
    )
    if smoke_exit_code != 0:
        payload["errors"].append("smoke_auth_oidc_mode: falhou")

    if include_playwright_critical:
        effective_playwright_base_url = (
            playwright_base_url.strip()
            or base_url.strip()
            or env_values.get("ONTRACKCHAIN_BASE_URL", "").strip()
            or env_values.get("NEXT_PUBLIC_API_BASE_URL", "").strip()
        )
        playwright_output_file = build_output_file(window_id, "oidc-playwright-critical", checks_dir)
        with temporary_environ(env_values):
            playwright_exit_code, playwright_payload = run_module_capture(
                "scripts/run_oidc_playwright_critical.py",
                [
                    "run_oidc_playwright_critical.py",
                    "--base-url",
                    effective_playwright_base_url,
                    "--frontend-dir",
                    str(frontend_dir),
                ],
                f"oidc_playwright_critical_{window_id}",
            )
        write_json_file(playwright_output_file, playwright_payload)
        payload["steps"]["oidc_playwright_critical"] = build_step(
            status=playwright_payload.get("status", "failed"),
            enabled=True,
            exit_code=playwright_exit_code,
            output_file=playwright_output_file,
            errors=playwright_payload.get("errors", []),
        )
        if playwright_exit_code != 0 and require_playwright_critical:
            payload["errors"].append("oidc_playwright_critical: falhou")
    else:
        payload["steps"]["oidc_playwright_critical"] = build_step(
            status="skipped",
            enabled=False,
            errors=[],
        )

    payload["status"] = "ok" if not payload["errors"] else "failed"
    payload["readiness"] = build_readiness_summary(payload)
    return (0 if payload["status"] == "ok" else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o bundle de readiness OIDC com artefatos anexaveis."
    )
    parser.add_argument("--window-id", default=f"stg-{utc_now().strftime('%Y-%m-%d')}-oidc")
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--checks-dir", default=str(DEFAULT_CHECKS_DIR))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--include-playwright-critical", action="store_true")
    parser.add_argument("--require-playwright-critical", action="store_true")
    parser.add_argument("--playwright-base-url", default="")
    parser.add_argument("--frontend-dir", default=str(REPO_ROOT / "apps" / "frontend"))
    parser.add_argument("--expected-oidc-provider", default="keycloak")
    parser.add_argument("--expected-mfa-provider-homologated")
    parser.add_argument("--expected-org-claim", default="")
    parser.add_argument("--expected-plan-claim", default="")
    parser.add_argument("--expected-role-claim", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code, payload = run_bundle(
        window_id=args.window_id,
        private_env_file=Path(args.private_env_file),
        checks_dir=Path(args.checks_dir),
        base_url=args.base_url.strip(),
        include_playwright_critical=args.include_playwright_critical,
        require_playwright_critical=args.require_playwright_critical,
        playwright_base_url=args.playwright_base_url.strip(),
        frontend_dir=Path(args.frontend_dir),
        expected_oidc_provider=args.expected_oidc_provider.strip(),
        expected_mfa_provider_homologated=(
            args.expected_mfa_provider_homologated.strip()
            if args.expected_mfa_provider_homologated is not None
            else None
        ),
        expected_org_claim=args.expected_org_claim.strip(),
        expected_plan_claim=args.expected_plan_claim.strip(),
        expected_role_claim=args.expected_role_claim.strip(),
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
