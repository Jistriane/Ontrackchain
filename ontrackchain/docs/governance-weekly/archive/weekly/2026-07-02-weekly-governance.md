# Governança Semanal — 2026-07-02

> Registro historico arquivado. Este arquivo preserva o snapshot semanal e o contexto operacional da epoca, mas a leitura viva atual deve partir dos scorecards, boards e ciclos mais recentes.

## Leitura do Ciclo

- Baseline técnica: `91%`
- Readiness regulatório: `78%`
- KPI total consolidado: `87%`
- Foco da semana: encerrar Sprint 4, abrir Sprint 5 com expansao de cockpits operacionais e preparar condicoes para homologacao real de P0-02 e P0-03

## Contexto Operacional do Ciclo

- Sprint 4 encerrada como `concluida` após revisao do board pos-90%
- Sprint 5 aberta com foco em `WorkItemTimelinePanel` para cockpits parciais restantes
- `blocks` recebeu timeline/comments completos como primeiro entregavel da Sprint 5
- war room `stg-2026-07-06-a` permanece `no-go` ate preencher handoff, canais, bridges e secrets reais

## KPI da Semana

- construção técnica: `91%`
- prontidão regulatória: `78%`
- KPI total consolidado: `87%`
- houve recalibração material?: `nao`
- fonte canonica: [Scorecard Oficial do Projeto](../../../project-kpi-scorecard.md)

## Itens Atualizados

- ID: `P1-11`
  - status anterior: `in_progress`
  - status atual: `done`
  - owner nominal: `Arquitetura/Governanca`
  - artefato revisado: `project-priority-board.md` revisado com backlog pos-90%
  - próxima evidência esperada: Sprint 5 aberta com primeiro entregavel executado

- ID: `P1-S5-01`
  - status anterior: `todo`
  - status atual: `done`
  - owner nominal: `Frontend/Arquitetura`
  - artefato revisado: `apps/frontend/app/blocks/page.tsx` com `WorkItemTimelinePanel` integrado + i18n pt-BR/en/es
  - próxima evidência esperada: validacao em runtime local com `docker compose up`

- ID: `P0-01`
  - status anterior: `blocked`
  - status atual: `blocked`
  - owner nominal: `Tech Lead Auth`
  - artefato revisado: nenhum novo
  - próxima evidência esperada: homologacao externa com provider real

- ID: `P0-02`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Owner de Integracao AML`
  - artefato revisado: gate `make check-compliance-provider-runtime` documentado
  - próxima evidência esperada: execucao verde com credenciais reais e bundle JSON em `artifacts/staging/checks/`

- ID: `P0-03`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Owner de Compliance/Sancoes`
  - artefato revisado: runner `make run-eu-sanctions-window-local` documentado
  - próxima evidência esperada: `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada + JSONs da janela UE

## Itens Blocked

- ID: `P0-01`
  - motivo: homologacao formal de identidade forte depende de evidencia externa e aceite institucional
  - dependência externa: provider de identidade OIDC com trilho serio e MFA externo
  - owner da escalação: `Tech Lead Auth`

- ID: `RUN-STG-01`
  - motivo: war room `stg-2026-07-06-a` permanece `no-go`; falta handoff, canais, bridges e secrets reais
  - dependência externa: owners online + `.env.staging.private` preenchido com valores reais
  - owner da escalação: `Release Manager Tecnico`

## Decisões

- Sprint 4 encerrada como `concluida` — baseline `91/78/87` institucionalizada
- Sprint 5 aberta com sequencia: `blocks` -> `ros-coaf` (revisao) -> `counterparties` -> `evidence` -> `reports` -> `sanctions`
- `blocks/page.tsx` recebeu `WorkItemTimelinePanel` completo como primeiro entregavel da Sprint 5
- manter baseline `91% / 78% / 87%` ate nova evidencia material de P0-02 ou P0-03
- nao executar janela seria antes de sair do estado `no-go`

## Ações da Próxima Semana

- [x] Validar `blocks` timeline em runtime local: `docker compose up` + abrir `/blocks`
- [x] Revisar `ros-coaf` para assignment formal por `owner_user_id` (P1-S5-02)
- [x] Rollout de `owner_user_id` concluido em todos os 7 cockpits regulatorios (`blocks`, `sanctions`, `alerts`, `ros-coaf`, `counterparties`, `evidence`, `reports`)
- [x] Util `app/lib/ownership.ts` criado e adotado globalmente para evitar drift
- [x] Smoke backend de ownership (`make smoke-work-items-ownership-backend`) validado com create 201 + patch 200 + list 200
- [x] Migration `0013_regulatory_work_items` aplicada e target `make apply-regulatory-work-items-migration` padronizado
- [x] CI integrado: smoke de ownership no job `smoke` do e2e-tests e compile gate no quality-gates
- [ ] DD/SoF manual review estruturado em `counterparties` (Sprint 6 P1)
- [ ] Preencher `COMPLIANCE_AML_KYT_API_KEY` quando credencial real estiver disponivel e rodar P0-02
- [ ] Preencher `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` quando URL real estiver disponivel e rodar P0-03
- [ ] Preencher handoff, canais e bridges no war room `stg-2026-07-06-a` para sair do `no-go`
- [ ] Atualizar scorecard quando P0-02 ou P0-03 fechar com artefato real

## Observações

- a maior entrega tecnica pendente e a expansao de timeline/comments para todos os cockpits parciais — codigo base ja existe no `WorkItemTimelinePanel` e nas libs `work-item-timeline-*`
- o gap de maturidade regulatoria esta concentrado em credenciais externas reais (P0-02, P0-03) e homologacao institucional (P0-01) — nao em ausencia de codigo
- referencia canonica do backlog: [Board de Prioridades do Projeto](../../../project-priority-board.md)
