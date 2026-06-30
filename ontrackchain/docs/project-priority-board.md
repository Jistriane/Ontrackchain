# Board de Prioridades do Projeto

## Objetivo

Consolidar, em uma unica visao operacional, as iniciativas necessarias para levar o Ontrackchain de:

- `89%` de construcao tecnica

para:

- `90%+` de maturidade tecnica

Este board complementa:

- [Avaliacao de Maturidade do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-maturity-assessment.md)
- [Plano de Execucao para 90%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-execution-plan-to-90.md)
- [Matriz Operacional de Execucao para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-execution-board.md)
- [Runbook de Governanca Semanal](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-weekly-governance-runbook.md)

## Como Ler Este Board

Cada item possui:

- prioridade executiva
- impacto esperado
- esforco relativo
- owner sugerido
- dependencias principais
- criterio objetivo de pronto

Camada de uso:

- este documento continua sendo a visao estrategica de prioridade e sequenciamento
- a [Matriz Operacional de Execucao para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-execution-board.md) passa a ser a camada de acompanhamento semanal por evidência, owner nominal, prazo alvo, risco e artefato esperado

Status sugeridos:

- `todo`
- `ready`
- `in_progress`
- `blocked`
- `done`

## Visao Executiva

### Prioridades P0

Itens que mais aumentam maturidade real:

- homologacao de auth real com IdP fora do local
- MFA real fora do contexto apenas local
- providers reais AML/KYT
- RPC primario com fallback
- contratos diretos de compliance sem sucesso ficticio
- retention policy, backup/restore e exportacao segura de evidencias

Ja consolidados:

- RBAC por dominio no core administrativo
- trilha auditavel de negacoes sensiveis no core endurecido
- gates de CI para `OIDC`, regressao completa e `dev auth` local

### Prioridades P1

Itens que consolidam governanca e capacidade de staging serio:

- retention policy
- backup e restore testados
- exportacao segura de evidencias
- evolucao operacional de `/audit`
- lint, typecheck, schema gates e security checks

### Prioridades P2

Itens de consolidacao operacional:

- staging com smoke pos-deploy
- owners, SLAs e runbooks formais

## Tabela Operacional

