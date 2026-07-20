from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

if FASTAPI_AVAILABLE:
    main: Any = importlib.import_module("investigation_api.main")
else:
    main = None


class _FakeCursor:
    def __init__(self) -> None:
        self.execute_calls: list[tuple[str, tuple[object, ...] | None]] = []
        self.fetchone_results: list[object] = []

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def execute(self, query: str, params=None) -> None:
        self.execute_calls.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor):
        self._cursor = cursor
        self.commit_calls = 0

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None

    def cursor(self) -> _FakeCursor:
        return self._cursor

    def commit(self) -> None:
        self.commit_calls += 1


class _FakePool:
    def __init__(self, conn: _FakeConnection):
        self._conn = conn

    def connection(self) -> _FakeConnection:
        return self._conn


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _build_seal_row(
    *,
    seal_id: str = "11111111-1111-1111-1111-111111111111",
    status: str = "pending_signoff",
    request_id: str = "req-dd-1",
    report_id: str | None = "rep-dd-1",
    package_sha256: str = "a" * 64,
    revoked_at: datetime | None = None,
    superseded_by_seal_id: UUID | None = None,
    signature_algorithm: str | None = None,
    certificate_bundle_ref: str | None = None,
    seal_envelope: dict[str, object] | None = None,
    verification_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "id": UUID(seal_id),
        "organization_id": "org-1",
        "package_kind": "manual_review_package",
        "request_id": request_id,
        "report_id": report_id,
        "scope_id": request_id,
        "manual_review_action": "compliance_due_diligence_checked",
        "package_sha256": package_sha256,
        "manifest_schema_version": "manual_review_package/v2",
        "classification": "restricted_regulatory",
        "signoff_mode": "compliance_ops_signoff",
        "seal_status": status,
        "seal_format": "jws_json_flattened",
        "signature_algorithm": signature_algorithm,
        "kms_key_ref": None,
        "certificate_fingerprint_sha256": None,
        "certificate_bundle_ref": certificate_bundle_ref,
        "policy_version": "manual_package_sealing/v1",
        "sealed_at": _dt("2026-07-08T10:09:00+00:00") if status == "sealed" else None,
        "sealed_by_user_id": "linked-user-1" if status == "sealed" else None,
        "revoked_at": revoked_at,
        "superseded_by_seal_id": superseded_by_seal_id,
        "seal_envelope": seal_envelope or {},
        "verification_summary": verification_summary or {},
        "created_at": _dt("2026-07-08T10:00:00+00:00"),
        "updated_at": _dt("2026-07-08T10:00:00+00:00"),
    }


def _build_signoff_row(
    *,
    signoff_id: str,
    signer_role: str,
    decision: str = "approved",
) -> dict[str, object]:
    return {
        "id": UUID(signoff_id),
        "seal_id": UUID("11111111-1111-1111-1111-111111111111"),
        "organization_id": "org-1",
        "signer_role": signer_role,
        "signer_user_id": "linked-user-1",
        "signer_display_name": signer_role.replace("_", " ").title(),
        "decision": decision,
        "signoff_method": "platform_authenticated_2fa",
        "ticket_ref": "GOV-1",
        "notes": None,
        "signed_at": _dt("2026-07-08T10:01:00+00:00"),
        "metadata": {"source": "unit-test"},
    }


