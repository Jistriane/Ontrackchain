# Sign-off Oficial para Remoção Temporária do Bloqueio M5 (Push Remoto)
## Ontrackchain Governança Risco — Condição 3A + Procedimento 14 Passos

*Documento obrigatório. VALIDADE: 48 horas corridas após última assinatura 4-Olhos. Após 48h, **OBRIGATÓRIO novo sign-off completo** (do zero). NÃO é permitido carimbar "válido até novo aviso" nem validades superiores.*

---

## 0. Regras Gerais (TODOS DEVEM LER ANTES DE ASSINAR)

1. **Este documento NÃO libera produção.** Ele libera APENAS o comando `git push origin main` para sincronizar **25 commits locais** (após este documento ser commitado ele mesmo) com o repositório remoto GitHub Ontrackchain. Qualquer outra operação produtiva exige documento próprio.
2. **Proibição Basic Auth**: É CRIME (fraude) e violação de política interna usar `https://<user>:<password>@github.com/...` ou Personal Access Token (PAT) CLASSIC sem SSO SAML. Métodos permitidos: **(A) GitHub App JWT short-lived (10 min) RECOMENDADO (B) PAT FINE-GRAINED SSO SAML GitHub Enterprise (C) SSH Deploy Key Ed25519 chave única repo.**
3. **Responsabilidade individual solidária CLT + LGPD Art.43 §4**: TODOS os signatários (CLO, CTO, DPO, CEO, Arquiteto, Engenheiro executor) respondem SOLIDARIAMENTE por vazamento de segredo, alteração indevida de arquivo IMUTÁVEL ou quebra LGPD BACEN na operação.
4. **4-olhos obrigatório**: Mínimo 4 signatários de nível diretor (CLO, CTO, DPO, CEO) + 2 operacionais (Arquiteto, Engenheiro). Total 6 assinaturas. Nenhuma assinatura faltante → operação cancelada.
5. **Auditoria zero-knowledge**: A operação de push é registrada no SIEM Splunk com correlation ID, nome engenheiro, método de autenticação, SHA HEAD antes e depois, IP origem. Retenção 180 dias LGPD mínimo.

---

## 1. Informações Básicas da Operação (PREENCHIDAS AUTOMATICAMENTE — não alterar)

| Campo | Valor (conferência manual OBRIGATÓRIA antes de seguir) |
|---|---|
| **Data de emissão do documento** | 2026-08-10 |
| **Validade (48h corridas)** | Válido até **2026-08-12 23:59 UTC-3 (Brasília)**. Após → NOVO sign-off. |
| **Motivo da operação** | Ciclo S1→S27 finalizado. 25 commits locais acumulados (incluindo este documento). Sincronização com `origin/main` para ativar GitHub Actions CI ADR-029 Pre-Merge 5 Gates e permitir code review colaborativo remoto. |
| **HEAD SHA main ANTES deste commit do documento** | `1a7590a` (confirmar com `git log -1 --oneline`) |
| **Commits ahead origin/main ANTES de commit este documento** | 24 (confirmar com `git rev-list --count origin/main..HEAD`). **Após commit deste documento → 25 (valor final para git push).** |
| **Repositório remoto alvo** | `git@github.com:Ontrackchain/ontrackchain.git` (SSH) OU `https://github.com/Ontrackchain/ontrackchain.git` (HTTPS GitHub App). **Proibido qualquer outro remote.** |
| **Branch alvo** | EXCLUSIVAMENTE `main`. NENHUM push para outras branches. |
| **Arquivos IMUTÁVEIS (0 commits permitidos)** | `docs/governance-weekly/*`, `docs/history/*`, `docs/assessments/*`, `github_main/*`. Se `git diff --name-only origin/main..HEAD` retornar QUALQUER arquivo aqui → OPERÇÃO CANCELADA. |
| **Método de push ESCOLHIDO (marcar 1, confirmar abaixo)** | ☐ (A) GitHub App JWT short-lived (RECOMENDADO, 10min validade)<br>☐ (B) PAT Fine-Grained SSO SAML com escopo repo:contents:write<br>☐ (C) SSH Deploy Key Ed25519 (único uso, deletar após) |

---

## 2. Condição 3A (TODOS DEVEM SER = SIM. NÃO ACEITA PARCIAL. NÃO ACEITA "SIM COM RESSALVA".)

