# Kit de Execucao por Evidencia

## Objetivo

Transformar a subida de maturidade do Ontrackchain em um rito operacional simples, repetivel e auditavel.

Este kit existe para:

- orientar a execucao diaria dos blocos que movem o score
- padronizar coleta de evidencia
- padronizar decisao `verde/amarelo/vermelho`
- evitar promocao artificial de baseline

Use este documento em conjunto com:

- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md)
- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Board Operacional Unico ate 90%+](./project-operational-execution-board.md)
- [Checklist Operacional para 95%](./EXECUTION_CHECKLIST_TO_95_PERCENT.md)
- [ADR-010 - Promocao de Maturidade Baseada em Evidencia](./adrs/ADR-010-promocao-de-maturidade-baseada-em-evidencia.md)

Nao use este documento para substituir os registros datados de uma semana real. Quando a execucao acontecer de fato, o resultado deve ser registrado em `docs/governance-weekly/`.

## Regra Mestra

Toda promocao de maturidade depende de quatro elementos:

1. execucao real
2. evidencia preservada
3. revisao humana
4. aprovacao explicita

Sem esses quatro elementos, o score oficial nao sobe.

## Semaforo

| Cor | Significado | Efeito |
| --- | --- | --- |
| `verde` | execucao completa com evidencia suficiente | pode promover status |
| `amarelo` | houve avancos, mas ainda existe lacuna residual explicita | promocao parcial ou nenhuma |
| `vermelho` | falha critica, evidencia insuficiente ou execucao invalida | bloqueia promocao |

## Ordem Recomendada

1. `P0-02` homologar `AML/KYT live`
2. `P0-03` ativar feed UE real
3. `P0-01` homologar `OIDC + MFA` serio
4. gerar bundle regulatorio oficial
5. executar janela seria completa
6. publicar nova baseline oficial

## Plano D1-D7

| Dia | Frente | Meta objetiva | Ganho esperado |
| --- | --- | --- | --- |
| `D1` | preparar `P0-02` | credencial real validada e ambiente pronto | destrava trilha |
| `D2` | executar `P0-02` | checker verde com evidencia anexavel | `+2 a +3` pontos de prontidao |
| `D3` | executar `P0-03` | sync UE real com persistencia valida | `+1,5 a +2,5` pontos |
| `D4` | consolidar `P0-02 + P0-03` | bundle regulatorio integro e revisavel | institucionaliza a prova |
| `D5` | preparar `P0-01` | ambiente OIDC serio pronto | reduz risco do bloco mais critico |
| `D6` | executar `P0-01` | login federado + MFA + enforcement comprovados | `+3 a +5` pontos |
| `D7` | janela seria completa | war room, sign-off e `go/no-go` formal | converte capacidade em maturidade comprovada |

## Template 1 - Execucao Diaria

```md
# Execucao Diaria - D<X>

## Objetivo do Dia
- Frente:
- Owner responsavel:
- Accountable:
- Dependencias criticas:
- Meta objetiva do dia:

## Checklist de Entrada
- [ ] credenciais e acessos confirmados
- [ ] ambiente correto selecionado
- [ ] sem placeholders criticos
- [ ] scripts e comandos validados
- [ ] owner e consulted alinhados
- [ ] criterio de pronto entendido
- [ ] criterio de abortar entendido

## Execucao
- Inicio:
- Comandos executados:
- Ambiente utilizado:
- Artefatos esperados:
- Resultado observado:

## Bloqueadores
- Bloqueador:
- Severidade:
- Impacto:
- Mitigacao:
- Precisa escalonamento? sim/nao

## Resultado do Dia
- Status: verde / amarelo / vermelho
- Meta atingida? sim/nao
- Evidencia preservada? sim/nao
- Pode seguir para o proximo dia? sim/nao

## Proxima Acao
- Responsavel:
- Prazo:
- Dependencia:
```

## Template 2 - Evidencia Diaria

```md
# Evidencia Diaria - D<X>

## Frente
- ID:
- Nome:
- Data:
- Ambiente:
- Responsavel:

## Evidencia Tecnica
- Comando principal:
- Saida esperada:
- Saida obtida:
- Arquivo(s) gerados:
- Caminho dos artefatos:

## Evidencia Funcional
- O que foi comprovado:
- O que ainda nao foi comprovado:
- Houve comportamento degradado? sim/nao
- Houve fallback indevido? sim/nao

## Evidencia de Governanca
- Quem revisou:
- Quem aprovou:
- Quem foi informado:
- Ha parecer formal? sim/nao

## Conclusao
- Evidencia suficiente para promover status? sim/nao
- Evidencia reproduzivel? sim/nao
- Evidencia auditavel? sim/nao
- Observacoes:
```

## Template 3 - Decisao de Status

