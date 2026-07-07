# Matriz de Execucao por Owner para Janela Seria

## Objetivo

Dar ao war room da janela seria uma visao unica de:

- owner responsavel por cada trilha
- dependencia previa para iniciar a execucao
- comando minimo de validacao
- evidencia minima exigida
- criterio de escalacao quando a trilha falhar

Use esta matriz junto com:

- [Ownership do `.env.staging`](staging-env-ownership.md)
- [Owners e SLAs Operacionais](operational-ownership-and-slas.md)
- [Gates de Release para Staging Serio](project-release-gates.md)

## Quando Usar

Usar este documento quando houver:

- janela seria planejada para a semana
- rerun de `prepare_staging_window.py --validate --preflight`
- necessidade de coordenacao rapida entre owners
- bloqueio externo que exija escalacao imediata

## Matriz de Execucao

| Trilha | Owner primario | Backup/Escalacao | Dependencia de entrada | Comando minimo | Evidencia minima | No-go imediato |
| --- | --- | --- | --- | --- | --- | --- |
| `Platform/Operations` | `Platform/SRE` | `Platform/DBA` | handoff iniciado e acesso ao vault/secret store | `python3 scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md` e `python3 scripts/check_staging_env_placeholders.py --file .env.staging.private` | JSONs de handoff/placeholders sem `pending` ou placeholder critico do dominio | senha de DB, Grafana ou webhook ainda em placeholder |
| `Auth/OIDC` | `Backend/Auth` | `Security` | `Platform/Operations` concluido e secrets OIDC nao-dev provisionados | `python3 scripts/preflight_oidc_serious_env.py` e `make run-oidc-readiness-bundle-local WINDOW_ID=<janela> BASE_URL=http://localhost:8080` | output verde do preflight OIDC, bundle `<janela>-oidc-readiness-bundle.json` e handoff de `Auth/OIDC` atualizado | fallback para `dev`, claims incoerentes, bundle OIDC ausente ou MFA serio ainda nao verificavel |
| `Investigation/RPC` | `Backend Core` | `Platform/SRE` | endpoints primario/fallback definidos e roteaveis | `python3 scripts/preflight_external_integrations.py` | output coerente com `ONTRACKCHAIN_EXPECT_RPC_MODE` e handoff de `Investigation/RPC` atualizado | RPC primario/fallback indisponivel ou placeholder ainda aberto |
| `Compliance/AML` | `Compliance/Backend` | `Security` | credenciais reais do provider, URL tokenizada da UE quando aplicavel, handoff pronto | `python3 scripts/preflight_external_integrations.py` e `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080` | runtime AML/KYT verde e, quando houver UE, JSONs `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` | provider real indisponivel, `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` placeholder ou bundle regulatorio falhando |
| `Gate Agregado da Janela` | `Arquiteto/Responsavel Tecnico` | `Platform/SRE` | todas as trilhas acima em estado verde ou waived formalmente | `python3 scripts/prepare_staging_window.py --window-id stg-YYYY-MM-DD-a --mode baseline --private-env-file .env.staging.private --validate --preflight` | resultado `status=ok` e pacote pronto para `make run-serious-window-local` | qualquer trilha anterior em `pending`, `failed` ou sem evidencia anexavel |

## Sequencia de War Room

1. confirmar `owner primario` e `backup/escalacao` por trilha
2. validar `Platform/Operations`
3. validar `Auth/OIDC`
4. validar `Investigation/RPC`
5. validar `Compliance/AML`
6. rerodar o gate agregado da janela
7. se verde, autorizar `make run-serious-window-local`

## Escalacao Recomendada

| Caso | Escalar para | Tempo alvo |
| --- | --- | ---: |
| placeholder critico ainda aberto | owner do dominio + `Platform/SRE` | `30 min` |
| preflight OIDC falhando | `Backend/Auth` + `Security` | `30 min` |
| provider AML/KYT ou UE indisponivel | `Compliance/Backend` + owner externo do provider | `60 min` |
| falha de RPC ou conectividade | `Backend Core` + `Platform/SRE` | `30 min` |
| gate agregado da janela falhando | `Arquiteto/Responsavel Tecnico` + owner da trilha vermelha | `15 min` |

## Definition of Ready para Execucao

A janela so entra em execucao quando:

- a matriz acima estiver toda em verde ou com waiver formal explicito
- `docs/staging-env-ownership.md` nao tiver mais linhas obrigatorias em `pending`
- `.env.staging.private` nao tiver placeholders criticos do escopo
- `prepare_staging_window.py --validate --preflight` retornar `status=ok`

## Artefatos de Saida Esperados

- `artifacts/staging/checks/<janela>-handoff.json`
- `artifacts/staging/checks/<janela>-placeholders.json`
- `artifacts/staging/checks/<janela>-oidc-readiness-bundle.json` quando `P0-01` estiver no escopo
- `artifacts/staging/dossiers/<janela>-oidc-readiness-bundle.md` quando `P0-01` estiver no escopo
- `artifacts/staging/checks/<janela>-compliance-provider-runtime.json` quando `AML/KYT live` estiver no escopo
- `artifacts/staging/checks/<janela>-eu-sanctions-preflight.json` quando a UE estiver no escopo
- `artifacts/staging/checks/<janela>-eu-sanctions-sync.json` quando a UE estiver no escopo
- `artifacts/staging/checks/<janela>-regulatory-readiness-bundle.json` quando `P0-02` e `P0-03` forem exercitados em conjunto
- `artifacts/staging/dossiers/<janela>-regulatory-readiness-bundle.md` quando `P0-02` e `P0-03` forem exercitados em conjunto
- `ci-artifacts/prepare-staging-window-output.json`
- `ci-artifacts/staging-serious-window-signoff.md`
