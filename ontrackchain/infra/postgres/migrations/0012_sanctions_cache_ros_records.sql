-- ============================================================
-- Migration 0012: sanctions_lists_cache + ros_records
-- Cache local de listas de sanções e registros de ROS COAF
-- Base regulatória:
--   sanctions_lists_cache:
--     BCB 520 Art. 34 III (controles de listas de sanções)
--     BCB 520 Art. 43 §2° V (listas CSNU, OFAC, EU)
--     Lei 13.810/2019 (cumprimento resoluções CSNU)
--     FATF R.6 (Targeted Financial Sanctions)
--   ros_records:
--     Lei 9.613/98 Art. 11 (obrigação de comunicação ao COAF)
--     Lei 9.613/98 Art. 11-B (prazo de 24h)
--     BCB 520 Art. 44 (informações completas ao destinatário)
--     IN BCB 739 Art. 1° V (procedimentos de comunicação COAF)
-- ============================================================

ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

DO $$
DECLARE
  orphan_index_exists BOOLEAN;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uq_reports_external_report_id'
      AND conrelid = 'reports'::regclass
  ) THEN
    SELECT EXISTS (
      SELECT 1
      FROM pg_class idx
      JOIN pg_index i ON i.indexrelid = idx.oid
      WHERE idx.relname = 'uq_reports_external_report_id'
        AND i.indrelid = 'reports'::regclass
        AND NOT EXISTS (
          SELECT 1
          FROM pg_constraint c
          WHERE c.conindid = idx.oid
        )
    )
    INTO orphan_index_exists;

    IF orphan_index_exists THEN
      EXECUTE 'DROP INDEX IF EXISTS uq_reports_external_report_id';
    END IF;

    ALTER TABLE reports
      ADD CONSTRAINT uq_reports_external_report_id UNIQUE (external_report_id);
  END IF;
END
$$;

