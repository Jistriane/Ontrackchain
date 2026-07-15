# Tracker Semanal de Owners para 95%

**Data base:** 2026-07-03

> Aviso de classificacao: este tracker e datado e deve ser lido como apoio historico de ciclo. Para a trilha viva de owners, prioridades e evidencias, use primeiro o [Board Operacional Unico](../project-operational-execution-board.md), o [Plano Consolidado ate 95%](../project-construction-plan-to-95-percent.md) e os registros ativos em [governance-weekly/README.md](../governance-weekly/README.md).

## Objetivo

Oferecer uma planilha operacional simples para acompanhamento semanal dos owners responsáveis pela trilha de subida de `87%` para `95%`.

Use este documento junto com:

- [Plano Consolidado ate 95%](../project-construction-plan-to-95-percent.md)
- [Board Operacional Unico ate 90%+](../project-operational-execution-board.md)
- [Governança Semanal 2026-07-03](../governance-weekly/archive/weekly/2026-07-03-weekly-governance.md)

## Instrução de Uso

- atualizar no início de cada ciclo semanal
- não marcar `verde` sem evidência revisada
- usar `bloqueado` quando faltar insumo externo real
- registrar sempre a próxima ação verificável

## Legenda

| Status | Significado |
| --- | --- |
| `verde` | item com evidência suficiente para avançar ou fechar |
| `amarelo` | item em andamento com dependência interna controlada |
| `vermelho` | item bloqueado por dependência crítica |
| `cinza` | item ainda não iniciado no ciclo |

## Tracker da Semana

| Bloco | Owner primario | Apoio/Escalação | Status | Evidência atual | Próxima ação | Prazo alvo |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | `Compliance/Backend` | `Security` | `vermelho` | nenhuma credencial real homologada anexada | cobrar provider e executar checker ao receber credenciais | próxima janela útil |
| `P0-03` feed UE real | `Compliance/Backend` | `Security` | `vermelho` | nenhuma URL real anexada | obter URL tokenizada e rodar janela UE local | próxima janela útil |
| `P0-01` `OIDC + MFA` | `Backend/Auth` | `Security` | `vermelho` | trilho local existe, sem homologação real | obter credenciais do provider e rodar preflight/smoke/E2E | próxima janela útil |
| Owners e SLA | `Platform/SRE` | `Security` | `amarelo` | documento publicado em `ready_for_approval` | obter aceites formais pendentes | sprint corrente |
| Retention e recovery | `Platform/DBA` | `Security` e `Compliance` | `amarelo` | política publicada e baseline pronta | executar restore evidenciado e coletar aceites | sprint corrente |
| Janela séria #1 | `Arquiteto/Responsavel Tecnico` | `Platform/SRE` | `cinza` | runbooks e templates prontos | confirmar war room e executar com artefato | janela planejada |
| Janela séria #2 | `Arquiteto/Responsavel Tecnico` | `Platform/SRE` | `cinza` | depende da primeira janela | agendar segunda execução comparável | após janela #1 |

## Snapshot Semanal

| Semana | Técnico | Regulatório | Consolidado | Observação |
| --- | ---: | ---: | ---: | --- |
| 2026-07-03 | 91% | 78% | 87% | baseline confirmada e documentada |

## Quadro Diário Sugerido

| Data | `P0-02` `AML/KYT live` | `P0-03` feed UE | `P0-01` `OIDC + MFA` | Owners/SLA | Retention/Recovery | Janela séria |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07-03 | bundle local executado, sem credencial real | preflight local executado, sem URL real tokenizada | bundle local executado, sem homologacao real | handoff com 8 campos pendentes (`date/status`) | sem nova evidência executada | rerun `21:40Z`: `prepare` `failed` + `run` `failed`; `placeholder_check`/`handoff_check` mantidos |
| 2026-07-04 | cobrar credencial + executar checker runtime | cobrar URL + executar janela UE local | cobrar provider + executar preflight/smoke | preencher `date/status` por dominio no handoff | definir janela de teste restore | rerodar `run_staging_window.py` apos gates locais verdes |
| 2026-07-05 | atualizar | atualizar | atualizar | atualizar | atualizar | atualizar |
| 2026-07-06 | atualizar | atualizar | atualizar | atualizar | atualizar | atualizar |

## Plano de Fechamento por Dominio (War Room)

### Auth/OIDC (`Backend/Auth` + `Security`)

- pendência atual: `P0-01` bloqueado por homologacao real
- ações:
  - preencher secrets/claims OIDC no `.env.staging.private`
  - executar `python scripts/preflight_oidc_serious_env.py`
  - executar `python scripts/smoke_auth_oidc_mode.py`
- evidência mínima de avanço:
  - `stg-2026-07-06-a-oidc-preflight.json` com `status=ok`
  - `stg-2026-07-06-a-oidc-smoke-auth.json` com `status=ok`

### Compliance/AML (`Compliance/Backend` + `Security`)

- pendência atual: `P0-02` sem credencial real
- ações:
  - preencher `COMPLIANCE_TRM_API_KEY` e `COMPLIANCE_TRM_SCREENING_URL`
  - executar `make check-compliance-provider-runtime`
- evidência mínima de avanço:
  - `stg-2026-07-06-a-compliance-provider-runtime.json` com `status=ok`

### Investigation/RPC (`Backend Core` + `Platform/DBA`)

- pendência atual: URLs RPC ainda em placeholder
- ações:
  - preencher `INVESTIGATION_RPC_PRIMARY_URL` e `INVESTIGATION_RPC_FALLBACK_URL`
  - executar `python scripts/preflight_external_integrations.py`
- evidência mínima de avanço:
  - `stg-2026-07-06-a-external_preflight.json` com `status=ok`

### Platform/Operations (`Platform/SRE` + `Platform/DBA`)

- pendência atual: placeholders transversais e handoff pendente
- ações:
  - preencher `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD`, `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
  - atualizar `docs/staging-env-ownership.md` em `Registro de Handoff` com `date/status`
  - executar `python scripts/check_staging_env_handoff.py --file docs/staging-env-ownership.md`
- evidência mínima de avanço:
  - `handoff-stg-2026-07-06-a.json` com `status=ok`
  - `placeholders-stg-2026-07-06-a.json` com `status=ok`

## Regra de Atualização Diária

- substituir `atualizar` apenas quando houver fato novo verificável
- registrar bloqueio explicitamente quando o owner não receber insumo externo
- não trocar `bloqueado` por `em andamento` sem credencial, URL, teste ou artefato real

## Regras de Escalação

- se `P0-01`, `P0-02` ou `P0-03` ficarem sem resposta externa por mais de 2 dias úteis, escalar
- se houver evidência parcial, mover o status para `amarelo`, nunca para `verde`
- se uma janela séria não gerar artefato anexável, manter o item fora de `done`
