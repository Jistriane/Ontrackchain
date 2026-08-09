# ADR-022 — Graph Intelligence 4.0 Cytoscape.js Counterparty↔Wallet↔Risk Network Multi-Layout Frontend

- **Status**: Aprovado e implementado na Sprint 21
- **Decisores**: Product Owner Visual Analytics + Arquiteto Frontend + Especialista Operações Investigativas
- **Data de aprovação**: Sprint 21 (2026-08-08)

---

## 1. Contexto

A Ontrackchain identificou em entrevistas com 8 clientes prospects de Financial
Services que **87%** deles tinham um GAP operacional grave:

> Equipes de investigação AML gastam **4,2 horas em média por caso** montando
> manualmente, em ferramentas de planilha ou draw.io, a REDE DE RELAÇÕES
> entre contrapartes, carteiras on-chain, transações, PEP, sanções OFAC, casos
> arquivados e sinais de risco. Elas pediam: *"Um produto que entregue a
> visualização pronta em 1 clique, com métricas de centralidade e ações
> recomendadas pela IA"*.

**Requisitos funcionais prioritários (RFP v3)**:

1.  **Visualização interativa grafo NÃO bloqueante** com ~20 a ~300 nós por sessão.
2.  **Múltiplos layouts**: investigadores preferem layouts diferentes por caso
    (análise transacional usa force-directed; hierarquia de UBO usa breadthfirst;
    auditoria estruturada usa grid).
3.  **Filtros por categoria de nó**: só contrapartes, só carteiras, só sinais,
    ou combinação.
4.  **Modo "Apenas Risco"**: toggle rápido para esconder contrapartes BAIXO e
    focar em MEDIUM / HIGH / ALERT (80% dos casos).
5.  **Pesquisa textual** por nome de contraparte, hash de carteira, ID de caso.
6.  **Acessibilidade WCAG 2.1 AA**: `role=application`, `aria-label`, legenda
    visual cores/formas.
7.  **Error Boundary próprio de segmento**: Erro cytoscape.js client render
    NÃO pode derrubar menu ou outros módulos.
8.  **6 métricas quantitativas no topo**: total nós, arestas, contrapartes,
    sinais risco alto, sanções+PEP, casos vinculados.

---

## 2. Alternativas Avaliadas — Biblioteca de Visualização Grafos

### Opção A: D3.js force graph customizado

- **Prós**: 100% flexível; build do zero; bundle min pequeno.
- **Contras**: Reescrever wheel: zoom/pan, seleção de nós, box selection,
  eventos tap/drag. Pelo menos **3 semanas de engenharia front-end** para
  igualar feature-parity do Cytoscape. D3.js NÃO tem suporte nativo a
  layouts cola/forceatlas2 como plug-and-play.

### Opção B: Sigma.js (Canvas acelerado)

- **Prós**: Performance excelente para 10K+ nós. Canvas rendering.
- **Contras**: Ecossistema menor; menos layouts oficiais; integração React
  (`react-sigma`) tem downloads 10x menor que `react-cytoscapejs`. Suporte a
  labels rich e formas geométricas (hexágono, triângulo, octógono — usadas para
  categorizar PEP, sanções, risco) **mais limitado**.

### **Opção C (RECOMENDADA): Cytoscape.js 3.30 + React Bindings react-cytoscapejs 2.0**

Decisão final Cytoscape.js por esses fatores PONDERADOS:

1.  **Ecossistema comprovado**: 10 anos, 10M+ npm downloads, Stanford, MIT,
    Pfizer, Roche, JPMorgan usam em produção.
2.  **~40 layouts oficiais**: cose, cola, forceatlas2, breadthfirst, grid,
    concentric, dagre (DAG hierarchies), avsdf, euler, spread...
3.  **Formas + estilos CSS-like**: 12 shapes nativas (roundrect, hexagon,
    triangle, diamond, octagon, vee, pentagon...) + `classes` em elementos
    para estilizar por categoria (usamos bastante para legenda visual).
4.  **Acessibilidade programática**: `cy.zoomingEnabled()`,
    `cy.panningEnabled()`, `cy.boxSelectionEnabled()` programáticos.

---

## 3. Decisão Final: Cytoscape.js SSR Disabled via next/dynamic

**⚠️ OBRIGATÓRIO SSR = false**

Cytoscape.js manipula o DOM diretamente via canvas + SVG e NÃO funciona sem
`window` / `document`. Next.js 14 App Router renderiza páginas server-side por
padrão. Temos OBRIGATORIAMENTE que envolver o componente:

```tsx
const CytoscapeComponent = dynamic(
  () => import("react-cytoscapejs").then((m) => m.default || m),
  { ssr: false, loading: () => <div role="status" aria-live="polite">Carregando grafo...</div> }
);
```

### 3.1 Arquitetura da Página `/graph` (Sprint 21)

```
 apps/frontend/app/graph/
 ├── page.tsx            ← 885 linhas App Router "use client" - SRP Graph 4.0
 └── error.tsx           ← Error Boundary segmento (S20 ADR-020 pattern)
```

**Componentes funcionais (1 Page TSX)**:

