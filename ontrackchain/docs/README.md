# Documentacao do Projeto

## Objetivo

Centralizar os documentos canonicos do Ontrackchain pós-Sprint 6, refletindo a consolidacao dos 7 cockpits regulatorios com history panels, i18n tri-locale e governanca operacional de forma coerente com o runtime atual, reduzindo drift entre codigo, operacao e narrativa executiva.

**Estado Atual:** Sprint 6 concluída (maturidade técnica 91%, regulatória 78%, consolidada 87%). Documentação canônica consolidada e mantida prioritariamente em `docs/` e `docs/governance-weekly/`.

## Como Navegar

### Visao Geral

- [README raiz](../README.md): estado atual, quick start e mapa principal do repositorio com Sprint 6 consolidada.
- [Arquitetura](./architecture.md): desenho macro dos 7 cockpits (counterparties, sanctions, evidence, reports, blocks, ros-coaf, alerts), history panels persistidos e fluxo de dados real.
- [Contratos de API](./api-contracts.md): contratos HTTP principais com endpoints de work-items, governance e operações consolidadas.
- [Cobertura do Frontend](./frontend-coverage-matrix.md): matriz canonica de telas `prontas/parciais/faltando` com Sprint 6 nos 7 cockpits cruzada com contratos reais.

### Operacao e Release

- [Deploy e Staging](./deploy-and-staging.md): fluxo tecnico canônico de deploy, `prepare -> validate -> preflight -> run` e artefatos do rito consolidado.
- [Operacao Local](./operations.md): subida local, migrations, validacoes e troubleshooting.
- [Variaveis de Ambiente](./environment-variables.md): baseline por servico e overrides operacionais.
- [Ownership do `.env.staging`](./staging-env-ownership.md): ownership nominal, handoff e bloqueios do arquivo privado da janela.
- [Matriz de Execucao por Owner para Janela Seria](./staging-serious-window-war-room-matrix.md): visao de war room com trilhas, dependencias, comandos, evidencias e escalacoes.
- [Template de War Room da Janela Seria](./governance-weekly/_template-staging-serious-window-war-room.md): modelo versionavel para coordenar `go/no-go`, bloqueadores e evidencias no dia da execucao.
- [Folha de Preenchimento Manual da Janela `stg-2026-07-06-a`](./governance-weekly/2026-07-06-staging-serious-window-manual-fill-sheet.md): lista unica de placeholders, owners e validacoes para tirar a janela de `no-go`.
- [CI/CD e Release](./ci-cd-and-release.md): quality gates, workflows e trilhos de validacao.
- [Runbooks Operacionais](./runbooks.md): troubleshooting por sintoma, severidade e resposta inicial de incidentes.
- [Gates de Release para Staging Serio](./project-release-gates.md): criterio formal e executivo de `go/no-go` da janela.

### Compliance, Seguranca e Auditoria

- [Compliance e Controles de Seguranca](./compliance-and-security-controls.md): controles ativos, enforcement e gaps residuais.
- [Matriz de Evidencias e Auditoria](./evidence-and-audit-matrix.md): mapeamento entre fluxos, eventos, hashes e artefatos.
- [Validacao e Auditoria](./validation-and-audit.md): smoke, Playwright, preflights e testes de regressao.
- [Readiness Regulatorio](./regulatory-readiness.md): leitura honesta de prontidao regulatoria.
- [RBAC e Permissoes](./rbac-and-permissions.md): matriz funcional de acesso.

### Planejamento e Governanca

- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md): leitura executiva da baseline `91% / 78% / 87%` e dos gaps residuais.
- [Avaliacao Consolidada de Status do Projeto](./PROJECT_STATUS_ASSESSMENT_2026_07_03.md): memorando executivo, matriz de subida para `95%` e parecer formal de `go/no-go`.
- [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md): checklist por owner para executar e cobrar a trilha de `87%` ate `95%`.
- [Tracker Semanal de Owners para 95%](./WEEKLY_OWNERS_TRACKER_TO_95_PERCENT.md): planilha em Markdown para cobrar evidência, próxima ação e prazo por owner.
- [Roteiro Operacional do Dia da Janela `stg-2026-07-06-a`](./DAY_OF_WINDOW_RUNBOOK_STG_2026_07_06_A.md): sequência condensada do dia da janela, do war room ao `go/no-go`.
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md): KPI canonico com pesos, formula e percentual total consolidado.
- [Board de Prioridades do Projeto](./project-priority-board.md): prioridades estrategicas atuais, Sprint 6 consolidada com paineis de historico.
- [Board Operacional Unico](./project-operational-execution-board.md): fila diaria `P0/P1/P2` com dependencias, evidencias e gates de fechamento.
- [Runbook de Governanca Semanal](./project-weekly-governance-runbook.md): rito de acompanhamento semanal.
- [Registros Semanais de Governanca](./governance-weekly/README.md): snapshots historicos, war room, tracking, sign-off e evidencias fechadas por ciclo.
- [Registro de Riscos do Projeto](./project-risk-register.md): riscos tecnicos, operacionais e regulatorios.

