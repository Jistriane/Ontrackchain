# GitHub Actions CI/CD Integration

## Visão Geral

O Ontrackchain agora integra automação de governança no pipeline CI/CD via GitHub Actions:

1. **governance-gate-check.yml** — Valida gate em PRs/pushes; bloqueia deployment se governança não permite
2. **governance-gate-refresh.yml** — Atualiza artefatos de governança diariamente (08:00 UTC) ou manualmente
3. **governance-status-notify.yml** — Envia notificação Slack de status diário (09:00 UTC)
4. **p0-01-oidc-local-gate.yml** — Executa o gate CI-friendly de `OIDC + MFA` com stack dockerizada local ao runner
5. **p0-02-aml-live-gate.yml** — Executa o gate hospedado de `AML/KYT live` usando `GitHub Environment` e `STAGING_WINDOW_PRIVATE_ENV`
6. **p0-03-eu-live-gate.yml** — Executa o gate hospedado do feed UE real usando `GitHub Environment`, stack local de compliance e artefatos da janela UE
7. **p0-04-regulatory-bundle-gate.yml** — Executa o bundle regulatório oficial de `P0-02 + P0-03` com JSON e resumo markdown anexáveis
8. **staging-serious-window.yml** — Executa a janela séria completa via gate canônico `P0-05`, incluindo postprocess de sign-off, decision packet, war room e live tracking

## Setup Inicial

### 1. Adicionar Slack Webhook Secret

Se você quer notificações automáticas no Slack:

1. Acesse seu repositório → Settings → Secrets and variables → Actions
2. Clique em "New repository secret"
3. Nome: `SLACK_WEBHOOK_URL`
4. Valor: Cole sua URL do Slack webhook (ex: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`)
5. Clique em "Add secret"

**Sem este secret:**
- ✅ Gate evaluation continua funcionando
- ⚠️ Notificações Slack serão skippadas (workflows continuam executando)
- ✅ Não há falha de pipeline

### 2. Verificar Workflows

Acesse seu repositório → Actions para ver:
- Governance Gate Check (automático em PRs/pushes)
- Governance Artefacts Refresh (schedule: 08:00 UTC daily)
- Governance Status Notification (schedule: 09:00 UTC daily)
- P0-01 OIDC Local Gate (manual, para validar o rito local canônico em runner GitHub)
- P0-02 AML Live Gate (manual, para validar `AML/KYT live` com segredo efêmero do environment)
- P0-03 EU Live Gate (manual, para validar feed UE real com JSONs formais da janela)
- P0-04 Regulatory Bundle Gate (manual, para consolidar `P0-02 + P0-03` em artefato executivo revisável)
- Staging Serious Window (manual, para executar a janela séria ponta a ponta via gate `P0-05`)

### 3. Configurar Branch Protection (Opcional)

Para forçar que PRs passem pelo gate antes de merge:

1. Acesse Settings → Branches → Branch protection rules
2. Clique em "Add rule"
3. Padrão de branch: `main`
4. Habilitar:
   - ✅ "Require status checks to pass before merging"
   - ✅ "Governance Gate" (assim que rodar primeira vez)
5. Salvar

## Workflows Detalhados

### governance-gate-check.yml

**Quando roda:**
- ✅ Em cada push para `main`, `staging`, `develop`
- ✅ Em cada PR para `main`, `staging`
- ✅ Manualmente via "Run workflow"
- ⏭️ Apenas se houver mudanças em scripts/docs/Makefile

**O que faz:**
1. Identifica a janela de governança mais recente
2. Se não existir JSON consolidado, tenta gerar
3. Avalia gate baseado em política (default: moderate)
4. Adiciona comentário em PR com resultado
5. Cria check run no commit (visível em PR)
6. Se gate bloqueia e é um push (não PR): notifica Slack

**Entrada (workflow_dispatch):**
- `window_id` — ID da janela (auto-detecta se vazio)
- `gate_policy` — `strict` | `moderate` | `relaxed` (default: moderate)
- `gate_operation` — `merge` | `deploy` | `release` (default: merge)

**Saída:**
- Comentário em PR
- Check run no commit
- Artefato: gate_result_json

**Exemplo: Rodar manualmente**
```
Repository → Actions → Governance Gate Check → Run workflow
  window_id: (deixar vazio)
  gate_policy: strict
  gate_operation: deploy
```

Resultado: Avalia se deployment é permitido com política strict.

### governance-gate-refresh.yml

**Quando roda:**
- ⏰ Diariamente às 08:00 UTC
- ✅ Manualmente via "Run workflow"

**O que faz:**
1. Identifica janela de governança mais recente
2. Executa `make refresh-staging-war-room-governance-local`
3. Avalia gate com política moderate
4. Envia notificação Slack (se webhook configurado)
5. Upload de artefatos
6. Comentário em PRs abertos (se houver)

**Entrada (workflow_dispatch):**
- `window_id` — ID da janela (auto-detecta se vazio)
- `notify_slack` — true/false (default: true)

**Saída:**
- 8 artefatos markdown atualizados
- JSON consolidado atualizado
- Artefatos salvos por 30 dias

**Exemplo: Executar refresh manualmente**
```
Repository → Actions → Governance Artefacts Refresh → Run workflow
  window_id: stg-2026-07-06-a
  notify_slack: true
```

### governance-status-notify.yml

**Quando roda:**
- ⏰ Diariamente às 09:00 UTC (1h após refresh)
- ✅ Manualmente via "Run workflow"
- ⚠️ Requer SLACK_WEBHOOK_URL configurado

**O que faz:**
1. Identifica janela mais recente
2. Envia notificação Slack com status consolidado
3. Emoji color-coded (🟢 verde, 🟡 amarelo, 🔴 vermelho)

**Entrada:**
- `window_id` — ID da janela (auto-detecta se vazio)

### p0-01-oidc-local-gate.yml

**Quando roda:**
- ✅ Manualmente via "Run workflow"

**Pre-requisitos:**
- o arquivo do workflow precisa estar commitado e presente no branch remoto selecionado no dispatch
- o runner hospedado precisa conseguir construir `docker compose` e executar Playwright
- se o operador nao tiver `gh` CLI autenticado, a execucao deve ser iniciada pela UI do GitHub

**O que faz:**
1. Prepara `ci-artifacts/`
2. Instala dependencias do `frontend` e browser do Playwright
3. Reseta stack OIDC local anterior para evitar drift entre execucoes
4. Executa `make gate-p0-01-oidc-ci`
5. Coleta diagnosticos do compose, do `/auth/config` externo, do `auth-service` e do env efetivo do `frontend`
6. Derruba a stack e remove o env efemero
7. Publica artefatos por 30 dias

**Artefatos esperados:**
- `ontrackchain/ci-artifacts/p0-01-oidc-local-gate.log`
- `ontrackchain/ci-artifacts/docker-compose-ps.txt`
- `ontrackchain/ci-artifacts/docker-compose-logs.txt`
- `ontrackchain/ci-artifacts/auth-config-public.json`
- `ontrackchain/ci-artifacts/auth-config-auth-service.json`
- `ontrackchain/ci-artifacts/frontend-env-snapshot.txt`
- `ontrackchain/apps/frontend/playwright-report`
- `ontrackchain/apps/frontend/test-results`

### p0-02-aml-live-gate.yml

**Quando roda:**
- ✅ Manualmente via "Run workflow"

**Pre-requisitos:**
- o arquivo do workflow precisa estar commitado e presente no branch remoto selecionado no dispatch
- o `GitHub Environment` selecionado precisa expor `STAGING_WINDOW_PRIVATE_ENV`
- o environment deve conter os segredos reais de compliance para `COMPLIANCE_TRM_*`
- o operador precisa informar um `window_id` correlacionavel com a janela seria

**O que faz:**
1. Materializa `.env.staging.private` de forma efemera
2. Gera um `request_id` correlacionavel para a run hospedada
3. Reseta stack residual de compliance do runner para evitar drift entre execucoes
4. Executa `make gate-p0-02-aml-live`
5. Coleta `docker compose ps/logs`
6. Opcionalmente executa `python3 scripts/homologation_external_evidence.py --mode compliance`
7. Publica `ci-artifacts/` e `artifacts/homologation/`

**Artefatos esperados:**
- `ontrackchain/ci-artifacts/p0-02-aml-live-gate.log`
- `ontrackchain/ci-artifacts/p0-02/p0-02-preflight.json`
- `ontrackchain/ci-artifacts/p0-02/p0-02-compliance-runtime.json`
- `ontrackchain/ci-artifacts/p0-02/p0-02-smoke-runtime.json`
- `ontrackchain/ci-artifacts/p0-02/p0-02-gate-summary.json`
- `ontrackchain/ci-artifacts/p0-02-docker-compose-ps.txt`
- `ontrackchain/ci-artifacts/p0-02-docker-compose-logs.txt`
- `ontrackchain/ci-artifacts/p0-02-homologation.log`, quando `run_homologation=true`
- `ontrackchain/artifacts/homologation`

### p0-03-eu-live-gate.yml

**Quando roda:**
- ✅ Manualmente via "Run workflow"

**Pre-requisitos:**
- o arquivo do workflow precisa estar commitado e presente no branch remoto selecionado no dispatch
- o `GitHub Environment` selecionado precisa expor `STAGING_WINDOW_PRIVATE_ENV`
- o environment deve conter `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` real e `DATABASE_URL`
- a execucao precisa poder subir `postgres`, `compliance-api` e `compliance-worker` via `docker compose`

**O que faz:**
1. Materializa `.env.staging.private` de forma efemera
2. Gera um `request_id` correlacionavel para a run hospedada
3. Reseta stack residual de compliance do runner
4. Executa `make gate-p0-03-eu-live`
5. Coleta `docker compose ps/logs`
6. Publica `ci-artifacts/` e os JSONs formais da janela em `artifacts/staging/checks/`

**Artefatos esperados:**
- `ontrackchain/ci-artifacts/p0-03-eu-live-gate.log`
- `ontrackchain/ci-artifacts/p0-03/p0-03-preflight.json`
- `ontrackchain/ci-artifacts/p0-03/p0-03-eu-window.json`
- `ontrackchain/ci-artifacts/p0-03/p0-03-eu-checker.json`
- `ontrackchain/ci-artifacts/p0-03/p0-03-gate-summary.json`
- `ontrackchain/ci-artifacts/p0-03-docker-compose-ps.txt`
- `ontrackchain/ci-artifacts/p0-03-docker-compose-logs.txt`
- `ontrackchain/artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `ontrackchain/artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`

### p0-04-regulatory-bundle-gate.yml

**Quando roda:**
- ✅ Manualmente via "Run workflow"

**Pre-requisitos:**
- o arquivo do workflow precisa estar commitado e presente no branch remoto selecionado no dispatch
- o `GitHub Environment` selecionado precisa expor `STAGING_WINDOW_PRIVATE_ENV`
- o environment deve conter os insumos reais de `P0-02` e `P0-03`
- a execucao precisa poder subir a stack local de compliance via `docker compose`

**O que faz:**
1. Materializa `.env.staging.private` de forma efemera
2. Gera correlacao explicita de `request_id` para as trilhas `P0-02` e `P0-03`
3. Reseta stack residual de compliance do runner
4. Executa `make gate-p0-04-regulatory-bundle`
5. Gera o JSON oficial e o resumo markdown do bundle regulatorio
6. Coleta `docker compose ps/logs`
7. Publica `ci-artifacts/`, `artifacts/staging/checks/` e `artifacts/staging/dossiers/`

**Artefatos esperados:**
- `ontrackchain/ci-artifacts/p0-04-regulatory-bundle-gate.log`
- `ontrackchain/ci-artifacts/p0-04-preflight.json`
- `ontrackchain/ci-artifacts/p0-04-regulatory-readiness-bundle.json`
- `ontrackchain/ci-artifacts/p0-04-regulatory-readiness-bundle.md`
- `ontrackchain/ci-artifacts/p0-04-gate-summary.json`
- `ontrackchain/ci-artifacts/p0-04-docker-compose-ps.txt`
- `ontrackchain/ci-artifacts/p0-04-docker-compose-logs.txt`
- `ontrackchain/artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `ontrackchain/artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`

### staging-serious-window.yml

**Quando roda:**
- ✅ Manualmente via "Run workflow"

**Pre-requisitos:**
- o arquivo do workflow precisa estar commitado e presente no branch remoto selecionado no dispatch
- o `GitHub Environment` selecionado precisa expor `STAGING_WINDOW_PRIVATE_ENV`
- o environment deve conter insumos reais de `P0-01`, `P0-02`, `P0-03` e `P0-04`
- o runner precisa conseguir instalar dependencias do frontend para o trilho critico de OIDC

**O que faz:**
1. Materializa `.env.staging.private` de forma efemera
2. Instala dependencias do frontend e Playwright para `P0-01`
3. Executa `make gate-p0-05-serious-window`
4. Gera payload, postprocess JSON e draft de sign-off em `ci-artifacts/`
5. Atualiza artefatos versionaveis da janela em `docs/governance-weekly/`
6. Publica checks, dossiers, homologacao, templates, sign-off draft e rastros do frontend

**Artefatos esperados:**
- `ontrackchain/ci-artifacts/p0-05-serious-window-gate.log`
- `ontrackchain/ci-artifacts/p0-05/p0-05-payload.json`
- `ontrackchain/ci-artifacts/p0-05/p0-05-postprocess.json`
- `ontrackchain/ci-artifacts/p0-05/p0-05-staging-serious-window-signoff.md`
- `ontrackchain/docs/governance-weekly/generated/windows`
- `ontrackchain/docs/governance-weekly/cycles`

## Exemplos de Uso

### Exemplo 1: Validar PR antes de merge

```
1. Abra um PR contra main
2. GitHub Actions executa governance-gate-check automaticamente
3. Resultado aparece como comentário no PR:
   ✅ Governance Gate ALLOWED (se verde + go)
   ou
   ❌ Governance Gate BLOCKED (se amarelo/vermelho)
4. Se bloqueado, revise a governança antes de merge
```

### Exemplo 2: Forçar validação com política strict

```bash
# Via GitHub UI:
Repository → Actions → Governance Gate Check → Run workflow
  window_id: (empty - auto-detect)
  gate_policy: strict
  gate_operation: release

# Resultado: Avalia se release é permitida com política strict
```

### Exemplo 3: Notificação diária de status

```
• Toda manhã às 08:00 UTC: refresh-governance executa
• 1h depois (09:00 UTC): status-notify envia Slack
• Slack #governance canal recebe mensagem com sinal + blockers
• Se vermelho: @channel mention automático
```

### Exemplo 4: Integrar gate check em deploy workflow

```yaml
# .github/workflows/deploy.yml (seu workflow existente)

jobs:
  check-governance:
    uses: ./.github/workflows/governance-gate-check.yml
    secrets:
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
    with:
      window_id: ${{ env.WINDOW_ID }}
      gate_policy: strict
      gate_operation: deploy

  deploy:
    needs: check-governance
    if: needs.check-governance.outputs.gate_allowed == 'true'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: docker compose -f ontrackchain/docker-compose.yml up -d
```

## Outputs & Integração

### Variáveis de Saída (governance-gate-check.yml)

```yaml
outputs:
  gate_allowed:      # 'true' | 'false'
  gate_reason:       # String explicando decisão
  gate_result_json:  # JSON completo com blocker_summary
  window_id:         # ID da janela processada
```

Usar em outros jobs:
```yaml
- name: Check gate result
  if: needs.governance-gate-check.outputs.gate_allowed == 'false'
  run: echo "Gate blocked: ${{ needs.governance-gate-check.outputs.gate_reason }}"
```

### Check Runs no Commit

Cada execução de gate cria um check run visível em:
- ✅ PR Checks tab
- ✅ Commit history
- ✅ Merge button (se branch protection ativo)

### Slack Messages

Formato automático:
- Título: "🟢 Ontrackchain Governance Update" (or 🟡, 🔴)
- Color: #28a745 (verde), #ffc107 (amarelo), #dc3545 (vermelho)
- Campos: Window, Status, Signal, Decision, Blockers, Artefacts
- Mention: @channel quando sinal é vermelho + `--mention-on-red`

## Troubleshooting

### Workflow não executa automaticamente

**Sintomas:**
- Pushes para main não disparam governance-gate-check
- Schedule workflows não rodam

**Causas possíveis:**
1. Workflows estão desabilitados
2. Arquivo .yml contém erro de sintaxe YAML
3. Trigger conditions não estão sendo atendidas

**Solução:**
```bash
# Validar YAML
cd .github/workflows
yamllint *.yml || python3 -m yaml *.yml

# Habilitar workflows
Repository → Actions → Enable workflows
```

### Slack notification não enviada

**Sintomas:**
- Workflow roda mas nenhuma mensagem no Slack
- Logs dizem "Slack webhook not configured"

**Causas:**
1. SLACK_WEBHOOK_URL secret não adicionado
2. Webhook URL expirada/revogada

**Solução:**
```bash
# Verificar secret existe
Repository → Settings → Secrets and variables → Actions

# Se não existir, adicionar novo secret SLACK_WEBHOOK_URL

# Se existe, testar webhook manualmente:
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "test"}'
```

### Gate sempre retorna "blocked"

**Sintomas:**
- Gate evaluation sempre retorna allowed=false
- Reason: "Governance signal is amarelo..."

**Causas:**
1. Janela atual tem sinal amarelo (esperado)
2. Problema com política muito restritiva

**Solução:**
```bash
# Verificar política sendo usada
Repository → Actions → Run workflow
  gate_policy: moderate  # menos restritiva

