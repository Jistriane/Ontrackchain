# Cobertura do Frontend

## Objetivo

Registrar de forma canonica o que ja esta construido no frontend, o que esta parcial e o que ainda nao possui tela propria, cruzando as rotas reais do App Router com os fluxos documentados em `api-contracts.md`.

## Escopo Auditado

- frontend auditado: `../apps/frontend/app`
- componentes de shell relevantes: `../apps/frontend/components/ui.tsx`
- contratos comparados: `./api-contracts.md`
- base de labels/estado UX: `../apps/frontend/app/lib/i18n.ts`

## Rotas Reais Encontradas

| Rota | Arquivo | Status |
| --- | --- | --- |
| `/` | `../apps/frontend/app/page.tsx` | pronta |
| `/login` | `../apps/frontend/app/login/page.tsx` | pronta |
| `/oidc/callback` | `../apps/frontend/app/oidc/callback/page.tsx` | pronta |
| `/dashboard` | `../apps/frontend/app/dashboard/page.tsx` | parcial |
| `/counterparties` | `../apps/frontend/app/counterparties/page.tsx` | parcial |
| `/sanctions` | `../apps/frontend/app/sanctions/page.tsx` | parcial |
| `/blocks` | `../apps/frontend/app/blocks/page.tsx` | parcial |
| `/ros-coaf` | `../apps/frontend/app/ros-coaf/page.tsx` | parcial |
| `/reports` | `../apps/frontend/app/reports/page.tsx` | parcial |
| `/evidence` | `../apps/frontend/app/evidence/page.tsx` | parcial |
| `/team` | `../apps/frontend/app/team/page.tsx` | parcial |
| `/alerts` | `../apps/frontend/app/alerts/page.tsx` | parcial |
| `/investigate` | `../apps/frontend/app/investigate/page.tsx` | pronta |
| `/cases/[id]` | `../apps/frontend/app/cases/[id]/page.tsx` | pronta |
| `/audit` | `../apps/frontend/app/audit/page.tsx` | pronta |
| `/monitoring` | `../apps/frontend/app/monitoring/page.tsx` | pronta |
| `/billing` | `../apps/frontend/app/billing/page.tsx` | parcial |

## Matriz de Cobertura por Modulo

| Modulo | Cobertura atual | Evidencia no frontend | Lacuna principal |
| --- | --- | --- | --- |
| Home institucional | pronta | leitura autenticada de catalogos e resumo do ecossistema | nao substitui telas operacionais dedicadas |
| Login `dev` | pronta | login JWT local, erro tratado e transicao para 2FA | sem lacuna relevante para o escopo atual |
| Login OIDC | pronta | `auth/config`, redirect seguro e callback dedicado | depende da homologacao externa do provedor |
| Dashboard operacional | parcial | shell, metricas reais, atalhos operacionais, casos recentes com ações para case/audit/evidence/reports/sanctions/blocks e cards de modulos ativos | ainda depende de snapshots/admin para parte dos KPIs e nao possui endpoint agregado proprio |
| Investigacao | pronta | `estimate -> start -> redirect case` | sem wizard expandido para addons, compliance ou block actions |
| Case e relatorios | pronta | polling de status, geracao e download de PDF | nao separa fluxos regulatorios mais fortes em tela dedicada |
| Auditoria | pronta | filtros, paginacao, detalhe expandido, export de evidencias e ações contextuais para case/evidence/reports/investigate/sanctions/blocks/counterparties/ROS | ainda depende dos metadados emitidos pelos eventos para abrir todos os atalhos contextuais |
| Monitoramento | pronta | watchlists, worker, DLQ, alertas operacionais, export e deep-links para case/audit/evidence | ainda concentra funcoes que gradualmente migraram para modulos dedicados |
| Billing e usuarios | parcial | saldo real, resumo operacional, atalhos para reports/monitoring/alerts e roster local filtrável com deep-link para equipe | nao entrega gestao real de usuarios, equipe, roles ou tenant |
| Reports formais | parcial | rota dedicada com catálogo real, filtros reidratáveis por query string, seleção de tipo preferido, fila compartilhada por `case_id` via `work-items` com fallback local e ações para case/audit/evidence/investigate | ainda sem listagem backend oficial de relatórios gerados por `report_id`, timeline/comentários na UI e geração formal orquestrada fim a fim |
| Contrapartes | parcial | rota dedicada com listagem paginada, onboarding regulado inicial, prefill via query string e workspace local persistido com ações para case/audit/evidence/sanctions | ainda sem historico backend, revisao detalhada e workflow multiusuario persistido no servidor |
| Sancoes | parcial | rota dedicada com verificação, triagem operacional, deep-link com prefill/autostart, ações para case/audit/evidence/blocks e sincronização da fila compartilhada via `work-items` como fonte primária com fallback local | ainda sem histórico backend oficial por endereço/caso, timeline/comentários expostos na UI e assignment formal por `owner_user_id` |
| Trilha de evidencias | parcial | rota dedicada com filtros, correlacao por chaves, export de bundle, workspace compartilhado por `event_id` via `work-items` com fallback local e ações contextuais por evento para case/audit/reports/investigate/sanctions/blocks/counterparties/ROS reaproveitando `audit/logs` e `evidence-export` | ainda sem timeline/comentários de `work-items` na UI, cadeia de custodia expandida por caso e assignment formal por `owner_user_id` |
| Central de alertas | parcial | rota dedicada reaproveitando o painel de incidentes globais com filtros, ack, export, abertura por query string, ações por incidente para case/audit/evidence/investigate/sanctions e rastreamento em `work-items` com sincronização de encerramento via `ack` | ainda sem timeline/comentários de `work-items` na UI e sem integração full com incident response |
| ROS/COAF | parcial | rota dedicada com geracao, aprovacao/rejeicao, submissao manual, workspace local persistido, prefill via query string e ações para case/audit/evidence/download | ainda sem listagem backend oficial por prazo, SLA e filas operacionais |
| Preventive blocks / lift | parcial | rota dedicada com avaliacao, lift assistido via MFA externo, fila compartilhada para `preventive_block` persistido com fallback local antes do `block_id` existir e ações para case/audit/evidence/ROS | ainda sem timeline/comentários na UI, feed backend oficial consolidado e cobertura multiusuário para avaliações sem bloco persistido |
| Gestao de equipe | parcial | rota dedicada com roster local persistido, contexto de autenticacao via `/validate`, reidratacao por query string e retorno ao billing por membro | ainda sem CRUD real no IdP, convites/SCIM e trilha administrativa multiusuario |