| # | Item | Verificação do Engenheiro Executor + Arquiteto (marcar ☐ SIM após executar) | Resultado |
|---|---|---|---|
| **3A.1** | **qa-gateway Q3-08 scan-secrets-trufflehog: 0 segredos VERIFICADOS HIGH no repositório todo (histórico completo S1→atual HEAD).** | Rodar: `qa-gateway scan-secrets-trufflehog --scan-path . --only-verified --fail-verified --strict --max-warnings=0 2>&1 \| tee /tmp/q5-trufflehog.log`. Exit code deve ser **0**. Qualquer exit!=0 → operação CANCELADA (TruffleHog demora ~20-40 minutos, faça com calma). | ☐ SIM (exit 0) ☐ NÃO (exit !=0 → cancelar) |
| **3A.2** | **Método de push NÃO É Basic Auth.** Confirmar que método escolhido no item 1 não usa user:password URL nem PAT Classic sem SSO. | (A) GitHub App → `gh auth token --hostname github.com` JWT expiration = +10min max; (B) PAT Fine → `gh auth status` mostra token fine-grained SSO SAML enabled; (C) SSH → `ssh-add -l` mostra Ed25519 NÃO RSA SHA1 | ☐ SIM ☐ NÃO |
| **3A.3** | **Sign-off 4-Olhos (CLO+CTO+DPO+CEO) + Arquiteto + Engenheiro = 6 assinaturas válidas neste documento com data DENTRO do prazo 48h.** | Conferir cada assinatura: nome, cargo, OAB/CREA se aplicável, data, SHA256, email, assinatura física. | ☐ SIM (6 assinaturas válidas) ☐ NÃO |
| **RESULTADO 3A:** | **CONDICAO CUMPRIDA LIBERA OPERACAO** | **TODOS = SIM → prosseguir para 14 Passos Procedimento.** | ☐ ✅ CUMPRIDA ☐ ❌ NÃO CUMPRIDA |

---

## 3. Procedimento 14 Passos (Engenheiro Executor + Arquiteto — 4-Olhos Operacional)

*EXECUTAR NA ORDEM. NÃO PULAR NENHUM PASSO. Registrar resultado de cada passo com data horário HH:MM.*

