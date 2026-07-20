from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "agents" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "shared" / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("compliance_api.main")
else:
    main = None


class _FakeAuditCursor:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._fetchone: dict[str, Any] | None = None

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized_query.startswith("SELECT set_config("):
            self._fetchone = {"set_config": params_tuple[0] if params_tuple else None}
            return

        if normalized_query == "SELECT 1 FROM users WHERE id = %s":
            self._fetchone = {"exists": 1} if str(params_tuple[0]) in self.state["users"] else None
            return

        if normalized_query.startswith("INSERT INTO audit_logs"):
            organization_id, user_id, action, resource_type, resource_id, metadata_json = params_tuple
            self.state["audit_logs"].append(
                {
                    "organization_id": str(organization_id),
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "metadata": json.loads(metadata_json),
                }
            )
            self._fetchone = None
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def fetchone(self) -> dict[str, Any] | None:
        return self._fetchone

    def __enter__(self) -> "_FakeAuditCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeAuditConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.commit_calls = 0

    def cursor(self) -> _FakeAuditCursor:
        return _FakeAuditCursor(self.state)

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_FakeAuditConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeAuditPool:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._connection = _FakeAuditConnection(state)

    def connection(self) -> _FakeAuditConnection:
        return self._connection


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class ComplianceRbacTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeAuditPool]:
        user_id = "11111111-1111-1111-1111-111111111111"
        state = {
            "users": {user_id},
            "audit_logs": [],
        }
        return state, _FakeAuditPool(state)

    def test_record_authorization_denial_persists_audit_log(self) -> None:
        state, pool = self._build_state()

        main._record_authorization_denial(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id="external-actor-1",
            request_id="req-rbac-1",
            effective_role="VIEWER",
            allowed_roles={"ADMIN", "ANALYST"},
            detail="compliance_write_role_required",
            resource_type="counterparty",
            resource_id="counterparty-1",
            endpoint="/api/v1/compliance/counterparties",
            method="POST",
        )

        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty")
        self.assertEqual(log_entry["resource_id"], "counterparty-1")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST"],
        )
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/counterparties")

    def test_create_counterparty_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.create_counterparty(
                    main.CounterpartyCreateRequest(
                        counterparty_type="individual",
                        legal_name="Counterparty QA",
                        document_type="cpf",
                        document_number="12345678900",
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="VIEWER",
                    x_request_id="req-counterparty-viewer",
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "counterparty_create_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty_creation")
        self.assertEqual(log_entry["metadata"]["request_id"], "req-counterparty-viewer")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")

    def test_counterparty_create_role_direct_guard_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_counterparty_create_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-co-role",
            x_role="COMPLIANCE_OFFICER",
            resource_id="counterparty-1",
            endpoint="/api/v1/compliance/counterparties",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_counterparty_create_role_direct_guard_accepts_legacy_otk_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_counterparty_create_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-legacy-co-role",
            x_role="OTK_COMPLIANCE_OFFICER",
            resource_id="block-1",
            endpoint="/api/v1/compliance/blocks/evaluate",
            method="POST",
        )

        self.assertEqual(normalized_role, "OTK_COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_compliance_estimate_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_compliance_estimate_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-compliance-estimate-analyst",
            x_role="ANALYST",
            resource_id=None,
            endpoint="/api/v1/compliance/estimate",
            method="POST",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_compliance_estimate_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_compliance_estimate_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-compliance-estimate-viewer",
                x_role="VIEWER",
                resource_id=None,
                endpoint="/api/v1/compliance/estimate",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "compliance_estimate_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_quote")
        self.assertEqual(log_entry["metadata"]["detail"], "compliance_estimate_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/estimate")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_compliance_start_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_compliance_start_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-compliance-start-analyst",
            x_role="ANALYST",
            resource_id=None,
            endpoint="/api/v1/compliance/start",
            method="POST",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_compliance_start_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_compliance_start_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-compliance-start-viewer",
                x_role="VIEWER",
                resource_id=None,
                endpoint="/api/v1/compliance/start",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "compliance_start_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_case_start")
        self.assertEqual(log_entry["metadata"]["detail"], "compliance_start_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/start")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_compliance_case_report_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_compliance_case_report_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-compliance-report-analyst",
            x_role="ANALYST",
            resource_id="44444444-4444-4444-8444-444444444444",
            endpoint="/api/v1/compliance/cases/{case_id}/report",
            method="POST",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_compliance_case_report_role_rejects_compliance_officer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_compliance_case_report_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-compliance-report-co",
                x_role="COMPLIANCE_OFFICER",
                resource_id="44444444-4444-4444-8444-444444444444",
                endpoint="/api/v1/compliance/cases/{case_id}/report",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "compliance_case_report_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_case_report")
        self.assertEqual(log_entry["resource_id"], "44444444-4444-4444-8444-444444444444")
        self.assertEqual(log_entry["metadata"]["detail"], "compliance_case_report_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/cases/{case_id}/report")
        self.assertEqual(log_entry["metadata"]["effective_role"], "COMPLIANCE_OFFICER")
        self.assertEqual(log_entry["metadata"]["allowed_roles"], ["ADMIN", "ANALYST"])

    def test_counterparty_read_role_accepts_reviewer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_counterparty_read_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-counterparty-read-reviewer",
            x_role="REVIEWER",
            resource_id=None,
            endpoint="/api/v1/compliance/counterparties",
            method="GET",
        )

        self.assertEqual(normalized_role, "REVIEWER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_counterparty_read_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_counterparty_read_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-counterparty-read-viewer",
                x_role="VIEWER",
                resource_id=None,
                endpoint="/api/v1/compliance/counterparties",
                method="GET",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "counterparty_read_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty_read")
        self.assertEqual(log_entry["metadata"]["detail"], "counterparty_read_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/counterparties")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER", "OTK_REVIEWER", "REVIEWER"],
        )

    def test_counterparty_create_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_counterparty_create_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-counterparty-create-co",
            x_role="COMPLIANCE_OFFICER",
            resource_id=None,
            endpoint="/api/v1/compliance/counterparties",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_counterparty_create_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_counterparty_create_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-counterparty-create-viewer",
                x_role="VIEWER",
                resource_id=None,
                endpoint="/api/v1/compliance/counterparties",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "counterparty_create_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty_creation")
        self.assertEqual(log_entry["metadata"]["detail"], "counterparty_create_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/counterparties")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_sanctions_check_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_sanctions_check_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-sanctions-check-co",
            x_role="COMPLIANCE_OFFICER",
            resource_id="0xabc",
            endpoint="/api/v1/compliance/sanctions-check/{address}",
            method="GET",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_sanctions_check_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_sanctions_check_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-sanctions-check-viewer",
                x_role="VIEWER",
                resource_id="0xabc",
                endpoint="/api/v1/compliance/sanctions-check/{address}",
                method="GET",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "sanctions_check_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "sanctions_screening")
        self.assertEqual(log_entry["resource_id"], "0xabc")
        self.assertEqual(log_entry["metadata"]["detail"], "sanctions_check_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/sanctions-check/{address}")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_kyc_wallet_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_kyc_wallet_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-kyc-wallet-analyst",
            x_role="ANALYST",
            resource_id="0xabc",
            endpoint="/api/v1/compliance/kyc-wallet",
            method="POST",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_kyc_wallet_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_kyc_wallet_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-kyc-wallet-viewer",
                x_role="VIEWER",
                resource_id="0xabc",
                endpoint="/api/v1/compliance/kyc-wallet",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "kyc_wallet_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_screening")
        self.assertEqual(log_entry["resource_id"], "0xabc")
        self.assertEqual(log_entry["metadata"]["detail"], "kyc_wallet_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/kyc-wallet")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_risk_check_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_risk_check_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-risk-check-co",
            x_role="COMPLIANCE_OFFICER",
            resource_id="0xabc",
            endpoint="/api/v1/compliance/risk-check",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_risk_check_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_risk_check_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-risk-check-viewer",
                x_role="VIEWER",
                resource_id="0xabc",
                endpoint="/api/v1/compliance/risk-check",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "risk_check_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_screening")
        self.assertEqual(log_entry["resource_id"], "0xabc")
        self.assertEqual(log_entry["metadata"]["detail"], "risk_check_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/risk-check")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_due_diligence_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_due_diligence_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-due-diligence-co",
            x_role="COMPLIANCE_OFFICER",
            resource_id="0xabc",
            endpoint="/api/v1/compliance/due-diligence",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_due_diligence_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_due_diligence_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-due-diligence-viewer",
                x_role="VIEWER",
                resource_id="0xabc",
                endpoint="/api/v1/compliance/due-diligence",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "due_diligence_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_screening")
        self.assertEqual(log_entry["resource_id"], "0xabc")
        self.assertEqual(log_entry["metadata"]["detail"], "due_diligence_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/due-diligence")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_source_of_funds_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_source_of_funds_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-source-of-funds-analyst",
            x_role="ANALYST",
            resource_id="0xabc",
            endpoint="/api/v1/compliance/source-of-funds",
            method="POST",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_source_of_funds_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_source_of_funds_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-source-of-funds-viewer",
                x_role="VIEWER",
                resource_id="0xabc",
                endpoint="/api/v1/compliance/source-of-funds",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "source_of_funds_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "compliance_screening")
        self.assertEqual(log_entry["resource_id"], "0xabc")
        self.assertEqual(log_entry["metadata"]["detail"], "source_of_funds_role_required")
        self.assertEqual(log_entry["metadata"]["endpoint"], "/api/v1/compliance/source-of-funds")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_block_evaluate_role_accepts_legacy_otk_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_block_evaluate_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-block-evaluate-legacy-co",
            x_role="OTK_COMPLIANCE_OFFICER",
            resource_id="block-eval-1",
            endpoint="/api/v1/compliance/blocks/evaluate",
            method="POST",
        )

        self.assertEqual(normalized_role, "OTK_COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_block_evaluate_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_block_evaluate_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-block-evaluate-viewer",
                x_role="VIEWER",
                resource_id="block-eval-1",
                endpoint="/api/v1/compliance/blocks/evaluate",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "block_evaluate_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "preventive_block_evaluation")
        self.assertEqual(log_entry["resource_id"], "block-eval-1")
        self.assertEqual(log_entry["metadata"]["detail"], "block_evaluate_role_required")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_block_read_role_accepts_analyst(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_block_read_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-block-read-analyst",
            x_role="ANALYST",
            resource_id=None,
            endpoint="/api/v1/compliance/blocks",
            method="GET",
        )

        self.assertEqual(normalized_role, "ANALYST")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_block_read_role_accepts_legacy_otk_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_block_read_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-block-read-legacy-co",
            x_role="OTK_COMPLIANCE_OFFICER",
            resource_id=None,
            endpoint="/api/v1/compliance/blocks",
            method="GET",
        )

        self.assertEqual(normalized_role, "OTK_COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_block_read_role_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_block_read_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-block-read-viewer",
                x_role="VIEWER",
                resource_id=None,
                endpoint="/api/v1/compliance/blocks",
                method="GET",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "preventive_block_read_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "preventive_block")
        self.assertIsNone(log_entry["resource_id"])
        self.assertEqual(log_entry["metadata"]["detail"], "preventive_block_read_role_required")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_block_lift_role_accepts_compliance_officer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_block_lift_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-block-lift-co",
            x_role="COMPLIANCE_OFFICER",
            resource_id="block-1",
            endpoint="/api/v1/compliance/blocks/{block_id}/lift",
            method="POST",
        )

        self.assertEqual(normalized_role, "COMPLIANCE_OFFICER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_block_lift_role_rejects_analyst_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_block_lift_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-block-lift-analyst",
                x_role="ANALYST",
                resource_id="block-1",
                endpoint="/api/v1/compliance/blocks/{block_id}/lift",
                method="POST",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "block_lift_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "preventive_block_lift")
        self.assertEqual(log_entry["resource_id"], "block-1")
        self.assertEqual(log_entry["metadata"]["detail"], "block_lift_role_required")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER"],
        )

    def test_counterparty_review_role_accepts_reviewer(self) -> None:
        _state, pool = self._build_state()

        normalized_role = main._require_counterparty_review_role(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-counterparty-reviewer",
            x_role="REVIEWER",
            resource_id="counterparty-1",
            endpoint="/api/v1/compliance/counterparties/{counterparty_id}/review",
            method="PATCH",
        )

        self.assertEqual(normalized_role, "REVIEWER")
        self.assertEqual(pool._connection.commit_calls, 0)

    def test_counterparty_review_role_rejects_analyst_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_counterparty_review_role(
                pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-counterparty-analyst-review",
                x_role="ANALYST",
                resource_id="counterparty-1",
                endpoint="/api/v1/compliance/counterparties/{counterparty_id}/review",
                method="PATCH",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "counterparty_review_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "counterparty_review")
        self.assertEqual(log_entry["resource_id"], "counterparty-1")
        self.assertEqual(log_entry["metadata"]["detail"], "counterparty_review_role_required")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "COMPLIANCE_OFFICER", "OTK_COMPLIANCE_OFFICER", "OTK_REVIEWER", "REVIEWER"],
        )


if __name__ == "__main__":
    unittest.main()
