#!/usr/bin/env bash
# SCRIPT: gov-m5-verify-pre-sign.sh
# CRIADO EM: Sprint S28+21 (hotfix metodologia)
# PROPÓSITO: Resolver o problema AUTO-REFERENCIAL do SHA256 em SIGNOFF-M5.md L7.
#   - O hash hardcoded na linha 7 foi calculado ANTES da linha 7 ser inserida.
#   - Quando a linha 7 foi escrita no arquivo, O HASH DO ARQUIVO MUDOU (chicken-egg impossível).
#   - Este script: (1) extrai linha 7 como HASH_ESPERADO, (2) gera versão do arquivo SEM as linhas 7..10 (bloco SHA hardcoded),
#     (3) calcula SHA256 dessa versão "limpa" e (4) compara com HASH_ESPERADO.
#   - Se bater = PASSO 0 válido. Assinaturas PGP podem prosseguir.
set -euo pipefail

M5_PATH="ontrackchain/docs/governance-sign-offs/SIGNOFF-M5.md"
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

echo "=== PASSO 0 - VERIFICACAO SHA256 PRE-ASSINATURA (METODOLOGIA AUTO-REFERENCIAL S28+21) ==="
echo "Arquivo alvo: $M5_PATH"

if [ ! -f "$M5_PATH" ]; then
  echo "[ERRO] SIGNOFF-M5.md nao encontrado em $M5_PATH — execute a partir da raiz do monorepo."
  exit 2
fi

# Extrai hash hardcoded esperado (linha comeca com **SHA256 pré-assinatura Sprint**, formato ...`HASH`...
HASH_HARDCODED=$(grep -nE '^\*\*SHA256 pré-assinatura Sprint' "$M5_PATH" | head -1 | sed -E 's/.*`([a-f0-9]{64})`.*/\1/')
if [ -z "$HASH_HARDCODED" ] || [ ${#HASH_HARDCODED} -ne 64 ]; then
  echo "[ERRO] Nao foi possivel extrair o hash hardcoded da linha 7 (64 chars hex esperados)."
  echo "       Extraido = [$HASH_HARDCODED] (len=${#HASH_HARDCODED})"
  exit 3
fi
echo "- Hash hardcoded esperado (L7):  $HASH_HARDCODED"

# Gera versao "limpa" = arquivo SEM linhas que contem o hash e sua descricao (linhas 7..11 inclusive — bloco completo do hash auto-referencial Sprint S28+21)
# Usamos awk para preservar TODAS as outras linhas exatamente, garantindo reprodutibilidade byte-a-byte.
awk 'NR<7 || NR>11' "$M5_PATH" > "$TMPDIR_WORK/SIGNOFF-M5.no-hash.md"
LINHAS_REMOVIDAS=$(( $(wc -l < "$M5_PATH") - $(wc -l < "$TMPDIR_WORK/SIGNOFF-M5.no-hash.md") ))
echo "- Linhas removidas (bloco hash auto-ref): $LINHAS_REMOVIDAS (esperado = 5: linhas 7 a 11 incl. metodologia)"
if [ "$LINHAS_REMOVIDAS" -ne 5 ]; then
  echo "[WARN] Esperava remover exatamente 5 linhas (7..11 = header + 4 bullets de explicacao). Removeu = $LINHAS_REMOVIDAS."
  echo "       Prosseguindo mesmo assim — compare os bytes."
fi

# Calcula SHA256 da versao "limpa"
HASH_LIMPO=$(sha256sum "$TMPDIR_WORK/SIGNOFF-M5.no-hash.md" | awk '{print $1}')
echo "- Hash do arquivo SEM linhas 7..11: $HASH_LIMPO"
echo
echo "=== COMPARACAO FINAL ==="
if [ "$HASH_LIMPO" = "$HASH_HARDCODED" ]; then
  echo "✅ PASSO 0 VALIDO: hash bate (metodologia S28+21). PGP clearsign PODE prosseguir."
  echo "   Dica: agora, o hash do arquivo REAL (com linha 7) sera outro valor — isso e esperado."
  echo "   O valor IMPORTANTE para o PASSO 0 e o hash DO ARQUIVO SEM AS LINHAS DO HASH (acima), que BATE com L7."
  exit 0
else
  echo "❌ PASSO 0 INVALIDO: hash NAO BATE. Arquivo foi corrompido/modificado apos Sprint S28+20."
  echo "   NÃO assine. Reporte imediatamente para o arquiteto responsavel."
  echo "   Diferença (diff -u hash): esperado=$HASH_HARDCODED atual=$HASH_LIMPO"
  exit 1
fi
