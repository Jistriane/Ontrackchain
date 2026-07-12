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
    HTTPException: Any = importlib.import_module("fastapi").HTTPException
    main: Any = importlib.import_module("compliance_api.main")
    MAIN_IMPORT_AVAILABLE = True
except ModuleNotFoundError:
    HTTPException = Exception
    main = None
    MAIN_IMPORT_AVAILABLE = False


@unittest.skipUnless(MAIN_IMPORT_AVAILABLE, "compliance_api.main dependencies not installed in current interpreter")
class ComplianceInternalMetricsTests(unittest.TestCase):
    def test_provider_readiness_returns_contract_for_current_provider(self) -> None:
        with (
            patch.object(main.settings, "compliance_internal_metrics_enabled", True),
            patch.object(main.settings, "compliance_risk_provider", "trm_labs"),
            patch.object(main.settings, "compliance_trm_enabled", False),
            patch.object(main.settings, "compliance_trm_screening_url", ""),
            patch.object(main.settings, "compliance_trm_api_key", ""),
        ):
            payload = asyncio.run(main.internal_compliance_provider_readiness())

        self.assertEqual(payload["provider"], "trm_labs")
        self.assertTrue(payload["provider_supported"])
        self.assertFalse(payload["enabled"])
        self.assertFalse(payload["configured"])
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["degraded_reason"], "provider_disabled")
        self.assertEqual(payload["details"]["operating_mode"], "disabled")
        self.assertIn("screening_url_configured", payload["details"])
        self.assertIn("api_key_configured", payload["details"])
        self.assertIn("timeout_ms", payload["details"])
        self.assertIn("max_retries", payload["details"])

    def test_provider_readiness_returns_404_when_internal_metrics_are_disabled(self) -> None:
        with patch.object(main.settings, "compliance_internal_metrics_enabled", False):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(main.internal_compliance_provider_readiness())

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "internal_metrics_disabled")

    def test_prometheus_metrics_include_provider_gauges(self) -> None:
        snapshot = {
            "catalog": {"operations_total": 4},
            "quotes": {"open_total": 1, "expired_total": 0},
            "cases": {
                "queued_total": 0,
                "processing_total": 0,
                "completed_total": 2,
                "completed_last_24h": 2,
                "failed_total": 0,
                "failed_last_24h": 0,
                "completed_without_report_total": 0,
            },
            "reports": {
                "total": 2,
                "last_24h": 2,
                "legal_last_24h": 1,
                "coaf_last_24h": 1,
                "orgs_with_reports_last_24h": 1,
            },
            "audit": {
                "risk_checks_last_24h": 3,
                "risk_checks_live_last_24h": 2,
                "risk_checks_degraded_last_24h": 1,
            },
            "provider": {
                "name": "trm_labs",
                "supported": True,
                "enabled": True,
                "configured": False,
                "ready": False,
                "degraded_reason": "provider_not_configured",
                "details": {},
            },
            "generated_at": "2026-06-27T00:00:00+00:00",
        }
        alerts = [
            {
                "code": "compliance_provider_degraded_recent",
                "severity": "warning",
                "status": "open",
                "metric": "audit.risk_checks_degraded_last_24h",
                "value": 1.0,
                "threshold": 1.0,
                "title": "Provider degradado",
                "message": "Provider em degradacao controlada.",
                "recommended_action": "Validar readiness.",
            }
        ]

        with (
            patch.object(main.settings, "compliance_internal_metrics_enabled", True),
            patch.object(main, "_build_compliance_platform_snapshot", return_value=snapshot),
            patch.object(main, "_build_compliance_platform_alerts", return_value=alerts),
        ):
            response = asyncio.run(main.internal_compliance_prometheus_metrics(pool=object()))

        content = response.body.decode("utf-8")
        self.assertIn("ontrack_compliance_platform_provider_supported 1", content)
        self.assertIn("ontrack_compliance_platform_provider_enabled 1", content)
        self.assertIn("ontrack_compliance_platform_provider_configured 0", content)
        self.assertIn("ontrack_compliance_platform_provider_ready 0", content)


if __name__ == "__main__":
    unittest.main()
