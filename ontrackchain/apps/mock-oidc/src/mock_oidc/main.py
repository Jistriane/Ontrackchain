from __future__ import annotations

import base64
import hashlib
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
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
    allowed = {
        "ADMIN",
        "AUDITOR",
        "ANALYST",
        "VIEWER",
        "TESTER",
        "COMPLIANCE_OFFICER",
        "LEGAL_REVIEWER",
        "OTK_ANALYST",
        "OTK_VIEWER",
        "OTK_TESTER",
    }
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="invalid_role")
    return normalized


@dataclass
class CredentialRecord:
    password: str
    role: str
    org: Optional[str]
    plan: str
    subject: str


_CREDENTIALS: dict[str, CredentialRecord] = {}


def _ensure_default_credentials() -> None:
    defaults = [
        ("kmd@ontrackchain.com", "KmdPass123!", "ADMIN", "00000000-0000-0000-0000-000000000001", "enterprise"),
        ("jibso@ontrackchain.com", "JIBSOPass123!", "ADMIN", "00000000-0000-0000-0000-000000000001", "enterprise"),
        ("system@ontrackchain.com", "SystemPass123!", "ADMIN", "00000000-0000-0000-0000-000000000001", "enterprise"),
        ("auditor@ontrackchain.com", "AuditorPass123!", "AUDITOR", "00000000-0000-0000-0000-000000000001", "enterprise"),
        ("analyst@ontrackchain.com", "AnalystPass123!", "ANALYST", "00000000-0000-0000-0000-000000000001", "professional"),
        ("viewer@ontrackchain.com", "ViewerPass123!", "VIEWER", "00000000-0000-0000-0000-000000000001", "professional"),
        ("demo@ontrackchain.local", "DemoPass123!", "ADMIN", "00000000-0000-0000-0000-000000000001", "enterprise"),
        ("sem-org@ontrackchain.com", "SemOrgPass123!", "VIEWER", None, "free"),
    ]
    for email, password, role, org, plan in defaults:
        if email not in _CREDENTIALS:
            _CREDENTIALS[email] = CredentialRecord(
                password=password,
                role=_normalize_role(role),
                org=org,
                plan=plan,
                subject=str(uuid.uuid4()),
            )


def _issue_access_token(
    *,
    issuer: str,
    audience: str,
    subject: str,
    org: Optional[str],
    plan: str,
    role: str,
    private_key,
    kid: str,
) -> str:
    now = _now_ts()
    payload: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + settings.token_ttl_seconds,
        "sub": subject,
        "plan": plan,
        "otk_role": role,
    }
    if org:
        payload["org"] = org
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
    org: Optional[str]
    plan: str
    subject: str
    created_at: int
    login_hint: Optional[str] = None


class MockTokenRequest(BaseModel):
    role: str
    org: Optional[str] = None
    plan: str = "professional"
    sub: Optional[str] = None


class LoginCredentials(BaseModel):
    username: str
    password: str
    code: Optional[str] = None
    state: Optional[str] = None
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


app = FastAPI(title="Ontrackchain Mock OIDC", version="0.1.0")

_private_key, _public_key = _rsa_keypair()
_kid = _b64url(os.urandom(12))
_jwks = _jwks_from_public_key(_public_key, kid=_kid)

_auth_codes: dict[str, AuthCodeRecord] = {}
_pending_authorizations: dict[str, AuthCodeRecord] = {}


def _purge_expired_codes() -> None:
    now = _now_ts()
    expired = [k for k, v in _auth_codes.items() if now - v.created_at > settings.code_ttl_seconds]
    for k in expired:
        _auth_codes.pop(k, None)
    pending_expired = [k for k, v in _pending_authorizations.items() if now - v.created_at > settings.code_ttl_seconds]
    for k in pending_expired:
        _pending_authorizations.pop(k, None)
    _ensure_default_credentials()


@app.on_event("startup")
async def _on_startup() -> None:
    _ensure_default_credentials()


