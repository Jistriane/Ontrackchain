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

Execucao real local mais recente, em `2026-07-19`:

- `P0-02`, `P0-03` e `P0-04` foram exercitados via `make check-regulatory-window-readiness`
- os tres retornaram `readiness_status=blocked`
- o scaffold local de `.env.staging.private` ja foi materializado sem secrets reais, entao o bloqueio dominante deixou de ser "arquivo ausente"
- o bloqueio dominante atual continua concentrado em `Compliance/AML.date`, `Compliance/AML.status` e nas variaveis reais pendentes do escopo regulatorio
- em `P0-02`, faltam `COMPLIANCE_TRM_SCREENING_URL` e `COMPLIANCE_TRM_API_KEY`
- em `P0-03`, faltam `DATABASE_URL` e uma `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` real, HTTPS e tokenizada
- em `P0-04`, o bundle combinado segue bloqueado pela soma das pendencias de `P0-02` e `P0-03`
- esta leitura substitui a interpretacao antiga de "`ready` aguardando apenas runtime", porque agora existe evidencia executada de bloqueio operacional real

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
- leitura executiva atual: `P0-01` permanece `blocked` e `P0-02` agora esta `blocked` ate `Compliance/AML` concluir handoff (`date/status`) e preencher `COMPLIANCE_TRM_SCREENING_URL` + `COMPLIANCE_TRM_API_KEY` reais

### 2. Feed da UE

- o desenho tecnico esta pronto
- falta ativacao da URL tokenizada real para fechar a prova em ambiente serio
- leitura executiva atual: `P0-03` agora esta `blocked`, porque a tentativa real local confirmou `Compliance/AML.status/date` pendentes, `DATABASE_URL` ausente e `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` ainda placeholder/nao-tokenizada

### 2.1. Bundle regulatorio combinado

- `P0-04` tambem esta `blocked` no estado atual local
- o bundle combinado nao pode ser tratado como `todo` abstrato enquanto os dois prechecks reais seguem falhando no mesmo dominio de handoff/segredos
- a tentativa local de `2026-07-19` confirmou que o prerequisito dominante do bundle e operacional: handoff humano + preenchimento real das variaveis de `P0-02` e `P0-03` no scaffold privado ja materializado

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

1. preencher `.env.staging.private` materializado em canal seguro e concluir o handoff de `Compliance/AML`
2. homologar `AML/KYT` live
3. ativar feed UE tokenizado real
4. homologar MFA federado como trilho serio oficial
5. obter sign-off formal de retention/recovery e owners
