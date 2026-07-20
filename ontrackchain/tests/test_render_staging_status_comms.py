import importlib.util
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


EXECUTIVE_BULLET = _load_module(
    "render_staging_executive_bullet",
    "scripts/render_staging_executive_bullet.py",
)
COMMS_SUMMARY = _load_module(
    "render_staging_comms_summary",
    "scripts/render_staging_comms_summary.py",
)


class RenderStagingStatusCommsTests(unittest.TestCase):
    def _payload(self) -> dict:
        return {
            "overall_status": "failed",
            "blockers": {
                "unresolved_placeholders_count": 2,
                "missing_handoff_fields_count": 1,
            },
            "prepare": {"status": "ok"},
            "run": {"status": "failed"},
            "artifact_validation": {"status": "failed"},
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
            },
        }

    def test_executive_bullet_includes_scope_and_p0_04_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            delta_file = Path(tmp_dir) / "delta.md"
            delta_file.write_text("- sinal: `amarelo`\n", encoding="utf-8")

            content = EXECUTIVE_BULLET.render_markdown(
                "stg-2026-07-11-a",
                Path(tmp_dir) / "snapshot.json",
                delta_file,
                self._payload(),
            )

        self.assertIn("escopo_regulatorio=P0-02", content)
        self.assertIn("p0_04=ready", content)
        self.assertIn("rca=2", content)
        self.assertIn("criticos_abertos=1", content)

    def test_comms_summary_includes_regulatory_reading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            delta_file = Path(tmp_dir) / "delta.md"
            delta_file.write_text(
                "- sinal: `amarelo`\n- leitura: houve progresso parcial, mas ainda sem condicao de go\n",
                encoding="utf-8",
            )

            content = COMMS_SUMMARY.render_markdown(
                "stg-2026-07-11-a",
                Path(tmp_dir) / "snapshot.json",
                delta_file,
                Path(tmp_dir) / "dashboard.md",
                Path(tmp_dir) / "unblock.md",
                Path(tmp_dir) / "regulatory-unblock.md",
                self._payload(),
            )

        self.assertIn("Escopo regulatorio: `P0-02` | `P0-04` readiness: `ready`.", content)
        self.assertIn("RCA cross-domain: `2` RCA(s) em `3` work-item(s) rastreado(s) | pendente `2` | criticos `1`.", content)
        self.assertIn("- escopo regulatorio da tentativa: `P0-02`", content)
        self.assertIn("- scope validado no gate final: `P0-01,P0-02`", content)
        self.assertIn("- leitura regulatoria: tentativa parcial (P0-02); endurece a trilha", content)
        self.assertIn("- work-items rastreados: `3`", content)
        self.assertIn("- dominios RCA em destaque: `compliance,monitoring`", content)
        self.assertIn("- checklist regulatorio consolidado: `", content)


if __name__ == "__main__":
    unittest.main()
