from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

AUTH_SERVICE_IMPORTABLE = True
try:
    main: Any = importlib.import_module("auth_service.main")
except Exception:
    AUTH_SERVICE_IMPORTABLE = False
    main = None


@unittest.skipUnless(AUTH_SERVICE_IMPORTABLE, "auth-service dependencies not installed in current interpreter")
class CanonicalizeRoleTests(unittest.TestCase):
    def test_maps_otk_compliance_officer(self) -> None:
        self.assertEqual(main._canonicalize_role("otk_compliance_officer"), "COMPLIANCE_OFFICER")

    def test_maps_otk_legal_reviewer(self) -> None:
        self.assertEqual(main._canonicalize_role("otk_legal_reviewer"), "LEGAL_REVIEWER")

    def test_preserves_explicit_compliance_officer(self) -> None:
        self.assertEqual(main._canonicalize_role("COMPLIANCE_OFFICER"), "COMPLIANCE_OFFICER")

    def test_maps_otk_reviewer(self) -> None:
        self.assertEqual(main._canonicalize_role("otk_reviewer"), "REVIEWER")

    def test_maps_otk_billing_admin(self) -> None:
        self.assertEqual(main._canonicalize_role("otk_billing_admin"), "BILLING_ADMIN")

    def test_preserves_explicit_reviewer(self) -> None:
        self.assertEqual(main._canonicalize_role("REVIEWER"), "REVIEWER")


if __name__ == "__main__":
    unittest.main()
