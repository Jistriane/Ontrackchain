# documentação canônica

## Objetivo

Centralizar a documentação viva do Ontrackchain em um unico indice, reduzindo drift entre codigo, runtime, operação e narrativa executiva.

## Portas de Entrada

- Sumário Executivo (fonte): [README.md](../../README.md)
- Readiness canônico: [project-executive-readiness-brief.md](./project-executive-readiness-brief.md)
- Apêndice técnico: [TECHNICAL_APPENDIX.md](./TECHNICAL_APPENDIX.md)

## Snapshot Atual (Sprint 14 M8 Helm)

- baseline executivo oficial: `100%` técnico, `100%` regulatório/operacional, `100%` consolidado (fonte: [Resumo Executivo de Readiness](./project-executive-readiness-brief.md))
- 12 GAPs do documento Arquitetura Técnica QA/DevOps = **12 × 100%** (Sprint 6)
- Milestones Pós-MVP: **M1→M4, M6→M16b, M8/M8b = 100% fechados**; M5 Push Remoto 🔴 intencionalmente bloqueado
- **Helm Chart v1.0.0 ontrackchain-platform**: single chart 9 FastAPI (DRY range) + PG16 pgvector StatefulSet + Prometheus/Grafana/Alertmanager observabilidade stack + Keycloak v25 + Traefik Ingress + HPA/PDB/NetworkPolicy PSP LGPD
- **DR M16 PG16**: Backup Restore semanal sáb 02UTC, 1% amostragem LGPD, validação row count, S3 sa-east-1 AES256 opcional, Dead Man duplo (Issue P1 + Healthchecks.io)
- **M16b Gate Observabilidade**: 9/9 FastAPI com `/healthz` + `/metrics`; enforcement tríplice (job CI + Policy #04 OPA + endpoints implementados)
- **Policies OPA M10 (4 regras Rego)**: (01) P0 continue-on-error=true deny; (02) jobs pesados ubuntu-latest deny → self-hosted; (03) timeout-minutes obrigatório 100% jobs; (04) FastAPI sem /healthz+/metrics deny
- RBAC fino consolidado (`P2-05` concluído) e RCA cross-domain leve institucionalizado (`P2-03`)
- Federação OTK_*: mapeamento canônico em `ontrackchain_shared` (Python) + `authz.ts` (Next.js): OTK_ADMIN→ADMIN, OTK_ANALYST→ANALYST, OTK_COMPLIANCE_OFFICER→COMPLIANCE_OFFICER, OTK_AUDITOR→AUDITOR, OTK_VIEWER→VIEWER
- AI Service e Case Management consolidados com persistência PostgreSQL, RBAC e trilha regulatória (`evidence_trail`)
- gap principal deixou de ser ausência de código; hoje é **M5 Push Remoto ✅ EFETIVADO 10/08 21:36 BRT (0 commits ahead origin/main, bloco 39 commits `6617fd4..a4f2231`, M5 Bloqueio Push Remoto formalmente QUEBRADO)** + **handoff humano 4-olhos (sign-off PGP 6 assinaturas CLO OAB primeiro, prazo 12/08 23:59 BRT)** + **homologação externa real AML/KYT + Feed UE tokenizado + OIDC MFA IdP produtivo + prova operacional revisável e aceite institucional**

## Precedencia Documental

Use esta ordem quando houver conflito:

1. arquivos canonicamente indexados neste `docs/README.md`
2. evidências datadas e sign-offs em `docs/governance-weekly/`
3. READMEs tecnicos locais em subpastas especificas

Arquivos paralelos fora dessa trilha devem ser consolidados, arquivados ou removidos.

## Taxonomia Documental

- `documentacao viva`: arquivos `docs/*.md` indexados aqui e usados como fonte primaria de arquitetura, contrato, operação, readiness e governança executiva
- `documentacao de ciclo`: materiais humanos datados ainda ativos em `docs/governance-weekly/cycles/`
- `documentacao gerada`: artefatos produzidos automaticamente em `docs/governance-weekly/generated/`, especialmente `generated/windows/<window_id>/`
- `documentacao historica`: artefatos datados preservados em `docs/history/` apenas como registro frio, nunca como baseline corrente
- `documentacao arquivada`: historico preservado em `docs/governance-weekly/archive/`
- o espelho legado `.publish_repo/` foi aposentado e removido em `2026-07-15`; a unica fonte primaria de baseline, contrato e status passa a ser esta arvore canônica

Regras objetivas:

- se o arquivo governa decisao atual, ele deve estar indexado neste `README`
- se o arquivo e evidência de uma semana ou janela especifica, ele deve viver em `governance-weekly/`
- se o arquivo foi superado mas ainda tem valor de trilha, ele deve viver em `history/` ou `archive/`
- se o arquivo repete contrato, comando ou checklist ja coberto por fonte canônica, ele deve ser consolidado ou removido

## Mapa canônico

### Arquitetura e Produto

- [Arquitetura](./architecture.md): boundaries do sistema, dados, tabelas-chave e regras criticas
- [Contratos de API](./api-contracts.md): endpoints, payloads e fluxos expostos
- [Arquitetura da Selagem DD/SoF](./evidence-manual-package-strong-sealing-architecture.md): visao arquitetural da trilha de selagem institucional forte ja implementada no baseline atual
- [Cobertura do Frontend](./frontend-coverage-matrix.md): rotas reais, cobertura por modulo, lacunas remanescentes e resumo executivo da trilha estatica
- [Rastreabilidade canônica de Regressao Estatica do Frontend](./frontend-static-regression-traceability.md): fonte unica do mapeamento `cockpit -> spec -> contrato protegido`
- [Checklist canônico de Regressao Estatica e Contratos Visuais do Frontend](./frontend-static-regression-checklist.md): documento canônico da trilha de contratos visuais, regressao estatica e gate de rollout
- [Checklist de Rollout dos Contratos Visuais](./frontend-visual-contract-rollout-checklist.md): ponte de compatibilidade para links legados, redirecionando ao checklist canônico
- [RBAC e Permissoes](./rbac-and-permissions.md): matriz funcional de acesso
- [Roadmap de Secrets e RBAC para Producao](./production-secrets-and-rbac-roadmap.md): caminho canônico pos-90% para `P2-04` e `P2-05`

### operação e Release

- [operação Local](./operations.md): bootstrap local, troubleshooting e comandos do dia a dia
- [Deploy e Staging](./deploy-and-staging.md): fonte canônica do fluxo tecnico `prepare -> validate -> preflight -> run`
- [Blueprint Render para Staging Full-Stack](./render-staging-blueprint.md): fonte canônica da topologia hospedada em `render.full-stack.yaml` e do preenchimento manual `sync: false` no Render
- [**Helm Chart Kubernetes (Sprint 14 M8)**](../infra/k8s/charts/ontrackchain-platform/): Single Chart `ontrackchain-platform` v1.0.0 — 9 FastAPI DRY range, PG16 pgvector StatefulSet, Prometheus/Grafana/Alertmanager, Keycloak v25, Traefik Ingress, HPA/PDB/NetworkPolicy PSP LGPD. Ver `Chart.yaml`, `values.yaml`, `templates/00-*.yaml`.
- [**Disaster Recovery PG16 (Sprint 13 M16)**](../.github/workflows/nightly-dr-backup-restore.yml): CRON sáb 02:00UTC, self-hosted, same-run restore 5433, 1% LGPD, validação 5 tabelas core, Dead Man duplo Issue/Healthchecks.io.
- [GitHub Environment para Staging Serio](./github-environment-staging-serious.md): fonte canônica do workflow manual, approvals e secret multi-linha da janela seria
- [Template Keycloak OIDC](./keycloak-oidc-template.md): referencia de configuração inicial do IdP, util para alinhamento com `environment-variables.md`
- [Variaveis de Ambiente](./environment-variables.md): baseline por servico + **padrão `REPLACE_WITH_` (.env-secrets.template SSOT)** + Helm existingSecret
- [Secrets Template One-Shot (4-eyes)](../.env-secrets.template): 10 placeholders `REPLACE_WITH_*` para UI one-shot provisionamento segredo por 2 SREs
- [Runbooks Operacionais](./runbooks.md): resposta inicial por sintoma e severidade, incluindo triagem de `hostedShowcaseFallback` em staging hospedado
- [CI/CD e Release](./ci-cd-and-release.md): **16 status checks ci.yml + 4 Policies OPA Rego + 6 nightly (DR, Explorers Live, Load Test, E2E PR shard=8, Dependabot Security Auto-Merge)**
- [Run Sheet da Malha E2E Local](./governance-weekly/guides/E2E_LOCAL_MESH_RUN_SHEET.md): preflight, guardrails e triagem objetiva da baseline Playwright local
- [Playbook de Incidente Cross-Domain e RCA](./cross-domain-incident-rca-playbook.md): escalacao leve, ownership e fechamento de causa raiz sem abrir um servico novo
- [Pre-Production Checklist](./pre-production-checklist.md): validações obrigatorias antes de promover
- [Branch Protection SSOT (16 main / 10 develop)](../.github/settings.yml): `enforce_admins=true` AMBOS, 15 status checks para main incluindo SBOM Grype M12, Policy OPA M10, Observabilidade Gate M16b
- [OPA Rego 4 Policies (M10 + M16b)](../policies/): 01_deny_continue_on_error, 02_deny_ubuntu_latest_heavy, 03_deny_missing_timeout_minutes, **04_deny_missing_observability_endpoints_fastapi** (M16b NOVO)

### Validação, Compliance e Auditoria

- [validação e Auditoria](./validation-and-audit.md): smoke, Playwright, preflights e evidências
- [Catálogo de Eventos — evidence_trail](./evidence-event-catalog.md): lista consolidada de `event_type` para trilha regulatória
- [validação em Staging - Diretorio Federado](./federated-directory-staging-validation.md): trilha complementar do diretorio federado em `staging`, usada por guias e validações ativas
- [Compliance e Controles de segurança](./compliance-and-security-controls.md): enforcement e gaps residuais
- [relatórios de Compliance (Gerados)](./compliance-reports/README.md): outputs gerados a partir das metricas de governança, usados como apoio para revisao operacional
- [Matriz de evidências e Auditoria](./evidence-and-audit-matrix.md): relacao entre fluxos, artefatos e provas
- [Readiness regulatório](./regulatory-readiness.md): leitura honesta da prontidao regulatoria
- [Retention e Recovery](./retention-and-recovery-policy.md): baseline de recuperacao e retencao
- [Checklist de Rollout do Manual Package DD/SoF](./evidence-manual-package-rollout-checklist.md): gate complementar para mudancas na trilha manual forte

### Planejamento e governança

- [Portal do Workspace](./workspace-root-readme.md): redirect para as fontes canônicas, evitando duplicação e drift
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md): leitura curta para sponsors e diretoria
- [Kit de Execucao por evidência](./project-maturity-evidence-execution-kit.md): templates, semaforo e plano `D1-D7`
- [Scorecard Oficial](./project-kpi-scorecard.md): formula e baseline executiva
- [Avaliacao de Maturidade](./project-maturity-assessment.md): baseline viva com racional tecnico e regulatório
- [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md): fonte canônica da execucao, dos gates operacionais e da cobranca por owner ate `95%`
- [Assessments formais](./assessments/README.md): pareceres datados de calibracao e `go/no-go`
- [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md): parecer formal datado de calibracao e `go/no-go`, preservado como corte historico e nao como baseline viva corrente
- [Board de Prioridades](./project-priority-board.md): fonte canônica da ordem estrategica de ataque por frente
- [Board Operacional](./project-operational-execution-board.md): fonte canônica do status, owner, evidência e fila diaria de execucao
- [Registro de Riscos](./project-risk-register.md): riscos tecnicos, operacionais e regulatórios
- [Checklist para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md): ponte legada de compatibilidade para o plano canônico

