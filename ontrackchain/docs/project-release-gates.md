# Gates de Release para Staging Serio

## Objetivo

Definir criterios minimos de promocao para staging serio com base no estado real do runtime regulatorio atual, sem exigir perfeicao inexistente nem aceitar falsa percepcao de prontidao.

## Escopo Canonico

Use este documento para responder:

- a janela pode ou nao pode ser promovida?
- quais gates sao obrigatorios, condicionais ou bloqueadores inaceitaveis?
- qual e a leitura executiva de `go/no-go` dada a baseline oficial?

Nao use este documento como runbook de execucao:

- deploy tecnico e comandos completos: [Deploy e Staging](deploy-and-staging.md)
- Refira-se a [Governanca Semanal](governance-weekly/) para tracking do ciclo atual

## Meta de Promocao

Uma promocao para staging serio so deve acontecer quando:

- os fluxos core estiverem validados ponta a ponta
- os controles minimos de identidade, autorizacao e auditoria estiverem ativos
- os modulos regulatorios implementados estiverem coerentes com o ambiente-alvo
- os gaps remanescentes estiverem explicitamente aceitos e documentados

Baseline canônica de referencia:

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada
- [Governança Semanal 2026-07-01](governance-weekly/2026-07-01-weekly-governance.md)
- [Atualização de KPI 2026-07-01](governance-weekly/2026-07-01-kpi-scorecard-update.md)

## Gates Obrigatorios

### 1. Auth e Identidade

- `AUTH_MODE=oidc` no ambiente serio
- `DEV_AUTH_ENABLED=false`
- `preflight_oidc_serious_env.py` verde
- `smoke_auth_oidc_mode.py` verde
- trilho `playwright` critico de OIDC verde
- enquanto `P0-01` permanecer `blocked`, nao promover janela regulatoria forte sem excecao explicitamente registrada

### 2. MFA em Fluxos Sensiveis

- `legal_report` validado com trilho serio homologado quando a janela exigir esse fluxo
- `ROS/COAF` e `block lift` protegidos por `external_provider`
- ausencia de fallback silencioso para `dev`

### 3. Core Regulatorio

O gate minimo agora exige que estes modulos estejam operacionais:

- `sanctions-check` direto via cache local
- `preventive_blocks`
- `counterparties`
- `ROS/COAF`

Observacoes de aceite:

- `due_diligence` e `source_of_funds` podem permanecer em `manual_review_required` se isso estiver explicitamente aceito para a janela

### 4. Providers Externos

- `preflight_external_integrations.py` verde para o modo esperado da janela
- se a janela exigir `AML/KYT live`, `make check-compliance-provider-runtime` deve ficar verde e produzir evidencia anexavel do runtime
- se a janela exigir feed da UE, `make run-eu-sanctions-window-local` ou fluxo equivalente deve persistir os JSONs em `artifacts/staging/checks/`
- para janelas com `P0-02` e `P0-03` juntos, preferir `make run-regulatory-readiness-bundle`, que consolida os artefatos de runtime AML/KYT e da janela UE em um bundle unico anexavel
- no rito consolidado via `run_staging_window.py`, esse bundle passa a ser executado automaticamente quando a janela estiver com `AML/KYT live` e/ou `EU_CONSOLIDATED` no escopo
- `check_sanctions_sync_status.py` verde apos rebuild/reexecucao do worker quando a janela envolver feeds de sancoes fora do runner dedicado
- se a janela exigir feed da UE, `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` deve estar preenchida, tokenizada e coerente com `sanctions_lists_meta.source_url`
- durante o war room da janela, usar a [Matriz de Execucao por Owner para Janela Seria](staging-serious-window-war-room-matrix.md) para coordenar trilhas, escalacoes e criterio de `no-go`

Leitura operacional atual:

- `P0-02` esta `ready`, mas nao pode ser promovido sem gate real do provider
- `P0-03` esta `ready`, mas nao pode ser promovido sem URL tokenizada valida e JSONs anexados

### 5. Reports e Evidencias

- `report_generated` e `report_downloaded` continuam auditados
- `coaf_report_generated`, `approved/rejected` e `submitted_manual` deixam trilha coerente
- `evidence_trail` recebe eventos regulatorios principais do fluxo da janela
- dossier final consolidado e anexado

### 6. Observabilidade

- `Prometheus`, `Alertmanager` e `Grafana` saudaveis
- incidente sintetico chega ao backlog global
- export administrativo continua auditado

### 7. Pipeline e Evidencia

- `smoke_runtime.py` verde
- `Playwright` relevante verde
- preflights e checks da janela verdes
- `run_staging_window.py` ou workflow oficial gera artefato consolidado
- quando houver janela `AML/KYT live`, o bundle da homologacao e o resultado de `make check-compliance-provider-runtime` ficam anexados
- quando houver janela UE, os arquivos `<janela>-eu-sanctions-preflight.json` e `<janela>-eu-sanctions-sync.json` ficam anexados
- quando `P0-02` e `P0-03` forem exercitados em conjunto, anexar tambem `<janela>-regulatory-readiness-bundle.json`

### 8. Dados, Retention e Restore

- backup disponivel antes de mudanca estrutural relevante
- ultimo restore evidenciado conhecido e anexavel
- sign-off de retention/recovery registrado ou excecao aprovada

## Gates Condicionais

Podem permanecer abertos apenas com risco registrado, owner e prazo:

- ausencia de `AML/KYT live` quando a janela for apenas tecnica ou voltada ao feed de sancoes
- ausencia da janela UE dedicada quando a janela nao envolver `EU_CONSOLIDATED` como criterio de aceite
- `P0-01` bloqueado quando a janela nao exigir trilho regulatorio forte de identidade e houver excecao formal aprovada

## Bloqueadores Nao Aceitaveis

- `AUTH_MODE=dev` como caminho principal em ambiente serio
- `legal_report`, `ROS/COAF` ou `block lift` sem enforcement serio de MFA
- screening de sancoes sem cache local consistente e sem checker pos-sync
- janelas de sancoes com feed UE exigido e sem URL tokenizada valida
- promocao sem dossier, sem ownership/handoff ou sem evidencias anexaveis

## Checklist de Aprovacao

| Item | Obrigatorio | Status Base |
| --- | --- | --- |
| Auth serio sem fallback para dev | Sim | `pending` |
| MFA serio em fluxos sensiveis | Sim | `pending` |
| Screening local de sancoes operacional | Sim | `ready_with_validation` |
| Preventive blocks operacionais | Sim | `ready` |
| Counterparties operacionais | Sim | `ready` |
| ROS/COAF operacional | Sim | `ready` |
| Provider AML/KYT live quando exigido | Sim | `pending_with_runtime_gate` |
| Feed UE homologado quando exigido | Sim | `pending_with_window_runner` |
| Pipeline verde e dossier anexado | Sim | `pending` |
| Backup/restore e retention aceitos | Sim | `pending` |

## Decisao Recomendada

A promocao para staging serio deve olhar menos para "existe feature?" e mais para "o modulo esta operando com prova auditavel no ambiente-alvo?".

No estado atual, os gates mais provaveis de continuar bloqueando uma janela regulatoria forte sao:

- `AML/KYT live`
- homologacao formal de MFA federado
- URL tokenizada real da UE
- sign-off institucional de retention/recovery

Regra executiva:

- manter esta leitura alinhada a baseline `91% / 78% / 87%` ate nova evidencia material publicada na governanca semanal
