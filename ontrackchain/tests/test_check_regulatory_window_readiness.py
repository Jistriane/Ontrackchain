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
    "check_regulatory_window_readiness",
    "scripts/check_regulatory_window_readiness.py",
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


class CheckRegulatoryWindowReadinessTests(unittest.TestCase):
    maxDiff = None

    def test_reports_blocking_summary_and_unblock_actions_when_env_is_missing_and_handoff_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_path = base / ".env.staging.private"
            handoff_path = base / "staging-env-ownership.md"
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `pending` | `pending` | aguardando provider live |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                scope="p0-02",
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["blocking_classification"], "regulatory_blocked")
        self.assertTrue(payload["blocking_context"]["missing_private_env_file"])
        self.assertIn("Compliance/AML", payload["blocking_summary"])
        self.assertIn(".env.staging.private", payload["blocking_summary"])
        self.assertEqual(payload["unblock_actions"][0]["kind"], "materialize_private_env")
        self.assertEqual(payload["unblock_actions"][1]["kind"], "complete_handoff")
        self.assertIn("materialize-staging-private-env", payload["readiness"]["next_action"])

    def test_passes_when_handoff_and_scope_variables_are_ready(self) -> None:
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
                ],
            )
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `2026-07-19` | `approved` | provider live validado |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                scope="p0-02",
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["blocking_classification"], "pending_execution")
        self.assertEqual(payload["blocking_summary"], "Trilha `p0-02` pronta para execucao; handoff e segredos obrigatorios estao coerentes.")
        self.assertEqual(payload["unblock_actions"], [])
        self.assertEqual(payload["readiness"]["readiness_status"], "ready_for_execution")

    def test_reports_scope_specific_env_actions_for_invalid_eu_feed_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_path = base / ".env.staging.private"
            handoff_path = base / "staging-env-ownership.md"
            _write_file(
                env_path,
                [
                    "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=https://eu.example.com/feed.xml",
                    "DATABASE_URL=postgresql://user:secret@db.example.com:5432/ontrackchain",
                ],
            )
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `2026-07-19` | `approved` | feed provisionado |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                scope="p0-03",
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(
            payload["blocking_context"]["env_invalid_contains_rules"],
            [{"name": "COMPLIANCE_EU_SANCTIONS_SOURCE_URL", "required_fragment": "token="}],
        )
        self.assertEqual(payload["unblock_actions"][0]["kind"], "fill_scope_env")
        self.assertIn(
            "COMPLIANCE_EU_SANCTIONS_SOURCE_URL",
            payload["unblock_actions"][0]["targets"],
        )

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
                ],
            )
            _write_handoff_file(
                handoff_path,
                [
                    "| Compliance/AML | `Compliance/Backend` | `2026-07-19` | `approved` | provider live validado |",
                ],
            )
            _, payload = MODULE.build_payload(
                scope="p0-02",
                private_env_file=env_path,
                ownership_file=handoff_path,
            )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
