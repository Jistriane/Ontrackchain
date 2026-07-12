# Playbook Canonico de Incidente Cross-Domain e RCA

## Objetivo

Padronizar quando um alerta operacional deixa de ser apenas triagem local e passa a exigir coordenacao cross-domain, war room leve e registro formal de RCA (root cause analysis) no baseline atual do Ontrackchain.

Este playbook existe para reduzir drift entre:

- deteccao tecnica via `operational_alert_events`
- triagem operacional em `/alerts` e `/monitoring`
- coordenacao humana em war room
- historico auditavel em `regulatory_work_items`, `regulatory_work_events`, `regulatory_work_comments` e `audit_logs`
- publicacao executiva em `docs/governance-weekly/`

Use este documento junto com:

- [Runbooks Operacionais](./runbooks.md)
- [Ownership e SLAs operacionais](./operational-ownership-and-slas.md)
- [Matriz de War Room](./staging-serious-window-war-room-matrix.md)
- [Runbook Semanal de Governanca](./project-weekly-governance-runbook.md)
- [Board de Prioridades](./project-priority-board.md)
- [Board Operacional](./project-operational-execution-board.md)

## Quando Abrir um Incidente Cross-Domain

Abra um incidente cross-domain quando pelo menos uma das condicoes abaixo for verdadeira:

- um alerta impacta dois ou mais dominios operacionais entre `monitoring`, `investigation`, `compliance`, `reporting`, `frontend` ou `platform`
- um alerta unico bloqueia um fluxo critico fim a fim (`case -> report`, `alert -> evidence`, `ros/coaf`, `staging serious window`, `OIDC/MFA`, `AML/KYT`, `EU sanctions`)
- o mesmo sintoma reaparece apos mitigacao inicial, sugerindo causa sistemica
- existe risco de violacao de SLA, backlog operacional relevante, degradacao regulatoria ou perda de observabilidade
- o owner da triagem solicita escalacao para war room ou comandante do incidente

Nao abra incidente cross-domain quando:

- o sintoma estiver restrito a um unico dominio sem risco de propagacao
- a mitigacao for local, reversivel e concluida sem efeito em fila, prazo ou integracao critica
- nao houver impacto operacional, regulatorio ou de disponibilidade observavel

## Limites do Sistema

No baseline atual, este playbook NAO cria um servico novo de incident management.

Ele reaproveita a trilha ja existente:

- `operational_alert_events` como source of truth de deteccao e acknowledge
- `regulatory_work_items` como workspace operacional e timeline persistida para incidentes rastreados
- `audit_logs` como trilha auditavel das acoes relevantes
- `docs/governance-weekly/` como registro datado de war room, sign-off e proximos passos

O diagrama abaixo mostra a passagem do incidente entre observabilidade, workspace operacional, auditoria e governanca.

[[diagram: fluxo de incidente cross-domain com RCA leve. Alertmanager e Prometheus disparam para monitoring-api. Monitoring-api persiste operational_alert_events e expõe leitura administrativa para /monitoring. O cockpit /alerts promove o alerta material para regulatory_work_item compartilhado sem abrir novo microservico. O work-item concentra metadata canônica, ownership, status, timeline, comentarios e campos de RCA leve. Audit_logs registram acknowledge, export, negacoes e transicoes relevantes. Quando o blast radius atravessa dominios, o resumo do incidente alimenta governance-weekly/cycles, war room e o artefato operacional de RCA summary. Domain Owners de backend, compliance, report, frontend e platform executam mitigacoes e retornam atualizacoes ao work-item ate causa raiz, comandante e evidencias ficarem rastreaveis para fechamento.]]

## Papeis e Responsabilidades

| Papel | Responsabilidade minima | Fonte canonica de apoio |
| --- | --- | --- |
| `Incident Commander` | coordenar resposta, definir prioridade, decidir escalacao e encerramento | `operational-ownership-and-slas.md` |
| `Domain Owner` | investigar sintoma no dominio, propor mitigacao e confirmar recuperacao | `runbooks.md` |
| `Scribe` | registrar timeline, causa suspeita, causa confirmada e acoes corretivas | `regulatory_work_comments` + `docs/governance-weekly/` |
| `Platform/SRE` | validar observabilidade, health checks, scraping, alert routing e estabilidade da plataforma | `runbooks.md` + `staging-serious-window-war-room-matrix.md` |
| `Arquitetura/Governanca` | revisar blast radius, impacto em baseline, follow-ups e backlog estrutural | `project-weekly-governance-runbook.md` |

## Fluxo Canonico

1. **Detectar**
   - alerta entra por `Alertmanager` e e persistido em `operational_alert_events`
   - triagem inicial ocorre em `/monitoring` ou `/alerts`
2. **Qualificar**
   - confirmar severidade, dominios afetados, risco regulatorio, impacto em backlog e repeticao
   - decidir se o evento continua local ou vira incidente cross-domain
3. **Promover**
   - para incidente cross-domain, garantir work-item rastreado em `module=alerts`
   - vincular contexto operacional (`case_id`, `address`, `report_id`, `ros_id`, `request_id`) quando houver
