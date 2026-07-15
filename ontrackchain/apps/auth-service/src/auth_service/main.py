import base64
import binascii
import hashlib
import hmac
import json
import logging
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Any, Optional
from uuid import UUID

import jwt
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
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
    # Redis — blocklist Stage 1 (pre-screening preventivo)
    redis_host: str = "redis"
    redis_port: int = 6379
    keycloak_admin_base_url: Optional[str] = None
    keycloak_admin_realm: str = "ontrackchain"
    keycloak_admin_client_id: Optional[str] = None
    keycloak_admin_client_secret: Optional[str] = None
    keycloak_admin_timeout_seconds: float = 5.0
    keycloak_admin_search_limit: int = 20
    keycloak_admin_org_attribute: str = "organization_id"
    keycloak_admin_role_attribute: str = "otk_role"


settings = Settings()
logger = logging.getLogger(__name__)

TEAM_USER_ALLOWED_ROLES = {
    "ADMIN",
    "ANALYST",
    "AUDITOR",
    "VIEWER",
    "COMPLIANCE_OFFICER",
    "LEGAL_REVIEWER",
    "REVIEWER",
    "BILLING_ADMIN",
}
TEAM_USER_ALLOWED_STATUSES = {"active", "invited", "disabled"}
TEAM_USER_WRITE_ALLOWED_ROLES = {"ADMIN"}
TEAM_USER_CREATE_ALLOWED_ROLES = {"ADMIN"}
TEAM_USER_UPDATE_ALLOWED_ROLES = {"ADMIN"}
TEAM_USER_DISABLE_ALLOWED_ROLES = {"ADMIN"}
TEAM_FEDERATED_IDENTITY_READ_ALLOWED_ROLES = {"ADMIN"}
TEAM_FEDERATED_IDENTITY_LINK_ALLOWED_ROLES = {"ADMIN"}
TEAM_FEDERATED_IDENTITY_UNLINK_ALLOWED_ROLES = {"ADMIN"}
TEAM_FEDERATED_DIRECTORY_SEARCH_ALLOWED_ROLES = {"ADMIN"}
TEAM_FEDERATED_DIRECTORY_SUGGESTION_ALLOWED_ROLES = {"ADMIN"}

app = FastAPI(title="OnTrackChain Auth Service")


class DevTokenRequest(BaseModel):
    org_id: str = "00000000-0000-0000-0000-000000000001"
    user_id: str = "00000000-0000-0000-0000-000000000002"
    plan: str = "enterprise"
    role: str = "ADMIN"
    expires_in_minutes: int = 60


class VerifyTwoFactorRequest(BaseModel):
    code: str


class TeamUserRecord(BaseModel):
    member_id: str
    name: str
    email: str
    role: str
    status: str
    note: str
    created_at: str
    updated_at: str
    linked_identity_count: int = 0
    last_identity_seen_at: Optional[str] = None


class TeamUserListResponse(BaseModel):
    data: list[TeamUserRecord]


class TeamExternalIdentityRecord(BaseModel):
    provider: str
    external_subject: str
    email_snapshot: Optional[str] = None
    role_snapshot: Optional[str] = None
    created_at: str
    last_seen_at: Optional[str] = None


class TeamExternalIdentityListResponse(BaseModel):
    data: list[TeamExternalIdentityRecord]


class CreateTeamUserRequest(BaseModel):
    name: str = ""
    email: str
    role: str = "ANALYST"
    status: str = "invited"
    note: str = ""


class UpdateTeamUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


class LinkExternalIdentityRequest(BaseModel):
    provider: str = "keycloak"
    external_subject: str
    email_snapshot: Optional[str] = None
    role_snapshot: Optional[str] = None


class UnlinkExternalIdentityRequest(BaseModel):
    provider: str
    external_subject: str


class FederatedDirectoryUserRecord(BaseModel):
    provider: str
    external_subject: str
    email: Optional[str] = None
    username: Optional[str] = None
    organization_id: Optional[str] = None
    role_snapshot: Optional[str] = None
    enabled: bool = True
    match_status: str
    linked_user_id: Optional[str] = None
    linked_user_email: Optional[str] = None
    role_validation_status: str
    warnings: list[str] = Field(default_factory=list)


class FederatedDirectoryUserListResponse(BaseModel):
    data: list[FederatedDirectoryUserRecord]


class ValidateFederatedDirectorySuggestionRequest(BaseModel):
    member_id: str
    provider: str = "keycloak"
    external_subject: str


