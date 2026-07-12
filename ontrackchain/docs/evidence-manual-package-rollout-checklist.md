# Checklist de Rollout do Pacote Manual DD/SoF

## Objetivo

Definir um gate operacional curto para a trilha manual de `due_diligence` e `source_of_funds`, cobrindo:

- contrato `manual_review_pending` no cockpit `/evidence`
- evento oficial `evidence_manual_review_package_exported` em `audit_logs`
- manifesto canônico SHA-256 do pacote manual
- leitura canônica do selo por `package_sha256`
- escrita controlada de `signoff-request`, `signoff`, `finalize`, `revoke` e `supersede`
- navegacao bidirecional `evidence <-> audit`, incluindo preset de governanca por `seal_id`
- handoff operacional do workspace correlacionado

Use este checklist junto com:

- `./frontend-static-regression-checklist.md`
- `./frontend-visual-contract-rollout-checklist.md`
- `./frontend-static-regression-traceability.md`
- `./evidence-and-audit-matrix.md`

## Quando Usar

- mudanças em `apps/frontend/app/evidence/page.tsx`
- mudanças em `apps/frontend/app/audit/page.tsx`
- mudanças em `apps/frontend/app/lib/evidence-manual-package.ts`
- mudanças em `apps/frontend/app/lib/manual-package-seal.ts`
- mudanças em labels de i18n da trilha manual DD/SoF
- mudanças no endpoint `/api/app/evidence/manual-package`
- mudanças nos endpoints `/api/app/evidence/manual-package/seal`, `/signoff-requests` ou `/seals/*`
- mudanças nos eventos `evidence_manual_review_package_exported`, `*_signoff_*`, `*_sealed`, `*_seal_revoked`, `*_seal_superseded`

## Pré-Flight

- [ ] confirmar se a mudança toca DD, SoF ou ambos
- [ ] localizar as specs focais da trilha:
  - `../apps/frontend/tests/e2e/evidence-custody.spec.ts`
  - `../apps/frontend/tests/e2e/audit-labels.spec.ts`
- [ ] confirmar quais chaves de contexto são obrigatórias no escopo:
  - `request_id`
  - `report_id` quando existir
  - `scope_id`
  - `manual_review_action`
  - `package_sha256`
  - `filename`

## Gate Funcional

- [ ] `evidence` continua resolvendo corretamente o domínio `due_diligence` ou `source_of_funds`
- [ ] o painel manual em `evidence` continua exibindo `workflow`, `access policy`, `sign-off`, `custody` e `anchor`
- [ ] o pacote manual continua exportável a partir do detalhe da evidência
- [ ] o manifesto canônico continua expondo `payload_sha256`, `scope_sha256`, `manual_review_sha256` e `dossier_sha256`
- [ ] o evento `evidence_manual_review_package_exported` continua sendo emitido com `request_id`, `scope_id`, `manual_review_action`, `filename` e `package_sha256`
- [ ] a leitura read-only do selo continua resolvida via `package_sha256` (`by-digest`) no cockpit `evidence`
- [ ] o painel de selagem continua exibindo `seal_status`, quorum, `seal_id`, `signature_algorithm`, `certificate_bundle_ref` e `verification_summary`
- [ ] a inicializacao da trilha institucional continua criando/reaproveitando `seal_id` e emitindo `evidence_manual_review_package_signoff_requested`
- [ ] o registro de sign-off continua respeitando quorum `Compliance + Ops` e transicao para `ready_to_seal`
- [ ] o `finalize` continua restrito a `ready_to_seal` e persiste `seal_envelope` + `verification_summary`
- [ ] revogacao e supersedencia continuam exigindo `ticket_ref` + `reason`
- [ ] o detalhe do `audit` continua exibindo `package_sha256` como hash principal quando o evento manual estiver selecionado
- [ ] o preset manual do `audit` continua agrupando a familia `export -> signoff -> seal -> revoke/supersede` por `request_id`
- [ ] o preset `governanca` do `audit` continua aceitando `request_id` ou `seal_id`

## Gate de Navegação

- [ ] `evidence` continua expondo deep-link explícito para o preset manual do `audit`
- [ ] `evidence` continua expondo deep-link explícito para a governanca do selo no `audit` por `seal_id`
- [ ] `audit` continua expondo retorno explícito ao evento-fonte DD/SoF em `evidence`
- [ ] o retorno `audit -> evidence` continua carregando `audit_origin=manual_package`
- [ ] o banner contextual de retorno em `evidence` continua visível quando a origem for `audit`
- [ ] o CTA do banner continua retornando ao preset manual do `audit`

## Gate de Contrato Visual

- [ ] `data-testid` mínimos permanecem estáveis nos blocos:
  - `evidence-manual-package-panel`
  - `evidence-manual-package-open-audit-preset`
  - `evidence-manual-package-open-audit-governance`
  - `evidence-manual-package-seal-panel`
  - `evidence-manual-package-finalize`
  - `evidence-manual-package-revoke-panel`
  - `evidence-manual-package-supersede-panel`
  - `evidence-audit-return-banner`
  - `audit-manual-package-detail-context`
  - `audit-manual-package-detail-open-evidence-source`
  - `audit-manual-open-evidence`
  - `audit-governance-preset-notice`
  - `audit-governance-open-evidence`
- [ ] timestamps continuam sem ISO cru nas superfícies visuais protegidas
- [ ] labels user-facing continuam saindo de `i18n.ts`
- [ ] labels de ação manual continuam coerentes com `compliance_due_diligence_checked` e `compliance_source_of_funds_checked`

## Evidências Mínimas

- [ ] diff revisado em `evidence/page.tsx`
- [ ] diff revisado em `audit/page.tsx`
- [ ] diff revisado em `evidence-manual-package.ts` quando houver mudança de payload/manifesto
- [ ] `evidence-custody.spec.ts` atualizado ou explicitamente revalidado
- [ ] `audit-labels.spec.ts` atualizado ou explicitamente revalidado
- [ ] `api-contracts.md` sincronizado quando o contrato HTTP da selagem mudar
- [ ] `frontend-coverage-matrix.md` sincronizado
- [ ] `frontend-static-regression-traceability.md` sincronizado
- [ ] `evidence-and-audit-matrix.md` sincronizado quando o contrato de correlação mudar

## Validação Técnica

- [ ] diagnósticos limpos nos arquivos alterados
- [ ] `npm run typecheck` validado com `.next/types` materializado
- [ ] `npx playwright test evidence-custody.spec.ts --reporter=line` verde
- [ ] `npx playwright test audit-labels.spec.ts --reporter=line` verde

## Go / No-Go

### Go

- [ ] manifesto, evento auditável e navegação bidirecional permanecem coerentes
- [ ] contrato canônico de leitura continua preferindo `by-digest`
- [ ] trilha de governanca do selo continua consistente entre `evidence`, `audit` e `api-contracts.md`
- [ ] specs focais da trilha manual estão verdes
- [ ] documentação canônica foi sincronizada

### No-Go

- [ ] `package_sha256` deixou de ser o hash principal no `audit`
- [ ] o evento oficial de export manual perdeu `request_id`, `scope_id` ou `manual_review_action`
- [ ] a leitura de selagem voltou a depender de `seal_id` no frontend como contrato primario
- [ ] o retorno `audit -> evidence` caiu para o evento de export em vez do evento-fonte DD/SoF
- [ ] o banner contextual do retorno desapareceu ou ficou incoerente
- [ ] a governanca pós-selagem perdeu `ticket_ref`, `reason` ou o vínculo para o selo substituto
- [ ] a trilha manual voltou a depender de strings inline ou de ISO cru na UI
