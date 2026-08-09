# ADR-020 — Frontend Next.js App Router: Error Boundaries Global + Segmentos + WCAG AA Loading Skeletons a11y

- **Status**: Aprovado e implementado na Sprint 19
- **Decisores**: Arquiteto Frontend + Especialista Acessibilidade WCAG + PO
- **Data de aprovação**: Sprint 19 (2026-08-07)

---

## 1. Contexto

Na linha do tempo de Sprints 1 a 18, focamos em backend, segurança e contratos de
API. O frontend Next.js 14.2.35 App Router (introduzido em S13/S14) expandiu de
5 telas para **24 páginas e múltiplos segmentos dinâmicos** (ex:
`/cases/[id]/page.tsx`). A quantidade de componentes renderizando dados assíncronos
(fetch API, autenticação, feature flags) gerou **3 GAPs CRÍTICOS de UX**:

1.  **Erros não capturados renderização cliente (`"use client"`) propagavam para raiz
    da aplicação**. BUG já observado em homologação: componente `alerts/page.tsx`
    recebeu dados incompletos de timeline → erro runtime → página inteira branca.
    Usuário precisava dar F5.
2.  **Feedback visual de loading inconsistente entre telas**. Tela dashboard
    exibia skeletons; tela cases só mostrava texto "Carregando...". Sem
    `aria-live="polite"` → usuários NVDA / VoiceOver NÃO RECEBIAM aviso de
    operação em andamento.
3.  **Página 404 inexistente para URLs deep-link quebrados** (ex: cliente recebia
    link `/evidence/wrong-id` → retornava 200 vazio, erro silencioso; contra
    boas práticas HTTP semântico).

### 1.1 Restrições Acessibilidade (WCAG 2.1 Nível AA — obrigação legal Brasil, Decreto 10.946/2022 e-MAG)

- **1.1.1 Non-text Content (A)**: Todos skeletons precisam de `role="status"`
  e `aria-busy="true"` para AT.
- **2.2.2 Pause, Stop, Hide (A)**: Animation shimmer não deve piscar mais que
  3Hz (limite WCAG 2.3.1).
- **3.3.1 Error Identification (A)**: Error Boundaries DEVEM informar o erro
  humanamente legível em português, não só stack trace.
- **4.1.2 Name, Role, Value (A)**: Botão "Tentar novamente" tem `aria-label`
  claro, reset boundary Next.js `reset()` callback.

---

## 2. Alternativas Avaliadas

### Opção A: Apenas Error Boundary Global (1 arquivo error.tsx em app/)

- **Prós**: Menos arquivos (1 arquivo), uniformidade.
- **Contras**: Erro em `/ai/*` (IA insights) derruba sidebar navegação e acesso
  a casos; usuário perde contexto. Não resolve GAP #2 / #3.

### Opção B: try/catch em cada componente + useState de erro

- **Prós**: Controle fino em nível de componente.
- **Contras**: DRY violation (30+ arquivos duplicando lógica). Desvio de
  comportamento entre componentes com o tempo. GAP de acessibilidade permanece.

### **Opção C (RECOMENDADA): Error Boundaries Hierárquicos + Loading Skeletons Global/Segmentos + Not-Found.tsx**

Next.js App Router 14 oferece nativamente mecanismo de co-location de
`error.tsx`, `loading.tsx`, `not-found.tsx` em **qualquer segmento de rota**.

**Escolhemos 7 arquivos distribuídos em camadas:**

| Local | Arquivo | Propósito |
|---|---|---|
| `apps/frontend/app/` | `error.tsx` GLOBAL | Captura erro NÃO tratado de qualquer segmento; fallback `<html>` completo. |
| `apps/frontend/app/` | `loading.tsx` GLOBAL | Skeletons shimmer com `aria-live=polite` e `role=status` + `aria-busy=true`. |
| `apps/frontend/app/` | `not-found.tsx` 404 | Página navegável (botão voltar dashboard) para qualquer URL não mapeada. |
| `apps/frontend/app/dashboard/` | `error.tsx` | Erro painel reseta só dashboard (mantém menu). |
| `apps/frontend/app/cases/` | `error.tsx` | Erro gestão casos reseta só segmento. |
| `apps/frontend/app/ai/` | `error.tsx` | Erro AI Insights (falta LLM, timeout) com retry local. |
| `apps/frontend/app/evidence/` | `error.tsx` | Erro evidências (hash mismatch, arquivo corrompido). |

Adicional: **+1 segment error.tsx criado Sprint 21 T2-05** → `app/graph/error.tsx`
para o módulo Graph Intelligence 4.0 Cytoscape.js.

---

## 3. Decisão Final: Opção C + @axe-core/playwright Suite a11y

### 3.1 Error Boundary Global (app/error.tsx) — Requisitos de implementação

- **OBRIGATÓRIO `"use client"` directive**: React Error Boundaries são
  exclusivamente Client Components no Next.js 14 App Router.
