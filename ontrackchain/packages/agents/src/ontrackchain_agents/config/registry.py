"""
Agent Registry — Lookup and query functions.
"""

from __future__ import annotations

from typing import Optional

from ontrackchain_agents.config.agent_classes import AgentClass, AgentConfig, AGENT_REGISTRY


def get_agent_config(agent_id: str) -> Optional[AgentConfig]:
    """Get configuration for a specific agent."""
    return AGENT_REGISTRY.get(agent_id.upper())


def list_agents() -> list[AgentConfig]:
    """List all registered agents."""
    return list(AGENT_REGISTRY.values())


def list_agents_by_class(agent_class: AgentClass) -> list[AgentConfig]:
    """List agents filtered by class."""
    return [a for a in AGENT_REGISTRY.values() if a.agent_class == agent_class]


def list_agents_by_domain(domain: str) -> list[AgentConfig]:
    """List agents filtered by domain."""
    return [a for a in AGENT_REGISTRY.values() if a.domain == domain]


def requires_llm(agent_id: str) -> bool:
    """Check if an agent requires LLM integration."""
    config = get_agent_config(agent_id)
    if not config:
        return False
    return config.agent_class in (AgentClass.B, AgentClass.C, AgentClass.A_C)


def requires_rag(agent_id: str) -> bool:
    """Check if an agent requires RAG pipeline."""
    config = get_agent_config(agent_id)
    if not config or not config.rag:
        return False
    return config.rag.enabled


def requires_tools(agent_id: str) -> bool:
    """Check if an agent requires function calling tools."""
    config = get_agent_config(agent_id)
    if not config:
        return False
    return len(config.tools) > 0


def get_all_corpus_ids() -> list[str]:
    """Get all unique corpus IDs across all agents."""
    corpus_ids = set()
    for config in AGENT_REGISTRY.values():
        if config.rag and config.rag.corpus_ids:
            corpus_ids.update(config.rag.corpus_ids)
    return sorted(corpus_ids)
