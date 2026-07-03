# Análise Completa do Projeto Ontrackchain e Roadmap de Continuação

**Data:** 2026-07-02  
**Maturidade Atual:** 91% técnica / 78% regulatória / 87% consolidada  
**Sprint Vigente:** 6 concluída, próximo: 7 (Q3 2026)

---

## 1. ESTADO ATUAL DO PROJETO

### 1.1 O Que Foi Construído (Sprint 1-6)

#### Núcleo Arquitetural ✅
- Stack multi-tenant: FastAPI + Next.js 14 + PostgreSQL + Redis
- Docker Compose com Traefik gateway, Prometheus, Grafana, Alertmanager
- RLS (Row-Level Security) por organização
- Migrations controladas com histórico auditável

#### Camada de Compliance Core ✅
1. **Sanctions Screening**
   - `sanctions_lists_meta`: metadata de feeds (UN, EU, OFAC, etc)
   - `sanctions_hits_cache`: triagem local de PEPs e entidades
   - `check_sanctions_sync_status.py`: validação de sincronização
   - Feed local sem dependência de API por request

2. **Preventive Blocks**
   - `preventive_blocks`: bloqueio por contra-parte/endereco/operacao
   - Hash determinístico por base regulatória
   - Fluxo de lift controlado com aprovação

3. **Counterparties & Due Diligence**
   - `counterparties` + `counterparty_history`: KYC/KYB + PEP tracking
   - `DD/SoF` manual review estruturado (4 campos: `ddReviewStatus`, `sofDescription`, `sofDocumentRef`, `ddReviewNote`)
   - Histórico rastreado em workspace

4. **ROS/COAF (Risk on Screen / Customer Due Diligence)**
   - Geração, aprovação/rejeição, submissão manual auditada
   - Status colorido com timeline

5. **Evidence Trail**
   - Append-only com encadeamento SHA-256
   - Rastreamento de eventos com source of truth único
   - Integração em todos os cockpits

#### Fila Operacional Compartilhada ✅
- `regulatory_work_items`: fila multiusuário persistida por módulo/recurso
- `regulatory_work_events`: eventos estruturados com timestamp
- `regulatory_work_comments`: discussão inline com owner_user_id
- Sincronia entre backend → frontend via `/api/app/operations/work-items`

#### Frontend Operacional - 7 Cockpits ✅
1. **Counterparties** (`/counterparties`)
   - DD/SoF manual review + histórico workspace
   - Status colorido, filtro por risco
   - i18n pt-BR/en/es

2. **Sanctions** (`/sanctions`)
   - Triagem por endereço/PEP
   - Painel histórico com filtro cliente
   - i18n tri-locale

3. **Evidence** (`/evidence`)
   - Timeline de eventos com navegação
   - Rastreamento de cadeia de custódia
   - i18n tri-locale

4. **Reports** (`/reports`)
   - Casos rastreados com busca
   - Painel histórico com status
   - i18n tri-locale

5. **Blocks** (`/blocks`)
   - Avaliações históricas de bloqueio
   - Status com timeline
   - i18n tri-locale

6. **ROS/COAF** (`/ros-coaf`)
   - Registros com status colorido
   - Histórico de aprovações/rejeições
   - i18n tri-locale

7. **Alerts** (`/alerts`)
   - Rastreamento por incidente
   - Sincronização de fechamento via `ack`
   - i18n tri-locale

#### Componentes Reutilizáveis ✅
- `WorkItemTimelinePanel`: painel universal de histórico com filtro/busca
- `WorkItemTimeline`: componente de timeline com comentários
- `work-item-timeline-client.ts`: sincronização com backend
- `work-item-timeline-labels.ts`: labels por tipo de evento
- `ownership.ts`: rastreamento de owner_user_id

#### Testes e Validação ✅
- Smoke tests: `smoke_runtime.py`, `smoke_work_items_ownership_backend.py`
- E2E: `timeline-workspace.spec.ts`
- Preflights: `preflight_oidc_serious_env.py`, `preflight_external_integrations.py`
- CI/CD: GitHub Actions com quality gates

