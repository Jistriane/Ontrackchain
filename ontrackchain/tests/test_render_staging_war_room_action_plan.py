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
    "render_staging_war_room_action_plan",
    "scripts/render_staging_war_room_action_plan.py",
)


class RenderStagingWarRoomActionPlanTests(unittest.TestCase):
    def test_build_model_reads_optional_regulatory_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            checks_dir = base / "checks"
            checks_dir.mkdir(parents=True, exist_ok=True)
            snapshot_file = base / "snapshot.json"

            (checks_dir / "placeholders-stg-2026-07-11-a.json").write_text(
                json.dumps({"unresolved_placeholders": [{"name": "COMPLIANCE_TRM_API_KEY"}]}),
                encoding="utf-8",
            )
            (checks_dir / "handoff-stg-2026-07-11-a.json").write_text(
                json.dumps({"incomplete_groups": [{"group": "Compliance/AML", "missing_fields": ["owner"]}]}),
                encoding="utf-8",
            )
            snapshot_file.write_text(
                json.dumps(
                    {
                        "regulatory": {
                            "scope_label": "P0-02",
                            "p0_04_bundle_readiness": "ready",
                            "promotion_note": "tentativa parcial (P0-02); endurece a trilha, mas a promocao oficial de P0-04 ainda exige P0-02 + P0-03",
                        }
                    }
                ),
                encoding="utf-8",
            )

            model = MODULE.build_model("stg-2026-07-11-a", checks_dir, snapshot_file)
            content = MODULE.render_markdown(model)

        self.assertEqual(model["regulatory"]["scope_label"], "P0-02")
        self.assertIn("## Contexto Regulatorio", content)
        self.assertIn("- escopo regulatorio da tentativa: `P0-02`", content)
        self.assertIn("tentativa atual cobre `P0-02`", content)


if __name__ == "__main__":
    unittest.main()
