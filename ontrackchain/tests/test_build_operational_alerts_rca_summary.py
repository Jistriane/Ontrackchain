import importlib.util
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(
    "build_operational_alerts_rca_summary",
    "scripts/build_operational_alerts_rca_summary.py",
)


class BuildOperationalAlertsRcaSummaryTests(unittest.TestCase):
    def test_build_summary_counts_tracked_items_and_rca(self) -> None:
        payload = {
            "count": 2,
            "data": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "status": "firing",
                    "triage_status": "pending",
                    "severity": "critical",
                    "work_item_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "work_item_queue_status": "READY",
                    "rca_domain": "compliance",
                    "rca_containment_status": "contained",
                    "rca_confirmed_root_cause": "Retry insuficiente",
                    "rca_affected_domains": ["compliance", "monitoring"],
                    "rca_corrective_actions": ["ampliar retry"],
                    "rca_evidence_refs": ["snapshot-1"],
                },
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "status": "resolved",
                    "triage_status": "acknowledged",
                    "severity": "warning",
                    "work_item_id": None,
                    "rca_domain": "",
                    "rca_affected_domains": [],
                    "rca_corrective_actions": [],
                    "rca_evidence_refs": [],
                },
            ],
        }

        result = MODULE.build_summary(window_id="stg-2026-07-13-a", payload=payload)

        self.assertEqual(result["exported_count"], 2)
        self.assertEqual(result["tracked_work_items_count"], 1)
        self.assertEqual(result["rca_attached_count"], 1)
        self.assertEqual(result["confirmed_root_cause_count"], 1)
        self.assertEqual(result["critical_open_count"], 1)
        self.assertEqual(result["pending_triage_count"], 1)
        self.assertEqual(result["acknowledged_count"], 1)
        self.assertEqual(result["ready_queue_count"], 1)
        self.assertEqual(result["top_rca_domains"], ["compliance"])
        self.assertEqual(result["top_affected_domains"], ["compliance", "monitoring"])


if __name__ == "__main__":
    unittest.main()
