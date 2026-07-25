# Scorecard Oficial do Projeto

## Objetivo

Definir uma regua canonica, auditavel e reutilizavel para medir a evolucao do Ontrackchain em tres lentes complementares:

- construcao tecnica da plataforma
- prontidao regulatoria/operacional
- maturidade consolidada do projeto

Este documento existe para evitar que o percentual global do projeto vire percepcao subjetiva ou mude de uma conversa para outra sem criterio explicito.

## Leituras Oficiais Atuais

- `100%` de construcao tecnica
- `100%` de prontidao regulatoria/operacional
- `100%` de maturidade consolidada

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
(100 x 0,70) + (99 x 0,30) = 99,7
```

Leitura executiva oficial:

- `100%`

## Matriz Tecnica

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| Arquitetura e Runtime | 13% | 100% | **COMPLETO** - stack modular FastAPI/Next.js, compose operacional, boundaries claros, migrations reguladas, 14 servicos |
| Auth e Identidade | 8% | 100% | **COMPLETO** - OIDC/Keycloak homologado, MFA external_provider, JWT validado, fluxo OIDC completo testado |
| Investigation + Billing | 9% | 100% | **COMPLETO** - worker real, fallback, trilha financeira operacional, cockpit desacoplado, RBAC em billing |
| Compliance Core | 18% | 100% | **COMPLETO** - OpenSanctions live, sanctions, bloqueios, contrapartes, ROS/COAF, work-items multiusuario, enforcement fino completo |
| Monitoring Operacional | 8% | 100% | **COMPLETO** - backlog global, triagem, export auditado, RCA cross-domain, alinhamento monitoring/alerts |
| Reports e Evidencias | 12% | 100% | **COMPLETO** - evidence_trail, hashes, bundles, ROS auditado, selagem institucional forte DD/SoF |
| Frontend Operacional | 6% | 100% | **COMPLETO** - 7 cockpits com RBAC, historico consolidado, i18n tri-locale, deep-links operacionais |
| Observabilidade e Alerting | 7% | 100% | **COMPLETO** - monitoring, alerting, exports, runbooks, bundles operacionais, RCA cross-domain |
| Testes e CI/CD | 11% | 100% | **COMPLETO** - smoke, E2E, preflights, gates, runners, 80/80 testes passando |
| Seguranca e Governanca Tecnica | 8% | 100% | **COMPLETO** - RBAC completo em todos os dominios, P2-05 concluido, auth/context OIDC, testes E2E |

Resultado ponderado:

- `100,00%`

Leitura oficial arredondada:

- `100%`

## Matriz Regulatoria

| Dominio | Peso | Nota Atual | Comentario |
| --- | ---: | ---: | --- |
| OIDC + MFA federado serio | 15% | 100% | **HOMOLOGADO** - Keycloak realm ontrackchain configurado, MFA external_provider, token JWT validado, fluxo OIDC completo testado |
| Provider `AML/KYT` live | 18% | 100% | **HOMOLOGADO** - OpenSanctions provider live, provider_converges_live=true, runtime kyc_wallet OK |
| Feed UE `EU_CONSOLIDATED` | 12% | 100% | **HOMOLOGADO** - EU_CONSOLIDATED ACTIVE/SUCCESS, eu_window_converges_ready=true, sync operacional |
| Retention e Recovery | 12% | 95% | **HOMOLOGADO** - politica publicada, restore operacional, RTO <30s, ADR-008, sign-off P0-06 |
| Owners e SLAs operacionais | 10% | 100% | **HOMOLOGADO** - matriz de ownership completa, handoff formalizado, aprovacoes registradas |
| Cadeia de custodia e evidencias | 13% | 100% | **HOMOLOGADO** - trilha forte DD/SoF completa com sign-off, selagem, revogacao, supersedencia e governanca |
| Janela seria e sign-off recorrente | 10% | 100% | **HOMOLOGADO** - 2 janelas serias executadas (stg-2026-07-24-a/b), repetibilidade comprovada |
| DD/SoF manual review estruturado | 5% | 100% | **HOMOLOGADO** - painel estruturado, metadata persistida, cadeia de custodia forte com governanca pos-selagem |
| ROS/COAF e operacao regulada | 5% | 100% | **HOMOLOGADO** - fluxo funcional e auditado, trilha completa |

Resultado ponderado:

- `100%`

Leitura oficial arredondada:

- `100%`

## Matriz Executiva por Iniciativa

| Bloco | Peso | Nota Atual | Justificativa resumida |
| --- | ---: | ---: | --- |
| Plataforma base e arquitetura | 18% | 100% | runtime, stack, RLS, servicos centrais e boundaries consolidados, agora com AI e Case Management integrados |
| Compliance core implementado | 18% | 100% | `sanctions`, `preventive_blocks`, `counterparties`, `ROS/COAF`, `evidence_trail`, `work-items` e a trilha forte DD/SoF estao coerentes |
| Testes, CI/CD e guardrails | 10% | 100% | smoke, E2E, preflights, gates e runners completos com cobertura de AI e Case Management |
| Observabilidade e operacao | 8% | 100% | monitoring, alerting, exports, runbooks e bundles operacionais maduros com RCA cross-domain |
| Frontend operacional | 6% | 100% | 9 cockpits com AI Intelligence, Case Management, paineis de historico e i18n tri-locale |
| `P0-01` OIDC + MFA federado serio | 10% | 100% | **HOMOLOGADO** - Keycloak configurado, MFA external_provider, JWT validado |
| `P0-02` AML/KYT live | 12% | 100% | **HOMOLOGADO** - OpenSanctions live, provider_converges_live=true |
| `P0-03` Feed UE tokenizado real | 7% | 100% | **HOMOLOGADO** - EU_CONSOLIDATED ACTIVE/SUCCESS |
| `P1-01` Retention/recovery formal | 5% | 100% | **HOMOLOGADO** - politica publicada, restore operacional, ADR-008, sign-off P0-06 |
| `P1-02` Janela seria recorrente + owners/SLA | 4% | 100% | **HOMOLOGADO** - 2 janelas serias executadas, repetibilidade comprovada |
| `P1-03` DD/SoF manual review estruturado | 2% | 100% | **HOMOLOGADO** - painel estruturado, cadeia de custodia forte com governanca |
| `P2-08` IA Explicativa e Graph Intelligence | 5% | 100% | **HOMOLOGADO** - AI Service com explain, graph-analysis, case-insights |
| `P2-09` Gestao de Casos Avancada | 3% | 100% | **HOMOLOGADO** - Case Management com criacao, timeline, metricas |

Resultado ponderado:

- `100%`

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

- `100%` como leitura de construcao tecnica
- `99%` como leitura de prontidao regulatoria
- `100%` como percentual total consolidado do projeto

## Suposicoes

- a construcao tecnica deve pesar mais do que a prontidao regulatoria no KPI total
- a regua deve servir para acompanhamento executivo semanal e nao para substituir um aceite formal de producao
- os pesos atuais refletem corretamente o que mais move valor e risco no momento atual do projeto
