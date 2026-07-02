"""
EvidenceTrailIntegration — Helpers para registrar na evidence_trail
a partir das APIs existentes (investigation-api, compliance-api, report-api).

Filosofia: NÃO refatora o código existente.
Adiciona uma chamada assíncrona em paralelo com os audit_logs existentes.

Uso típico em qualquer API:
    from ontrackchain_agents.evidence_integration import emit_evidence_event

    await emit_evidence_event(
        conn=conn,           # psycopg3 connection (pool.connection())
        org_id=org_id,
        event_type="CASE_CREATED",
        event_payload={
            "case_id": str(case_id),
            "target_address": address,
            "chain": chain,
            "status": "processing",
        },
        actor_user_id=effective_user_id,
        actor_agent_id=None,
        case_id=str(case_id),
        regulatory_basis=["BCB 520 Art. 43 — Início de investigação"],
    )

Tratamento de erros:
    Falhas no registro da evidence_trail são logadas mas NÃO propagadas.
    O fluxo principal da API continua independente de falhas na trilha.
    Isso evita que problemas na evidence_trail interrompam operações críticas.
    Em auditoria, gaps na trilha são detectáveis via verify_chain_integrity().
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from ontrackchain_agents.evidence_trail import EVIDENCE_EVENT_TYPES

logger = logging.getLogger(__name__)

# Alias explícito para preservar o contrato do módulo de integração
# sem duplicar o catálogo canônico de eventos.
VALID_EVENT_TYPES = EVIDENCE_EVENT_TYPES


def _json_safe(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return value


def _compute_event_hash(
    event_type: str,
    org_id: str,
    case_id: Optional[str],
    event_payload,
    actor_user_id: Optional[str],
    actor_agent_id: Optional[str],
    timestamp: str,
) -> str:
    """Calcula SHA-256 determinístico do evento."""
    canonical = {
        "event_type": event_type,
        "org_id": _json_safe(org_id),
        "case_id": _json_safe(case_id),
        "payload": _json_safe(event_payload),
        "actor_user_id": _json_safe(actor_user_id),
        "actor_agent_id": _json_safe(actor_agent_id),
        "timestamp": _json_safe(timestamp),
    }
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def emit_evidence_event_sync(
    cur,
    org_id: str,
    event_type: str,
    event_payload,
    actor_user_id: Optional[str] = None,
    actor_agent_id: Optional[str] = None,
    actor_ip_address: Optional[str] = None,
    case_id: Optional[str] = None,
    regulatory_basis: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Registra evento na evidence_trail de forma síncrona (psycopg3 cursor).

    Usa o cursor já aberto da transação existente — assim o evidence_trail
    entra no mesmo commit do audit_log e do case INSERT/UPDATE.
    Isso garante atomicidade: se o case falha, a evidence_trail também falha.

    Retorna: event_hash (str) ou None se falhar.

    Esta é a função preferida para uso dentro de blocos `with conn.cursor()`.
    """
    if event_type not in VALID_EVENT_TYPES:
        logger.warning(
            "evidence_integration.invalid_event_type",
            extra={"event_type": event_type, "org_id": org_id},
        )
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    event_id = str(uuid4())
    safe_event_payload = _json_safe(event_payload)

    event_hash = _compute_event_hash(
        event_type=event_type,
        org_id=org_id,
        case_id=case_id,
        event_payload=safe_event_payload,
        actor_user_id=actor_user_id,
        actor_agent_id=actor_agent_id,
        timestamp=timestamp,
    )

    try:
        cur.execute(
            """
            INSERT INTO evidence_trail (
                id,
                organization_id,
                case_id,
                event_type,
                event_payload,
                actor_user_id,
                actor_agent_id,
                actor_ip_address,
                event_hash,
                regulatory_basis,
                recorded_at
            )
            VALUES (
                %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                event_id,
                org_id,
                case_id,
                event_type,
                json.dumps(safe_event_payload, ensure_ascii=False),
                actor_user_id,
                actor_agent_id,
                actor_ip_address,
                event_hash,
                regulatory_basis or [],
                timestamp,
            ),
        )
        logger.debug(
            "evidence_integration.recorded",
            extra={
                "event_type": event_type,
                "event_hash": event_hash,
                "org_id": org_id,
                "case_id": case_id,
            },
        )
        return event_hash

    except Exception as exc:
        # Falha na evidence_trail NÃO propaga — auditável via verify_chain_integrity
        logger.error(
            "evidence_integration.insert_failed",
            extra={
                "event_type": event_type,
                "org_id": org_id,
                "case_id": case_id,
                "error": str(exc),
            },
        )
        return None