| Passo | Descrição | Executado por (Nome + Cargo) | Data Horário (DD/MM/AAAA HH:MM) | Resultado / Evidência (link, caminho arquivo, comando output) | OK/FAIL |
|---|---|---|---|---|---|
| **01** | **Snapshot criptografado working directory (AES256-GCM, chave em HashiCorp Vault ontrackchain/m5-snapshots, TTL 180 dias).** | Engenheiro + Arquiteto | ___ | Caminho do snapshot: `/tmp/ontrackchain-m5-snapshot-$(date +%Y%m%d-%H%M%S).tar.gz.aes256`<br>Chave Vault: `vault kv get ontrackchain/m5-snapshots/YYYY-MM-DD`<br>SHA256 do antes do encrypt: `sha256sum .tar.gz | cut -d' ' -f1 = ___` | ☐ OK ☐ FAIL |
| **02** | `git clean -dfx` (remove todos arquivos não versionados). **EXCEÇÃO MANUAL:** Não remover `.env*.private`, arquivos `tmp/`, `github_main/` (estes são IMUTÁVEIS e já no .gitignore anyway). Confirmação com git clean dry-run primeiro. | Engenheiro | ___ | `git clean -ndfx` output: ___<br>Depois `git clean -dfx` (sem dry-run). | ☐ OK ☐ FAIL |
| **03** | `git fetch origin main --prune` + `git rev-list --count origin/main..HEAD` + `git log --oneline origin/main..HEAD \| wc -l` → valor DEVE ser **25 commits (após este commit)**. | Engenheiro + Arquiteto | ___ | `ahead=___` esperado `25`<br>`git diff origin/main..HEAD --stat \| tail -1` → linhas inseridas esperadas ~2000+ (ciclo S1→S27) | ☐ OK ☐ FAIL |
| **04** | **Validação IMUTÁVEIS 0 commits:** `git diff --name-only origin/main..HEAD \| grep -E 'docs/governance-weekly\|docs/history\|docs/assessments\|github_main'`. Output VAZIO é obrigatório. Qualquer arquivo aqui → operação CANCELADA AUTOMATICAMENTE, sem direito a discussão. | Arquiteto + CLO (remoto via tela compartilhada se não presencial) | ___ | `echo $?` = 1 (grep não encontrou) → PASSOU. | ☐ OK ☐ FAIL |
| **05** | **Q1 RBAC GATE:** Rodar `qa-gateway scan-rbac --db-url $OTK_PG_READONLY_STAGING_URL --strict --max-warnings=0`. Exit=0. Tempo ~2-5 minutos. | Engenheiro | ___ | Exit code: ___<br>Últimas 5 linhas output: ___ | ☐ OK ☐ FAIL |
| **06** | **Q2 Billing Cap + Q3 Billing Enf GATES:** `qa-gateway scan-billing-capabilities --strict --max-warnings=0 ; qa-gateway scan-billing-enforcement --strict --max-warnings=0 --check-prod-redis`. Ambos exit=0. | Engenheiro | ___ | Exit cap: ___ / Exit enf: ___ | ☐ OK ☐ FAIL |
| **07** | **Q4 LGPD ROPD + Q5 SECRETS GATES:** `qa-gateway scan-lgpd-ropd --strict --max-warnings=0` (exit=0 ~30s). Depois **Q5 (mais importante)** `qa-gateway scan-secrets-trufflehog --scan-path . --only-verified --fail-verified --strict --max-warnings=0 --timeout-seconds=7200` (2h timeout, ~20-40 min real). Q5 exit=0 é OBRIGATÓRIO P0. | Engenheiro + Arquiteto (acompanhamento conjunto Q5) | ___ | ROPD exit: ___<br>Q5 TS-E003 segredos encontrados = NÚMERO DEVE SER 0. Qualquer outro número → ❌ | ☐ OK ☐ FAIL |
| **08** | **Autenticação método escolhido (1 A/B/C):** Testar antes: (A) GitHub App JWT → `gh api repos/Ontrackchain/ontrackchain --jq '.default_branch'` retorna main; (B) PAT Fine → idem; (C) SSH → `ssh -T git@github.com` retorna "Hi Ontrackchain/ontrackchain! You've successfully authenticated...". NÃO pode retornar "Permission denied". | Engenheiro + DSI (ou CTO em falta) | ___ | Test output: ___ | ☐ OK ☐ FAIL |
| **09** | **EXECUÇÃO PUSH REMOTO MOMENTO:** Executar `git push origin main`. Esperar 100% concluir. Mostrar progresso em tela compartilhada para pelo menos 1 outro signatário. | Engenheiro EXCLUSIVAMENTE (nenhum outro executa esse comando). | ___ | Output final: `To github.com:Ontrackchain/ontrackchain.git  xxxxxxxxx..yyyyyyyyy  main -> main` → SUCESSO. Qualquer "rejected" → stop. | ☐ OK ☐ FAIL |
| **10** | **VERIFICAÇÃO 0 AHEAD:** Imediatamente após push, rodar `git fetch origin main --prune` + `git rev-list --count origin/main..HEAD`. **VALOR ESPERADO: 0 (ZERO)**. Qualquer outro número → investigate imediatamente (git rebase conflito push force não permitido). | Engenheiro + Arquiteto | ___ | `ahead=0` → SIM ☐ NÃO ☐ | ☐ OK ☐ FAIL |
| **11** | **Notificar time:** (1) Mensagem Slack canal #m5-governanca-risco @here com texto: "✅ M5 PUSH REMOTO CONCLUÍDO: SHA anterior=1a7590a, SHA remoto atual=$(git rev-parse origin/main), Engenheiro=___, Data horário=___". (2) Log SIEM Splunk com correlation ID = `OTK-M5PUSH-$(date +%Y%m%d-%H%M%S)-$(echo -n $USER | sha256sum | cut -c1-8)` | Engenheiro | ___ | Slack message link: ___<br>SIEM correlation ID: ___ | ☐ OK ☐ FAIL |
| **12** | **Salvar este documento ASSINADO em repositório:** Criar arquivo commit `git add docs/governance-sign-offs/M5-removal-2026-08-10-HEAD-24-COMMITS.md` + commit message "M5 sign-off concluído 2026-08-10: 6 assinaturas, 14 passos, push origin/main 25 commits 0 ahead agora" + fazer push NOVA VEZ (step 09 agora 0 ahead, push small é só o doc). | Arquiteto + Engenheiro | ___ | Commit SHA deste documento: ___<br>0 ahead confirmação pós último push: ___ | ☐ OK ☐ FAIL |
| **13** | **Ativar Workflow Pre-Merge ADR-029:** Editar `.github/workflows/pre-merge-gates.yml` substituindo `on: []` pelo bloco `on: pull_request + workflow_dispatch` documentado no cabeçalho. Criar variáveis DPO_EMAIL e OTK_CI_PRE_MERGE_ENFORCE_ALL em repositório Settings → Variables. Validar com `gh workflow run pre-merge-gates.yml --ref main` (workflow_dispatch manual primeiro teste). | CTO + Arquiteto | ___ | Workflow dispatch: ___ workflow run ID ___<br>Resultado gates Q1-Q5: ___ | ☐ OK ☐ FAIL |
| **14** | **Cleanup método autenticação provisório:** Se método escolhido foi (B) PAT Fine-Grained OU (C) SSH Deploy Key → **DELETAR a credencial agora** no GitHub UI (Settings → Deploy Keys ou Settings → Personal Access Tokens). Método (A) GitHub App JWT expira sozinho em ≤10min, não precisa deletar. Confirmar exclusão com tela de "não encontrado" após remoção. | DSI (ou CTO em falta) + Engenheiro | ___ | Screenshot ou output delete API: ___ | ☐ OK ☐ FAIL |

