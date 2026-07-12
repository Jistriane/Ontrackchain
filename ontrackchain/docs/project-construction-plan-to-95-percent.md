# Plano Consolidado de Construcao ate 95%

## Objetivo

Converter a baseline atual do Ontrackchain em um plano executavel para sair de:

- `92%` de construcao tecnica
- `79%` de prontidao regulatoria/operacional
- `88%` de maturidade consolidada

e atingir a meta de `95%` de maturidade consolidada com criterio auditavel, evidencias anexaveis e promocao disciplinada por governanca.

Este plano nao substitui os documentos canônicos ja existentes. Ele os consolida em uma trilha unica de execucao.

## Fontes Canonicas

- `./project-kpi-scorecard.md`
- `./project-maturity-assessment.md`
- `./project-executive-readiness-brief.md`
- `./project-operational-execution-board.md`
- `./EXECUTION_CHECKLIST_TO_95_PERCENT.md`
- `./project-weekly-governance-runbook.md`
- `./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md`

## Leitura Executiva

O projeto ja nao tem o seu gargalo principal em construcao de software interno.

O caminho ate `95%` depende principalmente de:

1. homologacao externa com insumos reais;
2. execucao de janelas serias com evidencias persistidas;
3. sign-off formal de ownership, SLA, retention e recovery;
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
| Arquitetura backend | forte | servicos, dados, auditoria e work-items ja sustentam operacao assistida |
| Frontend operacional | forte | cockpits e contratos visuais ja nao sao o gargalo principal; `P2-03` ja adiciona RCA leve em `alerts`/`monitoring` sem abrir novo servico |
| Integracoes externas | parcial | `OIDC`, `AML/KYT`, feed UE e RPC serio ainda dependem de prova real |
| Governanca e staging | parcial | runbooks e workflows existem, incluindo resumo opcional de RCA cross-domain, mas falta recorrencia homologada |
| Sign-offs institucionais | fraco/parcial | owners, SLA, retention e recovery ainda travam promocao |

## Gaps que Impedem 95%

### Gaps P0

- `P0-01` homologar `OIDC + MFA serio`
- `P0-02` homologar `AML/KYT live`
- `P0-03` ativar feed UE real
- `P0-04` gerar bundle regulatorio oficial
- `P0-05` executar primeira janela seria material
- `P0-06` formalizar sign-off de retention/recovery
- `P0-07` publicar nova baseline oficial

### Gaps de Governanca

- owners por dominio ainda precisam de aceite formal
- SLA por severidade ainda precisa de aprovacao institucional
- restore controlado e `RTO` real ainda precisam de evidencia formal
- falta completar `2` janelas serias comparaveis com dossier e sign-off

### Gaps Tecnicos Residenciais

- `public-api` ainda e parcial e nao move a meta de `95%`
- `billing` e `team` continuam administrativos e nao sao bloqueadores primarios
- DD/SoF seguem dependentes de fluxo humano, o que e aceitavel para `95%`, mas nao para maturidade plena futura
- `P2-03` ja endurece triagem, export e governanca com RCA leve cross-domain, mas ainda nao possui serie recorrente suficiente para mover baseline sozinho

## Estrategia Recomendada

### Estrategia Escolhida

`External Readiness First`

### Racional

- maximiza impacto no KPI com o menor risco de refactor desnecessario;
- trata o ponto real de bloqueio: prova operacional e homologacao externa;
- respeita o `ADR-010`, que proibe promocao por narrativa sem evidencia;
- usa o frontend e o backend ja construidos como plataforma de prova, nao como proximo alvo de grandes mudancas.

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

- `P0-02` e `P0-03` saem de `ready` para `in_progress`
- `P0-01` sai de `blocked` para `ready` ou `in_progress`

### Fase 2 - Homologacao de Integracoes Vivas

Objetivo: executar as trilhas P0 com insumos reais e coletar evidencias anexaveis.

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

### Fase 3 - Bundle e Governanca Formal

Objetivo: transformar readiness tecnica em readiness institucional.

Entregas:

- bundle regulatorio oficial gerado
- tentativas regulatorias parciais tratadas como endurecimento de correlacao, dossier e narrativa executiva, sem confundir esse progresso com o fechamento oficial de `P0-04`
- owners por dominio aprovados
- SLA por severidade aprovado
- retention e recovery com restore evidenciado e aceite formal
- war room matrix fechada