#### Governança e Documentação ✅
- 28 documentos canônicos ativos
- 16 templates e tracking semanal em `governance-weekly/`
- 22 arquivos históricos em archive/
- Audit trail: `DOCUMENTATION_AUDIT_2026_07_02.md`
- Zero referências quebradas

---

## 2. O QUE AINDA FALTA (Gaps Residuais)

### 2.1 P0 — Bloqueadores de Prontidão Regulatória

#### P0-01: OIDC + MFA Federado Sério ⏳ `blocked` (78% → 88% se concluído)
**Status:** Trilho pronto, falta homologação formal recorrente

**O que já existe:**
- `auth-service` com suporte OIDC via Keycloak
- MFA TOTP local prototipado
- `preflight_oidc_serious_env.py` que valida o desenho
- Claims mapping estruturado

**O que falta:**
- Integração com provider real (e.g., Azure Entra ID, Auth0)
- Validação de certificados/tokens do provider
- Execução recorrente em ambiente sério
- Prova de funcionamento com usuários reais
- Aceite institucional formal

**Esforço estimado:** 8-10 dias (com credenciais disponíveis)

**Próximas ações:**
- [ ] Obter credenciais do provider de produção (Entra ID / Auth0 / outro)
- [ ] Configurar e validar certificados
- [ ] Executar `make run-serious-window-local AUTH_MODE=oidc` com sucesso
- [ ] E2E: `npm run test:e2e:oidc-critical` passando em ambiente sério
- [ ] Documentar runbook de setup OIDC para recorrência
- [ ] Aceite assinado da trilha por sponsor técnico

---

#### P0-02: AML/KYT Live (Provider Real) ⏳ `ready` (72% → 90% se concluído)
**Status:** Gate de runtime pronto, falta credencial real

**O que já existe:**
- `check_compliance_provider_runtime.py`: valida endpoint do provider
- `run_regulatory_readiness_bundle.py`: integra runtime AML/KYT + janela UE
- `compliance-api` com lógica de triagem estruturada
- Fallback local quando provider indisponível

**O que falta:**
- Credenciais reais de provider (TRM, Refinitiv, Actinver, etc)
- Chave de API e autenticação configurada
- Teste de conexão verde em `make check-compliance-provider-runtime`
- Histórico de JSONs de prova persistidos em `artifacts/staging/checks/`
- Aceite de que provider é homologado e ready para recorrência

**Esforço estimado:** 5-7 dias (com credenciais disponíveis)

**Próximas ações:**
- [ ] Obter credenciais e endpoint do provider AML/KYT
- [ ] Configurar `COMPLIANCE_PROVIDER_*` em `.env.staging.private`
- [ ] Executar: `make check-compliance-provider-runtime` → verde
- [ ] Executar: `make run-regulatory-readiness-bundle` → JSONs persistidos
- [ ] Validar que `sanctions_hits`, `aml_hits`, `aml_matches` retornam dados reais
- [ ] E2E: `npm run test:e2e` com provider real integrado
- [ ] Documentar runbook de setup provider para recorrência
- [ ] Aceite assinado

---

#### P0-03: Feed UE Tokenizado Real ⏳ `ready` (70% → 85% se concluído)
**Status:** Runner pronto, falta URL tokenizada real

**O que já existe:**
- `run_eu_sanctions_window.py`: runner para janela UE
- `make run-eu-sanctions-window-local` e targets equivalentes
- Checker integrado em `run_regulatory_readiness_bundle.py`
- JSONs de saída: `<janela>-eu-sanctions-preflight.json`, `<janela>-eu-sanctions-sync.json`

**O que falta:**
- URL tokenizada real da API de sancoes EU (e.g., CFTI, Deloitte, etc)
- Validação que URL é reachable e retorna dados
- Histórico de JSONs persistidos em artifacts/
- Prova recorrente de sincronização bem-sucedida
- Integração em janela seria real com dossier aceito

**Esforço estimado:** 4-6 dias (com URL disponível)

