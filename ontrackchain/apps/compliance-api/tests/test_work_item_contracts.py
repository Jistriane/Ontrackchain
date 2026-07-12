from __future__ import annotations

import asyncio
import importlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    HTTPException: Any = importlib.import_module("fastapi").HTTPException
    operations: Any = importlib.import_module("compliance_api.operations")
    OPERATIONS_IMPORT_AVAILABLE = True
except ModuleNotFoundError:
    HTTPException = Exception
    operations = None
    OPERATIONS_IMPORT_AVAILABLE = False


class _FakeWorkItemCursor:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._fetchone: dict[str, Any] | None = None
        self._fetchall: list[dict[str, Any]] = []

    def execute(self, query: str, params: tuple[Any, ...] | list[Any] = ()) -> None:
        normalized_query = " ".join(query.split())
        params_tuple = tuple(params)

        if normalized_query.startswith("SELECT set_config("):
            self._fetchone = {"set_config": params_tuple[0] if params_tuple else None}
            self._fetchall = []
            return

        if normalized_query == "SELECT 1 FROM users WHERE id = %s":
            self._fetchone = {"exists": 1} if str(params_tuple[0]) in self.state["users"] else None
            self._fetchall = []
            return

        if normalized_query == "SELECT 1":
            self._fetchone = {"exists": 1}
            self._fetchall = []
            return

        if normalized_query.startswith("INSERT INTO regulatory_work_items"):
            (
                organization_id,
                module,
                resource_type,
                resource_id,
                case_id,
                report_external_id,
                owner_user_id,
                assigned_by_user_id,
                queue_status,
                priority,
                due_at,
                sla_breached,
                title,
                note,
                metadata_json,
            ) = params_tuple
            now = datetime.now(timezone.utc)
            metadata = json.loads(metadata_json)
            existing = next(
                (
                    item
                    for item in self.state["work_items"].values()
                    if item["organization_id"] == str(organization_id)
                    and item["resource_type"] == resource_type
                    and str(item["resource_id"]) == str(resource_id)
                ),
                None,
            )
            if existing:
                merged_metadata = dict(existing["metadata"] or {})
                merged_metadata.update(metadata)
                existing.update(
                    {
                        "module": module,
                        "case_id": case_id or existing["case_id"],
                        "report_external_id": report_external_id or existing["report_external_id"],
                        "owner_user_id": owner_user_id or existing["owner_user_id"],
                        "assigned_by_user_id": assigned_by_user_id if owner_user_id else existing["assigned_by_user_id"],
                        "queue_status": queue_status,
                        "priority": priority,
                        "due_at": due_at,
                        "sla_breached": sla_breached,
                        "title": title or existing["title"],
                        "note": note or existing["note"],
                        "metadata": merged_metadata,
                        "updated_at": now,
                        "last_activity_at": now,
                    }
                )
                row = dict(existing)
            else:
                work_item_id = uuid4()
                row = {
                    "id": work_item_id,
                    "organization_id": str(organization_id),
                    "module": module,
                    "resource_type": resource_type,
                    "resource_id": UUID(str(resource_id)),
                    "case_id": case_id,
                    "report_external_id": report_external_id,
                    "owner_user_id": owner_user_id,
                    "assigned_by_user_id": assigned_by_user_id,
                    "queue_status": queue_status,
                    "priority": priority,
                    "due_at": due_at,
                    "sla_breached": sla_breached,
                    "title": title,
                    "note": note,
                    "metadata": metadata,
                    "created_at": now,
                    "updated_at": now,
                    "last_activity_at": now,
                }
                self.state["work_items"][str(work_item_id)] = row
            self._fetchone = row
            self._fetchall = []
            return

        if normalized_query.startswith("INSERT INTO regulatory_work_events"):
            (
                work_item_id,
                organization_id,
                actor_user_id,
                event_type,
                from_status,
                to_status,
                payload_json,
            ) = params_tuple
            self.state["events"].append(
                {
                    "work_item_id": str(work_item_id),
                    "organization_id": str(organization_id),
                    "actor_user_id": actor_user_id,
                    "event_type": event_type,
                    "from_status": from_status,
                    "to_status": to_status,
                    "payload": json.loads(payload_json),
                }
            )
            self._fetchone = None
            self._fetchall = []
            return

        if normalized_query.startswith("INSERT INTO audit_logs"):
            (
                organization_id,
                user_id,
                action,
                resource_type,
                resource_id,
                metadata_json,
            ) = params_tuple
            self.state["audit_logs"].append(
                {
                    "organization_id": str(organization_id),
                    "user_id": user_id,
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": str(resource_id) if resource_id else None,
                    "metadata": json.loads(metadata_json),
                }
            )
            self._fetchone = None
            self._fetchall = []
            return

        if normalized_query.startswith("SELECT COUNT(*) AS total FROM regulatory_work_items"):
            rows, _, _ = self._filter_work_items(normalized_query, params_tuple)
            self._fetchone = {"total": len(rows)}
            self._fetchall = []
            return

        if normalized_query.startswith("SELECT * FROM regulatory_work_items FROM regulatory_work_items"):
            rows, limit, offset = self._filter_work_items(normalized_query, params_tuple)
            sorted_rows = sorted(
                rows,
                key=lambda row: (
                    row["sla_breached"],
                    row["due_at"] is not None,
                    -(row["due_at"].timestamp()) if row["due_at"] else float("inf"),
                    -(row["last_activity_at"].timestamp()),
                    str(row["id"]),
                ),
                reverse=True,
            )
            self._fetchall = [dict(row) for row in sorted_rows[offset : offset + limit]]
            self._fetchone = None
            return

        if normalized_query == "SELECT * FROM regulatory_work_items WHERE id = %s AND organization_id = %s":
            work_item_id, organization_id = params_tuple
            row = self.state["work_items"].get(str(work_item_id))
            self._fetchone = dict(row) if row and row["organization_id"] == str(organization_id) else None
            self._fetchall = []
            return

        if normalized_query.startswith("UPDATE regulatory_work_items SET owner_user_id = %s,"):
            (
                owner_user_id,
                owner_user_id_compare,
                assigned_by_user_id,
                priority,
                queue_status,
                due_at,
                sla_breached,
                title,
                note,
                metadata_json,
                work_item_id,
                organization_id,
            ) = params_tuple
            current = self.state["work_items"].get(str(work_item_id))
            if not current or current["organization_id"] != str(organization_id):
                self._fetchone = None
                self._fetchall = []
                return
            now = datetime.now(timezone.utc)
            previous_owner = current["owner_user_id"]
            current.update(
                {
                    "owner_user_id": owner_user_id,
                    "assigned_by_user_id": assigned_by_user_id
                    if owner_user_id_compare != previous_owner
                    else current["assigned_by_user_id"],
                    "priority": priority or current["priority"],
                    "queue_status": queue_status,
                    "due_at": due_at,
                    "sla_breached": sla_breached,
                    "title": title or current["title"],
                    "note": note or current["note"],
                    "metadata": json.loads(metadata_json),
                    "updated_at": now,
                    "last_activity_at": now,
                }
            )
            self._fetchone = dict(current)
            self._fetchall = []
            return

        raise AssertionError(f"Query nao suportada no fake: {normalized_query}")

    def _filter_work_items(
        self, normalized_query: str, params_tuple: tuple[Any, ...]
    ) -> tuple[list[dict[str, Any]], int, int]:
        index = 0
        organization_id = str(params_tuple[index])
        index += 1
        rows = [
            dict(row)
            for row in self.state["work_items"].values()
            if row["organization_id"] == organization_id
        ]

        def consume_if(fragment: str, predicate) -> None:
            nonlocal index, rows
            if fragment in normalized_query:
                value = params_tuple[index]
                index += 1
                rows = [row for row in rows if predicate(row, value)]

        consume_if("AND module = %s", lambda row, value: row["module"] == value)
        consume_if("AND queue_status = %s", lambda row, value: row["queue_status"] == value)
        consume_if("AND owner_user_id = %s", lambda row, value: str(row["owner_user_id"]) == str(value))
        consume_if("AND priority = %s", lambda row, value: row["priority"] == value)
        consume_if("AND case_id = %s", lambda row, value: str(row["case_id"]) == str(value))
        consume_if("AND report_external_id = %s", lambda row, value: row["report_external_id"] == value)
        consume_if("AND resource_type = %s", lambda row, value: row["resource_type"] == value)
        consume_if(
            "AND due_at IS NOT NULL AND due_at <= %s",
            lambda row, value: row["due_at"] is not None and row["due_at"] <= value,
        )

        limit = params_tuple[index] if "LIMIT %s OFFSET %s" in normalized_query else len(rows)
        offset = params_tuple[index + 1] if "LIMIT %s OFFSET %s" in normalized_query else 0
        return rows, int(limit), int(offset)

    def fetchone(self) -> dict[str, Any] | None:
        return self._fetchone

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self._fetchall)

    def __enter__(self) -> "_FakeWorkItemCursor":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeWorkItemConnection:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self.commit = MagicMock()

    def cursor(self) -> _FakeWorkItemCursor:
        return _FakeWorkItemCursor(self.state)

    def __enter__(self) -> "_FakeWorkItemConnection":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        return None


