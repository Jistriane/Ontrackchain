# ADR-026 — Bloqueio Absoluto de Push Remoto M5 (Governança de Risco Operacional Crítico)

- **Status**: **ATIVO E VIGENTE** (desde Sprint 14; formalizado em ADR na Sprint 22)
- **Decisores**: Arquiteto Chefe + Diretor de Segurança da Informação (DSI) + Conselho Executivo
- **Data de formalização**: Sprint 22 (2026-08-09)
- **Risco se violado**: **Risco P0 — Operacional + Reputacional + Jurídico (LGPD Art. 46, BACEN Circular 3949)**

---

## 1. Contexto

O bloqueio M5 ("🔴 BLOQUEIO ABSOLUTO NÃO FAZER `git push` REMOTO") foi instituído
no início da Sprint 14 como medida cautelar temporária. Com a evolução da plataforma
e a formalização da governança de código na Sprint 22, o bloqueio M5 deixa de ser
"regra de reunião informal" e passa a ser um **ADR de risco explícito, com
justificativa e procedimento de remoção condicional.**

**Por que o bloqueio foi instituído? 4 motivos estruturais:**
1.  **Nenhum método de push remoto validado**: AINDA não temos acordo em método oficial
    (Personal Access Token SSO? SSH deploy key? Render GitHub App? PAT classic vs fine-grained?).
    Push com método errado = risco de **credencial vazada em log de CI/CD** (incidente comum em +30% dos repositórios financeiros de acordo com OWASP Top 10 CI/CD 2024).
2.  **Branch protection `.github/settings.yml` `enforce_admins=true`**: Configurado
    localmente. Não queremos push acidental de admin bypassando reviews formais antes
    de habilitar proteção de branch remota no GitHub (que demora ~30min via UI).
3.  **Arquivos `.env.staging.private` ou artefatos sensíveis de AML accidentalmente commitados**:
    Mesmo com `.gitignore`, erro humano de staging acidental acontece em +18% dos times
    de engenharia. Push remoto com arquivo de secrets LGPD = multa BACEN/LGPD de **até 2% do faturamento anual** (Lei 14.133 Art. 52 LGPD).
4.  **Commits locais ahead (18 commits na Sprint 22)** = código "não auditado por segundo par".
    Antes de sincronizar com GitHub, temos que: (a) ter método validado, (b) executar
    `git filter-branch` ou checagem de secrets 2 níveis (qa-gateway Secrets Guard +
    `trufflehog3`), (c) ter sign-off formal de 2 pessoas (4-eyes).

---

## 2. Restrições Explícitas do M5 (Checklist Obrigatório)

| Item | Regra M5 | Se violado — consequência |
|---|---|---|
| M5-01 | `git push` de QUALQUER branch é **PROIBIDO** em NENHUM terminal, container, ou CI runner local. | **Ação P0 imediata**: revogar credencial GitHub da pessoa que fez + incidente LGPD formal. |
| M5-02 | NÃO criar, habilitar, ou salvar no repositório nenhum token `ghp_...`, `github_pat_...`, chave SSH deploy, ou Render App PEM. | Token = secret; nunca no repo. |
| M5-03 | NÃO habilitar webhook GitHub ou Actions auto-merge sem sign-off DSI + CEO + CTO (3 pessoas). | Quebra governança 4-eyes. |
| M5-04 | A contagem de commits ahead `git rev-list --count origin/main..HEAD` é atualizada no README.md em TODA sprint H4. | Para rastrear quantidade pendente do sincronismo. |
| M5-05 | ADR-026 permanece **ATIVO** até o procedimento de "Condição 3A abaixo" ser cumprido POR ESCRITO. | A remoção do bloqueio NÃO é decisão de engenheiro solo. |

---

## 3. Alternativas de Método de Push (Quando M5 For Removido) — 3 Opções Avaliadas

### Opção A: GitHub Personal Access Token (Classic / Fine-Grained) armazenado no Vault

- **Prós**: Simples; documentado GitHub; 99% das equipes usam.
- **Contras**: Token long-lived 30/60/90 dias = risco de vazamento. Fine-grained PAT escopo por repo reduz risco mas não elimina.
- **Risco**: Médio.
- **Custo**: Zero.

### Opção B: SSH Deploy Key RSA-4096 por ambiente (deploy key write)

- **Prós**: Criptografia assimétrica; NÃO expõe conta pessoal de engenheiro.
- **Contras**: 1 deploy key por repo = complexidade de gestão de chaves; rotação manual 90d.
- **Risco**: Médio-baixo (se Vault HSM gerenciar chaves privadas).
- **Custo**: Baixo.

### **Opção C (RECOMENDADA PARA FUTURO, HOJE NÃO IMPLEMENTADA AINDA): GitHub App + Render App PEM short-lived token (JWT 10min expiry)**

- **Prós**:
  1. **Token de curtíssima duração (10 minutos default)**. Mesmo que vazado, janela exploração é mínima.
  2. Instalação por repo = escopo mínimo. Repo Ontrackchain + write contents + pull requests apenas.
  3. Audit log nativo GitHub Apps = trilha de auditoria imutável.
  4. Suporta sign-off do Render GitHub App integração deploy automática.
