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


MODULE = _load_module("prepare_staging_window", "scripts/prepare_staging_window.py")


def _write_env_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "APP_ENV=staging",
                "MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false",
                "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__",
                "KEYCLOAK_ADMIN_PASSWORD=__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                "ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_private_env_file(target: Path, *, homologated: bool, fill_required: bool = True) -> None:
    values = [
        "APP_ENV=staging",
        "AUTH_MODE=oidc",
        "DEV_AUTH_ENABLED=false",
        "NEXT_PUBLIC_AUTH_MODE=oidc",
        "NEXT_PUBLIC_APP_ENV=staging",
        "NEXT_PUBLIC_DEV_AUTH_ENABLED=false",
        f"MFA_EXTERNAL_PROVIDER_HOMOLOGATED={'true' if homologated else 'false'}",
        "OIDC_PROVIDER=keycloak",
        "NEXT_PUBLIC_API_BASE_URL=https://staging-api.example.com",
        "KEYCLOAK_PUBLIC_URL=https://keycloak.example.com",
        "KEYCLOAK_ADMIN_PASSWORD=strong-password" if fill_required else "KEYCLOAK_ADMIN_PASSWORD=",
        "KEYCLOAK_B2B_CLIENT_SECRET=client-secret",
        "JWT_HS256_SECRET=jwt-secret",
        "MFA_TOTP_SECRET=totp-secret",
        "OIDC_ISSUER_URL=https://issuer.example.com/realms/ontrackchain",
        "OIDC_AUDIENCE=ontrackchain",
        "OIDC_CLIENT_ID=frontend-client",
        "OIDC_JWKS_URL=https://issuer.example.com/realms/ontrackchain/protocol/openid-connect/certs",
        "OIDC_AUTHORIZATION_URL=https://issuer.example.com/realms/ontrackchain/protocol/openid-connect/auth",
        "OIDC_ORG_CLAIM=org_id",
        "OIDC_PLAN_CLAIM=plan",
        "OIDC_ROLE_CLAIM=roles",
        "ONTRACKCHAIN_ALLOW_INSECURE_OIDC_URLS=false",
        "ONTRACKCHAIN_ALLOW_LOCALHOST_OIDC_URLS=false",
        "INVESTIGATION_RPC_ENABLED=true",
        "INVESTIGATION_RPC_PROVIDER=evm_rpc",
        "INVESTIGATION_RPC_PRIMARY_URL=",
        "INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example.com",
        "INVESTIGATION_RPC_TIMEOUT_MS=5000",
        "INVESTIGATION_RPC_MAX_RETRIES=2",
        "COMPLIANCE_TRM_ENABLED=true",
        "COMPLIANCE_RISK_PROVIDER=trm_labs",
        "COMPLIANCE_TRM_SCREENING_URL=https://trm.example.com/screening",
        "COMPLIANCE_TRM_API_KEY=trm-key",
        "COMPLIANCE_TRM_TIMEOUT_MS=5000",
        "COMPLIANCE_TRM_MAX_RETRIES=2",
        "ONTRACKCHAIN_ALLOW_INSECURE_PROVIDER_URLS=false",
        "ONTRACKCHAIN_ALLOW_LOCAL_PROVIDER_URLS=false",
        "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
        "ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only",
    ]
    if homologated:
        values.append("ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=real-oidc-token")
    else:
        values.append("ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__")
    target.write_text("\n".join(values) + "\n", encoding="utf-8")


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
                "| `__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__` | `Backend/Auth` | `Security` | credencial admin validada |",
                "| `__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__` | `Backend/Auth` | `Security` | token OIDC controlado |",
                "",
                "## Registro de Handoff",
                "",
                "| Grupo | Owner | Data | Status | Observacoes |",
                "| --- | --- | --- | --- | --- |",
                "| Auth/OIDC | `Backend/Auth` | `2026-06-30` | `approved` | pronto para janela |",
                "| Compliance/AML | `Compliance/Backend` | `2026-06-30` | `approved` | provider confirmado |",
                "| Investigation/RPC | `Backend Core` | `2026-06-30` | `reviewed` | fallback_only aceito |",
                "| Platform/Operations | `Platform/SRE` | `2026-06-30` | `approved` | artefatos preparados |",
                "",
            ]
        ),
        encoding="utf-8",
    )


