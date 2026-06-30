# Template de Sign-Off da Janela Seria

## Objetivo

Padronizar o sign-off da janela seria executada pelo workflow `Staging Serious Window`, garantindo que o artifact e os status criticos sejam registrados de forma consistente.

Este documento complementa:

- [Runbook do Primeiro Disparo Real](first-serious-window-first-dispatch-runbook.md)
- [GitHub Environment para Staging Serio](github-environment-staging-serious.md)
- [Gates de Release para Staging Sério](project-release-gates.md)

## Quando Usar

Usar este template:

- ao final de cada janela seria via GitHub Actions
- antes de marcar `RUN-STG-01` como `done`
- quando o artifact `serious-staging-window-<janela>` precisar ser anexado ou referenciado formalmente

O workflow manual tambem gera um draft em:

- `ci-artifacts/staging-serious-window-signoff.md`

Comando local recomendado para pos-processar o artifact inteiro:

```bash
make postprocess-serious-window-dry-run \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

O comando acima:

- atualiza `ci-artifacts/staging-serious-window-signoff.md`
- gera a copia versionada em `docs/governance-weekly/`
- sincroniza o registro semanal da mesma janela

Se precisar executar os passos separadamente:

```bash
python scripts/render_staging_window_signoff.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --output-file ci-artifacts/staging-serious-window-signoff.md \
  --governance-weekly-dir docs/governance-weekly
```

Para sincronizar o registro semanal a partir do mesmo payload:

```bash
python scripts/render_staging_window_weekly_governance.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

## Template

```md
# Sign-Off da Janela Seria — <window_id>

## Identificacao

- workflow: `Staging Serious Window`
- run name:
- run url:
- window_id:
- mode:
- environment_name:
- artifact:

## Status Consolidado

- overall status:
- validation status:
- preflight status:
- run status:

## Artefatos Revisados

- checks:
- dossier:
- window packet:
- homologation:
- payload JSON:

## Gates Revisados

- auth/OIDC:
- MFA/2FA:
- compliance:
- investigation/RPC:
- reports e evidencias:
- CI/CD:
- restore/retention:

## Excecoes ou Bloqueios

- bloqueios externos:
- excecoes aceitas:
- risco residual:

## Aprovadores

- arquitetura/tech lead:
- backend/auth:
- platform/SRE:
- compliance/security:

## Decisao Final

- decisao: `approved` | `approved_with_exception` | `blocked`
- proximo passo:
- owner do proximo passo:
```

## Regra de Preenchimento

- nao marcar `approved` com qualquer status `failed`
- referenciar o artifact exatamente pelo nome publicado no GitHub Actions
- preencher `run url` sempre que a execucao vier do workflow manual
- descrever excecoes somente quando houver owner, prazo e mitigacao
- tratar `pending_manual_approval` como estado intermediario gerado automaticamente antes da aprovacao humana

## Criterio Minimo de Aprovacao

- `overall status=ok`
- `validation.status=ok`
- `preflight.status=ok`
- `run.status=ok`
- artifact `serious-staging-window-<janela>` preservado

## Suposicoes

- o artifact do GitHub Actions sera a evidencia oficial da janela seria
- o time fara o sign-off em markdown versionado ou anexado ao rito semanal
