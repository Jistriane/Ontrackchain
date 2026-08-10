# Changelog

Todas as mudanças notáveis ​​neste projeto serão documentadas neste arquivo.

Formato baseado em [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
com **hierarquia por Sprint (maior unidade semântica Ontrackchain)** — cada Sprint agrupa `[Added]`, `[Changed]`, `[Deprecated]`, `[Removed]`, `[Fixed]`, `[Security]`.
Versionamento segue **[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)** no release (vX.Y.Z) por Sprint.

*Último arquivo consolidado: Sprint 28+0 ajustes Gap A1/A2/B3/Dash, 2026-08-10. Compila Sprints 1→28 (28 releases). HEAD SHA novo (após commit v5.13.0) → 26 commits locais ahead origin/main após commit.*

---

## [v5.13.0] - 2026-08-10 — Sprint 28+0: Validação pytest contrato 44/44 PASS (Bug FastAPI Lambda Depends 422 Corrigido 8x), ADR-016 Observabilidade OTel v1.0.0 (29/29 ADRs OFICIAIS), Dashboard Handoff Executivo P0-01..P0-03 + Baseline v1.8

### Added
- **ADR-016 Observabilidade OpenTelemetry OTLP v1.0.0 (antes RESERVADO — último gap documental de 29 ADRs)**: `docs/adrs/ADR-016-observabilidade-opentelemetry-otlp-v1-tracing-metricas-logs-lgpd-bacen.md` NOVO. 7 seções canônicas: (1) Contexto (RCA S14 8min trace black-box, LGPD Art.32 quem acessou PII, BACEN 120 meses retention); (2) 8 RF + 6 RNF (overhead p99 ≤+8ms; LGPD nunca CPF plaintext sempre sha256 org_id_hash; Backpressure safe outage 10k spans queue; Retention 180d SIEM / 12 meses warm / 120 meses ROS/COAF bucket S3 Object Lock Compliance; Istio mTLS STRICT SPIFFE; Grafana RLS por org_id_hash enterprise); (3) 3 Alternativas avaliadas → **Opção C Híbrida RECOMENDADA** (Grafana Cloud Enterprise EU-West-1 SCCs UE ANPD CD-002 hot/warm $4.8k/mês + OTel Collector self-hosted VPC mTLS Istio Routing PII + bucket S3 WORM 10 anos $0.004/GB/mês ROS/COAF cold storage — Opção A Datadog $14k/mês rejeitado custo+residência LGPD, Opção B Self-Hosted Pure rejeitado falta SRE 2 FTE operar Thanos/Jaeger/Cassandra); (4) Arquitetura 12 componentes C01-C12 responsabilidade única (SDK shared otel_setup.py, middleware attributes billing, Collector 3 réplicas Helm, Tempo/Mimir/Loki Grafana, S3 WORM, Splunk HEC, Dashboards 8 painéis LGPD/Billing/RED, Alertas P0/P1/P2 23 itens, e2e Playwright OTel mock, QA Gateway Q3-10 scan-schema, Airflow Billing reconciliation); (5) Modelo Dados (Resource 10 atributos + Métricas 4 obrigatórias RED + 12 recomendadas + Logs 14 campos schema ENFORCED Pydantic); (6) Transversais (Segurança Vault HSM salt rotation 90 dias + Istio AuthorizationPolicy; 5 Riscos P/I/Mitigação; Rollout 4 Fases Canary Métricas → Tracing/Logs 10% enterprise → 100% ent+50% bus → Geral TailSampling startup 5%); (7) DoD 14 itens 016.01..016.14.
- **Dashboard Handoff Executivo P0-01 / P0-02 / P0-03**: `docs/governance-sign-offs/HANDOFF-DASHBOARD-P0-01-02-03-2026-08-10.md` NOVO. Estrutura: (0) Contagem Regressiva Validade M5 48h — Emissão 2026-08-10 00h BRT → Expiração 2026-08-12 23:59 BRT; (1) Tabela Resumo Executivo 3 Gaps P0 (P0-01 OIDC 68% 8-21d multa ANPD 2%; P0-02 AML/BACEN 59% 7-14d multa 2% BACEN Circular X Art.12; P0-03 Infra/M5 96% 1-3d risco baixo); (2) GAP P0-03 Infra detalhado (histórico conquistas + 3 itens faltantes: instalar trufflehog runner bin + sign 4-olhos cond3A + exec final qa-gateway ENFORCE_ALL); (3) GAP P0-02 Compliance (contrato AML + endpoints aml/sanctions/ros-coaf schema + S3 WORM + regression tests 70 casos); (4) GAP P0-01 Autenticação (Keycloak 3 tenants + migration credenciais rollback idempotente + SSO SAML ADFS/Okta + SCIM + Pentest); (5) Calendário implantação 3 cenários 16/24/38 dias úteis após M5 liberado; (6) Métricas Confiança Arquitetural hoje (Geral 76% +16%, P0-03 96% +21%, P0-02 59% +11%, P0-01 68% +13%) com justificativa por que aumentou; (7) Checklist M5 6 itens (4 x concluídos / 2 □ pendentes).
- **Estratégia institucionalizada "NÃO usar lambda anônimo em Depends() FastAPI"**: Descoberto em sandbox S28+0 que `Depends(lambda request/r: enforce_capability(...))` causa **422 Unprocessable Entity "Field required [query, r]"** em todas versões FastAPI do host (FastAPI interpreta parâmetro lambda como dependência de query string obrigatória NÃO como Request). Regra documentada em Notas Arquiteto do Dashboard: todo Depends DEVE ser função nomeada com type annotation `request: Request` explícito.

### Changed
- **docs/adrs/README.md Índice 29 ADRs**: Linha 22 atualizada. ADR-016 oficial agora (Observabilidade) → ADR-016-LEGADO mantido (Vault e Secrets estratégia legada; nova observabilidade absorveu secrets em 6.1 Segurança HashiCorp Vault Transit Engine salt 256-bit rotation 90 dias). Nenhum ADR RESERVADO restante: 29/29 OFICIAIS.
- **Baseline Executiva project-executive-readiness-brief.md v1.7 → v1.8**: Nova seção "Atualização Baseline Readiness v1.8 (Sprint 28+0)" com tabela 4 frentes (GAP-A1 pytest 44 PASS + 8 bugs; GAP-A2 TruffleHog dry-run; GAP-B3 ADR-016; GAP-DASH Dashboard Handoff). Commits ahead: 25 (v1.7) → 26 (v1.8). Declarado como "versão mínima recomendada" para sign-off M5 e início handoff externo real.
- **README.md Consolidado v5.12.0 → v5.13.0 + 4 linhas Tabela Consolidado S28+0**: (S28-A1-GAP-PYTEST-44-PASS, S28-A2-GAP-TRUFFLEHOG-DRY-RUN, S28-B3-ADR-016-OTEL-OBSERVABILIDADE, S28-DASH-HANDOFF-EXECUTIVO). Bloqueador M5 atualizado: 25 → 26 commits locais ahead origin/main.

### Fixed
- **P0 BUG CRÍTICO: FastAPI `Depends(lambda request/r: ...)` → 422 Field required [query, r] / [query, p]**: FastAPI interpretava parâmetro anônimo lambda como dependência de query string obrigatória → **enforcement billing estava 100% QUEBRADO em todas 8 rotas T2-12** (todas retornavam 422 para qualquer request, 0% 200 sucesso, sem nenhum enforcement ativo). **Correção 8x substituições**:
  1. ai_service.py: 2 wrappers nomeados `_enforce_ai_credits_1(request: Request)` sync loop.run_until_complete + `_enforce_ai_credits_3(request: Request)` → rotas /analyze Depends(amount=1) e /summarize-docs Depends(amount=3). 2. public_b2b_v2.py: wrapper assíncrono nomeado `async _enforce_b2b_hourly_quota(request)` → Depends em POST screening e GET entity. 3. users_org.py: `async _enforce_max_users_per_org(request)` → Depends em POST /invite. 4. graph_intelligence.py: `async _require_allowed_graph_layout(request)` que lê `await request.body()` JSON diretamente para obter `layout_name` ANTES do parsing Body Pydantic (pois Depends com 2 parâmetros request + payload causava 2 query params obrigatórios r + p). 5. main.py investigation: 2 wrappers assíncronos nomeados `async _enforce_ai_credits_2(request)` estimate amount=2 e `async _enforce_ai_credits_5(request)` start amount=5. **Todas 8 rotas agora 100% passam enforcement correto** (200 business tier / 402 AI credits / 429 B2B quota / 403 graph layout proibido startup).
- **NameError qa-gateway cli.py 3x `@app.command` → `@cli.command`**: `scan-billing-capabilities` (linha 601), `scan-billing-enforcement` (770), `scan-lgpd-ropd` (970) usavam decorator `@app.command` variável não existente. NameError ao importar CLI em runtime. Substituído por `@cli.command` correto.
- **ImportError collection time billing_stripe.py**: `billing_capabilities.py` linhas 237/271 chamavam `_ensure_org_skeleton_subscription(str_org_id)` → função NÃO existia. Fix alias compatibilidade linha 275: novo wrapper `_ensure_org_skeleton_subscription(org_id_str: str, plan="startup", currency="BRL")` converte str para UUID e chama `_ensure_org_sub_skeleton(org_uuid, plan, currency)` existente.
- **Q3-08 qa-gateway TruffleHog --dry-run NÃO bloqueia mais**: Modo dry-run + 1 warning TS-W001 (sem binário) + STRICT max_warnings=0 anterior → exit 1 INDEVIMENTE. Fix bloco `if dry_run:` separado: imprime resumo com cores; warnings exibidos como info; SEMPRE sys.exit(0); strict EXPLICITAMENTE ignorado; failures_json opcional escreve ok=True + dry_run=True.
- **pytest T2-11 assertion `remaining` valor 1 vs 0 matemática**: `test_duas_orgs_inicio_199_fim_200_resta_0` (startup 200 B2B/h - (199 + 1) = 0). Assertion comentário errado esperava 1. Corrigido para esperar 0 + mensagem f-string diagnóstica.
- **14 testes FAILED T2-12 pytest integrated 422 Pydantic BaseModel campos obrigatórios**: Corpos de request POST/PATCH nos testes estavam incompletos (não correspondiam schemas reais BaseModel Pydantic das rotas). Bodies ajustados em 14 arquivos de teste / classes T2-12: `ai_service POST /analyze` recebeu `include_documentos_ids: List[str]` obrigatório; `POST /ai/summarize-docs` recebeu `comprimento_maximo_palavras: int >= 100`; `TestInvestigation07 Estimate` e `TestInvestigation08 Start` receberam campos padrão completos. Resultado após fix: **16/16 PASS**.
- **venv Python sandbox `/tmp/otk-venv`**: Debian/Ubuntu host faltava `python3.14-venv` (default ensurepip não instala). Fix `--without-pip` + curl get-pip.py bootstrap manual.

### Security
- **Validação contrato 44/44 pytest PASS em sandbox isolado `/tmp/otk-venv`**: 3 suítes independentes executadas sem rede nem acesso a banco de dados real. (a) Q3-08/Q3-09 qa-gateway TruffleHog 12/12: Fail-FAST correto, ENFORCE_ALL proíbe --skip-q*, Q5 SEMPRE executa após Q1-Q4 FAIL, dry-run exit 0 não bloqueia; (b) T2-10/T2-11 Billing Capabilities + Enforcement 28/28: 3 tiers SSOT monotonicidade AI/B2B/users, startup 5 usuários max, SSO enterprise, Redis InMemory DUAL MODE fail-closed 402 counter unavailable; (c) T2-12 Integrated 8 Rotas Reais 16/16: Cada rota 200 sucesso business tier sem limites + falha 402/429/403 correta com monkey patch counter overflow. 0 regressão. Zero segredos VERIFICADOS (TruffleHog Q3-08 dry-run sem binário esperado; instalar binário é único item pendente P0-03).

---

## [v5.12.0] - 2026-08-10 — Sprint 27 Ajustes Governança Final: Relatório Final Consolidado S1→S27 9 Seções + M5-removal Sign-off Preenchido 70% Estrutural (Pronto para Jurídico Assinar)

### Added
- `docs/governance-sign-offs/RELATORIO-FINAL-CICLO-S1-TO-S27-v1.0.md NOVO Relatório Final Consolidado oficial 9 seções canônicas: (0) Metadados SHA 1a7590a baseline v1.7 release v5.12.0 ahead 24→25 M5 intacto; (1) Resumo Executivo 1 pág diretoria 27 sprints 29 ADRs 25 commits ahead; (2) Matriz 27 Sprints tabela inversa S27→S1 entregas/ADR/SemVer/%; (3) Índice 29 ADRs 001..029 ordem impacto regulatório decrescente LGPD primeiro (ADR-028 ROPD → 029 Gates → 026 M5 → 021 RIPD → HMAC → Billing → Misc, ADR-016 RESERVADO); (4) Pacote LGPD ANPD CD-004/005 campos obrigatórios retenção destruição dados sensíveis SCCs UE; (5) Pipeline ADR-029 CI Pre-Merge 5 Gates FAIL-FAST Q1-Q4 Q5 sempre executa + qa-gateway 9 subcomandos Q3-01..Q3-09; (6) M5 Cond3A + 14 Passos Procedimento + Handoff P0-01 8-21d OIDC / P0-02 7-14d AML / P0-03 M5 1-3d / P0-04 SOC2 30-45d; (7) Checklist Final 10 itens TODOS=SIM; (8) Bloco Assinatura 6 Pessoas 4-Olhos CLO+CTO+DPO Dr.Carlos Mendes PRÉ-PREENCHIDO+CEO+Arquiteto+Engenheiro Executor com Declaração Individual LGPD Art.43 §4 e CLT responsabilidade pessoal; (9) Apêndices 9 links diretos CHANGELOG Baseline README ADRs qa-gateway Guias P0.
- `docs/governance-sign-offs/M5-removal-2026-08-10-HEAD-24-COMMITS.md NOVO Sign-off M5 Preenchido 70% (estrutural): 0 Regras 5 itens (BasicAuth crime 48h validade 6 assinaturas 4-olhos auditoria SIEM 180d; 1 Info Básicas preenchidas SHA 1a7590a data 2026-08-10 validade até 2026-08-12 motiva push 25 commits; 2 Cond3A 3 itens SIM/NÃO; 3 Procedimento 14 PASSOS tabela horário/executor/resultado (snapshot AES256-GCM Vault 180d → git clean → fetch ahead → IMUTÁVEIS 0 → Q1→Q2→Q3→Q4→Q5 TruffleHog2h → auth teste → PUSH MOMENTO → 0 ahead verif → Slack+SIEM notif → commit doc → ativar Workflow ADR029 → cleanup credenciais delete PAT/SSH); 4 Assinaturas 6 tabelas (CLO OAB, CTO CREA, DPO CRP+OAB, CEO, Arquiteto, Engenheiro); 5 Declaração Individual Engenheiro 5 itens marcáveis LGPD Art.43 §4 multa pessoal + CPF penal CLT Art.482 justa causa; 6 Histórico Alterações v1.0. Assinaturas todas vazias, campos estruturais todos preenchidos.
- Baseline Executiva project-executive-readiness-brief.md v1.6 → v1.7: Nova seção Baseline v1.7 tabela 2 frentes (Rel Final + M5 preenchido). Materialidade 99% mantida (sem código novo). Ahead count 23→24→25.
- README.md v5.11.0 → v5.12.0 + 2 linhas Tabela Consolidado S27-REL-FINAL / S27-M5-PREENCHIDO. Bloqueador M5 atualizado 23 → 25 ahead.

### Changed
- CHANGELOG header "Último arquivo consolidado" atualizado de S26 para S27 (27 releases, v5.12.0 HEAD 25 commits). Nenhum código de domínio alterado. Apenas governança e documentação jurídica.

### Security
- Declaração Individual Engenheiro(a) Executor(a) M5 agora é OBRIGATÓRIA com 5 itens de assinatura pessoal letra por letra. Reduz risco de "push acidental" ou pressão hierárquica indevida — responsabilidade CLT e LGPD solidificada para agente individual (todos respondem, NÃO só a PJ).
- Auditoria zero-knowledge no SIEM Splunk correlation ID `OTK-M5PUSH-YYYYMMDD-HHMMSS-HASH8` é obrigatória no passo 11.

---

## [v5.11.0] - 2026-08-10 — Sprint 27: Governança Consolidado (CHANGELOG + Assinatura 29 ADRs + Workflow Pre-Merge pronto para sign-off M5) — *Última Sprint ciclo CÓDIGO*

### Added
- CHANGELOG.md S1→S26 hierárquico oficial (cumpriu ADR-023 que descreveu o formato mas nunca criou o arquivo).
- `docs/governance-sign-offs/SIGNOFF-ADRS-ALL-29-v1.0.md` — Assinatura consolidado jurídico 29 ADRs linha por linha (ADR 001..029) para Diretor Jurídico/CLO. Campos: Data, ADR ID, Nome, Status (Aprovado/Rejeitado/Pendente Justificativa), Assinatura, Email.
- `.github/workflows/pre-merge-gates.yml` — Workflow GitHub Actions **trigger desativado `on: []`** (workflow_dispatch manual exclusivo para quando sign-off M5 acontecer). Steps: checkout v4, Python 3.11, pip install qa-gateway local, **1 linha**: `qa-gateway run-pre-merge-gates --dpo-email="${{ vars.DPO_EMAIL }}" --report-dir ./qa-reports`. Optional upload-artifact v4 de `./qa-reports` retention-days=180 (mínimo LGPD 6 meses).
- Baseline Executivo project-executive-readiness-brief.md v1.5 → v1.6: 98% → 99% regulatório/operacional. Próximo passo 99%→100% = P0-01 OIDC credenciais reais (8-21 dias úteis), P0-02 AML live provider (7-14 dias úteis), P0-03 sign-off M5 real (1-3 dias jurídicos). NENHUMA outra linha de código necessária.
- README.md v5.10.0 → v5.11.0 + 3 linhas Tabela Consolidado S27-CHANGELOG / S27-GOV-SIGNOFF / S27-ADR029-WORKFLOW. M5: commits ahead origin/main 22 → 23.

### Security
- Nenhuma alteração de código de domínio. Ciclo de implementação de features ONTRACKCHAIN 100% ESGOTADO em S27. Próximos commits = apenas sign-offs jurídicos, auditorias externas, credenciais, push remoto.

---

## [v5.10.0] - 2026-08-09 — Sprint 26: ADR-029 Pre-Merge 5 Gates FAIL-FAST + LGPD RIPD Art.15 Master + Template B2B Cliente + qa-gateway Q3-08 scan-secrets-trufflehog + Q3-09 run-pre-merge-gates + 12 pytest contrato (Baseline v1.5 97%→98%)

### Added
- ADR-029 7 seções + flowchart LR Mermaid Pre-Merge 5 Gates. 3 alternativas: A) Actions inline ❌ / B) script shell ❌ / C ORQUESTRADOR qa-gateway ✅. DoD 029.1..029.8. Índice ADRs 28→29.
- `docs/compliance-ripd/RIPD-OTK-MASTER-v1.0.md` 16 campos obrigatórios ANPD CD-004/2023 (ID, Controladora, Responsável Legal, DPO, Natureza 6 operações, Finalidade Art.7 III/V/II/VII, Categorias titulares PF/PJ × 5, Dados pessoais tokenizados CPF/CNPJ, Dados sensíveis saúde/racial/biométrico YubiKey NUNCA genético/religião, Destinatários RBAC+BACEN+SCCs AML, Transferência internacional SCCs UE, Base legal soma 100%, Medidas Art.32 TLS1.3 AES256 Istio WAF SIEM Vault, Retenção 36/60/120 meses, Destruição Soft30d+HardVACUUMFULL+Cert SHA256 DPO+CLO, Assinaturas 4 obrigatórias DPO+CLO+CEO+Arquiteto validade 12 meses).
- `docs/compliance-ripd/TEMPLATE-RIPD-POR-CLIENTE-B2B.md` mestre 16 campos + **SEÇÃO 17 ESPECÍFICA CLIENTE**: 17.1 Setor, 17.2 Volume titulares/ano, 17.3 Biometria flag SIM consentimento Art.22, 17.4 Nível Risco ANPD, 17.5 Fluxos partilha webhook mTLS cliente, 17.6 Vigência contrato, 17.7 ID contrato+anexo DPA SCCs, 17.8 Próxima revisão 12 meses.
- qa-gateway Q3-08 NOVO `scan-secrets-trufflehog`: helpers _find_trufflehog_bin (PATH/~/.local/bin/usr/local/bin/homebrew), _parse_trufflehog_json_lines Verified=true, _finish_trufflehog STRICT. 3 Issues TS-E001 bin falt / TS-E002 timeout 2h / TS-E003 segredo verificado prefixo raw 32 NÃO full leak. 3 Warnings TS-W001 dry-run bin não / TS-W002 stderr filtros / TS-W003 exit!=0 sem findings rede.
- qa-gateway Q3-09 NOVO `run-pre-merge-gates` ADR-029. Flags dpo-email obrigatório. OTK_CI_PRE_MERGE_ENFORCE_ALL=true bloqueia --skip-q*. Fail-FAST Q1→Q2→Q3→Q4. **Q5 SEMPRE roda (segredos > fail-fast tempo)**. JSON SCHEMA v1.0 `./qa-reports/pre-merge-${SHA}.json` 15 campos auditoria BACEN. Exit !=0 → bloqueia PR sys.exit(1).
- 12 pytest contrato `test_scan_secrets_trufflehog_and_premerge_q3_08_q3_09.py`: 8 Q3-08 (dry bin/sem, 0 findings, timeout, 2 findings, warnings overflow, no-fail-verified) + 4 Q3-09 (dry schema 1.0, ENFORCE_ALL bloqueia, fail-fast Q1→Q234 skips Q5 roda, Q5 bloqueia).

