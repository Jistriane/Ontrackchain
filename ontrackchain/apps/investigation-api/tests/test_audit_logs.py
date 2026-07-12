from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("investigation_api.main")
else:
    main = None


class _FakeCursor:
    def __init__(self, *, total: int = 0, rows: list[dict] | None = None, fetchall_batches: list[list[dict]] | None = None):
        self.total = total
        self.rows = rows or []
        self.fetchall_batches = list(fetchall_batches) if fetchall_batches is not None else None
        self.execute_calls: list[tuple[str, list[object] | tuple[object, ...] | None]] = []
        self._fetchone_calls = 0

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def execute(self, query: str, params=None) -> None:
        self.execute_calls.append((query, params))

    def fetchone(self) -> dict:
        self._fetchone_calls += 1
        if self._fetchone_calls == 1:
            return {"total": self.total}
        raise AssertionError("fetchone called more times than expected")

    def fetchall(self) -> list[dict]:
        if self.fetchall_batches is not None:
            if not self.fetchall_batches:
                raise AssertionError("fetchall called more times than expected")
            return self.fetchall_batches.pop(0)
        return self.rows


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        return None


class _FakePool:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor

    def connection(self) -> _FakeConnection:
        return _FakeConnection(self._cursor)


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class AuditLogsPaginationTests(unittest.TestCase):
    def test_list_audit_logs_returns_page_metadata_and_uses_offset(self) -> None:
        cursor = _FakeCursor(
            total=3,
            rows=[
                {
                    "id": "log-2",
                    "user_id": None,
                    "action": "report_generated",
                    "resource_type": "case",
                    "resource_id": None,
                    "metadata": {"request_id": "req-2", "report_id": "rep-2"},
                    "created_at": None,
                }
            ],
        )
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            payload = asyncio.run(
                main.list_audit_logs(
                    action="report_generated",
                    limit=1,
                    page=2,
                    pool=pool,
                    x_org_id="org-1",
                    x_role="ADMIN",
                    x_request_id="req-audit-page-1",
                )
            )

        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["total_pages"], 3)
        self.assertTrue(payload["has_more"])
        self.assertEqual(payload["filters"]["action"], "report_generated")
        self.assertEqual(payload["data"][0]["request_id"], "req-2")
        self.assertEqual(len(cursor.execute_calls), 2)
        count_query, count_params = cursor.execute_calls[0]
        data_query, data_params = cursor.execute_calls[1]
        self.assertIn("SELECT COUNT(*) AS total", count_query)
        self.assertEqual(count_params, ["org-1", "report_generated"])
        self.assertIn("LIMIT %s OFFSET %s", data_query)
        self.assertEqual(data_params, ["org-1", "report_generated", 1, 1])

    def test_list_audit_logs_marks_last_page_without_more_results(self) -> None:
        cursor = _FakeCursor(total=2, rows=[])
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
        ):
            payload = asyncio.run(
                main.list_audit_logs(
                    limit=1,
                    page=2,
                    pool=pool,
                    x_org_id="org-1",
                    x_role="AUDITOR",
                    x_request_id="req-audit-page-2",
                )
            )

        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["total_pages"], 2)
        self.assertFalse(payload["has_more"])

    def test_export_evidence_bundle_includes_reports_section(self) -> None:
        cursor = _FakeCursor(
            fetchall_batches=[
                [
                    {
                        "id": "audit-1",
                        "user_id": None,
                        "action": "report_generated",
                        "resource_type": "case",
                        "resource_id": "case-1",
                        "metadata": {"request_id": "req-export-1", "report_id": "rep-1"},
                        "created_at": None,
                    }
                ],
                [
                    {
                        "id": "ledger-1",
                        "case_id": "case-1",
                        "action": "PRE_HOLD",
                        "amount": 3.5,
                        "balance_after": 10.0,
                        "metadata": {"request_id": "req-export-1", "quote_id": "quote-1"},
                        "created_at": None,
                    }
                ],
                [
                    {
                        "id": "report-row-1",
                        "case_id": "case-1",
                        "external_report_id": "rep-1",
                        "report_type_requested": "compliance_aml",
                        "report_type": "compliance_aml",
                        "content_type": "application/pdf",
                        "file_path": "/tmp/report.pdf",
                        "file_hash": "sha256-report",
                        "onchain_hash": None,
                        "is_coaf_ready": False,
                        "created_at": None,
                    }
                ],
            ]
        )
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log") as record_audit_log,
            patch.object(main, "_format_evidence_export_filename", return_value="bundle.json"),
        ):
            response = asyncio.run(
                main.export_evidence_bundle(
                    body=main.EvidenceExportRequest(
                        request_id="req-export-1",
                        report_id="rep-1",
                        resource_id="11111111-1111-1111-1111-111111111111",
                        limit=10,
                        include_audit_logs=True,
                        include_credit_ledger=True,
                        include_reports=True,
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_role="ADMIN",
                    x_request_id="req-export-call-1",
                )
            )

        payload = json.loads(response.body.decode("utf-8"))
        self.assertEqual(payload["sections"]["audit_logs"]["count"], 1)
        self.assertEqual(payload["sections"]["credit_ledger"]["count"], 1)
        self.assertEqual(payload["sections"]["reports"]["count"], 1)
        self.assertTrue(payload["sections"]["reports"]["included"])
        self.assertEqual(payload["sections"]["reports"]["data"][0]["report_id"], "rep-1")
        self.assertEqual(payload["sections"]["reports"]["data"][0]["file_hash_sha256"], "sha256-report")
        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="bundle.json"')
        self.assertEqual(len(cursor.execute_calls), 3)
        reports_query, reports_params = cursor.execute_calls[2]
        self.assertIn("FROM reports", reports_query)
        self.assertIn("EXISTS", reports_query)
        self.assertEqual(
            reports_params,
            [
                "org-1",
                "rep-1",
                "11111111-1111-1111-1111-111111111111",
                "org-1",
                "req-export-1",
                10,
            ],
        )
        audit_metadata = record_audit_log.call_args.kwargs["metadata"]
        self.assertEqual(audit_metadata["sections"]["reports"]["count"], 1)
        self.assertTrue(audit_metadata["sections"]["reports"]["included"])

    def test_record_manual_package_export_persists_audit_entry(self) -> None:
        cursor = _FakeCursor()
        pool = _FakePool(cursor)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_record_audit_log") as record_audit_log,
        ):
            payload = asyncio.run(
                main.record_manual_package_export(
                    body=main.ManualPackageAuditRequest(
                        request_id="req-dd-1",
                        report_id="rep-dd-1",
                        metadata={
                            "scope_id": "req-dd-1",
                            "filename": "ontrackchain-manual-review-due-diligence-req-dd-1.json",
                            "package_sha256": "a" * 64,
                            "manual_review_action": "compliance_due_diligence_checked",
                        },
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_user_id="external-user-1",
                    x_linked_user_id="linked-user-1",
                    x_role="ADMIN",
                    x_request_id="req-call-1",
                )
            )

        self.assertEqual(payload["action"], "evidence_manual_review_package_exported")
        self.assertEqual(payload["request_id"], "req-dd-1")
        self.assertEqual(payload["report_id"], "rep-dd-1")
        self.assertEqual(payload["resource_type"], "audit_log")
        audit_metadata = record_audit_log.call_args.kwargs["metadata"]
        self.assertEqual(audit_metadata["scope_id"], "req-dd-1")
        self.assertEqual(audit_metadata["filename"], "ontrackchain-manual-review-due-diligence-req-dd-1.json")
        self.assertEqual(audit_metadata["package_sha256"], "a" * 64)
        self.assertEqual(audit_metadata["manual_review_action"], "compliance_due_diligence_checked")
        self.assertEqual(audit_metadata["request_id"], "req-dd-1")
        self.assertEqual(audit_metadata["report_id"], "rep-dd-1")
        self.assertEqual(record_audit_log.call_args.kwargs["user_id"], "linked-user-1")

    def test_record_manual_package_audit_event_rejects_unknown_action(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported_manual_package_audit_action"):
            main._record_manual_package_audit_event(
                _FakeCursor(),
                organization_id="org-1",
                user_id="user-1",
                action="unsupported_action",
                resource_type="audit_log",
                resource_id=None,
                request_id="req-1",
                report_id="rep-1",
                metadata={"scope_id": "scope-1"},
                created_at="2026-07-08T16:00:00+00:00",
                external_user_id="external-user-1",
            )

    def test_local_hs256_seal_backend_generates_verified_flattened_jws(self) -> None:
        seal_row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "organization_id": "org-1",
            "package_kind": "manual_review_package",
            "request_id": "req-dd-1",
            "report_id": "rep-dd-1",
            "scope_id": "scope-dd-1",
            "manual_review_action": "compliance_due_diligence_checked",
            "package_sha256": "a" * 64,
            "manifest_schema_version": "manual_review_package/v2",
            "classification": "restricted_regulatory",
            "signoff_mode": "compliance_ops_signoff",
            "policy_version": "manual_package_sealing/v1",
        }
        signoff_rows = [
            {
                "id": "signoff-1",
                "seal_id": "11111111-1111-1111-1111-111111111111",
                "organization_id": "org-1",
                "signer_role": "compliance_owner",
                "signer_user_id": None,
                "signer_display_name": "Compliance Owner",
                "decision": "approved",
                "signoff_method": "platform_authenticated_2fa",
                "ticket_ref": "GOV-1",
                "notes": None,
                "signed_at": None,
                "metadata": {},
            },
            {
                "id": "signoff-2",
                "seal_id": "11111111-1111-1111-1111-111111111111",
                "organization_id": "org-1",
                "signer_role": "ops_owner",
                "signer_user_id": None,
                "signer_display_name": "Ops Owner",
                "decision": "approved",
                "signoff_method": "governance_ticket",
                "ticket_ref": "GOV-2",
                "notes": None,
                "signed_at": None,
                "metadata": {},
            },
        ]

        with patch.object(main.settings, "investigation_manual_seal_hs256_secret", "super-secret-test-key"):
            result = main._seal_manual_package_with_local_hs256(
                seal_row=seal_row,
                signoff_rows=signoff_rows,
                finalized_at="2026-07-08T17:00:00+00:00",
                finalized_by_user_id="user-1",
                finalize_metadata={"ticket": "PKG-1"},
            )

        self.assertEqual(result["signature_algorithm"], "HS256")
        self.assertEqual(result["verification_summary"]["seal_backend"], "local_hs256")
        self.assertTrue(result["verification_summary"]["verified"])
        self.assertEqual(result["verification_summary"]["package_sha256"], "a" * 64)
        self.assertIn("protected", result["seal_envelope"])
        self.assertIn("payload", result["seal_envelope"])
        self.assertIn("signature", result["seal_envelope"])

    def test_local_hs256_seal_backend_requires_secret(self) -> None:
        seal_row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "organization_id": "org-1",
            "package_kind": "manual_review_package",
            "request_id": "req-dd-1",
            "report_id": None,
            "scope_id": "scope-dd-1",
            "manual_review_action": "compliance_due_diligence_checked",
            "package_sha256": "a" * 64,
            "manifest_schema_version": "manual_review_package/v2",
            "classification": "restricted_regulatory",
            "signoff_mode": "compliance_ops_signoff",
            "policy_version": "manual_package_sealing/v1",
        }

        with patch.object(main.settings, "investigation_manual_seal_hs256_secret", ""):
            with self.assertRaises(main.HTTPException) as exc_info:
                main._seal_manual_package_with_local_hs256(
                    seal_row=seal_row,
                    signoff_rows=[],
                    finalized_at="2026-07-08T17:00:00+00:00",
                    finalized_by_user_id="user-1",
                    finalize_metadata={},
                )

        self.assertEqual(exc_info.exception.status_code, 424)
        self.assertEqual(exc_info.exception.detail["code"], "manual_seal_secret_missing")


if __name__ == "__main__":
    unittest.main()
