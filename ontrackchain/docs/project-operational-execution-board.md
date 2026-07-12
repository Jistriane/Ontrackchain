# Board Operacional Unico ate 90%+

## Objetivo

Consolidar a fila operacional diaria do projeto sem drift de taxonomia, usando o mesmo namespace `P0/P1/P2` do board estrategico, dos artefatos de governanca e das trilhas tecnicas realmente executadas no repositorio.

Este documento deve ser lido em conjunto com:

- [Board de Prioridades do Projeto](./project-priority-board.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Registro de Riscos do Projeto](./project-risk-register.md)
- [Governanca Semanal](./governance-weekly/README.md)
- [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md)

## Baseline Atual

- `92%` de construcao tecnica
- `79%` de prontidao regulatoria
- `88%` de maturidade consolidada

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
| `P0-01` | `blocked` | Homologar `OIDC + MFA` serio | Backend/Auth | preflight + smoke + bundle OIDC + Playwright critico | fluxos sensiveis exigem auth serio e MFA homologado sem fallback |
| `P0-02` | `ready` | Homologar `AML/KYT live` | Backend/Compliance | `check_compliance_provider_runtime.py` verde + artefato JSON | runtime e artefatos convergem com provider `live` |
| `P0-03` | `ready` | Ativar feed UE real | Backend/Compliance | JSONs da janela UE + `check_sanctions_sync_status.py` verde | `EU_CONSOLIDATED` valido com source URL real |
| `P0-04` | `todo` | Gerar bundle regulatorio oficial | Platform/SRE | bundle regulatorio consolidado | prova combinada de `P0-02` + `P0-03` sem erro residual nao classificado |
| `P0-05` | `todo` | Executar primeira janela seria material | Platform/SRE + Governanca | packet, dossier, war room e sign-off | janela ponta a ponta executada com decisao formal `go/no-go` |
| `P0-06` | `todo` | Formalizar sign-off de retention/recovery | Platform/Security | politica, checklist e aceite formal | aceite sincronizado com docs e governanca |
| `P0-07` | `todo` | Publicar nova baseline oficial | Arquitetura/Governanca | scorecard + maturity assessment + governanca semanal atualizados | baseline oficial revisada com evidencia coerente |

### P1 — Endurecimento canonico antes da promocao

| ID | Status | Iniciativa | Owner sugerido | Evidencia exigida | Criterio de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P1-01` | `done` | Padronizar metadata de `work-items` | Backend/Compliance + Frontend | contrato comum aplicado em frontend, backend e docs | aliases tolerados e campos canonicos convergem sem drift |
| `P1-02` | `in_progress` | Converter capacidade tecnica em evidencia operacional recorrente | Governanca + Platform/SRE | artefatos recorrentes, owners, handoff e sumarios coerentes | o que ja foi construído passa a aparecer como prova institucional repetivel |

### P2 — Sustentacao e proximo degrau

| ID | Status | Iniciativa | Owner sugerido | Evidencia exigida | Criterio de fechamento |
| --- | --- | --- | --- | --- | --- |
| `P2-01` | `todo` | Definir futuro do modulo `team` | Arquitetura + Produto | decisao documentada ou ADR | escopo do modulo deixa de ser ambiguo |
| `P2-02` | `done` | Consolidar timeline/comments compartilhados | Frontend | `useWorkItemTimeline` adotado nos 7 cockpits | controller compartilhado e E2E canonico estabilizados |
| `P2-03` | `done` | Consolidar RCA cross-domain leve | Platform + Monitoring | playbook + persistencia em `alerts` + leitura em `/monitoring` + export/governanca | RCA deixa de ficar implicita e vira dado reutilizavel |
| `P2-04` | `todo` | Implantar estrategia de vault/secrets de producao | Platform/Security | plano aprovado ou implantacao inicial | segredos criticos saem do modelo atual |
| `P2-05` | `in_progress` | Refinar papeis regulatorios por dominio | Security + Produto | docs + testes + enforcement fino em superficies reais | expandir `REVIEWER` e `BILLING_ADMIN` mantendo negacao auditada e UX coerente |
| `P2-06` | `todo` | Executar segunda janela seria comparavel | Platform/SRE + Governanca | historico comparavel de dossier | projeto prova repetibilidade alem do primeiro evento |
| `P2-07` | `todo` | Atualizar o plano para `95%` | Arquitetura/Governanca | plano trimestral revisado | proximo ciclo fica explicitamente priorizado |

## Kanban Recomendado

### Now

- `P0-02` homologar `AML/KYT live`
- `P0-03` ativar feed UE real
- `P0-01` destravar owner e ambiente de `OIDC + MFA` serio
- `P1-02` converter capacidade tecnica em evidencia operacional recorrente

### Next

- `P0-04` gerar bundle regulatorio oficial
- `P2-05` continuar RBAC fino pela proxima superficie de menor risco

### Then

- `P0-05` executar janela seria material
- `P0-06` formalizar retention/recovery
- `P0-07` publicar nova baseline

### Post-90

- `P2-04` implantar estrategia de vault/secrets
- `P2-06` executar segunda janela seria comparavel
- `P2-07` atualizar o plano para `95%`

## Gates de Validacao

### Gates P0

- `P0-01`: `preflight_oidc_serious_env.py`, `smoke_auth_oidc_mode.py`, bundle `<window>-oidc-readiness-bundle.json` e Playwright critico verdes
- `P0-02`: `check_compliance_provider_runtime.py` verde com artefato anexado
- `P0-03`: `check_sanctions_sync_status.py` verde com JSONs da janela UE persistidos
- `P0-04`: bundle regulatorio oficial coerente com `P0-02` + `P0-03`
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
