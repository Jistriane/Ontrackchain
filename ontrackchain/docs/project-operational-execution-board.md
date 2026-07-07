# Board Operacional Unico ate 90%+

## Objetivo

Consolidar uma fila unica de execucao para levar o Ontrackchain da baseline atual para `90%+` de maturidade consolidada com:

- prioridades `P0/P1/P2`
- status operacional padronizado
- dependencias explicitas
- owners sugeridos
- evidencia exigida por item
- criterio de fechamento auditavel

Este documento e a referencia diaria do ciclo atual. Ele deve ser lido em conjunto com:

- [Board de Prioridades do Projeto](./project-priority-board.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Kit de Execucao por Evidencia](./project-maturity-evidence-execution-kit.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Registro de Riscos do Projeto](./project-risk-register.md)
- [Governanca Semanal](./governance-weekly/README.md)
- [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md)

## Baseline Atual

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada

Baseline canonica de referencia:

- [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Governanca Semanal 2026-07-01](./governance-weekly/archive/weekly/2026-07-01-weekly-governance.md)
- [Atualizacao de KPI 2026-07-01](./governance-weekly/archive/weekly/2026-07-01-kpi-scorecard-update.md)

## Regras Operacionais

### Status

| Status | Significado |
| --- | --- |
| `todo` | item reconhecido, mas ainda sem insumo ou janela suficiente |
| `ready` | dependencias minimas atendidas; pode entrar em execucao |
| `in_progress` | execucao ativa com evidencia parcial |
| `blocked` | existe dependencia externa, institucional ou de ambiente |
| `ready_for_validation` | implementacao ou rito concluido, aguardando comprovacao final |
| `done` | criterio de fechamento atingido com evidencia e docs sincronizadas |

### Regra de Movimento

| Transicao | Condicao minima |
| --- | --- |
| `todo -> ready` | owner sugerido, dependencia conhecida e evidencia esperada definidas |
| `ready -> in_progress` | credencial, janela, ambiente ou capacidade efetiva disponiveis |
| `in_progress -> ready_for_validation` | comando, integracao ou rito concluido com saida inicial valida |
| `ready_for_validation -> done` | checker/artefato/sign-off verde + risco reclassificado + doc canonica atualizada |

### Regra de Fechamento

- sem artefato, o item nao esta `done`
- sem owner, o item nao entra em `in_progress`
- sem atualizacao canônica, o item nao move baseline
- usar `blocked` sempre que a pendencia depender de credencial, owner externo ou aceite institucional
- qualquer promocao de maturidade deve obedecer ao [ADR-010](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)
- usar [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md) como trilha de cobrança por owner para os itens `P0` e para a governanca de subida ate `95%`

## Fila Prioritaria

### P0 — Move KPI e destrava prontidao seria

