# Documentacao Canonica

## Objetivo

Centralizar a documentacao viva do Ontrackchain em um unico indice, reduzindo drift entre codigo, runtime, operacao e narrativa executiva.

Estado de referencia atual:

- baseline oficial: `91%` tecnico, `78%` regulatorio/operacional, `87%` consolidado
- frontend operacional com tri-locale, contratos compartilhados e cockpits endurecidos
- `monitoring` decomposto em loaders, hooks e paineis dedicados
- Playwright institucionalizado por classes (`stack real leve`, `browser-mocked`, `ssr-mocked`, `dev-auth`, `oidc-critical`)

## Precedencia Documental

Use esta ordem quando houver conflito:

1. arquivos canonicamente indexados neste `docs/README.md`
2. evidencias datadas e sign-offs em `docs/governance-weekly/`
3. READMEs tecnicos locais em subpastas especificas (`infra/`, `migrations/`, etc.)

Arquivos paralelos fora dessa trilha devem ser consolidados, arquivados ou removidos.

## Mapa Canonico

### Arquitetura e Produto

- [Arquitetura](./architecture.md): boundaries do sistema, dados, tabelas-chave e regras criticas
- [Contratos de API](./api-contracts.md): endpoints, payloads e fluxos expostos
- [Cobertura do Frontend](./frontend-coverage-matrix.md): rotas reais, cobertura por modulo e lacunas remanescentes
- [RBAC e Permissoes](./rbac-and-permissions.md): matriz funcional de acesso

### Operacao e Release

- [Operacao Local](./operations.md): bootstrap local, troubleshooting e comandos do dia a dia
- [Deploy e Staging](./deploy-and-staging.md): fluxo `prepare -> validate -> preflight -> run`
- [Variaveis de Ambiente](./environment-variables.md): baseline por servico e overrides
- [CI/CD e Release](./ci-cd-and-release.md): workflows, quality gates e promocao
- [Runbooks Operacionais](./runbooks.md): resposta inicial por sintoma e severidade
- [Pre-Production Checklist](./pre-production-checklist.md): validacoes obrigatorias antes de promover

### Validacao, Compliance e Auditoria

- [Validacao e Auditoria](./validation-and-audit.md): smoke, Playwright, preflights e evidencias
- [Compliance e Controles de Seguranca](./compliance-and-security-controls.md): enforcement e gaps residuais
- [Matriz de Evidencias e Auditoria](./evidence-and-audit-matrix.md): relacao entre fluxos, artefatos e provas
- [Readiness Regulatorio](./regulatory-readiness.md): leitura honesta da prontidao regulatoria
- [Retention e Recovery](./retention-and-recovery-policy.md): baseline de recuperacao e retencao

### Planejamento e Governanca

- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md): leitura curta para sponsors e diretoria
- [Kit de Execucao por Evidencia](./project-maturity-evidence-execution-kit.md): templates, semaforo e plano `D1-D7`
- [Scorecard Oficial](./project-kpi-scorecard.md): formula e baseline executiva
- [Avaliacao de Maturidade](./project-maturity-assessment.md): baseline viva com racional tecnico e regulatorio
- [Assessments formais](./assessments/README.md): pareceres datados de calibracao e `go/no-go`
- [Avaliacao de Status](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md): parecer formal datado de calibracao e `go/no-go`
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

## O Que Esta Documentado Agora

A trilha canonica atual reflete explicitamente:

- frontend com i18n tri-locale e labels institucionais
- `monitoring` modularizado em `monitoring-api.ts`, hooks dedicados e paineis apresentacionais
- contratos compartilhados em `app/lib/` para `audit`, `evidence`, `team`, `reports` e `monitoring`
- classificacao operacional das suites Playwright com preflight explicito
- work-items compartilhados como base da operacao multiusuario
- bundles de readiness para `OIDC`, `AML/KYT live` e feed UE
- promocao de maturidade regida por evidencia real, revisao humana e aprovacao explicita

## Estrutura Esperada

- `docs/*.md`: documentacao viva e canonicamente indexada
- `docs/governance-weekly/guides/*.md`: guias permanentes da governanca semanal
- `docs/governance-weekly/templates/*.md`: modelos reutilizaveis
- `docs/governance-weekly/cycles/**/*.md`: artefatos datados ainda ativos por ciclo
- `docs/governance-weekly/generated/**/*.md`: artefatos gerados e dashboards
- `docs/governance-weekly/archive/**/*.md`: historico preservado
- `docs/adrs/*.md`: decisoes arquiteturais formais