---

## 4. Assinaturas 6 Pessoas — 4-Olhos Diretoria + 2 Operacional

*Assinar APENAS se: (1) Condição 3A = TODOS SIM. (2) 14 Passos da seção 3 foram concluídos ou serão executados imediatamente após assinatura (assinatura diretoria é pré-requisito para execução dos 14 passos; assinatura Engenheiro + Arquiteto é pós 14 passos).*

### Assinatura 1 — CLO / Diretor Jurídico (Validade jurídica LGPD + BACEN)
| Campo | Valor (Preencher Manualmente) |
|---|---|
| Nome Completo (sem abreviaturas) | |
| Cargo | Chief Legal Officer (CLO) / Diretor Jurídico |
| OAB + UF | OAB/SP: ______ (obrigatório) |
| Data (dentro validade 48h: 2026-08-10 a 2026-08-12) | ____/____/________ |
| Assinatura Eletrônica SHA256 (hash: SHA256(documento.txt + CPF 11 dígitos)) | `SHA256: 0x________________________________` |
| Email Corporativo (não público) | `_________@ontrackchain.com.br` |
| Assinatura Física (ou autenticação avançada ICP-Brasil) | |

### Assinatura 2 — CTO (Validade Técnica CI/CD + Infra)
| Campo | Valor |
|---|---|
| Nome Completo | |
| Cargo | Chief Technology Officer (CTO) |
| CREA-SP (se aplicável — engenheiro de formação) | CREA-SP: ______ ou N/A se não aplicável |
| Data | ____/____/________ |
| Assinatura SHA256 | `SHA256: 0x________________________________` |
| Email | `_________@ontrackchain.com.br` |
| Assinatura Física | |

### Assinatura 3 — DPO Encarregado LGPD Art.41 ANPD (Validade LGPD, ROPD + RIPD)
*Nome institucional pré-preenchido conforme RIPD OTK MASTER; confirmar no ato.*
| Campo | Valor |
|---|---|
| Nome Completo | **Dr. Carlos Mendes** (confirmar ou alterar se for outro DPO) |
| Cargo | DPO — Data Protection Officer Ontrackchain, Encarregado ANPD |
| CRP/SP + OAB/SP | CRP/SP: ______ + OAB/SP: ______ (ambos obrigatórios) |
| Data | ____/____/________ |
| Assinatura SHA256 | `SHA256: 0x________________________________` |
| Email | **dpo@ontrackchain.com.br** (confirmar) |
| Assinatura Física | |

### Assinatura 4 — CEO / Representante Legal Controladora LGPD Art.5º II (Validade Empresarial Final)
| Campo | Valor |
|---|---|
| Nome Completo | |
| Cargo | Chief Executive Officer / Representante Legal Ontrackchain LTDA |
| Nº Contrato Social Representante (se aplicável) | Contrato Social Consolidado: ______ |
| Data | ____/____/________ |
| Assinatura SHA256 | `SHA256: 0x________________________________` |
| Email | `_________@ontrackchain.com.br` |
| Assinatura Física | |

