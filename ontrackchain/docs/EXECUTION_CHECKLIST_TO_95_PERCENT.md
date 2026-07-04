# Checklist Operacional para 95%

**Data base:** 2026-07-03

## Objetivo

Transformar a trilha de subida de `87%` para `95%` em um checklist operacional simples, verificavel e executavel por owner.

Este documento deve ser usado em conjunto com:

- [Avaliacao Consolidada de Status do Projeto](./PROJECT_STATUS_ASSESSMENT_2026_07_03.md)
- [Plano Tático Sprint 7-9: Escalação Controlada para 95%](./TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md)
- [Board Operacional Unico ate 90%+](./project-operational-execution-board.md)
- [Owners e SLAs Operacionais](./operational-ownership-and-slas.md)

## Regra de Uso

- nenhum item deve ser marcado como concluido sem artefato, checker verde, bundle, sign-off ou evidência equivalente
- itens com dependencia externa devem permanecer explicitamente bloqueados ate o insumo real existir
- a ordem recomendada de ataque continua sendo `P0-02 -> P0-03 -> P0-01 -> governanca -> janela seria recorrente`

## Checklist Executivo

| Bloco | Owner principal | Estado alvo | Evidência de fechamento |
| --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | `ready_for_validation` ou `done` | checker verde + JSON persistido |
| `P0-03` feed UE real | Regulatory/Ops | `ready_for_validation` ou `done` | preflight/sync JSON + validação |
| `P0-01` `OIDC + MFA` | Security/Auth Lead | `ready_for_validation` ou `done` | preflight + smoke + E2E |
| Owners e SLA | COO / Ops / Platform | `done` | aceite formal registrado |
| Retention e recovery | CTO / Security / Compliance | `done` | restore evidenciado + aceite |
| Janela seria recorrente | Ops Manager / Platform | `done` | dossier + sign-off de 2 execucoes |

## Checklist por Owner

### Compliance Lead

#### `P0-02` Homologar `AML/KYT live`

- [ ] solicitar credencial real do provider
- [ ] obter `api_key`, endpoint e requisitos de autenticacao
- [ ] preencher o segredo no ambiente privado correto
- [ ] executar `make check-compliance-provider-runtime`
- [ ] validar que o checker ficou verde
- [ ] persistir o artefato JSON do check
- [ ] registrar aceite operacional do provider como `ready`

Fechamento minimo:

- checker verde
- JSON persistido
- evidência revisada em governança semanal

#### `P1` Aceites regulatórios

- [ ] revisar o runbook do provider AML/KYT
- [ ] confirmar se a evidência coletada é suficiente para recorrência
- [ ] registrar aceite de compliance quando `P0-02` e janela real estiverem válidos

### Regulatory/Ops Manager

#### `P0-03` Ativar feed UE tokenizado real

- [ ] solicitar URL tokenizada real do feed UE
- [ ] validar reachability e formato de resposta
- [ ] preencher o segredo no ambiente privado correto
- [ ] executar `make run-eu-sanctions-window-local`
- [ ] validar `eu-sanctions-preflight.json`
- [ ] validar `eu-sanctions-sync.json`
- [ ] anexar os JSONs na trilha de governança

Fechamento minimo:

- URL real validada
- JSONs persistidos
- status do sync aceito em governança

#### Janela seria e war room

- [ ] agendar war room
- [ ] confirmar owners reais por dominio
- [ ] garantir coverage de placeholders e handoff
- [ ] preparar packet, dossier e sign-off da janela
- [ ] executar a primeira janela seria com artefato anexável
- [ ] organizar a segunda janela para provar recorrência

### Security/Auth Lead

#### `P0-01` Homologar `OIDC + MFA`

- [ ] definir provider oficial
- [ ] obter `client_id`, `client_secret`, issuer e claims necessários
- [ ] configurar o ambiente local/serio
- [ ] executar `python scripts/preflight_oidc_serious_env.py`
- [ ] executar `python scripts/smoke_auth_oidc_mode.py`
- [ ] executar `npm run test:e2e:oidc-critical`
- [ ] validar MFA federado sem fallback silencioso
- [ ] anexar bundle ou evidência equivalente

Fechamento minimo:

- preflight verde
- smoke verde
- E2E crítico verde
- evidência de autenticação forte homologada

#### `P1` Owners e segurança operacional

- [ ] revisar envolvimento obrigatório de Security em incidentes `P0/P1`
- [ ] aprovar formalmente owners e SLA sensíveis
- [ ] aprovar retention, descarte e cadeia de custódia quando os testes estiverem completos

### CTO / Platform / DBA

#### Retention e recovery

- [ ] validar política publicada
- [ ] confirmar owners técnicos de backup e restore
- [ ] executar restore controlado em base isolada
- [ ] medir `RTO`
- [ ] validar integridade mínima pós-restore
- [ ] registrar evidência do teste
- [ ] obter aceite formal de Platform/DBA

Fechamento minimo:

- restore executado
- `RTO` registrado
- evidência anexada
- aceite técnico formal

### COO / Governança

#### Owners e SLA

- [ ] validar owners por domínio
- [ ] validar backups operacionais
- [ ] aprovar SLA por severidade
- [ ] registrar aceite formal de ownership
- [ ] validar que o documento está referenciado nos gates de release

Fechamento minimo:

- owners aprovados
- SLA aprovado
- aceite formal registrado

### Tech Lead / QA

#### Validação cruzada da trilha P0

- [ ] consolidar `.env` privado apenas no ambiente correto
- [ ] executar bundle regulatório quando `P0-02` e `P0-03` estiverem prontos
- [ ] validar artefatos gerados
- [ ] registrar qualquer delta entre readiness documental e runtime
- [ ] manter a suíte principal de regressão verde

Fechamento minimo:

- bundle consistente
- evidências revisadas
- regressão verde

## Critérios para Dizer que o Projeto Chegou a 95%

- [ ] `AML/KYT live` validado com provider real
- [ ] feed UE real validado com artefatos persistidos
- [ ] `OIDC + MFA` homologados em trilho sério
- [ ] owners e SLA formalmente aceitos
- [ ] retention e recovery com evidência e aceite formal
- [ ] pelo menos 2 janelas sérias comparáveis executadas com dossier e sign-off

## Critérios para Não Promover Artificialmente

- [ ] não subir `P0-01`, `P0-02` ou `P0-03` sem artefato real
- [ ] não considerar aceite verbal como sign-off formal
- [ ] não confundir validação local com homologação externa
- [ ] não usar documentação forte para esconder ausência de prova operacional

## Uso Recomendado na Governança

- revisar este checklist em toda reunião semanal enquanto o projeto estiver abaixo de `95%`
- marcar apenas o que tiver evidência disponível no ciclo
- escalar imediatamente itens externos sem resposta em `P0`
- sincronizar qualquer conclusão com scorecard, board operacional e registro semanal
