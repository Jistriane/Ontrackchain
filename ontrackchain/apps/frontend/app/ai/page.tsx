"use client";

import { useState } from "react";
import { useI18n } from "../../components/i18n-provider";
import { AuthShell, Panel, Pill } from "../../components/ui";

type ExplanationResult = {
  explanation_id: string;
  case_id: string;
  decision_type: string;
  confidence_score: number;
  reasoning_steps: Array<{ step: number; action: string; result: string }>;
  factors: Array<{ factor: string; weight: number; impact: string; detail?: string }>;
  recommendation: string;
  generated_at: string;
};

type RiskModelResult = {
  assessment_id: string;
  model_type: string;
  address: string;
  chain: string;
  risk_score: number;
  risk_level: string;
  factors: Array<{ factor: string; weight: number; impact: string; detail: string }>;
  evidence: Array<{ type: string; description: string; hash?: string; source?: string }>;
  recommendation: string;
  confidence: number;
  classification: string;
  limitations: string[];
  generated_at: string;
};

type ConfidenceResult = {
  confidence_id: string;
  overall_confidence: number;
  uncertainty_factors: Array<{ factor: string; impact: string; detail: string }>;
  classifications: Record<string, string>;
  limitations: string[];
  generated_at: string;
};

type GraphResult = {
  analysis_id: string;
  address: string;
  chain: string;
  nodes: Array<{ id: string; type: string; label: string; risk: string; balance?: string; tx_count?: number }>;
  edges: Array<{ source: string; target: string; type: string; amount: number; count: number }>;
  clusters: Array<{ id: string; nodes: string[]; risk: string; label: string; volume?: string }>;
  risk_indicators: Array<{ indicator: string; severity: string; confidence: number; detail: string }>;
  generated_at: string;
};

type NarratorResult = {
  narrative_id: string;
  address: string;
  chain: string;
  narrative: string;
  profile: string;
  risk_badges: Array<{ label: string; color: string; score?: number; detail?: string }>;
  smart_annotations: Array<{ node: string; text: string }>;
  suggested_actions: string[];
  generated_at: string;
};

type CaseInsightResult = {
  insight_id: string;
  case_id: string;
  summary: string;
  risk_level: string;
  key_findings: string[];
  recommendations: string[];
  similar_cases: Array<{ case_id: string; similarity: number; outcome: string }>;
  generated_at: string;
};

type LEExportResult = {
  export_id: string;
  case_id: string;
  format: string;
  document: Record<string, any>;
  evidence_chain: Array<{ item: string; hash: string; timestamp: string }>;
  generated_at: string;
};

type THEMISResult = {
  themis_id: string;
  case_id: string;
  case_card: Record<string, any>;
  graph_narrative: Record<string, any>;
  risk_assessment: Record<string, any>;
  law_enforcement_package: Record<string, any>;
  human_gate_required: boolean;
  generated_at: string;
};

type Tab = "explain" | "risk-model" | "confidence" | "graph" | "narrator" | "insights" | "law-enforcement" | "themis";

const RISK_MODELS = [
  { value: "pld_ft", label: "PLD/FT (Circular 3.978)" },
  { value: "sanctions", label: "Sanções (OFAC/ONU/COAF)" },
  { value: "ransomware", label: "Ransomware" },
  { value: "scam", label: "Scam / Fraude" },
  { value: "defi", label: "Exposição DeFi" },
  { value: "travel_rule", label: "Travel Rule" },
];

const LE_FORMATS = [
  { value: "coaf", label: "COAF — Comunicação de Operação Suspeita" },
  { value: "vasp", label: "VASP — Ofício para Exchange" },
  { value: "judicial", label: "Judicial — Relatório Técnico" },
  { value: "fatf", label: "FATF/GAFILAT — Relatório Internacional" },
];

function toneForLevel(level: string): "danger" | "warning" | "success" {
  if (level === "CRITICAL" || level === "HIGH") return "danger";
  if (level === "MEDIUM") return "warning";
  return "success";
}

