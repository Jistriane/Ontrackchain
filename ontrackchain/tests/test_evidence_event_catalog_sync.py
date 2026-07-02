from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
AGENTS_SRC_DIR = ROOT_DIR / "packages/agents/src"

if str(AGENTS_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_SRC_DIR))


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


EVIDENCE_TRAIL = _load_module(
    "evidence_trail_module",
    "packages/agents/src/ontrackchain_agents/evidence_trail.py",
)
EVIDENCE_INTEGRATION = _load_module(
    "evidence_integration_module",
    "packages/agents/src/ontrackchain_agents/evidence_integration.py",
)
MIGRATION_PATH = ROOT_DIR / "infra/postgres/migrations/0009_evidence_trail.sql"


def _extract_migration_event_types() -> set[str]:
    text = MIGRATION_PATH.read_text(encoding="utf-8")
    comment_lines: list[str] = []
    capture = False

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "-- Valores válidos:":
            capture = True
            continue
        if capture and stripped.startswith("event_type"):
            break
        if capture and stripped.startswith("--   "):
            comment_lines.append(stripped)

    event_types: set[str] = set()
    for line in comment_lines:
        event_types.update(re.findall(r"\b[A-Z][A-Z0-9_]+\b", line))
    return event_types


class EvidenceEventCatalogSyncTests(unittest.TestCase):
    maxDiff = None

    def test_evidence_trail_and_integration_catalogs_match_exactly(self) -> None:
        self.assertSetEqual(
            EVIDENCE_TRAIL.EVIDENCE_EVENT_TYPES,
            EVIDENCE_INTEGRATION.VALID_EVENT_TYPES,
        )

    def test_migration_comment_catalog_matches_runtime_catalog(self) -> None:
        self.assertSetEqual(
            EVIDENCE_TRAIL.EVIDENCE_EVENT_TYPES,
            _extract_migration_event_types(),
        )

    def test_new_coaf_events_are_present_across_all_catalogs(self) -> None:
        required = {
            "COAF_ROS_REJECTED",
            "COAF_ROS_SUBMITTED_MANUAL",
        }

        self.assertTrue(required.issubset(EVIDENCE_TRAIL.EVIDENCE_EVENT_TYPES))
        self.assertTrue(required.issubset(EVIDENCE_INTEGRATION.VALID_EVENT_TYPES))
        self.assertTrue(required.issubset(_extract_migration_event_types()))


if __name__ == "__main__":
    unittest.main()
