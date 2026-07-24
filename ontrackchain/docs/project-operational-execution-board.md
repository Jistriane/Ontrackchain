# Board Operacional Unico ate 90%+

## Objetivo

Consolidar a fila operacional diaria do projeto sem drift de taxonomia, usando o mesmo namespace `P0/P1/P2` do board estrategico, dos artefatos de governanca e das trilhas tecnicas realmente executadas no repositorio.

## Papel Canonico

Este board e a fonte canonica unica para:

- status corrente por item `P0/P1/P2`
- owner sugerido ou owner em execucao
- evidencia exigida
- criterio de fechamento
- fila diaria e kanban do ciclo

Nao use este arquivo para redefinir ordem estrategica de ataque. Para a leitura macro do que vem antes do que, use o [Board de Prioridades do Projeto](./project-priority-board.md).

Este documento deve ser lido em conjunto com:

- [Board de Prioridades do Projeto](./project-priority-board.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Registro de Riscos do Projeto](./project-risk-register.md)
- [Governanca Semanal](./governance-weekly/README.md)
- [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md)

## Baseline Atual

- `97%` de construcao tecnica
- `86%` de prontidao regulatoria
- `94%` de maturidade consolidada

## Regras Operacionais

### Status

| Status | Significado |
| --- | --- |
| `todo` | item reconhecido, mas ainda sem insumo ou janela suficiente |
| `ready` | dependencias minimas atendidas; pode entrar em execucao |
| `in_progress` | execucao ativa com evidencia parcial |
| `blocked` | existe dependencia externa, institucional ou de ambiente |
| `ready_for_validation` | execucao concluida, aguardando comprovacao final |
| `done` | criterio de fechamento atingido com evidencia e docs sincronizadas |

### Regra de Fechamento

- sem artefato, o item nao esta `done`
- sem owner, o item nao entra em `in_progress`
- sem atualizacao canônica, o item nao move baseline
- qualquer promocao de maturidade deve obedecer ao [ADR-010](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)

## Fila Prioritaria

### P0 — Move KPI e destrava prontidao seria

| ID | Status | Iniciativa | Owner sugerido | Evidencia exigida | Criterio de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P0-01` | `ready_for_validation` | Homologar `OIDC + MFA` serio | Backend/Auth | preflight + smoke + bundle OIDC + Playwright critico | fluxos sensiveis exigem auth serio e MFA homologado sem fallback |
| `P0-02` | `done` | Homologar `AML/KYT live` | Backend/Compliance | `make check-compliance-provider-runtime-docker` verde + artefato JSON | runtime e artefatos convergem com provider `opensanctions` live sem handoff/segredos pendentes |
| `P0-03` | `done` | Ativar feed UE real | Backend/Compliance | `make check-sanctions-sync-status-docker` verde + JSONs da janela UE | `EU_CONSOLIDATED` valido com source URL tokenizada e sync SUCCESS |
| `P0-04` | `done` | Gerar bundle regulatorio oficial | Platform/SRE | `make check-compliance-provider-runtime-docker` + `make check-sanctions-sync-status-docker` verdes + bundle JSON | prova combinada de compliance runtime (opensanctions live) + EU sanctions (tokenized URL, sync SUCCESS) |
| `P0-05` | `done` | Executar primeira janela seria material | Platform/SRE + Governanca | packet, dossier, war room e sign-off | janela ponta a ponta executada com decisao formal `go/no-go` |
| `P0-06` | `done` | Formalizar sign-off de retention/recovery | Platform/Security | politica, checklist e aceite formal | aceite sincronizado com docs e governanca |
| `P0-07` | `done` | Publicar nova baseline oficial | Arquitetura/Governanca | scorecard + maturity assessment + governanca semanal atualizados | baseline oficial revisada com evidencia coerente |

### P1 — Endurecimento canonico antes da promocao

| ID | Status | Iniciativa | Owner sugerido | Evidencia exigida | Criterio de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P1-01` | `done` | Padronizar metadata de `work-items` | Backend/Compliance + Frontend | contrato comum aplicado em frontend, backend e docs | aliases tolerados e campos canonicos convergem sem drift |
| `P1-02` | `done` | Converter capacidade tecnica em evidencia operacional recorrente | Governanca + Platform/SRE | artefatos recorrentes, owners, handoff e sumarios coerentes | o que ja foi construído passa a aparecer como prova institucional repetivel; o pacote local agora inclui `regulatory-unblock-checklist` no `refresh-staging-war-room-governance-local` |

### P2 — Sustentacao e proximo degrau

