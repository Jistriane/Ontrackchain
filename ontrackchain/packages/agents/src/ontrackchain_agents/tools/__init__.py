"""
Tool Schemas — Function calling definitions for Class C agents.

Each tool is defined as a JSON Schema compatible with Anthropic's tool_use format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """Complete tool definition for function calling."""
    name: str
    description: str
    input_schema: dict[str, Any]
    timeout_ms: int = 1000
    retry_count: int = 1
    fallback_result: Any = None


# Canonical chain list — single source of truth for all tool schemas.
SUPPORTED_CHAINS = [
    "ethereum", "polygon", "bsc", "arbitrum", "base",
    "optimism", "bitcoin", "solana", "stellar",
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — Blockchain & On-Chain
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_GET_WALLET_TRANSACTIONS = ToolDefinition(
    name="get_wallet_transactions",
    description="Fetch recent transactions for a wallet address on a specific blockchain.",
    input_schema={
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Wallet address (0x... for EVM, bc1... for Bitcoin)",
            },
            "chain": {
                "type": "string",
                "enum": SUPPORTED_CHAINS,
                "description": "Blockchain network",
            },
            "limit": {
                "type": "integer",
                "default": 100,
                "maximum": 100,
                "description": "Maximum number of transactions to return. MUST NOT exceed 100.",
            },
            "start_block": {
                "type": "integer",
                "description": "Start block number (optional)",
            },
            "end_block": {
                "type": "integer",
                "description": "End block number (optional)",
            },
        },
        "required": ["address", "chain"],
    },
    timeout_ms=1000,
)

TOOL_GET_BRIDGE_EVENTS = ToolDefinition(
    name="get_bridge_events",
    description="Fetch cross-chain bridge events for a transaction or address.",
    input_schema={
        "type": "object",
        "properties": {
            "tx_hash": {
                "type": "string",
                "description": "Transaction hash to trace across chains",
            },
            "address": {
                "type": "string",
                "description": "Address to search bridge events for",
            },
            "source_chain": {
                "type": "string",
                "enum": SUPPORTED_CHAINS,
            },
            "dest_chain": {
                "type": "string",
                "enum": SUPPORTED_CHAINS,
            },
        },
        "required": [],
    },
    timeout_ms=1000,
)

TOOL_CHECK_MIXER_EXPOSURE = ToolDefinition(
    name="check_mixer_exposure",
    description="Check if an address has direct or indirect exposure to known mixers (Tornado Cash, Sinbad, Blender).",
    input_schema={
        "type": "object",
        "properties": {
            "address": {"type": "string"},
            "chain": {"type": "string"},
            "depth": {
                "type": "integer",
                "default": 3,
                "description": "Traversal depth for indirect exposure",
            },
        },
        "required": ["address", "chain"],
    },
    timeout_ms=500,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — Sanctions & Compliance
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_CHECK_SANCTIONS = ToolDefinition(
    name="check_sanctions_list",
    description="Check an entity or wallet against sanctions lists (OFAC SDN, UN CSNU, EU Consolidated, COAF).",
    input_schema={
        "type": "object",
        "properties": {
            "entity_name": {
                "type": "string",
                "description": "Name of the entity to check",
            },
            "wallet_address": {
                "type": "string",
                "description": "Wallet address to check (for wallet-based screening)",
            },
            "document_id": {
                "type": "string",
                "description": "CPF/CNPJ or other document ID",
            },
            "list_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED", "COAF_INTERNAL", "OPENSANCTIONS"],
                },
                "description": "Which lists to check (default: all)",
            },
        },
        "required": [],
    },
    timeout_ms=500,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — Graph & Analysis
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_QUERY_NEO4J = ToolDefinition(
    name="query_neo4j_graph",
    description="Execute a Cypher query against the Neo4j graph database.",
    input_schema={
        "type": "object",
        "properties": {
            "cypher_query": {
                "type": "string",
                "description": "Cypher query to execute",
            },
            "parameters": {
                "type": "object",
                "description": "Query parameters",
            },
            "limit": {
                "type": "integer",
                "default": 100,
                "maximum": 100,
                "description": "Max results to return. MUST NOT exceed 100.",
            },
        },
        "required": ["cypher_query"],
    },
    timeout_ms=500,
)

TOOL_CALCULATE_CLUSTER_SIMILARITY = ToolDefinition(
    name="calculate_cluster_similarity",
    description="Calculate similarity between two or more address clusters.",
    input_schema={
        "type": "object",
        "properties": {
            "addresses": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2,
                "description": "List of addresses to compare",
            },
            "metric": {
                "type": "string",
                "enum": ["jaccard", "cosine", "overlap"],
                "default": "jaccard",
            },
        },
        "required": ["addresses"],
    },
    timeout_ms=500,
)

TOOL_ANALYZE_TX_PATTERN = ToolDefinition(
    name="analyze_transaction_pattern",
    description="Analyze transaction patterns for forensic indicators.",
    input_schema={
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "description": "List of transactions to analyze",
            },
            "indicators": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "structuring",
                        "rapid_movement",
                        "mixer_usage",
                        "chain_hopping",
                        "round_amounts",
                        "peeling_chain",
                        "dormant_activation",
                    ],
                },
                "description": "Specific indicators to check for",
            },
        },
        "required": ["transactions"],
    },
    timeout_ms=500,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — OSINT & External
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_SEARCH_OSINT = ToolDefinition(
    name="search_osint_sources",
    description="Search open source intelligence databases for entity information.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (name, domain, wallet)",
            },
            "entity_type": {
                "type": "string",
                "enum": ["person", "company", "wallet", "domain"],
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["opencorporates", "whois", "blockchain_explorer", "social_media"],
                },
            },
        },
        "required": ["query"],
    },
    timeout_ms=1000,
)


# ═══════════════════════════════════════════════════════════════════════════════
# TOOL REGISTRY — All tools by name
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_REGISTRY: dict[str, ToolDefinition] = {}

TOOL_GET_CASE_EVIDENCE = ToolDefinition(
    name="get_case_evidence",
    description="Retrieve evidence items linked to a compliance case (alerts, transactions, risk scores, regulatory refs).",
    input_schema={
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "Case identifier (e.g., CASE-2026-0001)",
            },
            "evidence_type": {
                "type": "string",
                "enum": ["transaction", "risk_score", "alert", "regulatory_ref", "all"],
                "description": "Type of evidence to retrieve",
            },
        },
        "required": ["case_id"],
    },
)

TOOL_GET_WALLET_CONTEXT = ToolDefinition(
    name="get_wallet_context",
    description="Get enriched context for a wallet address: known owner tags, exchange attribution, risk flags, and historical patterns.",
    input_schema={
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "Wallet address to look up",
            },
            "chain": {
                "type": "string",
                "enum": SUPPORTED_CHAINS,
                "description": "Blockchain network",
            },
        },
        "required": ["address", "chain"],
    },
)


def _register_tool(tool: ToolDefinition) -> None:
    TOOL_REGISTRY[tool.name] = tool

_register_tool(TOOL_GET_WALLET_TRANSACTIONS)
_register_tool(TOOL_GET_BRIDGE_EVENTS)
_register_tool(TOOL_CHECK_MIXER_EXPOSURE)
_register_tool(TOOL_CHECK_SANCTIONS)
_register_tool(TOOL_QUERY_NEO4J)
_register_tool(TOOL_CALCULATE_CLUSTER_SIMILARITY)
_register_tool(TOOL_ANALYZE_TX_PATTERN)
_register_tool(TOOL_SEARCH_OSINT)
_register_tool(TOOL_GET_CASE_EVIDENCE)
_register_tool(TOOL_GET_WALLET_CONTEXT)


def get_tool_schema(tool_name: str) -> dict[str, Any] | None:
    """Get JSON Schema for a tool (Anthropic format)."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return None
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
    }


def get_tools_for_agent(agent_tools: list[str]) -> list[dict[str, Any]]:
    """Get tool schemas for an agent's tool list."""
    schemas = []
    for name in agent_tools:
        schema = get_tool_schema(name)
        if schema:
            schemas.append(schema)
    return schemas


def list_all_tools() -> list[ToolDefinition]:
    """List all registered tools."""
    return list(TOOL_REGISTRY.values())
