# ADR-018 — QA Gateway como Single Source of Truth para RLS + Padrão Shared-First / Fallback Inline

## Contexto

Na Sprint 1 (P0 Fundação Segura), tivemos que distribuir e garantir a mesma lógica de segurança
em **3 serviços Python** (case-management, auth-service, investigation-api) e em
**pelo menos 4 pontos do CI/CD** (gate RLS cross-tenant, scan tabelas, health checks,
LGPD scan).

Os riscos de termos implementações duplicadas e divergentes eram altos:

1. **Desvio semântico de RLS**: 1 serviço esquecer de setar bypass de rotas públicas
   (login/dev-token/sso), resultando em 401s em produção.
2. **Aumento de débito técnico**: Se adicionarmos um novo path bypass (ex: rota webhook
   pública), teríamos que editar 3 arquivos `main.py` manualmente.
3. **Falta de auditabilidade**: Qual foi a versão do algoritmo de validação de UUID que
   rodou no último deploy? Em script standalone vs middleware inline divergem é difícil
   provar conformidade regulatória (Bacen, LGPD).
4. **Risco de regressão**: Falta 1 serviço implementar `current_setting('app.organization_id', TRUE)`
   com o parâmetro de default NULL correto → vazamento cross-tenant silencioso.

## Decisão

### 1. Criar o package `packages/qa-gateway` como **Fonte Única da Verdade (SSOT)**.
   Toda lógica de:
   - scan RLS em tabelas (checar coluna org_id, RLS enabled, policy *tenant_isolation, índice);
   - scan LGPD (CPF plaintext, chaves privadas em DB);
   - health check paralelo de endpoints;
   - **scan SLA 24h Dead Man Switch** (último sucesso exploração há < 86400s);
   - (futuro) geração de relatórios de conformidade;
   é implementada APENAS no package, com console_scripts `qa-gateway` expondo CLI.

### 1.1 (Sprint 4 FINAL) Expansão QA Gateway: 6 comandos CLI MVP completo
```
qa-gateway --help          # Lista todos + versões + exit codes
qa-gateway scan-rls        # Fase 2/3 deploy — garante RLS ativo + policy tenant_isolation + índice org_id em TODAS tabelas
qa-gateway health          # Fase 2 warmup pós-deploy — HTTP(S) paralelo n endpoints com timeout e 2 retries
qa-gateway scan-lgpd       # Fase 4 nightly compliance — CPF plaintext, chaves privadas, PII não pseudonimizado em DB
qa-gateway scan-sla        # Fase 3 nightly-explorers — GAP#5 SLA 24h Dead Man Switch (último sucesso < 86400s)
qa-gateway scan-rbac       # Sprint 4 NOVO — Fase A static scan rotas write (POST/PUT/PATCH/DELETE) × _require_role_with_audit
                           #               + Fase B DB scan users.role ∈ {VIEWER..OWNER} e <=1 OWNER/organização
```
Os comandos aceitam múltiplas fontes (env vars, flags, arquivos `.prom` ou fail) e gravam
`--failures-json <path>` para artefatos de CI, além de **exit codes rigorosos**:
  - `0`  = sucesso zero issues;
  - `1`  = falha de regra (ex: SLA violado / RLS desativado / OWNER duplicado);
  - `2+` = erro de infra (sem conexão DB, serviço unreachable, token vazio).

