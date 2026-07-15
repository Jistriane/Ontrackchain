# Rastreabilidade Canonica de Regressao Estatica do Frontend

## Objetivo

Consolidar, em um artefato unico e canonico, quais specs E2E estaticas protegem os contratos visuais e semanticos mais sensiveis dos cockpits operacionais e regulatorios do frontend.

## Escopo

- frontend auditado: `../apps/frontend/app`
- specs canônicas: `../apps/frontend/tests/e2e`
- base de labels/estado UX: `../apps/frontend/app/lib/i18n.ts`
- matriz de contexto funcional: `./frontend-coverage-matrix.md`

## Papel Canonico

Este arquivo e a fonte unica da trilha:

- `cockpit -> spec canonica`
- `cockpit -> contratos protegidos`
- observacoes de rastreabilidade estatica

A matriz [frontend-coverage-matrix.md](./frontend-coverage-matrix.md) permanece como documento de cobertura funcional, rotas reais, lacunas e backlog, sem duplicar a tabela detalhada de rastreabilidade.

## Tabela de Rastreabilidade

| Cockpit | Spec canonica | Contratos protegidos | Observacoes |
| --- | --- | --- | --- |
| `audit` | `../apps/frontend/tests/e2e/audit-labels.spec.ts` | labels amigaveis de acao/recurso, preset do dossie regulatorio, preset dedicado da custodia manual DD/SoF por `request_id` cobrindo `export -> signoff -> seal -> revoke/supersede`, preset explícito de governança pós-selagem via `preset=governanca&request_id=...` ou `preset=governanca&seal_id=...`, com resolução do `request_id` a partir de `seal_id`, precedencia de `dossier_sha256`, precedencia de `package_sha256` para export manual DD/SoF, correlacao da trilha `export -> signoff -> seal -> revoke/supersede` com contexto criptografico do selo institucional, cards temporais do último ciclo observável (`export -> selagem` e `selagem -> governança`), detalhe semântico de governança pós-selagem com `ticket_ref`, `reason`, `superseded_by_seal_id` e timestamps normalizados, deep-links para `reports/ros-coaf/evidence`, incluindo retorno explícito ao evento-fonte DD/SoF em `evidence`, export do dossie oficial e timestamp sem ISO cru | spec focal do contexto regulatorio transversal |
| `ros-coaf` | `../apps/frontend/tests/e2e/roscoaf-regulatory-dossier.spec.ts` | export do dossie oficial, contexto regulatorio, badges semanticos do workspace, historico semantico e normalizacao visual de datas | cockpit com maior densidade regulatoria da trilha atual |
| `evidence` | `../apps/frontend/tests/e2e/evidence-roscoaf-dossier.spec.ts` + `../apps/frontend/tests/e2e/evidence-custody.spec.ts` | hash principal do contexto, contexto regulatorio do dossie, export oficial via `ros_id` resolvido, timestamps do log e datas da cadeia sem ISO cru, alem do contrato manual DD/SoF com manifesto canônico, trilha auditável de export, deep-link explícito para o preset manual do `audit` por `request_id`, deep-link explícito para a governança do selo no `audit` por `seal_id`, banner contextual quando o retorno vem do `audit`, materialização read-only da selagem institucional persistida por `package_sha256` com resumo de quorum/verificação, escrita controlada para inicializar a trilha institucional, registrar sign-offs obrigatórios, finalizar selagem em `ready_to_seal` e executar revogação/supersedência com ticket/motivo | espelha semanticamente o comportamento de `audit` e `ros-coaf`, adicionando cobertura focal para leitura e escrita privilegiada da trilha de selagem forte até a governança pós-selagem |
| `reports` | `../apps/frontend/tests/e2e/reports-history.spec.ts` | historico backend filtravel, labels de tipo, dossie formal, workspace com `priority/source/SLA` e deadline normalizado | protege a identidade operacional hibrida por `reportExternalId` ou `caseId` |
| `cases` | `../apps/frontend/tests/e2e/cases-rbac.spec.ts` + `../apps/frontend/tests/e2e/critical-path.spec.ts` | geração de relatório do case limitada a `ADMIN/ANALYST`, export sensível do bundle limitado a `ADMIN/AUDITOR`, download do artefato comum limitado ao recorte operacional e degradação explícita do `legal_report` fora de `ADMIN` com strong auth | combina spec estática focal de RBAC com fluxo real de geração/download para o trilho principal de investigação |
| `investigate` | `../apps/frontend/tests/e2e/investigation-rbac.spec.ts` | intake operacional com bloqueio preventivo da geração de quote para roles fora de `ADMIN`, `ANALYST` e `OTK_ANALYST`, mantendo geração de quote para papéis operacionais autorizados | cobre a UX preventiva do gateway humano sem alterar o contrato semântico já aplicado no backend/BFF |
| `dashboard` | `../apps/frontend/tests/e2e/alerts-dashboard-context-links.spec.ts` | links contextuais da tabela de casos recentes, status visivel do caso, normalizacao visual de `created_at/completed_at`, CTA rapido de `billing` condicionado ao recorte financeiro e handoff administrativo para `/team` oculto fora de `ADMIN`, inclusive no menu lateral global | compartilha fixture com `alerts` para navegacao operacional e gating leve de atalhos globais |
| `team` | `../apps/frontend/tests/e2e/team-role-labels.spec.ts` | labels amigaveis de role, status visivel do membro e normalizacao visual de `updated_at` na roster table | reaproveita o fluxo de criacao local do roster para provar a tabela sem fixture extra |
| `billing` | `../apps/frontend/tests/e2e/billing-users.spec.ts` | reconciliação financeira, export JSON e handoff explícito para `/team` sem projeção lateral de `team/users` | usa seed de autenticação e mocks das rotas de saldo, auth e operacoes |
| `counterparties` | `../apps/frontend/tests/e2e/timeline-workspace.spec.ts` + `../apps/frontend/tests/e2e/counterparties-rbac.spec.ts` | `source`, revisão DD/SoF, `status`, deadline normalizado, timeline persistida do workspace, degradação explícita da carteira/workspace para roles sem leitura operacional regulatória e ocultação do link lateral global fora do mesmo recorte | usa fixture compartilhada de work-item timeline e hardening focal de RBAC |
| `sanctions` | `../apps/frontend/tests/e2e/timeline-workspace.spec.ts` + `../apps/frontend/tests/e2e/sanctions-rbac.spec.ts` | `source`, `status`, `urgency`, deadline normalizado e timeline persistida do workspace, alem do gating operacional de `sanctions-check` e da humanizacao do `detail` canônico `sanctions_check_role_required` | combina fixture compartilhada de work-item timeline com hardening focal de RBAC no cockpit |
| `blocks` | `../apps/frontend/tests/e2e/timeline-workspace.spec.ts` | `source`, `status`, `urgency`, deadline normalizado e timeline persistida do workspace | usa fixture compartilhada de work-item timeline |
| `alerts` | `../apps/frontend/tests/e2e/alerts-dashboard-context-links.spec.ts` + `../apps/frontend/tests/e2e/alerts-rbac.spec.ts` + `../apps/frontend/tests/e2e/timeline-workspace.spec.ts` | links contextuais por incidente, estado visual de `severity/status/triage`, fila rastreada em `work-items`, timestamps visiveis sem ISO cru, timeline persistida do alerta rastreado e UX preventiva degradando a leitura para `ADMIN/AUDITOR`, com mutacoes ocultas fora de `ADMIN`, link lateral global oculto fora do mesmo recorte e sem flicker sensível antes da resolução do `auth/context` | combina navegacao operacional, hardening focal de RBAC e controller compartilhado de timeline/comments |
| `monitoring` | `../apps/frontend/tests/e2e/monitoring-rbac.spec.ts` | watchlists com `trigger-alert` segregado para QA/Admin, painéis administrativos de `monitoring` e `investigation` degradados para leitura privilegiada `ADMIN/AUDITOR` e mutações administrativas ocultas fora de `ADMIN` | cobre UX preventiva de leitura privilegiada e read-only para `AUDITOR` sem alterar os contratos RBAC já endurecidos no backend/BFF |

## Regras de Leitura

- Se um cockpit usa `timeline-workspace.spec.ts`, a fixture daquele modulo e parte do contrato canonico.
- Quando houver overlap entre cockpits regulatorios, a precedencia documental segue `audit` -> `evidence` -> `ros-coaf` para contexto compartilhado e `ros-coaf` -> `reports` para dossies oficiais.
- a camada compartilhada de persistencia local e normalizacao temporal dos workspaces vive em `apps/frontend/app/lib/workspace-storage.ts`; qualquer regressao em `source`, `deadline` ou ordenacao por atividade deve manter compatibilidade com essa base comum
- Mudancas em `data-testid`, labels semanticas ou formatacao visual de datas devem atualizar este arquivo e `frontend-coverage-matrix.md` na mesma rodada.

## Lacunas Restantes

- A trilha atual cobre os cockpits operacionais/regulatorios principais, mas nao substitui ADRs ou checklist de rollout.