| ID | Status Inicial | Prioridade | Iniciativa | Dominio | Impacto | Esforco | Owner Sugerido | Dependencias | Done |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0-01 | in_progress | P0 | Implementar IdP real e despriorizar modo dev fora de local | Auth | Muito alto | Alto | Backend/Auth | secrets, configuracao OIDC | `Keycloak` + `OIDC` validados localmente, gates de CI ativos e rollout operacional concluido fora de `AUTH_MODE=dev` em ambiente serio |
| P0-02 | in_progress | P0 | Expandir MFA real para contexto serio e runbooks de indisponibilidade | Auth | Muito alto | Medio | Backend/Auth + Frontend | P0-01 | MFA real protegendo fluxos sensiveis em ambiente serio com evidencia auditavel |
| P0-03 | done | P0 | Fechar RBAC por dominio de ponta a ponta | Seguranca | Muito alto | Medio | Arquiteto + Backend | P0-01 | papeis formalizados e enforcement ativo no core administrativo, `legal_report`, `/audit` e trilhas federadas principais |
| P0-04 | done | P0 | Expandir persistencia de negacoes sensiveis de autorizacao | Seguranca | Alto | Medio | Backend | P0-03 | eventos negativos auditados com `request_id`, papel e recurso no core endurecido e nas superficies administrativas federadas |
| P0-05 | in_progress | P0 | Integrar provider real AML/KYT | Compliance | Muito alto | Alto | Compliance/Backend | credenciais, contrato do provider | consultas reais disponiveis com timeout, retry, observabilidade, degradacao honesta e catalogo operacional de capability |
| P0-06 | in_progress | P0 | Integrar RPC primario com fallback | Investigation | Alto | Alto | Backend Core | configuracao segura de providers | resiliencia com fallback validado por smoke/teste |
| P0-07 | done | P0 | Remover stubs criticos de compliance | Compliance | Muito alto | Alto | Compliance/Backend | P0-05 | endpoints principais sem retorno stub nos fluxos core |
| P1-01 | in_progress | P1 | Definir retention policy de auditoria e evidencias | Governanca | Alto | Medio | Security/Platform | decisao de compliance | politica publicada com escopo, prazo e owner; aguardando sign-off formal de Security/Compliance |
| P1-02 | done | P1 | Implementar backup e restore testados | Operacao | Alto | Alto | Platform/DBA | P1-01 | backup e restore controlados com `rto_seconds`, `sha256` e manifestos JSON anexaveis |
| P1-03 | done | P1 | Criar exportacao segura multi-dominio de evidencias | Auditoria | Alto | Alto | Backend + Frontend | P1-01 | exportacao autorizada, auditada e filtravel cruzando `audit_logs`, `credit_ledger` e `reports` |
| P1-04 | done | P1 | Expandir `/audit` com paginação e exportacao operacional | Frontend/Ops | Medio | Medio | Frontend | P1-03 | UX operacional com navegacao paginada, filtros administrativos e export auditado |
| P1-05 | done | P1 | Adicionar lint e typecheck dedicados por app | CI/CD | Alto | Medio | DevOps | nenhuma | workflow dedicado executa `typecheck` no frontend e gate de qualidade Python por app/pacote |
| P1-06 | done | P1 | Adicionar gates de schema e migrations | CI/CD | Alto | Medio | DevOps + Backend | P1-05 | workflow valida sequencia, README e coerencia entre `infra/postgres/migrations` e `init.sql` |
| P1-07 | done | P1 | Adicionar checks de seguranca na pipeline | CI/CD | Alto | Medio | DevOps/Security | P1-05 | pipeline inclui baseline de secrets/defaults e `npm audit` de producao no frontend |
| P2-01 | done | P2 | Estruturar staging tecnico com smoke pos-deploy | Release | Medio | Medio | DevOps/Platform | P1-05, P1-06 | workflow manual de promocao tecnica publica evidencia unica do pos-deploy com runtime, compliance e investigation |
| P2-02 | in_progress | P2 | Formalizar owners, SLAs e runbooks de incidente | Operacao | Medio | Medio | Platform/SRE | P1-01 | runbooks publicados, owners nomeados e SLA base definido; aguardando aceite operacional |

## Espelhamento com a Matriz Operacional

### Itens Estrategicos com Correspondencia Direta

| ID do Board | ID na Matriz Operacional | Observacao |
| --- | --- | --- |
| `P0-01` | `P0-01` | mesmo item, com owner nominal, prazo alvo e artefato esperado detalhados |
| `P0-02` | `P0-02` | mesmo item, com risco e evidência operacional explicitados |
| `P0-05` | `P0-05` | mesmo item, com vínculo direto a homologação AML/KYT |
| `P0-06` | `P0-06` | mesmo item, com vínculo direto a homologação RPC |
| `P1-01` | `P1-01` | mesmo item, detalhado por sign-off formal e risco regulatório |
| `P2-02` | `P2-02` | mesmo item, detalhado por aceite operacional e rito de incidente |

### Itens Operacionais Derivados

| ID Operacional | Origem Estrategica | Papel |
| --- | --- | --- |
| `RUN-STG-01` | deriva de `P0-01`, `P0-05`, `P0-06` | primeira janela séria executada com `run_staging_window.py` e dossier |
| `GOV-01` | deriva de `P1-01` | classificar evidências por sensibilidade e descarte |
| `REL-02` | deriva de `RUN-STG-01` | comprovar repetibilidade operacional com segunda janela séria |
| `OBS-01` | deriva do bloco de observabilidade e operação | fechar RCA cross-domain com evidências de triagem |
| `SEC-01` | deriva da trilha de segurança e governança | institucionalizar vault e estratégia de segredos de produção |
| `OPS-01` | deriva de `P2-02` | formalizar war room, escalacao e execução de RCA |
| `AUD-01` | deriva de `GOV-01` | reforçar cadeia de custódia com selagem, assinatura ou equivalente |
| `REL-03` | deriva de `REL-02` | automatizar promoção para ambiente superior |
| `SEC-02` | deriva de `P0-03` e `P0-01` | granularizar RBAC regulatório além do corte administrativo principal |

