# Governança Semanal — 2026-07-03

> Registro historico arquivado. Este documento preserva a avaliacao semanal daquele ciclo, mas nao substitui a governanca viva, os ciclos correntes e os scorecards atuais.

## Leitura do Ciclo

- Baseline técnica: `91%`
- Readiness regulatório: `78%`
- Foco da semana: validar se a baseline documental segue sustentada pelo código, pelos testes e pelos artefatos operacionais já presentes no repositório

## Contexto da Janela Séria (quando aplicável)

- `window_id`: `stg-2026-07-06-a`
- `mode`: `pre-serious-window`
- `environment_name`: `staging-serious`
- run do GitHub Actions: `n/a`
- status esperado: manter `P0-01`, `P0-02` e `P0-03` sem promoção artificial até existir evidência real de homologação externa
- checklist canônico:
  - [Checklist de Evidência Mínima da Primeira Janela Séria](../../../history/first-serious-window-evidence-checklist.md)
- runbook do primeiro disparo:
  - [Runbook do Primeiro Disparo Real](../../../history/first-serious-window-first-dispatch-runbook.md)
- template de sign-off:
  - [Template de Sign-Off da Janela Seria](../../../history/staging-serious-window-signoff-template.md)

## Evidências Revisadas

- artifact `serious-staging-window-<janela>`: `n/a`
- overall status: `n/a`
- validation status: `ok` para a baseline técnica e documental auditada
- preflight status: `ok` no nível de documentação, scripts e guardrails canônicos já publicados
- run status: `n/a`
- window packet: `n/a`
- dossier: `n/a`
- homologation: `pendente de evidência externa real`
- oidc bundle summary: `pendente de credenciais e homologação real`
- regulatory bundle summary: `pendente de provider AML/KYT live e feed UE real`
- validação executável revisada nesta data: suíte principal Python local com `127 passed`
- parecer executivo consolidado:
  - [Avaliação Consolidada de Status do Projeto](../../../assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)

## KPI da Semana

- construção técnica: `91%`
- prontidão regulatória: `78%`
- KPI total consolidado: `87%`
- houve recalibração material?: `nao`
- template detalhado de KPI:
  - [Atualização de KPI 2026-07-03](../../cycles/2026-07-03/2026-07-03-kpi-scorecard-update.md)

## Itens Atualizados

- ID: `BASELINE-2026-07-03`
  - status anterior: `informalmente sustentada por documentos dispersos`
  - status atual: `consolidada e versionada com parecer executivo unico`
  - owner nominal: `Arquitetura/Governanca`
  - artefato revisado: [Avaliação Consolidada de Status do Projeto](../../../assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
  - próxima evidência esperada: uso do parecer nas decisões de `go/no-go` e revisão semanal

- ID: `DOC-GOV-2026-07-03`
  - status anterior: `boards e indice sem referencia executiva consolidada`
  - status atual: `boards, indice de docs e governança alinhados ao novo parecer`
  - owner nominal: `Arquitetura/Governanca`
  - artefato revisado: `docs/README`, `project-priority-board`, `project-operational-execution-board`, `governance-weekly/README`
  - próxima evidência esperada: uso recorrente no rito semanal e nas escalacoes externas

- ID: `TEST-BASELINE-2026-07-03`
  - status anterior: `baseline sustentada principalmente por documentação`
  - status atual: `baseline reforçada por validação executável local`
  - owner nominal: `Arquitetura/Tecnico`
  - artefato revisado: suíte principal Python com `127 passed`
  - próxima evidência esperada: manter regressão verde nas próximas mudanças de compliance/governança

## Itens Blocked

- ID: `P0-01`
  - motivo: `OIDC + MFA` ainda dependem de homologação real e aceite institucional
  - dependência externa: provider de identidade e credenciais do trilho sério
  - owner da escalação: `Security/Auth`

- ID: `P0-02`
  - motivo: `AML/KYT live` ainda depende de credenciais reais do provider
  - dependência externa: provider AML/KYT
  - owner da escalação: `Compliance/AML`

- ID: `P0-03`
  - motivo: feed UE tokenizado ainda depende de URL real e prova recorrente
  - dependência externa: provider do feed UE
  - owner da escalação: `Compliance/Backend`

## Decisões

- manter oficialmente `91% / 78% / 87%` como baseline executiva do projeto
- registrar formalmente que o estado atual e `go` para validacao seria controlada e `no-go` para producao regulada forte
- tratar a diferenca entre maturidade tecnica alta e prontidao regulatoria incompleta como gap de homologacao externa, nao como gap central de construcao de produto

## Ações da Próxima Semana

- obter retorno dos owners externos de `P0-01`, `P0-02` e `P0-03`
- executar o primeiro gate real que tiver insumo valido, sem promover status por expectativa
- usar o parecer consolidado como base da próxima reunião de governança e de qualquer discussão de `go/no-go`

## Observações

- este registro nao sobe o KPI; ele consolida e valida a baseline vigente
- a ausência de artefato de janela séria e consistente com o estado atual do projeto
- o próximo gatilho legítimo para recalibração relevante continua sendo homologação externa real ou execução séria com evidência anexável
