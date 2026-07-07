# Plano Tático Sprint 7-9: Escalação Controlada para 95%

**Versão:** 1.0
**Data:** 2026-07-02
**Liderado por:** Arquitetura / Compliance
**Stakeholders:** Tech Lead, Compliance Lead, COO, Ops Manager

> Aviso de classificacao: este documento e um planejamento datado do ciclo Sprint 7-9. Para a leitura viva de prioridades e execucao, use primeiro o [Board de Prioridades do Projeto](../project-priority-board.md), o [Board Operacional Unico](../project-operational-execution-board.md), o [Resumo Executivo de Readiness](../project-executive-readiness-brief.md) e o [Kit de Execucao por Evidencia](../project-maturity-evidence-execution-kit.md).

---

## Objetivo

Elevar o KPI consolidado de **87%** para **95%** em 9 semanas through:
1. Validação de provedores P0 (AML/KYT, Feed UE)
2. Formalização de governança P1-P2 (ownership, SLAs, sign-offs)
3. Execução recorrente de janelas sérias com aceites

---

## Sprint 7 (Semana de 02-08 de julho) — Validação P0

**Meta:** Verde em P0-02 e P0-03; preparação P0-01

### Tarefas Críticas

#### T7.1: Aquisição de Credenciais AML/KYT (P0-02)
- **Owner:** Compliance Lead
- **Prioridade:** CRÍTICA
- **Esforço:** 2 dias (1 dia negociação + 1 dia setup)
- **Dependência:** External (provider real)
- **Tarefas:**
  - [ ] Contato com TRM/Refinitiv/Actinver para credencial de produção
  - [ ] Obter chave API + endpoint + certificados
  - [ ] Documentar credenciais em `.env.staging.example` como `__FILL_COMPLIANCE_PROVIDER_API_KEY__`
  - [ ] Preencher em `.env.staging.private` (fora do repo)
  - [ ] Testar conexão em local: `make check-compliance-provider-runtime COMPLIANCE_PROVIDER_URL=<endpoint>`

**Critério de Sucesso:**
- `COMPLIANCE_PROVIDER_READY=true` retorna verde no check
- JSON de resposta com AML matches encontrados

**Entregável:**
- [ ] `artifacts/staging/checks/<janela>-compliance-provider-check.json` populado

---

#### T7.2: Aquisição de URL Feed UE (P0-03)
- **Owner:** Regulatory/Ops Manager
- **Prioridade:** CRÍTICA
- **Esforço:** 2 dias (1 dia negociação + 1 dia setup)
- **Dependência:** External (URL tokenizada real)
- **Tarefas:**
  - [ ] Contato com CFTI/Deloitte/provider de feed UE para URL tokenizada
  - [ ] Obter URL, validar reachability
  - [ ] Documentar em `.env.staging.example` como `__FILL_COMPLIANCE_EU_SANCTIONS_SOURCE_URL__`
  - [ ] Preencher em `.env.staging.private`
  - [ ] Executar: `make run-eu-sanctions-window-local WINDOW_ID=validation-eu COMPLIANCE_EU_SANCTIONS_SOURCE_URL=<url>`

**Critério de Sucesso:**
- `artifacts/staging/<janela>-eu-sanctions-preflight.json` retorna 0 errors
- `artifacts/staging/<janela>-eu-sanctions-sync.json` contém hits válidos

**Entregável:**
- [ ] JSONs de prova persistidos

---

#### T7.3: Setup do Provider OIDC (P0-01 — Preparação)
- **Owner:** Security/Auth Lead
- **Prioridade:** ALTA
- **Esforço:** 3 dias (desenho + setup + validação)
- **Dependência:** External (provider credentials)
- **Tarefas:**
  - [ ] Escolher provider (Azure Entra ID / Auth0 / outro)
  - [ ] Solicitar credenciais e documentação
  - [ ] Configurar `OIDC_PROVIDER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` em local
  - [ ] Executar local: `make up-local AUTH_MODE=oidc`
  - [ ] Validar preflight: `python scripts/preflight_oidc_serious_env.py`
  - [ ] Testes E2E: `npm run test:e2e:oidc-critical` no `/apps/frontend`

