from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from ontrackchain_agents.sanctions_engine import ScreeningResult

logger = logging.getLogger(__name__)


@dataclass
class CounterpartyInput:
    counterparty_type: str
    legal_name: str
    document_type: str
    document_number: str
    document_country: str = "BRA"
    trading_name: Optional[str] = None
    registration_data: dict = field(default_factory=dict)
    beneficial_owners: list[dict] = field(default_factory=list)
    wallet_addresses: list[dict] = field(default_factory=list)
    declared_risk_context: Optional[str] = None


@dataclass
class CounterpartyAssessment:
    risk_level: int
    risk_rationale: str
    kyc_status: str
    sanctions_cleared: bool
    sanctions_hits: list[dict]
    is_pep: bool
    pep_detail: dict
    onchain_risk_score: int
    onchain_analysis: dict
    enhanced_dd_required: bool
    enhanced_dd_status: Optional[str]
    review_frequency_days: int
    next_review_date: date
    status: str
    evidence_hash: str


class CounterpartyAgent:
    """
    Fluxo determinístico de onboarding KYC/KYB.

    Ordem:
      1. Validação documental básica
      2. Screening de sanções
      3. Heurística PEP
      4. Risco on-chain agregado
      5. Classificação final + necessidade de DD aprimorada
    """

    AGENT_ID = "CounterpartyAgent"

    def assess(
        self,
        payload: CounterpartyInput,
        *,
        sanctions_result: ScreeningResult,
        onchain_risk_score: Optional[int] = None,
    ) -> CounterpartyAssessment:
        document_ok = self._document_is_present(payload)
        normalized_onchain_score = max(0, min(int(onchain_risk_score or 0), 100))
        pep_detail = self._infer_pep(payload)
        is_pep = bool(pep_detail)
        sanctions_hits = [
            {
                "list_name": hit.list_name,
                "entity_name": hit.entity_name,
                "confidence": hit.confidence,
                "match_type": hit.match_type,
                "regulatory_basis": hit.regulatory_basis,
            }
            for hit in sanctions_result.hits
        ]
        sanctions_cleared = not sanctions_result.has_hit

        risk_level = 1
        rationale_parts: list[str] = []

        if not document_ok:
            risk_level = max(risk_level, 2)
            rationale_parts.append("documentação incompleta")
        if sanctions_result.has_hit:
            risk_level = 4
            rationale_parts.append("hit em lista de sanções")
        if is_pep:
            risk_level = max(risk_level, 3)
            rationale_parts.append("PEP identificado")
        if normalized_onchain_score >= 80:
            risk_level = max(risk_level, 4)
            rationale_parts.append(f"risco on-chain crítico ({normalized_onchain_score}/100)")
        elif normalized_onchain_score >= 60:
            risk_level = max(risk_level, 3)
            rationale_parts.append(f"risco on-chain elevado ({normalized_onchain_score}/100)")
        elif normalized_onchain_score >= 30:
            risk_level = max(risk_level, 2)
            rationale_parts.append(f"risco on-chain moderado ({normalized_onchain_score}/100)")

        if payload.counterparty_type in {"CONTRAPARTE_DEFI", "EXCHANGE_CEX", "PROVEDOR_LIQUIDEZ"}:
            risk_level = max(risk_level, 2)
            rationale_parts.append("contraparte com exposição operacional ampliada")

        if risk_level == 1:
            rationale_parts.append("baixo risco documental e on-chain")

        if sanctions_result.has_hit:
            kyc_status = "REJECTED"
            status = "BLOCKED"
            enhanced_dd_required = False
            enhanced_dd_status = None
        elif not document_ok:
            kyc_status = "DOCUMENTS_PENDING"
            status = "ACTIVE"
            enhanced_dd_required = False
            enhanced_dd_status = None
        elif risk_level >= 3:
            kyc_status = "ENHANCED_PENDING"
            status = "ACTIVE"
            enhanced_dd_required = True
            enhanced_dd_status = "PENDING"
        else:
            kyc_status = "APPROVED"
            status = "ACTIVE"
            enhanced_dd_required = False
            enhanced_dd_status = None

        review_frequency_days = {1: 365, 2: 180, 3: 90, 4: 30}[risk_level]
        next_review_date = date.today() + timedelta(days=review_frequency_days)

        snapshot = {
            "counterparty_type": payload.counterparty_type,
            "legal_name": payload.legal_name,
            "document_type": payload.document_type,
            "document_number": payload.document_number,
            "wallet_addresses": payload.wallet_addresses,
            "risk_level": risk_level,
            "kyc_status": kyc_status,
            "sanctions_hits": sanctions_hits,
            "is_pep": is_pep,
            "onchain_risk_score": normalized_onchain_score,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        evidence_hash = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()

        return CounterpartyAssessment(
            risk_level=risk_level,
            risk_rationale="; ".join(rationale_parts),
            kyc_status=kyc_status,
            sanctions_cleared=sanctions_cleared,
            sanctions_hits=sanctions_hits,
            is_pep=is_pep,
            pep_detail=pep_detail,
            onchain_risk_score=normalized_onchain_score,
            onchain_analysis={
                "risk_score": normalized_onchain_score,
                "wallet_count": len(payload.wallet_addresses),
                "screened_at": sanctions_result.screened_at,
            },
            enhanced_dd_required=enhanced_dd_required,
            enhanced_dd_status=enhanced_dd_status,
            review_frequency_days=review_frequency_days,
            next_review_date=next_review_date,
            status=status,
            evidence_hash=evidence_hash,
        )

    def _document_is_present(self, payload: CounterpartyInput) -> bool:
        return bool(payload.document_type and payload.document_number and payload.legal_name)

    def _infer_pep(self, payload: CounterpartyInput) -> dict:
        """
        Heurística leve para PEP enquanto a integração externa não existe.
        Prioriza campo explícito em `registration_data.pep`.
        """
        pep_info = payload.registration_data.get("pep")
        if isinstance(pep_info, dict) and pep_info.get("is_pep"):
            return pep_info
        if isinstance(pep_info, bool) and pep_info:
            return {"is_pep": True, "source": "registration_data"}
        return {}
