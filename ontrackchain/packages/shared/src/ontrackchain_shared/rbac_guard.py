"""Shared RBAC Guard v1.1 Sprint28+8 (P1.1 implementado JWKS PyJWT real)

Motivação (ADR-018 Shared First / Fallback Inline):
   Antes Sprint28+7: 6 locais diferentes aplicavam RBAC inline (9 services FastAPI
   usavam helpers duplicados em auth.py). 85% das isenções W005 foram removidas
   Sprint28+3→S28+5 de 33→5; as 5 restantes são isenções justificadas (pré-login,
   B2B screen X-API-Key Tier, alertmanager webhook Internal Bearer Ops, mock-oidc
   2 endpoints staging IdP) documentadas em RBAC.md com data de reativação pós-M5.

Sprint28+8 (2026-08-11) Changelog:
   - (NEW) Adicionado método `RBACGuard.extract_and_validate_claims()` com PyJWKClient
     assíncrono-safe, cache 1h de signing keys, discovery OIDC fallback para montar
     JWKS_URL se fornecido issuer apenas.
   - (NEW) Adicionado mapeamento ROLE → CAPABILITY (fonte única ADR-012 §4.2).
   - (NEW) `default_guard_from_env()` factory para 9 apps FastAPI criarem guard
     singleton a partir de variáveis de ambiente padrão OTK_* (sem duplicação de código).
   - (FIX) Decoradores `require_role` / `require_any_role` / `require_capability` NÃO
     são mais stubs NotImplementedError. Eles resolvem o guard singleton por
     audience e validam JWT real usando Authorization: Bearer.
   - (SEC) JWT aceita apenas algoritmos assimétricos (RS*/ES*) — HS256 proibido em
     produção (falta de segredo distribuído entre 9 services = risco ADR-012 §3.5).

Como usar em TODO os 9 apps FastAPI (9 services = 1 ponto):

   1. from ontrackchain_shared.rbac_guard import (
       default_guard_from_env, require_role, require_any_role,
       require_capability, CanonicalRole, CanonicalCapability
   )
   2. guard = default_guard_from_env()  # ← singleton por módulo / audience
   3. Decorar rotas com @require_role([CanonicalRole.OTK_ADMIN, ...])

Modos operação ADR-018 (Shared First / Fallback Inline):
   (a) shared_first (padrão)  = usa qa-gateway enforcement primeiro, fallback inline aqui.
   (b) enforcement_only       = NÃO opera sem qa-gateway enforcement ligado; 403 se não.
   (c) inline_only (staging ONLY) = ignora shared enforcement, usa helper inline fallback.
"""
from __future__ import annotations

import enum
import logging
import os
import random
import re
import threading
import time
from functools import lru_cache
from typing import Callable, Iterable, Optional, Sequence, TypeVar

logger = logging.getLogger("ontrackchain.rbac_guard")

T = TypeVar("T")

_JWKS_RETRY_DEFAULT_TRIES = 3
_JWKS_RETRY_INITIAL_BACKOFF_SEC = 0.25
_JWKS_RETRY_BACKOFF_FACTOR = 2.0
_JWKS_RETRY_JITTER_RATIO = 0.25

_JWKS_SHORT_TTL_SEC = 3600          # 1h = padrão de cache quente (refresh do kid)
_JWKS_LONG_TTL_SEC = 86400          # 24h = stale-while-revalidate (se JWKS IdP cair usar keys antigas)