**Próximas ações:**
- [ ] Obter URL tokenizada real de feed UE
- [ ] Configurar `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` em `.env.staging.private`
- [ ] Executar: `make run-eu-sanctions-window-local` → verde
- [ ] Validar JSONs de prova: `eu-sanctions-preflight.json`, `eu-sanctions-sync.json`
- [ ] Integrar em `run_regulatory_readiness_bundle.py`
- [ ] E2E: smoke test com feed UE real
- [ ] Documentar runbook de sincronização EU para recorrência
- [ ] Aceite assinado

---

### 2.2 P1 — Consolidação Operacional (Sprint 6-7)

#### P1-01: DD/SoF Manual Review Estruturado ✅ `done`
**Status:** Painel entregue em Sprint 6

**Entregáveis:**
- Painel em `/counterparties` com 4 campos: `ddReviewStatus`, `sofDescription`, `sofDocumentRef`, `ddReviewNote`
- Metadata persistida em `work-item`
- Histórico rastreado com timeline/comments
- i18n pt-BR/en/es

---

#### P1-02: Histórico de Cockpits Compartilhado ✅ `done`
**Status:** Todos os 7 cockpits entregues em Sprint 6

**Entregáveis:**
- `counterparties`: DD/SoF + histórico
- `sanctions`: triagem por endereço + histórico
- `evidence`: timeline de eventos + historico
- `reports`: casos rastreados + histórico
- `blocks`: avaliações históricas
- `ros-coaf`: registros históricos
- `alerts`: rastreamento por incidente + histórico

---

#### P1-03: Ownership e Assignment Formalizado ⏳ `in_progress` (75% → 90% se concluído)
**Status:** Estrutura pronta, falta aprovação institucional

**O que já existe:**
- `owner_user_id` rastreado em `regulatory_work_items`
- Assignment por cockpit consolidado
- UI com seletor de owner em cada item
- `operational-ownership-and-slas.md` com matriz de owners

**O que falta:**
- Formalizar lista de owners aprovados por domínio
- SLAs de resposta por severidade aceitos
- Runbook de escalação e handoff
- Prova recorrente de assignment respeitado
- Aceite formal de ownership por stakeholder

**Esforço estimado:** 3-5 dias

**Próximas ações:**
- [ ] Reunir lista definitiva de owners por domínio (Auth, Compliance, Investigation, Platform, Security)
- [ ] Definir SLAs de resposta por severidade (Critical: 1h, High: 4h, Medium: 1d, Low: 5d)
- [ ] Criar runbook de escalação cross-domain
- [ ] Validar que UI respeita assignment
- [ ] E2E: assignment workflow com múltiplos owners
- [ ] Obter aceite assinado de ownership

---

### 2.3 P2 — Governança Formal (T2 2026)

#### P2-01: Sign-off de Retention/Recovery ⏳ `in_progress` (78% → 95% se concluído)
**Status:** Política publicada, aceite pendente

**O que já existe:**
- `retention-and-recovery-policy.md` com período de retenção (7 anos para audit logs, etc)
- Backup automático via Docker volumes
- Restore playbook documentado
- Tests de restore em ambiente local

**O que falta:**
- Execução real de restore em dados de produção (simulação)
- Prova de integridade (checksums, hashes)
- Aceite formal do CTO/Security Lead
- Documentação de SLA de recovery
- Teste anual obrigatório registrado

**Esforço estimado:** 5-7 dias

**Próximas ações:**
- [ ] Simular restore de backup de 6 meses atrás
- [ ] Validar integridade com queries spot checks
- [ ] Documentar tempo de RTO (Recovery Time Objective)
- [ ] Documentar RPO (Recovery Point Objective)
- [ ] Obter assinatura de aceite formal
- [ ] Agendar teste anual

---

#### P2-02: Janela Sería Recorrente ⏳ `in_progress` (80% → 95% se concluído)
**Status:** Rito pronto, falta executar com aceite

**O que já existe:**
- `run_staging_window.py` + `run_regulatory_readiness_bundle.py` prontos
- War room template e matriz de execução
- Dossier builder
- Manual fill sheet
- E2E com smoke tests

