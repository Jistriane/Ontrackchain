# Plano Consolidado de Construcao ate 95%

## Objetivo

Converter a baseline atual do Ontrackchain em um plano executavel para sair de:

- `97%` de construcao tecnica
- `90%` de prontidao regulatoria/operacional
- `93%` de maturidade consolidada

e atingir a meta de `95%` de maturidade consolidada com criterio auditavel, evidências anexaveis e promocao disciplinada por governanca.

Este documento passa a ser a fonte canônica unica da trilha de execucao ate `95%`.

Ele consolida:

- a narrativa executavel do caminho ate `95%`
- os gates operacionais de promocao
- o checklist executivo de cobranca
- a operacionalizacao por owner

O arquivo legado `EXECUTION_CHECKLIST_TO_95_PERCENT.md` permanece apenas como ponte de compatibilidade para links antigos.

## Fontes canônicas

- `./project-kpi-scorecard.md`
- `./project-maturity-assessment.md`
- `./project-executive-readiness-brief.md`
- `./project-operational-execution-board.md`
- `./project-weekly-governance-runbook.md`
- `./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md`

## Leitura Executiva

O projeto ja nao tem o seu gargalo principal em construcao de software interno.

Com P0-01 a P0-07 concluidos, a baseline atual e:

- `97%` tecnico
- `90%` regulatorio/operacional
- `93%` consolidado

O caminho ate `95%` depende principalmente de:

1. execucao de P2-06 (segunda janela seria) - CONCLUIDO;
2. atualizacao do plano para 95% - EM ANDAMENTO;
3. consolidação operacional continua;
4. recalibracao oficial do scorecard e da baseline.

## Meta de 95%

Para cruzar `95%` consolidado usando a formula oficial do projeto, a meta operacional recomendada passa a ser:

- `96-97%` tecnico
- `91-92%` regulatorio/operacional
- `95%` consolidado

Racional:

- a parte tecnica ja esta alta e deve subir pouco com ajustes de homologacao e robustez;
- o maior salto precisa acontecer na camada regulatoria e operacional, hoje ainda presa por dependencias externas e falta de prova recorrente.

## Estado Atual por Frente

| Frente | Estado atual | Leitura executiva |
| --- | --- | --- |
| Arquitetura backend | forte | servicos, dados, auditoria e work-items ja sustentam operação assistida |
| Frontend operacional | forte | cockpits e contratos visuais ja nao sao o gargalo principal; `P2-03` ja adiciona RCA leve em `alerts`/`monitoring` sem abrir novo servico |
| integrações externas | parcial | `OIDC`, `AML/KYT`, feed UE e RPC serio ainda dependem de prova real |
| governança e staging | parcial | runbooks e workflows existem, incluindo resumo opcional de RCA cross-domain, mas falta recorrencia homologada |
| Sign-offs institucionais | fraco/parcial | owners, SLA, retention e recovery ainda travam promocao |

## Gaps que Impedem 95%

### Gaps P0

- `P0-01` homologar `OIDC + MFA serio`
- `P0-02` homologar `AML/KYT live`
- `P0-03` ativar feed UE real
- `P0-04` gerar bundle regulatório oficial
- `P0-05` executar primeira janela seria material
- `P0-06` formalizar sign-off de retention/recovery
- `P0-07` publicar nova baseline oficial

### Gaps de governança

- owners por dominio ainda precisam de aceite formal
- SLA por severidade ainda precisa de aprovacao institucional
- restore controlado e `RTO` real ainda precisam de evidência formal
- falta completar `2` janelas serias comparaveis com dossier e sign-off

### Gaps Tecnicos Residenciais

- `public-api` ainda e parcial e nao move a meta de `95%`
- `billing` e `team` continuam administrativos e nao sao bloqueadores primarios
- DD/SoF seguem dependentes de fluxo humano, o que e aceitavel para `95%`, mas nao para maturidade plena futura
- `P2-03` ja endurece triagem, export e governança com RCA leve cross-domain, mas ainda nao possui serie recorrente suficiente para mover baseline sozinho

## Estrategia Recomendada

### Estrategia Escolhida

`External Readiness First`

### Racional

