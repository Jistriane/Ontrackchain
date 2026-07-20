"""
Tests for SecretProvider (P2-04)
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "auth-service" / "src"))

from auth_service.secrets_loader import SecretProvider


class TestSecretProvider(unittest.TestCase):

    def setUp(self) -> None:
        self.provider = SecretProvider()
        self.provider.clear_cache()

    def test_env_fallback(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"}):
            self.provider.clear_cache()
            val = self.provider.get_secret("DATABASE_URL")
            self.assertEqual(val, "postgresql://user:pass@localhost:5432/db")

    def test_default_value_fallback(self) -> None:
        self.provider.clear_cache()
        val = self.provider.get_secret("NON_EXISTENT_KEY_12345", default="fallback_val")
        self.assertEqual(val, "fallback_val")

    def test_aws_secrets_file_loading(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump({"POSTGRES_PASSWORD": "SecretAwsPassword123!"}, tmp)
            tmp_path = tmp.name

        try:
            with patch.dict(os.environ, {"AWS_SECRETS_FILE": tmp_path}):
                provider = SecretProvider()
                val = provider.get_secret("POSTGRES_PASSWORD")
                self.assertEqual(val, "SecretAwsPassword123!")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_vault_http_loading(self) -> None:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "data": {
                "data": {
                    "REDIS_PASSWORD": "SecretVaultPassword999!"
                }
            }
        }).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        with patch.dict(os.environ, {"VAULT_ADDR": "http://127.0.0.1:8200", "VAULT_TOKEN": "root_token_123"}):
            with patch("urllib.request.urlopen", return_value=mock_response):
                provider = SecretProvider()
                val = provider.get_secret("REDIS_PASSWORD")
                self.assertEqual(val, "SecretVaultPassword999!")


if __name__ == "__main__":
    unittest.main()
