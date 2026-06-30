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


MODULE = _load_module("check_staging_env_handoff", "scripts/check_staging_env_handoff.py")


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


class CheckStagingEnvHandoffTests(unittest.TestCase):
    maxDiff = None

    def test_fails_when_file_is_missing(self) -> None:
        exit_code, payload = MODULE.build_payload(
            file_path=ROOT_DIR / "missing-handoff.md",
            required_groups=["Auth/OIDC", "Compliance/AML"],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("arquivo_ausente", payload["errors"][0])
        self.assertEqual(payload["checked_groups_count"], 0)

    def test_fails_when_groups_are_pending_or_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            handoff_path = Path(tmp_dir) / "staging-env-ownership.md"
            _write_handoff_file(
                handoff_path,
                [
                    "| Auth/OIDC | `Backend/Auth` | `pending` | `pending` | alinhar claims finais |",
                    "| Compliance/AML | `Compliance/Backend` | `2026-06-29` | `approved` | credencial validada |",
                    "| Platform/Operations | `Platform/SRE` | `2026-06-29` | `approved` | janela preparada |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                file_path=handoff_path,
                required_groups=MODULE.DEFAULT_REQUIRED_GROUPS,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("grupo_obrigatorio_ausente: Investigation/RPC", payload["errors"])
        self.assertIn("campo_obrigatorio_pendente: Auth/OIDC.date", payload["errors"])
        self.assertIn("campo_obrigatorio_pendente: Auth/OIDC.status", payload["errors"])
        self.assertEqual(payload["missing_groups"], ["Investigation/RPC"])

    def test_fails_when_status_or_date_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            handoff_path = Path(tmp_dir) / "staging-env-ownership.md"
            _write_handoff_file(
                handoff_path,
                [
                    "| Auth/OIDC | `Backend/Auth` | `29/06/2026` | `approved` | claims finalizadas |",
                    "| Compliance/AML | `Compliance/Backend` | `2026-06-29` | `signed` | provider validado |",
                    "| Investigation/RPC | `Backend Core` | `2026-06-29` | `waived` | `pending` |",
                    "| Platform/Operations | `Platform/SRE` | `2026-06-29` | `reviewed` | observabilidade revisada |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                file_path=handoff_path,
                required_groups=MODULE.DEFAULT_REQUIRED_GROUPS,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("status_invalido: Compliance/AML=signed", payload["errors"])
        self.assertIn("data_invalida: Auth/OIDC=29/06/2026", payload["errors"])
        self.assertIn("campo_obrigatorio_pendente: Investigation/RPC.observations", payload["errors"])

    def test_passes_when_all_required_groups_have_valid_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            handoff_path = Path(tmp_dir) / "staging-env-ownership.md"
            _write_handoff_file(
                handoff_path,
                [
                    "| Auth/OIDC | `Backend/Auth` | `2026-06-29` | `approved` | claims e secrets validados |",
                    "| Compliance/AML | `Compliance/Backend` | `2026-06-29` | `approved` | TRM live homologado |",
                    "| Investigation/RPC | `Backend Core` | `2026-06-29` | `reviewed` | fallback_only confirmado |",
                    "| Platform/Operations | `Platform/SRE` | `2026-06-29` | `waived` | owner DBA cobre credencial existente da janela |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                file_path=handoff_path,
                required_groups=MODULE.DEFAULT_REQUIRED_GROUPS,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["missing_groups"], [])
        self.assertEqual(payload["invalid_statuses"], [])
        self.assertEqual(payload["invalid_dates"], [])

    def test_output_payload_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            handoff_path = Path(tmp_dir) / "staging-env-ownership.md"
            _write_handoff_file(
                handoff_path,
                [
                    "| Auth/OIDC | `Backend/Auth` | `2026-06-29` | `approved` | claims e secrets validados |",
                    "| Compliance/AML | `Compliance/Backend` | `2026-06-29` | `approved` | TRM live homologado |",
                    "| Investigation/RPC | `Backend Core` | `2026-06-29` | `reviewed` | fallback_only confirmado |",
                    "| Platform/Operations | `Platform/SRE` | `2026-06-29` | `approved` | observabilidade revisada |",
                ],
            )
            _, payload = MODULE.build_payload(
                file_path=handoff_path,
                required_groups=MODULE.DEFAULT_REQUIRED_GROUPS,
            )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
