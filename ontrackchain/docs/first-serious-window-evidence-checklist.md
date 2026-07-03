# Checklist de Evidência Mínima da Primeira Janela Séria

## Objetivo

Definir o pacote mínimo de evidências para considerar a primeira janela séria de staging auditável, revisável e apta a sign-off.

Use este checklist junto com:

- `python scripts/run_staging_window.py`
- [Deploy e Staging](deploy-and-staging.md)
- [Gates de Release para Staging Serio](project-release-gates.md)
- [Ownership do `.env.staging`](staging-env-ownership.md)

## Pré-condições

- [ ] `docs/staging-env-ownership.md` está sem owners obrigatórios pendentes para o escopo da janela
- [ ] `.env.staging.private` está sem placeholders críticos do escopo
- [ ] `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline --validate --preflight` retorna `status=ok`
- [ ] war room da janela está em `go` ou `go_with_exception`

## Evidências Obrigatórias do Pacote

- [ ] `artifacts/staging/window-packet-<janela>.md`
- [ ] `artifacts/staging/checks/ownership-coverage-<janela>.json`
- [ ] `artifacts/staging/checks/placeholders-<janela>.json`
- [ ] `artifacts/staging/checks/handoff-<janela>.json`
- [ ] `artifacts/staging/checks/oidc-preflight-<janela>.json`
- [ ] `artifacts/staging/checks/external-preflight-<janela>.json`
- [ ] artefato de homologação externa em `artifacts/homologation/`
- [ ] dossier final `.json` em `artifacts/staging/dossiers/`
- [ ] manifesto `.manifest.json` do dossier com `sha256`

## Evidências Obrigatórias para `P0-01`

- [ ] `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json`
- [ ] `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md`
- [ ] bundle OIDC com `oidc_preflight` e `smoke_auth_oidc_mode` revisáveis no mesmo pacote
- [ ] quando aplicável, evidência externa homologada para MFA/`external_provider`

## Evidências Obrigatórias para `P0-02`

- [ ] `make check-compliance-provider-runtime` verde com evidência anexada
- [ ] `GET /internal/provider-readiness` coerente com `ready=true`
- [ ] homologação AML/KYT com `status=ok`

## Evidências Obrigatórias para `P0-03`

- [ ] `artifacts/staging/checks/<janela>-eu-sanctions-preflight.json`
- [ ] `artifacts/staging/checks/<janela>-eu-sanctions-sync.json`
- [ ] `EU_CONSOLIDATED` com `ACTIVE/SUCCESS` e `source_url` coerente

## Evidências Obrigatórias para `P0-02` + `P0-03`

- [ ] `artifacts/staging/checks/<janela>-regulatory-readiness-bundle.json`
- [ ] `artifacts/staging/dossiers/<janela>-regulatory-readiness-bundle.md`

## Critério de Aprovação

- [ ] sign-off contém links/paths do artifact do workflow, dossier, homologação e bundles aplicáveis
- [ ] não há bloqueador `WR-*` aberto sem waiver formal
- [ ] status consolidado da janela está `ok`

## No-Go Imediato

- [ ] fallback silencioso para `dev auth`
- [ ] ausência de dossier final
- [ ] ausência do bundle OIDC quando `P0-01` estiver no escopo
- [ ] ausência do bundle regulatório quando `P0-02/P0-03` estiverem no escopo
- [ ] homologação externa ausente para o modo exercitado