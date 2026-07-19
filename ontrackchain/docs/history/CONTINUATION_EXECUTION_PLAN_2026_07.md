# Plano Consolidado de Continuidade e Execucao

**Data base:** 2026-07-05

> Aviso de classificacao: este e um artefato datado de apoio ao ciclo de julho. Para a trilha viva e canonica, use primeiro o [Resumo Executivo de Readiness](../project-executive-readiness-brief.md), o [Kit de Execucao por Evidencia](../project-maturity-evidence-execution-kit.md), o [Board Operacional Unico](../project-operational-execution-board.md) e o [Scorecard Oficial do Projeto](../project-kpi-scorecard.md).

## Objetivo

Consolidar em um unico documento a baseline oficial do projeto, o caminho critico para subida de maturidade, a fila priorizada em formato Kanban e o cronograma diario recomendado para continuidade da execucao ate `95%`.

Este documento deve ser usado em conjunto com:

- [Avaliacao Consolidada de Status do Projeto](../assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- [Scorecard Oficial do Projeto](../project-kpi-scorecard.md)
- [Plano Tatico Sprint 7-9](./TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md)
- [Plano Consolidado ate 95%](../project-construction-plan-to-95-percent.md)
- [Board Operacional Unico](../project-operational-execution-board.md)
- [Owners e SLAs Operacionais](../operational-ownership-and-slas.md)
- [Readiness Regulatorio](../regulatory-readiness.md)
- [Workflow de Atualizacao Semanal da Governanca](../governance-weekly/guides/WEEKLY_GOVERNANCE_UPDATE_WORKFLOW.md)
- [ADR-009 Hardening First](../adrs/ADR-009-continuation-strategy-hardening-first.md)

## Baseline Oficial

- construcao tecnica: `91%`
- prontidao regulatoria/operacional: `78%`
- construcao consolidada: `87%`

Leitura executiva:

- a plataforma esta tecnicamente madura
- o maior gap remanescente nao e estrutural de codigo
- a prioridade do ciclo atual e homologacao real, prova operacional e aceite institucional

## Principio de Execucao

Adotar `hardening first` como estrategia de continuidade:

1. fechar integracoes e autenticacao em modo serio
2. anexar evidencias reais e repetiveis
3. formalizar governanca, ownership e recovery
4. so depois abrir frentes maiores de evolucao estrutural

## Caminho Critico

Ordem recomendada de ataque:

1. `P0-02` homologar provider `AML/KYT live`
2. `P0-03` homologar feed UE tokenizado real
3. `P0-01` homologar `OIDC + MFA` serio
4. executar `RUN-STG-01` com packet, dossier e sign-off
5. formalizar owners, SLA e drill operacional
6. formalizar retention/recovery com restore controlado
7. executar segunda janela seria comparavel
8. recalibrar scorecard e publicar nova baseline

## Quadro Kanban Consolidado

| ID | Bloco | Dominio | Status atual | Owner sugerido | Evidencia de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P0-01` | `OIDC + MFA` serio | Auth | `blocked` | Security/Auth Lead | `preflight_oidc_serious_env.py` + `smoke_auth_oidc_mode.py` + bundle OIDC + E2E critico |
| `P0-02` | `AML/KYT live` | Compliance | `ready` | Compliance Lead | `make check-compliance-provider-runtime` verde + JSON persistido |
| `P0-03` | Feed UE real | Compliance | `ready` | Regulatory/Ops | `eu-sanctions-preflight.json` + `eu-sanctions-sync.json` + `source_url` valida |
| `RUN-STG-01` | Primeira janela seria | Ops/Release | `pending_execucao` | Release Manager Tecnico | packet + dossier + sign-off + artifact do workflow |
| `P1-03` | Ownership e assignment formal | Ops/Governanca | `in_progress` | COO / Ops Manager | owners validados + aceite escrito + drill documentado |
| `P2-01` | Retention/recovery formal | Platform/Security | `in_progress` | CTO / Security / DBA | restore controlado + RTO/RPO + aceites formais |
| `P2-02` | Janela seria recorrente | Ops | `in_progress` | Ops Manager | duas execucoes comparaveis com dossier aceito |
| `P1-04` | Fechar `evidence` | Front/Reports | `todo` | Backend Core | fluxo operacional mais completo + regressao verde |
| `P1-05` | Fechar `reports` | Front/Reports | `todo` | Backend Core | listagem e filtros mais ricos + integracao com bundles |
| `P1-06` | Fechar `counterparties` | Front/Compliance | `todo` | Compliance/Backend | revisao detalhada e DD estruturado fim a fim |
| `P2-05` | Refinar RBAC por dominio | Auth/Core | `todo` | Backend/Auth | matriz por papel aplicada em dominios sensiveis |
| `P3-01` | Vault/secrets de producao | Infra | `todo` | Infra Lead | decisao + rollout + rotacao validada |
| `P3-02` | Selagem/assinatura de evidence trail | Security | `todo` | Security Lead | PKI/HSM definido + prova tecnica |
| `P3-03` | War room e RCA cross-domain | Ops | `todo` | Incident Manager | playbook + escalonamento + treino |
| `P3-04` | Promocao `staging -> producao` | DevOps | `todo` | Infra/Platform | workflow + rollback + aprovacoes |

## Owners Nominais e Datas-Alvo

### Observacao

- onde nao houver nome pessoal confirmado, usar o owner por papel como responsavel nominal canonico
- nenhum item deve mudar de status sem evidência associada
- datas abaixo sao datas-alvo operacionais e nao substituem aceite formal de stakeholder

| Bloco | Owner nominal | Apoio principal | Data-alvo inicial | Data-alvo de fechamento | Resultado esperado |
| --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | Backend Core / Security | `2026-07-05` | `2026-07-08` | checker verde + JSON persistido + readiness coerente |
| `P0-03` feed UE real | Regulatory/Ops Lead | Compliance/Backend | `2026-07-05` | `2026-07-08` | preflight/sync verde + `source_url` valida |
| `P0-01` `OIDC + MFA` serio | Security Lead | Auth Lead / Platform | `2026-07-05` | `2026-07-15` | preflight + smoke + bundle OIDC + E2E critico |
| `RUN-STG-01` primeira janela seria | Release Manager Tecnico | Ops Manager / todos os owners P0 | `2026-07-06` | `2026-07-15` | packet + dossier + sign-off + decisao final da janela |
| `P1-03` ownership/SLA | COO / Ops Manager | Platform/SRE / Security | `2026-07-08` | `2026-07-15` | owners aprovados + SLA aceito + drill executado |
| `P2-01` retention/recovery | CTO / Security Lead | Platform/DBA / Compliance | `2026-07-09` | `2026-07-18` | restore controlado + RTO/RPO + aceites |
| `P2-02` janela seria recorrente | Ops Manager | Release Manager Tecnico | `2026-07-16` | `2026-07-22` | segunda janela comparavel com dossier aceito |
| `P3-01` vault/secrets | Infra Lead | Security Lead | `2026-07-23` | `T3 2026` | decisao de tecnologia + backlog granular |
| `P3-02` selagem de evidence trail | Security Lead | Backend Core / Infra | `2026-07-23` | `T3 2026` | direcao PKI/HSM definida + plano tecnico |
| `P3-03` RCA/war room cross-domain | Incident Manager | Ops Manager / Security | `2026-07-23` | `T3 2026` | playbook formal e treino inicial |
| `P3-04` promocao `staging -> producao` | Platform Lead | Infra / Backend Core | `2026-07-23` | `T3 2026` | pipeline e rollback planejados |

## Checkpoints Semanais

### Semana de 2026-07-05 a 2026-07-08

#### Foco da Semana 2026-07-05 a 2026-07-08

- obter credenciais e URLs reais
- mover `P0-02` e `P0-03` de `ready` para `ready_for_validation`
- tirar `P0-01` de bloqueio parcial se o provider responder

#### Checklist da Semana 2026-07-05 a 2026-07-08

- owner nominal confirmado para cada trilha `P0`
- resposta dos provedores registrada
- tracker semanal atualizado
- artefatos iniciais anexados

### Semana de 2026-07-09 a 2026-07-15

#### Foco da Semana 2026-07-09 a 2026-07-15

- executar primeira janela seria
- formalizar ownership e SLA
- preparar aceite de retention/recovery

#### Checklist da Semana 2026-07-09 a 2026-07-15

- war room com owners online
- packet e dossier gerados
- resultado da janela registrado
- drill de ownership executado

### Semana de 2026-07-16 a 2026-07-22

#### Foco da Semana 2026-07-16 a 2026-07-22

- homologar OIDC serio
- executar segunda janela comparavel
- colher sign-offs formais
- recalibrar baseline

#### Checklist da Semana 2026-07-16 a 2026-07-22

- bundle OIDC anexado
- restore controlado evidenciado
- aceites de COO, CTO, Security e Compliance coletados
- scorecard revisado se houver prova material suficiente

## Ritual Semanal Recomendado

### Segunda-feira

- revisar matriz operacional
- revisar itens `blocked`
- confirmar owner nominal e proxima evidência esperada

### Quarta-feira

- checar se os itens `P0` entraram em execucao real
- escalar dependencias externas sem resposta
- revisar risco de `no-go`

### Sexta-feira

- classificar cada item em `blocked`, `in_progress`, `ready_for_validation` ou `done`
- anexar paths dos artefatos produzidos
- registrar decisao semanal em governanca

## Modelo Semanal Preenchivel

Usar esta secao como espelho rapido do estado da semana corrente, sem substituir os boards e checklists canonicos. O objetivo e facilitar a reuniao semanal, concentrando owner, status, ultima evidência e proxima acao verificavel.

### Regras de Preenchimento

- atualizar no inicio e no fim de cada semana
- nao preencher `verde` ou `done` sem artefato revisavel
- usar linguagem objetiva, orientada a evidencia
- sempre registrar um proximo passo verificavel com data

### Snapshot Semanal - Modelo

| Bloco | Owner nominal | Status da semana | Ultima evidencia revisada | Bloqueio atual | Proxima acao verificavel | Data alvo | Semaforo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P0-03` feed UE real | Regulatory/Ops Lead | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P0-01` `OIDC + MFA` serio | Security Lead | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `RUN-STG-01` primeira janela seria | Release Manager Tecnico | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P1-03` ownership/SLA | COO / Ops Manager | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P2-01` retention/recovery | CTO / Security Lead | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P2-02` janela seria recorrente | Ops Manager | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |

### Snapshot Semanal - 2026-07-06

| Bloco | Owner nominal | Status da semana | Ultima evidencia revisada | Bloqueio atual | Proxima acao verificavel | Data alvo | Semaforo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | `ready` sem evidencia real nova | gate `make check-compliance-provider-runtime` documentado e aguardando execucao com credenciais reais | credencial real do provider ainda nao anexada | executar checker com credenciais reais e persistir JSON em `artifacts/staging/checks/` | `2026-07-08` | `amarelo` |
| `P0-03` feed UE real | Regulatory/Ops Lead | `ready` sem evidencia real nova | gate `make gate-p0-03-eu-live` documentado e aguardando URL tokenizada valida | `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` real ainda nao confirmada | executar janela UE com `REQUEST_ID` e anexar JSONs de preflight/sync | `2026-07-08` | `amarelo` |
| `P0-01` `OIDC + MFA` serio | Security Lead | `blocked` | nenhum artefato novo revisado; segue dependendo de homologacao externa | provider OIDC serio e aceite institucional ainda ausentes | confirmar credenciais/claims reais e rodar `preflight_oidc_serious_env.py` + `smoke_auth_oidc_mode.py` | `2026-07-15` | `vermelho` |
| `RUN-STG-01` primeira janela seria | Release Manager Tecnico | `pending_execucao` | janela `stg-2026-07-06-a` aberta em `mode=baseline`, com war room e tracking ativos | war room ainda depende de sair de `no-go`; faltam handoff, canais e secrets reais | preencher folha manual, revisar unblock checklist e rerodar gate agregado antes do dispatch real | `2026-07-15` | `amarelo` |
| `P1-03` ownership/SLA | COO / Ops Manager | `in_progress` com aceite pendente | matriz de owners, SLA base e runbooks publicados; estado em `ready_for_approval` | aceite formal de Platform/SRE e Security ainda pendente | atualizar status de aceite e registrar decisao escrita dos papeis pendentes | `2026-07-15` | `amarelo` |
| `P2-01` retention/recovery | CTO / Security Lead | `in_progress` com baseline pronta | politica publicada; restore controlado tratado como baseline tecnica | sign-off formal de Security e Compliance ainda pendente | executar/revisar restore controlado, registrar RTO/RPO e colher aceite formal | `2026-07-18` | `amarelo` |
| `P2-02` janela seria recorrente | Ops Manager | `in_progress` dependente da primeira janela | rito, war room e sign-off publicados | ainda nao ha primeira execucao `ok` para tornar a recorrencia comparavel | concluir `RUN-STG-01` com dossier aceito e agendar segunda janela comparavel | `2026-07-22` | `amarelo` |

### Resumo Executivo da Semana - Modelo

- **baseline da semana:** `manter` ou `recalibrar`
- **principal ganho:** `preencher`
- **principal bloqueio:** `preencher`
- **item mais proximo de fechamento:** `preencher`
- **item que exige escalacao externa:** `preencher`
- **decisao recomendada:** `go` / `go_with_exception` / `pending` / `no-go`

### Resumo Executivo da Semana - 2026-07-06

- **baseline da semana:** `manter`
- **principal ganho:** a janela seria `stg-2026-07-06-a` ja esta institucionalizada no rito ativo, com war room, tracking, sign-off e checklist de desbloqueio publicados
- **principal bloqueio:** ainda faltam credenciais reais e aceite institucional para mover `P0-01`, `P0-02` e `P0-03` de readiness documental para prova operacional
- **item mais proximo de fechamento:** `P0-02` ou `P0-03`, desde que cheguem os insumos externos
- **item que exige escalacao externa:** `P0-01`
- **decisao recomendada:** `pending`

### Checklist de Fechamento da Semana

- [ ] snapshot semanal atualizado
- [ ] itens `blocked` explicitamente marcados
- [ ] paths dos artefatos anexados
- [ ] proxima evidencia esperada registrada por item critico
- [ ] riscos reclassificados quando necessario
- [ ] decisao executiva da semana registrada em governanca

### Checklist de Fechamento da Semana - 2026-07-06

- [x] snapshot semanal atualizado
- [x] itens `blocked` explicitamente marcados
- [ ] paths dos artefatos anexados
- [x] proxima evidencia esperada registrada por item critico
- [ ] riscos reclassificados quando necessario
- [x] decisao executiva da semana registrada em governanca

#### Leitura da Checklist - 2026-07-06

- `snapshot semanal atualizado`: atendido pelo preenchimento da secao `Snapshot Semanal - 2026-07-06`
- `itens blocked explicitamente marcados`: atendido por `P0-01` bloqueado e por `RUN-STG-01` ainda dependente de sair de `no-go`
- `paths dos artefatos anexados`: ainda pendente no sentido estrito de artifact real de execucao; hoje existem paths de war room, tracking, sign-off e checklist, mas o artifact final da janela segue `pending`
- `proxima evidencia esperada registrada`: atendido em todos os itens criticos do snapshot e da governanca semanal
- `riscos reclassificados quando necessario`: ainda sem gatilho material novo suficiente para reclassificacao forte; manter leitura conservadora
- `decisao executiva da semana registrada`: atendido pela recomendacao `pending`, manutencao da baseline e decisao de nao promover `P0-02/P0-03` sem artefato real

## Proxima Atualizacao Esperada

Esta secao existe para evitar promocao subjetiva de status. A proxima atualizacao semanal so deve mudar materialmente quando algum dos gatilhos abaixo ocorrer com evidencia revisavel.

### Gatilhos Legitimos de Avanco

| Bloco | Gatilho legitimo | Evidencia minima | Mudanca esperada |
| --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | provider entregar credenciais reais e checker executar verde | `check-compliance-provider-runtime` + JSON persistido | `ready -> ready_for_validation` ou `done` |
| `P0-03` feed UE real | URL tokenizada valida e sync verde | JSONs de preflight e sync com `EU_CONSOLIDATED` coerente | `ready -> ready_for_validation` ou `done` |
| `P0-01` `OIDC + MFA` serio | credenciais/claims reais disponiveis e fluxo serio validado | preflight + smoke + bundle OIDC + E2E critico | `blocked -> in_progress` ou `ready_for_validation` |
| `RUN-STG-01` primeira janela seria | war room sair de `no-go` e workflow concluir com artifact valido | packet + dossier + sign-off + artifact oficial | `pending_execucao -> ready_for_validation` ou `done` |
| `P1-03` ownership/SLA | aceite escrito de Platform/SRE e Security + drill executado | documento de ownership atualizado + registro do drill | `in_progress -> done` |
| `P2-01` retention/recovery | restore controlado revisado e sign-offs coletados | evidência de restore + RTO/RPO + aceite formal | `in_progress -> done` |
| `P2-02` janela seria recorrente | segunda janela comparavel executada com dossie aceito | artifact e dossie da segunda janela | `in_progress -> done` |

### O Que Nao Deve Mudar Status

- promessa verbal de provider sem credencial ou output revisavel
- preparacao de reuniao sem artefato de execucao
- disponibilidade declarada de owner sem war room atualizado
- documentacao de roteiro sem checker, bundle, dossie ou sign-off correspondente
- validacao `dev` usada como substituto de fluxo serio

### Proxima Revisao Recomendada

- data-alvo: `apos mudanca material em P0-01`, `P0-02`, `P0-03` ou `RUN-STG-01`
- rito: governanca semanal curta baseada em evidencia
- saida esperada:
  - manter baseline `91% / 78% / 87%`, se nao houver prova nova
  - ou recalibrar status/scorecard apenas quando houver artefato real anexavel

## Estado Esperado Pos-Gatilho

Esta secao traduz a passagem esperada de cada bloco quando o gatilho legitimo acontecer. O objetivo e reduzir duvida durante o rito semanal sobre qual deve ser o novo estado e o que ainda fica pendente depois da primeira prova.

| Bloco | Estado atual de referencia | Quando o gatilho ocorrer | Estado esperado imediato | Pendente residual esperado |
| --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | `ready` | checker verde com credencial real e JSON persistido | `ready_for_validation` | anexar bundle consolidado da janela ou promover para `done` se a prova ja for suficiente |
| `P0-03` feed UE real | `ready` | preflight/sync verde com `source_url` valida e JSONs persistidos | `ready_for_validation` | fechar coerencia do bundle regulatorio da janela e promover para `done` |
| `P0-01` `OIDC + MFA` serio | `blocked` | preflight, smoke e trilho serio com claims reais executados | `in_progress` ou `ready_for_validation` | homologacao institucional, bundle OIDC final e eventual E2E critico adicional |
| `RUN-STG-01` primeira janela seria | `pending_execucao` | workflow concluir com artifact, packet, dossie e sign-off revisaveis | `ready_for_validation` | validar `overall status`, classificar excecoes e promover para `done` se tudo estiver `ok` |
| `P1-03` ownership/SLA | `in_progress` | owners aceitos e drill documentado | `ready_for_validation` ou `done` | registrar aceite final pendente, se algum papel ainda nao tiver se manifestado por escrito |
| `P2-01` retention/recovery | `in_progress` | restore revisado com RTO/RPO e aceites coletados | `ready_for_validation` ou `done` | agendar proximo teste recorrente ou ajustar excecoes documentadas |
| `P2-02` janela seria recorrente | `in_progress` | segunda janela comparavel com dossie aceito | `ready_for_validation` ou `done` | institucionalizar cadencia e registrar baseline pos-janela |

### Regra Pratica de Passagem

- se houver artefato valido, mas ainda faltar revisao formal, usar `ready_for_validation`
- se houver artefato valido, revisao formal e documentacao sincronizada, usar `done`
- se houver apenas inicio de execucao sem bundle ou checker final, manter `in_progress`
- se o insumo externo nao chegou ou a prova falhou, manter `blocked` ou retornar para `ready`, conforme o caso

## Matriz de Decisao de Status

Usar esta matriz para classificar os itens sem inflar o progresso por expectativa, preparacao de reuniao ou readiness apenas documental.

| Status | Quando usar | Quando nao usar | Exemplo real no projeto |
| --- | --- | --- | --- |
| `todo` | o item foi reconhecido, mas ainda nao ha insumo minimo, owner confirmado ou janela pratica para iniciar | quando ja existe owner, dependencia conhecida e criterio de evidencia definido | `P3-01` vault/secrets e `P3-02` selagem antes da decisao de tecnologia |
| `ready` | owner existe, dependencia esta clara e a evidencia exigida esta definida; falta apenas insumo externo ou janela de execucao | quando o time ja iniciou execucao real ou quando ainda nao se sabe o que prova fechamento | `P0-02` AML/KYT e `P0-03` feed UE com gates documentados aguardando insumo real |
| `blocked` | existe dependencia externa, institucional ou de ambiente que impede execucao real ou promocao honesta | quando o item ainda pode progredir internamente com trabalho real | `P0-01` OIDC serio enquanto faltam provider real e aceite institucional |
| `in_progress` | ha execucao real em curso, com algum trabalho verificavel ja iniciado, mas ainda sem bundle/checker final que permita validacao completa | quando existe apenas planejamento, ritual ou expectativa de inicio | `RUN-STG-01` depois que o war room sair de preparo para execucao efetiva da janela |
| `ready_for_validation` | a execucao terminou e ja existe saida inicial valida, mas ainda falta revisao formal, sign-off, correlacao final ou doc sincronizada | quando ainda faltam evidencias minimas de execucao | `P0-02` apos checker verde com JSON, antes da revisao final no bundle da janela |
| `done` | criterio de fechamento atingido com artefato revisavel, aceite correspondente e documentacao sincronizada | quando existe apenas screenshot, teste parcial, output verbal ou status presumido | `P1-03` ownership/SLA somente apos owners aprovados, drill documentado e aceite formal |

### Exemplos de Classificacao Correta

- `P0-02` com gate documentado, mas sem credencial real: `ready`
- `P0-02` com checker verde e JSON persistido, aguardando revisao da janela: `ready_for_validation`
- `P0-02` com checker verde, bundle anexado e decisao registrada: `done`
- `P0-01` sem provider real: `blocked`
- `RUN-STG-01` com war room ativo, mas sem dispatch real: `pending_execucao` ou leitura equivalente de preparo; nao promover para `in_progress` sem execucao real
- `RUN-STG-01` com workflow iniciado e artifact parcial: `in_progress`
- `RUN-STG-01` com dossier e sign-off preenchidos, aguardando revisao final: `ready_for_validation`
- `RUN-STG-01` com `overall status=ok`, artifact oficial e docs sincronizadas: `done`

### Anti-Padroes de Classificacao

- marcar `done` porque a documentacao esta pronta, sem execucao correspondente
- marcar `in_progress` so porque a reuniao foi agendada
- marcar `ready_for_validation` sem checker, bundle, dossier ou artefato real
- remover `blocked` sem evidência de que a dependencia externa foi resolvida
- recalibrar KPI sem publicacao correspondente na governanca semanal

## Escalacao Recomendada por Tipo de Bloqueio

| Tipo de bloqueio | Owner de escalação | Acao em ate 24h | Acao em ate 48h |
| --- | --- | --- | --- |
| Credencial AML/KYT ausente | Compliance Lead | cobrar provider e registrar resposta | escalar via COO/CTO |
| URL feed UE ausente | Regulatory/Ops Lead | cobrar provider e registrar resposta | escalar via COO |
| Provider OIDC sem retorno | Security Lead | registrar atraso e manter fallback local so para regressao | escalar via CTO |
| Janela seria sem owners online | Release Manager Tecnico | confirmar disponibilidade nominal | replanejar janela ou declarar `no-go` |
| Restore sem aceite formal | CTO / Security Lead | revisar evidência tecnica | agendar reuniao de sign-off |

## Cronograma Diario Recomendado

### Sprint 7 - Validacao P0

#### Objetivo do ciclo da Sprint 7

sair de `87%` para `88%` ou `89%` com evidencias reais ou bloqueios formalmente explicitados.

#### Sprint 7 - Dia 1

- compartilhar o plano tatico e a baseline com stakeholders
- agendar kickoff da sprint
- confirmar owners nominais de `P0-01`, `P0-02` e `P0-03`
- disparar contato com provider AML/KYT
- disparar contato com provider do feed UE
- disparar contato com provider OIDC

##### Saida esperada do Dia 1

- comunicacao enviada
- kickoff agendado
- prazo de resposta dos provedores registrado

#### Sprint 7 - Dia 2

- executar kickoff Sprint 7
- revisar objetivo de `95%`
- revisar estrutura `P0/P1/P2/P3`
- registrar bloqueios externos
- agendar war room da Sprint 8
- atualizar tracker semanal de owners

##### Saida esperada do Dia 2

- responsaveis confirmados
- dependencias externas registradas
- war room agendada

#### Sprint 7 - Dia 3

- se credenciais AML chegaram: rodar `make check-compliance-provider-runtime`
- se URL UE chegou: exportar `REQUEST_ID="stg-$(date +%F)-eu-check"` e rodar `make gate-p0-03-eu-live WINDOW_ID=stg-$(date +%F)-eu REQUEST_ID="$REQUEST_ID"`
- se OIDC serio chegou: rodar `python scripts/preflight_oidc_serious_env.py`
- se OIDC serio chegou: rodar `python scripts/smoke_auth_oidc_mode.py`
- persistir JSONs, bundles e logs produzidos

##### Saida esperada do Dia 3

- ao menos uma trilha `P0` em `in_progress` ou `ready_for_validation`
- artefatos iniciais persistidos

#### Sprint 7 - Dia 4

- consolidar artefatos de `P0-02` e `P0-03`
- consolidar bundle OIDC quando aplicavel
- revisar se algum item continua `blocked`
- preparar sumario de readiness para a semana

##### Saida esperada do Dia 4

- pacote parcial de evidencias produzido
- bloqueios explicitamente mantidos quando necessario

#### Sprint 7 - Dia 5

- executar revisao semanal baseada em evidencia
- marcar cada item como `blocked`, `in_progress` ou `ready_for_validation`
- anexar links/paths dos artefatos
- confirmar proxima evidencia esperada
- preparar handoff para Sprint 8

##### Saida esperada do Dia 5

- baseline mantida ou recalibrada com prova
- semana encerrada sem status verbal generico

### Sprint 8 - Primeira Janela Seria

#### Objetivo do ciclo da Sprint 8

sair de `88-89%` para `91%` com prova operacional real.

#### Sprint 8 - Dia 1

- revisar se `P0-02` e `P0-03` estao prontos para entrar na janela
- revisar owners online por trilha
- revisar se `.env.staging.private` esta preenchido com valores reais

#### Sprint 8 - Dia 2

- rodar bundles regulatorios e preflights finais
- revisar checklist de evidencia minima
- validar que o war room pode sair de `no-go`

#### Sprint 8 - Dia 3

- executar a primeira janela seria
- preservar logs, packet, dossier e outputs
- registrar excecoes de forma explicita

#### Sprint 8 - Dia 4

- revisar artefatos da janela
- colher sign-off preliminar
- formalizar ownership/SLA
- registrar resultado do drill operacional

#### Sprint 8 - Dia 5

- publicar retrospectiva da janela
- registrar se a janela foi `go`, `go_with_exception` ou `no-go`
- agendar a segunda janela comparavel

### Sprint 9 - OIDC + Recorrencia + Aceites

#### Objetivo do ciclo da Sprint 9

atingir `95%` consolidado com homologacao seria e rotina repetivel.

#### Sprint 9 - Dia 1

- validar provider OIDC serio e claims finais
- repetir `preflight_oidc_serious_env.py`
- repetir `smoke_auth_oidc_mode.py`

#### Sprint 9 - Dia 2

- executar segunda janela seria comparavel
- preservar packet, dossier e relatorio de homologacao OIDC

#### Sprint 9 - Dia 3

- executar teste formal de restore
- registrar RTO/RPO
- validar integridade da trilha de evidencias

#### Sprint 9 - Dia 4

- colher sign-offs de COO, CTO, Security e Compliance
- revisar se todos os gates P0/P2 estao fechados

#### Sprint 9 - Dia 5

- publicar aceites formais consolidados
- recalibrar scorecard
- publicar baseline final do ciclo

## Matriz por Dominio

| Dominio | Forte hoje | Gap principal | Prioridade |
| --- | --- | --- | --- |
| Auth/Identidade | `auth-service`, callback OIDC, contexto federado local | homologacao real de `OIDC + MFA` serio | `P0` |
| Compliance | sanctions, counterparties, blocks, evidencias, work-items | provider real AML/KYT + feed UE + prova recorrente | `P0` |
| Investigation/Billing | fluxo principal e worker real | mais prova seria de runtime e RPC homologado | `P1` |
| Monitoring/Alerting | backlog global, triagem e export auditado | drill, ownership e maturidade de resposta | `P1` |
| Reports/Evidencias | hashes, bundles, downloads auditados, ROS/COAF | institucionalizar custodia e ampliar relatorios formais | `P1/P3` |
| Frontend | cockpits operacionais relevantes | team/IdP real, reports mais ricos, fechamento das areas parciais | `P1` |
| Infra/Ops | preflights, janela seria, runbooks, compose, observabilidade | sign-off, restore formal e recorrencia operacional | `P2` |

## Evidencias Minimas por Bloco

### `P0-01`

- `python scripts/preflight_oidc_serious_env.py`
- `python scripts/smoke_auth_oidc_mode.py`
- `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md`
- `Playwright` critico verde

### `P0-02`

- `make check-compliance-provider-runtime` verde
- `GET /internal/provider-readiness` coerente com `ready=true`
- homologacao AML/KYT com `status=ok`

### `P0-03`

- `artifacts/staging/checks/<janela>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<janela>-eu-sanctions-sync.json`
- `EU_CONSOLIDATED` com `ACTIVE/SUCCESS`

### `RUN-STG-01`

- packet da janela
- dossier final
- sign-off preenchido
- artifact oficial do workflow

### Ownership/SLA

- owners nomeados por dominio
- SLA base aceito
- drill executado
- aceite institucional registrado

### Retention/Recovery

- restore controlado em banco isolado
- validacao de integridade com spot checks
- RTO/RPO documentados
- aceites de Security, Compliance e Platform

## Gates de Go/No-Go

Nao promover um item para `done` quando houver qualquer uma das condicoes abaixo:

- ausencia de artefato real
- ausencia de owner nominal
- ausencia de documentacao canonica sincronizada
- dependencia externa sem resposta ainda nao marcada como `blocked`
- fallback silencioso para `dev auth`
- ausencia de dossier final de janela seria
- ausencia de bundle OIDC quando `P0-01` estiver no escopo
- ausencia de bundle regulatorio quando `P0-02/P0-03` estiverem no escopo

## Metas por Ciclo

| Ciclo | Meta tecnica | Meta regulatoria | Meta consolidada |
| --- | ---: | ---: | ---: |
| Baseline atual | `91%` | `78%` | `87%` |
| Fim Sprint 7 | `91%` | `82-84%` | `88-89%` |
| Fim Sprint 8 | `93-95%` | `85-88%` | `91%` |
| Fim Sprint 9 | `95%` | `95%` | `95%` |

## Recomendacao Final

- manter foco total em `P0`, ownership e recovery ate nova evidencia material
- nao abrir nova frente grande de feature ou replatform no ciclo atual
- nao usar validacao `dev` como prova seria
- tratar a governanca semanal como ritual obrigatorio baseado em evidencia

## Criterio de Encerramento do Ciclo

O ciclo atual so deve ser considerado concluido quando houver:

- `OIDC + MFA` serio homologado
- `AML/KYT` live homologado
- feed UE real homologado
- pelo menos duas janelas serias comparaveis com dossier aceito
- ownership, SLA e retention/recovery com aceite formal
- nova baseline executiva publicada com evidencias anexadas
