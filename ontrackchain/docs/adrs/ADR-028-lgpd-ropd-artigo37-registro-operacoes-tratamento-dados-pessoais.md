# ADR-028 — LGPD Art.37 Registro de Operações de Tratamento de Dados Pessoais (ROPD)

- **Status**: Aprovado Sprint 25
- **Decisores**: Arquiteto Chefe + DPO + Jurídico
- **Data de aprovação**: Sprint 25 (2026-08-09)
- **Referência Legal**: Lei Nº 13.709/2018 (LGPD), Art. 37 "Registro de operações de tratamento de dados pessoais"; Art. 42 (Direito de acesso do titular); Resolução ANPD CD-005/2023.

---

## 1. Contexto

A **Ontrackchain Regulatory Platform** processa **Dados Pessoais Sensíveis**
(CPF/CNPJ dos investigados, dados de vínculo empregatício, registros financeiros
transacionados PEPs, dados de endereço IP de clientes que consultam a API B2B,
dados biométricos dos usuários MFA WebAuthn).

LGPD Art. 37 obriga toda operadora que realiza operações de tratamento de dados
pessoais a **manter registro atualizado, em formato estruturado e interoperável**
das operações. Art. 48 §1º define **multa de até 2% do faturamento (grupo
econômico) e/ou R$ 50 Mi** se a ANPD requisitar o ROPD e NÃO houver.

Atual até S24: só tínhamos a RIPD Art.15 Due Diligence. ROPD Art.37 é uma
**obrigação complementar** (lista objetiva cada categoria de dados × base legal
× retenção × medidas de segurança). Sem ele, **não podemos passar em auditoria
ANPD Level 3**.

---

## 2. Estrutura Obrigatória do ROPD OTK (12 campos LGPD)

| Campo ROPD | Obrigatório ANPD? | Descrição |
|---|---|---|
| 1. ID operação | ✅ Sim | Código único `OTK-ROP-{NNNN}` sequencial por operação |
| 2. Nome da operação | ✅ Sim | Nome humano: "Triagem estrutural LGPD onboarding" |
| 3. Categorias titulares | ✅ Sim | Ex: Investido, Cliente PF B2B, Funcionário OTK |
| 4. Categorias dados pessoais | ✅ Sim | CPF, RG, Telefone, Email, IP, Biometria WebAuthn |
| 5. Categorias dados sensíveis? | ✅ Sim | Dados sobre saúde, origem racial/étnica, vida sexual/religiosa, biometria (SIM/NÃO e quais) |
| 6. Base legal Art.7 LGPD | ✅ Sim | I (consento), II (contrato), III (cumprimento obrigação legal/regulatória = BACEN Circular), V (legítimo interesse) |
| 7. Finalidade do tratamento | ✅ Sim | Descrição 1-3 frases. NÃO pode ser genérica. |
| 8. Compartilhamento/Transferência? | ✅ Sim | PEP OFAC feeds? AML Provider (Chainalysis/TRM/Elliptic)? País destino transferência internacional? |
| 9. Retenção máxima (meses) | ✅ Sim | Ex: RIPD due diligence = 60 meses (5 anos). Casos closed = 120 meses (10 anos). |
| 10. Destruição após retenção | ✅ Sim | Procedimento: PG `ON DELETE CASCADE soft delete expirados` + criptografia AES-256 at rest |
| 11. Medidas segurança Art.32 LGPD | ✅ Sim | Controles ISO/IEC 27001:2022 implementados (cifra TLS 1.3, WAF Cloudflare, MFA, RBAC OTK_*) |
| 12. DPO contato | ✅ Sim | Nome, email, telefone, link formulário LGPD |

---

## 3. Alternativas Avaliadas (3 Opções)

### Opção A: ROPD em planilha Excel compartilhada OneDrive RH

- **Prós**: Nenhuma. (Obrigatório ANPD, porém planilha tem risco de versões divergentes).
- **Contras**: 🔴 **Não auditável por commit Git** → se ANPD requisitar em DD-MM-YYYY, como provamos o conteúdo era o mesmo de 90 dias atrás? Sem hash SHA-256 criptografado por arquivo.
- **Complexidade**: 2h (mas risco jurídico).
- **Adequação**: ❌ Rejeitado — ANPD Art.53 poder de polícia.

### Opção B: ROPD em tabela PostgreSQL `lgpd_ropd` com migration SQL

- **Prós**: Consome enforcement billing; histórico versionado com trigger.
- **Contras**: 🟠 **Alterações no ROPD = precisam commit jurídico + sign-off DPO**.
  Tabela SQL editável por admin ≠ aprovado jurídico. Alterações ficam difíceis
  de "amarrar" a auditoria ANPD de 2 anos atrás.
- **Complexidade**: 16h migrations + admin UI.
- **Adequação**: ⚠️ Rejeitado por agora. Adiar UI para S27 quando handoff DPO.

### Opção C (RECOMENDADA): ROPD em Markdown estruturado + CSV export, pasta `docs/compliance-ropd/` versionada por Git + hash SHA-256

