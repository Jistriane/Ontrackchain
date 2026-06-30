# Plano Operacional Trimestral para 95%

## Objetivo

Transformar a matriz executiva de maturidade em um plano operacional trimestral que leve o Ontrackchain de:

- `89%` de construcao tecnica
- `76%` de prontidao regulatoria

para:

- `95%` de maturidade tecnica
- faixa regulatoria claramente superior, sem declarar prontidao plena de producao

Este documento complementa:

- [Avaliacao de Maturidade do Projeto](project-maturity-assessment.md)
- [Readiness Regulatorio](regulatory-readiness.md)
- [Registro de Riscos do Projeto](project-risk-register.md)
- [Board de Prioridades do Projeto](project-priority-board.md)
- [Matriz Operacional de Execucao para 95%](project-operational-execution-board.md)

## Resumo Executivo

Leitura recomendada:

- `Trimestre 1`: cruzar `90%+` com homologacao seria dos blocos mais criticos
- `Trimestre 2`: consolidar governanca e operacao recorrente para chegar a `93%`
- `Trimestre 3`: institucionalizar confiabilidade e cadeia de custodia para chegar a `95%`

Premissa central:

- o maior ganho remanescente nao vem de novas features, e sim de homologacao, governanca formal e operacao seria repetivel

## Regua Utilizada

### Impacto na Maturidade Tecnica

- `Muito alto`: move diretamente a baseline oficial
- `Alto`: reduz bloqueadores estruturais de release
- `Medio`: consolida operacao e governanca

### Esforco Relativo

- `Baixo`: ate 1 semana util concentrada
- `Medio`: 1 a 2 semanas uteis
- `Alto`: 2+ semanas uteis ou forte dependencia externa

## Trimestre 1 — Cruzar 90%+

### Objetivo

- remover os bloqueadores mais densos para `staging` serio

### Meta de Saida

- baseline tecnica em `90%+`
- prontidao regulatoria aproximada em `82%`

### Itens Prioritarios

| Ordem | Item | Dominio | Prioridade | Esforco | Impacto | Dependencias | Ganho Estimado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `P0-01` homologar `OIDC` serio com segredos nao-dev | Auth | P0 | Alto | Muito alto | IdP, claims, secrets | `+0.8 a +1.0` |
| 2 | `P0-02` fechar MFA serio e runbook de indisponibilidade | Auth | P0 | Medio | Alto | `P0-01` | `+0.4 a +0.7` |
| 3 | `P0-05` integrar provider real AML/KYT em modo `live` | Compliance | P0 | Alto | Muito alto | contrato e credenciais | `+0.8 a +1.0` |
| 4 | `P0-06` homologar RPC primario + fallback | Investigation | P0 | Alto | Alto | providers aceitos | `+0.5 a +0.8` |
| 5 | executar `run_staging_window.py` em janela seria controlada | Release | P1 | Medio | Alto | itens acima minimamente prontos | ganho transversal |

### Critérios de Aceite

- `OIDC` sem `localhost`, sem `dev auth` e com evidencias de login real
- MFA serio protegendo fluxo sensivel ou explicitamente federado pelo IdP
- `provider-readiness` e `rpc-readiness` validados em janela seria
- dossier de janela anexado ao sign-off

### Riscos Dominantes

- dependencia de credenciais externas
- drift entre ambiente serio e baseline local
- flakiness de provider em primeira homologacao

## Trimestre 2 — Consolidar 93%

### Objetivo

- converter capacidade tecnica em governanca operacional aceita

### Meta de Saida

- baseline tecnica em torno de `93%`
- prontidao regulatoria aproximada em `89%`

### Itens Prioritarios

