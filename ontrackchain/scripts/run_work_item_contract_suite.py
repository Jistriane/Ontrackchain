#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_TEST_MODULES = [
    "tests.test_work_item_contracts",
]

DEFAULT_PY_COMPILE_FILES = [
    "src/compliance_api/operations.py",
    "tests/test_work_item_contracts.py",
]


def _run(command: list[str], *, cwd: Path) -> int:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=str(cwd), check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Roda a suite de contrato de work-items do compliance-api com validacao sintatica previa."
    )
    parser.add_argument(
        "--app-dir",
        default="apps/compliance-api",
        help="Diretorio do compliance-api relativo a raiz do repositorio.",
    )
    parser.add_argument(
        "--skip-py-compile",
        action="store_true",
        help="Pula a etapa de py_compile.",
    )
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        default=[],
        help="Modulo unittest adicional. Pode ser repetido.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    app_dir = (repo_root / args.app_dir).resolve()
    if not app_dir.exists():
        sys.stderr.write(f"Diretorio do app nao encontrado: {app_dir}\n")
        return 1

    modules = DEFAULT_TEST_MODULES + args.modules
    if not args.skip_py_compile:
        py_compile_command = [
            "python3",
            "-m",
            "py_compile",
            *DEFAULT_PY_COMPILE_FILES,
        ]
        exit_code = _run(py_compile_command, cwd=app_dir)
        if exit_code != 0:
            return exit_code

    unittest_command = [
        "python3",
        "-m",
        "unittest",
        *modules,
    ]
    return _run(unittest_command, cwd=app_dir)


if __name__ == "__main__":
    raise SystemExit(main())
