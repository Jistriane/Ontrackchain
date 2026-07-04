# Próximas Ações Imediatas - Semana de 02-07 de julho

**Status atual:** 87% consolidado
**Meta:** 95% em 9 semanas

---

## Hoje (02 de julho)

### 1. Comunicação executiva
**Tempo estimado:** 30 min

Compartilhar com stakeholders:

```text
To: Tech Lead, Compliance Lead, COO, CTO, Security Lead
Subject: Sprint 7-9 Tactical Roadmap: Path to 95% Maturity

Pessoal,

Consolidei a análise completa do projeto e montei um plano detalhado para elevar o KPI de 87% para 95% em 9 semanas.

Documentos criados:
1. PROJECT_ANALYSIS_AND_ROADMAP_2026_07_02.md - análise estratégica completa
2. TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md - plano de execução Sprint 7-9

Caminho para 95%:
- Sprint 7 (02-08 jul): validação P0 -> 88%
- Sprint 8 (09-15 jul): primeira janela séria -> 91%
- Sprint 9 (16-22 jul): OIDC + recorrência -> 95%

Bloqueadores críticos (dependências externas):
- credenciais AML/KYT (Compliance Lead -> provedor)
- URL de feed UE (Regulatory -> provedor)
- credenciais OIDC (Security Lead -> Azure/Auth0)

Próxima reunião: amanhã, 09:00 - kickoff da Sprint 7
```

### 2. Agenda do kickoff da Sprint 7
**Tempo estimado:** 5 min

- [ ] convidar Tech Lead, Compliance Lead, Security Lead, Ops Manager e CTO
- [ ] reservar 1 hora de reunião
- [ ] marcar para amanhã às 09:00
- [ ] enviar os 2 documentos com antecedência

---

## Amanhã (03 de julho) - Kickoff da Sprint 7

### 1. Reunião de kickoff (09:00-10:00)
**Facilitador:** Tech Lead

**Agenda (60 min):**
- [ ] 0-10 min: contexto do objetivo de 95% e estrutura P0-P3
- [ ] 10-20 min: visão geral de T7.1-T7.6
- [ ] 20-30 min: dependências externas e riscos
- [ ] 30-45 min: definição de responsáveis por tarefa
- [ ] 45-60 min: escalação e próximos passos

**Decisões esperadas:**
- [ ] confirmar responsável de T7.1 (Compliance Lead)
- [ ] confirmar responsável de T7.2 (Regulatory/Ops)
- [ ] confirmar responsável de T7.3 (Security Lead)
- [ ] agendar war room da Sprint 8 (semana de 09-15 jul)

### 2. Contato com provedores
**Tempo estimado:** 30 min

#### Contato 1: AML/KYT

```text
Subject: Solicitação de Credenciais de Produção - AML/KYT (Ontrackchain)

Olá,

Iniciamos a fase de homologação de produção e precisamos de:
1. chave de API de produção
2. endpoint da API
3. certificados (se necessário)
4. SLA de disponibilidade
5. documentação técnica da integração

Prazo: até 04 de julho para validação local em 05 de julho.

Obrigado,
Compliance Lead
```

#### Contato 2: Feed de sanções UE

```text
Subject: Solicitação de URL Tokenizada - Feed de Sanções UE

Olá,

Para integração de sanções UE, precisamos de:
1. URL tokenizada da API
2. formato de resposta (schema JSON)
3. frequência de atualização
4. SLA de disponibilidade

Prazo: até 04 de julho para validação local em 05 de julho.

Obrigado,
Regulatory Lead
```

#### Contato 3: OIDC

```text
Subject: Solicitação de Credenciais - OIDC Integration (Staging Serious)

Olá,

Estamos iniciando integração federada via OIDC para staging.

Precisamos de:
1. Tenant ID / Organization ID
2. Client ID
3. Client Secret
4. scopes recomendados
5. documentação de integração MFA TOTP

Prazo: até 05 de julho para setup local.

Obrigado,
Security Lead
```

**Status de follow-up:**
- [ ] T7.1: AML/KYT - aguardando resposta
- [ ] T7.2: feed UE - aguardando resposta
- [ ] T7.3: OIDC - aguardando resposta

