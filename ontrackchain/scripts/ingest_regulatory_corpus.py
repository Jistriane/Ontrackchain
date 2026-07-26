"""
Regulatory Corpus Ingestion Script — Seeds the pgvector RAG store.

Usage:
    python scripts/ingest_regulatory_corpus.py
    python scripts/ingest_regulatory_corpus.py --corpus bcb_520
    python scripts/ingest_regulatory_corpus.py --dry-run

Requires:
    - PostgreSQL with pgvector extension (migration 0018)
    - VOYAGE_API_KEY env var (for embeddings) — without it, embeddings are NULL
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import date
from typing import Any

# ── Regulatory chunks: Brazilian crypto AML regulations ──────
# Each chunk = one article/inciso with metadata for temporal filtering.

CORPUS_CHUNKS: list[dict[str, Any]] = [
    # ═══ BCB Resolução 520/2022 ═══
    {
        "corpus_id": "bcb_520",
        "article": "Art. 1",
        "title": "Objeto e Âmbito de Aplicação",
        "text": (
            "A presente Resolução estabelece procedimentos para a prevenção e combate à lavagem de dinheiro, "
            "ao financiamento do terrorismo e à proliferação de armas de destruição em massa no âmbito das "
            "instituições financeiras e demais instituições autorizadas a funcionar pelo Banco Central do Brasil, "
            "incluindo aquelas que prestam serviços de transferência de valores e de cambio de moedas estrangeiras "
            "e de moedas virtuais."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["escopo", "aplicabilidade", "PLD", "FT"],
    },
    {
        "corpus_id": "bcb_520",
        "article": "Art. 3",
        "title": "Definições — Ativo Virtual",
        "text": (
            "Para fins desta Resolução, considera-se: "
            "I — ativo virtual: representação de valor digital que pode ser trocada ou utilizado como meio de "
            "troca ou investimento, e não é emitido ou garantido por nenhum banco central nem por nenhum "
            "governo, compreendidos os tokens virtuais e as criptomoedas; "
            "II — unidade de conta em ativo virtual: token, moeda virtual ou outro instrumento que possa ser "
            "utilizado como unidade de valor para ser trocado por ativo virtual ou por moeda fiduciária."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["definição", "ativo_virtual", "criptomoeda", "token"],
    },
    {
        "corpus_id": "bcb_520",
        "article": "Art. 11",
        "title": "Procedimentos de PLD/FT — Avaliação de Risco",
        "text": (
            "As instituições deverão adotar procedimentos de PLD/FT proporcionais aos riscos identificados, "
            "incluindo: "
            "I — identificação do cliente e de seus representantes; "
            "II — identificação do beneficial owner; "
            "III — conhecimento da finalidade e da natureza da relação de negócio; "
            "IV — monitoramento contínuo da relação de negócio; "
            "V — manutenção de registros. "
            "§ 1º Para as operações com ativos virtuais, os procedimentos deverão considerar as "
            "particularidades da tecnologia blockchain, incluindo a rastreabilidade de transações on-chain."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["PLD", "FT", "avaliação_risco", "KYC", "monitoramento", "blockchain"],
    },
    {
        "corpus_id": "bcb_520",
        "article": "Art. 20",
        "title": "Comunicação de Operação Suspeita ao COAF",
        "text": (
            "As instituições deverão comunicar ao COAF as operações que, em razão de suas peculiaridades, "
            "possam configurar prática de lavagem de dinheiro ou de financiamento do terrorismo, observados "
            "os prazos e procedimentos estabelecidos. "
            "§ 1º A comunicação deverá ser feita em até 24 horas após a identificação da operação suspeita. "
            "§ 2º As comunicações deverão ser mantidas em sigilo absoluto."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["COAF", "comunicação", "suspeita", "sigilo", "prazo"],
    },
    {
        "corpus_id": "bcb_520",
        "article": "Art. 43",
        "title": "Operações com Ativos Virtuais — Due Diligence Reforçada",
        "text": (
            "Nas operações com ativos virtuais, as instituições deverão adotar, no mínimo: "
            "I — identificação e verificação da identidade do remetente e do destinatário; "
            "II — registro dos endereços de carteiras digitais utilizados na operação; "
            "III — classificação de risco do endereço de origem e destino com base em análise on-chain; "
            "IV — verificação em listas de sanções nacionais e internacionais; "
            "V — análise de exposição a mixers, privacy coins e serviços de mixing; "
            "VI — monitoramento de transações com valor superior a R$ 1.000,00 (mil reais)."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["ativo_virtual", "due_diligence", "sanções", "mixer", "blockchain", "monitoramento"],
    },
    # ═══ IN BCB 739/2023 ═══
    {
        "corpus_id": "in_bcb_739",
        "article": "Art. 1",
        "title": "Objeto — Procedimentos Operacionais de PLD/FT",
        "text": (
            "Esta Instrução Normativa estabelece os procedimentos operacionais para a prevenção e o combate "
            "à lavagem de dinheiro e ao financiamento do terrorismo no âmbito das instituições sujeitas à "
            "supervisão do Banco Central do Brasil."
        ),
        "hierarchy": 3,
        "authority": "BCB",
        "vigencia": "2023-12-01",
        "tags": ["procedimentos", "PLD", "FT", "operacional"],
    },
    {
        "corpus_id": "in_bcb_739",
        "article": "Art. 7",
        "title": "Classificação de Risco do Cliente",
        "text": (
            "As instituições deverão classificar seus clientes quanto ao risco de lavagem de dinheiro e de "
            "financiamento do terrorismo, adotando, no mínimo, os seguintes critérios: "
            "I — nível de risco intrínseco do tipo de atividade econômica; "
            "II — nível de risco geográfico; "
            "III — nível de risco do produto ou serviço contratado; "
            "IV — nível de risco da estrutura societária e do beneficiário final; "
            "V — nível de risco de canal de relacionamento; "
            "VI — nível de risco de operações com ativos virtuais."
        ),
        "hierarchy": 3,
        "authority": "BCB",
        "vigencia": "2023-12-01",
        "tags": ["classificação_risco", "cliente", "ativo_virtual", "geográfico"],
    },
    {
        "corpus_id": "in_bcb_739",
        "article": "Art. 10",
        "title": "Monitoramento e Avaliação de Risco",
        "text": (
            "As instituições deverão realizar, de forma contínua e atualizada, a avaliação dos riscos de "
            "lavagem de dinheiro e de financiamento do terrorismo, considerando: "
            "I — a natureza, a complexidade e o volume das operações realizadas; "
            "II — as características dos clientes e suas atividades; "
            "III — os canais de distribuição utilizados; "
            "IV — as normas e os regulamentos aplicáveis; "
            "V — as ameaças, vulnerabilidades e demais informações relevantes."
        ),
        "hierarchy": 3,
        "authority": "BCB",
        "vigencia": "2023-12-01",
        "tags": ["monitoramento", "avaliação_risco", "contínuo"],
    },
    {
        "corpus_id": "in_bcb_739",
        "article": "Art. 15",
        "title": "Ferramentas de Análise — Automação e IA",
        "text": (
            "As instituições deverão dispor de ferramentas de análise que possibilitem: "
            "I — a identificação de operações incompatíveis com o perfil do cliente; "
            "II — a identificação de padrões suspeitos de transações; "
            "III — a vinculação de operações entre si; "
            "IV — a geração de alertas para investigação; "
            "V — o registro completo da cadeia de evidências. "
            "§ 1º As ferramentas poderão utilizar tecnologias de inteligência artificial, "
            "desde que acompanhadas de mecanismos de explicabilidade e supervisão humana."
        ),
        "hierarchy": 3,
        "authority": "BCB",
        "vigencia": "2023-12-01",
        "tags": ["ferramentas", "IA", "automação", "explicabilidade", "auditoria"],
    },
    # ═══ BCB Resolução 521/2022 ═══
    {
        "corpus_id": "bcb_521",
        "article": "Art. 2",
        "title": "Procedimentos — Pessoas Expostas Politicamente",
        "text": (
            "As instituições deverão adotar procedimentos específicos para o relacionamento com pessoas "
            "expostas politicamente, seus familiares e sócios em pessoas jurídicas deles dependentes, "
            "incluindo: "
            "I — adoção de medidas adicionais de conhecimento da atividade e da origem econômica; "
            "II — constituição de contas e operações no nível superior da hierarquia institucional; "
            "III — monitoramento especial da movimentação financeira."
        ),
        "hierarchy": 2,
        "authority": "BCB",
        "vigencia": "2022-12-01",
        "tags": ["PEP", "pessoa_exposta", "due_diligence", "monitoramento"],
    },
    # ═══ Lei 14.478/2022 ═══
    {
        "corpus_id": "lei_14478",
        "article": "Art. 2",
        "title": "Definições — Ativo Virtual (Lei)",
        "text": (
            "Para fins desta Lei, considera-se: "
            "I — ativo virtual: representação de valor digital que pode ser trocado ou utilizado como meio "
            "de troca ou investimento, e não é emitido ou garantido por nenhum banco central nem por nenhum "
            "governo, compreendidos os tokens virtuais e as criptomoedas; "
            "II — provedor de serviço de ativo virtual: pessoa jurídica que realize, em caráter profissional, "
            "uma ou mais das seguintes atividades relacionadas a ativos virtuais: "
            "a) administração de cadastros de ativos virtuais; "
            "b) custódia ou administração de carteiras de ativos virtuais; "
            "c) intermediação de negociação de ativos virtuais; "
            "d) transferência de ativos virtuais; "
            "e) conversão de ativos virtuais em moeda fiduciária e vice-versa; "
            "f) serviço de emissão ou oferta de ativos virtuais."
        ),
        "hierarchy": 1,
        "authority": "Congresso Nacional",
        "vigencia": "2022-12-29",
        "tags": ["definição", "ativo_virtual", "VASP", "lei"],
    },
    {
        "corpus_id": "lei_14478",
        "article": "Art. 5",
        "title": "Regulação e Supervisão — BCB e CVM",
        "text": (
            "O Banco Central do Brasil e a Comissão de Valores Mobiliários exercerão, de forma coordinada, "
            "as atividades de regulação e supervisão das atividades de prestação de serviços de ativo virtual "
            "nos termos de suas competências. "
            "§ 1º Ao Banco Central do Brasil caberá a regulação e supervisão dos provedores de serviços "
            "de ativo virtual que realizem: "
            "I — administração de cadastros de ativos virtuais; "
            "II — custódia ou administração de carteiras de ativos virtuais; "
            "III — intermediação de negociação de ativos virtuais; "
            "IV — transferência de ativos virtuais; "
            "V — conversão de ativos virtuais em moeda fiduciária e vice-versa."
        ),
        "hierarchy": 1,
        "authority": "Congresso Nacional",
        "vigencia": "2022-12-29",
        "tags": ["regulação", "supervisão", "BCB", "CVM", "VASP"],
    },
    # ═══ Lei 9.613/1998 ═══
    {
        "corpus_id": "lei_9613",
        "article": "Art. 9",
        "title": "Obrigações de Instituições — PLD/FT",
        "text": (
            "As instituições financeiras e as demais instituições autorizadas a funcionar pelo Banco Central "
            "do Brasil deverão, em suas relações com clientes e com o público em geral: "
            "I — comunicar ao Conselho de Controle de Atividades Financeiras (COAF) as transações que "
            "possam configurar lavagem de dinheiro ou financiamento do terrorismo; "
            "II — manter registro de todas as transações realizadas; "
            "III — adotar procedimentos de diligence e de identificação de clientes."
        ),
        "hierarchy": 1,
        "authority": "Congresso Nacional",
        "vigencia": "1998-03-03",
        "tags": ["obrigações", "COAF", "comunicação", "PLD", "FT"],
    },
    # ═══ FATF R.15 ═══
    {
        "corpus_id": "fatf_r15",
        "article": "Recommendation 15",
        "title": "New Technologies — Virtual Assets",
        "text": (
            "Countries should identify, assess, and understand the money laundering and terrorist financing "
            "risks associated with virtual asset activities and virtual asset service providers (VASPs). "
            "Countries should apply risk-based approach to the regulation and supervision of VASPs. "
            "Countries should ensure that VASPs are licensed or registered and subject to AML/CFT obligations. "
            "Countries should ensure that VASPs implement effective AML/CFT measures. "
            "Countries should ensure that VASPs report suspicious transactions."
        ),
        "hierarchy": 0,
        "authority": "FATF",
        "vigencia": "2015-01-01",
        "tags": ["FATF", "virtual_assets", "VASP", "risk_based", "AML", "CFT"],
    },
    {
        "corpus_id": "fatf_r15",
        "article": "Interpretive Note",
        "title": "IN R.15 — Red Flag Indicators for Virtual Assets",
        "text": (
            "Red flag indicators that may warrant enhanced due diligence include: "
            "1. Use of privacy-enhancing technologies (mixers, tumblers, privacy coins); "
            "2. Transactions involving addresses associated with darknet marketplaces; "
            "3. Large transactions with no apparent economic or business purpose; "
            "4. Structured transactions designed to avoid reporting thresholds; "
            "5. Rapid movement of funds through multiple addresses; "
            "6. Transactions with addresses associated with sanctioned entities; "
            "7. Use of multiple VASPs to obscure the audit trail; "
            "8. Transactions involving jurisdictions with weak AML/CFT frameworks."
        ),
        "hierarchy": 0,
        "authority": "FATF",
        "vigencia": "2015-01-01",
        "tags": ["red_flags", "privacy", "mixer", "darknet", "sanctions", "due_diligence"],
    },
    # ═══ FATF R.16 ═══
    {
        "corpus_id": "fatf_r16",
        "article": "Recommendation 16",
        "title": "Wire Transfers — Travel Rule",
        "text": (
            "Countries and financial institutions should ensure that accurate and meaningful originator "
            "and beneficiary information is obtained, secured, and transmitted with virtual asset "
            "transfer transactions. The originator and beneficiary information should be made available "
            "to the appropriate authorities upon request. VASPs should obtain and hold required and accurate "
            "originator and/or beneficiary information on virtual asset transfers."
        ),
        "hierarchy": 0,
        "authority": "FATF",
        "vigencia": "2015-01-01",
        "tags": ["travel_rule", "originador", "beneficiário", "VASP", "transferência"],
    },
]


def _chunk_hash(text: str) -> str:
    """Compute SHA-256 hash of chunk text for dedup."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _compute_embedding(text: str, api_key: str | None, attempt: int = 0) -> list[float] | None:
    """Compute embedding using Voyage AI API. Returns None if no API key."""
    if not api_key:
        return None

    try:
        import voyageai
        import time
        client = voyageai.Client(api_key=api_key)
        result = client.embed([text], model="voyage-3")
        return result.embeddings[0]
    except Exception as e:
        if attempt < 3:
            wait = 2 ** (attempt + 1)
            print(f"    Embedding failed (attempt {attempt+1}), retrying in {wait}s: {e}")
            time.sleep(wait)
            return _compute_embedding(text, api_key, attempt + 1)
        print(f"    Embedding failed after 3 attempts: {e}")
        return None


