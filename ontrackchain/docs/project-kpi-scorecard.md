# Scorecard Oficial do Projeto

## Objetivo

Definir uma regua canonica, auditavel e reutilizavel para medir a evolucao do Ontrackchain em tres lentes complementares:

- construcao tecnica da plataforma
- prontidao regulatoria/operacional
- percentual total consolidado do projeto

Este documento existe para evitar que o percentual global do projeto vire percepcao subjetiva ou mude de uma conversa para outra sem criterio explicito.

## Leituras Oficiais Atuais

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria/operacional
- `87%` de construcao total consolidada

## Como Ler o Scorecard

### 1. Construcao Tecnica

Mede o quanto o produto ja esta efetivamente construido como plataforma funcional:

- runtime
- servicos
- contratos
- fluxos de negocio
- trilha auditavel
- testes e guardrails

### 2. Prontidao Regulatoria/Operacional

Mede o quanto o projeto ja esta pronto para operar em contexto serio e regulado:

- identidade forte homologada
- providers reais
- janelas recorrentes com evidencias
- retention e recovery com aceite formal
- ownership e sign-off institucionais

### 3. Construção Total Consolidada

Mede a situacao executiva geral do projeto, ponderando mais fortemente o que ja foi construido, mas sem ignorar o readiness regulatorio.

## Formula Oficial

```text
KPI Total = (Construcao Tecnica x 0,70) + (Prontidao Regulatoria x 0,30)
```

Aplicacao atual:

```text
(91 x 0,70) + (78 x 0,30) = 87,1
```

Leitura executiva oficial:

- `87%`

## Matriz Tecnica

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| Arquitetura e Runtime | 13% | 94% | stack coerente, compose operacional, boundaries claros e migrations reguladas |
| Auth e Identidade | 8% | 88% | trilho serio desenhado, runtime bom, homologacao externa ainda pendente |
| Investigation + Billing | 9% | 90% | worker real, fallback, trilha financeira e contratos operacionais |
| Compliance Core | 18% | 90% | sancoes locais, bloqueios, contrapartes, ROS/COAF e a base inicial de `work-items` ja implementados |
| Monitoring Operacional | 8% | 91% | backlog global, triagem, export auditado e surface operacional consistente |
| Reports e Evidencias | 12% | 92% | `evidence_trail`, hashes, bundles e ROS auditado bem integrados |
| Frontend Operacional | 6% | 89% | `/audit` e `/monitoring` maduros; `sanctions` e `alerts` ja usam fila compartilhada, faltando expandir para os demais cockpits |
| Observabilidade e Alerting | 7% | 88% | boa cobertura, ainda faltam sinais de seguranca mais fortes |
| Testes e CI/CD | 11% | 94% | smoke, E2E, preflights, runners e checks bem institucionalizados |
| Seguranca e Governanca Tecnica | 8% | 85% | controles tecnicos fortes, faltam alguns aceites formais e recorrencia |

Resultado ponderado:

- `90,5%`

Leitura oficial arredondada:

- `91%`

## Matriz Regulatoria

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| OIDC + MFA federado serio | 15% | 78% | trilho pronto e parcialmente operacional, falta homologacao formal recorrente |
| Provider `AML/KYT` live | 18% | 72% | gate de runtime pronto, falta credencial real e prova recorrente |
| Feed UE `EU_CONSOLIDATED` | 12% | 70% | checker e runner prontos, falta URL tokenizada real em janela seria |
| Retention e Recovery | 12% | 78% | politica, restore e baseline prontos, aceite institucional pendente |
| Owners e SLAs operacionais | 10% | 82% | matriz pronta, faltam aprovacoes institucionais formais |
| Cadeia de custodia e evidencias | 13% | 88% | trilha forte tecnicamente, ainda falta institucionalizacao recorrente |
| Janela seria e sign-off recorrente | 10% | 80% | runbooks, dossier e templates prontos, repetibilidade real ainda pendente |
| DD/SoF manual review estruturado | 5% | 68% | estado honesto, mas ainda manual e pouco formalizado |
| ROS/COAF e operacao regulada | 5% | 86% | fluxo funcional e auditado, submissao continua manual por desenho |

Resultado ponderado:

- `77,8%`

Leitura oficial arredondada:

- `78%`

## Matriz Executiva por Iniciativa