class _FakeWorkItemPool:
    def __init__(self, state: dict[str, Any]) -> None:
        self.state = state
        self._connection = _FakeWorkItemConnection(state)

    def connection(self) -> _FakeWorkItemConnection:
        return self._connection


@unittest.skipUnless(OPERATIONS_IMPORT_AVAILABLE, "compliance_api.operations dependencies not installed in current interpreter")
class WorkItemContractTests(unittest.TestCase):
    def _build_state(self) -> tuple[dict[str, Any], _FakeWorkItemPool]:
        org_id = str(uuid4())
        linked_user_id = str(uuid4())
        owner_user_id = str(uuid4())
        state = {
            "organization_id": org_id,
            "users": {linked_user_id, owner_user_id},
            "work_items": {},
            "events": [],
            "audit_logs": [],
            "linked_user_id": linked_user_id,
            "owner_user_id": owner_user_id,
        }
        return state, _FakeWorkItemPool(state)

    def test_validate_module_resource_pair_accepts_canonical_pair(self) -> None:
        operations._validate_module_resource_pair("sanctions", "sanctions_screening")

    def test_validate_module_resource_pair_rejects_invalid_pair(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            operations._validate_module_resource_pair("sanctions", "operational_alert")

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail["code"], "invalid_module_resource_type_pair")
        self.assertEqual(ctx.exception.detail["expected_resource_type"], "sanctions_screening")

    def test_normalize_metadata_promotes_workspace_status_from_legacy_aliases(self) -> None:
        normalized = operations._normalize_work_item_metadata(
            resource_type="preventive_block",
            metadata={"local_block_status": "REVIEW"},
            case_id=None,
            owner_user_id=None,
            note=None,
        )

        self.assertEqual(normalized["workspace_status"], "REVIEW")
        self.assertEqual(normalized["local_workspace_status"], "REVIEW")
        self.assertEqual(normalized["local_block_status"], "REVIEW")

    def test_normalize_metadata_promotes_case_id_from_legacy_alias(self) -> None:
        normalized = operations._normalize_work_item_metadata(
            resource_type="sanctions_screening",
            metadata={"local_case_id": "case-legacy-1"},
            case_id=None,
            owner_user_id=None,
            note=None,
        )

        self.assertEqual(normalized["case_id"], "case-legacy-1")
        self.assertEqual(normalized["local_case_id"], "case-legacy-1")

    def test_normalize_metadata_copies_case_owner_and_note_into_metadata(self) -> None:
        case_id = uuid4()
        owner_user_id = str(uuid4())

        normalized = operations._normalize_work_item_metadata(
            resource_type="formal_report_case",
            metadata={},
            case_id=case_id,
            owner_user_id=owner_user_id,
            note="handoff pronto",
        )

        self.assertEqual(normalized["case_id"], str(case_id))
        self.assertEqual(normalized["owner_user_id"], owner_user_id)
        self.assertEqual(normalized["note"], "handoff pronto")

    def test_validate_metadata_accepts_known_shape_with_extra_fields(self) -> None:
        metadata = {
            "address": "0xabc",
            "chain": "ethereum",
            "lists": ["OFAC", "EU"],
            "matched_lists": ["OFAC"],
            "hit": True,
            "workspace_status": "UNDER_REVIEW",
            "custom_field_kept_for_compatibility": {"legacy": True},
        }

        operations._validate_work_item_metadata("sanctions_screening", metadata)

    def test_validate_metadata_accepts_operational_alert_rca_shape(self) -> None:
        metadata = {
            "alertname": "HighErrorRate",
            "receiver": "pagerduty",
            "fingerprint": "alert-fp-1",
            "first_received_at": "2026-07-11T12:00:00+00:00",
            "last_received_at": "2026-07-11T12:05:00+00:00",
            "delivery_count": 3,
            "triage_status": "pending",
            "domain": "monitoring",
            "affected_domains": ["monitoring", "compliance-api"],
            "incident_commander": "analyst-a",
            "containment_status": "in_progress",
            "runbook_ref": "RUN-ALERT-01",
            "impact_summary": "latencia elevada",
            "suspected_root_cause": "erro em worker",
            "confirmed_root_cause": "falha em fila",
            "corrective_actions": ["reiniciar worker", "validar backlog"],
            "evidence_refs": ["war-room-123", "grafana-incident-1"],
        }

        operations._validate_work_item_metadata("operational_alert", metadata)

    def test_validate_metadata_accepts_evidence_manual_review_shape(self) -> None:
        metadata = {
            "event_id": "audit-evt-1",
            "audit_action": "compliance_due_diligence_checked",
            "audit_resource_type": "address",
            "audit_resource_id": "0xabc",
            "request_id": "req-123",
            "report_id": "report-123",
            "file_hash_sha256": "sha256",
            "provider": "manual_review",
            "provider_status": "degraded",
            "degraded_reason": "manual_review_required",
            "capability_status": "degraded",
            "delivery_mode": "manual_review_pending",
            "origin_analysis_status": "manual_review_pending",
            "requires_human_review": True,
            "counterparty_context_present": True,
            "counterparty_context": "wallet vinculada ao cliente",
            "purpose": "analise reforcada",
            "amount": 4200.5,
            "manual_review_action": "compliance_due_diligence_checked",
            "package_sha256": "package-sha256",
            "filename": "manual-package.json",
        }

        operations._validate_work_item_metadata("evidence_event", metadata)

    def test_validate_metadata_accepts_ros_extended_shape(self) -> None:
        metadata = {
            "ros_id": str(uuid4()),
            "workspace_status": "SUBMITTED_MANUAL",
            "ros_status": "SUBMITTED_MANUAL",
            "ros_phase": "submission",
            "report_id": "report-123",
            "created_at": "2026-07-11T10:00:00+00:00",
            "approved_at": "2026-07-11T10:05:00+00:00",
            "approval_2fa_verified": True,
            "submitted_at": "2026-07-11T10:10:00+00:00",
            "coaf_protocol_number": "PROTO-123",
            "coaf_receipt_hash": "receipt-sha256",
            "rejection_reason": "",
        }

        operations._validate_work_item_metadata("ros_record", metadata)

    def test_validate_metadata_rejects_invalid_typed_field(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            operations._validate_work_item_metadata(
                "counterparty",
                {
                    "counterparty_id": str(uuid4()),
                    "risk_level": "high",
                },
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail["code"], "invalid_work_item_metadata")
        self.assertEqual(ctx.exception.detail["field"], "risk_level")
        self.assertEqual(ctx.exception.detail["expected"], "number")

    def test_normalize_metadata_keeps_ros_legacy_alias_in_sync(self) -> None:
        normalized = operations._normalize_work_item_metadata(
            resource_type="ros_record",
            metadata={"workspace_status": "SUBMITTED_MANUAL"},
            case_id=None,
            owner_user_id=None,
            note=None,
        )

        self.assertEqual(normalized["workspace_status"], "SUBMITTED_MANUAL")
        self.assertEqual(normalized["ros_status"], "SUBMITTED_MANUAL")

    def test_normalize_metadata_promotes_ros_status_when_only_alias_is_present(self) -> None:
        normalized = operations._normalize_work_item_metadata(
            resource_type="ros_record",
            metadata={"ros_status": "APPROVED"},
            case_id=None,
            owner_user_id=None,
            note=None,
        )

        self.assertEqual(normalized["workspace_status"], "APPROVED")
        self.assertEqual(normalized["ros_status"], "APPROVED")

    def test_create_work_item_persists_normalized_metadata_and_audit(self) -> None:
        state, pool = self._build_state()
        resource_id = uuid4()
        owner_user_id = UUID(state["owner_user_id"])

        response = asyncio.run(
            operations.create_work_item(
                operations.CreateWorkItemRequest(
                    module="sanctions",
                    resource_type="sanctions_screening",
                    resource_id=resource_id,
                    owner_user_id=owner_user_id,
                    priority="high",
                    queue_status="UNDER_REVIEW",
                    title="Sanctions hit",
                    note="triagem inicial",
                    metadata={
                        "address": "0xabc",
                        "chain": "ethereum",
                        "lists": ["OFAC"],
                        "hit": True,
                        "local_workspace_status": "UNDER_REVIEW",
                    },
                ),
                pool=pool,
                x_org_id=state["organization_id"],
                x_user_id=str(uuid4()),
                x_linked_user_id=state["linked_user_id"],
                x_role="ANALYST",
                x_request_id="req-create-1",
            )
        )

        self.assertEqual(response.resource_id, resource_id)
        self.assertEqual(response.owner_user_id, owner_user_id)
        self.assertEqual(response.metadata["workspace_status"], "UNDER_REVIEW")
        self.assertEqual(response.metadata["local_workspace_status"], "UNDER_REVIEW")
        self.assertEqual(response.metadata["owner_user_id"], state["owner_user_id"])
        self.assertEqual(len(state["events"]), 1)
        self.assertEqual(state["events"][0]["event_type"], "WORK_ITEM_UPSERTED")
        self.assertEqual(len(state["audit_logs"]), 1)
        self.assertEqual(state["audit_logs"][0]["action"], "regulatory_work_item_upserted")
        pool._connection.commit.assert_called_once()

    def test_create_work_item_promotes_local_case_id_to_canonical_case_id(self) -> None:
        state, pool = self._build_state()
        resource_id = uuid4()

        response = asyncio.run(
            operations.create_work_item(
                operations.CreateWorkItemRequest(
                    module="sanctions",
                    resource_type="sanctions_screening",
                    resource_id=resource_id,
                    priority="normal",
                    queue_status="UNDER_REVIEW",
                    metadata={
                        "address": "0xabc",
                        "chain": "ethereum",
                        "lists": ["OFAC"],
                        "hit": False,
                        "local_case_id": "case-legacy-2",
                    },
                ),
                pool=pool,
                x_org_id=state["organization_id"],
                x_user_id=str(uuid4()),
                x_linked_user_id=state["linked_user_id"],
                x_role="ANALYST",
                x_request_id="req-create-legacy-case",
            )
        )

        self.assertEqual(response.metadata["case_id"], "case-legacy-2")
        self.assertEqual(response.metadata["local_case_id"], "case-legacy-2")

    def test_list_work_items_filters_by_module_and_resource_type(self) -> None:
        state, pool = self._build_state()
        now = datetime.now(timezone.utc)
        sanctions_id = uuid4()
        alerts_id = uuid4()
        state["work_items"][str(sanctions_id)] = {
            "id": sanctions_id,
            "organization_id": state["organization_id"],
            "module": "sanctions",
            "resource_type": "sanctions_screening",
            "resource_id": uuid4(),
            "case_id": None,
            "report_external_id": None,
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "UNDER_REVIEW",
            "priority": "high",
            "due_at": now,
            "sla_breached": False,
            "title": "Sanctions item",
            "note": None,
            "metadata": {"workspace_status": "UNDER_REVIEW"},
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }
        state["work_items"][str(alerts_id)] = {
            "id": alerts_id,
            "organization_id": state["organization_id"],
            "module": "alerts",
            "resource_type": "operational_alert",
            "resource_id": uuid4(),
            "case_id": None,
            "report_external_id": None,
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "READY",
            "priority": "normal",
            "due_at": None,
            "sla_breached": False,
            "title": "Alert item",
            "note": None,
            "metadata": {"workspace_status": "READY"},
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }

        response = asyncio.run(
            operations.list_work_items(
                module="sanctions",
                resource_type="sanctions_screening",
                page=1,
                limit=20,
                pool=pool,
                x_org_id=state["organization_id"],
                x_role="VIEWER",
            )
        )

        self.assertEqual(response.total, 1)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].module, "sanctions")
        self.assertEqual(response.data[0].resource_type, "sanctions_screening")
        self.assertFalse(response.has_more)

    def test_list_work_items_filters_by_report_external_id(self) -> None:
        state, pool = self._build_state()
        now = datetime.now(timezone.utc)
        first_id = uuid4()
        second_id = uuid4()
        shared_case_id = uuid4()
        state["work_items"][str(first_id)] = {
            "id": first_id,
            "organization_id": state["organization_id"],
            "module": "reports",
            "resource_type": "formal_report_case",
            "resource_id": shared_case_id,
            "case_id": shared_case_id,
            "report_external_id": "report-001",
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "UNDER_REVIEW",
            "priority": "high",
            "due_at": now,
            "sla_breached": False,
            "title": "Formal report case",
            "note": None,
            "metadata": {"workspace_status": "draft", "report_id": "report-001"},
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }
        state["work_items"][str(second_id)] = {
            "id": second_id,
            "organization_id": state["organization_id"],
            "module": "reports",
            "resource_type": "formal_report_case",
            "resource_id": uuid4(),
            "case_id": uuid4(),
            "report_external_id": "report-002",
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "READY",
            "priority": "normal",
            "due_at": None,
            "sla_breached": False,
            "title": "Another report case",
            "note": None,
            "metadata": {"workspace_status": "ready", "report_id": "report-002"},
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }

        response = asyncio.run(
            operations.list_work_items(
                module="reports",
                resource_type="formal_report_case",
                report_external_id="report-001",
                page=1,
                limit=20,
                pool=pool,
                x_org_id=state["organization_id"],
                x_role="VIEWER",
            )
        )

        self.assertEqual(response.total, 1)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].report_external_id, "report-001")
        self.assertEqual(str(response.data[0].case_id), str(shared_case_id))

    def test_update_work_item_merges_metadata_and_records_status_change(self) -> None:
        state, pool = self._build_state()
        now = datetime.now(timezone.utc)
        work_item_id = uuid4()
        resource_id = uuid4()
        state["work_items"][str(work_item_id)] = {
            "id": work_item_id,
            "organization_id": state["organization_id"],
            "module": "sanctions",
            "resource_type": "sanctions_screening",
            "resource_id": resource_id,
            "case_id": None,
            "report_external_id": None,
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "UNDER_REVIEW",
            "priority": "normal",
            "due_at": now,
            "sla_breached": False,
            "title": "Sanctions item",
            "note": "triagem inicial",
            "metadata": {
                "address": "0xabc",
                "chain": "ethereum",
                "local_workspace_status": "UNDER_REVIEW",
                "workspace_status": "UNDER_REVIEW",
            },
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }

        response = asyncio.run(
            operations.update_work_item(
                work_item_id=work_item_id,
                body=operations.UpdateWorkItemRequest(
                    queue_status="ESCALATED",
                    priority="critical",
                    note="escalado para compliance officer",
                    metadata={
                        "local_workspace_status": "ESCALATED",
                        "triage_note": "manual escalation",
                    },
                ),
                pool=pool,
                x_org_id=state["organization_id"],
                x_user_id=str(uuid4()),
                x_linked_user_id=state["linked_user_id"],
                x_role="ANALYST",
                x_request_id="req-update-1",
            )
        )

        self.assertEqual(response.queue_status, "ESCALATED")
        self.assertEqual(response.priority, "critical")
        self.assertEqual(response.metadata["workspace_status"], "ESCALATED")
        self.assertEqual(response.metadata["local_workspace_status"], "ESCALATED")
        self.assertEqual(response.metadata["triage_note"], "manual escalation")
        self.assertEqual(len(state["events"]), 1)
        self.assertEqual(state["events"][0]["event_type"], "STATUS_CHANGED")
        self.assertEqual(len(state["audit_logs"]), 1)
        self.assertEqual(state["audit_logs"][0]["action"], "regulatory_work_item_updated")
        pool._connection.commit.assert_called_once()

    def test_update_preventive_block_keeps_canonical_and_legacy_status_aliases_in_sync(self) -> None:
        state, pool = self._build_state()
        now = datetime.now(timezone.utc)
        work_item_id = uuid4()
        resource_id = uuid4()
        state["preventive_blocks"].add(str(resource_id))
        state["work_items"][str(work_item_id)] = {
            "id": work_item_id,
            "organization_id": state["organization_id"],
            "module": "blocks",
            "resource_type": "preventive_block",
            "resource_id": resource_id,
            "case_id": None,
            "report_external_id": None,
            "owner_user_id": state["owner_user_id"],
            "assigned_by_user_id": state["linked_user_id"],
            "queue_status": "UNDER_REVIEW",
            "priority": "normal",
            "due_at": now,
            "sla_breached": False,
            "title": "Block item",
            "note": None,
            "metadata": {
                "workspace_status": "UNDER_REVIEW",
                "local_workspace_status": "UNDER_REVIEW",
                "local_block_status": "UNDER_REVIEW",
            },
            "created_at": now,
            "updated_at": now,
            "last_activity_at": now,
        }

        response = asyncio.run(
            operations.update_work_item(
                work_item_id=work_item_id,
                body=operations.UpdateWorkItemRequest(
                    queue_status="READY",
                    metadata={"local_block_status": "READY"},
                ),
                pool=pool,
                x_org_id=state["organization_id"],
                x_user_id=str(uuid4()),
                x_linked_user_id=state["linked_user_id"],
                x_role="ANALYST",
                x_request_id="req-update-block-alias",
            )
        )

        self.assertEqual(response.metadata["workspace_status"], "READY")
        self.assertEqual(response.metadata["local_workspace_status"], "READY")
        self.assertEqual(response.metadata["local_block_status"], "READY")


if __name__ == "__main__":
    unittest.main()