### Regra de Uso

1. alterar prioridade e narrativa macro neste board
2. alterar status operacional, bloqueio, owner nominal e artefato esperado na matriz operacional
3. nunca considerar um item como fechado aqui sem evidência correspondente na matriz operacional quando houver espelho

## Ordenacao Recomendada

### Progresso Relevante Ja Comprovado

- `P0-01` deixou de ser apenas preparacao documental: o fluxo `Keycloak + Redirect Web + PKCE` ja foi validado no runtime local
- a suite E2E oficial cobre login OIDC bem-sucedido, logout, callback sem estado e erro explicito `invalid_claims`
- o gap remanescente de `P0-01` foi reduzido com `preflight_oidc_serious_env.py`, que agora valida `APP_ENV`, `AUTH_MODE=oidc`, `DEV_AUTH_ENABLED=false`, secrets nao-dev e ausencia de `localhost` nas URLs publicas do IdP
- `P0-02` avancou com runbooks, separacao explicita de `OIDC` vs `dev auth` e endurecimento do contrato: `OIDC` nao mascara mais `2FA ok` local nem libera `legal_report` sem MFA serio homologado
- `P0-05` e `P0-06` reduziram o gap de rollout com `preflight_external_integrations.py` e `homologation_external_evidence.py`, que agora cobrem validacao previa de modo esperado, URLs, retries/timeouts, placeholders inseguros e a geracao de artefato anexavel com `preflight`, readiness, execucao funcional e bundle `/audit` correlacionado por `request_id`
- a preparacao de `staging` deixou de depender de montagem manual dispersa: agora existe um baseline serio em `.env.staging.example` para OIDC, AML/KYT e RPC, reduzindo erro operacional antes das proximas janelas de homologacao real
- a promocao para `staging` ganhou um gate executavel adicional com `check_staging_env_placeholders.py`, bloqueando placeholders `__FILL_*__` e secrets criticos ausentes/vazios antes dos preflights e da homologacao externa
- a preparacao do arquivo privado de `staging` ganhou matriz formal de handoff em `staging-env-ownership.md`, conectando placeholders criticos a owners de `Backend/Auth`, `Compliance/Backend`, `Backend Core`, `Platform/SRE` e `Security`
- o handoff de `staging` deixou de ser apenas checklist textual: `check_staging_env_handoff.py` agora valida grupos obrigatorios, owner, data e status permitidos antes da janela real
- o baseline serio tambem ganhou regressao estrutural: `check_staging_env_ownership_coverage.py` bloqueia placeholders novos sem owner explicito e detecta linhas obsoletas na matriz
- a janela de `staging` agora pode gerar um artefato redigido reutilizavel com `render_staging_window_packet.py`, consolidando baseline, ownership, handoff e sequencia operacional sem expor secrets
- o pacote final de release ganhou consolidacao unica: `build_staging_release_dossier.py` agrega `window packet`, JSONs dos checkers e homologacao em um dossier com manifesto proprio para sign-off
- a execucao da janela virou fluxo unico e repetivel com `run_staging_window.py`, que persiste checks, preflights, homologacao e dossier com falha honesta antes de qualquer promocao seria
- `P0-06` saiu do zero tecnico: o worker ja suporta `primary_url + fallback_url`, `rpc-readiness` expõe `operating_mode` e o smoke runtime agora valida a preservacao de `kyw_summary.rpc.*` no resultado final da investigation
- `P1-01` saiu do estado apenas "ready": agora existe baseline publicada de retention/recovery com classes, owners, regra minima de descarte e trilha explicita de sign-off; o delta remanescente e a aprovacao formal por Security/Compliance
- `P1-02` foi fechado com evidência operacional real: `backup_postgres.sh` e `restore_postgres.sh` geraram dump, restore em banco isolado, `rto_seconds=1` e manifestos JSON anexaveis
- `P1-03` foi fechado como produto operacional: a tela `/audit` agora exporta bundle autorizado e auditado cruzando `audit_logs`, `credit_ledger` e metadados persistidos de `reports`
- `P1-04` tambem foi fechado no escopo planejado: `/audit` agora tem paginação operacional `page/limit`, resumo de navegação, filtros administrativos e export auditado no mesmo fluxo
- `P2-02` tambem saiu do zero documental: existe matriz publicada de owners, SLA base por dominio, mapeamento de runbooks e trilha explicita de aceite operacional
- `P0-03` foi fechado no corte administrativo principal:
  - `monitoring` leitura privilegiada com `ADMIN|AUDITOR` e mutacoes/export com `ADMIN`
  - `investigation` leitura privilegiada com `ADMIN|AUDITOR` e mutacoes de DLQ com `ADMIN`
  - `audit/logs` com leitura privilegiada `ADMIN|AUDITOR`
  - `legal_report` exigindo `ADMIN + JWT + 2FA`
