# Owners e SLAs Operacionais

## Objetivo

Nomear owners operacionais minimos por dominio e padronizar tempos de resposta esperados para incidentes do Ontrackchain.

Este documento complementa [runbooks.md](./runbooks.md) e [retention-and-recovery-policy.md](./retention-and-recovery-policy.md).

## Matriz de Owners

| Dominio | Owner primario | Backup | Escopo |
| --- | --- | --- | --- |
| Gateway/Frontend | Frontend Platform | Platform/SRE | `traefik`, `frontend`, rotas `/api/app/*`, UX operacional |
| Auth/OIDC | Backend/Auth | Security | `auth-service`, `Keycloak`, `OIDC`, claims, MFA |
| Investigation/Billing | Backend Core | Platform/DBA | `investigation-api`, `investigation-worker`, `credit_ledger`, fila e DLQ |
| Compliance/AML | Compliance/Backend | Security | `compliance-api`, provider AML/KYT, score e degradacao controlada |
| Monitoring/Alerting | Platform/SRE | Backend Core | `prometheus`, `grafana`, `alertmanager`, `monitoring-api`, incidentes globais |
| Reports/Evidencias | Backend Core | Compliance | `report-api`, hashes, downloads auditados, export bundles |
| Banco/Recovery | Platform/DBA | Security | PostgreSQL, backup, restore, retention e legal hold |

## SLO/SLA Base

| Severidade | Definicao | Ack alvo | Atualizacao | Contencao/restore alvo |
| --- | --- | ---: | ---: | ---: |
| `P0` | indisponibilidade critica, risco a integridade ou vazamento | 15 min | 30 min | 60 min |
| `P1` | fluxo critico degradado sem vazamento confirmado | 60 min | 4 h | 1 dia util |
| `P2` | degradacao parcial ou falha auxiliar | 1 dia util | 1 dia util | proximo ciclo planejado |

## Mapeamento Rapido para Runbooks

| Dominio | Runbooks iniciais |
| --- | --- |
| Gateway/Frontend | 1, 5, 19, 20 |
| Auth/OIDC | 2, 3, 4 |
| Investigation/Billing | 6, 7, 8, 9, 10 |
| Monitoring/Alerting | 17, 18, 19, 20 |
| Banco/Recovery | 21 |

## Regras Minimas

- Todo incidente aberto deve registrar `request_id` quando houver correlacao tecnica disponivel.
- Nenhum workaround fora de `local|test` pode ser aplicado sem owner tecnico do dominio.
- Casos `P0/P1` que afetem evidencias, auditoria ou recovery exigem envolvimento de `Security`.
- Restore deve ocorrer preferencialmente em banco isolado antes de qualquer acao destrutiva no banco principal.

## Criterios para Fechar `P2-02`

- owners nomeados por dominio
- SLA base aceito pelo time
- runbooks principais mapeados por dominio
- documento referenciado nos checklists e gates de release

## Status de Aceite Operacional

Estado atual: `ready_for_approval`

### Evidencias para Sign-off

- matriz minima de owners por dominio publicada
- SLA base por severidade documentado
- mapeamento inicial de runbooks por dominio publicado
- referencia explicita em checklist pre-producao e gate de release

### Aprovações Necessarias

| Papel | Responsabilidade de aceite | Status | Evidencia esperada |
| --- | --- | --- | --- |
| Platform/SRE | validar escalacao, ownership e caminho de resposta | `pending` | comentario de aceite ou decisao registrada |
| Security | validar envolvimento obrigatorio em incidentes P0/P1 sensiveis | `pending` | comentario de aceite ou decisao registrada |
| Backend Core | validar aderencia dos dominios Investigation/Billing/Reports | `ready` | runbooks e owners ja publicados |

### Registro de Aceite

| Papel | Responsavel | Data | Decisao | Observacoes |
| --- | --- | --- | --- | --- |
| Platform/SRE | `pending` | `pending` | `pending` | confirmar escala real do time e on-call |
| Security | `pending` | `pending` | `pending` | confirmar envolvimento em P0/P1 com evidencias |
| Backend Core | `pending` | `pending` | `ready` | dominios core ja mapeados na baseline |
