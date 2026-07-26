-- ============================================================
-- Migration 0018: Agent Framework — pgvector RAG + Eval Tables
-- Vector store para corpus regulatório, golden dataset, production samples
-- Base regulatória: IN BCB 739 items II/VI, Res. 520/2022
-- ============================================================

-- ─── PGVECTOR EXTENSION ──────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── REGULATORY CORPUS CHUNKS (Vector Store for RAG) ────────
CREATE TABLE IF NOT EXISTS regulatory_corpus_chunks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  corpus_id           VARCHAR(50) NOT NULL,          -- bcb_520, lei_14478, etc.
  article             VARCHAR(100) NOT NULL,          -- Art. 43 §2° VI
  title               VARCHAR(500) NOT NULL,
  text                TEXT NOT NULL,
  embedding           vector(1024),                   -- voyage-3 dimensions
  hierarchy           INTEGER NOT NULL DEFAULT 3,     -- 0=FATF, 1=Lei, 2=Resolução, 3=IN
  authority           VARCHAR(100) NOT NULL,
  vigencia            DATE NOT NULL,
  revogacao           DATE,
  tags                TEXT[] DEFAULT '{}',
  chunk_hash          VARCHAR(64) NOT NULL UNIQUE,    -- SHA-256 of text for dedup
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE regulatory_corpus_chunks IS
  'Corpus regulatório chunked e vetorizado para RAG. '
  'Cada chunk é um artigo/inciso de legislação brasileira aplicável a PLD/FT de ativos virtuais. '
  'Embeddings gerados via Voyage-3 (1024 dimensões).';

COMMENT ON COLUMN regulatory_corpus_chunks.embedding IS
  'Vetor embedding (1024d) gerado pelo modelo voyage-3. '
  'Usado para similarity search no pipeline de RAG dos agentes Class B.';

COMMENT ON COLUMN regulatory_corpus_chunks.hierarchy IS
  'Hierarquia normativa: 0=FATF, 1=Lei, 2=Resolução BCB, 3=IN/CVM. '
  'Usado para re-ranking na recuperação.';

-- ─── AGENT GOLDEN DATASET ───────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_golden_dataset (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id            VARCHAR(50) NOT NULL,
  case_id             VARCHAR(100) NOT NULL,
  input_data          JSONB NOT NULL,
  expected_output     JSONB NOT NULL,
  expected_classification VARCHAR(20) DEFAULT ''
    CHECK (expected_classification IN ('', 'FATO', 'INFERÊNCIA', 'HIPÓTESE', 'RECOMENDAÇÃO')),
  expected_citations  TEXT[] DEFAULT '{}',
  expected_tool_calls TEXT[] DEFAULT '{}',
  difficulty          VARCHAR(10) NOT NULL DEFAULT 'medium'
    CHECK (difficulty IN ('easy', 'medium', 'hard')),
  reviewed_by         VARCHAR(255) DEFAULT '',
  is_active           BOOLEAN NOT NULL DEFAULT TRUE,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_golden_dataset_agent_case UNIQUE (agent_id, case_id)
);

COMMENT ON TABLE agent_golden_dataset IS
  'Golden dataset para avaliação contínua dos agentes. '
  'Usado em regression testing pré-deploy (IN BCB 739 item II). '
  'Cada caso é revisado por um humano antes de entrar no dataset.';

