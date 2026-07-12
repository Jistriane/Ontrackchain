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
    main: Any = importlib.import_module("report_api.main")
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

        if normalized_query.startswith("INSERT INTO reports"):
            (
                organization_id,
                case_id,
                external_report_id,
                report_type_requested,
                report_type,
                content_type,
                file_hash,
                onchain_hash,
                metadata_json,
            ) = params_tuple
            existing = next(
                (row for row in self.state["reports"] if row["external_report_id"] == str(external_report_id)),
                None,
            )
            payload = {
                "organization_id": str(organization_id),
                "case_id": str(case_id) if case_id is not None else None,
                "external_report_id": str(external_report_id),
                "report_type_requested": str(report_type_requested),
                "report_type": str(report_type),
                "content_type": str(content_type),
                "file_hash": str(file_hash),
                "onchain_hash": onchain_hash,
                "metadata": json.loads(metadata_json),
            }
            if existing is None:
                self.state["reports"].append(payload)
            else:
                existing.update(payload)
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
class ReportRbacTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeAuditPool]:
        user_id = "11111111-1111-1111-1111-111111111111"
        state = {
            "users": {user_id},
            "audit_logs": [],
            "reports": [],
        }
        return state, _FakeAuditPool(state)

    def test_record_authorization_denial_persists_audit_log(self) -> None:
        state, pool = self._build_state()

        main._record_authorization_denial(
            pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id="external-actor-1",
            request_id="req-rbac-report-1",
            effective_role="TESTER",
            allowed_roles={"ADMIN", "ANALYST", "AUDITOR", "VIEWER"},
            detail="report_read_role_required",
            resource_type="report",
            resource_id="report-1",
            endpoint="/api/v1/reports",
            method="GET",
        )

        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "report")
        self.assertIsNone(log_entry["resource_id"])
        self.assertEqual(log_entry["metadata"]["effective_role"], "TESTER")
        self.assertEqual(log_entry["metadata"]["resource_reference_id"], "report-1")
        self.assertEqual(
            log_entry["metadata"]["allowed_roles"],
            ["ADMIN", "ANALYST", "AUDITOR", "VIEWER"],
        )

    def test_list_reports_rejects_tester_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.list_reports(
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="TESTER",
                    x_request_id="req-report-list-tester",
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "report_read_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "report")
        self.assertEqual(log_entry["metadata"]["request_id"], "req-report-list-tester")
        self.assertEqual(log_entry["metadata"]["effective_role"], "TESTER")

    def test_generate_report_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            asyncio.run(
                main.generate_report(
                    main.GenerateReportRequest(case_id="case-1", report_type="technical"),
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="VIEWER",
                    x_request_id="req-report-generate-viewer",
                )
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "report_write_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "report")
        self.assertIsNone(log_entry["resource_id"])
        self.assertEqual(log_entry["metadata"]["request_id"], "req-report-generate-viewer")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")
        self.assertEqual(log_entry["metadata"]["resource_reference_id"], "case-1")

    def test_generate_report_allows_analyst(self) -> None:
        state, pool = self._build_state()

        payload = asyncio.run(
            main.generate_report(
                main.GenerateReportRequest(case_id="case-1", report_type="technical"),
                pool=pool,
                x_org_id="org-1",
                x_user_id="11111111-1111-1111-1111-111111111111",
                x_role="ANALYST",
                x_request_id="req-report-generate-analyst",
            )
        )

        self.assertEqual(payload.report_type, "technical_basic")
        self.assertEqual(payload.case_id, "case-1")
        self.assertEqual(len(state["reports"]), 1)
        persisted_report = state["reports"][0]
        self.assertEqual(persisted_report["external_report_id"], payload.report_id)
        self.assertIsNone(persisted_report["case_id"])
        self.assertEqual(persisted_report["report_type"], "technical_basic")
        self.assertEqual(persisted_report["report_type_requested"], "technical")
        self.assertEqual(persisted_report["metadata"]["case_reference_id"], "case-1")
        self.assertEqual(len(state["audit_logs"]), 1)
        self.assertEqual(state["audit_logs"][0]["action"], "report_generated")
        self.assertEqual(state["audit_logs"][0]["resource_type"], "case")
        self.assertIsNone(state["audit_logs"][0]["resource_id"])
        self.assertEqual(state["audit_logs"][0]["metadata"]["report_id"], payload.report_id)
        self.assertEqual(state["audit_logs"][0]["metadata"]["resource_reference_id"], "case-1")

    def test_generate_report_persists_uuid_case_id_when_available(self) -> None:
        state, pool = self._build_state()
        case_id = "22222222-2222-2222-2222-222222222222"

        payload = asyncio.run(
            main.generate_report(
                main.GenerateReportRequest(case_id=case_id, report_type="technical"),
                pool=pool,
                x_org_id="org-1",
                x_user_id="11111111-1111-1111-1111-111111111111",
                x_role="ANALYST",
                x_request_id="req-report-generate-uuid-case",
            )
        )

        self.assertEqual(payload.case_id, case_id)
        self.assertEqual(len(state["reports"]), 1)
        persisted_report = state["reports"][0]
        self.assertEqual(persisted_report["case_id"], case_id)
        self.assertNotIn("case_reference_id", persisted_report["metadata"])

    def test_require_coaf_report_review_auth_allows_reviewer(self) -> None:
        state, pool = self._build_state()

        normalized_role = main._require_coaf_report_review_auth(
            pool=pool,
            organization_id="org-1",
            user_id="11111111-1111-1111-1111-111111111111",
            external_user_id=None,
            request_id="req-ros-reviewer-1",
            ros_id="ros-1",
            x_role="REVIEWER",
            x_mfa_mode="external_provider",
            x_mfa_provider_homologated="true",
            x_2fa="managed_externally_homologated",
        )

        self.assertEqual(normalized_role, "REVIEWER")
        self.assertEqual(state["audit_logs"], [])

    def test_require_coaf_report_review_auth_rejects_viewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_coaf_report_review_auth(
                pool=pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-ros-review-viewer",
                ros_id="ros-2",
                x_role="VIEWER",
                x_mfa_mode="external_provider",
                x_mfa_provider_homologated="true",
                x_2fa="ok",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "coaf_report_review_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "ros_record")
        self.assertEqual(log_entry["resource_id"], "ros-2")
        self.assertEqual(log_entry["metadata"]["effective_role"], "VIEWER")
        self.assertEqual(log_entry["metadata"]["detail"], "coaf_report_review_role_required")

    def test_require_coaf_report_submission_auth_rejects_reviewer_and_records_denial(self) -> None:
        state, pool = self._build_state()

        with self.assertRaises(main.HTTPException) as ctx:
            main._require_coaf_report_submission_auth(
                pool=pool,
                organization_id="org-1",
                user_id="11111111-1111-1111-1111-111111111111",
                external_user_id=None,
                request_id="req-ros-submit-reviewer",
                ros_id="ros-3",
                x_role="REVIEWER",
                x_mfa_mode="external_provider",
                x_mfa_provider_homologated="true",
                x_2fa="ok",
            )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "coaf_report_submission_role_required")
        self.assertEqual(pool._connection.commit_calls, 1)
        self.assertEqual(len(state["audit_logs"]), 1)
        log_entry = state["audit_logs"][0]
        self.assertEqual(log_entry["action"], "authorization_denied")
        self.assertEqual(log_entry["resource_type"], "ros_record")
        self.assertEqual(log_entry["resource_id"], "ros-3")
        self.assertEqual(log_entry["metadata"]["effective_role"], "REVIEWER")
        self.assertEqual(log_entry["metadata"]["detail"], "coaf_report_submission_role_required")


if __name__ == "__main__":
    unittest.main()
