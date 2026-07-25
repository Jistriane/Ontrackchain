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
  factors: Array<{ factor: string; weight: number; impact: string }>;
  recommendation: string;
  generated_at: string;
};

type GraphAnalysisResult = {
  analysis_id: string;
  address: string;
  chain: string;
  nodes: Array<{ id: string; type: string; label: string; risk: string }>;
  edges: Array<{ source: string; target: string; type: string; amount: number; count: number }>;
  clusters: Array<{ id: string; nodes: string[]; risk: string; label: string }>;
  risk_indicators: Array<{ indicator: string; severity: string; confidence: number }>;
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

export default function AIPage() {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<"explain" | "graph" | "insights">("explain");
  const [caseId, setCaseId] = useState("");
  const [address, setAddress] = useState("");
  const [chain, setChain] = useState("ethereum");
  const [decisionType, setDecisionType] = useState("risk_score");
  const [loading, setLoading] = useState(false);
  const [explainResult, setExplainResult] = useState<ExplanationResult | null>(null);
  const [graphResult, setGraphResult] = useState<GraphAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExplain = async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/ai/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, decision_type: decisionType })
      });
      const data = await res.json();
      setExplainResult(data);
    } catch (err) {
      setError("Failed to explain decision");
    } finally {
      setLoading(false);
    }
  };

  const handleGraphAnalysis = async () => {
    if (!address) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/ai/graph-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address, chain, depth: 3, analysis_type: "relationship" })
      });
      const data = await res.json();
      setGraphResult(data);
    } catch (err) {
      setError("Failed to analyze graph");
    } finally {
      setLoading(false);
    }
  };

  const [caseInsightResult, setCaseInsightResult] = useState<CaseInsightResult | null>(null);

  const handleCaseInsights = async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/ai/case-insights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, include_history: true, include_recommendations: true })
      });
      const data = await res.json();
      setCaseInsightResult(data);
    } catch (err) {
      setError("Failed to generate case insights");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="AI Intelligence" subtitle="Explainable AI and Graph Intelligence 4.0">
      <div className="otc-stack">
        <div className="otc-panel" style={{ padding: 12, marginBottom: 8 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button
              className={`otc-button ${activeTab === "explain" ? "otc-button--accent" : ""}`}
              onClick={() => setActiveTab("explain")}
            >
              Explain Decision
            </button>
            <button
              className={`otc-button ${activeTab === "graph" ? "otc-button--accent" : ""}`}
              onClick={() => setActiveTab("graph")}
            >
              Graph Analysis
            </button>
            <button
              className={`otc-button ${activeTab === "insights" ? "otc-button--accent" : ""}`}
              onClick={() => setActiveTab("insights")}
            >
              Case Insights
            </button>
          </div>
        </div>

        {activeTab === "explain" && (
          <Panel title="Explainable AI Decision">
            <div className="otc-stack">
              <label className="otc-field">
                Case ID
                <input
                  className="otc-input"
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  placeholder="Enter case ID"
                />
              </label>
              <label className="otc-field">
                Decision Type
                <select
                  className="otc-input"
                  value={decisionType}
                  onChange={(e) => setDecisionType(e.target.value)}
                >
                  <option value="risk_score">Risk Score</option>
                  <option value="block_recommendation">Block Recommendation</option>
                  <option value="sanctions_match">Sanctions Match</option>
                </select>
              </label>
              <button
                className="otc-button otc-button--accent"
                onClick={handleExplain}
                disabled={loading || !caseId}
              >
                {loading ? "Analyzing..." : "Explain Decision"}
              </button>

              {explainResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem" }}>Explanation</h3>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <Pill>Confidence: {(explainResult.confidence_score * 100).toFixed(0)}%</Pill>
                    <Pill tone={explainResult.recommendation.includes("BLOCK") ? "danger" : "success"}>
                      {explainResult.recommendation}
                    </Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Reasoning Steps:</strong>
                    <ol style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {explainResult.reasoning_steps.map((step) => (
                        <li key={step.step}>
                          {step.action}: {step.result}
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Factors:</strong>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
                      {explainResult.factors.map((factor) => (
                        <Pill key={factor.factor}>
                          {factor.factor}: {(factor.weight * 100).toFixed(0)}% ({factor.impact})
                        </Pill>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {activeTab === "graph" && (
          <Panel title="Graph Intelligence 4.0">
            <div className="otc-stack">
              <label className="otc-field">
                Blockchain Address
                <input
                  className="otc-input"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="0x..."
                />
              </label>
              <label className="otc-field">
                Chain
                <select
                  className="otc-input"
                  value={chain}
                  onChange={(e) => setChain(e.target.value)}
                >
                  <option value="ethereum">Ethereum</option>
                  <option value="bitcoin">Bitcoin</option>
                  <option value="polygon">Polygon</option>
                  <option value="arbitrum">Arbitrum</option>
                </select>
              </label>
              <button
                className="otc-button otc-button--accent"
                onClick={handleGraphAnalysis}
                disabled={loading || !address}
              >
                {loading ? "Analyzing..." : "Analyze Graph"}
              </button>

              {graphResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem" }}>Graph Analysis</h3>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <Pill>Nodes: {graphResult.nodes.length}</Pill>
                    <Pill>Edges: {graphResult.edges.length}</Pill>
                    <Pill>Clusters: {graphResult.clusters.length}</Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Risk Indicators:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {graphResult.risk_indicators.map((indicator) => (
                        <li key={indicator.indicator}>
                          {indicator.indicator}: {indicator.severity} ({(indicator.confidence * 100).toFixed(0)}%)
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div style={{ fontSize: "0.85rem" }}>
                    <strong>Clusters:</strong>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
                      {graphResult.clusters.map((cluster) => (
                        <Pill key={cluster.id} tone={cluster.risk === "high" ? "danger" : "success"}>
                          {cluster.label}: {cluster.risk}
                        </Pill>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )}

        {activeTab === "insights" && (
          <Panel title="AI Case Insights">
            <div className="otc-stack">
              <label className="otc-field">
                Case ID
                <input
                  className="otc-input"
                  value={caseId}
                  onChange={(e) => setCaseId(e.target.value)}
                  placeholder="Enter case ID"
                />
              </label>
              <button
                className="otc-button otc-button--accent"
                onClick={handleCaseInsights}
                disabled={loading || !caseId}
              >
                {loading ? "Generating..." : "Generate Insights"}
              </button>

              {caseInsightResult && (
                <div className="otc-panel" style={{ padding: 12, marginTop: 8 }}>
                  <h3 style={{ margin: "0 0 8px 0", fontSize: "1rem" }}>Case Insights</h3>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <Pill tone={caseInsightResult.risk_level === "HIGH" ? "danger" : caseInsightResult.risk_level === "MEDIUM" ? "warning" : "success"}>
                      Risk: {caseInsightResult.risk_level}
                    </Pill>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Summary:</strong>
                    <p style={{ margin: "4px 0" }}>{caseInsightResult.summary}</p>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Key Findings:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {caseInsightResult.key_findings.map((finding, i) => (
                        <li key={i}>{finding}</li>
                      ))}
                    </ul>
                  </div>
                  <div style={{ fontSize: "0.85rem", marginBottom: 8 }}>
                    <strong>Recommendations:</strong>
                    <ul style={{ margin: "4px 0", paddingLeft: 20 }}>
                      {caseInsightResult.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                  {caseInsightResult.similar_cases.length > 0 && (
                    <div style={{ fontSize: "0.85rem" }}>
                      <strong>Similar Cases:</strong>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
                        {caseInsightResult.similar_cases.map((sc) => (
                          <Pill key={sc.case_id}>
                            {sc.case_id}: {(sc.similarity * 100).toFixed(0)}% ({sc.outcome})
                          </Pill>
                        ))}
                      </div>
                    </div>
                  )}
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