-- ─── AGENT PRODUCTION SAMPLES ───────────────────────────────
CREATE TABLE IF NOT EXISTS agent_production_samples (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id            VARCHAR(50) NOT NULL,
  input_data          JSONB NOT NULL,
  output_data         JSONB NOT NULL,
  latency_ms          INTEGER NOT NULL,
  tokens_used         INTEGER NOT NULL DEFAULT 0,
  provider            VARCHAR(50) NOT NULL DEFAULT 'deterministic',
  reviewed            BOOLEAN NOT NULL DEFAULT FALSE,
  review_score        INTEGER CHECK (review_score >= 1 AND review_score <= 5),
  review_notes        TEXT DEFAULT '',
  error               TEXT,
  sampled_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE agent_production_samples IS
  'Samples de chamadas de produção para review humano. '
  'Amostragem configurável por agente (default 5%). '
  'Usado para monitoramento contínuo e auditoria regulatória.';

-- ─── AGENT EVAL RUNS ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_eval_runs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id            VARCHAR(50) NOT NULL,
  total_cases         INTEGER NOT NULL,
  passed_cases        INTEGER NOT NULL,
  failed_cases        INTEGER NOT NULL,
  avg_precision       NUMERIC(5,4),
  avg_recall          NUMERIC(5,4),
  avg_citation_accuracy NUMERIC(5,4),
  avg_tool_accuracy   NUMERIC(5,4),
  avg_latency_ms      NUMERIC(10,2),
  p95_latency_ms      INTEGER,
  total_tokens        INTEGER NOT NULL DEFAULT 0,
  regression_detected BOOLEAN NOT NULL DEFAULT FALSE,
  run_type            VARCHAR(20) NOT NULL DEFAULT 'scheduled'
    CHECK (run_type IN ('scheduled', 'pre_deploy', 'manual', 'ci_cd')),
  executed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE agent_eval_runs IS
  'Histórico de execuções de evaluation pipeline. '
  'Cada run registra métricas contra o golden dataset. '
  'Bloqueia deploy se regression_detected = TRUE.';

-- ─── RLS ────────────────────────────────────────────────────
-- regulatory_corpus_chunks: shared table (not tenant-isolated — corpus is global)
-- No RLS needed — corpus is the same for all organizations.

ALTER TABLE agent_golden_dataset ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_production_samples ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_eval_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS agent_golden_dataset_tenant_isolation ON agent_golden_dataset;
CREATE POLICY agent_golden_dataset_tenant_isolation
  ON agent_golden_dataset FOR ALL
  USING (TRUE)   -- Global — golden dataset is shared across tenants
  WITH CHECK (TRUE);

DROP POLICY IF EXISTS agent_production_samples_tenant_isolation ON agent_production_samples;
CREATE POLICY agent_production_samples_tenant_isolation
  ON agent_production_samples FOR ALL
  USING (TRUE)   -- Global — production samples for central review
  WITH CHECK (TRUE);

DROP POLICY IF EXISTS agent_eval_runs_tenant_isolation ON agent_eval_runs;
CREATE POLICY agent_eval_runs_tenant_isolation
  ON agent_eval_runs FOR ALL
  USING (TRUE)
  WITH CHECK (TRUE);

-- ─── INDEXES ────────────────────────────────────────────────

-- Corpus: similarity search + temporal filtering
CREATE INDEX IF NOT EXISTS idx_corpus_chunks_corpus_article
  ON regulatory_corpus_chunks(corpus_id, article);

CREATE INDEX IF NOT EXISTS idx_corpus_chunks_vigencia
  ON regulatory_corpus_chunks(vigencia)
  WHERE revogacao IS NULL;

CREATE INDEX IF NOT EXISTS idx_corpus_chunks_hash
  ON regulatory_corpus_chunks(chunk_hash);

-- HNSW index for vector similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_corpus_chunks_embedding_hnsw
  ON regulatory_corpus_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Golden dataset: per-agent lookups
CREATE INDEX IF NOT EXISTS idx_golden_dataset_agent
  ON agent_golden_dataset(agent_id)
  WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_golden_dataset_difficulty
  ON agent_golden_dataset(agent_id, difficulty);

-- Production samples: review queue + agent filtering
CREATE INDEX IF NOT EXISTS idx_production_samples_agent
  ON agent_production_samples(agent_id, sampled_at DESC);

CREATE INDEX IF NOT EXISTS idx_production_samples_unreviewed
  ON agent_production_samples(agent_id, sampled_at DESC)
  WHERE reviewed = FALSE;

-- Eval runs: history per agent
CREATE INDEX IF NOT EXISTS idx_eval_runs_agent
  ON agent_eval_runs(agent_id, executed_at DESC);

-- ─── TRIGGERS ───────────────────────────────────────────────

-- auto-update updated_at on agent_golden_dataset
CREATE OR REPLACE FUNCTION update_agent_golden_dataset_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agent_golden_dataset_updated_at ON agent_golden_dataset;
CREATE TRIGGER agent_golden_dataset_updated_at
  BEFORE UPDATE ON agent_golden_dataset
  FOR EACH ROW EXECUTE FUNCTION update_agent_golden_dataset_updated_at();

-- auto-update updated_at on regulatory_corpus_chunks
CREATE OR REPLACE FUNCTION update_regulatory_corpus_chunks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS regulatory_corpus_chunks_updated_at ON regulatory_corpus_chunks;
CREATE TRIGGER regulatory_corpus_chunks_updated_at
  BEFORE UPDATE ON regulatory_corpus_chunks
  FOR EACH ROW EXECUTE FUNCTION update_regulatory_corpus_chunks_updated_at();
