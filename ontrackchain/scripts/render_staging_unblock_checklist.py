#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DOMAIN_ORDER = ["Auth/OIDC", "Compliance/AML", "Investigation/RPC", "Platform/Operations"]

PLACEHOLDER_DOMAIN_PREFIX: dict[str, str] = {
    "JWT_": "Auth/OIDC",
    "KEYCLOAK_": "Auth/OIDC",
    "MFA_": "Auth/OIDC",
    "COMPLIANCE_": "Compliance/AML",
    "INVESTIGATION_RPC_": "Investigation/RPC",
    "ALERTMANAGER_": "Platform/Operations",
    "GRAFANA_": "Platform/Operations",
    "POSTGRES_": "Platform/Operations",
}

DOMAIN_COMMANDS: dict[str, list[str]] = {
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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def detect_domain_for_placeholder(name: str) -> str:
    for prefix, domain in PLACEHOLDER_DOMAIN_PREFIX.items():
        if name.startswith(prefix):
            return domain
    return "Platform/Operations"


def detect_domain_for_handoff(field_name: str) -> str:
    prefix = field_name.split(".", maxsplit=1)[0]
    if prefix in DOMAIN_ORDER:
        return prefix
    return "Platform/Operations"


def build_domain_map(snapshot: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    blockers = snapshot.get("blockers") or {}
    placeholders = [str(item) for item in blockers.get("unresolved_placeholders") or []]
    handoff = [str(item) for item in blockers.get("missing_handoff_fields") or []]

    grouped: dict[str, dict[str, list[str]]] = {
        domain: {"placeholders": [], "handoff": []} for domain in DOMAIN_ORDER
    }

    for placeholder_name in sorted(placeholders):
        grouped[detect_domain_for_placeholder(placeholder_name)]["placeholders"].append(placeholder_name)

    for handoff_field in sorted(handoff):
        grouped[detect_domain_for_handoff(handoff_field)]["handoff"].append(handoff_field)

    return grouped


def regulatory_summary(snapshot: dict[str, Any]) -> dict[str, str]:
    regulatory = snapshot.get("regulatory") or {}
    return {
        "scope_label": str(regulatory.get("scope_label") or "none"),
        "validation_scope": ",".join(regulatory.get("validation_scope") or []) or "none",
        "p0_04_bundle_readiness": str(regulatory.get("p0_04_bundle_readiness") or "unknown"),
        "promotion_note": str(regulatory.get("promotion_note") or "indisponivel"),
    }


def blocking_summary(snapshot: dict[str, Any]) -> dict[str, str]:
    blocking = snapshot.get("blocking_state") or {}
    return {
        "classification": str(blocking.get("classification") or "unknown"),
        "summary": str(blocking.get("summary") or "indisponivel"),
    }


def render_markdown(window_id: str, snapshot_file: Path, snapshot: dict[str, Any]) -> str:
    blockers = snapshot.get("blockers") or {}
    generated_at = str(snapshot.get("generated_at") or "unknown")
    status = str(snapshot.get("overall_status") or "unknown")
    unresolved_count = int(blockers.get("unresolved_placeholders_count") or 0)
    handoff_count = int(blockers.get("missing_handoff_fields_count") or 0)
    regulatory = regulatory_summary(snapshot)
    blocking = blocking_summary(snapshot)

    grouped = build_domain_map(snapshot)

    lines: list[str] = [
        f"# Checklist de Desbloqueio - {window_id}",
        "",
        "## Resumo",
        "",
        f"- gerado em: `{generated_at}`",
        f"- snapshot fonte: `{snapshot_file}`",
        f"- status geral: `{status}`",
        f"- classificacao dominante: `{blocking['classification']}`",
        f"- resumo do bloqueio dominante: {blocking['summary']}",
        f"- placeholders pendentes: `{unresolved_count}`",
        f"- handoff pendente: `{handoff_count}`",
        f"- escopo regulatorio da tentativa: `{regulatory['scope_label']}`",
        f"- scope validado no gate final: `{regulatory['validation_scope']}`",
        f"- `P0-04` readiness: `{regulatory['p0_04_bundle_readiness']}`",
        f"- leitura regulatoria: {regulatory['promotion_note']}",
        "",
        "## Sequencia Segura (Sem Expor Segredos)",
        "",
        "1. Preencher segredos reais apenas em `.env.staging.private` local e nunca em documentos versionados.",
        "2. Atualizar `docs/staging-env-ownership.md` somente com `date` e `status` por trilha.",
        "3. Executar os comandos sugeridos por trilha e anexar evidencias em `artifacts/staging/checks` e `artifacts/staging/dossiers`.",
        "4. Reexecutar o pacote completo com `make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>`.",
        "5. Confirmar reducao objetiva de bloqueios no delta e no dashboard executivo.",
    ]
    if blocking["classification"] == "regulatory_blocked":
        lines.extend(
            [
                "",
                "## Tratamento do Bloqueio Dominante",
                "",
                f"- bloquear qualquer tentativa de promocao ate resolver: {blocking['summary']}",
                "- priorizar `Compliance/AML` e os insumos reais da trilha regulatoria antes do restante",
            ]
        )

    for domain in DOMAIN_ORDER:
        domain_placeholders = grouped[domain]["placeholders"]
        domain_handoff = grouped[domain]["handoff"]
        commands = DOMAIN_COMMANDS.get(domain) or []

        lines.extend(
            [
                "",
                f"## {domain}",
                "",
                f"- objetivo: reduzir bloqueios da trilha `{domain}`",
                "- placeholders:",
            ]
        )
        if domain == "Compliance/AML":
            lines.append(
                f"- contexto regulatorio: escopo atual `{regulatory['scope_label']}` "
                f"com `P0-04={regulatory['p0_04_bundle_readiness']}`"
            )
            lines.append(f"- classificacao dominante atual: `{blocking['classification']}`")

        if domain_placeholders:
            for name in domain_placeholders:
                lines.append(f"  - [ ] {name}")
        else:
            lines.append("  - [x] nenhum placeholder pendente")

        lines.append("- handoff:")
        if domain_handoff:
            for field_name in domain_handoff:
                lines.append(f"  - [ ] {field_name}")
        else:
            lines.append("  - [x] nenhum campo de handoff pendente")

        lines.append("- comandos de validacao:")
        if commands:
            for command in commands:
                lines.append(f"  - `{command}`")
        else:
            lines.append("  - [ ] definir comando da trilha")

    lines.extend(
        [
            "",
            "## Criterio de Saida",
            "",
            "- `prepare_staging_window`: `ok`",
            "- `run_staging_window`: `ok`",
            "- `validate_serious_window_artifact`: `ok`",
            "- placeholders pendentes: `0`",
            "- handoff pendente: `0`",
            "- se o escopo regulatorio for parcial, nao marcar `P0-04` como fechado",
            "- so considerar promocao oficial de `P0-04` quando `P0-02` e `P0-03` convergirem na mesma trilha revisavel",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera checklist de desbloqueio da janela seria.")
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--snapshot-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_file = Path(args.snapshot_file)
    output_file = Path(args.output_file)

    snapshot = load_json(snapshot_file)
    markdown = render_markdown(args.window_id, snapshot_file, snapshot)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(markdown, encoding="utf-8")

    print(
        json.dumps(
            {
                "kind": "staging_unblock_checklist",
                "status": "ok",
                "window_id": args.window_id,
                "snapshot_file": str(snapshot_file),
                "output_file": str(output_file),
                "blocking_classification": blocking_summary(snapshot).get("classification"),
            },
            ensure_ascii=True,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
