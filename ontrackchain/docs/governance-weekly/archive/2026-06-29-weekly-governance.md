# Governança Semanal — 2026-06-29

## Leitura do Ciclo

- Baseline técnica: `89%`
- Readiness regulatório: `76%`
- Foco da semana: fechar o rito de governança documental e preparar a primeira janela séria com evidências reais

## Evidências Revisadas

- publicação da [Matriz Operacional de Execução para 95%](../project-operational-execution-board.md)
- publicação do [Runbook de Governança Semanal](../project-weekly-governance-runbook.md)
- baseline de maturidade recalibrada em [project-maturity-assessment.md](../project-maturity-assessment.md)
- readiness regulatório recalibrado em [regulatory-readiness.md](../regulatory-readiness.md)
- registro de riscos alinhado em [project-risk-register.md](../project-risk-register.md)
- trilha séria de `staging` documentada e runner consolidado em `run_staging_window.py`

## Itens Atualizados

- ID: `P0-01`
  - status anterior: `in_progress`
  - status atual: `in_progress`
  - owner nominal: `Tech Lead Auth`
  - artefato revisado: preflight sério de `OIDC`, gates de CI e documentação de auth
  - próxima evidência esperada: execução `OIDC` séria sem `localhost` e com segredos não-dev

- ID: `P0-05`
  - status anterior: `in_progress`
  - status atual: `in_progress`
  - owner nominal: `Owner de Integracao AML`
  - artefato revisado: preflight externo, homologação externa e baseline sério de `staging`
  - próxima evidência esperada: bundle real de homologação AML/KYT em modo `live`

- ID: `P0-06`
  - status anterior: `in_progress`
  - status atual: `in_progress`
  - owner nominal: `Owner de Integracao RPC`
  - artefato revisado: readiness de RPC, fallback documentado e fluxo sério de homologação
  - próxima evidência esperada: bundle real de homologação RPC com primário e fallback

- ID: `RUN-STG-01`
  - status anterior: `ready`
  - status atual: `ready`
  - owner nominal: `Release Manager Tecnico`
  - artefato revisado: runner `run_staging_window.py`, dossier e packet de janela
  - próxima evidência esperada: primeira execução real com dossier `ok`

- ID: `P1-01`
  - status anterior: `in_progress`
  - status atual: `in_progress`
  - owner nominal: `Security Officer Operacional`
  - artefato revisado: politica de retention/recovery publicada
  - proxima evidencia esperada: sign-off formal de Security/Compliance

- ID: `P2-02`
  - status anterior: `in_progress`
  - status atual: `in_progress`
  - owner nominal: `Incident Manager`
  - artefato revisado: owners, SLA base e runbooks publicados
  - próxima evidência esperada: aceite operacional formal e uso em rito real

## Itens Blocked

- ID: `P0-01`
  - motivo: falta homologação fora do contexto local
  - dependência externa: credenciais e configuração séria do IdP
  - owner da escalação: `Tech Lead Auth`

- ID: `P0-02`
  - motivo: modelo final de MFA sério ainda não homologado
  - dependência externa: decisão de implementação/federação do MFA
  - owner da escalação: `Security Champion de Auth`

- ID: `P0-05`
  - motivo: provider real AML/KYT ainda não homologado
  - dependência externa: contrato, credenciais e janela com provider real
  - owner da escalação: `Owner de Integracao AML`

- ID: `P0-06`
  - motivo: RPC primário/fallback ainda não homologado em ambiente sério
  - dependência externa: endpoints aceitos e janela real de teste
  - owner da escalação: `Owner de Integracao RPC`

- ID: `P1-01`
  - motivo: sign-off formal ainda pendente
  - dependência externa: aceite de Security/Compliance
  - owner da escalação: `Security Officer Operacional`

- ID: `P2-02`
  - motivo: ownership operacional ainda não foi aceito formalmente
  - dependência externa: aceite operacional de owners/SLA/runbooks
  - owner da escalação: `Incident Manager`

## Decisões

- manter `89%` como baseline técnica oficial
- manter `76%` como readiness regulatório oficial
- tratar a governança documental como pronta, mas não contabilizar ganho adicional de maturidade sem primeira execução séria real
- usar a matriz operacional como fonte primaria da revisao semanal
- refletir no board apenas mudancas de leitura estrategica

## Acoes da Proxima Semana

- executar ou preparar a primeira janela seria real de `OIDC`, AML/KYT e RPC
- persistir outputs reais dos checkers e preflights para alimentar o dossier
- obter retorno de Security/Compliance sobre `P1-01`
- obter retorno operacional sobre `P2-02`
- reavaliar se `RUN-STG-01` pode sair de `ready` para `in_progress`

## Observacoes

- este primeiro registro e predominantemente de consolidacao documental e de readiness
- ainda nao existe evidência real de janela seria executada com `dossier ok`
- nenhum item foi promovido artificialmente para `done`
