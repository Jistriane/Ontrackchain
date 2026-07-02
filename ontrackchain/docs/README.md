# Documentacao do Projeto

## Objetivo

Centralizar os documentos canonicos do Ontrackchain de forma coerente com o runtime atual do projeto, reduzindo drift entre codigo, operacao e narrativa executiva.

## Como Navegar

### Visao Geral

- [README raiz](../README.md): estado atual, quick start e mapa principal do repositorio.
- [Arquitetura](./architecture.md): desenho macro, modulos regulatorios e fluxo de dados real.
- [Contratos de API](./api-contracts.md): contratos HTTP principais, catalogos operacionais e regras de `plan lock`.

### Operacao e Release

- [Deploy e Staging](./deploy-and-staging.md): fluxo tecnico canônico de deploy, `prepare -> validate -> preflight -> run` e artefatos do rito consolidado.
- [Operacao Local](./operations.md): subida local, migrations, validacoes e troubleshooting.
- [Variaveis de Ambiente](./environment-variables.md): baseline por servico e overrides operacionais.
- [Ownership do `.env.staging`](./staging-env-ownership.md): ownership nominal, handoff e bloqueios do arquivo privado da janela.
- [Checklist de Provisionamento por Owner](./staging-serious-window-owner-provisioning-checklist.md): provisioning por dominio, handoff e validacoes minimas antes do gate agregado.
- [Matriz de Execucao por Owner para Janela Seria](./staging-serious-window-war-room-matrix.md): visao de war room com trilhas, dependencias, comandos, evidencias e escalacoes.
- [Template de War Room da Janela Seria](./governance-weekly/_template-staging-serious-window-war-room.md): modelo versionavel para coordenar `go/no-go`, bloqueadores e evidencias no dia da execucao.
- [Folha de Preenchimento Manual da Janela `stg-2026-07-06-a`](./governance-weekly/2026-07-06-staging-serious-window-manual-fill-sheet.md): lista unica de placeholders, owners e validacoes para tirar a janela de `no-go`.
- [Primeiro Disparo Real da Janela Seria](./first-serious-window-first-dispatch-runbook.md): rito operacional do primeiro `Run workflow`, war room, tracking e sign-off.
- [CI/CD e Release](./ci-cd-and-release.md): quality gates, workflows e trilhos de validacao.
- [Runbooks Operacionais](./runbooks.md): troubleshooting por sintoma, severidade e resposta inicial de incidentes.
- [Checklist da Primeira Janela Seria](./first-serious-window-evidence-checklist.md): evidencia minima por iniciativa e pacote de sign-off.
- [Gates de Release para Staging Serio](./project-release-gates.md): criterio formal e executivo de `go/no-go` da janela.

### Compliance, Seguranca e Auditoria

- [Compliance e Controles de Seguranca](./compliance-and-security-controls.md): controles ativos, enforcement e gaps residuais.
- [Matriz de Evidencias e Auditoria](./evidence-and-audit-matrix.md): mapeamento entre fluxos, eventos, hashes e artefatos.
- [Validacao e Auditoria](./validation-and-audit.md): smoke, Playwright, preflights e testes de regressao.
- [Readiness Regulatorio](./regulatory-readiness.md): leitura honesta de prontidao regulatoria.
- [RBAC e Permissoes](./rbac-and-permissions.md): matriz funcional de acesso.

### Planejamento e Governanca

- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md): leitura executiva da baseline `91% / 78% / 87%` e dos gaps residuais.
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md): KPI canonico com pesos, formula e percentual total consolidado.
- [Board de Prioridades do Projeto](./project-priority-board.md): prioridades estrategicas atuais.
- [Plano de Execucao para 90%](./project-execution-plan-to-90.md): plano historico consolidado, agora usado para sustentar 90%+ e empurrar readiness regulatoria.
- [Registro de Riscos do Projeto](./project-risk-register.md): riscos tecnicos, operacionais e regulatorios.
- [Runbook de Governanca Semanal](./project-weekly-governance-runbook.md): rito de acompanhamento semanal.
- [Registros Semanais de Governanca](./governance-weekly/README.md): snapshots historicos, war room, tracking, sign-off e evidencias fechadas por ciclo.

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
5. `staging-serious-window-owner-provisioning-checklist.md`
6. `staging-serious-window-war-room-matrix.md`
7. `governance-weekly/_template-staging-serious-window-war-room.md`
8. `project-release-gates.md`

### Se o foco for Diagnostico e Validacao

1. `validation-and-audit.md`
2. `evidence-and-audit-matrix.md`
3. `project-risk-register.md`

## Estado Atual da Documentacao Canonica

A documentacao principal agora reflete explicitamente:

- `evidence_trail` append-only com encadeamento `SHA-256`
- `preventive_blocks`, `counterparties`, `sanctions_hits_cache` e `ros_records`
- `compliance-worker` com override operacional de `source_url`
- `check_compliance_provider_runtime.py` como gate de runtime para `AML/KYT live`
- `run_eu_sanctions_window.py` e alvos `make run-eu-sanctions-window*` para a janela UE
- `run_regulatory_readiness_bundle.py` e `make run-regulatory-readiness-bundle` para anexar runtime AML/KYT + janela UE em um bundle unico
- `run_staging_window.py` e `make run-serious-window-local*` como rito consolidado da janela seria
- fluxo `ROS/COAF` com aprovacao/rejeicao/submissao manual
- pacote operacional da janela seria com `war room`, `tracking ao vivo`, `manual fill sheet` e `sign-off`
- diferenca entre endpoints live, capacidades degradadas e gaps ainda abertos

## Regra de Manutencao

- atualizar primeiro estes documentos canonicos antes de criar novos artefatos paralelos
- quando houver divergencia entre contrato e runtime, registrar explicitamente a nuance em vez de suavizar o problema
- sempre sincronizar docs com migrations, scripts operacionais e endpoints reais no mesmo ciclo de mudanca
