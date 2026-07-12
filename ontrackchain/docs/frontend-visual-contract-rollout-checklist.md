# Checklist de Rollout para Contratos Visuais do Frontend

## Objetivo

Consolidar um gate curto de rollout para mudancas que alterem contratos visuais protegidos do frontend, especialmente quando a mudanca tocar labels, datas, contexto regulatorio, badges semanticos ou deep-links entre cockpits.

## Quando Usar

- mudancas em cockpits listados em `./frontend-static-regression-traceability.md`
- mudancas em `data-testid` usados por specs focais
- mudancas em formatacao visual de datas, timestamps e hashes
- mudancas em labels de i18n usadas como contrato operator-facing
- mudancas em deep-links entre cockpits regulatorios, operacionais ou administrativos

## Gate de Rollout

- [ ] identificar o cockpit e a spec canonica impactada
- [ ] validar que os `data-testid` alterados continuam minimos e semanticamente orientados
- [ ] validar que datas/timestamps protegidos nao regressaram para ISO cru
- [ ] validar que labels semanticas continuam coerentes com `i18n.ts`
- [ ] validar que deep-links preservam o contexto esperado (`case_id`, `report_id`, `ros_id`, `address`, `chain`)
- [ ] validar que a spec focal correspondente foi atualizada ou explicitamente revisada
- [ ] validar que `frontend-coverage-matrix.md` foi sincronizado
- [ ] validar que `frontend-static-regression-traceability.md` foi sincronizado
- [ ] validar que `frontend-static-regression-checklist.md` continua consistente

## Gate por Dominio

### Regulatorio

- [ ] `audit`: hash principal, preset de dossie e atalhos `reports/ros-coaf`
- [ ] `ros-coaf`: workspace, historico, `SLA` e contexto do dossie
- [ ] `evidence`: hash principal, cadeia contextual e dossie exportado
- [ ] `reports`: workspace semantico e handoff para `ros-coaf`

### Operacional

- [ ] `counterparties`: revisao DD/SoF e deadline
- [ ] `sanctions`: `status`, `urgency` e deadline
- [ ] `blocks`: `status`, `urgency` e deadline
- [ ] `alerts`: `severity/status/triage`, fila rastreada e timestamps
- [ ] `dashboard`: casos recentes e links contextuais

### Administrativo

- [ ] `team`: role, `status` e `updated_at`
- [ ] `billing`: roster filtrado, `status`, `updated_at` e deep-link para `team`

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