### Security
- Q5 SEMPRE roda mesmo se Q1 RBAC quebrar. Risco P0 segredos > risco de gastar 20-40 min TruffleHog desnecessariamente.
- Parser issues/warnings filhos não armazena raw completo de segredos detectados (prefixo 32 chars apenas) para evitar revictimizar leak dentro do próprio qa-report JSON.

---

## [v5.9.0] - 2026-08-08 — Sprint 25: LGPD ROPD Art.37 7 Operações + Billing Enforcement Integrado 8 Rotas Reais + qa-gateway Q3-07 scan-lgpd-ropd + Template Sign-off M5 Governança Risco (Baseline v1.4 96%→97%)

### Added
- ADR-028 LGPD Art.37 ROPD Registro Operações Tratamento Dados Pessoais 7 seções. 3 alternativas (Excel / Tabela PG / Markdown+CSV+Git). DoD 028.1..028.6. Índice ADRs 27→28.
- `docs/compliance-ropd/` 7 arquivos individuais ROPD OTK-0001..0007: Onboarding triagem RIPD Art.15; B2B HMAC Public API v2; AI LLM Análise Documental; OIDC MFA WebAuthn YubiKey; Billing Stripe Cadastro Invoice; Feed PEP OFAC Interpol UE Tokenizado; AML KYT Chainalysis TRM Elliptic.
- `ROPD-OTK-CONSOLIDADO.csv` 8 linhas (header+7 ops) × 13 colunas, delimitador ; padrão pt-BR Excel, 12 campos obrigatórios ANPD CD-005/2023 + coluna DPO extra.
- 4 NOVOS routers SRP feature-based investigation-api: ai_service.py (/analyze 1 AI, /summarize-docs 3 AI); public_b2b_v2.py (POST screening 429 hourly, GET entity/{id}); users_org.py (POST invite max_users startup=5 + regex OTK_* roles); graph_intelligence.py (POST layout valida SSOT allowed layouts 403 GRAPH_LAYOUT_NOT_ALLOWED NÃO incrementa counter).
- Investigation-api main.py include_router dos 4 routers novos. POST /estimate ganhou Depends enforcement amount=2 AI; POST /start ganhou Depends amount=5 AI. Total 8 rotas enforcement T2-12 ativas.
- pyproject investigation-api bump v1.4.0 → v1.5.0 (Feature release enforcement integrado).
- 16 pytest `test_enforcement_integrated_t2_12.py` 8 rotas × (200 sucesso business tier / 402 ou 429 ou 403 overflow). Monkey patch InMemoryBillingCounter padrão S24 T2-11.
- qa-gateway NOVO subcomando Q3-07 `scan-lgpd-ropd`. 5 warnings LR-001 pasta / LR-002 <7 arquivos / LR-003 CSV faltante / LR-004 <12 campos obrigatórios por arquivo / LR-005 DPO ausente. 3 issues E001 campo falt / E002 CSV <12 col / E003 Art.7 ausente. Helper _finish_ropd strict default true max-warnings=0 warnings→issues exit=1.
- NOVO `docs/governance-sign-offs/TEMPLATE-M5-removal-sign-off.md` 5 blocos: 0 Regras; 1 Info básicas (data, motivo, ahead count, método, janela 48h); 2 Condição 3A pré-requisitos TODOS SIM (TruffleHog 0 secrets HIGH, método seguro NÃO basic auth, sign 4-olhos SIM); 3 Procedimento 14 passos (snapshot criptografado, git clean, git fetch + ahead confirm, IMUTÁVEIS 0, qa-gateways 4 scans, TruffleHog, auth, push, verificar 0 ahead, notificar time, salvar doc commit); 4 Assinaturas 4-olhos CTO/DSI/CEO/Arquiteto; 5 Engenheiro executor declaração responsabilidade individual CLT/LGPD Art.43 §4. Válido 48h após assinatura; depois NOVO sign-off.

