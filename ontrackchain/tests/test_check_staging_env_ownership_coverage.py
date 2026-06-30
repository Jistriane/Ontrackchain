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
    "check_staging_env_ownership_coverage",
    "scripts/check_staging_env_ownership_coverage.py",
)


def _write_env_file(target: Path, lines: list[str]) -> None:
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_ownership_file(target: Path, rows: list[str]) -> None:
    target.write_text(
        "\n".join(
            [
                "# Ownership do `.env.staging`",
                "",
                "## Matriz de Ownership",
                "",
                "| Placeholder / grupo | Owner primario | Apoio | Evidencia esperada |",
                "| --- | --- | --- | --- |",
                *rows,
                "",
            ]
        ),
        encoding="utf-8",
    )


class CheckStagingEnvOwnershipCoverageTests(unittest.TestCase):
    maxDiff = None

    def test_fails_when_required_files_are_missing(self) -> None:
        exit_code, payload = MODULE.build_payload(
            env_file=ROOT_DIR / "missing.env",
            ownership_file=ROOT_DIR / "missing.md",
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("arquivo_env_ausente", payload["errors"][0])
        self.assertIn("arquivo_ownership_ausente", payload["errors"][1])

    def test_fails_when_placeholder_is_missing_from_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(
                env_file,
                [
                    "POSTGRES_PASSWORD=__FILL_STAGING_POSTGRES_PASSWORD__",
                    "COMPLIANCE_TRM_API_KEY=__FILL_STAGING_TRM_API_KEY__",
                ],
            )
            _write_ownership_file(
                ownership_file,
                [
                    "| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `Security` | secret provisionado |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                env_file=env_file,
                ownership_file=ownership_file,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["missing_in_matrix"], ["__FILL_STAGING_TRM_API_KEY__"])
        self.assertIn("placeholder_sem_owner: __FILL_STAGING_TRM_API_KEY__", payload["errors"])

    def test_fails_when_matrix_contains_stale_or_incomplete_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(
                env_file,
                [
                    "POSTGRES_PASSWORD=__FILL_STAGING_POSTGRES_PASSWORD__",
                    "GRAFANA_ADMIN_PASSWORD=__FILL_STAGING_GRAFANA_ADMIN_PASSWORD__",
                ],
            )
            _write_ownership_file(
                ownership_file,
                [
                    "| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `pending` | secret provisionado |",
                    "| `__FILL_STAGING_OBSOLETE__` | `Platform/SRE` | `Security` | item legado |",
                    "| `__FILL_STAGING_GRAFANA_ADMIN_PASSWORD__` | `Platform/SRE` | `Security` | senha admin nao-dev |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                env_file=env_file,
                ownership_file=ownership_file,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["stale_in_matrix"], ["__FILL_STAGING_OBSOLETE__"])
        self.assertIn("placeholder_obsoleto_na_matriz: __FILL_STAGING_OBSOLETE__", payload["errors"])
        self.assertIn("campo_owner_pendente: __FILL_STAGING_POSTGRES_PASSWORD__.support", payload["errors"])

    def test_passes_when_all_placeholders_have_valid_ownership_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(
                env_file,
                [
                    "POSTGRES_PASSWORD=__FILL_STAGING_POSTGRES_PASSWORD__",
                    "COMPLIANCE_TRM_API_KEY=__FILL_STAGING_TRM_API_KEY__",
                ],
            )
            _write_ownership_file(
                ownership_file,
                [
                    "| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `Security` | secret provisionado |",
                    "| `__FILL_STAGING_TRM_API_KEY__` | `Compliance/Backend` | `Security` | API key com trilha de provisionamento |",
                ],
            )

            exit_code, payload = MODULE.build_payload(
                env_file=env_file,
                ownership_file=ownership_file,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["missing_in_matrix"], [])
        self.assertEqual(payload["stale_in_matrix"], [])
        self.assertEqual(payload["checked_placeholders_count"], 2)

    def test_output_payload_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(env_file, ["POSTGRES_PASSWORD=__FILL_STAGING_POSTGRES_PASSWORD__"])
            _write_ownership_file(
                ownership_file,
                [
                    "| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `Security` | secret provisionado |",
                ],
            )
            _, payload = MODULE.build_payload(
                env_file=env_file,
                ownership_file=ownership_file,
            )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