4. **Conter**
   - aplicar mitigacao imediata
   - registrar owner, ETA e status de contencao
5. **Explicar**
   - registrar `suspected_root_cause`
   - confirmar ou revisar a causa apos coleta de evidencia
6. **Corrigir**
   - abrir acoes corretivas e preventivas com owner e prazo
   - diferenciar mitigacao temporaria de correcao estrutural
7. **Fechar**
   - rodar validacoes finais
   - registrar `confirmed_root_cause`, evidencias e follow-ups
   - publicar resumo em governanca quando o impacto justificar

## Modelo de RCA Leve no Baseline Atual

Enquanto nao existir schema dedicado de RCA, persista a analise no work-item compartilhado do alerta rastreado.

Campos minimos recomendados em `metadata` do `regulatory_work_item`:

| Campo | Uso | Obrigatorio no fechamento |
| --- | --- | --- |
| `domain` | dominio principal afetado | sim |
| `affected_domains` | lista de dominios impactados | sim |
| `incident_commander` | owner principal da resposta | sim |
| `runbook_ref` | runbook usado na mitigacao | sim |
| `impact_summary` | resumo curto do impacto | sim |
| `containment_status` | `not_started`, `in_progress`, `contained`, `validated` | sim |
| `suspected_root_cause` | hipotese inicial | sim |
| `confirmed_root_cause` | causa raiz validada | sim |
| `blast_radius` | escopo do impacto | sim |
| `corrective_actions` | lista curta de acoes estruturais | sim |
| `preventive_actions` | lista curta de acoes preventivas | recomendavel |
| `evidence_refs` | artefatos, logs, exports, reports, bundle ids | sim |
| `war_room_ref` | link para artefato datado quando houver escalacao formal | condicional |

Regras:

- usar comentarios para narrativa cronologica curta e legivel
- usar `audit_logs` para provas de ack, export, rerun, sign-off e operacoes automatizadas
- nao armazenar segredo, token, webhook ou dump sensivel em comentarios ou metadata

## Criticidade e Escalacao

| Nivel | Sinal | Resposta minima |
| --- | --- | --- |
| `L1` | incidente local com owner definido e mitigacao rapida | manter no dominio, sem war room formal |
| `L2` | impacto cross-domain controlado | abrir incidente cross-domain, work-item rastreado e comandante definido |
| `L3` | risco de SLA, bloqueio regulatorio ou indisponibilidade relevante | ativar war room leve, revisar a cada checkpoint e registrar resumo na governanca |
| `L4` | risco institucional, `no-go`, perda de controle operacional ou falha repetitiva critica | ativar matriz de war room, escalar sponsors tecnicos e anexar artefatos datados |

## Evidencias Minimas para Encerramento

Antes de encerrar um incidente cross-domain:

- rodar `smoke_runtime.py` quando o dominio impactado justificar
- rodar Playwright relevante para o caminho critico afetado
- validar `audit_logs` e export do alerta quando aplicavel
- confirmar recuperacao em `/monitoring`, `/alerts` ou no endpoint operacional do dominio
- registrar `confirmed_root_cause`
- registrar se houve gap de teste, observabilidade, ownership ou documentacao
- abrir follow-up para qualquer correcao estrutural que nao caiba no incidente atual

## Template de Registro

Use o formato abaixo no comentario principal do work-item ou no artefato datado da governanca:

```md
## RCA

- incidente: <work_item_id ou fingerprint>
- severidade: <L1|L2|L3|L4>
- commander: <owner>
- dominios_afetados: <lista>
- impacto: <resumo objetivo>
- runbook: <ref>
- causa_suspeita: <texto curto>
- causa_confirmada: <texto curto>
- mitigacao_imediata: <texto curto>
- correcao_estrutural: <texto curto>
- acao_preventiva: <texto curto>
- evidencias: <links, ids, artifacts>
- follow_up: <board item, issue, ADR ou none>
```

## Integracao com War Room

Se o incidente ocorrer durante a janela seria ou bloquear um gate `P0`, faca tambem:

- abrir ou atualizar o artefato datado de war room em `docs/governance-weekly/cycles/<ciclo>/`
- registrar `war_room_ref` no work-item
- refletir status e owner no sign-off ou no tracking ao vivo quando o impacto for material

Se o incidente for operacional, mas fora da janela seria:

- manter a RCA leve no work-item
- levar apenas o resumo executivo e os follow-ups para a governanca semanal

## Definition of Done

Um incidente cross-domain so pode ser fechado quando:

- a contencao estiver validada
- a causa raiz estiver confirmada
- a evidencia minima estiver anexavel
- houver owner e prazo para as acoes corretivas remanescentes
- a necessidade de update em runbook, dashboard, alerta, teste ou arquitetura estiver explicitamente registrada

## Proximo Incremento Tecnico Recomendado

Sem criar novo servico, o proximo incremento coerente e:

- enriquecer `module=alerts` com os campos de RCA leve acima
- expor esse bloco de RCA no cockpit `/alerts`
- preservar `/monitoring` como hub de triagem e saude da plataforma
- usar war room datado apenas quando a severidade justificar escalacao institucional