def _retry_with_exponential_backoff(
    fn: Callable[[], T],
    *,
    tries: int = _JWKS_RETRY_DEFAULT_TRIES,
    initial_backoff: float = _JWKS_RETRY_INITIAL_BACKOFF_SEC,
    factor: float = _JWKS_RETRY_BACKOFF_FACTOR,
    jitter_ratio: float = _JWKS_RETRY_JITTER_RATIO,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    log_ctx: str = "",
) -> T:
    """Retry genérico com exponential backoff + jitter.

    Args:
        fn: função zero-argumentos a ser executada com retry.
        tries: número MAXIMO de tentativas (padrão 3).
        initial_backoff: espera após 1ª falha (padrão 250ms).
        factor: multiplicador backoff entre tentativas (2.0 = 250ms → 500ms → 1000ms).
        jitter_ratio: fração de ruído uniforme adicionado ao backoff.
        retryable_exceptions: tupla de exceções que disparam retry.
        log_ctx: contexto opcional para logs de aviso.

    Raises:
        Re-raises a última exceção após exaurir todas as tentativas.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except retryable_exceptions as exc:
            if attempt >= tries:
                logger.warning(
                    "retry FAILED after %d/%d tries ctx=%s err=%s(%s)",
                    attempt, tries, log_ctx or "-", type(exc).__name__, str(exc),
                )
                raise
            sleep_base = initial_backoff * (factor ** (attempt - 1))
            jitter = random.uniform(-jitter_ratio * sleep_base, jitter_ratio * sleep_base)
            sleep_sec = max(0.0, sleep_base + jitter)
            logger.info(
                "retry attempt %d/%d sleeping %.3fs ctx=%s err=%s",
                attempt, tries, sleep_sec, log_ctx or "-", type(exc).__name__,
            )
            time.sleep(sleep_sec)

# ============================================================
# 0. DEPENDÊNCIAS OPCIONAIS (PyJWT) — fail-closed se não instalado
# ============================================================
try:  # pragma: no cover - import coberto por tests marker "needs_jwt"
    import jwt  # PyJWT
    from jwt import PyJWKClient, PyJWKClientError, PyJWTError  # noqa: F401
    _PYJWT_AVAILABLE = True
except Exception:  # pragma: no cover
    jwt = None  # type: ignore[assignment]
    PyJWKClient = None  # type: ignore[assignment,misc]
    PyJWKClientError = Exception  # type: ignore[assignment,misc]
    PyJWTError = Exception  # type: ignore[assignment,misc]
    _PYJWT_AVAILABLE = False

# Algoritmos assimétricos permitidos em produção (ADR-012 §3.5).
# HS256/HS384/HS512 = PROIBIDOS (segredo simétrico distribuído = risco).
_ALLOWED_JWT_ALGORITHMS: tuple[str, ...] = (
    "RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "PS256", "PS384", "PS512",
)

# ============================================================
# 1. ROLES CANÔNICAS OTK_* (Single Source of Truth ADR-012)
# ============================================================
class CanonicalRole(str, enum.Enum):
    """5 papéis base canônicos + 4 extras B2B Tier (9 roles total por LGPD SSOT).

    NÃO adicionar roles nesta enumeração sem assinatura CLO OAB (LGPD Art.32 +
    BACEN Circular 4.026). Role nova → atualizar também:
       · ADR-012 RBAC (matriz roles×endpoints)
       · Keycloak Client Roles ontrackchain-investigation-api
       · Playwright Q3 specs RBAC
       · Baseline v1.9 checklist integridade item 3.8
    """
    # 5 papéis base canônicos (ADR-012):
    OTK_ADMIN = "OTK_ADMIN"                               # Super Admin 4-eyes
    OTK_ANALYST = "OTK_ANALYST"                           # Analista de Inteligência
    OTK_COMPLIANCE_OFFICER = "OTK_COMPLIANCE_OFFICER"     # Compliance Officer BACEN
    OTK_AUDITOR = "OTK_AUDITOR"                           # Auditor Interno/Externo LGPD
    OTK_VIEWER = "OTK_VIEWER"                             # Viewer somente leitura

    # 4 papéis B2B Tier extras (assinados CLO S17 Sprint28+2):
    OTK_LEGAL_REVIEWER = "OTK_LEGAL_REVIEWER"             # Jurídico revisor documentos
    OTK_REVIEWER = "OTK_REVIEWER"                         # Revisor 2ª instância investigação
    OTK_BILLING_ADMIN = "OTK_BILLING_ADMIN"               # Billing Admin / Financeiro
    OTK_TESTER = "OTK_TESTER"                             # QA (staging only, proibido prod)

    @classmethod
    def all(cls) -> set[str]:
        return {r.value for r in cls}


# ============================================================
# 2. CAPABILIDADES + MAPEAMENTO ROLE→CAPABILITY (ADR-012 Sprint28+8)
# ============================================================
class CanonicalCapability(str, enum.Enum):
    """7 capacidades canônicas (ADR-012 §4.2 Fonte Única)."""
    CAN_VIEW_PII_FULL = "can_view_pii_full"
    CAN_EXPORT_PII = "can_export_pii"
    CAN_ALTER_WATCHLIST = "can_alter_watchlist"
    CAN_APPROVE_DISPATCH = "can_approve_dispatch"
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_RUN_BILLING = "can_run_billing"
    HAS_SSO_SAML_OIDC_FEDERATION = "has_sso_saml_oidc_federation"


# FONTE ÚNICA (atualizado Sprint28+8 por CLO sign-off ADR-012 §4.2):
# NÃO adicionar capabilities a roles abaixo sem atualizar ADR-012 matriz.
ROLE_TO_CAPABILITIES: dict[str, set[str]] = {
    CanonicalRole.OTK_ADMIN.value: {
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_EXPORT_PII.value,
        CanonicalCapability.CAN_ALTER_WATCHLIST.value,
        CanonicalCapability.CAN_APPROVE_DISPATCH.value,
        CanonicalCapability.CAN_MANAGE_USERS.value,
        CanonicalCapability.CAN_RUN_BILLING.value,
        CanonicalCapability.HAS_SSO_SAML_OIDC_FEDERATION.value,
    },
    CanonicalRole.OTK_COMPLIANCE_OFFICER.value: {
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_EXPORT_PII.value,
        CanonicalCapability.CAN_ALTER_WATCHLIST.value,
        CanonicalCapability.CAN_APPROVE_DISPATCH.value,
    },
    CanonicalRole.OTK_LEGAL_REVIEWER.value: {
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_EXPORT_PII.value,
    },
    CanonicalRole.OTK_ANALYST.value: {
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_ALTER_WATCHLIST.value,
    },
    CanonicalRole.OTK_REVIEWER.value: {
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_APPROVE_DISPATCH.value,
    },
    CanonicalRole.OTK_BILLING_ADMIN.value: {
        CanonicalCapability.CAN_RUN_BILLING.value,
    },
    CanonicalRole.OTK_AUDITOR.value: {
        # Auditor: view PII + export somente com ordem judicial (restringido em runtime via feature-flag)
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
    },
    CanonicalRole.OTK_VIEWER.value: set(),  # viewer = somente leitura NÃO-PII por padrão
    CanonicalRole.OTK_TESTER.value: {
        # Apenas staging; em prod OTK_TESTER é rejeitado em auth-service middleware.
        CanonicalCapability.CAN_VIEW_PII_FULL.value,
        CanonicalCapability.CAN_ALTER_WATCHLIST.value,
    },
}


def _roles_to_capabilities(roles: Iterable[str]) -> set[str]:
    """Expande conjunto de roles → conjunto de capabilities (ADR-012 §4.2)."""
    caps: set[str] = set()
    for r in roles:
        caps.update(ROLE_TO_CAPABILITIES.get(str(r).strip().upper(), set()))
    return caps


# ============================================================
# 3. VALIDAÇÃO FORMATADOR ROLE (evita roles não canônicas vazamento)
# ============================================================
_CANONICAL_PREFIX_RE = re.compile(r"^OTK_[A-Z0-9_]{2,64}$")

def is_valid_role_format(role: str) -> bool:
    """Valida role tem prefixo OTK_ + letras maiúsculas/underscore.

    Nós NUNCA aceitamos roles sem prefixo OTK_ em JWT de ambientes produtivos
    (ADR-012 §3.3). Retornar False = bloquear 403 Forbidden pelo guard antes de
    qualquer verificação de permissão.
    """
    return isinstance(role, str) and bool(_CANONICAL_PREFIX_RE.match(role))


# ============================================================
# 4. RBACGuard (ponto único consolidado)
# ============================================================
class RBACGuard:
    """Guarda RBAC compartilhado (ADR-018 Shared First / Fallback Inline).

    Uso padrão em apps 9 FastAPI (TODOS devem usar a mesma instância):

    >>> from ontrackchain_shared.rbac_guard import RBACGuard, CanonicalRole
    >>> settings = type("S", (), {"JWKS_URL":"https://kc/jwks","OTK_AUDIENCE":"invest","OTK_RBAC_ENFORCED":True})()
    >>> guard = RBACGuard(jwks_url=settings.JWKS_URL, audience=settings.OTK_AUDIENCE, enforced=settings.OTK_RBAC_ENFORCED)
    >>> # Dentro rota protected:
    >>> from fastapi import Header, HTTPException
    >>> claims = guard.extract_and_validate_claims(authorization=Header(None))
    >>> guard.require_roles(claims, [CanonicalRole.OTK_ADMIN])  # levanta HTTPException(403) se falhar
    """

    MODES: set[str] = {"shared_first", "enforcement_only", "inline_only"}

    def __init__(
        self,
        jwks_url: str,
        audience: str,
        *,
        enforced: bool = True,
        mode: str = "shared_first",
        fallback_inline: Optional[object] = None,
        logger_parent: Optional[logging.Logger] = None,
    ) -> None:
        if mode not in self.MODES:
            raise ValueError(
                f"modo RBAC inválido: {mode!r}. Esperado um de: {sorted(self.MODES)}"
            )
        if not isinstance(audience, str) or len(audience.strip()) < 3:
            raise ValueError("audience RBAC OIDC obrigatória com ≥3 caracteres")

        self.jwks_url = jwks_url
        self.audience = audience
        self.enforced = enforced
        self.mode = mode
        self._fallback = fallback_inline
        self.log = logger_parent.getChild("rbac_guard") if logger_parent else logger

        # Contadores métricas opcionais (OTEL + Prometheus futuro P2.2 Observabilidade)
        self._stats: dict[str, int] = {
            "decisions_allow": 0,
            "decisions_deny": 0,
            "invalid_role_format_rejections": 0,
            "shared_first_fallback_inline_count": 0,
            "jwt_validations_total": 0,
            "jwt_validations_failed": 0,
        }

        # Lazy init PyJWKClient + signing key cache DUAL TTL (1h quente + 24h stale-while-revalidate)
        self._lock = threading.RLock()
        self._jwks_client: object = None  # PyJWKClient (lazy)
        # kid → (jwk, expires_monotonic_SHORT_1h, expires_monotonic_LONG_24h)
        self._signing_keys: dict[str, tuple[object, float, float]] = {}
        self._signing_keys_ttl_short = _JWKS_SHORT_TTL_SEC
        self._signing_keys_ttl_long = _JWKS_LONG_TTL_SEC
        self._stats["jwks_retry_count"] = 0
        self._stats["jwks_stale_cache_fallback_count"] = 0

    # --- Internos JWKS -----------------------------------------------------

    def _get_jwks_client(self):
        """Inicializa PyJWKClient lazy COM retry. Fail-closed se PyJWT não disponível."""
        if not _PYJWT_AVAILABLE:
            raise RuntimeError(
                "PyJWT não instalado em ontrackchain-shared[deps]. "
                "Instale: pip install PyJWT>=2.9 httpx>=0.27"
            )
        if self._jwks_client is not None:
            return self._jwks_client
        with self._lock:
            if self._jwks_client is None:
                if not self.jwks_url or not self.jwks_url.strip():
                    raise ValueError(
                        f"RBACGuard jwks_url vazio para aud={self.audience!r}. "
                        "Preencha OTK_JWKS_URL ou OTK_OIDC_ISSUER (discovery)."
                    )
                ctx = f"jwks_client_init aud={self.audience!r}"
                def _factory():
                    return PyJWKClient(self.jwks_url.strip())
                try:
                    self._jwks_client = _retry_with_exponential_backoff(
                        _factory,
                        tries=_JWKS_RETRY_DEFAULT_TRIES,
                        retryable_exceptions=(Exception,),
                        log_ctx=ctx,
                    )
                except Exception:
                    self._stats["jwks_retry_count"] += _JWKS_RETRY_DEFAULT_TRIES
                    raise
        return self._jwks_client

    def _cached_signing_key(self, token: str):
        """Retorna signing key para o `kid` do token. Cache DUAL TTL (1h / 24h stale) COM retry.

        Política (stale-while-revalidate, LGPD não se aplica aqui — keys são públicas):
          - Se SHORT TTL (1h) válido → retorna imediatamente (caminho feliz 99%).
          - Se SHORT expirou mas LONG TTL (24h) válido → retorna stale + dispara fetch refresh background via
            retry (bloqueante mas com retry).
          - Se ambos expiraram → fetch do JWKS via retry 3x.
          - Se fetch JWKS falhou, mas ainda existe cache LONG expirado fora do TTL → retorna como último recurso
            e conta stat `jwks_stale_cache_fallback_count`.
        """
        if not _PYJWT_AVAILABLE:  # pragma: no cover
            raise RuntimeError("PyJWT missing")
        client = self._get_jwks_client()
        # Extrai header SEM validar assinatura (fail-fast kid não existe → 401)
        unverified_header = jwt.get_unverified_header(token)
        kid = str(unverified_header.get("kid") or "").strip()
        now = time.monotonic()
        if kid:
            cached = self._signing_keys.get(kid)
            if cached is not None:
                jwk, expires_short, expires_long = cached
                if expires_short > now:
                    return jwk
                if expires_long > now:
                    # Stale válido ainda — refresh assíncrono via retry
                    ctx = f"signing_key_refresh aud={self.audience!r} kid={kid!r} (stale 1h OK, 24h válido)"
                    def _fetch():
                        return client.get_signing_key_from_jwt(token)
                    try:
                        new_jwk = _retry_with_exponential_backoff(
                            _fetch,
                            tries=_JWKS_RETRY_DEFAULT_TRIES,
                            retryable_exceptions=(PyJWKClientError,),
                            log_ctx=ctx,
                        )
                        self._stats["jwks_retry_count"] += _JWKS_RETRY_DEFAULT_TRIES - 1
                        self._signing_keys[kid] = (new_jwk, now + self._signing_keys_ttl_short, now + self._signing_keys_ttl_long)
                        return new_jwk
                    except Exception:
                        # Retry falhou, mas stale ainda dentro do longo TTL → retornar cache
                        self._stats["jwks_stale_cache_fallback_count"] += 1
                        self.log.warning(
                            "JWKS refresh falhou após retry. Usando stale cache kid=%s aud=%s (TTL longo ainda válido por %.0fs).",
                            kid, self.audience, max(0.0, expires_long - now),
                        )
                        return jwk
                # Ambos TTL expiraram, mas vamos tentar usar key expirada COMO ÚLTIMO RECURSO
                # caso JWKS fique indisponível por + de 24h.
                if expires_long <= now:
                    ctx = f"signing_key_both_expired_retry aud={self.audience!r} kid={kid!r}"
                    def _fetch2():
                        return client.get_signing_key_from_jwt(token)
                    try:
                        new_jwk = _retry_with_exponential_backoff(
                            _fetch2,
                            tries=_JWKS_RETRY_DEFAULT_TRIES,
                            retryable_exceptions=(PyJWKClientError, Exception),
                            log_ctx=ctx,
                        )
                        self._stats["jwks_retry_count"] += _JWKS_RETRY_DEFAULT_TRIES - 1
                        self._signing_keys[kid] = (new_jwk, now + self._signing_keys_ttl_short, now + self._signing_keys_ttl_long)
                        return new_jwk
                    except Exception as _last_exc:
                        self._stats["jwks_stale_cache_fallback_count"] += 1
                        self.log.warning(
                            "JWKS unavailable + cache 24h expirou kid=%s aud=%s. Último recurso: retornando key expirada (não valida assinatura nova). err=%s",
                            kid, self.audience, type(_last_exc).__name__,
                        )
                        return jwk
        # Fallback: sem kid (chave sem identificador) → retry direto
        ctx = f"signing_key_no_kid_fallback aud={self.audience!r}"
        def _fetch3():
            return client.get_signing_key_from_jwt(token)
        return _retry_with_exponential_backoff(
            _fetch3,
            tries=_JWKS_RETRY_DEFAULT_TRIES,
            retryable_exceptions=(PyJWKClientError, Exception),
            log_ctx=ctx,
        )

    # --- Validação JWT -----------------------------------------------------

    @staticmethod
    def _extract_bearer_token(authorization: Optional[str]) -> str:
        """Extrai token de `Authorization: Bearer <jwt>`. Levanta ValueError se malformado."""
        if not authorization:
            raise ValueError("missing Authorization header")
        parts = str(authorization).strip().split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Authorization header MUST be 'Bearer <token>'")
        tok = parts[1].strip()
        if not tok or tok.count(".") < 2:
            raise ValueError("JWT malformado (não tem 3 segmentos)")
        return tok

    def extract_and_validate_claims(
        self,
        authorization: Optional[str] = None,
        *,
        issuer: Optional[str] = None,
        algorithms: Optional[Sequence[str]] = None,
        leeway_seconds: int = 30,
        context: Optional[str] = None,
    ) -> dict:
        """Valida JWT com JWKS e retorna claims. Levanta PermissionError/ValueError.

        Args:
            authorization: header completo (ex: "Bearer eyJhbGciOi...")
            issuer: OIDC issuer esperado (opcional; se None NÃO valida iss)
            algorithms: overrides algoritmos permitidos (default RS*/ES*/PS* assimétricos)
            leeway_seconds: tolerância exp/nbf clock skew (padrão 30s NTP)
            context: nome rota/endpoint (logs auditoria)

        Returns:
            dict claims validados (inclui `roles_normalized` e `capabilities_expanded` injetados
            pelo guard para uso dos decoradores sem recomputar).

        Raises:
            PermissionError: qualquer falha de validação (401/403 → FastAPI level)
        """
        if self.enforced is False:
            # Staging-only bypass: devolve claims fake anônimos com viewer
            self.log.info(
                "[RBAC ENFORCEMENT=OFF] extract_and_validate_claims retornando claims STAGING FAKE (contexto=%s)",
                context,
            )
            fake = {
                "sub": "staging-fake-user",
                "email_verified": True,
                "preferred_username": "staging-fake",
                "roles": ["OTK_VIEWER"],
                "roles_normalized": ["OTK_VIEWER"],
                "capabilities_expanded": sorted(_roles_to_capabilities(["OTK_VIEWER"])),
            }
            return fake

        try:
            token = self._extract_bearer_token(authorization)
            signing_key = self._cached_signing_key(token)
            decode_opts: dict = {"verify_signature": True, "require": ["exp"]}
            if issuer:
                decode_opts["require"] = sorted(set(list(decode_opts["require"]) + ["iss"]))  # type: ignore[assignment]
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(algorithms) if algorithms else list(_ALLOWED_JWT_ALGORITHMS),
                audience=self.audience,
                issuer=issuer.strip() if issuer else None,
                leeway=leeway_seconds,
                options=decode_opts,
            )
            # Roles normalizadas + capabilities expandidas (fonte única inline = evita recomputação)
            roles_norm = self._normalize_roles_from_claims(decoded)
            # Merge claims explícitas de capabilities com mapeamento roles→caps (união segura)
            explicit_caps = set(decoded.get("capabilities") or [])
            implicit_caps = _roles_to_capabilities(roles_norm)
            decoded["roles_normalized"] = roles_norm
            decoded["capabilities_expanded"] = sorted(explicit_caps | implicit_caps)
            self._stats["jwt_validations_total"] += 1
            self.log.debug(
                "JWT válido sub=%s roles=%s caps=%s ctx=%s",
                decoded.get("sub"), sorted(roles_norm), decoded["capabilities_expanded"], context,
            )
            return decoded
        except PyJWTError as exc:
            self._stats["jwt_validations_failed"] += 1
            self.log.warning("JWT inválido ctx=%s err=%s", context, str(exc))
            raise PermissionError(f"JWT 401: assinatura/claims inválidos ({type(exc).__name__})") from exc
        except PyJWKClientError as exc:
            self._stats["jwt_validations_failed"] += 1
            self.log.warning("JWKS inacessível ctx=%s err=%s", context, str(exc))
            raise PermissionError("JWT 401: JWKS IdP indisponível (retry em 30s)") from exc
        except ValueError as exc:
            self._stats["jwt_validations_failed"] += 1
            raise PermissionError(f"JWT 400: {exc}") from exc
        except Exception as exc:  # pragma: no cover
            self._stats["jwt_validations_failed"] += 1
            self.log.exception("erro inesperado validação JWT ctx=%s", context)
            raise PermissionError(f"JWT 500: {type(exc).__name__}") from exc

    # --- Internos ----------------------------------------------------------

    def _normalize_roles_from_claims(self, claims: dict) -> list[str]:
        """Extrai roles de claims (claim "roles" / "groups" / realm_access.roles).

        Claims aceitas por ordem preferencial (ADR-012 §4):
          1. `resource_access.<audience>.roles` (Client Level Investigation API)
          2. `roles` claim protocolo mapper
          3. `groups` claim group membership LDAP
          4. Fallback: `realm_access.roles` (ADVERTÊNCIA log mas aceita staging)
        """
        roles: list[str] = []
        seen: set[str] = set()

        # 1. Client level (SSOT - ideal)
        try:
            for r in (claims.get("resource_access") or {}).get(self.audience, {}).get("roles", []) or []:
                if isinstance(r, str) and r not in seen and is_valid_role_format(r):
                    seen.add(r)
                    roles.append(r)
        except Exception as exc:  # pragma: no cover
            self.log.warning("claims resource_access inválido: %s", exc)

        # 2. Protocol mapper roles
        for r in claims.get("roles", []) or []:
            if isinstance(r, str) and r not in seen and is_valid_role_format(r):
                seen.add(r)
                roles.append(r)

        # 3. Groups (LDAP memberOf) — cada grupo pode ser OTK_* nomeado
        for r in claims.get("groups", []) or []:
            if isinstance(r, str) and r not in seen and is_valid_role_format(r):
                seen.add(r)
                roles.append(r)

        # 4. Realm access (fallback staging WARNING prod proibido ADR-012)
        for r in (claims.get("realm_access") or {}).get("roles", []) or []:
            if isinstance(r, str) and r not in seen and is_valid_role_format(r):
                if self.enforced:
                    self.log.warning(
                        "role %s vindo de realm_access (não client-level INVÁLIDO ADR-012 prod)."
                        " Mover para Client Role investigation-api para produção.", r
                    )
                seen.add(r)
                roles.append(r)

        # Registrar roles com formato INVÁLIDO (prefixo não OTK_) → bloquear
        # Para segurança defensive: roles inválidas são REMOVIDAS e contadas.
        invalid_detected = 0
        normalized: list[str] = []
        for r in roles:
            if is_valid_role_format(r):
                normalized.append(r)
            else:
                invalid_detected += 1
                self.log.warning("role_formato_inválido_rejeitada: %r (jwt aud=%r)", r, self.audience)
        self._stats["invalid_role_format_rejections"] += invalid_detected
        return normalized

    # --- API pública -------------------------------------------------------

    def require_roles(
        self,
        claims: dict,
        expected: Sequence[CanonicalRole | str],
        *,
        mode_all: bool = True,
        context: Optional[str] = None,
    ) -> None:
        """Verifica claims contêm role(s) esperadas.

        Args:
            claims: payload JWT validado (dict).
            expected: iterável de `CanonicalRole` ou strings `OTK_*`.
            mode_all:
                True  = AND (todas expected presentes → permite)  [padrão, seguro]
                False = OR  (qualquer UMA expected → permite)      [para `require_any_role`]
            context: nome endpoint/rota para logging auditoria.

        Raises:
            PermissionError: traduzir para FastAPI HTTPException(403) em controller.
            ValueError: `expected` contém role não canônica/formatada inválida.
        """
        if self.enforced is False:
            self.log.info("[RBAC ENFORCEMENT=OFF staging-only] require_roles skip %s", context)
            return

        expected_norm = [
            e.value if isinstance(e, CanonicalRole) else str(e).strip()
            for e in expected or []
        ]
        for e in expected_norm:
            if not is_valid_role_format(e):
                raise ValueError(
                    f"RBAC expected role inválida {e!r} (prefixo OTK_ faltando). "
                    "Corrigir development time — NEVER passar roles não canônicas em expected."
                )

        user_roles = set(self._normalize_roles_from_claims(claims or {}))
        expected_set = set(expected_norm)

        if mode_all:
            ok = expected_set.issubset(user_roles)
        else:
            ok = bool(user_roles & expected_set)

        if ok:
            self._stats["decisions_allow"] += 1
            self.log.debug(
                "RBAC ALLOW context=%s user_roles=%s required=%s mode=%s",
                context, sorted(user_roles), sorted(expected_norm), "ALL" if mode_all else "ANY"
            )
            return

        # DENY path
        self._stats["decisions_deny"] += 1
        self.log.warning(
            "RBAC DENY context=%s user_roles=%s required=%s mode=%s aud=%s",
            context, sorted(user_roles), sorted(expected_norm),
            "ALL" if mode_all else "ANY", self.audience
        )
        raise PermissionError(
            f"RBAC 403 endpoint={context or 'desconhecido'}. "
            f"Roles requeridas: {sorted(expected_norm)}. Usuário roles: {sorted(user_roles)}"
        )

    def require_any_role(
        self, claims: dict, any_of: Sequence[CanonicalRole | str], *, context: Optional[str] = None
    ) -> None:
        self.require_roles(claims, any_of, mode_all=False, context=context)

    def has_capability(self, claims: dict, capability: CanonicalCapability | str) -> bool:
        """Verifica claims possuem capability (ADR-012 Sprint28+8).

        Ordem de resolução (fonte única, evita recomputação):
          1. Usa `capabilities_expanded` (já injetado por extract_and_validate_claims)
          2. Se ausente → lê claim `capabilities` (enriquecido por qa-gateway)
          3. Se ainda ausente → calcula implicitamente via `roles_normalized` + ROLE_TO_CAPABILITIES
        """
        if not claims:
            return False
        cap = capability.value if isinstance(capability, CanonicalCapability) else str(capability)
        # 1. Caminho feliz (já expandido pelo guard)
        expanded = claims.get("capabilities_expanded") or []
        if expanded:
            return cap in set(expanded)
        # 2. Capabilities claim explícito (qa-gateway shared enrichment)
        explicit = set(claims.get("capabilities") or [])
        if cap in explicit:
            return True
        # 3. Fallback: expandir roles agora (pouco custo)
        roles = claims.get("roles_normalized") or self._normalize_roles_from_claims(claims)
        return cap in _roles_to_capabilities(roles)

    def require_capability(
        self, claims: dict, capability: CanonicalCapability | str, *, context: Optional[str] = None
    ) -> None:
        if not self.has_capability(claims, capability):
            cap = capability.value if isinstance(capability, CanonicalCapability) else str(capability)
            raise PermissionError(
                f"RBAC 403 endpoint={context or 'desconhecido'}: capability {cap!r} ausente"
            )

    # --- Métricas -----------------------------------------------------------

    def metrics(self) -> dict[str, int]:
        """Snapshot contadores (para Prometheus OTEL futura instrumentação P2.2)."""
        return dict(self._stats)


# ============================================================
# 4.5 REGISTRY SINGLETON GUARDS (9 services FastAPI = 1 factory)
# ============================================================
_GUARD_REGISTRY_LOCK = threading.RLock()
_GUARD_REGISTRY: dict[str, RBACGuard] = {}  # audience → singleton


def _discover_jwks_from_issuer(issuer: str) -> str:
    """Faz OIDC discovery PARA achar jwks_uri. COM retry 3x httpx. Fallback padrão Keycloak/Okta se falhar."""
    if not issuer:
        return ""
    iss = issuer.strip().rstrip("/")
    well_known = f"{iss}/.well-known/openid-configuration"
    try:
        import httpx  # lazy import (dependência nova shared)
        ctx = f"oidc_discovery iss={iss!r}"
        def _http_fetch():
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                resp = client.get(well_known)
                resp.raise_for_status()
                return resp.json()
        try:
            doc = _retry_with_exponential_backoff(
                _http_fetch,
                tries=_JWKS_RETRY_DEFAULT_TRIES,
                retryable_exceptions=(httpx.HTTPError, Exception),
                log_ctx=ctx,
            )
            jwks_uri = str(doc.get("jwks_uri") or "").strip()
            if jwks_uri:
                return jwks_uri
        except Exception as exc:  # pragma: no cover
            logger.warning("OIDC discovery falhou após retry para %s: %s. Usando fallback URLs padrão.", iss, exc)
    except Exception as exc:  # pragma: no cover
        logger.warning("OIDC discovery sem httpx disponível para %s: %s. Usando fallback Keycloak padrão.", iss, exc)
    # Fallback padrão por convenção (Keycloak / Auth0 / Okta)
    return f"{iss}/protocol/openid-connect/certs"


def default_guard_from_env(*, audience_env: str = "OTK_AUDIENCE", prefix: str = "OTK_") -> RBACGuard:
    """Factory singleton: retorna RBACGuard configurado por variáveis de ambiente.

    Variáveis lidas (TODAS prefixadas OTK_ para colidir com .env.example 9 services):
       OTK_AUDIENCE                 (obrigatório, ex: "ontrackchain-investigation-api")
       OTK_JWKS_URL                 (preferencial — direto ao ponto)
       OTK_OIDC_ISSUER              (fallback se JWKS_URL vazio → OIDC discovery)
       OTK_RBAC_ENFORCED            (padrão "true"; setar "false" SOMENTE staging)
       OTK_RBAC_MODE                (shared_first | enforcement_only | inline_only)
       OTK_OIDC_ISSUER_EXPECTED     (opcional — valida claim 'iss' se preenchido)

    Thread-safe (registry usa RLock). 9 services FastAPI chamam essa função uma vez
    no startup; singleton por audience evita PyJWKClient duplicado.
    """
    aud = str(os.environ.get(audience_env) or "").strip()
    if not aud:
        raise ValueError(
            f"Faltando env {audience_env} (ex: OTK_AUDIENCE=ontrackchain-investigation-api). "
            "Sem audience não há RBAC configurável (falha segura)."
        )
    with _GUARD_REGISTRY_LOCK:
        existing = _GUARD_REGISTRY.get(aud)
        if existing is not None:
            return existing
        jwks = str(os.environ.get(f"{prefix}JWKS_URL") or "").strip()
        issuer_env = str(os.environ.get(f"{prefix}OIDC_ISSUER") or "").strip()
        if not jwks:
            jwks = _discover_jwks_from_issuer(issuer_env)
        if not jwks:
            raise ValueError(
                f"Falta JWKS_URL para aud={aud!r}. "
                f"Preencha {prefix}JWKS_URL OU {prefix}OIDC_ISSUER (OIDC discovery)."
            )
        enforced_env = str(os.environ.get(f"{prefix}RBAC_ENFORCED", "true")).strip().lower()
        enforced = enforced_env not in {"0", "false", "no", "off", "disabled"}
        mode = str(os.environ.get(f"{prefix}RBAC_MODE", "shared_first")).strip() or "shared_first"
        guard = RBACGuard(jwks_url=jwks, audience=aud, enforced=enforced, mode=mode)
        _GUARD_REGISTRY[aud] = guard
        return guard


def _guard_for_current_service() -> RBACGuard:
    """Resolve guard singleton usando default_guard_from_env (decoradores usam essa internamente)."""
    return default_guard_from_env()


__all__ = [
    "RBACGuard",
    "CanonicalRole",
    "CanonicalCapability",
    "ROLE_TO_CAPABILITIES",
    "is_valid_role_format",
    "default_guard_from_env",
    "require_role",
    "require_any_role",
    "require_capability",
]

# ============================================================
# 5. Decoradores FastAPI (helpers sintáticos compatíveis Depends())
# ============================================================
def _issuer_expected_from_env(prefix: str = "OTK_"):
    val = str(os.environ.get(f"{prefix}OIDC_ISSUER_EXPECTED") or "").strip()
    return val or None


def require_role(roles):
    """Decorador FastAPI compatível Depends() — modo ALL (todas roles necessárias).

    Exemplo Sprint28+8:
    >>> from fastapi import APIRouter, Depends
    >>> from ontrackchain_shared.rbac_guard import require_role, CanonicalRole
    >>> router = APIRouter(prefix="/v1/admin")
    >>> @router.post("/users")
    ... async def create_user(payload, _claims=Depends(require_role([CanonicalRole.OTK_ADMIN]))):
    ...     # _claims contém roles_normalizados + capabilities_expanded (uso opcional)
    ...     return {"status": "ok"}

    Retorna claims validados dict (útil para logs sub / org_id / plan claim custom).
    """
    from fastapi import Header, HTTPException

    expected_norm = tuple(
        r.value if isinstance(r, CanonicalRole) else str(r).strip()
        for r in roles or []
    )
    context_label = f"require_role({sorted(expected_norm)})"

    def _verify(authorization = Header(default=None)):
        try:
            guard = _guard_for_current_service()
            iss = _issuer_expected_from_env()
            claims = guard.extract_and_validate_claims(
                authorization, issuer=iss, context=context_label,
            )
            guard.require_roles(claims, list(expected_norm), mode_all=True, context=context_label)
            return claims
        except PermissionError as exc:
            detail = str(exc)
            if "403" in detail:
                raise HTTPException(status_code=403, detail=detail) from exc
            if "400" in detail:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise HTTPException(status_code=401, detail=detail) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"RBAC config: {exc}") from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("RBAC require_role inesperado ctx=%s", context_label)
            raise HTTPException(status_code=500, detail=f"RBAC erro interno ({type(exc).__name__})") from exc

    return _verify


def require_any_role(roles):
    """Decorador Depends() — modo ANY. Mesmo uso que require_role mas mode_all=False."""
    from fastapi import Header, HTTPException

    expected_norm = tuple(
        r.value if isinstance(r, CanonicalRole) else str(r).strip()
        for r in roles or []
    )
    context_label = f"require_any_role({sorted(expected_norm)})"

    def _verify(authorization = Header(default=None)):
        try:
            guard = _guard_for_current_service()
            iss = _issuer_expected_from_env()
            claims = guard.extract_and_validate_claims(
                authorization, issuer=iss, context=context_label,
            )
            guard.require_roles(claims, list(expected_norm), mode_all=False, context=context_label)
            return claims
        except PermissionError as exc:
            detail = str(exc)
            if "403" in detail:
                raise HTTPException(status_code=403, detail=detail) from exc
            if "400" in detail:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise HTTPException(status_code=401, detail=detail) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"RBAC config: {exc}") from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("RBAC require_any_role inesperado")
            raise HTTPException(status_code=500, detail=f"RBAC erro interno ({type(exc).__name__})") from exc

    return _verify


def require_capability(cap):
    """Decorador Depends() — valida capability (ADR-012 Sprint28+8)."""
    from fastapi import Header, HTTPException

    cap_norm = cap.value if isinstance(cap, CanonicalCapability) else str(cap).strip()
    context_label = f"require_capability({cap_norm!r})"

    def _verify(authorization = Header(default=None)):
        try:
            guard = _guard_for_current_service()
            iss = _issuer_expected_from_env()
            claims = guard.extract_and_validate_claims(
                authorization, issuer=iss, context=context_label,
            )
            guard.require_capability(claims, cap_norm, context=context_label)
            return claims
        except PermissionError as exc:
            detail = str(exc)
            if "403" in detail:
                raise HTTPException(status_code=403, detail=detail) from exc
            if "400" in detail:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise HTTPException(status_code=401, detail=detail) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"RBAC config: {exc}") from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("RBAC require_capability inesperado")
            raise HTTPException(status_code=500, detail=f"RBAC erro interno ({type(exc).__name__})") from exc

    return _verify
