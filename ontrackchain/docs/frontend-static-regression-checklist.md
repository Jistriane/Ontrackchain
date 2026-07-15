# Checklist Canonico de Regressao Estatica e Contratos Visuais do Frontend

## Objetivo

Fornecer um checklist operacional curto e repetivel para validar mudancas em labels, datas, contexto regulatorio, pills semanticos, `data-testid` e deep-links dos cockpits principais sem depender de execucao runtime arriscada durante a iteracao.

Este documento passa a ser a fonte canonica unica para:

- regressao estatica de contratos visuais
- gate curto de rollout seguro
- criterio de `go/no-go` para mudancas visuais protegidas

## Quando Usar

- mudancas em cockpits listados em `./frontend-static-regression-traceability.md`
- mudancas em `data-testid` usados por specs focais
- mudancas em formatacao visual de datas, timestamps e hashes
- mudancas em labels de i18n usadas como contrato operator-facing
- mudancas em deep-links entre cockpits regulatorios, operacionais ou administrativos

## Pre-Flight

- confirmar qual cockpit foi alterado
- localizar a spec focal correspondente em `./frontend-static-regression-traceability.md`
- identificar se a mudanca toca:
  - labels i18n
  - datas/timestamps
  - `data-testid`
  - deep-links
  - hash/contexto regulatorio
  - pills ou badges semanticos

## Checklist Geral

- validar que novos `data-testid` sao minimos, estaveis e semanticamente uteis
- validar que datas e timestamps nao vazam ISO cru quando a superficie e visual
- validar que labels user-facing usam i18n e nao string tecnica inline sem necessidade
- validar que deep-links preservam o contexto operacional esperado (`case_id`, `report_id`, `ros_id`, `address`, `chain`)
- validar que badges e pills mantem mapeamento consistente de label e tone
- validar que a spec focal correspondente foi atualizada ou explicitamente revisada
- validar que a documentacao foi sincronizada quando o contrato visual mudou

## Gate de Rollout

- [ ] identificar o cockpit e a spec canonica impactada
- [ ] validar que os `data-testid` alterados continuam minimos e semanticamente orientados
- [ ] validar que datas/timestamps protegidos nao regressaram para ISO cru
- [ ] validar que labels semanticas continuam coerentes com `i18n.ts`
- [ ] validar que deep-links preservam o contexto esperado (`case_id`, `report_id`, `ros_id`, `address`, `chain`)
- [ ] validar que a spec focal correspondente foi atualizada ou explicitamente revisada
- [ ] validar que `frontend-coverage-matrix.md` foi sincronizado
- [ ] validar que `frontend-static-regression-traceability.md` foi sincronizado
- [ ] validar que os diagnosticos dos arquivos tocados permanecem limpos

## Checklist por Dominio

### Regulatorio

- `audit`: confirmar precedencia de `dossier_sha256` sobre `file_hash_sha256`
- `ros-coaf`: confirmar `priority/source/SLA/phase` no workspace e historico
- `evidence`: confirmar hash principal, contexto do dossie e datas da cadeia
- `reports`: confirmar `priority/source/SLA` e deadline visual do workspace

### Operacional

- `counterparties`: confirmar `source`, revisao DD/SoF, `status` e deadline
- `sanctions`: confirmar `source`, `status`, `urgency` e deadline
- `blocks`: confirmar `source`, `status`, `urgency` e deadline
- `alerts`: confirmar `severity/status/triage`, fila rastreada e timestamps visiveis
- `dashboard`: confirmar links contextuais, `status` e datas dos casos recentes

### Administrativo

- `team`: confirmar label de role, `status` e `updated_at`
- `billing`: confirmar reconciliacao, export e handoff para `team` sem projeção lateral de roster

## Documentacao Obrigatoria

- atualizar `./frontend-coverage-matrix.md` se a superficie funcional/cobertura mudou
- atualizar `./frontend-static-regression-traceability.md` se a spec canonica ou o contrato protegido mudou
- refletir qualquer mudanca material no indice canonico `./README.md` quando a trilha de regressao estatica ganhar ou perder escopo oficial
- atualizar `./evidence-manual-package-rollout-checklist.md` quando a mudanca tocar manifesto, export manual, navegação `evidence <-> audit` ou handoff DD/SoF

## Evidencias Minimas

- [ ] diff final revisado nos arquivos do cockpit
- [ ] diff final revisado na spec focal
- [ ] docs sincronizadas
- [ ] diagnosticos limpos dos arquivos tocados

## Go / No-Go

### Go

- [ ] contrato visual protegido continua coberto por spec
- [ ] documentacao canonica foi sincronizada
- [ ] nao ha diagnosticos introduzidos pela rodada

### No-Go

- [ ] spec focal quebrada ou desatualizada
- [ ] `data-testid` removido sem reposicao equivalente
- [ ] regressao de ISO cru em superficie visual
- [ ] deep-link perdeu contexto necessario

## Encerramento Seguro

- rodar diagnosticos dos arquivos tocados
- reler os trechos alterados para garantir coerencia entre implementacao, spec e documentacao
- registrar no handoff final:
  - cockpit afetado
  - contrato protegido
  - spec atualizada
  - documentacao sincronizada
