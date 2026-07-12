# Atualização de KPI — 2026-07-01

> Snapshot historico arquivado. Este documento preserva a baseline formal daquele momento (`91/78/87`), mas a fonte viva atual do projeto e `docs/project-kpi-scorecard.md`.

## Objetivo

Registrar a primeira baseline formal do KPI consolidado do Ontrackchain apos a convergencia entre:

- scorecard oficial
- board de prioridades
- matriz operacional
- risk register
- documentacao canonica viva

## Snapshot Atual

- Construção técnica: `91%`
- Prontidão regulatória: `78%`
- KPI total consolidado: `87%`

## Snapshot Anterior

- Construção técnica: `89%`
- Prontidão regulatória: `76%`
- KPI total consolidado: `85%`

## Delta da Semana

- Construção técnica: `+2pp`
- Prontidão regulatória: `+2pp`
- KPI total consolidado: `+2pp`

## Domínios/Iniciativas Recalibrados

- Domínio ou bloco: `P0-04` alinhamento de `sanctions_check`
  - nota anterior: `82%`
  - nota atual: `100%`
  - motivo da mudança: catálogo, endpoint direto, testes e documentação convergiram para o estado `live`
  - evidência objetiva: testes de contrato e documentação operacional atualizada

- Domínio ou bloco: `P0-05` inventário de eventos da `evidence_trail`
  - nota anterior: `75%`
  - nota atual: `100%`
  - motivo da mudança: source of truth único + teste cruzado removeram o drift atual
  - evidência objetiva: `tests/test_evidence_event_catalog_sync.py` e alinhamento entre runtime, integração e migration

- Domínio ou bloco: `Compliance Core`
  - nota anterior: `88%`
  - nota atual: `90%`
  - motivo da mudança: endurecimento do core regulatório e dos guardrails de homologação externa
  - evidência objetiva: `check_compliance_provider_runtime.py`, `run_eu_sanctions_window.py` e documentação operacional convergente

- Domínio ou bloco: `Testes, CI/CD e guardrails`
  - nota anterior: `92%`
  - nota atual: `94%`
  - motivo da mudança: institucionalização dos novos checkers, runners e critérios de evidência
  - evidência objetiva: Make targets, runners dedicados e cobertura focal dos fluxos novos

- Domínio ou bloco: `Prontidão regulatória/operacional`
  - nota anterior: `76%`
  - nota atual: `78%`
  - motivo da mudança: documentação viva, runbooks e artefatos mínimos ficaram coerentes com os gaps reais
  - evidência objetiva: `project-release-gates.md`, `history/first-serious-window-evidence-checklist.md`, `runbooks.md` e `project-weekly-governance-runbook.md`

## Evidências Utilizadas

- artifact: documentação canônica atualizada e scorecard oficial publicado
- bundle: bundles e artifacts esperados formalizados para `AML/KYT live` e janela UE
- teste/check:
  - `tests/test_evidence_event_catalog_sync.py`
  - `tests/test_check_compliance_provider_runtime.py`
  - `tests/test_check_sanctions_sync_status.py`
  - `tests/test_run_eu_sanctions_window.py`
- sign-off: critérios e templates de sign-off institucionalizados, ainda pendentes de execução real recorrente
- runbook/janela:
  - `runbooks.md`
  - `history/first-serious-window-first-dispatch-runbook.md`
  - `history/staging-serious-window-signoff-template.md`

## Regras Aplicadas

- [x] nenhuma nota mudou sem evidência nova
- [x] itens `blocked` não receberam ganho artificial
- [x] alteração de peso não foi necessária
- [x] risco residual foi reavaliado quando aplicável

## Leitura Executiva

- resumo da semana: o projeto deixou de depender de leitura informal e passou a ter KPI oficial, scorecard canônico e critérios de atualização semanal
- gargalo principal atual: homologação externa real de `OIDC/MFA`, `AML/KYT live` e `EU_CONSOLIDATED`
- próximo gatilho para subida relevante do KPI: execução real das janelas `P0-01`, `P0-02` e `P0-03` com artefatos aceitos

## Decisão

- decisão: `recalibrar score`

## Próxima Revisão Esperada

- data: `2026-07-06`
- evento esperado: primeira atualização após janela séria com evidência operacional real ou confirmação explícita de bloqueio externo
- owner: `Arquiteto/Responsável Técnico`