### 1.2 (Sprint 4 FINAL) Workflows CI/CD consumidores do qa-gateway × Rollback Automático
| Workflow (.github/workflows/*.yml) | Jobs | Consumo qa-gateway + automação |
|---|---|---|
| **ci.yml** | `gate-p0-00-rls` + `pytest-matrix 7×` + `gate-p0-01-oidc` | Python API `qa_gateway.rls.assert_tables_have_rls` + fallback inline equivalente |
| **deploy-staging.yml** | wait-ci-green → render ×4 hook → health → scan-rls → **rollback Render API** | `qa-gateway health` + `qa-gateway scan-rls` (staging DB); **NEEDS_ROLLBACK → POST /v1/services/{id}/rollback AUTOMÁTICO em 4 serviços** (R7 GAP#9) |
| **deploy-production.yml** | preflight semver → canary 10% → 30min observe → promote → **rollback AUTOMÁTICO se falhar** | `qa-gateway health` + `qa-gateway scan-rls` (prod réplica read-only); Rollback Render API automático P0 se promote/observe falhar |
| **nightly-explorers-live.yml** (02h BR) | preflight → 10 casos live RPC mainnet + polling 15min → `sla-dead-man-switch` | `qa-gateway scan-sla` + cria **Issue GitHub label `P1-critical sla-deadman investigation-down`** se último sucesso há > 24h (R5 GAP#5) |
| **e2e-pr-playwright.yml** (paths filter front/stack) | filter → stack compose → playwright `@critical-path|rbac|api-consumer` → comentário PR | `qa-gateway health` opcional em warmup; Playwright 4 suítes + trace upload artifact 30d (R6 GAP#6) |

   Deve existir **apenas uma vez** dentro de `qa_gateway/`; duplicatas em scripts YAML
   são proibidas (exceto fallback inline em ci.yml gate-p0-00-rls-b, garantido por exit codes 100% iguais).

### 2. Todo serviço Python (FastAPI) deve **importar Shared First, Fallback Inline**.
   O padrão OBRIGATÓRIO para middleware RLS, helpers `canonicalize_role()`, e futuros
   helpers de segurança de cada serviço é:

   ```python
   try:  # SHARED PACKAGE FIRST — SEMPRE tentar importar de packages/
       from ontrackchain_shared.middleware_rls import register_rls_context_middleware as _mw
       _mw(app, ...)
   except Exception:  # noqa: BLE001 — FALLBACK INLINE — equivalente SEMÂNTICO 1:1
       # Código inline idêntico ao do shared package.
       # Este bloco SÓ executa se o host NÃO tiver o shared package instalado.
   ```

   **Regra de governança**: O fallback inline **nunca pode divergir semanticamente** do shared.
   Antes de abrir um PR que altere o helper do shared package, **o desenvolvedor é OBRIGADO
   a aplicar a mesma alteração no fallback inline de TODOS os serviços que usam aquele helper**.

### 3. O CI não depende exclusivamente do `qa-gateway` package instalado.
   Para evitar o risco de build de CI quebrar por falta do hatchling ou do package
   `packages/qa-gateway/` buildando em um checkout raso (shallow), o job
   `gate-p0-00-rls` tem **dois estágios**:
   - `P0-00a`: usa `qa-gateway` (SSOT) via Python import (scan completo de 15 tabelas).
   - `P0-00b`: fallback Python heredoc inline idêntico ao do teste
     `tests/test_p0_rls_cross_tenant.py` (prova de isolamento A vs B).
   Se o `qa-gateway` falhar por qualquer motivo de infraestrutura, o P0-00b **ainda
   bloqueia merge** se existir vazamento cross-tenant.

### 4. Imagem Docker standalone para QA Gateway.
   O package tem CLI `qa-gateway` (console_scripts via Click) + Dockerfile standalone
   (não depende do repositório de aplicação). Esta imagem é usada:
   - Em `deploy-staging.yml` (Post Deploy Health Check + Rollback Gate);
   - Em `nightly-compliance.yml` (LGPD scan com dump staging);
   - Em validação manual de auditoria (fora do ciclo CI/CD normal).

## Consequências

### Prós
- **Fonte única + resiliência**: Se o shared quebrar, os serviços continuam funcionando
  (fallback inline equivalente).
- **Auditabilidade**: Logs de `qa-gateway scan rls` tem hash e versão do pacote,
  fácil provar para auditoria "o que rodou no dia 08/08/2026".
- **Escalabilidade**: Novo serviço Python = **2 minutos para aplicar o padrão
  shared-first + fallback inline**, copiando 1 bloco de ~100 linhas.
- **Reduz risco de regressão**: Mudar o regex UUID? Melhorar path bypass? Basta 1 arquivo:
  `middleware_rls.py` (e sincronizar fallbacks inline, regra #2).

- **Risco R2**: "Fallback inline divergiu sem ninguém perceber" → **Mitigação**: todo
  fim de sprint (Sprint Review) o `qa-gateway` gera um `checksums.sha256` dos blocos
  inline vs shared e o CI nightly valida divergências (dif > 0 = aviso).
- **Risco R3**: "Imagem Docker standalone pesada (>1GB)" → **Mitigação**: usa
  `python:3.11-slim` + apagar cache pip; meta < 300MB comprimida. Smoke test `qa-gateway --version` + 3 `--help` no build para confirmar imagem.
- **Risco R4**: "Dependências `psycopg[binary]` com versões diferentes entre serviços" →
  **Mitigação**: ADR não força mesma versão; `qa-gateway` declara pin de versão mínimo
  (`>=3.2.3`); serviços antigos ficam no seu pin, novos no mais novo.
- **Risco R5 (NOVO Sprint 3)**: "Exploradores live down e ninguém percebe → violação SLA
  silenciosa" → **Mitigação**: Job `sla-dead-man-switch` no `nightly-explorers-live.yml`
  usa `qa-gateway scan-sla` e **cria issue GitHub label `P1-critical sla-deadman`** se
  último sucesso há > 24h.
- **Risco R6 (NOVO Sprint 3)**: "Playwright e2e em PR falha por flaky RPC mainnet
  (rate limit)" → **Mitigação**: E2E em PR roda com `AUTH_MODE=dev` e
  `INVESTIGATION_RPC_ENABLED=false`; exploração live real fica APENAS no
  nightly-explorers 02h BR em horário de menor tráfego RPC.
- **Risco R7 (NOVO Sprint 4 — GAP#9 fechado)**: "Deploy staging/prod quebrou, ninguém
  executa rollback por medo/esquecimento → downtime 2h+" → **Mitigação**: Jobs
  `summary-or-rollback` (staging) e `summary-and-notify` (prod) implementam **Render
  REST API Automático** com secrets `RENDER_API_TOKEN_{STAGING|PROD}` +
  `RENDER_{AUTH|PUBLIC|INVESTIGATION|CASE}_SERVICE_ID_{STAGING|PROD}`.
  POST `https://api.render.com/v1/services/<SVC_ID>/rollback` — 4 serviços em paralelo
  (throttling 300ms entre calls); exit code 1 garante bloqueio CI até rollback bem-sucedido.
- **Risco R8 (NOVO Sprint 4 — GAP#7 fechado 95%)**: "Alertas silenciosos, métricas SLA
  e RLS violadas sem notificar ninguém" → **Mitigação**:
  `infra/observability/platform.rules.yml` adicionou 3 regras Prometheus Alertmanager
  (1) `InvestigationExplorerSlaDeadManSwitch for 5m severity=critical`,
  (2) `RlsViolationBurstDetected rate(http_requests_total{status=401,reason=rls_organization_mismatch}[5m])>0.333 severity=warning`,
  (3) `E2ePlaywrightSuccessRateBelowSla < 0.90 severity=warning`. Todas têm runbook
  link em label `runbook:` e disparam Alertmanager → Slack/Teams webhook via monitoring-api.

### Workflow de Aplicação (Regra #2 prática)
1. Abrir PR alterando `packages/shared/src/ontrackchain_shared/<helper>.py`.
2. Abrir **no mesmo PR** commits sincronizando os fallbacks inline de:
   - `apps/case-management/src/case_management/main.py`
   - `apps/auth-service/src/auth_service/main.py`
   - `apps/investigation-api/src/investigation_api/main.py`
3. Adicionar 1 teste em `tests/test_p0_rls_cross_tenant.py` que valide o novo cenário
   (ex: novo bypass path).
4. Marcar no PR label `needs-security-review` (1 par extra de olhos antes do merge).
5. **Se PR altera CI/CD ou workflow deploy**:
   - Adicionar screenshots ou evidência de passagem do workflow em fork pessoal/branch de teste.
   - Validar sintaxe YAML local com `yamllint .github/workflows/` ou fallback `python -c`
     balanceamento de chaves `{}` e `[]`.
6. **SEMPRE evitar heredocs Python/YAML em blocos `run: |`** — trocar por
   `echo "linha" > /tmp/_aux.py` + `python3 /tmp/_aux.py`. Evita `ScannerError: while
   scanning a simple key could not find expected ':'` (regra padrão Sprint 3+4).
7. **Se PR adiciona comando novo qa-gateway**: adicionar no CI `job gate-p0-01-oidc`
   (ou job equivalente) o comando `--help` para garantir que o comando não quebre em
   merge, + adicionar linha na tabela §1.1 deste ADR e link de consumo na tabela §1.2.
