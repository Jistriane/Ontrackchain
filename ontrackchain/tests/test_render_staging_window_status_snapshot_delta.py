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
    "render_staging_window_status_snapshot_delta",
    "scripts/render_staging_window_status_snapshot_delta.py",
)


def _snapshot(*, overall_status: str, scope_label: str, p0_04_readiness: str, promotion_note: str) -> dict:
    return {
        "overall_status": overall_status,
        "blockers": {
            "unresolved_placeholders_count": 2,
            "unresolved_placeholders": ["A", "B"],
            "missing_handoff_fields_count": 1,
            "missing_handoff_fields": ["X.owner"],
        },
        "regulatory": {
            "scope_label": scope_label,
            "p0_04_bundle_readiness": p0_04_readiness,
            "promotion_note": promotion_note,
        },
    }


class RenderStagingWindowStatusSnapshotDeltaTests(unittest.TestCase):
    def test_render_markdown_marks_regulatory_progress_as_yellow(self) -> None:
        previous = _snapshot(
            overall_status="failed",
            scope_label="P0-02",
            p0_04_readiness="ready",
            promotion_note="tentativa parcial anterior",
        )
        current = _snapshot(
            overall_status="failed",
            scope_label="P0-02/P0-03",
            p0_04_readiness="ready_for_validation",
            promotion_note="tentativa combinada; P0-04 pode ser promovido se a validacao final convergir",
        )

        content = MODULE.render_markdown(
            "stg-2026-07-11-a",
            current,
            previous,
            Path("current.json"),
            Path("previous.json"),
        )

        self.assertIn("- sinal: `amarelo`", content)
        self.assertIn("houve progresso regulatorio material", content)
        self.assertIn("## Delta Regulatorio", content)
        self.assertIn("- escopo anterior: `P0-02`", content)
        self.assertIn("- escopo atual: `P0-02/P0-03`", content)
        self.assertIn("- `P0-04` readiness atual: `ready_for_validation`", content)

    def test_compute_executive_signal_marks_green_for_combined_ok_window(self) -> None:
        signal, note = MODULE.compute_executive_signal(
            "failed",
            "ok",
            0,
            0,
            [],
            [],
            {
                "scope_label": "P0-02",
                "p0_04_bundle_readiness": "ready",
                "promotion_note": "tentativa parcial anterior",
            },
            {
                "scope_label": "P0-02/P0-03",
                "p0_04_bundle_readiness": "ready_for_validation",
                "promotion_note": "tentativa combinada atual",
            },
        )

        self.assertEqual(signal, "verde")
        self.assertIn("bundle regulatorio promovivel", note)
        self.assertIn("tentativa combinada", note)


if __name__ == "__main__":
    unittest.main()