**Critério de Sucesso:**
- Login OIDC funciona com usuário de teste
- MFA (TOTP) valida corretamente
- E2E passa

**Entregável:**
- [ ] `.env` local com OIDC_* configurados (não committado)
- [ ] Runbook: `docs/keycloak-oidc-template.md` atualizado com steps do provider

---

#### T7.4: Testes de Integração P0-02 + P0-03
- **Owner:** QA / Tech Lead
- **Prioridade:** ALTA
- **Esforço:** 2 dias
- **Dependência:** T7.1, T7.2
- **Tarefas:**
  - [ ] Preencher `.env.staging.private` com credenciais de T7.1 e T7.2
  - [ ] Executar: `python scripts/run_regulatory_readiness_bundle.py --window-id sprint-7-validation --mode comprehensive`
  - [ ] Validar JSONs de output: compliance-provider-check, eu-sanctions-preflight, eu-sanctions-sync
  - [ ] Executar E2E smoke com providers reais: `npm run test:smoke-providers-real` (novo target)
  - [ ] Documentar qualquer delta com baseline local

**Critério de Sucesso:**
- Bundle completion rate ≥ 95%
- Todos os JSONs válidos e persistidos
- E2E passa

**Entregável:**
- [ ] `artifacts/staging/sprint-7-validation-bundle.md` com resumo

---

#### T7.5: Preparação da Janela 01 de Staging Sério
- **Owner:** Ops Manager
- **Prioridade:** ALTA
- **Esforço:** 3 dias (prep + review + ajustes)
- **Dependência:** T7.1-T7.4
- **Tarefas:**
  - [ ] Agendar war room para Sprint 8 (week of 09-15 July)
  - [ ] Preparar `docs/staging-env-ownership.md` com owners reais por domínio
  - [ ] Atualizar `.env.staging.example` com todos os placeholders documentados
  - [ ] Criar `docs/governance-weekly/2026-07-09-staging-serious-window-war-room.md` (usando template)
  - [ ] Distribuir manual fill sheet aos owners
  - [ ] Preparar bridge channels (Slack, Teams, etc)

**Critério de Sucesso:**
- Todos os owners confirmados
- Placeholder coverage = 100%
- War room agendado com ~10 participantes

**Entregável:**
- [ ] Manual fill sheet preenchido 80% (faltam apenas secrets)
- [ ] War room agenda com times

---

#### T7.6: Documentação e Aceites P0
- **Owner:** Compliance Lead / Tech Lead
- **Prioridade:** MÉDIA
- **Esforço:** 1 dia
- **Dependência:** T7.1-T7.5
- **Tarefas:**
  - [ ] Atualizar `docs/deploy-and-staging.md` com P0-02 e P0-03 prontos
  - [ ] Criar runbook de setup AML/KYT para recorrência
  - [ ] Criar runbook de setup Feed UE para recorrência
  - [ ] Obter e-mail assinado de Compliance Lead indicando P0-02 ready
  - [ ] Obter e-mail assinado de Regulatory indicando P0-03 ready

**Critério de Sucesso:**
- Runbooks escritos e revisados
- Aceites assinados

**Entregável:**
- [ ] `docs/setup-aml-provider-prod.md`
- [ ] `docs/setup-eu-sanctions-feed-prod.md`
- [ ] E-mails de aceite em `artifacts/sprint-7/`

---

### Métricas Sprint 7

| Métrica | Inicial | Target | Comentário |
| --- | ---: | ---: | --- |
| P0-02 AML/KYT | 72% | 85% | Credencial validada, falta janela seria recorrente |
| P0-03 Feed UE | 70% | 82% | URL tokenizada validada, falta janela seria recorrente |
| P0-01 OIDC | 78% | 80% | Setup local pronto, falta provider real |
| Consolidada | 87% | 88% | Mínima de validação local |

---

## Sprint 8 (Semana de 09-15 de julho) — Janela Sería #1

