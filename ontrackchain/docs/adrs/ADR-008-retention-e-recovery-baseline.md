# ADR-008: Retention e Recovery Baseline

## Contexto

O Ontrackchain ja possui trilha auditavel relevante em `audit_logs`, eventos administrativos em `operational_alert_events`, billing reconciliavel e evidencias correlacionadas por `request_id`.

Mesmo assim, a prontidao regulatoria continua travada porque faltam:

- retention minima formal para auditoria e evidencias
- owner claro para descarte e legal hold
- caminho operacional de backup/restore reproduzivel

## Decisao

Adotar uma baseline de retention e recovery publicada em [retention-and-recovery-policy.md](../retention-and-recovery-policy.md), com os seguintes principios:

- `audit_logs` e evidencias regulatorias entram em classe critica
- a politica define retention online, retention arquivada e regra de descarte
- backup logico do PostgreSQL passa a ter caminho operacional padronizado
- restore minimo deve ocorrer em banco separado do principal

## Consequencias

### Positivas

- reduz o gap de governanca que ainda segura a jornada de staging serio
- cria base concreta para `P1-02` e `P1-03`
- melhora cadeia de custodia e disciplina de descarte

### Negativas

- aumenta trabalho operacional para evidenciar restore periodico
- ainda depende de aprovacao formal de Security/Compliance para encerrar `P1-01`

## Trade-offs

- foi priorizada uma politica baseline viavel agora, em vez de esperar uma politica corporativa perfeita
- o restore baseline usa dump logico e banco isolado; isso e suficiente para provar caminho minimo, mas nao substitui estrategia completa de producao
