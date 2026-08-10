# Checklist M5 Sign-Off Operacional — 6 Assinaturas + 3 Revogações + 14 Passos
### Governança v5.16.0 (Baseline v1.9 / Sprint 28+2 / HEAD `d471ca8`)
**Prazo máximo:** 2026-08-12 23:59 UTC-3 (BRT). Após → NOVO sign-off do zero.

---

## 🚨 ANTES DE TUDO: Revogar 3 Credenciais Reais (P0)
Se qualquer uma abaixo estiver **Não Revogado** → **NÃO ASSINAR**. Cancelar operação.

| # | Credencial | Console (link) | Status | Data Revogação | Anexo (Screenshot) |
|:-:|-----------|---------------|--------|---------------|--------------------|
| **R1** | **Groq API Key** `gsk_9l…Ra90v` (apps/ai-service + shared) | console.groq.com/api-keys | ☐ Revogado / ☐ Não | ____/____/________ | ☐ Anexado |
| **R2** | **Infura Project ID + Secret** `WEB3_INFURA_*` | app.infura.io/dashboard | ☐ Revogado / ☐ Não | ____/____/________ | ☐ Anexado |
| **R3** | **Alchemy API Key** `ALCHEMY_API_KEY` (compliance/monitoring/investigation) | dashboard.alchemy.com/apps | ☐ Revogado / ☐ Não | ____/____/________ | ☐ Anexado |

> **Checkpoint 0:** TODAS R1+R2+R3 = ☐ Revogado (3/3) ☐ ❌ FALTAM → (abortar)

---

## 🔐 Condição 3A (TODOS = SIM. NÃO ACEITA PARCIAL.)
Aprovada pela Engenharia Executora + Arquiteto.

| # | Item | Critério | Status |
|:-:|------|----------|--------|
| **3A.1** | TruffleHog Q5 only-verified HIGH = 0 segredos | `qa-gateway scan-secrets-trufflehog --only-verified --strict ... exit=0` | ☐ SIM (exit 0) / ☐ NÃO |
| **3A.2** | Método Push não é Basic Auth nem PAT Classic sem SSO | (A) JWT GitHub App 10min / (B) PAT Fine SSO SAML / (C) SSH Deploy Ed25519 | ☐ SIM (escolha A/B/C abaixo) / ☐ NÃO |
| **3A.3** | 6 Assinaturas válidas + data dentro 48h (Seção 4 abaixo) | Todas preenchidas | ☐ SIM / ☐ NÃO |
| **3A.4** | Arquivos IMUTÁVEIS LGPD = 0 touch | `grep` em diff docs/governance-weekly, history, assessments, github_main → vazio | ☐ SIM / ☐ NÃO |

> **Checkpoint 3A:** 4/4 = ☐ SIM → **LIBERADO**. Qualquer NÃO → ABORTAR.

**Método de Push Remoto ESCOLHIDO (marcar 1 único):**
- ☐ **(A) RECOMENDADO — GitHub App JWT short-lived (≤10 min)** (não precisa deletar, expira sozinho)
- ☐ **(B) PAT Fine-Grained SSO SAML (repo:contents:write + workflow:read)** (deletar Step 14)
- ☐ **(C) SSH Deploy Key Ed25519 (único repo)** (deletar Step 14)

---

## 🧪 14 Passos Procedimento (Engenheiro Executor + Arquiteto = 4-Olhos)
Executar em ORDEM. Pular = CANCELA.

