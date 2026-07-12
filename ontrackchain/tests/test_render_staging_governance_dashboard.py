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
    "render_staging_governance_dashboard",
    "scripts/render_staging_governance_dashboard.py",
)


def _snapshot(*, overall_status: str, placeholders: int, handoff: int, scope_label: str, p0_04: str, note: str) -> dict:
    return {
        "overall_status": overall_status,
        "blockers": {
            "unresolved_placeholders_count": placeholders,
            "missing_handoff_fields_count": handoff,
        },
        "prepare": {"status": "ok"},
        "run": {"status": "failed" if overall_status != "ok" else "ok"},
        "artifact_validation": {"status": "failed" if overall_status != "ok" else "ok"},
        "regulatory": {
            "scope_label": scope_label,
            "p0_04_bundle_readiness": p0_04,
            "promotion_note": note,
        },
        "operational_incidents": {
            "status": "available",
            "rca_attached_count": 2,
            "critical_open_count": 1,
            "pending_triage_count": 1,
            "top_rca_domains": ["compliance", "monitoring"],
        },
    }


class RenderStagingGovernanceDashboardTests(unittest.TestCase):
    def test_compute_signal_marks_yellow_for_regulatory_progress(self) -> None:
        previous = _snapshot(
            overall_status="failed",
            placeholders=2,
            handoff=1,
            scope_label="P0-02",
            p0_04="ready",
            note="tentativa parcial anterior",
        )
        current = _snapshot(
            overall_status="failed",
            placeholders=2,
            handoff=1,
            scope_label="P0-02/P0-03",
            p0_04="ready_for_validation",
            note="tentativa combinada pronta para validacao",
        )

        signal, note = MODULE.compute_signal(previous, current)

        self.assertEqual(signal, "amarelo")
        self.assertIn("progresso regulatorio material", note)

    def test_render_markdown_includes_regulatory_fields(self) -> None:
        current = _snapshot(
            overall_status="failed",
            placeholders=2,
            handoff=1,
            scope_label="P0-02",
            p0_04="ready",
            note="tentativa parcial (P0-02); endurece a trilha, mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03",
        )
        previous = _snapshot(
            overall_status="failed",
            placeholders=2,
            handoff=1,
            scope_label="P0-02",
            p0_04="ready",
            note="tentativa parcial anterior",
        )

        content = MODULE.render_markdown(
            "stg-2026-07-11-a",
            Path("current.json"),
            Path("previous.json"),
            Path("action-plan.md"),
            Path("status-snapshot.md"),
            Path("status-delta.md"),
            "2026-07-11T12:00:00Z",
            current,
            previous,
        )

        self.assertIn("- escopo regulatorio da tentativa: `P0-02`", content)
        self.assertIn("- `P0-04` readiness: `ready`", content)
        self.assertIn("- leitura regulatoria: tentativa parcial (P0-02); endurece a trilha", content)
        self.assertIn("- RCA cross-domain: `available` | RCA(s) `2` | criticos `1` | pendentes `1`", content)
        self.assertIn("- dominios RCA em destaque: `compliance,monitoring`", content)


if __name__ == "__main__":
    unittest.main()
