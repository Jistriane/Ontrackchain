"""
Testes unitários para as Fases Enterprise P4, P5, P6 e P7 do Ontrackchain.
"""

from __future__ import annotations

import unittest

from ontrackchain_agents.bridge_mixer_risk import BridgeMixerRiskEngine
from ontrackchain_shared.regulatory_auto_filing import RegulatoryAutoFilingPipeline
from ontrackchain_agents.travel_rule_engine import TravelRuleEngine
from ontrackchain_agents.ai_dossier_summarizer import AIDossierSummarizer


class EnterprisePhasesTests(unittest.TestCase):
    def test_phase_p4_bridge_mixer_detection(self) -> None:
        engine = BridgeMixerRiskEngine()
        res = engine.analyze_wallet("0x8589427373d6d84e98730d7795d8f6f8731fda16")
        self.assertEqual(res["phase"], "P4")
        self.assertTrue(res["mixer_exposure"])
        self.assertEqual(res["risk_score"], 100)
        self.assertEqual(res["recommendation"], "REJECT")
        self.assertTrue(res["coaf_reporting_required"])

    def test_phase_p5_auto_filing(self) -> None:
        pipeline = RegulatoryAutoFilingPipeline(siscoaf_entity_id="OTC_FINTECH_123")
        reports = [{"case_id": "c1", "wallet": "0x123", "risk": 90}]
        filing = pipeline.generate_filing_dossier(reports, reporting_officer="Officer_Jane")
        self.assertEqual(filing["phase"], "P5")
        self.assertTrue(filing["batch_id"].startswith("coaf_batch_"))
        self.assertTrue(filing["receipt_protocol"].startswith("PROT_SISCOAF_"))
        self.assertIn("SISCOAFBatch", filing["xml_payload"])

    def test_phase_p6_travel_rule(self) -> None:
        engine = TravelRuleEngine()
        originator = {"name": "Alice Silva", "national_id": "123.456.789-00"}
        beneficiary = {"name": "Bob Santos"}

        res = engine.evaluate_transfer(
            amount_brl=10000.0,
            originator_info=originator,
            beneficiary_info=beneficiary,
            originator_vasp="VASP_A",
            beneficiary_vasp="VASP_B",
        )

        self.assertEqual(res["phase"], "P6")
        self.assertTrue(res["requires_travel_rule"])
        self.assertTrue(res["compliant"])
        self.assertEqual(res["action"], "ALLOW_TRANSFER")

    def test_phase_p7_ai_summarizer(self) -> None:
        summarizer = AIDossierSummarizer()
        case_data = {"target_wallet": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", "risk_score": 88}
        evidence = [{"id": "ev1", "sha256": "abc123456"}]

        res = summarizer.summarize_case("CASE_999", case_data, evidence)
        self.assertEqual(res["phase"], "P7")
        self.assertTrue(res["legal_defense_ready"])
        self.assertIn("DOSSIÊ FORENSE AUTOMATIZADO", res["summary_text"])
        self.assertEqual(len(res["dossier_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
