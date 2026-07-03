#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "staging" / "dossiers"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_ref(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validate_required_files(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"arquivo_ausente: {path}")
    return errors


def build_dossier_payload(
    *,
    window_id: str,
    window_packet: Path,
    ownership_coverage_check: Path,
    placeholder_check: Path,
    handoff_check: Path,
    homologation_artifact: Path,
    homologation_manifest: Path,
    oidc_readiness_bundle: Path | None,
    oidc_readiness_bundle_summary: Path | None,
    regulatory_readiness_bundle: Path | None,
    regulatory_readiness_bundle_summary: Path | None,
    generated_at: str,
) -> dict[str, Any]:
    required_paths = [
        window_packet,
        ownership_coverage_check,
        placeholder_check,
        handoff_check,
        homologation_artifact,
        homologation_manifest,
    ]
    if oidc_readiness_bundle is not None:
        required_paths.append(oidc_readiness_bundle)
    if oidc_readiness_bundle_summary is not None:
        required_paths.append(oidc_readiness_bundle_summary)
    if regulatory_readiness_bundle is not None:
        required_paths.append(regulatory_readiness_bundle)
    if regulatory_readiness_bundle_summary is not None:
        required_paths.append(regulatory_readiness_bundle_summary)
    errors = validate_required_files(required_paths)
    if errors:
        return {
            "kind": "staging_release_dossier",
            "status": "failed",
            "generated_at": generated_at,
            "window_id": window_id,
            "errors": errors,
        }

    ownership_payload = load_json_file(ownership_coverage_check)
    placeholder_payload = load_json_file(placeholder_check)
    handoff_payload = load_json_file(handoff_check)
    homologation_payload = load_json_file(homologation_artifact)
    homologation_manifest_payload = load_json_file(homologation_manifest)
    oidc_bundle_payload = (
        load_json_file(oidc_readiness_bundle)
        if oidc_readiness_bundle is not None
        else None
    )
    regulatory_bundle_payload = (
        load_json_file(regulatory_readiness_bundle)
        if regulatory_readiness_bundle is not None
        else None
    )

    checks_status = {
        "ownership_coverage": ownership_payload.get("status", "unknown"),
        "placeholder_check": placeholder_payload.get("status", "unknown"),
        "handoff_check": handoff_payload.get("status", "unknown"),
        "homologation": homologation_payload.get("status", "unknown"),
    }
    if oidc_bundle_payload is not None:
        checks_status["oidc_readiness_bundle"] = oidc_bundle_payload.get(
            "status", "unknown"
        )
    if regulatory_bundle_payload is not None:
        checks_status["regulatory_readiness_bundle"] = regulatory_bundle_payload.get(
            "status", "unknown"
        )

    status = "ok" if all(value == "ok" for value in checks_status.values()) else "failed"

    result = {
        "kind": "staging_release_dossier",
        "status": status,
        "generated_at": generated_at,
        "window_id": window_id,
        "checks_status": checks_status,
        "artifacts": {
            "window_packet": file_ref(window_packet),
            "ownership_coverage_check": file_ref(ownership_coverage_check),
            "placeholder_check": file_ref(placeholder_check),
            "handoff_check": file_ref(handoff_check),
            "homologation_artifact": file_ref(homologation_artifact),
            "homologation_manifest": file_ref(homologation_manifest),
        },
        "summaries": {
            "ownership_coverage": {
                "missing_in_matrix": ownership_payload.get("missing_in_matrix", []),
                "stale_in_matrix": ownership_payload.get("stale_in_matrix", []),
                "incomplete_mappings": ownership_payload.get("incomplete_mappings", []),
            },
            "placeholder_check": {
                "unresolved_placeholders": placeholder_payload.get("unresolved_placeholders", []),
                "missing_required": placeholder_payload.get("missing_required", []),
                "empty_required": placeholder_payload.get("empty_required", []),
            },
            "handoff_check": {
                "missing_groups": handoff_payload.get("missing_groups", []),
                "incomplete_groups": handoff_payload.get("incomplete_groups", []),
                "invalid_statuses": handoff_payload.get("invalid_statuses", []),
                "invalid_dates": handoff_payload.get("invalid_dates", []),
            },
            "homologation": {
                "mode": homologation_payload.get("mode"),
                "artifact_file": homologation_payload.get("artifact_file"),
                "manifest_file": homologation_payload.get("manifest_file"),
                "runs": {
                    "compliance_request_id": ((homologation_payload.get("runs") or {}).get("compliance") or {}).get(
                        "request_id"
                    ),
                    "rpc_request_id": ((homologation_payload.get("runs") or {}).get("rpc") or {}).get("request_id"),
                    "rpc_case_id": ((homologation_payload.get("runs") or {}).get("rpc") or {}).get("case_id"),
                    "oidc_legal_report_request_id": (
                        (homologation_payload.get("runs") or {}).get("oidc_legal_report") or {}
                    ).get("request_id"),
                    "oidc_legal_report_case_id": (
                        (homologation_payload.get("runs") or {}).get("oidc_legal_report") or {}
                    ).get("case_id"),
                    "oidc_legal_report_report_id": (
                        (homologation_payload.get("runs") or {}).get("oidc_legal_report") or {}
                    ).get("report_id"),
                },
                "manifest": homologation_manifest_payload,
            },
        },
        "sources": {
            "ownership_coverage": ownership_payload,
            "placeholder_check": placeholder_payload,
            "handoff_check": handoff_payload,
            "homologation": homologation_payload,
        },
    }
    if regulatory_readiness_bundle is not None and regulatory_bundle_payload is not None:
        result["artifacts"]["regulatory_readiness_bundle"] = file_ref(
            regulatory_readiness_bundle
        )
        if regulatory_readiness_bundle_summary is not None:
            result["artifacts"]["regulatory_readiness_bundle_summary"] = file_ref(
                regulatory_readiness_bundle_summary
            )
        result["summaries"]["regulatory_readiness_bundle"] = {
            "scope": regulatory_bundle_payload.get("scope", {}),
            "steps": {
                "compliance_provider_runtime": (
                    (regulatory_bundle_payload.get("steps") or {}).get(
                        "compliance_provider_runtime"
                    )
                    or {}
                ).get("status", "unknown"),
                "eu_sanctions_window": (
                    (regulatory_bundle_payload.get("steps") or {}).get(
                        "eu_sanctions_window"
                    )
                    or {}
                ).get("status", "unknown"),
            },
        }
        result["sources"]["regulatory_readiness_bundle"] = regulatory_bundle_payload
    if oidc_readiness_bundle is not None and oidc_bundle_payload is not None:
        result["artifacts"]["oidc_readiness_bundle"] = file_ref(oidc_readiness_bundle)
        if oidc_readiness_bundle_summary is not None:
            result["artifacts"]["oidc_readiness_bundle_summary"] = file_ref(
                oidc_readiness_bundle_summary
            )
        result["summaries"]["oidc_readiness_bundle"] = {
            "scope": oidc_bundle_payload.get("scope", {}),
            "steps": {
                "oidc_preflight": (
                    (oidc_bundle_payload.get("steps") or {}).get("oidc_preflight") or {}
                ).get("status", "unknown"),
                "smoke_auth_oidc_mode": (
                    (oidc_bundle_payload.get("steps") or {}).get("smoke_auth_oidc_mode") or {}
                ).get("status", "unknown"),
            },
        }
        result["sources"]["oidc_readiness_bundle"] = oidc_bundle_payload
    return result