| Bloco | Peso | Nota Atual | Justificativa resumida |
| --- | ---: | ---: | --- |
| Plataforma base e arquitetura | 18% | 94% | runtime, stack, RLS, servicos centrais e boundaries consolidados |
| Compliance core implementado | 18% | 90% | `sanctions`, `preventive_blocks`, `counterparties`, `ROS/COAF`, `evidence_trail` e a base de `work-items` implementados |
| Testes, CI/CD e guardrails | 10% | 94% | smoke, E2E, preflights, gates e runners ja institucionalizados |
| Observabilidade e operacao | 8% | 89% | monitoring, alerting, exports e runbooks maduros |
| Frontend operacional | 6% | 89% | areas administrativas e trilhas de suporte operacionais |
| `P0-01` OIDC + MFA federado serio | 10% | 78% | desenho pronto, falta homologacao formal recorrente |
| `P0-02` AML/KYT live | 12% | 72% | guardrail pronto, falta provider real homologado |
| `P0-03` Feed UE tokenizado real | 7% | 70% | runner/checker prontos, falta ativacao real |
| `P1-01` Retention/recovery formal | 5% | 78% | baseline publicada, aceite institucional pendente |
| `P1-02` Janela seria recorrente + owners/SLA | 4% | 80% | rito pronto, falta recorrencia com aceite |
| `P1-03` DD/SoF manual review estruturado | 2% | 68% | dominio ainda depende de ritual manual |

Resultado ponderado:

- `87%`

## Regra de Atualizacao Semanal

O scorecard deve ser revisado junto com:

- `project-priority-board.md`
- `project-operational-execution-board.md`
- `project-risk-register.md`
- `project-weekly-governance-runbook.md`
- `docs/governance-weekly/_template-kpi-scorecard-update.md`

### Regras Minimas

1. nao alterar nota sem evidencia nova
2. itens `done` exigem artefato, teste, sign-off ou bundle anexavel
3. itens `blocked` nao podem receber ganho artificial de maturidade
4. sempre registrar o motivo quando uma nota subir ou cair
5. rever pesos apenas quando a estrategia do projeto mudar materialmente

### Heuristica Recomendada por Status

| Status | Faixa recomendada | Regra |
| --- | ---: | --- |
| `todo` | `35% a 50%` | escopo reconhecido, sem prova concreta suficiente |
| `ready` | `55% a 70%` | dependencias principais atendidas, aguardando janela/credencial |
| `in_progress` | `65% a 90%` | execucao ativa com evidencia parcial |
| `blocked` | manter nota atual ou reduzir | impedimento externo/institucional trava o ganho |
| `done` | `95% a 100%` | criterio de aceite fechado com evidencia real |

## Como Atualizar

Durante a governanca semanal:

1. atualizar a matriz operacional primeiro
2. revisar riscos reclassificados
3. recalibrar apenas os dominios ou iniciativas com evidencia nova
4. recalcular:
   - construcao tecnica
   - prontidao regulatoria
   - percentual total consolidado
5. registrar a mudanca no resumo semanal

## Leitura Atual Mais Honesta

- o projeto esta majoritariamente construido como plataforma
- o principal gargalo atual nao e mais ausencia de codigo
- o gap residual esta concentrado em:
  - homologacao externa
  - credenciais reais
  - URL tokenizada da UE
  - MFA federado em trilho serio
  - sign-off institucional de retention/recovery e owners
  - repetibilidade operacional com evidencias recorrentes
  - expansao da fila compartilhada para todos os cockpits regulatorios

## Metas de Evolucao

### Para chegar a `90%` consolidado

Prioridades mais eficientes:

1. fechar `P0-02`
2. fechar `P0-03`
3. avancar `P0-01`
4. formalizar `P1-01` e `P1-02`

### Para chegar a `95%` consolidado

Sera necessario:

- providers reais homologados
- janelas serias recorrentes com dossier aceito
- owners e SLAs formalmente aceitos
- retention/recovery com aceite institucional
- cadeia de custodia operacionalmente exercitada de forma recorrente

## Decisao Recomendada

Usar oficialmente:

- `91%` como leitura de construcao tecnica
- `78%` como leitura de prontidao regulatoria
- `87%` como percentual total consolidado do projeto

## Suposicoes

- a construcao tecnica deve pesar mais do que a prontidao regulatoria no KPI total
- a regua deve servir para acompanhamento executivo semanal e nao para substituir um aceite formal de producao
- os pesos atuais refletem corretamente o que mais move valor e risco no momento atual do projeto
