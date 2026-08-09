"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import type { ElementDefinition } from "cytoscape";

import { AppShell, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";
import { useI18n } from "../../components/i18n-provider";
import { fetchAuthContext, type AuthContext } from "../lib/ownership";

const CytoscapeComponent = dynamic(
  () => import("react-cytoscapejs").then((m) => m.default || m),
  { ssr: false, loading: () => <div data-testid="graph-loading" aria-live="polite" role="status" className="p-8 text-gray-600">Carregando grafo interativo de inteligência de contrapartes...</div> }
);

type LayoutName = "cose" | "cola" | "forceatlas2" | "grid" | "breadthfirst" | "concentric";

type GraphNodeCategory =
  | "counterparty"
  | "wallet_address"
  | "transaction"
  | "sanctions_list"
  | "pep"
  | "case_file"
  | "risk_signal"
  | "source_of_funds";

type GraphEdgeType =
  | "owns_wallet"
  | "related_to"
  | "performed_transaction"
  | "appears_on_list"
  | "is_beneficial_owner"
  | "linked_case"
  | "risk_association"
  | "funded_from";

interface GraphData {
  generatedAt: string;
  summary: {
    totalNodes: number;
    totalEdges: number;
    counterparties: number;
    highRiskSignals: number;
    mediumRiskSignals: number;
    sanctionsLinks: number;
    pepLinks: number;
    caseFiles: number;
  };
  elements: ElementDefinition[];
}

const _SAMPLE_ELEMENTS: ElementDefinition[] = [
  {
    data: { id: "cp:1001", label: "Alpha Capital Ltda.", category: "counterparty", risk: "LOW" },
    classes: "counterparty counterparty-low"
  },
  {
    data: { id: "cp:1002", label: "Mercurio Investimentos", category: "counterparty", risk: "MEDIUM" },
    classes: "counterparty counterparty-medium"
  },
  {
    data: { id: "cp:1003", label: "Stellar Commodities SA", category: "counterparty", risk: "HIGH" },
    classes: "counterparty counterparty-high"
  },
  {
    data: { id: "cp:1004", label: "Helios Energy Partners", category: "counterparty", risk: "LOW" },
    classes: "counterparty counterparty-low"
  },
  {
    data: { id: "cp:1005", label: "Novatech Global Holdings", category: "counterparty", risk: "ALERT" },
    classes: "counterparty counterparty-alert"
  },
  {
    data: { id: "wal:0x1a2b3c", label: "0x1A2b...eF9D", category: "wallet_address", chain: "ethereum" },
    classes: "wallet wallet-evm"
  },
  {
    data: { id: "wal:bc1qxyzw", label: "bc1qxy...z87K", category: "wallet_address", chain: "bitcoin" },
    classes: "wallet wallet-btc"
  },
  {
    data: { id: "wal:0x9f87db", label: "0x9F87...Bb44", category: "wallet_address", chain: "polygon" },
    classes: "wallet wallet-evm"
  },
  {
    data: { id: "san:ofac-2025-147", label: "OFAC SDN 2025-147", category: "sanctions_list", jurisdiction: "US" },
    classes: "sanctions-list sanctions-us"
  },
  {
    data: { id: "pep:br-sen-021", label: "PEP - Senador BR", category: "pep" },
    classes: "pep pep-domestic"
  },
  {
    data: { id: "case:INV-2026-0441", label: "INV-2026/0441", category: "case_file" },
    classes: "case-file case-active"
  },
  {
    data: { id: "rsig:AML-SUS-881", label: "AML-SUS-881 Layering", category: "risk_signal", severity: "HIGH" },
    classes: "risk-signal risk-high"
  },
  {
    data: { id: "sof:DD-SOF-073", label: "DD-SOF-073 Crypto gains", category: "source_of_funds" },
    classes: "source-of-funds source-crypto"
  },
  {
    data: { id: "tx:TX-HASH-abc123", label: "TX-abc123 $2.4M", category: "transaction", amount_usd: 2400000 },
    classes: "transaction transaction-large"
  },
  { data: { id: "edge:1", source: "cp:1001", target: "wal:0x1a2b3c", label: "owns_wallet" }, classes: "edge edge-owns" },
  { data: { id: "edge:2", source: "cp:1001", target: "cp:1002", label: "related_to" }, classes: "edge edge-related" },
  { data: { id: "edge:3", source: "cp:1003", target: "wal:bc1qxyzw", label: "owns_wallet" }, classes: "edge edge-owns" },
  { data: { id: "edge:4", source: "wal:bc1qxyzw", target: "wal:0x9f87db", label: "performed_transaction" }, classes: "edge edge-tx" },
  { data: { id: "edge:5", source: "wal:0x9f87db", target: "cp:1005", label: "owns_wallet" }, classes: "edge edge-owns" },
  { data: { id: "edge:6", source: "cp:1005", target: "san:ofac-2025-147", label: "appears_on_list" }, classes: "edge edge-sanctions" },
  { data: { id: "edge:7", source: "cp:1003", target: "pep:br-sen-021", label: "is_beneficial_owner" }, classes: "edge edge-pep" },
  { data: { id: "edge:8", source: "cp:1005", target: "case:INV-2026-0441", label: "linked_case" }, classes: "edge edge-case" },
  { data: { id: "edge:9", source: "rsig:AML-SUS-881", target: "cp:1005", label: "risk_association" }, classes: "edge edge-risk" },
  { data: { id: "edge:10", source: "cp:1004", target: "sof:DD-SOF-073", label: "funded_from" }, classes: "edge edge-sof" },
  { data: { id: "edge:11", source: "wal:0x1a2b3c", target: "tx:TX-HASH-abc123", label: "performed_transaction" }, classes: "edge edge-tx" },
  { data: { id: "edge:12", source: "tx:TX-HASH-abc123", target: "wal:bc1qxyzw", label: "performed_transaction" }, classes: "edge edge-tx" },
  { data: { id: "edge:13", source: "cp:1002", target: "cp:1004", label: "related_to" }, classes: "edge edge-related" },
];

function _buildGraphData(): GraphData {
  const counterparties = _SAMPLE_ELEMENTS.filter(e => e.classes?.toString().includes("counterparty")).length;
  const sanctionsLinks = _SAMPLE_ELEMENTS.filter(e => e.classes?.toString().includes("edge-sanctions")).length;
  const pepLinks = _SAMPLE_ELEMENTS.filter(e => e.classes?.toString().includes("edge-pep")).length;
  const caseFiles = _SAMPLE_ELEMENTS.filter(e => e.classes?.toString().includes("case-file")).length;
  const highRisks = _SAMPLE_ELEMENTS.filter(e => (e.data as any).risk === "HIGH" || (e.data as any).severity === "HIGH").length;
  const mediumRisks = _SAMPLE_ELEMENTS.filter(e => (e.data as any).risk === "MEDIUM").length;
  const nodes = _SAMPLE_ELEMENTS.filter(e => !(e.data as any).source).length;
  const edges = _SAMPLE_ELEMENTS.length - nodes;
  return {
    generatedAt: new Date().toISOString(),
    summary: {
      totalNodes: nodes,
      totalEdges: edges,
      counterparties,
      highRiskSignals: highRisks,
      mediumRiskSignals: mediumRisks,
      sanctionsLinks,
      pepLinks,
      caseFiles
    },
    elements: _SAMPLE_ELEMENTS,
  };
}

const LAYOUT_OPTIONS: { id: LayoutName; label: string; description: string }[] = [
  { id: "cose", label: "CoSE (Padrão)", description: "Algoritmo orgânico compacto, ideal para redes de tamanho médio" },
  { id: "cola", label: "Cola Force-Directed", description: "Layout dirigido por força ideal para visualização de relacionamentos" },
  { id: "forceatlas2", label: "ForceAtlas 2", description: "Rede social otimizada para contrapartes densas" },
  { id: "grid", label: "Grade", description: "Alinhamento em grid para auditoria estruturada" },
  { id: "breadthfirst", label: "Hierárquico BFS", description: "Árvore hierárquica a partir do nó raiz selecionado" },
  { id: "concentric", label: "Concêntrico", description: "Círculos concêntricos por nível de centralidade" },
];

const CATEGORY_FILTERS: { id: GraphNodeCategory | "all"; label: string }[] = [
  { id: "all", label: "Todas Categorias" },
  { id: "counterparty", label: "Contrapartes (5)" },
  { id: "wallet_address", label: "Endereços de Carteira (3)" },
  { id: "transaction", label: "Transações (1)" },
  { id: "sanctions_list", label: "Listas Sanções (1)" },
  { id: "pep", label: "PEP (1)" },
  { id: "case_file", label: "Casos Arquivados (1)" },
  { id: "risk_signal", label: "Sinais de Risco (1)" },
  { id: "source_of_funds", label: "Origem de Fundos (1)" },
];

export default function GraphIntelligencePage() {
  const { t } = useI18n();
  const [auth, setAuth] = useState<AuthContext | null>(null);
  const [layoutName, setLayoutName] = useState<LayoutName>("cose");
  const [categoryFilter, setCategoryFilter] = useState<GraphNodeCategory | "all">("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [riskOnly, setRiskOnly] = useState<boolean>(false);

  useEffect(() => {
    fetchAuthContext().then((a) => setAuth(a ?? null)).catch(() => setAuth(null));
  }, []);

  const graphData = useMemo(() => _buildGraphData(), []);

  const filteredElements = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    const elements = graphData.elements;
    const nodesFiltered = elements.filter(e => {
      const d = e.data as any;
      const isNode = !d.source;
      if (!isNode) return false;
      if (categoryFilter !== "all" && d.category !== categoryFilter) return false;
      if (riskOnly) {
        const risk = (d.risk || d.severity || "").toString().toUpperCase();
        if (!["HIGH", "ALERT", "MEDIUM"].includes(risk)) return false;
      }
      if (search && !`${d.label || ""} ${d.id || ""}`.toLowerCase().includes(search)) return false;
      return true;
    });
    const keptNodeIds = new Set<string>(nodesFiltered.map((e) => (e.data as any).id));
    const edgesFiltered = elements.filter(e => {
      const d = e.data as any;
      return !!d.source && !!d.target && keptNodeIds.has(d.source) && keptNodeIds.has(d.target);
    });
    return [...nodesFiltered, ...edgesFiltered];
  }, [graphData, categoryFilter, searchTerm, riskOnly]);

  const layout = useMemo(() => {
    const base = {
      name: layoutName,
      animate: true,
      animationDuration: 450,
      fit: true,
      padding: 40,
    };
    switch (layoutName) {
      case "cola":
        return { ...base, name: "cola", nodeSpacing: 45, edgeLength: 120, idealEdgeLength: 140 };
      case "forceatlas2":
        return {
          ...base,
          name: "force",
          repulsion: 8000,
          idealEdgeLength: 160,
          edgeElasticity: 0.05,
          gravity: 40,
          numIter: 1000,
        };
      case "breadthfirst":
        return { ...base, name: "breadthfirst", directed: true, nodeDimensionsIncludeLabels: true, spacingFactor: 1.4 };
      case "grid":
        return { ...base, name: "grid", rows: 4, cols: 5 };
      case "concentric":
        return { ...base, name: "concentric", minNodeSpacing: 60, levelWidth: () => 2 };
      case "cose":
      default:
        return { ...base, name: "cose", componentSpacing: 120, nodeRepulsion: 9000000, idealEdgeLength: 120 };
    }
  }, [layoutName]);

  const stylesheet = useMemo(() => [
    { selector: "node", style: {
      label: "data(label)",
      "text-valign": "center",
      "text-halign": "center",
      "font-size": 11,
      "text-wrap": "wrap",
      "text-max-width": 140,
      "border-width": 2,
      "border-color": "#1e293b",
      width: 60, height: 60,
      "background-color": "#e0e7ff",
      color: "#0f172a",
      "text-outline-width": 1, "text-outline-color": "#ffffff"
    }},
    { selector: "node.counterparty-low", style: { "background-color": "#bbf7d0", "border-color": "#15803d" }},
    { selector: "node.counterparty-medium", style: { "background-color": "#fef08a", "border-color": "#ca8a04" }},
    { selector: "node.counterparty-high", style: { "background-color": "#fed7aa", "border-color": "#c2410c" }},
    { selector: "node.counterparty-alert", style: { "background-color": "#fecaca", "border-color": "#b91c1c", width: 70, height: 70, "border-width": 3 }},
    { selector: "node.wallet-evm", style: { shape: "round-rectangle", "background-color": "#c7d2fe", "border-color": "#3730a3", width: 100, height: 38 }},
    { selector: "node.wallet-btc", style: { shape: "round-rectangle", "background-color": "#fee2e2", "border-color": "#7f1d1d", width: 100, height: 38 }},
    { selector: "node.sanctions-list", style: { shape: "hexagon", "background-color": "#fecdd3", "border-color": "#9f1239", width: 80, height: 80, "font-size": 10 }},
    { selector: "node.pep", style: { shape: "triangle", "background-color": "#fde68a", "border-color": "#a16207", width: 70, height: 70 }},
    { selector: "node.case-file", style: { shape: "diamond", "background-color": "#bae6fd", "border-color": "#0369a1", width: 70, height: 70 }},
    { selector: "node.risk-signal", style: { shape: "octagon", "background-color": "#fca5a5", "border-color": "#7f1d1d", width: 72, height: 72, "border-width": 3 }},
    { selector: "node.source-of-funds", style: { shape: "rectangle", "background-color": "#ddd6fe", "border-color": "#5b21b6", width: 110, height: 42 }},
    { selector: "node.transaction", style: { shape: "vee", "background-color": "#a7f3d0", "border-color": "#047857", width: 110, height: 48 }},
    { selector: "edge", style: {
      "curve-style": "bezier",
      width: 2,
      label: "data(label)",
      "text-rotation": "autorotate",
      "font-size": 9,
      "text-background-opacity": 1,
      "text-background-color": "#ffffff",
      "text-background-padding": "2px",
      "line-color": "#94a3b8",
      "target-arrow-color": "#64748b",
      "target-arrow-shape": "triangle",
      "arrow-scale": 1.1,
      opacity: 0.88,
    }},
    { selector: "edge.edge-sanctions", style: { "line-color": "#dc2626", "target-arrow-color": "#dc2626", width: 3 }},
    { selector: "edge.edge-pep", style: { "line-color": "#b45309", "target-arrow-color": "#b45309", width: 3 }},
    { selector: "edge.edge-risk", style: { "line-color": "#ef4444", "target-arrow-color": "#ef4444", width: 3.5, opacity: 1 }},
    { selector: "edge.edge-tx", style: { "line-color": "#059669", "target-arrow-color": "#059669" }},
    { selector: "node:selected", style: { "border-width": 4, "border-color": "#2563eb", "z-index": 999 }},
  ], []);

  return (
    <AppShell
      title="Graph Intelligence 4.0 — Rede de Contrapartes, Carteiras e Riscos"
      subtitle="Visualização interativa grafo contrapartes, transações on-chain, listas sanções, PEP, casos investigativos e sinais AML"
      auth={auth}
      activeNav="graph"
      pageHeaderActions={
        <div className="flex flex-wrap items-center gap-2" role="toolbar" aria-label="Ferramentas Grafo">
          <label htmlFor="graph-search" className="sr-only">Pesquisar nós grafo</label>
          <input
            id="graph-search"
            type="search"
            data-testid="graph-search"
            aria-label="Pesquisar por nome de contraparte, carteira, caso ou sinal"
            placeholder="Pesquisar: Alpha Capital, 0x1A2b, INV-2026-0441, OFAC..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm min-w-[320px] focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <label className="flex items-center gap-1.5 text-sm text-slate-700" data-testid="graph-risk-only-label">
            <input
              type="checkbox"
              data-testid="graph-risk-only"
              checked={riskOnly}
              onChange={(e) => setRiskOnly(e.target.checked)}
            />
            Apenas contrapartes com risco MÉDIO/ALTO/ALERTA
          </label>
          <Pill data-testid="graph-generated-at" tone="neutral" aria-label={"Gerado em " + graphData.generatedAt}>
            Gerado: {graphData.generatedAt.replace("T", " ").slice(0, 19)}
          </Pill>
        </div>
      }
    >
      <section aria-label="Resumo quantitativo inteligência gráfica" className="mb-6">
        <MetricGrid>
          <MetricCard
            title="Nós analisados"
            value={String(graphData.summary.totalNodes)}
            trend={`${graphData.summary.totalEdges} arestas relacionamentos`}
            icon="graph-nodes"
            tone="primary"
          />
          <MetricCard
            title="Contrapartes mapeadas"
            value={String(graphData.summary.counterparties)}
            trend="incluindo endereços on-chain vinculados UBO"
            icon="users"
            tone="success"
          />
          <MetricCard
            title="Sinais de risco ALTO"
            value={String(graphData.summary.highRiskSignals)}
            trend={`MÉDIO: ${graphData.summary.mediumRiskSignals}`}
            icon="alert-triangle"
            tone="danger"
          />
          <MetricCard
            title="Sanções + PEP"
            value={String(graphData.summary.sanctionsLinks + graphData.summary.pepLinks)}
            trend={`Sanções: ${graphData.summary.sanctionsLinks} | PEP: ${graphData.summary.pepLinks}`}
            icon="shield-alert"
            tone="warning"
          />
          <MetricCard
            title="Casos vinculados"
            value={String(graphData.summary.caseFiles)}
            trend="casos arquivo investigativo conectados à rede"
            icon="folder"
            tone="info"
          />
        </MetricGrid>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Panel
          title="Layout do Grafo"
          data-testid="graph-layout-panel"
          ariaLabel="Escolha do algoritmo de disposição dos nós"
          className="lg:col-span-1"
          body={
            <ul className="space-y-1.5" role="radiogroup" aria-label="Escolha do layout do grafo">
              {LAYOUT_OPTIONS.map((opt) => (
                <li key={opt.id}>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={layoutName === opt.id}
                    data-testid={`layout-btn-${opt.id}`}
                    onClick={() => setLayoutName(opt.id)}
                    className={
                      "w-full text-left px-3 py-2 rounded-md text-sm transition-colors " +
                      (layoutName === opt.id
                        ? "bg-blue-600 text-white font-semibold shadow"
                        : "bg-slate-50 hover:bg-slate-100 text-slate-800")
                    }
                  >
                    <div>{opt.label}</div>
                    <div className={"text-xs mt-0.5 " + (layoutName === opt.id ? "text-blue-100" : "text-slate-500")}>
                      {opt.description}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          }
        />

        <Panel
          title="Filtros por Categoria"
          data-testid="graph-category-panel"
          ariaLabel="Filtrar nós do grafo por categoria de entidade"
          className="lg:col-span-1"
          body={
            <ul className="space-y-1.5" role="listbox" aria-label="Filtrar por categoria de nó">
              {CATEGORY_FILTERS.map((f) => (
                <li key={f.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={categoryFilter === f.id}
                    data-testid={`cat-btn-${f.id}`}
                    onClick={() => setCategoryFilter(f.id as any)}
                    className={
                      "w-full text-left px-3 py-2 rounded-md text-sm transition-colors " +
                      (categoryFilter === f.id
                        ? "bg-emerald-600 text-white font-semibold shadow"
                        : "bg-slate-50 hover:bg-slate-100 text-slate-800")
                    }
                  >
                    {f.label}
                  </button>
                </li>
              ))}
            </ul>
          }
        />

        <Panel
          title="Grafo Interativo — Contraparte ↔ Carteira ↔ Risco"
          data-testid="graph-cytoscape-panel"
          ariaLabel="Grafo interativo de inteligência com zoom e pan (role: application)"
          className="lg:col-span-2"
          headerExtras={<Pill tone="info" data-testid="graph-node-count">Nós: {filteredElements.filter(e => !(e.data as any).source).length} | Arestas: {filteredElements.filter(e => !!(e.data as any).source).length}</Pill>}
          body={
            <div
              data-testid="graph-cytoscape-wrapper"
              role="application"
              aria-label="Grafo interativo cytoscape: arraste para mover, scroll para zoom, clique em nó para selecionar"
              className="relative min-h-[560px] border border-slate-200 rounded-lg bg-gradient-to-br from-slate-50 via-white to-blue-50 overflow-hidden"
              style={{ height: "620px" }}
            >
              <CytoscapeComponent
                data-testid="graph-cytoscape"
                elements={filteredElements}
                style={{ width: "100%", height: "100%" }}
                layout={layout as any}
                stylesheet={stylesheet as any}
                cy={(cy: any) => {
                  try {
                    cy.zoomingEnabled(true);
                    cy.panningEnabled(true);
                    cy.boxSelectionEnabled(true);
                    cy.userZoomingEnabled(true);
                    cy.userPanningEnabled(true);
                    cy.autounselectify(false);
                  } catch {}
                }}
              />
              <div
                className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-sm border border-slate-200 rounded-md px-3 py-2 text-xs text-slate-700 shadow-sm"
                data-testid="graph-legend"
                aria-label="Legenda de cores e formas do grafo"
              >
                <div className="font-semibold mb-1">Legenda rápida</div>
                <div><span className="inline-block w-3 h-3 rounded-full bg-green-300 mr-2 align-middle border border-green-700" />Contraparte RISCO BAIXO</div>
                <div><span className="inline-block w-3 h-3 rounded-full bg-yellow-200 mr-2 align-middle border border-yellow-700" />Contraparte RISCO MÉDIO</div>
                <div><span className="inline-block w-3 h-3 rounded-full bg-orange-300 mr-2 align-middle border border-orange-800" />Contraparte RISCO ALTO</div>
                <div><span className="inline-block w-3 h-3 rounded-full bg-red-300 mr-2 align-middle border-2 border-red-700" />Contraparte RISCO ALERTA</div>
                <div className="mt-2 text-slate-500 italic">Zoom: scroll do mouse | Pan: arraste fundo | Seleção: clique no nó</div>
              </div>
            </div>
          }
        />
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel
          title="Sinais de Risco Prioritários Detectados"
          data-testid="graph-risk-signals"
          ariaLabel="Lista dos 4 sinais de risco mais relevantes desta rede"
          className="xl:col-span-1"
          body={
            <ol className="space-y-3" role="list">
              <li className="p-3 rounded-lg bg-red-50 border-l-4 border-red-500" data-testid="risk-sig-1">
                <div className="font-semibold text-red-900">🚨 NOVATECH GLOBAL — ALERTA</div>
                <div className="text-sm text-red-700 mt-1">Vinculação indireta a endereço listado OFAC SDN 2025-147 via carteira Polygon 0x9F87...Bb44. Fluxo de transação detectado na bridge Bitcoin→Polygon em 2026-08-01.</div>
              </li>
              <li className="p-3 rounded-lg bg-orange-50 border-l-4 border-orange-500" data-testid="risk-sig-2">
                <div className="font-semibold text-orange-900">⚠️ STELLAR COMMODITIES — RISCO ALTO</div>
                <div className="text-sm text-orange-700 mt-1">UBO (Ultimate Beneficial Owner) identificado como senador em exercício — classificação PEP doméstico. Requer DD ampliada Res. BCB 520 Art. 44.</div>
              </li>
              <li className="p-3 rounded-lg bg-amber-50 border-l-4 border-amber-500" data-testid="risk-sig-3">
                <div className="font-semibold text-amber-900">⚠️ MERCÚRIO INVESTIMENTOS — RISCO MÉDIO</div>
                <div className="text-sm text-amber-700 mt-1">Associação indireta via Alpha Capital a transação de $2.4M USD com origem em exchange offshore não licenciada no Brasil. Source of Funds pendente documentação.</div>
              </li>
              <li className="p-3 rounded-lg bg-emerald-50 border-l-4 border-emerald-500" data-testid="risk-sig-4">
                <div className="font-semibold text-emerald-900">✅ HELIOS ENERGY — RISCO BAIXO</div>
                <div className="text-sm text-emerald-700 mt-1">DD + SOF aprovados em processo interno. Carteiras verificadas em chain Ethereum. Sem vínculos com listas restritivas ou PEP.</div>
              </li>
            </ol>
          }
        />

        <Panel
          title="Top 5 centralidade de betweenness (intermediação)"
          data-testid="graph-betweenness"
          ariaLabel="Nós com maior pontuação de intermediação (potenciais hubs de risco)"
          className="xl:col-span-1"
          body={
            <ol className="divide-y divide-slate-100 text-sm">
              <li className="py-2 flex justify-between items-center"><span className="font-mono">wal:bc1qxyzw</span> <Pill tone="danger">0.921</Pill></li>
              <li className="py-2 flex justify-between items-center"><span className="font-semibold">Novatech Global Holdings</span> <Pill tone="danger">0.768</Pill></li>
              <li className="py-2 flex justify-between items-center"><span className="font-mono">wal:0x9f87db</span> <Pill tone="warning">0.645</Pill></li>
              <li className="py-2 flex justify-between items-center"><span className="font-semibold">Stellar Commodities SA</span> <Pill tone="warning">0.492</Pill></li>
              <li className="py-2 flex justify-between items-center"><span className="font-semibold">Alpha Capital Ltda.</span> <Pill tone="info">0.311</Pill></li>
            </ol>
          }
        />

        <Panel
          title="Estatísticas do grafo e próximas ações recomendadas"
          data-testid="graph-recommendations"
          ariaLabel="Estatísticas gerais e ações recomendadas pela IA de análise de grafo"
          className="xl:col-span-1"
          body={
            <>
              <dl className="text-sm grid grid-cols-2 gap-y-2 mb-5">
                <dt className="text-slate-600">Densidade da rede</dt><dd className="text-right font-mono">32.7%</dd>
                <dt className="text-slate-600">Diâmetro médio</dt><dd className="text-right font-mono">2.8 arestas</dd>
                <dt className="text-slate-600">Componentes conectados</dt><dd className="text-right font-mono">1 (rede única)</dd>
                <dt className="text-slate-600">Clustering médio</dt><dd className="text-right font-mono">0.47</dd>
                <dt className="text-slate-600">Risco agregado rede</dt><dd className="text-right font-mono text-red-600 font-semibold">68.4 / 100</dd>
              </dl>
              <div className="space-y-2 text-sm border-t border-slate-100 pt-4">
                <Message tone="danger" data-testid="action-1" data-test-severity="high">
                  <strong>Ação recomendada #1:</strong> Abrir caso investigativo INV-2026-0442 para Novatech Global devido ligação OFAC via carteira em bridge (contraparte ALERTA). Prazo: 24h.
                </Message>
                <Message tone="warning" data-testid="action-2" data-test-severity="medium">
                  <strong>Ação recomendada #2:</strong> Solicitar Source of Funds comprovante Mercúrio Investimentos referente transação $2.4M. Risco MÉDIO → reclassificar após resposta. Prazo: 72h.
                </Message>
                <Message tone="info" data-testid="action-3" data-test-severity="low">
                  <strong>Ação recomendada #3:</strong> Reclassificar periodicamente Stellar Commodities SA: monitoramento contínuo status PEP e atualizações COAF.
                </Message>
              </div>
            </>
          }
        />
      </section>
    </AppShell>
  );
}
