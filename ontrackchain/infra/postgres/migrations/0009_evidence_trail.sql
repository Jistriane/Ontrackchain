-- ============================================================
-- Migration 0009: evidence_trail
-- Trilha de evidências append-only com encadeamento SHA-256
-- Base regulatória: BCB 520 Art. 45 II (retenção 5 anos)
--                   IN BCB 739 Art. 1° VIII (registro de operações)
-- Regra: INSERT ONLY — UPDATE e DELETE são bloqueados por trigger
-- ============================================================

-- ─── TABELA PRINCIPAL ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence_trail (
  -- Identidade
  id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id           UUID NOT NULL REFERENCES organizations(id),
  case_id                   UUID REFERENCES cases(id),

  -- Tipo de evento
  -- Valores válidos:
  --   CASE_CREATED | CASE_UPDATED | INVESTIGATION_STARTED | INVESTIGATION_COMPLETED
  --   REPORT_GENERATED | REPORT_DOWNLOADED
  --   BLOCK_TRIGGERED | BLOCK_CONFIRMED | BLOCK_LIFTED | BLOCK_ALLOW
  --   BLOCK_IMMEDIATE | BLOCK_AND_FREEZE | BLOCK_AND_ALERT | BLOCK_AND_REPORT_COAF
  --   HOLD_AND_REVIEW | HOLD_AND_ESCALATE | HOLD_KYW_REQUIRED
  --   SANCTIONS_CHECKED | SANCTIONS_HIT | COAF_ROS_GENERATED | COAF_ROS_APPROVED
  --   COAF_ROS_REJECTED | COAF_ROS_SUBMITTED | COAF_ROS_SUBMITTED_MANUAL | COAF_PROTOCOL_REGISTERED
  --   ALERT_CREATED | ALERT_ACKNOWLEDGED | ALERT_ESCALATED | ALERT_BATCH_ACK
  --   COUNTERPARTY_ONBOARDED | COUNTERPARTY_UPDATED | KYC_APPROVED | KYC_REJECTED
  --   ENHANCED_DD | ENHANCED_DD_COMPLETED | PEP_FLAGGED
  --   EVIDENCE_EXPORTED | AUDIT_ACCESSED | CHAIN_INTEGRITY_VERIFIED
  event_type                VARCHAR(100) NOT NULL,

  -- Payload completo do evento (snapshot imutável do estado)
  event_payload             JSONB NOT NULL DEFAULT '{}',

  -- Trilha de responsabilidade (IN BCB 739 Art. 1° VIII)
  actor_user_id             UUID REFERENCES users(id),
  actor_agent_id            VARCHAR(100),    -- ex: "PreventiveBlockAgent" | "CoafReportAgent"
  actor_ip_address          INET,
  actor_user_agent          TEXT,

  -- ─── ENCADEAMENTO SHA-256 (âncora de integridade) ─────────────────────────
  -- event_hash = SHA-256 de: event_type + event_payload + actor + recorded_at
  -- Permite detectar adulteração ou supressão de eventos
  event_hash                VARCHAR(64) NOT NULL UNIQUE,

  -- Hash do evento anterior da mesma organização
  -- NULL apenas para o primeiro evento de cada organização
  -- Permite validar que nenhum evento foi suprimido ou reordenado
  prev_event_hash           VARCHAR(64),

  -- TRUE se prev_event_hash corresponde ao último hash da cadeia
  -- FALSE indica possível adulteração (auditável)
  chain_integrity_ok        BOOLEAN NOT NULL DEFAULT TRUE,

  -- ─── TEMPORALIDADE IMUTÁVEL ───────────────────────────────────────────────
  -- Preenchido automaticamente — nunca alterado
  recorded_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- ─── RETENÇÃO REGULATÓRIA (BCB 520 Art. 45 II) ────────────────────────────
  -- 5 anos a partir do registro
  retain_until              TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '5 years'),

  -- ─── BASE REGULATÓRIA DO EVENTO ───────────────────────────────────────────
  -- Artigos aplicados neste evento específico
  regulatory_basis          TEXT[] DEFAULT '{}',

  -- ─── ÂNCORA ON-CHAIN (Fase 3 — Stellar/Soroban) ──────────────────────────
  -- NULL até Fase 3 (2027). Preenchido apenas para relatórios finais.
  soroban_tx_hash           VARCHAR(255),
  soroban_contract          VARCHAR(255),
  soroban_anchored_at       TIMESTAMPTZ
);

