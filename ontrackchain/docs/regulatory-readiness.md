# Readiness Regulatorio

## Objetivo

Consolidar o estado atual do scaffold frente a requisitos de operacao mais regulada, com foco em trilha auditavel, controles de acesso, billing rastreavel e capacidade de produzir evidencias.

Este documento nao substitui parecer juridico ou validacao formal de compliance. Ele serve para:

- mapear controles tecnicos existentes
- identificar gaps reais
- orientar a Fase 2
- apoiar readiness para staging regulado

## Resumo Executivo

Leituras oficiais recomendadas:

- `76%` de prontidao para producao regulada
- `89%` de construcao tecnica como plataforma funcional

Interpretacao:

- a base tecnica do produto esta forte, mas a prontidao regulatoria continua atrasada em relacao a maturidade de engenharia
- os maiores bloqueios regulatórios reais seguem concentrados em identidade forte homologada, integracoes externas reais, cadeia de custodia formal e aceite operacional
- parte importante do gap deixou de ser falta de implementacao e passou a ser falta de homologacao, sign-off e execucao em ambiente serio

`[[diagram: mapa de readiness regulatorio do Ontrackchain mostrando camadas de governanca, autenticacao, RLS, billing, auditoria, reports e evidencias; cada camada ligada a controles tecnicos implementados e gaps residuais para operacao regulada ]]`

## Escopo de Readiness

O estado atual do projeto suporta readiness tecnico inicial para:

- trilha de auditoria
- isolamento multi-tenant
- controle de acesso reforcado em fluxos sensiveis
- correlacao de requests e eventos
- reproducao de relatorios e hash

Ainda nao suporta, por si so, readiness regulatorio pleno para producao.

## Mapa de Requisitos e Cobertura

| Requisito | Estado Atual | Evidencia Tecnica | Gap |
| --- | --- | --- | --- |
| Isolamento entre clientes | Coberto | `RLS`, contexto SQL, policies por organizacao | ampliar testes negativos de acesso |
| Rastreabilidade de operacoes | Coberto parcialmente | `audit_logs`, `request_id`, `report_downloaded`, export bundles e dossier de janela | retention formalmente aprovada e cadeia de custodia externa |
| Controle de acesso privilegiado | Coberto parcialmente | `legal_report` exige `JWT + ADMIN + 2FA`; superficies administrativas dependem de `X-Role` derivado pelo gateway a partir de `JWT` ou `API Key` | expandir semantica fina por dominio e reduzir ambiguidade operacional |
| Integridade documental | Coberto | `report_id` e `file_hash_sha256` deterministas | assinatura/selagem externa futura |
| Billing auditavel | Coberto | `quote -> start -> PRE_HOLD -> CONFIRMED/REFUND` | reconciliacao financeira mais rica |
| Segregacao de papeis | Coberto parcialmente | `X-Role` propagado pelo gateway, leitura privilegiada `ADMIN` ou `AUDITOR`, mutacoes `ADMIN` e `legal_report` com auth forte | ampliar granularidade para `ANALYST`, `TESTER` e `VIEWER` |
| Evidencia de screening/risk | Coberto parcialmente | `risk-check`, `report_generated`, baseline COAF | schema regulatorio mais forte |
| Autenticacao forte | Coberto parcialmente | fluxo local com JWT + `TOTP` real, caminho `OIDC` exercitado e separacao explicita entre MFA local e MFA do IdP | IdP corporativo e secrets de producao |
| Resposta a incidente | Coberto parcialmente | runbooks publicados, owners e SLA base operacionais | aceite formal e exercicio em ambiente serio |
| Governanca de retenção | Coberto parcialmente | politica publicada, owners nomeados, backup/restore evidenciados | sign-off formal de Security/Compliance e operacao recorrente |

## Controles Tecnicos Relevantes

### Isolamento de Dados

- `PostgreSQL RLS`
- validacao segura de API Key
- separacao por `organization_id`

### Auditoria

- `audit_logs`
- correlacao por `X-Request-Id`
- trilha de:
  - `case_started`
  - `case_completed`
  - `case_failed`
  - `compliance_risk_checked`
  - `report_generated`
  - `report_downloaded`
  - `operational_alerts_exported`

### Acesso a Recursos Sensíveis

- `legal_report` exige:
  - JWT
  - role `ADMIN`
  - `2FA`

### Integridade de Relatorios

- `report_id` deterministico
- `created_at` reproduzivel
- `file_hash_sha256` validado em smoke

### Billing e Trilha Financeira

- quote com TTL
- bloqueio de drift de plano
- ledger append-only com metadados

### Release e Evidencias Operacionais

- preflights serios de `OIDC`, AML/KYT e RPC
- `window packet` redigido por janela de `staging`
- dossier consolidado de release com `sha256`
- runner unico `run_staging_window.py` para checks, homologacao e anexos

## Evidencias Produzidas Hoje

O sistema ja consegue produzir evidencias tecnicas uteis para auditoria interna:

- logs de auditoria por acao
- correlacao request -> case -> report -> hash
- trilha de cobranca por quote e ledger
- prova de bloqueio antes do 2FA
- prova de download autorizado apos 2FA
- evidencia anexavel de backup/restore com manifesto
- artefatos anexaveis de homologacao externa e release dossier

## Gaps Regulatorios Reais

### 1. Autenticacao e Identidade

- `TOTP` ja e real no fluxo local, mas permanece restrito ao caminho `JWT` do scaffold
- no modo `OIDC`, o segundo fator ja e tratado como responsabilidade do provedor, porem isso ainda nao foi homologado com politica corporativa real de MFA
- nao ha ciclo formal de onboarding/offboarding de usuarios
- faltam secrets e politicas de identidade de producao

### 2. Retencao e Cadeia de Custodia

- a politica de retention minima ja existe, mas ainda nao possui aceite formal de Security/Compliance
- nao ha exportacao assinada de auditoria
- nao ha classificacao de evidencias por sensibilidade

### 3. Operacao e Governanca

- runbooks, owners e SLA base ja existem, mas ainda sem aceite formal e sem exercicio recorrente em ambiente serio
- falta rito operacional institucionalizado de war room, escalacao e RCA
- falta prova recorrente de uso desses artefatos fora do contexto local

### 4. Compliance de Conteudo

- baseline COAF/BCB existe, mas nao e schema regulatorio final
- falta versionamento formal dos templates de relatorio
- falta classificacao das justificativas e achados

### 5. Seguranca Operacional

- faltam secrets/vault de producao
- backup e restore ja foram testados, mas ainda faltam rotina operacional e governanca formal de producao
- faltam alertas de seguranca e telemetria centralizada

- o corte administrativo principal de `RBAC` ja existe, mas ainda nao ha papel fino por dominio para operacoes core
- `ANALYST`, `TESTER` e `VIEWER` seguem canônicos no auth, porem ainda nao representam perfis regulatoriamente fechados no backend

## Roadmap Recomendado de Adequacao

### Curto Prazo

- homologar `OIDC` e MFA serio com segredos nao-dev
- concluir provider real AML/KYT e RPC com evidencias de janela seria
- fechar sign-off formal de retention/recovery e owners operacionais
- exercitar `run_staging_window.py` em ambiente serio controlado

### Medio Prazo

- reduzir stubs remanescentes de compliance
- publicar workflow recorrente de incidente, escalacao e RCA
- versionar templates e schemas de relatorio
- fortalecer security monitoring e telemetria cross-domain
- transformar baseline de staging serio em rito oficial de promocao

### Antes de Producao Regulada

- IdP real + MFA real
- retention/backup/export seguros
- RBAC completo
- documentacao de controle com owner
- trilha de aprovacao e revisao de relatorios sensiveis

## Critério de Prontidão para Staging Regulado

O projeto pode ser considerado pronto para um staging regulado quando:

- autenticacao nao depender mais de fluxo dev
- `2FA` real estiver implementado fora do contexto apenas local ou federado pelo IdP corporativo com politica auditavel
- auditoria estiver consultavel pela operacao
- eventos negados sensiveis forem persistidos
- retention minima estiver definida
- runbooks de incidente estiverem documentados
- smoke e Playwright continuarem verdes apos essas mudancas

## Caminho de 76% para 95%

### Faixa 1 — 76% para 82%

Objetivo:

- remover os maiores bloqueadores regulatórios de identidade e integração externa

Entregas:

- `OIDC` serio homologado com secrets nao-dev
- MFA federado ou operacionalizado com politica auditavel
- provider AML/KYT real com evidencias
- RPC primario + fallback homologados

Ganho estimado:

- `+6 pontos`

### Faixa 2 — 82% para 89%

Objetivo:

- transformar baseline tecnica em governanca aceita

Entregas:

- sign-off formal de retention/recovery
- sign-off formal de owners/SLA/runbooks
- execucoes reais de janela com dossier anexado
- classificacao minima de evidencias por sensibilidade

Ganho estimado:

- `+7 pontos`

### Faixa 3 — 89% para 95%

Objetivo:

- aproximar o projeto de uma operacao regulada convincente, ainda sem declarar prontidao plena de producao

Entregas:

- vault e secrets management de producao
- incident response com war room, escalacao e RCA formal
- assinatura/selagem externa ou trilha equivalente de cadeia de custodia
- granularidade regulatoria adicional de papeis por dominio

Ganho estimado:

- `+6 pontos`

## Decisao Recomendada

Leitura recomendada:

- o projeto nao deve ser tratado como pronto para producao regulada
- a leitura honesta atual e `76%`
- o caminho mais eficiente para elevar essa nota passa primeiro por homologacao seria e sign-off formal, nao por criar novas features adjacentes

## Não Objetivos Deste Documento

- definir interpretacao juridica oficial
- substituir politica corporativa de seguranca
- atuar como especificacao legal final
