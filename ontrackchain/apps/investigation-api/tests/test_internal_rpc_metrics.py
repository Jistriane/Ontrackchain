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
    HTTPException = importlib.import_module("fastapi").HTTPException
    main: Any = importlib.import_module("investigation_api.main")
else:
    HTTPException = Exception
    main = None


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class InvestigationInternalRpcMetricsTests(unittest.TestCase):
    def test_rpc_readiness_returns_live_mode_when_primary_url_is_configured(self) -> None:
        with (
            patch.object(main.settings, "investigation_internal_metrics_enabled", True),
            patch.object(main.settings, "investigation_rpc_provider", "evm_rpc"),
            patch.object(main.settings, "investigation_rpc_enabled", True),
            patch.object(main.settings, "investigation_rpc_primary_url", "https://primary.rpc.example"),
            patch.object(main.settings, "investigation_rpc_fallback_url", "https://fallback.rpc.example"),
        ):
            payload = asyncio.run(main.internal_investigation_rpc_readiness())

        self.assertTrue(payload["enabled"])
        self.assertTrue(payload["configured"])
        self.assertTrue(payload["ready"])
        self.assertIsNone(payload["degraded_reason"])
        self.assertEqual(payload["details"]["operating_mode"], "live")
        self.assertTrue(payload["details"]["primary_url_configured"])
        self.assertTrue(payload["details"]["fallback_url_configured"])

    def test_rpc_readiness_returns_fallback_only_mode_when_primary_is_missing(self) -> None:
        with (
            patch.object(main.settings, "investigation_internal_metrics_enabled", True),
            patch.object(main.settings, "investigation_rpc_provider", "evm_rpc"),
            patch.object(main.settings, "investigation_rpc_enabled", True),
            patch.object(main.settings, "investigation_rpc_primary_url", ""),
            patch.object(main.settings, "investigation_rpc_fallback_url", "https://fallback.rpc.example"),
        ):
            payload = asyncio.run(main.internal_investigation_rpc_readiness())

        self.assertTrue(payload["enabled"])
        self.assertTrue(payload["configured"])
        self.assertTrue(payload["ready"])
        self.assertIsNone(payload["degraded_reason"])
        self.assertEqual(payload["details"]["operating_mode"], "fallback_only")
        self.assertFalse(payload["details"]["primary_url_configured"])
        self.assertTrue(payload["details"]["fallback_url_configured"])

    def test_rpc_readiness_returns_contract_for_current_provider(self) -> None:
        with (
            patch.object(main.settings, "investigation_internal_metrics_enabled", True),
            patch.object(main.settings, "investigation_rpc_provider", "evm_rpc"),
            patch.object(main.settings, "investigation_rpc_enabled", False),
            patch.object(main.settings, "investigation_rpc_primary_url", ""),
            patch.object(main.settings, "investigation_rpc_fallback_url", ""),
        ):
            payload = asyncio.run(main.internal_investigation_rpc_readiness())

        self.assertEqual(payload["provider"], "evm_rpc")
        self.assertTrue(payload["provider_supported"])
        self.assertFalse(payload["enabled"])
        self.assertFalse(payload["configured"])
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["degraded_reason"], "provider_disabled")
        self.assertEqual(payload["details"]["operating_mode"], "disabled")

    def test_rpc_readiness_returns_404_when_internal_metrics_are_disabled(self) -> None:
        with patch.object(main.settings, "investigation_internal_metrics_enabled", False):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(main.internal_investigation_rpc_readiness())
        exception: Any = ctx.exception
        self.assertEqual(exception.status_code, 404)
        self.assertEqual(exception.detail, "internal_metrics_disabled")

    def test_platform_prometheus_metrics_include_rpc_provider_gauges(self) -> None:
        snapshot = {
            "queue": {"ready": 1, "waiting": 2, "retry_pending": 0, "retry_due": 0, "wake_signals": 1},
            "concurrency": {"global_active": 1, "global_limit": 10},
            "throughput": {"completed_last_hour": 1, "failed_last_hour": 0, "avg_duration_ms_last_20": 42.0},
            "states": {"queued": 2, "processing": 1, "dlq_failed": 0, "dlq_resolved": 0, "orgs_with_open_dlq": 0},
            "timing": {"oldest_queued_age_seconds": 5, "oldest_dlq_age_seconds": 0},
            "security": {
                "manual_package_mfa_violations_last_hour": 3,
                "manual_package_mfa_2fa_required_last_hour": 2,
                "manual_package_mfa_provider_not_homologated_last_hour": 1,
            },
            "provider": {
                "name": "evm_rpc",
                "supported": True,
                "enabled": True,
                "configured": True,
                "ready": True,
                "degraded_reason": None,
                "details": {
                    "operating_mode": "live",
                    "primary_url_configured": True,
                    "fallback_url_configured": True,
                    "timeout_ms": 1500,
                    "max_retries": 1,
                },
            },
            "generated_at": "2026-01-01T00:00:00+00:00",
        }
        alerts = [
            {
                "code": "investigation_rpc_provider_not_ready",
                "severity": "warning",
                "status": "closed",
                "metric": "provider.ready",
                "value": 1,
                "threshold": 1,
                "title": "Provider RPC global não pronto",
                "message": "ok",
                "recommended_action": "none",
            }
        ]

        content = main._render_platform_prometheus_metrics(snapshot, alerts)

        self.assertIn("ontrack_investigation_platform_provider_supported 1", content)
        self.assertIn("ontrack_investigation_platform_provider_enabled 1", content)
        self.assertIn("ontrack_investigation_platform_provider_configured 1", content)
        self.assertIn("ontrack_investigation_platform_provider_ready 1", content)
        self.assertIn("ontrack_investigation_platform_manual_package_mfa_violations_last_hour 3", content)
        self.assertIn("ontrack_investigation_platform_manual_package_mfa_2fa_required_last_hour 2", content)
        self.assertIn("ontrack_investigation_platform_manual_package_mfa_provider_not_homologated_last_hour 1", content)

    def test_org_prometheus_metrics_include_manual_package_mfa_breakdown(self) -> None:
        snapshot = {
            "queue": {"ready": 0, "waiting": 0, "retry_pending": 0, "retry_due": 0, "wake_signals": 0},
            "concurrency": {"org_active": 0, "org_limit": 5, "global_active": 1, "global_limit": 10, "plan": "growth"},
            "throughput": {"completed_last_hour": 0, "failed_last_hour": 0, "billing_recalc_last_hour": 0, "avg_duration_ms_last_20": 0.0},
            "states": {"queued": 0, "processing": 0, "dlq_failed": 0, "dlq_resolved": 0},
            "timing": {"oldest_queued_age_seconds": 0, "oldest_dlq_age_seconds": 0},
            "security": {
                "manual_package_mfa_violations_last_hour": 4,
                "manual_package_mfa_2fa_required_last_hour": 3,
                "manual_package_mfa_provider_not_homologated_last_hour": 1,
            },
            "provider": {
                "name": "evm_rpc",
                "supported": True,
                "enabled": True,
                "configured": True,
                "ready": True,
                "degraded_reason": None,
                "details": {},
            },
            "recent_cases": [],
            "generated_at": "2026-01-01T00:00:00+00:00",
        }

        content = main._render_prometheus_metrics(snapshot, [])

        self.assertIn("ontrack_investigation_manual_package_mfa_violations_last_hour 4", content)
        self.assertIn("ontrack_investigation_manual_package_mfa_2fa_required_last_hour 3", content)
        self.assertIn("ontrack_investigation_manual_package_mfa_provider_not_homologated_last_hour 1", content)

    def test_platform_operational_alerts_open_manual_package_mfa_warning(self) -> None:
        snapshot = {
            "queue": {"waiting": 0, "retry_due": 0},
            "states": {"dlq_failed": 0},
            "timing": {"oldest_queued_age_seconds": 0, "oldest_dlq_age_seconds": 0},
            "concurrency": {"global_active": 0, "global_limit": 10},
            "provider": {"enabled": True, "ready": True},
            "security": {
                "manual_package_mfa_violations_last_hour": 2,
                "manual_package_mfa_2fa_required_last_hour": 1,
                "manual_package_mfa_provider_not_homologated_last_hour": 1,
            },
        }

        alerts = main._build_investigation_platform_alerts(snapshot)
        mfa_alert = next(alert for alert in alerts if alert["code"] == "investigation_manual_package_mfa_violations")

        self.assertEqual(mfa_alert["status"], "open")
        self.assertEqual(mfa_alert["severity"], "warning")
        self.assertEqual(mfa_alert["metric"], "security.manual_package_mfa_violations_last_hour")
        self.assertEqual(mfa_alert["value"], 2.0)
        self.assertEqual(mfa_alert["threshold"], 1.0)
