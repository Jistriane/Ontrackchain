# Runbook de Governança Semanal

## Objetivo

Definir o rito semanal oficial para acompanhar a evolução do projeto com base em:

- [Board de Prioridades do Projeto](project-priority-board.md)
- [Matriz Operacional de Execução](project-operational-execution-board.md)
- [Registro de Riscos do Projeto](project-risk-register.md)
- [Scorecard Oficial do Projeto](project-kpi-scorecard.md)

Este runbook existe para evitar:

- drift entre prioridade estrategica e execucao real
- atualização de status por expectativa
- promoção de maturidade sem evidências
- perda de ownership entre ciclos

Registros gerados por este rito devem ser armazenados em:

- [Registros Semanais de Governança](governance-weekly/README.md)
  - usar o template: [Template de Registro Semanal](governance-weekly/templates/_template-weekly-governance.md)
  - quando houver recalibracao material de nota, usar tambem: [Template de Atualizacao de KPI](governance-weekly/templates/_template-kpi-scorecard-update.md)
  - quando houver ciclo orientado por `D1-D7`, usar tambem: [Template de Execucao por Evidencia](governance-weekly/templates/_template-maturity-evidence-execution-cycle.md)

## Quando Executar

- frequência recomendada: `1x por semana`
- janela recomendada: início do ciclo semanal ou primeiro dia útil após mudança relevante
- duração alvo: `45 a 60 minutos`

## Participantes Mínimos

| Papel | Obrigatorio | Responsabilidade |
| --- | --- | --- |
| Arquiteto/Responsável Técnico | sim | validar leitura macro, trade-offs e prioridades |
| Owner nominal dos itens `in_progress` ou `blocked` | sim | apresentar evidencias, bloqueios e proximo movimento |
| Plataforma/DevOps | sim quando houver item de release, staging ou CI/CD | atualizar readiness operacional e gates |
| Security/Compliance | sim quando houver item regulatório, retention ou AML/KYT | validar sign-off, risco e pendências externas |
| SRE/Operação | sim quando houver item de incidente, SLA, RPC ou observabilidade | atualizar bloqueios operacionais e readiness de resposta |

## Entradas Obrigatórias

Antes da reunião, o facilitador deve reunir:

1. estado mais recente da [Matriz Operacional de Execução para 95%](project-operational-execution-board.md)
2. leitura macro atual do [Board de Prioridades do Projeto](project-priority-board.md)
3. riscos ativos do [Registro de Riscos do Projeto](project-risk-register.md)
4. leitura atual do [Scorecard Oficial do Projeto](project-kpi-scorecard.md)
5. evidências da semana:
   - dossiers
   - bundles de homologação
   - preflights
   - testes ou execuções operacionais
   - resultado de `make check-compliance-provider-runtime` quando houver `AML/KYT live`
   - `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` quando houver `P0-03`
   - artifact `serious-staging-window-<janela>` quando houver janela séria via CI controlado
   - `go/no-go decision packet` da janela, quando houver payload consolidado pós-processado
   - sign-offs formais recebidos
   - registro `D1-D7` quando houver execucao guiada pelo kit de evidencia
   - resumo RCA cross-domain quando houver incidente material na semana
6. lista de itens `blocked`, itens com prazo alvo vencido e itens sem artefato atualizado
7. quando houver janela seria ativa ou planejada:
   - [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md)
   - [Template de War Room da Janela Seria](governance-weekly/templates/_template-staging-serious-window-war-room.md)
   - [Template de Tracking ao Vivo da Janela Seria](governance-weekly/templates/_template-staging-serious-window-live-tracking.md)

## Preparação Prévia

Checklist do facilitador:

- confirmar participantes obrigatórios
- consolidar links dos artefatos da semana
- marcar previamente itens sem evidência como candidatos a `blocked`
- identificar se houve mudança de risco ou dependência externa
- confirmar qual `GitHub Environment` foi usado nas janelas sérias da semana, quando aplicável
- revisar se a baseline estratégica continua coerente com a execução
- confirmar se a matriz de war room da janela seria precisa de escalacao adicional por owner
- confirmar se houve incidente cross-domain aberto na semana, se a RCA minima foi registrada e se o resumo entrou em export/comms/snapshot quando aplicavel

## Agenda Recomendada

### 1. Abertura e Leitura Macro

Tempo alvo:

- `5 minutos`

Objetivo:

- relembrar a meta atual do ciclo
- confirmar a leitura oficial de maturidade e prontidão

Saída:

- consenso rapido sobre foco da semana

### 2. Revisão da Matriz Operacional

Tempo alvo:

- `20 a 25 minutos`

Para cada item `in_progress`, `ready` ou `blocked`, revisar:

- owner nominal
- prazo alvo
- risco associado
- artefato esperado
- evidencia mais recente
- proximo passo
- quando houver incidente cross-domain relevante: confirmar `work_item_id`, RCA minima, comentario automatico de timeline e presenca ou ausencia do resumo executivo

