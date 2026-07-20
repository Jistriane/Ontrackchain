from __future__ import annotations

import asyncio
import importlib
import sys
import unittest
from pathlib import Path
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
class OperationsCatalogCapabilityTests(unittest.TestCase):
    def test_operation_detail_exposes_live_capability_for_kyc_wallet(self) -> None:
        with patch.object(
            main,
            "_get_compliance_provider_readiness",
            return_value=main.describe_provider_readiness(
                provider_name="trm_labs",
                trm_config=main.TrmRiskProviderConfig(
                    enabled=True,
                    api_key="secret",
                    api_key_header="Authorization",
                    api_key_prefix="Bearer ",
                    screening_url="https://provider.example/screen",
                    timeout_ms=1500,
                    max_retries=1,
                ),
            ),
        ):
            item = main._build_operation_detail("kyc_wallet", "professional", include_deprecated=False)

        self.assertEqual(item["provider"], "trm_labs")
        self.assertEqual(item["provider_status"], "live")
        self.assertIsNone(item["degraded_reason"])
        self.assertEqual(item["capability_status"], "live")
        self.assertEqual(item["delivery_mode"], "risk_check_instant")
        self.assertEqual(item["capability_details"]["operating_mode"], "live")

    def test_operations_catalog_includes_live_sanctions_and_manual_review_capabilities(self) -> None:
        response = asyncio.run(
            main.get_operations_catalog(
                include_deprecated=False,
                include_unavailable=True,
                x_plan="starter",
            )
        )

        operations = {item.canonical: item for item in response.operations}
        dd = operations["due_diligence"]
        sanctions = operations["sanctions_check"]

        self.assertEqual(dd.provider, "manual_review")
        self.assertEqual(dd.provider_status, "degraded")
        self.assertEqual(dd.degraded_reason, "manual_review_required")
        self.assertEqual(dd.capability_status, "degraded")
        self.assertEqual(dd.delivery_mode, "manual_review_pending")
        self.assertTrue(dd.capability_details["requires_human_review"])

        self.assertEqual(sanctions.provider, "sanctions_lists_cache")
        self.assertEqual(sanctions.provider_status, "live")
        self.assertIsNone(sanctions.degraded_reason)
        self.assertEqual(sanctions.capability_status, "live")
        self.assertEqual(sanctions.delivery_mode, "local_cache")
        self.assertEqual(sanctions.capability_details["provider_dependency"], "sanctions_lists_meta")
        self.assertEqual(sanctions.capability_details["screening_source"], "sanctions_hits_cache")
        self.assertTrue(sanctions.capability_details["ready_for_live_homologation"])

    def test_operation_detail_route_returns_capability_fields(self) -> None:
        response = asyncio.run(
            main.get_operation_detail(
                operation_identifier="sof",
                include_deprecated=False,
                x_plan="professional",
            )
        )

        self.assertEqual(response.canonical, "source_of_funds")
        self.assertEqual(response.provider, "manual_review")
        self.assertEqual(response.provider_status, "degraded")
        self.assertEqual(response.degraded_reason, "manual_review_required")
        self.assertEqual(response.capability_status, "degraded")
        self.assertEqual(response.delivery_mode, "manual_review_pending")
        self.assertIn("requires_human_review", response.capability_details)


if __name__ == "__main__":
    unittest.main()
