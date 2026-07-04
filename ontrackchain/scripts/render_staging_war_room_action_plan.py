#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DOMAIN_ORDER = [
    "Auth/OIDC",
    "Compliance/AML",
    "Investigation/RPC",
    "Platform/Operations",
]

PLACEHOLDER_DOMAIN_RULES = {
    "Auth/OIDC": (
        "KEYCLOAK_",
        "JWT_",
        "MFA_",
        "OIDC_",
    ),
    "Compliance/AML": (
        "COMPLIANCE_",
    ),
    "Investigation/RPC": (
        "INVESTIGATION_RPC_",
    ),
    "Platform/Operations": (
        "POSTGRES_",
        "GRAFANA_",
        "ALERTMANAGER_",
    ),
}

DOMAIN_COMMANDS = {
    "Auth/OIDC": [
        "python scripts/preflight_oidc_serious_env.py",
        "python scripts/smoke_auth_oidc_mode.py",
    ],
    "Compliance/AML": [
        "make check-compliance-provider-runtime",
        "make run-eu-sanctions-window-local WINDOW_ID=<window_id>",
    ],
    "Investigation/RPC": [
        "python scripts/preflight_external_integrations.py",
    ],
    "Platform/Operations": [
        "python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md",
        "python scripts/check_staging_env_placeholders.py --file .env.staging.private",
    ],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def resolve_file(checks_dir: Path, canonical: str, legacy: str | None = None) -> Path:
    preferred = checks_dir / canonical
    if preferred.exists():
        return preferred
    if legacy:
        legacy_path = checks_dir / legacy
        if legacy_path.exists():
            return legacy_path
    return preferred


def detect_domain_from_placeholder(name: str) -> str:
    for domain, prefixes in PLACEHOLDER_DOMAIN_RULES.items():
        if any(name.startswith(prefix) for prefix in prefixes):
            return domain
    return "Platform/Operations"


def build_model(window_id: str, checks_dir: Path) -> dict[str, Any]:
    placeholders_file = resolve_file(
        checks_dir,
        f"placeholders-{window_id}.json",
        f"{window_id}-placeholders.json",
    )
    handoff_file = resolve_file(
        checks_dir,
        f"handoff-{window_id}.json",
        f"{window_id}-handoff.json",
    )

    placeholders_payload = load_json(placeholders_file)
    handoff_payload = load_json(handoff_file)

    by_domain: dict[str, dict[str, Any]] = {
        domain: {
            "placeholders": [],
            "handoff_missing_fields": [],
            "commands": DOMAIN_COMMANDS[domain],
        }
        for domain in DOMAIN_ORDER
    }

    for item in placeholders_payload.get("unresolved_placeholders", []):
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        domain = detect_domain_from_placeholder(name)
        by_domain[domain]["placeholders"].append(name)

    for item in handoff_payload.get("incomplete_groups", []):
        group = str(item.get("group") or "").strip()
        missing = item.get("missing_fields") or []
        if group in by_domain:
            by_domain[group]["handoff_missing_fields"].extend([str(field) for field in missing])

    for domain in DOMAIN_ORDER:
        by_domain[domain]["placeholders"] = sorted(set(by_domain[domain]["placeholders"]))
        by_domain[domain]["handoff_missing_fields"] = sorted(set(by_domain[domain]["handoff_missing_fields"]))

    return {
        "kind": "staging_war_room_action_plan",
        "window_id": window_id,
        "generated_at": utc_now_iso(),
        "checks_dir": str(checks_dir),
        "sources": {
            "placeholders": str(placeholders_file),
            "handoff": str(handoff_file),
        },
        "domains": by_domain,
    }


def render_markdown(model: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Plano de Acao do War Room - {model['window_id']}")
    lines.append("")
    lines.append(f"- gerado em: `{model['generated_at']}`")
    lines.append(f"- checks_dir: `{model['checks_dir']}`")
    lines.append(f"- fonte placeholders: `{model['sources']['placeholders']}`")
    lines.append(f"- fonte handoff: `{model['sources']['handoff']}`")
    lines.append("")

    domains = model["domains"]
    for domain in DOMAIN_ORDER:
        payload = domains[domain]
        lines.append(f"## {domain}")
        lines.append("")

        lines.append("- placeholders pendentes:")
        if payload["placeholders"]:
            for placeholder in payload["placeholders"]:
                lines.append(f"  - `{placeholder}`")
        else:
            lines.append("  - `none`")

        lines.append("- handoff pendente:")
        if payload["handoff_missing_fields"]:
            for field in payload["handoff_missing_fields"]:
                lines.append(f"  - `{field}`")
        else:
            lines.append("  - `none`")

        lines.append("- comandos sugeridos:")
        for command in payload["commands"]:
            lines.append(f"  - `{command}`")
        lines.append("")

    lines.append("## Fechamento")
    lines.append("")
    lines.append("- atualizar `docs/staging-env-ownership.md` com `date` e `status` nos 4 grupos")
    lines.append(
        f"- rerodar `python scripts/prepare_staging_window.py --window-id {model['window_id']} --mode baseline --private-env-file .env.staging.private --validate --preflight`"
    )
    lines.append(
        f"- se verde, executar `python scripts/run_staging_window.py --window-id {model['window_id']} --private-env-file .env.staging.private`"
    )
    lines.append("")

    normalized: list[str] = []
    for line in lines:
        if line == "" and normalized and normalized[-1] == "":
            continue
        normalized.append(line)
    return "\n".join(normalized).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera plano de acao do war room a partir dos checks da janela.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--checks-dir", default="artifacts/staging/checks")
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks_dir = Path(args.checks_dir)
    output_file = Path(args.output_file)

    model = build_model(args.window_id, checks_dir)
    markdown = render_markdown(model)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "kind": "staging_war_room_action_plan_render",
                "status": "ok",
                "window_id": args.window_id,
                "output_file": str(output_file),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
