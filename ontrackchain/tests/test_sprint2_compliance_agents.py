from __future__ import annotations

from ontrackchain_agents.coaf_report_agent import CoafReportAgent
from ontrackchain_agents.counterparty_agent import CounterpartyAgent, CounterpartyInput
from ontrackchain_agents.sanctions_engine import ScreeningMatch, ScreeningResult


def _screening_result(*, has_hit: bool, list_name: str = "OFAC_SDN") -> ScreeningResult:
    return ScreeningResult(
        address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        chain="ethereum",
        has_hit=has_hit,
        hits=[
            ScreeningMatch(
                list_name=list_name,
                entity_name="Entity X",
                confidence=0.99,
                match_type="wallet_exact",
                regulatory_basis="BCB 520 Art. 43 §2° V",
            )
        ]
        if has_hit
        else [],
        screened_lists=[list_name] if has_hit else ["OFAC_SDN"],
        screening_duration_ms=12,
    )


def test_counterparty_agent_rejects_sanctions_hit() -> None:
    assessment = CounterpartyAgent().assess(
        CounterpartyInput(
            counterparty_type="CLIENTE_PJ",
            legal_name="Empresa Sancionada",
            document_type="CNPJ",
            document_number="12345678000199",
        ),
        sanctions_result=_screening_result(has_hit=True),
        onchain_risk_score=10,
    )
    assert assessment.risk_level == 4
    assert assessment.kyc_status == "REJECTED"
    assert assessment.status == "BLOCKED"
    assert assessment.sanctions_cleared is False


def test_counterparty_agent_requires_enhanced_dd_for_pep() -> None:
    assessment = CounterpartyAgent().assess(
        CounterpartyInput(
            counterparty_type="CLIENTE_PF",
            legal_name="Pessoa PEP",
            document_type="CPF",
            document_number="12345678901",
            registration_data={"pep": {"is_pep": True, "position": "Senador"}},
        ),
        sanctions_result=_screening_result(has_hit=False),
        onchain_risk_score=20,
    )
    assert assessment.is_pep is True
    assert assessment.risk_level >= 3
    assert assessment.kyc_status == "ENHANCED_PENDING"
    assert assessment.enhanced_dd_required is True


def test_counterparty_agent_approves_low_risk_counterparty() -> None:
    assessment = CounterpartyAgent().assess(
        CounterpartyInput(
            counterparty_type="CLIENTE_PF",
            legal_name="Cliente Baixo Risco",
            document_type="CPF",
            document_number="12345678901",
        ),
        sanctions_result=_screening_result(has_hit=False),
        onchain_risk_score=5,
    )
    assert assessment.risk_level == 1
    assert assessment.kyc_status == "APPROVED"
    assert assessment.status == "ACTIVE"
    assert assessment.review_frequency_days == 365


def test_coaf_report_agent_generates_deterministic_structure() -> None:
    draft = CoafReportAgent().generate(
        ros_id="ros-123",
        case_id="case-456",
        trigger_reason="Contato direto com mixer",
        tipologia_code="TIP_004",
        suspected_amount_brl=12500.0,
        suspected_address="0xabc",
        suspected_chain="ethereum",
    )
    assert draft.title == "ROS/COAF"
    assert draft.content_type == "application/pdf"
    assert "ROS ID: ros-123" in draft.body_text
    assert "Motivo: Contato direto com mixer" in draft.body_text
    assert len(draft.file_hash_sha256) == 64
