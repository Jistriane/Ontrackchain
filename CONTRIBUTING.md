# Contribuindo para o Ontrackchain — Metodologia FAIL-CLOSED (Sprints S28+XX)

> **⚠️ Princípio fundamental**: Todo commit é FAIL-CLOSED. Qualquer regressão nos 8 gates padrão BLOQUEIA o merge, independentemente de "funcionar no meu ambiente".
> 
> **Papel do colaborador**: Entregar UM sprint por vez com Working Tree LIMPA, 8/8 gates PASS e hard constraints 0 violações.

---

## 1. Hard Constraints NÃO NEGOCIÁVEIS (válidos para TODO commit, TODO sprint)

NENHUM desses itens pode ser violado — validação automática via gates G1 (M5) e G8 (settings):

| # | Constraint | Como validar | Gate |
|---|---|---|---|
| HC-1 | `SIGNOFF-M5.md` INTACTO. NÃO alterar NENHUM byte. Hash L7 fixo obrigatório: `9dc536985265d3cc1c054eb4e2e47bc3697900899fef1b8c5ecfb2affc474cc6` | `make gov-m5-verify` | G1 |
| HC-2 | 0 segredos hardcoded. TUDO via `${{ secrets.X }}` ou `.env.*.example` (SOMENTE placeholders, 0 valores reais). TruffleHog --only-verified bloqueia push. | `make scan-secrets-strict` (opcional local, obrigatório CI remoto) | G8 + TruffleHog |
| HC-3 | `.github/settings.yml` NÃO PODE ter jobs `sonarcloud-*` adicionados aos 13 required contexts. QA Gate SEMPRE 2 jobs obrigatórios: `qa-gateway-cli-smoke` + `qa-gateway-scan-sla-ci-p008`. | `make settings-dry-run` | G8 |
| HC-4 | NENHUMA alteração de código de negócio de apps/pacotes sem sprint associado e validação AST + gates. Sprints P2/P3 de governança NÃO tocam src/. | `grep` + revisão humana + `healthz-bypass-test` (G4 garante RBAC healthz intacto) | G4 + humano |

---

## 2. Ciclo de Sprint Padrão (5 passos + COMMIT)

Todo sprint segue metodologia INV → DESIGN → IMPL → DOCS → VAL → COMMIT:

1. **INV (Investigação)**: Mapear estado atual, arquivos a tocar, lacunas.
2. **DESIGN**: Definir implementação, trade-offs, arquivos a alterar.
3. **IMPL**: Escrever/editar código (TAB 0x09 ASCII para blocos de comando Makefile).
4. **DOCS**: Atualizar `README.md` (seções relevantes) + `ontrackchain/pyproject.toml` (roadmap comentado L185+).
5. **VAL**: Rodar 8/8 gates padrão FAIL-CLOSED. NÃO skippar.
6. **COMMIT**: Working Tree LIMPA. Mensagem de commit no padrão (abaixo).

---

## 3. 8 Gates Padrão FAIL-CLOSED (validação obrigatória TODO sprint)

| Gate | Target Makefile | O que valida | Método |
|---|---|---|---|
| G1 | `gov-m5-verify` | Hash auto-referencial SIGNOFF-M5.md L7 | `sha256sum` awk NR<7 \|\| NR>11 |
| G2 | `gov-m5-unit-test` | Teste fail-closed do validador M5 (2 cenários: A PASS / B FAIL esperado exit=1) | bash script `s28p25-test-gov-m5-verify.sh` |
| G3 | `shell-syntax` | `bash -n` sintaxe 21 scripts shell do monorepo | `s28p25-bash-syntax-check.sh` |
| G4 | `healthz-bypass-test` | 18 asserts: 9 serviços FastAPI têm `/healthz` e `/metrics` públicos bypass RBAC (AST grep + regex em main.py) | `s28p24-check-healthz-metrics-bypass.sh` |
| G5 | `all-checks -n` | Dry-run parse do aggregator 15 gates (não executa hatch/mypy). Garante sintaxe Makefile válida. | GNU Make `--dry-run` |
| G6 | `typecheck -n` | Dry-run parse do target typecheck (hatch mypy strict). Garante sintaxe Makefile válida. | GNU Make `--dry-run` |
| G7 | `qa-gateway-all-strict-ci -n` | Dry-run parse do qa-gateway STRICT 4 scans (RBAC, LGPD ROPD, Billing, AML Live). | GNU Make `--dry-run` |
| G8 | `settings-dry-run` | Repository settings validador Python: 13 required contexts, 0 sonarcloud-* PROIBIDO, 2 jobs QA obrigatórios, 3 environments, 14 labels, GHAS + Push Protection enabled | `s28p36-settings-validate.py` |

**Resumo de atalhos (Sprint S28+54 P4)**:
- `make ci-validate` → 4 gates rápidos (<10s): G1 + G3 + G4 + G8.
- `make ci-local` → 8/8 gates completos (~40s). **RECOMENDADO ANTES DE TODO COMMIT**.
- `make ci-pre-merge` → 8 gates + `make lint` (Ruff) + `make test-shared` (6 unit tests). **RECOMENDADO ANTES DE PR/PUSH**.
- `make ci-smoke` → qa-gateway-smoke CLI rápido.

