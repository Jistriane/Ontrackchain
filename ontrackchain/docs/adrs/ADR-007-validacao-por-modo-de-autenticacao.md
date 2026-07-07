# ADR-007 — Validacao por Modo de Autenticacao

## Contexto

O projeto passou a operar com dois modos de autenticacao explicitamente distintos:

- `oidc`, que representa o caminho canonico para ambientes serios
- `dev`, que preserva o scaffold local com `TOTP` e emissao de `dev_jwt`

Durante o endurecimento de `OIDC`, identidade federada e `legal_report`, a suite E2E revelou dois riscos diferentes:

- o modo `oidc` concentra os controles obrigatorios para staging e producao
- o modo `dev` continua relevante para o scaffold local, mas nao deve contaminar os gates de promocao de ambiente serio

Antes desta decisao, o pipeline executava Playwright de forma unica, sem separar:

- validacao canonica de `OIDC` + `RBAC` + identidade federada
- validacao legada/local de `2FA` e `dev_jwt`

Isso dificultava interpretar falhas e misturava regras de seguranca com semanticas diferentes.

## Decisao

Adotar uma estrategia de validacao em dois trilhos no CI/CD:

- um gate `OIDC` explicito e prioritario para os fluxos canonicos de ambiente serio
- um job separado de `dev auth` para preservar cobertura do scaffold local com `TOTP`

Mapeamento aprovado:

- `npm run test:e2e:oidc-critical`
  - cobre `oidc-auth.spec.ts`
  - cobre `compliance-flows.spec.ts`
  - protege `OIDC`, `RBAC`, identidade federada e `legal_report`
- `npm run test:e2e:dev-auth`
  - cobre o teste local de `2FA` em `compliance-flows.spec.ts`
  - falha cedo se o ambiente nao estiver em `AUTH_MODE=dev`
  - valida apenas o modo `AUTH_MODE=dev`

No pipeline:

- o gate `OIDC` continua sendo parte obrigatoria da validacao para ambiente serio
- o job `dev auth` existe como regressao controlada do scaffold local

## Motivacao

- separar claramente autenticacao canonica de autenticacao local de compatibilidade
- evitar falso bloqueio de promocao por testes que pertencem apenas ao scaffold `dev`
- manter cobertura do `TOTP` local sem afrouxar o endurecimento de `OIDC`
- tornar as evidencias de release mais legiveis para auth, compliance e operacao

## Alternativas Consideradas

### Opcao A — Um unico job Playwright para tudo

- Vantagem:
  - configuracao mais simples
- Desvantagem:
  - mistura semanticas de seguranca diferentes
  - dificulta diagnostico quando o problema e apenas do scaffold `dev`
  - obscurece quais testes realmente bloqueiam promocao para ambiente serio

### Opcao B — Remover completamente os testes de `dev auth`

- Vantagem:
  - reduz tempo e complexidade do CI
- Desvantagem:
  - perde regressao do scaffold local
  - deixa sem cobertura o fluxo legado de `TOTP`
  - aumenta risco de drift silencioso no modo `dev`

### Opcao C — Separar gate `OIDC` e job `dev auth`

- Vantagem:
  - preserva cobertura sem misturar contextos
  - alinha o CI com a politica arquitetural do projeto
  - deixa explicito o que bloqueia promocao e o que e apenas regressao local
- Desvantagem:
  - aumenta custo de manutencao do pipeline
  - exige documentacao clara para evitar uso incorreto do job local como criterio de release

## Recomendacao

Escolher a `Opcao C`.

Ela oferece o melhor equilibrio entre:

- seguranca
- governanca operacional
- rastreabilidade de release
- preservacao do scaffold local

## Consequencias

- o time passa a tratar `OIDC` como gate principal de autenticacao em CI
- o fluxo `dev` deixa de ser criterio de promocao para staging/producao
- bugs do scaffold local continuam detectaveis sem poluir a leitura do gate serio
- runbooks e documentos de deploy precisam explicitar quando usar cada suite

## Trade-offs Aceitos

- mais tempo de pipeline em troca de evidencias mais claras por modo de autenticacao
- coexistencia temporaria de duas estrategias de auth validas, mas com pesos diferentes para release

## Status

- Aceito e implementado
