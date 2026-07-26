"""
Agent Configuration System — OnTrackChain v4.0

Architecture:
  Class A (Deterministic): Rules, math, thresholds — no LLM
  Class B (RAG): LLM with regulatory RAG — reasoning over law + case context
  Class C (Tool-use): LLM with function calling — external data + actions

Principle: Not every agent needs an LLM. Every agent must be auditable.
"""

from ontrackchain_agents.config.agent_classes import AgentClass, AgentConfig, AGENT_REGISTRY
from ontrackchain_agents.config.registry import get_agent_config, list_agents, list_agents_by_class

__all__ = [
    "AgentClass",
    "AgentConfig",
    "AGENT_REGISTRY",
    "get_agent_config",
    "list_agents",
    "list_agents_by_class",
]
