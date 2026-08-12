#!/usr/bin/env bash
# OnTrackChain — 1 CLIQUE = Push GitHub + Deploy automático no Render (SEM SENHA, SEM TOKEN digitado)
#
# COMO FUNCIONA:
#   - Step 1: Auto-detecta credenciais git existentes (HTTPS credential store OU SSH agent id_ed25519)
#             SEM pedir senha nem token; falha se nenhuma existir.
#   - Step 2: Faz git add -A + commit automático se houver dirty tree (mensagem: chore(devops)).
#   - Step 3: Push origin main.
#   - Step 4: (Se RENDER_API_KEY e RENDER_BLUEPRINT_ID existirem no env) — chama render-auto-deploy.sh
#             para trigger MANUAL deploy de todos 20 serviços via API.
#
# REQUISITOS PARA DEPLOY RENDER AUTOMÁTICO (step 4):
#   No seu shell, execute 1 vez:
#       export RENDER_API_KEY="rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#       export RENDER_BLUEPRINT_ID="bp-XXXXXXXXXXXXXXXXXXXXXX"
#   (Se não exportar, step 4 é SKIP e só faz push do GitHub — deploy manual por dashboard)
#
# USO:
#   bash infra/render/scripts/push-and-deploy.sh

set -euo pipefail

cd "$(dirname "$0")/../../.."
ROOTDIR=$(pwd)
echo "================================================================================"
echo " OnTrackChain — Push GitHub + Deploy Automático"
echo " Working directory: ${ROOTDIR}"
echo "================================================================================"
echo ""

cd ontrackchain || exit 2

START_HASH=$(git rev-parse --short HEAD)
echo "▶️  PASSO 1/5 — Verificar dirty tree (arquivos modificados ou untracked)..."
if ! git diff --quiet HEAD || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  echo "   📝 Alterações locais encontradas. Auto-commitando..."
  git -c core.quotepath=false add -A
  git -c core.quotepath=false commit -m "chore(devops): auto commit dirty tree before push-and-deploy
Hora: $(date -Iseconds)"
  NEW_HASH=$(git rev-parse --short HEAD)
  echo "   ✅ Novo commit: ${START_HASH} → ${NEW_HASH}"
else
  echo "   ✅ Working tree limpa. Nenhum commit adicional necessário."
fi
echo ""

echo "▶️  PASSO 2/5 — Auto-detectar método de push GitHub... (SEM pedir senha nem token)"
REMOTE_URL=$(git remote get-url origin)
PUSH_METHOD=""

# Método A: Tentar HTTPS store primeiro (já temos token salvo no ~/.git-credentials em sandbox)
if [[ "$REMOTE_URL" == https://* ]]; then
  echo "   🔒 Método A: HTTPS + credential helper store (token salvo localmente)."
  set +e
  PUSH_OUT=$(git -c credential.helper=store push origin main 2>&1)
  PUSH_RC=$?
  set -euo pipefail
  if [[ $PUSH_RC -eq 0 ]] || (echo "$PUSH_OUT" | grep -q "Everything up-to-date"); then
    PUSH_METHOD="https-store"
  else
    echo "   ⚠️  HTTPS store falhou: $PUSH_OUT"
  fi
fi

# Método B: Tentar SSH agent (id_ed25519 carregado no ssh-agent)
if [[ -z "$PUSH_METHOD" ]]; then
  if ssh-add -l >/dev/null 2>&1; then
    echo "   🔑 Método B: SSH + Agente (id_ed25519 carregada)."
    if [[ "$REMOTE_URL" != git@* ]]; then
      echo "      → Trocando origin temporariamente para SSH..."
      git remote set-url origin git@github.com:Jistriane/Ontrackchain.git
    fi
    set +e
    PUSH_OUT=$(GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/tmp/git_known_hosts -o BatchMode=no" git push origin main 2>&1)
    PUSH_RC=$?
    set -euo pipefail
    if [[ $PUSH_RC -eq 0 ]] || (echo "$PUSH_OUT" | grep -q "Everything up-to-date"); then
      PUSH_METHOD="ssh-agent"
      REMOTE_URL=$(git remote get-url origin)
      if [[ "$REMOTE_URL" == git@* ]]; then
        echo "      ✅ Manter origin como SSH (melhor sem senhas)."
      fi
    else
      echo "   ⚠️  SSH agent falhou: $PUSH_OUT"
      echo "      → Restaurando origin para HTTPS..."
      git remote set-url origin https://github.com/Jistriane/Ontrackchain.git
    fi
  fi
fi

# Nenhum método funcionou?
if [[ -z "$PUSH_METHOD" ]]; then
  echo "❌ Nenhum método de push automático disponível. Ação necessária manual:"
  echo "   → (1) Cole sua chave pública ~/.ssh/id_ed25519.pub em: https://github.com/settings/ssh/new"
  echo "   → (2) OU: export GITHUB_TOKEN=<seu PAT classic> e git push via HTTPS."
  exit 1
fi

echo ""
echo "▶️  PASSO 3/5 — Verificar GitHub atualizado (local == remote main)..."
set +e
git fetch origin main --depth=1 >/dev/null 2>&1
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main 2>/dev/null)
set -euo pipefail
echo "   Local  : ${LOCAL_HASH}"
echo "   Remoto : ${REMOTE_HASH}"
if [[ "$LOCAL_HASH" == "$REMOTE_HASH" ]]; then
  echo "   ✅ GitHub SINCRONIZADO. (método: ${PUSH_METHOD})"
else
  echo "❌ Local e remoto divergem. Manual push necessário."
  exit 2
fi
echo ""

echo "▶️  PASSO 4/5 — Deploy automático Render via API..."
if [[ -z "${RENDER_API_KEY:-}" || -z "${RENDER_BLUEPRINT_ID:-}" ]]; then
  echo "   ⏭️  SKIP (RENDER_API_KEY e/ou RENDER_BLUEPRINT_ID não foram exportadas no shell)."
  echo "      Manual: Acesse Dashboard → Blueprints → Apply. Ou:"
  echo "      export RENDER_API_KEY=\"rnd_<sua-chave>\""
  echo "      export RENDER_BLUEPRINT_ID=\"bp-<seu-blueprint-id>\""
  echo "      e rode este script novamente."
else
  echo "   🚀 Chamando render-auto-deploy.sh (API deploy 20 serviços em ordem correta)..."
  bash "${ROOTDIR}/ontrackchain/infra/render/scripts/render-auto-deploy.sh"
fi
echo ""
echo "▶️  PASSO 5/5 — Resumo"
echo "   Commit final: ${LOCAL_HASH}"
echo "   Push GitHub : OK (${PUSH_METHOD})"
if [[ -n "${RENDER_API_KEY:-}" ]] && [[ -n "${RENDER_BLUEPRINT_ID:-}" ]]; then
  echo "   Deploy Render: trigger via API (acima)"
else
  echo "   Deploy Render: manual (aguarda ação ou env vars)."
fi
echo ""
echo "✅ FINALIZADO. Acompanhe LIVE no Render Dashboard."
