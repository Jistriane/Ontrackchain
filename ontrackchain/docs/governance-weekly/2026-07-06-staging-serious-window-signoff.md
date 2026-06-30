# Sign-Off da Janela Seria — `stg-2026-07-06-a`

## Identificacao

- workflow: `Staging Serious Window`
- run name: `Serious staging window / stg-2026-07-06-a / baseline / staging-serious`
- run url: `pending`
- window_id: `stg-2026-07-06-a`
- mode: `baseline`
- environment_name: `staging-serious`
- artifact: `serious-staging-window-stg-2026-07-06-a`

## Status Consolidado

- overall status: `pending`
- validation status: `pending`
- preflight status: `pending`
- run status: `pending`

## Artefatos Revisados

- checks: `pending`
- dossier: `pending`
- window packet: `pending`
- homologation: `pending`
- payload JSON: `pending`

## Gates Revisados

- auth/OIDC: `pending`
- MFA/2FA: `pending`
- compliance: `pending`
- investigation/RPC: `pending`
- reports e evidencias: `pending`
- CI/CD: `pending`
- restore/retention: `pending`

## Excecoes ou Bloqueios

- bloqueios externos: `none_declared`
- excecoes aceitas: `none_declared`
- risco residual: `pending_execucao_real`

## Aprovadores

- arquitetura/tech lead: `pending`
- backend/auth: `pending`
- platform/SRE: `pending`
- compliance/security: `pending_if_applicable`

## Decisao Final

- decisao: `pending`
- proximo passo: executar o workflow e substituir todos os campos `pending` por links, paths e status reais
- owner do proximo passo: `Release Manager Tecnico`

## Regras de Atualizacao

- substituir `run url` pelo link real do GitHub Actions
- manter o nome do artifact exatamente como publicado
- mudar a decisao para `approved` somente se `overall`, `validation`, `preflight` e `run` forem `ok`
- se houver falha, registrar explicitamente se o bloqueio ocorreu em `validation`, `preflight` ou `run`
