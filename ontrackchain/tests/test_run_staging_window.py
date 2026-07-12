import importlib.util
import json
import tempfile
import unittest
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
    "run_staging_window",
    "scripts/run_staging_window.py",
)


def _write_env_file(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "KEYCLOAK_ADMIN_PASSWORD=__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                "KEYCLOAK_B2B_CLIENT_SECRET=__FILL_STAGING_KEYCLOAK_B2B_CLIENT_SECRET__",
                "JWT_HS256_SECRET=__FILL_STAGING_JWT_HS256_SECRET__",
                "MFA_TOTP_SECRET=__FILL_STAGING_MFA_TOTP_SECRET__",
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
                "| `__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__` | `Backend/Auth` | `Security` | credencial admin validada |",
                "| `__FILL_STAGING_KEYCLOAK_B2B_CLIENT_SECRET__` | `Backend/Auth` | `Security` | secret OIDC validado |",
                "| `__FILL_STAGING_JWT_HS256_SECRET__` | `Security` | `Backend/Auth` | secret JWT rotacionado |",
                "| `__FILL_STAGING_MFA_TOTP_SECRET__` | `Security` | `Backend/Auth` | segredo MFA emitido |",
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


def _write_private_env_file(target: Path, *, unresolved_jwt: bool = False) -> None:
    jwt_secret = "__FILL_STAGING_JWT_HS256_SECRET__" if unresolved_jwt else "jwt-secret-staging"
    target.write_text(
        "\n".join(
            [
                "APP_ENV=staging",
                "AUTH_MODE=oidc",
                "DEV_AUTH_ENABLED=false",
                "NEXT_PUBLIC_AUTH_MODE=oidc",
                "NEXT_PUBLIC_APP_ENV=staging",
                "NEXT_PUBLIC_DEV_AUTH_ENABLED=false",
                "OIDC_PROVIDER=keycloak",
                "NEXT_PUBLIC_API_BASE_URL=https://app.staging.ontrackchain.com",
                "KEYCLOAK_PUBLIC_URL=https://auth.staging.ontrackchain.com",
                "KEYCLOAK_ADMIN_PASSWORD=kc-admin-secret",
                "KEYCLOAK_B2B_CLIENT_SECRET=kc-b2b-secret",
                f"JWT_HS256_SECRET={jwt_secret}",
                "MFA_TOTP_SECRET=MZXW6YTBOI======",
                "OIDC_ISSUER_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain",
                "OIDC_AUDIENCE=ontrackchain-api",
                "OIDC_CLIENT_ID=ontrackchain-web",
                "OIDC_JWKS_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/certs",
                "OIDC_AUTHORIZATION_URL=https://auth.staging.ontrackchain.com/realms/ontrackchain/protocol/openid-connect/auth",
                "OIDC_ORG_CLAIM=org",
                "OIDC_PLAN_CLAIM=plan",
                "OIDC_ROLE_CLAIM=otk_role",
                "INVESTIGATION_RPC_ENABLED=true",
                "INVESTIGATION_RPC_PRIMARY_URL=https://rpc-primary.example",
                "INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example",
                "INVESTIGATION_RPC_TIMEOUT_MS=1500",
                "INVESTIGATION_RPC_MAX_RETRIES=1",
                "INVESTIGATION_RPC_PROVIDER=evm_rpc",
                "COMPLIANCE_TRM_ENABLED=true",
                "COMPLIANCE_TRM_SCREENING_URL=https://provider.example/screening",
                "COMPLIANCE_TRM_API_KEY=trm-secret",
                "COMPLIANCE_TRM_TIMEOUT_MS=1500",
                "COMPLIANCE_TRM_MAX_RETRIES=1",
                "COMPLIANCE_RISK_PROVIDER=trm_labs",
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                "ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only",
                "",
            ]
        ),
        encoding="utf-8",
    )


class RunStagingWindowTests(unittest.TestCase):
    maxDiff = None

    def test_run_window_happy_path_writes_checks_packet_and_dossier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            private_env_file = base / ".env.staging.private"
            ownership_file = base / "staging-env-ownership.md"
            checks_dir = base / "artifacts" / "checks"
            packet_file = base / "artifacts" / "window-packet.md"
            homologation_output_dir = base / "artifacts" / "homologation"
            dossier_output_dir = base / "artifacts" / "dossiers"

            _write_env_file(env_file)
            _write_private_env_file(private_env_file)
            _write_ownership_file(ownership_file)

            def fake_run_module_main(relative_path: str, argv: list[str], module_name: str):
                if relative_path.endswith("preflight_oidc_serious_env.py"):
                    return 0, {"status": "ok", "auth_mode": "oidc", "errors": []}
                if relative_path.endswith("preflight_external_integrations.py"):
                    return 0, {"status": "ok", "compliance": {"expect_mode": "live"}, "rpc": {"expect_mode": "fallback_only"}, "errors": []}
                if relative_path.endswith("run_oidc_readiness_bundle.py"):
                    return 0, {
                        "kind": "oidc_readiness_bundle",
                        "status": "ok",
                        "readiness": {
                            "readiness_status": "ready",
                            "blockers": ["provider MFA/OIDC ainda nao esta homologado para trilho serio"],
                            "next_action": "Substituir placeholders por provider serio homologado e rerodar o bundle com insumos reais.",
                        },
                        "scope": {
                            "mfa_external_provider_homologated": "false",
                            "expected_oidc_provider": "keycloak",
                        },
                        "steps": {
                            "oidc_preflight": {"status": "ok"},
                            "smoke_auth_oidc_mode": {"status": "ok"},
                        },
                        "errors": [],
                    }
                if relative_path.endswith("run_regulatory_readiness_bundle.py"):
                    return 0, {
                        "kind": "regulatory_readiness_bundle",
                        "status": "ok",
                        "readiness": {
                            "compliance_runtime": {
                                "readiness_status": "ready_for_validation",
                                "blockers": [],
                                "next_action": "Revisar o artefato de `compliance_provider_runtime` e anexar o bundle regulatorio a governanca semanal.",
                            },
                            "eu_window": {
                                "readiness_status": "ready",
                                "blockers": [],
                                "next_action": "Habilitar a trilha `eu_sanctions_window` com insumo real e rerodar o bundle regulatorio.",
                            },
                            "regulatory_bundle": {
                                "readiness_status": "ready_for_validation",
                                "blockers": [],
                                "next_action": "Anexar o bundle regulatorio ao dossier/governanca e executar revisao formal das evidencias.",
                            },
                        },
                        "scope": {
                            "compliance_runtime_enabled": True,
                            "eu_window_enabled": False,
                        },
                        "steps": {
                            "compliance_provider_runtime": {
                                "status": "ok",
                                "request_id": "req-comp-1",
                            },
                            "eu_sanctions_window": {
                                "status": "skipped",
                                "request_id": "req-eu-1",
                                "correlation": {
                                    "expected_source_url": "https://example.test/eu.xml?token=abc123",
                                    "observed_source_url": "",
                                    "source_url_matches_expected": False,
                                },
                            },
                        },
                        "errors": [],
                    }
                if relative_path.endswith("homologation_external_evidence.py"):
                    output_dir = Path(argv[argv.index("--output-dir") + 1])
                    output_dir.mkdir(parents=True, exist_ok=True)
                    artifact_file = output_dir / "external_homologation_both_20260629T120000Z.json"
                    manifest_file = output_dir / f"{artifact_file.name}.manifest.json"
                    artifact_payload = {
                        "kind": "external_homologation_evidence",
                        "status": "ok",
                        "mode": "both",
                        "runs": {
                            "compliance": {"request_id": "req-comp-1"},
                            "rpc": {"request_id": "req-rpc-1", "case_id": "case-1"},
                        },
                    }
                    manifest_payload = {
                        "kind": "external_homologation_evidence",
                        "status": "ok",
                        "artifact_file": str(artifact_file),
                    }
                    artifact_file.write_text(json.dumps(artifact_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    manifest_file.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    return 0, {
                        "status": "ok",
                        "mode": "both",
                        "artifact_file": str(artifact_file),
                        "manifest_file": str(manifest_file),
                        "runs": artifact_payload["runs"],
                        "errors": [],
                    }
                raise AssertionError(f"Chamado inesperado: {relative_path} / {module_name}")

            def fake_run_final_artifact_validation(**kwargs):
                return 0, {
                    "status": "ok",
                    "window_id": kwargs["window_id"],
                    "scope": kwargs["expected_scope"],
                    "errors": [],
                    "missing_artifacts": [],
                    "found_artifacts": [],
                }

            with patch.object(MODULE, "run_module_main", side_effect=fake_run_module_main), \
                 patch.object(MODULE, "run_final_artifact_validation", side_effect=fake_run_final_artifact_validation):
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-06-29-a",
                    env_file=env_file,
                    private_env_file=private_env_file,
                    ownership_file=ownership_file,
                    checks_dir=checks_dir,
                    window_packet_file=packet_file,
                    homologation_mode="both",
                    rpc_expected_mode=None,
                    homologation_output_dir=homologation_output_dir,
                    dossier_output_dir=dossier_output_dir,
                    generated_at="2026-06-29T12:00:00+00:00",
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["steps"]["ownership_coverage"]["status"], "ok")
            self.assertEqual(payload["steps"]["window_packet"]["status"], "ok")
            self.assertEqual(payload["steps"]["oidc_preflight"]["status"], "ok")
            self.assertEqual(payload["steps"]["external_preflight"]["status"], "ok")
            self.assertEqual(payload["steps"]["oidc_readiness_bundle"]["status"], "ok")
            self.assertEqual(payload["steps"]["oidc_readiness_bundle"]["readiness_status"], "ready")
            self.assertEqual(payload["steps"]["regulatory_readiness_bundle"]["status"], "ok")
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["readiness"]["compliance_runtime"]["readiness_status"],
                "ready_for_validation",
            )
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["compliance_provider_runtime_request_id"],
                "req-comp-1",
            )
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["eu_sanctions_window_request_id"],
                "req-eu-1",
            )
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["eu_sanctions_observed_source_url"],
                "pending",
            )
            self.assertTrue(payload["steps"]["regulatory_readiness_bundle"]["compliance_runtime_enabled"])
            self.assertFalse(payload["steps"]["regulatory_readiness_bundle"]["eu_window_enabled"])
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["compliance_provider_runtime_status"],
                "ok",
            )
            self.assertEqual(
                payload["steps"]["regulatory_readiness_bundle"]["eu_sanctions_window_status"],
                "skipped",
            )
            self.assertEqual(payload["steps"]["homologation"]["status"], "ok")
            self.assertEqual(payload["steps"]["release_dossier"]["status"], "ok")
            self.assertEqual(payload["steps"]["final_artifact_validation"]["status"], "ok")
            self.assertEqual(payload["steps"]["final_artifact_validation"]["scope"], ["P0-01", "P0-02"])
            self.assertTrue(packet_file.exists())
            self.assertTrue((checks_dir / "ownership-coverage-stg-2026-06-29-a.json").exists())
            self.assertTrue((checks_dir / "placeholders-stg-2026-06-29-a.json").exists())
            self.assertTrue((checks_dir / "handoff-stg-2026-06-29-a.json").exists())
            self.assertTrue((checks_dir / "oidc-preflight-stg-2026-06-29-a.json").exists())
            self.assertTrue((checks_dir / "external-preflight-stg-2026-06-29-a.json").exists())
            self.assertTrue((checks_dir / "stg-2026-06-29-a-oidc-readiness-bundle.json").exists())
            self.assertTrue((dossier_output_dir / "stg-2026-06-29-a-oidc-readiness-bundle.md").exists())
            self.assertTrue((checks_dir / "stg-2026-06-29-a-regulatory-readiness-bundle.json").exists())
            self.assertTrue((dossier_output_dir / "stg-2026-06-29-a-regulatory-readiness-bundle.md").exists())
            self.assertTrue((checks_dir / "homologation-stg-2026-06-29-a.json").exists())
            self.assertEqual(payload["steps"]["oidc_readiness_bundle"]["summary_status"], "ok")
            self.assertEqual(payload["steps"]["regulatory_readiness_bundle"]["summary_status"], "ok")
            self.assertTrue(Path(payload["steps"]["release_dossier"]["artifact_file"]).exists())
            self.assertTrue(Path(payload["steps"]["release_dossier"]["manifest_file"]).exists())

    def test_run_window_stops_before_preflights_when_local_gates_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            private_env_file = base / ".env.staging.private"
            ownership_file = base / "staging-env-ownership.md"
            checks_dir = base / "artifacts" / "checks"
            packet_file = base / "artifacts" / "window-packet.md"

            _write_env_file(env_file)
            _write_private_env_file(private_env_file, unresolved_jwt=True)
            _write_ownership_file(ownership_file)

            with patch.object(MODULE, "run_module_main", side_effect=AssertionError("preflights nao deveriam rodar")):
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-06-29-a",
                    env_file=env_file,
                    private_env_file=private_env_file,
                    ownership_file=ownership_file,
                    checks_dir=checks_dir,
                    window_packet_file=packet_file,
                    homologation_mode="both",
                    rpc_expected_mode=None,
                    homologation_output_dir=base / "artifacts" / "homologation",
                    dossier_output_dir=base / "artifacts" / "dossiers",
                    generated_at="2026-06-29T12:00:00+00:00",
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["steps"]["placeholder_check"]["status"], "failed")
            self.assertEqual(payload["steps"]["oidc_preflight"]["status"], "skipped")
            self.assertEqual(payload["steps"]["external_preflight"]["status"], "skipped")
            self.assertEqual(payload["steps"]["homologation"]["status"], "skipped")
            self.assertEqual(payload["steps"]["release_dossier"]["status"], "skipped")

    def test_run_window_skips_homologation_when_preflight_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            private_env_file = base / ".env.staging.private"
            ownership_file = base / "staging-env-ownership.md"
            checks_dir = base / "artifacts" / "checks"
            packet_file = base / "artifacts" / "window-packet.md"

            _write_env_file(env_file)
            _write_private_env_file(private_env_file)
            _write_ownership_file(ownership_file)

            def fake_run_module_main(relative_path: str, argv: list[str], module_name: str):
                if relative_path.endswith("preflight_oidc_serious_env.py"):
                    return 0, {"status": "ok", "errors": []}
                if relative_path.endswith("preflight_external_integrations.py"):
                    return 1, {"status": "failed", "errors": ["provider indisponivel"]}
                raise AssertionError(f"nao deveria chegar em {relative_path}")

            with patch.object(MODULE, "run_module_main", side_effect=fake_run_module_main):
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-06-29-a",
                    env_file=env_file,
                    private_env_file=private_env_file,
                    ownership_file=ownership_file,
                    checks_dir=checks_dir,
                    window_packet_file=packet_file,
                    homologation_mode="both",
                    rpc_expected_mode=None,
                    homologation_output_dir=base / "artifacts" / "homologation",
                    dossier_output_dir=base / "artifacts" / "dossiers",
                    generated_at="2026-06-29T12:00:00+00:00",
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["steps"]["oidc_preflight"]["status"], "ok")
            self.assertEqual(payload["steps"]["external_preflight"]["status"], "failed")
            self.assertEqual(payload["steps"]["oidc_readiness_bundle"]["status"], "skipped")
            self.assertEqual(payload["steps"]["regulatory_readiness_bundle"]["status"], "skipped")
            self.assertEqual(payload["steps"]["homologation"]["status"], "skipped")
            self.assertEqual(payload["steps"]["release_dossier"]["status"], "skipped")

    def test_run_window_skips_homologation_when_oidc_bundle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            env_file = base / ".env.staging.example"
            private_env_file = base / ".env.staging.private"
            ownership_file = base / "staging-env-ownership.md"
            checks_dir = base / "artifacts" / "checks"
            packet_file = base / "artifacts" / "window-packet.md"

            _write_env_file(env_file)
            _write_private_env_file(private_env_file)
            _write_ownership_file(ownership_file)

            def fake_run_module_main(relative_path: str, argv: list[str], module_name: str):
                if relative_path.endswith("preflight_oidc_serious_env.py"):
                    return 0, {"status": "ok", "errors": []}
                if relative_path.endswith("preflight_external_integrations.py"):
                    return 0, {"status": "ok", "errors": []}
                if relative_path.endswith("run_oidc_readiness_bundle.py"):
                    return 1, {
                        "kind": "oidc_readiness_bundle",
                        "status": "failed",
                        "scope": {
                            "mfa_external_provider_homologated": "false",
                            "expected_oidc_provider": "keycloak",
                        },
                        "steps": {
                            "oidc_preflight": {"status": "ok"},
                            "smoke_auth_oidc_mode": {"status": "failed"},
                        },
                        "errors": ["smoke_auth_oidc_mode: falhou"],
                    }
                raise AssertionError(f"nao deveria chegar em {relative_path}")

            with patch.object(MODULE, "run_module_main", side_effect=fake_run_module_main):
                exit_code, payload = MODULE.run_window(
                    window_id="stg-2026-06-29-a",
                    env_file=env_file,
                    private_env_file=private_env_file,
                    ownership_file=ownership_file,
                    checks_dir=checks_dir,
                    window_packet_file=packet_file,
                    homologation_mode="both",
                    rpc_expected_mode=None,
                    homologation_output_dir=base / "artifacts" / "homologation",
                    dossier_output_dir=base / "artifacts" / "dossiers",
                    generated_at="2026-06-29T12:00:00+00:00",
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["steps"]["oidc_readiness_bundle"]["status"], "failed")
            self.assertEqual(payload["steps"]["regulatory_readiness_bundle"]["status"], "skipped")
            self.assertEqual(payload["steps"]["homologation"]["status"], "skipped")
            self.assertEqual(payload["steps"]["release_dossier"]["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