| ID | Status Inicial | Iniciativa | Owner Sugerido | Dependencias | Evidencia Exigida | Impacto no KPI | Criterio de Fechamento |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-01` | `blocked` | Homologar `OIDC + MFA serio` | Backend/Auth | owner IdP, ambiente serio, claims finais | `preflight_oidc_serious_env.py` verde, `smoke_auth_oidc_mode.py` verde, bundle `<window>-oidc-readiness-bundle.json`, Playwright critico verde | muito alto | fluxos sensiveis exigem auth serio e MFA homologado sem fallback silencioso |
| `P0-02` | `ready` | Homologar `AML/KYT live` | Backend/Compliance | credencial real do provider | `check_compliance_provider_runtime.py` verde + artefato JSON | muito alto | readiness interna e API publica convergem com provider `live` |
| `P0-03` | `ready` | Ativar feed UE real | Backend/Compliance | URL tokenizada valida | JSONs da janela UE + `check_sanctions_sync_status.py` verde | muito alto | `EU_CONSOLIDATED` fica valido e os artefatos da janela sao persistidos |
| `P0-04` | `todo` | Gerar bundle regulatorio oficial | Platform/SRE | `P0-02`, `P0-03` | `<window>-regulatory-readiness-bundle.json` | muito alto | bundle reflete AML/KYT + sancoes UE sem erro residual nao classificado |
| `P0-05` | `todo` | Executar primeira janela seria material | Platform/SRE + Governanca | `P0-01` a `P0-04` | packet, dossier, bundles OIDC/regulatorio quando aplicaveis, war room e sign-off | muito alto | janela ponta a ponta executada com decisao formal `go/no-go` |
| `P0-06` | `todo` | Formalizar sign-off de retention/recovery | Platform/Security | resultado da janela, owner formal | aceite formal ou excecao registrada | alto | politica, checklist e aceite ficam sincronizados |
| `P0-07` | `todo` | Publicar nova baseline oficial | Arquitetura/Governanca | `P0-05`, `P0-06` | scorecard e maturity assessment atualizados | muito alto | projeto cruza `90%+` com narrativa e evidencia coerentes |

### Leitura Sugerida no Inicio do Dia 1

| Item | Status sugerido | Racional operacional | Condicao para mudar |
| --- | --- | --- | --- |
| `P0-01` | `blocked` | ainda depende de owner IdP, ambiente serio e validacao externa de MFA | mover para `in_progress` so quando houver owner confirmado e trilho serio verificavel |
| `P0-02` | `ready` | a trilha ja tem owner e checker definido, mas ainda depende de credencial real | mover para `in_progress` quando a credencial AML/KYT estiver disponivel para execucao |
| `P0-03` | `ready` | a trilha ja tem owner e rito claro, mas ainda depende de URL tokenizada real da UE | mover para `in_progress` quando a URL real estiver confirmada no ambiente |
| `P0-04` | `todo` | depende diretamente da conclusao operacional de `P0-02` e `P0-03` | mover para `ready` apenas depois que `P0-02` e `P0-03` estiverem ao menos em `ready_for_validation` |

Regra pratica para o Dia 1:

- manter `P0-01` em `blocked` se o impedimento ainda for institucional ou externo
- promover `P0-02` e `P0-03` para `in_progress` somente se houver insumo real, nao apenas intencao
- nao antecipar `P0-04` antes da existencia de artefatos reais das trilhas de compliance

### P1 — Fecha operacao multiusuario e institucionalizacao

| ID | Status Inicial | Iniciativa | Owner Sugerido | Dependencias | Evidencia Exigida | Impacto no KPI | Criterio de Fechamento |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P1-01` | `todo` | Padronizar `metadata` de `work-items` | Backend/Compliance + Frontend | nenhuma | contrato comum aplicado nos modulos | alto | modulos usam o mesmo modelo conceitual de metadata |
| `P1-02` | `todo` | Fechar `blocks` multiusuario | Frontend | `P1-01` | timeline/comments + origem `server/local` explicita | alto | `blocks` usa backend como primario e distingue rascunho local de item persistido |
| `P1-03` | `todo` | Fechar `ros-coaf` multiusuario | Frontend | `P1-01` | historico operacional completo do ROS | alto | fluxo `generated -> approved/rejected -> submitted` fica auditavel na UI |
| `P1-04` | `todo` | Fechar `evidence` multiusuario | Frontend | `P1-01` | evento com timeline/comments persistidos | alto | `evidence` vira cockpit compartilhado, nao apenas visor local |
| `P1-05` | `todo` | Fechar `reports` multiusuario | Frontend | `P1-01` | cockpit operacional por caso | medio | relatorios formais exibem owner, SLA, timeline e handoff |
| `P1-06` | `todo` | Fechar `counterparties` multiusuario | Frontend | `P1-01` | owner/review/handoff persistidos | medio | coordenacao entre analistas sai de memoria local |
| `P1-07` | `todo` | Rebaixar `localStorage` para fallback explicito | Frontend | `P1-02` a `P1-06` | `server > local draft` visivel na UX | alto | dado local nao mascara indisponibilidade ou falta de persistencia |
| `P1-08` | `todo` | Revisar risk register pos-janela | Arquitetura/Governanca | `P0-05` | riscos reclassificados com prova | alto | riscos refletem evidencias reais, nao expectativa |
| `P1-09` | `todo` | Institucionalizar janela seria recorrente | Governanca + Platform/SRE | `P0-05` | rito aprovado ou segunda execucao comparavel | alto | war room, handoff e sign-off deixam de ser evento isolado |
| `P1-10` | `todo` | Publicar governanca semanal consolidada | Governanca | `P0-07` | snapshot executivo versionado | alto | baseline, riscos e proximos passos ficam publicados no ciclo correto |
| `P1-11` | `todo` | Revisar priority board pos-90% | Arquitetura/Governanca | `P0-07` | board refletindo o proximo ciclo | medio | backlog deixa de priorizar gaps ja fechados |

### P2 — Sustentacao e proximo degrau

| ID | Status Inicial | Iniciativa | Owner Sugerido | Dependencias | Evidencia Exigida | Impacto no KPI | Criterio de Fechamento |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `P2-01` | `todo` | Definir futuro do modulo `team` | Arquitetura + Produto | baseline pos-90% | decisao documentada ou ADR | medio | escopo do modulo deixa de ser ambiguo |
| `P2-02` | `todo` | Consolidar componente compartilhado de timeline/comments | Frontend | `P1-02` a `P1-06` | reducao visivel de duplicacao | medio | cockpit compartilhado reaproveita o mesmo padrao de UX |
| `P2-03` | `todo` | Evoluir alertas e RCA cross-domain | Platform + Monitoring | `P0-05` | fluxo RCA reforcado | medio | monitoramento e resposta ganham rastreabilidade entre dominios |
| `P2-04` | `todo` | Implantar estrategia de vault/secrets de producao | Platform/Security | `P0-06` | plano aprovado ou implantacao inicial | alto | segredos criticos saem do modelo atual para trilha mais forte |
| `P2-05` | `todo` | Refinar papeis regulatorios por dominio | Security + Produto | pos-90% | matriz RBAC revisada | medio | papeis de operacao ficam mais granulares e auditaveis |
| `P2-06` | `todo` | Executar segunda janela seria comparavel | Platform/SRE + Governanca | `P1-09` | historico comparavel de dossier | alto | projeto prova repetibilidade e nao apenas um evento isolado |
| `P2-07` | `todo` | Atualizar o plano para `95%` | Arquitetura/Governanca | `P0-07` | plano trimestral revisado | medio | proximo ciclo fica explicitamente priorizado |