@unittest.skipUnless(FASTAPI_AVAILABLE, "fastapi dependency not installed in current interpreter")
class ManualPackageSealEndpointTests(unittest.TestCase):
    def test_record_manual_package_signoff_rejects_auditor_write(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_record_authorization_denial") as record_denial:
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="compliance_owner",
                            decision="approved",
                            signoff_method="platform_authenticated_2fa",
                            signer_display_name="Auditor",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="AUDITOR",
                        x_request_id="req-signoff-auditor-denied",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertEqual(exc_info.exception.detail, "manual_package_signoff_role_required")
        self.assertIsNotNone(record_denial.call_args)
        assert record_denial.call_args is not None
        self.assertEqual(record_denial.call_args.kwargs["effective_role"], "AUDITOR")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_record_manual_package_signoff_rejects_signer_role_mismatch(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_record_authorization_denial") as record_denial:
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="ops_owner",
                            decision="approved",
                            signoff_method="platform_authenticated_2fa",
                            signer_display_name="Legal Reviewer",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="LEGAL_REVIEWER",
                        x_request_id="req-signoff-role-mismatch",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertEqual(exc_info.exception.detail, "manual_package_signer_role_mismatch")
        self.assertIsNotNone(record_denial.call_args)
        assert record_denial.call_args is not None
        self.assertEqual(record_denial.call_args.kwargs["effective_role"], "LEGAL_REVIEWER")
        self.assertEqual(record_denial.call_args.kwargs["allowed_roles"], {"legal_owner_optional"})
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_record_manual_package_signoff_requires_real_2fa_for_platform_flow(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_record_manual_package_mfa_violation") as record_mfa_violation:
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="compliance_owner",
                            decision="approved",
                            signoff_method="platform_authenticated_2fa",
                            signer_display_name="Compliance Officer",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="COMPLIANCE_OFFICER",
                        x_request_id="req-signoff-2fa-required",
                        x_mfa_mode="local_totp",
                        x_2fa="pending",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertEqual(exc_info.exception.detail, "2fa_required")
        self.assertIsNotNone(record_mfa_violation.call_args)
        assert record_mfa_violation.call_args is not None
        self.assertEqual(record_mfa_violation.call_args.kwargs["detail"], "2fa_required")
        self.assertEqual(record_mfa_violation.call_args.kwargs["auth_role"], "COMPLIANCE_OFFICER")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_record_manual_package_signoff_accepts_homologated_external_provider_mfa(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        signoff_row = _build_signoff_row(
            signoff_id="33333333-3333-3333-3333-333333333333",
            signer_role="compliance_owner",
        )

        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value="linked-user-1"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[
                    (_build_seal_row(status="pending_signoff"), []),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                ],
            ),
            patch.object(main, "_record_manual_package_audit_event"),
            patch.object(cursor, "fetchone", side_effect=[{"id": UUID("33333333-3333-3333-3333-333333333333")}]),
        ):
            payload = asyncio.run(
                main.record_manual_package_signoff(
                    UUID("11111111-1111-1111-1111-111111111111"),
                    body=main.ManualPackageSignoffRecordRequest(
                        signer_role="compliance_owner",
                        decision="approved",
                        signoff_method="platform_authenticated_2fa",
                        signer_display_name="Compliance Officer",
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_role="COMPLIANCE_OFFICER",
                    x_linked_user_id="linked-user-1",
                    x_request_id="req-signoff-external-mfa",
                    x_mfa_mode="external_provider",
                    x_mfa_provider_homologated="true",
                    x_2fa="managed_externally_homologated",
                )
            )

        insert_params = cursor.execute_calls[0][1]
        assert insert_params is not None
        metadata_json = str(insert_params[9])
        self.assertIn('"mfa_mode": "external_provider"', metadata_json)
        self.assertIn('"mfa_provider_homologated": true', metadata_json)
        self.assertIn('"two_factor_status": "managed_externally_homologated"', metadata_json)
        self.assertEqual(payload["signoffs"][0]["signer_role"], "compliance_owner")
        self.assertEqual(conn.commit_calls, 1)

    def test_record_manual_package_signoff_allows_governance_ticket_without_2fa(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        signoff_row = _build_signoff_row(
            signoff_id="44444444-4444-4444-4444-444444444444",
            signer_role="legal_owner_optional",
            decision="approved",
        )
        signoff_row["signoff_method"] = "governance_ticket"

        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value="linked-user-2"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[
                    (_build_seal_row(status="pending_signoff"), []),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                ],
            ),
            patch.object(main, "_record_manual_package_audit_event"),
            patch.object(cursor, "fetchone", side_effect=[{"id": UUID("44444444-4444-4444-4444-444444444444")}]),
        ):
            payload = asyncio.run(
                main.record_manual_package_signoff(
                    UUID("11111111-1111-1111-1111-111111111111"),
                    body=main.ManualPackageSignoffRecordRequest(
                        signer_role="legal_owner_optional",
                        decision="approved",
                        signoff_method="governance_ticket",
                        signer_display_name="Legal Reviewer",
                        ticket_ref="GOV-42",
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_role="LEGAL_REVIEWER",
                    x_request_id="req-signoff-governance-ticket",
                )
            )

        insert_params = cursor.execute_calls[0][1]
        assert insert_params is not None
        metadata_json = str(insert_params[9])
        self.assertIn('"two_factor_status": "not_informed"', metadata_json)
        self.assertEqual(payload["signoffs"][0]["signoff_method"], "governance_ticket")
        self.assertEqual(conn.commit_calls, 1)

    def test_record_manual_package_signoff_allows_reviewer_for_legal_optional_role(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        signoff_row = _build_signoff_row(
            signoff_id="55555555-5555-5555-5555-555555555555",
            signer_role="legal_owner_optional",
            decision="approved",
        )
        signoff_row["signoff_method"] = "governance_ticket"

        with (
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value="linked-user-3"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[
                    (_build_seal_row(status="pending_signoff"), []),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                    (_build_seal_row(status="pending_signoff"), [signoff_row]),
                ],
            ),
            patch.object(main, "_record_manual_package_audit_event"),
            patch.object(cursor, "fetchone", side_effect=[{"id": UUID("55555555-5555-5555-5555-555555555555")}]),
        ):
            payload = asyncio.run(
                main.record_manual_package_signoff(
                    UUID("11111111-1111-1111-1111-111111111111"),
                    body=main.ManualPackageSignoffRecordRequest(
                        signer_role="legal_owner_optional",
                        decision="approved",
                        signoff_method="governance_ticket",
                        signer_display_name="Reviewer",
                        ticket_ref="GOV-55",
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_role="REVIEWER",
                    x_request_id="req-signoff-reviewer-governance-ticket",
                )
            )

        self.assertEqual(payload["signoffs"][0]["signer_role"], "legal_owner_optional")
        self.assertEqual(payload["signoffs"][0]["signoff_method"], "governance_ticket")
        self.assertEqual(conn.commit_calls, 1)

    def test_record_manual_package_signoff_rejects_reviewer_for_compliance_role(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_record_authorization_denial") as record_denial:
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="compliance_owner",
                            decision="approved",
                            signoff_method="governance_ticket",
                            signer_display_name="Reviewer",
                            ticket_ref="GOV-56",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="REVIEWER",
                        x_request_id="req-signoff-reviewer-mismatch",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertEqual(exc_info.exception.detail, "manual_package_signer_role_mismatch")
        self.assertIsNotNone(record_denial.call_args)
        assert record_denial.call_args is not None
        self.assertEqual(record_denial.call_args.kwargs["effective_role"], "REVIEWER")
        self.assertEqual(record_denial.call_args.kwargs["allowed_roles"], {"legal_owner_optional"})
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_record_manual_package_signoff_rejects_duplicate_role(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        signoffs = [
            _build_signoff_row(
                signoff_id="22222222-2222-2222-2222-222222222222",
                signer_role="compliance_owner",
            )
        ]

        with (
            patch.object(main, "_require_manual_package_signoff_role_binding", return_value="ADMIN"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                return_value=(_build_seal_row(status="pending_signoff"), signoffs),
            ),
        ):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="compliance_owner",
                            decision="approved",
                            signoff_method="platform_authenticated_2fa",
                            signer_display_name="Compliance Owner",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="ADMIN",
                        x_request_id="req-signoff-duplicate",
                        x_mfa_mode="local_totp",
                        x_2fa="ok",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 409)
        self.assertEqual(exc_info.exception.detail, "manual_package_signoff_role_already_recorded")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_record_manual_package_signoff_rejects_locked_seal(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with (
            patch.object(main, "_require_manual_package_signoff_role_binding", return_value="ADMIN"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                return_value=(_build_seal_row(status="sealed"), []),
            ),
        ):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.record_manual_package_signoff(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSignoffRecordRequest(
                            signer_role="ops_owner",
                            decision="approved",
                            signoff_method="platform_authenticated_2fa",
                            signer_display_name="Ops Owner",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="ADMIN",
                        x_request_id="req-signoff-locked",
                        x_mfa_mode="local_totp",
                        x_2fa="ok",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 409)
        self.assertEqual(exc_info.exception.detail, "manual_package_seal_locked")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_finalize_manual_package_seal_requires_ready_status(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                return_value=(
                    _build_seal_row(status="pending_signoff"),
                    [
                        _build_signoff_row(
                            signoff_id="22222222-2222-2222-2222-222222222222",
                            signer_role="compliance_owner",
                        )
                    ],
                ),
            ),
        ):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.finalize_manual_package_seal(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageFinalizeRequest(metadata={"source": "unit-test"}),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="AUDITOR",
                        x_request_id="req-finalize-not-ready",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 409)
        self.assertEqual(exc_info.exception.detail, "manual_package_seal_not_ready")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_finalize_manual_package_seal_persists_signed_envelope_and_audit_metadata(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        ready_seal = _build_seal_row(status="ready_to_seal")
        sealed_seal = _build_seal_row(
            status="sealed",
            signature_algorithm="HS256",
            certificate_bundle_ref="local-hs256-trust-bundle",
            seal_envelope={"protected": "header", "payload": "body", "signature": "sig"},
            verification_summary={
                "verified": True,
                "seal_backend": "local_hs256",
                "verification_method": "local_hs256_self_check",
            },
        )
        approved_signoffs = [
            _build_signoff_row(
                signoff_id="22222222-2222-2222-2222-222222222222",
                signer_role="compliance_owner",
            ),
            _build_signoff_row(
                signoff_id="33333333-3333-3333-3333-333333333333",
                signer_role="ops_owner",
            ),
        ]

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value="linked-user-1"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[
                    (ready_seal, approved_signoffs),
                    (sealed_seal, approved_signoffs),
                ],
            ),
            patch.object(
                main,
                "_finalize_manual_package_with_institutional_seal_service",
                return_value={
                    "signature_algorithm": "HS256",
                    "kms_key_ref": "manual-package-local-hs256",
                    "certificate_fingerprint_sha256": None,
                    "certificate_bundle_ref": "local-hs256-trust-bundle",
                    "seal_envelope": {"protected": "header", "payload": "body", "signature": "sig"},
                    "verification_summary": {
                        "verified": True,
                        "seal_backend": "local_hs256",
                        "verification_method": "local_hs256_self_check",
                    },
                },
            ),
            patch.object(main, "_record_manual_package_audit_event") as record_audit_event,
        ):
            payload = asyncio.run(
                main.finalize_manual_package_seal(
                    UUID("11111111-1111-1111-1111-111111111111"),
                    body=main.ManualPackageFinalizeRequest(metadata={"source": "unit-test"}),
                    pool=pool,
                    x_org_id="org-1",
                    x_linked_user_id="linked-user-1",
                    x_role="AUDITOR",
                    x_request_id="req-finalize-ok",
                )
            )

        self.assertEqual(payload["seal_status"], "sealed")
        self.assertEqual(payload["signature_algorithm"], "HS256")
        self.assertEqual(payload["verification_summary"]["seal_backend"], "local_hs256")
        self.assertEqual(conn.commit_calls, 1)
        self.assertEqual(len(cursor.execute_calls), 1)
        update_query, update_params = cursor.execute_calls[0]
        self.assertIn("UPDATE evidence_package_seals", update_query)
        self.assertIsNotNone(update_params)
        assert update_params is not None
        self.assertEqual(update_params[0], "sealed")
        self.assertEqual(update_params[1], "HS256")
        self.assertEqual(update_params[4], "local-hs256-trust-bundle")
        self.assertIsNotNone(record_audit_event.call_args)
        assert record_audit_event.call_args is not None
        audit_metadata = record_audit_event.call_args.kwargs["metadata"]
        self.assertEqual(audit_metadata["seal_backend"], "local_hs256")
        self.assertEqual(audit_metadata["signature_algorithm"], "HS256")
        self.assertEqual(audit_metadata["package_sha256"], "a" * 64)

    def test_finalize_manual_package_seal_rejects_auditor_mutation(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_record_authorization_denial") as record_denial:
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.finalize_manual_package_seal(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageFinalizeRequest(metadata={"source": "unit-test"}),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="AUDITOR",
                        x_request_id="req-finalize-auditor-denied",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 403)
        self.assertEqual(exc_info.exception.detail, "manual_package_admin_role_required")
        self.assertIsNotNone(record_denial.call_args)
        assert record_denial.call_args is not None
        self.assertEqual(record_denial.call_args.kwargs["effective_role"], "AUDITOR")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_revoke_manual_package_seal_allows_presealed_governance_and_records_reason(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)
        pending_seal = _build_seal_row(status="pending_signoff")
        revoked_seal = _build_seal_row(status="revoked", revoked_at=_dt("2026-07-08T10:10:00+00:00"))

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[(pending_seal, []), (revoked_seal, [])],
            ),
            patch.object(main, "_record_manual_package_audit_event") as record_audit_event,
        ):
            payload = asyncio.run(
                main.revoke_manual_package_seal(
                    UUID("11111111-1111-1111-1111-111111111111"),
                    body=main.ManualPackageRevokeRequest(
                        ticket_ref="GOV-123",
                        reason="Documento substituido",
                        metadata={"source": "unit-test"},
                    ),
                    pool=pool,
                    x_org_id="org-1",
                    x_role="ADMIN",
                    x_request_id="req-revoke-ok",
                )
            )

        self.assertEqual(payload["seal_status"], "revoked")
        self.assertIsNotNone(payload["revoked_at"])
        self.assertEqual(conn.commit_calls, 1)
        update_query, update_params = cursor.execute_calls[0]
        self.assertIn("UPDATE evidence_package_seals", update_query)
        self.assertIsNotNone(update_params)
        assert update_params is not None
        self.assertEqual(update_params[0], "revoked")
        self.assertIsNotNone(record_audit_event.call_args)
        assert record_audit_event.call_args is not None
        audit_metadata = record_audit_event.call_args.kwargs["metadata"]
        self.assertEqual(audit_metadata["previous_seal_status"], "pending_signoff")
        self.assertEqual(audit_metadata["ticket_ref"], "GOV-123")
        self.assertEqual(audit_metadata["reason"], "Documento substituido")

    def test_revoke_manual_package_seal_rejects_superseded_status(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                return_value=(
                    _build_seal_row(
                        status="superseded",
                        superseded_by_seal_id=UUID("44444444-4444-4444-4444-444444444444"),
                    ),
                    [],
                ),
            ),
        ):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.revoke_manual_package_seal(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageRevokeRequest(
                            ticket_ref="GOV-321",
                            reason="Nao deveria revogar",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="ADMIN",
                        x_request_id="req-revoke-superseded",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 409)
        self.assertEqual(exc_info.exception.detail, "manual_package_seal_already_superseded")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_supersede_manual_package_seal_requires_replacement_to_be_sealed(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with (
            patch.object(main, "_require_role_with_audit"),
            patch.object(main, "_apply_rls_context"),
            patch.object(
                main,
                "_load_manual_package_seal",
                side_effect=[
                    (_build_seal_row(status="sealed"), []),
                    (
                        _build_seal_row(
                            seal_id="44444444-4444-4444-4444-444444444444",
                            status="pending_signoff",
                            package_sha256="b" * 64,
                        ),
                        [],
                    ),
                ],
            ),
        ):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.supersede_manual_package_seal(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSupersedeRequest(
                            superseded_by_seal_id=UUID("44444444-4444-4444-4444-444444444444"),
                            ticket_ref="GOV-555",
                            reason="Nova versao do pacote",
                            metadata={"source": "unit-test"},
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="AUDITOR",
                        x_request_id="req-supersede-target-not-sealed",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 409)
        self.assertEqual(exc_info.exception.detail, "manual_package_supersede_target_not_sealed")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)

    def test_supersede_manual_package_seal_rejects_self_target(self) -> None:
        cursor = _FakeCursor()
        conn = _FakeConnection(cursor)
        pool = _FakePool(conn)

        with patch.object(main, "_require_role_with_audit"):
            with self.assertRaises(main.HTTPException) as exc_info:
                asyncio.run(
                    main.supersede_manual_package_seal(
                        UUID("11111111-1111-1111-1111-111111111111"),
                        body=main.ManualPackageSupersedeRequest(
                            superseded_by_seal_id=UUID("11111111-1111-1111-1111-111111111111"),
                            ticket_ref="GOV-555",
                            reason="Target invalido",
                        ),
                        pool=pool,
                        x_org_id="org-1",
                        x_role="AUDITOR",
                        x_request_id="req-supersede-self",
                    )
                )

        self.assertEqual(exc_info.exception.status_code, 422)
        self.assertEqual(exc_info.exception.detail, "manual_package_supersede_target_invalid")
        self.assertEqual(cursor.execute_calls, [])
        self.assertEqual(conn.commit_calls, 0)


if __name__ == "__main__":
    unittest.main()
