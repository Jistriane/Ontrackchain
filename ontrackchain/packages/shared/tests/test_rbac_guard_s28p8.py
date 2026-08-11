"""RBAC Guard v1.1 — testes Sprint28+8 (P1.05, P1.06, P1.07 validação em sandbox).

Cobertura alvo ≥ 80%:
   ✅ CanonicalRole 9 roles + CanonicalCapability 7 caps
   ✅ is_valid_role_format regex OTK_[A-Z0-9_]{2,64}
   ✅ ROLE_TO_CAPABILITIES (9 roles → capabilities merge ADR-012 §4.2)
   ✅ _roles_to_capabilities() união
   ✅ RBACGuard.__init__ modes + audience mínima length
   ✅ _extract_bearer_token (Bearer / malformado / faltando / menos de 3 segs)
   ✅ require_roles mode_all AND / mode OR
   ✅ require_capability via 3 caminhos (expanded / claim / implicit)
   ✅ enforced=False claims fake viewer
   ✅ extract_and_validate_claims INTEGRADO com RSA 2048 + JWKS
   ✅ default_guard_from_env registry singleton por audience
   ✅ SignatureError JWT → PermissionError 401
   ✅ Audience mismatch → PermissionError 401
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any

import pytest

from ontrackchain_shared.rbac_guard import (
    CanonicalCapability,
    CanonicalRole,
    RBACGuard,
    ROLE_TO_CAPABILITIES,
    _roles_to_capabilities,
    default_guard_from_env,
    is_valid_role_format,
)


# ============================================================
# Helpers: gerar RSA 2048 keypair + montar JWKS em memória
# ============================================================
def _rsa_keypair_and_jwks(kid: str = "kid-s28p8-unit-001") -> dict[str, Any]:
    """Gera par RSA 2048 + private JWK + public JWKS (padrão RFC 7517)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from jwt.algorithms import RSAAlgorithm

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = private_key.public_key()
    pub_jwk = RSAAlgorithm.to_jwk(pub, as_dict=True)
    pub_jwk["kid"] = kid
    pub_jwk["use"] = "sig"
    pub_jwk["alg"] = "RS256"
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    return {
        "kid": kid,
        "private_pem": priv_pem,
        "jwks_dict": {"keys": [pub_jwk]},
    }


def _sign_jwt(private_pem: str, kid: str, payload: dict, algorithm: str = "RS256") -> str:
    import jwt as _jwt

    return _jwt.encode(payload, private_pem, algorithm=algorithm, headers={"kid": kid})


# ============================================================
# 1. CanonicalRole / CanonicalCapability / Formato
# ============================================================
class TestCanonicalEnums:
    def test_nine_canonical_roles_exist(self):
        roles = {r.value for r in CanonicalRole}
        assert len(roles) == 9
        for required in ("OTK_ADMIN", "OTK_ANALYST", "OTK_COMPLIANCE_OFFICER",
                         "OTK_AUDITOR", "OTK_VIEWER", "OTK_LEGAL_REVIEWER",
                         "OTK_REVIEWER", "OTK_BILLING_ADMIN", "OTK_TESTER"):
            assert required in roles

    def test_seven_capabilities_exist(self):
        caps = {c.value for c in CanonicalCapability}
        assert len(caps) == 7

    @pytest.mark.parametrize("role,expected", [
        ("OTK_ADMIN", True),
        ("OTK_COMPLIANCE_OFFICER", True),
        ("OTK_X_123", True),
        ("OTK_", False),                 # min 2 chars pós prefixo
        ("otk_admin", False),            # minúsculas proibidas
        ("ADMIN", False),                # sem prefixo OTK_
        ("", False),
        (None, False),
        (1234, False),
        ("OTK_TOO_LONG_ROLE_NAME_A_B_C_D_E_F_G_H_I_J_K_L_M_N_O_P_Q_R_S_T", False),  # 64+ chars
    ])
    def test_is_valid_role_format(self, role, expected):
        assert is_valid_role_format(role) is expected


# ============================================================
# 2. ROLE_TO_CAPABILITIES — fonte única ADR-012 §4.2
# ============================================================
class TestRoleToCapabilities:
    def test_all_nine_roles_are_mapped(self):
        roles = {r.value for r in CanonicalRole}
        assert set(ROLE_TO_CAPABILITIES.keys()) == roles

    def test_admin_has_all_seven_capabilities(self):
        caps = ROLE_TO_CAPABILITIES[CanonicalRole.OTK_ADMIN.value]
        all_caps = {c.value for c in CanonicalCapability}
        assert caps == all_caps

    def test_viewer_has_no_capabilities(self):
        assert ROLE_TO_CAPABILITIES[CanonicalRole.OTK_VIEWER.value] == set()

    def test_billing_admin_only_run_billing(self):
        caps = ROLE_TO_CAPABILITIES[CanonicalRole.OTK_BILLING_ADMIN.value]
        assert caps == {CanonicalCapability.CAN_RUN_BILLING.value}

    def test_roles_to_capabilities_union(self):
        out = _roles_to_capabilities([
            CanonicalRole.OTK_BILLING_ADMIN.value,
            CanonicalRole.OTK_VIEWER.value,
            "ROLE_INVALIDO_IGNORADO",
        ])
        assert out == {CanonicalCapability.CAN_RUN_BILLING.value}