## Leitura Recomendada por Tema

### Se o foco for Compliance

1. `architecture.md`
2. `api-contracts.md`
3. `compliance-and-security-controls.md`
4. `evidence-and-audit-matrix.md`
5. `regulatory-readiness.md`

### Se o foco for Operacao de Staging

1. `deploy-and-staging.md`
2. `operations.md`
3. `environment-variables.md`
4. `staging-env-ownership.md`
5. `staging-serious-window-war-room-matrix.md`
6. `governance-weekly/_template-staging-serious-window-war-room.md`
7. `project-release-gates.md`

### Se o foco for Diagnostico e Validacao

1. `validation-and-audit.md`
2. `evidence-and-audit-matrix.md`
3. `project-risk-register.md`

## Estado Atual da Documentacao Canonica

### Sprint 6 - Consolidacao de Cockpits com History Panels

A documentacao principal agora reflete explicitamente:

**Arquitetura Operacional:**

- 7 cockpits regulatorios consolidados: `counterparties`, `sanctions`, `evidence`, `reports`, `blocks`, `ros-coaf`, `alerts`
- History panels persistidos em cada cockpit com i18n tri-locale (pt-BR/en/es)
- Workspace records como base de reusabilidade: timeline, comments, status history
- Metadata JSON em work-items para DD/SoF, notas operacionais e document refs

**Fluxos Implementados:**

- `evidence_trail` append-only com encadeamento `SHA-256`
- `preventive_blocks`, `counterparties`, `sanctions_hits_cache` e `ros_records` com persistência
- `compliance-worker` com override operacional de `source_url`
- `regulatory_work_items` como fila operacional multiusuario persistida no servidor com timeline e comentarios
- `sanctions` consumindo fila compartilhada como fonte primaria com fallback local controlado
- `alerts` com rastreamento por incidente em work-items e sincronizacao de fechamento via `ack`
- Fluxo `ROS/COAF` com aprovacao/rejeicao/submissao manual

**Gates e Validacoes:**

- `check_compliance_provider_runtime.py` como gate de runtime para AML/KYT live
- `run_eu_sanctions_window.py` para janela UE
- `run_regulatory_readiness_bundle.py` para anexar AML/KYT + janela UE em bundle unico
- `run_staging_window.py` e `make run-serious-window-local*` como rito consolidado

**Operacoes:**

- Pacote operacional da janela seria com war room, tracking ao vivo, manual fill sheet e sign-off
- Diferenca explícita entre endpoints live, capacidades degradadas e gaps ainda abertos
- Governance semanal consolidada em `/governance-weekly/` com active tracking + archive histórico

## Regra de Manutencao

- atualizar primeiro estes documentos canonicos antes de criar novos artefatos paralelos
- quando houver divergencia entre contrato e runtime, registrar explicitamente a nuance em vez de suavizar o problema
- sempre sincronizar docs com migrations, scripts operacionais e endpoints reais no mesmo ciclo de mudanca

## Limpeza e Organizacao (Julho 2026)

**Consolidacao:** Documentacao reduzida de 98+ arquivos para 28 canonicos + 16 governance + 22 archived.

- Todos os runbooks de Sprints 1-4 (45 files) movidos para `governance-weekly/archive/`
- Arquivos de planejamento antigos (project-execution-plan-to-90, project-operational-plan-to-95) deletados
- Referências atualizadas em 13 documentos principais para refletir Sprint 6 consolidada
- Zero referências quebradas no estado final

**Estrutura Atual:**

- `/docs/*.md`: 28 documentos canônicos (operação, compliance, planning, governance)
- `/docs/governance-weekly/`: 16 arquivos (templates + tracking atual)
- `/docs/governance-weekly/archive/`: 22 arquivos históricos (Sprints 1-4 preservados)
