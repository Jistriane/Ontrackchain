"""Shared v1.1 — Testes Sprint28+22 (P0.2 backlog independente PGP)

Módulo sob teste: ontrackchain_shared.regulatory_auto_filing.py (58 linhas)
Cobertura: 100% classe + métodos
  ✅ RegulatoryAutoFilingPipeline init default siscoaf_entity_id
  ✅ generate_filing_dossier() retorna todas as 7 chaves esperadas
  ✅ reports total_records correto
  ✅ phase == "P5", status == "READY_FOR_TRANSMISSION"
  ✅ sha256_signature 64 chars hex
  ✅ xml_payload contém batch_id / entity / sha256 attribute
  ✅ receipt_protocol formato PROT_SISCOAF_ + 8 hex upper
"""
from __future__ import annotations

import re

from ontrackchain_shared.regulatory_auto_filing import RegulatoryAutoFilingPipeline


class TestPipelineInit:
    def test_default_entity_id(self):
        p = RegulatoryAutoFilingPipeline()
        assert p.entity_id == "OTC_FINTECH_9613"

    def test_custom_entity_id(self):
        p = RegulatoryAutoFilingPipeline(siscoaf_entity_id="FOO_123")
        assert p.entity_id == "FOO_123"


class TestGenerateFilingDossier:
    @staticmethod
    def _default_pipeline():
        return RegulatoryAutoFilingPipeline(siscoaf_entity_id="TEST_ENT_01")

    def test_returns_all_expected_keys(self):
        p = self._default_pipeline()
        rep = [{"id": 1}, {"id": 2}, {"id": 3}]
        dossier = p.generate_filing_dossier(rep, "Officer Jane")
        for k in ("phase", "batch_id", "sha256_signature", "xml_payload",
                  "json_payload", "status", "receipt_protocol"):
            assert k in dossier, f"missing key {k}"

    def test_total_records_matches_reports_len(self):
        p = self._default_pipeline()
        reports = [{"a": 1} for _ in range(7)]
        d = p.generate_filing_dossier(reports, "X")
        assert d["json_payload"]["total_records"] == 7
        assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in d["xml_payload"]
        assert "<RecordsCount>7</RecordsCount>" in d["xml_payload"]

    def test_phase_and_status_constants(self):
        p = self._default_pipeline()
        d = p.generate_filing_dossier([], "Z")
        assert d["phase"] == "P5"
        assert d["status"] == "READY_FOR_TRANSMISSION"

    def test_sha256_signature_64_hex(self):
        p = self._default_pipeline()
        d = p.generate_filing_dossier([{"r": 1}], "O")
        assert len(d["sha256_signature"]) == 64
        int(d["sha256_signature"], 16)  # hex válido

    def test_xml_payload_contains_entity_and_batch_id(self):
        p = self._default_pipeline()
        d = p.generate_filing_dossier([{"x": 1}], "Officer1")
        batch_id = d["batch_id"]
        entity = p.entity_id
        assert f'<SISCOAFBatch id="{batch_id}" entity="{entity}"' in d["xml_payload"]
        assert f'sha256="{d["sha256_signature"]}"' in d["xml_payload"]
        assert f' officer="Officer1"' in d["xml_payload"]

    def test_receipt_protocol_format(self):
        p = self._default_pipeline()
        d = p.generate_filing_dossier([{"k": "v"}], "Some Officer")
        assert re.fullmatch(r"PROT_SISCOAF_[A-F0-9]{8}", d["receipt_protocol"]) is not None

    def test_json_payload_fields(self):
        p = self._default_pipeline()
        rep = [{"r1": True}]
        d = p.generate_filing_dossier(rep, "Maria")
        j = d["json_payload"]
        assert j["siscoaf_entity_id"] == "TEST_ENT_01"
        assert j["reporting_officer"] == "Maria"
        assert j["jurisdiction"] == "BR_BCB_COAF"
        assert j["regulatory_framework"] == "Lei 9.613/98 | Res. BCB 520"
        assert j["records"] == rep
