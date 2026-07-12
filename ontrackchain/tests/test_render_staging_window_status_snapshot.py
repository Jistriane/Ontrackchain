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
    "render_staging_window_status_snapshot",
    "scripts/render_staging_window_status_snapshot.py",
)


class RenderStagingWindowStatusSnapshotTests(unittest.TestCase):
    def test_render_markdown_includes_regulatory_section(self) -> None:
        payload = {
            "window_id": "stg-2026-07-11-a",
            "generated_at": "2026-07-11T12:00:00+00:00",
            "overall_status": "failed",
            "regulatory": {
                "scope_label": "P0-02",
                "validation_scope": ["P0-01", "P0-02"],
                "aml_kyt_runtime_status": "ok",
                "aml_kyt_runtime_readiness": "ready_for_validation",
                "eu_feed_status": "skipped",
                "eu_feed_readiness": "ready",
                "p0_04_bundle_readiness": "ready",
                "promotion_note": "tentativa parcial (P0-02); endurece a trilha, mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03",
            },
            "operational_incidents": {
                "status": "available",
                "exported_count": 3,
                "tracked_work_items_count": 2,
                "rca_attached_count": 2,
                "confirmed_root_cause_count": 1,
                "firing_count": 1,
                "critical_open_count": 1,
                "ready_queue_count": 1,
                "pending_triage_count": 1,
                "acknowledged_count": 1,
                "top_rca_domains": ["compliance"],
                "top_affected_domains": ["compliance", "monitoring"],
            },
            "blockers": {
                "unresolved_placeholders_count": 1,
                "unresolved_placeholders": ["KEYCLOAK_ADMIN_PASSWORD"],
                "missing_handoff_fields_count": 1,
                "missing_handoff_fields": ["Compliance.owner"],
            },
            "prepare": {"status": "ok", "exit_code": 0, "generated_at": "2026-07-11T11:00:00+00:00"},
            "run": {"status": "failed", "exit_code": 1, "generated_at": "2026-07-11T11:30:00+00:00", "errors": []},
            "artifact_validation": {"status": "failed", "exit_code": 1, "errors": [], "missing_artifacts": []},
        }

        content = MODULE.render_markdown(
            payload,
            Path("docs/governance-weekly/generated/windows/stg-2026-07-11-a/status-snapshot.json"),
        )

        self.assertIn("## Escopo Regulatorio", content)
        self.assertIn("- escopo regulatorio da tentativa: `P0-02`", content)
        self.assertIn("- scope validado pelo gate final: `P0-01,P0-02`", content)
        self.assertIn("- bundle regulatorio (`P0-04`) readiness: `ready`", content)
        self.assertIn("- leitura de promocao: tentativa parcial (P0-02); endurece a trilha", content)
        self.assertIn("## Incidentes Operacionais e RCA", content)
        self.assertIn("- RCAs anexadas: `2`", content)
        self.assertIn("- dominios RCA em destaque: `compliance`", content)


if __name__ == "__main__":
    unittest.main()
