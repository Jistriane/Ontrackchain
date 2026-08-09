# ADRs

Este diretorio concentra as Architectural Decision Records do scaffold atual.

## ADRs Atuais

- [ADR-001 — Isolamento Multi-tenant com RLS](./ADR-001-rls-multi-tenant.md)
- [ADR-002 — Billing por Quote com Plan Lock](./ADR-002-billing-quote-plan-lock.md)
- [ADR-003 — Auditoria Correlacionada por Request ID](./ADR-003-audit-request-id.md)
- [ADR-004 — Legal Report com Strong Auth e 2FA](./ADR-004-legal-report-strong-auth.md)
- [ADR-005 — Concorrencia MVP com Fila Leve](./ADR-005-investigation-concurrency-mvp.md)
- [ADR-006 — Identidade Federada e Users Locais](./ADR-006-identidade-federada-e-users-locais.md)
- [ADR-007 — validação por Modo de autenticação](./ADR-007-validacao-por-modo-de-autenticacao.md)
- [ADR-008 — Retention e Recovery Baseline](./ADR-008-retention-e-recovery-baseline.md)
- [ADR-009 — Continuidade: Hardening First e Modularização Guiada](./ADR-009-continuation-strategy-hardening-first.md)
- [ADR-010 — Promocao de Maturidade Baseada em evidência](./ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)
- [ADR-011 — Hardening Estatico de Contratos Visuais do Frontend](./ADR-011-hardening-estatico-de-contratos-visuais-do-frontend.md)
- [ADR-012 — Selagem Institucional Forte para Pacotes Manuais DD/SoF](./ADR-012-selagem-institucional-forte-para-pacotes-manuais-dd-sof.md)
- [ADR-013 — Digest canônico do Export no Showcase E2E](./ADR-013-digest-canonico-do-export-no-showcase-e2e.md)
- [ADR-014 — Expansão da Public API e Rate Limiting por IP com Cache CDN](./ADR-014-expansao-da-public-api-e-rate-limiting.md)
- [ADR-015 — Futuro do Modulo Team](./ADR-015-futuro-do-modulo-team.md)
- [ADR-016 — Estrategia de Vault e Secrets para Producao](./ADR-016-estrategia-de-vault-e-secrets-para-producao.md)
- [ADR-017 — Nomeação de Eventos de Evidência para IA (AI_DEGRADED)](./ADR-017-evidence-event-naming-ai-degraded.md)
- [ADR-018 — QA Gateway como Single Source of Truth para RLS + Shared First / Fallback Inline](./ADR-018-qa-gateway-ssot-rls-shared-first-fallback-inline.md)
- [ADR-019 — Public API v2.0.0 B2B Enterprise com Autenticação HMAC-SHA256 Timing-Safe e Anti-Replay](./ADR-019-public-api-v2-b2b-hmac-authentication-monetization.md)
- [ADR-020 — Frontend Next.js App Router: Error Boundaries Global + Segmentos + WCAG AA Loading Skeletons a11y](./ADR-020-frontend-nextjs-error-boundaries-wcag-aa-loading-skeletons.md)
- [ADR-021 — Compliance API Structural Screens RIPD Art.15 LGPD Due Diligence + Source of Funds CRUD](./ADR-021-compliance-api-structural-screens-lgpd-ripd-art15.md)
- [ADR-022 — Graph Intelligence 4.0 Cytoscape.js Counterparty↔Wallet↔Risk Network Multi-Layout Frontend](./ADR-022-graph-intelligence-4-cytoscape-counterparty-wallet-risk-network.md)
- [ADR-023 — CHANGELOG Oficial Hierárquico por Sprint Keep a Changelog 1.1.0 + SemVer 2.0.0](./ADR-023-changelog-hierarquico-keep-a-changelog-semver-sprint.md)
- [ADR-024 — Billing Stripe Multi-Tenant DUAL MODE optional-deps group [stripe] Fake Fallback contrato idêntico](./ADR-024-billing-stripe-multi-tenant-dual-mode-optional-sdk.md)
- [ADR-025 — Load Testing k6 Thresholds SLA Rigorosamente Definidos por Rota Crítica](./ADR-025-load-testing-k6-thresholds-sla-rigoroso-por-rota-critica.md)
- [ADR-026 — Bloqueio Absoluto Push Remoto M5 Governança de Risco Operacional Crítico Condição 3A](./ADR-026-m5-bloqueio-absoluto-push-remoto-risco-operacional-critico.md)
- [ADR-027 — Billing Capabilities Enforcement Middleware Redis Compartilhado Fail-Closed 402 DUAL MODE InMemory](./ADR-027-billing-capabilities-enforcement-middleware-redis-failclosed-402-dual-mode.md)
- [ADR-028 — LGPD Art.37 Registro Operações Tratamento Dados Pessoais (ROPD) Markdown CSV qa-gateway scan](./ADR-028-lgpd-ropd-artigo37-registro-operacoes-tratamento-dados-pessoais.md)
- [ADR-029 — Pre-Merge Gate CI Pipeline 5 Gates (qa-gateway ×4 + TruffleHog) Orquestrador run-pre-merge-gates](./ADR-029-ci-pre-merge-gate-pipeline-5-qa-gateway-4-scans-trufflehog.md)

## Como usar

- criar um novo ADR sempre que houver decisao estrutural relevante
- registrar contexto, decisao, trade-offs e consequencias
- atualizar ou substituir ADR somente com justificativa explicita