## Evidencias de Incompletude

### Dashboard com modulos ainda nao implementados

Nenhum. Todos os cards do dashboard apontam para rotas reais dedicadas.

### Dashboard ainda nao e 100% dinamico

O dashboard agora consome dados reais (billing, watchlists, incidentes globais e, quando permitido, snapshot admin de operacoes). A lacuna remanescente e nao ter um endpoint proprio de KPI agregado (sem exigir role admin) e alguns indicadores ainda dependerem de permissao elevada.

### Billing ainda e enxuto

`/billing` agora carrega saldo real com `reserved/used_total`, deriva plano/role do contexto e, quando permitido, mostra a concorrencia org do snapshot admin. A lacuna remanescente e gestao real de usuarios/tenant (CRUD no IdP, convites/SCIM e trilha administrativa persistida).

## Cruzamento com os Contratos de API

### Fluxos com boa cobertura visual

| Contrato | Cobertura no frontend |
| --- | --- |
| `GET /api/v1/report-types` | consumido pela home e pela investigacao |
| `GET /api/v1/compliance/operations` | consumido pela home |
| `GET /api/v1/monitoring/operations` | consumido pela home |
| fluxo `estimate -> start -> status -> generate/download` | coberto por `investigate` e `cases/[id]` |
| consulta e export de auditoria | coberto por `audit` |
| operacao de watchlists, incidentes globais, DLQ e export operacional | coberto por `monitoring` |
| `POST /api/v1/compliance/counterparties` | coberto por `counterparties` |
| `GET /api/v1/compliance/counterparties` | coberto por `counterparties` |
| `GET /api/v1/compliance/sanctions-check/{address}` | coberto por `sanctions` |
| `GET /api/v1/operations/work-items` | coberto por `sanctions`, `alerts`, `blocks`, `reports` e `evidence` |
| `POST /api/v1/operations/work-items` | coberto por `sanctions`, `alerts`, `blocks`, `reports` e `evidence` |
| `PATCH /api/v1/operations/work-items/{work_item_id}` | coberto por `sanctions`, `alerts`, `blocks`, `reports` e `evidence` |
| `POST /api/v1/compliance/blocks/evaluate` | coberto por `blocks` |
| `POST /api/v1/compliance/blocks/{block_id}/lift` | coberto por `blocks` |
| `POST /api/v1/reports/ros-coaf` | coberto por `ros-coaf` |
| `POST /api/v1/reports/ros-coaf/{ros_id}/approve` | coberto por `ros-coaf` |
| `POST /api/v1/reports/ros-coaf/{ros_id}/submitted` | coberto por `ros-coaf` |
| `GET /api/v1/audit/logs` | coberto por `audit` e `evidence` |
| `POST /api/v1/audit/evidence-export` | coberto por `audit` e `evidence` |

