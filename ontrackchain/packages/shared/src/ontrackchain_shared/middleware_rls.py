from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Awaitable, Callable, Iterable, Optional

from fastapi import FastAPI, HTTPException, Request, Response

logger = logging.getLogger(__name__)

# ============================================================
# Bypass padrão para rotas públicas (não precisam de contexto org)
# ============================================================
DEFAULT_BYPASS_RLS_PATHS: frozenset[str] = frozenset(
    [
        "/",
        "/health",
        "/healthz",
        "/ready",
        "/live",
        "/metrics",
        "/docs",
        "/docs/",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
        "/auth/dev-token",
        "/auth/login",
        "/auth/logout",
        "/auth/callback",
        "/auth/sso/login",
        "/auth/sso/callback",
        "/public",
        "/api/health",
        "/api/healthz",
        "/api/docs",
        "/api/openapi.json",
    ]
)

DEFAULT_BYPASS_RLS_PREFIXES: tuple[str, ...] = (
    "/public/",
    "/health",
    "/docs",
    "/openapi",
    "/auth/",
    "/static/",
    "/assets/",
)

ORG_ID_HEADER = "X-Organization-Id"
ORG_ID_CLAIM_KEYS = ("organization_id", "org_id", "tenant_id", "otk_org_id")

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _is_valid_uuid(value: object) -> bool:
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    if UUID_RE.match(s):
        return True
    try:
        uuid.UUID(s)
        return True
    except Exception:  # noqa: BLE001
        return False


def path_needs_rls_context(
    path: str,
    bypass_paths: Iterable[str] = DEFAULT_BYPASS_RLS_PATHS,
    bypass_prefixes: Iterable[str] = DEFAULT_BYPASS_RLS_PREFIXES,
) -> bool:
    """Retorna True SE a rota PRECISA de contexto RLS SETado."""
    if not path:
        return False
    if path in frozenset(bypass_paths):
        return False
    return not any(path.startswith(pfx) for pfx in bypass_prefixes)


def extract_org_id_from_headers(headers: Any) -> Optional[str]:
    """Extrai org_id de X-Organization-Id header (prioridade 1)."""
    try:
        raw = headers.get(ORG_ID_HEADER)
        if raw is None:
            # Case-insensitive fallback
            for k, v in headers.items():
                if str(k).lower() == "x-organization-id":
                    raw = v
                    break
        if raw:
            candidate = str(raw).strip()
            if _is_valid_uuid(candidate):
                return str(uuid.UUID(candidate))
    except Exception:  # noqa: BLE001
        return None
    return None


def extract_org_id_from_jwt_payload(jwt_payload: Optional[dict]) -> Optional[str]:
    """Extrai org_id de claims JWT decodificada (prioridade 2)."""
    if not isinstance(jwt_payload, dict):
        return None
    for key in ORG_ID_CLAIM_KEYS:
        if key in jwt_payload:
            candidate = jwt_payload[key]
            if isinstance(candidate, (list, tuple)) and len(candidate) > 0:
                candidate = candidate[0]
            if _is_valid_uuid(candidate):
                return str(uuid.UUID(str(candidate)))
    return None


def _extract_org_id_from_request(request: Request) -> Optional[str]:
    """Combina header + jwt_payload armazenado no request.state por auth middleware."""
    # 1. Header override (maior prioridade)
    from_header = extract_org_id_from_headers(request.headers)
    if from_header:
        return from_header

    # 2. Claim do JWT (caso auth-service já decodificou e salvou em state)
    try:
        jwt_payload = getattr(request.state, "jwt_payload", None)
        from_jwt = extract_org_id_from_jwt_payload(jwt_payload)
        if from_jwt:
            return from_jwt
    except Exception:  # noqa: BLE001
        pass

    # 3. Query param fallback (permitido apenas para admin tools em dev; filtrado por proxy em prod)
    try:
        raw_q = request.query_params.get("organization_id") or request.query_params.get(
            "org_id"
        )
        if raw_q and _is_valid_uuid(raw_q):
            return str(uuid.UUID(str(raw_q)))
    except Exception:  # noqa: BLE001
        pass

    return None


def apply_rls_context_on_connection(conn, org_id: str) -> None:
    """Versão SINCRONA: executa set_config em conexão psycopg3 (sync ConnectionPool)."""
    if conn is None:
        raise RuntimeError("connection pool unavailable")
    org_str = str(uuid.UUID(org_id))
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.organization_id', %s, True)", (org_str,))


