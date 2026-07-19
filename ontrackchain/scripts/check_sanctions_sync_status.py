#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import uuid
from typing import Any

DEFAULT_LISTS = ("OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED")
DEFAULT_REQUIRED_SUCCESS = ("OFAC_SDN", "UN_CSNU")


def _env(name: str, default: str | None = None) -> str:
    return os.getenv(name, default or "").strip()


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_rows(*, database_url: str, list_names: list[str]) -> list[dict[str, Any]]:
    try:
        psycopg = importlib.import_module("psycopg")
    except ImportError as exc:  # pragma: no cover - exercised in runtime, not unit tests
        raise RuntimeError("psycopg nao esta instalado no interpretador atual") from exc

    placeholders = ", ".join(["%s"] * len(list_names))
    query = f"""
        SELECT list_name, source_url, status, last_sync_status, status_reason, updated_at
          FROM sanctions_lists_meta
         WHERE list_name IN ({placeholders})
         ORDER BY list_name
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, list_names)
            rows = cur.fetchall()

    payload: list[dict[str, Any]] = []
    for row in rows:
        payload.append(
            {
                "list_name": row[0],
                "source_url": row[1] or "",
                "status": row[2] or "",
                "last_sync_status": row[3] or "",
                "status_reason": row[4] or "",
                "updated_at": row[5].isoformat() if row[5] is not None else None,
            }
        )
    return payload


def _build_eu_correlation(
    *,
    checks: list[dict[str, Any]],
    eu_override_url: str,
    require_eu_override: bool,
) -> dict[str, Any]:
    eu_check = next(
        (
            item
            for item in checks
            if isinstance(item, dict) and item.get("list_name") == "EU_CONSOLIDATED"
        ),
        {},
    )
    observed_source_url = str(eu_check.get("source_url") or "")
    persisted_status = str(eu_check.get("persisted_status") or "")
    last_sync_status = str(eu_check.get("last_sync_status") or "")
    override_tokenized = "token=" in eu_override_url.lower() if eu_override_url else False
    source_url_matches_expected = bool(eu_override_url) and observed_source_url == eu_override_url
    persisted_status_active = persisted_status == "ACTIVE"
    last_sync_status_success = last_sync_status == "SUCCESS"
    return {
        "expected_source_url": eu_override_url,
        "observed_source_url": observed_source_url,
        "source_url_matches_expected": source_url_matches_expected,
        "override_present": bool(eu_override_url),
        "override_required": require_eu_override,
        "override_tokenized": override_tokenized,
        "persisted_status": persisted_status,
        "persisted_status_active": persisted_status_active,
        "last_sync_status": last_sync_status,
        "last_sync_status_success": last_sync_status_success,
        "status_reason": str(eu_check.get("status_reason") or ""),
        "updated_at": eu_check.get("updated_at"),
        "eu_window_converges_ready": (
            source_url_matches_expected
            and override_tokenized
            and persisted_status_active
            and last_sync_status_success
        ),
    }


def build_payload(
    *,
    database_url: str,
    list_names: list[str],
    require_success: list[str],
    eu_override_url: str,
    ofac_override_url: str,
    require_eu_override: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    if not database_url:
        return {
            "kind": "sanctions_sync_status_check",
            "status": "failed",
            "errors": ["DATABASE_URL: variavel obrigatoria ausente"],
            "checks": [],
            "list_names": list_names,
            "require_success": require_success,
        }

    if require_eu_override and not eu_override_url:
        errors.append("COMPLIANCE_EU_SANCTIONS_SOURCE_URL: override tokenizado obrigatorio para janela UE")

    rows = _load_rows(database_url=database_url, list_names=list_names)
    rows_by_name = {row["list_name"]: row for row in rows}

    for list_name in list_names:
        row = rows_by_name.get(list_name)
        if row is None:
            detail = f"{list_name}: lista ausente em sanctions_lists_meta"
            errors.append(detail)
            checks.append({"list_name": list_name, "status": "failed", "details": detail})
            continue

        row_errors: list[str] = []
        expected_override = ""
        if list_name == "EU_CONSOLIDATED":
            expected_override = eu_override_url
        elif list_name == "OFAC_SDN":
            expected_override = ofac_override_url

        if list_name in require_success:
            if row["status"] != "ACTIVE":
                row_errors.append(f"status esperado=ACTIVE recebido={row['status'] or '<vazio>'}")
            if row["last_sync_status"] != "SUCCESS":
                row_errors.append(
                    f"last_sync_status esperado=SUCCESS recebido={row['last_sync_status'] or '<vazio>'}"
                )

        if expected_override and row["source_url"] != expected_override:
            row_errors.append(
                f"source_url divergente do override esperado ({row['source_url'] or '<vazio>'} != {expected_override})"
            )

        if list_name == "EU_CONSOLIDATED" and eu_override_url and "token=" not in eu_override_url.lower():
            row_errors.append("override da UE informado sem token=; esperado link XML tokenizado")

        details = (
            f"status={row['status'] or '<vazio>'}, "
            f"last_sync_status={row['last_sync_status'] or '<vazio>'}, "
            f"source_url={row['source_url'] or '<vazio>'}"
        )
        if row["status_reason"]:
            details += f", status_reason={row['status_reason']}"

        checks.append(
            {
                "list_name": list_name,
                "status": "failed" if row_errors else "ok",
                "details": details,
                "source_url": row["source_url"],
                "persisted_status": row["status"],
                "last_sync_status": row["last_sync_status"],
                "status_reason": row["status_reason"],
                "updated_at": row["updated_at"],
                "errors": row_errors,
            }
        )
        errors.extend(f"{list_name}: {message}" for message in row_errors)

    eu_correlation = _build_eu_correlation(
        checks=checks,
        eu_override_url=eu_override_url,
        require_eu_override=require_eu_override,
    )
    eu_window_ready = eu_correlation.get("eu_window_converges_ready") is True
    readiness = {
        "technical_status": "ok" if not errors else "blocked",
        "readiness_status": (
            "ready_for_validation"
            if require_eu_override and not errors and eu_window_ready
            else "ok" if not errors else "blocked"
        ),
        "promotion_requires_manual_review": True,
        "next_action": (
            "Revisar source_url, ACTIVE/SUCCESS e anexar a janela UE a governanca semanal antes de promover P0-03."
            if require_eu_override and not errors and eu_window_ready
            else "Corrigir o estado persistido ou o override esperado antes de promover a janela UE."
            if errors
            else "Usar este checker como validacao pontual do estado persistido e complementar com a janela UE formal quando aplicavel."
        ),
    }

    return {
        "kind": "sanctions_sync_status_check",
        "status": "failed" if errors else "ok",
        "errors": errors,
        "checks": checks,
        "request_id": request_id or f"sanctions-sync-{uuid.uuid4().hex[:12]}",
        "list_names": list_names,
        "require_success": require_success,
        "overrides": {
            "eu_present": bool(eu_override_url),
            "eu_required": require_eu_override,
            "eu_tokenized": "token=" in eu_override_url.lower() if eu_override_url else False,
            "ofac_present": bool(ofac_override_url),
        },
        "correlation": eu_correlation,
        "readiness": readiness,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica o estado persistido de sincronizacao das listas sancionatorias em sanctions_lists_meta."
    )
    parser.add_argument("--database-url", default=_env("DATABASE_URL"))
    parser.add_argument("--lists", default=",".join(DEFAULT_LISTS))
    parser.add_argument("--require-success", default="")
    parser.add_argument("--require-eu-success", action="store_true")
    parser.add_argument("--eu-window", action="store_true")
    parser.add_argument("--eu-override-url", default=_env("COMPLIANCE_EU_SANCTIONS_SOURCE_URL"))
    parser.add_argument("--ofac-override-url", default=_env("COMPLIANCE_OFAC_SDN_SOURCE_URL"))
    parser.add_argument(
        "--request-id",
        default=_env("ONTRACKCHAIN_REGULATORY_EU_REQUEST_ID", f"eu-sync-{uuid.uuid4().hex[:12]}"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    list_names = _parse_csv(args.lists) or list(DEFAULT_LISTS)
    require_success = _parse_csv(args.require_success) or list(DEFAULT_REQUIRED_SUCCESS)
    if args.eu_window and "EU_CONSOLIDATED" not in list_names:
        list_names.append("EU_CONSOLIDATED")
    if args.eu_window or args.require_eu_success or args.eu_override_url:
        if "EU_CONSOLIDATED" not in require_success:
            require_success.append("EU_CONSOLIDATED")

    payload = build_payload(
        database_url=args.database_url,
        list_names=list_names,
        require_success=require_success,
        eu_override_url=args.eu_override_url,
        ofac_override_url=args.ofac_override_url,
        require_eu_override=args.eu_window,
        request_id=args.request_id,
    )
    output = sys.stdout if payload["status"] == "ok" else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
