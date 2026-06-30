# Runbook de Governança Semanal

## Objetivo

Definir o rito semanal oficial para acompanhar a evolução do projeto com base em:

- [Board de Prioridades do Projeto](project-priority-board.md)
- [Matriz Operacional de Execução para 95%](project-operational-execution-board.md)
- [Plano Operacional Trimestral para 95%](project-operational-plan-to-95.md)
- [Registro de Riscos do Projeto](project-risk-register.md)

Este runbook existe para evitar:

- drift entre prioridade estrategica e execucao real
- atualização de status por expectativa
- promoção de maturidade sem evidências
- perda de ownership entre ciclos

Registros gerados por este rito devem ser armazenados em:

- [Registros Semanais de Governança](governance-weekly/README.md)
  - usar o template: [Template de Registro Semanal](governance-weekly/_template-weekly-governance.md)

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
4. evidências da semana:
   - dossiers
   - bundles de homologação
   - preflights
   - testes ou execuções operacionais
   - artifact `serious-staging-window-<janela>` quando houver janela séria via CI controlado
   - sign-offs formais recebidos
5. lista de itens `blocked`, itens com prazo alvo vencido e itens sem artefato atualizado

## Preparação Prévia

Checklist do facilitador:

- confirmar participantes obrigatórios
- consolidar links dos artefatos da semana
- marcar previamente itens sem evidência como candidatos a `blocked`
- identificar se houve mudança de risco ou dependência externa
- confirmar qual `GitHub Environment` foi usado nas janelas sérias da semana, quando aplicável
- revisar se a baseline estratégica continua coerente com a execução

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

## Template de Registro Semanal

```md
# Governança Semanal — YYYY-MM-DD

## Leitura do Ciclo
- Baseline técnica:
- Readiness regulatório:
- Foco da semana:

## Evidências Revisadas
- 

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

## Ações da Próxima Semana
- 
```

Registro inicial publicado:

- [Governança Semanal 2026-06-29](governance-weekly/2026-06-29-weekly-governance.md)
- rascunho da janela do dia: [Governança Semanal 2026-06-30](governance-weekly/2026-06-30-weekly-governance.md)
- rascunho do próximo ciclo: [Governança Semanal 2026-07-06](governance-weekly/2026-07-06-weekly-governance.md)

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
