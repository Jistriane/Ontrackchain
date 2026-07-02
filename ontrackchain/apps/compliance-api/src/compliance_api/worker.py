from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from compliance_api.main import _dsn
from ontrackchain_agents.sanctions_engine import SanctionsSyncWorker

logger = logging.getLogger(__name__)


class WorkerSettings(BaseSettings):
    compliance_worker_idle_wait_seconds: int = 60
    compliance_worker_ofac_sync_seconds: int = 6 * 3600
    compliance_worker_un_sync_seconds: int = 24 * 3600
    compliance_worker_eu_sync_seconds: int = 24 * 3600
    compliance_worker_coaf_sync_seconds: int = 12 * 3600
    compliance_worker_opensanctions_sync_seconds: int = 24 * 3600
    compliance_worker_ros_deadline_scan_seconds: int = 3600
    opensanctions_api_key: str = ""
    compliance_ofac_sdn_source_url: str = ""
    compliance_eu_sanctions_source_url: str = ""


worker_settings = WorkerSettings()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ComplianceWorker:
    def __init__(self) -> None:
        self.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
        self._next_runs = {
            "ofac": 0.0,
            "un": 0.0,
            "eu": 0.0,
            "coaf": 0.0,
            "opensanctions": 0.0,
            "ros_deadlines": 0.0,
        }

    async def run(self) -> None:
        try:
            while True:
                now = asyncio.get_running_loop().time()
                if now >= self._next_runs["ofac"]:
                    await self._run_ofac_sync()
                    self._next_runs["ofac"] = now + worker_settings.compliance_worker_ofac_sync_seconds
                if now >= self._next_runs["un"]:
                    await self._run_un_sync()
                    self._next_runs["un"] = now + worker_settings.compliance_worker_un_sync_seconds
                if now >= self._next_runs["eu"]:
                    await self._run_eu_sync()
                    self._next_runs["eu"] = now + worker_settings.compliance_worker_eu_sync_seconds
                if now >= self._next_runs["coaf"]:
                    await self._run_coaf_sync()
                    self._next_runs["coaf"] = now + worker_settings.compliance_worker_coaf_sync_seconds
                if now >= self._next_runs["opensanctions"]:
                    await self._run_opensanctions_sync()
                    self._next_runs["opensanctions"] = now + worker_settings.compliance_worker_opensanctions_sync_seconds
                if now >= self._next_runs["ros_deadlines"]:
                    await self._scan_ros_deadlines()
                    self._next_runs["ros_deadlines"] = now + worker_settings.compliance_worker_ros_deadline_scan_seconds
                await asyncio.sleep(worker_settings.compliance_worker_idle_wait_seconds)
        finally:
            self.pool.close()

    async def _run_ofac_sync(self) -> None:
        await asyncio.to_thread(self._sync_list, "ofac")

    async def _run_un_sync(self) -> None:
        await asyncio.to_thread(self._sync_list, "un")

    async def _run_eu_sync(self) -> None:
        await asyncio.to_thread(self._sync_list, "eu")

    async def _run_coaf_sync(self) -> None:
        await asyncio.to_thread(self._sync_list, "coaf")

    async def _run_opensanctions_sync(self) -> None:
        if not worker_settings.opensanctions_api_key:
            logger.info("compliance_worker.opensanctions.skip_missing_api_key")
            return
        await asyncio.to_thread(self._sync_list, "opensanctions")

    def _sync_list(self, provider: str) -> None:
        with self.pool.connection() as conn:
            worker = SanctionsSyncWorker(conn)
            if provider == "ofac":
                self._apply_source_url_override(
                    conn,
                    list_name="OFAC_SDN",
                    source_url=worker_settings.compliance_ofac_sdn_source_url,
                )
                result = worker.sync_ofac_sdn()
            elif provider == "un":
                result = worker.sync_un_csnu()
            elif provider == "eu":
                self._apply_source_url_override(
                    conn,
                    list_name="EU_CONSOLIDATED",
                    source_url=worker_settings.compliance_eu_sanctions_source_url,
                )
                result = worker.sync_eu_consolidated()
            elif provider == "coaf":
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE sanctions_lists_meta
                           SET last_sync_at = NOW(),
                               last_sync_status = 'FAILED',
                               status = 'PENDING_CONFIG',
                               status_reason = 'Feed COAF nao definido/homologado',
                               next_sync_at = NOW() + INTERVAL '12 hour',
                               updated_at = NOW()
                         WHERE list_name = 'COAF_INTERNAL'
                        """
                    )
                conn.commit()
                logger.warning("compliance_worker.coaf_feed_pending_config")
                return
            elif provider == "opensanctions":
                result = worker.sync_opensanctions(worker_settings.opensanctions_api_key)
            else:
                raise ValueError(f"provider inválido: {provider}")
        logger.info(
            "compliance_worker.sync_completed",
            extra={
                "provider": provider,
                "success": result.success,
                "records_added": result.records_added,
                "error_message": result.error_message,
            },
        )

    def _apply_source_url_override(self, conn, *, list_name: str, source_url: str) -> None:
        normalized = source_url.strip()
        if not normalized:
            return
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sanctions_lists_meta
                   SET source_url = %s,
                       updated_at = NOW()
                 WHERE list_name = %s
                   AND COALESCE(source_url, '') <> %s
                """,
                (normalized, list_name, normalized),
            )
            updated_rows = cur.rowcount
        if updated_rows:
            conn.commit()
            logger.info(
                "compliance_worker.source_url_override_applied",
                extra={"list_name": list_name, "source_url": normalized},
            )

    async def _scan_ros_deadlines(self) -> None:
        await asyncio.to_thread(self._scan_ros_deadlines_sync)

    def _scan_ros_deadlines_sync(self) -> None:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE ros_records
                       SET deadline_alert_sent = TRUE,
                           deadline_alert_sent_at = NOW()
                     WHERE status NOT IN ('SUBMITTED_MANUAL', 'REJECTED')
                       AND deadline_alert_sent = FALSE
                       AND submission_deadline <= NOW() + INTERVAL '4 hour'
                    RETURNING id, organization_id, submission_deadline
                    """
                )
                due_alerts = cur.fetchall()

                cur.execute(
                    """
                    UPDATE ros_records
                       SET deadline_breached = TRUE
                     WHERE status NOT IN ('SUBMITTED_MANUAL', 'REJECTED')
                       AND deadline_breached = FALSE
                       AND submission_deadline < NOW()
                    RETURNING id, organization_id, submission_deadline
                    """
                )
                breached = cur.fetchall()
            conn.commit()

        if due_alerts:
            logger.warning(
                "compliance_worker.ros_deadline_alerts",
                extra={"count": len(due_alerts)},
            )
        if breached:
            logger.error(
                "compliance_worker.ros_deadline_breached",
                extra={"count": len(breached)},
            )


async def _main() -> None:
    await ComplianceWorker().run()


if __name__ == "__main__":
    asyncio.run(_main())
