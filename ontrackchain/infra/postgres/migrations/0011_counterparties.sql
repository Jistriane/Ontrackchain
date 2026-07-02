-- ============================================================
-- Migration 0011: counterparties
-- Cadastro e supervisão de contrapartes (KYC/KYB regulado)
-- Base regulatória: BCB 520 Art. 47 (conhecimento de contrapartes)
--                   IN BCB 739 Art. 1° IV (procedimentos de parceiros)
--                   Circular BCB 3.978/2020 (KYC detalhado)
--                   BCB 520 Art. 58-59 (avaliação de perfil de risco)
-- ============================================================

CREATE TABLE IF NOT EXISTS counterparties (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  created_by_user_id        UUID NOT NULL REFERENCES users(id),

  -- ─── TIPO DE CONTRAPARTE ──────────────────────────────────────────────────
  -- CLIENTE_PF          | Pessoa física cliente final
  -- CLIENTE_PJ          | Pessoa jurídica cliente final
  -- PARCEIRO_COMERCIAL  | Parceiro com vínculo operacional
  -- PRESTADOR_SERVICO   | Prestador terceirizado relevante
  -- CONTRAPARTE_DEFI    | Protocolo DeFi com interação recorrente
  -- EXCHANGE_CEX        | Exchange centralizada parceira
  -- PROVEDOR_LIQUIDEZ   | Provedor de liquidez contratado
  counterparty_type         VARCHAR(50) NOT NULL,

  -- ─── IDENTIFICAÇÃO (Circular BCB 3.978/2020) ──────────────────────────────
  legal_name                VARCHAR(500) NOT NULL,
  trading_name              VARCHAR(500),              -- Nome fantasia (PJ)

  -- Documento principal
  document_type             VARCHAR(20) NOT NULL,      -- CPF | CNPJ | PASSPORT | FOREIGN_ID
  document_number           VARCHAR(50) NOT NULL,
  document_country          CHAR(3) NOT NULL DEFAULT 'BRA',  -- ISO 3166-1 alpha-3
  document_verified         BOOLEAN NOT NULL DEFAULT FALSE,
  document_verified_at      TIMESTAMPTZ,

  -- Dados de contato e localização
  registration_data         JSONB NOT NULL DEFAULT '{}',
  -- Ex: { "address": {...}, "phone": "...", "email": "...",
  --       "business_activity": "...", "incorporation_date": "...",
  --       "nationality": "..." }

  -- UBO — Ultimate Beneficial Owner (PJ — obrigatório BCB 520 Art. 47)
  -- Pessoas físicas que controlam ≥ 25% da entidade
  beneficial_owners         JSONB NOT NULL DEFAULT '[]',
  -- Ex: [{ "name": "...", "cpf": "...", "ownership_pct": 30.0 }]

  -- ─── ENDEREÇOS ON-CHAIN ───────────────────────────────────────────────────
  -- Endereços de carteira vinculados a esta contraparte
  wallet_addresses          JSONB NOT NULL DEFAULT '[]',
  -- Ex: [{ "chain": "ethereum", "address": "0x...", "label": "hot" }]

  -- ─── CLASSIFICAÇÃO DE RISCO (BCB 520 Art. 58-59) ─────────────────────────
  -- 1 = BAIXO    (revisão anual)
  -- 2 = MÉDIO    (revisão semestral)
  -- 3 = ALTO     (revisão trimestral + Due Diligence aprimorada)
  -- 4 = CRÍTICO  (decisão do Compliance Officer + escalonamento)
  risk_level                INTEGER NOT NULL DEFAULT 1
                            CHECK (risk_level BETWEEN 1 AND 4),

  risk_rationale            TEXT,           -- Justificativa da classificação
  risk_classified_by        UUID REFERENCES users(id),
  risk_classified_at        TIMESTAMPTZ,

  -- Score on-chain (0-100, calculado pelo CounterpartyAgent)
  onchain_risk_score        INTEGER CHECK (onchain_risk_score BETWEEN 0 AND 100),
  onchain_analysis          JSONB DEFAULT '{}',  -- Detalhes da análise on-chain

  -- ─── PEP — PESSOA EXPOSTA POLITICAMENTE (BCB 520 Art. 58) ────────────────
  is_pep                    BOOLEAN NOT NULL DEFAULT FALSE,
  pep_detail                JSONB DEFAULT '{}',
  -- Ex: { "position": "Senador", "country": "BRA", "since": "2020-01", "tier": 1 }

  -- ─── SANÇÕES ─────────────────────────────────────────────────────────────
  sanctions_cleared         BOOLEAN NOT NULL DEFAULT FALSE,
  sanctions_check_date      TIMESTAMPTZ,
  sanctions_hits            JSONB NOT NULL DEFAULT '[]',
  -- Registra hits encontrados; se cleared=FALSE, onboarding bloqueado

  -- ─── KYC/KYB STATUS ───────────────────────────────────────────────────────
  -- PENDING           | Aguardando análise
  -- DOCUMENTS_PENDING | Documentação incompleta
  -- UNDER_REVIEW      | Em análise pelo analista
  -- APPROVED          | KYC aprovado
  -- REJECTED          | KYC rejeitado
  -- ENHANCED_PENDING  | Aguardando Due Diligence aprimorada
  kyc_status                VARCHAR(50) NOT NULL DEFAULT 'PENDING',
  kyc_reviewed_by           UUID REFERENCES users(id),
  kyc_reviewed_at           TIMESTAMPTZ,
  kyc_rejection_reason      TEXT,

  -- ─── DUE DILIGENCE APRIMORADA (risk_level >= 3) ──────────────────────────
  enhanced_dd_required      BOOLEAN NOT NULL DEFAULT FALSE,
  enhanced_dd_status        VARCHAR(50),
  -- PENDING | IN_PROGRESS | COMPLETED | WAIVED_WITH_JUSTIFICATION
  enhanced_dd_completed_by  UUID REFERENCES users(id),
  enhanced_dd_completed_at  TIMESTAMPTZ,
  enhanced_dd_findings      TEXT,
  enhanced_dd_checklist     JSONB DEFAULT '[]',

  -- ─── REVALIDAÇÃO PERIÓDICA ────────────────────────────────────────────────
  next_review_date          DATE,
  review_frequency_days     INTEGER NOT NULL DEFAULT 365,
  -- 365 = risco BAIXO | 180 = MÉDIO | 90 = ALTO | 30 = CRÍTICO
  last_reviewed_at          TIMESTAMPTZ,
  last_reviewed_by          UUID REFERENCES users(id),

  -- ─── STATUS DA CONTRAPARTE ────────────────────────────────────────────────
  -- ACTIVE | SUSPENDED | OFFBOARDED | BLOCKED
  status                    VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  status_changed_at         TIMESTAMPTZ,
  status_changed_by         UUID REFERENCES users(id),
  status_reason             TEXT,

  -- ─── TRILHA DE INTEGRIDADE ────────────────────────────────────────────────
  -- SHA-256 do snapshot no momento do onboarding (BCB 520 Art. 45 II)
  evidence_hash             VARCHAR(64) NOT NULL,

  -- ─── TIMESTAMPS ───────────────────────────────────────────────────────────
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- ─── RETENÇÃO REGULATÓRIA (BCB 520 Art. 45 II) ────────────────────────────
  retain_until              TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 years'),

  -- ─── CONSTRAINT ───────────────────────────────────────────────────────────
  -- Unicidade: mesmo documento não pode ser cadastrado 2x na mesma organização
  CONSTRAINT uq_counterparty_doc_org
    UNIQUE (organization_id, document_type, document_number)
);

