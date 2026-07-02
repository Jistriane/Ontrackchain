import importlib.util
import io
import json
import os
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


PRE_OIDC = _load_module("preflight_oidc_serious_env", "scripts/preflight_oidc_serious_env.py")
PRE_EXTERNAL = _load_module("preflight_external_integrations", "scripts/preflight_external_integrations.py")


class PreflightTestCase(unittest.TestCase):
    maxDiff = None

    def _run_main(self, module, env: dict[str, str]) -> tuple[int, dict]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, env, clear=True):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = module.main()

        output = stdout.getvalue().strip() or stderr.getvalue().strip()
        self.assertTrue(output, "o script deve emitir um resumo JSON")
        return exit_code, json.loads(output)


class OidcSeriousEnvPreflightTests(PreflightTestCase):
    def test_accepts_serious_oidc_configuration(self) -> None:
        exit_code, payload = self._run_main(
            PRE_OIDC,
            {
                "APP_ENV": "staging",
                "AUTH_MODE": "oidc",
                "DEV_AUTH_ENABLED": "false",
                "NEXT_PUBLIC_AUTH_MODE": "oidc",
                "NEXT_PUBLIC_APP_ENV": "staging",
                "NEXT_PUBLIC_DEV_AUTH_ENABLED": "false",
                "OIDC_PROVIDER": "keycloak",
                "OIDC_AUDIENCE": "ontrackchain-api",
                "OIDC_CLIENT_ID": "ontrackchain-web",
                "OIDC_ORG_CLAIM": "org_id",
                "OIDC_PLAN_CLAIM": "plan",
                "OIDC_ROLE_CLAIM": "role",
                "OIDC_ISSUER_URL": "https://id.ontrackchain.example/realms/ontrackchain",
                "OIDC_AUTHORIZATION_URL": "https://id.ontrackchain.example/realms/ontrackchain/protocol/openid-connect/auth",
                "OIDC_JWKS_URL": "https://id.ontrackchain.example/realms/ontrackchain/protocol/openid-connect/certs",
                "JWT_HS256_SECRET": "prod-secret-value",
                "MFA_TOTP_SECRET": "PROD-TOTP-SECRET",
                "KEYCLOAK_ADMIN_PASSWORD": "strong-admin-password",
                "KEYCLOAK_B2B_CLIENT_SECRET": "strong-b2b-secret",
            },
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])

    def test_rejects_localhost_and_default_secrets(self) -> None:
        exit_code, payload = self._run_main(
            PRE_OIDC,
            {
                "APP_ENV": "production",
                "AUTH_MODE": "oidc",
                "DEV_AUTH_ENABLED": "true",
                "NEXT_PUBLIC_AUTH_MODE": "dev",
                "NEXT_PUBLIC_APP_ENV": "staging",
                "NEXT_PUBLIC_DEV_AUTH_ENABLED": "true",
                "OIDC_PROVIDER": "unknown",
                "OIDC_AUDIENCE": "",
                "OIDC_CLIENT_ID": "client",
                "OIDC_ORG_CLAIM": "org_id",
                "OIDC_PLAN_CLAIM": "plan",
                "OIDC_ROLE_CLAIM": "",
                "OIDC_ISSUER_URL": "http://localhost:8080/realms/ontrackchain",
                "OIDC_AUTHORIZATION_URL": "http://localhost:8080/auth",
                "OIDC_JWKS_URL": "http://localhost:8080/certs",
                "JWT_HS256_SECRET": "change-me",
                "MFA_TOTP_SECRET": "JBSWY3DPEHPK3PXP",
                "KEYCLOAK_ADMIN_PASSWORD": "admin",
                "KEYCLOAK_B2B_CLIENT_SECRET": "change-me-b2b-secret",
            },
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("DEV_AUTH_ENABLED: esperado=false em ambiente serio", payload["errors"])
        self.assertIn("NEXT_PUBLIC_AUTH_MODE: esperado=oidc recebido=dev", payload["errors"])
        self.assertIn("OIDC_AUDIENCE: variavel obrigatoria ausente", payload["errors"])
        self.assertIn(
            "OIDC_ISSUER_URL: em ambiente serio deve usar https (http://localhost:8080/realms/ontrackchain)",
            payload["errors"],
        )
        self.assertIn("JWT_HS256_SECRET: valor padrao/local detectado; configurar secret nao-dev", payload["errors"])


class ExternalIntegrationsPreflightTests(PreflightTestCase):
    def test_accepts_live_compliance_and_fallback_only_rpc(self) -> None:
        exit_code, payload = self._run_main(
            PRE_EXTERNAL,
            {
                "APP_ENV": "staging",
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE": "live",
                "ONTRACKCHAIN_EXPECT_RPC_MODE": "fallback_only",
                "COMPLIANCE_TRM_ENABLED": "true",
                "COMPLIANCE_RISK_PROVIDER": "trm_labs",
                "COMPLIANCE_TRM_SCREENING_URL": "https://screening.trm.example/v1/check",
                "COMPLIANCE_TRM_API_KEY": "trm-live-key",
                "COMPLIANCE_TRM_TIMEOUT_MS": "4000",
                "COMPLIANCE_TRM_MAX_RETRIES": "2",
                "COMPLIANCE_EU_SANCTIONS_SOURCE_URL": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=abc123",
                "INVESTIGATION_RPC_ENABLED": "true",
                "INVESTIGATION_RPC_PROVIDER": "evm_rpc",
                "INVESTIGATION_RPC_PRIMARY_URL": "",
                "INVESTIGATION_RPC_FALLBACK_URL": "https://rpc-fallback.ontrackchain.example",
                "INVESTIGATION_RPC_TIMEOUT_MS": "2500",
                "INVESTIGATION_RPC_MAX_RETRIES": "1",
            },
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["compliance"]["expect_mode"], "live")
        self.assertEqual(payload["rpc"]["expect_mode"], "fallback_only")
        self.assertTrue(payload["compliance"]["sanctions_source_overrides"]["eu_present"])
        self.assertTrue(payload["compliance"]["sanctions_source_overrides"]["eu_tokenized"])
        self.assertFalse(payload["compliance"]["sanctions_source_overrides"]["ofac_present"])

    def test_rejects_insecure_or_invalid_provider_setup(self) -> None:
        exit_code, payload = self._run_main(
            PRE_EXTERNAL,
            {
                "APP_ENV": "production",
                "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE": "live",
                "ONTRACKCHAIN_EXPECT_RPC_MODE": "live",
                "COMPLIANCE_TRM_ENABLED": "false",
                "COMPLIANCE_RISK_PROVIDER": "other",
                "COMPLIANCE_TRM_SCREENING_URL": "http://localhost:8081/check",
                "COMPLIANCE_TRM_API_KEY": "change-me",
                "COMPLIANCE_TRM_TIMEOUT_MS": "0",
                "COMPLIANCE_TRM_MAX_RETRIES": "-1",
                "COMPLIANCE_EU_SANCTIONS_SOURCE_URL": "http://localhost:8080/eu.xml?token=test",
                "INVESTIGATION_RPC_ENABLED": "true",
                "INVESTIGATION_RPC_PROVIDER": "other",
                "INVESTIGATION_RPC_PRIMARY_URL": "http://localhost:8545",
                "INVESTIGATION_RPC_FALLBACK_URL": "http://localhost:8545",
                "INVESTIGATION_RPC_TIMEOUT_MS": "0",
                "INVESTIGATION_RPC_MAX_RETRIES": "-3",
            },
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertIn("COMPLIANCE_RISK_PROVIDER: esperado=trm_labs recebido=other", payload["errors"])
        self.assertIn("COMPLIANCE_TRM_ENABLED: esperado=true para homologacao live", payload["errors"])
        self.assertIn(
            "COMPLIANCE_TRM_SCREENING_URL: em ambiente serio deve usar https (http://localhost:8081/check)",
            payload["errors"],
        )
        self.assertIn("COMPLIANCE_TRM_TIMEOUT_MS: esperado valor >= 1, recebido=0", payload["errors"])
        self.assertIn(
            "COMPLIANCE_EU_SANCTIONS_SOURCE_URL: em ambiente serio deve usar https (http://localhost:8080/eu.xml?token=test)",
            payload["errors"],
        )
        self.assertIn("INVESTIGATION_RPC_PROVIDER: esperado=evm_rpc recebido=other", payload["errors"])
        self.assertIn(
            "INVESTIGATION_RPC_PRIMARY_URL: em ambiente serio deve usar https (http://localhost:8545)",
            payload["errors"],
        )
        self.assertIn(
            "INVESTIGATION_RPC_FALLBACK_URL: deve diferir da URL primaria quando configurada",
            payload["errors"],
        )


if __name__ == "__main__":
    unittest.main()
