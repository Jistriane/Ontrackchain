from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("compliance_api.main")
else:
    main = None


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class OperationsCatalogCapabilityTests(unittest.TestCase):
    def test_operation_detail_exposes_live_capability_for_kyc_wallet(self) -> None:
        with patch.object(
            main,
            "_get_compliance_provider_readiness",
            return_value=main.describe_provider_readiness(
                provider_name="trm_labs",
                trm_config=main.TrmRiskProviderConfig(
                    api_key="secret",
                    screening_url="https://provider.example/screen",
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

    def test_operations_catalog_includes_degraded_manual_review_capabilities(self) -> None:
        response = asyncio.run(
            main.get_operations_catalog(
                include_deprecated=False,
                available_only=False,
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

        self.assertEqual(sanctions.provider, "sanctions_lists")
        self.assertEqual(sanctions.provider_status, "degraded")
        self.assertEqual(sanctions.degraded_reason, "sanctions_provider_not_integrated")
        self.assertEqual(sanctions.delivery_mode, "list_screening_pending")
        self.assertFalse(sanctions.capability_details["ready_for_live_homologation"])

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