### Janela Seria e evidências Datadas

- [Runbook Semanal de governança](./project-weekly-governance-runbook.md)
- [Gates de release](./project-release-gates.md): fonte canônica da decisao executiva de `go/no-go`
- [Ownership do `.env.staging`](./staging-env-ownership.md): aplicacao da taxonomia canônica de ownership aos placeholders, handoff e bloqueios da janela
- [Ownership e SLAs operacionais](./operational-ownership-and-slas.md): fonte canônica de dominios, owners, backups e SLA base por severidade
- [Matriz de War Room](./staging-serious-window-war-room-matrix.md)
- [Historico de apoio](./history/README.md): indice de planos, trackers e runbooks datados que nao sao fonte primaria
- [governança Semanal](./governance-weekly/README.md): ciclos, guias permanentes, templates, artefatos gerados e historico datado

### Decisoes Arquiteturais

- [ADRs](./adrs/README.md)

## Leitura Recomendada por Objetivo

### Entender o produto

1. `architecture.md`
2. `api-contracts.md`
3. `frontend-coverage-matrix.md`
4. `project-kpi-scorecard.md`

### Operar localmente

1. `operations.md`
2. `environment-variables.md`
3. `validation-and-audit.md`
4. `governance-weekly/guides/E2E_LOCAL_MESH_RUN_SHEET.md`
5. `apps/frontend/tests/e2e/README.md`
6. `deploy-and-staging.md`

