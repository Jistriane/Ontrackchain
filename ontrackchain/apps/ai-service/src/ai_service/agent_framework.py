"""
Agent Framework Integration — Bridges ai-service with the new agent configuration system.

This module provides the integration layer between the existing deterministic AI service
and the new LLM-powered agent framework (v4.0).

Usage:
    from ai_service.agent_framework import AgentFramework

    framework = AgentFramework()
    await framework.initialize()

    # For Class A agents (deterministic) — no LLM
    result = await framework.run_agent("AEGIS", input_data)

    # For Class B agents (LLM + RAG)
    result = await framework.run_agent("LEX", input_data)

    # For Class C agents (LLM + Tools)
    result = await framework.run_agent("TRACER", input_data)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from ontrackchain_agents.config import get_agent_config, list_agents, AgentClass
from ontrackchain_agents.config.agent_classes import AgentConfig
from ontrackchain_agents.llm import LLMRouter, LLMResponse, create_llm_router
from ontrackchain_agents.rag import RAGPipeline, RegulatoryCorpus
from ontrackchain_agents.prompts import get_prompt_template, PROMPT_TEMPLATES
from ontrackchain_agents.eval import EvalPipeline, ProductionSample
from ontrackchain_agents.tools import get_tool_schema, TOOL_REGISTRY

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionResult:
    """Result of executing an agent."""
    agent_id: str
    agent_class: str
    output: dict[str, Any]
    llm_response: Optional[LLMResponse] = None
    latency_ms: int = 0
    tokens_used: int = 0
    provider: str = "deterministic"
    cached: bool = False
    error: Optional[str] = None
    evidence_hash: Optional[str] = None


class AgentFramework:
    """
    Unified agent execution framework.

    Routes to the correct execution path based on agent class:
    - Class A: Deterministic rules (no LLM)
    - Class B: LLM + RAG
    - Class C: LLM + Tools
    - Class A+C: Hybrid (deterministic core + LLM on demand)
    """

    def __init__(self) -> None:
        self._router: Optional[LLMRouter] = None
        self._rag: Optional[RAGPipeline] = None
        self._corpus: Optional[RegulatoryCorpus] = None
        self._eval: EvalPipeline = EvalPipeline()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the framework with LLM providers and RAG."""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        groq_key = os.getenv("GROQ_API_KEY", "")

        if anthropic_key and groq_key:
            self._router = create_llm_router(
                anthropic_api_key=anthropic_key,
                groq_api_key=groq_key,
                anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            )
            logger.info("agent_framework.llm_initialized")
        else:
            logger.warning("agent_framework.llm_not_configured", extra={
                "anthropic_set": bool(anthropic_key),
                "groq_set": bool(groq_key),
            })

        # Initialize RAG
        self._corpus = RegulatoryCorpus()
        await self._corpus.initialize()
        self._rag = RAGPipeline(
            corpus=self._corpus,
            embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "voyage-3"),
            top_k=int(os.getenv("RAG_TOP_K", "10")),
            similarity_threshold=float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7")),
        )

        self._initialized = True
        logger.info("agent_framework.initialized", extra={
            "agents_registered": len(list_agents()),
            "llm_available": self._router is not None,
            "rag_available": self._rag is not None,
        })

    async def run_agent(
        self,
        agent_id: str,
        input_data: dict[str, Any],
        case_id: Optional[str] = None,
    ) -> AgentExecutionResult:
        """
        Execute an agent with the appropriate strategy.

        Args:
            agent_id: Agent identifier (e.g., "AEGIS", "LEX", "TRACER")
            input_data: Input data for the agent
            case_id: Optional case ID for evidence trail

        Returns:
            AgentExecutionResult with output and metadata
        """
        config = get_agent_config(agent_id)
        if not config:
            return AgentExecutionResult(
                agent_id=agent_id,
                agent_class="unknown",
                output={"error": f"Agent {agent_id} not found"},
                error=f"Agent {agent_id} not registered",
            )

        start = time.monotonic()

        try:
            if config.agent_class == AgentClass.A:
                result = await self._run_deterministic(config, input_data)
            elif config.agent_class == AgentClass.B:
                result = await self._run_llm_rag(config, input_data)
            elif config.agent_class == AgentClass.C:
                result = await self._run_llm_tools(config, input_data)
            elif config.agent_class == AgentClass.A_C:
                result = await self._run_hybrid(config, input_data)
            else:
                result = AgentExecutionResult(
                    agent_id=agent_id,
                    agent_class=config.agent_class.value,
                    output={"error": "Unknown agent class"},
                    error="Unknown agent class",
                )

            result.latency_ms = int((time.monotonic() - start) * 1000)

            # Sample for production review
            if config.eval.sampling_rate > 0:
                sample = self._eval.sample_production_call(
                    agent_id=agent_id,
                    input_data=input_data,
                    output_data=result.output,
                    latency_ms=result.latency_ms,
                    tokens_used=result.tokens_used,
                    provider=result.provider,
                    sampling_rate=config.eval.sampling_rate,
                )
                if sample:
                    self._persist_sample(sample)

            return result

        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "agent_framework.execution_error",
                extra={"agent_id": agent_id, "error": str(e), "latency_ms": latency_ms},
            )
            return AgentExecutionResult(
                agent_id=agent_id,
                agent_class=config.agent_class.value,
                output={"error": str(e)},
                latency_ms=latency_ms,
                error=str(e),
            )

    async def _run_deterministic(
        self,
        config: AgentConfig,
        input_data: dict[str, Any],
    ) -> AgentExecutionResult:
        """Execute a Class A (deterministic) agent — real logic, no LLM."""
        logger.info(
            "agent_framework.deterministic",
            extra={"agent_id": config.agent_id},
        )

        agent_id = config.agent_id

        if agent_id == "AEGIS":
            output = self._aegis_risk_scoring(input_data)
        elif agent_id == "PREVENTIVE_BLOCK":
            output = self._preventive_block_decision(input_data)
        elif agent_id == "EVIDENCE_LINKER":
            output = self._evidence_linker(input_data)
        elif agent_id == "CONFIDENCE_ENGINE":
            output = self._confidence_engine(input_data)
        else:
            output = {"status": "deterministic_execution", "agent": agent_id}

        return AgentExecutionResult(
            agent_id=agent_id,
            agent_class="A",
            output=output,
            provider="deterministic",
        )

    # ─── AEGIS — Deterministic Risk Scoring ───────────────────────────────
    # Weighted scoring: tx volume, mixer exposure, sanctions, jurisdiction, PEP.
    # Fully auditable — every factor and weight is versioned and logged.
    # Regulatory basis: BCB 520 Art. 43 §2° VI, IN BCB 739 Art. 1° VII

    def _aegis_risk_scoring(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deterministic risk scoring engine. Returns score 0-100 with breakdown."""
        tx_count = data.get("tx_count", 0)
        mixer_txs = data.get("mixer_transactions", 0)
        sanctions_matches = data.get("sanctions_matches", 0)
        high_risk_jurisdiction = data.get("high_risk_jurisdiction", False)
        pep_flag = data.get("pep_flag", False)

        factors = []
        weighted_score = 0.0
        total_weight = 0.0

        # Factor 1: Transaction volume (weight: 0.15)
        if tx_count > 0:
            volume_normalized = min(1.0, tx_count / 500)
            impact = "high" if tx_count > 200 else "medium" if tx_count > 50 else "low"
            factors.append({
                "factor": "tx_volume",
                "weight": 0.15,
                "input_value": tx_count,
                "normalized": round(volume_normalized, 3),
                "impact": impact,
            })
            weighted_score += 0.15 * volume_normalized
            total_weight += 0.15

        # Factor 2: Mixer exposure (weight: 0.30)
        if mixer_txs > 0:
            mixer_normalized = min(1.0, mixer_txs / 10)
            factors.append({
                "factor": "mixer_exposure",
                "weight": 0.30,
                "input_value": mixer_txs,
                "normalized": round(mixer_normalized, 3),
                "impact": "high",
            })
            weighted_score += 0.30 * mixer_normalized
            total_weight += 0.30

        # Factor 3: Sanctions match (weight: 0.25)
        if sanctions_matches > 0:
            sanctions_normalized = min(1.0, sanctions_matches / 3)
            factors.append({
                "factor": "sanctions_match",
                "weight": 0.25,
                "input_value": sanctions_matches,
                "normalized": round(sanctions_normalized, 3),
                "impact": "critical",
            })
            weighted_score += 0.25 * sanctions_normalized
            total_weight += 0.25

        # Factor 4: High-risk jurisdiction (weight: 0.15)
        if high_risk_jurisdiction:
            factors.append({
                "factor": "high_risk_jurisdiction",
                "weight": 0.15,
                "input_value": True,
                "normalized": 1.0,
                "impact": "high",
            })
            weighted_score += 0.15
            total_weight += 0.15

        # Factor 5: PEP flag (weight: 0.15)
        if pep_flag:
            factors.append({
                "factor": "pep_flag",
                "weight": 0.15,
                "input_value": True,
                "normalized": 1.0,
                "impact": "high",
            })
            weighted_score += 0.15
            total_weight += 0.15

        # Compute final score
        if total_weight > 0:
            score = round((weighted_score / total_weight) * 100, 1)
        else:
            score = 0.0

        # Risk level classification
        if score >= 70:
            level = "CRITICAL"
            recommendation = "BLOQUEAR — Bloqueio imediato e reporte ao COAF conforme Res. 520/2022 Art. 20"
        elif score >= 50:
            level = "HIGH"
            recommendation = "INVESTIGAR — Investigação reforçada obrigatória conforme IN BCB 739"
        elif score >= 30:
            level = "MEDIUM"
            recommendation = "MONITORAR — Monitoramento intensificado por 30 dias"
        else:
            level = "LOW"
            recommendation = "LIMPO — Monitoramento de rotina"

        return {
            "score": score,
            "level": level,
            "factors": factors,
            "recommendation": recommendation,
            "classification": "FATO" if score >= 70 else "INFERÊNCIA",
            "regulatory_basis": ["BCB 520 Art. 43 §2° VI", "IN BCB 739 Art. 1° VII"],
        }

    # ─── PREVENTIVE BLOCK — Priority-Based Block Decision ─────────────────
    # Deterministic block/allow based on risk level and factor types.
    # Always produces evidence trail regardless of decision.

    def _preventive_block_decision(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deterministic block decision. Returns ALLOW/BLOCK with reason."""
        risk_score = data.get("risk_score", 0)
        risk_level = data.get("risk_level", "LOW")
        sanctions_hit = data.get("sanctions_match", False)
        pep_flag = data.get("pep_flag", False)
        address = data.get("address", "")

        # Decision matrix
        if sanctions_hit or risk_score >= 80 or risk_level == "CRITICAL":
            decision = "BLOCK"
            reason = "Sanctions match or critical risk level"
            regulatory_ref = "BCB 520 Art. 43 §2° V — obrigação de bloqueio"
        elif risk_score >= 60 or pep_flag:
            decision = "BLOCK"
            reason = "High risk score or PEP association"
            regulatory_ref = "BCB 520 Art. 43 §2° VI — due diligence reforçada"
        elif risk_score >= 40:
            decision = "HOLD"
            reason = "Medium risk — requires human review before proceeding"
            regulatory_ref = "IN BCB 739 Art. 10 — avaliação contínua"
        else:
            decision = "ALLOW"
            reason = "Risk below threshold — standard monitoring"
            regulatory_ref = "BCB 520 Art. 11 — monitoramento contínuo"

        # Compute evidence hash for chain integrity
        evidence_data = json.dumps({
            "address": address,
            "decision": decision,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "sanctions_hit": sanctions_hit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()

        return {
            "decision": decision,
            "reason": reason,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "regulatory_ref": regulatory_ref,
            "evidence_hash": evidence_hash,
            "requires_human_review": decision == "HOLD",
        }

    # ─── EVIDENCE LINKER — Hash ↔ Evidence Binding ────────────────────────
    # Deterministic hash binding: input hash → evidence hash → chain.
    # 100% reproducible — same input always produces same output.

    def _evidence_linker(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deterministic evidence linking. Produces chain hash."""
        event_type = data.get("event_type", "UNKNOWN")
        event_payload = data.get("event_payload", {})
        case_id = data.get("case_id", "")
        actor_agent_id = data.get("actor_agent_id", "")
        timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Canonical JSON (sorted keys, deterministic)
        canonical = json.dumps({
            "event_type": event_type,
            "event_payload": event_payload,
            "case_id": case_id,
            "actor_agent_id": actor_agent_id,
            "timestamp": timestamp,
        }, sort_keys=True, ensure_ascii=False)

        event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return {
            "event_hash": event_hash,
            "event_type": event_type,
            "case_id": case_id,
            "chain_position": "pending_commit",
            "regulatory_basis": ["BCB Circular 3.978", "Res. 520/2022"],
        }

    # ─── CONFIDENCE ENGINE — Deterministic Confidence Scoring ─────────────
    # Statistical confidence based on evidence type weights.
    # Not probabilistic — deterministic formula applied to evidence counts.

    def _confidence_engine(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deterministic confidence scoring from evidence factors."""
        factors = data.get("factors", [])

        if not factors:
            factors = [
                {"type": "FATO", "count": 0, "reliability": 0.95},
                {"type": "INFERÊNCIA", "count": 0, "reliability": 0.72},
                {"type": "HIPÓTESE", "count": 0, "reliability": 0.45},
            ]

        # Reliability weights by evidence type
        reliability_map = {
            "FATO": 0.95,
            "INFERÊNCIA": 0.72,
            "HIPÓTESE": 0.45,
            "RECOMENDAÇÃO": 0.80,
        }

        total_count = 0
        weighted_sum = 0.0

        for f in factors:
            etype = f.get("type", "INFERÊNCIA")
            count = f.get("count", 1)
            reliability = f.get("reliability", reliability_map.get(etype, 0.5))
            total_count += count
            weighted_sum += count * reliability

        if total_count > 0:
            overall = round(weighted_sum / total_count, 4)
        else:
            overall = 0.0

        # Classify confidence level
        if overall >= 0.85:
            confidence_level = "ALTA"
        elif overall >= 0.60:
            confidence_level = "MEDIA"
        else:
            confidence_level = "BAIXA"

        # Uncertainty factors
        uncertainty = []
        if overall < 0.7:
            uncertainty.append({
                "factor": "Evidência insuficiente",
                "impact": "high",
                "detail": f"Apenas {total_count} evidências coletadas",
            })
        hip_count = sum(1 for f in factors if f.get("type") == "HIPÓTESE")
        if hip_count > 0:
            uncertainty.append({
                "factor": "Hipóteses não confirmadas",
                "impact": "medium",
                "detail": f"{hip_count} hipótese(s) aguardando verificação",
            })

        return {
            "overall": overall,
            "confidence_level": confidence_level,
            "total_evidence_count": total_count,
            "factors": factors,
            "uncertainty": uncertainty,
            "classification": "FATO" if overall >= 0.85 else "INFERÊNCIA",
            "regulatory_basis": ["IN BCB 739 item II", "IN BCB 739 item VI"],
        }

    async def _run_llm_rag(
        self,
        config: AgentConfig,
        input_data: dict[str, Any],
    ) -> AgentExecutionResult:
        """Execute a Class B (LLM + RAG) agent."""
        if not self._router:
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="B",
                output={"error": "LLM not configured"},
                error="LLM router not initialized",
            )

        # Get prompt template
        template = get_prompt_template(config.agent_id)
        if not template:
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="B",
                output={"error": "Prompt template not found"},
                error=f"No prompt template for {config.agent_id}",
            )

        # Retrieve regulatory context via RAG
        rag_context = ""
        if config.rag and config.rag.enabled and self._rag:
            query = input_data.get("question", input_data.get("context", ""))
            rag_response = await self._rag.retrieve(
                query=query,
                corpus_ids=config.rag.corpus_ids,
                temporal_filter=config.rag.temporal_filter,
            )
            rag_context = self._rag.format_context(rag_response.results)

        # Build messages
        system_prompt = template.system_prompt.format(
            regulatory_context=rag_context,
            profile_instructions="",
        )

        # Safe format: provide defaults for missing template vars
        safe_input = {k: str(v) if v is not None else "" for k, v in input_data.items()}
        try:
            user_prompt = template.user_prompt_template.format(**safe_input)
        except KeyError:
            class DefaultDict(dict):
                def __missing__(self, key):
                    return ""
            user_prompt = template.user_prompt_template.format_map(DefaultDict(safe_input))

        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"},
        ]

        # Call LLM
        llm_response = await self._router.complete(
            messages=messages,
            model=config.llm.model,
            fallback_model=config.llm.fallback_model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            timeout_ms=config.llm.timeout_ms,
            fallback_enabled=config.llm.fallback_enabled,
        )

        if llm_response.error:
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="B",
                output={"error": llm_response.error},
                llm_response=llm_response,
                provider=llm_response.provider,
                error=llm_response.error,
            )

        # Parse response
        try:
            output = json.loads(llm_response.content) if llm_response.content else {}
        except json.JSONDecodeError:
            output = {"narrative": llm_response.content}

        return AgentExecutionResult(
            agent_id=config.agent_id,
            agent_class="B",
            output=output,
            llm_response=llm_response,
            tokens_used=llm_response.input_tokens + llm_response.output_tokens,
            provider=llm_response.provider,
        )

    async def _run_llm_tools(
        self,
        config: AgentConfig,
        input_data: dict[str, Any],
    ) -> AgentExecutionResult:
        """Execute a Class C (LLM + Tools) agent."""
        if not self._router:
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="C",
                output={"error": "LLM not configured"},
                error="LLM router not initialized",
            )

        # Get prompt template
        template = get_prompt_template(config.agent_id)

        # Build tool schemas
        tool_schemas = [
            get_tool_schema(tool.name)
            for tool in config.tools
            if get_tool_schema(tool.name)
        ]

        # Build messages
        system_prompt = template.system_prompt if template else f"You are {config.name}."
        tool_descriptions = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in tool_schemas
        ])
        system_prompt = system_prompt.format(
            tool_schemas=tool_descriptions,
        )

        # Safe format: provide defaults for missing template vars
        safe_input_c = {k: str(v) if v is not None else "" for k, v in input_data.items()}
        try:
            user_prompt = template.user_prompt_template.format(**safe_input_c) if template else json.dumps(input_data)
        except KeyError:
            class _DefaultDict(dict):
                def __missing__(self, key):
                    return ""
            user_prompt = template.user_prompt_template.format_map(_DefaultDict(safe_input_c)) if template else json.dumps(input_data)

        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"},
        ]

        # Call LLM with tools
        llm_response = await self._router.complete(
            messages=messages,
            model=config.llm.model,
            fallback_model=config.llm.fallback_model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            tools=tool_schemas if tool_schemas else None,
            timeout_ms=config.llm.timeout_ms,
            fallback_enabled=config.llm.fallback_enabled,
        )

        if llm_response.error:
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="C",
                output={"error": llm_response.error},
                llm_response=llm_response,
                provider=llm_response.provider,
                error=llm_response.error,
            )

        # Handle tool calls
        tool_results = []
        if llm_response.tool_calls:
            for tool_call in llm_response.tool_calls:
                tool_results.append({
                    "tool": tool_call["name"],
                    "arguments": tool_call["arguments"],
                    "status": "invoked",
                })

        # Parse response
        try:
            output = json.loads(llm_response.content) if llm_response.content else {}
        except json.JSONDecodeError:
            output = {"summary": llm_response.content}

        output["tool_calls"] = tool_results

        return AgentExecutionResult(
            agent_id=config.agent_id,
            agent_class="C",
            output=output,
            llm_response=llm_response,
            tokens_used=llm_response.input_tokens + llm_response.output_tokens,
            provider=llm_response.provider,
        )

    async def _run_hybrid(
        self,
        config: AgentConfig,
        input_data: dict[str, Any],
    ) -> AgentExecutionResult:
        """Execute a Class A+C (hybrid) agent."""
        # Hybrid agents run deterministic first, then LLM if needed
        deterministic_result = await self._run_deterministic(config, input_data)

        # Check if LLM is needed (e.g., for complex cases)
        needs_llm = input_data.get("complex", False)

        if needs_llm and self._router and config.llm:
            llm_result = await self._run_llm_tools(config, input_data)
            return AgentExecutionResult(
                agent_id=config.agent_id,
                agent_class="A+C",
                output={
                    "deterministic": deterministic_result.output,
                    "llm_enhanced": llm_result.output,
                },
                llm_response=llm_result.llm_response,
                tokens_used=llm_result.tokens_used,
                provider=llm_result.provider,
            )

        return deterministic_result

    def _persist_sample(self, sample: ProductionSample) -> None:
        """Persist a production sample to DB."""
        if not self._corpus or not self._corpus._pool:
            return
        try:
            sample_uuid = str(uuid.uuid4())
            with self._corpus._pool.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO agent_production_samples
                        (id, agent_id, input_data, output_data, latency_ms,
                         tokens_used, provider, sampled_at)
                    VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s)
                    """,
                    (
                        sample_uuid, sample.agent_id,
                        json.dumps(sample.input_data), json.dumps(sample.output_data),
                        sample.latency_ms, sample.tokens_used, sample.provider,
                        sample.sampled_at,
                    ),
                )
            self._corpus._pool.commit()
            logger.info("agent_framework.sample_persisted", extra={"sample_id": sample_uuid})
        except Exception as e:
            logger.warning("agent_framework.sample_persist_failed", extra={"error": str(e)})

    # ─── Status & Health ───────────────────────────────────────────────────

    async def health_check(self) -> dict[str, Any]:
        """Check framework health."""
        llm_health = {}
        if self._router:
            llm_health = await self._router.health_check()

        return {
            "initialized": self._initialized,
            "agents_registered": len(list_agents()),
            "llm_health": llm_health,
            "rag_available": self._rag is not None,
            "eval_samples": len(self._eval._production_samples),
        }

    def get_agent_info(self, agent_id: str) -> Optional[dict[str, Any]]:
        """Get detailed info about an agent."""
        config = get_agent_config(agent_id)
        if not config:
            return None

        return {
            "agent_id": config.agent_id,
            "name": config.name,
            "agent_class": config.agent_class.value,
            "domain": config.domain,
            "description": config.description,
            "version": config.version,
            "requires_llm": config.llm is not None,
            "requires_rag": bool(config.rag and config.rag.enabled),
            "tool_count": len(config.tools),
            "target_latency_p95_ms": config.target_latency_p95_ms,
            "requires_human_review": config.requires_human_review,
            "audit_level": config.audit_level,
        }

    def list_all_agents(self) -> list[dict[str, Any]]:
        """List all agents with their configurations."""
        return [
            self.get_agent_info(config.agent_id)
            for config in list_agents()
            if self.get_agent_info(config.agent_id)
        ]
