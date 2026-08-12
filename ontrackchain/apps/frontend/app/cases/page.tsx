"use client";

import { useState, useEffect } from "react";
import { AuthShell, Panel, Pill } from "../../components/ui";

type Case = {
  case_id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  assigned_to: string | null;
  risk_score: number | null;
  created_at: string;
  updated_at: string;
};

type CaseMetrics = {
  total_cases: number;
  open_cases: number;
  closed_cases: number;
  avg_resolution_time_hours: number;
  cases_by_priority: Record<string, number>;
  cases_by_category: Record<string, number>;
};

const EMPTY_METRICS: CaseMetrics = {
  total_cases: 0,
  open_cases: 0,
  closed_cases: 0,
  avg_resolution_time_hours: 0,
  cases_by_priority: {},
  cases_by_category: {}
};

function resolveApiBase(): string {
  if (typeof window !== "undefined") {
    const fromEnv = (window as any).__NEXT_PUBLIC_API_BASE_URL__ || process.env.NEXT_PUBLIC_API_BASE_URL;
    if (fromEnv) return fromEnv.replace(/\/$/, "");
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8080`;
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://traefik";
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [metrics, setMetrics] = useState<CaseMetrics | null>(null);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCase, setNewCase] = useState({ title: "", description: "", priority: "medium", category: "aml" });

  useEffect(() => {
    fetchCases();
    fetchMetrics();
  }, []);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${resolveApiBase()}/api/v1/cases`, {
        cache: "no-store",
        credentials: "include",
        headers: { "Accept": "application/json" }
      });
      if (res.ok) {
        const data = await res.json();
        setCases(data.data ?? []);
      } else {
        setCases([]);
      }
    } catch (err) {
      console.error("Failed to fetch cases");
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch(`${resolveApiBase()}/api/v1/cases/metrics`, {
        cache: "no-store",
        credentials: "include",
        headers: { "Accept": "application/json" }
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data ?? EMPTY_METRICS);
      } else {
        setMetrics(EMPTY_METRICS);
      }
    } catch (err) {
      console.error("Failed to fetch metrics");
      setMetrics(EMPTY_METRICS);
    }
  };

  const createCase = async () => {
    try {
      const res = await fetch(`${resolveApiBase()}/api/v1/cases`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(newCase)
      });
      if (res.ok) {
        const data = await res.json();
        setCases([data, ...cases]);
        setShowCreateModal(false);
        setNewCase({ title: "", description: "", priority: "medium", category: "aml" });
        fetchMetrics();
      }
    } catch (err) {
      console.error("Failed to create case");
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical": return "danger";
      case "high": return "warning";
      case "medium": return "success";
      default: return "success";
    }
  };

  return (
    <AuthShell title="Case Management" subtitle="Investigation Case Lifecycle">
      <div className="otc-stack">
        {metrics && (
          <Panel title="Case Metrics">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
              <div className="otc-panel" style={{ padding: 12, textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics.total_cases}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>Total Cases</div>
              </div>
              <div className="otc-panel" style={{ padding: 12, textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--otc-warning)" }}>{metrics.open_cases}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>Open Cases</div>
              </div>
              <div className="otc-panel" style={{ padding: 12, textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--otc-success)" }}>{metrics.closed_cases}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>Closed Cases</div>
              </div>
              <div className="otc-panel" style={{ padding: 12, textAlign: "center" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{metrics.avg_resolution_time_hours.toFixed(1)}h</div>
                <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>Avg Resolution</div>
              </div>
            </div>
          </Panel>
        )}

        <Panel title="Investigation Cases">
          <div style={{ marginBottom: 12 }}>
            <button
              className="otc-button otc-button--accent"
              onClick={() => setShowCreateModal(true)}
            >
              + New Case
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: "center", padding: 20 }}>Loading cases...</div>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {cases.map((c) => (
                <div
                  key={c.case_id}
                  className="otc-panel"
                  style={{ padding: 12, cursor: "pointer" }}
                  onClick={() => setSelectedCase(c)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{c.title}</div>
                      <div style={{ fontSize: "0.8rem", color: "var(--otc-text-soft)" }}>
                        {c.case_id} | {c.category} | {c.assigned_to || "Unassigned"}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <Pill tone={getPriorityColor(c.priority)}>{c.priority}</Pill>
                      <Pill>{c.status}</Pill>
                      {c.risk_score && (
                        <Pill tone={c.risk_score > 70 ? "danger" : c.risk_score > 40 ? "warning" : "success"}>
                          Risk: {c.risk_score}
                        </Pill>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>

        {selectedCase && (
          <Panel title={`Case: ${selectedCase.case_id}`}>
            <div className="otc-stack">
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <strong>Title:</strong> {selectedCase.title}
                </div>
                <div>
                  <strong>Status:</strong> {selectedCase.status}
                </div>
                <div>
                  <strong>Priority:</strong> {selectedCase.priority}
                </div>
                <div>
                  <strong>Category:</strong> {selectedCase.category}
                </div>
                <div>
                  <strong>Assigned To:</strong> {selectedCase.assigned_to || "Unassigned"}
                </div>
                <div>
                  <strong>Risk Score:</strong> {selectedCase.risk_score || "N/A"}
                </div>
              </div>
              <div>
                <strong>Description:</strong>
                <p style={{ margin: "4px 0" }}>{selectedCase.description}</p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="otc-button" onClick={() => setSelectedCase(null)}>
                  Close
                </button>
                <button className="otc-button otc-button--accent">
                  Update Status
                </button>
              </div>
            </div>
          </Panel>
        )}

        {showCreateModal && (
          <Panel title="Create New Case">
            <div className="otc-stack">
              <label className="otc-field">
                Title
                <input
                  className="otc-input"
                  value={newCase.title}
                  onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
                  placeholder="Case title"
                />
              </label>
              <label className="otc-field">
                Description
                <textarea
                  className="otc-input"
                  value={newCase.description}
                  onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
                  placeholder="Case description"
                  rows={3}
                />
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <label className="otc-field">
                  Priority
                  <select
                    className="otc-input"
                    value={newCase.priority}
                    onChange={(e) => setNewCase({ ...newCase, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </label>
                <label className="otc-field">
                  Category
                  <select
                    className="otc-input"
                    value={newCase.category}
                    onChange={(e) => setNewCase({ ...newCase, category: e.target.value })}
                  >
                    <option value="aml">AML</option>
                    <option value="sanctions">Sanctions</option>
                    <option value="kyc">KYC</option>
                    <option value="investigation">Investigation</option>
                  </select>
                </label>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="otc-button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button
                  className="otc-button otc-button--accent"
                  onClick={createCase}
                  disabled={!newCase.title}
                >
                  Create Case
                </button>
              </div>
            </div>
          </Panel>
        )}
      </div>
    </AuthShell>
  );
}