def _render_login_html(
    *,
    error: Optional[str] = None,
    code: Optional[str] = None,
    state: Optional[str] = None,
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    login_hint: Optional[str] = None,
) -> str:
    error_html = ""
    if error == "invalid_credentials":
        error_html = '<div class="error">Credenciais inválidas. Tente novamente.</div>'
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Mock OIDC Login</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:#f5f6f8; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }}
    .card {{ background:#fff; padding: 32px 28px; border-radius: 12px; box-shadow: 0 6px 24px rgba(0,0,0,0.08); width: 360px; }}
    h1 {{ margin: 0 0 16px; font-size: 20px; }}
    label {{ display:block; font-size: 13px; color:#334155; margin: 12px 0 6px; }}
    input {{ width:100%; padding:10px 12px; border:1px solid #cbd5e1; border-radius:8px; box-sizing:border-box; font-size:14px; }}
    button {{ margin-top: 20px; width:100%; padding: 11px 12px; background:#2563eb; color:#fff; border:0; border-radius:8px; cursor:pointer; font-size:15px; font-weight:600; }}
    .error {{ margin-top:12px; padding:10px 12px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; color:#991b1b; font-size:13px; }}
    .hint {{ color:#64748b; font-size:12px; margin-top:12px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Mock OIDC — Sign in</h1>
    <form method="POST" action="/login">
      <input type="hidden" name="code" value="{code or ''}" />
      <input type="hidden" name="state" value="{state or ''}" />
      <input type="hidden" name="client_id" value="{client_id or ''}" />
      <input type="hidden" name="redirect_uri" value="{redirect_uri or ''}" />
      <input type="hidden" name="code_challenge" value="{code_challenge or ''}" />
      <input type="hidden" name="code_challenge_method" value="{code_challenge_method or ''}" />
      <label for="username">Usuário (e-mail)</label>
      <input id="username" name="username" type="email" autocomplete="username" value="{login_hint or ''}" required />
      <label for="password">Senha</label>
      <input id="password" name="password" type="password" autocomplete="current-password" required />
      <button id="kc-login" type="submit">Entrar</button>
      {error_html}
    </form>
    <div class="hint">Mock OIDC local do Ontrackchain para testes E2E.</div>
  </div>
</body>
</html>
"""


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
    role: Optional[str] = Query(None),
    org: Optional[str] = Query(None),
    plan: str = Query("professional"),
    login_hint: Optional[str] = Query(None),
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

    credential: Optional[CredentialRecord] = None
    if login_hint and login_hint in _CREDENTIALS:
        credential = _CREDENTIALS[login_hint]

    effective_role = _normalize_role(role) if role else (credential.role if credential else "ANALYST")
    effective_org: Optional[str] = org if org else (credential.org if credential else "00000000-0000-0000-0000-000000000001")
    effective_plan = plan or (credential.plan if credential else "professional")
    subject = credential.subject if credential else str(uuid.uuid4())
    pending_id = _b64url(os.urandom(12))

    _pending_authorizations[pending_id] = AuthCodeRecord(
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        redirect_uri=redirect_uri,
        role=effective_role,
        org=effective_org,
        plan=effective_plan,
        subject=subject,
        created_at=_now_ts(),
        login_hint=login_hint,
    )

    from fastapi.responses import HTMLResponse

    return HTMLResponse(
        _render_login_html(
            code=pending_id,
            state=state,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            login_hint=login_hint,
        ),
        status_code=200,
    )


@app.get("/login")
async def login_form(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    redirect_uri: Optional[str] = Query(None),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query(None),
    login_hint: Optional[str] = Query(None),
) -> Any:
    from fastapi.responses import HTMLResponse

    return HTMLResponse(
        _render_login_html(
            code=code,
            state=state,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            login_hint=login_hint,
        ),
        status_code=200,
    )


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    code: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
) -> Any:
    from fastapi.responses import HTMLResponse, RedirectResponse

    normalized_email = (username or "").strip().lower()
    credential = _CREDENTIALS.get(normalized_email)
    if not credential or credential.password != password:
        return HTMLResponse(
            _render_login_html(
                error="invalid_credentials",
                code=code,
                state=state,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method,
                login_hint=normalized_email,
            ),
            status_code=401,
        )

    pending: Optional[AuthCodeRecord] = None
    if code and code in _pending_authorizations:
        pending = _pending_authorizations.pop(code)

    final_redirect_uri = redirect_uri or (pending.redirect_uri if pending else None)
    if not final_redirect_uri:
        raise HTTPException(status_code=400, detail="missing_redirect_uri")
    if state is None:
        raise HTTPException(status_code=400, detail="missing_state")

    final_code = _b64url(os.urandom(18))
    _auth_codes[final_code] = AuthCodeRecord(
        code_challenge=(code_challenge if code_challenge is not None else (pending.code_challenge if pending else None)),
        code_challenge_method=(
            code_challenge_method if code_challenge_method is not None else (pending.code_challenge_method if pending else None)
        ),
        redirect_uri=final_redirect_uri,
        role=_normalize_role(credential.role),
        org=credential.org,
        plan=credential.plan,
        subject=credential.subject,
        created_at=_now_ts(),
        login_hint=normalized_email,
    )

    separator = "&" if "?" in final_redirect_uri else "?"
    return RedirectResponse(f"{final_redirect_uri}{separator}code={final_code}&state={state}", status_code=302)


@app.post("/oauth/token")
async def token(
    grant_type: str = Form("authorization_code"),
    client_id: str = Form(""),
    code: str = Form(""),
    redirect_uri: str = Form(""),
    code_verifier: str = Form(""),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    scope: str = Form("openid profile email"),
) -> dict[str, Any]:
    _purge_expired_codes()
    if not client_id or client_id != settings.client_id:
        raise HTTPException(status_code=400, detail="invalid_client_id")

    if grant_type == "password":
        normalized_email = (username or "").strip().lower()
        credential = _CREDENTIALS.get(normalized_email)
        if not credential or credential.password != password:
            raise HTTPException(status_code=400, detail="invalid_grant")
        if "openid" not in (scope or ""):
            raise HTTPException(status_code=400, detail="missing_openid_scope")
        access_token = _issue_access_token(
            issuer=settings.issuer_url.rstrip("/"),
            audience=settings.audience,
            subject=credential.subject,
            org=credential.org,
            plan=credential.plan,
            role=credential.role,
            private_key=_private_key,
            kid=_kid,
        )
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.token_ttl_seconds,
            "scope": scope or "openid profile email",
        }

    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
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


# ==========================================================================
# OBSERVABILIDADE M16b: /healthz (liveness) + /metrics (Prometheus)
# Gate CI Obrigatório: observability-endpoints-gate bloqueia merge se ausente
# Strategy: Try prometheus_fastapi_instrumentator primeiro, fallback inline
# ==========================================================================
@app.get("/healthz", tags=["Observabilidade"], summary="Liveness Probe Kubernetes / SRE")
async def healthz_liveness_probe():
    return {
        "status": "ok",
        "service": "mock-oidc",
        "version": "1.5.0",
        "liveness": "healthy",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

try:
    from prometheus_fastapi_instrumentator import Instrumentator as _PromInstrumentator
    _PromInstrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
except Exception:  # noqa: BLE001 - fallback inline sempre funciona, sem dependencia
    from fastapi.responses import PlainTextResponse as _FallbackPlainText

    _FALLBACK_METRICS_BASE = """# HELP fastapi_info Info about the running FastAPI service.
# TYPE fastapi_info gauge
fastapi_info{service="mock-oidc",version="1.5.0"} 1.0
# HELP http_requests_total Total HTTP requests (fallback inline).
# TYPE http_requests_total counter
http_requests_total{service="mock-oidc",endpoint="/healthz",method="GET",status_code="200"} 0
# HELP up Liveness probe (1 = UP).
# TYPE up gauge
up{service="mock-oidc"} 1.0
"""

    @app.get("/metrics", include_in_schema=False, response_class=_FallbackPlainText)
    async def fallback_metrics_prometheus_text_format():
        import time as _fb_time
        now_unix = _fb_time.time()
        body = _FALLBACK_METRICS_BASE + f"# HELP metrics_scrape_timestamp_seconds Unix UTC scrape timestamp.\n# TYPE metrics_scrape_timestamp_seconds gauge\nmetrics_scrape_timestamp_seconds{{service=\"mock-oidc\"}} {now_unix}\n"
        return body.rstrip() + "\n"
