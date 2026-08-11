# Checklist Operacional para 95%

## Status

Este documento foi consolidado no plano canônico:

- [Plano Consolidado de Construcao ate 95%](./project-construction-plan-to-95-percent.md)

## Como Usar Agora

Use o plano canônico acima para acessar:

- narrativa executavel do caminho ate `95%`
- checklist executivo canônico
- gates operacionais de promocao
- checklist por owner
- regras para dizer que o projeto chegou a `95%`
- regras para nao promover artificialmente a baseline

## Compatibilidade

Este arquivo permanece versionado apenas para preservar links antigos de guias, history e boards que ainda apontam para `EXECUTION_CHECKLIST_TO_95_PERCENT.md`.

## Nota de Escopo

Os documentos da trilha `readiness / 95%` passam a ter estes papeis:

- [Avaliacao de Maturidade do Projeto](./project-maturity-assessment.md): baseline viva
- [Resumo Executivo de Readiness](./project-executive-readiness-brief.md): leitura curta para sponsors
- [Plano Consolidado de Construcao ate 95%](./project-construction-plan-to-95-percent.md): execucao canônica ate `95%`
- [Board Operacional Unico ate 90%+](./project-operational-execution-board.md): fila diaria

---

## Checklist Padrão de Execução Sprint (6 passos canônicos + 8 Gates FAIL-CLOSED)

> Referencia: [CONTRIBUTING.md (raiz do repo)](../../CONTRIBUTING.md) seção 2. Ciclo de Sprint Padrão.
> **Regra Dura**: TODO sprint deve entregar 6/6 passos (NUNCA pular DOCS ou VAL). Working Tree DEVE estar LIMPO apos COMMIT.

### Passo 1 · INV (Inventário / Análise)
- [ ] Ler arquivos alvo; listar arquivos para criar/editar.
- [ ] Confirmar HC-1..HC-5 NÃO são violados (lembrar: HC-1 SIGNOFF-M5 imutável / HC-3 settings.yml 0 alterar / HC-4 NÃO tocar código src/apps).
- [ ] Escrever 1 linha propósito sprint: "O que este sprint entrega?"

### Passo 2 · DESIGN (Plano do sprint)
- [ ] Lista quais arquivos M vs NOVOS (??) vs INTACTOS (0 alterar).
- [ ] **Greps-alvo**: Antes de editar, defina 3-6 frases-índice que o código/documento DEVE conter para VAL posterior.
- [ ] Backlog menor esforço próximo sprint (1 item concreto).

### Passo 3 · IMPL (Implementação)
- [ ] Escrever código/edições.
- [ ] `bash -n` / `mypy` quando aplicável (sintaxe imediata).
- [ ] Apenas os arquivos do passo 2 são editados (NÃO "limpeza aleatória" fora do escopo).

### Passo 4 · DOCS (Documentação do sprint — NUNCA PULAR)
- [ ] Atualizar `ontrackchain/pyproject.toml` seção roadmap # comentários: adicionar 1 linha `#   · S28+XX ✅ Título (arquivos). Resumo 1 frase.`
- [ ] Atualizar final da linha docs chain em pyproject: adicionar `→ Título Sprint (S28+XX)`.
- [ ] Atualizar `CHANGELOG-SPRINTS.md` SSOT (apenas sprints finalizados — ciclo auto-referencial é gap, resolvido S28+64/S28+66).

### Passo 5 · VAL (Validação — NUNCA PULAR)
- **Greps Conteúdo**: `grep -c "frase índice" arquivo` ≥1 para cada item do Passo 2 (3-6 no total).
- **8 Gates FAIL-CLOSED OBRIGATÓRIOS** (todos exit code 0):
  - [ ] **G1**: `bash ontrackchain/scripts/gov-m5-verify-pre-sign.sh`
  - [ ] **G2**: `bash ontrackchain/scripts/s28p25-test-gov-m5-verify.sh` (2/2)
  - [ ] **G3**: `bash ontrackchain/scripts/s28p25-bash-syntax-check.sh` (21/21)
  - [ ] **G4**: `bash ontrackchain/scripts/s28p24-check-healthz-metrics-bypass.sh` (18/18)
  - [ ] **G5**: `make all-checks -n` (parse 15 gates, 155 linhas)
  - [ ] **G6**: `make typecheck -n` (parse mypy strict hatch)
  - [ ] **G7**: `make qa-gateway-all-strict-ci -n` (parse 4 scans 46 linhas)
  - [ ] **G8**: `make settings-dry-run` (8 itens HC-3 PASS)
- [ ] `git status --short` — APENAS arquivos esperados (NÃO tem diffs fantasmas).

### Passo 6 · COMMIT
- [ ] Mensagem COMMIT 6 blocos RÍGIDOS: (1) Título Sprint PX + 8/8 Gates + WT limpa / (2) HC 0 violações / (3) Implementação N arquivos + diffs / (4) Validação Greps + 8/8 Gates / (5) Backlog Próximo Sprint / (6) Working Tree LIMPA.
- [ ] `git status --short` VAZIO pós-commit.

---

## Checklist HC-5 Dotfiles (Sprints S28+58..S28+60)

Execute em máquina nova ANTES de começar a editar:

- [ ] `code --install-extension EditorConfig.EditorConfig` (VS Code) ou equivalente JetBrains (plugin EditorConfig ATIVADO).
- [ ] Confirmar LF newlines: `file -i ontrackchain/pyproject.toml` = `charset=utf-8` (Windows: autocrlf=input via `.gitattributes`).
- [ ] 3 conveniência docs: `make readme` (abre README raiz) / `make contributing` / `make changelog`.
- [ ] `git config --global pull.rebase true` (evita merges fantasmas no pull).