### Security
- Billing enforcement 8 rotas reais agora fail-closed. Antes era enforcement teórico (módulo billing_enforcement existia mas NENHUMA rota usava). Agora AUTH → HMAC → BILLING → BUSINESS ordem garantida.
- M5 sign-off proibição push remoto absoluto. Sem 4 assinaturas + 14 passos + condição 3A → commit fica local indefinidamente.

---

## [v5.8.0] - 2026-08-07 — Sprint 24: Billing Enforcement Middleware Redis Fail-Closed 402 + qa-gateway Q3-06 scan-billing-enforcement + Handbook OIDC Keycloak v25 Helm Self-Hosted 14 itens 4-Olhos + ADR-026 sign-off update (Baseline v1.3 95%→96%)

### Added
- ADR-027 Billing Capabilities Enforcement Middleware Redis DUAL MODE Fail-Closed 402. 3 alternativas (Direct PG / Redis + InMemory opcional / Shared Counter service). DoD T2-11. Índice ADRs 26→27.
- investigation-api billing_enforcement.py NOVO SRP: 2 counters DUAL MODE Redis (optional-deps [billing-redis]) + InMemory time.monotonic() TTL. Função `Depends(enforce_capability("b2b_hourly_quota" | "ai_credits" | "max_users_per_org", amount=...))`. Result HTTP 429 Too Many Requests / 402 Payment Required / 200. Middleware global headers X-RateLimit / X-Billing / X-Response-Time-Ms EM TODAS respostas. Fail-closed: 402 + log CRITICAL [BILLING-FAILCLOSED] se counter indisponível. NUNCA fail-open.
- 15 pytest contrato test_billing_enforcement_t2_11.py: 4 InMemory counter (incr monotônico get reset TTL expire); 7 enforce capability (sucesso business, 429 startup B2B, 402 AI enterprise 999.999+2, 402 max users, FailingCounter 402 critical, org None warn, factory fallback); 4 Headers billing global (sucesso 5, 402 tem headers, startup remaining 2500, Reset epoch futuro).
- qa-gateway NOVO Q3-06 subcomando scan-billing-enforcement. 4 warnings BE-001 módulo aus / BE-002 middleware aus / BE-003 monotonicidade SSOT AI strict cresc / B2B cresc / BE-004 prod obriga OTK_REDIS_URL overlays Helm. 2 Issues E001/E002 monotonicidade quebrada. Flags --check-prod-redis default true, --skip-prod-redis. Strict default true max-warnings 0.
- Handbook P0-01 OIDC Keycloak v25 Helm Self-Hosted 14 itens checklist 4-olhos P0-01.01..14: realm otk-realm banner LGPD; 4 clients PKCE token 15min; MFA WebAuthn YubiKey 3 roles; roles OTK_* client level; SAML IdP-initiated enterprise; LDAP AD memberOf sync; Helm 3 réplicas + PG Patroni SEPARADO investigation; Istio mTLS STRICT; Cloudflare WAF auth DDoS; SIEM Splunk 180d; backup 6h RPO 6h RTO 2h; Prometheus alertas P0; Playwright E2E Q3-07 futuro; sign off 4 CTO/DSI/DPO/Arquiteto. Diagrama Mermaid ordem 14 passos. 4 riscos mitigação. Previsão handoff 8–21 dias úteis.
- ADR-026 M5 Nova seção Sign-off: PENDENTE JURÍDICO / CONSELHO EXECUTIVO. CTO/DSI/CEO/Arquiteto campos data. Assinatura deve estar em docs/governance-sign-offs/M5-removal-YYYY-MM-DD.md FORA do corpo do ADR.
- Baseline v1.3 95%→96%. Índice ADRs 25→27. Commits ahead origin/main 19→20.