**O que falta:**
- Executar janela real com stakeholders presentes
- Coletar evidências (outputs, logs, JSONs)
- Dossier final aceito por compliance/legal
- Registrar lições aprendidas
- Agendar próxima janela (recorrência)

**Esforço estimado:** Evento de 1-2 dias + 3 dias de prep

**Próximas ações:**
- [ ] Agendar janela seria para próxima semana (quando P0-02 e P0-03 estiverem ready)
- [ ] Preparar `.env.staging.private` com todos os placeholders preenchidos
- [ ] Executar full war room com owners, bridge, facilitation
- [ ] Persistir dossier final
- [ ] Obter aceite assinado do compliance lead
- [ ] Publicar retrospectiva
- [ ] Agendar próxima janela (cadência recomendada: quinzenal ou mensal)

---

#### P2-03: Formalizar SLA e Runbooks ⏳ `in_progress`
**Status:** Estrutura pronta, falta aprovação

**O que já existe:**
- `operational-ownership-and-slas.md` com matriz de owners
- Runbooks por sintoma em `runbooks.md`
- War room matrix de execução
- Governance semanal template

**O que falta:**
- Aceite formal do COO/Ops Lead
- Comunicação aos teams
- Treinamento de runbooks
- Teste de acionamento (drill)
- Versionamento de SLAs

**Esforço estimado:** 2-3 dias

**Próximas ações:**
- [ ] Apresentar SLAs/owners ao COO
- [ ] Treinar teams em runbooks críticos
- [ ] Fazer drill de incident response
- [ ] Coletar feedback e atualizar docs
- [ ] Obter aceite assinado

---

### 2.4 P3 — Cadeia de Custódia Forte (T3 2026)

#### P3-01: Vault/Secrets de Produção ⏳ `todo`
**Status:** Desenho pendente

**O que falta:**
- Escolher vault (HashiCorp Vault, Azure Key Vault, AWS Secrets Manager)
- Migrar secrets de `.env` para vault
- Integrar auth-service e compliance-api
- Rotação automática de credenciais
- Auditoria de acesso a secrets

**Esforço estimado:** 10-14 dias

---

#### P3-02: Selagem/Assinatura de Evidence Trail ⏳ `todo`
**Status:** Desenho pendente

**O que falta:**
- Integrar PKI ou HSM para assinatura digital
- Estender `evidence_trail` com assinatura por entry
- Verificação de integridade periódica
- Certificado válido em produção

**Esforço estimado:** 15-20 dias

---

#### P3-03: War Room, Escalação e RCA ⏳ `todo`
**Status:** Template pronto, falta formalizar

**O que falta:**
- Playbook de incident response cross-domain
- Matriz de escalação por severidade
- Template de RCA (Root Cause Analysis)
- Treinar teams

**Esforço estimado:** 5-7 dias

---

#### P3-04: Automatizar Promoção Staging → Produção ⏳ `todo`
**Status:** Desenho pendente

**O que falta:**
- GitHub Actions workflow para promotion
- Quality gates antes da promoção
- Rollback playbook
- Aprovações formais integradas

**Esforço estimado:** 8-12 dias

---

## 3. ANÁLISE DE IMPACTO

### 3.1 Simulação de KPI com Completude de P0-P2

Se todos os P0 forem concluídos:
```
Técnica: 91% → 95% (provider real + OIDC operacional)
Regulatória: 78% → 92% (providers + sign-off + recorrência)
Consolidada: 87% → 93% (ponderação 70/30)
```

Se também P2 completos:
```
Técnica: 95% (estável)
Regulatória: 92% → 95% (ownership formalizado)
Consolidada: 93% → 95% (ponderação 70/30)
```

---

## 4. ROADMAP RECOMENDADO (Sprint 7-9)

### Sprint 7 (Próximos 7 dias) — P0 Ready

**Foco:** Obter credenciais e validar P0-02 e P0-03

- [ ] Obter credenciais de provider AML/KYT
- [ ] Obter URL tokenizada feed UE
- [ ] Executar `make check-compliance-provider-runtime` → verde
- [ ] Executar `make run-eu-sanctions-window-local` → verde
- [ ] E2E passa com providers reais
- [ ] Aceites assinados

