#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER_PATTERN = re.compile(r"^__FILL_[A-Z0-9_]+__$")

DEFAULT_REQUIRED_NON_EMPTY = [
    "APP_ENV",
    "AUTH_MODE",
    "DEV_AUTH_ENABLED",
    "NEXT_PUBLIC_AUTH_MODE",
    "NEXT_PUBLIC_APP_ENV",
    "NEXT_PUBLIC_DEV_AUTH_ENABLED",
    "OIDC_PROVIDER",
    "NEXT_PUBLIC_API_BASE_URL",
    "KEYCLOAK_PUBLIC_URL",
    "KEYCLOAK_ADMIN_PASSWORD",
    "KEYCLOAK_B2B_CLIENT_SECRET",
    "JWT_HS256_SECRET",
    "MFA_TOTP_SECRET",
    "OIDC_ISSUER_URL",
    "OIDC_AUDIENCE",
    "OIDC_CLIENT_ID",
    "OIDC_JWKS_URL",
    "OIDC_AUTHORIZATION_URL",
    "OIDC_ORG_CLAIM",
    "OIDC_PLAN_CLAIM",
    "OIDC_ROLE_CLAIM",
    "INVESTIGATION_RPC_ENABLED",
    "INVESTIGATION_RPC_PRIMARY_URL",
    "COMPLIANCE_TRM_ENABLED",
    "COMPLIANCE_TRM_SCREENING_URL",
    "COMPLIANCE_TRM_API_KEY",
    "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE",
    "ONTRACKCHAIN_EXPECT_RPC_MODE",
]


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def build_conditionally_allowed_placeholders(values: dict[str, str]) -> set[str]:
    allowed: set[str] = set()
    if not _as_bool(values.get("MFA_EXTERNAL_PROVIDER_HOMOLOGATED")):
        allowed.add("ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN")
    return allowed


def build_effective_required_non_empty(values: dict[str, str], required_non_empty: list[str]) -> list[str]:
    effective = set(required_non_empty)
    rpc_mode = (values.get("ONTRACKCHAIN_EXPECT_RPC_MODE") or "").strip().lower()
    compliance_mode = (values.get("ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE") or "").strip().lower()

    if rpc_mode == "fallback_only":
        effective.discard("INVESTIGATION_RPC_PRIMARY_URL")
        effective.add("INVESTIGATION_RPC_FALLBACK_URL")
    elif rpc_mode == "disabled":
        effective.discard("INVESTIGATION_RPC_PRIMARY_URL")
        effective.discard("INVESTIGATION_RPC_FALLBACK_URL")

    if compliance_mode == "disabled":
        effective.discard("COMPLIANCE_TRM_SCREENING_URL")
        effective.discard("COMPLIANCE_TRM_API_KEY")

    return sorted(effective)


def parse_env_file(file_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def build_payload(*, file_path: Path, required_non_empty: list[str]) -> tuple[int, dict]:
    if not file_path.exists():
        payload = {
            "kind": "staging_env_placeholder_check",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "file": str(file_path),
            "status": "failed",
            "errors": [f"arquivo_ausente: {file_path}"],
            "unresolved_placeholders": [],
            "missing_required": required_non_empty,
            "empty_required": [],
            "checked_keys_count": 0,
        }
        return 1, payload

    values = parse_env_file(file_path)
    conditionally_allowed_placeholders = build_conditionally_allowed_placeholders(values)
    effective_required_non_empty = build_effective_required_non_empty(values, required_non_empty)

    unresolved_placeholders = [
        {"name": key, "value": value}
        for key, value in sorted(values.items())
        if PLACEHOLDER_PATTERN.match(value) and key not in conditionally_allowed_placeholders
    ]

    missing_required = [key for key in effective_required_non_empty if key not in values]
    empty_required = [key for key in effective_required_non_empty if key in values and not values[key].strip()]

    errors: list[str] = []
    if unresolved_placeholders:
        errors.extend(
            [f"placeholder_nao_preenchido: {item['name']}={item['value']}" for item in unresolved_placeholders]
        )
    if missing_required:
        errors.extend([f"variavel_obrigatoria_ausente: {key}" for key in missing_required])
    if empty_required:
        errors.extend([f"variavel_obrigatoria_vazia: {key}" for key in empty_required])

    payload = {
        "kind": "staging_env_placeholder_check",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "file": str(file_path),
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "unresolved_placeholders": unresolved_placeholders,
        "conditionally_allowed_placeholders": sorted(conditionally_allowed_placeholders),
        "effective_required_non_empty": effective_required_non_empty,
        "missing_required": missing_required,
        "empty_required": empty_required,
        "checked_keys_count": len(values),
    }
    return (0 if not errors else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bloqueia rollout de staging enquanto houver placeholders ou variaveis criticas ausentes."
    )
    parser.add_argument(
        "--file",
        default=".env.staging.private",
        help="arquivo de ambiente privado a validar",
    )
    parser.add_argument(
        "--require-non-empty",
        action="append",
        default=[],
        help="variavel adicional que nao pode estar ausente/vazia; pode ser repetida",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    required_non_empty = sorted(set(DEFAULT_REQUIRED_NON_EMPTY + args.require_non_empty))
    exit_code, payload = build_payload(
        file_path=Path(args.file),
        required_non_empty=required_non_empty,
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
