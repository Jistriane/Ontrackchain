"""
users_org.py — Sprint 25 T2-12 enforcement max users org
SRP APIRouter prefix /api/v1/users. 1 rota:
  POST /invite → max_users_per_org enforcement (1 = +1 user)
"""
from __future__ import annotations

import re
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, EmailStr, Field

from investigation_api.billing_enforcement import BillingEnforcementResult, enforce_capability

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Usuários por Organização + Onboarding"],
)

# Roles família OTK_* autorizados para invite (SSOT = T2-10 billing capabilities)
ROLES_PERMITIDOS_INVITE = Literal[
    "OTK_ADMIN",
    "OTK_ANALYST",
    "OTK_COMPLIANCE_OFFICER",
    "OTK_AUDITOR",
    "OTK_VIEWER",
]


class UserInviteRequest(BaseModel):
    email: EmailStr
    nome_completo: str = Field(min_length=5, max_length=120)
    role: ROLES_PERMITIDOS_INVITE
    enviar_email_convite: bool = True


class UserInviteResponse(BaseModel):
    convite_id: uuid.UUID
    status: Literal["invited", "ja_existia"] = "invited"
    role_concedida: ROLES_PERMITIDOS_INVITE
    billing_enforcement_debug: dict


_VALID_ROLE = re.compile(r"^OTK_(ADMIN|ANALYST|COMPLIANCE_OFFICER|AUDITOR|VIEWER)$")


@router.post("/invite", response_model=UserInviteResponse)
async def users_org_invite(
    _enforce: Annotated[
        BillingEnforcementResult,
        Depends(lambda r: enforce_capability(r, "max_users_per_org")),
    ],
    payload: UserInviteRequest = Body(...),
) -> UserInviteResponse:
    if not _VALID_ROLE.match(payload.role):  # belt + suspenders
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Role inválida: {payload.role}")
    return UserInviteResponse(
        convite_id=uuid.uuid4(),
        role_concedida=payload.role,
        billing_enforcement_debug={
            "tier": _enforce.tier,
            "used": _enforce.used_after_incr,
            "remaining": _enforce.remaining,
            "engine": _enforce.counter_engine,
        },
    )
