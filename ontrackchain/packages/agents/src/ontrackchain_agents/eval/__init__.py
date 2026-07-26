"""
Evaluation Pipeline — Continuous quality assurance for all agents.

Architecture:
  Golden Dataset (per agent) → CI/CD Regression → Production Monitoring → Regulatory Audit

Metrics tracked:
  - Precision, Recall, Citation accuracy
  - Tool invocation accuracy (Class C)
  - Latency P50/P95/P99
  - Cost per call (tokens)
  - Fallback rate to Groq
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class GoldenTestCase:
    """A test case in the golden dataset."""
    case_id: str
    agent_id: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any]
    expected_classification: str = ""    # FATO, INFERÊNCIA, HIPÓTESE
    expected_citations: list[str] = field(default_factory=list)
    expected_tool_calls: list[str] = field(default_factory=list)
    difficulty: str = "medium"           # easy, medium, hard
    reviewed_by: str = ""                # Human reviewer
    created_at: str = ""


@dataclass
class EvalResult:
    """Result of evaluating a single test case."""
    case_id: str
    agent_id: str
    passed: bool
    precision: float = 0.0
    recall: float = 0.0
    citation_accuracy: float = 0.0
    tool_invocation_accuracy: float = 0.0
    latency_ms: int = 0
    tokens_used: int = 0
    error: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalReport:
    """Aggregate evaluation report for an agent."""
    agent_id: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    avg_precision: float
    avg_recall: float
    avg_citation_accuracy: float
    avg_tool_invocation_accuracy: float
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    regression_detected: bool
    timestamp: str = ""


@dataclass
class ProductionSample:
    """A sampled production call for review."""
    sample_id: str
    agent_id: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    latency_ms: int
    tokens_used: int
    provider: str                       # anthropic | groq
    reviewed: bool = False
    review_score: Optional[int] = None  # 1-5
    review_notes: str = ""
    sampled_at: str = ""


class EvalPipeline:
    """
    Continuous evaluation pipeline for all agents.

    Components:
      1. Golden Dataset Management
      2. CI/CD Regression Testing
      3. Production Sampling & Review
      4. Regulatory Audit Reporting
    """

    def __init__(self) -> None:
        self._golden_datasets: dict[str, list[GoldenTestCase]] = {}
        self._production_samples: list[ProductionSample] = []
        self._eval_results: list[EvalResult] = []

    # ─── Golden Dataset Management ─────────────────────────────────────────

    def register_golden_dataset(self, agent_id: str, cases: list[GoldenTestCase]) -> None:
        """Register a golden dataset for an agent."""
        self._golden_datasets[agent_id] = cases
        logger.info(
            "eval.golden_dataset.registered",
            extra={"agent_id": agent_id, "case_count": len(cases)},
        )

    def add_golden_case(self, agent_id: str, case: GoldenTestCase) -> None:
        """Add a single case to an agent's golden dataset."""
        if agent_id not in self._golden_datasets:
            self._golden_datasets[agent_id] = []
        self._golden_datasets[agent_id].append(case)

    def get_golden_dataset(self, agent_id: str) -> list[GoldenTestCase]:
        """Get the golden dataset for an agent."""
        return self._golden_datasets.get(agent_id, [])

    # ─── CI/CD Regression Testing ──────────────────────────────────────────

    async def run_regression(
        self,
        agent_id: str,
        eval_fn: Any,  # Callable that takes input_data and returns output
    ) -> EvalReport:
        """
        Run regression test against golden dataset.

        Called on every prompt/config change before deploy.
        Blocks deploy if regression detected.
        """
        cases = self.get_golden_dataset(agent_id)
        if not cases:
            logger.warning("eval.regression.no_dataset", extra={"agent_id": agent_id})
            return EvalReport(
                agent_id=agent_id,
                total_cases=0, passed_cases=0, failed_cases=0,
                avg_precision=0, avg_recall=0, avg_citation_accuracy=0,
                avg_tool_invocation_accuracy=0, avg_latency_ms=0,
                p95_latency_ms=0, total_tokens=0, regression_detected=False,
            )

        results = []
        for case in cases:
            start = time.monotonic()
            try:
                output = await eval_fn(case.input_data)
                latency_ms = int((time.monotonic() - start) * 1000)

                result = self._evaluate_case(case, output, latency_ms)
                results.append(result)

            except Exception as e:
                latency_ms = int((time.monotonic() - start) * 1000)
                results.append(EvalResult(
                    case_id=case.case_id,
                    agent_id=agent_id,
                    passed=False,
                    latency_ms=latency_ms,
                    error=str(e),
                ))

        return self._compile_report(agent_id, results)

    def _evaluate_case(
        self,
        expected: GoldenTestCase,
        actual: dict[str, Any],
        latency_ms: int,
    ) -> EvalResult:
        """Evaluate a single test case."""
        # Precision: how much of the output is correct
        precision = self._compute_precision(expected.expected_output, actual)

        # Recall: how much of the expected output is present
        recall = self._compute_recall(expected.expected_output, actual)

        # Citation accuracy
        citation_accuracy = self._compute_citation_accuracy(
            expected.expected_citations,
            actual.get("citations", []),
        )

        # Tool invocation accuracy (for Class C)
        tool_accuracy = 1.0
        if expected.expected_tool_calls:
            tool_accuracy = self._compute_tool_accuracy(
                expected.expected_tool_calls,
                actual.get("tool_calls", []),
            )

        # Overall pass/fail
        passed = (
            precision >= 0.8
            and recall >= 0.7
            and citation_accuracy >= 0.9
            and tool_accuracy >= 0.95
        )

        return EvalResult(
            case_id=expected.case_id,
            agent_id=expected.agent_id,
            passed=passed,
            precision=precision,
            recall=recall,
            citation_accuracy=citation_accuracy,
            tool_invocation_accuracy=tool_accuracy,
            latency_ms=latency_ms,
        )

    def _compute_precision(self, expected: dict, actual: dict) -> float:
        """Compute precision of output."""
        # Simplified: check key fields match
        if not expected or not actual:
            return 0.5

        matching = 0
        total = len(expected)
        for key, value in expected.items():
            if key in actual:
                if actual[key] == value:
                    matching += 1
                elif isinstance(value, str) and isinstance(actual[key], str):
                    # Partial match for text fields
                    if value.lower() in actual[key].lower():
                        matching += 0.8

        return matching / total if total > 0 else 0.5

    def _compute_recall(self, expected: dict, actual: dict) -> float:
        """Compute recall of output."""
        if not expected:
            return 1.0

        found = sum(1 for key in expected if key in actual)
        return found / len(expected)

    def _compute_citation_accuracy(
        self,
        expected_citations: list[str],
        actual_citations: list[str],
    ) -> float:
        """Compute citation accuracy."""
        if not expected_citations:
            return 1.0

        matched = 0
        for expected in expected_citations:
            for actual in actual_citations:
                if expected.lower() in actual.lower():
                    matched += 1
                    break

        return matched / len(expected_citations)

    def _compute_tool_accuracy(
        self,
        expected_tools: list[str],
        actual_tools: list[str],
    ) -> float:
        """Compute tool invocation accuracy."""
        if not expected_tools:
            return 1.0

        matched = sum(1 for t in expected_tools if t in actual_tools)
        return matched / len(expected_tools)

    def _compile_report(self, agent_id: str, results: list[EvalResult]) -> EvalReport:
        """Compile evaluation results into a report."""
        if not results:
            return EvalReport(
                agent_id=agent_id, total_cases=0, passed_cases=0, failed_cases=0,
                avg_precision=0, avg_recall=0, avg_citation_accuracy=0,
                avg_tool_invocation_accuracy=0, avg_latency_ms=0,
                p95_latency_ms=0, total_tokens=0, regression_detected=False,
            )

        passed = sum(1 for r in results if r.passed)
        latencies = sorted([r.latency_ms for r in results])
        p95_idx = int(len(latencies) * 0.95)

        return EvalReport(
            agent_id=agent_id,
            total_cases=len(results),
            passed_cases=passed,
            failed_cases=len(results) - passed,
            avg_precision=sum(r.precision for r in results) / len(results),
            avg_recall=sum(r.recall for r in results) / len(results),
            avg_citation_accuracy=sum(r.citation_accuracy for r in results) / len(results),
            avg_tool_invocation_accuracy=sum(r.tool_invocation_accuracy for r in results) / len(results),
            avg_latency_ms=sum(r.latency_ms for r in results) / len(results),
            p95_latency_ms=latencies[p95_idx] if latencies else 0,
            total_tokens=sum(r.tokens_used for r in results),
            regression_detected=passed / len(results) < 0.85,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # ─── Production Sampling ───────────────────────────────────────────────

    def sample_production_call(
        self,
        agent_id: str,
        input_data: dict,
        output_data: dict,
        latency_ms: int,
        tokens_used: int,
        provider: str,
        sampling_rate: float = 0.05,
    ) -> Optional[ProductionSample]:
        """
        Sample a production call for human review.

        Returns a sample if the call was selected for review.
        """
        import random
        if random.random() > sampling_rate:
            return None

        sample = ProductionSample(
            sample_id=f"sample_{agent_id}_{int(time.time())}",
            agent_id=agent_id,
            input_data=input_data,
            output_data=output_data,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            provider=provider,
            sampled_at=datetime.now(timezone.utc).isoformat(),
        )
        self._production_samples.append(sample)

        logger.info(
            "eval.production.sampled",
            extra={"agent_id": agent_id, "sample_id": sample.sample_id},
        )
        return sample

    def record_review(
        self,
        sample_id: str,
        score: int,
        notes: str = "",
    ) -> None:
        """Record a human review of a sampled call."""
        for sample in self._production_samples:
            if sample.sample_id == sample_id:
                sample.reviewed = True
                sample.review_score = score
                sample.review_notes = notes

                # Alert if score is low
                if score < 3:
                    logger.warning(
                        "eval.production.low_score",
                        extra={
                            "sample_id": sample_id,
                            "agent_id": sample.agent_id,
                            "score": score,
                        },
                    )
                break

    # ─── Regulatory Audit Reporting ────────────────────────────────────────

    def generate_regulatory_audit_report(self, agent_id: str) -> dict[str, Any]:
        """
        Generate quarterly regulatory audit report.

        For IN BCB 739 compliance (items II and VI).
        """
        samples = [s for s in self._production_samples if s.agent_id == agent_id]
        reviewed = [s for s in samples if s.reviewed]

        avg_score = (
            sum(s.review_score for s in reviewed) / len(reviewed)
            if reviewed else 0
        )

        disagreements = [
            s for s in reviewed
            if s.review_score and s.review_score < 3
        ]

        return {
            "agent_id": agent_id,
            "period": "quarterly",
            "total_samples": len(samples),
            "reviewed_samples": len(reviewed),
            "avg_review_score": round(avg_score, 2),
            "disagreement_count": len(disagreements),
            "disagreement_rate": round(len(disagreements) / len(reviewed), 4) if reviewed else 0,
            "disagreements": [
                {
                    "sample_id": s.sample_id,
                    "score": s.review_score,
                    "notes": s.review_notes,
                }
                for s in disagreements
            ],
            "compliance_references": [
                "IN BCB 739 item II — avaliação de risco",
                "IN BCB 739 item VI — fraudes e golpes",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
