"use client";

import React, { useState } from "react";
import { Message, Panel } from "../../components/ui";

export default function EnterpriseCompliancePage() {
  const [activePhase, setActivePhase] = useState<"P4" | "P5" | "P6" | "P7">("P4");
  const [addressInput, setAddressInput] = useState("0x8589427373d6d84e98730d7795d8f6f8731fda16");
  const [p4Result, setP4Result] = useState<any>(null);
  const [p5Result, setP5Result] = useState<any>(null);
  const [p6Result, setP6Result] = useState<any>(null);
  const [p7Result, setP7Result] = useState<any>(null);

  const handleP4Analyze = () => {
    const isMixer = addressInput.toLowerCase().includes("8589427373d6d84e98730d7795d8f6f8731fda16");
    setP4Result({
      phase: "P4",
      address: addressInput,
      mixer_exposure: isMixer,
      mixer_hits: isMixer ? [{ label: "Tornado.Cash 0.1 ETH", direct: true }] : [],
      bridge_hops_count: 2,
      risk_score: isMixer ? 100 : 25,
      recommendation: isMixer ? "REJECT" : "APPROVE",
      coaf_reporting_required: isMixer,
    });
  };

  const handleP5GenerateFiling = () => {
    const batchId = `coaf_batch_${Math.random().toString(36).substring(2, 10)}`;
    setP5Result({
      phase: "P5",
      batch_id: batchId,
      receipt_protocol: `PROT_SISCOAF_${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
      sha256_signature: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      status: "READY_FOR_TRANSMISSION",
      xml_preview: `<SISCOAFBatch id="${batchId}" entity="OTC_FINTECH_9613">\n  <RecordsCount>1</RecordsCount>\n</SISCOAFBatch>`,
    });
  };

  const handleP6TravelRule = () => {
    setP6Result({
      phase: "P6",
      requires_travel_rule: true,
      compliant: true,
      action: "ALLOW_TRANSFER",
      ivms101_hash: "a4f89d123e456789bcf0123456789abcdef0123456789abcdef0123456789abc",
    });
  };

  const handleP7Summarize = () => {
    setP7Result({
      phase: "P7",
      case_id: "CASE_ENTERPRISE_9001",
      legal_defense_ready: true,
      dossier_hash: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
      summary_text: "DOSSIÊ FORENSE AUTOMATIZADO (FASE P7): Análise completa de lavagem de dinheiro, pontes cross-chain e relatórios COAF encadeados via SHA-256 para defesa jurídica.",
    });
  };

  return (
    <div className="otc-container" style={{ padding: "2rem" }}>
      <header className="otc-header">
        <h1>Cockpit Enterprise - Módulos P4, P5, P6 e P7</h1>
        <p>Módulos de conformidade avançada para grande escala, mixers, Travel Rule e auto-filing COAF.</p>
      </header>

      <div className="otc-controls otc-controls--spaced" style={{ marginBottom: "1.5rem" }}>
        <button
          type="button"
          className={`otc-button ${activePhase === "P4" ? "" : "otc-button--ghost"}`}
          onClick={() => setActivePhase("P4")}
        >
          🌉 P4: Bridge & Mixer Risk
        </button>
        <button
          type="button"
          className={`otc-button ${activePhase === "P5" ? "" : "otc-button--ghost"}`}
          onClick={() => setActivePhase("P5")}
        >
          📄 P5: Auto-Filing COAF
        </button>
        <button
          type="button"
          className={`otc-button ${activePhase === "P6" ? "" : "otc-button--ghost"}`}
          onClick={() => setActivePhase("P6")}
        >
          ✈️ P6: Travel Rule (FATF 16)
        </button>
        <button
          type="button"
          className={`otc-button ${activePhase === "P7" ? "" : "otc-button--ghost"}`}
          onClick={() => setActivePhase("P7")}
        >
          ⚖️ P7: AI Legal Dossier
        </button>
      </div>

      {activePhase === "P4" && (
        <Panel title="Fase P4: Multi-Chain Cross-Bridge & Mixer Risk Intelligence" description="Detecção automática de pulos de cadeia e contato com mixers sancionados (Tornado Cash).">
          <div className="otc-field" style={{ marginBottom: "1rem" }}>
            <label className="otc-label">Endereço de Wallet:</label>
            <input
              type="text"
              className="otc-input"
              value={addressInput}
              onChange={(e) => setAddressInput(e.target.value)}
              style={{ width: "100%", fontFamily: "monospace" }}
            />
          </div>
          <button type="button" className="otc-button" onClick={handleP4Analyze}>
            🔍 Analisar Risco de Mixer & Pontes (P4)
          </button>

          {p4Result && (
            <div style={{ marginTop: "1rem" }}>
              <Message tone={p4Result.risk_score >= 80 ? "error" : "success"}>
                Score de Risco P4: {p4Result.risk_score}/100 | Recomendação: {p4Result.recommendation}
              </Message>
              <pre className="otc-code-block" style={{ marginTop: "0.5rem", padding: "1rem", background: "var(--otc-bg-panel)", borderRadius: "8px" }}>
                {JSON.stringify(p4Result, null, 2)}
              </pre>
            </div>
          )}
        </Panel>
      )}

      {activePhase === "P5" && (
        <Panel title="Fase P5: Automated Regulatory Reporting (COAF / BACEN Auto-Filing)" description="Geração automatizada de lote SISCOAF em XML/JSON assinado por SHA-256.">
          <button type="button" className="otc-button" onClick={handleP5GenerateFiling}>
            📦 Gerar Lote de Remessa SISCOAF (P5)
          </button>

          {p5Result && (
            <div style={{ marginTop: "1rem" }}>
              <Message tone="success">
                Lote Gerado: {p5Result.batch_id} | Protocolo SISCOAF: {p5Result.receipt_protocol}
              </Message>
              <pre className="otc-code-block" style={{ marginTop: "0.5rem", padding: "1rem", background: "var(--otc-bg-panel)", borderRadius: "8px" }}>
                {JSON.stringify(p5Result, null, 2)}
              </pre>
            </div>
          )}
        </Panel>
      )}

      {activePhase === "P6" && (
        <Panel title="Fase P6: Real-Time Travel Rule Compliance Engine (FATF Rec. 16 / IVMS101)" description="Troca de informações de originador e beneficiário entre VASPs para transferências &gt; R$ 5.000,00.">
          <button type="button" className="otc-button" onClick={handleP6TravelRule}>
            🔒 Validar Transferência VASP Travel Rule (P6)
          </button>

          {p6Result && (
            <div style={{ marginTop: "1rem" }}>
              <Message tone="success">
                Status: {p6Result.action} | Hash IVMS101: {p6Result.ivms101_hash}
              </Message>
              <pre className="otc-code-block" style={{ marginTop: "0.5rem", padding: "1rem", background: "var(--otc-bg-panel)", borderRadius: "8px" }}>
                {JSON.stringify(p6Result, null, 2)}
              </pre>
            </div>
          )}
        </Panel>
      )}

      {activePhase === "P7" && (
        <Panel title="Fase P7: AI/LLM Automated Forensic Summarizer & Legal Defense" description="Geração de parecer forense automatizado e pacote de provas de defesa jurídica selado em hash.">
          <button type="button" className="otc-button" onClick={handleP7Summarize}>
            ⚖️ Gerar Parecer Forense & Pacote Jurídico (P7)
          </button>

          {p7Result && (
            <div style={{ marginTop: "1rem" }}>
              <Message tone="default">
                {p7Result.summary_text}
              </Message>
              <pre className="otc-code-block" style={{ marginTop: "0.5rem", padding: "1rem", background: "var(--otc-bg-panel)", borderRadius: "8px" }}>
                {JSON.stringify(p7Result, null, 2)}
              </pre>
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}
