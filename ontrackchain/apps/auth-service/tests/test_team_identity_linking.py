from __future__ import annotations

import importlib
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

AUTH_SERVICE_IMPORTABLE = True
try:
    main: Any = importlib.import_module("auth_service.main")
except Exception:
    AUTH_SERVICE_IMPORTABLE = False
    main = None


@unittest.skipUnless(AUTH_SERVICE_IMPORTABLE, "auth-service dependencies not installed in current interpreter")
class TeamIdentityLinkingTests(unittest.TestCase):
    class _FakeCursor:
        def __init__(self, user_exists: bool = True) -> None:
            self.user_exists = user_exists
            self.executed: list[tuple[str, tuple[Any, ...]]] = []
            self._fetchone_result: Any = None

        def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
            self.executed.append((query.strip(), params))
            normalized_query = " ".join(query.split())
            if normalized_query.startswith("SELECT 1 FROM users WHERE id = %s"):
                self._fetchone_result = {"exists": True} if self.user_exists else None
            else:
                self._fetchone_result = None

        def fetchone(self) -> Any:
            return self._fetchone_result

    def test_normalize_identity_provider_lowercases_value(self) -> None:
        self.assertEqual(main._normalize_identity_provider(" Keycloak "), "keycloak")

    def test_normalize_identity_provider_rejects_whitespace(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._normalize_identity_provider("key cloak")

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "team_external_identity_provider_invalid")

    def test_normalize_external_subject_requires_value(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._normalize_external_subject("   ")

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail, "team_external_identity_subject_required")

    def test_normalize_optional_snapshot_returns_none_for_blank(self) -> None:
        self.assertIsNone(main._normalize_optional_snapshot("   "))

    def test_serialize_external_identity_row_preserves_snapshots(self) -> None:
        row = {
            "provider": "keycloak",
            "external_subject": "kc-sub-01",
            "email_snapshot": "admin@ontrackchain.local",
            "role_snapshot": "ADMIN",
            "created_at": datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
            "last_seen_at": datetime(2026, 7, 6, 12, 5, tzinfo=timezone.utc),
        }

        record = main._serialize_external_identity_row(row)

        self.assertEqual(record.provider, "keycloak")
        self.assertEqual(record.external_subject, "kc-sub-01")
        self.assertEqual(record.email_snapshot, "admin@ontrackchain.local")
        self.assertEqual(record.role_snapshot, "ADMIN")
        self.assertEqual(record.created_at, "2026-07-06T12:00:00+00:00")
        self.assertEqual(record.last_seen_at, "2026-07-06T12:05:00+00:00")

    def test_resolve_persisted_user_id_returns_none_for_non_uuid(self) -> None:
        cur = self._FakeCursor(user_exists=True)
        self.assertIsNone(main._resolve_persisted_user_id(cur, "external-subject"))

    def test_record_audit_log_persists_external_actor_in_metadata_when_user_not_found(self) -> None:
        cur = self._FakeCursor(user_exists=False)

        main._record_audit_log(
            cur,
            organization_id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000099",
            action="team_external_identity_linked",
            resource_type="team_user",
            resource_id="00000000-0000-0000-0000-000000000002",
            metadata={"request_id": "req-123"},
        )

        insert_query, insert_params = cur.executed[-1]
        self.assertIn("INSERT INTO audit_logs", insert_query)
        self.assertIsNone(insert_params[1])
        self.assertIn('"external_user_id": "00000000-0000-0000-0000-000000000099"', insert_params[5])

    def test_team_federated_identity_link_role_accepts_admin(self) -> None:
        main._require_team_federated_identity_link_role({"role": "ADMIN"})

    def test_team_user_create_role_accepts_admin(self) -> None:
        main._require_team_user_create_role({"role": "ADMIN"})

    def test_team_user_create_role_rejects_analyst(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_user_create_role({"role": "ANALYST"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_user_create_role_required")

    def test_team_user_update_role_accepts_admin(self) -> None:
        main._require_team_user_update_role({"role": "ADMIN"})

    def test_team_user_update_role_rejects_viewer(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_user_update_role({"role": "VIEWER"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_user_update_role_required")

    def test_team_user_disable_role_accepts_admin(self) -> None:
        main._require_team_user_disable_role({"role": "ADMIN"})

    def test_team_user_disable_role_rejects_viewer(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_user_disable_role({"role": "VIEWER"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_user_disable_role_required")

    def test_team_federated_identity_read_role_accepts_admin(self) -> None:
        main._require_team_federated_identity_read_role({"role": "ADMIN"})

    def test_team_federated_identity_read_role_rejects_analyst(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_federated_identity_read_role({"role": "ANALYST"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_federated_identity_read_role_required")

    def test_team_federated_identity_link_role_rejects_analyst(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_federated_identity_link_role({"role": "ANALYST"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_federated_identity_link_role_required")

    def test_team_federated_identity_unlink_role_accepts_admin(self) -> None:
        main._require_team_federated_identity_unlink_role({"role": "ADMIN"})

    def test_team_federated_identity_unlink_role_rejects_viewer(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_federated_identity_unlink_role({"role": "VIEWER"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_federated_identity_unlink_role_required")

    def test_team_federated_directory_search_role_accepts_admin(self) -> None:
        main._require_team_federated_directory_search_role({"role": "ADMIN"})

    def test_team_federated_directory_search_role_rejects_analyst(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_federated_directory_search_role({"role": "ANALYST"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_federated_directory_search_role_required")

    def test_team_federated_directory_suggestion_role_accepts_admin(self) -> None:
        main._require_team_federated_directory_suggestion_role({"role": "ADMIN"})

    def test_team_federated_directory_suggestion_role_rejects_viewer(self) -> None:
        with self.assertRaises(main.HTTPException) as ctx:
            main._require_team_federated_directory_suggestion_role({"role": "VIEWER"})

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "team_federated_directory_suggestion_role_required")

    def test_normalize_federated_directory_candidate_reads_org_and_role_attributes(self) -> None:
        candidate = main._normalize_federated_directory_candidate(
            {
                "id": "kc-sub-01",
                "email": "analyst@ontrackchain.local",
                "username": "analyst",
                "enabled": True,
                "attributes": {
                    "organization_id": ["00000000-0000-0000-0000-000000000001"],
                    "otk_role": ["otk_analyst"],
                },
            },
            "keycloak",
        )

        self.assertEqual(candidate["organization_id"], "00000000-0000-0000-0000-000000000001")
        self.assertEqual(candidate["role_snapshot"], "ANALYST")
        self.assertEqual(candidate["external_subject"], "kc-sub-01")

    def test_evaluate_federated_directory_suggestion_accepts_email_and_org_match(self) -> None:
        evaluation = main._evaluate_federated_directory_suggestion(
            tenant_org_id="00000000-0000-0000-0000-000000000001",
            member_id="00000000-0000-0000-0000-000000000010",
            member_email="analyst@ontrackchain.local",
            member_role="ANALYST",
            candidate_org_id="00000000-0000-0000-0000-000000000001",
            candidate_email="analyst@ontrackchain.local",
            candidate_role_snapshot="otk_analyst",
            linked_user_id=None,
        )

        self.assertTrue(evaluation["can_link"])
        self.assertEqual(evaluation["match_reason"], "ready")
        self.assertEqual(evaluation["role_validation_status"], "valid")
        self.assertEqual(evaluation["warnings"], [])

    def test_evaluate_federated_directory_suggestion_flags_org_mismatch(self) -> None:
        evaluation = main._evaluate_federated_directory_suggestion(
            tenant_org_id="00000000-0000-0000-0000-000000000001",
            member_id="00000000-0000-0000-0000-000000000010",
            member_email="analyst@ontrackchain.local",
            member_role="ANALYST",
            candidate_org_id="00000000-0000-0000-0000-000000000999",
            candidate_email="analyst@ontrackchain.local",
            candidate_role_snapshot="otk_analyst",
            linked_user_id=None,
        )

        self.assertFalse(evaluation["can_link"])
        self.assertEqual(evaluation["match_reason"], "org_mismatch")
        self.assertIn("candidate_org_mismatch", evaluation["warnings"])

    def test_evaluate_federated_directory_suggestion_flags_existing_link(self) -> None:
        evaluation = main._evaluate_federated_directory_suggestion(
            tenant_org_id="00000000-0000-0000-0000-000000000001",
            member_id="00000000-0000-0000-0000-000000000010",
            member_email="analyst@ontrackchain.local",
            member_role="ANALYST",
            candidate_org_id="00000000-0000-0000-0000-000000000001",
            candidate_email="analyst@ontrackchain.local",
            candidate_role_snapshot="otk_analyst",
            linked_user_id="00000000-0000-0000-0000-000000000011",
        )

        self.assertFalse(evaluation["can_link"])
        self.assertEqual(evaluation["match_reason"], "already_linked")
        self.assertIn("candidate_already_linked", evaluation["warnings"])


if __name__ == "__main__":
    unittest.main()
