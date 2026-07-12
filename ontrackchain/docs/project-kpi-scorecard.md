# Scorecard Oficial do Projeto

## Objetivo

Definir uma regua canonica, auditavel e reutilizavel para medir a evolucao do Ontrackchain em tres lentes complementares:

- construcao tecnica da plataforma
- prontidao regulatoria/operacional
- maturidade consolidada do projeto

Este documento existe para evitar que o percentual global do projeto vire percepcao subjetiva ou mude de uma conversa para outra sem criterio explicito.

## Leituras Oficiais Atuais

- `92%` de construcao tecnica
- `79%` de prontidao regulatoria/operacional
- `88%` de maturidade consolidada

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

### 3. Maturidade Consolidada

Mede a situacao executiva geral do projeto, ponderando mais fortemente o que ja foi construido, mas sem ignorar o readiness regulatorio.

## Formula Oficial

```text
KPI Total = (Construcao Tecnica x 0,70) + (Prontidao Regulatoria x 0,30)
```

Aplicacao atual:

```text
(92 x 0,70) + (79 x 0,30) = 88,1
```

Leitura executiva oficial:

- `88%`

## Matriz Tecnica

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| Arquitetura e Runtime | 13% | 94% | stack coerente, compose operacional, boundaries claros e migrations reguladas |
| Auth e Identidade | 8% | 88% | trilho serio desenhado, runtime bom, homologacao externa ainda pendente |
| Investigation + Billing | 9% | 90% | worker real, fallback, trilha financeira operacional e superfícies administrativas endurecidas em `billing/balance` e `billing/reconciliation` |
| Compliance Core | 18% | 91% | sancoes locais, bloqueios, contrapartes, ROS/COAF, `work-items` multiusuario e metadata canônica padronizada entre frontend/backend/contrato |
| Monitoring Operacional | 8% | 92% | backlog global, triagem, export auditado, RCA cross-domain leve derivada de `work-items` e surface operacional coerente com preset de governanca |
| Reports e Evidencias | 12% | 95% | `evidence_trail`, hashes, bundles, ROS auditado e selagem institucional forte DD/SoF integrados ponta a ponta |
| Frontend Operacional | 6% | 94% | todos 7 cockpits usam fila compartilhada, paineis de historico consolidados, i18n tri-locale e deep-links operacionais entre `audit` e `evidence` |
| Observabilidade e Alerting | 7% | 89% | boa cobertura e bundles operacionais mais consistentes; alertas agora carregam trilha leve de RCA entre `alerts`, `/monitoring`, export administrativo e governanca, mas ainda faltam sinais de seguranca mais fortes e recorrencia real |
| Testes e CI/CD | 11% | 95% | smoke, E2E, preflights, runners e checks ficaram mais fortes com a ampliacao da cobertura focal de custodia e governanca |
| Seguranca e Governanca Tecnica | 8% | 88% | RBAC, quorum, `finalize`, `revoke` e `supersede` fortaleceram a trilha; `P2-05` ja endurece `REVIEWER` e `BILLING_ADMIN`, mas faltam provider institucional definitivo e recorrencia formal |

Resultado ponderado:

- `91,86%`

Leitura oficial arredondada:

- `92%`

## Matriz Regulatoria

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| OIDC + MFA federado serio | 15% | 78% | trilho pronto e parcialmente operacional, falta homologacao formal recorrente |
| Provider `AML/KYT` live | 18% | 72% | gate de runtime pronto, falta credencial real e prova recorrente |
| Feed UE `EU_CONSOLIDATED` | 12% | 70% | checker e runner prontos, falta URL tokenizada real em janela seria |
| Retention e Recovery | 12% | 78% | politica, restore e baseline prontos, aceite institucional pendente |
| Owners e SLAs operacionais | 10% | 82% | matriz pronta, faltam aprovacoes institucionais formais |
| Cadeia de custodia e evidencias | 13% | 91% | trilha forte DD/SoF agora cobre sign-off, selagem, revogacao, supersedencia e governanca; falta institucionalizacao recorrente |
| Janela seria e sign-off recorrente | 10% | 80% | runbooks, dossier e templates prontos, repetibilidade real ainda pendente |
| DD/SoF manual review estruturado | 5% | 76% | painel e cadeia de custodia forte estao prontos, mas a operacao segue humana e sem provider institucional definitivo |
| ROS/COAF e operacao regulada | 5% | 86% | fluxo funcional e auditado, submissao continua manual por desenho |

Resultado ponderado:

- `78,55%`

Leitura oficial arredondada:

- `79%`

## Matriz Executiva por Iniciativa

