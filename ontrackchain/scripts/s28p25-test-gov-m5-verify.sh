#!/usr/bin/env bash
# SCRIPT: s28p25-test-gov-m5-verify.sh
# CRIADO EM: Sprint S28+25 P1
# PROPÓSITO: Teste unitário do gov-m5-verify-pre-sign.sh — NÃO TOCA arquivo real M5.md!
#   Testes (2):
#     1) Cenário A: hash limpo bate (PASSO 0 VÁLIDO → exit 0)
#     2) Cenário B: hash limpo NÃO bate (PASSO 0 INVÁLIDO → exit 1)
#   Usa TMPDIR, copia script, injeta M5.md mock temporário com parâmetro controlado.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOV_SCRIPT="$SCRIPT_DIR/gov-m5-verify-pre-sign.sh"
TMPDIR_WORK="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_WORK"' EXIT

if [ ! -x "$GOV_SCRIPT" ]; then
  echo "[ERRO] gov-m5-verify-pre-sign.sh não encontrado ou sem +x em: $GOV_SCRIPT"
  exit 2
fi

# Constrói diretório mock idêntico à estrutura relativa: ontrackchain/docs/governance-sign-offs/
mkdir -p "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs"
mkdir -p "$TMPDIR_WORK/ontrackchain/scripts"
cp "$GOV_SCRIPT" "$TMPDIR_WORK/ontrackchain/scripts/gov-m5-verify-pre-sign.sh"
chmod +x "$TMPDIR_WORK/ontrackchain/scripts/gov-m5-verify-pre-sign.sh"

# =====================================================================
# Cenário A: M5 válido → deve retornar exit 0 ✅
# =====================================================================
# Cria conteúdo base "fake" M5 + bloco 5 linhas hash auto-ref (awk NR<7 || NR>11)
MOCK_BODY_A="$(cat <<'EOF'
# Sign-off SSOT Mock A
**Document ID**: MOCK-A-v1
**Data referência**: 2026-08-11
**Status inicial**: MOCK_OK
**Regras de validação**: Mock
**Arquivo SSOT**: Mock
EOF
)"
# Primeiro calcula hash do body A limpo (linhas 1..6 → hash correto)
HASH_A=$(printf "%s\n" "$MOCK_BODY_A" | sha256sum | awk '{print $1}')
# Monta M5 final completo com hash HARDCODED correto em L7
{
  printf "%s\n" "$MOCK_BODY_A"
  echo "**SHA256 pré-assinatura Sprint S28+21**: \`${HASH_A}\`"
  echo "  — calculo awk NR<7 || NR>11"
  echo "  — verificacao script gov-m5-verify-pre-sign.sh"
  echo "  — NAO use sha256sum direto."
  echo "  — se retornar ❌ nao assine."
  echo ""
  echo "---"
  echo ""
  echo "## Check items"
  echo "Conteúdo após separador (preservado no hash limpo também? Sim, pq removidas apenas L7..L11)."
} > "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"

# Roda script mock A
(
  cd "$TMPDIR_WORK"
  ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh >cenario_a.log 2>&1
)
EXIT_A=$?
echo
echo "=== CENÁRIO A (deve PASSAR, exit=0) ==="
cat "$TMPDIR_WORK/cenario_a.log" | tail -3
if [ "$EXIT_A" -eq 0 ]; then
  echo "✅ CENÁRIO A: PASS (exit 0 esperado)"
  OK_A=1
else
  echo "❌ CENÁRIO A: FAIL (exit 0 esperado, recebeu $EXIT_A)"
  OK_A=0
fi

# =====================================================================
# Cenário B: M5 inválido (hash hardcoded = 64 zeros → NÃO BATE) → exit 1 ❌
# =====================================================================
HASH_BAD="0000000000000000000000000000000000000000000000000000000000000000"
{
  printf "%s\n" "$MOCK_BODY_A"
  echo "**SHA256 pré-assinatura Sprint S28+21**: \`${HASH_BAD}\`"
  echo "  — calculo awk NR<7 || NR>11"
  echo "  — verificacao script gov-m5-verify-pre-sign.sh"
  echo "  — NAO use sha256sum direto."
  echo "  — se retornar ❌ nao assine."
  echo ""
  echo "---"
  echo ""
  echo "## Check items — body idêntico ao cenário A, mas hash L7 é inválido."
} > "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"

(
  cd "$TMPDIR_WORK"
  ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh >cenario_b.log 2>&1 || true
)
EXIT_B=$?
echo
echo "=== CENÁRIO B (deve FALHAR, exit=1) ==="
cat "$TMPDIR_WORK/cenario_b.log" | tail -3
if [ "$EXIT_B" -ne 0 ]; then
  echo "✅ CENÁRIO B: PASS (exit !=0 esperado, recebeu $EXIT_B = comportamento fail-closed correto)"
  OK_B=1
else
  echo "❌ CENÁRIO B: FAIL (esperava exit 1, recebeu $EXIT_B = false negative!)"
  OK_B=0
fi

echo
echo "============================================================"
echo "RESULTADO TESTE gov-m5-verify-pre-sign.sh: 2 cenários."
echo "============================================================"
echo "  Cenário A (hash OK → exit 0):    $([ $OK_A -eq 1 ] && echo PASS || echo FAIL)"
echo "  Cenário B (hash RUIM → exit 1):  $([ $OK_B -eq 1 ] && echo PASS || echo FAIL)"
if [ $(( OK_A + OK_B )) -eq 2 ]; then
  echo "✅ 2/2 TESTES PASSARAM."
  exit 0
else
  echo "❌ TESTES FALHARAM — corrigir gov-m5-verify-pre-sign.sh."
  exit 1
fi
