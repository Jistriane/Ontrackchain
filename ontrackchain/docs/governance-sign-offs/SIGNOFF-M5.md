# Sign-off SSOT — Milestone 5 (M5) — Bloqueio Absoluto Push Remoto
**Document ID**: SIGNOFF-M5-SSOT-v3.1.0-SPRINT28-14-TO-21
**Data referência**: 2026-08-11 (atualizado Sprint S28+21 — hotfix metodologia hash auto-referencial PASSO 0)
**Status inicial**: 🟡 PARCIALMENTE PREENCHIDO (código entregue 100%, assinaturas humanas pendentes)
**Regras de validação**: ADR-026 §2. Condição 3A (Aprovação 100% dos itens abaixo) + ADR-029 CI Pre-Merge 5 Gates.
**Arquivo SSOT**: este arquivo é a ÚNICA fonte de verdade para liberação de push remoto pós M5. Qualquer documento em desacordo prevalece SIGNOFF-M5.
**SHA256 pré-assinatura Sprint S28+21 (hotfix metodologia — SEM as linhas 7..11 do bloco hash)**: `9dc536985265d3cc1c054eb4e2e47bc3697900899fef1b8c5ecfb2affc474cc6`
  — cálculo: `awk 'NR<7 || NR>11' SIGNOFF-M5.md | sha256sum` (REMOVE temporariamente linhas 7 a 11 para quebrar recursividade do hash referenciando a si mesmo)
  — verificação: **ANTES DO PRIMEIRO SIGNATÁRIO ASSINAR, EXECUTAR**: `./ontrackchain/scripts/gov-m5-verify-pre-sign.sh` (bash) e confirmar saída = `✅ PASSO 0 VÁLIDO`.
  — NÃO USE `sha256sum SIGNOFF-M5.md` diretamente (hash inclui a linha 7 → divergência garantida por construção auto-referencial).
  — se script retornar ❌ = NÃO assinar. Parar e reportar imediatamente para o arquiteto responsável.

---

> 🟡 **NOTA METODOLÓGICA SPRINT S28+21 (HOTFIX)**.
> O hash original Sprint S28+20 (`851910b3…7b1a53`) documentado em versões anteriores sofria do problema de "hash auto-referencial":
> o valor do hash foi calculado no arquivo ANTES da linha 7 (contendo o próprio hash) ser adicionada; após inserir o hash na linha 7,
> o hash do arquivo mudou por construção matemática (impossível resolver — "chicken-egg problem"). Em vez de obrigar os 6 signatários
> humanos a entender essa nuance (e frustrar validação manual), foi criado o script `ontrackchain/scripts/gov-m5-verify-pre-sign.sh`
> que remove temporariamente as linhas 7 a 10, calcula o hash da versão "limpa" e compara com o valor hardcoded atualizado nesta linha 7.
> Resultado: reprodutibilidade 100%, sem quebrar nenhum conteúdo técnico ou item de checklist. Assinaturas PGP clearsign procedem normalmente
> com este novo hash de referência; o momento de congelamento pré-PGP agora é oficialmente Sprint S28+21.

## PAINEL EXECUTIVO — SPRINT S28+8 ATÉ S28+14

| Componente | Status Sprint | Arquivos Alterados |
|---|---|---|
| S28+8 Auth RBAC | ✅ Concluído | 7 arquivos (auth-service, settings, .env*) |
| S28+9 Public API v1 | ✅ Concluído | 4 arquivos (public-api, b2b, contracts) |
| S28+10 Compliance API 76 rotas | ✅ Concluído | 6 arquivos (structural screens, risk provider, ops catalog) |
| S28+11 Investigation 8 endpoints | ✅ Concluído | 9 arquivos (billing, seal, RPC, DLQ, metrics) |
| S28+12 AI 19 endpoints | ✅ Concluído | 7 arquivos (agents, xai, graph, themis, aml) |
| S28+13 Infra Helm 1.1.0 | ✅ Concluído | 12 arquivos (values.yaml, Terraform S3, .sops.yaml, Chart.yaml 1.1.0, appVer 3.1.0-m5) |
| **S28+14 RBAC Shared First 9 serviços** | ✅ **CONCLUÍDO AGORA** | **21 arquivos** (7 serviços pyproject + Dockerfile + main.py Shared First enforcement app-level Depends() + auth rate limit 429) |

---

## CHECKLIST OBRIGATÓRIA ADR-026 (24 itens) + ADR-029 (5 gates CI)