**Meta:** Executar primeira janela sería com P0-02 e P0-03; formalizar P1

### Tarefas Críticas

#### T8.1: War Room Executivo (1-2 dias)
- **Owner:** Ops Manager / Facilitator
- **Prioridade:** CRÍTICA
- **Tarefas:**
  - [ ] Confirmar presença: Tech Lead, Compliance Lead, Security Lead, Platform/SRE, Finance
  - [ ] Fazer review técnico 24h antes (war room matrix)
  - [ ] Executar PREPARE: `python scripts/prepare_staging_window.py --window-id stg-2026-07-09 --mode baseline`
  - [ ] Executar VALIDATE: `python scripts/prepare_staging_window.py --window-id stg-2026-07-09 --mode baseline --validate`
  - [ ] Executar PREFLIGHT: `python scripts/prepare_staging_window.py --window-id stg-2026-07-09 --mode baseline --preflight`
  - [ ] Go/No-Go: todos os domínios devem estar em status=ready
  - [ ] Se verde, executar RUN: `make run-serious-window-local WINDOW_ID=stg-2026-07-09 MODE=baseline`

**Critério de Sucesso:**
- Preflight passou verde (0 críticos)
- Run completou sem erros
- Todos os 7 cockpits rodaram com dados reais

**Entregável:**
- [ ] `artifacts/staging/serious-window-stg-2026-07-09-packet.md`
- [ ] `artifacts/staging/serious-window-stg-2026-07-09-dossier.md`

---

#### T8.2: Coleta de Evidências
- **Owner:** Tech Lead / QA
- **Prioridade:** CRÍTICA
- **Tarefas:**
  - [ ] Capturar screenshots dos 7 cockpits após run
  - [ ] Persistir JSONs de output: compliance-provider-check, eu-sanctions-preflight, eu-sanctions-sync, evidence-trail
  - [ ] Logs de execution: `docker compose logs > artifacts/sprint-8/window-logs.txt`
  - [ ] Validar checksums de evidence_trail contra baseline anterior
  - [ ] Documentar qualquer exceção ou erro menor

**Entregável:**
- [ ] Pasta `artifacts/sprint-8/` com todos os artefatos

---

#### T8.3: Formalizar Ownership e SLAs (P1-03)
- **Owner:** COO / Ops Manager
- **Prioridade:** ALTA
- **Tarefas:**
  - [ ] Validar que todos os owners em `docs/operational-ownership-and-slas.md` correspondem a usuários reais no Keycloak
  - [ ] Obter assinatura escrita de COO confirmando owners e SLAs
  - [ ] Comunicar aos teams via e-mail/Slack com runbook e escalação
  - [ ] Fazer drill: simular incident crítico com escalação
  - [ ] Documentar resultado do drill

**Critério de Sucesso:**
- Todos os owners confirmados
- Aceite assinado de COO
- Drill completado com sucesso

**Entregável:**
- [ ] `docs/governance-weekly/2026-07-09-ownership-formalized.md`
- [ ] E-mail assinado COO

---

#### T8.4: Preparação de Sign-off Retention/Recovery (P2-01)
- **Owner:** CTO / Security Lead
- **Prioridade:** ALTA
- **Tarefas:**
  - [ ] Planejar teste de restore com dados de 6 meses atrás (simulação)
  - [ ] Executar restore em VM de teste: `docker exec postgres pg_restore --clean --if-exists -d ontrackchain < backup-6-months-ago.sql`
  - [ ] Validar integridade com query spot checks:
    - Count de transactions na evidence_trail antes vs depois
    - Hashes de alguns entries contra baseline
  - [ ] Documentar tempo de RTO (Recovery Time Objective) — deve ser < 30 minutos
  - [ ] Documentar RPO (Recovery Point Objective) — deve ser < 1 hora

**Critério de Sucesso:**
- Restore bem-sucedido
- Integridade validada
- RTO/RPO documentados

**Entregável:**
- [ ] `docs/governance-weekly/2026-07-09-retention-recovery-test.md`

---

