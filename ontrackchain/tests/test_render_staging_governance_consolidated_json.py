import importlib.util
import json
import tempfile
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
    "render_staging_governance_consolidated_json",
    "scripts/render_staging_governance_consolidated_json.py",
)


class RenderStagingGovernanceConsolidatedJsonTests(unittest.TestCase):
    def test_build_consolidated_json_preserves_regulatory_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            checks_dir = base / "artifacts" / "staging" / "checks"
            history_dir = checks_dir / "history"
            docs_dir = base / "docs" / "governance-weekly" / "generated" / "windows" / "stg-2026-07-11-a"
            dossiers_dir = base / "artifacts" / "staging" / "dossiers"
            checks_dir.mkdir(parents=True, exist_ok=True)
            history_dir.mkdir(parents=True, exist_ok=True)
            docs_dir.mkdir(parents=True, exist_ok=True)
            dossiers_dir.mkdir(parents=True, exist_ok=True)

            current_snapshot = {
                "window_id": "stg-2026-07-11-a",
                "overall_status": "failed",
                "regulatory": {
                    "scope_label": "P0-02",
                    "validation_scope": ["P0-01", "P0-02"],
                    "p0_04_bundle_readiness": "ready",
                    "promotion_note": "tentativa parcial (P0-02); endurece a trilha, mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03",
                },
                "operational_incidents": {
                    "status": "available",
                    "exported_count": 4,
                    "tracked_work_items_count": 3,
                    "rca_attached_count": 2,
                    "confirmed_root_cause_count": 1,
                    "critical_open_count": 1,
                    "pending_triage_count": 2,
                    "top_rca_domains": ["compliance", "monitoring"],
                    "top_affected_domains": ["compliance", "monitoring"],
                },
            }
            previous_snapshot = {
                "window_id": "stg-2026-07-11-a",
                "overall_status": "failed",
                "regulatory": {
                    "scope_label": "none",
                    "validation_scope": [],
                    "p0_04_bundle_readiness": "unknown",
                    "promotion_note": "indisponivel",
                },
                "operational_incidents": {
                    "status": "not_available",
                    "exported_count": 0,
                    "tracked_work_items_count": 0,
                    "rca_attached_count": 0,
                    "confirmed_root_cause_count": 0,
                    "critical_open_count": 0,
                    "pending_triage_count": 0,
                    "top_rca_domains": [],
                    "top_affected_domains": [],
                },
            }

            (checks_dir / "stg-2026-07-11-a-status-snapshot.json").write_text(
                json.dumps(current_snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (history_dir / "stg-2026-07-11-a-status-snapshot-20260711T110000Z.json").write_text(
                json.dumps(previous_snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (history_dir / "stg-2026-07-11-a-status-snapshot-20260711T120000Z.json").write_text(
                json.dumps(current_snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (docs_dir / "stg-2026-07-11-a-executive-bullet.md").write_text(
                "Ontrackchain | janela stg-2026-07-11-a | status=failed | semaforo=amarelo | escopo_regulatorio=P0-02 | p0_04=ready | rca=2 | criticos_abertos=1 | bloqueios=2 placeholders/1 handoff | decisao=recomendado_no_go\n",
                encoding="utf-8",
            )
            (docs_dir / "stg-2026-07-11-a-comms-summary.md").write_text(
                "# Comms\nEscopo regulatorio: `P0-02`\n",
                encoding="utf-8",
            )
            (checks_dir / "stg-2026-07-11-a-regulatory-unblock-checklist.json").write_text(
                json.dumps(
                    {
                        "status": "failed",
                        "blocking_classification": "regulatory_blocked",
                        "summary": {
                            "blocked_scopes": ["p0-02", "p0-03", "p0-04"],
                            "owner_action_groups_count": 2,
                            "dominant_blocking_summary": "Todos os escopos regulatórios seguem bloqueados.",
                        },
                        "owner_actions": [
                            {
                                "owner_group": "Compliance/AML",
                                "owner": "Compliance/Backend",
                                "kind": "fill_scope_env",
                                "targets": ["COMPLIANCE_TRM_API_KEY"],
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (dossiers_dir / "stg-2026-07-11-a-regulatory-unblock-checklist.md").write_text(
                "# Regulatory Unblock\n",
                encoding="utf-8",
            )

            result = MODULE.build_consolidated_json(
                "stg-2026-07-11-a",
                str(checks_dir),
                str(dossiers_dir),
                str(docs_dir),
            )

        self.assertEqual(result["governance_state"]["regulatory"]["scope_label"], "P0-02")
        self.assertEqual(result["governance_state"]["regulatory"]["p0_04_bundle_readiness"], "ready")
        self.assertEqual(result["regulatory_summary"]["current"]["scope_label"], "P0-02")
        self.assertEqual(result["regulatory_summary"]["current"]["p0_04_bundle_readiness"], "ready")
        self.assertEqual(result["regulatory_summary"]["previous"]["scope_label"], "none")
        self.assertEqual(result["governance_state"]["operational"]["rca_attached_count"], 2)
        self.assertEqual(result["governance_state"]["operational"]["critical_open_count"], 1)
        self.assertEqual(result["operational_summary"]["current"]["status"], "available")
        self.assertEqual(result["operational_summary"]["current"]["rca_attached_count"], 2)
        self.assertEqual(result["regulatory_unblock_summary"]["blocking_classification"], "regulatory_blocked")
        self.assertEqual(result["regulatory_unblock_summary"]["owner_action_groups_count"], 2)
        self.assertEqual(
            result["parsed_content"]["regulatory_unblock_owner_actions"][0]["owner_group"],
            "Compliance/AML",
        )
        self.assertTrue(result["artefact_files"]["regulatory_unblock_checklist"].endswith(".json"))


if __name__ == "__main__":
    unittest.main()
