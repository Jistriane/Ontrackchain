# Documentação do Projeto

## Objetivo

Organizar os documentos canônicos do Ontrackchain em grupos claros, reduzindo sobreposição entre artefatos de arquitetura, operação, compliance e planejamento.

## Como Navegar

### Visão Geral

- [README raiz](file:///home/jistriane/Ontracktchain/ontrackchain/README.md): visão executiva do projeto, quick start e mapa principal da documentação.
- [Arquitetura](file:///home/jistriane/Ontracktchain/ontrackchain/docs/architecture.md): desenho macro da plataforma e responsabilidades por componente.
- [Contratos de API](file:///home/jistriane/Ontracktchain/ontrackchain/docs/api-contracts.md): contratos funcionais principais do backend e integrações do frontend.

### Operação e Release

- [CI/CD e Release](file:///home/jistriane/Ontracktchain/ontrackchain/docs/ci-cd-and-release.md): pipelines, quality gates e critérios de promoção.
- [Deploy e Staging](file:///home/jistriane/Ontracktchain/ontrackchain/docs/deploy-and-staging.md): fluxo operacional de subida, preflight, homologação e dossier.
- [Variáveis de Ambiente](file:///home/jistriane/Ontracktchain/ontrackchain/docs/environment-variables.md): baseline de configuração por ambiente.
- [Ownership do `.env.staging`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-env-ownership.md): matriz de owners, handoff e rito de janela.
- [Checklist Pré-Produção](file:///home/jistriane/Ontracktchain/ontrackchain/docs/pre-production-checklist.md): checklist objetivo de go/no-go.
- [Gates de Release para Staging Sério](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-release-gates.md): regras formais de promoção.
- [Runbooks Operacionais](file:///home/jistriane/Ontracktchain/ontrackchain/docs/runbooks.md): resposta a incidentes e procedimentos críticos.
- [Owners e SLAs Operacionais](file:///home/jistriane/Ontracktchain/ontrackchain/docs/operational-ownership-and-slas.md): ownership por domínio e severidade.
- [Retention e Recovery](file:///home/jistriane/Ontracktchain/ontrackchain/docs/retention-and-recovery-policy.md): baseline de retenção, recovery e sign-off.
- [Operação Local](file:///home/jistriane/Ontracktchain/ontrackchain/docs/operations.md): uso do ambiente local via Docker.

### Segurança, Compliance e Auditoria

- [Compliance e Controles de Segurança](file:///home/jistriane/Ontracktchain/ontrackchain/docs/compliance-and-security-controls.md): controles ativos e gaps residuais.
- [RBAC e Permissões](file:///home/jistriane/Ontracktchain/ontrackchain/docs/rbac-and-permissions.md): matriz funcional de acesso.
- [Readiness Regulatório](file:///home/jistriane/Ontracktchain/ontrackchain/docs/regulatory-readiness.md): critérios de prontidão regulatória.
- [Validação e Auditoria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/validation-and-audit.md): smoke, E2E, trilhas de auditoria e critérios técnicos.
- [Matriz de Evidências e Auditoria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/evidence-and-audit-matrix.md): mapeamento de eventos, hashes e evidências.

### Produto e Planejamento

- [Board de Prioridades do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md): backlog executivo canônico e status por iniciativa.
- [Plano de Execução para 90%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-execution-plan-to-90.md): plano tático detalhado para fechar os gaps principais.
- [Plano Operacional Trimestral para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-plan-to-95.md): trilha executiva por trimestre para elevar maturidade técnica e regulatória.
- [Matriz Operacional de Execução para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-execution-board.md): board de execução com status, owner nominal, prazo, risco, artefato esperado e próxima evidência.
- [Runbook de Governança Semanal](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-weekly-governance-runbook.md): rito oficial de revisão semanal com participantes, agenda, entradas e saídas obrigatórias.
- [Registros Semanais de Governança](file:///home/jistriane/Ontracktchain/ontrackchain/docs/governance-weekly/README.md): histórico dos ciclos semanais executados a partir do runbook oficial.
- [Checklist de Evidência Mínima da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md): critério canônico para validar P0-01, P0-05, P0-06 e `RUN-STG-01`.
- [Plano Operacional da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-operational-plan.md): execução por owner, evidências esperadas e rito de encerramento.
- [Pacote de Execução da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-command-pack.md): comandos copy/paste e saídas esperadas do runner.
- [Passo a Passo Executável da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-execution-walkthrough.md): guia de execução com colagem dos paths no registro semanal.
- [Template de Execução de Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-window-execution-template.md): modelo reutilizável para futuras janelas.
- [Avaliação de Maturidade do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-maturity-assessment.md): leitura executiva e técnica da maturidade atual.
- [Registro de Riscos do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-risk-register.md): riscos técnicos, operacionais e regulatórios.
- [Planos, Limites e Catálogos](file:///home/jistriane/Ontracktchain/ontrackchain/docs/plans-limits-and-catalogs.md): política de planos, limites e capacidades.
- [Template Keycloak OIDC](file:///home/jistriane/Ontracktchain/ontrackchain/docs/keycloak-oidc-template.md): guia prático para realm, client e variáveis de ambiente.

### Decisões Arquiteturais

- [ADRs](file:///home/jistriane/Ontracktchain/ontrackchain/docs/adrs/README.md): índice das decisões arquiteturais formais.

## Consolidações Recentes

- `roadmap-phase2.md` foi consolidado em:
  - [project-priority-board.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md)
  - [project-execution-plan-to-90.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-execution-plan-to-90.md)
- `project-work-packages.md` foi consolidado em:
  - [project-priority-board.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md)
  - [project-execution-plan-to-90.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-execution-plan-to-90.md)
- `project-staging-readiness-scorecard.md` foi consolidado em:
  - [project-release-gates.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-release-gates.md)
  - [pre-production-checklist.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/pre-production-checklist.md)
  - [project-maturity-assessment.md](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-maturity-assessment.md)

## Regra de Manutenção

- atualizar primeiro os documentos canônicos acima antes de criar novos artefatos
- evitar abrir novos documentos de planejamento se o conteúdo puder viver no `board`, no `execution plan` ou nos `release gates`
- remover referências quebradas ou redundantes no mesmo PR que consolidar conteúdo
