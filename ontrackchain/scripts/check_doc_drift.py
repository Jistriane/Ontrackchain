#!/usr/bin/env python3
"""Check documentation drift across canonical baseline documents.

Validates that all canonical documents reference consistent baseline percentages.
Flags any document that deviates from the official scorecard baseline.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

CANONICAL_DOCS = [
    DOCS_DIR / "project-executive-readiness-brief.md",
    DOCS_DIR / "project-risk-register.md",
    DOCS_DIR / "project-release-gates.md",
    DOCS_DIR / "regulatory-readiness.md",
    DOCS_DIR / "project-kpi-scorecard.md",
]

SCORECARD = DOCS_DIR / "project-kpi-scorecard.md"

BASELINE_PATTERN = re.compile(
    r"`(\d{2,3})%`\s*(?:de\s+)?(?:construcao tecnica|construcao total|tecnico|prontidao|construcao)",
    re.IGNORECASE,
)


def extract_scorecard_baseline() -> dict[str, int]:
    """Extract the official baseline from the scorecard."""
    text = SCORECARD.read_text()
    result = {}
    for match in re.finditer(
        r"`(\d{2,3})%`\s+de\s+(construcao tecnica|prontidao regulatoria/operacional|maturidade consolidada)",
        text,
    ):
        result[match.group(2).strip()] = int(match.group(1))
    return result


def extract_doc_baselines(doc_path: Path) -> list[tuple[int, str]]:
    """Extract all baseline percentages from a document."""
    text = doc_path.read_text()
    return [(m.start(), m.group(0)) for m in BASELINE_PATTERN.finditer(text)]


def check_drift() -> list[str]:
    """Check all canonical docs for baseline drift."""
    issues = []

    if not SCORECARD.exists():
        issues.append(f"CRITICAL: Scorecard not found at {SCORECARD}")
        return issues

    official = extract_scorecard_baseline()
    if not official:
        issues.append("CRITICAL: Could not extract baseline from scorecard")
        return issues

    for doc_path in CANONICAL_DOCS:
        if not doc_path.exists():
            issues.append(f"MISSING: {doc_path.name}")
            continue

        baselines = extract_doc_baselines(doc_path)
        for pos, match in baselines:
            for key, expected in official.items():
                if str(expected) in match and key.split()[0] not in match.lower():
                    pass

        text = doc_path.read_text()
        for key, expected in official.items():
            pattern = re.compile(rf"`(\d{{2,3}})%`\s+de\s+.*?{re.escape(key.split()[0])}", re.IGNORECASE)
            for m in pattern.finditer(text):
                actual = int(m.group(1))
                if actual != expected:
                    issues.append(
                        f"DRIFT: {doc_path.name} has {actual}% for '{key}' but scorecard says {expected}%"
                    )

    return issues


def main() -> int:
    issues = check_drift()
    if issues:
        print("Documentation drift detected:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("No documentation drift detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
