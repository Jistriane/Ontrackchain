-- ============================================================
-- Migration 0010: preventive_blocks
-- Registro de bloqueios preventivos com trilha imutável
-- Base regulatória: BCB 520 Art. 43 §2° VI (bloqueios atípicos)
--                   BCB 520 Art. 43 §2° V (listas de sanções)
--                   Lei 13.810/2019 (indisponibilidade CSNU)
--                   IN BCB 739 Art. 1° VII (bloqueio administrativo)
-- ============================================================

CREATE TABLE IF NOT EXISTS preventive_blocks (
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  case_id                   UUID REFERENCES cases(id),

  -- ─── ALVO DO BLOQUEIO ───────────────────────────────────────────────────────
  target_address            VARCHAR(255) NOT NULL,
  target_chain              VARCHAR(50) NOT NULL,
  tx_hash                   VARCHAR(255),     -- NULL se bloqueio de endereço (não tx)
  tx_amount_usd             NUMERIC(20, 2),   -- Estimativa em USD (para relatório COAF)
  tx_direction              VARCHAR(10),      -- 'INFLOW' | 'OUTFLOW'

  -- ─── DECISÃO DE BLOQUEIO ────────────────────────────────────────────────────
  -- Ações possíveis (espelha PreventiveBlockAgent.BLOCK_MATRIX):
  --   ALLOW               | Permitido (registrado para auditoria)
  --   BLOCK_IMMEDIATE     | Bloqueio imediato (OFAC alta confiança)
  --   BLOCK_AND_FREEZE    | Bloqueio + indisponibilidade (CSNU)
  --   BLOCK_AND_ALERT     | Bloqueio + alerta 15min ao analista
  --   BLOCK_AND_REPORT_COAF | Bloqueio + ROS automático ao COAF
  --   HOLD_AND_REVIEW     | Suspensão 24h + revisão humana
  --   HOLD_AND_ESCALATE   | Suspensão + escalonamento ao Compliance Officer
  --   HOLD_KYW_REQUIRED   | Suspensão até KYW completo (BCB 521 Art. 76-A §5°)
  --   ENHANCED_DD         | Permite com Due Diligence aprimorada (PEP)
  block_action              VARCHAR(50) NOT NULL,

  -- Stage que gerou o bloqueio: 'gateway' (Stage 1) | 'backend' (Stage 2)
  block_stage               VARCHAR(20) NOT NULL DEFAULT 'backend',

  -- Triggers que dispararam a decisão (array — múltiplos podem coexistir)
  -- Ex: ["ofac_hit", "aml_score_critical"]
  block_triggers            JSONB NOT NULL DEFAULT '[]',

  -- Artigos de lei e normas aplicados neste bloqueio específico
  regulatory_basis          TEXT[] NOT NULL DEFAULT '{}',

  -- Score AML no momento do bloqueio (0-100)
  aml_score_at_block        INTEGER,

  -- Hits de sanções que motivaram o bloqueio (snapshot imutável)
  sanctions_hits            JSONB DEFAULT '[]',

  -- ─── SCORES E ANÁLISE ───────────────────────────────────────────────────────
  -- Confiança da decisão (0.0 a 1.0)
  decision_confidence       NUMERIC(4, 3) NOT NULL DEFAULT 1.0,

  -- Contexto adicional (mixer_detected, chain_hopping, structuring, etc.)
  analysis_context          JSONB DEFAULT '{}',

  -- ─── RESPONSABILIDADE ────────────────────────────────────────────────────────
  -- Agente que disparou o bloqueio
  triggered_by_agent        VARCHAR(100) NOT NULL DEFAULT 'PreventiveBlockAgent',

  -- Revisão humana (obrigatória para HOLD_* e BLOCK_AND_REPORT_COAF)
  review_status             VARCHAR(50) NOT NULL DEFAULT 'PENDING_REVIEW',
  -- PENDING_REVIEW | CONFIRMED | LIFTED | ESCALATED | FALSE_POSITIVE

  reviewed_by_user_id       UUID REFERENCES users(id),
  reviewed_at               TIMESTAMPTZ,
  review_note               TEXT,

  -- ─── TRILHA DE INTEGRIDADE ───────────────────────────────────────────────────
  -- SHA-256 do snapshot completo no momento do bloqueio
  -- Permite verificar que os dados não foram adulterados após o bloqueio
  evidence_hash             VARCHAR(64) NOT NULL,

  -- Referência ao evento na evidence_trail
  evidence_trail_event_hash VARCHAR(64) REFERENCES evidence_trail(event_hash),

  -- ─── STATUS DO BLOQUEIO ──────────────────────────────────────────────────────
  status                    VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  -- ACTIVE | CONFIRMED | LIFTED | ESCALATED_COAF | FALSE_POSITIVE

  block_timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Quando/como o bloqueio foi removido (se aplicável)
  lifted_at                 TIMESTAMPTZ,
  lifted_by_user_id         UUID REFERENCES users(id),
  lifted_reason             TEXT,
  lift_requires_2fa         BOOLEAN NOT NULL DEFAULT TRUE,

  -- ─── NOTIFICAÇÕES ────────────────────────────────────────────────────────────
  -- TRUE se notificação foi enviada ao Compliance Officer
  notification_sent         BOOLEAN NOT NULL DEFAULT FALSE,
  notification_sent_at      TIMESTAMPTZ,

  -- ─── ROS COAF ────────────────────────────────────────────────────────────────
  -- Preenchido se block_action = BLOCK_AND_REPORT_COAF
  coaf_ros_required         BOOLEAN NOT NULL DEFAULT FALSE,
  coaf_ros_id               UUID,          -- preenchido quando ROS for gerado
  coaf_deadline             TIMESTAMPTZ,   -- 24h após o bloqueio (Lei 9.613/98 Art. 11-B)

  -- ─── RETENÇÃO REGULATÓRIA ────────────────────────────────────────────────────
  -- 5 anos (BCB 520 Art. 45 II)
  retain_until              TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 years')
);