Regras:

- sem evidência nova, o status não sobe
- bloqueio externo deve ser marcado explicitamente como `blocked`
- item `ready` sem janela definida nao deve permanecer indefinidamente nesse estado

Saída:

- matriz operacional atualizada

### 3. Revisão de Riscos

Tempo alvo:

- `10 minutos`

Objetivo:

- revisar riscos reclassificados
- confirmar se algum item operacional mudou a severidade de risco
- identificar riscos novos ou expirados

Saída:

- [Registro de Riscos do Projeto](project-risk-register.md) revisado quando houver mudança material

### 4. Decisões de Prioridade

Tempo alvo:

- `10 minutos`

Objetivo:

- decidir se o board macro precisa de mudança
- confirmar se algum ID derivado precisa entrar ou sair da matriz operacional
- aprovar escalações para credenciais, sign-offs ou providers externos

Saída:

- [Board de Prioridades do Projeto](project-priority-board.md) atualizado apenas se houver mudança estratégica real

### 5. Fechamento

Tempo alvo:

- `5 minutos`

Objetivo:

- confirmar owners da semana
- confirmar próxima evidência esperada por item crítico
- registrar bloqueios que exigem ação externa

Saída:

- resumo do ciclo semanal

## Regras Operacionais

1. atualizar primeiro a matriz operacional
2. atualizar o board estratégico apenas se a leitura macro mudou
3. não promover item para `done` sem artefato, evidência operacional ou sign-off formal
4. tratar como `blocked` qualquer item dependente de credencial, provider, aceite formal ou owner externo sem resposta
5. registrar o próximo passo sempre como ação verificável

## Saídas Obrigatórias

Ao final de cada reunião, devem existir:

- matriz operacional atualizada
- lista de itens `blocked`
- lista de evidências recebidas na semana
- lista de owners nominais da próxima semana
- decisões estratégicas, se houver
- escalações externas necessárias
- explicitação dos artefatos `AML/KYT` e UE revisados quando estiverem no escopo
- scorecard recalibrado quando houver mudança material de nota
- matriz de war room revisada quando houver janela seria no ciclo
- war room versionado quando houver decisao `go/no-go` formal da janela
- tracking ao vivo versionado quando houver acompanhamento minuto a minuto da janela
- `decision packet` versionado quando a janela tiver payload consolidado e reconciliacao executiva
- status da RCA cross-domain explicitado quando houver incidente material, deixando claro se foi apenas endurecimento operacional ou se gerou artefato executivo revisado

Quando houver recalibracao relevante do scorecard, anexar ou embutir um bloco baseado em:

- [Template de Atualizacao de KPI](governance-weekly/templates/_template-kpi-scorecard-update.md)

## Template de Registro Semanal

```md
# Governança Semanal — YYYY-MM-DD

## Leitura do Ciclo
- Baseline técnica:
- Readiness regulatório:
- KPI total consolidado:
- Foco da semana:

## Evidências Revisadas
- artifact `serious-staging-window-<janela>` quando houver janela séria
- bundle AML/KYT + gate runtime quando `P0-02` estiver no escopo
- `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` quando `P0-03` estiver no escopo
- resumo RCA cross-domain quando houver incidente material

## Itens Atualizados
- ID:
  - status anterior:
  - status atual:
  - owner nominal:
  - artefato revisado:
  - próxima evidência esperada:

## Itens Blocked
- ID:
  - motivo:
  - dependência externa:
  - owner da escalação:

## Decisões
- 

## RCA Cross-Domain
- houve incidente material? sim/nao
- `work_item_id`:
- RCA minima registrada? sim/nao
- resumo entrou em export/comms/snapshot? sim/nao
- leitura executiva: endurecimento operacional / artefato revisado / nao aplicavel

## Ações da Próxima Semana
- 
```

Registro inicial publicado:

- usar [Registros Semanais de Governança](governance-weekly/README.md) como ponto de entrada para localizar o ciclo ativo, o ciclo fechado mais recente e o histórico arquivado
- quando precisar de snapshots antigos, navegar pelo índice [Histórico Semanal](governance-weekly/archive/weekly/README.md), nunca por links nominais hardcoded neste runbook

## Checklist de Fechamento

- [ ] matriz operacional atualizada
- [ ] riscos reclassificados quando necessário
- [ ] board estratégico revisado apenas se houve mudança macro
- [ ] itens `blocked` explicitamente marcados
- [ ] owners nominais confirmados
- [ ] artefatos da semana linkados

## Decisão Recomendada

- usar este runbook como rito oficial de revisão semanal
- executar a cerimônia mesmo quando não houver grande entrega, para evitar drift e esconder bloqueios
- considerar incompleta qualquer semana sem atualização da matriz operacional ou sem registro de evidências

## Suposições

- o time consegue manter um facilitador semanal do rito
- os owners nominais terão acesso aos artefatos mínimos do seu item
- a reunião semanal será curta e baseada em evidência, não em status verbal genérico
