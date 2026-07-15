#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"(__FILL_[A-Z0-9_]+__)")
OWNERSHIP_SECTION_HEADER = "## Matriz de Ownership"
HANDOFF_SECTION_HEADER = "## Registro de Handoff"
DEFAULT_ENV_FILE = ".env.staging.example"
DEFAULT_OWNERSHIP_FILE = "docs/staging-env-ownership.md"


def _clean_cell(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) >= 2:
        cleaned = cleaned[1:-1]
    return cleaned.strip()


def parse_env_placeholders(file_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        match = PLACEHOLDER_PATTERN.search(value)
        if match is None:
            continue
        rows.append(
            {
                "variable": key.strip(),
                "placeholder": match.group(1),
            }
        )
    return rows


def _extract_table_lines(lines: list[str], section_header: str) -> list[str]:
    section_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == section_header:
            section_index = index
            break

    if section_index is None:
        raise ValueError(f"secao_ausente: {section_header}")

    table_lines: list[str] = []
    for line in lines[section_index + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("|"):
            table_lines.append(stripped)

    return table_lines


def parse_ownership_matrix(file_path: Path) -> list[dict[str, str]]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    table_lines = _extract_table_lines(lines, OWNERSHIP_SECTION_HEADER)
    if len(table_lines) < 3:
        raise ValueError("tabela_ownership_ausente_ou_incompleta")

    rows: list[dict[str, str]] = []
    for raw_row in table_lines[2:]:
        parts = [_clean_cell(part) for part in raw_row.strip("|").split("|")]
        if len(parts) != 4:
            raise ValueError(f"linha_tabela_invalida: {raw_row}")
        rows.append(
            {
                "placeholder": parts[0],
                "owner": parts[1],
                "support": parts[2],
                "evidence": parts[3],
            }
        )
    return rows


def parse_handoff_rows(file_path: Path) -> list[dict[str, str]]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    table_lines = _extract_table_lines(lines, HANDOFF_SECTION_HEADER)
    if len(table_lines) < 3:
        raise ValueError("tabela_handoff_ausente_ou_incompleta")

    rows: list[dict[str, str]] = []
    for raw_row in table_lines[2:]:
        parts = [_clean_cell(part) for part in raw_row.strip("|").split("|")]
        if len(parts) != 5:
            raise ValueError(f"linha_tabela_invalida: {raw_row}")
        rows.append(
            {
                "group": parts[0],
                "owner": parts[1],
                "date": parts[2],
                "status": parts[3],
                "observations": parts[4],
            }
        )
    return rows


def parse_expected_modes(file_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key in {
            "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE",
            "ONTRACKCHAIN_EXPECT_RPC_MODE",
            "MFA_EXTERNAL_PROVIDER_HOMOLOGATED",
        }:
            values[key] = value.strip()
    return values


def build_packet_model(
    *,
    window_id: str,
    env_file: Path,
    ownership_file: Path,
    generated_at: str,
) -> dict:
    env_rows = parse_env_placeholders(env_file)
    ownership_rows = parse_ownership_matrix(ownership_file)
    handoff_rows = parse_handoff_rows(ownership_file)
    expected_modes = parse_expected_modes(env_file)

    ownership_by_placeholder = {row["placeholder"]: row for row in ownership_rows}

    placeholder_rows: list[dict[str, str]] = []
    for env_row in env_rows:
        ownership_row = ownership_by_placeholder.get(env_row["placeholder"])
        placeholder_rows.append(
            {
                "variable": env_row["variable"],
                "placeholder": env_row["placeholder"],
                "owner": ownership_row["owner"] if ownership_row else "unmapped",
                "support": ownership_row["support"] if ownership_row else "unmapped",
                "evidence": ownership_row["evidence"] if ownership_row else "unmapped",
            }
        )

    rows_by_owner: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in placeholder_rows:
        rows_by_owner[row["owner"]].append(row)

    owners = [
        {
            "owner": owner,
            "items": sorted(items, key=lambda item: item["variable"]),
        }
        for owner, items in sorted(rows_by_owner.items())
    ]

    return {
        "window_id": window_id,
        "generated_at": generated_at,
        "env_file": str(env_file),
        "ownership_file": str(ownership_file),
        "expected_modes": {
            "compliance": expected_modes.get("ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE", "unknown"),
            "rpc": expected_modes.get("ONTRACKCHAIN_EXPECT_RPC_MODE", "unknown"),
        },
        "mfa_external_provider_homologated": expected_modes.get("MFA_EXTERNAL_PROVIDER_HOMOLOGATED", "false"),
        "owners": owners,
        "placeholders": sorted(placeholder_rows, key=lambda item: item["variable"]),
        "handoff": handoff_rows,
        "commands": [
            "python scripts/check_staging_env_ownership_coverage.py --env-file .env.staging.example --ownership-file docs/staging-env-ownership.md",
            "python scripts/check_staging_env_placeholders.py --file .env.staging.private",
            "python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md",
            "python scripts/preflight_oidc_serious_env.py",
            "python scripts/preflight_external_integrations.py",
            "python scripts/homologation_external_evidence.py --mode both "
            f"--rpc-expected-mode {expected_modes.get('ONTRACKCHAIN_EXPECT_RPC_MODE', 'fallback_only')}",
        ],
    }


def render_packet_markdown(model: dict) -> str:
    lines = [
        f"# Staging Window Packet - {model['window_id']}",
        "",
        "## Resumo",
        "",
        f"- Window ID: `{model['window_id']}`",
        f"- Gerado em: `{model['generated_at']}`",
        f"- Baseline: `{model['env_file']}`",
        f"- Ownership: `{model['ownership_file']}`",
        f"- Compliance mode esperado: `{model['expected_modes']['compliance']}`",
        f"- RPC mode esperado: `{model['expected_modes']['rpc']}`",
        f"- MFA federado homologado: `{model['mfa_external_provider_homologated']}`",
        "",
        "## Sequencia Operacional",
        "",
    ]

    for index, command in enumerate(model["commands"], start=1):
        lines.append(f"{index}. `{command}`")

    lines.extend(
        [
            "",
            "## Placeholders por Owner",
            "",
        ]
    )

    for owner_entry in model["owners"]:
        lines.extend(
            [
                f"### {owner_entry['owner']}",
                "",
                "| Variavel | Placeholder | Apoio | Evidencia esperada |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in owner_entry["items"]:
            lines.append(
                f"| `{item['variable']}` | `{item['placeholder']}` | `{item['support']}` | {item['evidence']} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Snapshot do Handoff",
            "",
            "| Grupo | Owner | Data | Status | Observacoes |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in model["handoff"]:
        lines.append(
            f"| {row['group']} | `{row['owner']}` | `{row['date']}` | `{row['status']}` | {row['observations']} |"
        )

    lines.extend(
        [
            "",
            "## Matriz Redigida",
            "",
            "| Variavel | Placeholder | Owner primario | Apoio | Evidencia esperada |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in model["placeholders"]:
        lines.append(
            f"| `{row['variable']}` | `{row['placeholder']}` | `{row['owner']}` | `{row['support']}` | {row['evidence']} |"
        )

    lines.extend(
        [
            "",
            "## Notas",
            "",
            "- Este pacote e redigido: nao inclui secrets nem valores reais de `.env.staging.private`.",
            "- Use este artefato como anexo da janela e como referencia de handoff entre owners.",
            "- Se qualquer owner ou status continuar em `pending`, a janela deve ser bloqueada pelos checkers dedicados.",
            "- `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` so precisa ser resolvido quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`.",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera um packet redigido da janela de staging a partir do baseline e da matriz de ownership."
    )
    parser.add_argument("--window-id", required=True, help="identificador da janela, ex: stg-2026-06-29-a")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="arquivo baseline de staging")
    parser.add_argument(
        "--ownership-file",
        default=DEFAULT_OWNERSHIP_FILE,
        help="arquivo markdown com ownership e handoff",
    )
    parser.add_argument(
        "--output-file",
        help="arquivo markdown de saida; se omitido, escreve em stdout",
    )
    parser.add_argument(
        "--generated-at",
        help="timestamp ISO-8601 para reproducibilidade em testes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()
    model = build_packet_model(
        window_id=args.window_id,
        env_file=Path(args.env_file),
        ownership_file=Path(args.ownership_file),
        generated_at=generated_at,
    )
    markdown = render_packet_markdown(model)
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown + "\n", encoding="utf-8")
        payload = {
            "kind": "staging_window_packet",
            "status": "ok",
            "window_id": args.window_id,
            "output_file": str(output_path),
            "generated_at": generated_at,
            "placeholders_count": len(model["placeholders"]),
            "owners_count": len(model["owners"]),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
        return 0

    sys.stdout.write(markdown + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
