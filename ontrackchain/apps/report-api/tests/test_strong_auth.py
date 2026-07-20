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
class StrongAuthForLegalReportTests(unittest.TestCase):
    def test_accepts_dev_jwt_with_local_totp(self) -> None:
        _require_strong_auth_for_legal_report(
            x_auth_method="dev_jwt",
            x_role="ADMIN",
            x_2fa="ok",
            x_mfa_mode="local_totp",
            x_mfa_provider_homologated=None,
        )

    def test_rejects_oidc_mfa_until_homologated(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role="ADMIN",
                x_2fa="managed_externally",
                x_mfa_mode="external_provider",
                x_mfa_provider_homologated="false",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "mfa_not_homologated_for_oidc")

    def test_requires_local_2fa_for_jwt_scaffold_flow(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _require_strong_auth_for_legal_report(
                x_auth_method="jwt",
                x_role="ADMIN",
                x_2fa="pending",
                x_mfa_mode="local_totp",
                x_mfa_provider_homologated=None,
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "2fa_required")

    def test_accepts_homologated_oidc_mfa(self) -> None:
        _require_strong_auth_for_legal_report(
            x_auth_method="jwt",
            x_role="ADMIN",
            x_2fa="managed_externally_homologated",
            x_mfa_mode="external_provider",
            x_mfa_provider_homologated="true",
        )


if __name__ == "__main__":
    unittest.main()
