from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

import jwt
from fastapi import FastAPI, Form, HTTPException, Query, Request
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOCK_OIDC_")
    issuer_url: str = "http://oidc.localhost"
    audience: str = "ontrackchain-api"
    client_id: str = "ontrackchain-web"
    token_ttl_seconds: int = 3600
    code_ttl_seconds: int = 300


settings = Settings()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _pkce_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return _b64url(digest)


def _rsa_keypair():
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key


def _jwks_from_public_key(public_key, *, kid: str) -> dict[str, Any]:
    numbers = public_key.public_numbers()
    n = _b64url(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big"))
    e = _b64url(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big"))
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": kid,
                "n": n,
                "e": e,
            }
        ]
    }


def _now_ts() -> int:
    return int(time.time())


def _normalize_role(role: str) -> str:
    normalized = (role or "").strip().upper()
    allowed = {"ADMIN", "COMPLIANCE_OFFICER", "LEGAL_REVIEWER", "ANALYST"}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="invalid_role")
    return normalized


def _issue_access_token(
    *,
    issuer: str,
    audience: str,
    subject: str,
    org: str,
    plan: str,
    role: str,
    private_key,
    kid: str,
) -> str:
    now = _now_ts()
    payload = {
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + settings.token_ttl_seconds,
        "sub": subject,
        "org": org,
        "plan": plan,
        "otk_role": role,
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": kid, "typ": "JWT"},
    )


@dataclass
class AuthCodeRecord:
    code_challenge: Optional[str]
    code_challenge_method: Optional[str]
    redirect_uri: str
    role: str
    org: str
    plan: str
    subject: str
    created_at: int


class MockTokenRequest(BaseModel):
    role: str
    org: str = "00000000-0000-0000-0000-000000000001"
    plan: str = "professional"
    sub: Optional[str] = None


app = FastAPI(title="Ontrackchain Mock OIDC", version="0.1.0")

_private_key, _public_key = _rsa_keypair()
_kid = _b64url(os.urandom(12))
_jwks = _jwks_from_public_key(_public_key, kid=_kid)

_auth_codes: dict[str, AuthCodeRecord] = {}


def _purge_expired_codes() -> None:
    now = _now_ts()
    expired = [k for k, v in _auth_codes.items() if now - v.created_at > settings.code_ttl_seconds]
    for k in expired:
        _auth_codes.pop(k, None)


@app.get("/.well-known/openid-configuration")
async def openid_configuration() -> dict[str, Any]:
    issuer = settings.issuer_url.rstrip("/")
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/authorize",
        "token_endpoint": f"{issuer}/oauth/token",
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["none"],
        "claims_supported": ["sub", "org", "plan", "otk_role", "aud", "iss", "exp", "iat"],
    }


@app.get("/.well-known/jwks.json")
async def jwks() -> dict[str, Any]:
    return _jwks


@app.get("/authorize")
async def authorize(
    request: Request,
    response_type: str = Query("code"),
    client_id: str = Query(""),
    redirect_uri: str = Query(""),
    scope: str = Query("openid profile email"),
    state: str = Query(""),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query(None),
    role: str = Query("ANALYST"),
    org: str = Query("00000000-0000-0000-0000-000000000001"),
    plan: str = Query("professional"),
) -> Any:
    _purge_expired_codes()
    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported_response_type")
    if not client_id or client_id != settings.client_id:
        raise HTTPException(status_code=400, detail="invalid_client_id")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="missing_redirect_uri")
    if not state:
        raise HTTPException(status_code=400, detail="missing_state")
    if "openid" not in (scope or ""):
        raise HTTPException(status_code=400, detail="missing_openid_scope")

    normalized_role = _normalize_role(role)
    subject = str(uuid.uuid4())
    code = _b64url(os.urandom(18))

    _auth_codes[code] = AuthCodeRecord(
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        redirect_uri=redirect_uri,
        role=normalized_role,
        org=org,
        plan=plan,
        subject=subject,
        created_at=_now_ts(),
    )

    from fastapi.responses import RedirectResponse

    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{separator}code={code}&state={state}", status_code=302)


@app.post("/oauth/token")
async def token(
    grant_type: str = Form("authorization_code"),
    client_id: str = Form(""),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    code_verifier: str = Form(""),
) -> dict[str, Any]:
    _purge_expired_codes()
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    if not client_id or client_id != settings.client_id:
        raise HTTPException(status_code=400, detail="invalid_client_id")
    if not code or code not in _auth_codes:
        raise HTTPException(status_code=400, detail="invalid_code")

    record = _auth_codes.pop(code)
    if record.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="redirect_uri_mismatch")

    if record.code_challenge:
        if not code_verifier:
            raise HTTPException(status_code=400, detail="missing_code_verifier")
        if (record.code_challenge_method or "").upper() not in {"S256", ""}:
            raise HTTPException(status_code=400, detail="unsupported_code_challenge_method")
        if _pkce_s256(code_verifier) != record.code_challenge:
            raise HTTPException(status_code=400, detail="invalid_code_verifier")

    access_token = _issue_access_token(
        issuer=settings.issuer_url.rstrip("/"),
        audience=settings.audience,
        subject=record.subject,
        org=record.org,
        plan=record.plan,
        role=record.role,
        private_key=_private_key,
        kid=_kid,
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.token_ttl_seconds,
        "scope": "openid profile email",
    }


@app.post("/mock/token")
async def mock_token(body: MockTokenRequest) -> dict[str, Any]:
    normalized_role = _normalize_role(body.role)
    subject = body.sub or str(uuid.uuid4())
    access_token = _issue_access_token(
        issuer=settings.issuer_url.rstrip("/"),
        audience=settings.audience,
        subject=subject,
        org=body.org,
        plan=body.plan,
        role=normalized_role,
        private_key=_private_key,
        kid=_kid,
    )
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": settings.token_ttl_seconds,
        "scope": "openid profile email",
    }
