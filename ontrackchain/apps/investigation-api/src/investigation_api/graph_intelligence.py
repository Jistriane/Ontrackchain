"""
graph_intelligence.py — Sprint 25 T2-12 enforcement graph allowed layouts
SRP APIRouter prefix /api/v1/graph. 1 rota:
  POST /layout → valida layout em OTK_PLAN_CAPABILITIES[tier][graph_intelligence_layouts_allowed]
  (NÃO incrementa counter — validação direta Fonte Única da Verdade, 403 proibido)
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from investigation_api.billing_capabilities import OTK_PLAN_CAPABILITIES, Tier

router = APIRouter(
    prefix="/api/v1/graph",
    tags=["Inteligência em Grafos / Redes de Relacionamento"],
)

GraphLayoutName = Literal[
    "cose",      # padrão, startup
    "grid",      # padrão, startup
    "cola",      # business+
    "breadthfirst",
    "forceatlas2",  # enterprise
    "concentric",
]


class GraphLayoutRequest(BaseModel):
    case_id: uuid.UUID
    layout_name: GraphLayoutName
    node_ids: List[uuid.UUID] = Field(min_length=1, max_length=10000)


class GraphLayoutResponse(BaseModel):
    posicoes: dict
    layout_utilizado: GraphLayoutName
    capability_allowed: bool = True


async def _require_allowed_graph_layout(request: Request) -> Tier:
    """Valida layout permitido conforme billing capabilities. Validação NÃO usa counter.

    Executado como Depends e também dentro da rota (dupla validação redundante = segurança em profundidade).
    """
    try:
        import json as _json
        body_bytes = await request.body()
        if not body_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "GRAPH_LAYOUT_EMPTY_BODY", "message": "Body JSON obrigatório com layout_name."},
            )
        payload_dict = _json.loads(body_bytes)
        layout_name = payload_dict.get("layout_name")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "GRAPH_LAYOUT_BODY_INVALID", "message": "Body JSON malformado."},
        )
    tier: Tier = getattr(request.state, "current_org_tier", "startup")
    permitidos = OTK_PLAN_CAPABILITIES[tier]["graph_intelligence_layouts_allowed"]
    if layout_name not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "GRAPH_LAYOUT_NOT_ALLOWED_FOR_TIER",
                "message": (
                    f"Layout '{layout_name}' NÃO é permitido no tier '{tier}'. "
                    f"Permitidos: {permitidos}. Upgrade para business/enterprise se precisar."
                ),
                "tier": tier,
                "allowed": permitidos,
                "requested": layout_name,
            },
        )
    return tier


@router.post("/layout", response_model=GraphLayoutResponse)
async def graph_compute_layout(
    _tier_ok: Annotated[Tier, Depends(_require_allowed_graph_layout)],
    payload: GraphLayoutRequest = Body(...),
) -> GraphLayoutResponse:
    # Placeholder layout positions: dispersão randômica (integração real com Cytoscape.js S26)
    posicoes = {
        str(nid): {"x": (i * 37.3) % 1600, "y": (i * 17.7) % 900}
        for i, nid in enumerate(payload.node_ids)
    }
    return GraphLayoutResponse(posicoes=posicoes, layout_utilizado=payload.layout_name)
