from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence


PLAN_ORDER = ["free", "starter", "professional", "enterprise"]


def normalize_slug(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def normalize_plan(plan: str) -> str:
    normalized = normalize_slug(plan)
    return normalized if normalized in PLAN_ORDER else "starter"


def plan_rank(plan: str) -> int:
    return PLAN_ORDER.index(normalize_plan(plan))


def is_available_for_plan(min_plan: str, current_plan: str) -> bool:
    return plan_rank(current_plan) >= plan_rank(min_plan)


def next_plan(current_plan: str) -> str:
    rank = plan_rank(current_plan)
    if rank >= len(PLAN_ORDER) - 1:
        return PLAN_ORDER[-1]
    return PLAN_ORDER[rank + 1]


def resolve_canonical_identifier(
    raw_input: str,
    *,
    canonical_values: Sequence[str],
    aliases: Mapping[str, str],
) -> tuple[str, bool]:
    normalized = normalize_slug(raw_input)
    if normalized in canonical_values:
        return normalized, False
    if normalized in aliases:
        return aliases[normalized], True
    raise KeyError(raw_input)


def pricing_table_hash(table: Mapping) -> str:
    payload = json.dumps(table, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
