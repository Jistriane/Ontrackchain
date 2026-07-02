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


def build_step(*, status: str, exit_code: int | None = None, output_file: Path | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status}
    if exit_code is not None:
        payload["exit_code"] = exit_code
    if output_file is not None:
        payload["output_file"] = str(output_file)
    if errors is not None:
        payload["errors"] = errors
    return payload


def run_window(*, window_id: str, private_env_file: Path, checks_dir: Path) -> tuple[int, dict[str, Any]]:
    env_values = load_env_values(private_env_file)
    checks_dir.mkdir(parents=True, exist_ok=True)

    preflight_output_file = build_output_file(window_id, "eu-sanctions-preflight", checks_dir)
    sync_output_file = build_output_file(window_id, "eu-sanctions-sync", checks_dir)

    payload: dict[str, Any] = {
        "kind": "eu_sanctions_window_run",
        "window_id": window_id,
        "generated_at": utc_now().isoformat(),
        "status": "ok",
        "errors": [],
        "files": {
            "private_env_file": str(private_env_file),
            "checks_dir": str(checks_dir),
        },
        "steps": {},
    }

    with temporary_environ(env_values):
        preflight_exit_code, preflight_payload = run_module_main(
            "scripts/preflight_external_integrations.py",
            ["preflight_external_integrations.py"],
            f"eu_window_preflight_{window_id}",
        )
    write_json_file(preflight_output_file, preflight_payload)
    payload["steps"]["external_preflight"] = build_step(
        status=preflight_payload.get("status", "failed"),
        exit_code=preflight_exit_code,
        output_file=preflight_output_file,
        errors=preflight_payload.get("errors", []),
    )
    if preflight_exit_code != 0:
        payload["errors"].append("external_preflight: falhou")

    if preflight_exit_code != 0:
        payload["steps"]["eu_sync_status"] = build_step(
            status="skipped",
            errors=["preflight_failed"],
        )
        payload["status"] = "failed"
        return 1, payload

    with temporary_environ(env_values):
        sync_exit_code, sync_payload = run_module_main(
            "scripts/check_sanctions_sync_status.py",
            ["check_sanctions_sync_status.py", "--eu-window"],
            f"eu_window_sync_{window_id}",
        )
    write_json_file(sync_output_file, sync_payload)
    payload["steps"]["eu_sync_status"] = build_step(
        status=sync_payload.get("status", "failed"),
        exit_code=sync_exit_code,
        output_file=sync_output_file,
        errors=sync_payload.get("errors", []),
    )
    if sync_exit_code != 0:
        payload["errors"].append("eu_sync_status: falhou")

    payload["status"] = "ok" if not payload["errors"] else "failed"
    return (0 if payload["status"] == "ok" else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o rito leve da janela UE: preflight externo + checker canônico de EU_CONSOLIDATED."
    )
    parser.add_argument("--window-id", default=f"stg-{utc_now().strftime('%Y-%m-%d')}-eu")
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--checks-dir", default=str(DEFAULT_CHECKS_DIR))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code, payload = run_window(
        window_id=args.window_id,
        private_env_file=Path(args.private_env_file),
        checks_dir=Path(args.checks_dir),
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
