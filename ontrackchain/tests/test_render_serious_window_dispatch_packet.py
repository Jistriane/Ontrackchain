import importlib.util
import io
import json
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
    "render_serious_window_dispatch_packet",
    "scripts/render_serious_window_dispatch_packet.py",
)


def _write_workflow_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "on:",
                "  workflow_dispatch:",
                "    inputs:",
                "      environment_name:",
                "jobs:",
                "  run-serious-window:",
                "    environment: ${{ inputs.environment_name }}",
                "    steps:",
                "      - name: Validate required serious window secret",
                "        env:",
                "          STAGING_WINDOW_PRIVATE_ENV: ${{ secrets.STAGING_WINDOW_PRIVATE_ENV }}",
                "      - name: Upload serious staging artifacts",
                "        with:",
                "          name: serious-staging-window-${{ inputs.window_id }}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_weekly_file(target: Path, *, window_id: str, mode: str, environment_name: str) -> None:
    artifact_name = f"serious-staging-window-{window_id}"
    signoff_name = target.name.replace("-weekly-governance.md", "-staging-serious-window-signoff.md")
    target.write_text(
        "\n".join(
            [
                "# Governance",
                "",
                "## Contexto da Janela Séria",
                "",
                f"- `window_id`: `{window_id}`",
                f"- `mode`: `{mode}`",
                f"- `environment_name`: `{environment_name}`",
                f"- [Sign-Off da Janela `{window_id}`]({signoff_name})",
                "",
                "## Evidências Revisadas",
                "",
                f"- artifact `{artifact_name}`: `pending`",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_signoff_file(target: Path, *, window_id: str, mode: str, environment_name: str) -> None:
    artifact_name = f"serious-staging-window-{window_id}"
    target.write_text(
        "\n".join(
            [
                f"# Sign-Off da Janela Seria — `{window_id}`",
                "",
                "## Identificacao",
                "",
                f"- mode: `{mode}`",
                f"- environment_name: `{environment_name}`",
                f"- artifact: `{artifact_name}`",
                "",
            ]
        ),
        encoding="utf-8",
    )


class RenderSeriousWindowDispatchPacketTests(unittest.TestCase):
    maxDiff = None

    def test_render_packet_markdown_includes_commands_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            governance_dir = base / "docs" / "governance-weekly"
            workflow_file = base / ".github" / "workflows" / "staging-serious-window.yml"
            governance_dir.mkdir(parents=True, exist_ok=True)
            workflow_file.parent.mkdir(parents=True, exist_ok=True)

            window_id = "stg-2026-07-06-a"
            weekly_file = governance_dir / "2026-07-06-weekly-governance.md"
            signoff_file = governance_dir / "2026-07-06-staging-serious-window-signoff.md"
            _write_workflow_file(workflow_file)
            _write_weekly_file(weekly_file, window_id=window_id, mode="baseline", environment_name="staging-serious")
            _write_signoff_file(signoff_file, window_id=window_id, mode="baseline", environment_name="staging-serious")

            model = MODULE.build_dispatch_packet_model(
                window_id=window_id,
                mode="baseline",
                environment_name="staging-serious",
                governance_weekly_dir=governance_dir,
                workflow_file=workflow_file,
                workflow_name="Staging Serious Window",
            )
            content = MODULE.render_dispatch_packet_markdown(model)

        self.assertIn("# Serious Window Dispatch Packet — `stg-2026-07-06-a`", content)
        self.assertIn('make preflight-serious-window-dispatch WINDOW_ID="stg-2026-07-06-a"', content)
        self.assertIn("serious-staging-window-stg-2026-07-06-a", content)
        self.assertIn("2026-07-06-weekly-governance.md", content)
        self.assertIn("2026-07-06-staging-serious-window-signoff.md", content)

    def test_main_writes_json_when_output_file_is_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            governance_dir = base / "docs" / "governance-weekly"
            workflow_file = base / ".github" / "workflows" / "staging-serious-window.yml"
            output_file = base / "ci-artifacts" / "dispatch-packet.md"
            governance_dir.mkdir(parents=True, exist_ok=True)
            workflow_file.parent.mkdir(parents=True, exist_ok=True)

            window_id = "stg-2026-07-06-a"
            weekly_file = governance_dir / "2026-07-06-weekly-governance.md"
            signoff_file = governance_dir / "2026-07-06-staging-serious-window-signoff.md"
            _write_workflow_file(workflow_file)
            _write_weekly_file(weekly_file, window_id=window_id, mode="baseline", environment_name="staging-serious")
            _write_signoff_file(signoff_file, window_id=window_id, mode="baseline", environment_name="staging-serious")

            stdout = io.StringIO()
            with patch(
                "sys.argv",
                [
                    "render_serious_window_dispatch_packet.py",
                    "--window-id",
                    window_id,
                    "--mode",
                    "baseline",
                    "--environment-name",
                    "staging-serious",
                    "--governance-weekly-dir",
                    str(governance_dir),
                    "--workflow-file",
                    str(workflow_file),
                    "--output-file",
                    str(output_file),
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            payload = json.loads(stdout.getvalue())
            rendered = output_file.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["readiness_status"], "ok")
        self.assertIn("## Comandos", rendered)
        self.assertIn("make postprocess-serious-window", rendered)


if __name__ == "__main__":
    unittest.main()
