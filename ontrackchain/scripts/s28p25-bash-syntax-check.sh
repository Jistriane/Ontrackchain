#!/usr/bin/env bash
# SCRIPT: s28p25-bash-syntax-check.sh
# CRIADO EM: Sprint S28+25 P1
# PROPÓSITO: Rodar bash -n (syntax check, não executa) em TODOS scripts shell do monorepo.
#   - scripts/*.sh
#   - .github/workflows NÃO (são YAML, não shell)
#   - exit 0 = 100% syntax OK; exit N = N arquivos com SyntaxError.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/.." || exit 9  # volta para a raiz do monorepo (acima de ontrackchain/)

TOTAL=0
PASS=0
FAIL=0
FAIL_FILES=""

echo "============================================================"
echo "Sprint S28+25.2: bash -n syntax check em scripts/*.sh"
echo "Base dir: $(pwd)"
echo "============================================================"
echo

# Find todos arquivos .sh ou scripts com shebang bash (até 4 subdirs)
while IFS= read -r -d '' shfile; do
  TOTAL=$((TOTAL+1))
  if bash -n "$shfile" 2>/dev/null; then
    echo "  ✅ $shfile"
    PASS=$((PASS+1))
  else
    echo "  ❌ $shfile (bash -n falhou: erro de sintaxe)"
    FAIL=$((FAIL+1))
    FAIL_FILES="${FAIL_FILES}  $shfile\n"
  fi
done < <(find ontrackchain/scripts -type f \( -name "*.sh" -o -exec grep -lIqE '^#!.*bash|^#!.*sh' {} \; \) -print0 2>/dev/null | sort -z)

echo
echo "============================================================"
echo "RESULTADO: $PASS PASSADOS / $FAIL FALHOS / $TOTAL TOTAIS"
echo "============================================================"
if [ "$FAIL" -gt 0 ]; then
  printf "ARQUIVOS COM ERRO SINTAXE:\n%s" "$FAIL_FILES"
  exit "$FAIL"
fi
echo "✅ bash -n syntax check: 100% scripts shell com sintaxe válida."
exit 0
