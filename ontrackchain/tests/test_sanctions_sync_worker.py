from __future__ import annotations

from email.message import Message
from pathlib import Path
import sys
from typing import cast
import urllib.error

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "packages" / "agents" / "src"))

from ontrackchain_agents.sanctions_engine import SanctionsSyncWorker, SyncResult


class _RecordingWorker(SanctionsSyncWorker):
    def __init__(self, downloads: dict[str, object], *, configured_url: str | None = None) -> None:
        super().__init__(conn=object())
        self._downloads = downloads
        self._configured_url = configured_url
        self.requested_urls: list[str] = []
        self.persisted_urls: list[tuple[str, str]] = []
        self.upserted_entries: list[dict] = []

    def _get_source_url(self, list_name: str) -> str | None:
        return self._configured_url

    def _persist_working_source_url(self, list_name: str, source_url: str) -> None:
        self.persisted_urls.append((list_name, source_url))

    def _download(self, url: str, timeout: int = 30) -> bytes:
        self.requested_urls.append(url)
        response = self._downloads[url]
        if isinstance(response, Exception):
            raise response
        return cast(bytes, response)

    def _is_same_hash(self, list_name: str, new_hash: str) -> bool:
        return False

    def _upsert_entries(
        self,
        list_name: str,
        entries: list[dict],
        source_hash: str,
    ) -> SyncResult:
        self.upserted_entries = entries
        return SyncResult(
            list_name=list_name,
            success=True,
            records_added=len(entries),
            source_hash=source_hash,
        )

    def _fail(self, list_name: str, error: str) -> SyncResult:
        return SyncResult(list_name=list_name, success=False, error_message=error)


def test_sync_ofac_sdn_uses_fallback_and_parses_namespaced_xml() -> None:
    legacy_url = "https://legacy.example/ofac.xml"
    official_url = "https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML"
    headers = Message()
    worker = _RecordingWorker(
        {
            legacy_url: urllib.error.HTTPError(legacy_url, 404, "Not Found", headers, None),
            official_url: b"""<?xml version="1.0" encoding="utf-8"?>
<Sanctions xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ADVANCED_XML">
  <sdnEntry>
    <uid>123</uid>
    <firstName>Jane</firstName>
    <lastName>Doe</lastName>
    <sdnType>Individual</sdnType>
    <programList>
      <program>SDGT</program>
    </programList>
    <akaList>
      <aka>
        <wholeName>J. Doe</wholeName>
      </aka>
    </akaList>
  </sdnEntry>
</Sanctions>
""",
        },
        configured_url=legacy_url,
    )

    result = worker.sync_ofac_sdn()

    assert result.success is True
    assert result.records_added == 1
    assert worker.requested_urls[:2] == [legacy_url, official_url]
    assert worker.persisted_urls == [("OFAC_SDN", official_url)]
    assert worker.upserted_entries[0]["entity_name"] == "Jane Doe"
    assert worker.upserted_entries[0]["entity_aliases"] == ["J. Doe"]
    assert worker.upserted_entries[0]["entity_type"] == "INDIVIDUAL"
    assert worker.upserted_entries[0]["sanctions_programs"] == ["SDGT"]


def test_sync_eu_consolidated_returns_operational_hint_on_public_403() -> None:
    headers = Message()
    worker = _RecordingWorker(
        {
            "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content": urllib.error.HTTPError(
                "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content",
                403,
                "Forbidden",
                headers,
                None,
            ),
            "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content": urllib.error.HTTPError(
                "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content",
                403,
                "Forbidden",
                headers,
                None,
            ),
        }
    )

    result = worker.sync_eu_consolidated()

    assert result.success is False
    assert "HTTP 403" in result.error_message
    assert "source_url" in result.error_message
    assert "tokenizada" in result.error_message
