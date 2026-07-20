# Registro de Riscos do Projeto

## Objetivo

Consolidar os principais riscos tecnicos, operacionais e regulatorios do Ontrackchain com base no runtime real atual e na documentacao canonica atualizada.

## Resumo Executivo

Leituras oficiais:

- `93%` de construcao tecnica
- `79%` de prontidao regulatoria
- `89%` de construcao total consolidada conforme o [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)

Referencias canonicas da baseline atual:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)

Interpretacao:

- os riscos dominantes deixaram de ser "ausencia de modulo" e passaram a ser homologacao externa, coerencia contratual final e aceite formal de controles

## Registro Atual

| ID | Risco | Categoria | Status Atual | Probabilidade | Impacto | Severidade | Owner Sugerido | Mitigacao |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | MFA federado ainda nao homologado como trilho oficial serio | Auth | mitigado parcialmente | Alta | P0 | Critica | Backend/Auth | homologar o fluxo em janela seria e anexar evidencia |
| R-02 | Provider `AML/KYT` live ainda nao validado com credenciais reais | Compliance | aberto | Alta | P0 | Critica | Compliance/Backend | rodar `make check-compliance-provider-runtime` e a homologacao externa com provider real, anexando bundle e telemetria |
| R-03 | Feed `EU_CONSOLIDATED` depender de URL tokenizada e travar homologacao | Integracao | aberto | Media | P1 | Alta | Compliance/Backend | preencher `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`, reexecutar o worker e anexar os JSONs de `make gate-p0-03-eu-live` com `REQUEST_ID` |
| R-04 | Regressao futura no alinhamento entre catalogo `sanctions_check` e endpoint direto live | Produto/Contrato | mitigado | Baixa | P2 | Baixa | Backend | manter testes de contrato e revisar docs em mudancas de capability |
| R-05 | `due_diligence` e `source_of_funds` seguirem somente em manual review | Compliance | aberto | Media | P1 | Media | Compliance/Product | manter degradacao honesta e definir roadmap de motor homologado |
| R-06 | Novo drift futuro no inventario de eventos da `evidence_trail` voltar a surgir | Governanca | mitigado | Baixa | P2 | Baixa | Backend/Arquitetura | manter source of truth unico e o teste cruzado `test_evidence_event_catalog_sync.py` |
| R-07 | Sign-off de retention/recovery nao ser institucionalizado | Governanca | mitigado parcialmente | Media | P0 | Alta | Security/Platform | obter aceite formal e repetir restore evidenciado |
| R-08 | Janela seria ser executada sem dossier ou ownership completo | Operacao | mitigado parcialmente | Baixa | P1 | Media | Platform/SRE | manter `run_staging_window.py` e checkers como gate obrigatorio |
| R-09 | Screening local de sancoes divergir do estado persistido em `sanctions_lists_meta` | Dados/Integracao | mitigado parcialmente | Media | P1 | Alta | Compliance/Backend | executar `check_sanctions_sync_status.py` apos sync relevante |
| R-10 | Drift documental voltar a subestimar ou superestimar o runtime real | Governanca | mitigado parcialmente | Baixa | P1 | Baixa | Arquitetura/Engenharia | revalidar docs a cada corte regulatorio relevante |
| R-11 | Trilha DD/SoF permanecer sem endurecimento institucional final da selagem forte | Custodia/Compliance | mitigado parcialmente | Media | P1 | Alta | Compliance/Security/Arquitetura | consolidar provider institucional definitivo, trust bundle versionado e eventual prova temporal complementar, preservando a baseline `Opcao B` ja entregue |
| R-12 | RCA cross-domain permanecer eventual e nao entrar no rito recorrente de governanca | Operacao/Governanca | mitigado parcialmente | Media | P2 | Media | Platform/Monitoring + Governanca | usar o playbook canonico, materializar resumo RCA em artefato executivo quando houver incidente e revisar semanalmente sem inflar baseline |

## Top Riscos Atuais

1. `AML/KYT` live ainda nao homologado
2. MFA federado serio ainda nao homologado
3. feed da UE ainda depende de URL tokenizada valida
4. sign-off formal de retention/recovery ainda pendente
5. RCA cross-domain ainda precisa de uso recorrente em ciclo real para deixar de ser apenas endurecimento operacional

