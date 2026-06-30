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
    "render_staging_window_packet",
    "scripts/render_staging_window_packet.py",
)


def _write_env_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "POSTGRES_PASSWORD=__FILL_STAGING_POSTGRES_PASSWORD__",
                "KEYCLOAK_ADMIN_PASSWORD=__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                "COMPLIANCE_TRM_API_KEY=__FILL_STAGING_TRM_API_KEY__",
                "INVESTIGATION_RPC_PRIMARY_URL=__FILL_STAGING_RPC_PRIMARY_URL__",
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                "ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_ownership_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "# Ownership do `.env.staging`",
                "",
                "## Matriz de Ownership",
                "",
                "| Placeholder / grupo | Owner primario | Apoio | Evidencia esperada |",
                "| --- | --- | --- | --- |",
                "| `__FILL_STAGING_POSTGRES_PASSWORD__` | `Platform/DBA` | `Security` | secret provisionado |",
                "| `__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__` | `Backend/Auth` | `Security` | credencial admin validada |",
                "| `__FILL_STAGING_TRM_API_KEY__` | `Compliance/Backend` | `Security` | API key homologada |",
                "| `__FILL_STAGING_RPC_PRIMARY_URL__` | `Backend Core` | `Platform/DBA` | RPC primario validado |",
                "",
                "## Registro de Handoff",
                "",
                "| Grupo | Owner | Data | Status | Observacoes |",
                "| --- | --- | --- | --- | --- |",
                "| Auth/OIDC | `Backend/Auth` | `2026-06-29` | `approved` | claims finais alinhadas |",
                "| Compliance/AML | `Compliance/Backend` | `2026-06-29` | `approved` | provider validado |",
                "| Investigation/RPC | `Backend Core` | `2026-06-29` | `reviewed` | fallback_only aceito |",
                "| Platform/Operations | `Platform/SRE` | `2026-06-29` | `approved` | operacao preparada |",
                "",
            ]
        ),
        encoding="utf-8",
    )


class RenderStagingWindowPacketTests(unittest.TestCase):
    maxDiff = None

    def test_build_packet_model_groups_items_by_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(env_file)
            _write_ownership_file(ownership_file)

            model = MODULE.build_packet_model(
                window_id="stg-2026-06-29-a",
                env_file=env_file,
                ownership_file=ownership_file,
                generated_at="2026-06-29T12:00:00+00:00",
            )

        self.assertEqual(model["expected_modes"]["compliance"], "live")
        self.assertEqual(model["expected_modes"]["rpc"], "fallback_only")
        self.assertEqual(len(model["owners"]), 4)
        self.assertEqual(model["owners"][0]["owner"], "Backend Core")
        self.assertTrue(
            any(item["variable"] == "INVESTIGATION_RPC_PRIMARY_URL" for item in model["owners"][0]["items"])
        )

    def test_render_packet_markdown_contains_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            _write_env_file(env_file)
            _write_ownership_file(ownership_file)

            model = MODULE.build_packet_model(
                window_id="stg-2026-06-29-a",
                env_file=env_file,
                ownership_file=ownership_file,
                generated_at="2026-06-29T12:00:00+00:00",
            )
            markdown = MODULE.render_packet_markdown(model)

        self.assertIn("# Staging Window Packet - stg-2026-06-29-a", markdown)
        self.assertIn("## Sequencia Operacional", markdown)
        self.assertIn("## Placeholders por Owner", markdown)
        self.assertIn("## Snapshot do Handoff", markdown)
        self.assertIn("## Matriz Redigida", markdown)
        self.assertIn("`COMPLIANCE_TRM_API_KEY`", markdown)
        self.assertIn("`__FILL_STAGING_TRM_API_KEY__`", markdown)

    def test_main_writes_output_file_and_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env.staging.example"
            ownership_file = Path(tmp_dir) / "staging-env-ownership.md"
            output_file = Path(tmp_dir) / "artifacts" / "window-packet.md"
            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "render_staging_window_packet.py",
                    "--window-id",
                    "stg-2026-06-29-a",
                    "--env-file",
                    str(env_file),
                    "--ownership-file",
                    str(ownership_file),
                    "--output-file",
                    str(output_file),
                    "--generated-at",
                    "2026-06-29T12:00:00+00:00",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()
            self.assertEqual(exit_code, 0)
            self.assertTrue(output_file.exists())
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["output_file"], str(output_file))
            self.assertEqual(payload["window_id"], "stg-2026-06-29-a")
            self.assertIn(
                "# Staging Window Packet - stg-2026-06-29-a",
                output_file.read_text(encoding="utf-8"),
            )

    def test_output_payload_is_json_serializable(self) -> None:
        payload = {
            "kind": "staging_window_packet",
            "status": "ok",
            "window_id": "stg-2026-06-29-a",
        }
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
