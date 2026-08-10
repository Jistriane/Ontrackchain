# Planilha de Assinatura Consolidada — Todos os 29 ADRs Ontrackchain (001..029)

*Documento de governança jurídica oficial. Toda decisão arquitetural de impacto exige assinatura do Diretor Jurídico/CLO ou seu substituto legal. Aderência ao regime ANPD CD-004/2023 (LGPD Art.8, Art.14, Art.48) e BACEN Circular X Art.12 (Due Diligence Cadastro).*

**ID do documento:** SIGNOFF-ADRS-ALL-29-v1.0
**Data de emissão:** 2026-08-10
**Vigência:** 12 meses (até 2027-08-10), conforme LGPD Art.15 §3 RIPD revisão
**Orgão responsável:** Ontrackchain Soluções em RegTech LTDA — CNPJ 00.000.000/0001-00 (fictício)
**Emissor:** Conselho Executivo — CTO, CLO, CEO, DPO, Arquiteto Sênior
**Status global inicial:** 🔴 PENDENTE (29 ADRs, 0 assinados, 0 rejeitados)
**Regra de maioria:** Aprovação exige 29/29 = 100% dos ADRs marcados "Aprovado". **Qualquer ADR = Rejeitado/Pendente → bloqueia sign-off M5 (ADR-026 Condição 3A).**

---

## Campos por linha (1 linha = 1 ADR)

| Campo | Obrigatorio? | Descrição |
|---|---|---|
| Data Assinatura | SIM | DD/MM/AAAA |
| ADR ID | SIM | "ADR-001" até "ADR-029". NÃO admite números fora do intervalo. |
| Título ADR | SIM (auto-preenchido) | Copiado do arquivo `docs/adrs/README.md` índice oficial. |
| Nome Completo Assinante | SIM | Nome civil completo, sem abreviaturas. Deve ser Diretor Jurídico/CLO ou procurador com poderes explícitos. |
| Cargo Assinante | SIM | "CLO - Chief Legal Officer", "Diretor Jurídico", "Procurador Legal Ontrackchain" com registro OAB. |
| OAB/SP (ou equivalente) | SIM caso seja advogado | Número OAB + UF. Obrigatorio para advogados signatários. |
| Status | SIM ENUM | `Aprovado` / `Rejeitado` / `Pendente - Justificativa abaixo` |
| Justificativa (se não Aprovado) | SIM se != Aprovado | Texto descrevendo motivo de rejeição ou item pendente. **Deve referenciar artigo ANPD, BACEN, LGPD, CLT ou norma internacional aplicada (ISO 27001, NIST SP 800-53, SOC2 CC6.1) com número.** |
| Assinatura Eletrônica | SIM | Hash SHA-256 do arquivo ADR específico concatenado com CPF assinante. Formato: `SHA256: HEX64`. Gerado via `sha256sum ontrackchain/docs/adrs/ADR-XXX-*.md` + `cpf_hash = sha256(cpf_11digitos)` → concat → SHA256 novamente. |
| Email Corporativo Assinante | SIM | Formato `nome.sobrenome@ontrackchain.com.br`. Não aceita email público. |
| Revisão 12 meses (próxima) | AUTO | Data = Data Assinatura + 12 meses |

---

## TABELA DE ASSINATURAS — 29 ADRs (001..029)

Ordem de classificação: impacto regulatório decrescente (LGPD → BACEN → Cibersegurança → Operacional).

