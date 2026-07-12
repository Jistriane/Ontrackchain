# Execucao por Evidencia — 2026-07-13

## Objetivo

Rascunho inicial para o proximo ciclo de subida de maturidade baseado em evidencia real, usando como referencia o [Kit de Execucao por Evidencia](../../../project-maturity-evidence-execution-kit.md).

Estado deste arquivo:

- rascunho
- sem execucao real registrada ainda
- accountable final da baseline ainda pendente de definicao formal

## Baseline de Referencia

- construcao tecnica: `92%`
- prontidao regulatoria/operacional: `79%`
- consolidado total: `88%`
- accountable oficial da baseline: `pendente de definicao`

## Escopo do Ciclo

- janela ou ciclo: `subida orientada por evidencia para 90%+`
- ambiente: `staging serio` ou equivalente homologado
- owner principal: `Arquitetura / Governanca`
- accountable: `pendente de definicao`
- consulted: `Compliance`, `Security/Auth`, `Platform/SRE`, `Ops`
- informed: `sponsors` e stakeholders do ciclo

## Plano D1-D7

| Dia | Frente | Meta objetiva | Owner | Gate de entrada | Artefato esperado | Semaforo final |
| --- | --- | --- | --- | --- | --- | --- |
| `D1` | preparar `P0-02` | validar credencial real do provider e ambiente alvo | `Backend/Compliance Lead` | credencial real disponivel | preflight externo + checklist de ambiente | `cinza` |
| `D2` | executar `P0-02` | provar `AML/KYT live` em runtime | `Backend/Compliance Lead` | `D1` verde | `check-compliance-provider-runtime` + artefato JSON | `cinza` |
| `D3` | executar `P0-03` | ativar feed UE real com persistencia valida | `Compliance/Ops Lead` | URL tokenizada real validada | JSONs da janela UE + check de sync | `cinza` |
| `D4` | consolidar `P0-02 + P0-03` | gerar bundle regulatorio revisavel; se apenas uma trilha estiver disponivel, registrar endurecimento parcial do dossier sem fechar `P0-04` | `Arquitetura + Compliance` | `D2` e `D3` com evidencia valida | bundle regulatorio + resumo executivo | `cinza` |
| `D5` | preparar `P0-01` | deixar OIDC serio pronto sem fallback `dev` | `Auth/Infra Lead` | IdP real e MFA disponiveis | bundle de readiness OIDC | `cinza` |
| `D6` | executar `P0-01` | provar login federado, MFA e enforcement | `Auth/Infra Lead` | `D5` verde | E2E critico + evidencia auditavel | `cinza` |
| `D7` | janela seria completa | emitir `go/no-go` formal | `Ops / Release Manager` | `D2`, `D3` e `D6` suficientemente fechados | dossier, sign-off e decisao formal | `cinza` |

## Registro Diario

### D1

- objetivo: validar insumos reais de `P0-02`
- comando principal: `python scripts/preflight_external_integrations.py`
- evidencia preservada: `pendente`
- bloqueadores: credencial do provider
- decisao do dia: `pendente`
- proximo gate: credencial validada

### D2

- objetivo: executar checker `AML/KYT live`
- comando principal: `make check-compliance-provider-runtime INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- evidencia preservada: `pendente`
- bloqueadores: dependencia de `D1`
- decisao do dia: `pendente`
- proximo gate: `ready=true` e `provider_status=live`

### D3

- objetivo: executar janela UE real
- comando principal: `make run-eu-sanctions-window-local WINDOW_ID=stg-$(date +%F)-eu`
- evidencia preservada: `pendente`
- bloqueadores: URL tokenizada real
- decisao do dia: `pendente`
- proximo gate: JSONs persistidos e status coerente

### D4

- objetivo: consolidar `P0-02` e `P0-03`
- comando principal: `make run-regulatory-readiness-bundle-local WINDOW_ID=stg-$(date +%F)-reg INTERNAL_BASE_URL=http://compliance-api:8002 PUBLIC_BASE_URL=http://localhost:8080`
- evidencia preservada: `pendente`
- bloqueadores: dependencia de `D2` e `D3`
- decisao do dia: `pendente`
- proximo gate: bundle revisavel por governanca
- observacao: se o ciclo cobrir apenas `P0-02` ou apenas `P0-03`, registrar explicitamente progresso parcial sem promover fechamento oficial de `P0-04`

### D5

- objetivo: preparar OIDC serio
- comando principal: `make run-oidc-readiness-bundle-local WINDOW_ID=stg-$(date +%F)-oidc BASE_URL=http://localhost:8080`
- evidencia preservada: `pendente`
- bloqueadores: IdP real e MFA homologado
- decisao do dia: `pendente`
- proximo gate: ambiente sem fallback `dev`

### D6

- objetivo: executar trilho OIDC/MFA
- comando principal: `cd apps/frontend && npm run test:e2e:oidc-critical`
- evidencia preservada: `pendente`
- bloqueadores: dependencia de `D5`
- decisao do dia: `pendente`
- proximo gate: prova completa de login + MFA + enforcement

### D7

- objetivo: converter evidencias em decisao formal
- comando principal: `make run-serious-window-local WINDOW_ID=stg-2026-07-13-a MODE=baseline`
- evidencia preservada: `pendente`
- bloqueadores: dependencia de `D2`, `D3` e `D6`
- decisao do dia: `pendente`
- proximo gate: dossier, sign-off e `go/no-go`

## Evidencias Revisadas

- artifact: `pendente`
- bundle: `pendente`
- teste/check: `pendente`
- sign-off: `pendente`
- runbook/janela: `pendente`

## Decisao de Scorecard

- houve promocao permitida? `nao`
- delta tecnico: `0`
- delta regulatorio/operacional: `0`
- delta consolidado: `0`
- justificativa: rascunho sem execucao real ainda; tentativa parcial futura deve ser registrada como progresso operacional, nao como fechamento oficial de `P0-04`

## Bloqueios e Escalacoes

- bloco: `P0-02`
  - motivo: credencial real ainda nao confirmada no ciclo
  - owner da escalacao: `Compliance Lead`
  - prazo: `preencher`

- bloco: `P0-01`
  - motivo: accountable final e trilho serio com IdP ainda pendentes
  - owner da escalacao: `Security/Auth Lead`
  - prazo: `preencher`

## Decisao Final do Ciclo

- status do ciclo: `pending`
- principal ganho: trilha de execucao ja preparada e alinhada ao scorecard
- principal risco residual: falta de accountable formal e insumos externos reais
- proxima evidencia esperada: primeiro artefato validado de `P0-02` ou `P0-03`
