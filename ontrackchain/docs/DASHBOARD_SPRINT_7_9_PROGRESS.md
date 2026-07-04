# Painel: Progresso Sprint 7-9

**Última atualização:** 2026-07-02 23:30 UTC
**Próxima revisão:** 2026-07-03 09:00 (após kickoff)

---

## Acompanhamento de KPI

### Linha de base: 87% consolidado

```
Maturidade Técnica       ████████████████████░  91%  (estável)
Prontidão Regulatória    ███████████████░░░░░░  78%  (meta: 95%)
─────────────────────────────────────────────────────
KPI Consolidado          ████████████████░░░░░  87%  (meta: 95%)
```

### Caminho projetado Sprint 7-9

```
HOJE (02-Jul)    SPRINT 7     SPRINT 8     SPRINT 9     FINAL (22-Jul)
   ↓              ↓            ↓             ↓             ↓
  87%      ────→ 88%    ────→ 91%   ────→ 95%    ────→ 95%+
        Validação    1a Janela   OIDC+2a      Aprovações
        P0 Pronto    Prova P0    Recorrência  Completo

Semana:      1-2          3-4         5-6
Esforço:     14 pessoa-d  12 pessoa-d 8 pessoa-d
Status: Planejamento   Bloqueado   Futuro
```

---

## Sprint 7: Validação P0 (02-08 Jul)

**Status: PENDENTE DE KICKOFF**

### Quebra de Tarefas

```
T7.1: Credenciais AML/KYT
├─ Responsável: Liderança de Compliance
├─ Esforço: 2 dias
├─ Status: PENDENTE (externo)
├─ Bloqueador: resposta do provedor
└─ Sucesso: teste de API → saída JSON → roteiro

T7.2: URL do feed UE
├─ Responsável: Regulatório
├─ Esforço: 2 dias
├─ Status: PENDENTE (externo)
├─ Bloqueador: resposta do provedor
└─ Sucesso: teste de URL → saída JSON → roteiro

T7.3: Setup OIDC local
├─ Responsável: Liderança de Segurança
├─ Esforço: 3 dias
├─ Status: PENDENTE (externo)
├─ Bloqueador: credenciais do provedor
└─ Sucesso: setup do provedor → E2E aprovado → teste de MFA

T7.4: Testes de Integração
├─ Responsável: QA
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: T7.1, T7.2, T7.3)
├─ Bloqueador: conclusão de T7.1-T7.3
└─ Sucesso: execução do bundle → todos JSONs válidos → cobertura ≥95%

T7.5: Preparação do War Room
├─ Responsável: Gestão de Operações
├─ Esforço: 3 dias
├─ Status: EM PROGRESSO (agendamento)
├─ Bloqueador: disponibilidade do war room
└─ Sucesso: responsáveis confirmados → agenda definida → folha manual pronta

T7.6: Documentação e Aceites
├─ Responsável: Liderança de Compliance
├─ Esforço: 1 dia
├─ Status: BLOQUEADO (depende: T7.1-T7.5)
├─ Bloqueador: conclusão de T7.1-T7.5
└─ Sucesso: roteiros escritos → e-mails assinados → documentos commitados
```

### Trilhas paralelas

```
CAMINHO CRÍTICO (Dependências Externas)
────────────────────────────────────
T7.1 ─────────────────────────────────────→ Aguardar credenciais (2d)
  └─ Resposta do provedor BLOQUEADOR CRÍTICO

T7.2 ─────────────────────────────────────→ Aguardar credenciais (2d)
  └─ Resposta do provedor BLOQUEADOR CRÍTICO

T7.3 ─────────────────────────────────────→ Aguardar credenciais (3d)
  └─ Resposta do provedor BLOQUEADOR CRÍTICO

CAMINHO DE SUPORTE (Pode começar agora)
───────────────────────────────
T7.5 ──────────────────────→ Preparação do war room (3d)
  └─ Agendamento + folha manual

CAMINHO DEPENDENTE (começa quando T7.1-T7.5 terminar)
─────────────────────────────────────────
T7.4 ─────────────────────→ Testes de integração (2d)
  └─ Depende: T7.1, T7.2, T7.3

T7.6 ─────────────────────→ Docs + aceites (1d)
  └─ Depende: T7.4, T7.5
```