def main() -> None:
    """Ingest regulatory corpus into PostgreSQL + pgvector."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest regulatory corpus for RAG")
    parser.add_argument("--corpus", type=str, help="Specific corpus_id to ingest (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    parser.add_argument("--no-embeddings", action="store_true", help="Skip embedding generation")
    args = parser.parse_args()

    voyage_key = os.getenv("VOYAGE_API_KEY", "") if not args.no_embeddings else None

    # Filter chunks
    chunks = CORPUS_CHUNKS
    if args.corpus:
        chunks = [c for c in chunks if c["corpus_id"] == args.corpus]
        if not chunks:
            print(f"No chunks found for corpus_id={args.corpus}")
            sys.exit(1)

    print(f"Ingesting {len(chunks)} regulatory chunks...")
    if voyage_key:
        print("Voyage API key detected — generating embeddings")
    else:
        print("No VOYAGE_API_KEY — embeddings will be NULL (set for production)")

    # Build INSERT statements
    import time
    inserts = []
    for i, chunk in enumerate(chunks):
        chunk_hash = _chunk_hash(chunk["text"])
        embedding = _compute_embedding(chunk["text"], voyage_key)
        if embedding:
            print(f"  [{i+1}/{len(chunks)}] {chunk['corpus_id']} {chunk['article']} — embedding: OK")
        else:
            print(f"  [{i+1}/{len(chunks)}] {chunk['corpus_id']} {chunk['article']} — embedding: NULL")

        inserts.append({
            "corpus_id": chunk["corpus_id"],
            "article": chunk["article"],
            "title": chunk["title"],
            "text": chunk["text"],
            "embedding": embedding,
            "hierarchy": chunk["hierarchy"],
            "authority": chunk["authority"],
            "vigencia": chunk["vigencia"],
            "tags": chunk["tags"],
            "chunk_hash": chunk_hash,
        })
        # Rate limit: wait 1.5s between Voyage API calls
        if voyage_key and i < len(chunks) - 1:
            time.sleep(1.5)

    if args.dry_run:
        print("\n--- DRY RUN: Generated chunks ---")
        for i, insert in enumerate(inserts):
            has_emb = "YES" if insert["embedding"] else "NULL"
            print(f"  [{i+1}] {insert['corpus_id']} {insert['article']} — embedding: {has_emb}")
            print(f"       hash: {insert['chunk_hash']}")
        print(f"\nTotal: {len(inserts)} chunks")
        return

    # Execute inserts via psycopg
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

                for insert in inserts:
                    try:
                        if insert["embedding"] is not None:
                            cur.execute(
                                """
                                INSERT INTO regulatory_corpus_chunks
                                    (corpus_id, article, title, text, embedding,
                                     hierarchy, authority, vigencia, tags, chunk_hash)
                                VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s)
                                ON CONFLICT (chunk_hash) DO UPDATE SET
                                    title = EXCLUDED.title,
                                    text = EXCLUDED.text,
                                    embedding = EXCLUDED.embedding,
                                    tags = EXCLUDED.tags
                                """,
                                (
                                    insert["corpus_id"],
                                    insert["article"],
                                    insert["title"],
                                    insert["text"],
                                    str(insert["embedding"]),
                                    insert["hierarchy"],
                                    insert["authority"],
                                    insert["vigencia"],
                                    insert["tags"],
                                    insert["chunk_hash"],
                                ),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO regulatory_corpus_chunks
                                    (corpus_id, article, title, text, embedding,
                                     hierarchy, authority, vigencia, tags, chunk_hash)
                                VALUES (%s, %s, %s, %s, NULL, %s, %s, %s, %s, %s)
                                ON CONFLICT (chunk_hash) DO UPDATE SET
                                    title = EXCLUDED.title,
                                    text = EXCLUDED.text,
                                    tags = EXCLUDED.tags
                                """,
                                (
                                    insert["corpus_id"],
                                    insert["article"],
                                    insert["title"],
                                    insert["text"],
                                    insert["hierarchy"],
                                    insert["authority"],
                                    insert["vigencia"],
                                    insert["tags"],
                                    insert["chunk_hash"],
                                ),
                            )
                        inserted += 1
                    except Exception as e:
                        print(f"  ERROR inserting {insert['corpus_id']} {insert['article']}: {e}")
                        skipped += 1

                conn.commit()

                print(f"\nDone: {inserted} inserted/updated, {skipped} skipped")

                # Print summary by corpus
                cur.execute(
                    "SELECT corpus_id, COUNT(*) as cnt FROM regulatory_corpus_chunks GROUP BY corpus_id ORDER BY corpus_id"
                )
                print("\nCorpus summary:")
                for row in cur.fetchall():
                    print(f"  {row['corpus_id']}: {row['cnt']} chunks")

    except ImportError:
        print("ERROR: psycopg not installed. Install with: pip install 'psycopg[binary]>=3.2.0'")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