### Validar integrações e janela seria

1. `deploy-and-staging.md`
2. `project-release-gates.md`
3. `github-environment-staging-serious.md`
4. `render-staging-blueprint.md`
5. `staging-env-ownership.md`
6. `staging-serious-window-war-room-matrix.md`
7. `governance-weekly/README.md`

### Auditar segurança e compliance

1. `compliance-and-security-controls.md`
2. `evidence-and-audit-matrix.md`
3. `regulatory-readiness.md`
4. `rbac-and-permissions.md`

## Regras de Manutencao

- atualize primeiro os documentos canônicos antes de criar artefatos paralelos
- sincronize docs com codigo, migrations, scripts e endpoints no mesmo ciclo de mudanca
- quando houver diferenca entre contrato e runtime, registre a nuance explicitamente
- documentos datados de execucao devem viver em `governance-weekly/` ou `governance-weekly/archive/`
- documentos redundantes, snapshots soltos ou analises supersedidas devem ser removidos
- documentos datados mantidos fora de `governance-weekly/` devem carregar aviso explicito de que nao sao fonte primaria

## Consolidacoes Relevantes (Sprint 1 → Sprint 14)

Esta base ja foi racionalizada para reduzir drift. Referencias principais:

**Sprint 1-5 (Antigas, preservadas como histórico):**
- `api-contracts.md` passou a ser a fonte canônica dos contratos HTTP da trilha de selagem DD/SoF
- `docs/evidence-manual-package-strong-sealing-backlog.md` foi consolidado e removido
- `docs/frontend-hardening-executive-summary.md` foi absorvido pelo conjunto `frontend-coverage-matrix.md` + `frontend-static-regression-*` e removido
- os artefatos `first-serious-window-*` e `staging-serious-window-signoff-template.md` foram movidos para `history/` e deixaram de competir com a raiz viva de `docs/`
- a execucao integrada de janela seria foi consolidada em `governance-weekly/guides/SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md`
- `docs/history/DAY_OF_WINDOW_RUNBOOK_STG_2026_07_06_A.md` foi absorvido pelo ciclo `governance-weekly/cycles/2026-07-06/`
- os caminhos canônicos de artefatos gerados agora usam `docs/governance-weekly/generated/windows/<window_id>/`
- o pos-processamento da janela seria agora gera `sign-off`, sincronizacao semanal, board operacional e `go/no-go decision packet` a partir do mesmo payload consolidado
- o documento `render-staging-blueprint.md` voltou a refletir a topologia `full-stack` do Render, incluindo `Traefik`, `Keycloak`, `auth-service`, `Postgres`, `Key Value`, workers e observabilidade
- a auditoria de `.publish_repo/` foi concluida com aposentadoria definitiva do espelho em `2026-07-15`, apos confirmacao explicita para descontinuar qualquer uso externo/manual remanescente