def write_dossier_artifacts(*, payload: dict[str, Any], window_id: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    artifact_path = output_dir / f"staging_release_dossier_{window_id}_{stamp}.json"
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifact_path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    manifest_payload = {
        "kind": "staging_release_dossier",
        "status": payload.get("status"),
        "generated_at": payload.get("generated_at"),
        "window_id": window_id,
        "artifact_file": str(artifact_path),
        "artifact_file_size_bytes": artifact_path.stat().st_size,
        "artifact_file_sha256": digest,
        "attachments": payload.get("artifacts", {}),
        "checks_status": payload.get("checks_status", {}),
    }
    manifest_path = output_dir / f"{artifact_path.name}.manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact_path, manifest_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consolida packet, checks e homologacao em um dossier unico de release para staging."
    )
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--window-packet", required=True)
    parser.add_argument("--ownership-coverage-check", required=True)
    parser.add_argument("--placeholder-check", required=True)
    parser.add_argument("--handoff-check", required=True)
    parser.add_argument("--homologation-artifact", required=True)
    parser.add_argument("--homologation-manifest", required=True)
    parser.add_argument("--oidc-readiness-bundle")
    parser.add_argument("--oidc-readiness-bundle-summary")
    parser.add_argument("--regulatory-readiness-bundle")
    parser.add_argument("--regulatory-readiness-bundle-summary")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--generated-at", help="timestamp ISO-8601 para reproducibilidade em testes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = args.generated_at or utc_now().isoformat()
    payload = build_dossier_payload(
        window_id=args.window_id,
        window_packet=Path(args.window_packet),
        ownership_coverage_check=Path(args.ownership_coverage_check),
        placeholder_check=Path(args.placeholder_check),
        handoff_check=Path(args.handoff_check),
        homologation_artifact=Path(args.homologation_artifact),
        homologation_manifest=Path(args.homologation_manifest),
        oidc_readiness_bundle=(
            Path(args.oidc_readiness_bundle) if args.oidc_readiness_bundle else None
        ),
        oidc_readiness_bundle_summary=(
            Path(args.oidc_readiness_bundle_summary)
            if args.oidc_readiness_bundle_summary
            else None
        ),
        regulatory_readiness_bundle=(
            Path(args.regulatory_readiness_bundle)
            if args.regulatory_readiness_bundle
            else None
        ),
        regulatory_readiness_bundle_summary=(
            Path(args.regulatory_readiness_bundle_summary)
            if args.regulatory_readiness_bundle_summary
            else None
        ),
        generated_at=generated_at,
    )
    artifact_path, manifest_path = write_dossier_artifacts(
        payload=payload,
        window_id=args.window_id,
        output_dir=Path(args.output_dir),
    )
    sys.stdout.write(
        json.dumps(
            {
                "kind": "staging_release_dossier",
                "status": payload.get("status"),
                "window_id": args.window_id,
                "artifact_file": str(artifact_path),
                "manifest_file": str(manifest_path),
                "generated_at": generated_at,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