Owners primarios:

- COO / Governanca
- CTO / Platform / DBA
- Security
- Compliance

Criterio de saida:

- `P0-04` e `P0-06` concluidos
- documentacao de ownership, SLA e recovery sincronizada

Regra da fase:

- se apenas `P0-02` ou `P0-03` estiver disponivel em uma janela, o resultado pode fortalecer a trilha operacional e reduzir risco executivo
- a promocao oficial do bundle regulatorio continua exigindo convergencia revisavel de `P0-02` e `P0-03` na mesma trilha
- se houver incidente cross-domain material na semana, registrar RCA minima e resumo executivo como endurecimento operacional; isso melhora handoff e leitura de risco, mas nao substitui nenhum gate P0

### Fase 4 - Primeira Janela Seria Material

Objetivo: executar uma janela ponta a ponta com evidencias reais e decisao formal.

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
- Governanca
- Security
- Compliance

Criterio de saida:

- `P0-05` concluido com artefato revisavel
- sinais operacionais cross-domain, quando existirem, aparecem de forma coerente em war room, snapshot e comms

### Fase 5 - Segunda Janela Comparavel

Objetivo: provar recorrencia operacional, nao apenas um evento isolado.

Entregas:

- segunda janela seria executada sob o mesmo rito
- comparativo entre as duas execucoes
- confirmacao de estabilidade de handoff, evidencias e checklist
- uso recorrente e revisavel do resumo RCA quando houver incidente cross-domain relevante

Owners primarios:

- Platform/SRE
- Governanca
- Ops Manager

Criterio de saida:

- criterio de `2` janelas serias comparaveis satisfeito

### Fase 6 - Promocao Oficial para 95%

Objetivo: recalibrar o estado oficial do projeto com base em evidencias reais.

Entregas:

- `project-kpi-scorecard.md` atualizado
- `project-maturity-assessment.md` atualizado
- `project-operational-execution-board.md` atualizado
- governanca semanal publicada com nova baseline
- assessment formal ou parecer executivo atualizado

Owners primarios:

- Arquitetura
- Governanca
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
- corrigir falhas de integracao e persistencia de artefatos
- se a semana terminar com apenas uma trilha regulatoria disponivel, registrar a tentativa parcial como preparo da consolidacao, sem contar `P0-04` como fechado

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
| sign-off institucional lento | governanca | alto | agendar aprovacao como deliverable e nao como atividade paralela |
| apenas uma janela executada | maturidade | alto | nao promover baseline antes da segunda janela |

## Definition of Done para 95%

- `AML/KYT live` validado com provider real
- feed UE real validado com artefatos persistidos
- `P0-04` fechado apenas com bundle oficial coerente entre `P0-02` e `P0-03`; tentativa parcial nao substitui esse gate
- `OIDC + MFA` homologados em trilho serio
- owners e SLA formalmente aceitos
- retention e recovery com evidencia e aceite
- pelo menos `2` janelas serias comparaveis executadas
- scorecard e baseline oficial publicados
- RCA cross-domain, quando houver incidente material, registrada de forma revisavel sem ser usada como atalho para promocao artificial de baseline

## O que Nao Deve Mover o KPI Sozinho

- refinamento visual adicional no frontend
- RCA leve persistida apenas em UI/export, sem uso recorrente e revisao humana no ciclo
- fortalecimento documental sem execucao real
- testes locais sem homologacao externa
- aceite verbal sem sign-off registrado
- uma unica execucao bem-sucedida sem recorrencia

## Uso Recomendado

- usar este plano como narrativa executiva central do caminho ate `95%`
- usar `EXECUTION_CHECKLIST_TO_95_PERCENT.md` como cobranca por owner
- usar `project-operational-execution-board.md` como fila diaria
- usar a governanca semanal para mover status e recalibrar risco

## Proxima Acao Recomendada

Executar um kick-off de `D1-D2` com a seguinte pauta:

1. nomear owners reais de `P0-01`, `P0-02` e `P0-03`
2. confirmar insumos externos disponiveis
3. fechar data da primeira janela seria
4. confirmar criteria de sign-off de Security, Compliance e Platform