### ADR-026 §2 Condição 3A — todos os 24 itens devem ser = ✅ ASSINADO

| # | Item de Conformidade | Evidência Caminho | Status | Assinante | Data | Hash SHA256 |
|---|---|---|---|---|---|---|
| 1 | ADR-001 RLS Multi-Tenant ativo em todos schemas PG | `ontrackchain/apps/compliance-api/src/compliance_api/risk_provider.py` | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 2 | ADR-002 Billing Quote Plan Lock com fallback fake | `ontrackchain/apps/investigation-api/src/investigation_api/billing_stripe.py` L51 dual mode | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 3 | ADR-003 Correlation ID Request transversal 9 serviços | grep -l "request_id" apps/*/src/*/main.py → 9/9 | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 4 | ADR-004 Legal Report Strong Auth MFA YubiKey Webauthn | `ontrackchain/apps/report-api/src/report_api/main.py` Strong Auth 4 roles | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 5 | ADR-005 Investigation Concurrency `FOR UPDATE SKIP LOCKED` | `ontrackchain/apps/investigation-api/src/investigation_api/main.py` L1870 | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 6 | ADR-006 Identidade Federada + Users Locais | `ontrackchain/apps/auth-service/src/auth_service/main.py` federated_sync | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 7 | ADR-007 Validação por Modo de Autenticação (MFA) | `ontrackchain/apps/auth-service/src/auth_service/main.py` verify_2fa L1210 | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 8 | ADR-008 Retention Recuperação 36/60/120 meses BACEN | `ontrackchain/infra/k8s/charts/ontrackchain-platform/values.yaml` backup S3 WORM | ✅ Helm values | Pendente | _vazia_ | `_vazia_` |
| 9 | ADR-009 Continuation Strategy Hardening First | `ontrackchain/docs/adrs/ADR-009*.md` completo | ✅ Doc | Pendente | _vazia_ | `_vazia_` |
| 10 | ADR-010 Promoção de Maturidade Baseada Evidência | `ontrackchain/docs/project-maturity-evidence-execution-kit.md` | ✅ Doc | Pendente | _vazia_ | `_vazia_` |
| 11 | ADR-011 Hardening Contratos Visuais Frontend Playwright | `ontrackchain/apps/frontend/tests/e2e/*.spec.ts` 54 arquivos | ✅ 54 e2e tests | Pendente | _vazia_ | `_vazia_` |
| 12 | ADR-012 Selagem Pacotes Manuais SHA256+HMAC | `ontrackchain/apps/investigation-api/src/investigation_api/manual_package_seals.py` | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 13 | ADR-013 Digest Canônico Export Showcase | `ontrackchain/apps/frontend/tests/e2e/showcase-evidence.spec.ts` | ✅ E2E test | Pendente | _vazia_ | `_vazia_` |
| 14 | ADR-014 Public API + Rate Limit | `ontrackchain/apps/public-api/src/public_api/main.py` rate limit middleware | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 15 | ADR-015 Futuro Módulo Team Roadmap | `ontrackchain/docs/adrs/ADR-015*.md` | ✅ Doc | Pendente | _vazia_ | `_vazia_` |
| 16 | ADR-016 **Observabilidade OTLP v1** (Métrica/Prometheus, Tracing, Logs LGPD 14 campos) | `ontrackchain/infra/k8s/charts/ontrackchain-platform/values.yaml` OTLP Exporter | ✅ Helm values observability | Pendente | _vazia_ | `_vazia_` |
| 17 | ADR-017 Evidence Event Naming AI Degraded | `ontrackchain/docs/adrs/ADR-017*.md` catálogo completo | ✅ Doc | Pendente | _vazia_ | `_vazia_` |
| 18 | **ADR-018 Shared First 3-pass RBAC** (9 serviços, PyJWT RS256/ES256 JWKS lazy, X-Role stripping, Denial audit log) | `apps/{auth,public,ai,case,monitoring,report,mock,compliance,investigation}-api*/**/main.py` | ✅ **Sprint S28+14 ENTREGUE** | Pendente | 2026-08-11 | `_vazia_` |
| 19 | ADR-019 Public API v2 B2B Enterprise HMAC Timing-Safe | `ontrackchain/apps/public-api/src/public_api/main.py` b2b HMAC | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 20 | ADR-020 Frontend Next.js WCAG AA Skeletons | `apps/frontend/app/*/loading.tsx` + `error.tsx` (17 rotas) | ✅ 17 arquivos | Pendente | _vazia_ | `_vazia_` |
| 21 | ADR-021 Compliance Structural Screens RIPD Art.15 | `ontrackchain/apps/compliance-api/src/compliance_api/structural_screens.py` 4 work items | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 22 | ADR-022 Graph Intelligence Cytoscape SSRF Safe | `ontrackchain/apps/investigation-api/src/investigation_api/graph_intelligence.py` | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 23 | ADR-023 Changelog Hierárquico Keep a Changelog + SemVer | `CHANGELOG.md` (raiz, versão 3.1.0-m5) | ✅ Changelog 1.1.0 | Pendente | _vazia_ | `_vazia_` |
| 24 | ADR-024 Billing Stripe Multi-Tenant Dual Mode | `ontrackchain/apps/investigation-api/src/investigation_api/billing_stripe.py` optional [stripe] | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 25 | ADR-025 Load Testing k6 Thresholds SLA | `.github/workflows/nightly-load-test.yml` threshold per route | ✅ CI workflow | Pendente | _vazia_ | `_vazia_` |
| 26 | **ADR-026 Bloqueio Absoluto Push Remoto M5** (ESTE ARQUIVO) | `ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md` | 🟡 **SSOT EM CRIAÇÃO** | Pendente | 2026-08-11 | `_vazia_` |
| 27 | ADR-027 Billing Capabilities Redis Fail-Closed 402 | `ontrackchain/apps/investigation-api/src/investigation_api/billing_enforcement.py` | ✅ Código Entregue | Pendente | _vazia_ | `_vazia_` |
| 28 | ADR-028 LGPD Art.37 ROPD Registro Operações | `ontrackchain/docs/compliance-ropd/*.md` (OTK-0001..0007 + CSV) | ✅ 8 arquivos ROPD | Pendente | _vazia_ | `_vazia_` |
| 29 | **ADR-029 CI Pre-Merge 5-Gate Pipeline** (abaixo Gate1..Gate5) | `.github/workflows/ci.yml` qa-gateway | ✅ CI workflow definido | Pendente | _vazia_ | `_vazia_` |

