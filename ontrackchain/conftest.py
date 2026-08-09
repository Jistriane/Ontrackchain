"""
Workspace-level conftest.py — Ontrackchain Platform Root (Sprint 18)

Purpose:
  - Inject ALL monorepo package/app src/ directories into sys.path
    BEFORE pytest collects test modules.
  - Eliminate the need for individual sys.path.insert() HACK
    in every test file (T2-08 GAP).
  - This approach is configuration-as-code, requires NO
    `pip install -e ...` editable installs in CI, and is fully
    compatible with both local development and GitHub Actions.

LGPD Notice:
  - This file contains NO personal data. It is a pure build/test
    support file and is excluded from retention policy.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


# ---- Resolve the workspace root (ontrackchain/ directory) ----
WORKSPACE_ROOT: Path = Path(__file__).resolve().parent

PACKAGE_SRC_DIRS: tuple[Path, ...] = (
    WORKSPACE_ROOT / "packages" / "shared" / "src",
    WORKSPACE_ROOT / "packages" / "qa-gateway" / "src",
    WORKSPACE_ROOT / "packages" / "agents" / "src",
)

APP_SRC_DIRS: tuple[Path, ...] = (
    WORKSPACE_ROOT / "apps" / "auth-service" / "src",
    WORKSPACE_ROOT / "apps" / "compliance-api" / "src",
    WORKSPACE_ROOT / "apps" / "case-management" / "src",
    WORKSPACE_ROOT / "apps" / "investigation-api" / "src",
    WORKSPACE_ROOT / "apps" / "monitoring-api" / "src",
    WORKSPACE_ROOT / "apps" / "public-api" / "src",
    WORKSPACE_ROOT / "apps" / "report-api" / "src",
    WORKSPACE_ROOT / "apps" / "ai-service" / "src",
    WORKSPACE_ROOT / "apps" / "mock-oidc" / "src",
)

APP_TESTS_DIRS: tuple[Path, ...] = (
    WORKSPACE_ROOT / "apps" / "auth-service" / "tests",
    WORKSPACE_ROOT / "apps" / "investigation-api" / "tests",
    WORKSPACE_ROOT / "apps" / "case-management" / "tests",
    WORKSPACE_ROOT / "apps" / "compliance-api" / "tests",
    WORKSPACE_ROOT / "apps" / "monitoring-api" / "tests",
    WORKSPACE_ROOT / "apps" / "public-api" / "tests",
    WORKSPACE_ROOT / "apps" / "report-api" / "tests",
    WORKSPACE_ROOT / "apps" / "ai-service" / "tests",
    WORKSPACE_ROOT / "apps" / "mock-oidc" / "tests",
    WORKSPACE_ROOT / "tests",
)


def _ensure_path_in_sys_path(target: Path) -> None:
    """Insert a Path at position 0 in sys.path if not present."""
    path_str = str(target.resolve())
    if target.is_dir() and path_str not in sys.path:
        sys.path.insert(0, path_str)


# ---- Inject PYTHONPATH at collection time (pytest startup) ----
for _src in (*PACKAGE_SRC_DIRS, *APP_SRC_DIRS, *APP_TESTS_DIRS):
    _ensure_path_in_sys_path(_src)

# Also expose to subprocess pytest runners via env (tox/nox):
_PROJECT_PYTHONPATH = os.pathsep.join(str(p.resolve()) for p in (
    *PACKAGE_SRC_DIRS,
    *APP_SRC_DIRS,
    *APP_TESTS_DIRS,
    WORKSPACE_ROOT,
))
os.environ["PYTHONPATH"] = (
    f"{_PROJECT_PYTHONPATH}{os.pathsep}{os.environ['PYTHONPATH']}"
    if "PYTHONPATH" in os.environ
    else _PROJECT_PYTHONPATH
)
