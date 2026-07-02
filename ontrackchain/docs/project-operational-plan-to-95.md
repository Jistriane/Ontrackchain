# Plano Operacional Trimestral para 95%

## Objetivo

Transformar a baseline atual de maturidade em um plano operacional trimestral que leve o Ontrackchain de:

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada

para:

- `95%` de maturidade tecnica sustentada
- faixa regulatoria significativamente superior, ainda sem declarar producao plena

## Resumo Executivo

Leitura recomendada:

- `Trimestre 1`: homologar os gaps externos que ainda bloqueiam a leitura regulatoria
- `Trimestre 2`: institucionalizar governanca, sign-off e repetibilidade de janela seria
- `Trimestre 3`: reforcar cadeia de custodia, incident response e segredos de producao

Premissa central:

- o maior ganho remanescente nao vem de novos modulos, e sim de homologacao, coerencia contratual final e governanca formal

Baseline canônica de referencia:

- [Governança Semanal 2026-07-01](governance-weekly/2026-07-01-weekly-governance.md)
- [Atualização de KPI 2026-07-01](governance-weekly/2026-07-01-kpi-scorecard-update.md)

## Trimestre 1 — Homologacao Real

### Objetivo

- fechar os gaps externos que ainda impedem uma leitura regulatoria mais forte

### Meta de Saida

- baseline tecnica sustentada em `91%+`
- prontidao regulatoria em torno de `82%`

### Itens Prioritarios

| Ordem | Item | Dominio | Impacto |
| --- | --- | --- | --- |
| 1 | Desbloquear e homologar `OIDC` e MFA federado serio | Auth | muito alto |
| 2 | Executar provider `AML/KYT` em `live` com `check-compliance-provider-runtime` | Compliance | muito alto |
| 3 | Executar feed UE tokenizado real e validar `EU_CONSOLIDATED` com runner dedicado | Sancoes | muito alto |
| 4 | Sustentar catalogo `sanctions_check` alinhado e coberto por testes | Contrato/Produto | medio |
| 5 | Executar janela seria completa com dossier aceito e JSONs de checks anexados | Release | alto |

Leitura operacional do T1 apos a baseline de `2026-07-01`:

- `P0-01` continua `blocked` ate existir evidencia externa e aceite institucional do trilho serio
- `P0-02` esta `ready` e depende de credencial real + gate de runtime verde
- `P0-03` esta `ready` e depende de URL tokenizada real + JSONs anexados da janela UE

## Trimestre 2 — Governanca Aceita

### Objetivo

- transformar baseline tecnica em operacao institucionalmente aceita

### Meta de Saida

- baseline tecnica em torno de `93%`
- prontidao regulatoria em torno de `88%`

### Itens Prioritarios

| Ordem | Item | Dominio | Impacto |
| --- | --- | --- | --- |
| 1 | Obter sign-off formal de retention/recovery | Governanca | alto |
| 2 | Executar janelas serias recorrentes com historico comparavel | Release | alto |
| 3 | Alinhar inventario/catalogo de eventos da `evidence_trail` | Evidencias | medio |
| 4 | Formalizar owners, SLA e runbooks com aceite | Operacao | alto |
| 5 | Estruturar artefatos de manual review para DD/SoF | Compliance | medio |

## Trimestre 3 — Cadeia de Custodia Forte

### Objetivo

- institucionalizar confiabilidade, segredos e incident response

### Meta de Saida

- baseline tecnica em `95%`
- prontidao regulatoria acima de `90%`, ainda sem alegar producao automatica plena

### Itens Prioritarios

| Ordem | Item | Dominio | Impacto |
| --- | --- | --- | --- |
| 1 | Implantar estrategia de vault/secrets de producao | Seguranca | alto |
| 2 | Formalizar war room, escalacao e RCA | Operacao | alto |
| 3 | Reforcar cadeia de custodia com selagem/assinatura ou equivalente | Evidencias | alto |
| 4 | Automatizar promocao superior com menos passos manuais | Release | medio |
| 5 | Refinar papeis regulatorios por dominio | Seguranca | medio |

## KPIs do Plano

| KPI | Meta |
| --- | --- |
| Baseline tecnica | `91%+` no T1, `93%` no T2, `95%` no T3 |
| Readiness regulatorio | `82%` no T1, `88%` no T2, `90%+` no T3 |
| KPI total consolidado | `87%` baseline, `90%+` ao fim do T1, `92%+` no T2, `95%` no T3 |
| Janelas serias com dossier aceito | `>= 2` ate o fim do T2 |
| Sign-offs formais pendentes | `0` para retention/recovery e ownership ate o fim do T2 |
| Gaps contratuais conhecidos | `0` para `sanctions_check` e inventario de eventos ate o fim do T2 |
| Artefatos recorrentes anexados | `100%` das janelas AML/KYT e UE com JSONs e bundles em `artifacts/staging/checks/` |

## Decisao Recomendada

- nao abrir frentes grandes de feature antes de fechar homologacao externa e coerencia contratual do core regulatorio
- usar o T2 para institucionalizar o que hoje ja existe tecnicamente
- usar o T3 para aproximar o projeto de um padrao de operacao regulada repetivel
- usar `91% / 78% / 87%` como baseline executiva ate nova evidencia material publicada na governanca semanal