### Checklist de entregáveis da Sprint 7

**Prazo de sexta EOD (12 Jul):**

```
□ artifacts/sprint-7/
  □ compliance-provider-check.json          ← saída T7.1
  □ eu-sanctions-preflight.json             ← saída T7.2
  □ oidc-e2e-results.json                   ← saída T7.3
  □ sprint-7-validation-bundle.md           ← saída T7.4
  □ setup-aml-provider-prod.md              ← roteiro T7.6
  □ setup-eu-sanctions-feed-prod.md         ← roteiro T7.6
  □ compliance-sign-off.txt                 ← T7.6 aceite

□ docs/
  □ governance-weekly/2026-07-09-staging-serious-window-war-room.md ← saída T7.5

□ KPI alvo: 88% consolidado (ganho mínimo com prova de validação)
```

---

## Sprint 8: Primeira Janela Séria (09-15 Jul)

**Status: PENDENTE DE CONCLUSÃO DA SPRINT 7**

### Quebra de Tarefas

```
T8.1: Execução do War Room
├─ Responsável: Gestão de Operações
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: Sprint 7)
├─ Pré-requisitos: P0 validado, responsáveis prontos
└─ Sucesso: preflight aprovado → execução completa → packet criado

T8.2: Coleta de Evidências
├─ Responsável: QA/Tech Lead
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: T8.1)
├─ Pré-requisitos: saídas do war room
└─ Sucesso: screenshots capturados → JSONs persistidos → logs salvos

T8.3: Formalização de Ownership
├─ Responsável: COO
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: T8.1)
├─ Pré-requisitos: validação do war room
└─ Sucesso: responsáveis confirmados → SLAs assinados → drill aprovado

T8.4: Teste de Retenção/Recuperação
├─ Responsável: CTO
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: T8.1)
├─ Pré-requisitos: validação do war room
└─ Sucesso: restore bem-sucedido → RTO < 30min → sign-off realizado

T8.5: Sign-off de Compliance
├─ Responsável: Liderança de Compliance
├─ Esforço: 1 dia
├─ Status: BLOQUEADO (depende: T8.2-T8.4)
├─ Pré-requisitos: dossier completo
└─ Sucesso: dossier revisado → e-mail assinado

T8.6: Retrospectiva e Próxima Janela
├─ Responsável: Gestão de Operações
├─ Esforço: 1 dia
├─ Status: BLOQUEADO (depende: T8.5)
├─ Pré-requisitos: todas as tarefas concluídas
└─ Sucesso: aprendizados documentados → próxima janela agendada
```

### Checklist de entregáveis da Sprint 8

**Prazo de sexta EOD (19 Jul):**

```
□ artifacts/sprint-8/
  □ serious-window-stg-2026-07-09-packet.md
  □ serious-window-stg-2026-07-09-dossier.md
  □ window-logs.txt
  □ compliance-sign-off.txt
  □ cockpits-screenshots/
    □ counterparties-history.png
    □ sanctions-history.png
    □ evidence-timeline.png
    □ reports-tracked.png
    □ blocks-historical.png
    □ ros-coaf-status.png
    □ alerts-acknowledged.png

□ docs/governance-weekly/
  □ 2026-07-09-ownership-formalized.md
  □ 2026-07-09-retention-recovery-test.md
  □ 2026-07-09-retrospective.md
  □ Próxima janela agendada

□ KPI alvo: 91% consolidado (salto relevante com prova de P0 + P2)
```

---

## Sprint 9: OIDC + Recorrência (16-22 Jul)

**Status: PENDENTE DE CONCLUSÃO DA SPRINT 8**

### Quebra de Tarefas