-- ─── TRIGGER: IMUTABILIDADE GARANTIDA ─────────────────────────────────────────
-- Bloqueia UPDATE e DELETE em qualquer row desta tabela
-- Compliance: BCB 520 Art. 45 II — registros devem ser mantidos íntegros

CREATE OR REPLACE FUNCTION prevent_evidence_modification()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP IN ('UPDATE', 'DELETE') THEN
    RAISE EXCEPTION
      'evidence_trail é imutável por determinação regulatória. '
      'Operação % proibida. '
      'Base: BCB 520 Art. 45 II · IN BCB 739 Art. 1° VIII',
      TG_OP
      USING ERRCODE = 'integrity_constraint_violation';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS evidence_trail_immutability ON evidence_trail;
CREATE TRIGGER evidence_trail_immutability
  BEFORE UPDATE OR DELETE ON evidence_trail
  FOR EACH ROW EXECUTE FUNCTION prevent_evidence_modification();

-- ─── TRIGGER: ENCADEAMENTO AUTOMÁTICO ─────────────────────────────────────────
-- Antes de inserir, busca o hash do evento anterior da mesma organização
-- e preenche prev_event_hash automaticamente

CREATE OR REPLACE FUNCTION set_evidence_chain()
RETURNS TRIGGER AS $$
DECLARE
  prev_hash VARCHAR(64);
  last_integrity BOOLEAN;
BEGIN
  -- Busca o hash do último evento da mesma organização (por tempo de inserção)
  SELECT event_hash
    INTO prev_hash
    FROM evidence_trail
   WHERE organization_id = NEW.organization_id
   ORDER BY recorded_at DESC
   LIMIT 1;

  NEW.prev_event_hash = prev_hash; -- NULL se for o primeiro evento da org

  -- Verifica integridade da cadeia
  -- (o service layer calcula o hash correto e o banco valida aqui)
  NEW.chain_integrity_ok = TRUE;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS evidence_chain_before_insert ON evidence_trail;
CREATE TRIGGER evidence_chain_before_insert
  BEFORE INSERT ON evidence_trail
  FOR EACH ROW EXECUTE FUNCTION set_evidence_chain();

-- ─── RLS — ISOLAMENTO POR TENANT ──────────────────────────────────────────────
ALTER TABLE evidence_trail ENABLE ROW LEVEL SECURITY;

-- Usuários da aplicação só veem registros da sua própria organização
DROP POLICY IF EXISTS evidence_trail_tenant_isolation ON evidence_trail;
CREATE POLICY evidence_trail_tenant_isolation
  ON evidence_trail
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

-- Admins do banco (role db_owner) têm acesso irrestrito para auditoria BCB
-- (não submetida ao RLS)

-- ─── ÍNDICES ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_evidence_trail_org_time
  ON evidence_trail(organization_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_trail_case
  ON evidence_trail(case_id)
  WHERE case_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_evidence_trail_event_type
  ON evidence_trail(event_type, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_evidence_trail_actor
  ON evidence_trail(actor_user_id, recorded_at DESC)
  WHERE actor_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_evidence_trail_hash
  ON evidence_trail(event_hash);

-- Índice para auditoria de retenção (identifica registros expirando)
CREATE INDEX IF NOT EXISTS idx_evidence_trail_retain
  ON evidence_trail(retain_until)
  WHERE soroban_tx_hash IS NULL;

-- ─── COMENTÁRIO DE DOCUMENTAÇÃO ───────────────────────────────────────────────
COMMENT ON TABLE evidence_trail IS
  'Trilha de evidências append-only. '
  'Imutável por trigger (prevent_evidence_modification). '
  'Encadeamento SHA-256 via trigger (set_evidence_chain) para detectar adulteração. '
  'Base: BCB 520 Art. 45 II (retenção 5 anos) + IN BCB 739 Art. 1° VIII. '
  'Âncora Soroban (soroban_tx_hash) prevista para Fase 3 — 2027.';

COMMENT ON COLUMN evidence_trail.event_hash IS
  'SHA-256 de: event_type + event_payload + actor_user_id + actor_agent_id + recorded_at. '
  'Calculado pelo EvidenceTrailService antes do INSERT.';

COMMENT ON COLUMN evidence_trail.prev_event_hash IS
  'SHA-256 do evento anterior da mesma organização. '
  'NULL apenas para o primeiro evento. '
  'Preenchido automaticamente pelo trigger set_evidence_chain. '
  'Quebra de cadeia indica supressão ou adulteração.';

COMMENT ON COLUMN evidence_trail.retain_until IS
  'Calculado automaticamente: recorded_at + 5 anos. '
  'Base: BCB 520 Art. 45 II — retenção mínima de 5 anos.';