| # | Data | ADR ID | Título ADR Oficial | Nome Assinante | Cargo | OAB | Status | Justificativa (se Rejeitado/Pendente) | Assinatura SHA256 | Email | Próx Rev 12m |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | _vazia_ | ADR-028 | LGPD Art.37 ROPD Registro Operações Tratamento Dados Pessoais (7 arquivos OTK-0001..0007 + CSV) | | | | 🔴 PENDENTE | | | | |
| 2 | _vazia_ | ADR-029 | CI Pre-Merge 5 Gates FAIL-FAST Pipeline Orquestrador 4 qa-gateway scans + TruffleHog (segredos) | | | | 🔴 PENDENTE | | | | |
| 3 | _vazia_ | ADR-026 | Bloqueio Absoluto Push Remoto M5 Governança Risco Operacional Crítico (Condição 3A + Procedimento 14 passos) | | | | 🔴 PENDENTE | | | | |
| 4 | _vazia_ | ADR-021 | Compliance API Structural Screens RIPD Art.15 LGPD Due Diligence 4 Work Items Obrigatórios | | | | 🔴 PENDENTE | | | | |
| 5 | _vazia_ | ADR-019 | Public API v2.0.0 B2B Enterprise HMAC-SHA256 Timing-Safe Anti-Replay Nonce Rate Limit | | | | 🔴 PENDENTE | | | | |
| 6 | _vazia_ | ADR-027 | Billing Capabilities Enforcement Middleware Redis Fail-Closed 402 DUAL MODE | | | | 🔴 PENDENTE | | | | |
| 7 | _vazia_ | ADR-024 | Billing Stripe Multi-Tenant DUAL MODE optional-deps [stripe] Fake Fallback Contrato Idêntico | | | | 🔴 PENDENTE | | | | |
| 8 | _vazia_ | ADR-014 | Expansão da Public API e Rate Limiting (T2-05 precursor v2) | | | | 🔴 PENDENTE | | | | |
| 9 | _vazia_ | ADR-004 | Legal Report Strong Auth (BACEN Due Diligence Cadastro Relatórios) | | | | 🔴 PENDENTE | | | | |
| 10 | _vazia_ | ADR-012 | Selagem Institucional Forte para Pacotes Manuais DD SOF (SHA256 + HMAC corporativo) | | | | 🔴 PENDENTE | | | | |
| 11 | _vazia_ | ADR-003 | Audit Request ID (Correlation ID transversal todos serviços BACEN auditoria) | | | | 🔴 PENDENTE | | | | |
| 12 | _vazia_ | ADR-017 | Evidence Event Naming AI Degraded (padroniza eventos evidência IA) | | | | 🔴 PENDENTE | | | | |
| 13 | _vazia_ | ADR-013 | Digest Canônico do Export no Showcase E2E (non-repúdio export) | | | | 🔴 PENDENTE | | | | |
| 14 | _vazia_ | ADR-006 | Identidade Federada e Usuários Locais (AD-017 precursor RBAC OTK_*) | | | | 🔴 PENDENTE | | | | |
| 15 | _vazia_ | ADR-007 | Validação por Modo de Autenticação (MFA YubiKey precursor) | | | | 🔴 PENDENTE | | | | |
| 16 | _vazia_ | ADR-018 | qa-gateway SSOT RLS Shared First Fallback Inline 4 Gates (RBAC RIPD Secrets Billing) | | | | 🔴 PENDENTE | | | | |
| 17 | _vazia_ | ADR-001 | RLS Multi-Tenant (PostgreSQL 16 Row Level Security) | | | | 🔴 PENDENTE | | | | |
| 18 | _vazia_ | ADR-008 | Retention e Recovery Baseline (LGPD Art.15 retenção 36/60/120 meses) | | | | 🔴 PENDENTE | | | | |
| 19 | _vazia_ | ADR-025 | Load Testing k6 Thresholds SLA Rigorosamente Definidos por Rota Crítica | | | | 🔴 PENDENTE | | | | |
| 20 | _vazia_ | ADR-020 | Frontend Next.js App Router Error Boundaries Global WCAG AA Loading Skeletons | | | | 🔴 PENDENTE | | | | |
| 21 | _vazia_ | ADR-022 | Graph Intelligence 4.0 Cytoscape Counterparty↔Wallet↔Risk Network SSRF Safe Fetch | | | | 🔴 PENDENTE | | | | |
| 22 | _vazia_ | ADR-009 | Continuation Strategy Hardening First (continuidade negócio desastre) | | | | 🔴 PENDENTE | | | | |
| 23 | _vazia_ | ADR-005 | Investigation Concurrency MVP (FOR UPDATE SKIP LOCKED PG) | | | | 🔴 PENDENTE | | | | |
| 24 | _vazia_ | ADR-010 | Promoção de Maturidade Baseada em Evidência (ADR-025 precursor SLA) | | | | 🔴 PENDENTE | | | | |
| 25 | _vazia_ | ADR-011 | Hardening Estático de Contratos Visuais do Frontend (Playwright snapshot) | | | | 🔴 PENDENTE | | | | |
| 26 | _vazia_ | ADR-015 | Futuro do Módulo Team (Roadmap equipe colaboração) | | | | 🔴 PENDENTE | | | | |
| 27 | _vazia_ | ADR-023 | CHANGELOG Hierárquico por Sprint Keep a Changelog 1.1.0 + SemVer 2.0.0 | | | | 🔴 PENDENTE | | | | |
| 28 | _vazia_ | ADR-002 | Billing Quote Plan Lock (trava orçamento plano contratual) | | | | 🔴 PENDENTE | | | | |
| 29 | _vazia_ | ADR-016 | (RESERVADO PARA FUTURO ADR) — vago. Descoberto gap índice 16→17. Manter linha reservada. | | | | 🟡 RESERVADO | | | | |

