#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_SQL = ROOT / "infra/postgres/init.sql"
MIGRATIONS_DIR = ROOT / "infra/postgres/migrations"
README = MIGRATIONS_DIR / "README.md"
MIGRATION_PATTERN = re.compile(r"^(?P<number>\d{4})_.+\.sql$")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalize_sql(sql: str) -> list[str]:
    cleaned = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    return [statement.strip() for statement in cleaned.split(";") if statement.strip()]


def _extract_contracts(sql: str) -> set[str]:
    contracts: set[str] = set()
    for statement in _normalize_sql(sql):
        normalized = " ".join(statement.split())
        lowered = normalized.lower()

        match = re.match(r"create table if not exists ([a-zA-Z_][a-zA-Z0-9_]*)", lowered)
        if match:
            table_name = match.group(1)
            contracts.add(f"table:{table_name}")
            raw_body_match = re.search(
                r"create table if not exists [a-zA-Z_][a-zA-Z0-9_]*\s*\((.*)\)\s*$",
                statement,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if raw_body_match:
                body = raw_body_match.group(1)
                for line in body.splitlines():
                    candidate = line.strip().rstrip(",")
                    if not candidate:
                        continue
                    lowered_candidate = candidate.lower()
                    if lowered_candidate.startswith(("constraint ", "primary key", "foreign key", "unique ", "check ")):
                        continue
                    column_match = re.match(r'("?)([a-zA-Z_][a-zA-Z0-9_]*)\1\s+', candidate)
                    if column_match:
                        contracts.add(f"column:{table_name}.{column_match.group(2).lower()}")

        match = re.match(r"create (?:unique )?index if not exists ([a-zA-Z_][a-zA-Z0-9_]*)", lowered)
        if match:
            contracts.add(f"index:{match.group(1)}")

        match = re.match(r"alter table ([a-zA-Z_][a-zA-Z0-9_]*) enable row level security", lowered)
        if match:
            contracts.add(f"rls:{match.group(1)}")

        match = re.match(r"create policy ([a-zA-Z_][a-zA-Z0-9_]*) on ([a-zA-Z_][a-zA-Z0-9_]*)", lowered)
        if match:
            contracts.add(f"policy:{match.group(2)}.{match.group(1)}")

        alter_match = re.match(r"alter table ([a-zA-Z_][a-zA-Z0-9_]*) ", lowered)
        if alter_match:
            table_name = alter_match.group(1)
            for column_name in re.findall(r"add column if not exists ([a-zA-Z_][a-zA-Z0-9_]*)", lowered):
                contracts.add(f"column:{table_name}.{column_name}")

    return contracts


def _load_migration_files() -> list[Path]:
    migration_files = sorted(path for path in MIGRATIONS_DIR.glob("*.sql") if path.name != "init.sql")
    invalid_names = [path.name for path in migration_files if MIGRATION_PATTERN.match(path.name) is None]
    if invalid_names:
        raise AssertionError(f"Arquivos de migration com nome invalido: {', '.join(invalid_names)}")

    expected_number = 1
    for path in migration_files:
        match = MIGRATION_PATTERN.match(path.name)
        assert match is not None
        current_number = int(match.group("number"))
        if current_number != expected_number:
            raise AssertionError(
                f"Sequencia de migrations quebrada: esperado {expected_number:04d}, encontrado {path.name}"
            )
        expected_number += 1
    return migration_files


def main() -> int:
    init_contracts = _extract_contracts(_read_text(INIT_SQL))
    readme_text = _read_text(README)
    migration_files = _load_migration_files()

    failures: list[str] = []
    for migration_file in migration_files:
        if migration_file.name not in readme_text:
            failures.append(f"README nao referencia migration {migration_file.name}")

        migration_contracts = _extract_contracts(_read_text(migration_file))
        missing_from_init = sorted(contract for contract in migration_contracts if contract not in init_contracts)
        for missing in missing_from_init:
            failures.append(f"{migration_file.name}: contrato ausente em init.sql -> {missing}")

    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1

    print(f"OK: {len(migration_files)} migrations coerentes com {INIT_SQL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
