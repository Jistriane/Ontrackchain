#!/usr/bin/env bash
# SCRIPT: s28p25-test-gov-m5-verify.sh
# CRIADO EM: Sprint S28+25 P1
# PROPÓSITO: Teste unitário do gov-m5-verify-pre-sign.sh — NÃO TOCA arquivo real M5.md!
#   Testes (2):
#     1) Cenário A: hash limpo bate (PASSO 0 VÁLIDO → exit 0)
#     2) Cenário B: hash limpo NÃO bate (PASSO 0 INVÁLIDO → exit 1)
#   Usa TMPDIR, copia script, injeta M5.md mock temporário com parâmetro controlado.
set -uo pipefail   # sem "-e" — pois precisamos capturar exit codes != 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GOV_SCRIPT="$SCRIPT_DIR/gov-m5-verify-pre-sign.sh"
TMPDIR_WORK="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_WORK"' EXIT

if [ ! -x "$GOV_SCRIPT" ]; then
  echo "[ERRO] gov-m5-verify-pre-sign.sh não encontrado ou sem +x em: $GOV_SCRIPT"
  exit 2
fi

mkdir -p "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs"
mkdir -p "$TMPDIR_WORK/ontrackchain/scripts"
cp "$GOV_SCRIPT" "$TMPDIR_WORK/ontrackchain/scripts/gov-m5-verify-pre-sign.sh"
chmod +x "$TMPDIR_WORK/ontrackchain/scripts/gov-m5-verify-pre-sign.sh"

################################################################################
# Helper: monta mock M5.md com hash hardcoded opcional
################################################################################
monta_m5_mock() {
  # $1 = hash hardcoded (64 hex)
  HARD="$1"
  # Ordem das linhas é IMPORTANTE — linha 7 é a do hash hardcoded.
  cat <<EOF
# Sign-off SSOT Mock A
**Document ID**: MOCK-A-v1
**Data referência**: 2026-08-11
**Status inicial**: MOCK_OK
**Regras de validação**: Mock
**Arquivo SSOT**: Mock
**SHA256 pré-assinatura Sprint S28+21**: \`${HARD}\`
  — calculo awk NR<7 || NR>11
  — verificacao script gov-m5-verify-pre-sign.sh
  — NAO use sha256sum direto.
  — se retornar ❌ nao assine.

---

## Check items
Linha 12 em diante permanece na versão limpa, então CONTA no hash limpo.
Isso é CRÍTICO para o cenário A passar (hash deve bater exatamente).
EOF
}

# =====================================================================
# Cenário A: M5 válido → deve retornar exit 0 ✅
# =====================================================================
# PASSO 1: monta M5 com HASH temporário (placeholder), limpa L7..L11,
#          calcula hash do arquivo limpo.
monta_m5_mock "deadbeef00000000000000000000000000000000000000000000000000000000" \
  > "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"
# Limpa (awk NR<7 || NR>11) → gera o arquivo "limpo" → calcula SHA256 do limpo.
HASH_A=$(awk 'NR<7 || NR>11' "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md" | sha256sum | awk '{print $1}')
# PASSO 2: reescreve M5 com HASH_A correto (agora sim = baterá ao rodar gov-m5)
monta_m5_mock "$HASH_A" \
  > "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"
# Roda script gov
( cd "$TMPDIR_WORK" && ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh >cenario_a.log 2>&1; echo $? >cenario_a.exit )
EXIT_A=$(cat "$TMPDIR_WORK/cenario_a.exit")
echo
echo "=== CENÁRIO A (deve PASSAR, exit=0) ==="
tail -5 "$TMPDIR_WORK/cenario_a.log"
echo "exit=$EXIT_A"
if [ "$EXIT_A" -eq 0 ]; then
  echo "✅ CENÁRIO A: PASS (exit 0 esperado)"
  OK_A=1
else
  echo "❌ CENÁRIO A: FAIL (esperava exit 0, recebeu $EXIT_A)"
  OK_A=0
fi

# =====================================================================
# Cenário B: M5 inválido (hash hardcoded = 64 zeros → NÃO BATE) → exit 1 ❌
# =====================================================================
HASH_BAD="0000000000000000000000000000000000000000000000000000000000000000"
monta_m5_mock "$HASH_BAD" \
  > "$TMPDIR_WORK/ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"
( cd "$TMPDIR_WORK" && ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh >cenario_b.log 2>&1; echo $? >cenario_b.exit )
EXIT_B=$(cat "$TMPDIR_WORK/cenario_b.exit")
echo
echo "=== CENÁRIO B (deve FALHAR, exit=1) ==="
tail -5 "$TMPDIR_WORK/cenario_b.log"
echo "exit=$EXIT_B"
if [ "$EXIT_B" -ne 0 ]; then
  echo "✅ CENÁRIO B: PASS (exit !=0 esperado, recebeu $EXIT_B = fail-closed correto)"
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
