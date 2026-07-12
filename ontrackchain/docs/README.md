# Documentacao Canonica

## Objetivo

Centralizar a documentacao viva do Ontrackchain em um unico indice, reduzindo drift entre codigo, runtime, operacao e narrativa executiva.

Estado de referencia atual:

- baseline oficial: `92%` tecnico, `79%` regulatorio/operacional, `88%` consolidado
- frontend operacional com tri-locale, contratos compartilhados e 7 cockpits convergidos ao mesmo modelo de workspace
- `monitoring` decomposto em loaders, hooks e paineis dedicados
- `P1-01` concluido com contrato unificado de metadata para `work-items`
- `P2-03` consolidado com RCA cross-domain leve
- `P2-05` em execucao incremental com `REVIEWER` e `BILLING_ADMIN` em superficies reais
- Playwright institucionalizado por classes (`stack real leve`, `browser-mocked`, `ssr-mocked`, `dev-auth`, `oidc-critical`)
- o blueprint atual do Render foi reduzido para `frontend-only`; staging serio full-stack continua documentado separadamente

## Precedencia Documental

Use esta ordem quando houver conflito:

1. arquivos canonicamente indexados neste `docs/README.md`
2. evidencias datadas e sign-offs em `docs/governance-weekly/`
3. READMEs tecnicos locais em subpastas especificas (`infra/`, `migrations/`, etc.)

Arquivos paralelos fora dessa trilha devem ser consolidados, arquivados ou removidos.

## Taxonomia Documental

Use esta classificacao para decidir onde cada artefato deve viver:

- `documentacao viva`: arquivos `docs/*.md` indexados aqui e usados como fonte primaria de arquitetura, contrato, operacao, readiness e governanca executiva
- `documentacao historica`: artefatos datados preservados em `docs/history/` apenas como registro frio, nunca como baseline corrente
- `documentacao gerada`: artefatos produzidos automaticamente em `docs/governance-weekly/generated/`, especialmente no namespace `generated/windows/<window_id>/`
- `documentacao de ciclo`: materiais humanos datados ainda ativos em `docs/governance-weekly/cycles/`
- `documentacao arquivada`: historico preservado em `docs/governance-weekly/archive/`
- `.publish_repo/`, quando existir na raiz agregadora, deve ser tratado apenas como espelho de publicacao e nunca como fonte primaria de baseline, contrato ou status

Regras objetivas:

- se o arquivo governa decisao atual, ele deve estar indexado neste `README`
- se o arquivo e evidência de uma semana/janela especifica, ele deve viver em `governance-weekly/`
- se o arquivo foi superado mas ainda tem valor de trilha, ele deve viver em `history/` ou `archive/`
- se o arquivo repete contrato, comando ou checklist ja coberto por fonte canônica, ele deve ser consolidado ou removido

## Mapa Canonico

### Arquitetura e Produto

- [Arquitetura](./architecture.md): boundaries do sistema, dados, tabelas-chave e regras criticas
- [Contratos de API](./api-contracts.md): endpoints, payloads e fluxos expostos
- [Arquitetura da Selagem DD/SoF](./evidence-manual-package-strong-sealing-architecture.md): visao arquitetural da trilha de selagem institucional forte ja implementada no baseline atual
- [Cobertura do Frontend](./frontend-coverage-matrix.md): rotas reais, cobertura por modulo e lacunas remanescentes
- [Rastreabilidade de Regressao Estatica do Frontend](./frontend-static-regression-traceability.md): mapeia `cockpit -> spec -> contrato protegido`
- [Checklist de Regressao Estatica do Frontend](./frontend-static-regression-checklist.md): gate operacional da trilha de contratos visuais e semanticos
- [Checklist de Rollout dos Contratos Visuais](./frontend-visual-contract-rollout-checklist.md): criterio de rollout seguro do hardening de UI
- [RBAC e Permissoes](./rbac-and-permissions.md): matriz funcional de acesso
- [Roadmap de Secrets e RBAC para Producao](./production-secrets-and-rbac-roadmap.md): caminho canonico pos-90% para `P2-04` e `P2-05`

### Operacao e Release

