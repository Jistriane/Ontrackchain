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
    "run_regulatory_unblock_checklist",
    "scripts/run_regulatory_unblock_checklist.py",
)


def _write_file(target: Path, lines: list[str]) -> None:
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_handoff_file(target: Path, rows: list[str]) -> None:
    target.write_text(
        "\n".join(
            [
                "# Ownership do `.env.staging`",
                "",
                "## Registro de Handoff",
                "",
                "| Grupo | Owner | Data | Status | Observacoes |",
                "| --- | --- | --- | --- | --- |",
                *rows,
                "",
            ]
        ),
        encoding="utf-8",
    )


class RunRegulatoryUnblockChecklistTests(unittest.TestCase):
    maxDiff = None

    def test_build_payload_consolidates_scopes_for_same_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_path = base / ".env.staging.private"
            handoff_path = base / "staging-env-ownership.md"
            _write_file(
                env_path,
                [
                    "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                    "COMPLIANCE_TRM_ENABLED=true",
                    "COMPLIANCE_TRM_SCREENING_URL=__FILL_STAGING_TRM_SCREENING_URL__",
                    "COMPLIANCE_TRM_API_KEY=__FILL_STAGING_TRM_API_KEY__",
                    "COMPLIANCE_TRM_API_KEY_HEADER=Authorization",
                    "COMPLIANCE_TRM_API_KEY_PREFIX=Bearer",
                    "COMPLIANCE_TRM_TIMEOUT_MS=1500",
                    "COMPLIANCE_TRM_MAX_RETRIES=1",
                    "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=__FILL_STAGING_COMPLIANCE_EU_SANCTIONS_SOURCE_URL__",
                ],
            )
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `pending` | `pending` | aguardando provider live |",
                ],
            )

            payload = MODULE.build_payload(
                window_id="stg-2026-07-19-a",
                scopes=["p0-02", "p0-03"],
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["blocking_classification"], "regulatory_blocked")
        self.assertEqual(payload["summary"]["blocked_scopes"], ["p0-02", "p0-03"])
        self.assertEqual(payload["summary"]["owner_action_groups_count"], 2)

        complete_handoff = payload["owner_actions"][0]
        fill_scope_env = payload["owner_actions"][1]
        self.assertEqual(complete_handoff["kind"], "complete_handoff")
        self.assertEqual(complete_handoff["scopes"], ["p0-02", "p0-03"])
        self.assertEqual(fill_scope_env["kind"], "fill_scope_env")
        self.assertIn("COMPLIANCE_TRM_SCREENING_URL", fill_scope_env["targets"])
        self.assertIn("COMPLIANCE_EU_SANCTIONS_SOURCE_URL", fill_scope_env["targets"])

    def test_render_markdown_includes_scope_summaries_and_owner_sections(self) -> None:
        payload = {
            "window_id": "stg-2026-07-19-a",
            "generated_at": "2026-07-19T01:00:00+00:00",
            "status": "failed",
            "blocking_classification": "regulatory_blocked",
            "files": {
                "private_env_file": ".env.staging.private",
                "ownership_file": "docs/staging-env-ownership.md",
            },
            "summary": {
                "scopes_checked": ["p0-02", "p0-03"],
                "blocked_scopes": ["p0-02", "p0-03"],
                "dominant_blocking_summary": "Todos os escopos regulatórios seguem bloqueados.",
            },
            "scope_summaries": {
                "p0-02": "Trilha `p0-02` bloqueada.",
                "p0-03": "Trilha `p0-03` bloqueada.",
            },
            "owner_actions": [
                {
                    "owner_group": "Compliance/AML",
                    "owner": "Compliance/Backend",
                    "kind": "fill_scope_env",
                    "scopes": ["p0-02", "p0-03"],
                    "targets": ["COMPLIANCE_TRM_API_KEY", "DATABASE_URL"],
                    "actions": ["Preencher variáveis reais em canal seguro."],
                }
            ],
            "next_steps": ["Atualizar handoff."],
            "blockers": ["campo_obrigatorio_pendente: Compliance/AML.status"],
        }

        markdown = MODULE.render_markdown(payload)

        self.assertIn("# Regulatory Unblock Checklist - stg-2026-07-19-a", markdown)
        self.assertIn("- `p0-02`: Trilha `p0-02` bloqueada.", markdown)
        self.assertIn("### Compliance/AML - Compliance/Backend", markdown)
        self.assertIn("- acao: Preencher variáveis reais em canal seguro.", markdown)

    def test_output_payload_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_path = base / ".env.staging.private"
            handoff_path = base / "staging-env-ownership.md"
            _write_file(
                env_path,
                [
                    "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                    "COMPLIANCE_TRM_ENABLED=true",
                    "COMPLIANCE_TRM_SCREENING_URL=https://trm.example.com/screening",
                    "COMPLIANCE_TRM_API_KEY=trm-live-key",
                    "COMPLIANCE_TRM_API_KEY_HEADER=Authorization",
                    "COMPLIANCE_TRM_API_KEY_PREFIX=Bearer",
                    "COMPLIANCE_TRM_TIMEOUT_MS=1500",
                    "COMPLIANCE_TRM_MAX_RETRIES=1",
                    "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://eu.example.com/feed.xml?token=abc",
                    "DATABASE_URL=postgresql://user:secret@db.example.com:5432/ontrackchain",
                ],
            )
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `2026-07-19` | `approved` | janela pronta |",
                ],
            )
            payload = MODULE.build_payload(
                window_id="stg-2026-07-19-a",
                scopes=["p0-02", "p0-03"],
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
