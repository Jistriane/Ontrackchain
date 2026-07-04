import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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
    "check_workflow_hygiene",
    "scripts/check_workflow_hygiene.py",
)


def _write_workflow(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckWorkflowHygieneTests(unittest.TestCase):
    maxDiff = None

    def test_main_passes_when_workflow_has_required_hygiene_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "ok.yml",
                "\n".join(
                    [
                        "name: Sample",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: make check-workflow-hygiene",
                    ]
                )
                + "\n",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("OK: workflow hygiene sem regressao detectada", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_main_fails_when_required_hygiene_step_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "missing.yml",
                "\n".join(
                    [
                        "name: Missing Hygiene",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo hello",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("ausencia do passo obrigatorio", stderr.getvalue())

    def test_main_does_not_accept_required_step_only_in_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "comment-only.yml",
                "\n".join(
                    [
                        "name: Comment Only",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      # make check-workflow-hygiene",
                        "      - run: echo hello",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("ausencia do passo obrigatorio", stderr.getvalue())

    def test_main_validates_yaml_extension_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "missing.yaml",
                "\n".join(
                    [
                        "name: YAML Missing",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo hello",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("missing.yaml", stderr.getvalue())

    def test_main_does_not_accept_inline_echo_or_printf_as_hygiene_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "echo-inline.yml",
                "\n".join(
                    [
                        "name: Echo Inline",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: echo 'make check-workflow-hygiene'",
                    ]
                )
                + "\n",
            )
            _write_workflow(
                workflows_dir / "printf-inline.yml",
                "\n".join(
                    [
                        "name: Printf Inline",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: printf '%s\\n' 'make check-workflow-hygiene'",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        err = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("echo-inline.yml", err)
        self.assertIn("printf-inline.yml", err)

    def test_main_accepts_executable_step_with_prefix_before_make(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "prefixed.yml",
                "\n".join(
                    [
                        "name: Prefixed",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: PYTHON=python make check-workflow-hygiene",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_main_accepts_canonical_run_field_with_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "canonical-run.yml",
                "\n".join(
                    [
                        "name: Canonical Run",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - name: Validate",
                        "        run: make check-workflow-hygiene",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_main_accepts_multiline_run_block_with_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "multiline-run.yml",
                "\n".join(
                    [
                        "name: Multiline Run",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - name: Validate",
                        "        run: |",
                        "          echo preparing",
                        "          make check-workflow-hygiene",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_main_does_not_accept_command_only_as_argument_string(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "string-arg.yml",
                "\n".join(
                    [
                        "name: String Arg",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: python -c \"print('make check-workflow-hygiene')\"",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("ausencia do passo obrigatorio", stderr.getvalue())

    def test_main_accepts_command_in_if_then_shell_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "if-then.yml",
                "\n".join(
                    [
                        "name: If Then",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: if [ \"$CI\" = \"true\" ]; then make check-workflow-hygiene; fi",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_main_accepts_command_with_and_chaining(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "chained.yml",
                "\n".join(
                    [
                        "name: Chained",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: make check-workflow-hygiene && echo done",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")

    def test_main_fails_on_unsafe_patterns_even_with_required_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "unsafe.yml",
                "\n".join(
                    [
                        "name: Unsafe Patterns",
                        "on: [push]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    if: secrets.SLACK_WEBHOOK_URL != ''",
                        "    steps:",
                        "      - run: make check-workflow-hygiene",
                        "      - run: |",
                        "          cat > out.json << 'EOF'",
                        "          {\"ts\": \"$(date -u --iso-8601=seconds)\"}",
                        "          EOF",
                        "      - uses: actions/github-script@v7",
                        "        with:",
                        "          script: |",
                        "            github.rest.issues.createComment({",
                        "              issue_number: context.issue.number,",
                        "              owner: context.repo.owner,",
                        "              repo: context.repo.repo,",
                        "              body: 'x'",
                        "            });",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        err = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("uso de secrets em if", err)
        self.assertIn("heredoc quoted", err)
        self.assertIn("context.issue.number", err)

    def test_main_allows_context_issue_number_when_pull_request_event_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            workflows_dir = Path(tmp_dir) / ".github" / "workflows"
            _write_workflow(
                workflows_dir / "pr.yml",
                "\n".join(
                    [
                        "name: PR Comment",
                        "on:",
                        "  pull_request:",
                        "    branches: [main]",
                        "jobs:",
                        "  sample:",
                        "    runs-on: ubuntu-latest",
                        "    steps:",
                        "      - run: make check-workflow-hygiene",
                        "      - uses: actions/github-script@v7",
                        "        with:",
                        "          script: |",
                        "            github.rest.issues.createComment({",
                        "              issue_number: context.issue.number,",
                        "              owner: context.repo.owner,",
                        "              repo: context.repo.repo,",
                        "              body: 'ok'",
                        "            });",
                    ]
                )
                + "\n",
            )

            stderr = io.StringIO()
            with patch.object(MODULE, "WORKFLOWS_DIR", workflows_dir):
                with redirect_stderr(stderr):
                    exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
