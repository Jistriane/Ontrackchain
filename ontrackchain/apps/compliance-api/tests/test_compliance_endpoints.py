from __future__ import annotations

import asyncio
import importlib
import sys
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    main: Any = importlib.import_module("compliance_api.main")
    MAIN_IMPORT_AVAILABLE = True
except ModuleNotFoundError:
    main = None
    MAIN_IMPORT_AVAILABLE = False


class _FakeBlocksCursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self._fetchone: dict[str, Any] | None = None
        self._fetchall: list[dict[str, Any]] = []

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized_query.startswith("SELECT COUNT(*) AS total FROM preventive_blocks WHERE"):
            filtered_rows = self._filter_rows(normalized_query, params_tuple)
            self._fetchone = {"total": len(filtered_rows)}
            self._fetchall = []
            return

        if normalized_query.startswith("SELECT id, case_id, target_address, target_chain, block_action, review_status, status,"):
            filtered_rows = self._filter_rows(normalized_query, params_tuple[:-2])
            limit = int(params_tuple[-2])
            offset = int(params_tuple[-1])
            sorted_rows = sorted(
                filtered_rows,
                key=lambda row: (row["block_timestamp"], str(row["id"])),
                reverse=True,
            )
            self._fetchone = None
            self._fetchall = [dict(row) for row in sorted_rows[offset : offset + limit]]
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def _filter_rows(self, normalized_query: str, params_tuple: tuple[Any, ...]) -> list[dict[str, Any]]:
        organization_id = str(params_tuple[0])
        rows = [dict(row) for row in self.rows if str(row["organization_id"]) == organization_id]
        if "AND status = %s" in normalized_query:
            expected_status = str(params_tuple[1])
            rows = [row for row in rows if str(row["status"]) == expected_status]
        return rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._fetchone

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._fetchall)

    def __enter__(self) -> "_FakeBlocksCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeBlocksConnection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def cursor(self) -> _FakeBlocksCursor:
        return _FakeBlocksCursor(self.rows)

    def __enter__(self) -> "_FakeBlocksConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeBlocksPool:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def connection(self) -> _FakeBlocksConnection:
        return _FakeBlocksConnection(self.rows)


class _FakeEndpointCursor:
    def __init__(self, *, lift_row: dict[str, Any] | None = None) -> None:
        self.lift_row = dict(lift_row) if lift_row else None
        self._fetchone: dict[str, Any] | None = None
        self.executed_updates: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)
        if normalized_query.startswith("UPDATE preventive_blocks"):
            self.executed_updates.append((normalized_query, params_tuple))
            if self.lift_row and str(self.lift_row["id"]) == str(params_tuple[6]) and str(self.lift_row["organization_id"]) == str(params_tuple[7]):
                self.lift_row["status"] = "LIFTED"
                self.lift_row["review_status"] = "LIFTED"
                self.lift_row["lifted_at"] = params_tuple[0]
                self.lift_row["lifted_reason"] = params_tuple[2]
                self.lift_row["review_note"] = params_tuple[5]
                self._fetchone = {
                    "id": self.lift_row["id"],
                    "status": self.lift_row["status"],
                    "review_status": self.lift_row["review_status"],
                    "case_id": self.lift_row["case_id"],
                    "target_address": self.lift_row["target_address"],
                    "target_chain": self.lift_row["target_chain"],
                }
            else:
                self._fetchone = None
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def fetchone(self) -> dict[str, Any] | None:
        return self._fetchone

    def __enter__(self) -> "_FakeEndpointCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeEndpointConnection:
    def __init__(self, *, lift_row: dict[str, Any] | None = None) -> None:
        self.cursor_instance = _FakeEndpointCursor(lift_row=lift_row)
        self.commit_calls = 0

    def cursor(self) -> _FakeEndpointCursor:
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_calls += 1

    def __enter__(self) -> "_FakeEndpointConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeEndpointPool:
    def __init__(self, *, lift_row: dict[str, Any] | None = None) -> None:
        self.connection_instance = _FakeEndpointConnection(lift_row=lift_row)

    def connection(self) -> _FakeEndpointConnection:
        return self.connection_instance