---

## 4. Estrutura Monorepo Resumida

```
Ontrackchain/
├── Makefile                         # GATES 8 FAIL-CLOSED + Utilitários dev (S28+49/S28+51/S28+54)
├── README.md                        # Visão geral, gatilhos, utilitários, observabilidade
├── CONTRIBUTING.md                  # ESTE ARQUIVO: metodologia + hard constraints + SOP
├── .gitignore                       # Hardening: tmp_qa, tmp_audit, .env*.bak, venv, override compose
├── .github/
│   ├── settings.yml                 # HC-3: 13 required contexts, QA Gate 2 jobs obrigatórios
│   └── workflows/                   # CI remoto: TruffleHog segredos + qa-gateway + pytest apps
├── SIGNOFF-M5.md                    # HC-1: Documento de governança (hash L7 fixo, NÃO EDITAR)
└── ontrackchain/                    # Monorepo Python
    ├── pyproject.toml               # mypy strict + roadmap sprints S28+XX comentado (L185+)
    ├── docker-compose.yml           # 21 services (S28+50 otimizado + S28+52 depends_on healthy)
    ├── Dockerfile.*                 # 11 Dockerfiles single-stage non-root UID/GID 10001 (S28+50)
    ├── apps/                        # 9 FastAPI + 1 frontend + mock-oidc
    │   ├── auth-service/src/auth_service/main.py           # P0 logging estruturado S28+48
    │   ├── public-api/src/public_api/main.py               # P0
    │   ├── case-management/src/case_management/main.py     # P0
    │   ├── compliance-api/src/compliance_api/main.py       # P3 S28+53
    │   ├── investigation-api/src/investigation_api/main.py # P3 S28+53
    │   ├── monitoring-api/src/monitoring_api/main.py       # P3 S28+53
    │   ├── report-api/src/report_api/main.py               # P3 S28+53
    │   ├── ai-service/src/ai_service/main.py               # P3 S28+53
    │   └── mock-oidc/src/mock_oidc/main.py                 # P3 S28+53
    ├── packages/
    │   ├── shared/src/ontrackchain_shared/       # logging_util.py (S28+48), RBAC helpers
    │   ├── qa-gateway/src/qa_gateway/            # CLI scan: RBAC / LGPD / Billing / AML
    │   └── agents/src/ontrackchain_agents/       # LangChain agentes compliance
    └── scripts/                                   # Shell scripts de governança (21 scripts bash -n)
```

---

## 5. Padrão de Mensagem de Commit

```
Sprint S28+XX PX: Título Curto (resultado esperado, 0 regressão)

Hard constraints (0 violações):
  · SIGNOFF-M5.md INTACTO (hash L7: 9dc53698... — G1 M5 PASS)
  · settings.yml INTACTO (13 contexts, G8 PASS). 0 job sonarcloud-* PROIBIDO. QA Gate 2 jobs OK.
  · 0 segredos hardcoded. 0 dependência assinatura humana. 0 alteração código de negócio.

IMPLEMENTAÇÃO (N arquivos, X insertions / Y deletions):
  · caminho/arquivo-X: descrição objetiva da mudança.
  · caminho/arquivo-Y: descrição objetiva da mudança.
  · ...

VALIDAÇÃO (8/8 gates padrão FAIL-CLOSED PASS):
  · G1 gov-m5-verify:           ✅
  · G2 gov-m5-unit-test:        2/2 cenários PASS. ✅
  · G3 shell-syntax:            21/21 PASS. ✅
  · G4 healthz-bypass-test:     18/18 asserts PASS. ✅
  · G5 all-checks -n:           dry-run parse OK. ✅
  · G6 typecheck -n:            dry-run parse OK. ✅
  · G7 qa-gateway-all-strict-ci -n: dry-run parse OK. ✅
  · G8 settings-dry-run:        13 contexts / 0 sonarcloud-* / 2 QA jobs OK. ✅
  · Adicionais (opcional): XXX

Backlog P2 proximo sprint menor esforço: S28+XX+1 (descrição breve INV pendente)
Working Tree: LIMPA (N arquivos commitados).
```

---

## 6. Checklist Rápido ANTES de `git commit`

- [ ] `make ci-local` PASSOU (8/8 gates FAIL-CLOSED).
- [ ] Working Tree: `git status --short` → **SOMENTE arquivos do sprint atual staged**.
- [ ] NENHUM `tmp_qa/`, `tmp_audit/`, `.env.bak`, `docker-compose.override.yml` staged (verificar .gitignore).
- [ ] `ontrackchain/pyproject.toml` L185+ linha roadmap sprint adicionada + Docs chain atualizada.
- [ ] `README.md` seção relevante atualizada com bullets e tags `[S28+XX]`.
- [ ] Hard constraints HC-1..HC-4 mentalmente verificadas.

**Se QUALQUER item for NÃO → NÃO commite. Resolva primeiro.**

---

*Governança contínua. Qualidade não é opcional. FAIL-CLOSED sempre.*
