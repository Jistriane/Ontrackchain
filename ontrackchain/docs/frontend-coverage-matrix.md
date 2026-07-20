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
| `/incident-response` | `../apps/frontend/app/incident-response/page.tsx` | parcial |
| `/billing` | `../apps/frontend/app/billing/page.tsx` | parcial |

## Matriz de Cobertura por Modulo

| Modulo | Cobertura atual | Evidencia no frontend | Lacuna principal |
| --- | --- | --- | --- |
| Home institucional | pronta | leitura autenticada de catalogos e resumo do ecossistema | nao substitui telas operacionais dedicadas |
| Login `dev` | pronta | login JWT local, erro tratado e transicao para 2FA | sem lacuna relevante para o escopo atual |
| Login OIDC | pronta | `auth/config`, redirect seguro e callback dedicado | depende da homologacao externa do provedor |
| Dashboard operacional | parcial | shell, metricas reais, atalhos operacionais, casos recentes com ações para case/audit/evidence/reports/sanctions/blocks e cards de modulos ativos, com cobertura E2E estática focal para os links contextuais, status visível, normalização visual das datas na tabela de casos recentes, CTA de billing condicionado ao recorte financeiro e handoff administrativo para `/team` oculto fora de `ADMIN`, inclusive no menu lateral global | ainda depende de snapshots/admin para parte dos KPIs e nao possui endpoint agregado proprio |
| Investigacao | pronta | `estimate -> start -> redirect case` com UX preventiva ocultando a abertura operacional para roles fora de `ADMIN`, `ANALYST` e `OTK_ANALYST`, coberta por spec focal de RBAC, e carga do catálogo de tipos preservando `not_authenticated` semanticamente em vez de erro genérico opaco | sem wizard expandido para addons, compliance ou block actions |
| Case e relatorios | pronta | polling de status, geracao e download de PDF, com fallback amigável do tipo de relatório preservado quando o catálogo não carrega e mensagem semântica explícita para `not_authenticated` no consumo de `report-types` | nao separa fluxos regulatorios mais fortes em tela dedicada |
| Auditoria | pronta | filtros, paginacao, detalhe expandido, export de evidencias, resolução `report_id -> ros_id` para atalhos/contexto ROS/COAF, com preservação explícita de `report_read_role_required` quando `ros-coaf-ref` nega a referência derivada, preservação de `not_authenticated` na leitura de `audit/logs` sem degradar para vazio sintético nem empty state concorrente, exibição amigável da ação auditável `coaf_regulatory_dossier_downloaded`, preset dedicado por query string para emissões do dossiê regulatório ROS/COAF, cards agregados do preset com volume, `ros_id` distintos, último hash visível, `report_id` e `filename` mais recentes, resumo textual do último artefato visível diretamente no aviso do preset, atalho direto para `reports` via `history_report_id` do último evento visível, bloco explícito de contexto regulatório no detalhe do evento do dossiê com `filename`, `dossier_sha256`, distinção explícita entre hash principal e `file_hash_sha256` com precedência do hash do dossie, timestamps exibidos com helper local aderente ao locale atual e validados por spec E2E estática focal, classificação visual do tipo de artefato resolvido, preset manual DD/SoF cobrindo `export -> signoff -> seal -> revoke/supersede`, preset explícito de governança pós-selagem via `preset=governanca&request_id=...` ou `preset=governanca&seal_id=...`, com resolução segura do `request_id` a partir do selo, cards temporais do último ciclo observável (`export -> selagem` e `selagem -> governança`), detalhe contextual com `ticket_ref`, `reason`, `superseded_by_seal_id` e timestamps normalizados de governança pós-selagem, preset dedicado de identidade federada por query string para `team_external_identity_linked/unlinked` com `resource_type=team_user`, métricas agregadas do recorte, contexto auditável do principal federado (`provider`, `external_subject`, snapshots e ator efetivo) e deep-link de retorno para `Team`, além de deep-links para `reports`, `ros-coaf` e `evidence`, incluindo atalho direto originado do cockpit `evidence` para abrir a governança do selo por `seal_id`, atalho inverso do preset para abrir diretamente o cockpit `ros-coaf`, e export do dossie regulatório oficial de ROS/COAF em JSON a partir do detalhe selecionado, além de ações contextuais para case/evidence/reports/investigate/sanctions/blocks/counterparties/ROS | ainda depende dos metadados emitidos pelos eventos para abrir todos os atalhos contextuais |
| Monitoramento | pronta | hub `/monitoring` agora orquestra watchlists e alertas de teste via `use-monitoring-watchlist-alerts.ts` + `watchlist-alerts-panel.tsx`, loaders centralizados em `app/lib/monitoring-api.ts`, reaproveita o hook de `platform alerts` (`use-monitoring-platform-alerts.ts`) apenas para resumo e handoff, expõe handoff explícito para `/incident-response` e `/alerts`, UX preventiva degradando leituras administrativas para `ADMIN/AUDITOR`, bloqueando preventivamente a carteira core fora do recorte `ADMIN/ANALYST/AUDITOR/VIEWER/TESTER`, ocultando o handoff dedicado fora do recorte privilegiado, preservando `not_authenticated` semanticamente nas watchlists (`monitoring/watchlists` e `monitoring/watchlists/[watchlistId]/items`) sem degradar para lista vazia ou empty state concorrente, preservando a negação semântica tardia da triagem global quando `operational-alerts`/`filter-options` devolvem `monitoring_read_role_required`, e preservando a negação semântica da fila rastreada (`operations/work-items?module=alerts&resource_type=operational_alert`) sem degradar o resumo para vazio sintético, além de cobertura E2E focal para `trigger-alert`, read-only de `AUDITOR`, bloqueio precoce do core para `REVIEWER` e negação semântica tardia nessas superfícies compartilhadas | ainda não promove o resumo global para `/incident-response`; o hub depende de `/alerts` como cockpit canônico da triagem rica |
| Incident response | parcial | rota dedicada `/incident-response` para operações do worker, alertas operacionais de investigation e remediação de DLQ, reaproveitando `use-monitoring-operations.ts`, `investigation-operations-panel.tsx` e `dlq-remediation-panel.tsx`, com navegação lateral própria para `ADMIN/AUDITOR`, handoff para `/monitoring` e `/alerts`, consumo de contexto por query string vindo de `alerts` (`alertId`, `alertName`, `severity`) para destacar o incidente de origem e filtrar visualmente os alertas operacionais compatíveis, além de CTA de retorno contextual que devolve esse mesmo recorte ao cockpit canônico de `alerts`, degradação read-only para `AUDITOR`, ocultação das mutações de DLQ fora de `ADMIN` e preservação semântica de `not_authenticated` nas superfícies `investigation/operations`, `investigation/alerts` e `investigation/metrics` sem snapshot vazio | ainda sem consolidar também a triagem global de `platform alerts` nesta mesma rota dedicada |
| Billing e usuarios | parcial | saldo real, resumo operacional, atalhos para reports/monitoring/alerts, handoff explícito para `/team` e cockpit financeiro agora desacoplado da projeção lateral de `team/users`, com cobertura E2E estática focal para reconciliação, export e links contextuais de delegação administrativa | gestão administrativa local existe no app, mas permanece concentrada em `/team` e ainda sem CRUD real no IdP, convites/SCIM e trilha multiusuario federada |
| Reports formais | parcial | rota dedicada com catálogo real, filtros reidratáveis por query string, seleção de tipo preferido com labels institucionais para plano/tipo, fila compartilhada por `case_id` via `work-items`, timeline/comentários de `work-items` na UI, histórico de casos rastreados com busca client-side por `report_id`, tipo canônico e label amigável, listagem backend oficial de relatórios gerados por `report_id`, `report_type`, `case_id` e janela temporal, preservando negação semântica `report_read_role_required` no App Router em vez de achatar `401/403` para lista vazia, preservando também `privileged_read_role_required` na leitura oficial de casos via `investigation/cases` em vez de degradar o workspace para vazio, preservando `not_authenticated` na carga do catálogo de tipos via `report-types` em vez de catálogo vazio sintético e preservando `not_authenticated` na carga do workspace compartilhado (`operations/work-items?module=reports&resource_type=formal_report_case`) sem apagar o histórico oficial nem degradar para empty state, leitura operacional oficial por `report_id` com download, detalhe exibindo tipo solicitado e tipo resolvido com fallback técnico, deep-link de evidência filtrado por `report_id`, export direto de evidence bundle por relatório, painel de dossiê formal com classificação/política de acesso/âncora/estado de download e manifesto operacional complementar de custódia/distribuição/retenção, workspace backend-only com coluna de SLA, correlação operacional também por `report_external_id`, hidratação seletiva do workspace via filtro backend por `report_external_id`, identidade híbrida do workspace por `reportExternalId` ou `caseId`, tabela operacional exibindo `report_id` explícito e seleção/timeline priorizando o relatório oficial quando disponível, detalhe enriquecido com `reportExternalId`, `source`, `sla` e último handoff, UX preventiva ocultando exports sensíveis de evidências/dossiê para roles fora de `ADMIN` e `AUDITOR`, gate semântico dedicado no App Router para a exportação do dossiê formal com negação tardia humanizada, ocultando o download comum e o detalhe operacional rico para `VIEWER` com regra própria `ADMIN/AUDITOR/ANALYST`, e ocultando o download de `legal_report` fora do trilho compatível com `ADMIN`, auth `jwt/dev_jwt` e `2FA`, com cobertura E2E estática focal para `priority`, `source`, `SLA`, export RBAC, listagem negada semanticamente, `formal-dossier`, detail/download comum, `legal_report` strong-auth, resolução semântica de `report_id -> ros_id` quando `ros-coaf-ref` devolve `report_read_role_required` e normalização visual do deadline no workspace, atalho direto do detalhe para abrir o ROS/COAF vinculado quando `report_type=coaf_ready_report` e o `metadata.ros_id` estiver disponível, além do resumo do workspace no JSON exportado do dossiê por endpoint próprio no App Router e ações para case/audit/evidence/investigate | ainda sem geração formal orquestrada fim a fim para toda a superfície regulatória e sem decisão final de modelagem entre unidade operacional por `case_id` ou por `report_id` |
| Contrapartes | parcial | rota dedicada com listagem paginada, onboarding regulado inicial, prefill via query string, workspace compartilhado por `counterparty_id` via `work-items`, timeline/comentários de `work-items` na UI, assignment por `owner_user_id`, distinção explícita de origem server-side, coluna dedicada de revisão DD/SoF, formulário operacional estruturado para `ddReviewStatus`, nota interna, descrição de origem dos fundos e referência documental, persistência oficial da revisão DD/SoF no backend de `counterparties` usando `enhanced_dd_status`, `enhanced_dd_findings`, `enhanced_dd_checklist` e `last_reviewed_at/by`, com espelhamento no `work-item` compartilhado, painel oficial de dossiê por contraparte via endpoint dedicado de detalhe e histórico formal DD/SoF paginado via `counterparty_history`, degradando o histórico formal com negação semântica para roles fora de `ADMIN`, `COMPLIANCE_OFFICER` e `REVIEWER`, preservando também `not_authenticated` na carga do workspace compartilhado (`operations/work-items?module=counterparties&resource_type=counterparty`) sem apagar o dossiê oficial nem degradar o painel para empty state sintético, além de UX preventiva ocultando onboarding, carteira operacional, workspace e o link lateral global para roles fora do recorte regulatório de leitura, com ações para case/audit/evidence/sanctions e cobertura E2E estática focal para `source`, `status`, onboarding RBAC, leitura RBAC, navegação global, revisão DD/SoF, dossiê oficial, histórico formal e deadline do workspace compartilhado | ainda sem workflow DD/SoF regulatório mais amplo além do registro oficial, do dossiê oficial e da trilha operacional/histórica dedicada |
| Sancoes | parcial | rota dedicada com verificação, triagem operacional, deep-link com prefill/autostart, ações para case/audit/evidence/blocks, sincronização da fila compartilhada via `work-items`, timeline/comentários na UI, assignment por `owner_user_id` e painel de histórico de triagens por endereço agora backend-first, exibindo apenas itens sincronizados, preservando também `not_authenticated` na carga do workspace compartilhado (`operations/work-items?module=sanctions&resource_type=sanctions_screening`) sem degradar o cockpit para workspace vazio, histórico vazio ou aviso falso de pendência de sincronização, com UX preventiva ocultando `sanctions-check` e transições operacionais para roles fora de `ADMIN`, `ANALYST`, `COMPLIANCE_OFFICER` e alias legado `OTK_COMPLIANCE_OFFICER`, além de humanização do `detail` `sanctions_check_role_required`, com cobertura E2E estática focal para `source`, `status`, `urgency`, deadline do workspace e RBAC do screening | sem fallback local de negócio; ainda sem histórico backend oficial por endereço/caso com paginação dedicada própria |
| Blocks | parcial | rota dedicada com avaliação preventiva, lift regulatório, feed oficial backend-first de `preventive_blocks`, sincronização/enriquecimento via `work-items`, timeline/comentários na UI, merge entre trilha oficial e workspace operacional, preservando `preventive_block_read_role_required` para leitura restrita e preservando também `not_authenticated` na carga do workspace compartilhado (`operations/work-items?module=blocks&resource_type=preventive_block`) sem degradar o cockpit para `workspace.empty` ou `history.empty` sintético, com UX preventiva ocultando `evaluate` fora de `ADMIN/ANALYST/COMPLIANCE_OFFICER`, ocultando `lift` fora de `ADMIN/COMPLIANCE_OFFICER` e cobertura E2E estática focal para `source`, `status`, `urgency`, merge com o feed oficial, RBAC de `evaluate/lift` e negação semântica do workspace compartilhado | ainda sem página separada para governança/analytics de bloqueios além do cockpit operacional unificado |
| Trilha de evidências | parcial | rota dedicada com filtros, correlacao por chaves, export de bundle, workspace compartilhado por `event_id` via `work-items`, timeline/comentários de `work-items` na UI, assignment por `owner_user_id`, painel de histórico de eventos rastreados com navegação para timeline, foco contextual da cadeia por `request_id/report_id`, resumo operacional da cadeia correlacionada, presets para `due_diligence`/`source_of_funds`, leitura explícita do contrato `manual_review_pending`, painel de pacote regulatório DD/SoF com manifesto institucional visível na UI (workflow, access policy, sign-off, custody e anchor) com labels institucionais tri-locale e código técnico preservado, campos obrigatórios/checklist baseados em códigos estáveis renderizados via i18n, datas aderentes ao locale atual do cockpit com helpers locais reutilizados no workspace, detalhe e chain summary, incluindo cobertura E2E estática focal para timestamps de log e datas da cadeia contextual, contrato compartilhado do pacote manual extraído para `app/lib/evidence-manual-package.ts`, atalhos diretos para foco/export da cadeia contextual e navegação operacional para `case`/`audit`/`reports` e módulos derivados por `address/chain` (`investigate`, `sanctions`, `blocks`), incluindo deep-link explícito do pacote manual para o preset auditável em `audit` por `request_id` e banner contextual quando o usuário retorna do `audit`, navegação para `ros-coaf` quando o evento possui `ros_id` ou quando `report_id` referencia um COAF-ready report (resolução via endpoint de referência), com preservação explícita de `report_read_role_required` quando `ros-coaf-ref` nega a referência derivada, export do dossiê regulatório oficial de ROS/COAF em JSON quando `ros_id` estiver resolvido (via endpoint unificado do `report-api`), bloco de contexto de hash exibindo hash principal, origem e tipo de artefato resolvido no detalhe e no painel de cadeia, agora com precedência de `package_sha256` quando um export manual correlacionado estiver presente, bloco explícito de contexto regulatório do dossiê exportado com `filename`, `dossier_sha256` e deep-links para `reports` e `ros-coaf` no detalhe e no painel de cadeia, reconhecimento amigável do evento auditável `coaf_regulatory_dossier_downloaded`, leitura read-only da selagem institucional persistida por `package_sha256` com proxy autenticado do App Router e preservação explícita de `manual_package_read_role_required` sem degradar para "Nenhum selo persistido para este pacote", preservando também `not_authenticated` na carga do workspace compartilhado (`operations/work-items?module=evidence&resource_type=evidence_event`) sem apagar a trilha principal nem degradar o painel para empty state, resumo visual de status/quorum/sign-offs/verificação/trust bundle no detalhe do pacote manual para roles `ADMIN/AUDITOR`, inicialização controlada da trilha institucional de sign-off por `package_sha256`, registro de sign-offs obrigatórios por papel, CTA de selagem final condicionado a `ready_to_seal` e CTAs de revogação/supersedência com ticket/motivo diretamente no cockpit `evidence`, UX preventiva ocultando os exports sensíveis de cadeia e pacote manual para roles fora de `ADMIN` e `AUDITOR`, distinção explícita de origem server-side no workspace, sincronização compartilhada também para `event_id` não-UUID via `resource_id` canônico determinístico, resumo de workspace do evento manual no detalhe com `resource`, `case_id`, `request_id`, `report_id`, `file_hash_sha256` e `source`, ações para carregar o handoff manual no workspace, abrir diretamente a timeline compartilhada correlacionada, transicionar status (`queued/reviewing/sealed`) no próprio detalhe, export dedicado do dossiê manual com `workspace_summary` enriquecido (`action`, `resource`, `case_id`, `request_id`, `report_id`, `file_hash_sha256`) por endpoint próprio no App Router reutilizando `audit/evidence-export`, manifesto canônico SHA-256 por JSON ordenado, checksums separados de `payload/evidence_bundle/workspace_summary` e evento oficial `evidence_manual_review_package_exported` em `audit_logs`, com cobertura E2E explícita para os contratos manuais, handoffs operacionais de `due_diligence` e `source_of_funds`, a materialização visual da selagem forte, a escrita controlada de sign-off, a selagem final protegida e a governança pós-selagem | escrita da trilha restrita a roles privilegiadas |
| Central de alertas | parcial | rota dedicada agora é a fonte canônica da triagem global de `platform alerts`, com filtros, ack, export, abertura por query string, ações por incidente para case/audit/evidence/investigate/sanctions, rastreamento em `work-items`, sincronização de encerramento via `ack`, timeline/comentários para incidentes rastreados, painel de alertas rastreados como work-items e assignment por `owner_user_id`, handoff contextual explícito para `/incident-response` com `alertId`, `alertName` e `severity`, retorno contextual vindo de `/incident-response` com banner de origem, marcador visual da linha devolvida e reabertura automática da timeline do alerta rastreado, agora com UX preventiva degradando a leitura privilegiada para `ADMIN/AUDITOR`, ocultando `ack/export/track/save` fora de `ADMIN`, removendo o link lateral global fora do mesmo recorte de leitura, evitando flicker de links sensíveis antes da resolução do contexto autenticado, preservando `monitoring_read_role_required` em negação tardia de `operational-alerts`/`filter-options` sem degradar a triagem global para estado vazio, preservando `not_authenticated` semanticamente na carga da fila rastreada (`operations/work-items?module=alerts&resource_type=operational_alert`) sem apagar silenciosamente o contexto RCA, e com o proxy standalone/showcase do App Router aceitando o rastreamento de `operational_alert` com timeline compartilhada validada em runtime, além de cobertura E2E focal para links contextuais, estado visual `severity/status/triage`, fila rastreada, timestamps sem ISO cru e RBAC do cockpit | ainda sem integração full com `/incident-response` para unificar triagem global e resposta operacional em um único fluxo |
| ROS/COAF | parcial | rota dedicada com geracao, aprovacao/rejeicao, submissao manual, leitura backend oficial via `report-api` para `ros_records`, workspace compartilhado por `ros_id` via `work-items`, prefill via query string, timeline/comentários de `work-items` na UI, painel de histórico de registros ROS/COAF rastreados, assignment por `owner_user_id`, origem server-side explícita, fases semânticas `generated/approved/rejected/submitted`, persistência do motivo de rejeição no `work-item`, vínculo operacional também por `report_external_id` para reduzir drift com o módulo de reports, hidratação oficial de `report_id`, protocolo, recibo, `submission_deadline` e `deadline_breached` com badges/colunas de SLA COAF no workspace e no histórico, centralização local dos pills semânticos de `priority`, `source`, `phase`, `urgency` e `SLA`, datas opcionais formatadas com fallback consistente, painel dedicado de detalhe oficial do ros_record e trilha de auditoria (audit_logs) para o ros_id selecionado, preservando `not_authenticated` semanticamente na carga do workspace compartilhado (`operations/work-items?module=ros_coaf&resource_type=ros_record`) sem apagar a listagem oficial nem degradar para empty state, timeline regulatória unificada no detalhe consolidando `audit_logs`, eventos operacionais e comentários persistidos do `work-item` em sequência cronológica única, incluindo o evento auditável de emissão/download do dossiê com `filename` e `dossier_sha256`, painel visual dedicado do histórico de emissões/downloads do dossiê no detalhe oficial, resumo executivo com contagem, última emissão e último hash auditado, deep-link dedicado para `/audit` já com preset do evento `coaf_regulatory_dossier_downloaded`, emissão oficial do dossiê regulatório unificado via endpoint `GET /api/v1/reports/ros-coaf/{ros_id}/regulatory-dossier` (domínio + operacional), consumido pelo cockpit via proxy App Router e baixado como JSON, além de malha E2E focal de RBAC por persona para `generate/approve/submit` e para os pré-requisitos de sessão forte (`linked_user_id`, MFA externo homologado) | ainda sem timeline gerada transacionalmente no backend regulatório e sem padronização institucional adicional (ex: assinatura/selagem forte) para o dossiê |
| Preventive blocks / lift | parcial | rota dedicada com avaliação, `lift` assistido via MFA externo, feed oficial backend-first para `preventive_blocks`, enriquecimento operacional via `work-items` na UI, timeline/comentários persistidos, painel de histórico de bloqueios rastreados, origem server-side explícita no workspace/timeline/histórico, UX preventiva ocultando a superfície de avaliação para roles fora de `ADMIN`, `ANALYST` e `COMPLIANCE_OFFICER`, o CTA de `lift` para roles fora de `ADMIN` e `COMPLIANCE_OFFICER`, além de humanização das negações tardias do backend para `block_evaluate_role_required` e `block_lift_role_required`, com cobertura E2E estática focal para `source`, `status`, `urgency`, normalização visual do deadline no workspace, feed oficial consolidado e segregação RBAC de `evaluate` + `lift`, além de ações para case/audit/evidence/ROS | ainda sem cobertura multiusuário para avaliações sem bloco persistido |
| Gestao de equipe | parcial | rota dedicada com diretório real do tenant em `users + external_identities`, contexto de autenticacao via `/validate`, reidratacao por query string e retorno ao billing por membro, vínculo manual inicial do principal federado, leitura detalhada dos vínculos persistidos por membro, desvinculação administrativa com confirmação explícita no cockpit, deep-link contextual direto para o preset `identity-federated` do cockpit `Audit` por `member_id` tanto na seção de identidade quanto na roster table, busca assistida no IdP via `Keycloak Admin API` com validação antes do vínculo (matching `email + org` e validação de role) e execução do vínculo em fluxo único na UI, trilha auditável local de `link/unlink` em `audit_logs`, além de UX preventiva ocultando o formulário manual de vínculo e o CTA de desvinculação para roles fora de `ADMIN`, e humanização das negações tardias do diretório assistido, da leitura detalhada de vínculos persistidos, da leitura da roster quando a sessão falha, e das mutações locais de usuário quando o backend devolve `team_federated_directory_search_role_required`, `team_federated_directory_suggestion_role_required`, `team_federated_identity_read_role_required`, `team_user_create_role_required`, `team_user_update_role_required`, `team_user_disable_role_required` ou `not_authenticated`, com cobertura E2E estática focal para labels amigáveis de role, status visível do membro, fluxo de vínculo/desvínculo, bloqueio precoce por role, busca assistida federada, negação tardia traduzida, mutações locais semânticas, leitura da roster sem degradar para diretório vazio, deep-link para auditoria e normalização visual de `updated_at` na roster table | ainda sem CRUD real no IdP, convites/SCIM e trilha administrativa multiusuario federada |