---

## Painel Resumo (auto-preenchido após preenchimento tabela)

| Métrica | Valor | Status |
|---|---|---|
| Total ADRs | 29 | ✅ |
| Aprovados | 0/29 | 🔴 **PENDENTE JURÍDICO** |
| Rejeitados | 0 | 🟢 |
| Pendentes | 28/29 | 🔴 |
| Reservados (ADR-016 vago) | 1/29 | 🟡 (não bloqueia sign-off) |
| **Condição 3A do M5 (ADR-026)** | 29/29 aprovados exceto reservado? | **❌ NÃO CUMPRIDA — bloqueia push remoto** |

---

## Bloco de Assinatura 4-Olhos (Conselho Executivo — sign-off FINAL do consolidado 29 ADRs)

**Assinatura 1 — CLO / Diretor Jurídico:**
| Campo | Valor |
|---|---|
| Nome Completo | _vazio_ |
| Cargo | Chief Legal Officer |
| OAB | _vazio_ |
| Data | DD/MM/AAAA |
| Assinatura Eletrônica SHA256 | `SHA256: 0x___` |
| Email | `nome@ontrackchain.com.br` |

**Assinatura 2 — CTO:**
| Campo | Valor |
|---|---|
| Nome Completo | _vazio_ |
| Cargo | Chief Technology Officer |
| CREA (se aplicável) | _vazio_ |
| Data | DD/MM/AAAA |
| Assinatura Eletrônica SHA256 | `SHA256: 0x___` |
| Email | `nome@ontrackchain.com.br` |

**Assinatura 3 — DPO (Encarregado LGPD Art.41):**
| Campo | Valor |
|---|---|
| Nome Completo | Dr. Carlos Mendes (referência RIPD mestre) |
| Cargo | DPO - Data Protection Officer Ontrackchain |
| CRP/SP + OAB/SP | _vazio_ |
| Data | DD/MM/AAAA |
| Assinatura Eletrônica SHA256 | `SHA256: 0x___` |
| Email | `dpo@ontrackchain.com.br` |

**Assinatura 4 — CEO / Representante Legal Controladora LGPD Art.5º II:**
| Campo | Valor |
|---|---|
| Nome Completo | _vazio_ |
| Cargo | Chief Executive Officer / Representante Legal Ontrackchain |
| Data | DD/MM/AAAA |
| Assinatura Eletrônica SHA256 | `SHA256: 0x___` |
| Email | `ceo@ontrackchain.com.br` |

**Assinatura 5 — Arquiteto Sênior Responsável Técnico:**
| Campo | Valor |
|---|---|
| Nome Completo | _vazio_ |
| Cargo | Arquiteto de Software Sênior / Liderança Técnica |
| Data | DD/MM/AAAA |
| Assinatura Eletrônica SHA256 | `SHA256: 0x___` |
| Email | `arquiteto@ontrackchain.com.br` |

---

### Notas Internas (Apenas Ontrackchain — NÃO publica p/ cliente ou auditor)

1. O **ADR-016 ausente no índice** (contagem README.md era 001..015 → pulou para 017) é flag documental. **Não é risco técnico.** Preencher ADR-016 no futuro com qualquer decisão nova (ex: "ADR-016 Observabilidade OpenTelemetry OTLP v1.0.0"). Atualizar esta planilha linha 29 de RESERVADO para ADR-016 quando acontecer.
2. Prazo ideal para 29/29 Aprovação: **antes do sign-off M5 (P0-03)**. Ordem recomendada de assinatura por impacto: Linhas 1→8 primeiro (LGPD/BACEN/Billing), depois 9→16, depois 17→28.
3. Assinaturas em papel físico com firma autenticada em cartório são **permitidas como substituto** do hash SHA256 eletrônico, desde que o digitalizador do PDF assinado seja anexado em `docs/governance-sign-offs/assinaturas-fisicas/` com nome `SIGNOFF-ADR-XXX-YYYY-MM-DD.pdf` e referenciado neste CSV consolidado.
4. Rejeição de qualquer ADR exige **novo commit** do ADR rejeitado com ajuste, **nova revisão + versão minor ADR**, e nova submissão para assinatura nesta planilha. Processo: rejeição → comentário GitHub issue → PR com ajuste → merge local → nova linha nesta planilha status "Aprovado".
5. LGPD Art.8 §5: o controladora deve manter registro das decisões arquiteturais que afetem tratamento de dados pessoais. Esta planilha é o registro oficial para ANPD em caso de auditoria. Prazo apresentação ANPD: até 15 dias corridos após solicitação (LGPD Art.59).
