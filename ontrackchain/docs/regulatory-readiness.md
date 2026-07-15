# Readiness Regulatorio

## Objetivo

Consolidar o estado atual do Ontrackchain frente a um contexto de operacao regulada, com foco em trilha auditavel, sancoes, bloqueio preventivo, onboarding de contrapartes e workflow ROS/COAF.

## Resumo Executivo

Leituras oficiais:

- `79%` de prontidao para operacao regulada forte
- `93%` de construcao tecnica como plataforma funcional
- `89%` de construcao total consolidada conforme o [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)

Referencias canonicas da baseline atual:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)

Interpretacao:

- o projeto ja possui base tecnica regulatoria substancialmente mais madura do que antes
- os maiores gaps deixaram de ser estruturalmente de codigo e passaram a ser de homologacao, aceite formal e integracao real recorrente

## Mapa de Cobertura Atual

| Requisito | Estado Atual | Evidencia | Gap Residual |
| --- | --- | --- | --- |
| Isolamento entre organizacoes | coberto | `RLS` + contexto SQL | ampliar testes negativos especificos |
| Screening de sancoes | coberto parcialmente | cache local + worker + checker pos-sync + runner UE | homologacao recorrente do feed UE tokenizado com URL real |
| Bloqueio preventivo | coberto | `preventive_blocks` + evidencia + audit log | refinamento de operacao/manual review |
| Onboarding regulado de contraparte | coberto | `counterparties` + `counterparty_history` | documentar artefatos de manual review complementares |
| ROS/COAF | coberto | `ros_records` + `reports` + `evidence_trail` | submissao continua manual por desenho |
| Fila operacional compartilhada | coberto | `regulatory_work_items` + `regulatory_work_events/comments` + integracao multi-cockpit com paineis de historico e timeline | aprofundar actions customizadas por owner, escalacao e handoff operacional |
| Auth forte | coberto parcialmente | OIDC + MFA federado previsto | homologacao formal fora do contexto local |
| Billing auditavel | coberto | `credit_ledger` + `audit_logs` | reconciliacao financeira mais rica |
| Cadeia de custodia | coberto parcialmente | `evidence_trail`, manifestos, dossier | sign-off formal e classificacao de evidencias |
| Retention e recovery | coberto parcialmente | politica publicada + restore evidenciado | aceite institucional recorrente |
| Operacao seria | coberto parcialmente | preflights + handoff + dossier | execucao recorrente e aprovadores formais |

## O Que Ja Esta Operacional

### Sancoes

- `sanctions_lists_meta` controla status, hash, source e agenda de sync
- `sanctions_hits_cache` permite screening local
- worker suporta overrides operacionais para OFAC e UE
- `check_sanctions_sync_status.py` valida convergencia pos-sync
- `run_eu_sanctions_window.py` transforma a janela UE em rito leve com artefatos persistidos

### Bloqueio Preventivo

- decisao persistida em `preventive_blocks`
- `lift` protegido por MFA externo homologado
- vinculo com `evidence_trail` e base regulatoria

### Contrapartes

- KYC/KYB, PEP, DD reforcada e periodicidade de revisao
- historico regulado em `counterparty_history`
- hash deterministico de evidencia

### ROS/COAF

- geracao de `coaf_ready_report`
- aprovacao ou rejeicao por operador habilitado
- submissao manual com `coaf_protocol_number` e `coaf_receipt_hash`
- eventos regulatorios correspondentes na trilha de evidencia

### Fila Operacional Compartilhada

- `regulatory_work_items`, `regulatory_work_events` e `regulatory_work_comments` ja existem com `RLS` por organizacao
- `sanctions` sincroniza sua fila operacional no backend e bloqueia com erro explicito quando a fila compartilhada nao estiver disponivel
- `alerts` rastreia incidentes em `work-items` e sincroniza o fechamento do item compartilhado quando ocorre `ack`

## Gaps Regulatorios Reais

### 1. Homologacao externa

- MFA federado ainda nao esta aceito institucionalmente como trilho serio concluido
- `AML/KYT` live ainda depende de credenciais reais, `check-compliance-provider-runtime` verde e prova recorrente
- leitura executiva atual: `P0-01` permanece `blocked` e `P0-02` permanece `ready`

### 2. Feed da UE

- o desenho tecnico esta pronto
- falta ativacao da URL tokenizada real para fechar a prova em ambiente serio
- leitura executiva atual: `P0-03` permanece `ready`, mas nao pode ser promovido sem os JSONs da janela UE

### 3. Cadeia formal de custodia

- artefatos, hashes e manifestos existem
- a trilha forte de selagem DD/SoF ja entrega sign-off institucional por papel, `finalize`, `revoke`, `supersede`, leitura canônica por `package_sha256` e preset de governanca no `audit`
- faltam classificacao formal de sensibilidade recorrente, homologacao do provider institucional definitivo e trust bundle institucional versionado
- contrato HTTP canônico documentado em `./api-contracts.md`
- arquitetura complementar documentada em `./evidence-manual-package-strong-sealing-architecture.md`

### 4. Profundidade operacional da fila compartilhada

- a camada multiusuario ja cobre os cockpits regulatorios principais
- o gap residual saiu de "cobertura de cockpit" e foi para "actions mais profundas", como escalacao, handoff mais rico e governanca por owner

### 5. Manual review estruturado

- `due_diligence` e `source_of_funds` permanecem em `manual_review_required`
- isso e honesto e aceitavel como estado atual, mas limita a prontidao regulatoria plena

## Decisao Atual

- o projeto nao deve ser tratado como pronto para producao regulada
- ele ja deve ser tratado como uma base regulatoria tecnicamente funcional, com foco agora em homologacao, aceite e repetibilidade operacional

## Caminho Mais Eficiente para 85%+

1. homologar `AML/KYT` live
2. ativar feed UE tokenizado real
3. homologar MFA federado como trilho serio oficial
4. obter sign-off formal de retention/recovery e owners
