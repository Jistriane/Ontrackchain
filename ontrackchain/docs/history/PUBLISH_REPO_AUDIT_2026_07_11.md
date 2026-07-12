# Auditoria de `.publish_repo` - 2026-07-11

## Objetivo

Registrar a decisao documental sobre o diretorio `.publish_repo/`, reduzindo reabertura recorrente da mesma duvida: ele deve ser tratado como fonte canônica, espelho de publicacao ou candidato imediato a delecao.

## Escopo da Auditoria

Foi auditado:

- uso interno por referencias textuais no repositório principal
- divergencia estrutural em relacao a `README.md`, `ontrackchain/README.md` e `ontrackchain/docs/README.md`
- presenca de arquivos ja removidos ou reclassificados na trilha canônica
- aderencia do espelho as mudancas recentes de `history/`, `P2-05` e saneamento documental

## Achados

### 1. Nao ha evidencia de uso interno pelo repositório ativo

As buscas internas nao encontraram referencias operacionais ou de build apontando para `.publish_repo/` como source of truth do projeto.

Leitura resultante:

- o repositório ativo nao consome `.publish_repo/` para decidir baseline, contrato ou governanca
- se existir uso real, ele provavelmente e externo ao workspace atual ou manual

### 2. O espelho esta materialmente divergente da trilha canônica

Foram observados sinais concretos de drift:

- o espelho ainda manteve os caminhos antigos de `first-serious-window-*` e `staging-serious-window-signoff-template.md`
- o espelho nao refletiu a migracao desses artefatos para `docs/history/`
- o espelho preserva versoes anteriores do `README` raiz e do indice `docs/README.md`
- o espelho nao acompanhou a limpeza recente da documentacao viva e da taxonomia de governanca

### 3. O drift e suficiente para desqualificar `.publish_repo/` como fonte primaria

Conclusao objetiva:

- `.publish_repo/` nao pode ser usado como baseline, contrato, matriz de governanca ou status executivo
- qualquer decisao arquitetural, regulatoria ou operacional deve continuar partindo do repositorio ativo e da trilha `ontrackchain/docs/`

### 4. O drift ainda nao prova delecao segura

Apesar da divergencia, a auditoria nao produziu prova forte de que:

- nenhum processo externo/manual dependa do espelho
- nenhum handoff humano use `.publish_repo/` como pacote de publicacao
- nao exista rotina fora do repositorio que ainda espere essa arvore

## Decisao

### Decisao Atual

Tratar `.publish_repo/` como:

- **espelho de publicacao nao-canônico**
- **fora da governanca viva do projeto**
- **nao elegivel a delecao automatica nesta rodada**

### Regra Pratica

Enquanto nao houver prova adicional:

- nao atualizar `.publish_repo/` como parte do ciclo normal de engenharia
- nao usar `.publish_repo/` para validar baseline, readiness, RBAC, contratos ou maturidade
- nao deletar `.publish_repo/` sem uma auditoria adicional focada em consumidores externos

## Proxima Decisao Segura

A proxima rodada recomendada, se houver interesse em remover o espelho, e:

1. identificar se existe processo externo/manual de publicacao usando `.publish_repo/`
2. validar se o espelho precisa ser regenerado ou se pode ser aposentado
3. so entao executar delecao controlada ou congelamento formal

## Relacao com a Trilha Canonica

Esta auditoria complementa:

- [Indice Canônico da Documentacao](../README.md)
- [Historico de Apoio](./README.md)
- [README raiz](../../../README.md)

E reforca a regra ja publicada de que `.publish_repo/` nao e fonte primaria de status, contrato ou baseline.