| Região na página | Responsabilidade |
|---|---|
| Header Actions | Search box, Risco-only toggle, timestamp gerado em ISO |
| Metric Cards (5) | Nós, contrapartes, sinais risco alto, sanções+PEP, casos |
| Painel Layouts (6) | cose, cola, forceatlas2, grid, breadthfirst, concentric |
| Painel Filtros Categoria (9 opções) | Todas, Counterparty, Wallet, Tx, Sanctions, PEP, Case, Risk, SoF |
| Cytoscape (painel direito) | Canvas interativo + legenda cores |
| Painel Inferior Esquerdo | 4 Sinais Risco Prioritários (Alerta / Alto / Médio / Baixo) |
| Painel Central Inferior | Top 5 nós betweenness centrality (potenciais hubs) |
| Painel Inferior Direito | Estatísticas gerais rede (densidade, diâmetro, clustering, risco agregado) + 3 ações recomendadas IA |

### 3.2 Nós vs Arestas Diferenciados

- **14 nós / 13 arestas** = MVP demo 28 elementos. MVP cobre 8 categorias de nós
  e 8 tipos de aresta.
- **Cada categoria usa uma FORMA + COR distinta**:
  - Contrapartes: círculos coloridos por risco (verde→amarelo→laranja→vermelho)
  - Carteiras (EVM/BTC): retângulos arredondados azul/vermelho claro
  - Sanções: **hexágono** vermelho ROSA
  - PEP: **triângulo** amarelo
  - Casos: **losango (diamond)** azul claro
  - Sinais de Risco: **octógono** vermelho BORDA DUPLA
  - Source of Funds: retângulo roxo
  - Transações: forma "vee" verde

### 3.3 Acessibilidade (WCAG AA — segue ADR-020)

1.  Container grafo `role="application"` (screen readers entram modo focus
    navegação aplicação).
2.  `aria-label` descritivo: "Grafo interativo cytoscape...".
3.  Legenda inferior esquerda com texto (não depende só da cor).
4.  Todos botões layout e categorias com `aria-checked`, `aria-selected`
    (roles radiogroup / listbox).
5.  Error boundary segmento — se cytoscape.js falha: botão retry local.

---

## 4. Trade-offs

### 4.1 Positivas

1.  **Diferencial competitivo MATERIAL**: Feature pedida por 87% prospects em
    pesquisa de validação P de produto. Entrega visibilidade gráfica que planilhas
    não conseguem (ex: betweenness top 5 nós identifica hubs criminosos invisíveis
    em tabela).
2.  **Evolução futura trivial**: Adicionar um novo layout = 1 objeto novo em
    LAYOUT_OPTIONS + entrada stylesheet. Demanda 10 minutos.
3.  **Cobertura E2E Playwright**: 7 specs graph-intelligence-t205.spec.ts
    (layouts, categorias, pesquisa, sinais, centralidade, ações).

### 4.2 Negativas / Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Bundle size: Cytoscape.js ~600KB minificado | Média | UX (LCP +150ms) | Dynamic import `ssr:false` NÃO carrega no entry bundle — só carrega quando usuário acessa `/graph`. |
| Perfomance em 500+ nós (browser pesado) | Baixa hoje, cresce | Médio | Layouts `cola` e `cose` iteram 1000+ steps — temos `animationDuration: 450ms` e `numIter:1000` com limite. Próximo passo: webworker layout. |
| Navegação por teclado dentro canvas limitada | Média | WCAG 2.1 ponto de atenção | Implementamos navegação alternativa (lista de nós abaixo grafo) para compensar. |

---

## 5. Testes E2E (Q3-04 Playwright Graph Intelligence)

`apps/frontend/tests/e2e/graph-intelligence-t205.spec.ts`:

| ID Teste | Caso |
|---|---|
| G1 | Header, métricas 5 cards, painel layout visível |
| G2 | 6 layouts todos selecionáveis (aria-checked=true) |
| G3 | Filtro Counterparty + Apenas Risco toggle ativado |
| G4 | Pesquisa "Alpha Capital" no search input |
| G5 | Legenda cytoscape + betweenness + 4 sinais risco |
| G6 | Ações recomendadas IA e Estatísticas (densidade etc) |
| G7 | 7 categorias de nó listadas em filtro + "Todas Categorias" |

---

## 6. DoD (Definition of Done)

- [x] Pacote frontend versão 1.9.0 → **2.0.0** (Major — feature graph nova)
- [x] Dependencies `cytoscapejs` + `react-cytoscapejs` adicionadas
- [x] DevDependencies `@types/cytoscape` adicionada
- [x] Novo route `/graph` Next.js App Router `app/graph/page.tsx`
- [x] Novo boundary segmento `app/graph/error.tsx` (DRY ADR-020)
- [x] 6 layouts, 9 categorias, pesquisa, Risco-only toggle
- [x] 4 sinais risco prioritários, Top 5 betweenness, 3 ações recomendadas IA
- [x] Script npm: `npm run test:graph`
- [x] 7 testes Playwright graph E2E
- [x] Acessibilidade WCAG 2.1 AA: aria-labels, roles, legenda cores+texto
