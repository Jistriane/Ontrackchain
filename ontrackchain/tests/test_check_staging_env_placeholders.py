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


MODULE = _load_module("check_staging_env_placeholders", "scripts/check_staging_env_placeholders.py")


class CheckStagingEnvPlaceholdersTests(unittest.TestCase):
    maxDiff = None

    def test_fails_when_file_is_missing(self) -> None:
        exit_code, payload = MODULE.build_payload(
            file_path=ROOT_DIR / "does-not-exist.env",
            required_non_empty=["APP_ENV", "AUTH_MODE"],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("arquivo_ausente", payload["errors"][0])
        self.assertEqual(payload["checked_keys_count"], 0)

    def test_fails_when_placeholder_or_empty_critical_values_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_ENV=staging",
                        "AUTH_MODE=oidc",
                        "KEYCLOAK_ADMIN_PASSWORD=__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                        "JWT_HS256_SECRET=",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=["APP_ENV", "AUTH_MODE", "KEYCLOAK_ADMIN_PASSWORD", "JWT_HS256_SECRET"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(
            payload["unresolved_placeholders"],
            [
                {
                    "name": "KEYCLOAK_ADMIN_PASSWORD",
                    "value": "__FILL_STAGING_KEYCLOAK_ADMIN_PASSWORD__",
                }
            ],
        )
        self.assertIn("variavel_obrigatoria_vazia: JWT_HS256_SECRET", payload["errors"])
        self.assertEqual(payload["missing_required"], [])

    def test_passes_when_required_values_are_filled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_ENV=staging",
                        "AUTH_MODE=oidc",
                        "DEV_AUTH_ENABLED=false",
                        "KEYCLOAK_ADMIN_PASSWORD=strong-password",
                        "JWT_HS256_SECRET=top-secret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=[
                    "APP_ENV",
                    "AUTH_MODE",
                    "DEV_AUTH_ENABLED",
                    "KEYCLOAK_ADMIN_PASSWORD",
                    "JWT_HS256_SECRET",
                ],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["empty_required"], [])
        self.assertEqual(payload["missing_required"], [])

    def test_allows_oidc_homologation_token_placeholder_when_mfa_homologation_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_ENV=staging",
                        "AUTH_MODE=oidc",
                        "DEV_AUTH_ENABLED=false",
                        "MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false",
                        "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__",
                        "KEYCLOAK_ADMIN_PASSWORD=strong-password",
                        "JWT_HS256_SECRET=top-secret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=[
                    "APP_ENV",
                    "AUTH_MODE",
                    "DEV_AUTH_ENABLED",
                    "KEYCLOAK_ADMIN_PASSWORD",
                    "JWT_HS256_SECRET",
                ],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["unresolved_placeholders"], [])
        self.assertEqual(payload["conditionally_allowed_placeholders"], ["ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN"])

    def test_requires_oidc_homologation_token_placeholder_to_be_resolved_when_mfa_homologation_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_ENV=staging",
                        "AUTH_MODE=oidc",
                        "DEV_AUTH_ENABLED=false",
                        "MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true",
                        "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN=__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__",
                        "KEYCLOAK_ADMIN_PASSWORD=strong-password",
                        "JWT_HS256_SECRET=top-secret",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=[
                    "APP_ENV",
                    "AUTH_MODE",
                    "DEV_AUTH_ENABLED",
                    "KEYCLOAK_ADMIN_PASSWORD",
                    "JWT_HS256_SECRET",
                ],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(
            payload["unresolved_placeholders"],
            [
                {
                    "name": "ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN",
                    "value": "__FILL_STAGING_HOMOLOGATION_OIDC_TOKEN__",
                }
            ],
        )
        self.assertEqual(payload["conditionally_allowed_placeholders"], [])

    def test_allows_empty_primary_rpc_url_when_expected_mode_is_fallback_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_ENV=staging",
                        "AUTH_MODE=oidc",
                        "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live",
                        "ONTRACKCHAIN_EXPECT_RPC_MODE=fallback_only",
                        "COMPLIANCE_TRM_SCREENING_URL=https://trm.example.com/screening",
                        "COMPLIANCE_TRM_API_KEY=trm-key",
                        "INVESTIGATION_RPC_PRIMARY_URL=",
                        "INVESTIGATION_RPC_FALLBACK_URL=https://rpc-fallback.example.com",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=[
                    "APP_ENV",
                    "AUTH_MODE",
                    "COMPLIANCE_TRM_SCREENING_URL",
                    "COMPLIANCE_TRM_API_KEY",
                    "INVESTIGATION_RPC_PRIMARY_URL",
                ],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["empty_required"], [])
        self.assertIn("INVESTIGATION_RPC_FALLBACK_URL", payload["effective_required_non_empty"])
        self.assertNotIn("INVESTIGATION_RPC_PRIMARY_URL", payload["effective_required_non_empty"])

    def test_output_payload_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env.staging.private"
            env_path.write_text("APP_ENV=staging\nAUTH_MODE=oidc\n", encoding="utf-8")
            _, payload = MODULE.build_payload(
                file_path=env_path,
                required_non_empty=["APP_ENV", "AUTH_MODE"],
            )

        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