**Sprint 6-14 (Novas, consolidações MVP + Pós-MVP):**
- **GAPs 100% média (Sprint 6)**: 12 GAPs do documento Arquitetura Técnica QA/DevOps 100% (antes 99,3%). Label `e2e-required` gate E2E shard=8 apenas em PRs frontend/case. Grafana Dashboard Único QA 9 paineis consolidados.
- **Branch Protection M6 (Sprint 8)**: `.github/settings.yml` Probot SSOT — main=16 checks, develop=10 checks, `enforce_admins=true` BOTH ninguém bypassa (incluindo CODEOWNERS/admins).
- **SonarCloud + CodeCov M8 (Sprint 9)**: 2 gates P0 obrigatórios, 80% overall / 85% patch cobertura mínima, Sonar analysis on main + PRs.
- **Policies OPA M10 (Sprint 10)**: 4 regras Rego `policies/01_04.rego` — nega continue-on-error P0 / nega ubuntu-latest em jobs pesados (pytest matrix ×7, playwright shard=8, run-explorers-live) / timeout obrigatório 100% jobs / nega FastAPI sem /healthz+/metrics. Job `policy-gate-conftest` usa `openpolicyagent/conftest:v0.52.0`.
- **SBOM Grype M12 (Sprint 11)**: CycloneDX ISO/IEC 5962 sbom-python-monorepo.cdx.json gerado a cada merge main, retenção 90 dias compliance LGPD/SOC2. Grype `--fail-on high` bloqueia merge — HIGH/CRITICAL bypass proibido, nenhum admin pode sobrescrever.
- **Dependabot Security Auto-Merge M13 (Sprint 11)**: Cron quartas 04:00UTC, apenas `security-only`, SQUASH via Merge Queue, 15 gates → Canary 30min → Prod 4-eyes. SLA 0-day CVE <2h.
- **Validação Regressão + Diagramas M14/M15 (Sprint 12)**: AST Parse 212 arquivos Python 0 SyntaxErrors, YAML safe_load 18 arquivos, 3 Policies simulação 0 violações, Branch Protection SSOT, Tokens guard 11 prefixos 0 reais detectados. Diagramas C4 L2 D1/D2/D3 no ADR-018.
- **DR PG16 M16 + Observabilidade M16b + Secrets M16b (Sprint 13)**: Workflow `nightly-dr-backup-restore.yml` sáb 02UTC; 10 Secrets `.env-secrets.template` UI one-shot 4-eyes; Gate Observabilidade tríplice (job CI + Policy #04 OPA + 9 endpoints /healthz /metrics).
- **Helm Chart M8/M8b (Sprint 14)**: Single Chart `ontrackchain-platform` v1.0.0. 9 Deployments FastAPI DRY range (`{{ range $svcName, $svc := .Values.services }}`), PG16 pgvector + Prometheus StatefulSets PVC LGPD label, 9 HPA autoscaling/v2, 13 PDB policy/v1, 4 NetworkPolicy default-deny LGPD + block IMDS 169.254.169.254, PSP PodSecurity runAsNonRoot/drop ALL caps/seccomp RuntimeDefault/readOnlyRootFilesystem, Traefik IngressClass + Ingress multi-host tls cert-manager, Keycloak v25 realm import ConfigMap.
- **Federação Roles OTK_* (Sprints anteriores)**: Pacote `ontrackchain_shared` função `canonicalize_role()` SSOT + `authz.ts` frontend — 5 aliases federados (ADMIN/ANALYST/COMPLIANCE_OFFICER/AUDITOR/VIEWER prefixados OTK_).

## O Que Esta Documentado Agora

A trilha canônica atual reflete explicitamente:

- frontend com i18n tri-locale e labels institucionais
- trilha DD/SoF com pacote manual canônico, selagem institucional forte, governança pós-selagem e contratos HTTP consolidados em `api-contracts.md`
- `monitoring` modularizado em `monitoring-api.ts`, hooks dedicados e paineis apresentacionais
- contratos compartilhados em `app/lib/` para `audit`, `evidence`, `team`, `reports` e `monitoring`
- classificacao operacional das suites Playwright com preflight explicito
- work-items compartilhados como base da operação multiusuario
- bundles de readiness para `OIDC`, `AML/KYT live` e feed UE
- `decision packet` executivo de `go/no-go` como artefato derivado do payload consolidado da janela seria
- promocao de maturidade regida por evidência real, revisao humana e aprovacao explicita

## Estrutura Esperada

- `docs/*.md`: documentação viva e canonicamente indexada
- `docs/governance-weekly/guides/*.md`: guias permanentes da governança semanal
- `docs/governance-weekly/templates/*.md`: modelos reutilizaveis
- `docs/governance-weekly/cycles/**/*.md`: artefatos datados ainda ativos por ciclo
- `docs/governance-weekly/generated/**/*.md`: artefatos gerados e dashboards
- `docs/governance-weekly/archive/**/*.md`: historico preservado
- `docs/adrs/*.md`: decisoes arquiteturais formais
