# Board de Prioridades do Projeto

## Objetivo

Consolidar a visao estrategica das iniciativas necessarias para levar o Ontrackchain de runtime tecnicamente maduro (`92%`) para operacao regulatoriamente convincente e repetivel (`95%+`).

## Baseline Atual

- `92%` de construcao tecnica
- `79%` de prontidao regulatoria
- `88%` de construcao total consolidada

Baseline canonica de referencia:

- [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md)
- [Governanca Semanal](./governance-weekly/README.md)
- [Ciclo Ativo 2026-07-13](./governance-weekly/cycles/2026-07-13/README.md)
- [Governanca Semanal 2026-07-06](governance-weekly/cycles/2026-07-06/2026-07-06-weekly-governance.md): ultimo registro fechado de referencia
- [Tracking Sprint 4 Dia 5](governance-weekly/archive/sprint-tracking/2026-07-07-sprint-4-day-5-tracking.md)

Leitura executiva:

- a baseline institucionalizada passa a ser `92/79/88`
- o maior ganho remanescente nao vem de scaffold novo, mas de homologacao externa, readiness operacional e aceite institucional
- as frentes de frontend e operacao passaram a focar hardening, decomposicao de cockpits densos e reducao de drift documental
- o ciclo vivo de decisao humana passa por `docs/governance-weekly/cycles/2026-07-13/`, enquanto `2026-07-06` permanece como ultimo corte fechado

## Prioridades P0 — Move KPI e destrava prontidao regulatoria

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P0-01 | blocked | Homologar `OIDC` e MFA federado em ambiente serio | fecha o maior risco de identidade; depende de provider externo e aceite institucional |
| P0-02 | ready | Homologar provider `AML/KYT` live | credencial real + `make check-compliance-provider-runtime` verde + bundle JSON |
| P0-03 | ready | Ativar feed UE tokenizado real e validar `EU_CONSOLIDATED` | URL tokenizada + `make run-eu-sanctions-window-local` + JSONs persistidos |

## Prioridades P1 — Hardening de Cockpits Operacionais

| ID | Status | Iniciativa | Modulo | Motivo |
| --- | --- | --- | --- | --- |
| P1-S5-01 | done | Integrar timeline/comments em `blocks` | `/blocks` | cockpit multiusuario completo com work-item server-first |
| P1-S5-02 | done | Integrar timeline/comments em `sanctions` | `/sanctions` | `WorkItemTimelinePanel` + i18n pt-BR/en/es + botao "Ver timeline" por linha |
| P1-S5-03 | done | Integrar timeline/comments em `alerts` | `/alerts` | `WorkItemTimelinePanel` vinculado ao `trackedWorkItem` + i18n pt-BR/en/es |
| P1-S5-04 | done | timeline/comments ja existem em `ros-coaf` | `/ros-coaf` | `WorkItemTimelinePanel` integrado e assignment por `owner_user_id` habilitado |
| P1-S5-05 | done | timeline/comments ja existem em `counterparties` | `/counterparties` | `WorkItemTimelinePanel` integrado + DD/SoF review estruturado (campos, metadata, i18n tri-locale) |
| P1-S5-06 | done | timeline/comments ja existem em `evidence` | `/evidence` | `WorkItemTimelinePanel` ja integrado; cadeia de custodia expandida pendente |
| P1-S5-07 | done | timeline/comments e listagem backend oficial em `reports` | `/reports` | `WorkItemTimelinePanel` integrado + `GET /api/v1/reports` com paginação/filtros e proxy frontend `/api/app/reports/list` |

## Prioridades P2 — Governanca Formal (Trimestre 2)

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P2-01 | in_progress | Formalizar sign-off de retention/recovery | transforma baseline em controle institucionalmente aceito |
| P2-02 | in_progress | Executar janela seria recorrente com dossier aceito | sai de validacao pontual para rotina com historico comparavel |
| P2-03 | done | Estruturar artefatos de manual review para DD/SoF | `counterparties` agora possui painel de DD/SoF com campos `ddReviewStatus`, `sofDescription`, `sofDocumentRef`, `ddReviewNote` persistidos em work-item |
| P2-04 | todo | Formalizar owners, SLA e runbooks com aceite | `operational-ownership-and-slas.md` com aprovacoes institucionais |

