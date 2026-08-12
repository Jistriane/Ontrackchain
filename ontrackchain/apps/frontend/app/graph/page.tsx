"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";

import { AppShell, MetricCard, MetricGrid, Panel, Pill } from "../../components/ui";

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
  elements: any[];
}

const _SAMPLE_ELEMENTS: any[] = [];

function _buildGraphData(): GraphData {
  const nodes = _SAMPLE_ELEMENTS.filter(e => !(e.data as any).source).length;
  const edges = _SAMPLE_ELEMENTS.length - nodes;
  return {
    generatedAt: new Date().toISOString(),
    summary: {
      totalNodes: nodes,
      totalEdges: edges,
      counterparties: 0,
      highRiskSignals: 0,
      mediumRiskSignals: 0,
      sanctionsLinks: 0,
      pepLinks: 0,
      caseFiles: 0
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
  { id: "counterparty", label: "Contrapartes" },
  { id: "wallet_address", label: "Endereços de Carteira" },
  { id: "transaction", label: "Transações" },
  { id: "sanctions_list", label: "Listas Sanções" },
  { id: "pep", label: "PEP" },
  { id: "case_file", label: "Casos Arquivados" },
  { id: "risk_signal", label: "Sinais de Risco" },
  { id: "source_of_funds", label: "Origem de Fundos" },
];

export default function GraphIntelligencePage() {
  const [layoutName, setLayoutName] = useState<LayoutName>("cose");
  const [categoryFilter, setCategoryFilter] = useState<GraphNodeCategory | "all">("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [riskOnly, setRiskOnly] = useState<boolean>(false);

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
      activePath="/graph"
      actions={
        <div className="flex flex-wrap items-center gap-2" role="toolbar" aria-label="Ferramentas Grafo">
          <label htmlFor="graph-search" className="sr-only">Pesquisar nós grafo</label>
          <input
            id="graph-search"
            type="search"
            data-testid="graph-search"
            aria-label="Pesquisar por nome de contraparte, carteira, caso ou sinal"
            placeholder="Pesquisar: contraparte, carteira, caso investigativo, OFAC..."
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
          <Pill data-testid="graph-generated-at" tone="success" aria-label={"Gerado em " + graphData.generatedAt}>
            Gerado: {graphData.generatedAt.replace("T", " ").slice(0, 19)}
          </Pill>
        </div>
      }
    >
      <section aria-label="Resumo quantitativo inteligência gráfica" className="mb-6">
        <MetricGrid>
          <MetricCard
            label="Nós analisados"
            value={String(graphData.summary.totalNodes)}
            meta={`${graphData.summary.totalEdges} arestas relacionamentos`}
          />
          <MetricCard
            label="Contrapartes mapeadas"
            value={String(graphData.summary.counterparties)}
            meta="incluindo endereços on-chain vinculados UBO"
          />
          <MetricCard
            label="Sinais de risco ALTO"
            value={String(graphData.summary.highRiskSignals)}
            meta={`MÉDIO: ${graphData.summary.mediumRiskSignals}`}
            accent
          />
          <MetricCard
            label="Sanções + PEP"
            value={String(graphData.summary.sanctionsLinks + graphData.summary.pepLinks)}
            meta={`Sanções: ${graphData.summary.sanctionsLinks} | PEP: ${graphData.summary.pepLinks}`}
          />
          <MetricCard
            label="Casos vinculados"
            value={String(graphData.summary.caseFiles)}
            meta="casos arquivo investigativo conectados à rede"
          />
        </MetricGrid>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <Panel
          title="Layout do Grafo"
          description="Escolha do algoritmo de disposição dos nós"
          className="lg:col-span-1"
          actions={<Pill tone="warning">6 algoritmos</Pill>}
        >
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
        </Panel>

        <Panel
          title="Filtros por Categoria"
          description="Filtrar nós do grafo por categoria de entidade"
          className="lg:col-span-1"
          actions={<Pill tone="success">{CATEGORY_FILTERS.length} categorias</Pill>}
        >
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
        </Panel>

        <Panel
          title="Grafo Interativo — Contraparte ↔ Carteira ↔ Risco"
          description="Grafo interativo de inteligência com zoom e pan (role: application)"
          className="lg:col-span-2"
          actions={
            <Pill tone="warning" data-testid="graph-node-count">
              Nós: {filteredElements.filter(e => !(e.data as any).source).length} | Arestas: {filteredElements.filter(e => !!(e.data as any).source).length}
            </Pill>
          }
        >
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
        </Panel>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Panel
          title="Sinais de Risco Prioritários Detectados"
          description="Lista dos sinais de risco mais relevantes desta rede (atualizada dinamicamente por backend)"
          className="xl:col-span-1"
        >
          <div className="text-sm text-slate-600 italic" data-testid="risk-signals-empty">
            Nenhum sinal de risco priorizado. Carregue dados do backend de inteligência de contrapartes.
          </div>
        </Panel>

        <Panel
          title="Top centralidade de betweenness (intermediação)"
          description="Nós com maior pontuação de intermediação (potenciais hubs de risco)"
          className="xl:col-span-1"
        >
          <div className="text-sm text-slate-600 italic" data-testid="betweenness-empty">
            Sem nós carregados. Calcule centralidade de betweenness a partir de dados reais de rede.
          </div>
        </Panel>

        <Panel
          title="Estatísticas do grafo e próximas ações recomendadas"
          description="Estatísticas gerais e ações recomendadas pela IA de análise de grafo"
          className="xl:col-span-1"
        >
          <dl className="text-sm grid grid-cols-2 gap-y-2 mb-5">
            <dt className="text-slate-600">Densidade da rede</dt><dd className="text-right font-mono text-slate-400">—</dd>
            <dt className="text-slate-600">Diâmetro médio</dt><dd className="text-right font-mono text-slate-400">—</dd>
            <dt className="text-slate-600">Componentes conectados</dt><dd className="text-right font-mono text-slate-400">—</dd>
            <dt className="text-slate-600">Clustering médio</dt><dd className="text-right font-mono text-slate-400">—</dd>
            <dt className="text-slate-600">Risco agregado rede</dt><dd className="text-right font-mono text-slate-400">—</dd>
          </dl>
          <div className="space-y-2 text-sm border-t border-slate-100 pt-4 text-slate-600 italic" data-testid="actions-empty">
            Ações recomendadas serão calculadas automaticamente quando dados de rede forem carregados do backend de inteligência.
          </div>
        </Panel>
      </section>
    </AppShell>
  );
}