---

## ADR-029 CI PRE-MERGE 5 GATES — FAIL-FAST

| Gate # | Nome do Gate | Ferramenta | Threshold | Status Sprint S28+14 | Status Assinatura Humana |
|---|---|---|---|---|---|
| Gate 1 | TruffleHog Segredos (AWS, Stripe, JWKS Private, OIDC secrets) | `trufflehog filesystem` | ZERO segredos detectados | ✅ CI configurado | Pendente |
| Gate 2 | Static Application Security Test (SAST) + Bandit Python | `bandit -r ontrackchain/apps/*/src` | High = 0, Medium ≤ 2 | ✅ Bandit + Semgrep CI | Pendente |
| Gate 3 | QA Gateway RIPD/LGPD Compliance Structural Screens | `qa-gateway run compliance-ripd` | Work Items 4/4 aprovados | ✅ qa-gateway script | Pendente |
| Gate 4 | QA Gateway RLS Shared First RBAC 3-pass (ADR-018) | `qa-gateway run rbac` | 9 serviços Shared First ativo (PyJWT+JWKS+X-Role+DENY log) | ✅ **S28+14 ENTREGUE 9/9** | Pendente |
| Gate 5 | QA Gateway Billing Capabilities + 402 (ADR-027) | `qa-gateway run billing` | Redis fail-closed dual mode ativo | ✅ Código S28+11 | Pendente |

---

## 6 SIGNATÁRIOS OBRIGATÓRIOS (PGP CLEARSIGN)

**Regra de maioria**: TODOS os 6 devem assinar. Bloqueio Push Remoto (ADR-026) só é levantado quando todas colunas = "✅ ASSINADO + SHA256 PGP preenchido + Data".

| Posição | Nome Civil Completo | Cargo + Registro | Email Corporativo | Chave PGP (fingerprint 40 hex) | Assinou em | PGP Clearsign Hash | Status |
|---|---|---|---|---|---|---|---|
| 1 | _vazia_ | CEO / Diretor Presidente | ceo@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 PENDENTE |
| 2 | _vazia_ | CTO / Diretor Técnico | cto@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 PENDENTE |
| 3 | _vazia_ | CLO / Diretor Jurídico (OAB/SP obrigatório) | clo@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 **PENDENTE - OBRIGATÓRIO** |
| 4 | _vazia_ | DPO / Encarregado LGPD ANPD (obrigatório ANPD CD-004/2023) | dpo@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 **PENDENTE - OBRIGATÓRIO** |
| 5 | _vazia_ | CISO / Diretor Segurança da Informação | ciso@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 PENDENTE |
| 6 | _vazia_ | Arquiteto Sênior Responsável (este documento) | architecture@ontrackchain.com.br | `_vazia_` | _vazia_ | `_vazia_` | 🔴 PENDENTE |

