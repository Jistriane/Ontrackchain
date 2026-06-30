#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOVERNANCE_WEEKLY_DIR = REPO_ROOT / "docs" / "governance-weekly"
DEFAULT_WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "staging-serious-window.yml"


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"nao_foi_possivel_carregar_modulo: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


READINESS_MODULE = load_module(
    "check_serious_window_dispatch_readiness",
    "scripts/check_serious_window_dispatch_readiness.py",
)


def default_output_file(window_id: str) -> Path:
    return REPO_ROOT / "ci-artifacts" / f"serious-window-dispatch-packet-{window_id}.md"


def build_dispatch_packet_model(
    *,
    window_id: str,
    mode: str,
    environment_name: str,
    governance_weekly_dir: Path,
    workflow_file: Path,
    workflow_name: str,
) -> dict[str, Any]:
    readiness = READINESS_MODULE.validate_dispatch_readiness(
        window_id=window_id,
        mode=mode,
        environment_name=environment_name,
        governance_weekly_dir=governance_weekly_dir,
        workflow_file=workflow_file,
    )
    artifact_name = readiness["artifact_name"]
    return {
        "window_id": window_id,
        "mode": mode,
        "environment_name": environment_name,
        "workflow_name": workflow_name,
        "workflow_file": str(workflow_file),
        "artifact_name": artifact_name,
        "weekly_file": readiness.get("weekly_file", "pending"),
        "signoff_file": readiness.get("signoff_file", "pending"),
        "readiness": readiness,
        "commands": {
            "preflight": f'make preflight-serious-window-dispatch WINDOW_ID="{window_id}" MODE="{mode}" ENVIRONMENT_NAME="{environment_name}"',
            "postprocess_dry_run": 'make postprocess-serious-window-dry-run RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"',
            "postprocess": 'make postprocess-serious-window RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"',
        },
        "manual_steps": [
            f"Abrir o workflow `{workflow_name}` no GitHub Actions.",
            f"Preencher `window_id={window_id}`, `mode={mode}` e `environment_name={environment_name}`.",
            "Aguardar approvals do GitHub Environment antes da execução.",
            f"Baixar o artifact `{artifact_name}` ao final do run.",
        ],
    }


def render_dispatch_packet_markdown(model: dict[str, Any]) -> str:
    readiness = model["readiness"]
    lines = [
        f"# Serious Window Dispatch Packet — `{model['window_id']}`",
        "",
        "> Pacote copy/paste para o disparo real da janela seria e o fechamento imediato do artifact.",
        "",
        "## Identificacao",
        "",
        f"- workflow: `{model['workflow_name']}`",
        f"- window_id: `{model['window_id']}`",
        f"- mode: `{model['mode']}`",
        f"- environment_name: `{model['environment_name']}`",
        f"- artifact esperado: `{model['artifact_name']}`",
        f"- weekly governance: `{model['weekly_file']}`",
        f"- sign-off versionado: `{model['signoff_file']}`",
        "",
        "## Prontidao Atual",
        "",
        f"- status: `{readiness['status']}`",
    ]

    for check in readiness.get("checks", []):
        lines.append(f"- {check['name']}: `{check['status']}` - {check['details']}")

    if readiness.get("errors"):
        lines.extend(["", "## Erros", ""])
        lines.extend(f"- {error}" for error in readiness["errors"])

    lines.extend(
        [
            "",
            "## Comandos",
            "",
            "```bash",
            model["commands"]["preflight"],
            model["commands"]["postprocess_dry_run"],
            model["commands"]["postprocess"],
            "```",
            "",
            "## Passos Manuais no GitHub Actions",
            "",
        ]
    )
    for index, step in enumerate(model["manual_steps"], start=1):
        lines.append(f"{index}. {step}")

    lines.extend(
        [
            "",
            "## Fechamento Esperado",
            "",
            f"- revisar `{model['signoff_file']}`",
            f"- revisar `{model['weekly_file']}`",
            f"- confirmar o artifact `{model['artifact_name']}` referenciado no sign-off",
            "",
            "## Proximos Passos Sugeridos",
            "",
        ]
    )
    lines.extend(f"- {step}" for step in readiness.get("next_steps", []))
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um pacote copy/paste do disparo real da janela seria."
    )
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--mode", default="baseline")
    parser.add_argument("--environment-name", default="staging-serious")
    parser.add_argument("--governance-weekly-dir", default=str(DEFAULT_GOVERNANCE_WEEKLY_DIR))
    parser.add_argument("--workflow-file", default=str(DEFAULT_WORKFLOW_FILE))
    parser.add_argument("--workflow-name", default="Staging Serious Window")
    parser.add_argument("--output-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = build_dispatch_packet_model(
        window_id=args.window_id,
        mode=args.mode,
        environment_name=args.environment_name,
        governance_weekly_dir=Path(args.governance_weekly_dir),
        workflow_file=Path(args.workflow_file),
        workflow_name=args.workflow_name,
    )
    markdown = render_dispatch_packet_markdown(model)
    output_file = Path(args.output_file) if args.output_file else None
    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        sys.stdout.write(
            json.dumps(
                {
                    "kind": "serious_window_dispatch_packet",
                    "status": "ok" if model["readiness"]["status"] == "ok" else "warning",
                    "window_id": model["window_id"],
                    "output_file": str(output_file),
                    "artifact_name": model["artifact_name"],
                    "readiness_status": model["readiness"]["status"],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 0

    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
