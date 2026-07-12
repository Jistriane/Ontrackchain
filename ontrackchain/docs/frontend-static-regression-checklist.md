# Checklist de Regressao Estatica do Frontend

## Objetivo

Fornecer um checklist operacional curto e repetivel para validar mudancas em labels, datas, contexto regulatorio, pills semanticos e deep-links dos cockpits principais sem depender de execucao runtime arriscada durante a iteracao.

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
- validar que a documentacao foi sincronizada quando o contrato visual mudou

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
- `billing`: confirmar `status` amigavel, `updated_at` e deep-link para `team`

## Documentacao Obrigatoria

- atualizar `./frontend-coverage-matrix.md` se a superficie funcional/cobertura mudou
- atualizar `./frontend-static-regression-traceability.md` se a spec canonica ou o contrato protegido mudou
- refletir qualquer mudanca material no indice canonico `./README.md` quando a trilha de regressao estatica ganhar ou perder escopo oficial
- atualizar `./frontend-visual-contract-rollout-checklist.md` se o gate de rollout do contrato visual mudou
- atualizar `./evidence-manual-package-rollout-checklist.md` quando a mudanca tocar manifesto, export manual, navegação `evidence <-> audit` ou handoff DD/SoF

## Encerramento Seguro

- rodar diagnosticos dos arquivos tocados
- reler os trechos alterados para garantir coerencia entre implementacao, spec e documentacao
- registrar no handoff final:
  - cockpit afetado
  - contrato protegido
  - spec atualizada
  - documentacao sincronizada