| Passo | Descrição (conferir) | Responsável | Data Horário (DD/MM HH:MM) | Evidência / Link | OK |
|:-----:|----------------------|-------------|-----------------------------|-----------------|:--:|
| **01** | Snapshot criptografado wd AES256-GCM (Vault `ontrackchain/m5-snapshots`) | Eng + Arq | __/__ ____:__ | SHA256 pré-encrypt: `0x____________________` | ☐ |
| **02** | `git clean -ndfx` + `git clean -dfx` (NÃO remover .env*.private, tmp/, github_main/) | Eng | __/__ ____:__ | `dry-run output: ` | ☐ |
| **03** | `git fetch origin main --prune` + `ahead` = 29 commits locais (29 antes, após este doc = 30) | Eng + Arq | __/__ ____:__ | `ahead=$(git rev-list --count origin/main..HEAD) = ___` | ☐ |
| **04** | **IMUTÁVEIS 0 commits:** `git diff --name-only origin/main..HEAD | grep ...` → VAZIO | Arq + CLO (ou tela) | __/__ ____:__ | `exit = 1 (grep no hit)` → SIM | ☐ |
| **05** | **Q1 RBAC:** `qa-gateway scan-rbac --strict --max-warnings=0` exit=0 | Eng | __/__ ____:__ | exit 0, 0 issues, 5 W005 isentos | ☐ |
| **06** | **Q2 Billing Cap + Q3 Enf:** 2 exit=0 (só ignora BW-003/BE-003 import error sandbox) | Eng | __/__ ____:__ | exit cap 0 / enf 0 | ☐ |
| **07** | **Q4 LGPD ROPD + Q5 SECRETS:** Q4 exit=0, **Q5 NÚMERO = 0** segredos HIGH only-verified | Eng + Arq | __/__ ____:__ | Q4=0 / **Q5=0** (qualquer outro número → ❌) | ☐ |
| **08** | Teste autenticação método (A/B/C): NÃO pode retornar Permission denied | Eng + CTO | __/__ ____:__ | output: | ☐ |
| **09** | 🚨 **PUSH REMOTO MOMENTO:** `git push origin main`. Mostrar tela compartilhada ≥1 signatário | Eng EXCLUSIVO | __/__ ____:__ | `… xxxxx..yyyyyyy  main -> main` | ☐ |
| **10** | PUSH VALIDO: `git fetch --prune` + `ahead = 0` (ZERO). Qualquer outro → investigar (sem rebase force!) | Eng + Arq | __/__ ____:__ | `ahead=$(…) = 0` ✅ | ☐ |
| **11** | Notificar: (1) Slack #m5-governanca-risco @here (2) SIEM Splunk correlation ID `OTK-M5PUSH-…` | Eng | __/__ ____:__ | Slack link: / SIEM CID: | ☐ |
| **12** | Commit **este documento ASSINADO** + 2º push pequeno (agora 0 → 1 → 0 ahead). | Arq + Eng | __/__ ____:__ | Commit SHA doc: `___` (último push 0 ahead) | ☐ |
| **13** | Ativar Workflow Pre-Merge ADR-029: `on: pull_request + workflow_dispatch` + vars repo: `DPO_EMAIL`, `OTK_CI_PRE_MERGE_ENFORCE_ALL=true`. Rodar 1x workflow_dispatch. | CTO + Arq | __/__ ____:__ | Workflow Run ID: `___` (gates Q1-Q5 = PASS) | ☐ |
| **14** | Cleanup credencial provisória: se B (PAT Fine) ou C (SSH Deploy Key) → **DELETAR agora** (confirma tela "não encontrado"). A (JWT) expira sozinho. | DSI + Eng | __/__ ____:__ | Screenshot delete API / UI: ☐ Anexado | ☐ |

> **Checkpoint Final 14 Passos:** 14/14 ☐ OK → ✅ CONCLUÍDO. Registrar passo 15 no SIEM.

---

## ✍️ Assinaturas 6 Pessoas (4 Diretoria + 2 Operacionais)
Assinar **SOMENTE APÓS** (1) R1+R2+R3 revogados, (2) 3A todos SIM, (3) 14 passos 14/14 OK.

### 1. CLO (Diretor Jurídico — LGPD + BACEN, OAB obrigatório)
| Campo | Valor (preencher manualmente) |
|---|---|
| Nome completo (sem abreviaturas) | ___________________________ |
| OAB + UF | OAB/___:__________  (obrigatório) |
| Data (DD/MM/AAAA) | ____/____/2026 |
| Assinatura Digital SHA256 (SHA256(este_doc + CPF 11 dígitos)) | `SHA256: 0x________________________________` |
| E-mail corporativo | ___________@ontrackchain.com.br |
| Assinatura Física / Eletrônica | ________________________ (assinatura) |