#### T8.5: Aceite Compliance da Janela
- **Owner:** Compliance Lead
- **Prioridade:** CRÍTICA
- **Tarefas:**
  - [ ] Revisar dossier `serious-window-stg-2026-07-09-dossier.md`
  - [ ] Validar que todas as evidências obrigatórias estão presentes
  - [ ] Assinar aceite: "A janela sería de 2026-07-09 foi executada com sucesso e pronta para recorrência"
  - [ ] Persistir aceite em `artifacts/sprint-8/`

**Critério de Sucesso:**
- Dossier 100% preenchido
- Assinatura digital ou e-mail formal

**Entregável:**
- [ ] Aceite assinado em `artifacts/sprint-8/compliance-sign-off.txt`

---

#### T8.6: Lições Aprendidas e Próxima Cadência
- **Owner:** Ops Manager
- **Prioridade:** ALTA
- **Tarefas:**
  - [ ] Retrospectiva: o que funcionou, o que quebrou, adjustments
  - [ ] Atualizar runbooks com learnings
  - [ ] Agendar próxima janela sería (recomendação: 2 semanas, ~22-23 de julho)
  - [ ] Documentar em `docs/governance-weekly/2026-07-09-retrospective.md`

**Entregável:**
- [ ] Retrospective doc
- [ ] Próxima janela no calendário

---

### Métricas Sprint 8

| Métrica | Inicial | Target | Comentário |
| --- | ---: | ---: | --- |
| P0-02 AML/KYT | 85% | 90% | Prova recorrente com dados reais |
| P0-03 Feed UE | 82% | 88% | Prova recorrente com dados reais |
| P1-03 Ownership | 75% | 90% | Formalizado e aceito |
| P2-01 Retention | 78% | 90% | Teste executado com sucesso |
| Consolidada | 88% | 91% | Salto significativo com P0 + P2 prova |

---

## Sprint 9 (Semana de 16-22 de julho) — P0-01 Homologação + P2 Conclusão

**Meta:** OIDC homologado; segunda janela sería; 93%+ consolidada

### Tarefas Críticas

#### T9.1: Homologação OIDC (P0-01)
- **Owner:** Security/Auth Lead
- **Prioridade:** CRÍTICA
- **Tarefas:**
  - [ ] Integrar provider OIDC real (Entra ID ou Auth0) em staging
  - [ ] Validar certificados e tokens
  - [ ] E2E: `npm run test:e2e:oidc-critical` passou com provider real
  - [ ] Executar MFA TOTP no trilho sério
  - [ ] Obter aceite de Security Lead

**Critério de Sucesso:**
- Login OIDC + MFA funciona end-to-end
- Aceite assinado

**Entregável:**
- [ ] `docs/setup-oidc-production.md`

---

#### T9.2: Segunda Janela Sería (Recorrência)
- **Owner:** Ops Manager
- **Prioridade:** CRÍTICA
- **Tarefas:**
  - [ ] Executar segunda janela com P0-02, P0-03 e agora P0-01 (OIDC) se pronto
  - [ ] Mesma rigor que Sprint 8
  - [ ] Coletar evidências
  - [ ] Aceite compliance

**Entregável:**
- [ ] `artifacts/sprint-9/serious-window-stg-2026-07-23-*.md`

---

#### T9.3: Formalizar Sign-offs
- **Owner:** Compliance Lead / COO
- **Prioridade:** ALTA
- **Tarefas:**
  - [ ] Consolidar aceites de P0, P1, P2 em documento único
  - [ ] Obter assinaturas de Compliance Lead, COO, CTO, Security Lead
  - [ ] Publicar em `docs/governance-weekly/2026-07-20-formal-sign-offs.md`

**Entregável:**
- [ ] Documento assinado com todos os aceites

---

#### T9.4: Planejamento P3 e Roadmap T3
- **Owner:** Tech Lead / Infra Lead
- **Prioridade:** MÉDIA
- **Tarefas:**
  - [ ] Decisão: Vault (HashiCorp vs Azure Key Vault vs AWS Secrets Manager)
  - [ ] Decisão: PKI/HSM para selagem
  - [ ] Criar backlog P3 com tasks granulares
  - [ ] Estimar esforço para T3

