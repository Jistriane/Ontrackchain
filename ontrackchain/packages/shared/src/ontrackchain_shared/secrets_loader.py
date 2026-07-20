"""
Ontrackchain - Shared Secret Manager Client Module (P2-04)

Provides unified secret loading abstraction supporting HashiCorp Vault,
AWS Secrets Manager simulation, and local environment variable fallbacks across all microservices.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any

logger = logging.getLogger("ontrackchain_shared.secrets_loader")


class SecretProvider:
    """
    Unified Secret Manager client for all microservices.
    Priority order:
    1. HashiCorp Vault (if VAULT_ADDR and VAULT_TOKEN configured)
    2. AWS Secrets Manager JSON File (if AWS_SECRETS_FILE configured)
    3. Environment Variables fallback (os.getenv)
    """

    def __init__(self) -> None:
        self.vault_addr = os.getenv("VAULT_ADDR")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.aws_secrets_file = os.getenv("AWS_SECRETS_FILE")
        self.app_env = os.getenv("APP_ENV", "local").lower()
        self._cache: dict[str, str] = {}

    def get_secret(self, key: str, default: str | None = None) -> str | None:
        """Retrieves a secret by key, utilizing cache if available."""
        if key in self._cache:
            return self._cache[key]

        # 1. Try HashiCorp Vault if enabled
        if self.vault_addr and self.vault_token:
            vault_val = self._fetch_from_vault(key)
            if vault_val is not None:
                self._cache[key] = vault_val
                return vault_val

        # 2. Try AWS Secrets Manager file if enabled
        if self.aws_secrets_file and os.path.isfile(self.aws_secrets_file):
            aws_val = self._fetch_from_aws_file(key)
            if aws_val is not None:
                self._cache[key] = aws_val
                return aws_val

        # 3. Fallback to OS environment
        env_val = os.getenv(key, default)
        if env_val is not None:
            self._cache[key] = env_val
        return env_val

    def _fetch_from_vault(self, key: str) -> str | None:
        """Fetches secret from HashiCorp Vault KV v2 API."""
        try:
            url = f"{self.vault_addr.rstrip('/')}/v1/secret/data/ontrackchain"
            req = urllib.request.Request(
                url,
                headers={"X-Vault-Token": self.vault_token},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    data = payload.get("data", {}).get("data", {})
                    return data.get(key)
        except Exception as err:
            logger.warning("Failed to fetch secret '%s' from Vault: %s", key, err)
        return None

    def _fetch_from_aws_file(self, key: str) -> str | None:
        """Fetches secret from local AWS Secrets Manager JSON export file."""
        try:
            with open(self.aws_secrets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(key)
        except Exception as err:
            logger.warning("Failed to fetch secret '%s' from AWS secrets file: %s", key, err)
        return None

    def clear_cache(self) -> None:
        """Clears cached secret values."""
        self._cache.clear()


# Default singleton instance
secret_provider = SecretProvider()