### 2. CTO (Diretor de Tecnologia — Risco Técnico)
| Campo | Valor |
|---|---|
| Nome completo | ___________________________ |
| Cargo | Chief Technology Officer |
| Data | ____/____/2026 |
| Assinatura Digital SHA256 | `SHA256: 0x________________________________` |
| E-mail corporativo | ___________@ontrackchain.com.br |
| Assinatura | _________________________ |

### 3. DPO (Encarregado LGPD — LGPD Art.43 §4)
| Campo | Valor |
|---|---|
| Nome completo | Dr. Carlos Eduardo Mendes (contato já cadastrado em ROPDs) |
| Cargo / Registro ANPD (se aplicável) | Data Protection Officer |
| Data | ____/____/2026 |
| Assinatura Digital SHA256 | `SHA256: 0x________________________________` |
| E-mail corporativo | dpo@ontrackchain.com.br |
| Assinatura | _________________________ |

### 4. CEO (Diretor Executivo — Aprovação Final)
| Campo | Valor |
|---|---|
| Nome completo | ___________________________ |
| Cargo | Chief Executive Officer |
| Data | ____/____/2026 |
| Assinatura Digital SHA256 | `SHA256: 0x________________________________` |
| E-mail corporativo | ___________@ontrackchain.com.br |
| Assinatura | _________________________ |

### 5. Arquiteto de Software (Validação Arquitetural + Segurança)
| Campo | Valor |
|---|---|
| Nome completo | ___________________________ |
| CREA (se aplicável) / Certificação | CREA-___:_________  (opcional) |
| Data | ____/____/2026 |
| Assinatura Digital SHA256 | `SHA256: 0x________________________________` |
| E-mail corporativo | architecture@ontrackchain.com.br |
| Assinatura | _________________________ |

### 6. Engenheiro Executor (Quem executa os 14 passos)
| Campo | Valor |
|---|---|
| Nome completo | ___________________________ |
| Cargo / Matrícula CLT | ___________________________ |
| Data | ____/____/2026 |
| Assinatura Digital SHA256 | `SHA256: 0x________________________________` |
| E-mail corporativo | ___________@ontrackchain.com.br |
| Assinatura | _________________________ |

---

## 📎 Anexos Obrigatórios (TODOS = ☐ Anexado)
- [ ] Anexo A1: Screenshot R1 (Groq API Key Revogada — console.groq.com)
- [ ] Anexo A2: Screenshot R2 (Infura Project ID + Secret — Deleted)
- [ ] Anexo A3: Screenshot R3 (Alchemy App — API Key Deleted)
- [ ] Anexo B: Log Q5 TruffleHog completo `/tmp/q5-trufflehog.log` (exit 0, 0 HIGH)
- [ ] Anexo C: Push Step09 tela compartilhada (screenshot terminal)
- [ ] Anexo D: Workflow Pre-Merge ADR-029 Run Step13 (Screenshot Actions → Run)
- [ ] Anexo E: Credencial Deletada Step14 (screenshot "não encontrado" se método B ou C)
- [ ] Anexo F: Evidência SIEM Step11 (log do correlation ID OTK-M5PUSH-…)
- [ ] Anexo G: Hash Baseline v1.9 (arquivo `baselines/BASELINE-v1.9-SPRINT-28-2-HEAD-d471ca84.md`) → não contradiz HEAD SHA atual após pushes.

**Controle de Anexos:** __/__ anexos presentes ☐ COMPLETO ☐ INCOMPLETO

---

## ✅ Fim do Checklist
Quando 6 assinaturas + 3 revogações + 14 passos + 9 anexos = 100% →
M5 Bloqueio Push Remoto é **REMOVIDO TEMPORARIAMENTE** até 2026-08-12 23:59 BRT.
Após horário, bloqueio retorna automaticamente; novo push exige novo sign-off completo.
