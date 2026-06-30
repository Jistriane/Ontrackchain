import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


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
    "render_staging_private_env_templates",
    "scripts/render_staging_private_env_templates.py",
)


def _write_env_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "APP_ENV=staging",
                "MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false",
                "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__",
                "OIDC_PROVIDER=keycloak",
                "KEYCLOAK_ADMIN_PASSWORD=__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                "",
            ]
        ),
        encoding="utf-8",
    )


class RenderStagingPrivateEnvTemplatesTests(unittest.TestCase):
    maxDiff = None

    def test_write_templates_generates_baseline_and_homologated_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            output_dir = base / "artifacts"
            _write_env_file(env_file)

            files = MODULE.write_templates(
                env_file=env_file,
                output_dir=output_dir,
                generated_at="2026-06-30T12:00:00+00:00",
            )

            baseline = Path(files["baseline"]).read_text(encoding="utf-8")
            homologated = Path(files["homologated"]).read_text(encoding="utf-8")

        self.assertIn("Modo da janela: baseline", baseline)
        self.assertIn("MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false", baseline)
        self.assertIn("Opcional nesta janela", baseline)

        self.assertIn("Modo da janela: homologated", homologated)
        self.assertIn("MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true", homologated)
        self.assertIn("Obrigatorio quando MFA federado homologado", homologated)

    def test_main_writes_json_payload_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            output_dir = base / "artifacts"
            _write_env_file(env_file)
            stdout = io.StringIO()

            with patch.object(
                sys,
                "argv",
                [
                    "render_staging_private_env_templates.py",
                    "--env-file",
                    str(env_file),
                    "--output-dir",
                    str(output_dir),
                    "--generated-at",
                    "2026-06-30T12:00:00+00:00",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            payload = json.loads(stdout.getvalue())
            baseline_exists = Path(payload["files"]["baseline"]).exists()
            homologated_exists = Path(payload["files"]["homologated"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(baseline_exists)
        self.assertTrue(homologated_exists)


if __name__ == "__main__":
    unittest.main()