**KPI esperado:** 87% → 89% consolidada

---

### Sprint 8 (7-14 dias) — P1 Completo + P2 Início

**Foco:** Janela sería com P0-02 e P0-03

- [ ] Validar `regulatory_readiness_bundle` com providers reais
- [ ] Executar janela sería com owners presentes
- [ ] Dossier final aceito
- [ ] Formalizar ownership e SLAs
- [ ] Início de sign-off retention/recovery

**KPI esperado:** 89% → 91% consolidada

---

### Sprint 9 (7-14 dias) — P0-01 + P2 Conclusão

**Foco:** OIDC homologado + janela recorrente

- [ ] Provider OIDC integrado e testado
- [ ] Segunda janela sería executada
- [ ] Sign-off retention/recovery formalizado
- [ ] Runbooks aprovados

**KPI esperado:** 91% → 93-94% consolidada

---

### T3 2026 (Trimestre 3) — P3 Implementação

**Foco:** Cadeia de custódia forte

- [ ] Vault implementado
- [ ] Selagem de evidence trail
- [ ] RCA playbook
- [ ] Promoção automatizada

**KPI esperado:** 94% → 95%+ consolidada

---

## 5. DEPENDÊNCIAS CRÍTICAS

| Iniciativa | Bloqueador | Dono | Prazo |
| --- | --- | --- | --- |
| P0-02 AML/KYT | Credenciais provider | Compliance Lead | ASAP |
| P0-03 Feed UE | URL tokenizada | Regulatory/Ops | ASAP |
| P0-01 OIDC | Provider credentials + policy | Security Lead | 1-2 sem |
| P1-03 Ownership | Stakeholder approval | COO | 1 sem |
| P2-01 Sign-off Retention | Teste de restore real | CTO/Security | 2 sem |
| P2-02 Janela Recorrente | Providers P0 operacionais | Ops Lead | 3 sem |
| P3-01 Vault | Arquitetura cloud | Infra Lead | T3 |
| P3-02 Selagem | Decision PKI/HSM | Security Lead | T3 |

---

## 6. RECOMENDAÇÕES FINAIS

### ✅ Força Atual
1. **Plataforma técnica madura:** 91% com todos os cockpits operacionais
2. **Trilha regulatória estruturada:** Componentes prontos, falta homologação
3. **Documentação consolidada:** Zero referências quebradas, 28 docs canônicos
4. **Testes robustos:** Smoke, E2E, preflights bem institucionalizados
5. **Timeline/Comments universal:** Reusabilidade máxima em todos os 7 cockpits

### ⚠️ Gaps Críticos
1. **Providers reais:** AML/KYT e Feed UE ainda não homologados
2. **OIDC federado:** Trilho pronto, falta provider de produção
3. **Prova recorrente:** Falta institucionalizar execução periódica de janelas
4. **Sign-offs formais:** Retention/recovery, ownership, SLAs ainda pendentes
5. **Escalation formalizado:** Playbook de RCA e incident response não estruturado

### 🎯 Próximos Passos (Imediatos)
1. **Reunir credenciais:** Contatar providers de AML/KYT e feed UE
2. **Preparar janela seria:** Com providers reais assim que credenciais disponíveis
3. **Formalizar ownership:** Reunir COO e domínios para aceite de SLAs
4. **Agendar sign-offs:** Compliance lead para retention/recovery

### 📈 Potencial de Maturidade
- **90% consolidada** em 3 semanas (com credenciais disponíveis)
- **95% consolidada** em 6-8 semanas (com janelas recorrentes + P2 completo)

---

## Apêndice: Arquivos de Referência

- **Maturity:** `docs/project-maturity-assessment.md`
- **KPI:** `docs/project-kpi-scorecard.md`
- **Prioridades:** `docs/project-priority-board.md`
- **Operação:** `docs/operational-ownership-and-slas.md`
- **Riscos:** `docs/project-risk-register.md`
- **Staging:** `docs/deploy-and-staging.md`
- **Governance Semanal:** `docs/governance-weekly/2026-07-06-weekly-governance.md`
