#!/usr/bin/env python3
from __future__ import annotations

import argparse
import py_compile
import sys
from pathlib import Path


IGNORED_PARTS = {"__pycache__", ".venv", "venv", "node_modules", ".next", ".git"}


def _iter_python_files(base_path: Path) -> list[Path]:
    if not base_path.exists():
        return []
    candidates: list[Path] = []
    for path in base_path.rglob("*.py"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        candidates.append(path)
    return sorted(candidates)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compila arquivos Python de um app/pacote para validar sintaxe.")
    parser.add_argument("target", help="Diretorio base do app/pacote")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Subdiretorio relativo a incluir. Pode ser repetido. Default: src, tests e scripts se existirem.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    includes = args.include or ["src", "tests", "scripts"]

    python_files: list[Path] = []
    for include in includes:
        python_files.extend(_iter_python_files(target / include))

    # Fallback para pacotes simples onde o codigo fonte fica diretamente no alvo.
    if not python_files:
        python_files = _iter_python_files(target)

    if not python_files:
        sys.stderr.write(f"Nenhum arquivo Python encontrado em {target}\n")
        return 1

    failures: list[str] = []
    for file_path in python_files:
        try:
            py_compile.compile(str(file_path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{file_path}: {exc.msg}")

    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1

    print(f"OK: {len(python_files)} arquivos Python compilados em {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
