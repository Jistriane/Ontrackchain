# Janelas Geradas

## Objetivo

Concentrar artefatos gerados separados por `window_id`, evitando colisao entre snapshots, dashboards e planos de acao de janelas diferentes.

## Regra de Namespace

- todo artefato gerado da janela deve viver em `docs/governance-weekly/generated/windows/<window_id>/`
- evite caminhos legados em `docs/governance-weekly/generated/<window_id>-...`, que foram substituidos por este namespace

## Regra de Leitura

- trate esta pasta como camada gerada, nunca como fonte primaria de decisao humana
- artefatos vivos de war room, tracking, sign-off e `decision packet` do ciclo corrente continuam em `docs/governance-weekly/cycles/<data>/`
- um namespace novo em `generated/windows/<window_id>/` so deve aparecer depois que o refresh gerado da janela for executado com sucesso

## Janelas Disponiveis

- [Janela `stg-2026-07-06-a`](./stg-2026-07-06-a/README.md): ultimo namespace gerado preservado como referencia historica

## Ciclo Ativo

- a tentativa humana atual segue em `docs/governance-weekly/cycles/2026-07-13/`
- a janela operacional corrente e `stg-2026-07-13-a`
- o namespace gerado correspondente deve surgir aqui somente apos execucao do refresh gerado da janela