- maximiza impacto no KPI com o menor risco de refactor desnecessario;
- trata o ponto real de bloqueio: prova operacional e homologacao externa;
- respeita o `ADR-010`, que proibe promocao por narrativa sem evidência;
- usa o frontend e o backend ja construidos como plataforma de prova, nao como próximo alvo de grandes mudancas.

## Plano por Fases

### Fase 1 - Desbloqueio Externo

Objetivo: remover dependencias externas que hoje mantem o projeto artificialmente abaixo de `95%`.

Entregas:

- provider oficial de `OIDC + MFA` definido
- credencial real de `AML/KYT` disponivel
- URL tokenizada real do feed UE disponivel
- placeholders e handoffs da janela seria reduzidos a zero

Owners primarios:

- Security/Auth Lead
- Compliance Lead
- Regulatory/Ops Manager
- Platform/SRE

Criterio de saida:

- `.env.staging.private` existe fora do repositorio com ownership/handoff concluido
- `P0-02` e `P0-03` saem de `blocked` para `in_progress` somente depois do `check-regulatory-window-readiness` verde
- `P0-01` sai de `blocked` para `ready` ou `in_progress`

### Fase 2 - Homologacao de integrações Vivas

Objetivo: executar as trilhas P0 com insumos reais e coletar evidências anexaveis.

Entregas:

- `check_compliance_provider_runtime.py` verde com JSON persistido
- janela UE com `preflight` e `sync` persistidos
- `preflight_oidc_serious_env.py` verde
- `smoke_auth_oidc_mode.py` verde
- `test:e2e:oidc-critical` verde

Owners primarios:

- Compliance Lead
- Security/Auth Lead
- Platform/SRE
- Tech Lead / QA

Criterio de saida:

- `P0-01`, `P0-02` e `P0-03` ficam ao menos em `ready_for_validation`

### Fase 3 - Bundle e governança Formal

Objetivo: transformar readiness tecnica em readiness institucional.

Entregas:

- bundle regulatório oficial gerado
- tentativas regulatorias parciais tratadas como endurecimento de correlacao, dossier e narrativa executiva, sem confundir esse progresso com o fechamento oficial de `P0-04`
- owners por dominio aprovados
- SLA por severidade aprovado
- retention e recovery com restore evidenciado e aceite formal
- war room matrix fechada

Owners primarios:

- COO / governança
- CTO / Platform / DBA
- Security
- Compliance

Criterio de saida:

- `P0-04` e `P0-06` concluidos
- documentação de ownership, SLA e recovery sincronizada

Regra da fase:

- se apenas `P0-02` ou `P0-03` estiver disponivel em uma janela, o resultado pode fortalecer a trilha operacional e reduzir risco executivo
- a promocao oficial do bundle regulatório continua exigindo convergencia revisável de `P0-02` e `P0-03` na mesma trilha
- se houver incidente cross-domain material na semana, registrar RCA minima e resumo executivo como endurecimento operacional; isso melhora handoff e leitura de risco, mas nao substitui nenhum gate P0

### Fase 4 - Primeira Janela Seria Material

Objetivo: executar uma janela ponta a ponta com evidências reais e decisao formal.

Entregas:

- `window packet`
- `dossier`
- bundles OIDC/regulatorio
- snapshot de status da janela
- war room log
- sign-off formal `go/no-go`
- resumo RCA cross-domain anexado quando houver incidente material na mesma janela ou no mesmo ciclo

Owners primarios:

- Platform/SRE
- governança
- Security
- Compliance

Criterio de saida:

- `P0-05` concluido com artefato revisável
- sinais operacionais cross-domain, quando existirem, aparecem de forma coerente em war room, snapshot e comms

### Fase 5 - Segunda Janela Comparavel

Objetivo: provar recorrencia operacional, nao apenas um evento isolado.

Entregas:

- segunda janela seria executada sob o mesmo rito
- comparativo entre as duas execucoes
- confirmacao de estabilidade de handoff, evidências e checklist
- uso recorrente e revisável do resumo RCA quando houver incidente cross-domain relevante

Owners primarios:

- Platform/SRE
- governança
- Ops Manager

Criterio de saida:

- criterio de `2` janelas serias comparaveis satisfeito

### Fase 6 - Promocao Oficial para 95%

Objetivo: recalibrar o estado oficial do projeto com base em evidências reais.

Entregas:

- `project-kpi-scorecard.md` atualizado
- `project-maturity-assessment.md` atualizado
- `project-operational-execution-board.md` atualizado
- governança semanal publicada com nova baseline
- assessment formal ou parecer executivo atualizado

Owners primarios:

- Arquitetura
- governança
- CTO
- COO

Criterio de saida:

- baseline oficial publicada em `95%`

## Roadmap Sugerido

### Semana 1

- definir owners P0 nominais
- obter credenciais e URLs reais
- fechar placeholders e handoffs do staging serio
- validar agenda da primeira janela

### Semana 2

- executar `P0-02`
- executar `P0-03`
- corrigir falhas de integração e persistencia de artefatos
- se a semana terminar com apenas uma trilha regulatoria disponivel, registrar a tentativa parcial como preparo da consolidação, sem contar `P0-04` como fechado

### Semana 3

- executar `P0-01`
- gerar bundles de readiness
- fechar sign-offs tecnicos preliminares

### Semana 4

- executar primeira janela seria
- executar segunda janela comparavel ou agendar a segunda dentro do mesmo ciclo
- atualizar scorecard e baseline se todos os gates estiverem fechados

## Criticos de Caminho

| Item | Tipo | Impacto | Mitigacao |
| --- | --- | --- | --- |
| provider `OIDC + MFA` nao definido | externo | muito alto | escalar decisao de IAM como bloqueador executivo |
| credencial AML/KYT indisponivel | externo | muito alto | tratar como dependencia P0 diaria com owner claro |
| URL UE real indisponivel | externo | alto | escalar para Regulatory/Ops e registrar `blocked` formal |
| placeholders no staging serio | operacional | alto | gate pre-janela obrigatorio |
| sign-off institucional lento | governança | alto | agendar aprovacao como deliverable e nao como atividade paralela |
| apenas uma janela executada | maturidade | alto | nao promover baseline antes da segunda janela |

## Definition of Done para 95%

- `AML/KYT live` validado com provider real
- feed UE real validado com artefatos persistidos
- `P0-04` fechado apenas com bundle oficial coerente entre `P0-02` e `P0-03`; tentativa parcial nao substitui esse gate
- `OIDC + MFA` homologados em trilho serio
- owners e SLA formalmente aceitos
- retention e recovery com evidência e aceite
- pelo menos `2` janelas serias comparaveis executadas
- scorecard e baseline oficial publicados
- RCA cross-domain, quando houver incidente material, registrada de forma revisável sem ser usada como atalho para promocao artificial de baseline

## O que Nao Deve Mover o KPI Sozinho

- refinamento visual adicional no frontend
- RCA leve persistida apenas em UI/export, sem uso recorrente e revisao humana no ciclo
- fortalecimento documental sem execucao real
- testes locais sem homologacao externa
- aceite verbal sem sign-off registrado
- uma unica execucao bem-sucedida sem recorrencia

## Uso Recomendado

- usar este plano como narrativa executiva central e checklist operacional canônico do caminho ate `95%`
- usar `EXECUTION_CHECKLIST_TO_95_PERCENT.md` apenas como ponte legada de compatibilidade
- usar `project-operational-execution-board.md` como fila diaria
- usar a governança semanal para mover status e recalibrar risco

## Proxima Acao Recomendada

Executar um kick-off de `D1-D2` com a seguinte pauta:

1. nomear owners reais de `P0-01`, `P0-02` e `P0-03`
2. confirmar insumos externos disponiveis
3. fechar data da primeira janela seria
4. confirmar criteria de sign-off de Security, Compliance e Platform

## Checklist Executivo canônico

| Bloco | Owner principal | Estado alvo | evidência de fechamento |
| --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | `ready_for_validation` ou `done` | readiness `p0-02` verde + checker verde + JSON persistido |
| `P0-03` feed UE real | Regulatory/Ops | `ready_for_validation` ou `done` | readiness `p0-03` verde + preflight/sync JSON + validação |
| `P0-04` bundle regulatório oficial | Platform/SRE | `ready_for_validation` ou `done` | readiness `p0-04` verde + bundle regulatório coerente + validador final; tentativa parcial alimenta o dossier, mas nao encerra o item |
| `P0-01` `OIDC + MFA` | Security/Auth Lead | `ready_for_validation` ou `done` | preflight + smoke + E2E |
| `P0-05` primeira janela seria material | Release Manager / Platform | `ready_for_validation` ou `done` | packet + dossier + war room + sign-off |
| `P0-06` retention e recovery | CTO / Security / Compliance | `done` | restore evidenciado + aceite |
| `P1-02` owners, SLA e janela recorrente | COO / Ops / Platform | `done` | aceite formal + rito recorrente institucionalizado |
| `P2-01` futuro do modulo team | Arquitetura + Produto | `done` | ADR-015 criado com definicao de escopo |
| `P2-03` RCA cross-domain leve | Platform/SRE + Monitoring | `done` | playbook + persistencia + export |
| `P2-04` vault/secrets producao | Platform/Security | `done` | ADR-016 criado com estrategia em 3 camadas |
| `P2-05` RBAC por dominio | Security + Produto | `done` | enforcement completo, 80/80 testes passando |

## Gates Operacionais de Promocao

### Gate `89% -> 90%`

- [ ] existe pelo menos uma prova revisável completa de `P0-02` ou `P0-03`
- [ ] o artefato esta persistido e referenciado na governança semanal
- [ ] o risco correspondente foi reavaliado como menor ou explicitamente melhor delimitado

### Gate `90% -> 90%+`

- [ ] `P0-02` possui checker verde com credencial real e JSON persistido
- [ ] `P0-03` possui JSONs validos da janela UE e checker coerente
- [ ] `P0-04` consolida o bundle regulatório oficial com `P0-02` e `P0-03` na mesma trilha revisável; tentativa parcial isolada nao substitui esse gate
- [ ] `P0-05` transforma a prova combinada em pacote executivo revisável
- [ ] a leitura executiva foi atualizada sem depender apenas de narrativa

### Gate de Sustentacao Institucional

- [ ] `P0-01` reduziu materialmente o risco de identidade com provider real e sem fallback silencioso
- [ ] `RUN-STG-01` deixou de ser somente preparacao e passou a ter trilha objetiva para `go/no-go`
- [ ] `P0-06` e `P1-02` possuem aceite ou excecao formal registrada
- [ ] quando houver incidente cross-domain material, a RCA minima foi registrada e a leitura executiva deixou claro se houve apenas endurecimento operacional ou artefato revisado

## Checklist por Owner

### Compliance Lead

#### `P0-02` Homologar `AML/KYT live`

- [ ] solicitar credencial real do provider
- [ ] obter `api_key`, endpoint e requisitos de autenticação
- [ ] preencher o segredo no ambiente privado correto
- [ ] executar `make check-compliance-provider-runtime`
- [ ] validar que o checker ficou verde
- [ ] persistir o artefato JSON do check
- [ ] registrar aceite operacional do provider como `ready`

Fechamento minimo:

- checker verde
- JSON persistido
- evidência revisada em governança semanal

#### `P1` Aceites regulatórios

- [ ] revisar o runbook do provider AML/KYT
- [ ] confirmar se a evidência coletada e suficiente para recorrencia
- [ ] registrar aceite de compliance quando `P0-02` e janela real estiverem validos

### Regulatory/Ops Manager

#### `P0-03` Ativar feed UE tokenizado real

- [ ] solicitar URL tokenizada real do feed UE
- [ ] validar reachability e formato de resposta
- [ ] preencher o segredo no ambiente privado correto
- [ ] executar `make gate-p0-03-eu-live` com `WINDOW_ID` e `REQUEST_ID`
- [ ] validar `eu-sanctions-preflight.json`
- [ ] validar `eu-sanctions-sync.json`
- [ ] anexar os JSONs na trilha de governança

Fechamento minimo:

- URL real validada
- JSONs persistidos
- status do sync aceito em governança

#### Janela seria e war room

- [ ] agendar war room
- [ ] confirmar owners reais por dominio
- [ ] garantir coverage de placeholders e handoff
- [ ] preparar packet, dossier e sign-off da janela
- [ ] executar a primeira janela seria com artefato anexavel
- [ ] organizar a segunda janela para provar recorrencia
- [ ] quando houver incidente material no ciclo, confirmar `work_item_id`, RCA minima e resumo RCA coerente com war room/comms

