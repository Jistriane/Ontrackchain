# Governança Semanal Operacional — 2026-07-13

## Objetivo

Conduzir a revisao semanal de forma curta, orientada a evidencia, usando como baseline o estado consolidado ate `2026-07-06` e os gatilhos legitimos definidos no plano de continuidade.

Referencias de apoio:

- [Plano Consolidado de Continuidade e Execucao](../../../history/CONTINUATION_EXECUTION_PLAN_2026_07.md)
- [Governança Semanal 2026-07-06](../2026-07-06/2026-07-06-weekly-governance.md)
- [Rascunho da Governança Semanal 2026-07-13](./2026-07-13-weekly-governance-draft.md)

## Baseline de Referencia

- construcao tecnica: `91%`
- prontidao regulatoria: `78%`
- KPI consolidado: `87%`
- houve evidencia nova material?: `nao`, salvo checker, bundle, dossie ou sign-off novo revisavel no proprio encontro

## Decisao Executiva Rapida

- decisao da semana: `manter baseline`, salvo evidencia nova material apresentada no encontro
- principal ganho: `artifact validation` da janela segue `ok` e a trilha documental/operacional continua consistente
- principal bloqueio: `12` placeholders + `8` campos de handoff ainda pendentes, somados a credenciais externas nao homologadas
- item mais proximo de fechamento: `P0-02`, se a credencial real do provider AML/KYT chegar com checker verde
- item que exige escalacao externa: `P0-01`, por depender de provider OIDC serio e aceite institucional

## Snapshot dos Itens Criticos

| Bloco | Status atual | Ultima evidencia revisada | Bloqueio atual | Proxima acao verificavel | Data alvo | Semaforo |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-02` `AML/KYT live` | `ready` salvo nova evidencia | gate `check-compliance-provider-runtime` documentado | credencial real do provider ainda pendente | executar checker com credencial real e persistir JSON | `2026-07-08` | `amarelo` |
| `P0-03` feed UE real | `ready` salvo nova evidencia | runner `run-eu-sanctions-window-local` documentado | URL tokenizada real ainda pendente | executar janela UE e anexar JSONs de preflight/sync | `2026-07-08` | `amarelo` |
| `P0-01` `OIDC + MFA` serio | `blocked` salvo nova evidencia | nenhum bundle serio final revisado | provider OIDC serio e aceite institucional pendentes | rodar preflight + smoke + bundle OIDC com provider real | `2026-07-15` | `vermelho` |
| `RUN-STG-01` primeira janela seria | `pending_execucao` salvo artifact novo | war room, tracking e sign-off da janela `stg-2026-07-06-a` publicados | janela ainda depende de sair de `no-go` | revisar unblock checklist, preencher folha manual e disparar workflow so com `go` ou `go_with_exception` | `2026-07-15` | `amarelo` |
| ownership/SLA | `in_progress` com aceite pendente | matriz de owners, SLA base e runbooks publicados | aceite formal de Platform/SRE e Security pendente | registrar decisao escrita e fechar drill | `2026-07-15` | `amarelo` |
| retention/recovery | `in_progress` com baseline pronta | politica publicada e restore baseline tratado como pronto tecnicamente | sign-off formal de Security e Compliance pendente | registrar RTO/RPO, revisar restore e colher aceite formal | `2026-07-18` | `amarelo` |

## Regras de Passagem

- usar `blocked` quando a dependencia externa ou institucional impedir execucao real
- usar `ready` quando o gate existir, mas ainda faltar insumo real
- usar `in_progress` apenas quando houver execucao real em curso
- usar `ready_for_validation` quando a prova existir, mas ainda faltar revisao formal
- usar `done` apenas com artefato revisavel, aceite correspondente e documentacao sincronizada

## Checklist de Encerramento do Encontro

- [x] itens `blocked` explicitamente marcados
- [ ] paths dos artefatos relevantes registrados
- [x] proxima evidencia esperada anotada por item critico
- [x] decisao executiva da semana registrada
- [x] owner de escalacao definido para cada bloqueio que permaneceu

## Escalacoes Necessarias

- bloco: `P0-01`
  - motivo: provider OIDC serio e aceite institucional ainda ausentes
  - owner da escalacao: `Security/Auth`
  - prazo: `2026-07-15`

- bloco: `P0-02`
  - motivo: credencial AML/KYT real ainda nao anexada
  - owner da escalacao: `Compliance/AML`
  - prazo: `2026-07-08`

- bloco: `P0-03`
  - motivo: URL tokenizada do feed UE ainda nao confirmada
  - owner da escalacao: `Compliance/Backend`
  - prazo: `2026-07-08`

- bloco: `RUN-STG-01`
  - motivo: janela ainda nao saiu de `no-go`
  - owner da escalacao: `Release Manager Tecnico`
  - prazo: `2026-07-15`

## Proxima Revisao

- data: `2026-07-20`, ou antes se surgir artifact novo revisavel
- gatilho legitimo esperado: `artifact novo de P0-01, P0-02, P0-03 ou RUN-STG-01`, com delta negativo real em bloqueios ou aceite formal
- artefato esperado: `checker, bundle, dossie, sign-off ou workflow artifact revisavel`
