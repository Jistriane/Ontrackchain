# Ciclo Semanal de Governanca — 2026-07-23

## Resumo Executivo

Ciclo focado em consolidacao de P2-05 (RBAC), P2-01 (modulo team) e P2-04 (vault/secrets). Todos os itens P2 estao concluidos. Projeto atinge 93% de construcao tecnica com 80/80 testes E2E passando.

## Itens Concluidos Neste Ciclo

### P2-05 — RBAC (done)
- Enforcement completo em todos os dominios (compliance, reports, evidence, billing, monitoring, team)
- `canDownloadLegalReport` corrigido para verificar role + auth method + MFA
- `auth/context` route corrigida para usar X-Role do auth-service
- `roleByEmail` em session/start corrigido para mapeamento correto por papel
- 80/80 testes E2E passando
- Documentacao sincronizada

### P2-01 — Modulo Team (done)
- ADR-015 criado com definicao de escopo e evolucao incremental
- Modulo team consolidado como cockpit unico de gestao de identidade

### P2-04 — Vault/Secrets (done)
- ADR-016 criado com estrategia em 3 camadas (producao, staging, desenvolvimento)
- Mapeamento de segredos documentado
- Nomenclatura padrao definida

### Testes Enterprise-Compliance
- Nova suíte com 5 testes para modulos P4-P7
- Cobertura completa para Bridge/Mixer Risk, Auto-Filing COAF, Travel Rule e AI Legal Dossier

## Metricas do Ciclo

| Metrica | Valor |
|---------|-------|
| Testes browser-mocked | 80/80 |
| Testes enterprise-compliance | 5/5 |
| Typecheck | Passando |
| P2-05 | done |
| P2-01 | done |
| P2-04 | done |

## Proximos Passos

### Now
- P1-02: Converter capacidade tecnica em evidencia operacional recorrente
- P0-07: Publicar nova baseline oficial

### Next
- P0-05: Executar primeira janela seria material
- P0-06: Formalizar sign-off de retention/recovery
- P2-06: Executar segunda janela seria comparavel
- P2-07: Atualizar o plano para 95%

## Evidencias

- 80/80 testes browser-mocked passando
- 5/5 testes enterprise-compliance passando
- Typecheck passando
- ADR-015 e ADR-016 criados
- Todos os P2 concluidos

## Decisoes

- P2-05 concluido: enforcement completo de RBAC em todos os dominios
- P2-01 concluido: ADR-015 define futuro do modulo team
- P2-04 concluido: ADR-016 define estrategia de vault/secrets

## Acoes da Proxima Semana

1. Concluir P1-02 (evidencia operacional recorrente)
2. Atualizar baseline oficial (P0-07)
3. Preparar para proxima janela seria (P2-06)