```
T9.1: Homologação OIDC
├─ Responsável: Liderança de Segurança
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: Sprint 8)
├─ Pré-requisitos: setup de P0-01 validado
└─ Sucesso: provedor integrado → MFA verificado → E2E aprovado

T9.2: Segunda Janela Séria (Recorrência)
├─ Responsável: Gestão de Operações
├─ Esforço: 3 dias
├─ Status: BLOQUEADO (depende: T9.1, Sprint 8)
├─ Pré-requisitos: T9.1 pronto, aprendizados aplicados
└─ Sucesso: janela executada → dossier assinado → recorrência comprovada

T9.3: Aprovações Formais
├─ Responsável: COO
├─ Esforço: 2 dias
├─ Status: BLOQUEADO (depende: T9.2)
├─ Pré-requisitos: todas as janelas concluídas
└─ Sucesso: documento consolidado → todas assinaturas → publicado

T9.4: Planejamento P3 (Trabalho Futuro)
├─ Responsável: Tech Lead
├─ Esforço: 1 dia
├─ Status: BLOQUEADO (depende: T9.3)
├─ Pré-requisitos: P0-P2 concluído
└─ Sucesso: decisão de Vault → roadmap PKI → planejamento Q3
```

### Checklist de entregáveis da Sprint 9

**Prazo de sexta EOD (26 Jul):**

```
□ artifacts/sprint-9/
  □ serious-window-stg-2026-07-23-packet.md
  □ serious-window-stg-2026-07-23-dossier.md
  □ compliance-sign-off.txt
  □ oidc-homologation-report.md

□ docs/
  □ governance-weekly/2026-07-20-formal-sign-offs.md (consolidated)
  □ setup-oidc-production.md
  □ p3-roadmap-q3-2026.md

□ KPI alvo: 95% consolidado  META ALCANÇADA
```

---

## Caminho Crítico e Bloqueadores

### Semana 1 (02-08 Jul) — Janela de Dependências Externas

```
BLOQUEADORES CRÍTICOS (resolver em até 48 horas):

1. Credenciais do provedor AML/KYT
  └─ Ação: liderança de Compliance contata provedor HOJE
  └─ Prazo: 04 Jul 17:00 UTC
  └─ Se falhar: atraso de 1-2 dias, extensão da Sprint 7

2. URL do feed UE
  └─ Ação: regulatório contata provedor HOJE
  └─ Prazo: 04 Jul 17:00 UTC
  └─ Se falhar: atraso de 1-2 dias, extensão da Sprint 7

3. Credenciais do provedor OIDC
  └─ Ação: liderança de Segurança contata provedor HOJE
  └─ Prazo: 05 Jul 17:00 UTC
  └─ Se falhar: manter Keycloak local e estender Sprint 7

MITIGAÇÃO:
├─ Ter mocks de fallback prontos em dev
├─ Acompanhamento diário se não houver resposta
├─ Escalar via CTO para nível C do provedor quando necessário
└─ Contingência: estender Sprint 7 para 2 semanas se houver >2 bloqueadores
```

### Grafo de Dependências

```
Credenciais Externas (04-05 Jul)
    ↓
Setup Local e Validação (05-08 Jul)
  ├─ T7.1-T7.3 (AML/KYT, feed UE, setup OIDC)
  └─ T7.5 (prep de war room)
        ↓
Testes de Integração (07-08 Jul)
    └─ T7.4
        ↓
Fechamento da Sprint 7 (08 Jul EOD)
  └─ T7.6 (docs + aceites)
        ↓
INÍCIO DA SPRINT 8 (09 Jul 09:00)
  └─ Execução de war room
        ↓
Ownership + Retenção (09-12 Jul)
    └─ T8.3, T8.4
        ↓
Sign-off de Compliance (13 Jul)
    └─ T8.5
        ↓
FECHAMENTO DA SPRINT 8 (15 Jul EOD)
  └─ T8.6 (retrospectiva + próxima janela)
        ↓
INÍCIO DA SPRINT 9 (16 Jul 09:00)
  └─ Homologação OIDC
        ↓
2a Janela Séria (16-19 Jul)
    └─ T9.2
        ↓
Aprovações finais (20-21 Jul)
    └─ T9.3
        ↓
 95% META ALCANÇADA (22 Jul)
```

---

## Template de Standup Diário

**Quando:** 09:00 UTC (09:00-09:15)
**Participantes:** todos os responsáveis de tarefas + Tech Lead + Ops Manager
**Formato:** 30s por pessoa

```
[TEMPLATE POR PESSOA]

Nome: ___________
Tarefa(s): T7.X, T7.Y, ...
Status: No prazo / Em risco / Bloqueado
Ontem: <o que foi feito>
Hoje: <o que será feito>
Bloqueador: <se houver>
ETA correção: <até quando>
```

**Registrar em:** `artifacts/sprint-7/daily-standups.md`