-- ─── SANCTIONS LISTS METADATA ────────────────────────────────────────────────
-- Controle de sincronização das listas de sanções
CREATE TABLE IF NOT EXISTS sanctions_lists_meta (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_name                 VARCHAR(50) NOT NULL UNIQUE,
  -- OFAC_SDN | OFAC_CONSOLIDATED | UN_CSNU | EU_CONSOLIDATED
  -- COAF_INTERNAL | OPENSANCTIONS | CUSTOM

  list_label                VARCHAR(255) NOT NULL,
  -- Ex: "OFAC Specially Designated Nationals"

  source_url                TEXT,
  regulatory_basis          TEXT NOT NULL,
  -- Ex: "Lei 13.810/2019 · BCB 520 Art. 43 §2° V"

  -- Status da lista
  -- ACTIVE | PENDING_CONFIG | DISABLED | ERROR
  status                    VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  status_reason             TEXT,          -- Motivo se PENDING_CONFIG ou ERROR

  -- Configuração de sync
  sync_interval_hours       INTEGER NOT NULL DEFAULT 24,
  last_sync_at              TIMESTAMPTZ,
  last_sync_status          VARCHAR(20),   -- SUCCESS | FAILED | PARTIAL
  last_sync_record_count    INTEGER,       -- Quantidade de registros na última sync
  last_sync_hash            VARCHAR(64),   -- SHA-256 do arquivo baixado

  -- Próxima sync agendada
  next_sync_at              TIMESTAMPTZ,

  -- Configuração de confiança mínima para hit
  min_confidence_threshold  NUMERIC(4, 3) NOT NULL DEFAULT 0.90,
  -- 0.95 para OFAC (bloqueio imediato), 0.90 para demais

  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Popula configuração inicial das listas (conforme v3.0 do documento)
INSERT INTO sanctions_lists_meta
  (list_name, list_label, source_url, regulatory_basis, status,
   sync_interval_hours, min_confidence_threshold)
VALUES
  (
    'OFAC_SDN',
    'OFAC Specially Designated Nationals (mirror local)',
    'https://sanctionslistservice.ofac.treas.gov/api/download/SDN_ADVANCED.XML',
    'Lei 13.810/2019 · BCB 520 Art. 43 §2° V',
    'ACTIVE', 6, 0.95
  ),
  (
    'UN_CSNU',
    'United Nations Security Council Consolidated List',
    'https://scsanctions.un.org/resources/xml/en/consolidated.xml',
    'Lei 13.810/2019 Art. 1° · BCB 520 Art. 43 §5°',
    'ACTIVE', 24, 0.90
  ),
  (
    'EU_CONSOLIDATED',
    'EU Consolidated Financial Sanctions List',
    'https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content',
    'FATF R.6 — Targeted Financial Sanctions · BCB 520 Art. 34 III',
    'ACTIVE', 24, 0.90
  ),
  (
    'COAF_INTERNAL',
    'COAF — Lista interna de suspeição Brasil',
    'https://www.coaf.fazenda.gov.br/api',
    'BCB 520 Art. 43 §2° V · Lei 9.613/98',
    'PENDING_CONFIG',     -- Aguarda definição/contratação do feed oficial
    12, 0.90
  ),
  (
    'OPENSANCTIONS',
    'OpenSanctions — Base consolidada internacional',
    'https://api.opensanctions.org',
    'FATF R.6 · BCB 520 Art. 34 III',
    'PENDING_CONFIG',     -- Aguarda OPENSANCTIONS_API_KEY
    24, 0.90
  )
ON CONFLICT (list_name) DO NOTHING;

-- ─── SANCTIONS HITS CACHE ────────────────────────────────────────────────────
-- Cache local dos registros das listas de sanções
-- Usado pelo SanctionsEngine para screening sem latência de API externa
CREATE TABLE IF NOT EXISTS sanctions_hits_cache (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  list_name                 VARCHAR(50) NOT NULL
                              REFERENCES sanctions_lists_meta(list_name),

  -- Tipo de entidade sancionada
  entity_type               VARCHAR(20) NOT NULL DEFAULT 'INDIVIDUAL',
  -- INDIVIDUAL | ORGANIZATION | VESSEL | AIRCRAFT

  -- Identificação da entidade
  entity_name               VARCHAR(500) NOT NULL,
  entity_aliases            JSONB NOT NULL DEFAULT '[]',
  -- Ex: ["José da Silva", "J. Silva", "JOSE SILVA"]

  -- Identificadores documentais
  entity_documents          JSONB NOT NULL DEFAULT '[]',
  -- Ex: [{ "type": "CPF", "number": "..." }, { "type": "PASSPORT", ... }]

  -- Endereços de carteira sancionados (se aplicável)
  wallet_addresses          JSONB NOT NULL DEFAULT '[]',
  -- Ex: [{ "chain": "ethereum", "address": "0x..." }]

  -- Dados da sanção
  designation_date          DATE,
  designation_reason        TEXT,
  sanctions_programs        TEXT[],       -- Ex: ["IRAN", "CUBA", "SDN"]

  -- Identificador único na lista de origem
  source_entity_id          VARCHAR(255),

  -- Dados geográficos
  nationalities             CHAR(3)[],    -- ISO 3166-1 alpha-3
  countries_of_activity     CHAR(3)[],

  -- Controle de cache
  synced_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  is_active                 BOOLEAN NOT NULL DEFAULT TRUE,

  -- Índice para busca fuzzy (busca por nome aproximado)
  entity_name_tsv           TSVECTOR GENERATED ALWAYS AS
                              (to_tsvector('simple', entity_name)) STORED,

  CONSTRAINT uq_sanctions_hits_cache_source
    UNIQUE (list_name, source_entity_id)
);

-- ─── ÍNDICES PARA SCREENING RÁPIDO ────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sanctions_cache_name_tsv
  ON sanctions_hits_cache USING GIN (entity_name_tsv);

CREATE INDEX IF NOT EXISTS idx_sanctions_cache_wallets
  ON sanctions_hits_cache USING GIN (wallet_addresses jsonb_path_ops)
  WHERE wallet_addresses != '[]';

CREATE INDEX IF NOT EXISTS idx_sanctions_cache_list
  ON sanctions_hits_cache(list_name, is_active);

CREATE INDEX IF NOT EXISTS idx_sanctions_cache_source_id
  ON sanctions_hits_cache(list_name, source_entity_id)
  WHERE source_entity_id IS NOT NULL;

-- ─── ROS RECORDS ─────────────────────────────────────────────────────────────
-- Registros de Relatório de Operação Suspeita para o COAF
-- Base: Lei 9.613/98 Art. 11 + BCB 520 Art. 44 + IN BCB 739 Art. 1° V
CREATE TABLE IF NOT EXISTS ros_records (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  case_id                   UUID REFERENCES cases(id),
  preventive_block_id       UUID REFERENCES preventive_blocks(id),

  -- ─── TIPOLOGIA COAF ───────────────────────────────────────────────────────
  -- Códigos de tipologia conforme COAF
  tipologia_code            VARCHAR(10) NOT NULL,
  -- TIP_001 | TIP_002 | TIP_003 | TIP_004 | TIP_005 | TIP_006 | TIP_007
  tipologia_description     TEXT NOT NULL,

  -- ─── DADOS DO ROS ─────────────────────────────────────────────────────────
  trigger_reason            TEXT NOT NULL,       -- O que disparou o ROS
  suspected_amount_brl      NUMERIC(20, 2),      -- Valor estimado em BRL
  suspected_address         VARCHAR(255),        -- Endereço suspeito principal
  suspected_chain           VARCHAR(50),

  -- ─── GERAÇÃO DO PDF ───────────────────────────────────────────────────────
  pdf_hash                  VARCHAR(64),         -- SHA-256 do PDF gerado
  pdf_path                  TEXT,                -- Path no storage

  -- ─── WORKFLOW DE APROVAÇÃO (Compliance Officer + 2FA obrigatório) ─────────
  -- PENDING_GENERATION   | PDF ainda não gerado
  -- PENDING_APPROVAL     | Aguardando aprovação do Compliance Officer
  -- APPROVED             | Aprovado pelo CO (com 2FA verificado)
  -- REJECTED             | Rejeitado pelo CO (falso positivo)
  -- SUBMITTED_MANUAL     | Submetido manualmente via COAF ONLINE
  status                    VARCHAR(30) NOT NULL DEFAULT 'PENDING_GENERATION',

  -- Geração
  generated_by_user_id      UUID REFERENCES users(id),
  generated_at              TIMESTAMPTZ,

  -- Aprovação (requer 2FA — IN BCB 739 Art. 1° V c.1)
  approved_by_user_id       UUID REFERENCES users(id),
  approved_at               TIMESTAMPTZ,
  approval_2fa_verified     BOOLEAN NOT NULL DEFAULT FALSE,
  rejection_reason          TEXT,

  -- ─── PRAZO LEGAL ──────────────────────────────────────────────────────────
  -- 24h após identificação da operação suspeita (Lei 9.613/98 Art. 11-B)
  submission_deadline       TIMESTAMPTZ NOT NULL,
  -- Alerta gerado em T+20h (4h antes do prazo)
  deadline_alert_sent       BOOLEAN NOT NULL DEFAULT FALSE,
  deadline_alert_sent_at    TIMESTAMPTZ,
  deadline_breached         BOOLEAN NOT NULL DEFAULT FALSE,

  -- ─── SUBMISSÃO MANUAL VIA COAF ONLINE ────────────────────────────────────
  submitted_by_user_id      UUID REFERENCES users(id),
  submitted_at              TIMESTAMPTZ,
  coaf_protocol_number      VARCHAR(100),        -- Nº de protocolo do COAF ONLINE
  coaf_receipt_hash         VARCHAR(64),         -- Hash do comprovante de recebimento

  -- ─── TRILHA DE INTEGRIDADE ────────────────────────────────────────────────
  evidence_hash             VARCHAR(64) NOT NULL,
  evidence_trail_ref        VARCHAR(64) REFERENCES evidence_trail(event_hash),

  -- ─── TIMESTAMPS ───────────────────────────────────────────────────────────
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- ─── RETENÇÃO (BCB 520 Art. 45 II) ───────────────────────────────────────
  retain_until              TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 years')
);

-- ─── TRIGGER: updated_at automático ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_ros_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ros_records_updated_at ON ros_records;
CREATE TRIGGER ros_records_updated_at
  BEFORE UPDATE ON ros_records
  FOR EACH ROW EXECUTE FUNCTION update_ros_updated_at();

-- ─── RLS ──────────────────────────────────────────────────────────────────────
ALTER TABLE ros_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ros_records_tenant_isolation ON ros_records;
CREATE POLICY ros_records_tenant_isolation
  ON ros_records FOR ALL
  USING (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

-- Sanctions cache não tem RLS (dados públicos de listas internacionais)
-- mas tem controle de acesso no nível de aplicação

-- ─── ÍNDICES ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ros_records_org_status
  ON ros_records(organization_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ros_records_deadline
  ON ros_records(organization_id, submission_deadline)
  WHERE status NOT IN ('SUBMITTED_MANUAL', 'REJECTED');

CREATE INDEX IF NOT EXISTS idx_ros_records_case
  ON ros_records(case_id)
  WHERE case_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ros_records_block
  ON ros_records(preventive_block_id)
  WHERE preventive_block_id IS NOT NULL;

-- ─── COMENTÁRIOS ──────────────────────────────────────────────────────────────
COMMENT ON TABLE sanctions_lists_meta IS
  'Configuração e controle de sync das listas de sanções. '
  'Base: BCB 520 Art. 34 III · Lei 13.810/2019 · FATF R.6.';

COMMENT ON TABLE sanctions_hits_cache IS
  'Cache local dos registros de entidades sancionadas. '
  'Permite screening offline sem dependência de APIs externas. '
  'Atualizado via Celery Beat (SanctionsAgent).';

COMMENT ON TABLE ros_records IS
  'Registros de Relatório de Operação Suspeita (ROS) para o COAF. '
  'Workflow: geração automática → aprovação CO (2FA) → submissão manual COAF ONLINE. '
  'Base: Lei 9.613/98 Art. 11 · Prazo: 24h (Art. 11-B). '
  'Retenção: 5 anos (BCB 520 Art. 45 II).';
