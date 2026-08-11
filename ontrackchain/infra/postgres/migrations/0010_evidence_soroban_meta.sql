-- Migration 0010: Soroban evidence anchor metadata (Compliance Layer 2 Fase 3 2027)
-- Idempotentemente: só cria colunas se não existirem. Escopo PostgreSQL >= 12.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'evidence_trail'
          AND column_name = 'soroban_contract_address'
    ) THEN
        ALTER TABLE evidence_trail
            ADD COLUMN soroban_contract_address VARCHAR(56) NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'evidence_trail'
          AND column_name = 'soroban_merkle_batch_id'
    ) THEN
        ALTER TABLE evidence_trail
            ADD COLUMN soroban_merkle_batch_id BIGINT NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'evidence_trail'
          AND column_name = 'soroban_salt_environment'
    ) THEN
        ALTER TABLE evidence_trail
            ADD COLUMN soroban_salt_environment BYTEA NOT NULL DEFAULT gen_random_bytes(16);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_evidence_trail_soroban_merkle
    ON evidence_trail (soroban_merkle_batch_id)
    WHERE soroban_merkle_batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_evidence_trail_soroban_contract
    ON evidence_trail (soroban_contract_address)
    WHERE soroban_contract_address IS NOT NULL;

COMMENT ON COLUMN evidence_trail.soroban_contract_address
    IS 'Stellar/Soroban contract address G... (C strkey ed25519 or contract) where this row was anchored via anchor_single or anchor_merkle_root.';

COMMENT ON COLUMN evidence_trail.soroban_merkle_batch_id
    IS 'Batch id when anchored via Merkle root (method anchor_merkle_root). NULL when anchored individually via anchor_single.';

COMMENT ON COLUMN evidence_trail.soroban_salt_environment
    IS 'Random 16 bytes SALT attached to every evidence hash BEFORE SHA-256 (KDF blinding). Prevents rainbow tables against the blind hashes published on-chain. LGPD/BCB 520 compliant: zero PII on-chain.';
