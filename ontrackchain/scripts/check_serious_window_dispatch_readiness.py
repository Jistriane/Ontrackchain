#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOVERNANCE_WEEKLY_DIR = REPO_ROOT / "docs" / "governance-weekly"
DEFAULT_WORKFLOW_FILE = REPO_ROOT.parent / ".github" / "workflows" / "staging-serious-window.yml"
WINDOW_ID_PATTERN = re.compile(r"stg-(\d{4}-\d{2}-\d{2})-[a-z0-9]+")


def extract_window_date(window_id: str) -> str:
    match = WINDOW_ID_PATTERN.fullmatch(window_id)
    if not match:
        raise ValueError(f"window_id_invalido: {window_id}")
    return match.group(1)


def default_weekly_file(window_id: str, governance_weekly_dir: Path) -> Path:
    return governance_weekly_dir / f"{extract_window_date(window_id)}-weekly-governance.md"


def default_signoff_file(window_id: str, governance_weekly_dir: Path) -> Path:
    return governance_weekly_dir / f"{extract_window_date(window_id)}-staging-serious-window-signoff.md"


def build_check(name: str, *, status: str, details: str) -> dict[str, str]:
    return {
        "name": name,
        "status": status,
        "details": details,
    }


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_dispatch_readiness(
    *,
    window_id: str,
    mode: str,
    environment_name: str,
    governance_weekly_dir: Path,
    workflow_file: Path,
) -> dict[str, Any]:
    artifact_name = f"serious-staging-window-{window_id}"
    checks: list[dict[str, str]] = []
    errors: list[str] = []
    next_steps = [
        f"Confirmar reviewers e secret `STAGING_WINDOW_PRIVATE_ENV` no environment `{environment_name}`.",
        f"Disparar o workflow `Staging Serious Window` para `{window_id}` em modo `{mode}`.",
        "Baixar o artifact oficial e executar `make postprocess-serious-window RUN_URL=<github-actions-run-url>`.",
    ]

    try:
        window_date = extract_window_date(window_id)
        weekly_file = default_weekly_file(window_id, governance_weekly_dir)
        signoff_file = default_signoff_file(window_id, governance_weekly_dir)
        checks.append(
            build_check(
                "window_id_format",
                status="ok",
                details=f"window_id valido para a janela semanal `{window_date}`.",
            )
        )
    except ValueError as exc:
        errors.append(str(exc))
        checks.append(
            build_check(
                "window_id_format",
                status="failed",
                details=str(exc),
            )
        )
        return {
            "kind": "serious_window_dispatch_readiness",
            "status": "failed",
            "window_id": window_id,
            "mode": mode,
            "environment_name": environment_name,
            "artifact_name": artifact_name,
            "checks": checks,
            "errors": errors,
            "next_steps": next_steps,
        }

    if workflow_file.exists():
        workflow_content = read_text_file(workflow_file)
        required_tokens = [
            "workflow_dispatch:",
            "STAGING_WINDOW_PRIVATE_ENV",
            "environment_name:",
            "serious-staging-window-${{ inputs.window_id }}",
        ]
        missing_tokens = [token for token in required_tokens if token not in workflow_content]
        if missing_tokens:
            detail = f"workflow sem contratos esperados: {', '.join(missing_tokens)}"
            errors.append(detail)
            checks.append(build_check("workflow_contract", status="failed", details=detail))
        else:
            checks.append(
                build_check(
                    "workflow_contract",
                    status="ok",
                    details=f"workflow encontrado em `{workflow_file}` com os contratos esperados do rito serio.",
                )
            )
    else:
        detail = f"workflow_nao_encontrado: {workflow_file}"
        errors.append(detail)
        checks.append(build_check("workflow_contract", status="failed", details=detail))

    if weekly_file.exists():
        weekly_content = read_text_file(weekly_file)
        required_weekly_tokens = [
            f"- `window_id`: `{window_id}`",
            f"- `mode`: `{mode}`",
            f"- `environment_name`: `{environment_name}`",
            "## Evidências Revisadas",
            f"- artifact `{artifact_name}`:",
            signoff_file.name,
        ]
        missing_weekly_tokens = [token for token in required_weekly_tokens if token not in weekly_content]
        if missing_weekly_tokens:
            detail = f"governanca_semanal_sem_alinhamento: {', '.join(missing_weekly_tokens)}"
            errors.append(detail)
            checks.append(build_check("weekly_governance_alignment", status="failed", details=detail))
        else:
            checks.append(
                build_check(
                    "weekly_governance_alignment",
                    status="ok",
                    details=f"board semanal `{weekly_file.name}` alinhado com `window_id`, sign-off e artifact esperados.",
                )
            )
    else:
        detail = f"governanca_semanal_nao_encontrada: {weekly_file}"
        errors.append(detail)
        checks.append(build_check("weekly_governance_alignment", status="failed", details=detail))

    if signoff_file.exists():
        signoff_content = read_text_file(signoff_file)
        required_signoff_tokens = [
            f"# Sign-Off da Janela Seria — `{window_id}`",
            f"- mode: `{mode}`",
            f"- environment_name: `{environment_name}`",
            f"- artifact: `{artifact_name}`",
        ]
        missing_signoff_tokens = [token for token in required_signoff_tokens if token not in signoff_content]
        if missing_signoff_tokens:
            detail = f"signoff_sem_alinhamento: {', '.join(missing_signoff_tokens)}"
            errors.append(detail)
            checks.append(build_check("signoff_alignment", status="failed", details=detail))
        else:
            checks.append(
                build_check(
                    "signoff_alignment",
                    status="ok",
                    details=f"sign-off versionado `{signoff_file.name}` pronto para receber o run real.",
                )
            )
    else:
        detail = f"signoff_nao_encontrado: {signoff_file}"
        errors.append(detail)
        checks.append(build_check("signoff_alignment", status="failed", details=detail))

    return {
        "kind": "serious_window_dispatch_readiness",
        "status": "failed" if errors else "ok",
        "window_id": window_id,
        "mode": mode,
        "environment_name": environment_name,
        "artifact_name": artifact_name,
        "workflow_file": str(workflow_file),
        "weekly_file": str(weekly_file),
        "signoff_file": str(signoff_file),
        "checks": checks,
        "errors": errors,
        "next_steps": next_steps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida a prontidao do disparo real da janela seria antes do workflow_dispatch."
    )
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--mode", default="baseline")
    parser.add_argument("--environment-name", default="staging-serious")
    parser.add_argument("--governance-weekly-dir", default=str(DEFAULT_GOVERNANCE_WEEKLY_DIR))
    parser.add_argument("--workflow-file", default=str(DEFAULT_WORKFLOW_FILE))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = validate_dispatch_readiness(
        window_id=args.window_id,
        mode=args.mode,
        environment_name=args.environment_name,
        governance_weekly_dir=Path(args.governance_weekly_dir),
        workflow_file=Path(args.workflow_file),
    )
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
