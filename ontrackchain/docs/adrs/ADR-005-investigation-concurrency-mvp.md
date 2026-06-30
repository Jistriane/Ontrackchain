# ADR-005 — Concorrencia MVP com Fila Leve

## Contexto

Investigation e a trilha mais sujeita a custo e variacao de carga. No MVP, ainda nao existe worker dedicado, mas tambem nao e aceitavel permitir crescimento sem contencao.

## Decisao

Aplicar limite de concorrencia por plano e um teto global no `investigation-api`. Quando o limite for atingido, o sistema cria o case e retorna `202` com `status=queued` e `position_in_queue`.

## Motivacao

- proteger estabilidade do MVP
- evitar picos destrutivos
- manter contrato previsivel para o cliente

## Alternativas Consideradas

### Opcao A — Sem limite de concorrencia

- Vantagem:
  - implementacao minima
- Desvantagem:
  - alto risco operacional

### Opcao B — Worker/queue completa desde o inicio

- Vantagem:
  - arquitetura mais robusta
- Desvantagem:
  - complexidade maior que o necessario para o scaffold atual

### Opcao C — Contencao leve no servico com fila logica

- Vantagem:
  - entrega rapida
  - comportamento explicavel
- Desvantagem:
  - ainda nao substitui worker real

## Consequencias

- clientes precisam lidar com `202 queued`
- smoke precisa validar concorrencia e finalizacao
- a Fase 2 deve substituir esse modelo por worker real

## Trade-offs Aceitos

- solucao intermediaria de menor custo agora, com plano explicito de evolucao depois

## Status

- Aceito e implementado
