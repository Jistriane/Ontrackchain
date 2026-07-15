#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FRONTEND_DIR = REPO_ROOT / "apps" / "frontend"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o Playwright critico de OIDC contra um ambiente serio e retorna payload JSON."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--frontend-dir", default=str(DEFAULT_FRONTEND_DIR))
    parser.add_argument("--suite-command", default="npm run test:e2e:oidc-critical")
    return parser.parse_args()


def build_payload(
    *,
    base_url: str,
    frontend_dir: Path,
    suite_command: str,
    exit_code: int,
    stdout_text: str,
    stderr_text: str,
) -> dict[str, Any]:
    playwright_report_dir = frontend_dir / "playwright-report"
    test_results_dir = frontend_dir / "test-results"
    status = "ok" if exit_code == 0 else "failed"
    errors: list[str] = []
    if exit_code != 0:
        raw_error = stderr_text.strip() or stdout_text.strip() or "oidc_playwright_critical_failed"
        errors.append(raw_error.splitlines()[-1].strip() or "oidc_playwright_critical_failed")

    return {
        "kind": "oidc_playwright_critical",
        "generated_at": utc_now().isoformat(),
        "status": status,
        "base_url": base_url,
        "frontend_dir": str(frontend_dir),
        "suite_command": suite_command,
        "exit_code": exit_code,
        "errors": errors,
        "artifacts": {
            "playwright_report_dir": str(playwright_report_dir),
            "playwright_report_present": playwright_report_dir.exists(),
            "test_results_dir": str(test_results_dir),
            "test_results_present": test_results_dir.exists(),
            "junit_report": str(test_results_dir / "junit.xml"),
            "junit_report_present": (test_results_dir / "junit.xml").exists(),
        },
        "output_excerpt": {
            "stdout_tail": stdout_text.strip().splitlines()[-20:],
            "stderr_tail": stderr_text.strip().splitlines()[-20:],
        },
    }


def main() -> int:
    args = parse_args()
    frontend_dir = Path(args.frontend_dir).resolve()
    base_url = args.base_url.strip().rstrip("/")
    suite_command = args.suite_command.strip()

    if not base_url:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "oidc_playwright_critical",
                    "status": "failed",
                    "errors": ["base_url_ausente"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    if not frontend_dir.exists():
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "oidc_playwright_critical",
                    "status": "failed",
                    "errors": [f"frontend_dir_ausente: {frontend_dir}"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    npm_path = shutil.which("npm")
    if npm_path is None:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "oidc_playwright_critical",
                    "status": "failed",
                    "errors": ["npm_ausente_no_runner"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    command = [part for part in suite_command.split(" ") if part]
    if not command:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "oidc_playwright_critical",
                    "status": "failed",
                    "errors": ["suite_command_invalido"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    env = os.environ.copy()
    env["TEST_BASE_URL"] = base_url

    completed = subprocess.run(
        command,
        cwd=frontend_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    payload = build_payload(
        base_url=base_url,
        frontend_dir=frontend_dir,
        suite_command=suite_command,
        exit_code=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
    )
    output = sys.stdout if completed.returncode == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