| Ordem | Item | Dominio | Prioridade | Esforco | Impacto | Dependencias | Ganho Estimado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `P1-01` obter sign-off formal de retention/recovery | Governanca | P0 | Medio | Alto | baseline publicada | `+0.5 a +0.8` |
| 2 | `P2-02` obter aceite formal de owners/SLA/runbooks | Operacao | P1 | Medio | Alto | owners e runbooks publicados | `+0.4 a +0.6` |
| 3 | classificar evidencias por sensibilidade e descarte | Governanca | P1 | Medio | Medio | `P1-01` | `+0.3 a +0.5` |
| 4 | repetir janelas serias com dossier e historico comparavel | Release | P1 | Medio | Alto | Trimestre 1 | `+0.5 a +0.8` |
| 5 | reforcar RCA cross-domain e alertas operacionais | Observabilidade | P1 | Medio | Medio | trilha de incidentes | `+0.4 a +0.6` |

### Critérios de Aceite

- registros formais de aceite em retention/recovery e ownership operacional
- pelo menos duas janelas serias com artefatos consistentes
- rito minimo de incidente e escalacao documentado e exercitado
- classificacao minima de evidencias aplicada aos fluxos mais sensiveis

### Riscos Dominantes

- atraso de sign-off por stakeholders externos
- governanca publicada, mas sem uso real recorrente
- evidencias produzidas sem disciplina operacional suficiente

## Trimestre 3 — Alcançar 95%

### Objetivo

- institucionalizar confiabilidade e reduzir dependencia de validacao manual dispersa

### Meta de Saida

- baseline tecnica em `95%`
- prontidao regulatoria significativamente superior, ainda sem afirmar producao plena automatica

### Itens Prioritarios

| Ordem | Item | Dominio | Prioridade | Esforco | Impacto | Dependencias | Ganho Estimado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | implantar vault e estrategia de secrets de producao | Seguranca | P0 | Alto | Alto | auth serio e ambientes estáveis | `+0.5` |
| 2 | formalizar incident response com war room e RCA | Operacao | P1 | Medio | Alto | runbooks aceitos | `+0.4 a +0.6` |
| 3 | elevar cadeia de custodia com assinatura/selagem externa ou equivalente | Evidencias | P1 | Alto | Alto | classificacao de evidencias | `+0.4 a +0.6` |
| 4 | automatizar mais a promocao para ambiente superior | Release | P1 | Medio | Medio | janelas serias recorrentes | `+0.3 a +0.5` |
| 5 | granularizar papeis regulatoriamente mais finos por dominio | Seguranca | P1 | Medio | Medio | `RBAC` base homologado | `+0.3 a +0.4` |

### Critérios de Aceite

- secrets de producao fora de arquivos locais sensiveis
- war room, escalacao e RCA com evidencias executadas
- cadeia de custodia reforcada em evidencias mais criticas
- promocao mais previsivel e menos manual

### Riscos Dominantes

- complexidade institucional maior que a técnica
- custo de integração de vault e selagem externa
- aumento de overhead operacional sem automação suficiente

## Sequencia Recomendada

1. resolver primeiro o que destrava `staging` serio de verdade
2. depois transformar baseline em governanca aceita
3. por fim institucionalizar confiabilidade e cadeia de custodia

## KPIs do Plano

| KPI | Meta |
| --- | --- |
| Baseline tecnica | `90%+` ao fim do Trimestre 1, `93%` ao fim do Trimestre 2, `95%` ao fim do Trimestre 3 |
| Readiness regulatorio | `82%` ao fim do Trimestre 1, `89%` ao fim do Trimestre 2 |
| Janelas serias com dossier | pelo menos `2` ate o fim do Trimestre 2 |
| Sign-offs formais pendentes | `0` para retention/recovery e owners/SLA ate o fim do Trimestre 2 |
| Providers reais homologados | AML/KYT e RPC em modo serio ate o fim do Trimestre 1 |

## Decisao Recomendada

- nao abrir grandes frentes novas de feature antes de encerrar os itens do Trimestre 1
- usar o Trimestre 2 para converter maturidade tecnica em governanca aceita
- usar o Trimestre 3 para institucionalizar producao seria sem alegar prontidao regulatoria plena antes das evidencias finais

## Suposicoes

- o projeto continua priorizando seguranca, compliance e evidencias acima de feature velocity
- existe acesso progressivo a credenciais, owners e sign-offs externos nos proximos ciclos
- a maturidade sera recalculada ao final de cada trimestre com base em evidencias reais, nao em expectativa
