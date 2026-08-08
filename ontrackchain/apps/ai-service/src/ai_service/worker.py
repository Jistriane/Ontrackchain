import argparse
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ai_service.main import (
    LawEnforcementExportRequest,
    Settings,
    THEMISRequest,
    _apply_rls_context,
    _fetch_case_data,
    _generate_law_enforcement_package,
    _record_audit_log,
    _record_evidence_event,
    _run_themis,
)


def _dsn(settings: Settings) -> str:
    return (
        f"host={settings.postgres_host} port={settings.postgres_port} "
        f"dbname={settings.postgres_db} user={settings.postgres_user} password={settings.postgres_password}"
    )


def _claim_next_job(cur) -> Optional[dict[str, Any]]:
    cur.execute(
        """
        WITH next_job AS (
            SELECT id
            FROM ai_service_jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        UPDATE ai_service_jobs
        SET status = 'processing'
        WHERE id IN (SELECT id FROM next_job)
        RETURNING *
        """
    )
    return cur.fetchone()


def process_next_job(pool: ConnectionPool, org_id: str) -> Optional[str]:
    with pool.connection() as conn:
        _apply_rls_context(conn, org_id)
        with conn.cursor() as cur:
            job = _claim_next_job(cur)
        conn.commit()

    if not job:
        return None

    analysis_type = job["analysis_type"]
    input_data = job.get("input_data") or {}
    if isinstance(input_data, str):
        input_data = json.loads(input_data)

    actor_user_id = input_data.get("x_user_id")
    case_id = job.get("case_id") or input_data.get("case_id")

    try:
        if analysis_type == "law_enforcement_export":
            request = LawEnforcementExportRequest(
                case_id=str(input_data.get("case_id")),
                format=str(input_data.get("format") or "coaf"),
                include_evidence_hash=bool(input_data.get("include_evidence_hash", True)),
            )
            case_data = _fetch_case_data(pool, org_id, request.case_id)
            result = _generate_law_enforcement_package(request, case_data)
            export_id = str(uuid.uuid4())

            with pool.connection() as conn:
                _apply_rls_context(conn, org_id)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO ai_analysis_results
                            (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                        VALUES (%s, %s, %s, 'law_enforcement_export', %s::jsonb, %s::jsonb, %s)
                        """,
                        (
                            export_id,
                            job["organization_id"],
                            request.case_id,
                            json.dumps({"format": request.format}),
                            json.dumps({"document_type": result["document"].get("type", ""), "evidence_count": len(result["evidence_chain"])}),
                            datetime.now(timezone.utc),
                        ),
                    )
                    _record_evidence_event(
                        cur,
                        organization_id=str(job["organization_id"]),
                        event_type="AI_LAW_ENFORCEMENT_EXPORT_GENERATED",
                        event_payload={"export_id": export_id, "case_id": request.case_id, "format": request.format},
                        actor_user_id=actor_user_id,
                        actor_agent_id="AI-LEExport-Service",
                        case_id=request.case_id,
                        regulatory_basis=["Lei 9.613/98", "Res. 520/2022", "Res. 739/2023"],
                    )

                    cur.execute(
                        """
                        UPDATE ai_service_jobs
                        SET status = 'awaiting_human_gate',
                            human_gate_required = TRUE,
                            required_approvals = 2,
                            result_analysis_id = %s
                        WHERE id = %s
                        """,
                        (export_id, job["id"]),
                    )
                    _record_evidence_event(
                        cur,
                        organization_id=str(job["organization_id"]),
                        event_type="AI_JOB_AWAITING_HUMAN_GATE",
                        event_payload={"job_id": str(job["id"]), "analysis_type": analysis_type, "case_id": request.case_id, "required_approvals": 2},
                        actor_user_id=actor_user_id,
                        actor_agent_id="AI-Jobs-Worker",
                        case_id=request.case_id,
                        regulatory_basis=["BCB Circular 3.978"],
                    )
                    _record_audit_log(
                        cur,
                        organization_id=str(job["organization_id"]),
                        user_id=actor_user_id,
                        action="ai_law_enforcement_export_generated",
                        resource_type="ai_law_enforcement_export",
                        resource_id=export_id,
                        metadata={"case_id": request.case_id, "format": request.format, "evidence_count": len(result["evidence_chain"])},
                    )
                conn.commit()

        elif analysis_type == "themis":
            request = THEMISRequest(
                case_id=str(input_data.get("case_id")),
                address=str(input_data.get("address")),
                chain=str(input_data.get("chain") or "ethereum"),
                action=str(input_data.get("action") or "full"),
            )
            case_data = _fetch_case_data(pool, org_id, request.case_id)
            result = _run_themis(request, case_data)
            themis_id = str(uuid.uuid4())
            human_gate = bool(result.get("human_gate"))

            with pool.connection() as conn:
                _apply_rls_context(conn, org_id)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO ai_analysis_results
                            (id, organization_id, case_id, analysis_type, input_data, result_data, generated_at)
                        VALUES (%s, %s, %s, 'themis', %s::jsonb, %s::jsonb, %s)
                        """,
                        (
                            themis_id,
                            job["organization_id"],
                            request.case_id,
                            json.dumps({"address": request.address, "chain": request.chain, "action": request.action}),
                            json.dumps({"risk_score": result["case_card"].get("risk_score"), "human_gate": human_gate}),
                            datetime.now(timezone.utc),
                        ),
                    )
                    _record_evidence_event(
                        cur,
                        organization_id=str(job["organization_id"]),
                        event_type="AI_THEMIS_CASE_INTELLIGENCE_GENERATED",
                        event_payload={"themis_id": themis_id, "case_id": request.case_id, "human_gate_required": human_gate},
                        actor_user_id=actor_user_id,
                        actor_agent_id="AI-THEMIS-Service",
                        case_id=request.case_id,
                        regulatory_basis=["BCB Circular 3.978", "Res. 520/2022", "Lei 9.613/98"],
                    )
                    status = "awaiting_human_gate" if human_gate else "completed"
                    cur.execute(
                        """
                        UPDATE ai_service_jobs
                        SET status = %s,
                            human_gate_required = %s,
                            required_approvals = 1,
                            result_analysis_id = %s
                        WHERE id = %s
                        """,
                        (status, human_gate, themis_id, job["id"]),
                    )
                    if human_gate:
                        _record_evidence_event(
                            cur,
                            organization_id=str(job["organization_id"]),
                            event_type="AI_JOB_AWAITING_HUMAN_GATE",
                            event_payload={"job_id": str(job["id"]), "analysis_type": analysis_type, "case_id": request.case_id, "required_approvals": 1},
                            actor_user_id=actor_user_id,
                            actor_agent_id="AI-Jobs-Worker",
                            case_id=request.case_id,
                            regulatory_basis=["BCB Circular 3.978"],
                        )
                    _record_audit_log(
                        cur,
                        organization_id=str(job["organization_id"]),
                        user_id=actor_user_id,
                        action="ai_themis_case_intelligence_generated",
                        resource_type="ai_themis",
                        resource_id=themis_id,
                        metadata={"case_id": request.case_id, "action": request.action, "human_gate_required": human_gate},
                    )
                conn.commit()

        else:
            with pool.connection() as conn:
                _apply_rls_context(conn, org_id)
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE ai_service_jobs SET status = 'failed', error_data = %s::jsonb WHERE id = %s",
                        (json.dumps({"code": "UNSUPPORTED_JOB_TYPE", "analysis_type": analysis_type}), job["id"]),
                    )
                conn.commit()

        return str(job["id"])
    except Exception as e:
        with pool.connection() as conn:
            _apply_rls_context(conn, org_id)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ai_service_jobs SET status = 'failed', error_data = %s::jsonb WHERE id = %s",
                    (json.dumps({"code": "WORKER_ERROR", "message": str(e)}), job["id"]),
                )
            conn.commit()
        return str(job["id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--org-id", default=None)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    args = parser.parse_args()

    resolved_org_id = args.org_id or os.getenv("AI_WORKER_ORG_ID")
    if not resolved_org_id:
        raise SystemExit("AI worker requires --org-id or AI_WORKER_ORG_ID")

    settings = Settings()
    pool = ConnectionPool(conninfo=_dsn(settings), kwargs={"row_factory": dict_row})

    try:
        while True:
            processed = process_next_job(pool, resolved_org_id)
            if args.once:
                break
            if not processed:
                time.sleep(args.sleep_seconds)
    finally:
        pool.close()


if __name__ == "__main__":
    main()
