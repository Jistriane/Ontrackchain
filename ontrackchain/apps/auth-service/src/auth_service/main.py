import base64
import binascii
import hashlib
import hmac
import json
import struct
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


class Settings(BaseSettings):
    app_env: str = "local"
    auth_mode: str = "dev"
    dev_auth_enabled: Optional[bool] = None
    oidc_provider: str = "keycloak"
    jwt_issuer: str = "ontrackchain"
    jwt_audience: str = "ontrackchain"
    jwt_hs256_secret: str = "change-me"
    mfa_totp_secret: str = "JBSWY3DPEHPK3PXP"
    mfa_totp_issuer: str = "OnTrackChain"
    mfa_totp_account_name: str = "local-admin@ontrackchain"
    mfa_totp_period_seconds: int = 30
    mfa_totp_digits: int = 6
    mfa_totp_window: int = 1
    oidc_issuer_url: Optional[str] = None
    oidc_audience: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_jwks_url: Optional[str] = None
    oidc_authorization_url: Optional[str] = None
    oidc_org_claim: Optional[str] = None
    oidc_plan_claim: Optional[str] = None
    oidc_role_claim: Optional[str] = None
    mfa_external_provider_homologated: bool = False
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "ontrackchain"
    postgres_password: str = "ontrackchain"
    postgres_db: str = "ontrackchain"


settings = Settings()

app = FastAPI(title="OnTrackChain Auth Service")


class DevTokenRequest(BaseModel):
    org_id: str = "00000000-0000-0000-0000-000000000001"
    user_id: str = "00000000-0000-0000-0000-000000000002"
    plan: str = "enterprise"
    role: str = "ADMIN"
    expires_in_minutes: int = 60


class VerifyTwoFactorRequest(BaseModel):
    code: str


def _dsn() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


@app.on_event("startup")
async def _startup() -> None:
    app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})


@app.on_event("shutdown")
async def _shutdown() -> None:
    pool: ConnectionPool = app.state.pool
    pool.close()


def get_pool() -> ConnectionPool:
    return app.state.pool


def _normalized_auth_mode() -> str:
    mode = settings.auth_mode.strip().lower()
    if mode not in {"dev", "oidc"}:
        raise HTTPException(status_code=500, detail="invalid_auth_mode")
    return mode


def _normalized_app_env() -> str:
    raw = settings.app_env.strip().lower()
    aliases = {
        "dev": "local",
        "development": "local",
        "prod": "production",
    }
    normalized = aliases.get(raw, raw)
    if normalized not in {"local", "test", "staging", "production"}:
        raise HTTPException(status_code=500, detail="invalid_app_env")
    return normalized


def _dev_auth_enabled() -> bool:
    app_env = _normalized_app_env()
    if app_env not in {"local", "test"}:
        return False
    if settings.dev_auth_enabled is not None:
        return settings.dev_auth_enabled
    return True


def _effective_auth_mode() -> str:
    mode = _normalized_auth_mode()
    if mode == "dev" and not _dev_auth_enabled():
        return "oidc"
    return mode


def _totp_secret_bytes() -> bytes:
    normalized = settings.mfa_totp_secret.strip().replace(" ", "").upper()
    if not normalized:
        raise HTTPException(status_code=500, detail="mfa_totp_secret_missing")
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    try:
        return base64.b32decode(f"{normalized}{padding}", casefold=True)
    except binascii.Error as exc:
        raise HTTPException(status_code=500, detail="invalid_mfa_totp_secret") from exc


