"""
Tests for ontrackchain_shared.secrets_loader (P2-04)
Includes failover, cache verification, Vault timeout, and fallback test cases.
"""

import os
import urllib.error
import unittest
from unittest.mock import patch, MagicMock
from ontrackchain_shared.secrets_loader import SecretProvider


class TestSharedSecretProvider(unittest.TestCase):

    def setUp(self):
        self.provider = SecretProvider()

    def test_env_fallback(self):
        with patch.dict(os.environ, {"MY_TEST_KEY": "env_val"}):
            provider = SecretProvider()
            val = provider.get_secret("MY_TEST_KEY")
            self.assertEqual(val, "env_val")

    def test_default_value(self):
        val = self.provider.get_secret("NON_EXISTENT_KEY_XYZ", default="fallback")
        self.assertEqual(val, "fallback")

    def test_aws_secrets_file_loading(self):
        mock_json = '{"DB_PASS": "secret123"}'
        with patch("os.path.isfile", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=mock_json)):
                with patch.dict(os.environ, {"AWS_SECRETS_FILE": "/fake/secrets.json"}):
                    provider = SecretProvider()
                    val = provider.get_secret("DB_PASS")
                    self.assertEqual(val, "secret123")

    def test_vault_success(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"data": {"data": {"JWT_SECRET": "vault_jwt_secret_99"}}}'
        mock_response.__enter__.return_value = mock_response

        with patch.dict(os.environ, {"VAULT_ADDR": "http://127.0.0.1:8200", "VAULT_TOKEN": "s.token123"}):
            with patch("urllib.request.urlopen", return_value=mock_response):
                provider = SecretProvider()
                val = provider.get_secret("JWT_SECRET")
                self.assertEqual(val, "vault_jwt_secret_99")

    def test_vault_failover_to_env(self):
        """Simulates Vault network error/timeout falling back smoothly to OS Environment."""
        with patch.dict(os.environ, {
            "VAULT_ADDR": "http://127.0.0.1:8200",
            "VAULT_TOKEN": "s.token123",
            "API_KEY_FALLBACK": "env_api_key_456"
        }):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
                provider = SecretProvider()
                val = provider.get_secret("API_KEY_FALLBACK")
                self.assertEqual(val, "env_api_key_456")

    def test_vault_failover_to_aws_file(self):
        """Simulates Vault network failure falling back to AWS Secrets File."""
        mock_aws_json = '{"API_KEY_FALLBACK": "aws_api_key_789"}'
        with patch.dict(os.environ, {
            "VAULT_ADDR": "http://127.0.0.1:8200",
            "VAULT_TOKEN": "s.token123",
            "AWS_SECRETS_FILE": "/fake/aws.json"
        }):
            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Vault Timeout")):
                with patch("os.path.isfile", return_value=True):
                    with patch("builtins.open", unittest.mock.mock_open(read_data=mock_aws_json)):
                        provider = SecretProvider()
                        val = provider.get_secret("API_KEY_FALLBACK")
                        self.assertEqual(val, "aws_api_key_789")

    def test_cache_hit_and_clear(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"data": {"data": {"CACHED_SECRET": "first_fetch"}}}'
        mock_response.__enter__.return_value = mock_response

        with patch.dict(os.environ, {"VAULT_ADDR": "http://127.0.0.1:8200", "VAULT_TOKEN": "s.token123"}):
            with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
                provider = SecretProvider()
                val1 = provider.get_secret("CACHED_SECRET")
                self.assertEqual(val1, "first_fetch")
                self.assertEqual(mock_urlopen.call_count, 1)

                # Second fetch should hit cache and not invoke urlopen again
                val2 = provider.get_secret("CACHED_SECRET")
                self.assertEqual(val2, "first_fetch")
                self.assertEqual(mock_urlopen.call_count, 1)

                # Clear cache and verify urlopen is called on next fetch
                provider.clear_cache()
                val3 = provider.get_secret("CACHED_SECRET")
                self.assertEqual(val3, "first_fetch")
                self.assertEqual(mock_urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