# ============================================================
# 3. RBACGuard init / Bearer extract / Require roles mode
# ============================================================
class TestRBACGuardBasics:
    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="modo RBAC inválido"):
            RBACGuard(jwks_url="https://x/jwks", audience="aud-teste", mode="banana")

    def test_short_audience_raises(self):
        with pytest.raises(ValueError, match="audience RBAC OIDC obrigatória"):
            RBACGuard(jwks_url="https://x/jwks", audience="ab")

    def test_default_mode_shared_first(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud-min-tres")
        assert g.mode == "shared_first"
        assert g.enforced is True

    @pytest.mark.parametrize("auth,expect", [
        ("Bearer abc.def.ghi", "abc.def.ghi"),
        ("  BEARER   a.b.c  ", "a.b.c"),
    ])
    def test_extract_bearer_ok(self, auth, expect):
        assert RBACGuard._extract_bearer_token(auth) == expect

    @pytest.mark.parametrize("auth", [
        None, "", "Basic dXNlcjpwYXNz", "Bearer",
        "Bearer dois-segmentos-so", "Bearer  .  .",
    ])
    def test_extract_bearer_bad(self, auth):
        with pytest.raises(ValueError):
            RBACGuard._extract_bearer_token(auth)

    def test_require_roles_all_and_any(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud-teste", enforced=True)
        claims = {"roles": ["OTK_ADMIN", "OTK_ANALYST"]}
        # ALL: ambas
        g.require_roles(claims, [CanonicalRole.OTK_ADMIN, CanonicalRole.OTK_ANALYST], mode_all=True)
        # ANY: uma das duas
        g.require_roles(claims, [CanonicalRole.OTK_VIEWER, CanonicalRole.OTK_ADMIN], mode_all=False)

    def test_require_roles_all_fails_missing(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud-teste", enforced=True)
        claims = {"roles": ["OTK_ANALYST"]}
        with pytest.raises(PermissionError, match="RBAC 403"):
            g.require_roles(claims, [CanonicalRole.OTK_ADMIN, CanonicalRole.OTK_ANALYST], mode_all=True)

    def test_require_any_roles_all_missing_fails(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud-teste", enforced=True)
        with pytest.raises(PermissionError):
            g.require_roles({"roles": ["OTK_VIEWER"]}, [CanonicalRole.OTK_ADMIN, CanonicalRole.OTK_ANALYST], mode_all=False)

    def test_enforced_off_bypasses_everything(self):
        g = RBACGuard(jwks_url="", audience="aud-teste", enforced=False)
        claims = {}
        g.require_roles(claims, [CanonicalRole.OTK_ADMIN], mode_all=True)  # não levanta
        fake = g.extract_and_validate_claims(None)
        assert fake["roles_normalized"] == ["OTK_VIEWER"]
        assert fake["sub"] == "staging-fake-user"


# ============================================================
# 4. Capabilities 3 caminhos resolução
# ============================================================
class TestCapabilitiesResolution:
    def test_path_1_capabilities_expanded(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud", enforced=True)
        claims = {"capabilities_expanded": ["can_view_pii_full"]}
        assert g.has_capability(claims, CanonicalCapability.CAN_VIEW_PII_FULL) is True

    def test_path_2_capabilities_claim_explicit(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud", enforced=True)
        claims = {"capabilities": ["can_run_billing"]}
        assert g.has_capability(claims, CanonicalCapability.CAN_RUN_BILLING) is True

    def test_path_3_implicit_via_role_mapping(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud", enforced=True)
        claims = {"roles": ["OTK_BILLING_ADMIN"]}
        assert g.has_capability(claims, CanonicalCapability.CAN_RUN_BILLING) is True
        assert g.has_capability(claims, CanonicalCapability.CAN_MANAGE_USERS) is False

    def test_require_capability_fails(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud", enforced=True)
        with pytest.raises(PermissionError, match="capability"):
            g.require_capability({"roles": ["OTK_VIEWER"]}, CanonicalCapability.CAN_EXPORT_PII)

    def test_empty_claims_false(self):
        g = RBACGuard(jwks_url="https://x/jwks", audience="aud", enforced=True)
        assert g.has_capability({}, CanonicalCapability.CAN_VIEW_PII_FULL) is False


# ============================================================
# 5. extract_and_validate_claims RSA+JWKS integração
# ============================================================
class TestJwtWithJwks:
    @pytest.fixture(scope="class")
    def kp(self):
        return _rsa_keypair_and_jwks()

    @pytest.fixture
    def guard(self, monkeypatch, kp):
        """Cria guard apontando para JWKS servido por httpx mocado local."""
        import httpx

        aud = "aud-s28p8-int"
        jwks_url = "https://kc-fake.local/auth/realms/otk/protocol/openid-connect/certs"

        # Stub do PyJWKClient substituindo método de fetch: mais simples — usamos transport custom httpx
        def _get_jwks(self_ref, *args, **kwargs):  # type: ignore[no-untyped-def]
            return kp["jwks_dict"]

        # Monkeypatch PyJWKClient fetch_data para não sair da rede
        import jwt as _jwtmod
        monkeypatch.setattr(_jwtmod.PyJWKClient, "fetch_data", _get_jwks)

        guard = RBACGuard(jwks_url=jwks_url, audience=aud, enforced=True)
        return guard

    def test_valid_rs256_admin_claims(self, guard, kp):
        iat = int(time.time()) - 10
        exp = int(time.time()) + 3600
        payload = {
            "iss": "https://kc-fake.local/auth/realms/otk",
            "aud": guard.audience,
            "sub": "usr-e2e-0001",
            "iat": iat,
            "exp": exp,
            "roles": ["OTK_ADMIN"],
        }
        token = _sign_jwt(kp["private_pem"], kp["kid"], payload)
        claims = guard.extract_and_validate_claims(f"Bearer {token}", issuer="https://kc-fake.local/auth/realms/otk")
        assert claims["sub"] == "usr-e2e-0001"
        assert "OTK_ADMIN" in claims["roles_normalized"]
        assert CanonicalCapability.CAN_MANAGE_USERS.value in claims["capabilities_expanded"]
        # require role admin OK
        guard.require_roles(claims, [CanonicalRole.OTK_ADMIN])

    def test_bad_signature_rejected(self, guard, kp):
        # Gerar OUTRA keypair e assinar com ela — kid colide mas key dif
        kp2 = _rsa_keypair_and_jwks(kid=kp["kid"])  # mesmo kid, key errada
        payload = {"aud": guard.audience, "exp": int(time.time()) + 3600, "roles": ["OTK_ADMIN"]}
        fake_token = _sign_jwt(kp2["private_pem"], kp2["kid"], payload)
        with pytest.raises(PermissionError, match="JWT 401"):
            guard.extract_and_validate_claims(f"Bearer {fake_token}")

    def test_audience_mismatch_rejected(self, guard, kp):
        payload = {"aud": "audience-errada", "exp": int(time.time()) + 3600}
        token = _sign_jwt(kp["private_pem"], kp["kid"], payload)
        with pytest.raises(PermissionError, match="JWT 401"):
            guard.extract_and_validate_claims(f"Bearer {token}")

    def test_jwt_metrics_incremented(self, guard, kp):
        before = guard.metrics()["jwt_validations_total"]
        payload = {"aud": guard.audience, "exp": int(time.time()) + 3600, "roles": ["OTK_VIEWER"]}
        token = _sign_jwt(kp["private_pem"], kp["kid"], payload)
        guard.extract_and_validate_claims(f"Bearer {token}")
        after = guard.metrics()["jwt_validations_total"]
        assert after == before + 1


# ============================================================
# 6. default_guard_from_env + Registry singleton thread-safe
# ============================================================
class TestDefaultGuardFromEnv:
    def test_missing_audience_env_raises(self, monkeypatch):
        for k in ("OTK_AUDIENCE",):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.delenv("OTK_JWKS_URL", raising=False)
        # Limpar registry para garantir singleton não persiste cross-testes
        from ontrackchain_shared import rbac_guard as _mod
        _mod._GUARD_REGISTRY.clear()
        with pytest.raises(ValueError, match="Faltando env OTK_AUDIENCE"):
            default_guard_from_env()

    def test_singleton_per_audience(self, monkeypatch):
        from ontrackchain_shared import rbac_guard as _mod
        _mod._GUARD_REGISTRY.clear()
        monkeypatch.setenv("OTK_AUDIENCE", "aud-registry-a")
        monkeypatch.setenv("OTK_JWKS_URL", "https://x/a/jwks")
        monkeypatch.setenv("OTK_RBAC_ENFORCED", "false")
        g1 = default_guard_from_env()
        g2 = default_guard_from_env()
        assert g1 is g2

    def test_oidc_issuer_fallback_builds_jwks_keycloak(self, monkeypatch):
        from ontrackchain_shared import rbac_guard as _mod
        _mod._GUARD_REGISTRY.clear()
        monkeypatch.setenv("OTK_AUDIENCE", "aud-discovery")
        monkeypatch.delenv("OTK_JWKS_URL", raising=False)
        monkeypatch.setenv("OTK_OIDC_ISSUER", "https://kc.example/realms/otk")
        # httpx discovery vai falhar sem rede — mas a branch de fallback padrão é /protocol/openid-connect/certs
        # Portanto guard ainda vai ser construído; jwks_url montado corretamente
        g = default_guard_from_env()
        assert g.jwks_url.endswith("/protocol/openid-connect/certs")
