"""
Agent Class Definitions — Three-tier architecture.

Class A (Deterministic):
  - Rules, math, thresholds
  - No LLM — fully auditable in court
  - Examples: Risk scoring, PreventiveBlock, EvidenceLinker

Class B (LLM + Regulatory RAG):
  - Needs to reason about law + case context
  - Claude Sonnet 4.5 + RAG pipeline
  - Examples: Regulatory/LEX, Synthesis, Reporter/ESCREVA

Class C (LLM + Tools / Function Calling):
  - Needs to fetch external data and act
  - Claude Haiku 4.5 with tool schemas
  - Examples: Tracer/TRACER, OSINT, Cluster, HERMES
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class AgentClass(enum.Enum):
    """Three classes of agents."""
    A = "deterministic"      # No LLM — rules, math, thresholds
    B = "llm_rag"           # LLM + Regulatory RAG
    C = "llm_tools"         # LLM + Function Calling
    A_C = "hybrid_ac"       # Deterministic core + LLM on demand (Class A+C)


@dataclass
class LLMConfig:
    """LLM provider configuration for an agent."""
    provider: str = "anthropic"          # anthropic | groq
    model: str = "claude-sonnet-4-5"    # Model identifier
    max_tokens: int = 4096
    temperature: float = 0.1            # Low for regulatory precision
    timeout_ms: int = 3500              # Hard timeout
    fallback_provider: str = "groq"     # Fallback provider
    fallback_model: str = "llama-3.3-70b"  # Fallback model
    fallback_enabled: bool = True
    cache_results: bool = True          # Redis cache for identical queries
    cache_ttl_seconds: int = 3600


@dataclass
class RAGConfig:
    """RAG pipeline configuration."""
    enabled: bool = False
    vector_store: str = "pgvector"      # pgvector | qdrant
    embedding_model: str = "voyage-3"
    embedding_dimensions: int = 1024
    top_k: int = 10                     # Number of chunks to retrieve
    similarity_threshold: float = 0.7
    rerank_enabled: bool = True
    corpus_ids: list[str] = field(default_factory=list)  # Regulatory corpus IDs
    temporal_filter: bool = True        # Filter by regulation validity date


@dataclass
class EvalConfig:
    """Evaluation pipeline configuration."""
    golden_dataset_size: int = 100
    sampling_rate: float = 0.05        # 5% of production calls sampled
    review_required: bool = True       # Human review for compliance
    regression_blocking: bool = True   # Block deploy on regression
    target_precision: float = 0.90
    target_recall: float = 0.85
    target_tool_invocation_accuracy: float = 0.98
    target_latency_p95_ms: int = 450


@dataclass
class ToolSchema:
    """Function calling schema for Class C agents."""
    name: str
    description: str
    parameters: dict[str, Any]         # JSON Schema
    timeout_ms: int = 1000
    required: bool = True
    fallback: Optional[str] = None      # Fallback if tool fails


@dataclass
class AgentConfig:
    """Complete configuration for a single agent."""
    # Identity
    agent_id: str                       # Unique identifier
    name: str                           # Human-readable name
    agent_class: AgentClass             # A, B, C, or A+C
    domain: str                         # Functional domain

    # Description
    description: str = ""
    regulatory_basis: list[str] = field(default_factory=list)

    # LLM Configuration (only for Class B and C)
    llm: Optional[LLMConfig] = None

    # RAG Configuration (only for Class B)
    rag: Optional[RAGConfig] = None

    # Tool Schemas (only for Class C)
    tools: list[ToolSchema] = field(default_factory=list)

    # Evaluation
    eval: EvalConfig = field(default_factory=EvalConfig)

    # Performance Targets
    target_latency_p95_ms: int = 450
    timeout_ms: int = 3500

    # Governance
    version: str = "1.0.0"
    requires_human_review: bool = False
    audit_level: str = "full"           # full | minimal | none

    # Data Governance
    zero_retention: bool = True         # No data retained by LLM provider
    anonymize_inputs: bool = True       # Anonymize before sending to LLM


# ─── AGENT REGISTRY ───────────────────────────────────────────────────────────
# Complete configuration for all production agents

AGENT_REGISTRY: dict[str, AgentConfig] = {}

def _register(config: AgentConfig) -> None:
    AGENT_REGISTRY[config.agent_id] = config


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS A — DETERMINISTIC AGENTS (No LLM)
# ═══════════════════════════════════════════════════════════════════════════════

_register(AgentConfig(
    agent_id="AEGIS",
    name="AEGIS Risk Scoring Engine",
    agent_class=AgentClass.A,
    domain="risk_scoring",
    description="Deterministic risk scoring — auditável em perícia. Scoring baseado em regras versionadas.",
    regulatory_basis=[
        "BCB 520 Art. 43 §2° VI",
        "BCB 520 Art. 90 III",
        "IN BCB 739 Art. 1° VII",
    ],
    target_latency_p95_ms=50,
    eval=EvalConfig(target_precision=0.95, target_recall=0.90),
    requires_human_review=False,
    audit_level="full",
))

_register(AgentConfig(
    agent_id="PREVENTIVE_BLOCK",
    name="PreventiveBlockAgent",
    agent_class=AgentClass.A,
    domain="blocking",
    description="Stage 2 blocking — priority-based decision logic with evidence trail.",
    regulatory_basis=[
        "BCB 520 Art. 43 §2° V-VI",
        "BCB 520 Art. 90 III",
        "Lei 13.810/2019",
        "IN BCB 739 Art. 1° VII",
    ],
    target_latency_p95_ms=500,
    eval=EvalConfig(target_precision=0.95),
    requires_human_review=False,
    audit_level="full",
))

_register(AgentConfig(
    agent_id="EVIDENCE_LINKER",
    name="EvidenceLinker (THEMIS)",
    agent_class=AgentClass.A,
    domain="evidence",
    description="Vínculo hash ↔ evidência — determinístico. 100% reproduzível.",
    regulatory_basis=[
        "BCB Circular 3.978",
        "Res. 520/2022",
        "ARQUIVO protocol",
    ],
    target_latency_p95_ms=100,
    eval=EvalConfig(target_precision=1.0),
    requires_human_review=False,
    audit_level="full",
))

_register(AgentConfig(
    agent_id="CONFIDENCE_ENGINE",
    name="Confidence Engine (XAI)",
    agent_class=AgentClass.A,
    domain="xai",
    description="Deterministic confidence scoring — statistical, not probabilistic.",
    regulatory_basis=[
        "IN BCB 739 item II",
        "IN BCB 739 item VI",
    ],
    target_latency_p95_ms=100,
    eval=EvalConfig(target_precision=0.95),
    requires_human_review=False,
    audit_level="full",
))


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS B — LLM + REGULATORY RAG AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

_register(AgentConfig(
    agent_id="ARGOS",
    name="ARGOS Triage Agent",
    agent_class=AgentClass.B,
    domain="triage",
    description="Classificação complexa de intenção multi-etapa.",
    regulatory_basis=[
        "BCB 520 Art. 43",
        "BCB 521 Art. 76-A",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        temperature=0.1,
        timeout_ms=3500,
    ),
    rag=RAGConfig(
        enabled=True,
        top_k=10,
        corpus_ids=["bcb_519", "bcb_520", "bcb_521", "bcb_552", "bcb_553", "bcb_580",
                     "in_bcb_704", "in_bcb_739", "lei_14478", "lei_9613", "lei_13810",
                     "fatf_r15", "fatf_r16", "fatf_r25", "cvm_245"],
    ),
    target_latency_p95_ms=3500,
    eval=EvalConfig(
        target_precision=0.90,
        target_recall=0.85,
        golden_dataset_size=100,
        sampling_rate=0.10,
    ),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="LEX",
    name="Regulatory/LEX Agent",
    agent_class=AgentClass.B,
    domain="regulatory_interpretation",
    description="Interpretação normativa exige base atualizada. RAG jurídico + templates.",
    regulatory_basis=[
        "Todas normas BCB sobre ativos virtuais",
        "FATF Recommendations 15, 16, 25",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        temperature=0.05,   # Ultra-low for legal precision
        timeout_ms=5000,
    ),
    rag=RAGConfig(
        enabled=True,
        top_k=15,           # More chunks for comprehensive legal analysis
        corpus_ids=["bcb_519", "bcb_520", "bcb_521", "bcb_552", "bcb_553", "bcb_580",
                     "in_bcb_704", "in_bcb_739", "lei_14478", "lei_9613", "lei_13810",
                     "fatf_r15", "fatf_r16", "fatf_r25", "cvm_245"],
        similarity_threshold=0.75,  # Higher threshold for legal accuracy
    ),
    target_latency_p95_ms=5000,
    eval=EvalConfig(
        target_precision=0.95,
        target_recall=0.90,
        golden_dataset_size=150,
        sampling_rate=0.10,
    ),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="SYNTHESIS",
    name="Synthesis Agent",
    agent_class=AgentClass.B,
    domain="synthesis",
    description="Consolidação de múltiplas fontes conflitantes.",
    regulatory_basis=[
        "BCB Circular 3.978",
        "Res. 520/2022",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        temperature=0.1,
    ),
    rag=RAGConfig(enabled=False),
    target_latency_p95_ms=3500,
    eval=EvalConfig(target_precision=0.90),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="ESCREVA",
    name="Reporter/ESCREVA Agent",
    agent_class=AgentClass.B,
    domain="reporting",
    description="Geração de relatório jurídico/técnico com linguagem formal.",
    regulatory_basis=[
        "Lei 9.613/98",
        "Res. 520/2022",
        "Res. 739/2023",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        temperature=0.1,
        timeout_ms=5000,
    ),
    rag=RAGConfig(
        enabled=True,
        top_k=10,
        corpus_ids=["bcb_519", "bcb_520", "bcb_521", "in_bcb_739", "lei_9613"],
    ),
    target_latency_p95_ms=5000,
    eval=EvalConfig(
        target_precision=0.95,
        golden_dataset_size=50,
    ),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="GRAPH_NARRATOR",
    name="GraphNarrator Engine",
    agent_class=AgentClass.B,
    domain="narration",
    description="Narrativa adaptada por perfil (técnico/jurídico/executivo).",
    regulatory_basis=[
        "BCB Circular 3.978",
        "Res. 520/2022",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        temperature=0.2,
    ),
    rag=RAGConfig(enabled=False),
    target_latency_p95_ms=3500,
    eval=EvalConfig(
        target_precision=0.90,
        sampling_rate=0.10,
    ),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="SIMULATOR",
    name="Simulator Agent",
    agent_class=AgentClass.B,
    domain="simulation",
    description="Simulação de cenários complexos.",
    regulatory_basis=[],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        temperature=0.3,   # Slightly higher for scenario diversity
    ),
    rag=RAGConfig(enabled=False),
    target_latency_p95_ms=5000,
    eval=EvalConfig(target_precision=0.85),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="ATLAS",
    name="ATLAS Digital Twin",
    agent_class=AgentClass.B,
    domain="digital_twin",
    description="Simulação institucional complexa.",
    regulatory_basis=[
        "BCB 520/521",
        "IN BCB 739",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        temperature=0.2,
        timeout_ms=5000,
    ),
    rag=RAGConfig(
        enabled=True,
        top_k=10,
        corpus_ids=["bcb_520", "bcb_521", "in_bcb_739"],
    ),
    target_latency_p95_ms=5000,
    eval=EvalConfig(target_precision=0.90),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="CASE_REVIEW",
    name="CaseReview (THEMIS)",
    agent_class=AgentClass.B,
    domain="case_review",
    description="Revisão final antes de human-in-the-loop.",
    regulatory_basis=[
        "BCB Circular 3.978",
        "Res. 520/2022",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        temperature=0.05,
    ),
    rag=RAGConfig(enabled=False),
    target_latency_p95_ms=3500,
    eval=EvalConfig(target_precision=0.95),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS C — LLM + TOOLS (FUNCTION CALLING) AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

_register(AgentConfig(
    agent_id="TRACER",
    name="Tracer/TRACER Agent",
    agent_class=AgentClass.C,
    domain="on_chain_tracing",
    description="Coleta on-chain — narrativa jurídica/técnica.",
    regulatory_basis=[
        "BCB 520 Art. 43",
        "Lei 9.613/98",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="get_wallet_transactions",
            description="Fetch recent transactions for a wallet address",
            parameters={
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "Wallet address"},
                    "chain": {"type": "string", "enum": ["ethereum", "bitcoin", "polygon", "bsc"]},
                    "limit": {"type": "integer", "default": 100, "maximum": 1000},
                },
                "required": ["address", "chain"],
            },
            timeout_ms=1000,
        ),
        ToolSchema(
            name="get_bridge_events",
            description="Fetch cross-chain bridge events for a transaction",
            parameters={
                "type": "object",
                "properties": {
                    "tx_hash": {"type": "string"},
                    "source_chain": {"type": "string"},
                    "dest_chain": {"type": "string"},
                },
                "required": ["tx_hash"],
            },
            timeout_ms=1000,
        ),
        ToolSchema(
            name="check_mixer_exposure",
            description="Check if address has direct or indirect mixer exposure",
            parameters={
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "chain": {"type": "string"},
                    "depth": {"type": "integer", "default": 3},
                },
                "required": ["address", "chain"],
            },
            timeout_ms=500,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(
        target_tool_invocation_accuracy=0.98,
        target_latency_p95_ms=450,
    ),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="HERMES",
    name="HERMES Counterparty Agent",
    agent_class=AgentClass.C,
    domain="counterparty",
    description="Onboarding com regras + IA leve. KYC/KYB + sanctions + PEP.",
    regulatory_basis=[
        "BCB 520 Art. 58",
        "BCB 521 Art. 76-A",
        "IN BCB 739 Art. 1° III",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="check_sanctions_list",
            description="Check entity against sanctions lists",
            parameters={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string"},
                    "document_id": {"type": "string"},
                    "list_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["OFAC_SDN", "UN_CSNU", "EU_CONSOLIDATED", "COAF_INTERNAL"]},
                    },
                },
                "required": ["entity_name"],
            },
            timeout_ms=500,
        ),
        ToolSchema(
            name="search_osint_sources",
            description="Search open source intelligence for entity information",
            parameters={
                "type": "object",
                "properties": {
                    "entity_name": {"type": "string"},
                    "document_id": {"type": "string"},
                    "jurisdiction": {"type": "string"},
                },
                "required": ["entity_name"],
            },
            timeout_ms=1000,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(target_tool_invocation_accuracy=0.98),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="CLUSTER",
    name="Cluster Agent",
    agent_class=AgentClass.C,
    domain="graph_analysis",
    description="Consultas Cypher estruturadas — Graph Intelligence.",
    regulatory_basis=[],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="query_neo4j_graph",
            description="Execute Cypher query against Neo4j graph database",
            parameters={
                "type": "object",
                "properties": {
                    "cypher_query": {"type": "string", "description": "Cypher query to execute"},
                    "parameters": {"type": "object", "description": "Query parameters"},
                    "limit": {"type": "integer", "default": 100},
                },
                "required": ["cypher_query"],
            },
            timeout_ms=500,
        ),
        ToolSchema(
            name="calculate_cluster_similarity",
            description="Calculate similarity between address clusters",
            parameters={
                "type": "object",
                "properties": {
                    "addresses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                    },
                    "metric": {"type": "string", "enum": ["jaccard", "cosine", "overlap"], "default": "jaccard"},
                },
                "required": ["addresses"],
            },
            timeout_ms=500,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(target_tool_invocation_accuracy=0.98),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="OSINT",
    name="OSINT Agent",
    agent_class=AgentClass.C,
    domain="open_source_intelligence",
    description="Busca rápida, baixa criticidade. Coleta de dados públicos.",
    regulatory_basis=[],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="search_osint_sources",
            description="Search open source intelligence databases",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "entity_type": {"type": "string", "enum": ["person", "company", "wallet", "domain"]},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["opencorporates", "linkedin", "whois", "blockchain_explorer"]},
                    },
                },
                "required": ["query"],
            },
            timeout_ms=1000,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(target_tool_invocation_accuracy=0.95),
    requires_human_review=False,
    audit_level="minimal",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="FORENSIC_MIND",
    name="FORENSIC MIND Agent",
    agent_class=AgentClass.C,
    domain="forensic_analysis",
    description="Detecção de padrão com contexto. Análise forense de transações.",
    regulatory_basis=[
        "Lei 9.613/98",
        "BCB 520 Art. 43",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="get_wallet_transactions",
            description="Fetch transactions for forensic analysis",
            parameters={
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "chain": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["address", "chain"],
            },
            timeout_ms=1000,
        ),
        ToolSchema(
            name="analyze_transaction_pattern",
            description="Analyze transaction patterns for forensic indicators",
            parameters={
                "type": "object",
                "properties": {
                    "transactions": {"type": "array"},
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["structuring", "rapid_movement", "mixer_usage", "chain_hopping", "round_amounts"]},
                    },
                },
                "required": ["transactions"],
            },
            timeout_ms=500,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(target_tool_invocation_accuracy=0.98),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))


# ═══════════════════════════════════════════════════════════════════════════════
# CLASS A+C — HYBRID AGENTS (Deterministic core + LLM on demand)
# ═══════════════════════════════════════════════════════════════════════════════

_register(AgentConfig(
    agent_id="SENTINEL",
    name="SENTINEL Scheduler",
    agent_class=AgentClass.A_C,
    domain="scheduling",
    description="Scheduler determinístico + IA sob demanda. Watchlist scanning.",
    regulatory_basis=[
        "BCB 520 Art. 43",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=1024,
        temperature=0.1,
        timeout_ms=450,
    ),
    rag=RAGConfig(enabled=False),
    target_latency_p95_ms=450,
    eval=EvalConfig(
        target_precision=0.90,
        sampling_rate=0.05,
    ),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="ORION_OPS",
    name="ORION Ops Agent",
    agent_class=AgentClass.A_C,
    domain="operations",
    description="Monitoramento operacional pré/pós execução. Regras + Haiku.",
    regulatory_basis=[
        "BCB 520/521",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=1024,
        temperature=0.1,
        timeout_ms=450,
    ),
    target_latency_p95_ms=450,
    eval=EvalConfig(target_precision=0.90),
    requires_human_review=False,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))


# ═══════════════════════════════════════════════════════════════════════════════
# NEW v4.0 AGENTS (Proposed)
# ═══════════════════════════════════════════════════════════════════════════════

_register(AgentConfig(
    agent_id="CASE_BUILDER",
    name="CaseBuilder (THEMIS)",
    agent_class=AgentClass.C,
    domain="case_management",
    description="Montagem automatizada de caso com dados estruturados.",
    regulatory_basis=[
        "BCB Circular 3.978",
        "Res. 520/2022",
    ],
    llm=LLMConfig(
        model="claude-haiku-4-5",
        max_tokens=2048,
        temperature=0.1,
        timeout_ms=450,
    ),
    tools=[
        ToolSchema(
            name="get_case_evidence",
            description="Retrieve evidence trail for a case",
            parameters={
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "event_types": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["case_id"],
            },
            timeout_ms=500,
        ),
        ToolSchema(
            name="get_wallet_context",
            description="Retrieve wallet context for case building",
            parameters={
                "type": "object",
                "properties": {
                    "address": {"type": "string"},
                    "chain": {"type": "string"},
                },
                "required": ["address", "chain"],
            },
            timeout_ms=500,
        ),
    ],
    target_latency_p95_ms=450,
    eval=EvalConfig(target_tool_invocation_accuracy=0.98),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))

_register(AgentConfig(
    agent_id="LAW_ENFORCEMENT",
    name="LawEnforcement (THEMIS)",
    agent_class=AgentClass.B,
    domain="law_enforcement_export",
    description="Formatação jurídica para autoridades. COAF, VASP, judicial, FATF.",
    regulatory_basis=[
        "Lei 9.613/98",
        "Res. 520/2022",
        "Res. 739/2023",
    ],
    llm=LLMConfig(
        model="claude-sonnet-4-5",
        max_tokens=8192,
        temperature=0.05,
        timeout_ms=5000,
    ),
    rag=RAGConfig(
        enabled=True,
        top_k=10,
        corpus_ids=["lei_9613", "bcb_520", "in_bcb_739"],
    ),
    target_latency_p95_ms=5000,
    eval=EvalConfig(target_precision=0.95),
    requires_human_review=True,
    audit_level="full",
    zero_retention=True,
    anonymize_inputs=True,
))