## Prioridades P3 — Cadeia de Custodia Forte (Trimestre 3)

| ID | Status | Iniciativa | Motivo |
| --- | --- | --- | --- |
| P3-01 | todo | Implantar vault/secrets de producao | eliminar segredos em `.env` em ambiente de producao |
| P3-02 | in_progress | Endurecer cadeia de custodia com selagem institucional homologada | baseline forte DD/SoF ja entregue; falta provider institucional definitivo, trust bundle versionado e eventual TSA/ancora externa |
| P3-03 | todo | Formalizar war room, escalacao e RCA cross-domain | playbook de incident response repetivel |
| P3-04 | todo | Automatizar promocao superior com menos passos manuais | reduzir fricao no fluxo `staging -> producao` |

## Itens Ja Consolidados

- `evidence_trail` append-only com `SHA-256`
- `preventive_blocks`
- `counterparties` + `counterparty_history`
- `sanctions_lists_meta` + `sanctions_hits_cache`
- `ROS/COAF` com aprovacao/rejeicao/submissao manual auditada
- `regulatory_work_items` + `regulatory_work_events` + `regulatory_work_comments`
- `check_sanctions_sync_status.py`
- `check_compliance_provider_runtime.py`
- `run_eu_sanctions_window.py` + targets `make run-eu-sanctions-window*`
- janela seria com `run_staging_window.py` + war room + dossier
- alinhamento `sanctions_check` catalogo x endpoint direto live
- inventario de eventos `evidence_trail` com source of truth unico
- baseline `92/79/88` institucionalizada na documentacao viva e pronta para publicacao no proximo ciclo semanal
- timeline/comments integrada em `ros-coaf`, `evidence`, `counterparties`, `reports`, `blocks`
- timeline/comments integrada em todos os cockpits parciais: `blocks`, `sanctions`, `alerts`, `ros-coaf`, `evidence`, `counterparties`, `reports`

## Sequenciamento Recomendado do Proximo Ciclo

As entregas de timeline/workspace ja estao institucionalizadas. O sequenciamento residual recomendado e:

1. ~~`DD/SoF manual review estruturado`~~: **entregue** — painel dedicado em `/counterparties`
2. ~~`listagem de casos rastreados em reports`~~: **entregue** — painel de histórico client-side em `/reports`
3. ~~`historico de sanctions por endereco`~~: **entregue** — painel de histórico em `/sanctions`
4. ~~`workspace de evidencias rastreadas`~~: **entregue** — painel de histórico em `/evidence`
5. ~~`historico de blocks, ros-coaf e alerts`~~: **entregue** — paineis de histórico em `/blocks`, `/ros-coaf` e `/alerts`
6. `cadeia de custodia expandida em evidence`: baseline funcional entregue; manter P3 aberto apenas para endurecimento institucional (provider homologado, trust bundle e prova temporal complementar)

Estado atual do rollout de ownership:

- assignment formal por `owner_user_id` consolidado nos cockpits: `blocks`, `sanctions`, `alerts`, `ros-coaf`, `counterparties`, `evidence` e `reports`

Em paralelo, se credencial/URL disponivel:

- P0-02: `make check-compliance-provider-runtime`
- P0-03: `make run-eu-sanctions-window-local`

## KPIs Alvo por Ciclo

| Ciclo | Tecnico | Regulatorio | Total |
| --- | ---: | ---: | ---: |
| Baseline atual | 92% | 79% | 88% |
| Sprint 5 + P0-02/03 (T1) | 92%+ | 82% | 90%+ |
| T2 (governanca aceita) | 93% | 88% | 92%+ |
| T3 (custodia forte) | **95%** | 90%+ | **95%** |

## Regra de Baseline

- manter `92% / 79% / 88%` como referencia executiva ate existir nova evidencia material publicada na governanca semanal
- usar [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md) como parecer executivo padrao para comunicacao com stakeholders e decisoes de `go/no-go`
- usar [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md) quando a necessidade for comunicar sequenciamento executivo ou proxima frente de entrega
- nao promover `P0-01`, `P0-02` ou `P0-03` sem artefato real, checker verde ou aceite institucional correspondente
- nao marcar `P1-S5-*` como `done` sem o `WorkItemTimelinePanel` operacional e chaves de i18n completas no modulo
