"""
QA Gateway Q3-08 scan-secrets-trufflehog + Q3-09 run-pre-merge-gates contrato pytest (12 casos).

ADR-029 DoD 029.6 — 12 testes pytest: 8 × scan-secrets + 4 × run-pre-merge-gates.

Estratégia: monkeypatch `subprocess.run` para simular saídas do trufflehog e comandos qa-gateway
subprocesso do orquestrador. NUNCA roda trufflehog REAL (são 20min+ e precisa de rede).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from click.testing import CliRunner

from qa_gateway.cli import cli


# ---------------------------------------------------------------------------
# Helpers mock subprocess.run
# ---------------------------------------------------------------------------
class FakeProcessResult:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _make_trufflehog_zero_findings(returncode: int = 0) -> FakeProcessResult:
    return FakeProcessResult(returncode=returncode, stdout="", stderr="")


def _make_trufflehog_2_verified_findings() -> FakeProcessResult:
    finding1 = {
        "Verified": True,
        "DetectorName": "aws-access-key",
        "Raw": "AKIAIOSFODNN7EXAMPLE + secret key prefix",
        "SourceMetadata": {
            "Data": {"Filesystem": {"file": ".env.prod.private", "line": 3}}
        },
    }
    finding2 = {
        "Verified": True,
        "DetectorName": "slack-webhook",
        "Raw": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX prefix",
        "SourceMetadata": {
            "Data": {"Filesystem": {"file": "apps/frontend/.env.local", "line": 12}}
        },
    }
    stdout = json.dumps(finding1) + "\n" + json.dumps(finding2) + "\n"
    return FakeProcessResult(returncode=1, stdout=stdout, stderr="")


def _make_trufflehog_timeout(monkeypatch):
    def _sub_run(cmd, capture_output=True, text=True, timeout=None):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)
    return _sub_run


def _build_qa_subprocess_side_effect(
    exit_map: Dict[str, int],
    issues_map: Optional[Dict[str, List[str]]] = None,
    warnings_map: Optional[Dict[str, List[str]]] = None,
):
    """Mapeia primeiro token do comando (ex: scan-rbac) → exit code + mensagens."""
    issues_map = issues_map or {}
    warnings_map = warnings_map or {}

    def side_effect(cmd, capture_output=True, text=True, timeout=None):
        if len(cmd) < 2:
            return FakeProcessResult(returncode=0)
        token = cmd[1]
        exit_code = exit_map.get(token, 0)
        stdout_chunks: List[str] = []
        for issue in issues_map.get(token, []):
            stdout_chunks.append(f"  ❌ {issue}")
        for warn in warnings_map.get(token, []):
            stdout_chunks.append(f"  ⚠️  {warn}")
        stdout = "\n".join(stdout_chunks) + ("\n" if stdout_chunks else "")
        return FakeProcessResult(returncode=exit_code, stdout=stdout, stderr="")
    return side_effect


# ---------------------------------------------------------------------------
# 8 Testes Q3-08: scan-secrets-trufflehog
# ---------------------------------------------------------------------------
class TestScanSecretsTrufflehogQ308:
    def setup_method(self):
        self.runner = CliRunner()

    def test_q3_08_01_dry_run_no_bin(self, monkeypatch):
        """Caso 1: dry-run, trufflehog não instalado → warning TS-W001, exit 0 (dry run não é erro)."""
        # força _find_trufflehog_bin → None
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: None)
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog", "--dry-run"])
        assert result.exit_code == 0
        assert "TS-W001" in result.output or "dry-run" in result.output

    def test_q3_08_02_dry_run_bin_found_ok(self, monkeypatch):
        """Caso 2: dry-run, binário encontrado → ✅ detectado, exit 0."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/fake-th")
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog", "--dry-run"])
        assert result.exit_code == 0
        assert "Binário detectado" in result.output or "✅" in result.output

    def test_q3_08_03_bin_not_found_not_dry_exit1(self, monkeypatch):
        """Caso 3: Não dry-run, binário não existe → TS-E001 exit=1."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: None)
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog"])
        assert result.exit_code == 1
        assert "TS-E001" in result.output

    def test_q3_08_04_zero_findings_exit0(self, monkeypatch):
        """Caso 4: trufflehog executou, 0 findings, exit 0, 0 issues."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/th")
        def sub_run(*args, **kwargs):
            return _make_trufflehog_zero_findings(returncode=0)
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", sub_run)
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog"])
        assert result.exit_code == 0
        assert "Achados VERIFICADOS: 0" in result.output

    def test_q3_08_05_timeout_2h_exit1(self, monkeypatch):
        """Caso 5: Timeout 2h → TS-E002 exit=1."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/th")
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", _make_trufflehog_timeout(monkeypatch))
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog"])
        assert result.exit_code == 1
        assert "TS-E002" in result.output

    def test_q3_08_06_two_verified_findings_strict_exit1(self, monkeypatch):
        """Caso 6: 2 segredos VERIFICADOS → 2× TS-E (fail-verified), exit=1 P0."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/th")
        def sub_run(*args, **kwargs):
            return _make_trufflehog_2_verified_findings()
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", sub_run)
        result = self.runner.invoke(cli, ["scan-secrets-trufflehog"])
        assert result.exit_code == 1
        assert "TS-E001" in result.output or "Segredo VERIFICADO" in result.output

    def test_q3_08_07_warnings_exceed_max_strict_exit1(self, monkeypatch):
        """Caso 7: 3 warnings (stderr filtros + W003), max-warnings=1 STRICT → warnings elevados a issues exit=1."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/th")
        def sub_run(*args, **kwargs):
            stderr = (
                "WARN filter unused1\nWARN filter unused2\nWARN invalid regex filter\n"
            )
            return FakeProcessResult(returncode=3, stdout="", stderr=stderr)
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", sub_run)
        result = self.runner.invoke(cli, [
            "scan-secrets-trufflehog", "--max-warnings", "1", "--strict"
        ])
        assert result.exit_code == 1
        assert "STRICT default" in result.output or "WARNINGS elevados" in result.output

    def test_q3_08_08_no_fail_verified_2_findings_become_warnings(self, monkeypatch):
        """Caso 8: --no-fail-verified, 2 findings → viram warnings (TS-W), não issues. exit 0 se warnings<=max."""
        monkeypatch.setattr("qa_gateway.cli._find_trufflehog_bin", lambda: "/tmp/th")
        def sub_run(*args, **kwargs):
            return _make_trufflehog_2_verified_findings()
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", sub_run)
        # --max-warnings 5 + strict aceita 2 warnings → exit 0
        result = self.runner.invoke(cli, [
            "scan-secrets-trufflehog", "--no-fail-verified",
            "--max-warnings", "5", "--strict"
        ])
        assert result.exit_code == 0
        assert (
            "TS-W001" in result.output
            or "[TS-W" in result.output
            or "warning(s)" in result.output
        )


# ---------------------------------------------------------------------------
# 4 Testes Q3-09: run-pre-merge-gates orquestrador ADR-029
# ---------------------------------------------------------------------------
class TestRunPreMergeGatesQ309:
    def setup_method(self):
        self.runner = CliRunner()

    def test_q3_09_01_dry_run_all_pass_exit0_report_exists(self, tmp_path, monkeypatch):
        """Caso 1: --dry-run, todos gates passam, exit=0, arquivo JSON consolidado criado com schema 1.0."""
        report_dir = str(tmp_path / "qa-reports")
        result = self.runner.invoke(cli, [
            "run-pre-merge-gates",
            "--dpo-email", "dpo@ontrackchain.com.br",
            "--dry-run",
            "--report-dir", report_dir,
        ])
        assert result.exit_code == 0, result.output
        # Procurar relatório JSON
        report_files = list(Path(report_dir).glob("pre-merge-local-*.json"))
        assert len(report_files) == 1
        data = json.loads(report_files[0].read_text())
        assert data["schema_version"] == "1.0"
        assert data["dpo_email"] == "dpo@ontrackchain.com.br"
        assert data["dry_run"] is True
        assert data["overall_exit"] == 0
        assert len(data["gates"]) == 5  # Q1 Q2 Q3 Q4 Q5

    def test_q3_09_02_enforce_all_true_skip_proibido_exit1(self, monkeypatch):
        """Caso 2: OTK_CI_PRE_MERGE_ENFORCE_ALL=true + --skip-q1 → exit 1, skips proibidos."""
        monkeypatch.setenv("OTK_CI_PRE_MERGE_ENFORCE_ALL", "true")
        result = self.runner.invoke(cli, [
            "run-pre-merge-gates",
            "--dpo-email", "dpo@ontrackchain.com.br",
            "--skip-q1",
        ])
        assert result.exit_code == 1
        assert "OTK_CI_PRE_MERGE_ENFORCE_ALL=true" in result.output

    def test_q3_09_03_failfast_q1_fail_q5_still_runs_exit1(self, tmp_path, monkeypatch):
        """Caso 3: Q1-RBAC falha (issues). Fail-FAST skips Q2/Q3/Q4 MAS Q5 SEMPRE roda. overall_exit=1."""
        exit_map: Dict[str, int] = {
            "scan-rbac": 1,
            "scan-billing-capabilities": 0,
            "scan-billing-enforcement": 0,
            "scan-lgpd-ropd": 0,
            "scan-secrets-trufflehog": 0,
        }
        issues_map: Dict[str, List[str]] = {
            "scan-rbac": ["Rotas /api/v1/deletar SEM rbac_required — vulnerável ADR-018"],
        }
        side = _build_qa_subprocess_side_effect(exit_map, issues_map=issues_map)
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", side)
        report_dir = str(tmp_path / "qa-reports")
        result = self.runner.invoke(cli, [
            "run-pre-merge-gates",
            "--dpo-email", "dpo@ontrackchain.com.br",
            "--report-dir", report_dir,
        ])
        assert result.exit_code == 1, result.output
        # Verificar relatório: Q1 exit=1 + skipped=[]; Q5 exit=0 skipped=False
        files = list(Path(report_dir).glob("pre-merge-*.json"))
        assert len(files) == 1
        report = json.loads(files[0].read_text())
        q1 = next(g for g in report["gates"] if g["id"] == "Q1-RBAC")
        q5 = next(g for g in report["gates"] if g["id"] == "Q5-SECRETS")
        assert q1["exit"] == 1
        assert q5["skipped"] is False
        assert q5["exit"] == 0  # Q5 SEMPRE rodou

    def test_q3_09_04_q5_secrets_fail_always_blocks_exit1(self, tmp_path, monkeypatch):
        """Caso 4: Q1-Q4 passam tudo, Q5 detecta 2 segredos TS-E → overall_exit=1 bloqueia merge."""
        exit_map = {
            "scan-rbac": 0,
            "scan-billing-capabilities": 0,
            "scan-billing-enforcement": 0,
            "scan-lgpd-ropd": 0,
            "scan-secrets-trufflehog": 1,
        }
        issues_map = {
            "scan-secrets-trufflehog": [
                "TS-E001 AWS .env AKIAIOSFODNN7EXAMPLE",
                "TS-E002 Slack webhook XXXXXXXXXXXXXXXXXXXXXXXX",
            ]
        }
        side = _build_qa_subprocess_side_effect(exit_map, issues_map=issues_map)
        monkeypatch.setattr("qa_gateway.cli.subprocess.run", side)
        report_dir = str(tmp_path / "qa-reports")
        result = self.runner.invoke(cli, [
            "run-pre-merge-gates",
            "--dpo-email", "dpo@ontrackchain.com.br",
            "--report-dir", report_dir,
        ])
        assert result.exit_code == 1, result.output
        files = list(Path(report_dir).glob("pre-merge-*.json"))
        assert len(files) == 1
        report = json.loads(files[0].read_text())
        assert report["overall_exit"] == 1
        q5 = next(g for g in report["gates"] if g["id"] == "Q5-SECRETS")
        assert len(q5["issues"]) == 2