**Entregável:**
- [ ] `docs/p3-roadmap-q3-2026.md`

---

### Métricas Sprint 9

| Métrica | Inicial | Target | Comentário |
| --- | ---: | ---: | --- |
| P0-01 OIDC | 80% | 92% | Homologado e operacional |
| P0-02 AML/KYT | 90% | 92% | Recorrência validada |
| P0-03 Feed UE | 88% | 92% | Recorrência validada |
| P1-03 Ownership | 90% | 95% | Drill completado |
| P2-01 Retention | 90% | 95% | Sign-off formal |
| P2-02 Janelas Recorrentes | 80% | 95% | 2ª janela concluída |
| **Consolidada** | **91%** | **95%** | **META ALCANÇADA** |

---

## Dependências e Riscos

### Riscos Críticos (Mitigation Required)

| Risco | Probabilidade | Impacto | Mitigation |
| --- | ---: | ---: | --- |
| Credenciais AML/KYT não disponíveis | 30% | CRÍTICA | Contatar fornecedor na semana 1; ter fallback teste |
| URL feed UE indisponível | 25% | ALTA | Contatar fornecedor na semana 1; setup mock se necessário |
| Provider OIDC indisponível | 40% | ALTA | Setup local com Keycloak continua válido; estender para 2 semanas |
| Stakeholder sign-offs atrasados | 50% | MÉDIA | Agendar reuniões com 2 semanas de antecedência |
| Restore test falha | 15% | MÉDIA | Praticar em dev primeiro; ter backup de restore playbook |

### Dependências Externas

- [ ] Credenciais AML/KYT — Compliance Lead → Provider (Target: semana 1)
- [ ] URL tokenizada Feed UE — Regulatory → Provider (Target: semana 1)
- [ ] Provider OIDC credentials — Security Lead → Azure/Auth0 (Target: semana 2)
- [ ] Stakeholder availability — Ops → Teams (Target: agora)

---

## Entregas Finais (Ao fim de Sprint 9)

### Documentação
- [ ] Runbook AML/KYT setup
- [ ] Runbook Feed UE setup
- [ ] Runbook OIDC federado
- [ ] Runbook Ownership e escalation
- [ ] Runbook Retention/Recovery com restore prova
- [ ] Retrospective consolidada

### Artefatos
- [ ] 2 janelas sérias completadas com dossier aceito
- [ ] JSONs de prova (compliance-provider-check, eu-sanctions-preflight/sync, evidence-trail)
- [ ] Screenshots dos 7 cockpits operacionais
- [ ] Drill de incident response documentado

### Aceites Formais
- [ ] Compliance Lead: P0-02, P0-03, janelas, recorrência
- [ ] Security Lead: OIDC, MFA, ownership
- [ ] CTO: Retention/Recovery, RTO/RPO
- [ ] COO: SLAs, owners, cadência

### KPI Final
- Técnica: **95%** (consolidada com providers reais)
- Regulatória: **95%** (P0-01-03 operacionais + P2 aceites formais)
- **Consolidada: 95%**
---

## Próximos Passos Imediatos (Esta Semana)

1. **Hoje:**
   - [ ] Compartilhar este plano com Tech Lead, Compliance Lead, COO
   - [ ] Agendar kick-off Sprint 7 amanhã

2. **Amanhã:**
   - [ ] Kick-off Sprint 7 (30 min)
   - [ ] Compliance Lead inicia contato com providers AML/KYT
   - [ ] Regulatory inicia contato com providers Feed UE

3. **Próximos 2 dias:**
   - [ ] Security Lead agenda setup OIDC provider
   - [ ] Ops Manager agenda war room para Sprint 8 (semana 09-15 julho)
   - [ ] CTO agenda teste de restore

---

**Aprovado por:** [Assinar]**Data:** 2026-07-02**Próxima revisão:** 2026-07-09 (End of Sprint 7)
