import importlib.util
import io
import json
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
    "run_oidc_playwright_critical",
    "scripts/run_oidc_playwright_critical.py",
)


class RunOidcPlaywrightCriticalTests(unittest.TestCase):
    def test_build_payload_marks_success_and_detects_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            frontend_dir = Path(tmp_dir)
            (frontend_dir / "playwright-report").mkdir()
            test_results_dir = frontend_dir / "test-results"
            test_results_dir.mkdir()
            (test_results_dir / "junit.xml").write_text("<xml />\n", encoding="utf-8")

            payload = MODULE.build_payload(
                base_url="https://app.staging.example.com",
                frontend_dir=frontend_dir,
                suite_command="npm run test:e2e:oidc-critical",
                exit_code=0,
                stdout_text="all green\n",
                stderr_text="",
            )

        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["artifacts"]["playwright_report_present"])
        self.assertTrue(payload["artifacts"]["junit_report_present"])

    def test_main_fails_when_npm_is_missing(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir:
            with (
                patch.object(
                    MODULE,
                    "parse_args",
                    return_value=type(
                        "Args",
                        (),
                        {
                            "base_url": "https://app.staging.example.com",
                            "frontend_dir": tmp_dir,
                            "suite_command": "npm run test:e2e:oidc-critical",
                        },
                    )(),
                ),
                patch.object(MODULE.shutil, "which", return_value=None),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = MODULE.main()

        self.assertEqual(exit_code, 1)
        payload = json.loads(stderr.getvalue().strip() or stdout.getvalue().strip())
        self.assertEqual(payload["status"], "failed")
        self.assertIn("npm_ausente_no_runner", payload["errors"])

    def test_main_runs_suite_with_test_base_url(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_completed = type(
                "CompletedProcess",
                (),
                {
                    "returncode": 0,
                    "stdout": "passed\n",
                    "stderr": "",
                },
            )()
            with (
                patch.object(
                    MODULE,
                    "parse_args",
                    return_value=type(
                        "Args",
                        (),
                        {
                            "base_url": "https://app.staging.example.com",
                            "frontend_dir": tmp_dir,
                            "suite_command": "npm run test:e2e:oidc-critical",
                        },
                    )(),
                ),
                patch.object(MODULE.shutil, "which", return_value="/usr/bin/npm"),
                patch.object(MODULE.subprocess, "run", return_value=fake_completed) as mock_run,
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        kwargs = mock_run.call_args.kwargs
        self.assertEqual(kwargs["env"]["TEST_BASE_URL"], "https://app.staging.example.com")
        payload = json.loads(stdout.getvalue().strip() or stderr.getvalue().strip())
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()
