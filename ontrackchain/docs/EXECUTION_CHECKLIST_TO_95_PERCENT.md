# Checklist Operacional para 95%

**Data base:** 2026-07-10

**Baseline oficial de referencia:** `92%` tecnico, `79%` regulatorio/operacional, `88%` consolidado

## Objetivo

Transformar a trilha de subida de `88%` para `95%` em um checklist operacional simples, verificavel e executavel por owner.

Este documento deve ser usado em conjunto com:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md)
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Plano Consolidado ate 95%](./project-construction-plan-to-95-percent.md)
- [Board Operacional Unico ate 90%+](./project-operational-execution-board.md)
- [Owners e SLAs Operacionais](./operational-ownership-and-slas.md)

## Regra de Uso

- nenhum item deve ser marcado como concluido sem artefato, checker verde, bundle, sign-off ou evidência equivalente
- itens com dependencia externa devem permanecer explicitamente bloqueados ate o insumo real existir
- a ordem recomendada de ataque continua sendo `P0-02 -> P0-03 -> P0-04 -> P0-01 -> P0-05 -> P0-06/P0-07 -> P1`
- este checklist nao redefine baseline por conta propria; ele operacionaliza a subida de `88%` para `95%` com base nos docs canônicos acima
- tentativa regulatoria parcial pode contar como endurecimento de trilha e preparo de janela, mas nao substitui o fechamento oficial combinado de `P0-04`
- RCA cross-domain, quando houver incidente material, conta como endurecimento operacional e melhora handoff/governanca, mas nao promove baseline sozinha sem recorrencia e revisao humana

## Checklist Executivo

| Bloco | Owner principal | Estado alvo | Evidência de fechamento |
| --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | Compliance Lead | `ready_for_validation` ou `done` | checker verde + JSON persistido |
| `P0-03` feed UE real | Regulatory/Ops | `ready_for_validation` ou `done` | preflight/sync JSON + validação |
| `P0-04` bundle regulatorio oficial | Platform/SRE | `ready_for_validation` ou `done` | bundle regulatorio coerente + validador final; tentativa parcial alimenta o dossier, mas nao encerra o item |
| `P0-01` `OIDC + MFA` | Security/Auth Lead | `ready_for_validation` ou `done` | preflight + smoke + E2E |
| `P0-05` primeira janela seria material | Release Manager / Platform | `ready_for_validation` ou `done` | packet + dossier + war room + sign-off |
| `P0-06` retention e recovery | CTO / Security / Compliance | `done` | restore evidenciado + aceite |
| `P1-02` owners, SLA e janela recorrente | COO / Ops / Platform | `done` | aceite formal + rito recorrente institucionalizado |
| `P2-03` RCA cross-domain leve | Platform/SRE + Monitoring | `in_progress` sustentado | `work_item_id` rastreado + RCA minima + comentario de timeline quando aplicavel + resumo RCA em export/comms/snapshot quando houver incidente material |

## Gates para Cruzar `90%+`

### Gate `88% -> 89%`

- [ ] existe pelo menos uma prova revisavel completa de `P0-02` ou `P0-03`
- [ ] o artefato esta persistido e referenciado na governanca semanal
- [ ] o risco correspondente foi reavaliado como menor ou explicitamente melhor delimitado

### Gate `89% -> 90%+`

- [ ] `P0-02` possui checker verde com credencial real e JSON persistido
- [ ] `P0-03` possui JSONs validos da janela UE e checker coerente
- [ ] `P0-04` consolida o bundle regulatorio oficial com `P0-02` e `P0-03` na mesma trilha revisavel; tentativa parcial isolada nao substitui esse gate
- [ ] `P0-05` transforma a prova combinada em pacote executivo revisavel
- [ ] a leitura executiva foi atualizada sem depender apenas de narrativa

### Gate de Sustentacao Institucional

- [ ] `P0-01` reduziu materialmente o risco de identidade com provider real e sem fallback silencioso
- [ ] `RUN-STG-01` deixou de ser somente preparacao e passou a ter trilha objetiva para `go/no-go`
- [ ] `P0-06` e `P1-02` possuem aceite ou excecao formal registrada
- [ ] quando houver incidente cross-domain material, a RCA minima foi registrada e a leitura executiva deixou claro se houve apenas endurecimento operacional ou artefato revisado

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
- [ ] quando houver incidente material no ciclo, confirmar `work_item_id`, RCA minima e resumo RCA coerente com war room/comms

### Security/Auth Lead

#### `P0-01` Homologar `OIDC + MFA`

- [ ] definir provider oficial
- [ ] obter `client_id`, `client_secret`, issuer e claims necessários
- [ ] configurar o ambiente local/serio
- [ ] executar `python scripts/preflight_oidc_serious_env.py`
- [ ] executar `python scripts/smoke_auth_oidc_mode.py`
- [ ] executar `npm run test:e2e:oidc-critical` com preflight explicito do ambiente OIDC serio
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
- [ ] se apenas uma trilha regulatória estiver disponível, registrar explicitamente o resultado como endurecimento parcial, sem promover `P0-04` artificialmente

Fechamento minimo:

- bundle consistente
- evidências revisadas
- regressão verde

#### `P2-03` Evidência complementar de RCA cross-domain

- [ ] confirmar se houve incidente cross-domain material na semana
- [ ] registrar `work_item_id` do alerta rastreado quando aplicavel
- [ ] validar que a RCA minima foi persistida no `work-item`
- [ ] validar que houve comentario automatico de timeline quando a RCA mudou materialmente
- [ ] validar se o resumo RCA entrou em export/comms/snapshot quando aplicavel
- [ ] registrar explicitamente se o resultado conta apenas como endurecimento operacional ou como artefato executivo revisado

Fechamento minimo:

- RCA minima registrada
- leitura executiva coerente com o artefato
- sem promocao artificial de baseline

## Critérios para Dizer que o Projeto Chegou a 95%

- [ ] `AML/KYT live` validado com provider real
- [ ] feed UE real validado com artefatos persistidos
- [ ] `OIDC + MFA` homologados em trilho sério
- [ ] owners e SLA formalmente aceitos
- [ ] retention e recovery com evidência e aceite formal
- [ ] pelo menos 2 janelas sérias comparáveis executadas com dossier e sign-off
- [ ] incidentes cross-domain materiais, quando existirem, possuem RCA revisavel sem serem usados como atalho para mover score

## Critérios para Não Promover Artificialmente

- [ ] não subir `P0-01`, `P0-02` ou `P0-03` sem artefato real
- [ ] não considerar aceite verbal como sign-off formal
- [ ] não confundir validação local com homologação externa
- [ ] não usar documentação forte para esconder ausência de prova operacional
- [ ] não considerar tentativa regulatória parcial como equivalente ao fechamento oficial de `P0-04`
- [ ] não usar RCA leve em UI/export/governança como substituto de gate regulatório ou de recorrência operacional

## Uso Recomendado na Governança

- revisar este checklist em toda reunião semanal enquanto o projeto estiver abaixo de `95%`
- marcar apenas o que tiver evidência disponível no ciclo
- escalar imediatamente itens externos sem resposta em `P0`
- sincronizar qualquer conclusão com scorecard, board operacional e registro semanal
- usar os gates acima para diferenciar avanço documental de avanço que realmente justifica `89%` ou `90%+`
