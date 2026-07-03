#!/usr/bin/env python3
"""
Validador agregado para artifact da janela séria.

Verifica a presença de bundles OIDC e regulatório conforme o escopo da janela.

Uso:
    python scripts/validate_serious_window_artifact.py \\
        --window-id stg-2026-07-06-a \\
        --checks-dir artifacts/staging/checks \\
        --dossiers-dir artifacts/staging/dossiers \\
        --scope P0-01,P0-02,P0-03
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any]:
    """Load JSON file safely."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def validate_artifact(
    *,
    window_id: str,
    checks_dir: Path,
    dossiers_dir: Path,
    scope: list[str],
) -> tuple[int, dict[str, Any]]:
    """
    Validate serious window artifact completeness.

    Args:
        window_id: Window identifier (e.g., "stg-2026-07-06-a")
        checks_dir: Path to checks directory
        dossiers_dir: Path to dossiers directory
        scope: List of P0 items in scope (e.g., ["P0-01", "P0-02", "P0-03"])

    Returns:
        (exit_code, payload)
    """
    payload: dict[str, Any] = {
        "kind": "serious_window_artifact_validation",
        "window_id": window_id,
        "scope": scope,
        "status": "ok",
        "errors": [],
        "missing_artifacts": [],
        "found_artifacts": [],
    }

    checks_dir.mkdir(parents=True, exist_ok=True)
    dossiers_dir.mkdir(parents=True, exist_ok=True)

    # Artefatos esperados baseado no escopo
    expected: dict[str, list[tuple[Path, str]]] = {
        "P0-01": [
            (checks_dir / f"{window_id}-oidc-readiness-bundle.json", "OIDC bundle JSON"),
            (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md", "OIDC bundle summary"),
        ],
        "P0-02": [
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json", "Regulatory bundle JSON"),
        ],
        "P0-03": [
            (checks_dir / f"{window_id}-eu-sanctions-preflight.json", "EU sanctions preflight"),
            (checks_dir / f"{window_id}-eu-sanctions-sync.json", "EU sanctions sync"),
        ],
    }

    # Artefatos obrigatórios para qualquer escopo
    mandatory_artifacts = [
        (checks_dir / f"ownership-coverage-{window_id}.json", "Ownership coverage"),
        (checks_dir / f"placeholders-{window_id}.json", "Placeholders check"),
        (checks_dir / f"handoff-{window_id}.json", "Handoff check"),
        (checks_dir / f"oidc-preflight-{window_id}.json", "OIDC preflight"),
        (checks_dir / f"external-preflight-{window_id}.json", "External preflight"),
        (dossiers_dir / f"{window_id}-dossier.json", "Release dossier"),
    ]

    # Se P0-02 e P0-03 estão juntos, exige o bundle regulatório consolidado
    if "P0-02" in scope and "P0-03" in scope:
        expected["P0-02/P0-03"] = [
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json", "Regulatory bundle JSON"),
            (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md", "Regulatory bundle summary"),
        ]
        # Remove os artefatos individuais quando bundlificado
        if "P0-02" in expected:
            del expected["P0-02"]
        if "P0-03" in expected:
            del expected["P0-03"]

    # Valida artefatos obrigatórios
    for artifact_path, artifact_name in mandatory_artifacts:
        if not artifact_path.exists():
            payload["missing_artifacts"].append(str(artifact_path))
            payload["errors"].append(f"Mandatory artifact missing: {artifact_name} ({artifact_path.name})")
        else:
            payload["found_artifacts"].append(str(artifact_path))

    # Valida artefatos por escopo
    for p0_item in scope:
        if p0_item in expected:
            for artifact_path, artifact_name in expected[p0_item]:
                if not artifact_path.exists():
                    payload["missing_artifacts"].append(str(artifact_path))
                    payload["errors"].append(
                        f"Scoped artifact missing for {p0_item}: {artifact_name} ({artifact_path.name})"
                    )
                else:
                    payload["found_artifacts"].append(str(artifact_path))

    if payload["missing_artifacts"]:
        payload["status"] = "failed"

    return (0 if payload["status"] == "ok" else 1, payload)


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Validate serious window artifact completeness.",
    )
    parser.add_argument("--window-id", required=True, help="Window ID (e.g., stg-2026-07-06-a)")
    parser.add_argument(
        "--checks-dir",
        default="artifacts/staging/checks",
        help="Path to checks directory",
    )
    parser.add_argument(
        "--dossiers-dir",
        default="artifacts/staging/dossiers",
        help="Path to dossiers directory",
    )
    parser.add_argument(
        "--scope",
        required=True,
        help="Comma-separated scope (e.g., P0-01,P0-02,P0-03)",
    )

    args = parser.parse_args()
    checks_dir = Path(args.checks_dir)
    dossiers_dir = Path(args.dossiers_dir)
    scope = [item.strip() for item in args.scope.split(",")]

    exit_code, payload = validate_artifact(
        window_id=args.window_id,
        checks_dir=checks_dir,
        dossiers_dir=dossiers_dir,
        scope=scope,
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
