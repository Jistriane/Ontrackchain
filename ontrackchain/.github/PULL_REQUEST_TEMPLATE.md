<!--
  PULL REQUEST TEMPLATE — Ontrackchain (Sprint 7 M2)
  NÃO apague seções abaixo. Seção "N/A" marque [x] onde aplicável.
  O que for falso/falta preencher → PR fica bloqueado pelo CODEOWNERS.
-->

## Resumo Executivo (1-2 frases)
> (Motivação, qual problema resolvido e qual estratégia de alto nível)

---

## Tipo de PR
- `[ ] Bugfix (hotfix / regressão / incidente P0/P1)`
- `[ ] Feature nova (tem correspondente Issue #NNN FEAT ou epic)`
- `[ ] Refactor (sem mudança funcional — DRY, SOLID, arquitetura interna)`
- `[ ] Config / Infra / CI (YAML, Grafana, labels, secrets provisionamento)`
- `[ ] Documentação (README, ADR, markdown docs/adr/*)`
- `[ ] Dependências (bump CVE remediado — já passou por pip-audit HIGH/CRITICAL = 0)`

Issue relacionada (se houver): `Closes #NNN, Refs #MMM, Partially implements #PPP`

---

## Checklist OBRIGATÓRIO (Todo PR deve marcar TUDO que é aplicável)
### 🔒 Segurança & RLS / RBAC
- `[ ] NÃO toquei em nada de RLS/RBAC/middleware/auth → pular esta seção → marcar abaixo "N/A 🔵"`
- `[ ] Se toquei RLS/RBAC: PR TEM label `needs-security-review` E CODEOWNER security reviewou`
- `[ ] RLS: package `shared/middleware_rls.py` E fallback inline em 3×`main.py` (auth/case/inv) SÃO IDÊNTICOS semanticamente (Regra ADR-018 §2)`
- `[ ] RBAC: `qa-gateway scan-rbac --apps-root apps/ --database-url $STAGING_DB_URL` passou 0 issues`
- `[x] N/A (esta seção) 🔵`

### ✅ QA Gateway SSOT 6 comandos (ADR-018 §1.1 / §Workflow item 7)
- `[ ] NÃO adicionei novo comando qa-gateway → pular esta seção`
- `[ ] Adicionei comando novo: incluí `qa-gateway <comando-novo> --help` obrigatório no job `qa-gateway-cli-smoke` de ci.yml`
- `[ ] Incluí linha nova na tabela §1.1 de ADR-018 + tabela §1.2 qual workflow consome`
- `[x] N/A (esta seção) 🔵`

### 🧪 Cobertura Testes (Python + E2E)
- `[ ] pytest-matrix 7× CI verde (apps/auth/case/inv/ai + packages/shared/qa-gateway/agents)`
- `[ ] Alterei shared package ou middleware_rls: rodei `tests/test_p0_rls_cross_tenant.py` = 0 leak`
- `[ ] Alterei FRONTEND (apps/frontend/**) OU case/auth/inv: ADICIONEI label `e2e-required` NO PR (Sprint 6 upgrade label-gate E2E shard=8)`
- `[ ] Nenhuma das opções (somente docs ou infra YAML): label `e2e-required` desnecessário`

### 🛡️ SAST + CVE (Sprint 7 M1 agora BLOQUEANTE)
- `[ ] `sast-bandit-python`: ZERO findings MEDIUM+/HIGH com confiança MEDIUM+ (bandit -lll -iii)`
- `[ ] `dependency-audit-pip`: ZERO HIGH + ZERO CRITICAL CVE (7 roots apps+packages)`
- `[ ] Apenas docs YAML/ADR: não aplicável (ci.yml validado por yaml safe_load mesmo assim)`

### 🚀 Deploy / Rollback (Sprint 4 GAP#9 Render API automático)
- `[ ] Alterei código de serviço Python (main.py / package) → rollback automático staging/prod validado via deploy-staging.yml summary-or-rollback`
- `[ ] Alterei YAMLs deploys (`deploy-staging.yml` / `deploy-production.yml`) → fiz teste em branch fork pessoal (screenshot workflow)`
- `[x] N/A (somente docs / CI / templates)`

### 📊 Observabilidade (GAP#7 Prometheus + Grafana Dashboard Único)
- `[ ] Adicionei métrica nova: métrica tem `{org_id, service, endpoint}` labels?`
- `[ ] Adicionei regra de alerta nova em `platform.rules.yml`: tem painel correspondente no dashboard `ontrackchain-qa-overview.json` (ADR-018 Sprint 6 item 9)?`
- `[x] N/A (esta seção) 🔵`

### 🧭 Governança (ADR-018 + Workflow aplicação itens 1..10)
- `[ ] Mudou padrão de segurança/arquitetura: criado ADR novo OU anexada Sprint update em ADR-018?`
- `[ ] Evitei heredocs Python/YAML em blocos `run: |` (padrão echo linha → /tmp/_arquivo.py → executa)? (Sprint 3..6 sempre evitou ScannerError!)`
- `[x] N/A 🔵`

---

## Screenshots / Evidências (se aplicável)
<!-- Cole GIF/screenshot/link para artifact do CI (Playwright merged report, SAST artifact JSON, etc). -->
| Item | Evidência |
|---|---|
| CI verde (9 jobs ci.yml) | ![ci](https://img.shields.io/badge/ci-passing-green) · run_id:<NNNNNNNN> |
| E2E Playwright (se tem label `e2e-required`) | [artifact merged](https://github.com/..../runs/<run_id>/artifacts) |
| Bandit (0 issues) | artifact sast-bandit-<sha>.json `results.length = 0` |
| pip-audit (0 HIGH/CRITICAL) | artifact pip-audit-<sha>.zip |

---

## Rollback / Plano B — Se algo der errado
- Como dar rollback? (ex: `git revert <sha>` → deploy-staging roda automaticamente no commit revertido)
- Tempo estimado até estabilizar: `<X> min`
- Ponto de rollback confirmado por: `[ ] staging rollback automático render hook` `[ ] manual`