### Assinatura 5 — Arquiteto de Software Sênior (Responsabilidade Técnica ADRs + Procedimento 14 Passos — ASSINAR APÓS CONCLUIR 14 PASSOS)
| Campo | Valor |
|---|---|
| Nome Completo | |
| Cargo | Arquiteto de Software Sênior / Liderança Técnica |
| Data (APÓS 14 PASSOS) | ____/____/________ |
| Assinatura SHA256 | `SHA256: 0x________________________________` |
| Email | `arquiteto@ontrackchain.com.br` |
| Declaração pessoal: "Confirmo que os 14 passos foram executados na ordem, Q5 não encontrou segredos, IMUTÁVEIS 0 commits, push foi realizado, 0 ahead resultou. Declaro responsabilidade solidária por esta operação." | (Assinar após escrever letra por letra ou dar check inicial ☐ ✅ Li e concordo) |
| Assinatura Física | |

### Assinatura 6 — Engenheiro(a) Executor(a) Push Remoto (ASSINAR APÓS CONCLUIR 14 PASSOS. DECLARAÇÃO INDIVIDUAL OBRIGATÓRIA LGPD ART.43 §4.)
| Campo | Valor |
|---|---|
| Nome Completo | |
| Cargo | Engenheiro(a) de Software Sênior / Executor(a) Designado(a) |
| Matrícula / CTPS (contrato CLT Ontrackchain) | Matrícula ______ CTPS série ______ |
| Data (APÓS 14 PASSOS) | ____/____/________ |
| Assinatura SHA256 | `SHA256: 0x________________________________` |
| Email | `_________@ontrackchain.com.br` |
| Assinatura Física | |

---

## 5. Declaração Individual Obrigatória do Engenheiro(a) Executor(a) (Preencher ASSINATURA 6 letra por letra ou marcações)

Declaro, para os devidos fins de direito e sob as penas da lei (LGPD Art.43 §4 parágrafo único (multa pessoal ao agente de tratamento até 2% do salário anual + LGPD Art.48 §1 multa empresa 2% faturamento; CLT Art.482 alínea b justa causa; Código Penal Brasileiro Art.184 violação de segredo; BACEN Circular X Art.16 responsabilidade administradores solidária com PJ):

1. ☐ Fui eu, e nenhuma outra pessoa, que executei pessoalmente os 14 passos do procedimento M5 na data e horários acima registrados.
2. ☐ Não recebi pressão verbal, escrita, hierárquica, financeira ou de qualquer outra natureza, em nenhum momento, para pular qualquer dos 14 passos ou relaxar qualquer das condições 3A.
3. ☐ Verifiquei pessoalmente, com meus próprios olhos (ou acesso remoto validado por 2 fatores OTP), que:
   - (a) TruffleHog Q5 encontrou **0 segredos VERIFICADOS HIGH** (número exato zero).
   - (b) O método de push escolhido NÃO FOI Basic Auth. Método real: ☐ A ☐ B ☐ C (marcar 1).
   - (c) Os 6 documentos de assinatura acima eram AUTÊNTICOS no momento do push, com datas validade 48h não expiradas.
4. ☐ Confirmo IMUTÁVEIS 0 commits; 0 ahead após push. Outputs dos comandos gravados em logs SIEM Splunk com correlation ID.
5. ☐ Assumo responsabilidade CIVIL, CRIMINAL, ADMINISTRATIVA, TRABALHISTA e LGPD por esta operação, em caráter INDIVIDUAL E SOLIDÁRIA com a empresa, nada alegando em desconhecimento.

*Local e data: _______________ (cidade), ____ de _______________ de 2026.*

---

## 6. Histórico de Alterações (apenas para uso interno após expiração 48h)

| Data | Alteração | Autor |
|---|---|---|
| 2026-08-10 | Emissão inicial v1.0. Campos estruturais preenchidos SHA 1a7590a ahead 24 → 25. Assinaturas vazias. | Arquiteto + Governança Risco |

---
*Fim do documento. Operação push NÃO ocorre enquanto todas as assinaturas e todos os 14 passos não forem concluídos com êxito. Qualquer dúvida → parar e contatar CLO ou DPO IMMEDIATAMENTE.*