class ValidateFederatedDirectorySuggestionResponse(BaseModel):
    can_link: bool
    match_reason: str
    org_match: bool
    email_match: bool
    provider: str
    external_subject: str
    candidate_email: Optional[str] = None
    candidate_username: Optional[str] = None
    candidate_org: Optional[str] = None
    role_snapshot: Optional[str] = None
    role_validation_status: str
    linked_user_id: Optional[str] = None
    linked_user_email: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class KeycloakDirectoryClient:
    def __init__(
        self,
        *,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.realm = realm.strip()
        self.client_id = client_id.strip()
        self.client_secret = client_secret
        self.timeout_seconds = timeout_seconds
        self._access_token: Optional[str] = None
        self._access_token_expires_at: float = 0.0

    def search_users(self, *, query: str, limit: int) -> list[dict]:
        params = {"search": query, "max": str(limit), "briefRepresentation": "false"}
        response = self._request_json(
            method="GET",
            path=f"/admin/realms/{urllib.parse.quote(self.realm, safe='')}/users",
            query=params,
            authorized=True,
        )
        return response if isinstance(response, list) else []

    def get_user(self, *, external_subject: str) -> dict:
        response = self._request_json(
            method="GET",
            path=(
                f"/admin/realms/{urllib.parse.quote(self.realm, safe='')}/users/"
                f"{urllib.parse.quote(external_subject, safe='')}"
            ),
            authorized=True,
        )
        return response if isinstance(response, dict) else {}

    def _get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._access_token_expires_at:
            return self._access_token

        payload = urllib.parse.urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        ).encode("utf-8")
        response = self._request_json(
            method="POST",
            path=f"/realms/{urllib.parse.quote(self.realm, safe='')}/protocol/openid-connect/token",
            body=payload,
            content_type="application/x-www-form-urlencoded",
            authorized=False,
        )
        if not isinstance(response, dict) or not response.get("access_token"):
            raise HTTPException(status_code=503, detail="federated_directory_unavailable")

        self._access_token = str(response["access_token"])
        expires_in = int(response.get("expires_in") or 60)
        self._access_token_expires_at = now + max(expires_in - 10, 5)
        return self._access_token

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        query: Optional[dict[str, str]] = None,
        body: Optional[bytes] = None,
        content_type: str = "application/json",
        authorized: bool,
    ) -> Any:
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        headers: dict[str, str] = {"accept": "application/json"}
        if body is not None:
            headers["content-type"] = content_type
        if authorized:
            headers["authorization"] = f"Bearer {self._get_access_token()}"

        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                payload = response.read().decode(charset).strip()
                return json.loads(payload) if payload else {}
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise HTTPException(status_code=503, detail="federated_directory_forbidden") from exc
            if exc.code == 404:
                raise HTTPException(status_code=404, detail="federated_directory_candidate_not_found") from exc
            raise HTTPException(status_code=503, detail="federated_directory_unavailable") from exc
        except urllib.error.URLError as exc:
            raise HTTPException(status_code=503, detail="federated_directory_unavailable") from exc
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=503, detail="federated_directory_unavailable") from exc


def _dsn() -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


@app.on_event("startup")
async def _startup() -> None:
    app.state.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
    # Redis client para pre-screening Stage 1 (blocklist preventiva)
    app.state.redis = aioredis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )


@app.on_event("shutdown")
async def _shutdown() -> None:
    pool: ConnectionPool = app.state.pool
    pool.close()
    await app.state.redis.aclose()


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
        "otk_compliance_officer": "COMPLIANCE_OFFICER",
        "otk_legal_reviewer": "LEGAL_REVIEWER",
        "otk_reviewer": "REVIEWER",
        "otk_billing_admin": "BILLING_ADMIN",
    }
    return mapping.get(normalized.lower(), normalized.upper())


def _normalize_team_user_role(raw_role: Optional[str]) -> str:
    normalized_role = _canonicalize_role(raw_role or "ANALYST")
    if normalized_role not in TEAM_USER_ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail="invalid_team_user_role")
    return normalized_role


def _normalize_team_user_status(raw_status: Optional[str]) -> str:
    normalized_status = str(raw_status or "invited").strip().lower()
    if normalized_status not in TEAM_USER_ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail="invalid_team_user_status")
    return normalized_status


def _normalize_team_user_name(raw_name: Optional[str], *, fallback_email: str) -> str:
    normalized_name = str(raw_name or "").strip()
    return normalized_name or fallback_email


def _normalize_team_user_note(raw_note: Optional[str]) -> str:
    return str(raw_note or "").strip()


def _normalize_team_user_email(raw_email: Optional[str]) -> str:
    normalized_email = str(raw_email or "").strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise HTTPException(status_code=422, detail="invalid_team_user_email")
    return normalized_email


def _normalize_identity_provider(raw_provider: Optional[str]) -> str:
    normalized_provider = str(raw_provider or "").strip().lower()
    if not normalized_provider:
        raise HTTPException(status_code=422, detail="team_external_identity_provider_required")
    if any(char.isspace() for char in normalized_provider):
        raise HTTPException(status_code=422, detail="team_external_identity_provider_invalid")
    return normalized_provider


def _normalize_external_subject(raw_subject: Optional[str]) -> str:
    normalized_subject = str(raw_subject or "").strip()
    if not normalized_subject:
        raise HTTPException(status_code=422, detail="team_external_identity_subject_required")
    return normalized_subject


def _normalize_optional_snapshot(raw_value: Optional[str]) -> Optional[str]:
    normalized_value = str(raw_value or "").strip()
    return normalized_value or None


def _normalize_federated_directory_query(raw_query: Optional[str]) -> str:
    normalized_query = str(raw_query or "").strip()
    if len(normalized_query) < 2:
        raise HTTPException(status_code=422, detail="federated_directory_query_required")
    return normalized_query


def _normalize_federated_directory_limit(raw_limit: Optional[int]) -> int:
    try:
        normalized_limit = int(raw_limit or settings.keycloak_admin_search_limit)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="federated_directory_limit_invalid") from None
    if normalized_limit < 1 or normalized_limit > 50:
        raise HTTPException(status_code=422, detail="federated_directory_limit_invalid")
    return normalized_limit


def _normalize_keycloak_attribute_value(raw_value: Any) -> Optional[str]:
    if isinstance(raw_value, list):
        raw_value = raw_value[0] if raw_value else None
    normalized_value = str(raw_value or "").strip()
    return normalized_value or None


def _keycloak_admin_required(value: Optional[str], setting_name: str) -> str:
    if value and str(value).strip():
        return str(value).strip()
    raise HTTPException(status_code=503, detail=f"missing_{setting_name}")