## Rastreabilidade E2E Estatica

Fonte canonica: [frontend-static-regression-traceability.md](./frontend-static-regression-traceability.md)

Resumo executivo desta matriz:

- a trilha estatica cobre os cockpits `audit`, `ros-coaf`, `evidence`, `reports`, `dashboard`, `team`, `billing`, `counterparties`, `sanctions`, `blocks`, `alerts`, `monitoring` e `incident-response`
- a rastreabilidade detalhada `cockpit -> spec canonica -> contratos protegidos` foi consolidada no documento canonico para evitar drift com a cobertura funcional desta matriz
- qualquer mudanca em `data-testid`, labels semanticas, datas visuais, hash/contexto regulatorio ou deep-links deve sincronizar esta matriz e o documento canonico de rastreabilidade na mesma rodada

## Fundacao Compartilhada de Work-Items

- `P1-01` avancou com contrato compartilhado em `apps/frontend/app/lib/work-items.ts` para `module`, `resource_type`, `priority`, `queue_status`, requests/responses e helpers de leitura de `metadata`
- `reports`, `evidence`, `sanctions`, `alerts`, `blocks`, `counterparties` e `ros-coaf` passaram a consumir a mesma base tipada de `work-items`
- a normalizacao de `deadline` para `datetime-local` e a ordenacao por `lastActionAt` dos cockpits operacionais compartilham o helper `apps/frontend/app/lib/workspace-storage.ts`, agora sem reidratacao/persistencia de dados de negocio no navegador
- a identidade operacional continua especifica por cockpit para evitar drift semantico: `reportExternalId/caseId` em `reports`, `event_id/resource_id` canônico em `evidence` e chaves locais orientadas ao dominio nos demais modulos
- `metadata.workspace_status` passa a ser a chave canonica de status operacional no frontend, com leitura retrocompativel de aliases legados como `local_workspace_status`, `local_block_status` e `ros_status`
- a migracao atual ainda preserva dual-read/dual-write de chaves legadas para compatibilidade de metadados operacionais, sem restaurar workspaces locais de negocio
- `blocks` agora explicita melhor a hierarquia `server > local draft` com origem visivel no workspace, na timeline e no historico, alem de feedback claro para comentarios persistidos
- `ros-coaf` agora propaga `rejection_reason`, `approval_2fa_verified` e `ros_phase` na camada operacional de `work-items`, reduzindo drift entre aprovacao/rejeicao/submissao e a timeline compartilhada
- `evidence` agora deriva `resource_id` deterministico para itens cujo `event_id` nao nasce como UUID, preservando o identificador original em `metadata` e removendo o bloqueio artificial de sincronizacao compartilhada
- `reports`, `evidence` e `counterparties` agora expõem estado operacional backend-only e labels tri-locale sincronizadas para `source`, `review`, `SLA` e handoff operacional
- `audit`, `evidence` e `ros-coaf` agora compartilham a mesma semantica de contexto regulatorio para hash principal, com precedencia explicita de `dossier_sha256` sobre `file_hash_sha256`, alem de helpers locais para datas e badges semanticos que reduzem drift visual entre cockpits
- `P2-02` foi consolidado: o controller de timeline/comments foi centralizado no hook `apps/frontend/app/lib/use-work-item-timeline.ts`, adotado em `blocks`, `sanctions`, `alerts`, `counterparties`, `evidence`, `reports` e `ros-coaf`, e sustentado pela spec canonica `timeline-workspace.spec.ts` para a trilha compartilhada