| Bloco | Peso | Nota Atual | Justificativa resumida |
| --- | ---: | ---: | --- |
| Plataforma base e arquitetura | 18% | 95% | runtime, stack, RLS, servicos centrais e boundaries consolidados, agora com cadeia de custodia forte mais madura |
| Compliance core implementado | 18% | 91% | `sanctions`, `preventive_blocks`, `counterparties`, `ROS/COAF`, `evidence_trail`, `work-items` e a trilha forte DD/SoF estao coerentes |
| Testes, CI/CD e guardrails | 10% | 95% | smoke, E2E, preflights, gates e runners ficaram mais completos com a cobertura focal da governanca de custodia |
| Observabilidade e operacao | 8% | 90% | monitoring, alerting, exports, runbooks e bundles operacionais maduros, agora com RCA cross-domain leve conectando `alerts`, `monitoring` e artefatos executivos sem mudar a baseline por si só |
| Frontend operacional | 6% | 94% | todos 7 cockpits com paineis de historico consolidados, i18n tri-locale, fila compartilhada sincronizada e navegacao `audit <-> evidence` |
| `P0-01` OIDC + MFA federado serio | 10% | 78% | desenho pronto, falta homologacao formal recorrente |
| `P0-02` AML/KYT live | 12% | 72% | guardrail pronto, falta provider real homologado |
| `P0-03` Feed UE tokenizado real | 7% | 70% | runner/checker prontos, falta ativacao real |
| `P1-01` Retention/recovery formal | 5% | 78% | baseline publicada, aceite institucional pendente |
| `P1-02` Janela seria recorrente + owners/SLA | 4% | 80% | rito pronto, falta recorrencia com aceite |
| `P1-03` DD/SoF manual review estruturado | 2% | 84% | painel estruturado, metadata persistida, historico rastreado e cadeia de custodia forte com governanca pos-selagem ja entregues |

Resultado ponderado:

- `88%`

## Regra de Leitura por Taxonomia

- `P0` mede os blocos que movem KPI imediatamente e destravam a subida legitima para `90%+`
- `P1` mede a institucionalizacao minima para sustentar o salto para `90%+`
- `P2` mede sustentacao pos-90, reducao de debito operacional e preparacao do caminho para `95%`
- leituras historicas de sprint ou IDs antigos devem ser tratadas apenas como referencia documental, nunca como namespace prioritario atual

## Regra de Atualizacao Semanal

O scorecard deve ser revisado junto com:

- `project-priority-board.md`
- `project-operational-execution-board.md`
- `project-risk-register.md`
- `project-weekly-governance-runbook.md`
- `docs/governance-weekly/templates/_template-kpi-scorecard-update.md`

### Regras Minimas

1. nao alterar nota sem evidencia nova
2. itens `done` exigem artefato, teste, sign-off ou bundle anexavel
3. itens `blocked` nao podem receber ganho artificial de maturidade
4. sempre registrar o motivo quando uma nota subir ou cair
5. rever pesos apenas quando a estrategia do projeto mudar materialmente
6. aplicar a regra de promocao por evidencia formalizada em [ADR-010](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)
7. melhorias de rastreabilidade operacional, como RCA cross-domain em `alerts`/`monitoring`/exports/governanca, podem endurecer comentario executivo e reduzir risco percebido, mas nao sobem nota sem uso recorrente e evidencia revisada no ciclo

### Regra de Promocao

Em caso de duvida sobre subida de score, vale a regra:

- execucao real primeiro
- evidencia preservada depois
- revisao humana em seguida
- aprovacao explicita por ultimo

Sem esses quatro elementos, a baseline oficial nao deve subir.

Regra complementar para `P0-04`:

- tentativa parcial de `P0-02` ou `P0-03` pode justificar melhoria localizada de leitura regulatoria quando houver artefato revisavel e risco melhor delimitado
- a travessia oficial de `89% -> 90%+` continua exigindo prova combinada de `P0-02` e `P0-03`, preferencialmente consolidada por `P0-04`
- da mesma forma, `P2-03` pode endurecer leitura operacional e reduzir ambiguidade de incidentes, mas nao altera a baseline executiva sem artefato recorrente, war room exercitado e uso real do resumo RCA no ciclo

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
  - endurecimento institucional final da selagem DD/SoF

## Metas de Evolucao

### Para chegar a `90%` consolidado

Prioridades mais eficientes:

1. fechar `P0-02`
2. fechar `P0-03`
3. consolidar `P0-04` apenas quando `P0-02` e `P0-03` convergirem na mesma trilha revisavel
4. avancar `P0-01`
5. converter `RUN-STG-01` em execucao auditavel via `P0-05`
6. formalizar `P0-06` e sincronizar a narrativa em `P0-07`

### Para chegar a `95%` consolidado

Sera necessario:

- providers reais homologados
- primeira janela seria material (`P0-05`) fechada com artefatos coerentes
- retention/recovery com aceite institucional (`P0-06` / `P1-01`)
- owners e SLAs formalmente aceitos com rito recorrente (`P1-02`)
- janelas serias recorrentes com dossier aceito
- cadeia de custodia operacionalmente exercitada de forma recorrente

## Decisao Recomendada

Usar oficialmente:

- `92%` como leitura de construcao tecnica
- `79%` como leitura de prontidao regulatoria
- `88%` como percentual total consolidado do projeto

## Suposicoes

- a construcao tecnica deve pesar mais do que a prontidao regulatoria no KPI total
- a regua deve servir para acompanhamento executivo semanal e nao para substituir um aceite formal de producao
- os pesos atuais refletem corretamente o que mais move valor e risco no momento atual do projeto
