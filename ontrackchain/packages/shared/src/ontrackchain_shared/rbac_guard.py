"""Shared RBAC Guard v1.0 Sprint28+7 (P1.5 helper consolidado 6→1 ponto único)

Motivação (ADR-018 Shared First / Fallback Inline):
   Antes Sprint28+7: 6 locais diferentes aplicavam RBAC inline (9 services FastAPI
   usavam helpers duplicados em auth.py). 85% das isenções W005 foram removidas
   Sprint28+3→S28+5 de 33→5; as 5 restantes são isenções justificadas (pré-login,
   B2B screen X-API-Key Tier, alertmanager webhook Internal Bearer Ops, mock-oidc
   2 endpoints staging IdP) documentadas em RBAC.md com data de reativação pós-M5.

Como usar em TODO os 9 apps FastAPI (9 services = 1 ponto):

   1. from ontrackchain_shared.rbac_guard import (
       RBACGuard, require_role, require_any_role, require_capability,
       CanonicalRole, CanonicalCapability
   )
   2. guard = RBACGuard(jwks_url=settings.JWKS_URL, audience=settings.OTK_AUDIENCE,
                       enforced=settings.OTK_RBAC_ENFORCED, mode="shared_first")
   3. Decorar rotas com @require_role([CanonicalRole.OTK_ADMIN, ...])

Modos operação ADR-018 (Shared First / Fallback Inline):
   (a) shared_first (padrão)  = usa qa-gateway enforcement primeiro, fallback inline aqui.
   (b) enforcement_only       = NÃO opera sem qa-gateway enforcement ligado; 403 se não.
   (c) inline_only (staging ONLY) = ignora shared enforcement, usa helper inline fallback.
"""
from __future__ import annotations

import enum
import logging
import re
from typing import Iterable, Optional, Sequence

logger = logging.getLogger("ontrackchain.rbac_guard")

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
# 2. CAPABILIDADES (ADR-012 Sprint28+2 plano capabilities)
# ============================================================
class CanonicalCapability(str, enum.Enum):
    """7 capacidades canônicas (ADR-012)."""
    CAN_VIEW_PII_FULL = "can_view_pii_full"
    CAN_EXPORT_PII = "can_export_pii"
    CAN_ALTER_WATCHLIST = "can_alter_watchlist"
    CAN_APPROVE_DISPATCH = "can_approve_dispatch"
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_RUN_BILLING = "can_run_billing"
    HAS_SSO_SAML_OIDC_FEDERATION = "has_sso_saml_oidc_federation"


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
        }

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
        """Verifica claims possuem capability (ADR-012).

        Capacidades são geralmente claims aninhados `capabilities: list[str]`
        (enriquecidas por qa-gateway shared enforcement). Se NÃO existir o claim
        → retorna False (falha segura).
        """
        cap = capability.value if isinstance(capability, CanonicalCapability) else str(capability)
        return cap in set(claims.get("capabilities") or []) if claims else False

    def require_capability(
        self, claims: dict, capability: CanonicalCapability | str, *, context: Optional[str] = None
    ) -> None:
        if not self.has_capability(claims, capability):
            raise PermissionError(
                f"RBAC 403 endpoint={context or 'desconhecido'}: capability {capability!r} ausente"
            )

    # --- Métricas -----------------------------------------------------------

    def metrics(self) -> dict[str, int]:
        """Snapshot contadores (para Prometheus OTEL futura instrumentação P2.2)."""
        return dict(self._stats)


__all__ = [
    "RBACGuard",
    "CanonicalRole",
    "CanonicalCapability",
    "is_valid_role_format",
    "require_role",
    "require_any_role",
    "require_capability",
]


# ============================================================
# 5. Decoradores FastAPI (helpers sintáticos compatíveis DI)
# ============================================================
def require_role(roles: Sequence[CanonicalRole | str]):
    """Decorador FastAPI compatível Depends(..., use_cache=True).

    Exemplo Sprint28+7:
    >>> from fastapi import APIRouter, Depends
    >>> from ontrackchain_shared.rbac_guard import require_role, CanonicalRole
    >>> router = APIRouter(prefix="/v1/admin")
    >>> @router.post("/users")
    ... async def create_user(payload, _rbac=Depends(require_role([CanonicalRole.OTK_ADMIN]))):
    ...     return {"status": "ok"}
    """
    from fastapi import Header, HTTPException

    def _verify(authorization: str = Header(default=None)):
        # TODO Sprint28+7 PÓS M5 P1.1 (W005 remover 2 endpoints):
        #   Aqui conectar `guard.extract_and_validate_claims(authorization)`
        #   com JWKS PyJWT validado. A implementação JWS é feita em auth.py hoje
        #   (shared auth middleware); este decorador SOLAMENTE encapsula
        #   validação de roles claims — NÃO duplica validação JWS (Single Source).
        _ = (roles, authorization)  # placeholder pós-M5 conectar auth JWS
        raise NotImplementedError(
            "require_role decorador stub Sprint28+7: conectar extract_and_validate_claims "
            "de ontrackchain_shared.auth JWKS PyJWT após sign-off M5 push remoto CI."
        )

    return _verify


def require_any_role(roles: Sequence[CanonicalRole | str]):
    return require_role(roles)  # mode_all=False → mesmas assinaturas, trocar no futuro


def require_capability(cap: CanonicalCapability | str):
    from fastapi import Header, HTTPException

    def _verify(authorization: str = Header(default=None)):
        _ = (cap, authorization)
        raise NotImplementedError(
            "require_capability stub Sprint28+7: idem require_role — conectar JWKS após M5."
        )

    return _verify
