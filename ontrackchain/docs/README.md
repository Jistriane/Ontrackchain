# Documentação do Projeto

## Objetivo

Organizar os documentos canônicos do Ontrackchain em grupos claros, reduzindo sobreposição entre artefatos de arquitetura, operação, compliance e planejamento.

## Como Navegar

### Visão Geral

- [README raiz](../README.md): visão executiva do projeto, quick start e mapa principal da documentação.
- [Arquitetura](./architecture.md): desenho macro da plataforma e responsabilidades por componente.
- [Contratos de API](./api-contracts.md): contratos funcionais principais do backend e integrações do frontend.

### Operação e Release

- [CI/CD e Release](./ci-cd-and-release.md): pipelines, quality gates e critérios de promoção.
- [Deploy e Staging](./deploy-and-staging.md): fluxo operacional de subida, preflight, homologação e dossier.
- [GitHub Environment para Staging Sério](./github-environment-staging-serious.md): configuração do environment, approvals e secret `STAGING_WINDOW_PRIVATE_ENV`.
- [Variáveis de Ambiente](./environment-variables.md): baseline de configuração por ambiente.
- [Ownership do `.env.staging`](./staging-env-ownership.md): matriz de owners, handoff e rito de janela.
- [Checklist Pré-Produção](./pre-production-checklist.md): checklist objetivo de go/no-go.
- [Gates de Release para Staging Sério](./project-release-gates.md): regras formais de promoção.
- [Runbooks Operacionais](./runbooks.md): resposta a incidentes e procedimentos críticos.
- [Owners e SLAs Operacionais](./operational-ownership-and-slas.md): ownership por domínio e severidade.
- [Retention e Recovery](./retention-and-recovery-policy.md): baseline de retenção, recovery e sign-off.
- [Operação Local](./operations.md): uso do ambiente local via Docker.

### Segurança, Compliance e Auditoria

- [Compliance e Controles de Segurança](./compliance-and-security-controls.md): controles ativos e gaps residuais.
- [RBAC e Permissões](./rbac-and-permissions.md): matriz funcional de acesso.
- [Readiness Regulatório](./regulatory-readiness.md): critérios de prontidão regulatória.
- [Validação e Auditoria](./validation-and-audit.md): smoke, E2E, trilhas de auditoria e critérios técnicos.
- [Matriz de Evidências e Auditoria](./evidence-and-audit-matrix.md): mapeamento de eventos, hashes e evidências.

### Produto e Planejamento

- [Board de Prioridades do Projeto](./project-priority-board.md): backlog executivo canônico e status por iniciativa.
- [Plano de Execução para 90%](./project-execution-plan-to-90.md): plano tático detalhado para fechar os gaps principais.
- [Plano Operacional Trimestral para 95%](./project-operational-plan-to-95.md): trilha executiva por trimestre para elevar maturidade técnica e regulatória.
- [Matriz Operacional de Execução para 95%](./project-operational-execution-board.md): board de execução com status, owner nominal, prazo, risco, artefato esperado e próxima evidência.
- [Runbook de Governança Semanal](./project-weekly-governance-runbook.md): rito oficial de revisão semanal com participantes, agenda, entradas e saídas obrigatórias.
- [Registros Semanais de Governança](./governance-weekly/README.md): histórico dos ciclos semanais executados a partir do runbook oficial.
- [Checklist de Evidência Mínima da Primeira Janela Séria](./first-serious-window-evidence-checklist.md): critério canônico para validar P0-01, P0-05, P0-06 e `RUN-STG-01`.
- [Runbook do Primeiro Disparo Real](./first-serious-window-first-dispatch-runbook.md): roteiro operacional canônico da primeira janela, com `prepare-serious-window-dispatch`, inputs recomendados, artifact esperado e fechamento pós-run.
- [Template de Sign-Off da Janela Seria](./staging-serious-window-signoff-template.md): modelo padronizado para aprovar ou bloquear a janela com referência ao artifact oficial.
- [Workflow manual de janela séria](../.github/workflows/staging-serious-window.yml): rito controlado de CI/CD para executar `prepare_staging_window.py --run` com `GitHub Environment` aprovado.
- `python scripts/prepare_staging_window.py`: prepara a janela séria gerando `.env.staging.private`, `window packet` e diretórios-base no modo `baseline` ou `homologated`.
- `python scripts/prepare_staging_window.py --validate|--preflight`: reaproveita `.env.staging.private` preenchido para persistir gates locais e, opcionalmente, os preflights reais antes da janela completa.
- `python scripts/prepare_staging_window.py --run`: encadeia `prepare -> validate -> preflight -> run_staging_window` em um gate unico, falhando cedo e persistindo o payload consolidado da execucao.
- `python scripts/render_staging_private_env_templates.py`: gera templates redigidos de `.env.staging.private` para janelas `baseline` e `homologada`.
- [Avaliação de Maturidade do Projeto](./project-maturity-assessment.md): leitura executiva e técnica da maturidade atual.
- [Registro de Riscos do Projeto](./project-risk-register.md): riscos técnicos, operacionais e regulatórios.
- [Planos, Limites e Catálogos](./plans-limits-and-catalogs.md): política de planos, limites e capacidades.
- [Template Keycloak OIDC](./keycloak-oidc-template.md): guia prático para realm, client e variáveis de ambiente.

### Decisões Arquiteturais

- [ADRs](./adrs/README.md): índice das decisões arquiteturais formais.

## Consolidações Recentes

- `roadmap-phase2.md` foi consolidado em:
  - [project-priority-board.md](./project-priority-board.md)
  - [project-execution-plan-to-90.md](./project-execution-plan-to-90.md)
- `project-work-packages.md` foi consolidado em:
  - [project-priority-board.md](./project-priority-board.md)
  - [project-execution-plan-to-90.md](./project-execution-plan-to-90.md)
- `project-staging-readiness-scorecard.md` foi consolidado em:
  - [project-release-gates.md](./project-release-gates.md)
  - [pre-production-checklist.md](./pre-production-checklist.md)
  - [project-maturity-assessment.md](./project-maturity-assessment.md)
- `first-serious-window-command-pack.md`, `first-serious-window-execution-walkthrough.md`, `first-serious-window-operational-plan.md` e `staging-window-execution-template.md` foram consolidados em:
  - [first-serious-window-first-dispatch-runbook.md](./first-serious-window-first-dispatch-runbook.md)
  - [first-serious-window-evidence-checklist.md](./first-serious-window-evidence-checklist.md)
  - [staging-serious-window-signoff-template.md](./staging-serious-window-signoff-template.md)

## Regra de Manutenção

- atualizar primeiro os documentos canônicos acima antes de criar novos artefatos
- evitar abrir novos documentos de planejamento se o conteúdo puder viver no `board`, no `execution plan` ou nos `release gates`
- remover referências quebradas ou redundantes no mesmo PR que consolidar conteúdo