---

## 04-05 de julho - Preparação local

### Setup paralelo (2-3 horas)

#### Compliance Lead (T7.1)
```bash
cd /home/jistriane/Ontracktchain/ontrackchain

echo "COMPLIANCE_PROVIDER_API_KEY=<key_recebida>" >> .env.staging.private
echo "COMPLIANCE_PROVIDER_URL=<endpoint_recebido>" >> .env.staging.private

make up-local
python scripts/preflight_compliance_provider.py
```

#### Regulatory (T7.2)
```bash
cd /home/jistriane/Ontracktchain/ontrackchain

echo "COMPLIANCE_EU_SANCTIONS_SOURCE_URL=<url_tokenizada>" >> .env.staging.private

make up-local
python scripts/test_eu_sanctions_feed.py
```

#### Security Lead (T7.3)
```bash
cd /home/jistriane/Ontracktchain/ontrackchain

echo "OIDC_PROVIDER=<entra_id_ou_auth0>" >> .env.staging.private
echo "OIDC_CLIENT_ID=<client_id>" >> .env.staging.private
echo "OIDC_CLIENT_SECRET=<client_secret>" >> .env.staging.private

make up-local AUTH_MODE=oidc

cd apps/frontend
npm run test:e2e:oidc-critical
```

---

## Semana de 08-12 de julho - Sprint 7 intensa

### Daily standup (09:00)
- [ ] T7.1 AML/KYT: status e bloqueadores
- [ ] T7.2 feed UE: status e bloqueadores
- [ ] T7.3 OIDC: status e bloqueadores
- [ ] T7.4 testes de integração
- [ ] T7.5 preparação de war room
- [ ] T7.6 documentação e aceites

### Entregas esperadas (sexta, 12 de julho)

```text
artifacts/sprint-7/
├── compliance-provider-check.json
├── eu-sanctions-preflight.json
├── oidc-e2e-results.json
├── sprint-7-validation-bundle.md
├── setup-aml-provider-prod.md
├── setup-eu-sanctions-feed-prod.md
└── compliance-sign-off.txt
```

**KPI alvo na sexta:** 88% consolidado.

---

## Riscos Críticos e Mitigação

| Risco | Probabilidade | Se ocorrer | Mitigação |
| --- | ---: | --- | --- |
| credenciais AML/KYT não chegam | 30% | atrasa T7.1 e T7.4 | usar mock de provedor em dev |
| URL do feed UE indisponível | 25% | atrasa T7.2 e T7.4 | usar snapshot de dados para teste |
| provedor OIDC indisponível | 40% | manter OIDC local | estender 2 semanas, se necessário |
| war room sem staff suficiente | 50% | adia janela | agendar com antecedência e confirmar RTAs |
| falha da janela séria | 15% | reexecução | debug guiado por scripts e rastros |

**Plano B:** bloqueio por mais de 2 dias deve ser escalado para CTO/COO.

---

## Checklist de Comunicação

- [ ] compartilhar PROJECT_ANALYSIS + TACTICAL_ROADMAP
- [ ] kickoff agendado para amanhã, 09:00
- [ ] e-mails enviados aos provedores
- [ ] responsáveis informados sobre cronograma e dependências
- [ ] war room agendada para semana de 09-15 jul
- [ ] próxima standup agendada para segunda, 08 jul

---

## Escalação

- indisponibilidade de Tech Lead: CTO assume facilitação
- ausência de Compliance Lead: COO aciona com prazo crítico
- falta de retorno dos provedores: COO escala para nível executivo
- atraso na preparação da janela séria: CTO decide extensão ou compactação

---

## Visão de 30K pés

```text
Hoje (02 jul)      Semana (08 jul)      Semana (15 jul)      Semana (22 jul)
    |                   |                    |                    |
Comunicar         Validar P0           Executar S8            OIDC + P2
Kickoff           Sprint intensa       1a janela séria        95%
                  -> 88%               -> 91%                 -> 95%
```

---

**Próxima atualização:** amanhã, após o kickoff (14:00)

**Referências:** PROJECT_ANALYSIS_AND_ROADMAP_2026_07_02.md e TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md

**Pronto para iniciar execução da Sprint 7.**
