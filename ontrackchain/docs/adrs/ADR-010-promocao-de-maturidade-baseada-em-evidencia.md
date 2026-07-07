# ADR-010 - Promocao de Maturidade Baseada em Evidencia

## Status

Aceito

## Contexto

O projeto atingiu uma fase em que a maior parte do valor remanescente nao vem de novas features, mas de:

- homologacao externa
- validacao de providers reais
- execucao de janelas serias
- aceite institucional recorrente

Nesse contexto, havia risco de inflar a leitura de maturidade com base em:

- configuracao pronta sem execucao
- readiness documental sem prova em runtime
- sucesso parcial sem reproducibilidade
- narrativa executiva desconectada do artefato coletado

Como o score oficial do projeto (`91% / 78% / 87%`) passou a orientar priorizacao executiva, a regua de promocao precisava deixar de ser implicita.

## Decisao

A partir deste ADR, qualquer promocao de maturidade no Ontrackchain deve obedecer a seguinte regra:

> Status so sobe quando houver execucao real, evidencia preservada, revisao humana e aprovacao explicita.

Essa regra vale para:

- scorecard executivo
- fechamento de itens `P0/P1/P2`
- mudanca de baseline
- classificacao `done` em boards operacionais
- pareceres de readiness e `go/no-go`

## Criterios Obrigatorios

Uma frente so pode ser promovida quando todos os itens abaixo forem verdadeiros:

1. houve execucao real em ambiente valido
2. a evidencia foi preservada em artefato rastreavel
3. a evidencia e reproduzivel e auditavel
4. nao houve fallback indevido ou bypass nao aceito
5. runtime, contrato e narrativa executiva estao coerentes
6. houve revisao humana do resultado
7. o accountable aprovou explicitamente a promocao

## Semaforo Operacional

| Cor | Significado | Efeito sobre maturidade |
| --- | --- | --- |
| `verde` | execucao completa com evidencia suficiente | promocao permitida |
| `amarelo` | houve avancos, mas ainda existe lacuna residual explicita | promocao parcial ou nenhuma promocao |
| `vermelho` | falha critica, evidencia insuficiente ou execucao invalida | promocao proibida e possivel rollback executivo |

## Consequencias

### Positivas

- reduz autoengano organizacional
- evita score inflado artificialmente
- melhora rastreabilidade para auditoria e governanca
- alinha engenharia, seguranca, operacao e sponsors na mesma regua de pronto

### Negativas

- aumenta o rigor para declarar avancos
- pode retardar promocao de status no curto prazo
- exige disciplina de artefatos, revisao e sincronizacao documental

## Aplicacao Imediata

Este ADR se aplica especialmente a:

- `P0-01` OIDC + MFA serio
- `P0-02` AML/KYT live
- `P0-03` feed UE tokenizado real
- primeira janela seria material
- publicacao de nova baseline oficial

## Documentos Afetados

- [Scorecard Oficial do Projeto](../project-kpi-scorecard.md)
- [Board Operacional Unico ate 90%+](../project-operational-execution-board.md)
- [Resumo Executivo de Readiness](../project-executive-readiness-brief.md)
- [Documentacao Canonica](../README.md)