- **Prós**:
  1. ✅ **Git imutável**: cada alteração no ROPD = commit Git com sign-off DPO.
     Hash SHA-256 por arquivo = prova para ANPD de data.
  2. ✅ **12 campos estruturados**: Markdown tabela `| Campo | Valor |` + CSV
     export `docs/compliance-ropd/ROPD-OTK-CONSOLIDADO.csv`.
  3. ✅ **qa-gateway cmd_scan_lgpd_ropd Q3-07**: valida em PRE-MERGE HOOK se os
     12 campos existem e não estão vazios. Evita template incompleto.
- **Contras**:
  1. Primeiro preenchimento manual = 8h de trabalho jurídico/DPO.
  2. Precisa rotina de atualização trimestral (tarefa calendário).
- **Complexidade**: 8h template + 2h qa-gateway scan = 10h.
- **Adequação**: ✅ Recomendado arquitetura. Melhor equilíbrio risco/custo jurídico.

---

## 4. Decisão — Opção C (Markdown estruturado + CSV consolidado + qa-gateway scan + Git sign-off DPO)

### Lista Operações ROPD Iniciais (Sprint 25 — 7 operações obrigatórias):

| ID | Operação | Categoria Titulares | Base Legal | Retenção (meses) |
|---|---|---|---|---|
| `OTK-ROP-0001` | Onboarding estrutural triagem LGPD RIPD Art.15 | Investido / PEPs | Art.7 III (BACEN Circular 3.978 obrigação) | 60 meses (5a) |
| `OTK-ROP-0002` | Consulta B2B Public API v2 HMAC | Cliente B2B PJ + IP do cliente | Art.7 II (Contrato prestação serviço) | 12 meses |
| `OTK-ROP-0003` | Análise documental AI GPT/LLM caso investigativo | Investido | Art.7 V (Legítimo interesse prevenção fraude) | 120 meses (10a) |
| `OTK-ROP-0004` | Autenticação OIDC + MFA WebAuthn/YubiKey | Usuários otk (PF) + Biometria | Art.7 III (Controle acesso BACEN Art.12) | 36 meses (3a) |
| `OTK-ROP-0005` | Billing Stripe cadastro cliente + invoice | Cliente B2B PJ | Art.7 II (Contrato faturamento) | 60 meses (5a BACEN) |
| `OTK-ROP-0006` | Feed PEP OFAC Interpol UE tokenizado (read only) | Investido (dados públicos) | Art.7 III (obrigação legal BACEN) | 120 meses (10a) |
| `OTK-ROP-0007` | AML/KYT Provider (Chainalysis/TRM/Elliptic) compartilhamento internacional | Investido transações suspeitas | Art.7 III (BACEN Circular 3.949) | 120 meses (10a) |

---

## 5. Riscos & Mitigações

| Risco | Prob | Impacto | Mitigação |
|---|---|---|---|
| **R-028-01** ANPD requisita ROPD atualizado mas último sign-off DPO tem 9 meses | Baixa 15% | Muito alto (2% faturamento) | Tarefa cron calendário: trimestral DPO revisa + commit assinado. |
| **R-028-02** Campo 4 "Categorias Dados" incompleto (esquecemos CPF/biometria) | Média 25% | Alto | qa-gateway scan Q3-07 valida os 12 campos NÃO vazios em PRE-MERGE. |
| **R-028-03** DPO não aprova a base legal Art.7 usada (obrigação vs legítimo) | Baixa 10% | Alto | Todo ROPD só staged após merge de PR com approval DPO no GitHub CODEOWNERS `docs/compliance-ropd/**`. |

---

## 6. Definition of Done (ADR-028) — 6 Itens

- [ ] **DoD 028.1**: 7 arquivos `docs/compliance-ropd/ROPD-OTK-000{1..7}-*.md` criados com os 12 campos LGPD preenchidos (template exato ADR).
- [ ] **DoD 028.2**: `docs/compliance-ropd/ROPD-OTK-CONSOLIDADO.csv` arquivo CSV estruturado 8×13 (7 linhas + header, 13 colunas).
- [ ] **DoD 028.3**: qa-gateway `scan-lgpd-ropd` Q3-07 implementado, 5 warnings LR-001..005 + 3 issues E001/E002/E003.
- [ ] **DoD 028.4**: CODEOWNERS entry `docs/compliance-ropd/**  @dpo-otk @legal-otk` obrigatório aprovação no merge.
- [ ] **DoD 028.5**: Template sign-off M5 `docs/governance-sign-offs/TEMPLATE-M5-removal-sign-off.md` NOVO com campos CTO/DSI/CEO/Arquiteto + data + motivo do push.
- [ ] **DoD 028.6**: Baseline Executivo v1.4 96%→97% + linha S25 README tabela consolidado.

---

## 7. Referências Cruzadas

- **ADR-019 Public API v2 B2B HMAC** → OTK-ROP-0002.
- **ADR-024 Billing Stripe Multi-Tenant** → OTK-ROP-0005.
- **ADR-026 M5 Bloqueio Push Remoto** → Template sign-off M5 DOD 028.5.
- **ADR-027 Billing Enforcement** → dados billing faturamento ROPD 0005 + 0002.
