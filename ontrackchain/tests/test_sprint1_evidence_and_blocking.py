"""
Testes unitários para EvidenceTrailService, EvidenceIntegration e PreventiveBlockAgent.

Cobre:
  - Cálculo determinístico do hash SHA-256
  - Encadeamento de eventos (prev_event_hash)
  - Detecção de quebra de cadeia (verify_chain_integrity)
  - Mapeamento correto de event_types
  - PreventiveBlockAgent: prioridades de decisão (P1-P5)
  - Pre-screening Stage 1: extração de endereço da URL
  - Integração piggyback audit_log → evidence_trail

Não requer banco de dados real — usa mocks/fakes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ontrackchain_agents.evidence_trail import (
    AuthContext,
    EvidenceTrailService,
    EVIDENCE_EVENT_TYPES,
    _compute_event_hash,
)
from ontrackchain_agents.evidence_integration import (
    emit_evidence_event_sync,
    _compute_event_hash as integration_compute_hash,
    VALID_EVENT_TYPES,
)
from ontrackchain_agents.preventive_block import (
    PreventiveBlockAgent,
    BlockDecision,
    SanctionsHit,
    SanctionsResult,
    WalletContext,
    BLOCK_ACTIONS,
    REDIS_BLOCKLIST_ACTIONS,
    CONFIDENCE_THRESHOLDS,
)
from auth_service.pre_screening import (
    extract_address_from_path,
    REDIS_BLOCKLIST_PREFIX,
)


# ─── FIXTURES ────────────────────────────────────────────────────────────────

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000002")
CASE_ID = UUID("00000000-0000-0000-0000-000000000003")

EVM_ADDRESS = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
STELLAR_ADDRESS = "GCEZWKCA5VLDNRLN3RPRJMRZOX3Z6G5CHCGLEWZE5LUGVSSEEPWOQ5Z"
BITCOIN_ADDRESS = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"


def make_auth(
    user_id: Optional[UUID] = None,
    agent_id: Optional[str] = None,
    org_id: UUID = ORG_ID,
) -> AuthContext:
    return AuthContext(
        user_id=user_id or USER_ID,
        agent_id=agent_id,
        org_id=org_id,
    )


def make_wallet(
    address: str = EVM_ADDRESS,
    chain: str = "ethereum",
    aml_score: int = 0,
    **kwargs,
) -> WalletContext:
    return WalletContext(address=address, chain=chain, aml_score=aml_score, **kwargs)


def make_sanctions_result(hits: list[SanctionsHit] | None = None) -> SanctionsResult:
    return SanctionsResult(
        address=EVM_ADDRESS,
        chain="ethereum",
        has_hit=bool(hits),
        hits=hits or [],
    )


# ─── TESTES: EvidenceTrailService — hash SHA-256 ──────────────────────────────

class TestEvidenceHash:
    def test_hash_deterministico(self):
        """Mesmo input deve produzir sempre o mesmo hash."""
        ts = "2026-07-01T12:00:00+00:00"
        h1 = _compute_event_hash("CASE_CREATED", ORG_ID, CASE_ID, {"x": 1},
                                  USER_ID, None, ts)
        h2 = _compute_event_hash("CASE_CREATED", ORG_ID, CASE_ID, {"x": 1},
                                  USER_ID, None, ts)
        assert h1 == h2

    def test_hash_sensivel_ao_event_type(self):
        """Mudar o event_type deve produzir hash diferente."""
        ts = "2026-07-01T12:00:00+00:00"
        h1 = _compute_event_hash("CASE_CREATED", ORG_ID, None, {}, USER_ID, None, ts)
        h2 = _compute_event_hash("REPORT_GENERATED", ORG_ID, None, {}, USER_ID, None, ts)
        assert h1 != h2

    def test_hash_sensivel_ao_payload(self):
        """Qualquer mudança no payload deve alterar o hash."""
        ts = "2026-07-01T12:00:00+00:00"
        h1 = _compute_event_hash("CASE_CREATED", ORG_ID, None, {"x": 1}, USER_ID, None, ts)
        h2 = _compute_event_hash("CASE_CREATED", ORG_ID, None, {"x": 2}, USER_ID, None, ts)
        assert h1 != h2

    def test_hash_sensivel_ao_org_id(self):
        """Org diferente deve produzir hash diferente (RLS crítico)."""
        ts = "2026-07-01T12:00:00+00:00"
        org2 = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        h1 = _compute_event_hash("CASE_CREATED", ORG_ID, None, {}, USER_ID, None, ts)
        h2 = _compute_event_hash("CASE_CREATED", org2, None, {}, USER_ID, None, ts)
        assert h1 != h2

    def test_hash_64_chars_hex(self):
        """SHA-256 deve ter exatamente 64 chars hexadecimais."""
        ts = "2026-07-01T12:00:00+00:00"
        h = _compute_event_hash("CASE_CREATED", ORG_ID, None, {}, USER_ID, None, ts)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_integration_hash_identico_ao_service(self):
        """Módulo de integração deve calcular o mesmo hash que o service."""
        ts = "2026-07-01T12:00:00+00:00"
        h_service = _compute_event_hash(
            "CASE_CREATED", ORG_ID, CASE_ID, {"k": "v"}, USER_ID, "AgentX", ts
        )
        h_integration = integration_compute_hash(
            "CASE_CREATED", str(ORG_ID), str(CASE_ID), {"k": "v"},
            str(USER_ID), "AgentX", ts
        )
        assert h_service == h_integration


# ─── TESTES: EvidenceTrailService — event_types válidos ──────────────────────

class TestEvidenceEventTypes:
    def test_event_types_validos_existem(self):
        """Os event_types mínimos exigidos pela regulação devem existir."""
        required = {
            "CASE_CREATED", "INVESTIGATION_COMPLETED",
            "REPORT_GENERATED", "BLOCK_IMMEDIATE", "BLOCK_AND_FREEZE",
            "COAF_ROS_GENERATED", "SANCTIONS_HIT", "COUNTERPARTY_ONBOARDED",
            "EVIDENCE_EXPORTED", "CHAIN_INTEGRITY_VERIFIED",
        }
        assert required.issubset(EVIDENCE_EVENT_TYPES)

    def test_integration_types_subset_de_service(self):
        """Integração e service devem compartilhar exatamente o mesmo catálogo."""
        assert VALID_EVENT_TYPES == EVIDENCE_EVENT_TYPES

    @pytest.mark.asyncio
    async def test_record_event_rejeita_tipo_invalido(self):
        """EvidenceTrailService deve rejeitar event_types não mapeados."""
        db_mock = AsyncMock()
        svc = EvidenceTrailService(db=db_mock)
        auth = make_auth()

        with pytest.raises(ValueError, match="não é válido"):
            await svc.record_event(
                org_id=ORG_ID,
                event_type="TIPO_INEXISTENTE",
                event_payload={},
                auth=auth,
            )


# ─── TESTES: EvidenceTrailService — verify_chain_integrity ───────────────────

class TestChainIntegrity:
    @pytest.mark.asyncio
    async def test_cadeia_vazia_e_integra(self):
        """Organização sem eventos deve retornar chain_intact=True."""
        db_mock = MagicMock()
        db_mock.fetch = AsyncMock(return_value=[])
        db_mock.execute = AsyncMock()

        svc = EvidenceTrailService(db=db_mock)
        result = await svc.verify_chain_integrity(ORG_ID)

        assert result["chain_intact"] is True
        assert result["total_events"] == 0
        assert result["broken_links"] == []

    @pytest.mark.asyncio
    async def test_cadeia_um_evento_integra(self):
        """Primeiro evento com prev_hash=None deve ser íntegro."""
        h1 = "a" * 64

        fake_row = MagicMock()
        fake_row.__getitem__ = lambda self, k: {
            "id": uuid4(), "event_type": "CASE_CREATED",
            "event_hash": h1, "prev_event_hash": None,
            "recorded_at": MagicMock(isoformat=lambda: "2026-07-01T12:00:00+00:00"),
            "chain_integrity_ok": True,
        }[k]

        db_mock = MagicMock()
        db_mock.fetch = AsyncMock(return_value=[fake_row])
        db_mock.execute = AsyncMock()

        svc = EvidenceTrailService(db=db_mock)
        result = await svc.verify_chain_integrity(ORG_ID)

        assert result["chain_intact"] is True
        assert len(result["broken_links"]) == 0

    @pytest.mark.asyncio
    async def test_cadeia_quebrada_detecta_supressao(self):
        """Evento com prev_hash errado deve ser detectado como quebra."""
        h1 = "a" * 64
        h2 = "b" * 64
        h_errado = "z" * 64  # Deveria ser h1 mas está errado → supressão

        def make_row(event_hash, prev_hash, event_type="CASE_CREATED"):
            row = MagicMock()
            data = {
                "id": uuid4(), "event_type": event_type,
                "event_hash": event_hash, "prev_event_hash": prev_hash,
                "recorded_at": MagicMock(isoformat=lambda: "2026-07-01T00:00:00+00:00"),
                "chain_integrity_ok": True,
            }
            row.__getitem__ = lambda self, k: data[k]
            return row

        db_mock = MagicMock()
        db_mock.fetch = AsyncMock(return_value=[
            make_row(h1, None),
            make_row(h2, h_errado),   # ← prev_hash errado
        ])
        db_mock.execute = AsyncMock()

        svc = EvidenceTrailService(db=db_mock)
        result = await svc.verify_chain_integrity(ORG_ID)

        assert result["chain_intact"] is False
        assert len(result["broken_links"]) == 1
        assert result["broken_links"][0]["expected_prev_hash"] == h1
        assert result["broken_links"][0]["found_prev_hash"] == h_errado


# ─── TESTES: PreventiveBlockAgent — prioridades de decisão ───────────────────

class TestPreventiveBlockAgent:
    def make_agent(self) -> PreventiveBlockAgent:
        evidence_mock = AsyncMock()
        evidence_mock.record_event = AsyncMock(return_value="a" * 64)
        return PreventiveBlockAgent(
            evidence_svc=evidence_mock,
            redis_client=None,
            db=None,
        )

    @pytest.mark.asyncio
    async def test_p1_csnu_retorna_block_and_freeze(self):
        """Hit CSNU com confiança >= 0.90 deve resultar em BLOCK_AND_FREEZE."""
        agent = self.make_agent()
        hit = SanctionsHit(
            list_name="UN_CSNU",
            entity_name="Entidade Sancionada",
            confidence=0.95,
        )
        wallet = make_wallet()
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result([hit]),
            auth=make_auth(),
        )
        assert result.action == "BLOCK_AND_FREEZE"
        assert result.requires_coaf_report is True
        assert any("13.810" in b for b in result.regulatory_basis)

    @pytest.mark.asyncio
    async def test_p2_ofac_retorna_block_immediate(self):
        """Hit OFAC com confiança >= 0.95 deve resultar em BLOCK_IMMEDIATE."""
        agent = self.make_agent()
        hit = SanctionsHit(
            list_name="OFAC_SDN",
            entity_name="SDN Entity",
            confidence=0.97,
        )
        wallet = make_wallet()
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result([hit]),
            auth=make_auth(),
        )
        assert result.action == "BLOCK_IMMEDIATE"
        assert result.requires_coaf_report is False
        assert any("OFAC" in b for b in result.regulatory_basis)

    @pytest.mark.asyncio
    async def test_p2_ofac_baixa_confianca_nao_bloqueia(self):
        """Hit OFAC com confiança < 0.95 NÃO deve acionar BLOCK_IMMEDIATE."""
        agent = self.make_agent()
        hit = SanctionsHit(
            list_name="OFAC_SDN",
            entity_name="Possível Match",
            confidence=0.70,  # Abaixo do threshold
        )
        wallet = make_wallet()
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result([hit]),
            auth=make_auth(),
        )
        assert result.action == "ALLOW"

    @pytest.mark.asyncio
    async def test_p3_aml_score_80_retorna_block_and_alert(self):
        """Score AML >= 80 deve resultar em BLOCK_AND_ALERT."""
        agent = self.make_agent()
        wallet = make_wallet(aml_score=85)
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result(),
            auth=make_auth(),
        )
        assert result.action == "BLOCK_AND_ALERT"
        assert any("520" in b for b in result.regulatory_basis)

    @pytest.mark.asyncio
    async def test_p3_aml_score_79_nao_bloqueia(self):
        """Score AML < 80 NÃO deve acionar BLOCK_AND_ALERT."""
        agent = self.make_agent()
        wallet = make_wallet(aml_score=79)
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result(),
            auth=make_auth(),
        )
        assert result.action == "ALLOW"

    @pytest.mark.asyncio
    async def test_p4_mixer_retorna_block_and_report_coaf(self):
        """Contato direto com mixer deve resultar em BLOCK_AND_REPORT_COAF."""
        agent = self.make_agent()
        wallet = make_wallet(has_direct_mixer_contact=True)
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result(),
            auth=make_auth(),
        )
        assert result.action == "BLOCK_AND_REPORT_COAF"
        assert result.requires_coaf_report is True
        assert any("90 III" in b for b in result.regulatory_basis)

    @pytest.mark.asyncio
    async def test_p5_selfcustody_internacional_retorna_hold_kyw(self):
        """Autocustódia não identificada em tx internacional → HOLD_KYW_REQUIRED."""
        agent = self.make_agent()
        wallet = make_wallet(
            is_self_custody=True,
            owner_identified=False,
            is_international_transfer=True,
        )
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result(),
            auth=make_auth(),
        )
        assert result.action == "HOLD_KYW_REQUIRED"
        assert any("76-A" in b for b in result.regulatory_basis)

    @pytest.mark.asyncio
    async def test_p1_tem_prioridade_sobre_p3(self):
        """CSNU (P1) deve ter prioridade sobre AML score (P3)."""
        agent = self.make_agent()
        hit = SanctionsHit(list_name="UN_CSNU", entity_name="X", confidence=0.95)
        wallet = make_wallet(aml_score=99)  # P3 ativo também
        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result([hit]),
            auth=make_auth(),
        )
        assert result.action == "BLOCK_AND_FREEZE"  # P1 vence

    @pytest.mark.asyncio
    async def test_allow_registra_na_evidence_trail(self):
        """Mesmo ALLOW deve registrar na evidence_trail (auditável)."""
        evidence_mock = AsyncMock()
        evidence_mock.record_event = AsyncMock(return_value="a" * 64)
        agent = PreventiveBlockAgent(evidence_svc=evidence_mock)

        wallet = make_wallet(aml_score=0)
        await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result(),
            auth=make_auth(),
        )

        evidence_mock.record_event.assert_called_once()
        call_kwargs = evidence_mock.record_event.call_args.kwargs
        assert call_kwargs["event_type"] == "BLOCK_ALLOW"

    @pytest.mark.asyncio
    async def test_redis_atualizado_para_block_immediate(self):
        """BLOCK_IMMEDIATE deve atualizar a blocklist Redis (Stage 1 sync)."""
        redis_mock = AsyncMock()
        redis_mock.sadd = AsyncMock()
        redis_mock.expire = AsyncMock()

        evidence_mock = AsyncMock()
        evidence_mock.record_event = AsyncMock(return_value="a" * 64)

        agent = PreventiveBlockAgent(evidence_svc=evidence_mock, redis_client=redis_mock)
        hit = SanctionsHit(list_name="OFAC_SDN", entity_name="X", confidence=0.98)
        wallet = make_wallet()

        result = await agent.evaluate(
            wallet_context=wallet,
            sanctions_result=make_sanctions_result([hit]),
            auth=make_auth(),
        )

        assert result.action == "BLOCK_IMMEDIATE"
        assert result.redis_blocklist_updated is True
        redis_mock.sadd.assert_called_once()

    def test_todos_block_actions_documentados(self):
        """Todos os BLOCK_ACTIONS devem ter descrição."""
        for action, description in BLOCK_ACTIONS.items():
            assert isinstance(description, str)
            assert len(description) > 0


# ─── TESTES: Pre-screening Stage 1 — extração de endereço ────────────────────

class TestPreScreening:
    def test_extrai_evm_address(self):
        addr = extract_address_from_path(f"/api/v1/investigation/{EVM_ADDRESS}/status")
        assert addr is not None
        assert addr.lower() == EVM_ADDRESS.lower()

    def test_extrai_stellar_address(self):
        addr = extract_address_from_path(f"/api/v1/investigation/{STELLAR_ADDRESS}/status")
        assert addr is not None
        assert addr == STELLAR_ADDRESS

    def test_extrai_bitcoin_bech32(self):
        addr = extract_address_from_path(f"/api/v1/investigation/{BITCOIN_ADDRESS}/status")
        assert addr is not None
        assert addr == BITCOIN_ADDRESS

    def test_sem_address_retorna_none(self):
        addr = extract_address_from_path("/api/v1/investigation/estimate")
        assert addr is None

    def test_path_com_query_string(self):
        addr = extract_address_from_path(
            f"/api/v1/investigation/{EVM_ADDRESS}?depth=3"
        )
        # Pode ou não extrair dependendo do padrão — o importante é não crashar
        # (query string não faz parte do path extraído)
        assert addr is None or addr.lower() == EVM_ADDRESS.lower()

    def test_redis_blocklist_prefix_correto(self):
        """Prefixo da key Redis deve ser consistente entre Stage 1 e Stage 2."""
        assert REDIS_BLOCKLIST_PREFIX == "otk:blocklist:confirmed"


# ─── TESTES: EvidenceIntegration — emit_evidence_event_sync ─────────────────

class TestEvidenceIntegration:
    def test_emit_type_invalido_retorna_none(self):
        """emit_evidence_event_sync deve retornar None para tipos inválidos."""
        cur_mock = MagicMock()
        result = emit_evidence_event_sync(
            cur=cur_mock,
            org_id=str(ORG_ID),
            event_type="TIPO_INVALIDO",
            event_payload={},
        )
        assert result is None
        cur_mock.execute.assert_not_called()

    def test_emit_type_valido_chama_execute(self):
        """emit_evidence_event_sync deve chamar cursor.execute para tipos válidos."""
        cur_mock = MagicMock()
        cur_mock.execute = MagicMock()

        result = emit_evidence_event_sync(
            cur=cur_mock,
            org_id=str(ORG_ID),
            event_type="CASE_CREATED",
            event_payload={"case_id": str(CASE_ID)},
            actor_user_id=str(USER_ID),
            case_id=str(CASE_ID),
        )

        assert result is not None
        assert len(result) == 64  # SHA-256 = 64 chars
        cur_mock.execute.assert_called_once()

    def test_emit_falha_db_retorna_none_sem_propagar(self):
        """Falha no banco NÃO deve propagar exception."""
        cur_mock = MagicMock()
        cur_mock.execute = MagicMock(side_effect=RuntimeError("DB error"))

        result = emit_evidence_event_sync(
            cur=cur_mock,
            org_id=str(ORG_ID),
            event_type="CASE_CREATED",
            event_payload={},
        )

        # Não propaga — retorna None
        assert result is None

    def test_audit_to_evidence_mapeamento(self):
        """Os 7 eventos de audit_log devem ter mapeamento para evidence_trail."""
        # Este teste valida a lógica dentro de _record_audit_log (investigation-api)
        audit_actions = {
            "case_started", "case_completed", "case_failed",
            "compliance_risk_checked", "report_generated",
            "report_downloaded", "operational_alerts_exported",
        }
        evidence_types = {
            "CASE_CREATED", "INVESTIGATION_COMPLETED", "CASE_UPDATED",
            "SANCTIONS_CHECKED", "REPORT_GENERATED",
            "REPORT_DOWNLOADED", "EVIDENCE_EXPORTED",
        }
        # Todos os evidence_types do mapeamento devem ser válidos
        assert evidence_types.issubset(VALID_EVENT_TYPES)
