#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = REPO_ROOT / ".env.staging.example"
DEFAULT_PRIVATE_ENV_FILE = REPO_ROOT / ".env.staging.private"
DEFAULT_OWNERSHIP_FILE = REPO_ROOT / "docs" / "staging-env-ownership.md"
DEFAULT_CHECKS_DIR = REPO_ROOT / "artifacts" / "staging" / "checks"
DEFAULT_WINDOW_PACKET_DIR = REPO_ROOT / "artifacts" / "staging"
DEFAULT_HOMOLOGATION_OUTPUT_DIR = REPO_ROOT / "artifacts" / "homologation"
DEFAULT_DOSSIER_OUTPUT_DIR = REPO_ROOT / "artifacts" / "staging" / "dossiers"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def step_payload(*, status: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": status}
    payload.update(extra)
    return payload


def build_window_packet_path(window_id: str, packet_path: str | None) -> Path:
    if packet_path:
        return Path(packet_path)
    return DEFAULT_WINDOW_PACKET_DIR / f"window-packet-{window_id}.md"


def run_window(
    *,
    window_id: str,
    env_file: Path,
    private_env_file: Path,
    ownership_file: Path,
    checks_dir: Path,
    window_packet_file: Path,
    homologation_mode: str,
    rpc_expected_mode: str | None,
    homologation_output_dir: Path,
    dossier_output_dir: Path,
    generated_at: str,
) -> tuple[int, dict[str, Any]]:
    checks_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "kind": "staging_window_run",
        "window_id": window_id,
        "generated_at": generated_at,
        "status": "ok",
        "errors": [],
        "files": {
            "env_file": str(env_file),
            "private_env_file": str(private_env_file),
            "ownership_file": str(ownership_file),
            "checks_dir": str(checks_dir),
            "window_packet_file": str(window_packet_file),
            "homologation_output_dir": str(homologation_output_dir),
            "dossier_output_dir": str(dossier_output_dir),
        },
        "steps": {},
    }

    ownership_output_file = checks_dir / f"ownership-coverage-{window_id}.json"
    placeholder_output_file = checks_dir / f"placeholders-{window_id}.json"
    handoff_output_file = checks_dir / f"handoff-{window_id}.json"
    oidc_preflight_output_file = checks_dir / f"oidc-preflight-{window_id}.json"
    external_preflight_output_file = checks_dir / f"external-preflight-{window_id}.json"
    regulatory_bundle_output_file = checks_dir / f"{window_id}-regulatory-readiness-bundle.json"
    homologation_output_file = checks_dir / f"homologation-{window_id}.json"

    ownership_module = load_module("check_staging_env_ownership_coverage", "scripts/check_staging_env_ownership_coverage.py")
    ownership_exit_code, ownership_payload = ownership_module.build_payload(
        env_file=env_file,
        ownership_file=ownership_file,
    )
    write_json_file(ownership_output_file, ownership_payload)
    payload["steps"]["ownership_coverage"] = step_payload(
        status=ownership_payload.get("status", "failed"),
        exit_code=ownership_exit_code,
        output_file=str(ownership_output_file),
    )
    if ownership_exit_code != 0:
        payload["errors"].append("ownership_coverage: falhou")

    if ownership_exit_code == 0:
        try:
            packet_module = load_module("render_staging_window_packet", "scripts/render_staging_window_packet.py")
            model = packet_module.build_packet_model(
                window_id=window_id,
                env_file=env_file,
                ownership_file=ownership_file,
                generated_at=generated_at,
            )
            markdown = packet_module.render_packet_markdown(model)
            window_packet_file.parent.mkdir(parents=True, exist_ok=True)
            window_packet_file.write_text(markdown + "\n", encoding="utf-8")
            payload["steps"]["window_packet"] = step_payload(
                status="ok",
                output_file=str(window_packet_file),
                placeholders_count=len(model["placeholders"]),
                owners_count=len(model["owners"]),
            )
        except Exception as exc:  # noqa: BLE001
            payload["steps"]["window_packet"] = step_payload(status="failed", error=str(exc))
            payload["errors"].append(f"window_packet: {exc}")
    else:
        payload["steps"]["window_packet"] = step_payload(
            status="skipped",
            reason="ownership_coverage_failed",
        )

    placeholders_module = load_module("check_staging_env_placeholders", "scripts/check_staging_env_placeholders.py")
    placeholders_exit_code, placeholders_payload = placeholders_module.build_payload(
        file_path=private_env_file,
        required_non_empty=sorted(placeholders_module.DEFAULT_REQUIRED_NON_EMPTY),
    )
    write_json_file(placeholder_output_file, placeholders_payload)
    payload["steps"]["placeholder_check"] = step_payload(
        status=placeholders_payload.get("status", "failed"),
        exit_code=placeholders_exit_code,
        output_file=str(placeholder_output_file),
    )
    if placeholders_exit_code != 0:
        payload["errors"].append("placeholder_check: falhou")

    handoff_module = load_module("check_staging_env_handoff", "scripts/check_staging_env_handoff.py")
    handoff_exit_code, handoff_payload = handoff_module.build_payload(
        file_path=ownership_file,
        required_groups=sorted(handoff_module.DEFAULT_REQUIRED_GROUPS),
    )
    write_json_file(handoff_output_file, handoff_payload)
    payload["steps"]["handoff_check"] = step_payload(
        status=handoff_payload.get("status", "failed"),
        exit_code=handoff_exit_code,
        output_file=str(handoff_output_file),
    )
    if handoff_exit_code != 0:
        payload["errors"].append("handoff_check: falhou")

    local_gate_failed = any(
        step_name in payload["steps"] and payload["steps"][step_name]["status"] != "ok"
        for step_name in ("ownership_coverage", "window_packet", "placeholder_check", "handoff_check")
    )
    if local_gate_failed:
        payload["steps"]["oidc_preflight"] = step_payload(status="skipped", reason="local_gates_failed")
        payload["steps"]["external_preflight"] = step_payload(status="skipped", reason="local_gates_failed")
        payload["steps"]["homologation"] = step_payload(status="skipped", reason="local_gates_failed")
        payload["steps"]["release_dossier"] = step_payload(status="skipped", reason="local_gates_failed")
        payload["status"] = "failed"
        return 1, payload

    env_values = load_env_values(private_env_file)
    effective_rpc_expected_mode = rpc_expected_mode or env_values.get("ONTRACKCHAIN_EXPECT_RPC_MODE", "live")
    include_oidc_legal_report = env_values.get("MFA_EXTERNAL_PROVIDER_HOMOLOGATED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    with temporary_environ(env_values):
        oidc_exit_code, oidc_payload = run_module_main(
            "scripts/preflight_oidc_serious_env.py",
            ["preflight_oidc_serious_env.py"],
            "preflight_oidc_serious_env_window",
        )
    write_json_file(oidc_preflight_output_file, oidc_payload)
    payload["steps"]["oidc_preflight"] = step_payload(
        status=oidc_payload.get("status", "failed"),
        exit_code=oidc_exit_code,
        output_file=str(oidc_preflight_output_file),
    )
    if oidc_exit_code != 0:
        payload["errors"].append("oidc_preflight: falhou")

    with temporary_environ(env_values):
        external_exit_code, external_payload = run_module_main(
            "scripts/preflight_external_integrations.py",
            ["preflight_external_integrations.py"],
            "preflight_external_integrations_window",
        )
    write_json_file(external_preflight_output_file, external_payload)
    payload["steps"]["external_preflight"] = step_payload(
        status=external_payload.get("status", "failed"),
        exit_code=external_exit_code,
        output_file=str(external_preflight_output_file),
    )
    if external_exit_code != 0:
        payload["errors"].append("external_preflight: falhou")

    preflight_failed = any(
        payload["steps"][step_name]["status"] != "ok"
        for step_name in ("oidc_preflight", "external_preflight")
    )
    if preflight_failed:
        payload["steps"]["regulatory_readiness_bundle"] = step_payload(status="skipped", reason="preflight_failed")
        payload["steps"]["homologation"] = step_payload(status="skipped", reason="preflight_failed")
        payload["steps"]["release_dossier"] = step_payload(status="skipped", reason="preflight_failed")
        payload["status"] = "failed"
        return 1, payload

    with temporary_environ(env_values):
        regulatory_bundle_exit_code, regulatory_bundle_payload = run_module_main(
            "scripts/run_regulatory_readiness_bundle.py",
            [
                "run_regulatory_readiness_bundle.py",
                "--window-id",
                window_id,
                "--private-env-file",
                str(private_env_file),
                "--checks-dir",
                str(checks_dir),
            ],
            "regulatory_readiness_bundle_window",
        )
    write_json_file(regulatory_bundle_output_file, regulatory_bundle_payload)
    payload["steps"]["regulatory_readiness_bundle"] = step_payload(
        status=regulatory_bundle_payload.get("status", "failed"),
        exit_code=regulatory_bundle_exit_code,
        output_file=str(regulatory_bundle_output_file),
    )
    if regulatory_bundle_exit_code != 0:
        enabled_scope = (regulatory_bundle_payload.get("scope") or {}).get(
            "compliance_runtime_enabled"
        ) or (regulatory_bundle_payload.get("scope") or {}).get("eu_window_enabled")
        if enabled_scope or regulatory_bundle_payload.get("errors"):
            payload["errors"].append("regulatory_readiness_bundle: falhou")

    regulatory_bundle_failed = (
        payload["steps"]["regulatory_readiness_bundle"]["status"] == "failed"
    )
    if regulatory_bundle_failed:
        payload["steps"]["homologation"] = step_payload(
            status="skipped", reason="regulatory_readiness_bundle_failed"
        )
        payload["steps"]["release_dossier"] = step_payload(
            status="skipped", reason="regulatory_readiness_bundle_failed"
        )
        payload["status"] = "failed"
        return 1, payload

    with temporary_environ(env_values):
        homologation_exit_code, homologation_payload = run_module_main(
            "scripts/homologation_external_evidence.py",
            [
                "homologation_external_evidence.py",
                "--mode",
                homologation_mode,
                "--rpc-expected-mode",
                effective_rpc_expected_mode,
                "--output-dir",
                str(homologation_output_dir),
                *(
                    ["--include-oidc-legal-report"]
                    if include_oidc_legal_report
                    else []
                ),
            ],
            "homologation_external_evidence_window",
        )
    write_json_file(homologation_output_file, homologation_payload)
    payload["steps"]["homologation"] = step_payload(
        status=homologation_payload.get("status", "failed"),
        exit_code=homologation_exit_code,
        output_file=str(homologation_output_file),
        artifact_file=homologation_payload.get("artifact_file"),
        manifest_file=homologation_payload.get("manifest_file"),
    )
    if homologation_exit_code != 0:
        payload["errors"].append("homologation: falhou")

    homologation_artifact = Path(str(homologation_payload.get("artifact_file") or ""))
    homologation_manifest = Path(str(homologation_payload.get("manifest_file") or ""))
    if not window_packet_file.exists() or not homologation_artifact.exists() or not homologation_manifest.exists():
        payload["steps"]["release_dossier"] = step_payload(
            status="skipped",
            reason="release_inputs_missing",
        )
        payload["errors"].append("release_dossier: artefatos obrigatorios ausentes")
        payload["status"] = "failed"
        return 1, payload

    dossier_module = load_module("build_staging_release_dossier", "scripts/build_staging_release_dossier.py")
    dossier_payload = dossier_module.build_dossier_payload(
        window_id=window_id,
        window_packet=window_packet_file,
        ownership_coverage_check=ownership_output_file,
        placeholder_check=placeholder_output_file,
        handoff_check=handoff_output_file,
        homologation_artifact=homologation_artifact,
        homologation_manifest=homologation_manifest,
        regulatory_readiness_bundle=regulatory_bundle_output_file,
        generated_at=generated_at,
    )
    dossier_artifact_file, dossier_manifest_file = dossier_module.write_dossier_artifacts(
        payload=dossier_payload,
        window_id=window_id,
        output_dir=dossier_output_dir,
    )
    payload["steps"]["release_dossier"] = step_payload(
        status=dossier_payload.get("status", "failed"),
        artifact_file=str(dossier_artifact_file),
        manifest_file=str(dossier_manifest_file),
    )
    if dossier_payload.get("status") != "ok":
        payload["errors"].append("release_dossier: falhou")

    payload["status"] = "ok" if not payload["errors"] else "failed"
    return (0 if payload["status"] == "ok" else 1), payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa a janela de staging ponta a ponta e consolida checks, homologacao e dossier."
    )
    parser.add_argument("--window-id", required=True, help="identificador da janela, ex: stg-2026-06-29-a")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--private-env-file", default=str(DEFAULT_PRIVATE_ENV_FILE))
    parser.add_argument("--ownership-file", default=str(DEFAULT_OWNERSHIP_FILE))
    parser.add_argument("--checks-dir", default=str(DEFAULT_CHECKS_DIR))
    parser.add_argument("--window-packet-file", help="arquivo markdown para o packet; se omitido usa o path padrao da janela")
    parser.add_argument("--homologation-mode", choices=["compliance", "rpc", "both"], default="both")
    parser.add_argument("--rpc-expected-mode", choices=["live", "fallback_only"])
    parser.add_argument("--homologation-output-dir", default=str(DEFAULT_HOMOLOGATION_OUTPUT_DIR))
    parser.add_argument("--dossier-output-dir", default=str(DEFAULT_DOSSIER_OUTPUT_DIR))
    parser.add_argument("--generated-at", help="timestamp ISO-8601 para reproducibilidade em testes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = args.generated_at or utc_now().isoformat()
    exit_code, payload = run_window(
        window_id=args.window_id,
        env_file=Path(args.env_file),
        private_env_file=Path(args.private_env_file),
        ownership_file=Path(args.ownership_file),
        checks_dir=Path(args.checks_dir),
        window_packet_file=build_window_packet_path(args.window_id, args.window_packet_file),
        homologation_mode=args.homologation_mode,
        rpc_expected_mode=args.rpc_expected_mode,
        homologation_output_dir=Path(args.homologation_output_dir),
        dossier_output_dir=Path(args.dossier_output_dir),
        generated_at=generated_at,
    )
    output = sys.stdout if exit_code == 0 else sys.stderr
    output.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