- **Interface obrigatória props**: `{ error: Error & { digest?: string }; reset: () => void }`
- **Reset Button**: Chama `reset()` (re-renderiza boundary árvore abaixo; **não**
  refaz fetch de rota pai).
- **Mecanismo de segurança**: NÃO expõe stack trace ao usuário final. Apenas
  `message` e `digest` (Next.js opaco correlaciona com server logs).

### 3.2 Loading Skeleton WCAG 2.1 AA

Design system OBRIGATÓRIO shimmer (padrão produto):

```tsx
<div aria-live="polite" role="status" aria-busy="true">
  {/* 4 Skeleton cards metric shimmer */}
  {/* 1 Skeleton gráfico barras */}
  {/* 1 Skeleton tabela 6 linhas */}
</div>
```

**Controle WCAG 2.3.1 Seizures**: frequência do gradiente shimmer animada ≤ 1
ciclo / 1,5s (0.66 Hz) — NUNCA acima de 3Hz.

### 3.3 404 not-found.tsx

- Retorna HTTP **404** (Next.js seta automaticamente status code quando rota é
  invocada via `notFound()` do next/navigation).
- **Botões obrigatórios**: (1) Voltar para Dashboard (link); (2) Ir para lista
  de casos; (3) Reportar URL quebrada (mailto:suporte).

---

## 4. Qualidade & Validação: @axe-core/playwright WCAG 2.1 AA

Arquivo novo Sprint 19:
`apps/frontend/tests/e2e/accessibility-wcag-aa.spec.ts`

**4 cenários scan a11y obrigatórios em CI:**

| Teste ID | Rota | Critérios WCAG 2.1 AA aplicados |
|---|---|---|
| `a11y-01` | `/login` | 1.3.1 Info and Relationships (label inputs) |
| `a11y-02` | `/dashboard` | 1.4.3 Contraste (AA), 4.1.2 Name/Role/Value |
| `a11y-03` | `/cases` | 2.1.1 Keyboard (acessível via Tab/Shift+Tab) |
| `a11y-04` | Fluxo navegação teclado | 2.4.7 Focus Visible + ordem lógica TAB |

**Script npm adicionado**: `npm run test:a11y` → executa somente suíte a11y.

---

## 5. Arquitetura de Escalabilidade Hierárquica

```
app/
├── error.tsx      ← GLOBAL ERROR BOUNDARY (absoluto último fallback)
├── loading.tsx    ← GLOBAL SKELETON a11y
├── not-found.tsx  ← 404 navegável
├── dashboard/
│   ├── page.tsx
│   └── error.tsx  ← boundary dashboard (nível 1)
├── cases/
│   ├── [id]/
│   ├── page.tsx
│   └── error.tsx  ← boundary casos
├── ai/
│   ├── page.tsx
│   └── error.tsx  ← boundary insights IA
├── evidence/
│   ├── page.tsx
│   └── error.tsx  ← boundary evidence
└── graph/         (Sprint 21 T2-05)
    ├── page.tsx
    └── error.tsx  ← boundary graph cytoscape (render client-only)
```

### 5.1 Regra de Governança Frontend (SRP)

> **Toda nova página de domínio do produto (ex: /billing, /compliance) criada
> daqui para frente DEVE possuir seu próprio arquivo `error.tsx` de segmento,
> além da existência do global.** Ajuste via PR e verificação QA-gateway
> futura scanner.

---

## 6. Trade-offs e Consequências

### 6.1 Positivas

- **Confiança do usuário**: Quebra de componente não mais torna página branca.
- **Conformidade legal (e-MAG WCAG AA)**: Status perante auditoria acessibilidade.
- **Melhoria métrica UX INP (Interaction to Next Paint)**: Skeletons a11y
  apresentam feedback perceptível em < 200ms.
- **Playwright 38 → 45 specs** (incluindo 7 T2-05 Graph Intel): +18% cobertura E2E.

### 6.2 Negativas / Riscos

- **Aumento arquivos boilerplate**: 7 arquivos error.tsx + loading.tsx +
  not-found.tsx (2,5 KLoC) → mitigamos documentando padrão no Storybook futuro.
- **Reset granular**: `reset()` só re-renderiza a boundary — se erro ocorreu por
  server data obsoleto, o botão sozinho não resolve; precisamos pairar
  `router.refresh()` — mitigamos adicionando em todos boundary botões de retry
  + voltar dashboard (que navegação recarrega dados).

---

## 7. Definition of Done (DoD)

- [x] Pacote Frontend `version`: **`0.1.0 → 1.9.0`** (Sprint 19); **`1.9.0 → 2.0.0`** (Sprint 21 Graph Intelligence 4.0)
- [x] Pacote devDep `@axe-core/playwright@^4.10.0` instalado
- [x] Script npm `test:a11y` adicionado package.json
- [x] 4 Testes WCAG AA a11y.spec.ts Playwright 100% verde em homologação
- [x] 7 arquivos `error.tsx` + `loading.tsx` + `not-found.tsx` validados
- [x] Novo boundary: `app/graph/error.tsx` Cytoscape segmento
