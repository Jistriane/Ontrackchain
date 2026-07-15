from __future__ import annotations

import asyncio
import hashlib
import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic_settings import BaseSettings
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from redis.asyncio import Redis

from investigation_api.config.agent_concurrency import CONCURRENCY_LIMITS_MVP
from investigation_api.main import (
    _apply_rls_context,
    _concurrency_limit_for_plan,
    _dsn,
    _get_rpc_provider_config,
    _get_active_counts,
    _global_active_counter_key,
    _org_active_counter_key,
    _record_audit_log,
    settings as api_settings,
)
from investigation_api.rpc_provider import fetch_chain_context


class WorkerSettings(BaseSettings):
    redis_host: str = "redis"
    redis_port: int = 6379
    investigation_internal_base_url: str = "http://investigation-api:8001"
    investigation_internal_worker_token: str = "investigation-local-token"
    investigation_worker_processing_seconds: float = 2.0
    investigation_worker_local_concurrency: int = 8
    investigation_worker_base_backoff_seconds: int = 5
    investigation_worker_idle_wait_seconds: int = 2


@dataclass
class ClaimedJob:
    case_id: str
    org_id: str
    request_id: str
    plan: str
    target_address: str
    target_chain: str
    credits_estimated: float
    attempt_count: int
    max_attempts: int
    report_type_canonical: str
    dlq_requeue_count: int