### Fluxos suportados pela API, mas sem tela dedicada

| Contrato | Status no frontend | Impacto |
| --- | --- | --- |
| regras fortes de `legal_report` e `block lift` | sem tela propria | risco de drift entre capacidade backend e operacao humana |

## Diagnostico Consolidado

### Pronto

- autenticacao `dev`
- autenticacao OIDC com callback
- investigacao on-chain
- pagina de caso com polling e download
- auditoria com filtros e export
- monitoramento operacional principal
- home institucional com leitura real de catalogos

### Parcial

- dashboard
- contrapartes
- sancoes
- blocks e lift
- ROS/COAF
- billing e usuarios
- central de alertas
- trilha de evidencias, porque ja possui cockpit dedicado, mas ainda sem workflow operacional expandido

### Faltando

- gestao real multiusuario no IdP (convites/SCIM/admin API), alem do roster local
- timeline/comentarios de `work-items` em telas regulatórias adicionais (`blocks`, `reports`, `evidence`, `counterparties`, `ros-coaf`)
- relatorios formais (evolucao): expandir `/reports` com filtros mais ricos (por report_id, por tipo, por janela temporal) e integrar trilha de evidencias/export bundles por report

## Opcoes Arquiteturais para Fechar o Gap

| Criterio | Opcao A: expandir paginas existentes | Opcao B: criar modulos dedicados por dominio | Opcao C: cockpit unico com drawers/modais |
| --- | --- | --- | --- |
| Complexidade | baixa | media | media |
| Custo de manutencao | medio | baixo | alto |
| Escalabilidade de produto | media | alta | baixa |
| Seguranca operacional | media | alta | media |
| Time-to-market | alto | medio | alto |
| Clareza para auditoria | media | alta | baixa |

### Recomendacao

Recomendo a **Opcao B: criar modulos dedicados por dominio**, porque:

- reduz o acoplamento crescente de `monitoring`, `audit` e `billing`
- alinha a UX com os bounded contexts reais do produto regulatorio
- facilita controle de acesso, evidencias e trilhas especificas por modulo
- evita que `dashboard` vire um hub inflado com funcionalidades misturadas

## Backlog Priorizado

### P0

1. `ros-coaf`
2. hardening de `blocks` com fila, SLA e ligacao por caso
3. hardening de `counterparties` com historico, revisao e workflow administrativo
4. expandir a fila multiusuario para `counterparties` e `ros-coaf`

### P1

1. hardening de `evidence-trail`
2. `reports`
3. `team-users-roles`

### P2

1. hardening do `dashboard` com dados reais
2. evolucao de `billing` para tenant management
3. separacao da central de alertas hoje embutida em `monitoring`

## Ordem Recomendada de Implementacao

1. ROS/COAF
2. Hardening de evidence trail
3. Hardening de blocks e lift
4. Expandir a fila compartilhada para os cockpits regulatórios restantes
5. Hardening de contrapartes
6. Gestao de equipe e roles
7. Reports formais
8. Refactor de dashboard e billing

## Definition of Done por Nova Tela

- rota App Router criada e ligada ao shell lateral
- chamada real aos endpoints canonicos, sem payload mockado
- estados `loading`, erro, vazio e sucesso
- validacao de permissao e mensagens de erro do catalogo de API
- exportacao e evidencias quando o fluxo exigir
- teste E2E ou fluxo de regressao equivalente para o caminho critico

## Conclusao

O frontend atual cobre bem o **core operacional de investigacao, auditoria e monitoramento**, e ja possui base inicial para **contrapartes, sancoes, bloqueios preventivos, ROS/COAF e trilha de evidencias dedicada**, mas ainda nao cobre integralmente o **core regulatorio expandido** documentado pela plataforma. O estado honesto atual e:

- `pronto` para demonstrar o fluxo principal
- `parcial` para o cockpit executivo e administrativo
- `incompleto` para gestao real de equipe/IdP, timeline compartilhada entre todos os módulos regulatórios e reports formais expandidos