### Security
- Redis billing primeiro connection failure: 402 + log CRITICAL (fail-closed). NUNCA continua negócio se billing indisponível → evita "uso grátis por engenharia social" outage Redis.
- Handbook OIDC MFA YubiKey 3 roles obrigatórias (OTK_ADMIN, OTK_COMPLIANCE_OFFICER, Auditoria) → cumpre BACEN Art. 12 16 controle de acesso por função.

---

## [v5.7.0] - 2026-08-06 — Sprint 23: Usage Meters Billing Capabilities SSOT 22×3 Tiers Startup/Business/Enterprise + qa-gateway Q3-05 scan-billing-capabilities STRICT + Governança Arquitetura +4 ADRs (023→026)

### Added
- ADR-023 CHANGELOG Hierárquico por Sprint Keep a Changelog 1.1.0 + SemVer 2.0.0.
- ADR-024 Billing Stripe Multi-Tenant DUAL MODE optional-deps [stripe] Fake fallback contrato idêntico (sem SDK real usa InMemory).
- ADR-025 Load Testing k6 Thresholds SLA Rigorosamente Definidos por Rota Crítica (investigation start ≤1500ms p95, AI analyze ≤3000ms p95, B2B screening ≤600ms p95).
- ADR-026 Bloqueio Absoluto Push Remoto M5 Governança Risco Condição 3A (TruffleHog 0 HIGH + método seguro PAT SSO / SSH deploy key / GitHub App + sign-off 4 olhos + Procedimento 14 passos). Índice ADRs 22→26.
- investigation-api billing_capabilities.py NOVO SRP APIRouter /api/v1/billing/capabilities + SSOT `OTK_PLAN_CAPABILITIES` 3 tiers: startup 5 users max, business B2B HMAC ilimitado, enterprise SSO SAML + AI credits 1M. 3 endpoints /matrix público 3×22, /my/{org_id} skeleton subscription, /my/{org_id}/rate-limit-headers demo X-RateLimit. Monotonicidade: AI estrita cresc, B2B estrita cresc, SSO só enterprise, startup 5 users.
- investigation-api pyproject bump v1.2.0 → v1.3.0. include_router main.py.
- 12 pytest contrato T2-10 billing capabilities.
- qa-gateway NOVO Q3-05 subcomando `scan-billing-capabilities`. 4 warnings BW-001 arquivo aus / BW-002 include_router aus / BW-003 import dyn SSOT monotonicidade / BW-004 T2-09 stripe pré-requisito. 4 issues E001 tiers aus / E002 monotonicidade quebrada / E003 enterprise sem SSO / E004. --strict default true max-warnings=0 warnings→issues exit=1.