- `P0-04` tambem foi fechado no core endurecido:
  - `authorization_denied` persistido com `request_id`
  - trilha federada preservando `external_user_id`
  - regressao E2E cobrindo negacao administrativa em `OIDC`
- a baseline do board subiu para `89%`, puxada por identidade federada, endurecimento de `RBAC`, cobertura E2E, quality gates por componente e operacionalizacao seria de `staging`

### Faixa 1 — Ganho Estrutural Imediato

- `P0-01`
- `P0-02`
- `P0-05`
- `P0-06`

Motivo:

- esses itens alteram diretamente a credibilidade do projeto para staging serio

### Faixa 2 — Fechamento do Core Regulado

- `P1-01`
- `P1-02`

Motivo:

- fecham seguranca, integracao real e base de governanca

### Faixa 3 — Operabilidade e Gating

- `P1-05`
- `P1-06`
- `P1-07`
- `P2-01`

Motivo:

- tornam o sistema operavel com mais confiabilidade e melhor criterio de promocao

### Faixa 4 — Consolidacao

- `P2-02`

Motivo:

- transformam maturidade pontual em capacidade sustentavel de operacao

## Regras de Priorizacao

Quando houver conflito entre itens, priorizar:

1. seguranca e identidade
2. reducao de stubs em fluxos core
3. governanca de evidencias
4. gates de release
5. refinamentos de UX operacional

## KPIs do Board

### KPI 1 — Percentual de Itens P0 Concluidos

Meta:

- `>= 80%`

### KPI 2 — Fluxos Core Sem Stub

Meta:

- compliance core e investigation core sem dependencia de stub em staging serio

### KPI 3 — Trilhas Auditaveis Sensiveis

Meta:

- autenticacao, negacao, exportacao e evidencias com correlacao por `request_id`

### KPI 4 — Release Readiness

Meta:

- pipeline com gates tecnicos minimos e smoke pos-deploy

## Ritos Recomendados

### Revisao Semanal

- revisar status de cada item
- validar bloqueios
- ajustar owner se necessario
- atualizar primeiro a matriz operacional e depois refletir aqui apenas mudancas estrategicas
- seguir agenda, entradas e saídas obrigatórias do [Runbook de Governanca Semanal](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-weekly-governance-runbook.md)

### Revisao por Sprint

- recalcular impacto percentual
- confirmar se algum item pode migrar de `todo` para `ready`
- revisar ordem do board sem quebrar as prioridades P0
- revisar se surgiram novos IDs operacionais derivados que merecem entrar na matriz sem inflar este board

### Gate de Promocao

Antes de promover para staging serio:

- nenhum P0 critico de auth/compliance deve permanecer em `todo`
- pelo menos um caminho de restore deve estar testado
- gates minimos de CI/CD devem estar ativos
- a matriz operacional deve registrar a evidência mais recente da janela séria e seu risco associado

## Suposicoes

- a ordem atual privilegia maturidade tecnica e regulatoria acima de feature velocity
- o time consegue executar auth, backend core e platform em paralelo parcial
- os owners sugeridos serao adaptados conforme a composicao real do time
- a baseline oficial do board passou a ser `89%`, refletindo o fechamento do `P0-03`, do `P0-04` no core endurecido, a institucionalizacao dos quality gates e a trilha executavel de janela seria para `staging`
