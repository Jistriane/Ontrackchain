# Governança Semanal — 2026-07-01

## Leitura do Ciclo

- Baseline técnica: `91%`
- Readiness regulatório: `78%`
- Foco da semana: consolidar o scorecard oficial, fechar os drifts documentais e preparar a próxima rodada operacional de `P0-01`, `P0-02` e `P0-03`

## Contexto da Janela Séria (quando aplicável)

- `window_id`: `n/a`
- `mode`: `pre-serious-window`
- `environment_name`: `staging-serious`
- run do GitHub Actions: `n/a`
- status esperado: manter `RUN-STG-01` em `ready` até existir janela real com artifact anexável
- checklist canônico:
  - [Checklist de Evidência Mínima da Primeira Janela Séria](../first-serious-window-evidence-checklist.md)
- runbook do primeiro disparo:
  - [Runbook do Primeiro Disparo Real](../first-serious-window-first-dispatch-runbook.md)
- template de sign-off:
  - [Template de Sign-Off da Janela Seria](../staging-serious-window-signoff-template.md)

## Evidências Revisadas

- artifact `serious-staging-window-<janela>`: `n/a`
- overall status: `n/a`
- validation status: `n/a`
- preflight status: `ok` para os guardrails locais/canônicos já publicados
- run status: `n/a`
- window packet: `n/a`
- dossier: `n/a`
- homologation: `n/a`

## KPI da Semana

- construção técnica: `91%`
- prontidão regulatória: `78%`
- KPI total consolidado: `87%`
- houve recalibração material?: `sim`
- template detalhado de KPI:
  - [Atualização de KPI 2026-07-01](./2026-07-01-kpi-scorecard-update.md)

## Itens Atualizados

- ID: `P0-04`
  - status anterior: `in_progress`
  - status atual: `done`
  - owner nominal: `Backend/Compliance`
  - artefato revisado: alinhamento do catálogo `sanctions_check`, testes e documentação viva
  - próxima evidência esperada: nenhuma corretiva; apenas manutenção regressiva por testes

- ID: `P0-05`
  - status anterior: `in_progress`
  - status atual: `done`
  - owner nominal: `Backend/Compliance`
  - artefato revisado: convergência do catálogo de eventos da `evidence_trail` com source of truth único
  - próxima evidência esperada: manter `tests/test_evidence_event_catalog_sync.py` verde nas próximas mudanças

- ID: `P0-02`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Compliance/AML`
  - artefato revisado: gate `make check-compliance-provider-runtime`
  - próxima evidência esperada: execução real do gate com credenciais válidas do provider

- ID: `P0-03`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Compliance/Backend`
  - artefato revisado: `make run-eu-sanctions-window-local` + JSONs da janela UE
  - próxima evidência esperada: execução real da janela UE com `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` válida

- ID: `RUN-STG-01`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Release Manager Tecnico`
  - artefato revisado: runbooks, template de sign-off e checklist da primeira janela séria
  - próxima evidência esperada: artifact `serious-staging-window-<janela>` com `overall status=ok`

## Itens Blocked

- ID: `P0-01`
  - motivo: homologação formal de `OIDC/MFA` federado ainda depende de evidência externa e aceite institucional
  - dependência externa: provider de identidade e validação do fluxo sério com `X-MFA-Mode=external_provider`
  - owner da escalação: `Auth/IAM`

- ID: `P0-02`
  - motivo: ausência de credenciais reais homologadas para fechamento do trilho `AML/KYT live`
  - dependência externa: provider AML/KYT e owner de compliance
  - owner da escalação: `Compliance/AML`

- ID: `P0-03`
  - motivo: ausência de URL tokenizada real para `EU_CONSOLIDATED`
  - dependência externa: provisionamento do feed UE tokenizado
  - owner da escalação: `Compliance/Backend`

## Decisões

- oficializar `91% / 78% / 87%` como baseline canônica do projeto até nova evidência material
- manter `P0-04` e `P0-05` fora do foco prioritário, tratando-os como fechados e protegidos por teste
- direcionar o próximo ganho de maturidade para execução real de `P0-01`, `P0-02` e `P0-03`

## Ações da Próxima Semana

- executar `make check-compliance-provider-runtime` com credenciais reais quando `P0-02` estiver liberado
- executar `make run-eu-sanctions-window-local WINDOW_ID=stg-$(date +%F)-eu` quando `P0-03` estiver liberado
- preparar a primeira janela séria real com artifact e sign-off anexáveis para mover `RUN-STG-01`

## Observações

- este registro funciona como baseline operacional da governança pós-scorecard
- a ausência de artifact de janela séria nesta data é intencional e honesta; o ciclo ainda está em fase de preparação operacional
- a próxima recalibração relevante do KPI só deve ocorrer com evidência real de homologação externa ou execução de janela séria