- **Contras**: Complexidade de setup inicial (2h engenheiro senior + DSI).
- **Risco**: BAIXO (menor risco entre as 3 opções).
- **Custo**: Zero.

---

## 4. Decisão de Governança

### A) Situação HOJE (Sprint 22): M5 PERMANECE ATIVO
Aguardamos 3 condições cumulativas para remoção. Nenhuma foi cumprida até hoje.

### B) Condição de Remoção do M5 = "Condição 3A":
O bloqueio M5 será REMOVIDO SOMENTE quando TODAS as 3 condições abaixo forem cumpridas:

| ID | Condição | Status Sprint 22 | Responsável |
|---|---|---|---|
| 3A-1 | **Método escolhido e configurado**: Opção C (GitHub App) com PEM no Vault HSM. | ❌ PENDENTE | Diretor Segurança + CTO |
| 3A-2 | **Varredura de secrets em TODOS os 18 commits ahead**: `qa-gateway secrets guard` + `trufflehog filesystem --regex --entropy=True` no commit mais recente (HEAD) e NENHUM positivo. | ❌ PENDENTE (já rodamos secrets guard CI, mas não trufflehog filesystem full) | Engenheiro SRE + QA |
| 3A-3 | **Sign-off formal por escrito (4-eyes)**: CTO + DSI + CEO + Arquiteto Chefe. Arquivo `docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md` criado e commitado ANTES do push. | ❌ PENDENTE | Conselho Executivo |

### C) Procedimento de Push (14 passos), quando 3A cumprido:
1.  Criar branch `sync/origin-main-YYYY-MM-DD`.
2.  `git fetch origin main`.
3.  `git rebase origin/main` (squash optional? = decisão separada por ocasião).
4.  Executar `trufflehog3 filesystem ontrackchain/ --regex --entropy=True`. Se positivo = abortar.
5.  Executar `qa-gateway secrets-guard` (CI job local). Se positivo = abortar.
6.  Verificar `github_main/`, `tmp/`, `docs/governance-weekly/*`, `assessments/*`, `history/*` → NÃO staged.
7.  Dupla validação: Engenheiro A mostrando tela, Engenheiro B confirmando por call.
8.  Gerar GitHub App JWT (ttl=5min).
9.  `git push origin sync/origin-main-YYYY-MM-DD`.
10. Abrir Pull Request via UI `sync/origin-main-YYYY-MM-DD → main`.
11.  Executar CI completo em PR (17 gates). Todos passar.
12. Merge de PR via SQUASH (decisão default, salvo oposta).
13. Atualizar README.md M5 `N commits ahead = 0`.
14. Criar ADR `ADR-027 M5 removido oficialmente data X` com data, método, sign-offs.

---

## 5. Riscos e Trade-offs

### Risco P0 se Violado
- Vazamento de credencial de push.
- Vazamento de `.env.staging.private` ou arquivo de AML real com dados pessoais de clientes reais.
- Bypass de branch protection (`enforce_admins=true`) por engano = commit de código sem review.
- LGPD Art. 52 multa até 2% do faturamento anual + obrigação de comunicar ANPD em 48h.

### Trade-off Aceito (Até Sprint 22):
- **Trade-off**: 18 commits locais ahead = não colaboramos com contribuintes externos via GitHub.
- **Em troca recebemos**: 0 risco de vazamento de secrets via push; 0 risco de código sem passar CI; tempo de planejamento para configurar método Opção C corretamente sem pressa.
- **Cálculo custo/risco**: Risco P0 de vazamento > benefício de ter 18 commits no GitHub hoje. → **Decisão correta de manter M5 ativo.**

---

## 6. Definition of Done do ADR-026

| Critério | Status Sprint 22 |
|---|---|
| M5 documentado formalmente em ADR próprio 026, não só README nota de rodapé. | ✅ Concluído |
| Procedimento Condição 3A + 14 passos push descritos. | ✅ Concluído |
| 3 opções de método de push avaliadas com trade-offs e recomendação Opção C (GitHub App). | ✅ Concluído |
| docs/adrs/README.md índice atualizado: 22 → 26 ADRs. | ⬜ A fazer no final H1 |
| Tabela Consolidado README com linha S23-ADRS (Sprint23 +4 ADRs 023→026) | ⬜ Sprint23 H4 |

---

## 7. Consequências Operacionais Permanentes (Vigentes Enquanto M5 = Ativo)

1.  Todo commit de sprint é LOCAL NA BRANCH MAIN DO REPOSITÓRIO PESSOAL. NÃO tem backup remoto.
    → Engenheiro deve rodar em máquina local script de backup incremental para disco externo
    criptografado AES-256 semanal (Domingo 22h30).
2.  Nenhum workflow de CD deploy automático (Render / Heroku / AWS) está habilitado enquanto
    M5 = ativo, pois todos dependem de push remoto para trigger.
3.  Sincronismo de código entre engenheiros da equipe = via arquivo `.patch` assinado GPG
    e enviado por canal seguro, NÃO via PR remoto.
4.  Este ADR-026 é a **fonte única da verdade do bloqueio M5** a partir de Sprint 22; referência no README.md
    passa a apontar para este ADR, duplicamos a nota mas não duplicamos o texto.
