#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_FILE = "docs/staging-env-ownership.md"
DEFAULT_REQUIRED_GROUPS = [
    "Auth/OIDC",
    "Compliance/AML",
    "Investigation/RPC",
    "Platform/Operations",
]
VALID_STATUSES = {"approved", "reviewed", "waived"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _clean_cell(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) >= 2:
        cleaned = cleaned[1:-1]
    return cleaned.strip()


def parse_handoff_rows(file_path: Path) -> list[dict[str, str]]:
    lines = file_path.read_text(encoding="utf-8").splitlines()

    section_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == "## Registro de Handoff":
            section_index = index
            break

    if section_index is None:
        raise ValueError("secao_ausente: Registro de Handoff")

    table_lines: list[str] = []
    for line in lines[section_index + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("|"):
            table_lines.append(stripped)

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


def build_payload(*, file_path: Path, required_groups: list[str]) -> tuple[int, dict]:
    if not file_path.exists():
        payload = {
            "kind": "staging_env_handoff_check",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "file": str(file_path),
            "status": "failed",
            "errors": [f"arquivo_ausente: {file_path}"],
            "required_groups": required_groups,
            "missing_groups": required_groups,
            "incomplete_groups": [],
            "invalid_statuses": [],
            "invalid_dates": [],
            "checked_groups_count": 0,
            "groups": [],
        }
        return 1, payload

    try:
        rows = parse_handoff_rows(file_path)
    except ValueError as exc:
        payload = {
            "kind": "staging_env_handoff_check",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "file": str(file_path),
            "status": "failed",
            "errors": [str(exc)],
            "required_groups": required_groups,
            "missing_groups": required_groups,
            "incomplete_groups": [],
            "invalid_statuses": [],
            "invalid_dates": [],
            "checked_groups_count": 0,
            "groups": [],
        }
        return 1, payload

    rows_by_group = {row["group"]: row for row in rows}
    missing_groups = [group for group in required_groups if group not in rows_by_group]

    incomplete_groups: list[dict[str, object]] = []
    invalid_statuses: list[dict[str, str]] = []
    invalid_dates: list[dict[str, str]] = []
    errors: list[str] = []

    for group in required_groups:
        row = rows_by_group.get(group)
        if row is None:
            errors.append(f"grupo_obrigatorio_ausente: {group}")
            continue

        missing_fields = [
            field_name
            for field_name in ("owner", "date", "status")
            if not row[field_name] or row[field_name].lower() == "pending"
        ]

        status = row["status"].lower()
        if status and status not in VALID_STATUSES and status != "pending":
            invalid_statuses.append({"group": group, "status": row["status"]})
            errors.append(f"status_invalido: {group}={row['status']}")

        if status == "waived" and (
            not row["observations"] or row["observations"].lower() == "pending"
        ):
            missing_fields.append("observations")

        if row["date"] and row["date"].lower() != "pending" and not DATE_PATTERN.match(row["date"]):
            invalid_dates.append({"group": group, "date": row["date"]})
            errors.append(f"data_invalida: {group}={row['date']}")

        if missing_fields:
            incomplete_groups.append({"group": group, "missing_fields": missing_fields})
            for field_name in missing_fields:
                errors.append(f"campo_obrigatorio_pendente: {group}.{field_name}")

    payload = {
        "kind": "staging_env_handoff_check",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "file": str(file_path),
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "required_groups": required_groups,
        "missing_groups": missing_groups,
        "incomplete_groups": incomplete_groups,
        "invalid_statuses": invalid_statuses,
        "invalid_dates": invalid_dates,
        "checked_groups_count": len(rows),
        "groups": rows,
    }
    return (0 if not errors else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida o registro de handoff do staging antes dos preflights e da homologacao."
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_FILE,
        help="arquivo markdown com a secao 'Registro de Handoff'",
    )
    parser.add_argument(
        "--require-group",
        action="append",
        default=[],
        help="grupo adicional obrigatorio; pode ser repetido",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_groups = sorted(set(DEFAULT_REQUIRED_GROUPS + args.require_group))
    exit_code, payload = build_payload(
        file_path=Path(args.file),
        required_groups=required_groups,
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