export default function AIPage() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<Tab>("explain");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Shared inputs
  const [caseId, setCaseId] = useState("");
  const [address, setAddress] = useState("");
  const [chain, setChain] = useState("ethereum");

  // Explain
  const [decisionType, setDecisionType] = useState("risk_score");
  const [explainResult, setExplainResult] = useState<ExplanationResult | null>(null);

  // Risk Model
  const [riskModelType, setRiskModelType] = useState("pld_ft");
  const [riskModelResult, setRiskModelResult] = useState<RiskModelResult | null>(null);

  // Confidence
  const [confidenceResult, setConfidenceResult] = useState<ConfidenceResult | null>(null);

  // Graph
  const [graphResult, setGraphResult] = useState<GraphResult | null>(null);

  // Narrator
  const [narratorProfile, setNarratorProfile] = useState("analyst");
  const [narratorResult, setNarratorResult] = useState<NarratorResult | null>(null);

  // Case Insights
  const [insightResult, setInsightResult] = useState<CaseInsightResult | null>(null);

  // Law Enforcement
  const [leFormat, setLeFormat] = useState("coaf");
  const [leResult, setLeResult] = useState<LEExportResult | null>(null);

  // THEMIS
  const [themisResult, setThemisResult] = useState<THEMISResult | null>(null);

  const api = async (path: string, body: Record<string, any>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      return await res.json();
    } catch {
      setError("Erro ao comunicar com o serviço de IA");
      return null;
    } finally {
      setLoading(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "explain", label: "XAI Explain" },
    { key: "risk-model", label: "Risk Models" },
    { key: "confidence", label: "Confidence" },
    { key: "graph", label: "Graph Intel" },
    { key: "narrator", label: "Narrator" },
    { key: "insights", label: "Case Insights" },
    { key: "law-enforcement", label: "Law Enforcement" },
    { key: "themis", label: "THEMIS" },
  ];

  return (
    <AuthShell title="AI Intelligence 4.0" subtitle="XAI Layer · Graph Narrator · Confidence Engine · THEMIS Agent">
      <div className="otc-stack">
        {/* Tab bar */}
        <div className="otc-panel" style={{ padding: 8, marginBottom: 8 }}>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                className={`otc-button ${activeTab === tab.key ? "otc-button--accent" : ""}`}
                onClick={() => setActiveTab(tab.key)}
                style={{ fontSize: "0.75rem", padding: "4px 8px" }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ═══ TAB: XAI Explain ═══ */}
        {activeTab === "explain" && (
          <Panel title="Explainable AI — Decisão">
            <div className="otc-stack">
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Case ID
                  <input className="otc-input" value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="CASE-2026-XXXX" />
                </label>
                <label className="otc-field" style={{ flex: 1 }}>
                  Tipo de Decisão
                  <select className="otc-input" value={decisionType} onChange={(e) => setDecisionType(e.target.value)}>
                    <option value="risk_score">Risk Score</option>
                    <option value="block_recommendation">Recomendação de Bloqueio</option>
                    <option value="sanctions_match">Match de Sanções</option>
                  </select>
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !caseId} onClick={async () => {
                const r = await api("/api/v1/ai/explain", { case_id: caseId, decision_type: decisionType });
                if (r) setExplainResult(r);
              }}>{loading ? "Analisando..." : "Explicar Decisão"}</button>
              {explainResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                    <Pill>Confiança: {(explainResult.confidence_score * 100).toFixed(0)}%</Pill>
                    <Pill tone={explainResult.recommendation.includes("BLOQUEAR") ? "danger" : explainResult.recommendation.includes("REVISÃO") ? "warning" : "success"}>
                      {explainResult.recommendation.split("—")[0].trim()}
                    </Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Passos de Raciocínio:</strong>
                    <ol style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {explainResult.reasoning_steps.map((s) => (
                        <li key={s.step}><strong>{s.action}:</strong> {s.result}</li>
                      ))}
                    </ol>
                  </div>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Fatores de Decisão:</strong>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                      {explainResult.factors.map((f) => (
                        <Pill key={f.factor}>{f.factor}: {(f.weight * 100).toFixed(0)}% — {f.detail}</Pill>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Risk Models ═══ */}
        {activeTab === "risk-model" && (
          <Panel title="Modelos de Avaliação de Risco Regulatório">
            <div className="otc-stack">
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Endereço Blockchain
                  <input className="otc-input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="0x..." />
                </label>
                <label className="otc-field" style={{ flex: 1 }}>
                  Modelo
                  <select className="otc-input" value={riskModelType} onChange={(e) => setRiskModelType(e.target.value)}>
                    {RISK_MODELS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
                  </select>
                </label>
                <label className="otc-field" style={{ width: 120 }}>
                  Chain
                  <select className="otc-input" value={chain} onChange={(e) => setChain(e.target.value)}>
                    <option value="ethereum">Ethereum</option>
                    <option value="bitcoin">Bitcoin</option>
                    <option value="polygon">Polygon</option>
                  </select>
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !address} onClick={async () => {
                const r = await api("/api/v1/ai/risk-model", { address, chain, model_type: riskModelType });
                if (r) setRiskModelResult(r);
              }}>{loading ? "Avaliando..." : "Executar Avaliação"}</button>
              {riskModelResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                    <Pill tone={toneForLevel(riskModelResult.risk_level)}>
                      {riskModelResult.risk_level}: {riskModelResult.risk_score}/100
                    </Pill>
                    <Pill>Confiança: {(riskModelResult.confidence * 100).toFixed(0)}%</Pill>
                    <Pill>{riskModelResult.classification}</Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Fatores:</strong>
                    {riskModelResult.factors.map((f, i) => (
                      <div key={i} style={{ margin: "4px 0", padding: 6, background: "var(--otc-surface)", borderRadius: 4 }}>
                        <strong>{f.factor}</strong> ({(f.weight * 100).toFixed(0)}%) — {f.detail}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Evidências:</strong>
                    {riskModelResult.evidence.map((e, i) => (
                      <div key={i} style={{ margin: "2px 0" }}>• {e.description} {e.hash ? `(${e.hash})` : ""}</div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Recomendação:</strong> {riskModelResult.recommendation}
                  </div>
                  {riskModelResult.limitations.length > 0 && (
                    <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>
                      <strong>Limitações:</strong> {riskModelResult.limitations.join("; ")}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Confidence Engine ═══ */}
        {activeTab === "confidence" && (
          <Panel title="Confidence Engine — Classificação FATO/INFERÊNCIA/HIPÓTESE/RECOMENDAÇÃO">
            <div className="otc-stack">
              <button className="otc-button otc-button--accent" disabled={loading} onClick={async () => {
                const r = await api("/api/v1/ai/confidence", { analysis_id: caseId || "default" });
                if (r) setConfidenceResult(r);
              }}>{loading ? "Computando..." : "Calcular Confiança"}</button>
              {confidenceResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <Pill>Confiança Geral: {(confidenceResult.overall_confidence * 100).toFixed(0)}%</Pill>
                  <div style={{ fontSize: "0.85rem", marginTop: 8, marginBottom: 8 }}>
                    <strong>Classificações:</strong>
                    {Object.entries(confidenceResult.classifications).map(([k, v]) => (
                      <div key={k} style={{ margin: "4px 0", padding: 6, background: "var(--otc-surface)", borderRadius: 4 }}>
                        <Pill tone={k === "FATO" ? "success" : k === "HIPÓTESE" ? "warning" : k === "INFERÊNCIA" ? "warning" : "danger"}>{k}</Pill> — {v}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Fatores de Incerteza:</strong>
                    {confidenceResult.uncertainty_factors.map((f, i) => (
                      <div key={i} style={{ margin: "2px 0" }}>• {f.factor} ({f.impact}): {f.detail}</div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>
                    <strong>Limitações:</strong> {confidenceResult.limitations.join("; ")}
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Graph Intelligence ═══ */}
        {activeTab === "graph" && (
          <Panel title="Graph Intelligence 4.0">
            <div className="otc-stack">
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Endereço
                  <input className="otc-input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="0x..." />
                </label>
                <label className="otc-field" style={{ width: 120 }}>
                  Chain
                  <select className="otc-input" value={chain} onChange={(e) => setChain(e.target.value)}>
                    <option value="ethereum">Ethereum</option>
                    <option value="bitcoin">Bitcoin</option>
                    <option value="polygon">Polygon</option>
                  </select>
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !address} onClick={async () => {
                const r = await api("/api/v1/ai/graph-analysis", { address, chain, depth: 3 });
                if (r) setGraphResult(r);
              }}>{loading ? "Analisando..." : "Analisar Grafo"}</button>
              {graphResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                    <Pill>Nós: {graphResult.nodes.length}</Pill>
                    <Pill>Arestas: {graphResult.edges.length}</Pill>
                    <Pill>Clusters: {graphResult.clusters.length}</Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Nós do Grafo:</strong>
                    {graphResult.nodes.map((n) => (
                      <div key={n.id} style={{ margin: "4px 0", padding: 6, background: "var(--otc-surface)", borderRadius: 4 }}>
                        <Pill tone={toneForLevel(n.risk.toUpperCase())}>{n.risk}</Pill> {n.label} ({n.id.slice(0, 12)}...) {n.balance ? `— ${n.balance}` : ""}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Indicadores de Risco:</strong>
                    {graphResult.risk_indicators.map((r, i) => (
                      <div key={i} style={{ margin: "2px 0" }}>
                        <Pill tone={toneForLevel(r.severity.toUpperCase())}>{r.severity}</Pill> {r.indicator} ({(r.confidence * 100).toFixed(0)}%) — {r.detail}
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Clusters:</strong>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                      {graphResult.clusters.map((c) => (
                        <Pill key={c.id} tone={toneForLevel(c.risk.toUpperCase())}>{c.label}: {c.risk} {c.volume ? `(${c.volume})` : ""}</Pill>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Graph Narrator ═══ */}
        {activeTab === "narrator" && (
          <Panel title="Graph Narrator Engine — Narração Automática">
            <div className="otc-stack">
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Endereço
                  <input className="otc-input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="0x..." />
                </label>
                <label className="otc-field" style={{ width: 150 }}>
                  Perfil
                  <select className="otc-input" value={narratorProfile} onChange={(e) => setNarratorProfile(e.target.value)}>
                    <option value="analyst">Analista</option>
                    <option value="legal">Jurídico</option>
                    <option value="executive">Executivo</option>
                  </select>
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !address} onClick={async () => {
                const r = await api("/api/v1/ai/graph-narrator", { address, chain, profile: narratorProfile });
                if (r) setNarratorResult(r);
              }}>{loading ? "Narrando..." : "Gerar Narração"}</button>
              {narratorResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap" }}>
                    {narratorResult.risk_badges.map((b, i) => (
                      <Pill key={i} tone={b.color === "danger" ? "danger" : b.color === "warning" ? "warning" : "success"}>
                        {b.label} {b.score ? `(${b.score})` : ""} {b.detail ? `— ${b.detail}` : ""}
                      </Pill>
                    ))}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8, lineHeight: 1.6 }}>
                    {narratorResult.narrative}
                  </div>
                  {narratorResult.smart_annotations.length > 0 && (
                    <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                      <strong>Smart Annotations:</strong>
                      {narratorResult.smart_annotations.map((a, i) => (
                        <div key={i} style={{ margin: "2px 0" }}>• <code>{a.node.slice(0, 12)}...</code>: {a.text}</div>
                      ))}
                    </div>
                  )}
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Próximas Ações Sugeridas:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {narratorResult.suggested_actions.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Case Insights ═══ */}
        {activeTab === "insights" && (
          <Panel title="Case Intelligence — Insights">
            <div className="otc-stack">
              <label className="otc-field">
                Case ID
                <input className="otc-input" value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="CASE-2026-XXXX" />
              </label>
              <button className="otc-button otc-button--accent" disabled={loading || !caseId} onClick={async () => {
                const r = await api("/api/v1/ai/case-insights", { case_id: caseId });
                if (r) setInsightResult(r);
              }}>{loading ? "Gerando..." : "Gerar Insights"}</button>
              {insightResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <Pill tone={toneForLevel(insightResult.risk_level)}>Risco: {insightResult.risk_level}</Pill>
                  <div style={{ fontSize: "0.85rem", marginTop: 8, marginBottom: 8 }}>{insightResult.summary}</div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Achados Principais:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {insightResult.key_findings.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Recomendações:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {insightResult.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                  {insightResult.similar_cases.length > 0 && (
                    <div style={{ fontSize: "0.85rem" }}>
                      <strong>Casos Similares:</strong>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
                        {insightResult.similar_cases.map((sc) => (
                          <Pill key={sc.case_id}>{sc.case_id}: {(sc.similarity * 100).toFixed(0)}% ({sc.outcome})</Pill>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: Law Enforcement ═══ */}
        {activeTab === "law-enforcement" && (
          <Panel title="Law Enforcement Package — Exportação Regulatória">
            <div className="otc-stack">
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Case ID
                  <input className="otc-input" value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="CASE-2026-XXXX" />
                </label>
                <label className="otc-field" style={{ flex: 1 }}>
                  Formato
                  <select className="otc-input" value={leFormat} onChange={(e) => setLeFormat(e.target.value)}>
                    {LE_FORMATS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </select>
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !caseId} onClick={async () => {
                const r = await api("/api/v1/ai/law-enforcement-export", { case_id: caseId, format: leFormat, include_evidence_hash: true });
                if (r) setLeResult(r);
              }}>{loading ? "Gerando..." : "Gerar Pacote"}</button>
              {leResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <Pill>{leResult.document.type}</Pill>
                  <div style={{ fontSize: "0.85rem", marginTop: 8, marginBottom: 8, whiteSpace: "pre-wrap" }}>
                    {JSON.stringify(leResult.document.sections || leResult.document, null, 2)}
                  </div>
                  {leResult.evidence_chain.length > 0 && (
                    <div style={{ fontSize: "0.85rem" }}>
                      <strong>Cadeia de Custódia Digital:</strong>
                      {leResult.evidence_chain.map((e, i) => (
                        <div key={i} style={{ margin: "2px 0" }}>• {e.item} — <code>{e.hash}</code> ({e.timestamp})</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Panel>
        )}

        {/* ═══ TAB: THEMIS ═══ */}
        {activeTab === "themis" && (
          <Panel title="THEMIS — Case Intelligence Agent">
            <div className="otc-stack">
              <p style={{ fontSize: "0.85rem", color: "var(--otc-text-soft)", margin: "0 0 8px 0" }}>
                THEMIS orquestra todos os módulos de IA: Case Card + Graph Narrator + Risk Assessment + Law Enforcement Package
              </p>
              <div style={{ display: "flex", gap: 8 }}>
                <label className="otc-field" style={{ flex: 1 }}>
                  Case ID
                  <input className="otc-input" value={caseId} onChange={(e) => setCaseId(e.target.value)} placeholder="CASE-2026-XXXX" />
                </label>
                <label className="otc-field" style={{ flex: 1 }}>
                  Endereço
                  <input className="otc-input" value={address} onChange={(e) => setAddress(e.target.value)} placeholder="0x..." />
                </label>
              </div>
              <button className="otc-button otc-button--accent" disabled={loading || !caseId || !address} onClick={async () => {
                const r = await api("/api/v1/ai/themis", { case_id: caseId, address, chain, action: "full" });
                if (r) setThemisResult(r);
              }}>{loading ? "THEMIS processando..." : "Executar THEMIS"}</button>
              {themisResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  {themisResult.human_gate_required && (
                    <div style={{ padding: 8, background: "#fef3cd", borderRadius: 4, marginBottom: 8, fontSize: "0.85rem" }}>
                      <strong>⚠️ Human-in-the-Loop Gate Ativado</strong> — Score &gt; 70 ou nível HIGH/CRITICAL. Decisão requer aprovação humana.
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                    <Pill tone={toneForLevel(themisResult.risk_assessment.level)}>
                      Risk: {themisResult.risk_assessment.score}/100 ({themisResult.risk_assessment.level})
                    </Pill>
                    <Pill>Confiança: {(themisResult.risk_assessment.confidence * 100).toFixed(0)}%</Pill>
                    <Pill>{themisResult.risk_assessment.classification}</Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Case Card:</strong> {themisResult.case_card.origin_agent} — {themisResult.case_card.status}
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Graph:</strong> {themisResult.graph_narrative.nodes} nós, {themisResult.graph_narrative.edges} arestas, {themisResult.graph_narrative.clusters} clusters
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Recomendação:</strong> {themisResult.risk_assessment.recommendation}
                  </div>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Law Enforcement:</strong> {themisResult.law_enforcement_package.document_type} ({themisResult.law_enforcement_package.evidence_count} evidências)
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {error && (
          <div className="otc-panel" style={{ padding: 12, borderLeft: "3px solid var(--otc-danger)" }}>
            <span style={{ color: "var(--otc-danger)" }}>{error}</span>
          </div>
        )}
      </div>
    </AuthShell>
  );
}
