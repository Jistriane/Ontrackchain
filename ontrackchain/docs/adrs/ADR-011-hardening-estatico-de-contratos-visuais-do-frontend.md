# ADR-011: Hardening Estatico de Contratos Visuais do Frontend

## Contexto

O frontend do Ontrackchain passou a concentrar uma superficie ampla de cockpits:

- regulatorios: `audit`, `ros-coaf`, `evidence`, `reports`
- operacionais: `counterparties`, `sanctions`, `blocks`, `alerts`, `dashboard`
- administrativos: `team`, `billing`

Antes desta trilha, a maior parte desses cockpits ja possuia comportamento funcional relevante, mas ainda havia risco operacional alto de regressao silenciosa em:

- labels e pills semanticos
- datas e timestamps exibidos ao operador
- deep-links contextuais entre cockpits
- precedencia de contexto regulatorio (`dossier_sha256` vs `file_hash_sha256`)
- consistencia visual entre workspace, historico e detalhe

O problema principal nao era falta de feature, e sim falta de testabilidade estatica consistente e de rastreabilidade clara entre cockpit, spec E2E e contrato visual protegido.

## Decisao

Adotar `hardening estatico` como baseline canonico para os contratos visuais sensiveis do frontend, com os seguintes pilares:

1. adicionar `data-testid` minimos, estaveis e semanticamente orientados apenas nas superficies de maior risco operacional;
2. padronizar helpers locais para datas, timestamps, badges e pills quando a superficie visual estiver sujeita a drift;
3. endurecer specs E2E focais por cockpit, evitando suites novas quando um spec existente puder ser reaproveitado com baixo acoplamento;
4. manter rastreabilidade documental explicita entre cockpit, spec canonica e contrato protegido;
5. exigir sincronizacao da documentacao toda vez que um contrato visual protegido for alterado.

## Consequencias

### Positivas

- reduz regressao silenciosa de UX regulatoria e operacional
- melhora a capacidade de handoff entre implementacao, spec e documentacao
- diminui dependencias de verificacao manual para contratos visuais recorrentes
- reforca consistencia entre cockpits relacionados sem exigir refatoracao estrutural ampla

### Negativas

- aumenta a disciplina necessaria para manter `data-testid` e specs sincronizados
- adiciona custo documental em mudancas pequenas de UX
- pode expor duplicacoes visuais antigas ao endurecer contratos antes implícitos

## Trade-offs

- foi priorizado `baixo risco + alta rastreabilidade` sobre refatoracao massiva de componentes compartilhados
- foi preferido ampliar specs focais existentes em vez de criar uma suite por cockpit quando o reaproveitamento era seguro
- foi aceito manter helpers locais por cockpit para reduzir acoplamento prematuro, desde que a semantica permanecesse alinhada

## Criterios de Aceitacao

- cada cockpit critico possui ao menos uma spec focal cobrindo seu contrato visual mais sensivel
- datas e timestamps sensiveis nao aparecem em ISO cru nas superficies operator-facing cobertas
- contextos regulatorios compartilhados possuem precedencia e semantica documentadas
- `frontend-coverage-matrix.md` e `frontend-static-regression-traceability.md` refletem o estado real da cobertura
- existe um checklist repetivel para futuras mudancas de contratos visuais