-- ─── RLS — ISOLAMENTO POR TENANT ──────────────────────────────────────────────
ALTER TABLE preventive_blocks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS preventive_blocks_tenant_isolation ON preventive_blocks;
CREATE POLICY preventive_blocks_tenant_isolation
  ON preventive_blocks
  FOR ALL
  USING (
    check_rls_context()
    AND
    organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  )
  WITH CHECK (
    check_rls_context()
    AND
    organization_id = NULLIF(current_setting('app.organization_id', TRUE), '')::UUID
  );

-- ─── ÍNDICES ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_preventive_blocks_org_time
  ON preventive_blocks(organization_id, block_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_preventive_blocks_address
  ON preventive_blocks(target_address, target_chain);

CREATE INDEX IF NOT EXISTS idx_preventive_blocks_status
  ON preventive_blocks(organization_id, status)
  WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_preventive_blocks_review
  ON preventive_blocks(organization_id, review_status)
  WHERE review_status = 'PENDING_REVIEW';

CREATE INDEX IF NOT EXISTS idx_preventive_blocks_coaf
  ON preventive_blocks(organization_id, coaf_ros_required, coaf_deadline)
  WHERE coaf_ros_required = TRUE;

CREATE INDEX IF NOT EXISTS idx_preventive_blocks_case
  ON preventive_blocks(case_id)
  WHERE case_id IS NOT NULL;

-- UPDATE permitido para: review_status, reviewed_by_user_id, reviewed_at,
-- review_note, status, lifted_at, lifted_by_user_id, lifted_reason,
-- notification_sent, coaf_ros_id
-- DELETE é PROIBIDO por política — registros de bloqueio são permanentes

-- ─── COMENTÁRIO ───────────────────────────────────────────────────────────────
COMMENT ON TABLE preventive_blocks IS
  'Registro de bloqueios preventivos de ilícitos. '
  'DELETE proibido por política regulatória. '
  'Retenção: 5 anos (BCB 520 Art. 45 II). '
  'Base: BCB 520 Art. 43 §2° VI · Lei 13.810/2019 · IN BCB 739 Art. 1° VII.';
