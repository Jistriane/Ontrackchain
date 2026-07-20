from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "agents" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

try:
    from fastapi import HTTPException
    from report_api.main import _require_strong_auth_for_legal_report
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "fastapi nao disponivel no interpretador local")
class StrongAuthMissingHeadersTests(unittest.TestCase):
    """Cobre os cenários de headers ausentes — os mais prováveis em misconfiguration de gateway."""

    def test_rejects_when_auth_method_is_none(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method=None,
                x_role="ADMIN",
                x_2fa="ok",
                x_mfa_mode="local_totp",
                x_mfa_provider_homologated=None,
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "legal_report_requires_jwt_auth")

    def test_rejects_when_auth_method_is_invalid(self) -> None:
        for invalid in ("api_key", "saml", "basic", "", "oauth2"):
            with self.subTest(auth_method=invalid):
                with self.assertRaises(HTTPException) as ctx:
                    _require_strong_auth_for_legal_report(
                        x_auth_method=invalid,
                        x_role="ADMIN",
                        x_2fa="ok",
                        x_mfa_mode="local_totp",
                        x_mfa_provider_homologated=None,
                    )
                self.assertEqual(ctx.exception.status_code, 403)
                self.assertEqual(ctx.exception.detail, "legal_report_requires_jwt_auth")

    def test_rejects_when_role_is_none(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role=None,
                x_2fa="ok",
                x_mfa_mode="local_totp",
                x_mfa_provider_homologated=None,
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "legal_report_requires_admin_role")

    def test_rejects_when_role_is_non_admin(self) -> None:
        for role in ("VIEWER", "COMPLIANCE_OFFICER", "LEGAL_REVIEWER", "ANALYST"):
            with self.subTest(role=role):
                with self.assertRaises(HTTPException) as ctx:
                    _require_strong_auth_for_legal_report(
                        x_auth_method="jwt",
                        x_role=role,
                        x_2fa="ok",
                        x_mfa_mode="local_totp",
                        x_mfa_provider_homologated=None,
                    )
                self.assertEqual(ctx.exception.status_code, 403)
                self.assertEqual(ctx.exception.detail, "legal_report_requires_admin_role")

    def test_rejects_when_2fa_is_none_with_local_totp(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role="ADMIN",
                x_2fa=None,
                x_mfa_mode="local_totp",
                x_mfa_provider_homologated=None,
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "2fa_required")


@unittest.skipUnless(HAS_FASTAPI, "fastapi nao disponivel no interpretador local")
class StrongAuthNormalizationTests(unittest.TestCase):
    """Cobre robustez de normalização (case-insensitive) nos headers."""

    def test_accepts_jwt_uppercase(self) -> None:
        _require_strong_auth_for_legal_report(
            x_auth_method="JWT",
            x_role="ADMIN",
            x_2fa="ok",
            x_mfa_mode="local_totp",
            x_mfa_provider_homologated=None,
        )

    def test_accepts_dev_jwt_mixed_case(self) -> None:
        _require_strong_auth_for_legal_report(
            x_auth_method="Dev_JWT",
            x_role="ADMIN",
            x_2fa="ok",
            x_mfa_mode="local_totp",
            x_mfa_provider_homologated=None,
        )

    def test_accepts_admin_role_lowercase(self) -> None:
        _require_strong_auth_for_legal_report(
            x_auth_method="jwt",
            x_role="admin",
            x_2fa="ok",
            x_mfa_mode="local_totp",
            x_mfa_provider_homologated=None,
        )


@unittest.skipUnless(HAS_FASTAPI, "fastapi nao disponivel no interpretador local")
class StrongAuthOidcEdgeCasesTests(unittest.TestCase):
    """Cobre edge cases do fluxo OIDC/external_provider."""

    def test_accepts_managed_externally_without_homologated_suffix(self) -> None:
        # "managed_externally" (sem _homologated) deve ser aceito quando homologado=true
        _require_strong_auth_for_legal_report(
            x_auth_method="jwt",
            x_role="ADMIN",
            x_2fa="managed_externally",
            x_mfa_mode="external_provider",
            x_mfa_provider_homologated="true",
        )

    def test_rejects_homologated_oidc_with_2fa_pending(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role="ADMIN",
                x_2fa="pending",
                x_mfa_mode="external_provider",
                x_mfa_provider_homologated="true",
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "2fa_required")

    def test_rejects_homologated_oidc_with_2fa_none(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role="ADMIN",
                x_2fa=None,
                x_mfa_mode="external_provider",
                x_mfa_provider_homologated="true",
            )
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "2fa_required")

    def test_auth_method_checked_before_role(self) -> None:
        # Verificar que auth_method inválido dispara ANTES do role inválido
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method=None,
                x_role=None,
                x_2fa=None,
                x_mfa_mode=None,
                x_mfa_provider_homologated=None,
            )
        self.assertEqual(ctx.exception.detail, "legal_report_requires_jwt_auth")

    def test_mfa_provider_homologated_case_insensitive(self) -> None:
        # "TRUE" uppercase deve ser aceito
        _require_strong_auth_for_legal_report(
            x_auth_method="jwt",
            x_role="ADMIN",
            x_2fa="managed_externally_homologated",
            x_mfa_mode="external_provider",
            x_mfa_provider_homologated="TRUE",
        )

    def test_accepts_local_totp_with_mfa_mode_none(self) -> None:
        # mfa_mode ausente + x_2fa="ok" deve aceitar
        _require_strong_auth_for_legal_report(
            x_auth_method="jwt",
            x_role="ADMIN",
            x_2fa="ok",
            x_mfa_mode=None,
            x_mfa_provider_homologated=None,
        )


if __name__ == "__main__":
    unittest.main()
