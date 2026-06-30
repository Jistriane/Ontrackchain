# Retention e Recovery

## Objetivo

Definir a baseline minima de retention, cadeia de custodia e recovery para auditoria, evidencias e dados operacionais do Ontrackchain.

Este documento nao substitui uma politica corporativa final nem parecer juridico. Ele estabelece a base tecnica e operacional que o projeto precisa para sair do estado "scaffold validado" e caminhar para staging serio.

## Escopo

- `audit_logs`
- `operational_alert_events`
- metadados de relatorios e downloads auditados
- `credit_ledger`, `quotes` e casos investigativos/compliance
- backups logicos do PostgreSQL

## Owners

| Dominio | Owner primario | Apoio | Responsabilidade |
| --- | --- | --- | --- |
| Politica de retention | Security | Compliance | aprovar classes, prazos e excecoes |
| Execucao de backup/restore | Platform/DBA | Security | garantir backup, restore e evidencias |
| Evidencias de auditoria | Security | Backend | preservar cadeia de custodia e `request_id` |
| Evidencias operacionais | Platform | Monitoring | preservar alertas, exportacoes e runbooks |

## Classes de Dados

| Classe | Exemplos | Retention online | Retention arquivada | Regra de descarte |
| --- | --- | ---: | ---: | --- |
| Auditoria critica | `audit_logs`, `report_downloaded`, `operational_alerts_exported`, acessos negados sensiveis | 365 dias | 2555 dias | purge apenas apos expiracao, sem legal hold e com aprovacao de Security |
| Evidencia regulatoria | metadados de relatorios, hashes, correlacao `request_id/case_id/report_id` | 365 dias | 2555 dias | purge apenas apos expiracao, sem incidente aberto e com aprovacao de Security + Compliance |
| Financeiro operacional | `credit_ledger`, reconciliacoes, `PRE_HOLD/CONFIRMED/REFUND` | 365 dias | 2555 dias | purge apenas com backup valido e reconciliacao fechada |
| Operacao de plataforma | `operational_alert_events`, alertas roteados via Alertmanager, snapshots administrativos | 90 dias | 365 dias | purge automatizavel se nao houver incidente/RCA pendente |
| Artefatos temporarios | dumps locais, exports transitarios, arquivos restaurados para teste | 7 dias | 0 dias | purge automatico apos validacao ou handoff da evidencia |

## Regras de Cadeia de Custodia

- Toda evidencia auditavel deve preservar pelo menos um identificador correlacionavel entre `request_id`, `case_id`, `report_id` ou `fingerprint`.
- Evidencias exportadas devem manter hash ou trilha equivalente quando aplicavel.
- Nenhum dado marcado para `legal hold`, incidente P0/P1 ou investigacao regulatoria pode ser purgado.
- A remocao definitiva precisa registrar quem aprovou, qual foi o escopo e qual backup cobria o periodo removido.

## Baseline de Backup e Restore

- Frequencia minima:
  - backup logico diario do PostgreSQL
  - backup adicional antes de migrations destrutivas ou mudancas de schema sensiveis
- Evidencias minimas por execucao:
  - timestamp UTC
  - arquivo gerado ou caminho do artefato
  - manifesto `.manifest.json` associado ao artefato
  - banco alvo
  - tamanho do dump
  - `sha256` do dump ou arquivo de origem
  - status final
- Restore minimo exigido:
  - restaurar em banco separado do principal
  - registrar `RTO` observado
  - validar que o schema restaurado possui tabelas esperadas

## Procedimento Minimo

### Backup local/controlado

```bash
bash scripts/backup_postgres.sh
```

### Restore em banco isolado

```bash
RESTORE_TARGET_DB=ontrackchain_restore_check bash scripts/restore_postgres.sh artifacts/backups/<arquivo>.dump
```

### Evidencia esperada

- log do backup
- log do restore
- manifesto JSON do backup
- manifesto JSON do restore
- nome do banco de restore
- `RTO` observado

## Critérios para Fechar o Gap de Governanca

`P1-01` pode ser considerado encerrado quando:

- a politica estiver publicada
- owners estiverem nomeados
- os prazos por classe estiverem definidos
- houver aprovacao explicita de Security/Compliance

`P1-02` pode ser considerado encerrado quando:

- houver pelo menos um backup recente
- um restore controlado tiver sido executado com evidencia
- o `RTO` observado estiver registrado

## Status de Aprovacao Formal

Estado atual: `ready_for_approval`

### Evidencias para Sign-off

- politica publicada com classes, prazos e regra minima de descarte
- owners de retention, recovery e cadeia de custodia nomeados
- scripts de `backup_postgres.sh` e `restore_postgres.sh` disponiveis
- evidencia recente de restore controlado em banco isolado com `RTO` observado e manifesto JSON anexado
- referencia cruzada com [ADR-008](adrs/ADR-008-retention-e-recovery-baseline.md)

### Aprovações Necessarias

| Papel | Responsabilidade de aceite | Status | Evidencia esperada |
| --- | --- | --- | --- |
| Security | validar classes de retention, cadeia de custodia e regra de descarte | `pending` | comentario de aceite ou decisao registrada |
| Compliance | validar retention arquivada, legal hold e compatibilidade regulatoria | `pending` | comentario de aceite ou decisao registrada |
| Platform/DBA | confirmar exequibilidade operacional de backup/restore | `ready` | restore controlado ja evidenciado |

### Registro de Aceite

| Papel | Responsavel | Data | Decisao | Observacoes |
| --- | --- | --- | --- | --- |
| Security | `pending` | `pending` | `pending` | validar prazos finais e excecoes |
| Compliance | `pending` | `pending` | `pending` | validar aderencia regulatoria por jurisdicao |
| Platform/DBA | `pending` | `pending` | `ready` | baseline tecnica publicada e restore evidenciado |

## Não Objetivos

- definir interpretacao juridica final por jurisdicao
- substituir vault corporativo ou politica oficial de SI
- cobrir backup fisico/WAL shipping de producao