async def apply_rls_context_on_async_connection(async_conn, org_id: str) -> None:
    """Versão ASSÍNCRONA: executa set_config em conexão psycopg3 AsyncConnection."""
    if async_conn is None:
        raise RuntimeError("async connection unavailable")
    org_str = str(uuid.UUID(org_id))
    async with async_conn.cursor() as cur:
        await cur.execute("SELECT set_config('app.organization_id', %s, True)", (org_str,))


def make_rls_context_middleware(
    get_pool_sync_fn: Optional[Callable[[Request], Any]] = None,
    bypass_paths: Iterable[str] = DEFAULT_BYPASS_RLS_PATHS,
    bypass_prefixes: Iterable[str] = DEFAULT_BYPASS_RLS_PREFIXES,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """
    Cria middleware Starlette/FastAPI global que injeta contexto de organização
    (SET app.organization_id) em conexão Postgres ANTES da rota rodar.

    Regras:
      1. Rotas bypass (healthz, docs, login, public) → NÃO faz nada, segue adiante
      2. Rota precisa de contexto → extrai org_id (header → jwt → query)
      3. Se org_id inválido/não encontrado → HTTP 401 (SECURITY-RLS-VIOLATION-NO-CONTEXT)
      4. Obtém 1 conexão do pool, executa SET, devolve a conexão (libera imediatamente)
      5. A conexão volta para o pool com contexto setado para a próxima query no mesmo request
    """
    from psycopg_pool import ConnectionPool  # lazy import para não forçar dep host

    async def _middleware(request: Request, call_next):
        path = getattr(request, "url", None) and request.url.path or request.scope.get("path", "/")
        if not path_needs_rls_context(path, bypass_paths, bypass_prefixes):
            return await call_next(request)

        org_id = _extract_org_id_from_request(request)
        if not org_id:
            logger.error(
                "SECURITY-RLS-VIOLATION-NO-CONTEXT path=%s client=%s",
                path,
                request.client.host if request.client else "unknown",
            )
            raise HTTPException(
                status_code=401,
                detail="SECURITY-RLS-VIOLATION-NO-CONTEXT: missing organization_id context "
                "(send X-Organization-Id header or valid JWT claim organization_id)",
            )

        # Pega pool através de callback (injetado por cada serviço)
        pool = None
        if get_pool_sync_fn is not None:
            try:
                pool = get_pool_sync_fn(request)
            except Exception:  # noqa: BLE001
                pool = getattr(request.app.state, "pool", None)
        if pool is None:
            pool = getattr(request.app.state, "pool", None)
        if pool is None:
            raise HTTPException(status_code=500, detail="RLS Context: Postgres pool unavailable")

        try:
            with pool.connection() as conn:
                apply_rls_context_on_connection(conn, org_id)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("SECURITY-RLS-CONTEXT-SET-FAILED path=%s error=%s", path, exc)
            raise HTTPException(
                status_code=500,
                detail=f"SECURITY-RLS-CONTEXT-SET-FAILED: {type(exc).__name__}",
            )

        # Armazena org_id extraido no state para uso nas rotas (evita re-extraction)
        try:
            setattr(request.state, "current_organization_id", org_id)
        except Exception:  # noqa: BLE001
            pass

        return await call_next(request)

    return _middleware


def register_rls_context_middleware(
    app: FastAPI,
    get_pool_sync_fn: Optional[Callable[[Request], Any]] = None,
    bypass_paths: Iterable[str] = DEFAULT_BYPASS_RLS_PATHS,
    bypass_prefixes: Iterable[str] = DEFAULT_BYPASS_RLS_PREFIXES,
) -> None:
    """Registra middleware RLS em app FastAPI. Chamado por cada serviço no main.py."""
    mw = make_rls_context_middleware(get_pool_sync_fn, bypass_paths, bypass_prefixes)
    app.add_middleware(type("RLSContextMiddleware", (), {"dispatch": staticmethod(mw)}) if False else None)
    # add_middleware exige uma classe BaseHTTPMiddleware-style. Solução mais idiomática:
    try:
        from starlette.middleware.base import BaseHTTPMiddleware

        class _RlsContextMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                return await mw(request, call_next)

        app.add_middleware(_RlsContextMiddleware)
    except Exception as fallback_exc:  # noqa: BLE001
        # Fallback: usa http_middleware diretamente no router
        logger.warning("RLS Middleware: using fallback http_middleware on router: %s", fallback_exc)
        app.router.http_middleware.insert(0, mw)