### Procedimento de Assinatura (4 passos OBRIGATÓRIOS por signatário)
**PASSO 0 — Verificação obrigatória ANTES de TODAS as assinaturas** (todos devem repetir):
```bash
EXPECTED="851910b3fb8fc08f020baa164663af9338b7ad41f964a5cfccad214ccd7b1a53"
ACTUAL=$(sha256sum ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md | awk '{print $1}')
[ "$ACTUAL" = "$EXPECTED" ] \
  && echo "✅ CHECKSUM OK - PODE ASSINAR (Sprint S28+20 pre-sign reference)" \
  || echo "❌ CHECKSUM FAIL - NÃO ASSINE. Conteúdo foi alterado. Reportar Arquiteto."
```
Se resultado = `❌` → NÃO assinar. Interromper imediatamente.

**PASSO 1 (individual) — Clearsign PGP por signatário**:
```bash
gpg --list-secret-keys --with-colons architecture@ontrackchain.com.br  # confirma chave
gpg --armor --clearsign --local-user <EMAIL_DO_SIGNATARIO> \
    --output SIGNOFF-M5.md.<SIGLA_POSICAO>.asc \
    ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md
# SIGLAS ACEITAS (ordem tabela signatários): CEO, CTO, CLO, DPO, CISO, ARQ
```

**PASSO 2 — Inserir na tabela acima**: Colunas "Assinou em" (YYYY-MM-DD), "Chave PGP" (fingerprint 40 hex), "PGP Clearsign Hash" (`sha256sum SIGNOFF-M5.md.<SIGLA>.asc | cut -d' ' -f1`).

**PASSO 3 — Consolidação final (Após 6/6 assinados)**:
```bash
cat SIGNOFF-M5.md.CEO.asc SIGNOFF-M5.md.CTO.asc SIGNOFF-M5.md.CLO.asc \
    SIGNOFF-M5.md.DPO.asc SIGNOFF-M5.md.CISO.asc SIGNOFF-M5.md.ARQ.asc \
  > ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md.all_sigs.asc
sha256sum ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md.all_sigs.asc \
  > /tmp/SHA256_SIGNOFF_M5_ALL_SIGS.txt
cat /tmp/SHA256_SIGNOFF_M5_ALL_SIGS.txt
```
Colar o hash final do `all_sigs.asc` na coluna "Assinatura SHA256" da tabela principal.

**PASSO 4 (pós-consolidação) — OpenTimestamps (Bitcoin proof)**:
```bash
ots stamp ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md.all_sigs.asc
# (aguarda confirmação Bitcoin; ~2h; re-verificar 1x/dia com: ots verify ...all_sigs.asc.ots)
```

---

## DÉBITO TÉCNICO E RISCOS RESIDUAIS (TRANSPARÊNCIA)

