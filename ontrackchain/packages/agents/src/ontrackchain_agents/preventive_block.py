"""
PreventiveBlockAgent — Stage 2 do sistema de bloqueio preventivo.

Arquitetura de 2 estágios (conforme ADR do .odt):
  Stage 1 (Traefik/Redis, < 50ms): pre_screening.py — hits OFAC óbvios
  Stage 2 (Backend, < 500ms): este módulo — decisão completa + trilha auditável

Base regulatória:
  - BCB 520 Art. 43 §2° VI: bloqueios para transações atípicas ou suspeitas
  - BCB 520 Art. 43 §2° V: listas de sanções (CSNU, OFAC, EU, COAF)
  - BCB 520 Art. 90 III: veda mixers/embaralhadores
  - Lei 13.810/2019: indisponibilidade imediata para hits CSNU
  - Lei 9.613/98 Art. 11: obrigação de comunicação ao COAF
  - BCB 521 Art. 76-A §5°: identificação de carteira autocustodiada
  - IN BCB 739 Art. 1° VII: bloqueio administrativo de ativos

Modelo de IA: WORKER tier (Haiku 4.5) — latência < 500ms P95
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from ontrackchain_agents.evidence_trail import AuthContext, EvidenceTrailService

logger = logging.getLogger(__name__)

# ─── TIPOS DE DADOS ───────────────────────────────────────────────────────────


@dataclass
class SanctionsHit:
    """Hit individual em lista de sanções."""
    list_name: str          # OFAC_SDN | UN_CSNU | EU_CONSOLIDATED | COAF_INTERNAL
    entity_name: str
    confidence: float       # 0.0 a 1.0
    designation_date: Optional[str] = None
    regulatory_basis: str = ""


@dataclass
class SanctionsResult:
    """Resultado do screening de sanções para um endereço."""
    address: str
    chain: str
    has_hit: bool
    hits: list[SanctionsHit] = field(default_factory=list)
    screened_lists: list[str] = field(default_factory=list)
    screening_duration_ms: int = 0


@dataclass
class WalletContext:
    """Contexto da carteira avaliada."""
    address: str
    chain: str
    is_self_custody: bool = False
    owner_identified: bool = True
    is_international_transfer: bool = False
    has_direct_mixer_contact: bool = False
    has_chain_hopping: bool = False           # Chain hop em < 5 minutos
    structuring_detected: bool = False        # Múltiplas tx abaixo de threshold
    aml_score: int = 0                        # 0-100


@dataclass
class BlockDecision:
    """Decisão de bloqueio produzida pelo PreventiveBlockAgent."""
    address: str
    chain: str
    action: str                               # Ver BLOCK_ACTIONS abaixo
    regulatory_basis: list[str] = field(default_factory=list)
    requires_coaf_report: bool = False
    decision_confidence: float = 1.0
    analysis_context: dict = field(default_factory=dict)
    evidence_hash: Optional[str] = None      # Hash registrado na evidence_trail
    block_id: Optional[UUID] = None          # ID na tabela preventive_blocks
    decision_timestamp: str = ""
    redis_blocklist_updated: bool = False


# ─── CONSTANTES DE AÇÃO ───────────────────────────────────────────────────────

BLOCK_ACTIONS = {
    "ALLOW":                 "Permitido após avaliação completa (registrado para auditoria)",
    "BLOCK_IMMEDIATE":       "Bloqueio imediato — sem intervenção humana",
    "BLOCK_AND_FREEZE":      "Bloqueio + indisponibilidade patrimonial (CSNU)",
    "BLOCK_AND_ALERT":       "Bloqueio + alerta ao analista em < 15min",
    "BLOCK_AND_REPORT_COAF": "Bloqueio + ROS automático ao COAF (24h)",
    "HOLD_AND_REVIEW":       "Suspensão temporária — revisão em 24h",
    "HOLD_AND_ESCALATE":     "Suspensão + escalonamento ao Compliance Officer",
    "HOLD_KYW_REQUIRED":     "Suspensão até KYW completo do proprietário (BCB 521)",
    "ENHANCED_DD":           "Permite com Due Diligence aprimorada (PEP flag)",
}

# Ações que atualizam a blocklist Redis (Stage 1 próximos requests)
REDIS_BLOCKLIST_ACTIONS = {"BLOCK_IMMEDIATE", "BLOCK_AND_FREEZE"}

# Ações que requerem notificação imediata ao Compliance Officer
COAF_REQUIRED_ACTIONS = {"BLOCK_AND_REPORT_COAF", "BLOCK_AND_FREEZE"}

# Limiares de confiança por lista
CONFIDENCE_THRESHOLDS = {
    "UN_CSNU":        0.90,   # Indisponibilidade imediata (Lei 13.810/2019)
    "OFAC_SDN":       0.95,   # Bloqueio imediato (alta confiança)
    "EU_CONSOLIDATED": 0.90,
    "COAF_INTERNAL":  0.90,
    "OPENSANCTIONS":  0.85,
}


class PreventiveBlockAgent:
    """
    Agente de bloqueio preventivo — Stage 2.

    Avalia endereços/transações em tempo real e produz decisões de bloqueio
    regulatoriamente defensáveis com trilha completa de auditoria.

    Prioridades de avaliação (da mais grave para a menos grave):
      P1: Sanções CSNU → BLOCK_AND_FREEZE (Lei 13.810/2019)
      P2: OFAC direto  → BLOCK_IMMEDIATE (BCB 520 Art. 43 §2° V)
      P3: Score AML >= 80 → BLOCK_AND_ALERT (BCB 520 Art. 43 §2° VI)
      P4: Mixer direto → BLOCK_AND_REPORT_COAF (BCB 520 Art. 90 III)
      P5: Autocustódia não identificada em tx internacional
          → HOLD_KYW_REQUIRED (BCB 521 Art. 76-A §5°)

    Ações restantes:
      PEP flag → ENHANCED_DD (BCB 520 Art. 58)
      ALLOW → registrado para auditoria (sem bloqueio)
    """

    AGENT_ID = "PreventiveBlockAgent"
    TIER = "WORKER"          # Haiku 4.5 — latência < 500ms
    TIMEOUT_MS = 450         # Hard limit antes do SLA de 500ms

    def __init__(
        self,
        evidence_svc: EvidenceTrailService,
        redis_client=None,        # redis.asyncio.Redis — opcional (Stage 1 sync)
        db=None,                  # AsyncSession — para INSERT em preventive_blocks
    ) -> None:
        self._evidence_svc = evidence_svc
        self._redis = redis_client
        self._db = db

    # ─── AVALIAÇÃO PRINCIPAL ──────────────────────────────────────────────────

    async def evaluate(
        self,
        wallet_context: WalletContext,
        sanctions_result: SanctionsResult,
        auth: AuthContext,
        case_id: Optional[UUID] = None,
    ) -> BlockDecision:
        """
        Avalia se um endereço/transação deve ser bloqueado.

        Sempre registra na evidence_trail, independente da decisão (ALLOW ou BLOCK).
        Isso garante que a ausência de bloqueio também é auditável.

        Returns: BlockDecision com action e regulatory_basis preenchidos.
        """
        decision = BlockDecision(
            address=wallet_context.address,
            chain=wallet_context.chain,
            action="ALLOW",
            decision_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # ── P1: Sanções CSNU (Lei 13.810/2019 — indisponibilidade imediata) ───
        for hit in sanctions_result.hits:
            if (
                hit.list_name == "UN_CSNU"
                and hit.confidence >= CONFIDENCE_THRESHOLDS["UN_CSNU"]
            ):
                decision.action = "BLOCK_AND_FREEZE"
                decision.requires_coaf_report = True
                decision.decision_confidence = hit.confidence
                decision.regulatory_basis.extend([
                    "Lei 13.810/2019 Art. 1° — Indisponibilidade imediata CSNU",
                    "BCB 520 Art. 43 §2° V — Lista CSNU/ONU",
                    "IN BCB 739 Art. 1° VII a.1 — Bloqueio administrativo",
                ])
                decision.analysis_context["csnu_hit"] = {
                    "entity": hit.entity_name,
                    "confidence": hit.confidence,
                    "date": hit.designation_date,
                }
                logger.warning(
                    "preventive_block.csnu_hit",
                    extra={"address": wallet_context.address, "entity": hit.entity_name},
                )
                break

        # ── P2: OFAC direto (sem CSNU) ────────────────────────────────────────
        if decision.action == "ALLOW":
            for hit in sanctions_result.hits:
                if (
                    hit.list_name == "OFAC_SDN"
                    and hit.confidence >= CONFIDENCE_THRESHOLDS["OFAC_SDN"]
                ):
                    decision.action = "BLOCK_IMMEDIATE"
                    decision.decision_confidence = hit.confidence
                    decision.regulatory_basis.extend([
                        "BCB 520 Art. 43 §2° V — Lista OFAC/SDN",
                        "IN BCB 739 Art. 1° VII a.1 — Bloqueio administrativo",
                    ])
                    decision.analysis_context["ofac_hit"] = {
                        "entity": hit.entity_name,
                        "confidence": hit.confidence,
                    }
                    break

        # ── P3: Score AML crítico (BCB 520 Art. 43 §2° VI) ───────────────────
        if decision.action == "ALLOW" and wallet_context.aml_score >= 80:
            decision.action = "BLOCK_AND_ALERT"
            decision.decision_confidence = min(
                wallet_context.aml_score / 100.0, 0.99
            )
            decision.regulatory_basis.extend([
                f"BCB 520 Art. 43 §2° VI — Score AML {wallet_context.aml_score}/100 (crítico ≥80)",
                "BCB 520 Art. 45 III — Operação suspeita",
            ])
            decision.analysis_context["aml_score"] = wallet_context.aml_score

        # ── P4: Contato direto com mixer (BCB 520 Art. 90 III) ───────────────
        if decision.action == "ALLOW" and wallet_context.has_direct_mixer_contact:
            decision.action = "BLOCK_AND_REPORT_COAF"
            decision.requires_coaf_report = True
            decision.regulatory_basis.extend([
                "BCB 520 Art. 90 III — Uso de mixer/embaralhador expressamente vedado",
                "Lei 9.613/98 Art. 11 — Obrigação de comunicação ao COAF",
            ])
            decision.analysis_context["mixer_contact"] = True

        # ── P5: Autocustódia não identificada em transferência internacional ──
        if (
            decision.action == "ALLOW"
            and wallet_context.is_self_custody
            and not wallet_context.owner_identified
            and wallet_context.is_international_transfer
        ):
            decision.action = "HOLD_KYW_REQUIRED"
            decision.regulatory_basis.extend([
                "BCB 521 Art. 76-A §5° — Identificação obrigatória do proprietário "
                "de carteira autocustodiada em transferência internacional",
                "IN BCB 739 Art. 1° III — Procedimentos KYC",
            ])
            decision.analysis_context["selfcustody_unidentified"] = True

        # ── Chain hopping rápido ───────────────────────────────────────────────
        if decision.action == "ALLOW" and wallet_context.has_chain_hopping:
            decision.action = "HOLD_AND_REVIEW"
            decision.regulatory_basis.extend([
                "BCB 520 Art. 43 §2° VI — Padrão atípico: chain hopping em < 5min",
            ])
            decision.analysis_context["chain_hopping"] = True

        # ── Structuring ────────────────────────────────────────────────────────
        if decision.action == "ALLOW" and wallet_context.structuring_detected:
            decision.action = "HOLD_AND_ESCALATE"
            decision.regulatory_basis.extend([
                "BCB 520 Art. 43 §2° VI — Structuring/fracionamento detectado",
                "Lei 9.613/98 Art. 11 — Indício de ocultação de origem",
            ])
            decision.analysis_context["structuring"] = True

        # ── PEP (sem bloqueio — Due Diligence aprimorada) ─────────────────────
        # Verifica hits PEP nas listas (não bloqueia, mas eleva DD)
        if decision.action == "ALLOW":
            pep_hits = [h for h in sanctions_result.hits if h.list_name not in {
                "OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED"
            }]
            if pep_hits:
                decision.action = "ENHANCED_DD"
                decision.regulatory_basis.extend([
                    "BCB 520 Art. 58 — PEP identificado — Due Diligence aprimorada obrigatória",
                ])
                decision.analysis_context["pep_detected"] = True

        # ─── REGISTRA NA evidence_trail (SEMPRE, inclusive ALLOW) ─────────────
        agent_auth = AuthContext(
            user_id=auth.user_id,
            agent_id=self.AGENT_ID,
            org_id=auth.org_id,
            ip_address=auth.ip_address,
        )

        # O event_type espelha o block_action para facilitar filtragem na auditoria
        event_type = decision.action if decision.action in {
            "BLOCK_IMMEDIATE", "BLOCK_AND_FREEZE", "BLOCK_AND_ALERT",
            "BLOCK_AND_REPORT_COAF", "HOLD_AND_REVIEW", "HOLD_AND_ESCALATE",
            "HOLD_KYW_REQUIRED", "ENHANCED_DD",
        } else "BLOCK_ALLOW"

        decision.evidence_hash = await self._evidence_svc.record_event(
            org_id=auth.org_id,
            event_type=event_type,
            event_payload={
                "address": wallet_context.address,
                "chain": wallet_context.chain,
                "action": decision.action,
                "aml_score": wallet_context.aml_score,
                "sanctions_hits": [
                    {
                        "list": h.list_name,
                        "entity": h.entity_name,
                        "confidence": h.confidence,
                    }
                    for h in sanctions_result.hits
                ],
                "requires_coaf": decision.requires_coaf_report,
                "regulatory_basis": decision.regulatory_basis,
                "analysis_context": decision.analysis_context,
                "decision_confidence": decision.decision_confidence,
                "is_self_custody": wallet_context.is_self_custody,
                "has_mixer_contact": wallet_context.has_direct_mixer_contact,
            },
            auth=agent_auth,
            case_id=case_id,
            regulatory_basis=decision.regulatory_basis or [
                "BCB 520 Art. 43 — Avaliação de transação (ALLOW)"
            ],
        )

        # ─── PERSISTE EM preventive_blocks ────────────────────────────────────
        if self._db and decision.action != "ALLOW":
            decision.block_id = await self._persist_block(
                decision=decision,
                wallet_context=wallet_context,
                sanctions_result=sanctions_result,
                auth=auth,
                case_id=case_id,
            )

        # ─── ATUALIZA BLOCKLIST REDIS (Stage 1 sync) ──────────────────────────
        if self._redis and decision.action in REDIS_BLOCKLIST_ACTIONS:
            await self._update_redis_blocklist(
                address=wallet_context.address,
                chain=wallet_context.chain,
            )
            decision.redis_blocklist_updated = True

        logger.info(
            "preventive_block.decision",
            extra={
                "action": decision.action,
                "address": wallet_context.address,
                "chain": wallet_context.chain,
                "aml_score": wallet_context.aml_score,
                "evidence_hash": decision.evidence_hash,
                "requires_coaf": decision.requires_coaf_report,
            },
        )

        return decision

    # ─── PERSISTÊNCIA ─────────────────────────────────────────────────────────

    async def _persist_block(
        self,
        decision: BlockDecision,
        wallet_context: WalletContext,
        sanctions_result: SanctionsResult,
        auth: AuthContext,
        case_id: Optional[UUID],
    ) -> UUID:
        """Persiste o bloqueio na tabela preventive_blocks."""
        # Calcula evidence_hash para o snapshot do bloqueio
        snapshot = {
            "address": wallet_context.address,
            "chain": wallet_context.chain,
            "action": decision.action,
            "aml_score": wallet_context.aml_score,
            "sanctions_hits": len(sanctions_result.hits),
            "timestamp": decision.decision_timestamp,
        }
        block_evidence_hash = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True).encode()
        ).hexdigest()

        block_id = uuid4()

        db = self._db
        assert db is not None, "db não configurado no PreventiveBlockAgent"
        await db.execute(
            """
            INSERT INTO preventive_blocks (
                id, organization_id, case_id,
                target_address, target_chain,
                block_action, block_stage, block_triggers,
                regulatory_basis, aml_score_at_block,
                sanctions_hits, decision_confidence,
                analysis_context, triggered_by_agent,
                coaf_ros_required, evidence_hash,
                evidence_trail_event_hash
            )
            VALUES (
                %(id)s, %(org_id)s, %(case_id)s,
                %(address)s, %(chain)s,
                %(action)s, 'backend', %(triggers)s,
                %(regulatory_basis)s, %(aml_score)s,
                %(sanctions_hits)s, %(confidence)s,
                %(analysis_context)s, %(agent)s,
                %(coaf_required)s, %(evidence_hash)s,
                %(evidence_trail_hash)s
            )
            """,
            {
                "id": str(block_id),
                "org_id": str(auth.org_id),
                "case_id": str(case_id) if case_id else None,
                "address": wallet_context.address,
                "chain": wallet_context.chain,
                "action": decision.action,
                "triggers": json.dumps(list(decision.analysis_context.keys())),
                "regulatory_basis": decision.regulatory_basis,
                "aml_score": wallet_context.aml_score,
                "sanctions_hits": json.dumps([
                    {"list": h.list_name, "entity": h.entity_name,
                     "confidence": h.confidence}
                    for h in sanctions_result.hits
                ]),
                "confidence": decision.decision_confidence,
                "analysis_context": json.dumps(decision.analysis_context),
                "agent": self.AGENT_ID,
                "coaf_required": decision.requires_coaf_report,
                "evidence_hash": block_evidence_hash,
                "evidence_trail_hash": decision.evidence_hash,
            },
        )

        return block_id

    # ─── REDIS BLOCKLIST (Stage 1 sync) ───────────────────────────────────────

    async def _update_redis_blocklist(
        self,
        address: str,
        chain: str,
        ttl_seconds: int = 900,  # 15 minutos de cache
    ) -> None:
        """
        Adiciona endereço à blocklist Redis para Stage 1 (Traefik ForwardAuth).
        TTL de 15 minutos — SanctionsAgent faz sync completo a cada 6h (OFAC).
        Endereços com BLOCK_IMMEDIATE permanecem bloqueados até refresh.
        """
        if not self._redis:
            return
        try:
            key = f"otk:blocklist:confirmed:{chain}"
            await self._redis.sadd(key, address.lower())
            # Garante TTL no set (não por membro — limitação do Redis)
            await self._redis.expire(key, ttl_seconds)
            logger.info(
                "preventive_block.redis_blocklist_updated",
                extra={"address": address, "chain": chain, "key": key},
            )
        except Exception as exc:
            # Falha no Redis não deve impedir o bloqueio no banco
            logger.error(
                "preventive_block.redis_update_failed",
                extra={"error": str(exc), "address": address},
            )
