"""
Ontrackchain - Phase P6: Real-Time Anomaly & Travel Rule Compliance Engine (FATF Rec. 16 / IVMS101)

Validates originator and beneficiary VASP identity data for crypto transfers exceeding statutory thresholds ($1,000 USD / R$ 5,000 BRL).
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Dict, Optional


TRAVEL_RULE_THRESHOLD_BRL = 5000.0


class TravelRuleEngine:
    """Implements FATF Recommendation 16 (IVMS101) VASP-to-VASP Travel Rule data exchange."""

    def evaluate_transfer(
        self,
        amount_brl: float,
        originator_info: Dict,
        beneficiary_info: Dict,
        originator_vasp: str,
        beneficiary_vasp: str,
    ) -> Dict:
        requires_travel_rule = amount_brl >= TRAVEL_RULE_THRESHOLD_BRL

        missing_fields = []
        if requires_travel_rule:
            if not originator_info.get("name"):
                missing_fields.append("originator.name")
            if not originator_info.get("national_id"):
                missing_fields.append("originator.national_id")
            if not beneficiary_info.get("name"):
                missing_fields.append("beneficiary.name")

        is_compliant = len(missing_fields) == 0

        ivms101_payload = {
            "transfer_id": f"tr_{uuid.uuid4().hex[:12]}",
            "originator_vasp": originator_vasp,
            "beneficiary_vasp": beneficiary_vasp,
            "originator": originator_info,
            "beneficiary": beneficiary_info,
            "amount_brl": amount_brl,
        }

        canonical = str(sorted(ivms101_payload.items()))
        ivms_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return {
            "phase": "P6",
            "requires_travel_rule": requires_travel_rule,
            "compliant": is_compliant,
            "missing_fields": missing_fields,
            "ivms101_payload": ivms101_payload,
            "ivms101_hash": ivms_hash,
            "action": "ALLOW_TRANSFER" if is_compliant else "HOLD_FOR_VASP_KYC_EXCHANGE",
        }
