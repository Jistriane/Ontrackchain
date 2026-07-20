"""
Testes unitários para o endpoint público de API B2B em apps/compliance-api.
"""

from __future__ import annotations

import unittest

try:
    from fastapi.testclient import TestClient
    from compliance_api.main import app

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "FastAPI backend não instalado")
class B2BPublicEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_b2b_screen_missing_header(self) -> None:
        response = self.client.post("/api/v1/b2b/screen", json={"address": "0x1234567890abcdef"})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Formato de chave B2B X-API-Key inválido ou ausente", response.json()["detail"])

    def test_b2b_screen_success(self) -> None:
        headers = {"X-API-Key": "otc_live_abcdef1234567890abcdef1234567890"}
        payload = {"address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", "chain": "ethereum"}
        response = self.client.post("/api/v1/b2b/screen", headers=headers, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["b2b_client"])
        self.assertEqual(data["recommendation"], "APPROVE")


if __name__ == "__main__":
    unittest.main()
