# Primeiro Disparo Real da Janela Seria

## Objetivo

Fornecer um roteiro unico para a primeira execucao real do workflow manual `Staging Serious Window`, reduzindo improviso em:

- definicao dos inputs
- confirmacao de approvals
- verificacao de precondicoes
- registro da evidencia final

Este documento complementa:

- [GitHub Environment para Staging Serio](github-environment-staging-serious.md)
- [Checklist de Evidência Mínima da Primeira Janela Séria](first-serious-window-evidence-checklist.md)
- [Gates de Release para Staging Sério](project-release-gates.md)
- [Template de Sign-Off da Janela Seria](staging-serious-window-signoff-template.md)

## Quando Usar

Use este runbook quando:

- a janela seria for disparada pela primeira vez via GitHub Actions
- o owner operacional precisar de um roteiro unico de go/no-go
- a governanca semanal exigir um pacote minimo de evidencia anexavel

## Inputs Recomendados

Primeira janela sugerida:

- `window_id`: `stg-2026-07-06-a`
- `mode`: `baseline`
- `environment_name`: `staging-serious`

Usar `mode=homologated` apenas quando:

- `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`
- os providers externos esperados estiverem homologados
- o sign-off regulatorio exigir a trilha homologada

## Checklist de Precondicoes

Antes de clicar em `Run workflow`, confirmar:

- [ ] o environment `staging-serious` existe no GitHub
- [ ] o environment tem reviewers coerentes para a janela
- [ ] o secret `STAGING_WINDOW_PRIVATE_ENV` foi cadastrado no environment correto
- [ ] o secret nao contem placeholders `__FILL_*__`
- [ ] o `.env.staging.private` equivalente passou em `prepare_staging_window.py --validate`
- [ ] o `window_id` da semana esta reservado no rito operacional
- [ ] o owner de release e o owner de escalacao externa estao nomeados

Comando recomendado para validar essa prontidao antes de abrir o GitHub Actions:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
```

Se precisar separar explicitamente as etapas, usar:

```bash
make preflight-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
make render-serious-window-dispatch-packet \
  WINDOW_ID="stg-2026-07-06-a"
```

## Preflight Humano de Aprovação

Perguntas objetivas antes do disparo:

1. O objetivo da janela e apenas baseline tecnica ou envolve homologacao regulatoria?
2. Existe algum provider externo em manutencao, throttling ou janela de risco?
3. O environment selecionado corresponde ao secret correto da janela?
4. O artifact final sera anexado ao sign-off ainda nesta semana?

Se qualquer resposta for "nao sei", tratar como `no-go` temporario.

## Sequencia de Execucao

1. abrir `Actions` no repositório
2. selecionar `Staging Serious Window`
3. clicar em `Run workflow`
4. preencher:
   - `window_id`
   - `mode`
   - `environment_name`
5. aguardar approvals do `GitHub Environment`
6. acompanhar o `GITHUB_STEP_SUMMARY`
7. baixar ou referenciar o artifact `serious-staging-window-<janela>`

## Resultado Esperado e Artefatos Minimos

Ao final do run oficial, o artifact `serious-staging-window-<janela>` deve conter no minimo:

- `status=ok` no payload consolidado
- `validation.status=ok`
- `preflight.status=ok`
- `run.status=ok`
- `ci-artifacts/prepare-staging-window-output.json`
- `ci-artifacts/staging-serious-window-signoff.md`
- `artifacts/staging/checks/`
- `artifacts/staging/dossiers/`
- `artifacts/staging/templates/`
- `artifacts/staging/window-packet-<janela>.md`
- `artifacts/homologation/`

## No-Go e Escalacao

Tratar como `no-go` quando:

- o workflow falhar antes de materializar `.env.staging.private`
- o payload nao for JSON valido
- `validation`, `preflight` ou `run` retornarem `failed`
- o artifact nao for publicado

Escalacao recomendada:

- Auth/OIDC: falhas de `validation` ligadas a identidade, claims ou MFA
- Compliance: falhas de provider AML/KYT ou readiness regulatorio
- Platform/DevOps: secret ausente, approvals incorretos ou artifact ausente
- Investigation/RPC: falhas de primario/fallback ou indisponibilidade de endpoint

## Registro na Governanca Semanal

Em `## Contexto da Janela Séria`, registrar:

- `window_id`
- `mode`
- `environment_name`
- status esperado da transicao

Em `## Evidências Revisadas`, registrar:

- link ou referencia ao run do GitHub Actions
- artifact `serious-staging-window-<janela>`
- status geral e status de `validation`, `preflight` e `run`
- paths relevantes do `window packet`, `checks`, `homologation` e `dossier`
- caminho do draft `ci-artifacts/staging-serious-window-signoff.md`

Comando unico recomendado para pos-processar o artifact baixado:

```bash
make postprocess-serious-window-dry-run \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

O comando acima cria ou atualiza automaticamente:

- `ci-artifacts/staging-serious-window-signoff.md`
- `docs/governance-weekly/<data-da-janela>-staging-serious-window-signoff.md`
- `docs/governance-weekly/<data-da-janela>-weekly-governance.md`

No registro semanal, o comando sincroniza automaticamente:

- `run do GitHub Actions`
- artifact da janela
- `overall status`, `validation`, `preflight` e `run`
- `window packet`, `dossier` e `homologation`
- status do item `RUN-STG-01`

Se precisar rodar os passos individualmente, manter como fallback:

```bash
python scripts/render_staging_window_signoff.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --output-file ci-artifacts/staging-serious-window-signoff.md \
  --governance-weekly-dir docs/governance-weekly

python scripts/render_staging_window_weekly_governance.py \
  --payload-file ci-artifacts/prepare-staging-window-output.json \
  --governance-weekly-dir docs/governance-weekly \
  --run-url "https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

## Modelo Copy/Paste para o Sign-Off

```md
## Janela Seria

- workflow: `Staging Serious Window`
- window_id: `stg-2026-07-06-a`
- mode: `baseline`
- environment_name: `staging-serious`
- artifact: `serious-staging-window-stg-2026-07-06-a`
- overall status:
- validation status:
- preflight status:
- run status:
- owners presentes:
- bloqueios externos:
```

## Decisao Recomendada

- usar este runbook para a primeira execucao real e para qualquer troca de owner operacional
- reutilizar o draft gerado em `ci-artifacts/staging-serious-window-signoff.md` como base do fechamento formal
- materializar a copia versionada em `docs/governance-weekly/` antes de fechar o rito semanal
- sincronizar o registro semanal a partir do mesmo payload antes do sign-off final
- preencher o sign-off usando [Template de Sign-Off da Janela Seria](staging-serious-window-signoff-template.md)
- promover para o pacote canonico somente apos uma primeira execucao bem-sucedida com artifact anexado

## Suposicoes

- a primeira janela real sera `baseline`, nao `homologated`
- o environment inicial sera `staging-serious`
- o sign-off semanal aceita referencia ao artifact do GitHub Actions como evidencia oficial
