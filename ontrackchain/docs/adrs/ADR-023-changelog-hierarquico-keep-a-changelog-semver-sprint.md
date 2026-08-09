# ADR-023 — CHANGELOG Oficial Hierárquico por Sprint com Keep a Changelog 1.1.0 + SemVer 2.0.0

- **Status**: Aprovado e implementado na Sprint 22
- **Decisores**: Arquiteto de Software + Head de Produto
- **Data de aprovação**: Sprint 22 (2026-08-09)

---

## 1. Contexto

Até a Sprint 21 o repositório Ontrackchain NÃO possuía um CHANGELOG.md oficial
em formato industrial. Cada sprint tinha registro de entrega apenas no README
principal (snapshot executivo), no arquivo `docs/project-executive-readiness-brief.md`
(baseline regulatório) e nas mensagens longas de commit git. O problema era:

1.  **Sem rastreabilidade release-to-release entre sprints**: Um cliente em v5.3.0 (S19)
    não conseguia saber, em 10 segundos, quais features foram adicionadas entre S19→S22
    sem abrir 5 arquivos diferentes.
2.  **Sem vinculo formal com SemVer**: O README tinha versão "release atual" mas não
    havia documento de comparação Added/Changed/Fixed/Security por release.
3.  **Sem documentação de migração para releases major**: O salto de v4.x (S1-13)
    para v5.0.0 (S14-16) major não tinha registro formal das breaking changes.

**4 requisitos NÃO FUNCIONAIS OBRIGATÓRIOS ADR-023:**
1.  Formato 100% compatível com `keepachangelog.com/pt-BR/1.1.0/`.
2.  Hierarquia: Release de plataforma = Sprint. Cada sprint = 1 entrada semver.
3.  Entradas internas por componente (frontend, apps/*, packages/*) documentadas
    dentro da mesma release.
4.  Links para commits SHA locais (mesmo em modo M5 bloqueado) para auditabilidade.

---

## 2. Requisitos Funcionais Mapeados (8 Releases Documentadas)

| Release SemVer | Sprint Coberta | Tipo | Tema Principal |
|---|---|---|---|
| `v5.6.0` | Sprint 22 | MINOR | CHANGELOG oficial + Billing Stripe + k6 Load Testing |
| `v5.5.0` | Sprint 21 | MINOR | Graph Intelligence 4.0 Cytoscape + 4 ADRs (019→022) + Baseline v1.1 |
| `v5.4.0` | Sprint 20 | MINOR | Structural Screens LGPD + qa-gateway STRICT mode + Hypothesis fuzzing |
| `v5.3.0` | Sprint 19 | MINOR | Public API v2.0.0 B2B HMAC + Frontend Error Boundaries WCAG + Playwright 42 specs |
| `v5.2.0` | Sprint 18 | MINOR | Helm Backup Diário LGPD + CI 17 gates bloqueantes + Monorepo Hatchling |
| `v5.1.0` | Sprint 17 | PATCH | Helm Chart 3.1.0 hotfixes + CI SLA P0-08 refinamentos |
| `v5.0.0` | Sprint 14-16 | MAJOR | HelmL Chart v3 + AI Service v4 + Federação Roles OTK_* + CI 16 Gates |
| `v4.x.x` | Sprint 1-13 | MAJOR legacy | Scaffold inicial + 9 serviços FastAPI + PG16 + Frontend Next.js |

---

## 3. Alternativas Avaliadas (3 Opções + Trade-offs)

### Opção A: Arquivo mensal `docs/changelogs/2026-08.md` por data

- **Prós**: Fácil de escrever; ordem cronológica natural; não precisa SemVer.
- **Contras**: Não responde a pergunta "que versão eu preciso adotar para ter feature X?";
  não tem padrão industrial; release semver desacoplado da data.
- **Custo de manutenção**: Médio (1 arquivo/mês).

### Opção B: CHANGELOG.md gerado automaticamente por conventional-commits via `release-please`

- **Prós**: Zero esforço manual; mensagens de commit viram changelog automaticamente;
  integração com GitHub Actions nativa.
- **Contras**: 🚨 **Quebra restrição M5**: `release-please` precisa de push
  remoto para criar tag/release automática via token. Não podemos adotar até
  o bloqueio M5 ser removido oficialmente.
- **Custo de manutenção**: Baixo porém incompatível com M5 atual.

### **Opção C (RECOMENDADA): Arquivo manual CHANGELOG.md raiz + padrão Keep a Changelog 1.1.0 hierárquico por sprint + commit links locais**

- **Prós**:
  1.  100% compatível com M5 bloqueado (nenhum push remoto necessário).
  2.  Formato industrial amplamente reconhecido (duvida zero stakeholders).
  3.  Controle manual = qualidade editorial; engenheiro de release valida antes de publicar.
  4.  Links de commit SHA locais funcionam mesmo sem push remoto.
  5.  Sem dependência de CI/CD extra para escrita.
- **Contras**: Processo manual (10min por sprint adicionar a nova release).
- **Custo de manutenção**: Baixo (1 bloco de texto por sprint, template fixo).

---

## 4. Decisão Final: Opção C

**Justificativa 4 perguntas do arquiteto:**

| Pergunta | Resposta |
|---|---|
| (1) Fecha objetivo de negócio? | ✅ Sim. Rastreabilidade release-2-release para clientes B2B Enterprise. |
| (2) Conforme restrições (M5, LGPD)? | ✅ Sim. M5 intacto (nenhum push). Dados em CHANGELOG = públicos por design. |
| (3) Atributos qualidade? | ✅ Mant. (processo 10min/sprint) + Legibilidade (padrão industrial). |
| (4) Opção mais barata/risco? | ✅ Sim. Opção B requer lift M5 primeiro; opção A é incompatível com padrão. |

---

## 5. Trade-offs Aceitos e Riscos Identificados

1.  **Trade-off aceito**: Esforço manual 10min/sprint → em troca de compatibilidade M5 + qualidade editorial.
2.  **Risco baixo**: Redator esquecer de atualizar CHANGELOG no final da sprint → mitigado via
    item obrigatório no checklist H5 de todo sprint (Sprint 22+).
3.  **Risco médio futuro**: Quando M5 for removido, migrar de manual para Opção B
    (`release-please` conventional-commits) **é uma decisão reversível**, sem breaking changes.

---

## 6. Definition of Done (DoD)

| Critério | Status na Sprint 22 |
|---|---|
| CHANGELOG.md criado na raiz do workspace | ✅ Concluído |
| 8 releases hierárquicas documentadas (S1→S22) | ✅ Concluído |
| Formato 100% Keep a Changelog 1.1.0 (Added/Changed/Fixed/Security) | ✅ Concluído |
| Cada release tem identificador sprint + semver | ✅ Concluído |
| Referências commits SHA locais incluídas | ✅ Concluído (mensagens de commit SHA longas) |
| README.md release atual sincronizada | ✅ Concluído (v5.5.0 → v5.6.0 Sprint 22) |

---

## 7. Consequências Operacionais e de Governança

### Positivas
- Registro imutável por release de plataforma.
- Comunicação com clientes enterprise (ex: Banco parceiro) agora tem documento canônico de entrega.
- Baseline Readiness Brief agora pode referenciar CHANGELOG como fonte formal.

### Futuras Melhorias Reversíveis (Quando M5 Removido)
1.  Adotar conventional-commits + `release-please` geração automática (Opção B).
2.  Criar workflow "release-drafter" com rascunho automático baseado em PRs.
3.  Adicionar validação qa-gateway `scan-changelog-completeness` (Sprint 24+ Q3-06).
