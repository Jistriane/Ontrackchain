# Plano de Execucao para 90% de Maturidade

## Objetivo

Este arquivo e mantido por continuidade historica. O corte de `90%` tecnico ja foi ultrapassado, e o documento agora serve para consolidar o plano de sustentacao de `90%+` e empurrar a prontidao regulatoria.

## Baseline Atual

- `91%` de construcao tecnica
- `78%` de prontidao regulatoria
- `87%` de construcao total consolidada

Baseline oficial de referencia:

- [Scorecard Oficial do Projeto](./project-kpi-scorecard.md)
- [Atualizacao de KPI 2026-07-01](./governance-weekly/2026-07-01-kpi-scorecard-update.md)
- [Governanca Semanal 2026-07-01](./governance-weekly/2026-07-01-weekly-governance.md)

## Meta Atualizada

Sustentar `90%+` tecnico sem regressao e elevar a prontidao regulatoria para a proxima faixa de homologacao seria.

## Bloqueadores Atuais

1. MFA federado ainda nao homologado como trilho oficial serio
2. provider `AML/KYT` live ainda nao validado com credenciais reais
3. feed `EU_CONSOLIDATED` ainda depende de URL tokenizada real
4. sign-off institucional de retention/recovery ainda nao concluido

Observacao importante de baseline:

- a fila compartilhada multiusuario `regulatory_work_items` ja foi entregue para `sanctions` e `alerts`
- o gap de produto mudou para expansao dessa camada aos demais cockpits regulatorios, nao mais para ausencia total de handoff persistido no servidor

Leitura operacional atual:

- `P0-01` continua `blocked` ate existir evidencia externa e aceite institucional do trilho serio de identidade
- `P0-02` esta `ready` e depende de credenciais reais + `make check-compliance-provider-runtime` verde
- `P0-03` esta `ready` e depende de URL tokenizada valida + JSONs da janela UE anexados

## Ondas de Execucao Atualizadas

### Onda 1 - Homologacao Externa

Entregas:

- `OIDC` + MFA federado homologados
- provider `AML/KYT` live homologado com `check-compliance-provider-runtime` verde
- janela seria com dossier completo e bundle externo anexado

### Onda 2 - Fechamento de Sancoes

Entregas:

- URL tokenizada real da UE ativada
- `make run-eu-sanctions-window-local` verde com artefatos persistidos
- `check_sanctions_sync_status.py` verde com `EU_CONSOLIDATED`
- sustentacao do catalogo `sanctions_check` alinhado ao endpoint live

### Onda 3 - Governanca da Evidencia

Entregas:

- comentarios e inventario de eventos da `evidence_trail` alinhados
- timeline/comentarios de `work-items` expostos progressivamente nas UIs regulatorias
- sign-off formal de retention/recovery
- rotina recorrente de janela seria

### Onda 4 - Manual Review Estruturado

Entregas:

- artefatos e trilha operacional para `due_diligence` e `source_of_funds`
- bundles regulatorios complementares quando o caso exigir

## Backlog Prioritario

| ID | Iniciativa | Prioridade | Resultado Esperado |
| --- | --- | --- | --- |
| N90-01 | Homologar MFA federado serio | P0 | fechar risco de identidade |
| N90-02 | Homologar `AML/KYT` live | P0 | fechar maior gap funcional restante |
| N90-03 | Ativar feed UE tokenizado real | P0 | fechar janela de sancoes europeias |
| N90-04 | Sustentar catalogo `sanctions_check` alinhado | P1 | evitar regressao de contrato |
| N90-05 | Sustentar inventario da `evidence_trail` alinhado | P2 | evitar regressao documental/regulatoria |
| N90-06 | Expandir `work-items` para os cockpits regulatorios restantes | P1 | reduzir ilhas locais e fortalecer handoff multiusuario |
| N90-07 | Formalizar sign-off de retention/recovery | P1 | institucionalizar a cadeia de custodia |
| N90-08 | Estruturar manual review de DD/SoF | P1 | reduzir gap regulatorio residual |

## Criterio de Go/No-Go Atual

### Go

- modulo regulatorio principal permanece operacional
- screening local de sancoes e checker pos-sync estao verdes
- quando houver `AML/KYT live`, `check-compliance-provider-runtime` esta verde e anexado
- quando houver feed UE, `run-eu-sanctions-window-local` gera JSONs anexaveis
- janela seria gera dossier consistente
- riscos abertos estao explicitamente registrados e aceitos

### No-Go

- feed UE exigido sem URL tokenizada valida
- MFA serio ausente nos fluxos sensiveis da janela
- `AML/KYT live` exigido sem homologacao real
- contradicao de runtime nao registrada em docs ou risco

## Decisao Recomendada

O plano mais eficiente nao e abrir novas features grandes. E:

1. homologar o que ja existe
2. alinhar contratos/documentacao onde ainda ha drift
3. institucionalizar o rito serio com prova auditavel recorrente