## Evidencias de Incompletude

### Dashboard com modulos ainda nao implementados

Nenhum. Todos os cards do dashboard apontam para rotas reais dedicadas.

### Dashboard ainda nao e 100% dinamico

O dashboard agora consome dados reais (billing, watchlists, incidentes globais e, quando permitido, snapshot admin de operacoes). Os atalhos globais ja escondem `billing` fora do recorte financeiro e o handoff administrativo para `/team` fora de `ADMIN`. A lacuna remanescente e nao ter um endpoint proprio de KPI agregado (sem exigir role admin) e alguns indicadores ainda dependerem de permissao elevada.

### Billing ainda e enxuto

`/billing` agora carrega saldo real com `reserved/used_total`, deriva plano/role do contexto e, quando permitido, mostra a concorrencia org do snapshot admin. O cockpit deixou de consumir `team/users` diretamente e delega a gestao do tenant para `/team`. A lacuna remanescente continua sendo gestao real de usuarios/tenant (CRUD no IdP, convites/SCIM e trilha administrativa persistida).

## Cruzamento com os Contratos de API

### Fluxos com boa cobertura visual

| Contrato | Cobertura no frontend |
| --- | --- |
| `GET /api/v1/report-types` | consumido pela home e pela investigacao |
| `GET /api/v1/compliance/operations` | consumido pela home |
| `GET /api/v1/monitoring/operations` | consumido pela home |
| fluxo `estimate -> start -> status -> generate/download` | coberto por `investigate`, `cases/[id]` e pela degradacao preventiva das acoes sensiveis de `cases` para `VIEWER`/`AUDITOR`/`ANALYST` conforme o tipo do artefato |
| consulta e export de auditoria | coberto por `audit` |
| operacao de watchlists, incidentes globais, DLQ e export operacional | coberto por `monitoring` |
| `POST /api/v1/compliance/counterparties` | coberto por `counterparties` |
| `GET /api/v1/compliance/counterparties` | coberto por `counterparties` |
| `GET /api/v1/compliance/sanctions-check/{address}` | coberto por `sanctions` |
| `GET /api/v1/operations/work-items` | coberto por `sanctions`, `alerts`, `blocks`, `reports`, `evidence`, `counterparties` e `ros-coaf` |
| `POST /api/v1/operations/work-items` | coberto por `sanctions`, `alerts`, `blocks`, `reports`, `evidence`, `counterparties` e `ros-coaf` |
| `PATCH /api/v1/operations/work-items/{work_item_id}` | coberto por `sanctions`, `alerts`, `blocks`, `reports`, `evidence`, `counterparties` e `ros-coaf` |
| `GET /api/v1/compliance/blocks` | coberto por `blocks` |
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
| `block lift` | cobertura de cockpit em `/blocks` | feed backend consolidado agora exposto em `GET /api/app/compliance/blocks`, com `work-items` usados apenas para enriquecimento operacional |

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
- trilha de evidencias, porque ja possui cockpit dedicado, cadeia contextual expandida, pacote regulatório DD/SoF no frontend e selagem institucional forte funcional com governança pós-selagem

### Faltando

- gestao real multiusuario no IdP (convites/SCIM/admin API), alem da camada administrativa local sobre `users + external_identities`
- hardening de ownership por SLA/capacidade (assignment por `owner_user_id` ja consolidado nos cockpits regulatórios)
- relatorios formais (evolucao): fechar a orquestracao formal fim a fim da superficie regulatoria e institucionalizar o dossiê formal gerado no cockpit

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
4. consolidar politicas de ownership por SLA, capacidade e escalacao

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
- `incompleto` para gestao real de equipe/IdP, assinatura/classificação forte da cadeia de custodia e reports formais expandidos
