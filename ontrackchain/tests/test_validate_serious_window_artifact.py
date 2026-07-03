#!/usr/bin/env python3
"""Tests for validate_serious_window_artifact.py"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent))

from validate_serious_window_artifact import validate_artifact


def test_validate_p0_01_only():
    """Test validation for P0-01 scope only."""
    with TemporaryDirectory() as tmpdir:
        checks_dir = Path(tmpdir) / "checks"
        dossiers_dir = Path(tmpdir) / "dossiers"
        window_id = "stg-2026-07-06-a"

        # Create mandatory artifacts
        checks_dir.mkdir(parents=True)
        dossiers_dir.mkdir(parents=True)
        (checks_dir / f"ownership-coverage-{window_id}.json").touch()
        (checks_dir / f"placeholders-{window_id}.json").touch()
        (checks_dir / f"handoff-{window_id}.json").touch()
        (checks_dir / f"oidc-preflight-{window_id}.json").touch()
        (checks_dir / f"external-preflight-{window_id}.json").touch()
        (dossiers_dir / f"{window_id}-dossier.json").touch()

        # Create P0-01 artifacts
        (checks_dir / f"{window_id}-oidc-readiness-bundle.json").touch()
        (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md").touch()

        exit_code, payload = validate_artifact(
            window_id=window_id,
            checks_dir=checks_dir,
            dossiers_dir=dossiers_dir,
            scope=["P0-01"],
        )

        assert exit_code == 0
        assert payload["status"] == "ok"
        assert not payload["missing_artifacts"]
        assert len(payload["found_artifacts"]) > 0


def test_validate_p0_01_missing_oidc_bundle():
    """Test validation fails when OIDC bundle is missing."""
    with TemporaryDirectory() as tmpdir:
        checks_dir = Path(tmpdir) / "checks"
        dossiers_dir = Path(tmpdir) / "dossiers"
        window_id = "stg-2026-07-06-a"

        checks_dir.mkdir(parents=True)
        dossiers_dir.mkdir(parents=True)

        # Create mandatory artifacts
        (checks_dir / f"ownership-coverage-{window_id}.json").touch()
        (checks_dir / f"placeholders-{window_id}.json").touch()
        (checks_dir / f"handoff-{window_id}.json").touch()
        (checks_dir / f"oidc-preflight-{window_id}.json").touch()
        (checks_dir / f"external-preflight-{window_id}.json").touch()
        (dossiers_dir / f"{window_id}-dossier.json").touch()

        # Missing P0-01 bundles
        exit_code, payload = validate_artifact(
            window_id=window_id,
            checks_dir=checks_dir,
            dossiers_dir=dossiers_dir,
            scope=["P0-01"],
        )

        assert exit_code == 1
        assert payload["status"] == "failed"
        assert len(payload["missing_artifacts"]) == 2  # JSON and MD bundles


def test_validate_p0_02_p0_03_consolidated():
    """Test validation for P0-02+P0-03 requiring consolidated bundle."""
    with TemporaryDirectory() as tmpdir:
        checks_dir = Path(tmpdir) / "checks"
        dossiers_dir = Path(tmpdir) / "dossiers"
        window_id = "stg-2026-07-06-a"

        checks_dir.mkdir(parents=True)
        dossiers_dir.mkdir(parents=True)

        # Create mandatory artifacts
        (checks_dir / f"ownership-coverage-{window_id}.json").touch()
        (checks_dir / f"placeholders-{window_id}.json").touch()
        (checks_dir / f"handoff-{window_id}.json").touch()
        (checks_dir / f"oidc-preflight-{window_id}.json").touch()
        (checks_dir / f"external-preflight-{window_id}.json").touch()
        (dossiers_dir / f"{window_id}-dossier.json").touch()

        # Create P0-02/P0-03 consolidated artifacts
        (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").touch()
        (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md").touch()

        exit_code, payload = validate_artifact(
            window_id=window_id,
            checks_dir=checks_dir,
            dossiers_dir=dossiers_dir,
            scope=["P0-02", "P0-03"],
        )

        assert exit_code == 0
        assert payload["status"] == "ok"
        assert not payload["missing_artifacts"]


def test_validate_all_p0_items():
    """Test validation for all P0 items in scope."""
    with TemporaryDirectory() as tmpdir:
        checks_dir = Path(tmpdir) / "checks"
        dossiers_dir = Path(tmpdir) / "dossiers"
        window_id = "stg-2026-07-06-a"

        checks_dir.mkdir(parents=True)
        dossiers_dir.mkdir(parents=True)

        # Create mandatory artifacts
        (checks_dir / f"ownership-coverage-{window_id}.json").touch()
        (checks_dir / f"placeholders-{window_id}.json").touch()
        (checks_dir / f"handoff-{window_id}.json").touch()
        (checks_dir / f"oidc-preflight-{window_id}.json").touch()
        (checks_dir / f"external-preflight-{window_id}.json").touch()
        (dossiers_dir / f"{window_id}-dossier.json").touch()

        # Create P0-01 artifacts
        (checks_dir / f"{window_id}-oidc-readiness-bundle.json").touch()
        (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md").touch()

        # Create P0-02/P0-03 consolidated artifacts
        (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").touch()
        (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md").touch()

        exit_code, payload = validate_artifact(
            window_id=window_id,
            checks_dir=checks_dir,
            dossiers_dir=dossiers_dir,
            scope=["P0-01", "P0-02", "P0-03"],
        )

        assert exit_code == 0
        assert payload["status"] == "ok"
        assert not payload["missing_artifacts"]
        assert len(payload["found_artifacts"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
