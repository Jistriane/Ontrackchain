from __future__ import annotations

from typing import Final


OTK_PREFIX: Final[str] = "OTK_"


CANONICAL_ROLE_TO_OTK: Final[dict[str, str]] = {
    "ADMIN": "OTK_ADMIN",
    "ANALYST": "OTK_ANALYST",
    "AUDITOR": "OTK_AUDITOR",
    "VIEWER": "OTK_VIEWER",
    "COMPLIANCE_OFFICER": "OTK_COMPLIANCE_OFFICER",
    "LEGAL_REVIEWER": "OTK_LEGAL_REVIEWER",
    "TESTER": "OTK_TESTER",
    "REVIEWER": "OTK_REVIEWER",
    "BILLING_ADMIN": "OTK_BILLING_ADMIN",
}

OTK_TO_CANONICAL_ROLE: Final[dict[str, str]] = {
    alias: canonical for canonical, alias in CANONICAL_ROLE_TO_OTK.items()
}

CANONICAL_ROLES: Final[frozenset[str]] = frozenset(CANONICAL_ROLE_TO_OTK.keys())
ALL_ROLE_STRINGS: Final[frozenset[str]] = frozenset(
    list(CANONICAL_ROLE_TO_OTK.keys()) + list(CANONICAL_ROLE_TO_OTK.values())
)


def canonicalize_role(raw_role: object) -> str:
    if raw_role is None:
        return ""
    if isinstance(raw_role, (list, tuple)):
        first = raw_role[0] if raw_role else None
        if first is None:
            return ""
        raw_role = first
    role = str(raw_role).strip()
    if not role:
        return ""
    if role in OTK_TO_CANONICAL_ROLE:
        return OTK_TO_CANONICAL_ROLE[role]
    lower = role.lower()
    if lower in OTK_TO_CANONICAL_ROLE:
        return OTK_TO_CANONICAL_ROLE[lower]
    upper = role.upper()
    if upper in OTK_TO_CANONICAL_ROLE:
        return OTK_TO_CANONICAL_ROLE[upper]
    return upper


def is_otk_role(raw_role: object) -> bool:
    if raw_role is None:
        return False
    role = str(raw_role).strip().upper()
    return role in OTK_TO_CANONICAL_ROLE


def expand_allowed_roles(base_roles: set[str] | frozenset[str] | list[str]) -> set[str]:
    expanded: set[str] = set()
    for r in base_roles:
        role = str(r).strip().upper() if r else ""
        if not role:
            continue
        if role in CANONICAL_ROLES:
            expanded.add(role)
            expanded.add(CANONICAL_ROLE_TO_OTK[role])
        elif role in OTK_TO_CANONICAL_ROLE:
            expanded.add(role)
            expanded.add(OTK_TO_CANONICAL_ROLE[role])
        else:
            expanded.add(role)
    return expanded


__all__ = [
    "OTK_PREFIX",
    "CANONICAL_ROLE_TO_OTK",
    "OTK_TO_CANONICAL_ROLE",
    "CANONICAL_ROLES",
    "ALL_ROLE_STRINGS",
    "canonicalize_role",
    "is_otk_role",
    "expand_allowed_roles",
]