class PrepareStagingWindowTests(unittest.TestCase):
    maxDiff = None

    def test_prepare_window_generates_private_env_and_packet_for_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-a",
                mode="baseline",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=False,
                preflight=False,
                run=False,
            )

            private_env_content = private_env_file.read_text(encoding="utf-8")
            packet_content = Path(payload["artifacts"]["window_packet_file"]).read_text(encoding="utf-8")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "baseline")
        self.assertIn("MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false", private_env_content)
        self.assertIn("MFA federado homologado", packet_content)
        self.assertIn("placeholder e `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false`", payload["next_steps"][1])

    def test_prepare_window_generates_private_env_and_packet_for_homologated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-b",
                mode="homologated",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=False,
                preflight=False,
                run=False,
            )

            private_env_content = private_env_file.read_text(encoding="utf-8")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["mode"], "homologated")
        self.assertIn("MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true", private_env_content)
        self.assertIn("token OIDC administrativo valido", payload["next_steps"][1])

    def test_main_emits_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"
            stdout = io.StringIO()

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)

            with patch.object(
                sys,
                "argv",
                [
                    "prepare_staging_window.py",
                    "--window-id",
                    "stg-2026-06-30-a",
                    "--mode",
                    "baseline",
                    "--env-file",
                    str(env_file),
                    "--ownership-file",
                    str(ownership_file),
                    "--private-env-file",
                    str(private_env_file),
                    "--templates-dir",
                    str(templates_dir),
                    "--window-packet-dir",
                    str(packet_dir),
                    "--checks-dir",
                    str(checks_dir),
                    "--dossiers-dir",
                    str(dossiers_dir),
                    "--homologation-dir",
                    str(homologation_dir),
                    "--generated-at",
                    "2026-06-30T12:00:00+00:00",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            payload = json.loads(stdout.getvalue())
            private_env_exists = Path(payload["artifacts"]["private_env_file"]).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["window_id"], "stg-2026-06-30-a")
        self.assertTrue(private_env_exists)

    def test_prepare_window_with_validate_persists_successful_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=False, fill_required=True)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-c",
                mode="baseline",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=True,
                preflight=False,
                run=False,
            )

            check_files = sorted(path.name for path in checks_dir.glob("*.json"))

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["validation"]["status"], "ok")
        self.assertTrue(payload["summary"]["private_env_preserved_for_validation"])
        self.assertEqual(len(payload["validation"]["checks"]), 3)
        self.assertEqual(
            check_files,
            [
                "stg-2026-06-30-c-handoff.json",
                "stg-2026-06-30-c-ownership_coverage.json",
                "stg-2026-06-30-c-placeholders.json",
            ],
        )

    def test_prepare_window_with_validate_fails_when_placeholder_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=True, fill_required=False)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-d",
                mode="homologated",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=True,
                preflight=False,
                run=False,
            )

        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["validation"]["status"], "failed")
        self.assertTrue(payload["summary"]["private_env_preserved_for_validation"])
        self.assertEqual(payload["next_steps"][0], "Corrigir os checks em `artifacts/staging/checks` antes de executar a janela completa.")
        placeholder_result = next(
            check for check in payload["validation"]["checks"] if check["name"] == "placeholders"
        )
        self.assertEqual(placeholder_result["status"], "failed")

    def test_prepare_window_with_preflight_runs_preflights_after_successful_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=False, fill_required=True)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-e",
                mode="baseline",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=False,
                preflight=True,
                run=False,
            )

            preflight_files = sorted(
                path.name
                for path in checks_dir.glob("*.json")
                if path.name in {"stg-2026-06-30-e-oidc_preflight.json", "stg-2026-06-30-e-external_preflight.json"}
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["validation"]["status"], "ok")
        self.assertEqual(payload["preflight"]["status"], "ok")
        self.assertTrue(payload["summary"]["private_env_preserved_for_validation"])
        self.assertEqual(len(payload["preflight"]["checks"]), 2)
        self.assertEqual(
            sorted(check["name"] for check in payload["preflight"]["checks"]),
            ["external_preflight", "oidc_preflight"],
        )
        self.assertEqual(
            preflight_files,
            [
                "stg-2026-06-30-e-external_preflight.json",
                "stg-2026-06-30-e-oidc_preflight.json",
            ],
        )

    def test_prepare_window_with_preflight_skips_preflights_when_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=True, fill_required=False)

            payload = MODULE.prepare_window(
                window_id="stg-2026-06-30-f",
                mode="homologated",
                env_file=env_file,
                ownership_file=ownership_file,
                private_env_file=private_env_file,
                templates_dir=templates_dir,
                window_packet_dir=packet_dir,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                homologation_dir=homologation_dir,
                generated_at="2026-06-30T12:00:00+00:00",
                validate=False,
                preflight=True,
                run=False,
            )

        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["validation"]["status"], "failed")
        self.assertEqual(payload["preflight"]["status"], "skipped")
        self.assertEqual(payload["preflight"]["reason"], "validation_failed")

    def test_prepare_window_with_run_executes_runner_after_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=False, fill_required=True)

            with patch.object(
                MODULE,
                "run_window_execution",
                return_value={
                    "enabled": True,
                    "status": "ok",
                    "exit_code": 0,
                    "output_file": str(checks_dir / "stg-2026-06-30-run_window.json"),
                    "payload": {"status": "ok"},
                    "errors": [],
                },
            ) as run_mock:
                payload = MODULE.prepare_window(
                    window_id="stg-2026-06-30-run",
                    mode="baseline",
                    env_file=env_file,
                    ownership_file=ownership_file,
                    private_env_file=private_env_file,
                    templates_dir=templates_dir,
                    window_packet_dir=packet_dir,
                    checks_dir=checks_dir,
                    dossiers_dir=dossiers_dir,
                    homologation_dir=homologation_dir,
                    generated_at="2026-06-30T12:00:00+00:00",
                    validate=False,
                    preflight=False,
                    run=True,
                )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["validation"]["status"], "ok")
        self.assertEqual(payload["preflight"]["status"], "ok")
        self.assertEqual(payload["run"]["status"], "ok")
        self.assertTrue(run_mock.called)

    def test_prepare_window_with_run_skips_runner_when_preflight_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            ownership_file = base / "staging-env-ownership.md"
            private_env_file = base / ".env.staging.private"
            templates_dir = base / "artifacts" / "templates"
            packet_dir = base / "artifacts" / "staging"
            checks_dir = base / "artifacts" / "checks"
            dossiers_dir = base / "artifacts" / "dossiers"
            homologation_dir = base / "artifacts" / "homologation"

            _write_env_file(env_file)
            _write_ownership_file(ownership_file)
            _write_private_env_file(private_env_file, homologated=False, fill_required=True)

            with patch.object(
                MODULE,
                "run_preflight_checks",
                return_value={"enabled": True, "status": "failed", "checks": [], "errors": ["boom"]},
            ), patch.object(MODULE, "run_window_execution") as run_mock:
                payload = MODULE.prepare_window(
                    window_id="stg-2026-06-30-run-failed",
                    mode="baseline",
                    env_file=env_file,
                    ownership_file=ownership_file,
                    private_env_file=private_env_file,
                    templates_dir=templates_dir,
                    window_packet_dir=packet_dir,
                    checks_dir=checks_dir,
                    dossiers_dir=dossiers_dir,
                    homologation_dir=homologation_dir,
                    generated_at="2026-06-30T12:00:00+00:00",
                    validate=False,
                    preflight=False,
                    run=True,
                )

        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["preflight"]["status"], "failed")
        self.assertEqual(payload["run"]["status"], "skipped")
        self.assertEqual(payload["run"]["reason"], "preflight_failed")
        self.assertFalse(run_mock.called)


if __name__ == "__main__":
    unittest.main()
