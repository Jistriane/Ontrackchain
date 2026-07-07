# Registro de Riscos do Projeto

## Objetivo

Consolidar os principais riscos tecnicos, operacionais e regulatorios do Ontrackchain com base no runtime real atual e na documentacao canonica atualizada.

## Resumo Executivo

Leituras oficiais:

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada conforme o [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)

Referencias canonicas da baseline atual:

- [Atualizacao de KPI 2026-07-01](./governance-weekly/archive/weekly/2026-07-01-kpi-scorecard-update.md)
- [Governanca Semanal 2026-07-01](./governance-weekly/archive/weekly/2026-07-01-weekly-governance.md)

Interpretacao:

- os riscos dominantes deixaram de ser "ausencia de modulo" e passaram a ser homologacao externa, coerencia contratual final e aceite formal de controles

## Registro Atual

| ID | Risco | Categoria | Status Atual | Probabilidade | Impacto | Severidade | Owner Sugerido | Mitigacao |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-01 | MFA federado ainda nao homologado como trilho oficial serio | Auth | mitigado parcialmente | Alta | P0 | Critica | Backend/Auth | homologar o fluxo em janela seria e anexar evidencia |
| R-02 | Provider `AML/KYT` live ainda nao validado com credenciais reais | Compliance | aberto | Alta | P0 | Critica | Compliance/Backend | rodar `make check-compliance-provider-runtime` e a homologacao externa com provider real, anexando bundle e telemetria |
| R-03 | Feed `EU_CONSOLIDATED` depender de URL tokenizada e travar homologacao | Integracao | aberto | Media | P1 | Alta | Compliance/Backend | preencher `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`, reexecutar o worker e anexar os JSONs de `make run-eu-sanctions-window-local` |
| R-04 | Regressao futura no alinhamento entre catalogo `sanctions_check` e endpoint direto live | Produto/Contrato | mitigado | Baixa | P2 | Baixa | Backend | manter testes de contrato e revisar docs em mudancas de capability |
| R-05 | `due_diligence` e `source_of_funds` seguirem somente em manual review | Compliance | aberto | Media | P1 | Media | Compliance/Product | manter degradacao honesta e definir roadmap de motor homologado |
| R-06 | Novo drift futuro no inventario de eventos da `evidence_trail` voltar a surgir | Governanca | mitigado | Baixa | P2 | Baixa | Backend/Arquitetura | manter source of truth unico e o teste cruzado `test_evidence_event_catalog_sync.py` |
| R-07 | Sign-off de retention/recovery nao ser institucionalizado | Governanca | mitigado parcialmente | Media | P0 | Alta | Security/Platform | obter aceite formal e repetir restore evidenciado |
| R-08 | Janela seria ser executada sem dossier ou ownership completo | Operacao | mitigado parcialmente | Baixa | P1 | Media | Platform/SRE | manter `run_staging_window.py` e checkers como gate obrigatorio |
| R-09 | Screening local de sancoes divergir do estado persistido em `sanctions_lists_meta` | Dados/Integracao | mitigado parcialmente | Media | P1 | Alta | Compliance/Backend | executar `check_sanctions_sync_status.py` apos sync relevante |
| R-10 | Drift documental voltar a subestimar ou superestimar o runtime real | Governanca | mitigado parcialmente | Baixa | P1 | Baixa | Arquitetura/Engenharia | revalidar docs a cada corte regulatorio relevante |

## Top Riscos Atuais

1. `AML/KYT` live ainda nao homologado
2. MFA federado serio ainda nao homologado
3. feed da UE ainda depende de URL tokenizada valida
4. sign-off formal de retention/recovery ainda pendente

Leitura executiva atual dos P0 associados:

- `P0-01` permanece `blocked` enquanto a homologacao formal de identidade nao for anexada
- `P0-02` permanece `ready`, mas ainda aberto como risco critico ate o gate real do provider ficar verde
- `P0-03` permanece `ready`, mas ainda aberto como risco alto ate a janela UE produzir artefatos anexaveis

## Mitigacoes Prioritarias

### Imediatas

- homologar provider `AML/KYT` com `check_compliance_provider_runtime` e bundle externo anexado
- ativar URL tokenizada real da UE com `run-eu-sanctions-window-local` e JSONs versionados

### Curto prazo

- fechar sign-off formal de retention/recovery
- exercitar MFA federado em janela seria real
- institucionalizar a revisao periodica dos artefatos `artifacts/staging/checks/` no sign-off

## Criterio para Encerrar um Risco

Um risco so deve ser reduzido quando houver:

- implementacao ou ajuste concluido
- evidencia objetiva em runtime, teste ou janela seria
- atualizacao dos documentos canonicos relacionados
- aceite do owner responsavel quando houver dependencia institucional
