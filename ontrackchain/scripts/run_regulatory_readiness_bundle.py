#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
import uuid
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


def run_module_main(relative_path: str, argv: list[str], module_name: str) -> tuple[int, dict[str, Any]]:
    module = load_module(module_name, relative_path)
    stdout = io.StringIO()
    stderr = io.StringIO()
    previous_argv = sys.argv[:]
    try:
        sys.argv = argv
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = module.main()
    finally:
        sys.argv = previous_argv

    exit_code = int(result or 0)
    raw_output = stdout.getvalue().strip() or stderr.getvalue().strip()
    if not raw_output:
        return exit_code, {
            "status": "failed",
            "errors": [f"{relative_path}: execucao sem payload JSON"],
        }
    return exit_code, json.loads(raw_output)


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


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def should_include_compliance_runtime(env_values: dict[str, str], forced: bool) -> bool:
    if forced:
        return True
    expect_mode = env_values.get("ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE", "").strip().lower()
    return expect_mode == "live"


def should_include_eu_window(env_values: dict[str, str], forced: bool) -> bool:
    if forced:
        return True
    eu_override_url = env_values.get("COMPLIANCE_EU_SANCTIONS_SOURCE_URL", "").strip()
    return bool(eu_override_url)


def build_step(
    *,
    status: str,
    enabled: bool,
    exit_code: int | None = None,
    output_file: Path | None = None,
    errors: list[str] | None = None,
    reason: str | None = None,
    request_id: str | None = None,
    correlation: dict[str, Any] | None = None,
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
    if reason is not None:
        payload["reason"] = reason
    if request_id is not None:
        payload["request_id"] = request_id
    if correlation is not None:
        payload["correlation"] = correlation
    return payload


def build_track_readiness(
    *,
    enabled: bool,
    step_name: str,
    step_payload: dict[str, Any],
) -> dict[str, Any]:
    step_status = str(step_payload.get("status") or "skipped")
    step_errors = [str(error) for error in (step_payload.get("errors") or []) if str(error).strip()]
    step_reason = str(step_payload.get("reason") or "").strip()
    correlation = step_payload.get("correlation") or {}
    correlation_blockers: list[str] = []

    if enabled and step_status == "ok":
        request_id = str(step_payload.get("request_id") or "").strip()
        if not request_id:
            correlation_blockers.append(f"{step_name}: request_id obrigatorio ausente para trilha auditavel")
        if step_name == "compliance_provider_runtime":
            if correlation.get("provider_converges_live") is not True:
                correlation_blockers.append(
                    f"{step_name}: correlacao estruturada do provider nao confirma convergencia live"
                )
        if step_name == "eu_sanctions_window":
            if correlation.get("eu_window_converges_ready") is not True:
                correlation_blockers.append(
                    f"{step_name}: correlacao estruturada da janela UE nao confirma convergencia pronta para validacao"
                )

    if not enabled:
        return {
            "readiness_status": "ready",
            "blockers": [],
            "next_action": f"Habilitar a trilha `{step_name}` com insumo real e rerodar o bundle regulatorio.",
        }
    if correlation_blockers:
        return {
            "readiness_status": "blocked",
            "blockers": correlation_blockers,
            "next_action": f"Corrigir a correlacao auditavel de `{step_name}` antes de promover o bundle regulatorio.",
        }
    if step_status == "ok":
        return {
            "readiness_status": "ready_for_validation",
            "blockers": [],
            "next_action": f"Revisar o artefato de `{step_name}` e anexar o bundle regulatorio a governanca semanal.",
        }
    blockers = step_errors or (
        [f"{step_name}: {step_reason}"] if step_reason else [f"{step_name}: status={step_status}"]
    )
    return {
        "readiness_status": "blocked",
        "blockers": blockers,
        "next_action": f"Corrigir a trilha `{step_name}` e rerodar o bundle regulatorio com insumos reais.",
    }


def build_bundle_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    scope = payload.get("scope") or {}
    steps = payload.get("steps") or {}
    compliance_enabled = bool(scope.get("compliance_runtime_enabled"))
    eu_enabled = bool(scope.get("eu_window_enabled"))
    compliance_track = build_track_readiness(
        enabled=compliance_enabled,
        step_name="compliance_provider_runtime",
        step_payload=(steps.get("compliance_provider_runtime") or {}),
    )
    eu_track = build_track_readiness(
        enabled=eu_enabled,
        step_name="eu_sanctions_window",
        step_payload=(steps.get("eu_sanctions_window") or {}),
    )

    if payload.get("status") == "failed":
        bundle_status = "blocked"
        bundle_blockers = [str(error) for error in (payload.get("errors") or []) if str(error).strip()]
        bundle_next_action = "Corrigir as trilhas regulatórias bloqueadas e rerodar o bundle antes de promover a janela."
    else:
        track_blockers = [
            *[str(error) for error in (compliance_track.get("blockers") or []) if str(error).strip()],
            *[str(error) for error in (eu_track.get("blockers") or []) if str(error).strip()],
        ]
        both_in_scope = compliance_enabled and eu_enabled
        both_ready_for_validation = (
            compliance_track.get("readiness_status") == "ready_for_validation"
            and eu_track.get("readiness_status") == "ready_for_validation"
        )

        if track_blockers:
            bundle_status = "blocked"
            bundle_blockers = track_blockers
            bundle_next_action = "Corrigir correlacao ou falhas das trilhas regulatórias antes de promover o bundle oficial."
        elif both_in_scope and both_ready_for_validation:
            bundle_status = "ready_for_validation"
            bundle_blockers = []
            bundle_next_action = "Anexar o bundle regulatorio ao dossier/governanca e executar revisao formal das evidencias."
        else:
            bundle_status = "ready"
            bundle_blockers = []
            if not both_in_scope:
                bundle_next_action = "Executar a mesma janela com P0-02 e P0-03 simultaneamente para gerar o bundle regulatorio oficial."
            else:
                bundle_next_action = "Completar a trilha regulatoria remanescente e rerodar o bundle oficial antes da promocao."

    return {
        "compliance_runtime": compliance_track,
        "eu_window": eu_track,
        "regulatory_bundle": {
            "readiness_status": bundle_status,
            "blockers": bundle_blockers,
            "next_action": bundle_next_action,
        },
    }


def run_bundle(
    *,
    window_id: str,
    private_env_file: Path,
    checks_dir: Path,
    internal_base_url: str,
    public_base_url: str,
    force_compliance_runtime: bool,
    force_eu_window: bool,
) -> tuple[int, dict[str, Any]]:
    env_values = load_env_values(private_env_file)
    checks_dir.mkdir(parents=True, exist_ok=True)

    include_compliance_runtime = should_include_compliance_runtime(
        env_values, force_compliance_runtime
    )
    include_eu_window = should_include_eu_window(env_values, force_eu_window)

    payload: dict[str, Any] = {
        "kind": "regulatory_readiness_bundle",
        "window_id": window_id,
        "generated_at": utc_now().isoformat(),
        "status": "ok",
        "errors": [],
        "files": {
            "private_env_file": str(private_env_file),
            "checks_dir": str(checks_dir),
        },
        "scope": {
            "compliance_runtime_enabled": include_compliance_runtime,
            "eu_window_enabled": include_eu_window,
        },
        "steps": {},
    }

    if not include_compliance_runtime and not include_eu_window:
        payload["status"] = "skipped"
        payload["steps"]["compliance_provider_runtime"] = build_step(
            status="skipped",
            enabled=False,
            reason="out_of_scope",
        )
        payload["steps"]["eu_sanctions_window"] = build_step(
            status="skipped",
            enabled=False,
            reason="out_of_scope",
        )
        payload["readiness"] = build_bundle_readiness(payload)
        return 0, payload

    if include_compliance_runtime:
        compliance_request_id = env_values.get(
            "ONTRACKCHAIN_REGULATORY_COMPLIANCE_REQUEST_ID",
            f"{window_id}-compliance-{uuid.uuid4().hex[:8]}",
        )
        runtime_output_file = build_output_file(
            window_id, "compliance-provider-runtime", checks_dir
        )
        argv = [
            "check_compliance_provider_runtime.py",
            "--request-id",
            compliance_request_id,
        ]
        if internal_base_url:
            argv.extend(["--internal-base-url", internal_base_url])
        if public_base_url:
            argv.extend(["--public-base-url", public_base_url])

        with temporary_environ(env_values):
            runtime_exit_code, runtime_payload = run_module_main(
                "scripts/check_compliance_provider_runtime.py",
                argv,
                f"regulatory_bundle_compliance_runtime_{window_id}",
            )
        write_json_file(runtime_output_file, runtime_payload)
        payload["steps"]["compliance_provider_runtime"] = build_step(
            status=runtime_payload.get("status", "failed"),
            enabled=True,
            exit_code=runtime_exit_code,
            output_file=runtime_output_file,
            errors=runtime_payload.get("errors", []),
            request_id=str(runtime_payload.get("request_id") or compliance_request_id),
            correlation=runtime_payload.get("correlation", {}),
        )
        if runtime_exit_code != 0:
            payload["errors"].append("compliance_provider_runtime: falhou")
    else:
        payload["steps"]["compliance_provider_runtime"] = build_step(
            status="skipped",
            enabled=False,
            reason="out_of_scope",
        )

    if include_eu_window:
        eu_request_id = env_values.get(
            "ONTRACKCHAIN_REGULATORY_EU_REQUEST_ID",
            f"{window_id}-eu-{uuid.uuid4().hex[:8]}",
        )
        eu_output_file = build_output_file(window_id, "eu-sanctions-window", checks_dir)
        eu_exit_code, eu_payload = run_module_main(
            "scripts/run_eu_sanctions_window.py",
            [
                "run_eu_sanctions_window.py",
                "--window-id",
                window_id,
                "--private-env-file",
                str(private_env_file),
                "--checks-dir",
                str(checks_dir),
                "--request-id",
                eu_request_id,
            ],
            f"regulatory_bundle_eu_window_{window_id}",
        )
        write_json_file(eu_output_file, eu_payload)
        payload["steps"]["eu_sanctions_window"] = build_step(
            status=eu_payload.get("status", "failed"),
            enabled=True,
            exit_code=eu_exit_code,
            output_file=eu_output_file,
            errors=eu_payload.get("errors", []),
            request_id=str(eu_payload.get("request_id") or eu_request_id),
            correlation=eu_payload.get("correlation", {}),
        )
        if eu_exit_code != 0:
            payload["errors"].append("eu_sanctions_window: falhou")
    else:
        payload["steps"]["eu_sanctions_window"] = build_step(
            status="skipped",
            enabled=False,
            reason="out_of_scope",
        )

    payload["status"] = "ok" if not payload["errors"] else "failed"
    payload["readiness"] = build_bundle_readiness(payload)
    if ((payload.get("readiness") or {}).get("regulatory_bundle") or {}).get("readiness_status") == "blocked":
        for blocker in (((payload.get("readiness") or {}).get("regulatory_bundle") or {}).get("blockers") or []):
            blocker_text = str(blocker).strip()
            if blocker_text:
                payload["errors"].append(f"regulatory_bundle_readiness: {blocker_text}")
        payload["status"] = "failed"
    return (0 if payload["status"] == "ok" else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o bundle regulatorio de P0-02/P0-03 com artefatos anexaveis."
    )
    parser.add_argument("--window-id", default=f"stg-{utc_now().strftime('%Y-%m-%d')}-reg")
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--checks-dir", default=str(DEFAULT_CHECKS_DIR))
    parser.add_argument("--internal-base-url", default="")
    parser.add_argument("--public-base-url", default="")
    parser.add_argument("--include-compliance-runtime", action="store_true")
    parser.add_argument("--include-eu-window", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code, payload = run_bundle(
        window_id=args.window_id,
        private_env_file=Path(args.private_env_file),
        checks_dir=Path(args.checks_dir),
        internal_base_url=args.internal_base_url.strip(),
        public_base_url=args.public_base_url.strip(),
        force_compliance_runtime=bool(args.include_compliance_runtime),
        force_eu_window=bool(args.include_eu_window),
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