def _keycloak_admin_base_url() -> str:
    if settings.keycloak_admin_base_url and settings.keycloak_admin_base_url.strip():
        return settings.keycloak_admin_base_url.strip().rstrip("/")
    issuer = settings.oidc_issuer_url
    if issuer and issuer.strip():
        parsed = urllib.parse.urlparse(issuer.strip())
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    raise HTTPException(status_code=503, detail="missing_keycloak_admin_base_url")


def _keycloak_admin_realm() -> str:
    return _keycloak_admin_required(settings.keycloak_admin_realm, "keycloak_admin_realm")


def _keycloak_admin_client_id() -> str:
    return _keycloak_admin_required(settings.keycloak_admin_client_id, "keycloak_admin_client_id")


def _keycloak_admin_client_secret() -> str:
    return _keycloak_admin_required(settings.keycloak_admin_client_secret, "keycloak_admin_client_secret")


def _keycloak_admin_timeout_seconds() -> float:
    timeout_seconds = float(settings.keycloak_admin_timeout_seconds or 5.0)
    if timeout_seconds <= 0:
        raise HTTPException(status_code=500, detail="invalid_keycloak_admin_timeout_seconds")
    return timeout_seconds


def _keycloak_admin_org_attribute() -> str:
    return _keycloak_admin_required(settings.keycloak_admin_org_attribute, "keycloak_admin_org_attribute")


def _keycloak_admin_role_attribute() -> str:
    return _keycloak_admin_required(settings.keycloak_admin_role_attribute, "keycloak_admin_role_attribute")


@lru_cache(maxsize=1)
def _get_keycloak_directory_client() -> KeycloakDirectoryClient:
    return KeycloakDirectoryClient(
        base_url=_keycloak_admin_base_url(),
        realm=_keycloak_admin_realm(),
        client_id=_keycloak_admin_client_id(),
        client_secret=_keycloak_admin_client_secret(),
        timeout_seconds=_keycloak_admin_timeout_seconds(),
    )