| ID | Status | Iniciativa | Owner sugerido | Evidencia exigida | Criterio de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P2-01` | `done` | Definir futuro do modulo `team` | Arquitetura + Produto | decisao documentada ou ADR | escopo do modulo deixa de ser ambiguo |
| `P2-02` | `done` | Consolidar timeline/comments compartilhados | Frontend | `useWorkItemTimeline` adotado nos 7 cockpits | controller compartilhado e E2E canonico estabilizados |
| `P2-03` | `done` | Consolidar RCA cross-domain leve | Platform + Monitoring | playbook + persistencia em `alerts` + leitura em `/monitoring` + export/governanca | RCA deixa de ficar implicita e vira dado reutilizavel |
| `P2-04` | `done` | Implantar estrategia de vault/secrets de producao | Platform/Security | plano aprovado ou implantacao inicial | segredos criticos saem do modelo atual |
| `P2-05` | `done` | Refinar papeis regulatorios por dominio | Security + Produto | docs + testes + enforcement fino em superficies reais | expandir `REVIEWER` e `BILLING_ADMIN` mantendo negacao auditada e UX coerente |
| `P2-06` | `done` | Executar segunda janela seria comparavel | Platform/SRE + Governanca | historico comparavel de dossier | projeto prova repetibilidade alem do primeiro evento |
| `P2-07` | `done` | Atualizar o plano para `95%` | Arquitetura/Governanca | plano trimestral revisado | proximo ciclo fica explicitamente priorizado |

## Kanban Recomendado

### Now

- materializar `.env.staging.private` fora do repositorio
- concluir `Compliance/AML.date/status` em `docs/staging-env-ownership.md`
- `P0-01` executar `make gate-p0-01-oidc-local` — preflight, smoke e Playwright criticos verdes (8/8 OIDC + 80/80 browser-mocked); proximo: bundle OIDC local
- `P1-02` converter capacidade tecnica em evidencia operacional recorrente e manter o `regulatory-unblock-checklist` acoplado ao pacote local de governanca

### Next

- `P0-04` DONE — bundle regulatorio oficial gerado (compliance runtime + EU sanctions ambos OK)
- `P0-05` executar janela seria material
- `P0-06` formalizar retention/recovery
- `P0-07` publicar nova baseline oficial

### Then

- `P0-07` publicar nova baseline oficial

### Post-90

- `P2-04` implantar estrategia de vault/secrets
- `P2-06` executar segunda janela seria comparavel
- `P2-07` atualizar o plano para `95%`

## Gates de Validacao

### Gates P0

- `P0-01`: `make gate-p0-01-oidc-local` verde como preparo local, mais `preflight_oidc_serious_env.py`, `smoke_auth_oidc_mode.py`, bundle `<window>-oidc-readiness-bundle.json` e Playwright critico verdes no trilho serio
- `P0-02`: `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-02` verde antes de `check_compliance_provider_runtime.py` e do artefato anexado
- `P0-03`: `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-03` verde antes de `check_sanctions_sync_status.py` e dos JSONs da janela UE persistidos
- `P0-04`: `make check-regulatory-window-readiness REGULATORY_SCOPE=p0-04` verde antes do bundle regulatorio oficial coerente com `P0-02` + `P0-03`
- `P0-05`: `run_staging_window.py` concluido com packet, dossier, war room e sign-off
- `P0-06`: politica e checklist de retention/recovery atualizados com aceite formal
- `P0-07`: scorecard, maturity assessment e governanca semanal publicados

### Gates P2-05

- backend registra `authorization_denied` com contexto suficiente
- docs de contrato e RBAC ficam sincronizadas no mesmo ciclo
- frontend esconde ou degrada CTAs sem permissao
- `typecheck`, testes focados e diagnosticos permanecem sem regressao

## Metricas do Board

| Metrica | Regra |
| --- | --- |
| `% P0 concluido` | mede prontidao seria e a chance real de cruzar `90%+` |
| `% itens com artefato anexado` | mede confiabilidade da execucao e da governanca |
| `% riscos reclassificados com prova` | mede disciplina de documentacao e aceite |
| `% gates sincronizados com docs` | mede se runtime, contrato e narrativa executiva continuam coerentes |

## Decisao Recomendada

- usar este board como fila unica de execucao diaria ate a promocao para `90%+`
- manter a mesma taxonomia do [Board de Prioridades do Projeto](./project-priority-board.md)
- nao abrir frentes grandes que nao estejam conectadas a um item `P0/P1/P2`
- atualizar o status somente com base em checker, artefato, teste, evidencia operacional ou sign-off
