"""
AI Service — ONTRACKCHAIN Graph Intelligence 4.0
Modules: XAI Layer, Graph Narrator, Confidence Engine, Risk Models, THEMIS Agent
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="OnTrackChain AI Service",
    description="Explainable AI, Graph Intelligence 4.0, Case Intelligence",
    version="4.0.0",
)

# ──────────────────────────────────────────────
#  MODELS
# ──────────────────────────────────────────────

class ExplanationRequest(BaseModel):
    case_id: str
    decision_type: str  # risk_score | block_recommendation | sanctions_match
    context: dict[str, Any] = {}


class ExplanationResponse(BaseModel):
    explanation_id: str
    case_id: str
    decision_type: str
    confidence_score: float
    reasoning_steps: list[dict[str, Any]]
    factors: list[dict[str, Any]]
    recommendation: str
    generated_at: str


class GraphAnalysisRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    depth: int = 3
    analysis_type: str = "relationship"


class GraphAnalysisResponse(BaseModel):
    analysis_id: str
    address: str
    chain: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    clusters: list[dict[str, Any]]
    risk_indicators: list[dict[str, Any]]
    generated_at: str


class CaseInsightRequest(BaseModel):
    case_id: str
    include_history: bool = True
    include_recommendations: bool = True


class CaseInsightResponse(BaseModel):
    insight_id: str
    case_id: str
    summary: str
    risk_level: str
    key_findings: list[str]
    recommendations: list[str]
    similar_cases: list[dict[str, Any]]
    generated_at: str


# ── XAI Layer models ──

class RiskModelRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    model_type: str  # pld_ft | sanctions | ransomware | scam | defi | travel_rule
    context: dict[str, Any] = {}


class RiskModelResponse(BaseModel):
    assessment_id: str
    model_type: str
    address: str
    chain: str
    risk_score: float
    risk_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    factors: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    recommendation: str
    confidence: float
    classification: str  # FATO | INFERÊNCIA | HIPÓTESE | RECOMENDAÇÃO
    limitations: list[str]
    generated_at: str


class ConfidenceRequest(BaseModel):
    analysis_id: str
    factors: list[dict[str, Any]] = []


class ConfidenceResponse(BaseModel):
    confidence_id: str
    overall_confidence: float
    uncertainty_factors: list[dict[str, Any]]
    classifications: dict[str, str]
    limitations: list[str]
    generated_at: str


class NarratorRequest(BaseModel):
    address: str
    chain: str = "ethereum"
    graph_data: dict[str, Any] = {}
    profile: str = "analyst"  # analyst | legal | executive


class NarratorResponse(BaseModel):
    narrative_id: str
    address: str
    chain: str
    narrative: str
    profile: str
    risk_badges: list[dict[str, Any]]
    smart_annotations: list[dict[str, Any]]
    suggested_actions: list[str]
    generated_at: str


class LawEnforcementExportRequest(BaseModel):
    case_id: str
    format: str = "coaf"  # coaf | vasp | judicial | fatf
    include_evidence_hash: bool = True


class LawEnforcementExportResponse(BaseModel):
    export_id: str
    case_id: str
    format: str
    document: dict[str, Any]
    evidence_chain: list[dict[str, Any]]
    generated_at: str


class THEMISRequest(BaseModel):
    case_id: str
    address: str
    chain: str = "ethereum"
    action: str  # build | narrate | export | review | full


class THEMISResponse(BaseModel):
    themis_id: str
    case_id: str
    case_card: dict[str, Any]
    graph_narrative: dict[str, Any]
    risk_assessment: dict[str, Any]
    law_enforcement_package: dict[str, Any]
    human_gate_required: bool
    generated_at: str


# ──────────────────────────────────────────────
#  HEALTH
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-service", "version": "4.0.0"}


# ──────────────────────────────────────────────
#  MODULE 2 — XAI LAYER
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/explain", response_model=ExplanationResponse)
async def explain_decision(
    request: ExplanationRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> ExplanationResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    explanation = _generate_explanation(request)
    return ExplanationResponse(
        explanation_id=str(uuid.uuid4()),
        case_id=request.case_id,
        decision_type=request.decision_type,
        confidence_score=explanation["confidence"],
        reasoning_steps=explanation["steps"],
        factors=explanation["factors"],
        recommendation=explanation["recommendation"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/risk-model", response_model=RiskModelResponse)
async def risk_model_assessment(
    request: RiskModelRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> RiskModelResponse:
    """Avaliação de risco por modelo regulatório (PLD/FT, Sanções, Ransomware, etc.)"""
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    result = _run_risk_model(request)
    return RiskModelResponse(
        assessment_id=str(uuid.uuid4()),
        model_type=request.model_type,
        address=request.address,
        chain=request.chain,
        risk_score=result["score"],
        risk_level=result["level"],
        factors=result["factors"],
        evidence=result["evidence"],
        recommendation=result["recommendation"],
        confidence=result["confidence"],
        classification=result["classification"],
        limitations=result["limitations"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/confidence", response_model=ConfidenceResponse)
async def confidence_engine(
    request: ConfidenceRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
) -> ConfidenceResponse:
    """Engine de confiança — distingue FATO / INFERÊNCIA / HIPÓTESE / RECOMENDAÇÃO"""
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    result = _compute_confidence(request)
    return ConfidenceResponse(
        confidence_id=str(uuid.uuid4()),
        overall_confidence=result["overall"],
        uncertainty_factors=result["uncertainty"],
        classifications=result["classifications"],
        limitations=result["limitations"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  MODULE 1 — CASE MANAGEMENT HUB
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/case-insights", response_model=CaseInsightResponse)
async def get_case_insights(
    request: CaseInsightRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> CaseInsightResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    insights = _generate_case_insights(request)
    return CaseInsightResponse(
        insight_id=str(uuid.uuid4()),
        case_id=request.case_id,
        summary=insights["summary"],
        risk_level=insights["risk_level"],
        key_findings=insights["findings"],
        recommendations=insights["recommendations"],
        similar_cases=insights["similar_cases"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  MODULE 3 — GRAPH NARRATOR ENGINE
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/graph-analysis", response_model=GraphAnalysisResponse)
async def analyze_graph(
    request: GraphAnalysisRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> GraphAnalysisResponse:
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    analysis = _generate_graph_analysis(request)
    return GraphAnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        address=request.address,
        chain=request.chain,
        nodes=analysis["nodes"],
        edges=analysis["edges"],
        clusters=analysis["clusters"],
        risk_indicators=analysis["risk_indicators"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/ai/graph-narrator", response_model=NarratorResponse)
async def graph_narrator(
    request: NarratorRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> NarratorResponse:
    """Narração automática do grafo blockchain em linguagem natural"""
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    result = _narrate_graph(request)
    return NarratorResponse(
        narrative_id=str(uuid.uuid4()),
        address=request.address,
        chain=request.chain,
        narrative=result["narrative"],
        profile=request.profile,
        risk_badges=result["badges"],
        smart_annotations=result["annotations"],
        suggested_actions=result["actions"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  LAW ENFORCEMENT EXPORT
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/law-enforcement-export", response_model=LawEnforcementExportResponse)
async def law_enforcement_export(
    request: LawEnforcementExportRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> LawEnforcementExportResponse:
    """Exportação formatada para COAF / VASP / Judiciário / FATF"""
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    result = _generate_law_enforcement_package(request)
    return LawEnforcementExportResponse(
        export_id=str(uuid.uuid4()),
        case_id=request.case_id,
        format=request.format,
        document=result["document"],
        evidence_chain=result["evidence_chain"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ──────────────────────────────────────────────
#  THEMIS — CASE INTELLIGENCE AGENT
# ──────────────────────────────────────────────

@app.post("/api/v1/ai/themis", response_model=THEMISResponse)
async def themis_case_intelligence(
    request: THEMISRequest,
    x_org_id: Optional[str] = Header(default=None, alias="X-Org-Id"),
    x_role: Optional[str] = Header(default=None, alias="X-Role"),
) -> THEMISResponse:
    """THEMIS — Case Intelligence Agent: orquestra todos os módulos de IA"""
    if not x_org_id:
        raise HTTPException(status_code=400, detail="X-Org-Id required")
    result = _run_themis(request)
    return THEMISResponse(
        themis_id=str(uuid.uuid4()),
        case_id=request.case_id,
        case_card=result["case_card"],
        graph_narrative=result["graph_narrative"],
        risk_assessment=result["risk_assessment"],
        law_enforcement_package=result["law_enforcement"],
        human_gate_required=result["human_gate"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ══════════════════════════════════════════════
#  INTERNAL ENGINES
# ══════════════════════════════════════════════

def _generate_explanation(request: ExplanationRequest) -> dict[str, Any]:
    ctx = request.context
    if request.decision_type == "risk_score":
        return {
            "confidence": 0.87,
            "steps": [
                {"step": 1, "action": "Análise de histórico transacional", "result": f"{ctx.get('tx_count', 150)} transações nos últimos 30 dias"},
                {"step": 2, "action": "Verificação em listas de sanções", "result": "Nenhuma correspondência direta encontrada"},
                {"step": 3, "action": "Avaliação de indicadores de risco", "result": "Risco médio por volume elevado e exposição a mixers"},
                {"step": 4, "action": "Análise de padrão comportamental", "result": "Desvio do perfil esperado detectado"},
                {"step": 5, "action": "Cálculo do score final", "result": f"Risk score: {ctx.get('score', 67)}/100"},
            ],
            "factors": [
                {"factor": "Volume Transacional", "weight": 0.25, "impact": "high", "detail": "Acima do percentil 80 para o perfil"},
                {"factor": "Exposição a Mixer", "weight": 0.30, "impact": "high", "detail": "3 transações via Tornado Cash"},
                {"factor": "Correspondência Sanções", "weight": 0.20, "impact": "none", "detail": "Sem match em OFAC/ONU/COAF"},
                {"factor": "Padrão Comportamental", "weight": 0.15, "impact": "medium", "detail": "Horários atípicos detectados"},
                {"factor": "Rede de Contrapartes", "weight": 0.10, "impact": "medium", "detail": "2 contrapartes de risco médio"},
            ],
            "recommendation": "REVISÃO — Revisão manual recomendada devido ao volume elevado e exposição a mixers",
        }
    elif request.decision_type == "block_recommendation":
        return {
            "confidence": 0.93,
            "steps": [
                {"step": 1, "action": "Verificação de status da contraparte", "result": "Contraparte ativa com histórico"},
                {"step": 2, "action": "Avaliação de score de risco", "result": "Risk score: 78/100"},
                {"step": 3, "action": "Verificação de regras de compliance", "result": "Violação de regra detectada: exposição a endereço sancionado"},
                {"step": 4, "action": "Verificação de PEP", "result": "Nenhum PEP identificado"},
                {"step": 5, "action": "Geração de recomendação", "result": "BLOQUEIO recomendado"},
            ],
            "factors": [
                {"factor": "Score de Risco", "weight": 0.40, "impact": "high", "detail": "78/100 — acima do limiar de bloqueio"},
                {"factor": "Regras de Compliance", "weight": 0.35, "impact": "high", "detail": "Exposição a endereço da lista OFAC SDN"},
                {"factor": "Padrão Histórico", "weight": 0.15, "impact": "medium", "detail": "Mudança recente de comportamento"},
                {"factor": "Conexão com Entidade de Risco", "weight": 0.10, "impact": "high", "detail": "Vínculo com cluster de risco"},
            ],
            "recommendation": "BLOQUEAR — Bloqueio imediato recomendado por violação de compliance com exposição a endereço sancionado",
        }
    else:
        return {
            "confidence": 0.79,
            "steps": [
                {"step": 1, "action": "Análise de correspondência em sanções", "result": "Possível match parcial encontrado"},
                {"step": 2, "action": "Verificação de identidade", "result": "Verificação de identidade pendente"},
                {"step": 3, "action": "Análise de endereços vinculados", "result": "3 endereços associados sob investigação"},
                {"step": 4, "action": "Geração de recomendação", "result": "INVESTIGAR recomendado"},
            ],
            "factors": [
                {"factor": "Match em Sanções", "weight": 0.50, "impact": "high", "detail": "Match parcial — 85% similaridade"},
                {"factor": "Verificação de Identidade", "weight": 0.30, "impact": "medium", "detail": "KYC pendente"},
                {"factor": "Rede de Endereços", "weight": 0.20, "impact": "medium", "detail": "3 endereços vinculados"},
            ],
            "recommendation": "INVESTIGAR — Investigação adicional necessária devido a possível correspondência parcial com lista de sanções",
        }


def _run_risk_model(request: RiskModelRequest) -> dict[str, Any]:
    models = {
        "pld_ft": {
            "score": 72.0, "level": "HIGH",
            "factors": [
                {"factor": "Operação com País de Alto Risco", "weight": 0.25, "impact": "high", "detail": "Transações com jurisdição FATF grey list"},
                {"factor": "Estrutura Societária Opaca", "weight": 0.20, "impact": "high", "detail": "Beneficiário final não identificado"},
                {"factor": "Volume Incompatível", "weight": 0.20, "impact": "medium", "detail": "Volume 5x acima do perfil declarado"},
                {"factor": "Padrão de Layering", "weight": 0.25, "impact": "high", "detail": "Múltiplas transferências fracionadas"},
                {"factor": "Ausência de Due Diligence", "weight": 0.10, "impact": "medium", "detail": "KYC desatualizado"},
            ],
            "evidence": [
                {"type": "transaction_pattern", "description": "15 transferências fracionadas em 48h", "hash": "0xabc...def"},
                {"type": "jurisdiction", "description": "Contraparte registrada em jurisdição FATF grey list", "source": "offshore-registry"},
            ],
            "recommendation": "DECLARAR — Recomenda-se declaração de operação suspeita ao COAF conforme Circular 3.978",
            "confidence": 0.82, "classification": "INFERÊNCIA",
            "limitations": ["Dados limitados sobre beneficiário final", "Horizonte temporal de 30 dias insuficiente para padrão completo"],
        },
        "ransomware": {
            "score": 85.0, "level": "CRITICAL",
            "factors": [
                {"factor": "Endereço Único de Recebimento", "weight": 0.30, "impact": "high", "detail": "Pattern típico de carteira de resgate"},
                {"factor": "Valores Redondos", "weight": 0.20, "impact": "high", "detail": "Pagamentos em valores exatos (2.5 ETH, 5.0 ETH)"},
                {"factor": "Mixers/Privacy Coins", "weight": 0.25, "impact": "high", "detail": "Uso de Tornado Cash para obfuscação"},
                {"factor": "Velocidade de Movimentação", "weight": 0.15, "impact": "medium", "detail": "Funds movidos em < 2 horas após recebimento"},
                {"factor": "Conexões Conhecidas", "weight": 0.10, "impact": "high", "detail": "Vinculado a cluster identificado como ransomware"},
            ],
            "evidence": [
                {"type": "address_cluster", "description": "Endereço vinculado a cluster de ransomware conhecido", "source": "threat-intel"},
                {"type": "transaction_pattern", "description": "8 pagamentos de resgate nos últimos 14 dias", "hash": "0x123...789"},
            ],
            "recommendation": "BLOQUEAR E REPORTAR — Bloqueio imediato e reporte ao CERT/COAF conforme protocolo de ransomware",
            "confidence": 0.91, "classification": "FATO",
            "limitations": ["Identificação da vítima pendente", "Confirmação do tipo de ransomware em andamento"],
        },
        "scam": {
            "score": 68.0, "level": "HIGH",
            "factors": [
                {"factor": "Contrato Não Verificado", "weight": 0.25, "impact": "high", "detail": "Smart contract sem código verificado"},
                {"factor": "Promessas de Retorno Alto", "weight": 0.20, "impact": "high", "detail": "ROI prometido > 500% ao mês"},
                {"factor": "Pressa Artificial", "weight": 0.15, "impact": "medium", "detail": "Contagem regressiva para criar urgência"},
                {"factor": "Redes Sociais Falsas", "weight": 0.25, "impact": "high", "detail": "Perfis verificados artificialmente"},
                {"factor": "Histórico de Rug Pull", "weight": 0.15, "impact": "high", "detail": "Deployer vinculado a projeto encerrado"},
            ],
            "evidence": [
                {"type": "contract_analysis", "description": "Função de withdraw bloqueada por owner", "source": "on-chain-analysis"},
                {"type": "social_analysis", "description": "Campanha de marketing com bots detectada", "source": "osint"},
            ],
            "recommendation": "ALERTAR — Alerta preventivo para clientes sobre possibilidade de fraude tipo rug pull",
            "confidence": 0.75, "classification": "HIPÓTESE",
            "limitations": ["Contrato ainda ativo — não há confirmação de rug pull", "Investigação depende de cooperação da exchange"],
        },
        "defi": {
            "score": 55.0, "level": "MEDIUM",
            "factors": [
                {"factor": "Entrada/Saída Rápida em Pool", "weight": 0.30, "impact": "high", "detail": "Sandwich attack pattern detectado"},
                {"factor": "Flash Loan Usage", "weight": 0.25, "impact": "medium", "detail": "Uso de flash loans para manipulação"},
                {"factor": "Impermanent Loss Pattern", "weight": 0.15, "impact": "low", "detail": "Padrão compatível com farming ordinário"},
                {"factor": "MEV Extraction", "weight": 0.20, "impact": "medium", "detail": "Extração de valor máximalista detectada"},
                {"factor": "Conexão com Protocólos", "weight": 0.10, "impact": "low", "detail": "Protocolos verificados e auditados"},
            ],
            "evidence": [
                {"type": "defi_interaction", "description": "3 transações de sandwich attack em Uniswap V3", "hash": "0xdef...456"},
            ],
            "recommendation": "MONITORAR — Atividade suspeita mas compatível com operações DeFi avançadas; monitorar por 30 dias",
            "confidence": 0.68, "classification": "INFERÊNCIA",
            "limitations": ["Dificuldade em distinguir MEV legítimo de manipulação", "Necessário contexto adicional sobre a instituição"],
        },
        "sanctions": {
            "score": 95.0, "level": "CRITICAL",
            "factors": [
                {"factor": "Match OFAC SDN", "weight": 0.40, "impact": "high", "detail": "Correspondência direta com lista SDN"},
                {"factor": "Match ONU", "weight": 0.25, "impact": "high", "detail": "Listado na Resolução 1267"},
                {"factor": "Match COAF", "weight": 0.20, "impact": "high", "detail": "Listado na portaria COAF"},
                {"factor": "PEP Association", "weight": 0.10, "impact": "high", "detail": "Vinculado a PEP sancionado"},
                {"factor": "Jurisdiction Risk", "weight": 0.05, "impact": "high", "detail": "País sob embargo"},
            ],
            "evidence": [
                {"type": "sanctions_match", "description": "Match direto OFAC SDN — confidence 99.2%", "source": "OFAC SDN List"},
                {"type": "sanctions_match", "description": "Match ONU Resolução 1267 — confidence 97.8%", "source": "UN Sanctions List"},
            ],
            "recommendation": "BLOQUEAR E REPORTAR — Bloqueio imediato obrigatório. Reporte ao COAF em até 24h conforme Res. 520/BCB",
            "confidence": 0.97, "classification": "FATO",
            "limitations": [],
        },
        "travel_rule": {
            "score": 42.0, "level": "MEDIUM",
            "factors": [
                {"factor": "Dados do Originador Ausentes", "weight": 0.35, "impact": "high", "detail": "Nome e CPF/CNPJ não informados"},
                {"factor": "Dados do Beneficiário Incompletos", "weight": 0.25, "impact": "medium", "detail": "Conta bancária parcialmente informada"},
                {"factor": "Valor Acima do Limite", "weight": 0.25, "impact": "high", "detail": "Transferência > R$ 1.000 — Travel Rule obrigatório"},
                {"factor": "VASP Receptor Não Verificado", "weight": 0.15, "impact": "medium", "detail": "VASP receptor sem certificação Travel Rule"},
            ],
            "evidence": [
                {"type": "travel_rule_check", "description": "Transferência de 2.5 ETH sem dados completos do originador", "source": "compliance-engine"},
            ],
            "recommendation": "INCOMPLETO — Solicitar dados completos do originador e beneficiário antes de processar a transferência",
            "confidence": 0.85, "classification": "FATO",
            "limitations": ["VASP receptor pode não suportar Travel Rule", "Dados podem estar em processo de coleta"],
        },
    }
    return models.get(request.model_type, models["pld_ft"])


def _compute_confidence(request: ConfidenceRequest) -> dict[str, Any]:
    factors = request.factors
    if not factors:
        factors = [
            {"type": "FATO", "count": 5, "reliability": 0.95},
            {"type": "INFERÊNCIA", "count": 3, "reliability": 0.72},
            {"type": "HIPÓTESE", "count": 2, "reliability": 0.45},
            {"type": "RECOMENDAÇÃO", "count": 2, "reliability": 0.80},
        ]
    total = sum(f.get("count", 1) for f in factors)
    weighted = sum(f.get("count", 1) * f.get("reliability", 0.5) for f in factors)
    overall = round(weighted / total, 2) if total else 0.5
    return {
        "overall": overall,
        "uncertainty": [
            {"factor": "Disponibilidade de dados on-chain", "impact": "medium", "detail": "Dados limitados a transações públicas"},
            {"factor": "Horizonte temporal", "impact": "low", "detail": "Análise baseada nos últimos 90 dias"},
            {"factor": "Qualidade do KYC", "impact": "medium", "detail": "Dados de identidade dependem de cooperação da exchange"},
        ],
        "classifications": {
            "FATO": "Dados verificados diretamente na blockchain ou em listas oficiais",
            "INFERÊNCIA": "Conclusão derivada de padrões observados com probabilidade > 70%",
            "HIPÓTESE": "Suspeita que requer investigação adicional para confirmação",
            "RECOMENDAÇÃO": "Ação sugerida com base na análise, sujeita a aprovação humana",
        },
        "limitations": [
            "Análise limitada a dados públicos da blockchain",
            "Identidade real por trás dos endereços não verificada",
            "Scores baseados em padrões históricos — podem não capturar comportamento novo",
        ],
    }


def _generate_graph_analysis(request: GraphAnalysisRequest) -> dict[str, Any]:
    addr = request.address[:10] + "..."
    nodes = [
        {"id": request.address, "type": "source", "label": "Endereço Alvo", "risk": "medium", "balance": "12.5 ETH", "tx_count": 342},
        {"id": "0x1234...5678", "type": "exchange", "label": "Binance Hot Wallet", "risk": "low", "balance": "15,420 ETH", "tx_count": 89234},
        {"id": "0x8765...4321", "type": "mixer", "label": "Tornado Cash Pool", "risk": "high", "balance": "0 ETH", "tx_count": 15234},
        {"id": "0xabcd...ef01", "type": "defi", "label": "Uniswap V3 Router", "risk": "low", "balance": "0 ETH", "tx_count": 234567},
        {"id": "0xdead...beef", "type": "suspicious", "label": "Endereço Suspeito", "risk": "critical", "balance": "0.5 ETH", "tx_count": 89},
    ]
    edges = [
        {"source": request.address, "target": "0x1234...5678", "type": "transfer", "amount": 5.2, "count": 12, "first_seen": "2026-01-15", "last_seen": "2026-07-20"},
        {"source": request.address, "target": "0x8765...4321", "type": "mixer", "amount": 15.8, "count": 3, "first_seen": "2026-03-01", "last_seen": "2026-06-15"},
        {"source": "0x8765...4321", "target": "0xdead...beef", "type": "transfer", "amount": 22.5, "count": 8, "first_seen": "2026-02-10", "last_seen": "2026-07-18"},
        {"source": request.address, "target": "0xabcd...ef01", "type": "swap", "amount": 3.1, "count": 5, "first_seen": "2026-04-20", "last_seen": "2026-07-22"},
    ]
    clusters = [
        {"id": "cluster_1", "nodes": [request.address, "0x1234...5678"], "risk": "medium", "label": "Cluster Primário", "volume": "58.2 ETH"},
        {"id": "cluster_2", "nodes": ["0x8765...4321", "0xdead...beef"], "risk": "critical", "label": "Cluster de Risco", "volume": "22.5 ETH"},
        {"id": "cluster_3", "nodes": [request.address, "0xabcd...ef01"], "risk": "low", "label": "Cluster DeFi", "volume": "3.1 ETH"},
    ]
    risk_indicators = [
        {"indicator": "Exposição a Mixer (Tornado Cash)", "severity": "high", "confidence": 0.92, "detail": "3 transações via mixer nos últimos 90 dias"},
        {"indicator": "Conexão com Endereço de Risco", "severity": "critical", "confidence": 0.88, "detail": "Vínculo indireto com cluster classificado como ransomware"},
        {"indicator": "Movimentação Rápida de Fundos", "severity": "medium", "confidence": 0.75, "detail": "Funds recebidos e movidos em < 2 horas"},
        {"indicator": "Volume Incompatível com Perfil", "severity": "medium", "confidence": 0.68, "detail": "Volume 3x acima do esperado para carteira declarada"},
    ]
    return {"nodes": nodes, "edges": edges, "clusters": clusters, "risk_indicators": risk_indicators}


def _narrate_graph(request: NarratorRequest) -> dict[str, Any]:
    profiles = {
        "analyst": {
            "narrative": (
                f"O endereço {request.address[:10]}... apresenta um padrão de movimentação "
                f"que merece atenção. Nos últimos 90 dias, foram identificadas 15 transações "
                f"de saída, das quais 3 passaram por um mixer (Tornado Cash), totalizando "
                f"15.8 ETH. O endereço manteve interação regular com a Binance (12 depósitos, "
                f"5.2 ETH total) e realizou 5 swaps no Uniswap V3. O score de risco calculado "
                f"é de 67/100, classificado como MÉDIO. A principal preocupação é a exposição "
                f"ao mixer e a conexão indireta com um endereço vinculado a atividades suspeitas."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "Exposição Mixer", "color": "danger", "detail": "Tornado Cash"},
                {"label": "Exchange Ativa", "color": "success", "detail": "Binance"},
            ],
            "annotations": [
                {"node": request.address, "text": "Score 67/100 — padrão comportamental desviante detectado"},
                {"node": "0x8765...4321", "text": "Tornado Cash Pool — mixer de privacidade classificado como high-risk"},
                {"node": "0xdead...beef", "text": "Endereço vinculado a cluster de ransomware — investigação em andamento"},
            ],
            "actions": [
                "Verificar provedor de identidade desta wallet",
                "Solicitar documentação de origem dos fundos",
                "Monitorar por 30 dias com alertas de novo depósito via mixer",
            ],
        },
        "legal": {
            "narrative": (
                f"O endereço {request.address[:10]}... foi submetido a análise de compliance "
                f"conforme Circular 3.978 do BCB e Resolução 520/2022. A análise identificou "
                f"movimentação compatível com tentativa de obfuscação de origem de recursos, "
                f"por meio de utilização de mixer de privacidade. Conforme art. 11 da Res. 520, "
                f"a instituição deve avaliar se a operação apresenta indícios de lavagem de "
                f"dinheiro ou financiamento do terrorismo. O score de risco de 67/100 indica "
                f"necessidade de due diligence reforçada. Recomenda-se a abertura de "
                f"comunicação de operação suspeita ao COAF conforme art. 9 da Lei 9.613/98."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "PLD/FT Aplicável", "color": "danger", "detail": "Circular 3.978"},
                {"label": "Due Diligence Reforçada", "color": "warning", "detail": "Obrigatória"},
            ],
            "annotations": [
                {"node": request.address, "text": "Indício de obfuscação — art. 11 Res. 520/2022"},
                {"node": "0x8765...4321", "text": "Uso de mixer configura indício de lavagem"},
            ],
            "actions": [
                "Solicitar origem documentada dos fundos ao cliente",
                "Avaliar necessidade de declaração de ops suspeita ao COAF",
                "Documentar toda a cadeia de evidências para cadeia de custódia",
            ],
        },
        "executive": {
            "narrative": (
                f"Carteira analisada: risco MÉDIO (67/100). A carteira interage com exchanges "
                f"legítimas mas utiliza mixer de privacidade, o que gera risco regulatório. "
                f"Recomendação: due diligence reforçada antes de permitir novas operações. "
                f"Potencial impacto regulatório: MÉDIO. Nenhuma ação imediata de bloqueio "
                f"necessária, mas monitoramento contínuo é mandatório."
            ),
            "badges": [
                {"label": "Risco Médio", "color": "warning", "score": 67},
                {"label": "Ação: Monitorar", "color": "info"},
            ],
            "annotations": [],
            "actions": [
                "Aprovar due diligence reforçada",
                "Definir alerta para novas transações via mixer",
            ],
        },
    }
    return profiles.get(request.profile, profiles["analyst"])


def _generate_case_insights(request: CaseInsightRequest) -> dict[str, Any]:
    return {
        "summary": f"Caso {request.case_id} envolve risco de compliance com múltiplos indicadores que requerem atenção. Análise XAI identificou 4 fatores de risco, 2 inferências e 1 hipótese pendente de confirmação.",
        "risk_level": "HIGH",
        "findings": [
            "Padrão transacional com desvio significativo detectado nos últimos 7 dias",
            "Vinculação com 2 contrapartes classificadas como high-risk identificada",
            "Screening de sanções retornou correspondências parciais que requerem verificação",
            "Análise comportamental indica desvio de 2.3 desvios-padrão do perfil declarado",
            "Score de confiança: 87% — classificação: INFERÊNCIA",
        ],
        "recommendations": [
            "Escalar para officer de compliance sênior para revisão",
            "Solicitar documentação complementar de origem dos fundos ao contraparte",
            "Monitorar conta por 30 dias com vigilância reforçada",
            "Considerar declaração de operação suspeita ao COAF conforme Circular 3.978",
            "Documentar cadeia de evidências no ARQUIVO para cadeia de custódia",
        ],
        "similar_cases": [
            {"case_id": "CASE-2026-0156", "similarity": 0.84, "outcome": "BLOQUEADO", "reason": "Mesmo padrão de mixer + exchange"},
            {"case_id": "CASE-2026-0089", "similarity": 0.76, "outcome": "INVESTIGADO", "reason": "Exposição similar a Tornado Cash"},
            {"case_id": "CASE-2026-0234", "similarity": 0.69, "outcome": "LIMPO", "reason": "Mixer usage com justificativa legítima"},
            {"case_id": "CASE-2026-0312", "similarity": 0.62, "outcome": "REPORTADO", "reason": "Declaração COAF por layering"},
        ],
    }


def _generate_law_enforcement_package(request: LawEnforcementExportRequest) -> dict[str, Any]:
    formats = {
        "coaf": {
            "document": {
                "type": "Comunicação de Operação Suspeita",
                "authority": "COAF",
                "legal_basis": "Lei 9.613/98, Art. 9; Res. 520/2022",
                "institution": "Instituição Financeira Cadastrada",
                "case_reference": request.case_id,
                "sections": {
                    "identificacao": {
                        "instituicao": "[RAZÃO SOCIAL]",
                        "cnpj": "[CNPJ]",
                        "responsavel": "[NOME DO RESPONSÁVEL]",
                        "cargo": "[CARGO]",
                        "contato": "[TELEFONE/EMAIL]",
                    },
                    "dados_da_operacao": {
                        "tipo": "Transferência de ativos virtuais",
                        "valor": "15.8 ETH (~R$ 285.000,00)",
                        "data_inicio": "2026-03-01",
                        "data_fim": "2026-07-20",
                        "partes_envolvidas": [
                            {"endereco": request.case_id, "tipo": " originador"},
                            {"endereco": "0x8765...4321", "tipo": "destinatário"},
                        ],
                    },
                    "motivo_suspeita": [
                        "Utilização de mixer de privacidade (Tornado Cash)",
                        "Movimentação rápida de fundos (< 2 horas)",
                        "Vinculação com endereço classificado como ransomware",
                        "Volume incompatível com perfil declarado",
                    ],
                    "classificacao_tipologia": "Lavagem de dinheiro via obfuscação em blockchain",
                    "normas_aplicaveis": [
                        "Circular 3.978/2019 (PLD/FT)",
                        "Resolução 520/2022 (Regulamento PLD/FT)",
                        "Resolução 521/2022 (Procedimentos)",
                        "Resolução 739/2023 (Ativos Virtuais)",
                    ],
                },
            },
            "evidence_chain": [
                {"item": "Captura de tela da transação", "hash": "sha256:abc123...", "timestamp": "2026-07-24T10:00:00Z"},
                {"item": "Exportação JSON do grafo", "hash": "sha256:def456...", "timestamp": "2026-07-24T10:01:00Z"},
                {"item": "Relatório XAI completo", "hash": "sha256:ghi789...", "timestamp": "2026-07-24T10:02:00Z"},
            ],
        },
        "vasp": {
            "document": {
                "type": "Ofício para VASP/Exchange",
                "recipient": "[NOME DA EXCHANGE]",
                "legal_basis": "Res. 739/2023, Art. 12; Travel Rule",
                "sections": {
                    "solicitacao": "Solicitação de informações sobre titular da conta",
                    "endereco_suspeito": "0x8765...4321",
                    "motivo": "Vinculação com atividade suspeita identificada",
                    "informacoes_solicitadas": [
                        "Nome completo do titular",
                        "CPF/CNPJ",
                        "Data de abertura da conta",
                        "Histórico de transações dos últimos 90 dias",
                        "Documentação de KYC",
                    ],
                    "prazo_resposta": "15 dias úteis",
                },
            },
            "evidence_chain": [],
        },
        "judicial": {
            "document": {
                "type": "Relatório Técnico para Autoridade Judiciária",
                "authority": "Delegacia / Ministério Público",
                "legal_basis": "Lei 9.613/98; CPP Art. 13",
                "sections": {
                    "objeto": "Relatório técnico de análise forense de ativos virtuais",
                    "metodologia": "Análise on-chain com Graph Intelligence 4.0 e XAI Layer",
                    "conclusao_tecnica": "Identificada movimentação compatível com lavagem de dinheiro via obfuscação em mixer de privacidade",
                    "cadeia_custodia": "Todas as evidências havebeen hasheadas e versionadas conforme protocolo ARQUIVO",
                },
            },
            "evidence_chain": [],
        },
        "fatf": {
            "document": {
                "type": "Relatório FATF/GAFILAT",
                "standard": "Recomendação 15 (Novas Tecnologias) e 20 (Relatórios de Transações Suspeitas)",
                "sections": {
                    "typology": "Abuse of Decentralized Mixers for ML/TF",
                    "red_flags": [
                        "Use of privacy-enhancing technologies",
                        "Rapid movement of funds through multiple addresses",
                        "Connection to known illicit addresses",
                    ],
                    "jurisdictional_notes": "Brazil — BCB Circular 3.978, Res. 520/2022, Res. 739/2023",
                },
            },
            "evidence_chain": [],
        },
    }
    return formats.get(request.format, formats["coaf"])


def _run_themis(request: THEMISRequest) -> dict[str, Any]:
    risk_result = _run_risk_model(RiskModelRequest(address=request.address, chain=request.chain, model_type="pld_ft"))
    graph = _generate_graph_analysis(GraphAnalysisRequest(address=request.address, chain=request.chain))
    narrator = _narrate_graph(NarratorRequest(address=request.address, chain=request.chain, profile="analyst"))
    le_export = _generate_law_enforcement_package(LawEnforcementExportRequest(case_id=request.case_id, format="coaf"))
    human_gate = risk_result["score"] > 70 or risk_result["level"] in ("HIGH", "CRITICAL")
    return {
        "case_card": {
            "case_id": request.case_id,
            "origin_agent": "THEMIS — Case Intelligence Agent",
            "wallets_linked": [request.address],
            "risk_score": risk_result["score"],
            "risk_level": risk_result["level"],
            "typology": risk_result["factors"][0]["factor"] if risk_result["factors"] else "N/A",
            "status": "open",
            "responsible": "auto-assigned by THEMIS",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "graph_narrative": {
            "narrative": narrator["narrative"],
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "clusters": len(graph["clusters"]),
            "risk_indicators": len(graph["risk_indicators"]),
        },
        "risk_assessment": {
            "model": "PLD/FT (Circular 3.978 + Res. 520)",
            "score": risk_result["score"],
            "level": risk_result["level"],
            "confidence": risk_result["confidence"],
            "classification": risk_result["classification"],
            "factors": risk_result["factors"],
            "recommendation": risk_result["recommendation"],
        },
        "law_enforcement": {
            "format": "coaf",
            "document_type": le_export["document"]["type"],
            "evidence_count": len(le_export["evidence_chain"]),
        },
        "human_gate": human_gate,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
