#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"__FILL_[A-Z0-9_]+__")
OWNERSHIP_SECTION_HEADER = "## Matriz de Ownership"
DEFAULT_ENV_FILE = ".env.staging.example"
DEFAULT_OWNERSHIP_FILE = "docs/staging-env-ownership.md"


def extract_placeholders_from_env(file_path: Path) -> list[str]:
    placeholders: set[str] = set()
    for line in file_path.read_text(encoding="utf-8").splitlines():
        placeholders.update(PLACEHOLDER_PATTERN.findall(line))
    return sorted(placeholders)


def _clean_cell(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) >= 2:
        cleaned = cleaned[1:-1]
    return cleaned.strip()


def parse_ownership_matrix(file_path: Path) -> list[dict[str, str]]:
    lines = file_path.read_text(encoding="utf-8").splitlines()

    section_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == OWNERSHIP_SECTION_HEADER:
            section_index = index
            break

    if section_index is None:
        raise ValueError(f"secao_ausente: {OWNERSHIP_SECTION_HEADER}")

    table_lines: list[str] = []
    for line in lines[section_index + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if stripped.startswith("|"):
            table_lines.append(stripped)

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


def build_payload(*, env_file: Path, ownership_file: Path) -> tuple[int, dict]:
    errors: list[str] = []

    if not env_file.exists():
        errors.append(f"arquivo_env_ausente: {env_file}")
    if not ownership_file.exists():
        errors.append(f"arquivo_ownership_ausente: {ownership_file}")

    if errors:
        payload = {
            "kind": "staging_env_ownership_coverage_check",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "env_file": str(env_file),
            "ownership_file": str(ownership_file),
            "status": "failed",
            "errors": errors,
            "env_placeholders": [],
            "matrix_placeholders": [],
            "missing_in_matrix": [],
            "stale_in_matrix": [],
            "incomplete_mappings": [],
            "checked_placeholders_count": 0,
        }
        return 1, payload

    env_placeholders = extract_placeholders_from_env(env_file)
    try:
        matrix_rows = parse_ownership_matrix(ownership_file)
    except ValueError as exc:
        payload = {
            "kind": "staging_env_ownership_coverage_check",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "env_file": str(env_file),
            "ownership_file": str(ownership_file),
            "status": "failed",
            "errors": [str(exc)],
            "env_placeholders": env_placeholders,
            "matrix_placeholders": [],
            "missing_in_matrix": env_placeholders,
            "stale_in_matrix": [],
            "incomplete_mappings": [],
            "checked_placeholders_count": len(env_placeholders),
        }
        return 1, payload

    matrix_by_placeholder = {row["placeholder"]: row for row in matrix_rows}
    matrix_placeholders = sorted(matrix_by_placeholder)

    missing_in_matrix = [placeholder for placeholder in env_placeholders if placeholder not in matrix_by_placeholder]
    stale_in_matrix = [placeholder for placeholder in matrix_placeholders if placeholder not in env_placeholders]

    incomplete_mapping_entries: list[tuple[str, list[str]]] = []
    for placeholder in env_placeholders:
        row = matrix_by_placeholder.get(placeholder)
        if row is None:
            continue
        missing_fields = [
            field_name
            for field_name in ("owner", "support", "evidence")
            if not row[field_name] or row[field_name].lower() == "pending"
        ]
        if missing_fields:
            incomplete_mapping_entries.append((placeholder, missing_fields))

    if missing_in_matrix:
        errors.extend([f"placeholder_sem_owner: {placeholder}" for placeholder in missing_in_matrix])
    if stale_in_matrix:
        errors.extend([f"placeholder_obsoleto_na_matriz: {placeholder}" for placeholder in stale_in_matrix])
    for placeholder, missing_fields in incomplete_mapping_entries:
        for field_name in missing_fields:
            errors.append(f"campo_owner_pendente: {placeholder}.{field_name}")

    incomplete_mappings = [
        {
            "placeholder": placeholder,
            "missing_fields": missing_fields,
        }
        for placeholder, missing_fields in incomplete_mapping_entries
    ]

    payload = {
        "kind": "staging_env_ownership_coverage_check",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "env_file": str(env_file),
        "ownership_file": str(ownership_file),
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "env_placeholders": env_placeholders,
        "matrix_placeholders": matrix_placeholders,
        "missing_in_matrix": missing_in_matrix,
        "stale_in_matrix": stale_in_matrix,
        "incomplete_mappings": incomplete_mappings,
        "checked_placeholders_count": len(env_placeholders),
    }
    return (0 if not errors else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida se todos os placeholders do .env.staging.example possuem ownership explicito."
    )
    parser.add_argument(
        "--env-file",
        default=DEFAULT_ENV_FILE,
        help="arquivo de ambiente baseline a comparar",
    )
    parser.add_argument(
        "--ownership-file",
        default=DEFAULT_OWNERSHIP_FILE,
        help="arquivo markdown com a matriz de ownership",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code, payload = build_payload(
        env_file=Path(args.env_file),
        ownership_file=Path(args.ownership_file),
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