-- ─── TRIGGER: updated_at automático ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_counterparty_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS counterparty_updated_at ON counterparties;
CREATE TRIGGER counterparty_updated_at
  BEFORE UPDATE ON counterparties
  FOR EACH ROW EXECUTE FUNCTION update_counterparty_updated_at();

-- ─── HISTÓRICO DE MUDANÇAS ────────────────────────────────────────────────────
-- Auditoria de alterações em dados da contraparte (exigida pela IN BCB 739)
CREATE TABLE IF NOT EXISTS counterparty_history (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  counterparty_id           UUID NOT NULL REFERENCES counterparties(id),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  changed_by_user_id        UUID NOT NULL REFERENCES users(id),
  change_type               VARCHAR(50) NOT NULL,
  -- KYC_STATUS_CHANGE | RISK_LEVEL_CHANGE | SANCTIONS_UPDATE
  -- DD_COMPLETED | REVIEW_COMPLETED | ADDRESS_ADDED | STATUS_CHANGE
  field_changed             VARCHAR(100),
  old_value                 TEXT,
  new_value                 TEXT,
  change_reason             TEXT,
  changed_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  evidence_hash             VARCHAR(64) NOT NULL
);

-- ─── RLS ──────────────────────────────────────────────────────────────────────
ALTER TABLE counterparties ENABLE ROW LEVEL SECURITY;
ALTER TABLE counterparty_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS counterparties_tenant_isolation ON counterparties;
CREATE POLICY counterparties_tenant_isolation
  ON counterparties FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

DROP POLICY IF EXISTS counterparty_history_tenant_isolation ON counterparty_history;
CREATE POLICY counterparty_history_tenant_isolation
  ON counterparty_history FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

-- ─── ÍNDICES ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_counterparties_org
  ON counterparties(organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_counterparties_kyc_status
  ON counterparties(organization_id, kyc_status)
  WHERE kyc_status != 'APPROVED';

CREATE INDEX IF NOT EXISTS idx_counterparties_risk_level
  ON counterparties(organization_id, risk_level)
  WHERE risk_level >= 3;

CREATE INDEX IF NOT EXISTS idx_counterparties_review_due
  ON counterparties(organization_id, next_review_date)
  WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_counterparties_pep
  ON counterparties(organization_id)
  WHERE is_pep = TRUE;

CREATE INDEX IF NOT EXISTS idx_counterparties_sanctions
  ON counterparties(organization_id)
  WHERE sanctions_cleared = FALSE;

CREATE INDEX IF NOT EXISTS idx_counterparty_history_cp
  ON counterparty_history(counterparty_id, changed_at DESC);

COMMENT ON TABLE counterparties IS
  'Cadastro de contrapartes com KYC/KYB regulado. '
  'Base: BCB 520 Art. 47 · IN BCB 739 Art. 1° IV · Circular BCB 3.978/2020. '
  'Retenção: 5 anos (BCB 520 Art. 45 II).';