```md
# Decisao de Status - D<X>

## Frente
- ID:
- Nome:
- Owner:
- Accountable:

## Resultado
- Cor final: verde / amarelo / vermelho

## Justificativa
- O que funcionou:
- O que falhou:
- O que ficou parcial:
- Ha divergencia entre runtime, contrato e narrativa? sim/nao

## Regra Aplicada
- Verde:
  - [ ] execucao completa
  - [ ] evidencia preservada
  - [ ] criterio de pronto atendido
- Amarelo:
  - [ ] houve avancos reais
  - [ ] existe lacuna residual explicita
  - [ ] nao pode promover score cheio
- Vermelho:
  - [ ] falha critica
  - [ ] prova invalida ou incompleta
  - [ ] avanca bloqueado

## Decisao
- Seguir para proximo dia? sim/nao
- Promover status da frente? sim/nao
- Aplicar rollback executivo? sim/nao
- Acao corretiva obrigatoria:
- Novo gate de entrada:
```

## Template 4 - Atualizacao do Scorecard

```md
# Atualizacao de Scorecard - D<X>

## Snapshot Anterior
- Construcao tecnica:
- Prontidao regulatoria/operacional:
- Consolidado total:

## Evento do Dia
- Frente executada:
- Resultado:
- Status final: verde / amarelo / vermelho

## Impacto no Scorecard
- Construcao tecnica:
- Prontidao regulatoria/operacional:
- Consolidado total:
- Delta do dia:

## Motivo da Mudanca
- Evidencia que sustenta a mudanca:
- Artefatos anexados:
- Revisor:
- Aprovador:

## Regra de Promocao
- [ ] houve execucao real
- [ ] houve evidencia anexavel
- [ ] houve revisao humana
- [ ] nao existe bypass ou manualidade invalida
- [ ] mudanca de score foi explicitamente aprovada

## Observacao Executiva
- Leitura honesta do dia:
- Principal risco residual:
- Proximo gatilho legitimo:
```

## Pacote Preenchido - D1 a D7

### D1 - Preparacao `P0-02`

- owner sugerido: `Backend/Compliance Lead`
- accountable sugerido: `Arquiteto / Tech Lead`
- meta: validar credencial real e deixar o ambiente pronto sem placeholders criticos
- comando principal: `python scripts/preflight_external_integrations.py`
- gate de saida: credencial validada e ambiente apto para `D2`

### D2 - Execucao `P0-02`

- owner sugerido: `Backend/Compliance Lead`
- accountable sugerido: `Arquiteto / Tech Lead`
- meta: provar runtime real do provider `AML/KYT`
- comando principal: `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- gate de saida: `ready=true` e `provider_status=live` coerentes com artefato preservado

### D3 - Execucao `P0-03`

- owner sugerido: `Compliance/Ops Lead`
- accountable sugerido: `Arquiteto / Tech Lead`
- meta: executar sync real do feed UE e persistir evidencia
- comandos principais:
  - `make run-eu-sanctions-window-local WINDOW_ID=stg-$(date +%F)-eu`
  - `python scripts/check_sanctions_sync_status.py`
- gate de saida: URL real validada, JSONs persistidos e status coerente

### D4 - Consolidacao Regulatoria

- owner sugerido: `Arquitetura + Compliance`
- accountable sugerido: `Sponsor tecnico / Tech Lead`
- meta: transformar `P0-02` e `P0-03` em pacote revisavel por governanca
- comando principal: `make run-regulatory-readiness-bundle-local WINDOW_ID=stg-$(date +%F)-reg INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- gate de saida: bundle integro e revisavel

### D5 - Preparacao `P0-01`

- owner sugerido: `Auth/Infra Lead`
- accountable sugerido: `Arquiteto / Tech Lead`
- meta: deixar o ambiente pronto para homologacao seria sem fallback `dev`
- comando principal: `make run-oidc-readiness-bundle-local WINDOW_ID=stg-$(date +%F)-oidc BASE_URL=http://localhost:8080`
- gate de saida: ambiente serio pronto para `D6`

### D6 - Execucao `P0-01`

- owner sugerido: `Auth/Infra Lead`
- accountable sugerido: `Sponsor tecnico + Seguranca`
- meta: comprovar login federado real, MFA e enforcement em fluxo sensivel
- comando principal: `cd apps/frontend && npm run test:e2e:oidc-critical`
- gate de saida: trilho serio homologado com evidencia auditavel

### D7 - Janela Seria Completa

- owner sugerido: `Ops / Release Manager`
- accountable sugerido: `Owner executivo da janela`
- meta: converter capacidade tecnica em decisao formal `go/no-go`
- comandos principais:
  - `make run-serious-window-local WINDOW_ID=stg-2026-07-07-a MODE=baseline`
  - `make postprocess-serious-window RUN_URL=...`
- gate de saida: dossier final, sign-off e decisao formal publicados

## Como Usar

1. preencher `Template 1` antes de iniciar o dia
2. preencher `Template 2` logo apos os comandos
3. emitir a decisao no `Template 3`
4. atualizar o score apenas com base no `Template 4`
5. registrar a execucao real em `docs/governance-weekly/` quando o ciclo acontecer

## Decisao Recomendada

Use este kit como trilha canonica de execucao ate a proxima recalibracao material do scorecard.