@unittest.skipUnless(MAIN_IMPORT_AVAILABLE, "compliance_api.main dependencies not installed in current interpreter")
class ComplianceEndpointContractTests(unittest.TestCase):
    def _build_block_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "organization_id": "org-1",
                "id": uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                "case_id": uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
                "target_address": "0x1111111111111111111111111111111111111111",
                "target_chain": "ethereum",
                "block_action": "BLOCK_AND_ALERT",
                "review_status": "CONFIRMED",
                "status": "CONFIRMED",
                "regulatory_basis": ["OFAC corroborated hit"],
                "sanctions_hits": [{"list_name": "OFAC"}],
                "decision_confidence": 0.97,
                "coaf_ros_required": True,
                "evidence_hash": "hash-block-1",
                "block_timestamp": datetime(2026, 7, 16, 8, 0, tzinfo=timezone.utc),
                "lifted_at": None,
                "lifted_reason": None,
                "review_note": "Primary confirmed block",
            },
            {
                "organization_id": "org-1",
                "id": uuid.UUID("aa86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                "case_id": uuid.UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd"),
                "target_address": "0x2222222222222222222222222222222222222222",
                "target_chain": "polygon",
                "block_action": "BLOCK_IMMEDIATE",
                "review_status": "CONFIRMED",
                "status": "CONFIRMED",
                "regulatory_basis": ["Internal policy OTC-HIGH-RISK-07"],
                "sanctions_hits": [{"list_name": "EU"}],
                "decision_confidence": 0.93,
                "coaf_ros_required": False,
                "evidence_hash": "hash-block-2",
                "block_timestamp": datetime(2026, 7, 15, 18, 35, tzinfo=timezone.utc),
                "lifted_at": None,
                "lifted_reason": None,
                "review_note": "Secondary confirmed block",
            },
            {
                "organization_id": "org-1",
                "id": uuid.UUID("cc86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                "case_id": None,
                "target_address": "0x3333333333333333333333333333333333333333",
                "target_chain": "base",
                "block_action": "BLOCK_AND_ALERT",
                "review_status": "LIFTED",
                "status": "LIFTED",
                "regulatory_basis": ["False positive resolution"],
                "sanctions_hits": [],
                "decision_confidence": 0.55,
                "coaf_ros_required": False,
                "evidence_hash": "hash-block-3",
                "block_timestamp": datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc),
                "lifted_at": datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
                "lifted_reason": "Lifted after manual review",
                "review_note": "Lifted block",
            },
        ]

    def _build_lift_row(self) -> dict[str, Any]:
        return {
            "id": uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
            "organization_id": "11111111-1111-4111-8111-111111111111",
            "case_id": uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            "target_address": "0x1111111111111111111111111111111111111111",
            "target_chain": "ethereum",
            "status": "CONFIRMED",
            "review_status": "CONFIRMED",
            "lifted_at": None,
            "lifted_reason": None,
            "review_note": None,
        }

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
                    x_role="ANALYST",
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
                    x_role="ANALYST",
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
                    x_role="ANALYST",
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
        screening = SimpleNamespace(
            has_hit=False,
            hits=[],
            screening_duration_ms=9,
            screened_at="2026-07-19T12:00:00Z",
        )

        with (
            patch.object(main, "_screen_address_local", return_value=screening),
            patch.object(main, "_record_optional_compliance_audit") as audit_mock,
            patch.object(main, "_record_optional_compliance_evidence"),
        ):
            response = asyncio.run(
                main.sanctions_check(
                    address="0x456",
                    pool=object(),
                    chain="base",
                    lists="OFAC, UN ,COAF",
                    x_org_id="org-1",
                    x_role="ANALYST",
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
        self.assertFalse(response.hit)
        self.assertEqual(response.matched_lists, [])
        self.assertIsNone(response.entity_name)
        self.assertIsNone(response.designation_date)
        audit_mock.assert_called_once()
        metadata = audit_mock.call_args.kwargs["metadata"]
        self.assertEqual(metadata["lists"], ["OFAC", "UN", "COAF"])
        self.assertEqual(metadata["delivery_mode"], "local_cache")

    def test_serialize_counterparty_detail_preserves_review_snapshot_and_regulatory_fields(self) -> None:
        row = {
            "id": uuid.UUID("22222222-2222-4222-8222-222222222222"),
            "legal_name": "Counterparty QA",
            "counterparty_type": "CLIENTE_PJ",
            "document_type": "CNPJ",
            "document_number": "12.345.678/0001-90",
            "document_country": "BRA",
            "registration_data": {"email": "qa@example.com"},
            "beneficial_owners": [{"name": "Owner QA", "document": "123", "ownership_pct": 80}],
            "wallet_addresses": [{"chain": "ethereum", "address": "0xabc", "label": "primary"}],
            "risk_level": 4,
            "risk_rationale": "Escalated corridor risk",
            "onchain_risk_score": 88,
            "onchain_analysis": {"provider": "local"},
            "is_pep": False,
            "pep_detail": {},
            "sanctions_cleared": False,
            "sanctions_hits": [{"list": "OFAC"}],
            "kyc_status": "UNDER_REVIEW",
            "enhanced_dd_required": True,
            "enhanced_dd_status": "completed",
            "enhanced_dd_findings": "Documentacao validada",
            "enhanced_dd_checklist": {"sof_description": "Receita operacional", "sof_document_ref": "SOF-001"},
            "next_review_date": datetime(2026, 8, 1, tzinfo=timezone.utc),
            "last_reviewed_at": datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc),
            "status": "UNDER_REVIEW",
            "created_at": datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc),
        }

        response = main._serialize_counterparty_detail(row)

        self.assertEqual(str(response.counterparty_id), "22222222-2222-4222-8222-222222222222")
        self.assertEqual(response.legal_name, "Counterparty QA")
        self.assertEqual(response.review_snapshot.dd_review_status, "completed")
        self.assertEqual(response.review_snapshot.sof_document_ref, "SOF-001")
        self.assertEqual(response.registration_data["email"], "qa@example.com")
        self.assertEqual(response.wallet_addresses[0]["address"], "0xabc")
        self.assertEqual(response.sanctions_hits[0]["list"], "OFAC")

    def test_serialize_counterparty_history_item_preserves_audit_fields(self) -> None:
        row = {
            "id": uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            "counterparty_id": uuid.UUID("22222222-2222-4222-8222-222222222222"),
            "changed_by_user_id": uuid.UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
            "change_type": "DD_REVIEW_UPDATED",
            "field_changed": "enhanced_dd_status",
            "old_value": "pending",
            "new_value": "completed",
            "change_reason": "Documentacao validada",
            "changed_at": datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc),
            "evidence_hash": "hash-counterparty-1",
        }

        response = main._serialize_counterparty_history_item(row)

        self.assertEqual(str(response.id), "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertEqual(response.change_type, "DD_REVIEW_UPDATED")
        self.assertEqual(response.field_changed, "enhanced_dd_status")
        self.assertEqual(response.new_value, "completed")
        self.assertEqual(response.evidence_hash, "hash-counterparty-1")

    def test_serialize_block_list_item_preserves_regulatory_and_lift_fields(self) -> None:
        row = {
            "id": uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
            "case_id": uuid.UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
            "target_address": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
            "target_chain": "ethereum",
            "block_action": "BLOCK_AND_ALERT",
            "review_status": "CONFIRMED",
            "status": "CONFIRMED",
            "regulatory_basis": ["OFAC corroborated hit", "Internal policy OTC-HIGH-RISK-07"],
            "sanctions_hits": [{"list_name": "OFAC"}, {"list_name": "EU"}],
            "decision_confidence": 0.94,
            "coaf_ros_required": True,
            "evidence_hash": "hash-block-1",
            "block_timestamp": datetime(2026, 7, 15, 18, 35, tzinfo=timezone.utc),
            "lifted_at": datetime(2026, 7, 16, 8, 15, tzinfo=timezone.utc),
            "lifted_reason": "False positive confirmed",
            "review_note": "Lift approved after manual review",
        }

        response = main._serialize_block_list_item(row)

        self.assertEqual(str(response.block_id), "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f")
        self.assertEqual(str(response.case_id), "cccccccc-cccc-4ccc-8ccc-cccccccccccc")
        self.assertEqual(response.address, "0x8ba1f109551bD432803012645Ac136ddd64DBA72")
        self.assertEqual(response.action, "BLOCK_AND_ALERT")
        self.assertEqual(response.review_status, "CONFIRMED")
        self.assertEqual(response.status, "CONFIRMED")
        self.assertEqual(response.matched_lists, ["OFAC", "EU"])
        self.assertTrue(response.requires_coaf_report)
        self.assertEqual(response.evidence_hash, "hash-block-1")
        self.assertEqual(response.lifted_reason, "False positive confirmed")
        self.assertEqual(response.review_note, "Lift approved after manual review")

    def test_list_blocks_filters_by_status_and_preserves_pagination_contract(self) -> None:
        rows = self._build_block_rows()
        pool = _FakeBlocksPool(rows)

        with (
            patch.object(main, "_require_block_read_role") as role_mock,
            patch.object(main, "_apply_rls_context") as rls_mock,
        ):
            response = asyncio.run(
                main.list_blocks(
                    pool=pool,
                    limit=1,
                    offset=1,
                    status="confirmed",
                    x_org_id="org-1",
                    x_user_id="external-user-1",
                    x_linked_user_id="11111111-1111-1111-1111-111111111111",
                    x_role="ANALYST",
                    x_request_id="req-block-list-1",
                )
            )

        role_mock.assert_called_once()
        rls_mock.assert_called_once()
        role_kwargs = role_mock.call_args.kwargs
        self.assertEqual(role_kwargs["organization_id"], "org-1")
        self.assertEqual(role_kwargs["user_id"], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(role_kwargs["external_user_id"], "external-user-1")
        self.assertEqual(role_kwargs["request_id"], "req-block-list-1")
        self.assertEqual(role_kwargs["x_role"], "ANALYST")
        self.assertEqual(role_kwargs["endpoint"], "/api/v1/compliance/blocks")
        self.assertEqual(role_kwargs["method"], "GET")
        self.assertEqual(response.total, 2)
        self.assertEqual(response.limit, 1)
        self.assertEqual(response.offset, 1)
        self.assertEqual(len(response.items), 1)
        self.assertEqual(str(response.items[0].block_id), "aa86c0d1-1b7e-55dd-8e6b-a8f4318fb91f")
        self.assertEqual(response.items[0].address, "0x2222222222222222222222222222222222222222")
        self.assertEqual(response.items[0].chain, "polygon")
        self.assertEqual(response.items[0].matched_lists, ["EU"])
        self.assertFalse(response.items[0].requires_coaf_report)
        self.assertEqual(response.items[0].review_note, "Secondary confirmed block")

    def test_list_blocks_without_status_returns_all_items_sorted_by_timestamp_desc(self) -> None:
        pool = _FakeBlocksPool(self._build_block_rows())

        with (
            patch.object(main, "_require_block_read_role") as role_mock,
            patch.object(main, "_apply_rls_context") as rls_mock,
        ):
            response = asyncio.run(
                main.list_blocks(
                    pool=pool,
                    limit=10,
                    offset=0,
                    status=None,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_linked_user_id=None,
                    x_role="OTK_COMPLIANCE_OFFICER",
                    x_request_id="req-block-list-all",
                )
            )

        role_mock.assert_called_once()
        rls_mock.assert_called_once()
        role_kwargs = role_mock.call_args.kwargs
        self.assertEqual(role_kwargs["user_id"], "11111111-1111-1111-1111-111111111111")
        self.assertIsNone(role_kwargs["external_user_id"])
        self.assertEqual(role_kwargs["x_role"], "OTK_COMPLIANCE_OFFICER")
        self.assertEqual(response.total, 3)
        self.assertEqual([str(item.block_id) for item in response.items], [
            "cc86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
            "bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
            "aa86c0d1-1b7e-55dd-8e6b-a8f4318fb91f",
        ])
        self.assertEqual(response.items[0].status, "LIFTED")
        self.assertEqual(response.items[0].lifted_reason, "Lifted after manual review")
        self.assertEqual(response.items[1].matched_lists, ["OFAC"])

    def test_list_blocks_excludes_other_organizations_and_returns_empty_page_when_offset_exceeds_total(self) -> None:
        rows = self._build_block_rows() + [
            {
                "organization_id": "org-2",
                "id": uuid.UUID("dd86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                "case_id": None,
                "target_address": "0x4444444444444444444444444444444444444444",
                "target_chain": "arbitrum",
                "block_action": "BLOCK_AND_ALERT",
                "review_status": "CONFIRMED",
                "status": "CONFIRMED",
                "regulatory_basis": ["Foreign organization row"],
                "sanctions_hits": [{"list_name": "OFAC"}],
                "decision_confidence": 0.99,
                "coaf_ros_required": True,
                "evidence_hash": "hash-block-foreign-org",
                "block_timestamp": datetime(2026, 7, 18, 9, 0, tzinfo=timezone.utc),
                "lifted_at": None,
                "lifted_reason": None,
                "review_note": "Must stay invisible to org-1",
            }
        ]
        pool = _FakeBlocksPool(rows)

        with (
            patch.object(main, "_require_block_read_role") as role_mock,
            patch.object(main, "_apply_rls_context") as rls_mock,
        ):
            first_page = asyncio.run(
                main.list_blocks(
                    pool=pool,
                    limit=10,
                    offset=0,
                    status=None,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_linked_user_id=None,
                    x_role="ANALYST",
                    x_request_id="req-block-list-org-1-first-page",
                )
            )
            empty_page = asyncio.run(
                main.list_blocks(
                    pool=pool,
                    limit=10,
                    offset=99,
                    status=None,
                    x_org_id="org-1",
                    x_user_id="11111111-1111-1111-1111-111111111111",
                    x_linked_user_id=None,
                    x_role="ANALYST",
                    x_request_id="req-block-list-org-1-empty-page",
                )
            )

        self.assertEqual(role_mock.call_count, 2)
        self.assertEqual(rls_mock.call_count, 2)
        self.assertEqual(first_page.total, 3)
        self.assertEqual(len(first_page.items), 3)
        self.assertNotIn("dd86c0d1-1b7e-55dd-8e6b-a8f4318fb91f", [str(item.block_id) for item in first_page.items])
        self.assertEqual(empty_page.total, 3)
        self.assertEqual(empty_page.offset, 99)
        self.assertEqual(empty_page.items, [])

    def test_evaluate_block_returns_contract_and_records_audit_context(self) -> None:
        org_id = "11111111-1111-4111-8111-111111111111"
        linked_user_id = "22222222-2222-4222-8222-222222222222"
        block_id = uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f")
        pool = _FakeEndpointPool()
        screening = SimpleNamespace(
            has_hit=True,
            hits=[
                SimpleNamespace(
                    list_name="OFAC",
                    entity_name="Wallet QA",
                    confidence=0.98,
                    designation_date="2026-07-15",
                    regulatory_basis=["OFAC corroborated hit"],
                )
            ],
            screened_lists=["OFAC", "EU"],
            screening_duration_ms=12,
            screened_at="2026-07-19T12:00:00Z",
        )
        decision = SimpleNamespace(
            action="BLOCK_AND_ALERT",
            requires_coaf_report=True,
            decision_confidence=0.97,
            regulatory_basis=["BCB 520 Art. 43 §2° V"],
            evidence_hash="hash-block-evaluate",
            block_id=block_id,
        )

        with (
            patch.object(main, "_require_block_evaluate_role") as role_mock,
            patch.object(main, "_validate_chain", return_value="ethereum"),
            patch.object(main, "_screen_address_local", return_value=screening),
            patch.object(main, "_apply_rls_context") as rls_mock,
            patch.object(main, "_resolve_persisted_user_id", return_value=linked_user_id),
            patch.object(main, "_record_audit_log") as audit_mock,
            patch.object(main, "PreventiveBlockAgent") as agent_cls,
        ):
            agent_cls.return_value.evaluate = AsyncMock(return_value=decision)
            response = asyncio.run(
                main.evaluate_block(
                    main.BlockEvaluateRequest(
                        address="0x1111111111111111111111111111111111111111",
                        chain="ethereum",
                        aml_score=91,
                        is_international_transfer=True,
                    ),
                    pool=pool,
                    x_org_id=org_id,
                    x_user_id="external-user-1",
                    x_linked_user_id=linked_user_id,
                    x_role="ANALYST",
                    x_request_id="req-block-evaluate-1",
                )
            )

        role_mock.assert_called_once()
        rls_mock.assert_called_once()
        audit_mock.assert_called_once()
        agent_cls.assert_called_once()
        agent_kwargs = agent_cls.call_args.kwargs
        self.assertIsNotNone(agent_kwargs["evidence_svc"])
        self.assertIsNotNone(agent_kwargs["db"])
        evaluate_kwargs = agent_cls.return_value.evaluate.call_args.kwargs
        self.assertEqual(evaluate_kwargs["wallet_context"].aml_score, 91)
        self.assertTrue(evaluate_kwargs["wallet_context"].is_international_transfer)
        self.assertEqual(evaluate_kwargs["auth"].user_id, uuid.UUID(linked_user_id))
        self.assertEqual(response.action, "BLOCK_AND_ALERT")
        self.assertTrue(response.requires_coaf_report)
        self.assertEqual(response.matched_lists, ["OFAC"])
        self.assertEqual(response.evidence_hash, "hash-block-evaluate")
        self.assertEqual(response.block_id, block_id)
        audit_kwargs = audit_mock.call_args.kwargs
        self.assertEqual(audit_kwargs["organization_id"], org_id)
        self.assertEqual(audit_kwargs["user_id"], linked_user_id)
        self.assertEqual(audit_kwargs["action"], "preventive_block_evaluated")
        self.assertEqual(audit_kwargs["metadata"]["request_id"], "req-block-evaluate-1")
        self.assertEqual(audit_kwargs["metadata"]["external_user_id"], "external-user-1")
        self.assertEqual(pool.connection_instance.commit_calls, 1)

    def test_lift_block_returns_contract_and_emits_audit_and_evidence(self) -> None:
        org_id = "11111111-1111-4111-8111-111111111111"
        linked_user_id = "22222222-2222-4222-8222-222222222222"
        lift_row = self._build_lift_row()
        pool = _FakeEndpointPool(lift_row=lift_row)

        with (
            patch.object(main, "_require_external_provider_2fa") as twofa_mock,
            patch.object(main, "_require_block_lift_role") as role_mock,
            patch.object(main, "_apply_rls_context") as rls_mock,
            patch.object(main, "_resolve_persisted_user_id", return_value=linked_user_id),
            patch.object(main, "_record_audit_log") as audit_mock,
            patch.object(main, "emit_evidence_event_sync") as evidence_mock,
        ):
            response = asyncio.run(
                main.lift_block(
                    lift_row["id"],
                    main.BlockLiftRequest(reason="False positive resolved"),
                    pool=pool,
                    x_org_id=org_id,
                    x_user_id="external-user-1",
                    x_linked_user_id=linked_user_id,
                    x_role="COMPLIANCE_OFFICER",
                    x_mfa_mode="external_provider",
                    x_mfa_provider_homologated="true",
                    x_request_id="req-block-lift-1",
                )
            )

        twofa_mock.assert_called_once()
        role_mock.assert_called_once()
        rls_mock.assert_called_once()
        audit_mock.assert_called_once()
        evidence_mock.assert_called_once()
        self.assertEqual(response.block_id, lift_row["id"])
        self.assertEqual(response.status, "LIFTED")
        self.assertEqual(response.review_status, "LIFTED")
        self.assertTrue(response.lifted_at)
        audit_kwargs = audit_mock.call_args.kwargs
        self.assertEqual(audit_kwargs["organization_id"], org_id)
        self.assertEqual(audit_kwargs["user_id"], linked_user_id)
        self.assertEqual(audit_kwargs["action"], "preventive_block_lifted")
        self.assertEqual(audit_kwargs["metadata"]["reason"], "False positive resolved")
        self.assertEqual(audit_kwargs["metadata"]["external_user_id"], "external-user-1")
        evidence_kwargs = evidence_mock.call_args.kwargs
        self.assertEqual(evidence_kwargs["org_id"], org_id)
        self.assertEqual(evidence_kwargs["event_type"], "BLOCK_LIFTED")
        self.assertEqual(evidence_kwargs["case_id"], str(lift_row["case_id"]))
        self.assertEqual(evidence_kwargs["event_payload"]["reason"], "False positive resolved")
        self.assertEqual(pool.connection_instance.commit_calls, 1)

    def test_lift_block_requires_persisted_linked_user_context(self) -> None:
        org_id = "11111111-1111-4111-8111-111111111111"
        linked_user_id = "22222222-2222-4222-8222-222222222222"
        pool = _FakeEndpointPool(lift_row=self._build_lift_row())

        with (
            patch.object(main, "_require_external_provider_2fa"),
            patch.object(main, "_require_block_lift_role"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value=None),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                asyncio.run(
                    main.lift_block(
                        uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                        main.BlockLiftRequest(reason="False positive resolved"),
                        pool=pool,
                        x_org_id=org_id,
                        x_user_id="external-user-1",
                        x_linked_user_id=linked_user_id,
                        x_role="COMPLIANCE_OFFICER",
                        x_mfa_mode="external_provider",
                        x_mfa_provider_homologated="true",
                        x_request_id="req-block-lift-missing-linked",
                    )
                )

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "linked_user_required_for_block_lift")
        self.assertEqual(pool.connection_instance.commit_calls, 0)

    def test_lift_block_returns_not_found_when_block_is_missing(self) -> None:
        org_id = "11111111-1111-4111-8111-111111111111"
        linked_user_id = "22222222-2222-4222-8222-222222222222"
        pool = _FakeEndpointPool(lift_row=None)

        with (
            patch.object(main, "_require_external_provider_2fa"),
            patch.object(main, "_require_block_lift_role"),
            patch.object(main, "_apply_rls_context"),
            patch.object(main, "_resolve_persisted_user_id", return_value=linked_user_id),
        ):
            with self.assertRaises(main.HTTPException) as ctx:
                asyncio.run(
                    main.lift_block(
                        uuid.UUID("bb86c0d1-1b7e-55dd-8e6b-a8f4318fb91f"),
                        main.BlockLiftRequest(reason="False positive resolved"),
                        pool=pool,
                        x_org_id=org_id,
                        x_user_id="external-user-1",
                        x_linked_user_id=linked_user_id,
                        x_role="COMPLIANCE_OFFICER",
                        x_mfa_mode="external_provider",
                        x_mfa_provider_homologated="true",
                        x_request_id="req-block-lift-not-found",
                    )
                )

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "preventive_block_not_found")
        self.assertEqual(pool.connection_instance.commit_calls, 0)


if __name__ == "__main__":
    unittest.main()
