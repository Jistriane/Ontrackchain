#!/usr/bin/env python3
"""
Evaluate readiness for automated environment promotion.

Uses historical governance metrics to decide if a staged auto-promotion
(staging -> production) can be safely attempted.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def load_metrics(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def pct(value):
    return round(float(value), 2)


def evaluate(metrics, env, min_allow_rate, max_override_rate, max_block_rate, min_total):
    by_env = metrics.get("by_environment", {}) or {}
    env_stats = by_env.get(env, {})

    total = int(env_stats.get("total", 0))
    allowed = int(env_stats.get("allowed", 0))
    blocked = int(env_stats.get("blocked", 0))
    overridden = int(env_stats.get("overridden", 0))

    allow_rate = pct((allowed / total) * 100) if total else 0.0
    block_rate = pct((blocked / total) * 100) if total else 0.0
    override_rate = pct((overridden / total) * 100) if total else 0.0

    checks = {
        "enough_history": total >= min_total,
        "allow_rate_ok": allow_rate >= min_allow_rate,
        "block_rate_ok": block_rate <= max_block_rate,
        "override_rate_ok": override_rate <= max_override_rate,
    }

    ready = all(checks.values())
    reasons = []
    if not checks["enough_history"]:
        reasons.append(f"insufficient_history(total={total}, required>={min_total})")
    if not checks["allow_rate_ok"]:
        reasons.append(f"allow_rate_too_low({allow_rate}% < {min_allow_rate}%)")
    if not checks["block_rate_ok"]:
        reasons.append(f"block_rate_too_high({block_rate}% > {max_block_rate}%)")
    if not checks["override_rate_ok"]:
        reasons.append(f"override_rate_too_high({override_rate}% > {max_override_rate}%)")

    return {
        "ready": ready,
        "environment": env,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "min_allow_rate": min_allow_rate,
            "max_override_rate": max_override_rate,
            "max_block_rate": max_block_rate,
            "min_total": min_total,
        },
        "stats": {
            "total": total,
            "allowed": allowed,
            "blocked": blocked,
            "overridden": overridden,
            "allow_rate": allow_rate,
            "block_rate": block_rate,
            "override_rate": override_rate,
        },
        "checks": checks,
        "reasons": reasons,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate auto-promotion readiness")
    parser.add_argument("--metrics-file", required=True, help="Path to gate-history-metrics.json")
    parser.add_argument("--environment", default="staging", help="Environment to evaluate")
    parser.add_argument("--min-allow-rate", type=float, default=85.0)
    parser.add_argument("--max-override-rate", type=float, default=10.0)
    parser.add_argument("--max-block-rate", type=float, default=15.0)
    parser.add_argument("--min-total", type=int, default=10)
    parser.add_argument("--output-file", default="", help="Optional file to persist result JSON")
    parser.add_argument("--github-output", action="store_true", help="Emit key=value for GitHub output")

    args = parser.parse_args()

    try:
        metrics = load_metrics(args.metrics_file)
        result = evaluate(
            metrics=metrics,
            env=args.environment,
            min_allow_rate=args.min_allow_rate,
            max_override_rate=args.max_override_rate,
            max_block_rate=args.max_block_rate,
            min_total=args.min_total,
        )
    except Exception as exc:  # pylint: disable=broad-except
        fallback = {
            "ready": False,
            "error": str(exc),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
        if args.github_output:
            print("ready=false")
            print(f"reason={str(exc).replace(' ', '_')}")
        print(json.dumps(fallback, indent=2))
        return 0

    if args.output_file:
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        with open(args.output_file, "w", encoding="utf-8") as file_obj:
            json.dump(result, file_obj, indent=2)

    if args.github_output:
        print(f"ready={'true' if result['ready'] else 'false'}")
        print(f"reason={'ok' if result['ready'] else ';'.join(result['reasons'])}")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
