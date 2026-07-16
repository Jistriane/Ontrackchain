# ADR-013: Digest Canonico do Export no Showcase E2E

## Contexto

O fluxo standalone de `evidence` para pacotes manuais DD/SoF ja possui:

- export via `POST /api/app/evidence/manual-package`
- `package_sha256` emitido no header `x-ontrack-manual-package-sha256`
- renderizacao do hash no painel visual de `evidence`
- selagem posterior via `signoff-request`, `signoff` e `finalize`

O gap residual identificado na suite segmentada nao era mais de backend nem de persistencia principal. O problema passou a ser sincronizacao entre:

- o hash canonico emitido imediatamente pela resposta HTTP do export
- o hash ainda renderizado no DOM logo apos o clique de export

Em algumas execucoes, o helper Playwright lia um `package_sha256` antigo no painel antes da convergencia do estado React, criava o fluxo de selagem para esse hash stale e, em seguida, a UI reabria mostrando o hash novo. O resultado era um desencontro aparente entre pacote exibido e selo persistido.

## Decisao

Adotar como baseline para o showcase E2E a `Opcao B`: tratar a resposta do export como fonte canonica imediata do digest e usar o DOM apenas como confirmacao de convergencia visual.

Na pratica:

1. o helper deve capturar o `x-ontrack-manual-package-sha256` diretamente da resposta de `POST /api/app/evidence/manual-package`;
2. o fluxo de `signoff-request` e `finalize` deve usar esse digest canonico, nao o primeiro texto disponivel no DOM;
3. o teste deve aguardar a UI renderizar o mesmo hash antes de seguir, preservando validacao visual sem depender de estado transitorio;
4. o contrato HTTP continua sendo a fonte primaria de verdade para correlacao de pacote no momento do export;
5. o DOM permanece relevante como superficie de verificacao, mas nao como autoridade inicial de correlacao.

## Consequencias

### Positivas

- elimina falso negativo causado por leitura de estado stale no frontend
- alinha o helper E2E ao contrato canonico do proprio endpoint de export
- reduz flakiness em fluxos com reconciliacao assincrona de estado
- preserva a verificacao visual sem sacrificar determinismo operacional

### Negativas

- aumenta o acoplamento do helper ao header HTTP do endpoint de export
- exige disciplina para manter header e painel visual semanticamente alinhados
- explicita que a UI pode ter uma pequena janela de convergencia apos o export

## Trade-offs

- foi priorizado `determinismo do contrato + baixa flakiness` sobre a simplicidade de ler apenas o DOM
- foi evitada mudanca estrutural no frontend de producao, porque o problema residia no ponto de observacao do teste
- foi aceita dependencia controlada do header HTTP, pois ele ja representa o artefato canonico emitido pelo backend

## Criterios de Aceitacao

- o helper E2E captura o digest canonico da resposta de export
- o fluxo de selagem usa o mesmo digest retornado pelo endpoint
- a UI e aguardada ate refletir o mesmo hash antes da continuidade do teste
- `showcase-evidence.spec.ts` passa de forma deterministica no modo standalone
- a suite publica segmentada do showcase permanece verde apos a mudanca
