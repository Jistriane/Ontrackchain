# Board de Prioridades do Projeto

## Objetivo

Consolidar a visao estrategica das iniciativas que realmente movem o Ontrackchain da baseline atual (`93/79/89`) para um estado regulatoriamente convincente e repetivel, sem drift entre engenharia, governanca e narrativa executiva.

## Papel Canonico

Este board passa a ser a fonte canonica apenas para:

- ordem estrategica de ataque
- racional de priorizacao por `P0/P1/P2`
- leitura macro do que mais move baseline

Nao use este arquivo como fonte primaria para:

- status corrente por item
- owner operacional do ciclo
- evidencia exigida para fechamento
- fila diaria de execucao

Para esses pontos, use o [Board Operacional Unico ate 90%+](./project-operational-execution-board.md).

## Baseline Atual

- `93%` de construcao tecnica
- `79%` de prontidao regulatoria/operacional
- `89%` de maturidade consolidada

Fontes canônicas de referencia:

- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade](./project-maturity-assessment.md)
- [Governanca Semanal](./governance-weekly/README.md)
- [Ciclo Ativo 2026-07-13](./governance-weekly/cycles/2026-07-13/README.md)

## Regra de Taxonomia

- `P0`: itens que movem KPI imediatamente e destravam a subida legitima para `90%+`
- `P1`: endurecimento canônico do modelo operacional e contratual que reduz drift antes da promocao de baseline
- `P2`: sustentacao pos-90, reducao de debito operacional e preparacao do degrau rumo a `95%`

## Prioridades P0

| ID | Prioridade estrategica | Iniciativa | Motivo |
| --- | --- | --- | --- |
| `P0-02` | `agora` | Homologar provider `AML/KYT` live | credencial real + checker verde + bundle revisavel |
| `P0-03` | `agora` | Ativar feed UE tokenizado real e validar `EU_CONSOLIDATED` | URL tokenizada + artefatos persistidos + check coerente |
| `P0-04` | `agora, logo apos P0-02/P0-03` | Gerar bundle regulatorio oficial | consolida `P0-02` + `P0-03` em prova revisavel; tentativas parciais endurecem correlacao, mas nao fecham o item |
| `P0-01` | `na sequencia critica` | Homologar `OIDC` e MFA federado em ambiente serio | fecha o maior risco de identidade; depende de provider externo e aceite institucional |
| `P0-05` | `depois da prova combinada` | Executar primeira janela seria material (`RUN-STG-01`) | transforma preparo documental em execucao auditavel com `go/no-go` formal |
| `P0-06` | `antes da promocao formal` | Formalizar sign-off recorrente de retention/recovery | fecha aceite operacional minimo antes de nova baseline |
| `P0-07` | `fechamento executivo` | Publicar nova baseline oficial | converte evidencia em narrativa executiva e baseline atualizada |

## Prioridades P1

| ID | Prioridade estrategica | Iniciativa | Motivo |
| --- | --- | --- | --- |
| `P1-01` | `consolidado` | Padronizar metadata de `work-items` | contrato unificado entre frontend, backend e `api-contracts.md`, reduzindo drift de ownership/status/aliases |
| `P1-02` | `continuo` | Converter capacidade tecnica em evidencia operacional recorrente | transformar o que ja foi construído em rito repetivel, rastreavel e aceito em governanca |

## Prioridades P2

| ID | Prioridade estrategica | Iniciativa | Motivo |
| --- | --- | --- | --- |
| `P2-05` | `primeiro pos-90` | Refinar RBAC regulatorio por dominio | `REVIEWER` e `BILLING_ADMIN` ja endurecidos em superficies reais; falta expandir para novas superficies |
| `P2-04` | `infraestrutural` | Implantar vault/secrets de producao | elimina segredos criticos em `.env` no trilho de producao |
| `P2-06` | `prova de recorrencia` | Executar segunda janela seria comparavel | prova repetibilidade operacional alem do primeiro `RUN-STG-01` |
| `P2-07` | `replanejamento pos-90` | Atualizar o plano para `95%` | reabre o roadmap com baseline pos-90 consolidada |
| `P2-01` | `produto/escopo` | Definir futuro do modulo `team` | remove ambiguidade de escopo depois do salto para `90%+` |
| `P2-02` | `consolidado` | Consolidar componente compartilhado de timeline/comments | `useWorkItemTimeline` absorve o controller compartilhado nos 7 cockpits |
| `P2-03` | `consolidado` | Consolidar RCA cross-domain leve | playbook canonico indexado, RCA persistida em `alerts`, leitura em `/monitoring` e export/governanca enriquecidos |

## Entregas Consolidadas Relevantes

- `evidence_trail` append-only com `SHA-256`
- `preventive_blocks`
- `counterparties` + `counterparty_history`
- `sanctions_lists_meta` + `sanctions_hits_cache`
- `ROS/COAF` com aprovacao/rejeicao/submissao manual auditada
- `regulatory_work_items` + `regulatory_work_events` + `regulatory_work_comments`
- `P1-01` metadata unificada para `work-items`
- `P2-02` timeline/comments compartilhados em `blocks`, `sanctions`, `alerts`, `counterparties`, `evidence`, `reports` e `ros-coaf`
- `P2-03` RCA cross-domain leve entre `alerts`, `/monitoring`, export administrativo e snapshots executivos
- `P2-05` enforcement fino ja expandido por `team`, `reports`, `billing`, `investigate`, `compliance`, `alerts`, `counterparties` e navegacao global sensivel

## Ordem Recomendada de Ataque

1. fechar `P0-02`
2. fechar `P0-03`
3. consolidar `P0-04`
4. homologar `P0-01`
5. executar `P0-05`
6. formalizar `P0-06`
7. publicar `P0-07`
8. manter `P1-02` como trilha de recorrencia institucional
9. continuar `P2-05` na proxima superficie financeira/regulatoria mais barata e menos arriscada

## Regra de Leitura Conjunta

- este arquivo responde "o que vem antes do que"
- o board operacional responde "quem esta executando, com qual status e qual evidencia falta"
- se houver conflito entre ordem estrategica e status operacional, preservar a ordem deste board e registrar a excecao no board operacional

## KPIs Alvo por Ciclo

| Ciclo | Tecnico | Regulatorio | Total |
| --- | ---: | ---: | ---: |
| Baseline atual | 93% | 79% | 89% |
| Fechamento combinado `P0-02 + P0-03 + P0-04` | 93%+ | 82% | 90%+ |
| Janela seria valida + aceite operacional | 94% | 88% | 92%+ |
| Baseline pos-90 com recorrencia institucional | 95% | 90%+ | 95% |

## Regra de Baseline

- manter `93 / 79 / 89` como referencia executiva ate existir nova evidencia material publicada na governanca semanal
- nao promover `P0-01`, `P0-02` ou `P0-03` sem artefato real, checker verde ou aceite institucional correspondente
- nao considerar tentativa regulatoria parcial como equivalente ao fechamento oficial de `P0-04`
- considerar `P1-01`, `P2-02`, `P2-03` e a fatia atual de `P2-05` como endurecimentos relevantes, mas insuficientes sozinhos para mover o baseline
