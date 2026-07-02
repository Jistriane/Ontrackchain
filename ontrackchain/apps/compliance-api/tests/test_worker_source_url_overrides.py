from __future__ import annotations

import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR.parents[1] / "packages" / "agents" / "src"))

WORKER_DEPS_AVAILABLE = all(
    importlib.util.find_spec(module_name) is not None
    for module_name in ("pydantic_settings", "psycopg", "psycopg_pool")
)

if WORKER_DEPS_AVAILABLE:
    worker_module: Any = importlib.import_module("compliance_api.worker")
else:
    worker_module = None


class _FakeCursor:
    def __init__(self, *, rowcount: int) -> None:
        self.rowcount = rowcount
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        self.executed.append((query, params))

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeConnection:
    def __init__(self, *, rowcount: int) -> None:
        self._cursor = _FakeCursor(rowcount=rowcount)
        self.commit = MagicMock()

    def cursor(self) -> _FakeCursor:
        return self._cursor


@unittest.skipUnless(WORKER_DEPS_AVAILABLE, "worker dependencies not installed in current interpreter")
class WorkerSourceUrlOverrideTests(unittest.TestCase):
    def test_apply_source_url_override_persists_and_commits_when_value_changes(self) -> None:
        conn = _FakeConnection(rowcount=1)
        worker = worker_module.ComplianceWorker.__new__(worker_module.ComplianceWorker)

        worker._apply_source_url_override(
            conn,
            list_name="EU_CONSOLIDATED",
            source_url=" https://token.example/eu.xml ",
        )

        self.assertEqual(len(conn._cursor.executed), 1)
        _, params = conn._cursor.executed[0]
        self.assertEqual(
            params,
            (
                "https://token.example/eu.xml",
                "EU_CONSOLIDATED",
                "https://token.example/eu.xml",
            ),
        )
        conn.commit.assert_called_once()

    def test_apply_source_url_override_is_noop_for_blank_value(self) -> None:
        conn = _FakeConnection(rowcount=1)
        worker = worker_module.ComplianceWorker.__new__(worker_module.ComplianceWorker)

        worker._apply_source_url_override(
            conn,
            list_name="EU_CONSOLIDATED",
            source_url="   ",
        )

        self.assertEqual(conn._cursor.executed, [])
        conn.commit.assert_not_called()

    def test_apply_source_url_override_skips_commit_when_url_is_already_current(self) -> None:
        conn = _FakeConnection(rowcount=0)
        worker = worker_module.ComplianceWorker.__new__(worker_module.ComplianceWorker)

        worker._apply_source_url_override(
            conn,
            list_name="OFAC_SDN",
            source_url="https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML",
        )

        self.assertEqual(len(conn._cursor.executed), 1)
        conn.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
