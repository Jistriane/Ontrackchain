#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {"node_modules", ".next", "__pycache__", "playwright-report", "test-results"}
ALLOWED_EXACT_PATHS = {
    Path(".env.example"),
    Path(".env.oidc-local.example"),
    Path("docker-compose.yml"),
    Path("docker-compose.oidc-local.yml"),
    Path("apps/auth-service/src/auth_service/main.py"),
    Path("infra/keycloak/realm-ontrackchain.json"),
    Path("infra/keycloak/README.md"),
    Path("scripts/smoke_runtime.py"),
    Path("scripts/smoke_work_items_ownership.py"),
    Path("scripts/smoke_work_items_ownership_backend.py"),
    Path("scripts/check_security_baseline.py"),
    Path("scripts/preflight_external_integrations.py"),
    Path("scripts/preflight_oidc_serious_env.py"),
    Path("tests/test_preflight_guards.py"),
    Path("apps/frontend/tests/e2e/totp.ts"),
}
ALLOWED_PREFIXES = (Path("docs"),)
RULES = (
    ("placeholder_change_me", re.compile(r"change-me(?:-[a-z0-9-]+)?", re.IGNORECASE)),
    ("default_totp_secret", re.compile(r"JBSWY3DPEHPK3PXP")),
    ("placeholder_hash", re.compile(r"not-a-real-hash", re.IGNORECASE)),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    ),
)
TARGET_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".yml", ".yaml", ".env", ".example", ".md"}


def _iter_candidate_files() -> list[Path]:
    candidates: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix in TARGET_SUFFIXES or path.name in {".env.example"}:
            candidates.append(path)
    return sorted(candidates)


def _is_allowlisted(relative_path: Path) -> bool:
    if relative_path in ALLOWED_EXACT_PATHS:
        return True
    return any(relative_path.is_relative_to(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> int:
    failures: list[str] = []
    for file_path in _iter_candidate_files():
        relative_path = file_path.relative_to(ROOT)
        if _is_allowlisted(relative_path):
            continue
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for rule_name, pattern in RULES:
            if pattern.search(content):
                failures.append(f"{relative_path}: encontrou marcador bloqueado ({rule_name})")

    if failures:
        sys.stderr.write("\n".join(failures) + "\n")
        return 1

    print("OK: baseline de seguranca sem placeholders/secrets fora da allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