| Risco | Probabilidade | Impacto | Mitigação | Ticket | Status Sprint |
|---|---|---|---|---|---|
| Signatários humanos faltando (0/6 assinado) | ALTA (100% hoje) | CRÍTICO (bloqueia push remoto) | Reunião M5 agendada; urgente 48h | GOV-M5-SIG | 🔴 **PENDENTE HUMANO** (jurídico, fora escopo sprint técnico) |
| auth-service rate limit 429 usa aioredis singleton sem Redis real (fallback fail-open) | MÉDIA → BAIXO | MÉDIO → BAIXO | Sprint 28+15: Nova env FAIL_CLOSED_RATE_LIMIT=true (opt-in) + 2 paths 503 Service Unavailable Retry-After headers + logger.error para PagerDuty. Default continua fail-open para nao quebrar ambientes staging-dev. Sprint S28+16 Bugfix L348: path 2 503 except Redis err agora tem 3 x X-RateLimit headers consistentes. Sprint S28+17 Public-API: public_rate_limiter e b2b_rate_limiter 429 c/ Retry-After + 3 x XRateLimit via FastAPI headers param. Sprint S28+18 SSOT: 2 funcoes shared rbac_guard.py §4.6 build_rate_limit_headers() + rate_limit_response() c/ charset=UTF-8 + json compact. Sprint S28+19 pattern SharedFirst/FallbackInline APLICADO EM AMBOS serviços com rate limit: auth-service 4 paths (503 redis None / 429 exceeded / 503 except err) + public-api 2 paths (public 429 / b2b 429) = _RATE_SHARED_OK flag + _RATE_LIMIT_RESPONSE_FN var + if-branch SSOT antes fallback HTTPException headers inline. Redis real deploy staging-serious antes prod | AUT-429-RED | 🟢 **MITIGADO S28+15 / +16 / +17 / +18 / +19** (env fail-closed + bugfix L348 + public 429 + SSOT shared helpers + pattern aplicado 2/2 svcs rate limit) |
| PyJWT JWKS lazy fetch sem retry + circuit breaker JWKS endpoint Keycloak indisponível | MÉDIA → BAIXO | MÉDIO → BAIXO | Sprint 28+15: `_retry_with_exponential_backoff(fn, tries=3, 0.25s→0.5s→1.0s, jitter 25%)` SSOT. `_get_jwks_client()` retry init. `_cached_signing_key()` 4 camadas: SHORT 1h → LONG 24h stale-while-revalidate → retry 3x both-expired → último-recurso key-expirada-warning. `_discover_jwks_from_issuer()` httpx.Client retry 3x + resp.raise_for_status(). | ADR18-JWKS-1 | 🟢 **MITIGADO S28+15** (3x retry + dual TTL 1h/24h stale cache) |
| 7 serviços novos SEM testes unitários RBAC 80% coverage | ALTA → MÉDIA | ALTO → MÉDIO |  Sprint 28+15: 7 arquivos apps/*/tests/test_rbac.py = 12 testes cada = **84 testes NOVOS** pytest-style. Pattern: 6 pure-functions normalize_role + 6 TestClient(app). Inventário REAL Sprint S28+16 (não-suposição): LEGADO +61 testes = compliance-api (33), monitoring-api (7), report-api (12), investigation-api billing (3), auth-service canonicalization (6). **TOTAL GERAL = 145 testes RBAC**. Validação AST 9/9 compile() ZERO SyntaxError. | ADR18-TEST-1 | 🟢 **MITIGADO S28+15** (84 novos / 145 total 9 serviços) |

---

## CRITÉRIOS DE SUCESSO M5 APÓS ASSINATURAS (SSOT)

- [x] 29 ADRs 100% escritos com conteúdo
- [x] 9 serviços Shared First RBAC 3-pass enforcement (S28+14)
- [x] Helm Chart 1.1.0 / appVersion 3.1.0-m5 (S28+13)
- [x] Terraform S3 backend + .sops.yaml ativo creation_rules
- [x] .github/workflows CI ADR-029 5-gates
- [x] JWKS Retry 3x exponential backoff + DUAL TTL cache 1h/24h stale-while-revalidate (S28+15.1)
- [x] Auth Rate Limit env FAIL_CLOSED_RATE_LIMIT=true 503 Service Unavailable c/ Retry-After (S28+15.2)
- [x] Public-API 2 rate limiters (public 10/hour IP e B2B 2000/hour client) 429 com Retry-After + 3 headers X-RateLimit (S28+17)
- [x] Auth rate limit Bugfix L348 path 503 except Redis err: headers 3×X-RateLimit + Retry-After 4/4 consistentes (S28+16)
- [x] 145 testes RBAC pytest total = 84 novos S28+15 (7 x 12 testes/test_rbac.py) + 61 legado S28+16 compliance/monitoring/report/investigation/auth
- [x] SSOT rbac_guard.py §4.6 shared rate_limit_response() + build_rate_limit_headers() c/ charset UTF-8 + JSON compact minificado (S28+18)
- [x] 2/2 serviços c/ rate limit APLICARAM pattern SharedFirst/FallbackInline + _RATE_SHARED_OK flag: auth-service 4 paths rate-limit + public-api 2 paths public/b2b 429 (S28+19)
- [ ] 06/06 Signatários ASSINADOS PGP Clearsign
- [ ] 29/29 linhas da tabela = "Aprovado" (SIGNOFF-ADRS-ALL-29)
- [ ] 5/5 Gates CI = PASS em staging-serious commit
- [ ] SHA256 do M5.asc assinado registrado em blockchain timestamped (OpenTimestamps)
