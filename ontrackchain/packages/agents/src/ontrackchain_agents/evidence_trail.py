"""
EvidenceTrailService — Trilha de evidências imutável com encadeamento SHA-256.

Base regulatória:
- BCB 520 Art. 45 II: retenção mínima de 5 anos
- IN BCB 739 Art. 1° VIII: registro de operações com identificação completa
- frameworkontrackchain: "Toda ação deve ser auditável: input · agente · decisão · output"

Arquitetura:
- Camada 1 (operacional, MVP): PostgreSQL append-only com encadeamento SHA-256
- Camada 2 (Fase 3, 2027): Âncora pública Stellar/Soroban para relatórios finais

Regra de ouro: esta tabela é INSERT ONLY.
O trigger prevent_evidence_modification() no banco bloqueia UPDATE e DELETE.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# ─── TIPOS DE EVENTOS VÁLIDOS ─────────────────────────────────────────────────
# Deve ser mantido em sincronia com os COMMENTs da migration 0009

EVIDENCE_EVENT_TYPES = {
    # Investigação
    "CASE_CREATED",
    "CASE_UPDATED",
    "INVESTIGATION_STARTED",
    "INVESTIGATION_COMPLETED",
    # Relatórios
    "REPORT_GENERATED",
    "REPORT_DOWNLOADED",
    # Bloqueios preventivos
    "BLOCK_TRIGGERED",       # Genérico (resultado de avaliação)
    "BLOCK_ALLOW",           # Permitido após avaliação completa
    "BLOCK_IMMEDIATE",
    "BLOCK_AND_FREEZE",
    "BLOCK_AND_ALERT",
    "BLOCK_AND_REPORT_COAF",
    "HOLD_AND_REVIEW",
    "HOLD_AND_ESCALATE",
    "HOLD_KYW_REQUIRED",
    "BLOCK_CONFIRMED",
    "BLOCK_LIFTED",
    "ENHANCED_DD",
    # Sanções
    "SANCTIONS_CHECKED",
    "SANCTIONS_HIT",
    # COAF
    "COAF_ROS_GENERATED",
    "COAF_ROS_APPROVED",
    "COAF_ROS_REJECTED",
    "COAF_ROS_SUBMITTED",
    "COAF_ROS_SUBMITTED_MANUAL",
    "COAF_PROTOCOL_REGISTERED",
    # Alertas
    "ALERT_CREATED",
    "ALERT_ACKNOWLEDGED",
    "ALERT_ESCALATED",
    "ALERT_BATCH_ACK",
    # Contrapartes
    "COUNTERPARTY_ONBOARDED",
    "COUNTERPARTY_UPDATED",
    "KYC_APPROVED",
    "KYC_REJECTED",
    "ENHANCED_DD_COMPLETED",
    "PEP_FLAGGED",
    # Exportação e auditoria
    "EVIDENCE_EXPORTED",
    "AUDIT_ACCESSED",
    "CHAIN_INTEGRITY_VERIFIED",
}


@dataclass
class AuthContext:
    """Contexto de autenticação do ator que originou o evento."""
    user_id: Optional[UUID]
    agent_id: Optional[str]    # ex: "PreventiveBlockAgent"
    org_id: UUID
    email: Optional[str] = None
    role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class EvidenceRecord:
    """Registro de evidência retornado após INSERT."""
    id: UUID
    event_hash: str            # SHA-256 do evento
    prev_event_hash: Optional[str]
    recorded_at: str           # ISO 8601 UTC
    event_type: str
    org_id: UUID
    case_id: Optional[UUID]


def _compute_event_hash(
    event_type: str,
    org_id: UUID,
    case_id: Optional[UUID],
    event_payload: dict,
    actor_user_id: Optional[UUID],
    actor_agent_id: Optional[str],
    timestamp: str,
) -> str:
    """
    Função de módulo para calcular SHA-256 de evento de forma determinística.
    Delega ao método estático da classe para manter single-source-of-truth.
    """
    canonical = {
        "event_type": event_type,
        "org_id": str(org_id),
        "case_id": str(case_id) if case_id else None,
        "payload": event_payload,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_agent_id": actor_agent_id,
        "timestamp": timestamp,
    }
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class EvidenceTrailService:
    """
    Serviço de trilha de evidências imutável.

    Uso:
        svc = EvidenceTrailService(db)
        event_hash = await svc.record_event(
            org_id=org_id,
            event_type="BLOCK_IMMEDIATE",
            event_payload={"address": "0x...", "chain": "ethereum"},
            auth=auth_ctx,
            case_id=case_id,
            regulatory_basis=["BCB 520 Art. 43 §2° V", "Lei 13.810/2019"],
        )

    Encadeamento SHA-256:
        event_hash_N = SHA256(
            event_type + org_id + case_id + payload + actor + timestamp
        )
        O trigger set_evidence_chain() no banco preenche prev_event_hash
        automaticamente com o event_hash do evento anterior da mesma org.

    Integridade:
        verify_chain_integrity() percorre todos os eventos da organização
        em ordem cronológica e verifica se o encadeamento está íntegro.
        Qualquer supressão ou reordenação é detectada.
    """

    def __init__(self, db) -> None:
        # db: AsyncSession (psycopg/SQLAlchemy) ou ConnectionPool (psycopg3)
        # Aceita ambos para compatibilidade com o padrão do projeto
        self._db = db

    # ─── CÁLCULO DO HASH ──────────────────────────────────────────────────────

    @staticmethod
    def _compute_event_hash(
        event_type: str,
        org_id: UUID,
        case_id: Optional[UUID],
        event_payload: dict,
        actor_user_id: Optional[UUID],
        actor_agent_id: Optional[str],
        timestamp: str,
    ) -> str:
        """
        Calcula SHA-256 do evento de forma determinística.
        A ordem dos campos é fixa — qualquer alteração produz hash diferente.
        Isso garante que o payload não pode ser adulterado sem invalidar o hash.
        """
        canonical = {
            "event_type": event_type,
            "org_id": str(org_id),
            "case_id": str(case_id) if case_id else None,
            "payload": event_payload,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
            "actor_agent_id": actor_agent_id,
            "timestamp": timestamp,
        }
        serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ─── REGISTRO DE EVENTO ───────────────────────────────────────────────────

    async def record_event(
        self,
        org_id: UUID,
        event_type: str,
        event_payload: dict,
        auth: AuthContext,
        case_id: Optional[UUID] = None,
        regulatory_basis: Optional[list[str]] = None,
    ) -> str:
        """
        Registra evento na trilha de evidências.

        Retorna: event_hash (SHA-256) para referência e linkagem.

        O trigger set_evidence_chain() preenche prev_event_hash automaticamente.
        O trigger prevent_evidence_modification() impede UPDATE e DELETE.

        Raises:
            ValueError: se event_type não é válido
            Exception: se o INSERT falhar (relançado para o caller tratar)
        """
        if event_type not in EVIDENCE_EVENT_TYPES:
            raise ValueError(
                f"event_type '{event_type}' não é válido. "
                f"Use um dos: {sorted(EVIDENCE_EVENT_TYPES)}"
            )

        timestamp = datetime.now(timezone.utc).isoformat()

        event_hash = self._compute_event_hash(
            event_type=event_type,
            org_id=org_id,
            case_id=case_id,
            event_payload=event_payload,
            actor_user_id=auth.user_id,
            actor_agent_id=auth.agent_id,
            timestamp=timestamp,
        )

        # Em caso de colisão de hash (extremamente improvável), adiciona uuid
        # para garantir unicidade (constraint UNIQUE no event_hash)
        event_id = uuid4()

        try:
            await self._db.execute(
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
                    actor_user_agent,
                    event_hash,
                    regulatory_basis,
                    recorded_at
                )
                VALUES (
                    %(id)s,
                    %(org_id)s,
                    %(case_id)s,
                    %(event_type)s,
                    %(payload)s,
                    %(user_id)s,
                    %(agent_id)s,
                    %(ip_address)s,
                    %(user_agent)s,
                    %(event_hash)s,
                    %(regulatory_basis)s,
                    %(recorded_at)s
                )
                """,
                {
                    "id": str(event_id),
                    "org_id": str(org_id),
                    "case_id": str(case_id) if case_id else None,
                    "event_type": event_type,
                    "payload": json.dumps(event_payload, ensure_ascii=False),
                    "user_id": str(auth.user_id) if auth.user_id else None,
                    "agent_id": auth.agent_id,
                    "ip_address": auth.ip_address,
                    "user_agent": auth.user_agent,
                    "event_hash": event_hash,
                    "regulatory_basis": regulatory_basis or [],
                    "recorded_at": timestamp,
                },
            )

            logger.info(
                "evidence_trail.recorded",
                extra={
                    "event_type": event_type,
                    "event_hash": event_hash,
                    "org_id": str(org_id),
                    "case_id": str(case_id) if case_id else None,
                    "actor_user_id": str(auth.user_id) if auth.user_id else None,
                    "actor_agent_id": auth.agent_id,
                },
            )

        except Exception as exc:
            logger.error(
                "evidence_trail.insert_failed",
                extra={
                    "event_type": event_type,
                    "org_id": str(org_id),
                    "error": str(exc),
                },
            )
            raise

        return event_hash

    # ─── VERIFICAÇÃO DE INTEGRIDADE ───────────────────────────────────────────

    async def verify_chain_integrity(
        self,
        org_id: UUID,
    ) -> dict:
        """
        Verifica se a cadeia de hashes está íntegra para uma organização.

        Percorre todos os eventos em ordem cronológica e valida que:
        1. prev_event_hash de cada evento == event_hash do evento anterior
        2. Nenhum evento foi suprimido ou reordenado

        Retorna dict com:
        - chain_intact: bool
        - total_events: int
        - broken_links: lista de eventos com cadeia quebrada
        - verified_at: ISO 8601

        Uso típico: auditoria BCB, exportação de evidências, COAF.
        """
        rows = await self._db.fetch(
            """
            SELECT
                id,
                event_type,
                event_hash,
                prev_event_hash,
                recorded_at,
                chain_integrity_ok
            FROM evidence_trail
            WHERE organization_id = %(org_id)s
            ORDER BY recorded_at ASC, id ASC
            """,
            {"org_id": str(org_id)},
        )

        broken_links = []
        expected_prev_hash: Optional[str] = None

        for row in rows:
            found_prev = row["prev_event_hash"]
            if found_prev != expected_prev_hash:
                broken_links.append({
                    "event_id": str(row["id"]),
                    "event_type": row["event_type"],
                    "recorded_at": row["recorded_at"].isoformat()
                    if hasattr(row["recorded_at"], "isoformat")
                    else str(row["recorded_at"]),
                    "expected_prev_hash": expected_prev_hash,
                    "found_prev_hash": found_prev,
                    "diagnosis": (
                        "Primeiro evento — prev_hash deveria ser NULL"
                        if expected_prev_hash is None
                        else "Cadeia quebrada — possível supressão ou adulteração de evento"
                    ),
                })
            expected_prev_hash = row["event_hash"]

        result = {
            "org_id": str(org_id),
            "total_events": len(rows),
            "chain_intact": len(broken_links) == 0,
            "broken_links": broken_links,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "regulatory_basis": [
                "BCB 520 Art. 45 II — integridade de registros",
                "IN BCB 739 Art. 1° VIII — verificação de registros de operações",
            ],
        }

        # Registra o próprio resultado da verificação na trilha
        # (para que auditorias BCB possam ver quando foi verificado)
        try:
            verify_auth = AuthContext(
                user_id=None,
                agent_id="EvidenceTrailService.verify_chain_integrity",
                org_id=org_id,
            )
            await self.record_event(
                org_id=org_id,
                event_type="CHAIN_INTEGRITY_VERIFIED",
                event_payload={
                    "total_events": result["total_events"],
                    "chain_intact": result["chain_intact"],
                    "broken_links_count": len(broken_links),
                },
                auth=verify_auth,
                regulatory_basis=[
                    "BCB 520 Art. 45 II",
                    "IN BCB 739 Art. 1° VIII",
                ],
            )
        except Exception as exc:
            # Não falha a verificação se o registro da verificação falhar
            logger.warning(
                "evidence_trail.verify_self_record_failed",
                extra={"error": str(exc)},
            )

        return result

    # ─── BUSCA DE EVENTOS ─────────────────────────────────────────────────────

    async def get_case_events(
        self,
        org_id: UUID,
        case_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Retorna todos os eventos de um caso em ordem cronológica.
        Usado por: CoafReportAgent, relatórios forenses, exportação.
        """
        rows = await self._db.fetch(
            """
            SELECT
                id,
                event_type,
                event_payload,
                actor_user_id,
                actor_agent_id,
                event_hash,
                prev_event_hash,
                chain_integrity_ok,
                recorded_at,
                retain_until,
                regulatory_basis,
                soroban_tx_hash
            FROM evidence_trail
            WHERE organization_id = %(org_id)s
              AND case_id = %(case_id)s
            ORDER BY recorded_at ASC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {"org_id": str(org_id), "case_id": str(case_id),
             "limit": limit, "offset": offset},
        )

        return [dict(row) for row in rows]

    async def get_event_by_hash(
        self,
        event_hash: str,
    ) -> Optional[dict]:
        """
        Busca evento específico pelo SHA-256.
        Usado para verificação pontual e linkagem de registros.
        """
        row = await self._db.fetchrow(
            """
            SELECT *
            FROM evidence_trail
            WHERE event_hash = %(event_hash)s
            """,
            {"event_hash": event_hash},
        )
        return dict(row) if row else None
