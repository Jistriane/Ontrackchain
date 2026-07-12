from __future__ import annotations

import asyncio
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    main: Any = importlib.import_module("compliance_api.main")
    MAIN_IMPORT_AVAILABLE = True
except ModuleNotFoundError:
    main = None
    MAIN_IMPORT_AVAILABLE = False


@unittest.skipUnless(MAIN_IMPORT_AVAILABLE, "compliance_api.main dependencies not installed in current interpreter")
class ComplianceEndpointContractTests(unittest.TestCase):
    def test_kyc_wallet_uses_provider_contract_and_records_optional_audit(self) -> None:
        outcome = SimpleNamespace(
            provider_name="trm_labs",
            provider_status="live",
            degraded_reason=None,
            risk_score=87,
            dimensions=None,
            raw_payload={},
            latency_ms=12,
            retries_used=0,
            score_source="provider_live",
            upstream_status_code=200,
            screening_host="provider.example",
            request_id_forwarded=True,
        )

        with (
            patch.object(main, "screen_address", return_value=outcome),
            patch.object(main, "_record_optional_compliance_audit") as audit_mock,
        ):
            response = asyncio.run(
                main.kyc_wallet(
                    main.KycWalletRequest(address="0xabc", chain="ethereum"),
                    pool=object(),
                    x_org_id="org-1",
                    x_user_id="user-1",
                    x_request_id="req-kyc-1",
                )
            )

        self.assertEqual(response.address, "0xabc")
        self.assertEqual(response.chain, "ethereum")
        self.assertEqual(response.provider, "trm_labs")
        self.assertEqual(response.provider_status, "live")
        self.assertEqual(response.capability_status, "live")
        self.assertEqual(response.risk_score, 87)
        self.assertEqual(response.recommendation, "ESCALATE")
        self.assertEqual(response.aml_flags, [])
        self.assertIsNone(response.report_id)
        audit_mock.assert_called_once()
        metadata = audit_mock.call_args.kwargs["metadata"]
        self.assertEqual(metadata["provider_status"], "live")
        self.assertEqual(metadata["capability_status"], "live")
        self.assertEqual(metadata["recommendation"], "ESCALATE")

    def test_due_diligence_returns_explicit_manual_review_contract(self) -> None:
        with patch.object(main, "_record_optional_compliance_audit") as audit_mock:
            response = asyncio.run(
                main.due_diligence(
                    main.DueDiligenceRequest(
                        address="0xdef",
                        chain="polygon",
                        counterparty_context="exchange settlement",
                    ),
                    pool=object(),
                    x_org_id="org-1",
                    x_request_id="req-dd-1",
                )
            )

        self.assertEqual(response.address, "0xdef")
        self.assertEqual(response.chain, "polygon")
        self.assertEqual(response.provider, "manual_review")
        self.assertEqual(response.provider_status, "degraded")
        self.assertEqual(response.degraded_reason, "manual_review_required")
        self.assertEqual(response.capability_status, "degraded")
        self.assertIsNone(response.dd_score)
        self.assertEqual(response.red_flags, [])
        self.assertIsNone(response.comfort_level)
        audit_mock.assert_called_once()
        metadata = audit_mock.call_args.kwargs["metadata"]
        self.assertEqual(metadata["delivery_mode"], "manual_review_pending")
        self.assertTrue(metadata["counterparty_context_present"])

    def test_source_of_funds_returns_manual_review_payload_without_fake_percentages(self) -> None:
        with patch.object(main, "_record_optional_compliance_audit") as audit_mock:
            response = asyncio.run(
                main.source_of_funds(
                    main.SourceOfFundsRequest(
                        address="0x123",
                        chain="arbitrum",
                        amount=1200.5,
                        purpose="treasury top-up",
                    ),
                    pool=object(),
                    x_org_id="org-1",
                    x_request_id="req-sof-1",
                )
            )

        self.assertEqual(response.address, "0x123")
        self.assertEqual(response.chain, "arbitrum")
        self.assertEqual(response.provider, "manual_review")
        self.assertEqual(response.provider_status, "degraded")
        self.assertEqual(response.degraded_reason, "manual_review_required")
        self.assertEqual(response.capability_status, "degraded")
        self.assertEqual(
            response.origin_analysis,
            {
                "status": "manual_review_pending",
                "requires_human_review": True,
            },
        )
        self.assertIsNone(response.suspicious_pct)
        self.assertIsNone(response.clean_pct)
        audit_mock.assert_called_once()
        metadata = audit_mock.call_args.kwargs["metadata"]
        self.assertEqual(metadata["amount"], 1200.5)
        self.assertEqual(metadata["purpose"], "treasury top-up")

    def test_sanctions_check_returns_live_local_cache_capability(self) -> None:
        with patch.object(main, "_record_optional_compliance_audit") as audit_mock:
            response = asyncio.run(
                main.sanctions_check(
                    address="0x456",
                    pool=object(),
                    chain="base",
                    lists="OFAC, UN ,COAF",
                    x_org_id="org-1",
                    x_request_id="req-sanctions-1",
                )
            )

        self.assertEqual(response.address, "0x456")
        self.assertEqual(response.chain, "base")
        self.assertEqual(response.provider, "sanctions_lists_cache")
        self.assertEqual(response.provider_status, "live")
        self.assertIsNone(response.degraded_reason)
        self.assertEqual(response.capability_status, "live")
        self.assertEqual(response.lists, ["OFAC", "UN", "COAF"])
        self.assertIsNone(response.hit)
        self.assertEqual(response.matched_lists, [])
        self.assertIsNone(response.entity_name)
        self.assertIsNone(response.designation_date)
        audit_mock.assert_called_once()
        metadata = audit_mock.call_args.kwargs["metadata"]
        self.assertEqual(metadata["lists"], ["OFAC", "UN", "COAF"])
        self.assertEqual(metadata["delivery_mode"], "local_cache")


if __name__ == "__main__":
    unittest.main()