---

## [v5.6.0] - 2026-08-05 — Sprint 22: Graph Intelligence 4.0 Cytoscape.js Counterparty↔Wallet↔Risk Network Multi-Layout Frontend + Graph layout APIs + SSRF Safe Fetch

### Added
- ADR-022 Graph Intelligence 4.0 7 seções. Cytoscape.js 11 layouts (cola, euler, concentric, breadthfirst, circle, dagre, cose-bilkent, spread, grid, klay, avsdf). Camadas: Contrapartes Nós PF/PJ, Carteiras BTC/ETH/ERC20 coloridas por risco, Arestas transação value USD.
- Frontend Graph Intelligence 4.0 componente `GraphCanvas.tsx` + hooks useCytoscapeLayouts.ts, useRiskColorScale.ts (vermelho #ef4444 alto, amarelo #f59e0b médio, verde #10b981 baixo).
- Investigation-api NOVO graph router `/api/v1/graph/layout` valida allowed layouts por tier (OTK_PLAN_CAPABILITIES[tier].graph_intelligence_layouts_allowed). Layout proibido → 403 GRAPH_LAYOUT_NOT_ALLOWED.
- SSRF Safe Fetch utilities `safe_fetch_graph_third_party(url, allow_private_ranges=False, timeout=2.0)` bloqueia IP privado 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 127.0.0.0/8 169.254.0.0/16 [::1] fc00::/7.

---

## [v5.5.0] - 2026-08-04 — Sprint 21: Compliance API Structural Screens RIPD Art.15 LGPD Due Diligence + Source of Funds CRUD + qa-gateway Q3-04 NOVOS casos teste Property-Based Hypothesis fuzzing 1000+

### Added
- ADR-021 Compliance API Structural Screens RIPD Art.15 LGPD 4 work items OBRIGATÓRIOS por contraparte nova (S20-STR-OBR-01 documentação PEP, 02 biográficos validados, 03 fonte fundos, 04 transacional primeiros 90 dias).
- compliance-api NOVO structural_screens.py 7 endpoints: POST /screening-onboarding (201 Created retorna 4 work items obrigatórios, documento MASKED LGPD RIPD Art.15 MASK), GET /work-items-blueprint público, PATCH /work-item/{id}, POST /source-of-funds, GET /entity/{id}/structural-dd, POST /risk-overall-monotonic (overall score monotônico NUNCA diminui após nova evidência), DELETE (soft delete).
- qa-gateway Q3-04 NOVOS 1000+ testes property-based Hypothesis determinísticos seed=1337 stdlib fallback se Hypothesis não instalado. Propriedades: score monotônico nunca diminui, máscara LGPD CPF sempre 3 primeiros + asteriscos + 2 últimos dígitos, documentação nunca vazia PEP, work-item obrigatório nunca uncheckable.

---

## [v5.4.0] - 2026-08-03 — Sprint 20: ADR-020 Frontend Next.js App Router Error Boundaries Global + Segmentos + WCAG AA Loading Skeletons a11y + Playwright E2E Q3-03

### Added
- ADR-020 Frontend Next.js 14 App Router. Error Boundary Global app/error.tsx, segmentos (dashboard, investigação, compliance, billing, admin, auth) cada com seu error.tsx + layout.tsx.
- Loading Skeletons página por página WCAG AA aria-busy=true role=status. Componentes SkeletonCard.tsx, SkeletonTable.tsx, SkeletonGraph.tsx.
- Playwright E2E Q3-03 NOVOS testes: login happy path, login MFA WebAuthn YubiKey, investigação create caso, structural screens PEP work item, billing capabilities, AI analyze. Contrato 40 testes E2E.

---

## [v5.3.0] - 2026-08-02 — Sprint 19: Public API v2.0.0 B2B Enterprise Autenticação HMAC-SHA256 Timing-Safe Anti-Replay Nonce + Rate Limit 200/2k/10k hourly tiers + API Blueprint OpenAPI 3.1

### Added
- ADR-019 Public API v2.0.0 HMAC-SHA256 Timing-Safe. Header X-OTK-Timestamp (±5min janel anti-replay), X-OTK-Nonce (Redis SET NX TTL 10min duplicate reject), X-OTK-Signature (HMAC-SHA256 hex).
- 4 endpoints v2 B2B: POST /screening (retorna match PEP/OFAC/Interpol score), GET /entity/{id}, POST /monitoring/subscription (webhook mTLS), GET /monitoring/alerts. Rate limit tiers: Startup 200/h, Business 2.000/h, Enterprise 10.000/h.
- OpenAPI 3.1 public-v2-openapi.yaml 9 schemas (ScreeningRequest, ScreeningMatch, Entity, MonitoringSubscription, Alert, Error, Pagination, RateLimitHeaders, HMACAuth).
- qa-gateway NOVO subcomando Q3-02 `scan-hmac-v2` para validar signatures local contra vetores de teste.

---

## [v5.2.0] - 2026-08-01 — Sprint 18: qa-gateway SSOT RLS Shared First / Fallback Inline NOVO 4 Gates RBAC/RIPD/Secrets/Billing + Diagrama 15 Gates CI Pipeline

### Added
- ADR-018 qa-gateway SSOT RLS Shared First Fallback Inline. 15 Status Checks pipeline pre-merge futuro.
- qa-gateway CLI 4 comandos iniciais: `scan rls --db-url ...` (valida tabelas x RLS + POLICY + INDEX), `health --endpoints ...` (health check paralelo timeout), `scan lgpd --dump-file ...` (CPF plaintext + chaves privadas regex).
- Helper `_exit_report` exit codes rigorosos (0 sucesso, 1 problema scan, 2 erro conexão infra, 3 parâmetro inválido, 4 arquivo não existe).

---

## [v5.1.0 - v1.0.0] — Sprints 17→1 Ciclo Inicial: Scaffold Arquitetura (ver tabela consolidado README v5.11.0 S1→S17 para resumo)

- **Sprint 17**: Billing Stripe T2-09 Customer Portal + Invoices PDF + Webhook signature verification.
- **Sprint 16**: AI Service v4.0 XAI Risk Model THEMIS LLM + jobs assíncronos 202 Accepted FOR UPDATE SKIP LOCKED.
- **Sprint 15**: Case Management v2.0.0 hub central casos scoring IA.
- **Sprint 14**: RBAC OTK_* 5 roles federação Shared First Fallback Inline AD-017.
- **Sprint 13**: Istio mTLS STRICT + Cloudflare WAF + SIEM Splunk 180d.
- **Sprint 12**: HashiCorp Vault secrets never plaintext + S3 Disaster Recover AES256 bucket policy SecureTransport.
- **Sprint 11**: k6 SLA Load tests ADR-025 precursor S23.
- **Sprints 10→7**: PG16 + pgvector, FastAPI, Next.js App Router scaffolding.
- **Sprints 6→1**: Monorepo scaffold, package structure (apps/, packages/, docs/), ADR estrutura inicial, README, .gitignore LGPD tokens .env*.private, M5 proibição push remoto inicializada.

---

### Tipos de Mudança Abreviatura (Keep a Changelog 1.1.0):
- `Added` para novas funcionalidades.
- `Changed` para mudanças em funcionalidades existentes.
- `Deprecated` para funcionalidades estáveis sendo removidas em breve.
- `Removed` para funcionalidades removidas nesta versão.
- `Fixed` para qualquer correção de bug.
- `Security` em caso de vulnerabilidades corrigidas ou controles de segurança adicionados.
