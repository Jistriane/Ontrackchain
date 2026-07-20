"""
Tests for ontrackchain_shared.secrets_loader (P2-04)
"""

import os
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


if __name__ == "__main__":
    unittest.main()
