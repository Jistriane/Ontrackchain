# Governança Semanal Operacional — YYYY-MM-DD

## Objetivo

Template curto para conduzir a reuniao semanal com foco em evidencia, decisao de status e proxima acao verificavel.

Usar este template quando a necessidade principal for:

- revisar `P0/P1/P2` rapidamente
- confirmar bloqueios e escalacoes
- decidir se a baseline muda ou permanece

Para registro completo, complementar com:

- [Template de Governança Semanal Completa](./_template-weekly-governance.md)
- [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md)

## Baseline de Referencia

- construcao tecnica:
- prontidao regulatoria:
- KPI consolidado:
- houve evidencia nova material?: `sim | nao`

## Decisao Executiva Rapida

- decisao da semana: `manter baseline | recalibrar | pending | no-go | go_with_exception`
- principal ganho:
- principal bloqueio:
- item mais proximo de fechamento:
- item que exige escalacao externa:

## Snapshot dos Itens Criticos

| Bloco | Status atual | Ultima evidencia revisada | Bloqueio atual | Proxima acao verificavel | Data alvo | Semaforo |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P0-03` feed UE real | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `P0-01` `OIDC + MFA` serio | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| `RUN-STG-01` primeira janela seria | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| ownership/SLA | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |
| retention/recovery | `preencher` | `preencher` | `preencher` | `preencher` | `preencher` | `vermelho/amarelo/verde` |

## Regras de Passagem

- usar `blocked` quando a dependencia externa ou institucional impedir execucao real
- usar `ready` quando o gate existir, mas ainda faltar insumo real
- usar `in_progress` apenas quando houver execucao real em curso
- usar `ready_for_validation` quando a prova existir, mas ainda faltar revisao formal
- usar `done` apenas com artefato revisavel, aceite correspondente e documentacao sincronizada

## Checklist de Encerramento do Encontro

- [ ] itens `blocked` explicitamente marcados
- [ ] paths dos artefatos relevantes registrados
- [ ] proxima evidencia esperada anotada por item critico
- [ ] decisao executiva da semana registrada
- [ ] owner de escalacao definido para cada bloqueio que permaneceu

## Escalacoes Necessarias

- bloco:
  - motivo:
  - owner da escalacao:
  - prazo:

- bloco:
  - motivo:
  - owner da escalacao:
  - prazo:

## Proxima Revisao

- data:
- gatilho legitimo esperado:
- artefato esperado:
