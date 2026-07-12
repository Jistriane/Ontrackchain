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
    "render_staging_unblock_checklist",
    "scripts/render_staging_unblock_checklist.py",
)


class RenderStagingUnblockChecklistTests(unittest.TestCase):
    def test_render_markdown_includes_regulatory_context(self) -> None:
        snapshot = {
            "generated_at": "2026-07-11T12:00:00Z",
            "overall_status": "failed",
            "blockers": {
                "unresolved_placeholders_count": 1,
                "unresolved_placeholders": ["COMPLIANCE_TRM_API_KEY"],
                "missing_handoff_fields_count": 1,
                "missing_handoff_fields": ["Compliance/AML.owner"],
            },
            "regulatory": {
                "scope_label": "P0-02",
                "validation_scope": ["P0-01", "P0-02"],
                "p0_04_bundle_readiness": "ready",
                "promotion_note": "tentativa parcial (P0-02); endurece a trilha, mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03",
            },
        }

        content = MODULE.render_markdown(
            "stg-2026-07-11-a",
            Path("snapshot.json"),
            snapshot,
        )

        self.assertIn("- escopo regulatorio da tentativa: `P0-02`", content)
        self.assertIn("- scope validado no gate final: `P0-01,P0-02`", content)
        self.assertIn("- `P0-04` readiness: `ready`", content)
        self.assertIn("- contexto regulatorio: escopo atual `P0-02` com `P0-04=ready`", content)
        self.assertIn("- se o escopo regulatorio for parcial, nao marcar `P0-04` como fechado", content)


if __name__ == "__main__":
    unittest.main()
