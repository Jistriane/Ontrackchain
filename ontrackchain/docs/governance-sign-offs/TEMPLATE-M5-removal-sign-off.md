# TEMPLATE - Sign-off 4-Olhos Remoção Bloqueio M5 Push Remoto

Referência legal / governança: **ADR-026 M5 Governança Risco P0 + LGPD Art.52 §II Multa até 2% faturamento anual no Brasil**

---

## 0. Regras deste documento

ESTE ARQUIVO É **OBRIGATÓRIO** antes de QUALQUER `git push origin/main` que sincronize os commits locais (21 commits ahead até Sprint 25) com a origin remota GitHub. Sem a assinatura das 4 partes abaixo (ou justificativa de falta de uma delas aprovada por maioria), NENHUM engenheiro tem permissão de executar `git push`. Nenhuma exceção.

- Nome do arquivo após clone do template → renomear para `M5-removal-YYYY-MM-DD.md` (ex: `M5-removal-2026-08-10.md`)
- Data do sign-off = data do preenchimento; data do push = data da execução (podem ser datas diferentes)

---

## 1. Informações Básicas da Operação

| Campo | Valor a preencher |
|---|---|
| **Data do sign-off (dd/mm/aaaa)** | __/__/____ |
| **Descrição objetiva do motivo do push** (ex: release v6.0.0 homologação prod deploy, correção P0 bug MFA, etc.) | |
| **Quantidade commits a serem enviados (ahead origin/main)** | |
| **Método de push aprovado (ADR-026 Opção C / Recomendado)** | `GitHub App PEM private key short-lived JWT (90s)` ☐ ou `Personal Access Token SSO SAML` ☐ ou `SSH deploy key (ed25519)` ☐ |
| **Data de execução prevista do `git push` (máximo 48h após sign-off)** | __/__/____ (se passar de 48h, novo sign-off obrigatório) |
| **Janela de execução** (ex: 09:00-10:00 horário comercial 2 engenheiros online) | |

---

## 2. Condição 3A - Pré-requisitos cumulativos (TODOS devem ter `SIM`)

| Item Obrigatório | Cumprido? (SIM / NÃO) | Evidência / link |
|---|---|---|
| **Condição 3A-1**: TruffleHog secrets scanner rodou em TODO o repositório (workspace inteiro). Nenhum high-severity secret (AWS AKIA, GitHub PAT `ghp_*`, Stripe `sk_live_*`, private key RSA/EC, client_secret OIDC) encontrado. **Se algum encontrado, bloqueio permanece, remover antes de preencher.** | ☐ SIM ☐ NÃO | Arquivo de log trufflehog: `tmp/trufflehog-secrets-YYYYMMDD.json` (apagado após confirmação) |
| **Condição 3A-2**: Método de push seguro não é `HTTPS password basic auth` nem `credencial em arquivo .netrc`. Método confirmado: GitHub App short-lived JWT OU PAT SSO OU SSH deploy key (único propósito), com validade máxima de 24h após o push (rotacionar 1 vez antes de 24h passar). | ☐ SIM ☐ NÃO | |
| **Condição 3A-3**: Sign-off 4-olhos de 4 cargos abaixo (CTO, DSI, CEO, Arquiteto). Todos assinaram com data e nome completo. Se qualquer um dos 4 faltar, **bloqueio M5 NÃO pode ser suspenso.** | ☐ SIM ☐ NÃO | Bloco 4 abaixo |
| **Condição 3A-Extra (NÃO obrigatória, recomendada)**: Duplicate push para mirror de backup (AWS CodeCommit / Gitlab privado) durante a mesma janela, para redundância. | ☐ SIM ☐ NÃO | |

---

## 3. Procedimento de 14 Passos (Execução do Push)

1.  ☐ 00h00m - Criar snapshot .tar.gz criptografado AES-256 do repositório antes do push (incluindo .git). Guardar hash SHA-256 em local separado.
2.  ☐ Garantir que `git status --porcelain` retorna VAZIO (NENHUM arquivo unstaged ou untracked não-stageado).
3.  ☐ `git fetch origin main` + `git log --oneline origin/main..HEAD | wc -l` confirma contagem ahead igual ao item 1.3.
4.  ☐ Confirmar IMUTÁVEIS LGPD não tem commits: `git log --oneline origin/main..HEAD -- docs/governance-weekly/ docs/history/ docs/assessments/ github_main/` retorna VAZIO.
5.  ☐ Rodar qa-gateway scan-billing-capabilities --strict --max-warnings 0 → exit 0
6.  ☐ Rodar qa-gateway scan-billing-enforcement --strict --max-warnings 0 → exit 0
7.  ☐ Rodar qa-gateway scan-lgpd-ropd --strict --max-warnings 0 → exit 0
8.  ☐ Rodar qa-gateway scan-rbac --strict → exit 0
9.  ☐ Rodar trufflehog filesystem --no-update . → 0 segredos high (3A-1)
10. ☐ Login no método de push aprovado (GitHub App JWT, PAT SSO, etc) → validar com `gh auth status` ou equivalente.
11. ☐ `git push origin main` apenas na BRANCH `main`. NÃO forçar push (--force proibido, exceto em incidente P0 com sign-off EXTRA).
12. ☐ Confirmar `git rev-list --count origin/main..HEAD` == 0 após push. Verificar GitHub UI que os commits apareceram.
13. ☐ Notificar time via canal oficial Slack/MS Teams: "M5 Push remoto concluído, N commits enviados, data XX, método YY, sem segredos encontrados".
14. ☐ Salvar este documento preenchido em `docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md` + COMMITAR + FAZER PARTE DO PRÓXIMO push. Procedimento completo.

---

## 4. Assinaturas 4-Olhos Obrigatórias (ADR-026 Condição 3A)

> IMPORTANTE: **As assinaturas abaixo são documentos jurídicos e atestam responsabilidade individual** em caso de incidente de vazamento de dados / violação LGPD Art.52. Não assine sem ler TODO o documento, blocos 1-3.

| Cargo | Nome Completo | Assinatura (texto) | Data | E-mail profissional |
|---|---|---|---|---|
| **CTO (Chief Technology Officer)** | | | __/__/____ | |
| **DSI (Diretor Segurança Informação / CISO)** | | | __/__/____ | |
| **CEO (Chief Executive Officer)** | | | __/__/____ | |
| **Arquiteto Chefe / Sênior Responsável** | | | __/__/____ | |

### Observações / Diligência Extra:

---

## 5. Assinatura Engenheiro(a) que Executará o `git push`

| Nome Engenheiro(a) | Assinatura | Data execução | E-mail |
|---|---|---|---|
| | | __/__/____ | |

---

> "Declaro, para os devidos fins de direito, que li o presente termo, verifiquei os itens 3A, os procedimentos de 14 passos, e assumo responsabilidade pela liberação e execução do M5 Push Remoto no dia indicado, sob pena das sanções legais cabíveis (LGPD e/ou CLT, conforme vínculo empregatício). Confirmo que NENHUM dado pessoal ou segredo de negócio foi exfiltrado propositalmente nesta operação."
