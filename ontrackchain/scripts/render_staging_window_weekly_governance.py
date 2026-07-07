#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_window_date(window_id: str) -> str:
    match = re.fullmatch(r"stg-(\d{4}-\d{2}-\d{2})-[a-z0-9]+", window_id)
    if not match:
        raise ValueError(f"window_id_invalido_para_governanca: {window_id}")
    return match.group(1)


def default_weekly_file(window_id: str, governance_weekly_dir: Path) -> Path:
    window_date = extract_window_date(window_id)
    return governance_weekly_dir / "cycles" / window_date / f"{window_date}-weekly-governance.md"


def safe_get_step(step_payload: dict[str, Any], step_name: str) -> dict[str, Any]:
    return (step_payload.get("steps") or {}).get(step_name) or {}


def safe_get_value(value: Any, *, default: str = "pending") -> str:
    if value in (None, ""):
        return default
    return str(value)


def replace_line(lines: list[str], prefix: str, new_line: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = new_line
            return
    raise ValueError(f"linha_nao_encontrada: {prefix}")


def replace_after_anchor(lines: list[str], anchor_prefix: str, relative_prefix: str, new_line: str) -> None:
    for index, line in enumerate(lines):
        if line.startswith(anchor_prefix):
            for nested_index in range(index + 1, len(lines)):
                current = lines[nested_index]
                if current.startswith("- ID: `") and nested_index > index + 1:
                    break
                if current.startswith(relative_prefix):
                    lines[nested_index] = new_line
                    return
            raise ValueError(f"linha_relativa_nao_encontrada: {anchor_prefix} -> {relative_prefix}")
    raise ValueError(f"ancora_nao_encontrada: {anchor_prefix}")


def build_weekly_sync_model(
    *,
    payload: dict[str, Any],
    payload_file: Path,
    run_url: str,
) -> dict[str, str]:
    window_id = safe_get_value(payload.get("window_id"), default="unknown-window")
    mode = safe_get_value(payload.get("mode"))
    environment_name = safe_get_value(payload.get("environment_name"), default="staging-serious")
    overall_status = safe_get_value(payload.get("status"))
    validation_status = safe_get_value((payload.get("validation") or {}).get("status"))
    preflight_status = safe_get_value((payload.get("preflight") or {}).get("status"))
    run_status = safe_get_value((payload.get("run") or {}).get("status"))

    run_payload = (payload.get("run") or {}).get("payload") or {}
    release_dossier = safe_get_step(run_payload, "release_dossier")
    homologation = safe_get_step(run_payload, "homologation")
    regulatory_bundle = safe_get_step(run_payload, "regulatory_readiness_bundle")
    artifact_name = f"serious-staging-window-{window_id}"
    artifact_ref = f"artifact `{artifact_name}`"

    if overall_status == "ok" and validation_status == "ok" and preflight_status == "ok" and run_status == "ok":
        run_stg_status = "done"
        next_evidence = "sign-off humano com aprovadores preenchidos e decisao final `approved`"
    elif overall_status == "failed":
        run_stg_status = "blocked"
        next_evidence = "registro do ponto de falha e owner da escalacao"
    else:
        run_stg_status = "pending_execucao"
        next_evidence = "sign-off preenchido com links, status e aprovadores humanos"

    return {
        "window_id": window_id,
        "mode": mode,
        "environment_name": environment_name,
        "run_url": run_url or "pending",
        "artifact_name": artifact_name,
        "artifact_ref": artifact_ref,
        "overall_status": overall_status,
        "validation_status": validation_status,
        "preflight_status": preflight_status,
        "run_status": run_status,
        "window_packet_path": safe_get_value((payload.get("artifacts") or {}).get("window_packet_file")),
        "dossier_path": safe_get_value(release_dossier.get("artifact_file")),
        "homologation_path": safe_get_value(homologation.get("artifact_file")),
        "regulatory_bundle_path": safe_get_value(regulatory_bundle.get("output_file")),
        "run_stg_status": run_stg_status,
        "next_evidence": next_evidence,
        "payload_json_path": str(payload_file),
    }


def update_weekly_governance_markdown(content: str, model: dict[str, str]) -> str:
    lines = content.splitlines()
    replace_line(lines, "- `window_id`:", f"- `window_id`: `{model['window_id']}`")
    replace_line(lines, "- `mode`:", f"- `mode`: `{model['mode']}`")
    replace_line(lines, "- `environment_name`:", f"- `environment_name`: `{model['environment_name']}`")
    replace_line(lines, "- run do GitHub Actions:", f"- run do GitHub Actions: `{model['run_url']}`")
    replace_line(lines, "- artifact `serious-staging-window-", f"- artifact `{model['artifact_name']}`: `{model['artifact_ref']}`")
    replace_line(lines, "- overall status:", f"- overall status: `{model['overall_status']}`")
    replace_line(lines, "- validation status:", f"- validation status: `{model['validation_status']}`")
    replace_line(lines, "- preflight status:", f"- preflight status: `{model['preflight_status']}`")
    replace_line(lines, "- run status:", f"- run status: `{model['run_status']}`")
    replace_line(lines, "- window packet:", f"- window packet: `{model['window_packet_path']}`")
    replace_line(lines, "- dossier:", f"- dossier: `{model['dossier_path']}`")
    replace_line(lines, "- homologation:", f"- homologation: `{model['homologation_path']}`")
    try:
        replace_line(
            lines,
            "- regulatory-readiness-bundle:",
            f"- regulatory-readiness-bundle: `{model['regulatory_bundle_path']}`",
        )
    except ValueError:
        for index, line in enumerate(lines):
            if line.startswith("- homologation:"):
                lines.insert(
                    index + 1,
                    f"- regulatory-readiness-bundle: `{model['regulatory_bundle_path']}`",
                )
                break

    replace_after_anchor(lines, "- ID: `RUN-STG-01`", "  - status atual:", f"  - status atual: `{model['run_stg_status']}`")
    replace_after_anchor(
        lines,
        "- ID: `RUN-STG-01`",
        "  - artefato revisado:",
        f"  - artefato revisado: workflow `Staging Serious Window` + {model['artifact_ref']}",
    )
    replace_after_anchor(
        lines,
        "- ID: `RUN-STG-01`",
        "  - próxima evidência esperada:",
        f"  - próxima evidência esperada: {model['next_evidence']}",
    )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sincroniza o registro semanal da janela seria a partir do payload consolidado do prepare_staging_window."
    )
    parser.add_argument("--payload-file", required=True)
    parser.add_argument("--weekly-file")
    parser.add_argument("--governance-weekly-dir")
    parser.add_argument("--run-url", default="pending")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload_file = Path(args.payload_file)

    try:
        payload = load_json_file(payload_file)
        window_id = safe_get_value(payload.get("window_id"), default="unknown-window")
        if args.weekly_file:
            weekly_file = Path(args.weekly_file)
        elif args.governance_weekly_dir:
            weekly_file = default_weekly_file(window_id, Path(args.governance_weekly_dir))
        else:
            raise ValueError("weekly_file_ou_governance_weekly_dir_obrigatorio")

        model = build_weekly_sync_model(payload=payload, payload_file=payload_file, run_url=args.run_url)
        content = weekly_file.read_text(encoding="utf-8")
        updated_content = update_weekly_governance_markdown(content, model)
        weekly_file.write_text(updated_content, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        sys.stderr.write(
            json.dumps(
                {
                    "kind": "staging_window_weekly_governance_render",
                    "status": "failed",
                    "payload_file": str(payload_file),
                    "errors": [str(exc)],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
        return 1

    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_window_weekly_governance_render",
                "status": "ok",
                "payload_file": str(payload_file),
                "weekly_file": str(weekly_file),
                "window_id": model["window_id"],
                "run_stg_status": model["run_stg_status"],
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