- [Operacao Local](./operations.md): bootstrap local, troubleshooting e comandos do dia a dia
- [Deploy e Staging](./deploy-and-staging.md): fluxo `prepare -> validate -> preflight -> run`
- [Blueprint Render para Frontend-Only](./render-staging-blueprint.md): estado atual do deploy publico no Render, limitado ao shell do frontend
- [GitHub Environment para Staging Serio](./github-environment-staging-serious.md): contrato operacional do environment manual usado na janela seria
- [Template Keycloak OIDC](./keycloak-oidc-template.md): referencia de configuracao inicial do IdP, util para alinhamento com `environment-variables.md`
- [Variaveis de Ambiente](./environment-variables.md): baseline por servico e overrides
- [CI/CD e Release](./ci-cd-and-release.md): workflows, quality gates e promocao
- [Runbooks Operacionais](./runbooks.md): resposta inicial por sintoma e severidade
- [Playbook de Incidente Cross-Domain e RCA](./cross-domain-incident-rca-playbook.md): escalacao leve, ownership e fechamento de causa raiz sem abrir um servico novo
- [Pre-Production Checklist](./pre-production-checklist.md): validacoes obrigatorias antes de promover

### Validacao, Compliance e Auditoria

- [Validacao e Auditoria](./validation-and-audit.md): smoke, Playwright, preflights e evidencias
- [Compliance e Controles de Seguranca](./compliance-and-security-controls.md): enforcement e gaps residuais
- [Matriz de Evidencias e Auditoria](./evidence-and-audit-matrix.md): relacao entre fluxos, artefatos e provas
- [Readiness Regulatorio](./regulatory-readiness.md): leitura honesta da prontidao regulatoria
- [Retention e Recovery](./retention-and-recovery-policy.md): baseline de recuperacao e retencao
- [Checklist de Rollout do Manual Package DD/SoF](./evidence-manual-package-rollout-checklist.md): gate complementar para mudancas na trilha manual forte

### Planejamento e Governanca

- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md): leitura curta para sponsors e diretoria
- [Kit de Execucao por Evidencia](./project-maturity-evidence-execution-kit.md): templates, semaforo e plano `D1-D7`
- [Scorecard Oficial](./project-kpi-scorecard.md): formula e baseline executiva
- [Avaliacao de Maturidade](./project-maturity-assessment.md): baseline viva com racional tecnico e regulatorio
- [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md): caminho executivo unificado para sair de `88%` e atingir `95%`
- [Assessments formais](./assessments/README.md): pareceres datados de calibracao e `go/no-go`
- [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md): parecer formal datado de calibracao e `go/no-go`, preservado como corte historico e nao como baseline viva corrente
- [Board de Prioridades](./project-priority-board.md): prioridades por frente
- [Board Operacional](./project-operational-execution-board.md): fila diaria de execucao
- [Registro de Riscos](./project-risk-register.md): riscos tecnicos, operacionais e regulatorios
- [Checklist para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md): checklist de cobranca por frente

### Janela Seria e Evidencias Datadas

- [Runbook Semanal de Governanca](./project-weekly-governance-runbook.md)
- [Gates de release](./project-release-gates.md)
- [Ownership do `.env.staging`](./staging-env-ownership.md)
- [Ownership e SLAs operacionais](./operational-ownership-and-slas.md)
- [Matriz de War Room](./staging-serious-window-war-room-matrix.md)
- [Historico de apoio](./history/README.md): indice de planos, trackers e runbooks datados que nao sao fonte primaria
- [Governanca Semanal](./governance-weekly/README.md): ciclos, guias permanentes, templates, artefatos gerados e historico datado

### Legado Mantido por Compatibilidade

- [Checklist de Evidencia Minima da Primeira Janela Seria](./history/first-serious-window-evidence-checklist.md): apoio historico movido para `history/`; a fonte viva e `governance-weekly/guides/`
- [Runbook do Primeiro Disparo Real](./history/first-serious-window-first-dispatch-runbook.md): apoio historico movido para `history/` para reconciliar ciclos antigos
- [Template de Sign-Off da Janela Seria](./history/staging-serious-window-signoff-template.md): template legado movido para `history/` e preservado apenas para compatibilidade de referencia

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
4. `deploy-and-staging.md`

