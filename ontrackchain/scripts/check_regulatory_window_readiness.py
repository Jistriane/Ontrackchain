#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_ENV_FILE = REPO_ROOT / ".env.staging.private"
DEFAULT_OWNERSHIP_FILE = REPO_ROOT / "docs/staging-env-ownership.md"
PLACEHOLDER_PATTERN = re.compile(r"^__FILL_[A-Z0-9_]+__$")
URL_TOKEN_REQUIREMENT = "token="

ScopeConfig = dict[str, Any]

SCOPE_CONFIG: dict[str, ScopeConfig] = {
    "p0-02": {
        "required_groups": ["Compliance/AML"],
        "required_vars": [
            "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE",
            "COMPLIANCE_TRM_ENABLED",
            "COMPLIANCE_TRM_SCREENING_URL",
            "COMPLIANCE_TRM_API_KEY",
            "COMPLIANCE_TRM_API_KEY_HEADER",
            "COMPLIANCE_TRM_API_KEY_PREFIX",
            "COMPLIANCE_TRM_TIMEOUT_MS",
            "COMPLIANCE_TRM_MAX_RETRIES",
        ],
        "expected_values": {
            "ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE": "live",
            "COMPLIANCE_TRM_ENABLED": "true",
        },
        "https_vars": ["COMPLIANCE_TRM_SCREENING_URL"],
        "contains_rules": {},
    },
    "p0-03": {
        "required_groups": ["Compliance/AML"],
        "required_vars": [
            "COMPLIANCE_EU_SANCTIONS_SOURCE_URL",
            "DATABASE_URL",
        ],
        "expected_values": {},
        "https_vars": ["COMPLIANCE_EU_SANCTIONS_SOURCE_URL"],
        "contains_rules": {
            "COMPLIANCE_EU_SANCTIONS_SOURCE_URL": URL_TOKEN_REQUIREMENT,
        },
    },
}
SCOPE_CONFIG["p0-04"] = {
    "required_groups": sorted(
        {
            *SCOPE_CONFIG["p0-02"]["required_groups"],
            *SCOPE_CONFIG["p0-03"]["required_groups"],
        }
    ),
    "required_vars": sorted(
        {
            *SCOPE_CONFIG["p0-02"]["required_vars"],
            *SCOPE_CONFIG["p0-03"]["required_vars"],
        }
    ),
    "expected_values": {
        **SCOPE_CONFIG["p0-02"]["expected_values"],
        **SCOPE_CONFIG["p0-03"]["expected_values"],
    },
    "https_vars": sorted(
        {
            *SCOPE_CONFIG["p0-02"]["https_vars"],
            *SCOPE_CONFIG["p0-03"]["https_vars"],
        }
    ),
    "contains_rules": {
        **SCOPE_CONFIG["p0-02"]["contains_rules"],
        **SCOPE_CONFIG["p0-03"]["contains_rules"],
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_env_file(file_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not file_path.exists():
        return values
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def load_module(module_name: str, relative_path: str) -> ModuleType:
    file_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"nao_foi_possivel_carregar_modulo: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_handoff_check(ownership_file: Path, required_groups: list[str]) -> tuple[int, dict[str, Any]]:
    handoff_module = load_module("check_regulatory_window_handoff", "scripts/check_staging_env_handoff.py")
    return handoff_module.build_payload(file_path=ownership_file, required_groups=required_groups)


def normalize_expected(value: str) -> str:
    return value.strip().lower()


def is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.match(value.strip()))


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def build_owner_map(handoff_payload: dict[str, Any]) -> dict[str, str]:
    rows = handoff_payload.get("groups") or []
    owner_map: dict[str, str] = {}
    for row in rows:
        group = str(row.get("group") or "").strip()
        owner = str(row.get("owner") or "").strip()
        if group and owner:
            owner_map[group] = owner
    return owner_map


def build_blocking_classification(*, blockers: list[str]) -> str:
    return "regulatory_blocked" if blockers else "pending_execution"


def build_blocking_context(handoff_payload: dict[str, Any], env_payload: dict[str, Any]) -> dict[str, Any]:
    unresolved_placeholders = [
        str(name)
        for name in (env_payload.get("unresolved_placeholders") or [])
        if str(name).strip()
    ]
    invalid_expected_values = [
        {
            "name": str(item.get("name") or "").strip(),
            "expected": str(item.get("expected") or "").strip(),
            "received": str(item.get("received") or "").strip(),
        }
        for item in (env_payload.get("invalid_expected_values") or [])
        if str(item.get("name") or "").strip()
    ]
    invalid_contains_rules = [
        {
            "name": str(item.get("name") or "").strip(),
            "required_fragment": str(item.get("required_fragment") or "").strip(),
        }
        for item in (env_payload.get("invalid_contains_rules") or [])
        if str(item.get("name") or "").strip()
    ]
    return {
        "missing_private_env_file": any(
            str(error).startswith("arquivo_ausente: ") for error in (env_payload.get("errors") or [])
        ),
        "handoff_missing_groups": [
            str(group)
            for group in (handoff_payload.get("missing_groups") or [])
            if str(group).strip()
        ],
        "handoff_incomplete_groups": handoff_payload.get("incomplete_groups") or [],
        "env_missing_required": [
            str(name)
            for name in (env_payload.get("missing_required") or [])
            if str(name).strip()
        ],
        "env_empty_required": [
            str(name)
            for name in (env_payload.get("empty_required") or [])
            if str(name).strip()
        ],
        "env_unresolved_placeholders": unresolved_placeholders,
        "env_invalid_expected_values": invalid_expected_values,
        "env_invalid_https_values": [
            str(name)
            for name in (env_payload.get("invalid_https_values") or [])
            if str(name).strip()
        ],
        "env_invalid_contains_rules": invalid_contains_rules,
    }


def build_unblock_actions(
    *,
    scope: str,
    config: ScopeConfig,
    private_env_file: Path,
    handoff_payload: dict[str, Any],
    env_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    owner_map = build_owner_map(handoff_payload)
    actions: list[dict[str, Any]] = []
    missing_private_env = any(
        str(error).startswith("arquivo_ausente: ") for error in (env_payload.get("errors") or [])
    )

    if missing_private_env:
        actions.append(
            {
                "owner_group": "Gate Agregado da Janela",
                "owner": "Arquiteto/Responsavel Tecnico",
                "kind": "materialize_private_env",
                "targets": [str(private_env_file)],
                "action": (
                    "Materializar o scaffold privado com "
                    f"`make materialize-staging-private-env WINDOW_ID=<janela> MODE=baseline PRIVATE_ENV_FILE={private_env_file}` "
                    "antes de preencher os segredos reais em canal seguro."
                ),
            }
        )

    for incomplete in (handoff_payload.get("incomplete_groups") or []):
        group = str(incomplete.get("group") or "").strip()
        missing_fields = [
            str(field_name)
            for field_name in (incomplete.get("missing_fields") or [])
            if str(field_name).strip()
        ]
        if not group:
            continue
        actions.append(
            {
                "owner_group": group,
                "owner": owner_map.get(group, "owner_nao_mapeado"),
                "kind": "complete_handoff",
                "targets": missing_fields,
                "action": (
                    "Atualizar `docs/staging-env-ownership.md` em `## Registro de Handoff` "
                    f"para remover pendencias de `{group}` ({', '.join(missing_fields)})."
                ),
            }
        )

    env_targets = unique_preserve_order(
        [
            *[str(name) for name in (env_payload.get("missing_required") or [])],
            *[str(name) for name in (env_payload.get("empty_required") or [])],
            *[str(name) for name in (env_payload.get("unresolved_placeholders") or [])],
            *[
                str(item.get("name") or "")
                for item in (env_payload.get("invalid_expected_values") or [])
            ],
            *[str(name) for name in (env_payload.get("invalid_https_values") or [])],
            *[
                str(item.get("name") or "")
                for item in (env_payload.get("invalid_contains_rules") or [])
            ],
        ]
    )
    if env_targets:
        for group in config["required_groups"]:
            actions.append(
                {
                    "owner_group": group,
                    "owner": owner_map.get(group, "owner_nao_mapeado"),
                    "kind": "fill_scope_env",
                    "targets": env_targets,
                    "action": (
                        f"Preencher/corrigir no `{private_env_file}` as variaveis obrigatorias da trilha `{scope}` "
                        f"sob ownership de `{group}`: {', '.join(env_targets)}."
                    ),
                }
            )
    return actions


def build_blocking_summary(
    *,
    scope: str,
    blocking_context: dict[str, Any],
    blockers: list[str],
) -> str:
    if not blockers:
        return f"Trilha `{scope}` pronta para execucao; handoff e segredos obrigatorios estao coerentes."

    reasons: list[str] = []
    if blocking_context["missing_private_env_file"]:
        reasons.append("`.env.staging.private` ainda nao foi materializado")

    incomplete_groups = [
        str(item.get("group") or "").strip()
        for item in blocking_context["handoff_incomplete_groups"]
        if str(item.get("group") or "").strip()
    ]
    if incomplete_groups:
        reasons.append(f"handoff pendente em {', '.join(unique_preserve_order(incomplete_groups))}")
    elif blocking_context["handoff_missing_groups"]:
        reasons.append(
            "grupos obrigatorios ausentes no handoff: "
            + ", ".join(unique_preserve_order(blocking_context["handoff_missing_groups"]))
        )

    env_problem_count = sum(
        len(blocking_context[key])
        for key in (
            "env_missing_required",
            "env_empty_required",
            "env_unresolved_placeholders",
            "env_invalid_expected_values",
            "env_invalid_https_values",
            "env_invalid_contains_rules",
        )
    )
    if env_problem_count and not blocking_context["missing_private_env_file"]:
        reasons.append(f"{env_problem_count} pendencia(s) de configuracao no escopo regulatorio")

    return f"Trilha `{scope}` bloqueada: {'; '.join(reasons)}."


def build_env_check(file_path: Path, scope: str, config: ScopeConfig) -> tuple[int, dict[str, Any]]:
    values = parse_env_file(file_path)
    errors: list[str] = []
    missing_required: list[str] = []
    empty_required: list[str] = []
    unresolved_placeholders: list[str] = []
    invalid_expected_values: list[dict[str, str]] = []
    invalid_https_values: list[str] = []
    invalid_contains_rules: list[dict[str, str]] = []

    if not file_path.exists():
        payload = {
            "kind": "regulatory_window_env_check",
            "checked_at": utc_now().isoformat(),
            "scope": scope,
            "file": str(file_path),
            "status": "failed",
            "errors": [f"arquivo_ausente: {file_path}"],
            "missing_required": config["required_vars"],
            "empty_required": [],
            "unresolved_placeholders": [],
            "invalid_expected_values": [],
            "invalid_https_values": [],
            "invalid_contains_rules": [],
            "checked_keys_count": 0,
        }
        return 1, payload

    for name in config["required_vars"]:
        raw_value = values.get(name)
        if raw_value is None:
            missing_required.append(name)
            errors.append(f"variavel_obrigatoria_ausente: {name}")
            continue
        if not raw_value.strip():
            empty_required.append(name)
            errors.append(f"variavel_obrigatoria_vazia: {name}")
            continue
        if is_placeholder(raw_value):
            unresolved_placeholders.append(name)
            errors.append(f"placeholder_nao_preenchido: {name}")

    for name, expected in config["expected_values"].items():
        current = values.get(name, "")
        if current and normalize_expected(current) != normalize_expected(expected):
            invalid_expected_values.append(
                {
                    "name": name,
                    "expected": expected,
                    "received": current,
                }
            )
            errors.append(f"valor_invalido: {name} esperado={expected} recebido={current}")

    for name in config["https_vars"]:
        current = values.get(name, "").strip()
        if current and not current.lower().startswith("https://"):
            invalid_https_values.append(name)
            errors.append(f"url_nao_https: {name}")

    for name, required_fragment in config["contains_rules"].items():
        current = values.get(name, "").strip()
        if current and required_fragment.lower() not in current.lower():
            invalid_contains_rules.append(
                {
                    "name": name,
                    "required_fragment": required_fragment,
                }
            )
            errors.append(f"fragmento_obrigatorio_ausente: {name} precisa_conter={required_fragment}")

    payload = {
        "kind": "regulatory_window_env_check",
        "checked_at": utc_now().isoformat(),
        "scope": scope,
        "file": str(file_path),
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "missing_required": missing_required,
        "empty_required": empty_required,
        "unresolved_placeholders": unresolved_placeholders,
        "invalid_expected_values": invalid_expected_values,
        "invalid_https_values": invalid_https_values,
        "invalid_contains_rules": invalid_contains_rules,
        "checked_keys_count": len(values),
    }
    return (0 if not errors else 1), payload


def build_payload(*, scope: str, private_env_file: Path, ownership_file: Path) -> tuple[int, dict[str, Any]]:
    config = SCOPE_CONFIG[scope]
    handoff_exit_code, handoff_payload = build_handoff_check(
        ownership_file=ownership_file,
        required_groups=list(config["required_groups"]),
    )
    env_exit_code, env_payload = build_env_check(
        file_path=private_env_file,
        scope=scope,
        config=config,
    )

    blockers: list[str] = []
    blockers.extend(str(error) for error in (handoff_payload.get("errors") or []) if str(error).strip())
    blockers.extend(str(error) for error in (env_payload.get("errors") or []) if str(error).strip())
    blocking_context = build_blocking_context(handoff_payload, env_payload)
    blocking_classification = build_blocking_classification(blockers=blockers)
    unblock_actions = build_unblock_actions(
        scope=scope,
        config=config,
        private_env_file=private_env_file,
        handoff_payload=handoff_payload,
        env_payload=env_payload,
    )
    blocking_summary = build_blocking_summary(
        scope=scope,
        blocking_context=blocking_context,
        blockers=blockers,
    )

    if blockers:
        readiness_status = "blocked"
        next_action = (
            unblock_actions[0]["action"]
            if unblock_actions
            else f"Corrigir handoff/segredos obrigatorios da trilha `{scope}` antes de executar o gate regulatorio correspondente."
        )
    else:
        readiness_status = "ready_for_execution"
        next_action = f"Executar o gate canônico de `{scope}` com `request_id` auditável e preservar os artefatos da janela."

    payload = {
        "kind": "regulatory_window_readiness_check",
        "checked_at": utc_now().isoformat(),
        "scope": scope,
        "status": "ok" if not blockers else "failed",
        "errors": blockers,
        "blocking_classification": blocking_classification,
        "blocking_summary": blocking_summary,
        "files": {
            "private_env_file": str(private_env_file),
            "ownership_file": str(ownership_file),
        },
        "requirements": {
            "required_groups": list(config["required_groups"]),
            "required_vars": list(config["required_vars"]),
        },
        "checks": {
            "handoff": handoff_payload,
            "env": env_payload,
        },
        "blocking_context": blocking_context,
        "unblock_actions": unblock_actions,
        "readiness": {
            "readiness_status": readiness_status,
            "blockers": blockers,
            "blocking_classification": blocking_classification,
            "blocking_summary": blocking_summary,
            "unblock_actions": unblock_actions,
            "next_action": next_action,
        },
    }
    exit_code = 0 if handoff_exit_code == 0 and env_exit_code == 0 else 1
    return exit_code, payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida se a trilha regulatória P0-02/P0-03/P0-04 está pronta para execução com insumos reais."
    )
    parser.add_argument(
        "--scope",
        choices=sorted(SCOPE_CONFIG),
        required=True,
        help="escopo regulatório a validar",
    )
    parser.add_argument(
        "--private-env-file",
        default=str(DEFAULT_PRIVATE_ENV_FILE),
        help="arquivo privado com secrets e overrides da janela",
    )
    parser.add_argument(
        "--ownership-file",
        default=str(DEFAULT_OWNERSHIP_FILE),
        help="arquivo markdown com o handoff da janela",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exit_code, payload = build_payload(
        scope=args.scope,
        private_env_file=Path(args.private_env_file),
        ownership_file=Path(args.ownership_file),
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
