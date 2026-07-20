"""
Ontrackchain - B2B API Key & Rate Limiting Manager (P3 B2B API)

Handles B2B API Key hashing, validation, permissions, and rate-limiting quotas.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Dict, List, Optional, Tuple


class B2BApiKeyValidator:
    """Validates B2B API Keys and manages per-organization rate limits."""

    def __init__(self) -> None:
        # Armazena registros de chaves ativas {key_hash: metadata}
        self._active_keys: Dict[str, Dict] = {}
        # Armazena timestamps de requisições por chave para rate-limiting {key_hash: [timestamp1, timestamp2]}
        self._request_windows: Dict[str, List[float]] = {}

    @staticmethod
    def generate_key(org_id: str, plan_tier: str = "pro") -> Tuple[str, str, Dict]:
        """Generates a secure B2B API Key (otc_live_...) and returns (raw_key, key_hash, metadata)."""
        raw_key = f"otc_live_{secrets.token_hex(24)}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        
        limit_rpm = 100 if plan_tier == "enterprise" else (30 if plan_tier == "pro" else 10)

        metadata = {
            "org_id": org_id,
            "plan_tier": plan_tier,
            "rate_limit_rpm": limit_rpm,
            "created_at": time.time(),
            "enabled": True,
            "scopes": ["compliance:read", "investigation:read", "report:create"],
        }

        return raw_key, key_hash, metadata

    def register_key_hash(self, key_hash: str, metadata: Dict) -> None:
        """Registers a key hash in active memory/cache."""
        self._active_keys[key_hash] = metadata

    def validate_key(self, raw_key: str) -> Tuple[bool, Optional[Dict], str]:
        """Validates a raw API key. Returns (is_valid, metadata, error_reason)."""
        if not raw_key or not raw_key.startswith("otc_live_"):
            return False, None, "Formato de chave B2B inválido. Deve iniciar com otc_live_"

        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        key_info = self._active_keys.get(key_hash)

        if not key_info:
            return False, None, "Chave B2B não encontrada ou desativada"

        if not key_info.get("enabled", True):
            return False, None, "Chave B2B revogada ou inativa"

        # Check rate limit
        now = time.time()
        window = self._request_windows.setdefault(key_hash, [])
        # Remover requisições mais antigas que 60 segundos
        self._request_windows[key_hash] = [t for t in window if now - t < 60.0]

        limit_rpm = key_info.get("rate_limit_rpm", 30)
        if len(self._request_windows[key_hash]) >= limit_rpm:
            return False, key_info, f"Cota de requisições excedida ({limit_rpm} req/min). Faça upgrade para Enterprise."

        # Registrar requisição atual
        self._request_windows[key_hash].append(now)

        return True, key_info, ""