### Security/Auth Lead

#### `P0-01` Homologar `OIDC + MFA`

- [ ] definir provider oficial
- [ ] obter `client_id`, `client_secret`, issuer e claims necessarios
- [ ] configurar o ambiente local/serio
- [ ] executar `python scripts/preflight_oidc_serious_env.py`
- [ ] executar `python scripts/smoke_auth_oidc_mode.py`
- [ ] executar `npm run test:e2e:oidc-critical` com preflight explicito do ambiente OIDC serio
- [ ] validar MFA federado sem fallback silencioso
- [ ] anexar bundle ou evidência equivalente

Fechamento minimo:

- preflight verde
- smoke verde
- E2E critico verde
- evidência de autenticação forte homologada

#### `P1` Owners e segurança operacional

- [ ] revisar envolvimento obrigatorio de Security em incidentes `P0/P1`
- [ ] aprovar formalmente owners e SLA sensiveis
- [ ] aprovar retention, descarte e cadeia de custodia quando os testes estiverem completos

### CTO / Platform / DBA

#### Retention e recovery

- [ ] validar politica publicada
- [ ] confirmar owners tecnicos de backup e restore
- [ ] executar restore controlado em base isolada
- [ ] medir `RTO`
- [ ] validar integridade minima pos-restore
- [ ] registrar evidência do teste
- [ ] obter aceite formal de Platform/DBA

Fechamento minimo:

- restore executado
- `RTO` registrado
- evidência anexada
- aceite tecnico formal

### COO / governança

#### Owners e SLA

- [ ] validar owners por dominio
- [ ] validar backups operacionais
- [ ] aprovar SLA por severidade
- [ ] registrar aceite formal de ownership
- [ ] validar que o documento esta referenciado nos gates de release

Fechamento minimo:

- owners aprovados
- SLA aprovado
- aceite formal registrado

### Tech Lead / QA

#### Validação cruzada da trilha P0

- [ ] consolidar `.env` privado apenas no ambiente correto
- [ ] executar bundle regulatório quando `P0-02` e `P0-03` estiverem prontos
- [ ] validar artefatos gerados
- [ ] registrar qualquer delta entre readiness documental e runtime
- [ ] manter a suite principal de regressao verde
- [ ] se apenas uma trilha regulatoria estiver disponivel, registrar explicitamente o resultado como endurecimento parcial, sem promover `P0-04` artificialmente

Fechamento minimo:

- bundle consistente
- evidências revisadas
- regressao verde

#### `P2-03` evidência complementar de RCA cross-domain

- [ ] confirmar se houve incidente cross-domain material na semana
- [ ] registrar `work_item_id` do alerta rastreado quando aplicavel
- [ ] validar que a RCA minima foi persistida no `work-item`
- [ ] validar que houve comentario automatico de timeline quando a RCA mudou materialmente
- [ ] validar se o resumo RCA entrou em export/comms/snapshot quando aplicavel
- [ ] registrar explicitamente se o resultado conta apenas como endurecimento operacional ou como artefato executivo revisado

Fechamento minimo:

- RCA minima registrada
- leitura executiva coerente com o artefato
- sem promocao artificial de baseline

## Regras para Dizer que o Projeto Chegou a `95%`

- [ ] `AML/KYT live` validado com provider real
- [ ] feed UE real validado com artefatos persistidos
- [ ] `OIDC + MFA` homologados em trilho serio
- [ ] owners e SLA formalmente aceitos
- [ ] retention e recovery com evidência e aceite formal
- [ ] pelo menos `2` janelas serias comparaveis executadas com dossier e sign-off
- [ ] incidentes cross-domain materiais, quando existirem, possuem RCA revisável sem serem usados como atalho para mover score

## Regras para Nao Promover Artificialmente

- [ ] nao subir `P0-01`, `P0-02` ou `P0-03` sem artefato real
- [ ] nao considerar aceite verbal como sign-off formal
- [ ] nao confundir validação local com homologacao externa
- [ ] nao usar documentação forte para esconder ausencia de prova operacional
- [ ] nao considerar tentativa regulatoria parcial como equivalente ao fechamento oficial de `P0-04`
- [ ] nao usar RCA leve em UI/export/governanca como substituto de gate regulatório ou de recorrencia operacional