# Ou revisar governance status atual:
make evaluate-governance-gate GATE_POLICY=moderate
```

### "No consolidated JSON found"

**Sintomas:**
- Workflows falham com "No consolidated JSON found"

**Causas:**
1. Primeira execução — nenhum JSON gerado ainda
2. JSON foi deletado

**Solução:**
```bash
# Gerar JSON localmente
make refresh-staging-war-room-governance-local

# Ou trigger refresh workflow
Repository → Actions → Governance Artefacts Refresh → Run workflow
```

## Best Practices

1. **Configurar Branch Protection**
   - Force que PRs passem gate antes de merge
   - Evita código com governance baixa

2. **Monitor Schedule Workflows**
   - Acompanhe os logs das 08:00 e 09:00 UTC runs
   - Identifique padrões de bloqueios

3. **Integrar com Deployment**
   - Use gate_allowed output em deploy workflows
   - Bloqueia deploy se governance não permite

4. **Revisão Manual de Bloqueios**
   - Quando gate bloqueia, equipe deve revisar
   - Resolver placeholders/handoff issues
   - Re-run workflow após resolução

5. **Rotação de Slack Webhook**
   - Trocar webhook URL a cada 6 meses
   - Usar rotação automática do Slack

## Próximos Passos

- [ ] Adicionar SLACK_WEBHOOK_URL secret
- [ ] Executar governance-gate-check manualmente para testar
- [ ] Configurar branch protection para `main`
- [ ] Revisar outputs em primeiro PR
- [ ] Monitorar schedule workflows por 1 semana
- [ ] Ajustar gate policies conforme necessário
- [ ] Integrar gate check em deploy workflow existente

## Referências

- Documentação oficial: [GitHub Actions](https://docs.github.com/en/actions)
- Slack Webhooks: [Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- Workflows usados:
  - `.github/workflows/governance-gate-check.yml`
  - `.github/workflows/governance-gate-refresh.yml`
  - `.github/workflows/governance-status-notify.yml`