---

## Matriz de Escalacao

| Cenario | Gatilho | Acao | Responsável |
| --- | --- | --- | --- |
| Provedor sem resposta | >12 horas | Acompanhamento diário | Compliance/Regulatório/Segurança |
| Provedor atrasado | >24 horas | Escalar para CFO/CTO | COO |
| Conflito de war room | >48 horas | Mover data ou dividir time | Ops Manager |
| Falha em teste de integração | Qualquer | Debug + tentativa de correção em 2 horas | Tech Lead + QA |
| Teste excede correção de 2h | Após 2 horas | Debug hands-on com CTO | CTO |
| Janela séria atrasada | >2 horas de execução | HOLD, pós-mortem, nova tentativa no dia seguinte | Ops Manager + Tech Lead |
| Atraso de sign-off de stakeholders | >3 dias | Lembrete do COO + extensão de prazo | COO |

---

## Agenda de Revisão Semanal

### Sexta EOD (toda semana)
- [ ] Verificar entregáveis concluídos
- [ ] Atualizar métricas de KPI
- [ ] Documentar aprendizados
- [ ] Planejar próxima semana

**Reuniões de revisão:**
- Sprint 7: sexta 12 Jul 17:00 UTC
- Sprint 8: sexta 19 Jul 17:00 UTC
- Sprint 9: sexta 26 Jul 17:00 UTC

---

## Checklist Final (antes da celebração de 95%)

### Documentação
- [ ] Todos os roteiros operacionais escritos (AML/KYT, feed UE, OIDC)
- [ ] 2 janelas sérias concluídas com dossiers
- [ ] Teste de retenção/recuperação documentado com RTO/RPO
- [ ] Retrospectivas registradas
- [ ] Roadmap de P3 definido

### Aprovações
- [ ] Liderança de Compliance: P0-02, P0-03, janelas, recorrência
- [ ] Liderança de Segurança: OIDC, MFA, ownership
- [ ] CTO: Retenção/Recuperação, RTO/RPO
- [ ] COO: SLAs, responsáveis, cadência

### Métricas
- [ ] Técnica: 91% (sem mudança)
- [ ] Regulatória: 95% (partindo de 78%)
- [ ] Consolidada: 95%  META

---

## Referência de Documentos

| Documento | Finalidade | Status |
| --- | --- | --- |
| **PROJECT_ANALYSIS_AND_ROADMAP_2026_07_02.md** | Análise estratégica dos 6 sprints + gap analysis | Completo |
| **TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md** | Plano detalhado de execução Sprint 7-9 | Completo |
| **EXECUTIVE_SUMMARY_95_PERCENT.md** | Resumo executivo (1 página) | Completo |
| **PRÓXIMAS_AÇÕES_IMEDIATAS.md** | Ações desta semana | Completo |
| **PAINEL (este arquivo)** | Progresso e status visual | Completo |

---

**Última atualização:** 2026-07-02 23:45 UTC
**Próxima atualização:** 2026-07-03 17:00 (após kickoff) ou imediatamente se houver bloqueadores
**Responsável:** Tech Lead / Ops Manager

---

## RESUMO DE UMA PAGINA PARA PARTES INTERESSADAS

```
╔════════════════════════════════════════════════════════════════════╗
║          ONTRACKCHAIN PLANO DE MATURIDADE 95% SPRINT 7-9          ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Estado Atual:       KPI consolidado de 87% (Jun 2026)           ║
║  Estado Alvo:        KPI consolidado de 95% (22 Jul 2026)        ║
║                                                                    ║
║  Linha do tempo:     9 semanas (3 sprints)                        ║
║  Esforço:            34 pessoa-dias (~€15-20K)                    ║
║  Bloq. Críticos:     3 credenciais externas de provedores         ║
║                                                                    ║
║  Trajetória KPI:     87% ─→ 88% ─→ 91% ─→ 95%                  ║
║                      S7    S8    S9                               ║
║                                                                    ║
║  PRÓXIMA AÇÃO:       Início da Sprint 7 amanhã (09:00)            ║
║                      Contatar 3 provedores HOJE                   ║
║                      Confirmar responsáveis das tarefas            ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

**Painel pronto. Aguardando kickoff e respostas dos provedores.**
