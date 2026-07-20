#!/usr/bin/env python3
from __future__ import annotations

import sys

from run_python_unittest_suite import main as run_suite_main


DEFAULT_ARGS = [
    "--app-dir",
    "apps/compliance-api",
    "--docker-service",
    "compliance-api",
    "--py-compile-file",
    "src/compliance_api/operations.py",
    "--py-compile-file",
    "tests/test_work_item_contracts.py",
    "--module",
    "tests.test_work_item_contracts",
    "--required-import",
    "fastapi",
    "--required-import",
    "pydantic_settings",
    "--required-import",
    "psycopg_pool",
]


def main() -> int:
    return run_suite_main(DEFAULT_ARGS + sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