## Ordem Recomendada de Ataque

1. `P0-02` homologar `AML/KYT live`
2. `P0-03` ativar feed UE real
3. `P0-01` destravar e homologar `OIDC + MFA serio`
4. `P0-04` gerar bundle regulatorio oficial
5. `P1-01` padronizar `metadata` de `work-items`
6. `P1-02` e `P1-03` fechar `blocks` e `ros-coaf`
7. `P1-04`, `P1-05` e `P1-06` fechar `evidence`, `reports` e `counterparties`
8. `P1-07` rebaixar fallback local para cache explicito
9. `P0-05` executar primeira janela seria material
10. `P0-06` formalizar retention/recovery
11. `P0-07` publicar nova baseline
12. `P1-08`, `P1-09`, `P1-10` e `P1-11` consolidar governanca do novo ciclo

## Quadro Kanban Recomendado

### Now

- `P0-02` homologar `AML/KYT live`
- `P0-03` ativar feed UE real
- `P0-01` destravar owner e ambiente de `OIDC + MFA serio`

Rito recomendado para execucao imediata:

- Refira-se ao [Board de Prioridades do Projeto](./project-priority-board.md) para itens atuais
- Rastreie progresso em [Governanca Semanal](./governance-weekly/README.md)
- Use [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md) para cobrar artefatos, aceite e evidência por owner

### Next

- `P0-04` gerar bundle regulatorio oficial
- `P1-01` padronizar `metadata` de `work-items`
- `P1-02` fechar `blocks`
- `P1-03` fechar `ros-coaf`

### Then

- `P1-04` fechar `evidence`
- `P1-05` fechar `reports`
- `P1-06` fechar `counterparties`
- `P1-07` rebaixar fallback local

### Later

- `P0-05` executar janela seria material
- `P0-06` formalizar retention/recovery
- `P0-07` publicar nova baseline
- `P1-08` revisar risk register
- `P1-09` institucionalizar janela recorrente
- `P1-10` publicar governanca semanal consolidada
- `P1-11` revisar priority board

### Post-90

- `P2-01` definir futuro do modulo `team`
- `P2-02` consolidar componente compartilhado de timeline/comments
- `P2-03` evoluir alertas e RCA cross-domain
- `P2-04` implantar estrategia de vault/secrets
- `P2-05` refinar papeis regulatorios por dominio
- `P2-06` executar segunda janela seria comparavel
- `P2-07` atualizar o plano para `95%`

## Gates de Validacao

### Gates P0

- `P0-01`: `preflight_oidc_serious_env.py`, `smoke_auth_oidc_mode.py`, bundle `<window>-oidc-readiness-bundle.json` e Playwright critico verdes
- `P0-02`: `check_compliance_provider_runtime.py` verde com artefato anexado
- `P0-03`: `check_sanctions_sync_status.py` verde com JSONs da janela UE persistidos
- `P0-04`: bundle regulatorio gerado sem erro residual nao classificado
- `P0-05`: `run_staging_window.py` concluido com packet, dossier, war room e sign-off
- `P0-06`: politica e checklist de retention/recovery atualizados com aceite formal
- `P0-07`: scorecard, maturity assessment e governanca semanal publicados

### Gates P1 de Frontend

- backend e a fonte primaria
- owner, prioridade, SLA e status aparecem na UI
- timeline fica visivel
- comments ficam persistidos
- origem `server/local` fica explicita
- `npm run typecheck` permanece verde
- regressao critica do fluxo principal e validada

## Metricas do Board

| Metrica | Regra |
| --- | --- |
| `% P0 concluido` | mede prontidao seria e a chance real de cruzar `90%+` |
| `% cockpits server-primary` | mede a reducao de ilhas locais nos modulos regulatorios |
| `% itens com artefato anexado` | mede confiabilidade da execucao e da governanca |
| `% riscos reclassificados com prova` | mede disciplina de documentacao e aceite |
| `% sign-offs criticos concluídos` | mede institucionalizacao da operacao |

## Decisao Recomendada

- usar este board como fonte unica de priorizacao do ciclo ate `90%+`
- nao abrir frentes grandes que nao estejam conectadas a um item `P0/P1/P2`
- manter `91% / 78% / 87%` como baseline executiva ate nova evidencia material publicada na governanca semanal
- usar [Avaliacao Consolidada de Status do Projeto](./assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md) como leitura executiva de suporte para status, subida para `95%` e parecer formal de `go/no-go`
- atualizar o status somente com base em checker, artefato, teste, evidencia operacional ou sign-off