worker_settings = WorkerSettings()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _request_json(method: str, url: str, *, data: dict, headers: dict[str, str]) -> tuple[int, dict[str, Any]]:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={**headers, "content-type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


class InvestigationWorker:
    def __init__(self) -> None:
        self.pool = ConnectionPool(conninfo=_dsn(), kwargs={"row_factory": dict_row})
        self.redis = Redis(host=worker_settings.redis_host, port=worker_settings.redis_port, decode_responses=True)
        self.active_tasks: set[asyncio.Task[None]] = set()

    async def run(self) -> None:
        try:
            while True:
                self._cleanup_finished_tasks()
                await self._promote_due_retries()
                await self._promote_waiting_cases()
                started = await self._start_ready_jobs()
                if started:
                    continue
                await self.redis.blpop(api_settings.investigation_worker_wake_queue_key, timeout=worker_settings.investigation_worker_idle_wait_seconds)
        finally:
            self.pool.close()
            await self.redis.aclose()

    def _cleanup_finished_tasks(self) -> None:
        done = {task for task in self.active_tasks if task.done()}
        self.active_tasks.difference_update(done)

    async def _start_ready_jobs(self) -> bool:
        started_any = False
        while len(self.active_tasks) < worker_settings.investigation_worker_local_concurrency:
            raw = await self.redis.lpop(api_settings.investigation_ready_queue_key)
            if not raw:
                break
            payload = json.loads(raw)
            task = asyncio.create_task(self._process_job(payload))
            self.active_tasks.add(task)
            started_any = True
        return started_any

    async def _promote_due_retries(self) -> None:
        now_score = _utc_now().timestamp()
        due = await self.redis.zrangebyscore(api_settings.investigation_retry_zset_key, min="-inf", max=now_score)
        if not due:
            return
        for raw in due:
            await self.redis.zrem(api_settings.investigation_retry_zset_key, raw)
            await self.redis.rpush(api_settings.investigation_waiting_queue_key, raw)
        await self.redis.rpush(api_settings.investigation_worker_wake_queue_key, json.dumps({"event": "retry_due", "count": len(due)}))

    async def _promote_waiting_cases(self) -> None:
        async with self.redis.lock(api_settings.investigation_dispatch_lock_key, timeout=10):
            queued_len = await self.redis.llen(api_settings.investigation_waiting_queue_key)
            if queued_len <= 0:
                return
            rotated = 0
            while rotated < queued_len and len(self.active_tasks) < worker_settings.investigation_worker_local_concurrency:
                raw = await self.redis.lpop(api_settings.investigation_waiting_queue_key)
                if not raw:
                    return
                payload = json.loads(raw)
                org_active, global_active = await _get_active_counts(self.redis, payload["org_id"])
                org_limit = _concurrency_limit_for_plan(payload["plan"])
                global_limit = int(CONCURRENCY_LIMITS_MVP.get("global_max_concurrent_investigations", 10))
                if org_active >= org_limit or global_active >= global_limit:
                    await self.redis.rpush(api_settings.investigation_waiting_queue_key, raw)
                    rotated += 1
                    continue

                self._update_case_status(
                    payload["org_id"],
                    payload["case_id"],
                    "processing",
                    {
                        "worker_queue_state": "processing",
                        "queue_promoted_at": _utc_now().isoformat(),
                    },
                )
                self._record_worker_audit(
                    payload["org_id"],
                    payload["case_id"],
                    "case_promoted_from_queue",
                    {
                        "request_id": payload["request_id"],
                        "queue": "waiting",
                        "processing_mode": "redis_async_worker_v1",
                    },
                )
                await self.redis.incr(_org_active_counter_key(payload["org_id"]))
                await self.redis.incr(_global_active_counter_key())
                payload["status"] = "processing"
                await self.redis.rpush(api_settings.investigation_ready_queue_key, json.dumps(payload, sort_keys=True))
                await self.redis.rpush(
                    api_settings.investigation_worker_wake_queue_key,
                    json.dumps({"event": "case_promoted", "case_id": payload["case_id"], "org_id": payload["org_id"]}),
                )

    async def _process_job(self, payload: dict[str, Any]) -> None:
        claimed = self._claim_case(payload)
        if not claimed:
            if payload.get("status") == "processing":
                await self._decrement_active_counters(payload["org_id"])
                await self._promote_waiting_cases()
            return

        try:
            result = await asyncio.wait_for(
                self._simulate_case_execution(claimed),
                timeout=int(api_settings.investigation_worker_timeout_seconds),
            )
            await self._complete_case(claimed, result)
        except Exception as exc:
            await self._handle_processing_failure(claimed, str(exc))

    def _claim_case(self, payload: dict[str, Any]) -> ClaimedJob | None:
        with self.pool.connection() as conn:
            _apply_rls_context(conn, payload["org_id"])
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                      c.id,
                      c.target_address,
                      c.target_chain,
                      c.credits_estimated,
                      c.status,
                      c.metadata,
                      ar.id AS agent_run_id,
                      ar.input AS agent_input
                    FROM cases c
                    JOIN agent_runs ar ON ar.case_id = c.id
                    WHERE c.id = %s
                      AND c.case_type = 'investigation'
                      AND ar.agent_name = 'investigation_executor'
                    ORDER BY ar.started_at DESC NULLS FIRST, ar.id DESC
                    LIMIT 1
                    """,
                    (payload["case_id"],),
                )
                row = cur.fetchone()
                if not row:
                    return None
                if row["status"] not in {"processing", "queued"}:
                    return None

                agent_input = row["agent_input"] or {}
                attempt_count = int(agent_input.get("attempt_count", 0))
                max_attempts = int(agent_input.get("max_attempts", api_settings.investigation_worker_max_attempts))
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'running',
                        started_at = NOW(),
                        completed_at = NULL,
                        error_message = NULL,
                        input = %s::jsonb
                    WHERE id = %s
                    """,
                    (
                        json.dumps(
                            {
                                **agent_input,
                                "attempt_count": attempt_count,
                                "worker_claimed_at": _utc_now().isoformat(),
                                "worker_request_id": payload["request_id"],
                            }
                        ),
                        row["agent_run_id"],
                    ),
                )
            conn.commit()

        metadata = row["metadata"] or {}
        return ClaimedJob(
            case_id=str(row["id"]),
            org_id=payload["org_id"],
            request_id=payload["request_id"],
            plan=payload["plan"],
            target_address=str(row["target_address"]),
            target_chain=str(row["target_chain"]),
            credits_estimated=float(row["credits_estimated"]),
            attempt_count=attempt_count,
            max_attempts=max_attempts,
            report_type_canonical=str(metadata.get("report_type_canonical", "technical_basic")),
            dlq_requeue_count=int(metadata.get("dlq_requeue_count") or 0),
        )

    async def _simulate_case_execution(self, claimed: ClaimedJob) -> dict[str, Any]:
        if claimed.target_address.lower().startswith("0xfeed") and claimed.dlq_requeue_count == 0:
            raise RuntimeError("simulated_permanent_failure")
        if claimed.target_address.lower().startswith("0xdead") and claimed.attempt_count == 0:
            raise RuntimeError("transient_provider_error")
        await asyncio.sleep(worker_settings.investigation_worker_processing_seconds)
        provider_outcome = fetch_chain_context(
            provider_name=api_settings.investigation_rpc_provider,
            config=_get_rpc_provider_config(),
            address=claimed.target_address,
            chain=claimed.target_chain,
        )
        seed = hashlib.sha256(f"{claimed.case_id}:{claimed.target_address}:{claimed.target_chain}".encode("utf-8")).hexdigest()
        risk_score = int(seed[:8], 16) % 100
        if provider_outcome.latest_block_number is not None:
            risk_score = (risk_score + provider_outcome.latest_block_number) % 100
        risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 35 else "low"
        patterns = ["bridge_activity"] if claimed.target_chain in {"arbitrum", "base"} else ["cluster_overlap"]
        if provider_outcome.provider_status != "live":
            patterns.append("rpc_degraded_mode")
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "patterns_detected": patterns,
            "kyw_summary": {
                "chain": claimed.target_chain,
                "address": claimed.target_address,
                "analysis_version": "rpc_provider_v1",
                "rpc": {
                    "provider": provider_outcome.provider_name,
                    "provider_status": provider_outcome.provider_status,
                    "degraded_reason": provider_outcome.degraded_reason,
                    "rpc_source": provider_outcome.rpc_source,
                    "latest_block_number": provider_outcome.latest_block_number,
                    "balance_wei": provider_outcome.balance_wei,
                    "latency_ms": provider_outcome.latency_ms,
                    "retries_used": provider_outcome.retries_used,
                },
            },
            "report_url": None,
            "report_hash": None,
        }

    async def _complete_case(self, claimed: ClaimedJob, result: dict[str, Any]) -> None:
        request_id = f"worker-complete-{claimed.case_id}-{uuid.uuid4().hex[:8]}"
        with self.pool.connection() as conn:
            _apply_rls_context(conn, claimed.org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cases
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                    WHERE id = %s
                    """,
                    (
                        json.dumps(
                            {
                                "worker_last_result": result,
                                "worker_completed_at": _utc_now().isoformat(),
                                "worker_queue_state": "completed",
                            }
                        ),
                        claimed.case_id,
                    ),
                )
            conn.commit()

        status, body = _request_json(
            "POST",
            f"{worker_settings.investigation_internal_base_url}/api/v1/investigation/{claimed.case_id}/internal/complete",
            data={"credits_used": claimed.credits_estimated},
            headers={
                "X-Org-Id": claimed.org_id,
                "X-Request-Id": request_id,
                "X-Internal-Token": worker_settings.investigation_internal_worker_token,
            },
        )
        if status not in {200, 409}:
            raise RuntimeError(f"internal_complete_failed:{status}:{body}")

        with self.pool.connection() as conn:
            _apply_rls_context(conn, claimed.org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'completed',
                        completed_at = NOW(),
                        output = %s::jsonb,
                        duration_ms = GREATEST(0, FLOOR(EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, NOW()))) * 1000))::integer
                    WHERE case_id = %s
                      AND agent_name = 'investigation_executor'
                    """,
                    (json.dumps(result), claimed.case_id),
                )
            conn.commit()

        await self._decrement_active_counters(claimed.org_id)
        await self._promote_waiting_cases()

    async def _handle_processing_failure(self, claimed: ClaimedJob, error_message: str) -> None:
        next_attempt = claimed.attempt_count + 1
        if next_attempt < claimed.max_attempts:
            backoff_seconds = worker_settings.investigation_worker_base_backoff_seconds * (2 ** claimed.attempt_count)
            next_retry_at = _utc_now().timestamp() + backoff_seconds
            payload = {
                "case_id": claimed.case_id,
                "org_id": claimed.org_id,
                "request_id": f"worker-retry-{claimed.case_id}-{uuid.uuid4().hex[:8]}",
                "plan": claimed.plan,
                "status": "queued",
                "quote_id": None,
            }
            with self.pool.connection() as conn:
                _apply_rls_context(conn, claimed.org_id)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE cases
                        SET status = 'queued',
                            metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                        WHERE id = %s
                        """,
                        (
                            json.dumps(
                                {
                                    "worker_last_error": error_message,
                                    "worker_queue_state": "queued",
                                    "worker_next_retry_at": datetime.fromtimestamp(next_retry_at, tz=timezone.utc).isoformat(),
                                }
                            ),
                            claimed.case_id,
                        ),
                    )
                    cur.execute(
                        """
                        UPDATE agent_runs
                        SET status = 'pending',
                            started_at = NULL,
                            completed_at = NULL,
                            error_message = %s,
                            input = COALESCE(input, '{}'::jsonb) || %s::jsonb
                        WHERE case_id = %s
                          AND agent_name = 'investigation_executor'
                        """,
                        (
                            error_message,
                            json.dumps({"attempt_count": next_attempt, "last_error": error_message}),
                            claimed.case_id,
                        ),
                    )
                    _record_audit_log(
                        cur,
                        organization_id=claimed.org_id,
                        user_id=None,
                        action="case_retry_scheduled",
                        resource_type="case",
                        resource_id=UUID(claimed.case_id),
                        metadata={
                            "request_id": payload["request_id"],
                            "reason": error_message,
                            "attempt_count": next_attempt,
                            "max_attempts": claimed.max_attempts,
                            "next_retry_at": datetime.fromtimestamp(next_retry_at, tz=timezone.utc).isoformat(),
                        },
                    )
                conn.commit()

            await self.redis.zadd(api_settings.investigation_retry_zset_key, {json.dumps(payload, sort_keys=True): next_retry_at})
            await self._decrement_active_counters(claimed.org_id)
            await self.redis.rpush(
                api_settings.investigation_worker_wake_queue_key,
                json.dumps({"event": "retry_scheduled", "case_id": claimed.case_id, "org_id": claimed.org_id}),
            )
            await self._promote_waiting_cases()
            return

        request_id = f"worker-fail-{claimed.case_id}-{uuid.uuid4().hex[:8]}"
        status, body = _request_json(
            "POST",
            f"{worker_settings.investigation_internal_base_url}/api/v1/investigation/{claimed.case_id}/internal/fail",
            data={"reason": error_message},
            headers={
                "X-Org-Id": claimed.org_id,
                "X-Request-Id": request_id,
                "X-Internal-Token": worker_settings.investigation_internal_worker_token,
            },
        )
        if status not in {200, 409}:
            raise RuntimeError(f"internal_fail_failed:{status}:{body}")

        with self.pool.connection() as conn:
            _apply_rls_context(conn, claimed.org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE agent_runs
                    SET status = 'failed',
                        completed_at = NOW(),
                        error_message = %s,
                        output = %s::jsonb,
                        duration_ms = GREATEST(0, FLOOR(EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, NOW()))) * 1000))::integer
                    WHERE case_id = %s
                      AND agent_name = 'investigation_executor'
                    """,
                    (error_message, json.dumps({"error": error_message, "attempt_count": claimed.attempt_count + 1}), claimed.case_id),
                )
            conn.commit()

        await self._decrement_active_counters(claimed.org_id)
        await self._promote_waiting_cases()

    async def _decrement_active_counters(self, org_id: str) -> None:
        async with self.redis.lock(api_settings.investigation_dispatch_lock_key, timeout=10):
            org_count, global_count = await _get_active_counts(self.redis, org_id)
            await self.redis.set(_org_active_counter_key(org_id), max(org_count - 1, 0))
            await self.redis.set(_global_active_counter_key(), max(global_count - 1, 0))

    def _update_case_status(self, org_id: str, case_id: str, status: str, metadata_patch: dict[str, Any]) -> None:
        with self.pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE cases
                    SET status = %s,
                        metadata = COALESCE(metadata, '{}'::jsonb) || %s::jsonb
                    WHERE id = %s
                    """,
                    (status, json.dumps(metadata_patch), case_id),
                )
            conn.commit()

    def _record_worker_audit(self, org_id: str, case_id: str, action: str, metadata: dict[str, Any]) -> None:
        with self.pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                _record_audit_log(
                    cur,
                    organization_id=org_id,
                    user_id=None,
                    action=action,
                    resource_type="case",
                    resource_id=UUID(case_id),
                    metadata=metadata,
                )
            conn.commit()


async def _main() -> None:
    worker = InvestigationWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(_main())
