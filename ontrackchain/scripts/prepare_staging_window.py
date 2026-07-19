#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import re
import shutil
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = REPO_ROOT / ".env.staging.example"
DEFAULT_OWNERSHIP_FILE = REPO_ROOT / "docs" / "staging-env-ownership.md"
DEFAULT_TEMPLATES_DIR = REPO_ROOT / "artifacts" / "staging" / "templates"
DEFAULT_WINDOW_PACKET_DIR = REPO_ROOT / "artifacts" / "staging"
DEFAULT_CHECKS_DIR = REPO_ROOT / "artifacts" / "staging" / "checks"
DEFAULT_DOSSIERS_DIR = REPO_ROOT / "artifacts" / "staging" / "dossiers"
DEFAULT_HOMOLOGATION_DIR = REPO_ROOT / "artifacts" / "homologation"
DEFAULT_PRIVATE_ENV_FILE = REPO_ROOT / ".env.staging.private"
MODE_TO_TEMPLATE = {
    "baseline": "staging-private-baseline.example.env",
    "homologated": "staging-private-homologated.example.env",
}
DEFAULT_REQUIRED_HANDOFF_GROUPS = [
    "Auth/OIDC",
    "Compliance/AML",
    "Investigation/RPC",
    "Platform/Operations",
]
PLACEHOLDER_PATTERN = re.compile(r"^__FILL_[A-Z0-9_]+__$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_directories(paths: list[Path]) -> list[str]:
    created: list[str] = []
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    return created


def build_window_packet_path(window_id: str, output_dir: Path) -> Path:
    return output_dir / f"window-packet-{window_id}.md"


def build_validation_file_path(window_id: str, check_name: str, checks_dir: Path) -> Path:
    return checks_dir / f"{window_id}-{check_name}.json"


def load_env_values(file_path: Path) -> dict[str, str]:
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


def is_placeholder_value(value: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.match(value.strip()))


def determine_regulatory_validation_scopes(private_env_values: dict[str, str]) -> list[str]:
    scopes: list[str] = []
    expect_compliance_mode = private_env_values.get("ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE", "").strip().lower()
    eu_source_url = private_env_values.get("COMPLIANCE_EU_SANCTIONS_SOURCE_URL", "").strip()

    if expect_compliance_mode == "live":
        scopes.append("p0-02")
    if eu_source_url and not is_placeholder_value(eu_source_url):
        scopes.append("p0-03")
    if "p0-02" in scopes and "p0-03" in scopes:
        scopes.append("p0-04")

    return scopes


def run_module_main(relative_path: str, argv: list[str], module_name: str) -> tuple[int, dict[str, Any]]:
    module = load_module(module_name, relative_path)
    stdout = io.StringIO()
    stderr = io.StringIO()
    previous_argv = sys.argv[:]
    try:
        sys.argv = argv
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = module.main()
    finally:
        sys.argv = previous_argv

    exit_code = int(result or 0)
    raw_output = stdout.getvalue().strip() or stderr.getvalue().strip()
    if not raw_output:
        return exit_code, {
            "status": "failed",
            "errors": [f"{relative_path}: execucao sem payload JSON"],
        }
    return exit_code, json.loads(raw_output)


@contextmanager
def temporary_environ(overrides: dict[str, str]) -> Iterator[None]:
    previous: dict[str, str | None] = {}
    for key, value in overrides.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def run_validation_checks(
    *,
    window_id: str,
    env_file: Path,
    ownership_file: Path,
    private_env_file: Path,
    checks_dir: Path,
) -> dict[str, Any]:
    private_env_values = load_env_values(private_env_file)
    ownership_module = load_module(
        "check_staging_env_ownership_coverage",
        "scripts/check_staging_env_ownership_coverage.py",
    )
    handoff_module = load_module(
        "check_staging_env_handoff",
        "scripts/check_staging_env_handoff.py",
    )
    placeholders_module = load_module(
        "check_staging_env_placeholders",
        "scripts/check_staging_env_placeholders.py",
    )
    regulatory_module = load_module(
        "check_regulatory_window_readiness",
        "scripts/check_regulatory_window_readiness.py",
    )

    check_specs = [
        (
            "ownership_coverage",
            ownership_module.build_payload,
            {
                "env_file": env_file,
                "ownership_file": ownership_file,
            },
        ),
        (
            "handoff",
            handoff_module.build_payload,
            {
                "file_path": ownership_file,
                "required_groups": list(DEFAULT_REQUIRED_HANDOFF_GROUPS),
            },
        ),
        (
            "placeholders",
            placeholders_module.build_payload,
            {
                "file_path": private_env_file,
                "required_non_empty": list(placeholders_module.DEFAULT_REQUIRED_NON_EMPTY),
            },
        ),
    ]

    for scope in determine_regulatory_validation_scopes(private_env_values):
        check_specs.append(
            (
                f"regulatory_{scope}",
                regulatory_module.build_payload,
                {
                    "scope": scope,
                    "private_env_file": private_env_file,
                    "ownership_file": ownership_file,
                },
            )
        )

    results: list[dict[str, Any]] = []
    has_failures = False
    for check_name, builder, kwargs in check_specs:
        exit_code, payload = builder(**kwargs)
        output_file = build_validation_file_path(window_id, check_name, checks_dir)
        output_file.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        results.append(
            {
                "name": check_name,
                "status": payload.get("status", "failed"),
                "exit_code": exit_code,
                "output_file": str(output_file),
                "errors": payload.get("errors", []),
            }
        )
        if exit_code != 0:
            has_failures = True

    return {
        "enabled": True,
        "status": "failed" if has_failures else "ok",
        "checks": results,
    }


def run_preflight_checks(
    *,
    window_id: str,
    private_env_file: Path,
    checks_dir: Path,
) -> dict[str, Any]:
    env_values = load_env_values(private_env_file)
    check_specs = [
        (
            "oidc_preflight",
            "scripts/preflight_oidc_serious_env.py",
            ["preflight_oidc_serious_env.py"],
            "prepare_window_oidc_preflight",
        ),
        (
            "external_preflight",
            "scripts/preflight_external_integrations.py",
            ["preflight_external_integrations.py"],
            "prepare_window_external_preflight",
        ),
    ]

    results: list[dict[str, Any]] = []
    has_failures = False
    with temporary_environ(env_values):
        for check_name, relative_path, argv, module_name in check_specs:
            exit_code, payload = run_module_main(relative_path, argv, module_name)
            output_file = build_validation_file_path(window_id, check_name, checks_dir)
            output_file.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
            results.append(
                {
                    "name": check_name,
                    "status": payload.get("status", "failed"),
                    "exit_code": exit_code,
                    "output_file": str(output_file),
                    "errors": payload.get("errors", []),
                }
            )
            if exit_code != 0:
                has_failures = True

    return {
        "enabled": True,
        "status": "failed" if has_failures else "ok",
        "checks": results,
    }


def run_window_execution(
    *,
    window_id: str,
    env_file: Path,
    private_env_file: Path,
    ownership_file: Path,
    checks_dir: Path,
    window_packet_file: Path,
    dossiers_dir: Path,
    homologation_dir: Path,
    generated_at: str,
) -> dict[str, Any]:
    exit_code, payload = run_module_main(
        "scripts/run_staging_window.py",
        [
            "run_staging_window.py",
            "--window-id",
            window_id,
            "--env-file",
            str(env_file),
            "--private-env-file",
            str(private_env_file),
            "--ownership-file",
            str(ownership_file),
            "--checks-dir",
            str(checks_dir),
            "--window-packet-file",
            str(window_packet_file),
            "--homologation-output-dir",
            str(homologation_dir),
            "--dossier-output-dir",
            str(dossiers_dir),
            "--generated-at",
            generated_at,
        ],
        "prepare_window_run_staging_window",
    )
    output_file = build_validation_file_path(window_id, "run_window", checks_dir)
    output_file.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {
        "enabled": True,
        "status": payload.get("status", "failed"),
        "exit_code": exit_code,
        "output_file": str(output_file),
        "payload": payload,
        "errors": payload.get("errors", []),
    }


def prepare_window(
    *,
    window_id: str,
    mode: str,
    env_file: Path,
    ownership_file: Path,
    private_env_file: Path,
    templates_dir: Path,
    window_packet_dir: Path,
    checks_dir: Path,
    dossiers_dir: Path,
    homologation_dir: Path,
    generated_at: str,
    validate: bool,
    preflight: bool,
    run: bool,
) -> dict[str, Any]:
    created_directories = ensure_directories([templates_dir, window_packet_dir, checks_dir, dossiers_dir, homologation_dir])

    templates_module = load_module(
        "render_staging_private_env_templates",
        "scripts/render_staging_private_env_templates.py",
    )
    packet_module = load_module(
        "render_staging_window_packet",
        "scripts/render_staging_window_packet.py",
    )

    template_files = templates_module.write_templates(
        env_file=env_file,
        output_dir=templates_dir,
        generated_at=generated_at,
    )

    selected_template = Path(template_files[mode])
    private_env_file.parent.mkdir(parents=True, exist_ok=True)
    preserved_existing_private_env = False
    if (validate or preflight or run) and private_env_file.exists():
        preserved_existing_private_env = True
    else:
        shutil.copyfile(selected_template, private_env_file)

    packet_model = packet_module.build_packet_model(
        window_id=window_id,
        env_file=env_file,
        ownership_file=ownership_file,
        generated_at=generated_at,
    )
    packet_markdown = packet_module.render_packet_markdown(packet_model)
    window_packet_file = build_window_packet_path(window_id, window_packet_dir)
    window_packet_file.write_text(packet_markdown + "\n", encoding="utf-8")

    checklist = [
        "Escolher o canal seguro para preencher secrets.",
        f"Preencher placeholders do arquivo `{private_env_file}`.",
        "Atualizar `docs/staging-env-ownership.md` em `## Registro de Handoff`.",
        "Se a janela incluir `P0-02/P0-03`, confirmar `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` e reachability do `compliance-api` para o bundle regulatorio embutido.",
        f"Executar `python scripts/run_staging_window.py --window-id {window_id} --private-env-file {private_env_file}`.",
    ]
    if mode == "homologated":
        checklist.insert(
            1,
            "Preencher `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` com token OIDC administrativo valido.",
        )
    else:
        checklist.insert(
            1,
            "Manter `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` como placeholder e `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false` se a janela for apenas baseline.",
        )

    should_preflight = preflight or run
    should_validate = validate or should_preflight
    validation = {
        "enabled": False,
        "status": "skipped",
        "checks": [],
    }
    if should_validate:
        validation = run_validation_checks(
            window_id=window_id,
            env_file=env_file,
            ownership_file=ownership_file,
            private_env_file=private_env_file,
            checks_dir=checks_dir,
        )
        if validation["status"] == "failed":
            checklist.insert(
                0,
                "Corrigir os checks em `artifacts/staging/checks` antes de executar a janela completa.",
            )

    preflight_result = {
        "enabled": False,
        "status": "skipped",
        "checks": [],
    }
    if should_preflight and validation["status"] == "ok":
        preflight_result = run_preflight_checks(
            window_id=window_id,
            private_env_file=private_env_file,
            checks_dir=checks_dir,
        )
        if preflight_result["status"] == "failed":
            checklist.insert(
                0,
                "Corrigir os preflights em `artifacts/staging/checks` antes de executar a janela completa.",
            )
    elif should_preflight and validation["status"] != "ok":
        preflight_result = {
            "enabled": True,
            "status": "skipped",
            "reason": "validation_failed",
            "checks": [],
        }

    run_result = {
        "enabled": run,
        "status": "skipped" if run else "disabled",
        "errors": [],
    }
    if run and validation["status"] == "ok" and preflight_result["status"] == "ok":
        run_result = run_window_execution(
            window_id=window_id,
            env_file=env_file,
            private_env_file=private_env_file,
            ownership_file=ownership_file,
            checks_dir=checks_dir,
            window_packet_file=window_packet_file,
            dossiers_dir=dossiers_dir,
            homologation_dir=homologation_dir,
            generated_at=generated_at,
        )
        if run_result["status"] != "ok":
            checklist.insert(
                0,
                "Corrigir a execucao consolidada em `artifacts/staging/checks` antes de promover a janela.",
            )
    elif run and validation["status"] != "ok":
        run_result = {
            "enabled": True,
            "status": "skipped",
            "reason": "validation_failed",
            "errors": [],
        }
    elif run and preflight_result["status"] != "ok":
        run_result = {
            "enabled": True,
            "status": "skipped",
            "reason": "preflight_failed",
            "errors": [],
        }

    return {
        "kind": "staging_window_preparation",
        "status": "failed"
        if validation["status"] == "failed" or preflight_result["status"] == "failed" or run_result["status"] == "failed"
        else "ok",
        "window_id": window_id,
        "mode": mode,
        "generated_at": generated_at,
        "created_directories": created_directories,
        "env_file": str(env_file),
        "ownership_file": str(ownership_file),
        "artifacts": {
            "selected_template": str(selected_template),
            "private_env_file": str(private_env_file),
            "window_packet_file": str(window_packet_file),
            "templates": template_files,
            "checks_dir": str(checks_dir),
            "dossiers_dir": str(dossiers_dir),
            "homologation_dir": str(homologation_dir),
        },
        "summary": {
            "mfa_external_provider_homologated": "true" if mode == "homologated" else "false",
            "packet_placeholders_count": len(packet_model["placeholders"]),
            "packet_owners_count": len(packet_model["owners"]),
            "private_env_preserved_for_validation": preserved_existing_private_env,
        },
        "validation": validation,
        "preflight": preflight_result,
        "run": run_result,
        "next_steps": checklist,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara a janela seria de staging gerando template privado, packet redigido e diretorios de artefatos."
    )
    parser.add_argument("--window-id", required=True)
    parser.add_argument("--mode", choices=["baseline", "homologated"], default="baseline")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--ownership-file", default=str(DEFAULT_OWNERSHIP_FILE))
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--templates-dir", default=str(DEFAULT_TEMPLATES_DIR))
    parser.add_argument("--window-packet-dir", default=str(DEFAULT_WINDOW_PACKET_DIR))
    parser.add_argument("--checks-dir", default=str(DEFAULT_CHECKS_DIR))
    parser.add_argument("--dossiers-dir", default=str(DEFAULT_DOSSIERS_DIR))
    parser.add_argument("--homologation-dir", default=str(DEFAULT_HOMOLOGATION_DIR))
    parser.add_argument("--generated-at", help="timestamp ISO-8601 para reproducibilidade")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="executa ownership, handoff, placeholders e checks regulatorios aplicaveis apos o preparo, persistindo JSONs em artifacts/staging/checks",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="executa tambem os preflights reais; implica validacao local antes de rodar OIDC e integracoes externas",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="encadeia prepare -> preflight -> run_staging_window; implica validacao local e preflights antes do runner completo",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = args.generated_at or utc_now().isoformat()

    try:
        payload = prepare_window(
            window_id=args.window_id,
            mode=args.mode,
            env_file=Path(args.env_file),
            ownership_file=Path(args.ownership_file),
            private_env_file=Path(args.private_env_file),
            templates_dir=Path(args.templates_dir),
            window_packet_dir=Path(args.window_packet_dir),
            checks_dir=Path(args.checks_dir),
            dossiers_dir=Path(args.dossiers_dir),
            homologation_dir=Path(args.homologation_dir),
            generated_at=generated_at,
            validate=args.validate,
            preflight=args.preflight,
            run=args.run,
        )
    except Exception as exc:  # noqa: BLE001
        payload = {
            "kind": "staging_window_preparation",
            "status": "failed",
            "window_id": args.window_id,
            "mode": args.mode,
            "generated_at": generated_at,
            "errors": [str(exc)],
        }
        sys.stderr.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
        return 1

    output = sys.stdout if payload["status"] == "ok" else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