def _resolve_persisted_user_id(cur, user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    try:
        candidate_user_id = str(UUID(str(user_id)))
    except (TypeError, ValueError):
        return None

    cur.execute("SELECT 1 FROM users WHERE id = %s", (candidate_user_id,))
    return candidate_user_id if cur.fetchone() else None


def _record_audit_log(
    cur,
    *,
    organization_id: str,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    metadata: dict,
) -> None:
    normalized_metadata = dict(metadata)
    persisted_user_id = _resolve_persisted_user_id(cur, user_id)
    persisted_resource_id: Optional[str] = None

    if user_id and not persisted_user_id:
        normalized_metadata.setdefault("external_user_id", str(user_id))

    if resource_id:
        try:
            persisted_resource_id = str(UUID(str(resource_id)))
        except (TypeError, ValueError):
            normalized_metadata.setdefault("resource_reference_id", str(resource_id))

    cur.execute(
        """
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (organization_id, persisted_user_id, action, resource_type, persisted_resource_id, json.dumps(normalized_metadata)),
    )


def _require_team_user_write_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_USER_WRITE_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_user_write_role_required")


def _require_team_user_create_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_USER_CREATE_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_user_create_role_required")


def _require_team_user_update_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_USER_UPDATE_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_user_update_role_required")


def _require_team_user_disable_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_USER_DISABLE_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_user_disable_role_required")


def _require_team_federated_identity_read_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_FEDERATED_IDENTITY_READ_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_federated_identity_read_role_required")


def _require_team_federated_identity_link_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_FEDERATED_IDENTITY_LINK_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_federated_identity_link_role_required")


def _require_team_federated_identity_unlink_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_FEDERATED_IDENTITY_UNLINK_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_federated_identity_unlink_role_required")


def _require_team_federated_directory_search_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_FEDERATED_DIRECTORY_SEARCH_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_federated_directory_search_role_required")


def _require_team_federated_directory_suggestion_role(auth: dict) -> None:
    if str(auth.get("role") or "").upper() not in TEAM_FEDERATED_DIRECTORY_SUGGESTION_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="team_federated_directory_suggestion_role_required")


def _serialize_team_user_row(row: dict) -> TeamUserRecord:
    created_at = row.get("created_at")
    updated_at = row.get("updated_at")
    last_identity_seen_at = row.get("last_identity_seen_at")

    return TeamUserRecord(
        member_id=str(row.get("id") or row.get("member_id")),
        name=str(row.get("display_name") or row.get("email") or ""),
        email=str(row.get("email") or ""),
        role=str(row.get("role") or "ANALYST"),
        status=str(row.get("status") or "active"),
        note=str(row.get("note") or ""),
        created_at=created_at.astimezone(timezone.utc).isoformat() if isinstance(created_at, datetime) else str(created_at or ""),
        updated_at=updated_at.astimezone(timezone.utc).isoformat() if isinstance(updated_at, datetime) else str(updated_at or ""),
        linked_identity_count=int(row.get("linked_identity_count") or 0),
        last_identity_seen_at=(
            last_identity_seen_at.astimezone(timezone.utc).isoformat()
            if isinstance(last_identity_seen_at, datetime)
            else (str(last_identity_seen_at) if last_identity_seen_at else None)
        ),
    )


def _serialize_external_identity_row(row: dict) -> TeamExternalIdentityRecord:
    created_at = row.get("created_at")
    last_seen_at = row.get("last_seen_at")

    return TeamExternalIdentityRecord(
        provider=str(row.get("provider") or ""),
        external_subject=str(row.get("external_subject") or ""),
        email_snapshot=str(row.get("email_snapshot")) if row.get("email_snapshot") else None,
        role_snapshot=str(row.get("role_snapshot")) if row.get("role_snapshot") else None,
        created_at=created_at.astimezone(timezone.utc).isoformat() if isinstance(created_at, datetime) else str(created_at or ""),
        last_seen_at=(
            last_seen_at.astimezone(timezone.utc).isoformat()
            if isinstance(last_seen_at, datetime)
            else (str(last_seen_at) if last_seen_at else None)
        ),
    )


def _fetch_team_user_with_identity_summary(cur, organization_id: str, member_id: str) -> Optional[dict]:
    cur.execute(
        """
        SELECT
          u.id,
          u.display_name,
          u.email,
          u.role,
          u.status,
          u.note,
          u.created_at,
          u.updated_at,
          COUNT(ei.id)::int AS linked_identity_count,
          MAX(ei.last_seen_at) AS last_identity_seen_at
        FROM users u
        LEFT JOIN external_identities ei
          ON ei.user_id = u.id
         AND ei.organization_id = u.organization_id
        WHERE u.organization_id = %s
          AND u.id = %s
        GROUP BY u.id, u.display_name, u.email, u.role, u.status, u.note, u.created_at, u.updated_at
        """,
        (organization_id, member_id),
    )
    return cur.fetchone()


def _fetch_team_user_external_identities(cur, organization_id: str, member_id: str) -> list[dict]:
    cur.execute(
        """
        SELECT
          provider,
          external_subject,
          email_snapshot,
          role_snapshot,
          created_at,
          last_seen_at
        FROM external_identities
        WHERE organization_id = %s
          AND user_id = %s
        ORDER BY last_seen_at DESC NULLS LAST, created_at DESC, external_subject ASC
        """,
        (organization_id, member_id),
    )
    return cur.fetchall() or []


def _fetch_team_user_by_email(cur, organization_id: str, email: str) -> Optional[dict]:
    cur.execute(
        """
        SELECT id, display_name, email, role, status
        FROM users
        WHERE organization_id = %s
          AND lower(email) = %s
        LIMIT 1
        """,
        (organization_id, email.strip().lower()),
    )
    return cur.fetchone()


def _fetch_external_identity_link_summary(cur, organization_id: str, provider: str, external_subject: str) -> Optional[dict]:
    cur.execute(
        """
        SELECT ei.user_id, u.email
        FROM external_identities ei
        LEFT JOIN users u
          ON u.id = ei.user_id
         AND u.organization_id = ei.organization_id
        WHERE ei.organization_id = %s
          AND ei.provider = %s
          AND ei.external_subject = %s
        LIMIT 1
        """,
        (organization_id, provider, external_subject),
    )
    return cur.fetchone()


def _normalize_federated_directory_candidate(raw_candidate: dict, provider: str) -> dict:
    raw_attributes = raw_candidate.get("attributes")
    attributes: dict[str, Any] = raw_attributes if isinstance(raw_attributes, dict) else {}
    org_attribute_name = _keycloak_admin_org_attribute()
    role_attribute_name = _keycloak_admin_role_attribute()
    organization_id = _normalize_keycloak_attribute_value(
        attributes.get(org_attribute_name) or attributes.get("org") or attributes.get("organization_id")
    )
    raw_role = _normalize_keycloak_attribute_value(
        attributes.get(role_attribute_name) or attributes.get("otk_role") or raw_candidate.get(role_attribute_name)
    )
    if not raw_role:
        raw_role = _normalize_keycloak_attribute_value(raw_candidate.get("realmRoles"))
    role_snapshot = _canonicalize_role(raw_role) if raw_role else None
    email = _normalize_optional_snapshot(str(raw_candidate.get("email") or "").lower())

    return {
        "provider": provider,
        "external_subject": _normalize_external_subject(str(raw_candidate.get("id") or "")),
        "email": email,
        "username": _normalize_optional_snapshot(raw_candidate.get("username")),
        "organization_id": organization_id,
        "role_snapshot": role_snapshot,
        "enabled": bool(raw_candidate.get("enabled", True)),
    }


def _resolve_federated_directory_role_validation_status(
    candidate_role_snapshot: Optional[str],
    *,
    expected_role: Optional[str] = None,
) -> tuple[Optional[str], str]:
    normalized_role_snapshot = _normalize_optional_snapshot(candidate_role_snapshot)
    if not normalized_role_snapshot:
        return None, "missing"

    canonical_role = _canonicalize_role(normalized_role_snapshot)
    if canonical_role not in TEAM_USER_ALLOWED_ROLES:
        return canonical_role, "unknown"
    if expected_role and canonical_role != _canonicalize_role(expected_role):
        return canonical_role, "mismatch"
    return canonical_role, "valid"


def _evaluate_federated_directory_suggestion(
    *,
    tenant_org_id: str,
    member_id: str,
    member_email: str,
    member_role: str,
    candidate_org_id: Optional[str],
    candidate_email: Optional[str],
    candidate_role_snapshot: Optional[str],
    linked_user_id: Optional[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    normalized_candidate_email = _normalize_optional_snapshot(str(candidate_email or "").lower())
    normalized_member_email = _normalize_team_user_email(member_email)
    normalized_role_snapshot, role_validation_status = _resolve_federated_directory_role_validation_status(
        candidate_role_snapshot,
        expected_role=member_role,
    )
    org_match = bool(candidate_org_id) and candidate_org_id == tenant_org_id
    email_match = bool(normalized_candidate_email) and normalized_candidate_email == normalized_member_email

    if not candidate_org_id:
        warnings.append("candidate_org_missing")
    elif not org_match:
        warnings.append("candidate_org_mismatch")

    if not normalized_candidate_email:
        warnings.append("candidate_email_missing")
    elif not email_match:
        warnings.append("candidate_email_mismatch")

    if role_validation_status == "missing":
        warnings.append("candidate_role_missing")
    elif role_validation_status == "unknown":
        warnings.append("candidate_role_unknown")
    elif role_validation_status == "mismatch":
        warnings.append("candidate_role_mismatch")

    if linked_user_id and linked_user_id != member_id:
        warnings.append("candidate_already_linked")
        return {
            "can_link": False,
            "match_reason": "already_linked",
            "org_match": org_match,
            "email_match": email_match,
            "role_snapshot": normalized_role_snapshot,
            "role_validation_status": role_validation_status,
            "warnings": warnings,
        }

    if not org_match:
        match_reason = "org_mismatch"
        can_link = False
    elif not email_match:
        match_reason = "email_mismatch"
        can_link = False
    elif role_validation_status in {"missing", "unknown", "mismatch"}:
        match_reason = f"role_{role_validation_status}"
        can_link = False
    else:
        match_reason = "ready"
        can_link = True

    if linked_user_id == member_id:
        warnings.append("candidate_already_linked_to_member")

    return {
        "can_link": can_link,
        "match_reason": match_reason,
        "org_match": org_match,
        "email_match": email_match,
        "role_snapshot": normalized_role_snapshot,
        "role_validation_status": role_validation_status,
        "warnings": warnings,
    }


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


@app.get("/validate/block-check")
async def validate_block_check(
    request: Request,
    response: Response,
) -> dict:
    """
    Endpoint de pre-screening Stage 1 — blocklist Redis.

    Chamado como ForwardAuth pelo Traefik para rotas de escrita
    (transações, investigações, relatórios) ANTES da validação de JWT.

    Latência alvo: < 50ms (Redis SISMEMBER O(1)).

    Retorna 200 se o endereço NÃO está bloqueado.
    Retorna 451 (Legal Reason) se está na blocklist confirmada.
    O Traefik interpreta qualquer não-2xx como bloqueio e retorna 403 ao client.
    """
    from auth_service.pre_screening import pre_screen_blocklist

    redis_client: aioredis.Redis = request.app.state.redis
    blocked_response = await pre_screen_blocklist(request, redis_client)

    if blocked_response is not None:
        # Copia headers do response de bloqueio para o response atual
        for key, value in blocked_response.headers.items():
            response.headers[key] = value
        response.status_code = 451
        return {"status": "blocked", "stage": "gateway_pre_screening"}

    return {"status": "pass", "stage": "gateway_pre_screening"}


@app.get("/validate")
async def validate(
    request: Request,
    response: Response,
    auth: dict = Depends(_require_auth),
) -> dict:
    """
    Validação JWT/OIDC com pre-screening de blocklist integrado.
    Stage 1 (Redis) é executado antes de qualquer processamento de auth.
    """
    # Stage 1: Pre-screening blocklist antes de validar JWT
    from auth_service.pre_screening import pre_screen_blocklist

    redis_client: aioredis.Redis = request.app.state.redis
    blocked_response = await pre_screen_blocklist(request, redis_client)

    if blocked_response is not None:
        for key, value in blocked_response.headers.items():
            response.headers[key] = value
        response.status_code = 451
        return {"status": "blocked", "stage": "gateway_pre_screening"}

    # Stage 2: Validação JWT/OIDC normal
    response.headers["X-Org-Id"] = auth["org_id"]
    response.headers["X-User-Id"] = auth["user_id"]
    if auth.get("linked_user_id"):
        response.headers["X-Linked-User-Id"] = auth["linked_user_id"]
    response.headers["X-Plan"] = auth["plan"]
    response.headers["X-Role"] = auth["role"]
    response.headers["X-Auth-Method"] = auth["auth_method"]
    response.headers["X-MFA-Mode"] = auth["mfa_mode"]
    response.headers["X-MFA-Provider-Homologated"] = (
        "true" if auth.get("mfa_provider_homologated") else "false"
    )
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


@app.get("/api/v1/team/users", response_model=TeamUserListResponse)
async def list_team_users(auth: dict = Depends(_require_auth), pool: ConnectionPool = Depends(get_pool)) -> TeamUserListResponse:
    organization_id = str(auth["org_id"])
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  u.id,
                  u.display_name,
                  u.email,
                  u.role,
                  u.status,
                  u.note,
                  u.created_at,
                  u.updated_at,
                  COUNT(ei.id)::int AS linked_identity_count,
                  MAX(ei.last_seen_at) AS last_identity_seen_at
                FROM users u
                LEFT JOIN external_identities ei
                  ON ei.user_id = u.id
                 AND ei.organization_id = u.organization_id
                WHERE u.organization_id = %s
                GROUP BY u.id, u.display_name, u.email, u.role, u.status, u.note, u.created_at, u.updated_at
                ORDER BY u.updated_at DESC, u.created_at DESC, u.id DESC
                """,
                (organization_id,),
            )
            rows = cur.fetchall() or []

    return TeamUserListResponse(data=[_serialize_team_user_row(row) for row in rows])


@app.post("/api/v1/team/users", response_model=TeamUserRecord)
async def create_team_user(
    body: CreateTeamUserRequest,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> TeamUserRecord:
    _require_team_user_create_role(auth)
    organization_id = str(auth["org_id"])
    normalized_email = _normalize_team_user_email(body.email)
    normalized_role = _normalize_team_user_role(body.role)
    normalized_status = _normalize_team_user_status(body.status)
    normalized_note = _normalize_team_user_note(body.note)
    normalized_name = _normalize_team_user_name(body.name, fallback_email=normalized_email)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM users
                WHERE organization_id = %s
                  AND lower(email) = %s
                """,
                (organization_id, normalized_email),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="team_user_email_already_exists")

            cur.execute(
                """
                INSERT INTO users (
                  organization_id,
                  email,
                  password_hash,
                  display_name,
                  role,
                  status,
                  note,
                  updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING
                  id,
                  display_name,
                  email,
                  role,
                  status,
                  note,
                  created_at,
                  updated_at
                """,
                (
                    organization_id,
                    normalized_email,
                    "managed-by-app",
                    normalized_name,
                    normalized_role,
                    normalized_status,
                    normalized_note,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=500, detail="team_user_create_failed")
    return _serialize_team_user_row(row)


@app.patch("/api/v1/team/users/{member_id}", response_model=TeamUserRecord)
async def update_team_user(
    member_id: str,
    body: UpdateTeamUserRequest,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> TeamUserRecord:
    if body.status is not None and str(body.status).strip().lower() == "disabled":
        _require_team_user_disable_role(auth)
    else:
        _require_team_user_update_role(auth)
    organization_id = str(auth["org_id"])
    try:
        normalized_member_id = str(UUID(member_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_team_user_id") from None

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, display_name, email, role, status, note, created_at, updated_at
                FROM users
                WHERE organization_id = %s
                  AND id = %s
                """,
                (organization_id, normalized_member_id),
            )
            current_row = cur.fetchone()
            if not current_row:
                raise HTTPException(status_code=404, detail="team_user_not_found")

            next_email = (
                _normalize_team_user_email(body.email)
                if body.email is not None
                else str(current_row.get("email") or "")
            )
            if next_email != str(current_row.get("email") or ""):
                cur.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE organization_id = %s
                      AND lower(email) = %s
                      AND id <> %s
                    """,
                    (organization_id, next_email, normalized_member_id),
                )
                if cur.fetchone():
                    raise HTTPException(status_code=409, detail="team_user_email_already_exists")

            next_role = _normalize_team_user_role(body.role if body.role is not None else current_row.get("role"))
            next_status = _normalize_team_user_status(body.status if body.status is not None else current_row.get("status"))
            next_note = _normalize_team_user_note(body.note if body.note is not None else current_row.get("note"))
            next_name = _normalize_team_user_name(
                body.name if body.name is not None else current_row.get("display_name"),
                fallback_email=next_email,
            )

            cur.execute(
                """
                UPDATE users
                SET
                  email = %s,
                  display_name = %s,
                  role = %s,
                  status = %s,
                  note = %s,
                  updated_at = NOW()
                WHERE organization_id = %s
                  AND id = %s
                RETURNING
                  id,
                  display_name,
                  email,
                  role,
                  status,
                  note,
                  created_at,
                  updated_at
                """,
                (
                    next_email,
                    next_name,
                    next_role,
                    next_status,
                    next_note,
                    organization_id,
                    normalized_member_id,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=500, detail="team_user_update_failed")
    return _serialize_team_user_row(row)


@app.post("/api/v1/team/users/{member_id}/external-identities", response_model=TeamUserRecord)
async def link_team_user_external_identity(
    member_id: str,
    body: LinkExternalIdentityRequest,
    request: Request,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> TeamUserRecord:
    _require_team_federated_identity_link_role(auth)
    organization_id = str(auth["org_id"])
    try:
        normalized_member_id = str(UUID(member_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_team_user_id") from None

    normalized_provider = _normalize_identity_provider(body.provider)
    normalized_external_subject = _normalize_external_subject(body.external_subject)
    normalized_email_snapshot = _normalize_optional_snapshot(body.email_snapshot)
    normalized_role_snapshot = (
        _canonicalize_role(body.role_snapshot)
        if _normalize_optional_snapshot(body.role_snapshot)
        else None
    )

    with pool.connection() as conn:
        with conn.cursor() as cur:
            current_row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
            if not current_row:
                raise HTTPException(status_code=404, detail="team_user_not_found")

            cur.execute(
                """
                SELECT user_id
                FROM external_identities
                WHERE organization_id = %s
                  AND provider = %s
                  AND external_subject = %s
                """,
                (organization_id, normalized_provider, normalized_external_subject),
            )
            existing_identity = cur.fetchone()
            existing_user_id = existing_identity.get("user_id") if existing_identity else None
            if existing_user_id and str(existing_user_id) != normalized_member_id:
                raise HTTPException(status_code=409, detail="team_external_identity_already_linked")

            cur.execute(
                """
                INSERT INTO external_identities (
                  organization_id,
                  provider,
                  external_subject,
                  user_id,
                  email_snapshot,
                  role_snapshot,
                  last_seen_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NULL)
                ON CONFLICT (provider, external_subject, organization_id)
                DO UPDATE SET
                  user_id = EXCLUDED.user_id,
                  email_snapshot = COALESCE(EXCLUDED.email_snapshot, external_identities.email_snapshot),
                  role_snapshot = COALESCE(EXCLUDED.role_snapshot, external_identities.role_snapshot)
                """,
                (
                    organization_id,
                    normalized_provider,
                    normalized_external_subject,
                    normalized_member_id,
                    normalized_email_snapshot,
                    normalized_role_snapshot,
                ),
            )

            _record_audit_log(
                cur,
                organization_id=organization_id,
                user_id=str(auth.get("linked_user_id") or auth.get("user_id") or ""),
                action="team_external_identity_linked",
                resource_type="team_user",
                resource_id=normalized_member_id,
                metadata={
                    "request_id": request.headers.get("x-request-id"),
                    "actor_user_id": str(auth.get("user_id") or ""),
                    "linked_user_id": str(auth.get("linked_user_id") or ""),
                    "member_id": normalized_member_id,
                    "provider": normalized_provider,
                    "external_subject": normalized_external_subject,
                    "email_snapshot": normalized_email_snapshot,
                    "role_snapshot": normalized_role_snapshot,
                    "auth_method": str(auth.get("auth_method") or ""),
                    "tenant_role": str(auth.get("role") or ""),
                },
            )

            row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
        conn.commit()

    if not row:
        raise HTTPException(status_code=500, detail="team_external_identity_link_failed")
    logger.info(
        "team_external_identity_linked org_id=%s actor_user_id=%s linked_user_id=%s member_id=%s provider=%s external_subject=%s",
        organization_id,
        str(auth.get("user_id") or ""),
        str(auth.get("linked_user_id") or ""),
        normalized_member_id,
        normalized_provider,
        normalized_external_subject,
    )
    return _serialize_team_user_row(row)


@app.get("/api/v1/team/users/{member_id}/external-identities", response_model=TeamExternalIdentityListResponse)
async def list_team_user_external_identities(
    member_id: str,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> TeamExternalIdentityListResponse:
    _require_team_federated_identity_read_role(auth)
    organization_id = str(auth["org_id"])
    try:
        normalized_member_id = str(UUID(member_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_team_user_id") from None

    with pool.connection() as conn:
        with conn.cursor() as cur:
            current_row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
            if not current_row:
                raise HTTPException(status_code=404, detail="team_user_not_found")
            rows = _fetch_team_user_external_identities(cur, organization_id, normalized_member_id)

    return TeamExternalIdentityListResponse(data=[_serialize_external_identity_row(row) for row in rows])


@app.delete("/api/v1/team/users/{member_id}/external-identities", response_model=TeamUserRecord)
async def unlink_team_user_external_identity(
    member_id: str,
    body: UnlinkExternalIdentityRequest,
    request: Request,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> TeamUserRecord:
    _require_team_federated_identity_unlink_role(auth)
    organization_id = str(auth["org_id"])
    try:
        normalized_member_id = str(UUID(member_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_team_user_id") from None

    normalized_provider = _normalize_identity_provider(body.provider)
    normalized_external_subject = _normalize_external_subject(body.external_subject)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            current_row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
            if not current_row:
                raise HTTPException(status_code=404, detail="team_user_not_found")

            cur.execute(
                """
                DELETE FROM external_identities
                WHERE organization_id = %s
                  AND user_id = %s
                  AND provider = %s
                  AND external_subject = %s
                RETURNING provider, external_subject
                """,
                (organization_id, normalized_member_id, normalized_provider, normalized_external_subject),
            )
            deleted_row = cur.fetchone()
            if not deleted_row:
                raise HTTPException(status_code=404, detail="team_external_identity_not_found")

            _record_audit_log(
                cur,
                organization_id=organization_id,
                user_id=str(auth.get("linked_user_id") or auth.get("user_id") or ""),
                action="team_external_identity_unlinked",
                resource_type="team_user",
                resource_id=normalized_member_id,
                metadata={
                    "request_id": request.headers.get("x-request-id"),
                    "actor_user_id": str(auth.get("user_id") or ""),
                    "linked_user_id": str(auth.get("linked_user_id") or ""),
                    "member_id": normalized_member_id,
                    "provider": normalized_provider,
                    "external_subject": normalized_external_subject,
                    "auth_method": str(auth.get("auth_method") or ""),
                    "tenant_role": str(auth.get("role") or ""),
                },
            )

            row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
        conn.commit()

    if not row:
        raise HTTPException(status_code=500, detail="team_external_identity_unlink_failed")
    logger.info(
        "team_external_identity_unlinked org_id=%s actor_user_id=%s linked_user_id=%s member_id=%s provider=%s external_subject=%s",
        organization_id,
        str(auth.get("user_id") or ""),
        str(auth.get("linked_user_id") or ""),
        normalized_member_id,
        normalized_provider,
        normalized_external_subject,
    )
    return _serialize_team_user_row(row)


@app.get("/api/v1/team/federated-directory/users", response_model=FederatedDirectoryUserListResponse)
async def list_federated_directory_users(
    request: Request,
    query: str,
    limit: int = 20,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> FederatedDirectoryUserListResponse:
    _require_team_federated_directory_search_role(auth)
    organization_id = str(auth["org_id"])
    normalized_query = _normalize_federated_directory_query(query)
    normalized_limit = _normalize_federated_directory_limit(limit)
    provider = "keycloak"
    client = _get_keycloak_directory_client()
    raw_candidates = client.search_users(query=normalized_query, limit=normalized_limit)
    results: list[FederatedDirectoryUserRecord] = []

    with pool.connection() as conn:
        with conn.cursor() as cur:
            for raw_candidate in raw_candidates:
                candidate = _normalize_federated_directory_candidate(raw_candidate, provider)
                link_row = _fetch_external_identity_link_summary(
                    cur,
                    organization_id,
                    provider,
                    candidate["external_subject"],
                )
                linked_user_id = str(link_row.get("user_id")) if link_row and link_row.get("user_id") else None
                linked_user_email = str(link_row.get("email")) if link_row and link_row.get("email") else None
                local_email_user = (
                    _fetch_team_user_by_email(cur, organization_id, candidate["email"])
                    if candidate.get("email") and candidate.get("organization_id") == organization_id
                    else None
                )
                _, role_validation_status = _resolve_federated_directory_role_validation_status(candidate.get("role_snapshot"))
                warnings: list[str] = []

                if not candidate.get("organization_id"):
                    warnings.append("candidate_org_missing")
                elif candidate["organization_id"] != organization_id:
                    warnings.append("candidate_org_mismatch")

                if not candidate.get("email"):
                    warnings.append("candidate_email_missing")

                if role_validation_status == "missing":
                    warnings.append("candidate_role_missing")
                elif role_validation_status == "unknown":
                    warnings.append("candidate_role_unknown")

                if linked_user_id:
                    match_status = "linked"
                elif local_email_user:
                    match_status = "suggested"
                elif candidate.get("organization_id") == organization_id:
                    match_status = "org_match_only"
                else:
                    match_status = "org_mismatch"

                results.append(
                    FederatedDirectoryUserRecord(
                        provider=provider,
                        external_subject=candidate["external_subject"],
                        email=candidate.get("email"),
                        username=candidate.get("username"),
                        organization_id=candidate.get("organization_id"),
                        role_snapshot=candidate.get("role_snapshot"),
                        enabled=bool(candidate.get("enabled")),
                        match_status=match_status,
                        linked_user_id=linked_user_id,
                        linked_user_email=linked_user_email,
                        role_validation_status=role_validation_status,
                        warnings=warnings,
                    )
                )

            _record_audit_log(
                cur,
                organization_id=organization_id,
                user_id=str(auth.get("linked_user_id") or auth.get("user_id") or ""),
                action="team_federated_directory_searched",
                resource_type="team_federated_directory",
                resource_id=None,
                metadata={
                    "request_id": request.headers.get("x-request-id"),
                    "actor_user_id": str(auth.get("user_id") or ""),
                    "linked_user_id": str(auth.get("linked_user_id") or ""),
                    "query": normalized_query,
                    "provider": provider,
                    "result_count": len(results),
                    "auth_method": str(auth.get("auth_method") or ""),
                    "tenant_role": str(auth.get("role") or ""),
                },
            )
        conn.commit()

    return FederatedDirectoryUserListResponse(data=results)


@app.post(
    "/api/v1/team/federated-directory/suggestions",
    response_model=ValidateFederatedDirectorySuggestionResponse,
)
async def validate_federated_directory_suggestion(
    body: ValidateFederatedDirectorySuggestionRequest,
    request: Request,
    auth: dict = Depends(_require_auth),
    pool: ConnectionPool = Depends(get_pool),
) -> ValidateFederatedDirectorySuggestionResponse:
    _require_team_federated_directory_suggestion_role(auth)
    organization_id = str(auth["org_id"])
    normalized_provider = _normalize_identity_provider(body.provider)
    if normalized_provider != "keycloak":
        raise HTTPException(status_code=422, detail="team_external_identity_provider_invalid")

    try:
        normalized_member_id = str(UUID(body.member_id))
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid_team_user_id") from None

    normalized_external_subject = _normalize_external_subject(body.external_subject)
    client = _get_keycloak_directory_client()
    raw_candidate = client.get_user(external_subject=normalized_external_subject)
    candidate = _normalize_federated_directory_candidate(raw_candidate, normalized_provider)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            member_row = _fetch_team_user_with_identity_summary(cur, organization_id, normalized_member_id)
            if not member_row:
                raise HTTPException(status_code=404, detail="team_user_not_found")

            link_row = _fetch_external_identity_link_summary(
                cur,
                organization_id,
                normalized_provider,
                candidate["external_subject"],
            )
            linked_user_id = str(link_row.get("user_id")) if link_row and link_row.get("user_id") else None
            linked_user_email = str(link_row.get("email")) if link_row and link_row.get("email") else None
            evaluation = _evaluate_federated_directory_suggestion(
                tenant_org_id=organization_id,
                member_id=normalized_member_id,
                member_email=str(member_row.get("email") or ""),
                member_role=str(member_row.get("role") or "ANALYST"),
                candidate_org_id=candidate.get("organization_id"),
                candidate_email=candidate.get("email"),
                candidate_role_snapshot=candidate.get("role_snapshot"),
                linked_user_id=linked_user_id,
            )

            _record_audit_log(
                cur,
                organization_id=organization_id,
                user_id=str(auth.get("linked_user_id") or auth.get("user_id") or ""),
                action="team_federated_directory_suggestion_validated",
                resource_type="team_user",
                resource_id=normalized_member_id,
                metadata={
                    "request_id": request.headers.get("x-request-id"),
                    "actor_user_id": str(auth.get("user_id") or ""),
                    "linked_user_id": str(auth.get("linked_user_id") or ""),
                    "member_id": normalized_member_id,
                    "provider": normalized_provider,
                    "external_subject": candidate["external_subject"],
                    "candidate_email": candidate.get("email"),
                    "candidate_org": candidate.get("organization_id"),
                    "role_snapshot": evaluation["role_snapshot"],
                    "role_validation_status": evaluation["role_validation_status"],
                    "match_reason": evaluation["match_reason"],
                    "warnings": evaluation["warnings"],
                    "auth_method": str(auth.get("auth_method") or ""),
                    "tenant_role": str(auth.get("role") or ""),
                },
            )
        conn.commit()

    return ValidateFederatedDirectorySuggestionResponse(
        can_link=bool(evaluation["can_link"]),
        match_reason=str(evaluation["match_reason"]),
        org_match=bool(evaluation["org_match"]),
        email_match=bool(evaluation["email_match"]),
        provider=normalized_provider,
        external_subject=candidate["external_subject"],
        candidate_email=candidate.get("email"),
        candidate_username=candidate.get("username"),
        candidate_org=candidate.get("organization_id"),
        role_snapshot=evaluation["role_snapshot"],
        role_validation_status=str(evaluation["role_validation_status"]),
        linked_user_id=linked_user_id,
        linked_user_email=linked_user_email,
        warnings=list(evaluation["warnings"]),
    )
