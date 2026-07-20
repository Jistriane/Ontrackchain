#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRIVATE_ENV_FILE = REPO_ROOT / ".env.staging.private"
DEFAULT_OWNERSHIP_FILE = REPO_ROOT / "docs" / "staging-env-ownership.md"
DEFAULT_SCOPES = ["p0-02", "p0-03", "p0-04"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def collect_scope_payloads(
    *,
    scopes: list[str],
    private_env_file: Path,
    ownership_file: Path,
) -> dict[str, dict[str, Any]]:
    readiness_module = load_module(
        "check_regulatory_window_readiness",
        "scripts/check_regulatory_window_readiness.py",
    )
    payloads: dict[str, dict[str, Any]] = {}
    for scope in scopes:
        _, payload = readiness_module.build_payload(
            scope=scope,
            private_env_file=private_env_file,
            ownership_file=ownership_file,
        )
        payloads[scope] = payload
    return payloads


def merge_actions(scope_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for scope, payload in scope_payloads.items():
        for action in (payload.get("unblock_actions") or []):
            owner_group = str(action.get("owner_group") or "").strip()
            owner = str(action.get("owner") or "").strip()
            kind = str(action.get("kind") or "").strip()
            key = (owner_group, owner, kind)
            entry = merged.setdefault(
                key,
                {
                    "owner_group": owner_group,
                    "owner": owner,
                    "kind": kind,
                    "scopes": [],
                    "targets": [],
                    "actions": [],
                },
            )
            entry["scopes"] = unique_preserve_order(
                [*entry["scopes"], scope]
            )
            entry["targets"] = unique_preserve_order(
                [
                    *entry["targets"],
                    *[
                        str(target)
                        for target in (action.get("targets") or [])
                        if str(target).strip()
                    ],
                ]
            )
            action_text = str(action.get("action") or "").strip()
            if action_text:
                entry["actions"] = unique_preserve_order([*entry["actions"], action_text])
    return list(merged.values())


def build_payload(
    *,
    window_id: str,
    scopes: list[str],
    private_env_file: Path,
    ownership_file: Path,
) -> dict[str, Any]:
    scope_payloads = collect_scope_payloads(
        scopes=scopes,
        private_env_file=private_env_file,
        ownership_file=ownership_file,
    )
    blocked_scopes = [
        scope
        for scope, payload in scope_payloads.items()
        if ((payload.get("readiness") or {}).get("readiness_status") or "blocked") == "blocked"
    ]
    merged_actions = merge_actions(scope_payloads)

    all_blockers = unique_preserve_order(
        [
            str(blocker)
            for payload in scope_payloads.values()
            for blocker in (((payload.get("readiness") or {}).get("blockers")) or [])
            if str(blocker).strip()
        ]
    )
    blocking_summaries = {
        scope: str(payload.get("blocking_summary") or "").strip()
        for scope, payload in scope_payloads.items()
    }

    next_steps = unique_preserve_order(
        [
            str((payload.get("readiness") or {}).get("next_action") or "").strip()
            for payload in scope_payloads.values()
        ]
    )

    dominant_classification = (
        "regulatory_blocked"
        if blocked_scopes
        else "pending_execution"
    )
    status = "failed" if blocked_scopes else "ok"
    return {
        "kind": "regulatory_unblock_checklist",
        "generated_at": utc_now().isoformat(),
        "window_id": window_id,
        "status": status,
        "blocking_classification": dominant_classification,
        "files": {
            "private_env_file": str(private_env_file),
            "ownership_file": str(ownership_file),
        },
        "summary": {
            "scopes_checked": scopes,
            "blocked_scopes": blocked_scopes,
            "blocked_scopes_count": len(blocked_scopes),
            "owner_action_groups_count": len(merged_actions),
            "dominant_blocking_summary": (
                "Todos os escopos regulatórios seguem bloqueados por handoff pendente e/ou variáveis reais ausentes."
                if blocked_scopes
                else "Escopos regulatórios prontos para execução."
            ),
        },
        "scope_summaries": blocking_summaries,
        "owner_actions": merged_actions,
        "next_steps": next_steps,
        "blockers": all_blockers,
        "scopes": scope_payloads,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    files = payload.get("files") or {}
    lines = [
        f"# Regulatory Unblock Checklist - {payload.get('window_id')}",
        "",
        "## Resumo",
        "",
        f"- gerado em: `{payload.get('generated_at')}`",
        f"- status: `{payload.get('status')}`",
        f"- classificacao dominante: `{payload.get('blocking_classification')}`",
        f"- escopos verificados: `{', '.join(summary.get('scopes_checked') or [])}`",
        f"- escopos bloqueados: `{', '.join(summary.get('blocked_scopes') or []) or 'none'}`",
        f"- arquivo privado: `{files.get('private_env_file')}`",
        f"- ownership file: `{files.get('ownership_file')}`",
        f"- resumo executivo: {summary.get('dominant_blocking_summary')}",
        "",
        "## Leitura por Escopo",
        "",
    ]

    for scope, scope_summary in (payload.get("scope_summaries") or {}).items():
        lines.append(f"- `{scope}`: {scope_summary}")

    lines.extend(["", "## Acoes por Owner", ""])
    owner_actions = payload.get("owner_actions") or []
    if not owner_actions:
        lines.append("- `none`")
    else:
        for action in owner_actions:
            lines.append(
                f"### {action.get('owner_group')} - {action.get('owner')}"
            )
            lines.append("")
            lines.append(f"- tipo: `{action.get('kind')}`")
            lines.append(f"- escopos: `{', '.join(action.get('scopes') or [])}`")
            targets = action.get("targets") or []
            lines.append(f"- targets: `{', '.join(targets) if targets else 'none'}`")
            for action_text in (action.get("actions") or []):
                lines.append(f"- acao: {action_text}")
            lines.append("")

    lines.extend(["## Proximos Passos", ""])
    for item in (payload.get("next_steps") or []):
        lines.append(f"- {item}")

    lines.extend(["", "## Bloqueios Consolidados", ""])
    blockers = payload.get("blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- `none`")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolida um checklist de desbloqueio regulatorio a partir dos gates p0-02/p0-03/p0-04."
    )
    parser.add_argument("--window-id", default=f"stg-{utc_now().strftime('%Y-%m-%d')}-reg")
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--ownership-file", default=str(DEFAULT_OWNERSHIP_FILE))
    parser.add_argument("--scope", action="append", dest="scopes", default=[])
    parser.add_argument("--json-output-file")
    parser.add_argument("--markdown-output-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scopes = args.scopes or list(DEFAULT_SCOPES)
    payload = build_payload(
        window_id=args.window_id,
        scopes=scopes,
        private_env_file=Path(args.private_env_file),
        ownership_file=Path(args.ownership_file),
    )

    if args.json_output_file:
        json_output_file = Path(args.json_output_file)
        json_output_file.parent.mkdir(parents=True, exist_ok=True)
        json_output_file.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.markdown_output_file:
        markdown_output_file = Path(args.markdown_output_file)
        markdown_output_file.parent.mkdir(parents=True, exist_ok=True)
        markdown_output_file.write_text(
            render_markdown(payload),
            encoding="utf-8",
        )

    output = sys.stdout if payload["status"] == "ok" else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