### Validar integracoes e janela seria

1. `deploy-and-staging.md`
2. `project-release-gates.md`
3. `staging-env-ownership.md`
4. `staging-serious-window-war-room-matrix.md`
5. `governance-weekly/README.md`

### Auditar seguranca e compliance

1. `compliance-and-security-controls.md`
2. `evidence-and-audit-matrix.md`
3. `regulatory-readiness.md`
4. `rbac-and-permissions.md`

## Regras de Manutencao

- atualize primeiro os documentos canonicos antes de criar artefatos paralelos
- sincronize docs com codigo, migrations, scripts e endpoints no mesmo ciclo de mudanca
- quando houver diferenca entre contrato e runtime, registre a nuance explicitamente
- documentos datados de execucao devem viver em `governance-weekly/` ou `governance-weekly/archive/`
- documentos redundantes, snapshots soltos ou analises supersedidas devem ser removidos
- documentos datados mantidos fora de `governance-weekly/` devem carregar aviso explicito de que nao sao fonte primaria

## Consolidacoes Recentes

Esta base ja foi racionalizada para reduzir drift. Como referencia:

- `api-contracts.md` passou a ser a fonte canônica dos contratos HTTP da trilha de selagem DD/SoF
- `docs/evidence-manual-package-strong-sealing-backlog.md` foi consolidado e removido
- `docs/frontend-hardening-executive-summary.md` foi absorvido pelo conjunto `frontend-coverage-matrix.md` + `frontend-static-regression-*` e removido
- os artefatos `first-serious-window-*` e `staging-serious-window-signoff-template.md` foram movidos para `history/` e deixaram de competir com a raiz viva de `docs/`
- a execucao integrada de janela seria foi consolidada em `governance-weekly/guides/SERIOUS_WINDOW_FINAL_EXECUTION_PACKET.md`
- `docs/history/DAY_OF_WINDOW_RUNBOOK_STG_2026_07_06_A.md` foi absorvido pelo ciclo `governance-weekly/cycles/2026-07-06/`
- os caminhos canônicos de artefatos gerados agora usam `docs/governance-weekly/generated/windows/<window_id>/`
- o pos-processamento da janela seria agora gera `sign-off`, sincronizacao semanal, board operacional e `go/no-go decision packet` a partir do mesmo payload consolidado
- a trilha antiga de Render full-stack foi consolidada no documento `render-staging-blueprint.md`, agora alinhado ao blueprint `frontend-only`; o runbook de primeiro sync e o checklist de secrets completos foram removidos por estarem obsoletos
- `.publish_repo/` foi auditado e classificado como espelho de publicacao nao-canônico, sem evidencia suficiente para delecao automatica nesta rodada

## O Que Esta Documentado Agora

A trilha canonica atual reflete explicitamente:

- frontend com i18n tri-locale e labels institucionais
- trilha DD/SoF com pacote manual canônico, selagem institucional forte, governanca pós-selagem e contratos HTTP consolidados em `api-contracts.md`
- `monitoring` modularizado em `monitoring-api.ts`, hooks dedicados e paineis apresentacionais
- contratos compartilhados em `app/lib/` para `audit`, `evidence`, `team`, `reports` e `monitoring`
- classificacao operacional das suites Playwright com preflight explicito
- work-items compartilhados como base da operacao multiusuario
- bundles de readiness para `OIDC`, `AML/KYT live` e feed UE
- `decision packet` executivo de `go/no-go` como artefato derivado do payload consolidado da janela seria
- promocao de maturidade regida por evidencia real, revisao humana e aprovacao explicita

## Estrutura Esperada

- `docs/*.md`: documentacao viva e canonicamente indexada
- `docs/governance-weekly/guides/*.md`: guias permanentes da governanca semanal
- `docs/governance-weekly/templates/*.md`: modelos reutilizaveis
- `docs/governance-weekly/cycles/**/*.md`: artefatos datados ainda ativos por ciclo
- `docs/governance-weekly/generated/**/*.md`: artefatos gerados e dashboards
- `docs/governance-weekly/archive/**/*.md`: historico preservado
- `docs/adrs/*.md`: decisoes arquiteturais formais
