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


def _has_minimal_bootstrap(sql: str) -> bool:
    return "create table if not exists organizations" in sql.lower()


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
    init_sql = _read_text(INIT_SQL)
    readme_text = _read_text(README)
    migration_files = _load_migration_files()

    failures: list[str] = []
    if not _has_minimal_bootstrap(init_sql):
        failures.append("init.sql nao contem bootstrap minimo: CREATE TABLE IF NOT EXISTS organizations")

    for migration_file in migration_files:
        if migration_file.name not in readme_text:
            failures.append(f"README nao referencia migration {migration_file.name}")

    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1

    print(f"OK: {len(migration_files)} migrations coerentes e README atualizado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