def _totp_code_for_counter(secret: bytes, counter: int) -> str:
    digest = hmac.new(secret, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    otp = binary % (10**settings.mfa_totp_digits)
    return str(otp).zfill(settings.mfa_totp_digits)


def _verify_totp_code(code: str) -> bool:
    normalized = code.strip()
    if not normalized.isdigit() or len(normalized) != settings.mfa_totp_digits:
        return False
    secret = _totp_secret_bytes()
    counter = int(time.time() // settings.mfa_totp_period_seconds)
    for offset in range(-settings.mfa_totp_window, settings.mfa_totp_window + 1):
        expected = _totp_code_for_counter(secret, counter + offset)
        if hmac.compare_digest(expected, normalized):
            return True
    return False


def _normalized_oidc_provider() -> str:
    provider = settings.oidc_provider.strip().lower()
    if provider not in {"generic", "keycloak", "auth0", "entra"}:
        raise HTTPException(status_code=500, detail="invalid_oidc_provider")
    return provider


def _oidc_provider_defaults() -> dict[str, str]:
    provider = _normalized_oidc_provider()
    defaults: dict[str, dict[str, str]] = {
        "generic": {
            "org_claim": "org_id",
            "plan_claim": "plan",
            "role_claim": "role",
        },
        "keycloak": {
            "org_claim": "org",
            "plan_claim": "plan",
            "role_claim": "otk_role",
        },
        "auth0": {
            "org_claim": "org_id",
            "plan_claim": "plan",
            "role_claim": "role",
        },
        "entra": {
            "org_claim": "tenant_id",
            "plan_claim": "extension_plan",
            "role_claim": "roles",
        },
    }
    return defaults[provider]


def _oidc_required(value: Optional[str], setting_name: str) -> str:
    if value and value.strip():
        return value.strip()
    raise HTTPException(status_code=500, detail=f"missing_{setting_name}")


def _oidc_issuer() -> str:
    return _oidc_required(settings.oidc_issuer_url, "oidc_issuer_url")


def _oidc_client_id() -> str:
    return _oidc_required(settings.oidc_client_id, "oidc_client_id")


@lru_cache(maxsize=1)
def _get_oidc_discovery_document() -> dict:
    issuer = _oidc_issuer().rstrip("/")
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    with urllib.request.urlopen(discovery_url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _oidc_audience() -> str:
    if settings.oidc_audience and settings.oidc_audience.strip():
        return settings.oidc_audience.strip()
    if settings.oidc_client_id and settings.oidc_client_id.strip():
        return settings.oidc_client_id.strip()
    raise HTTPException(status_code=500, detail="missing_oidc_audience")


def _oidc_org_claim() -> str:
    return (settings.oidc_org_claim or _oidc_provider_defaults()["org_claim"]).strip()


def _oidc_plan_claim() -> str:
    return (settings.oidc_plan_claim or _oidc_provider_defaults()["plan_claim"]).strip()


def _oidc_role_claim() -> str:
    return (settings.oidc_role_claim or _oidc_provider_defaults()["role_claim"]).strip()


def _oidc_jwks_url() -> str:
    if settings.oidc_jwks_url and settings.oidc_jwks_url.strip():
        return settings.oidc_jwks_url.strip()
    try:
        jwks_uri = _get_oidc_discovery_document().get("jwks_uri")
        if jwks_uri:
            return str(jwks_uri)
    except Exception:
        pass
    issuer = _oidc_issuer().rstrip("/")
    if _normalized_oidc_provider() == "keycloak":
        return f"{issuer}/protocol/openid-connect/certs"
    return f"{issuer}/.well-known/jwks.json"


def _oidc_authorization_url() -> Optional[str]:
    if settings.oidc_authorization_url and settings.oidc_authorization_url.strip():
        return settings.oidc_authorization_url.strip()
    try:
        authorization_endpoint = _get_oidc_discovery_document().get("authorization_endpoint")
        if authorization_endpoint:
            return str(authorization_endpoint)
    except Exception:
        pass
    issuer = _oidc_issuer().rstrip("/")
    if _normalized_oidc_provider() == "keycloak":
        return f"{issuer}/protocol/openid-connect/auth"
    return None


def _oidc_token_url() -> Optional[str]:
    try:
        token_endpoint = _get_oidc_discovery_document().get("token_endpoint")
        if token_endpoint:
            return str(token_endpoint)
    except Exception:
        pass
    issuer = _oidc_issuer().rstrip("/")
    if _normalized_oidc_provider() == "keycloak":
        return f"{issuer}/protocol/openid-connect/token"
    return None


def _canonicalize_role(raw_role: object) -> str:
    if isinstance(raw_role, list):
        raw_role = raw_role[0] if raw_role else "ANALYST"
    normalized = str(raw_role or "ANALYST").strip()
    mapping = {
        "otk_admin": "ADMIN",
        "otk_analyst": "ANALYST",
        "otk_tester": "TESTER",
        "otk_auditor": "AUDITOR",
        "otk_viewer": "VIEWER",
    }
    return mapping.get(normalized.lower(), normalized.upper())


@lru_cache(maxsize=1)
def _get_oidc_jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(_oidc_jwks_url())


def _validate_api_key(raw_key: str, pool: ConnectionPool) -> dict:
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM validate_api_key_and_get_context(%s)", (key_hash,))
            row = cur.fetchone()
            if not row or not row["is_valid"]:
                raise HTTPException(status_code=401, detail=row["error_code"] if row else "invalid_api_key")

    return {
        "org_id": str(row["org_id"]),
        "user_id": str(row["user_id"]),
        "linked_user_id": str(row["user_id"]),
        "plan": str(row["plan"]),
        "role": str(row["permission_scope"]),
        "auth_method": "api_key",
        "mfa_mode": "not_applicable",
    }


def _resolve_linked_user_id(
    *,
    pool: ConnectionPool,
    auth_method: str,
    org_id: str,
    user_id: str,
    provider: Optional[str] = None,
    email_snapshot: Optional[str] = None,
    role_snapshot: Optional[str] = None,
) -> Optional[str]:
    if auth_method in {"api_key", "dev_jwt"}:
        return user_id
    if auth_method != "jwt" or not provider:
        return None

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE external_identities
                SET
                  last_seen_at = NOW(),
                  email_snapshot = COALESCE(%s, email_snapshot),
                  role_snapshot = COALESCE(%s, role_snapshot)
                WHERE organization_id = %s
                  AND provider = %s
                  AND external_subject = %s
                RETURNING user_id
                """,
                (email_snapshot, role_snapshot, org_id, provider, user_id),
            )
            row = cur.fetchone()
            if not row or not row["user_id"]:
                return None
            return str(row["user_id"])


def _build_jwt_context(
    decoded: dict,
    *,
    pool: ConnectionPool,
    org_claim: str,
    plan_claim: str,
    role_claim: str,
    provider: Optional[str] = None,
    auth_method_label: str = "jwt",
) -> dict:
    org_id = decoded.get(org_claim)
    user_id = decoded.get("sub")
    plan = decoded.get(plan_claim, "free")
    role = _canonicalize_role(decoded.get(role_claim, "ANALYST"))
    if not org_id or not user_id:
        raise HTTPException(status_code=401, detail="invalid_claims")

    linked_user_id = _resolve_linked_user_id(
        pool=pool,
        auth_method=auth_method_label,
        org_id=str(org_id),
        user_id=str(user_id),
        provider=provider,
        email_snapshot=str(decoded.get("email")) if decoded.get("email") else None,
        role_snapshot=role,
    )

    return {
        "org_id": str(org_id),
        "user_id": str(user_id),
        "linked_user_id": linked_user_id,
        "plan": str(plan),
        "role": role,
        "auth_method": "jwt" if auth_method_label == "jwt" else auth_method_label,
        "mfa_mode": "external_provider" if auth_method_label == "jwt" else "local_totp",
        "mfa_provider_homologated": settings.mfa_external_provider_homologated if auth_method_label == "jwt" else True,
    }


def _validate_dev_jwt(token: str, pool: ConnectionPool) -> dict:
    if not _dev_auth_enabled():
        raise HTTPException(status_code=401, detail="dev_auth_disabled")
    try:
        decoded = jwt.decode(
            token,
            settings.jwt_hs256_secret,
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc
    return _build_jwt_context(
        decoded,
        pool=pool,
        org_claim="org_id",
        plan_claim="plan",
        role_claim="role",
        auth_method_label="dev_jwt",
    )


def _validate_oidc_jwt(token: str, pool: ConnectionPool) -> dict:
    try:
        signing_key = _get_oidc_jwks_client().get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"],
            audience=_oidc_audience(),
            issuer=_oidc_issuer(),
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc
    return _build_jwt_context(
        decoded,
        pool=pool,
        org_claim=_oidc_org_claim(),
        plan_claim=_oidc_plan_claim(),
        role_claim=_oidc_role_claim(),
        provider=_normalized_oidc_provider(),
        auth_method_label="jwt",
    )


def _require_auth(
    authorization: Annotated[Optional[str], Header()] = None,
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
    pool: ConnectionPool = Depends(get_pool),
) -> dict:
    if x_api_key:
        return _validate_api_key(x_api_key, pool)

    if not authorization:
        raise HTTPException(status_code=401, detail="missing_authorization")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="invalid_authorization_scheme")

    token = parts[1].strip()
    if _effective_auth_mode() == "oidc":
        return _validate_oidc_jwt(token, pool)
    return _validate_dev_jwt(token, pool)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/validate")
async def validate(response: Response, auth: dict = Depends(_require_auth)) -> dict:
    response.headers["X-Org-Id"] = auth["org_id"]
    response.headers["X-User-Id"] = auth["user_id"]
    if auth.get("linked_user_id"):
        response.headers["X-Linked-User-Id"] = auth["linked_user_id"]
    response.headers["X-Plan"] = auth["plan"]
    response.headers["X-Role"] = auth["role"]
    response.headers["X-Auth-Method"] = auth["auth_method"]
    response.headers["X-MFA-Mode"] = auth["mfa_mode"]
    response.headers["X-MFA-Provider-Homologated"] = "true" if auth.get("mfa_provider_homologated") else "false"
    return {"status": "ok", "linked_user_id": auth.get("linked_user_id")}


@app.get("/auth/config")
async def auth_config() -> dict:
    mode = _normalized_auth_mode()
    effective_mode = _effective_auth_mode()
    if effective_mode == "dev":
        return {
            "auth_mode": "dev",
            "effective_auth_mode": "dev",
            "app_env": _normalized_app_env(),
            "dev_auth_enabled": True,
            "oidc": {
                "enabled": False,
                "provider": _normalized_oidc_provider(),
                "issuer_url": None,
                "client_id": None,
                "audience": None,
                "authorization_url": None,
            },
            "mfa": {
                "enabled": True,
                "method": "totp",
                "managed_by": "auth_service",
                "provider_homologated": True,
                "issuer": settings.mfa_totp_issuer,
                "account_name": settings.mfa_totp_account_name,
                "period_seconds": settings.mfa_totp_period_seconds,
                "digits": settings.mfa_totp_digits,
            },
        }

    authorization_url = _oidc_authorization_url()
    if not authorization_url:
        raise HTTPException(status_code=500, detail="missing_oidc_authorization_url")

    token_url = _oidc_token_url()
    if not token_url:
        raise HTTPException(status_code=500, detail="missing_oidc_token_url")

    return {
        "auth_mode": mode,
        "effective_auth_mode": "oidc",
        "app_env": _normalized_app_env(),
        "dev_auth_enabled": _dev_auth_enabled(),
        "oidc": {
            "enabled": True,
            "provider": _normalized_oidc_provider(),
            "issuer_url": _oidc_issuer(),
            "client_id": _oidc_client_id(),
            "audience": _oidc_audience(),
            "authorization_url": authorization_url,
            "token_url": token_url,
            "claims": {
                "org": _oidc_org_claim(),
                "plan": _oidc_plan_claim(),
                "role": _oidc_role_claim(),
            },
        },
        "mfa": {
            "enabled": True,
            "method": "external_provider",
            "managed_by": "oidc_provider",
            "provider": _normalized_oidc_provider(),
            "provider_homologated": settings.mfa_external_provider_homologated,
        },
    }


@app.post("/auth/issue-dev-token")
async def issue_dev_token(req: DevTokenRequest) -> dict:
    if _normalized_auth_mode() != "dev" or not _dev_auth_enabled():
        raise HTTPException(status_code=404, detail="dev_auth_disabled")
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=req.expires_in_minutes)
    payload = {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": req.user_id,
        "org_id": req.org_id,
        "plan": req.plan,
        "role": req.role,
    }
    token = jwt.encode(payload, settings.jwt_hs256_secret, algorithm="HS256")
    return {"token": token, "expires_at": exp.isoformat()}


@app.post("/auth/verify-2fa")
async def verify_two_factor(body: VerifyTwoFactorRequest, auth: dict = Depends(_require_auth)) -> dict:
    if auth.get("auth_method") != "dev_jwt":
        raise HTTPException(status_code=403, detail="2fa_requires_dev_auth")
    if not _verify_totp_code(body.code):
        raise HTTPException(status_code=401, detail="invalid_2fa")
    return {
        "status": "ok",
        "method": "totp",
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
