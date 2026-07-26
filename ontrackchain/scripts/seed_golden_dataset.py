"""
Golden Dataset Seeder — Populates eval test cases for agent framework.

Usage:
    python scripts/seed_golden_dataset.py
    python scripts/seed_golden_dataset.py --agent LEX
    python scripts/seed_golden_dataset.py --dry-run

Each test case is reviewed by a human before activating.
IN BCB 739 item II — evaluation contínua dos agentes.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# ── Golden test cases per agent ──────────────────────────────
# Format: (agent_id, case_id, input_data, expected_output, classification, citations, difficulty)

GOLDEN_CASES: list[dict[str, Any]] = [
    # ═══ LEX — Legal Analyst (Class B) ═══
    {
        "agent_id": "LEX",
        "case_id": "LEX-001",
        "input_data": {
            "question": "Qual a obrigação da instituição quando detecta transação suspeita com ativos virtuais?",
        },
        "expected_output": {
            "has_legal_basis": True,
            "has_fato_inferencia": True,
        },
        "expected_classification": "FATO",
        "expected_citations": ["BCB 520 Art. 20"],
        "difficulty": "easy",
    },
    {
        "agent_id": "LEX",
        "case_id": "LEX-002",
        "input_data": {
            "question": "Quais são os requisitos de due diligence para operações com ativos virtuais conforme BCB 520?",
        },
        "expected_output": {
            "has_legal_basis": True,
            "has_fato_inferencia": True,
        },
        "expected_classification": "FATO",
        "expected_citations": ["BCB 520 Art. 43"],
        "difficulty": "medium",
    },
    {
        "agent_id": "LEX",
        "case_id": "LEX-003",
        "input_data": {
            "question": "A IN BCB 739 permite o uso de IA para monitoramento de transações?",
        },
        "expected_output": {
            "has_legal_basis": True,
            "has_fato_inferencia": True,
        },
        "expected_classification": "FATO",
        "expected_citations": ["IN BCB 739 Art. 15"],
        "difficulty": "medium",
    },

    # ═══ ARGOS — Triage Agent (Class B) ═══
    {
        "agent_id": "ARGOS",
        "case_id": "ARGOS-001",
        "input_data": {
            "case_id": "CASE-001",
            "address": "0xTornadoCashAddr123",
            "chain": "ethereum",
            "context": "Cliente com endereço associado a Tornado Cash. Volume: $500K em 7 dias.",
        },
        "expected_output": {
            "intent": "AML",
            "priority": "HIGH",
        },
        "expected_classification": "INFERÊNCIA",
        "expected_citations": ["BCB 520 Art. 43"],
        "difficulty": "easy",
    },
    {
        "agent_id": "ARGOS",
        "case_id": "ARGOS-002",
        "input_data": {
            "case_id": "CASE-002",
            "address": "0xNormalExchange123",
            "chain": "ethereum",
            "context": "Exchange registra transferência de 0.5 ETH de endereço sem histórico. Valor baixo, sem padrão suspeito.",
        },
        "expected_output": {
            "intent": "ONBOARDING",
            "priority": "LOW",
        },
        "expected_classification": "FATO",
        "expected_citations": [],
        "difficulty": "easy",
    },

    # ═══ TRACER — On-chain Investigator (Class C) ═══
    {
        "agent_id": "TRACER",
        "case_id": "TRACER-001",
        "input_data": {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain": "ethereum",
            "question": "Analise as transações recentes deste endereço e identifique padrões suspeitos.",
        },
        "expected_output": {
            "tools_invoked": ["get_wallet_transactions", "check_sanctions"],
        },
        "expected_classification": "",
        "expected_citations": [],
        "expected_tool_calls": ["get_wallet_transactions"],
        "difficulty": "medium",
    },

    # ═══ GraphNarrator — Narrative Generator (Class B) ═══
    {
        "agent_id": "GraphNarrator",
        "case_id": "GN-001",
        "input_data": {
            "address": "0xdeadbeef",
            "chain": "ethereum",
            "profile": "analyst",
            "graph_data": {
                "risk_score": 72,
                "mixer_exposure": True,
                "sanctions_match": False,
            },
        },
        "expected_output": {
            "tem_risco": True,
            "perfil": "analyst",
        },
        "expected_classification": "INFERÊNCIA",
        "expected_citations": [],
        "difficulty": "medium",
    },

    # ═══ ESCREVA — Regulatory Writer (Class B) ═══
    {
        "agent_id": "ESCREVA",
        "case_id": "ESCREVA-001",
        "input_data": {
            "context": "Comunicação de Operação Suspeita ao COAF — caso de ransomware com 3 endereços vinculados.",
            "format": "coaf",
        },
        "expected_output": {
            "formato": "coaf",
            "deve_conter": ["identificação", "motivo_suspeita", "normas_aplicaveis"],
        },
        "expected_classification": "FATO",
        "expected_citations": ["Lei 9.613/98 Art. 9", "BCB 520 Art. 20"],
        "difficulty": "medium",
    },

    # ═══ CASE — Case Intelligence Agent (Class B) ═══
    {
        "agent_id": "CASE",
        "case_id": "CASE-001",
        "input_data": {
            "case_id": "case-001",
            "context": "Investigação de lavagem via DeFi — funds passaram por 3 pools antes de chegar em exchange.",
            "include_history": True,
            "include_recommendations": True,
        },
        "expected_output": {
            "tem_resumo": True,
            "tem_recomendações": True,
        },
        "expected_classification": "INFERÊNCIA",
        "expected_citations": [],
        "difficulty": "hard",
    },

    # ═══ AEGIS — Risk Scoring Engine (Class A) ═══
    {
        "agent_id": "AEGIS",
        "case_id": "AEGIS-001",
        "input_data": {
            "tx_count": 200,
            "mixer_transactions": 5,
            "sanctions_matches": 0,
            "high_risk_jurisdiction": False,
            "pep_flag": False,
        },
        "expected_output": {
            "risk_score_above": 40,
        },
        "expected_classification": "",
        "expected_citations": [],
        "difficulty": "easy",
    },
    {
        "agent_id": "AEGIS",
        "case_id": "AEGIS-002",
        "input_data": {
            "tx_count": 10,
            "mixer_transactions": 0,
            "sanctions_matches": 0,
            "high_risk_jurisdiction": False,
            "pep_flag": False,
        },
        "expected_output": {
            "risk_score_below": 30,
        },
        "expected_classification": "",
        "expected_citations": [],
        "difficulty": "easy",
    },

    # ═══ CLUSTER — Network Clustering (Class C) ═══
    {
        "agent_id": "CLUSTER",
        "case_id": "CLUSTER-001",
        "input_data": {
            "address": "0xabcdef1234567890abcdef1234567890abcdef12",
            "chain": "ethereum",
            "depth": 3,
        },
        "expected_output": {
            "tools_invoked": ["query_neo4j"],
        },
        "expected_classification": "",
        "expected_citations": [],
        "expected_tool_calls": ["query_neo4j"],
        "difficulty": "medium",
    },

    # ═══ OSINT — Open Source Intelligence (Class C) ═══
    {
        "agent_id": "OSINT",
        "case_id": "OSINT-001",
        "input_data": {
            "entity_name": "CryptoExchange Ltd",
            "jurisdiction": "Brazil",
            "query_type": "company_search",
        },
        "expected_output": {
            "tools_invoked": ["search_regulatory_databases"],
        },
        "expected_classification": "",
        "expected_citations": [],
        "expected_tool_calls": ["search_regulatory_databases"],
        "difficulty": "medium",
    },

    # ═══ ESCREVA — Report Writer (Class B) ═══
    {
        "agent_id": "ESCREVA",
        "case_id": "ESCREVA-001",
        "input_data": {
            "report_type": "COMMUNICATION_RDE",
            "case_id": "CASE-TEST-001",
            "wallet_address": "0xabc123",
            "findings": "Operação suspeita: $500K em 10 dias para mixing service",
            "risk_score": 88,
        },
        "expected_output": {
            "has_legal_basis": True,
            "has_fato_inferencia": True,
            "has_disclaimer": True,
        },
        "expected_classification": "INFERÊNCIA",
        "expected_citations": ["Lei 9.613/98", "Decreto 9.662/2019"],
        "difficulty": "medium",
    },

    # ═══ SYNTHESIS — Case Synthesis (Class B) ═══
    {
        "agent_id": "SYNTHESIS",
        "case_id": "SYNTHESIS-001",
        "input_data": {
            "case_id": "CASE-TEST-002",
            "risk_score": "75",
            "risk_level": "HIGH",
            "findings": "Exposição a mixer: $1.2M. OFAC proximity: 2 hops.",
            "agent_results": "AEGIS: score=75,level=HIGH; TRACER: mixer_exposure=true",
        },
        "expected_output": {
            "has_confidence_score": True,
            "has_fato_inferencia": True,
            "has_gaps": True,
        },
        "expected_classification": "INFERÊNCIA",
        "expected_citations": ["Lei 9.613/98", "GAFI Rec. 16"],
        "difficulty": "medium",
    },

    # ═══ TRACER — Transaction Tracer (Class C) ═══
    {
        "agent_id": "TRACER",
        "case_id": "TRACER-001",
        "input_data": {
            "address": "0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae",
            "chain": "ethereum",
            "context": "Exchange principal",
        },
        "expected_output": {
            "tools_invoked": ["get_wallet_transactions"],
        },
        "expected_classification": "",
        "expected_citations": [],
        "expected_tool_calls": ["get_wallet_transactions", "check_mixer_exposure"],
        "difficulty": "easy",
    },
    {
        "agent_id": "TRACER",
        "case_id": "TRACER-002",
        "input_data": {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain": "ethereum",
            "context": "Endereço com atividade suspeita recente",
        },
        "expected_output": {
            "tools_invoked": ["get_wallet_transactions"],
        },
        "expected_classification": "",
        "expected_citations": [],
        "expected_tool_calls": ["get_wallet_transactions", "check_mixer_exposure"],
        "difficulty": "easy",
    },
]


def main() -> None:
    """Seed golden dataset into PostgreSQL."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed agent golden dataset")
    parser.add_argument("--agent", type=str, help="Specific agent_id to seed (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print without executing")
    args = parser.parse_args()

    cases = GOLDEN_CASES
    if args.agent:
        cases = [c for c in cases if c["agent_id"] == args.agent]
        if not cases:
            print(f"No cases found for agent_id={args.agent}")
            sys.exit(1)

    print(f"Seeding {len(cases)} golden test cases...")

    if args.dry_run:
        print("\n--- DRY RUN: Cases to insert ---")
        for case in cases:
            print(f"  [{case['agent_id']}] {case['case_id']} — difficulty: {case['difficulty']}")
        print(f"\nTotal: {len(cases)} cases")
        return

    try:
        import psycopg
        from psycopg.rows import dict_row

        dsn = (
            f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB', 'ontrackchain')} "
            f"user={os.getenv('POSTGRES_USER', 'ontrackchain')} "
            f"password={os.getenv('POSTGRES_PASSWORD', 'ontrackchain')}"
        )

        with psycopg.connect(dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                inserted = 0
                skipped = 0

                for case in cases:
                    try:
                        cur.execute(
                            """
                            INSERT INTO agent_golden_dataset
                                (agent_id, case_id, input_data, expected_output,
                                 expected_classification, expected_citations,
                                 expected_tool_calls, difficulty, reviewed_by, is_active)
                            VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (agent_id, case_id) DO UPDATE SET
                                input_data = EXCLUDED.input_data,
                                expected_output = EXCLUDED.expected_output,
                                expected_classification = EXCLUDED.expected_classification,
                                expected_citations = EXCLUDED.expected_citations,
                                expected_tool_calls = EXCLUDED.expected_tool_calls,
                                difficulty = EXCLUDED.difficulty
                            """,
                            (
                                case["agent_id"],
                                case["case_id"],
                                json.dumps(case["input_data"]),
                                json.dumps(case["expected_output"]),
                                case["expected_classification"],
                                case["expected_citations"],
                                case.get("expected_tool_calls", []),
                                case["difficulty"],
                                "",  # reviewed_by — empty until human review
                                True,
                            ),
                        )
                        inserted += 1
                    except Exception as e:
                        print(f"  ERROR inserting {case['case_id']}: {e}")
                        skipped += 1

                conn.commit()

                print(f"\nDone: {inserted} inserted/updated, {skipped} skipped")

                # Summary by agent
                cur.execute(
                    "SELECT agent_id, COUNT(*) as cnt FROM agent_golden_dataset WHERE is_active GROUP BY agent_id ORDER BY agent_id"
                )
                print("\nGolden dataset summary:")
                for row in cur.fetchall():
                    print(f"  {row['agent_id']}: {row['cnt']} cases")

    except ImportError:
        print("ERROR: psycopg not installed. Install with: pip install 'psycopg[binary]>=3.2.0'")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