Leitura executiva atual dos P0 associados:

- `P0-01` permanece `blocked` enquanto a homologacao formal de identidade nao for anexada
- `P0-02` agora esta `blocked` no estado local real ate `Compliance/AML` concluir handoff e preencher `COMPLIANCE_TRM_SCREENING_URL` + `COMPLIANCE_TRM_API_KEY` reais
- `P0-03` agora esta `blocked` no estado local real ate `Compliance/AML` concluir handoff e preencher `DATABASE_URL` + `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` tokenizada
- `P0-04` tambem esta `blocked` pelo mesmo prerequisito operacional, antes mesmo da correlacao combinada

## Mitigacoes Prioritarias

### Imediatas

- homologar provider `AML/KYT` com `check_compliance_provider_runtime` e bundle externo anexado
- ativar URL tokenizada real da UE com `gate-p0-03-eu-live` e `REQUEST_ID`, preservando os JSONs versionados
- preencher `.env.staging.private` ja materializado em canal seguro, tirar `Compliance/AML` de `pending` e usar `make run-regulatory-unblock-checklist-local` como fila unica de handoff antes de qualquer nova tentativa real

### Curto prazo

- fechar sign-off formal de retention/recovery
- exercitar MFA federado em janela seria real
- institucionalizar a revisao periodica dos artefatos `artifacts/staging/checks/` no sign-off
- endurecer a baseline ja entregue da selagem forte DD/SoF e fechar a cadeia de confianca institucional final
- revisar semanalmente se incidentes cross-domain relevantes tiveram RCA minima registrada, export enriquecido e leitura executiva coerente

## Riscos Emergentes de Operacao Cross-Domain

### R-12. RCA cross-domain ainda sem recorrencia institucional

- estado atual: playbook canonico indexado, RCA leve persistida em `alerts`/`work-items`, leitura read-only em `/monitoring`, export administrativo enriquecido e resumo opcional para governanca executiva
- impacto real: reduz ambiguidade operacional e melhora handoff, mas ainda nao serve como prova recorrente de maturidade enquanto nao aparecer de forma revisavel no ciclo semanal
- bloqueadores atuais:
  - ausencia de serie historica com incidentes reais tratados pelo novo rito
  - falta de uso recorrente do resumo RCA em snapshot/comms de semanas reais
  - dependencia de disciplina operacional para nao deixar a RCA apenas na UI
- mitigacao recomendada:
  - manter o [Playbook Canonico de Incidente Cross-Domain e RCA](./cross-domain-incident-rca-playbook.md) como source of truth do rito
  - registrar RCA minima sempre que houver impacto cross-domain relevante
  - anexar resumo RCA ao artefato executivo quando a semana contiver incidente material

## Riscos Emergentes de Custodia

### R-11. Endurecimento institucional final ainda pendente em DD/SoF

- estado atual: baseline funcional entregue com manifesto, `package_sha256`, sign-off, selagem local, revogacao, supersedencia e verificacao offline basica; ainda falta endurecimento institucional final
- impacto real: nao bloqueia a trilha operacional atual, mas limita o grau maximo de confianca regulatoria enquanto o provider definitivo e o trust bundle institucional nao forem homologados
- bloqueadores atuais:
  - backend criptografico final ainda nao escolhido atras da abstracao aprovada
  - trust model/cadeia de certificados nao aprovado
  - trust bundle versionado ainda nao modelado operacionalmente
  - runbook de evolucao para TSA/ancora externa ainda nao faseado
- mitigacao recomendada:
  - manter `Opcao B` como baseline oficial ja implementada
  - usar `./api-contracts.md` como contrato canônico e `./evidence-manual-package-strong-sealing-architecture.md` como referencia arquitetural
  - manter `package_sha256` como digest principal e proibir updates silenciosos de revogacao/supersedencia

## Criterio para Encerrar um Risco

Um risco so deve ser reduzido quando houver:

- implementacao ou ajuste concluido
- evidencia objetiva em runtime, teste ou janela seria
- atualizacao dos documentos canonicos relacionados
- aceite do owner responsavel quando houver dependencia institucional
