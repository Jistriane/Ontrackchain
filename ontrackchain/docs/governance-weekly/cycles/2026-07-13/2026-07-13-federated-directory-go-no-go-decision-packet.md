# Go/No-Go Decision Packet - `stg-2026-07-13-federated-a`

## Objetivo

Dar uma leitura executiva unica da tentativa `stg-2026-07-13-federated-a`, com:

- decisao atual
- bloqueadores ativos
- evidencias minimas faltantes
- criterio objetivo para promocao

Use este packet junto com:

- [Bridge Quick-Fill `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-bridge-quick-fill.md)
- [War Room da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-war-room.md)
- [Roteiro Minuto a Minuto `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-minute-by-minute-execution.md)
- [Sign-Off da Janela `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-signoff.md)
- [Run Sheet Datada `stg-2026-07-13-federated-a`](./2026-07-13-federated-directory-staging-run-sheet.md)

## Decisao Atual

- `window_id`: `stg-2026-07-13-federated-a`
- `modo`: `dress_rehearsal_controlado`
- `decisao_atual`: `pending_no_go`
- `motivo_principal`: aguardando execucao real em `staging` com client tecnico do `Keycloak`, operador `ADMIN` online e par coerente `users + principal externo`
- `owner_da_decisao`: `Release Manager Tecnico`
- `proximo_checkpoint`: `<preencher_HH:MMZ>`

## Leitura Curta por Frente

| Frente | Estado atual | O que falta | Saida honesta hoje |
| --- | --- | --- | --- |
| `auth-service` / diretório federado | `ready` | confirmar escopo minimo do client tecnico em runtime | `ready_for_validation` |
| `Team` / busca assistida | `ready` | execucao manual real de `search -> suggestion -> link` | `ready_for_validation` |
| `Audit` / preset `identity-federated` | `ready` | confirmar evento real de `link/unlink` no cockpit | `ready_for_validation` |
| `audit_logs` / correlacao tecnica | `ready` | confirmar `search + suggestion + link` via SQL | `ready_for_validation` |
| `Gate agregado federado` | `pending_execucao` | owners online + runtime real + evidencias capturadas | `pending` |

## Bloqueadores Ativos

- `FD-01`: client tecnico do `Keycloak` ainda nao confirmado com escopo minimo real neste ciclo
- `FD-02`: operador `ADMIN` do tenant e principal externo de teste ainda nao confirmados para a tentativa datada
- `FD-03`: evidencias reais de `Team`, `Audit` e `audit_logs` ainda nao foram capturadas

## Evidencias Minimas Faltantes

- screenshot da busca assistida no `Team`
- screenshot do `link` persistido no `Team`
- screenshot do preset `identity-federated` no `Audit`
- screenshot do evento `team_external_identity_unlinked`
- output ou screenshot da consulta SQL em `audit_logs`
- `request_id` ou timestamp correlacionavel da tentativa

## Criterio Objetivo de Promocao

Promover de `pending_no_go` para `pending_go` somente se todos forem verdadeiros:

- owner de `Backend/Auth` confirmar o runtime do `auth-service`
- owner de `Frontend` confirmar o operador `ADMIN` online
- tenant e principal externo de teste confirmados
- bridge principal e owners online registrados

Promover de `pending_go` para `approved` somente se:

- a busca assistida em `Team` retornar o candidato correto
- a sugestao de vinculo for aprovada
- o `link` for persistido
- o `Audit` exibir `team_external_identity_linked`
- a consulta SQL confirmar `team_federated_directory_searched`, `team_federated_directory_suggestion_validated` e `team_external_identity_linked`
- o `unlink` reversivel for validado

## No-Go Imediato

- `federated_directory_forbidden`
- `federated_directory_unavailable`
- `candidate_org_mismatch`
- `team_external_identity_already_linked`
- ausencia de evento de `link` no `Audit`
- ausencia de qualquer um dos eventos obrigatorios em `audit_logs`

## Proximo Passo Executivo

- acao: preencher owners/canais, validar o client tecnico do `Keycloak`, preparar o tenant de teste e executar a tentativa datada
- owner: `Release Manager Tecnico`
- destino esperado apos o checkpoint: `pending_go` ou `no-go`
