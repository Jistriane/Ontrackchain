import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "agents" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages" / "shared" / "src"))

from report_api.main import _normalize_reports_pagination, _serialize_report_list_row
from report_api.main import _normalize_report_filter_datetime


class ReportListHelpersTests(unittest.TestCase):
    def test_normalize_reports_pagination_keeps_valid_values(self) -> None:
        page, limit, offset = _normalize_reports_pagination(page=3, limit=25)
        self.assertEqual(page, 3)
        self.assertEqual(limit, 25)
        self.assertEqual(offset, 50)

    def test_normalize_reports_pagination_applies_safe_defaults(self) -> None:
        page, limit, offset = _normalize_reports_pagination(page=0, limit=500)
        self.assertEqual(page, 1)
        self.assertEqual(limit, 20)
        self.assertEqual(offset, 0)

    def test_normalize_report_filter_datetime_assumes_utc_for_naive_value(self) -> None:
        value = datetime(2026, 7, 3, 12, 0)

        normalized = _normalize_report_filter_datetime(value)

        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized.tzinfo, timezone.utc)
        self.assertEqual(normalized.isoformat(), "2026-07-03T12:00:00+00:00")

    def test_normalize_report_filter_datetime_converts_aware_value_to_utc(self) -> None:
        value = datetime.fromisoformat("2026-07-03T09:00:00-03:00")

        normalized = _normalize_report_filter_datetime(value)

        self.assertIsNotNone(normalized)
        assert normalized is not None
        self.assertEqual(normalized.isoformat(), "2026-07-03T12:00:00+00:00")

    def test_serialize_report_list_row_with_datetime(self) -> None:
        row = {
            "external_report_id": "rep-123",
            "case_id": "11111111-1111-1111-1111-111111111111",
            "report_type_requested": "technical",
            "report_type": "technical_basic",
            "content_type": "application/pdf",
            "file_hash": "a" * 64,
            "onchain_hash": None,
            "created_at": datetime(2026, 7, 3, 12, 0, tzinfo=timezone.utc),
            "has_download_audit": True,
        }

        item = _serialize_report_list_row(row)

        self.assertEqual(item.report_id, "rep-123")
        self.assertEqual(item.case_id, "11111111-1111-1111-1111-111111111111")
        self.assertEqual(item.report_type, "technical_basic")
        self.assertEqual(item.report_type_requested, "technical")
        self.assertEqual(item.content_type, "application/pdf")
        self.assertEqual(item.file_hash_sha256, "a" * 64)
        self.assertTrue(item.has_download_audit)
        self.assertTrue(item.created_at.endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
