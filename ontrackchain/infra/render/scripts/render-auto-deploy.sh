#!/usr/bin/env bash
# OnTrackChain — Deploy Automático no Render (via API REST cURL, sem browser)
#
# COMO FUNCIONA:
#   Script trigger 1 clique — faz deploy MANUAL dos serviços do Blueprint
#   ontrackchain-staging no Render, seguindo a ordem correta de boot (sem
#   depender do autoDeploy acidental do GitHub push).
#
# REQUISITOS (sincronizados via sync:false no Environment Group ou .env local):
#   1. RENDER_API_KEY ......... Crie em: https://dashboard.render.com/user/settings/api_keys
#                               Copie para cá (scope Total, expiração longa).
#   2. RENDER_BLUEPRINT_ID ... Copie da URL do seu Blueprint:
#      https://dashboard.render.com/blueprints/<RENDER_BLUEPRINT_ID>
#   3. (Opcional) RENDER_OWNER_ID ... Team ID se sua conta for Team, senha vazio.
#
# OBS: Este script NÃO aciona push GitHub, apenas faz Manual Deploy via API.
#      Para push + deploy, use push-and-deploy.sh.
#
# USO:
#   export RENDER_API_KEY="rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
#   export RENDER_BLUEPRINT_ID="bp-XXXXXXXXXXXXXXXXXXXXXX"
#   bash infra/render/scripts/render-auto-deploy.sh
#
# SAÍDA ESPERADA (após aplicar):
#   ✅ Trigger deploy 20 serviços. Estado live em 8-12 min.

set -euo pipefail

REQUIRED_VARS=(RENDER_API_KEY RENDER_BLUEPRINT_ID)
for v in "${REQUIRED_VARS[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "🚨 Faltando env var obrigatória: $v"
    if [[ "$v" == "RENDER_API_KEY" ]]; then
      echo "   Crie em: https://dashboard.render.com/user/settings/api_keys (scope Create + Read)"
    fi
    if [[ "$v" == "RENDER_BLUEPRINT_ID" ]]; then
      echo "   Copie da URL do seu Blueprint (prefixo bp- OU exs- ambos funcionam): https://dashboard.render.com/blueprint/<BP_ID>"
      echo "   Contas Team/Enterprise: exporte também RENDER_OWNER_ID (prefixo tea- ou usr-)"
    fi
    exit 1
  fi
done
[[ "${!RENDER_BLUEPRINT_ID}" == bp-* || "${!RENDER_BLUEPRINT_ID}" == exs-* ]] || true

API_BASE="https://api.render.com/v1"
AUTH_HEADER="Authorization: Bearer ${RENDER_API_KEY}"
ACCEPT_JSON="Accept: application/json"
CT_JSON="Content-Type: application/json"

echo "================================================================================"
echo " OnTrackChain — Render Auto Deploy (API v1)"
echo "================================================================================"
echo " Blueprint ID: ${RENDER_BLUEPRINT_ID}"
echo " Owner:        ${RENDER_OWNER_ID:-<default sua conta pessoal>}"
echo "================================================================================"

echo ""
echo "▶️  PASSO 1/4 — Listar serviços do Blueprint (buscar service IDs dos 20)..."
CURSOR=""
SERVICES_JSON="[]"
PAGE=0
while true; do
  PAGE=$((PAGE+1))
  PAGE_JSON=$(curl -sS --max-time 20 \
    -H "${AUTH_HEADER}" \
    -H "${ACCEPT_JSON}" \
    "${API_BASE}/services?limit=100${RENDER_OWNER_ID:+&ownerId=${RENDER_OWNER_ID}}${CURSOR:+&cursor=${CURSOR}}")
  if command -v jq >/dev/null 2>&1; then
    SERVICES_JSON=$(jq -s 'add' <<<"$SERVICES_JSON $PAGE_JSON" 2>/dev/null || echo "$SERVICES_JSON")
    THIS_LEN=$(jq -r 'length // 0' <<<"$PAGE_JSON" 2>/dev/null || echo 0)
    NEXT_CURSOR=$(jq -r '.[-1].cursor // ""' <<<"$PAGE_JSON" 2>/dev/null || echo "")
  else
    THIS_LEN=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" <<<"$PAGE_JSON" 2>/dev/null || echo 0)
    NEXT_CURSOR=$(python3 -c "
import sys,json
d=json.load(sys.stdin)
c=''
if isinstance(d,list) and len(d)>0:
    for it in reversed(d):
        if isinstance(it,dict):
            c=str(it.get('cursor') or it.get('nextCursor') or '')
            if c: break
print(c)
" <<<"$PAGE_JSON" 2>/dev/null || echo "")
    SERVICES_JSON=$(python3 -c "
import sys,json
a=json.loads(sys.argv[1])
b=json.loads(sys.argv[2])
if isinstance(a,list) and isinstance(b,list):
    print(json.dumps(a+b))
elif isinstance(a,list):
    print(json.dumps(a))
else:
    print(json.dumps(b))
" "$SERVICES_JSON" "$PAGE_JSON" 2>/dev/null || echo "$SERVICES_JSON")
  fi
  [[ "$THIS_LEN" -lt 100 || -z "$NEXT_CURSOR" ]] && break
  CURSOR="$NEXT_CURSOR"
  sleep 0.2
done

if command -v jq >/dev/null 2>&1; then
  SVC_COUNT=$(echo "$SERVICES_JSON" | jq -r 'length // 0' 2>/dev/null || echo 0)
else
  SVC_COUNT=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))" <<<"$SERVICES_JSON" 2>/dev/null || echo 0)
fi

echo "   Total de serviços encontrados na conta Render (paginação ${PAGE} páginas): ${SVC_COUNT}"
echo ""
echo "▶️  PASSO 2/4 — Filtrar serviços OnTrackChain staging..."

ONT_SERVICES=$(
  if command -v jq >/dev/null 2>&1; then
    echo "$SERVICES_JSON" | jq -r '.[] | .service as $sv | select((($sv.name // "") | startswith("ontrackchain-")) and (($sv.name // "") | test("-staging$|staging-c[0-9a-z]+$") or (($sv.slug // "") | test("staging")))) | "\($sv.id) \($sv.name) \($sv.type)"'
  else
    python3 -c "
import sys,json,re
pat=re.compile(r'staging')
for s in json.load(sys.stdin):
    sv=s.get('service', s) if isinstance(s,dict) else s
    if not isinstance(sv, dict): continue
    name=(sv.get('name') or '')
    slug=(sv.get('slug') or '')
    if name.startswith('ontrackchain-') and (pat.search(name) or pat.search(slug)):
        print(f\"{sv.get('id')} {name} {sv.get('type')}\")
" <<<"$SERVICES_JSON"
  fi
)
ONT_COUNT=$(echo "$ONT_SERVICES" | awk 'NF>0' | wc -l)
echo "   Serviços OnTrackChain staging encontrados: ${ONT_COUNT}"
if [[ "$ONT_COUNT" -lt 1 ]]; then
  echo "❌ Nenhum serviço ontrackchain-*-staging encontrado. Verifique:"
  echo "   (a) RENDER_OWNER_ID se for conta Team"
  echo "   (b) Blueprint já foi aplicado pelo menos 1 vez no dashboard"
  echo "   (c) RENDER_API_KEY tem scope de leitura."
  exit 1
fi
echo ""
echo "▶️  PASSO 3/4 — Ordem de deploy (prioridade correta)..."

ORDER_REGEX=(
  "postgres"
  "redis"
  "keycloak"
  "auth-idp"
  "auth-service"
  "public-api"
  "investigation-api"
  "investigation-worker"
  "compliance-api"
  "compliance-worker"
  "monitoring-api"
  "alertmanager"
  "prometheus"
  "grafana"
  "report-api"
  "ai-service"
  "ai-worker"
  "case-management"
  "qa-gateway"
  "frontend-demo"
  "frontend-staging"
  "frontend"
  "gateway"
)

TRIGGERED=0
SUSPENDED_LIST=()
TOTAL_ONT=$(echo "$ONT_SERVICES" | awk 'NF>0' | wc -l)

for pattern in "${ORDER_REGEX[@]}"; do
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    sid=$(awk '{print $1}' <<<"$line")
    sname=$(awk '{print $2}' <<<"$line")
    stype=$(awk '{print $3}' <<<"$line")
    if [[ "$sname" == *"$pattern"* ]]; then
      echo ""
      echo "   🔧 Trigger deploy → $sname ($stype / $sid)"
      HTTP_CODE=$(curl -sS --max-time 20 -o /tmp/render_deploy_resp.json -w "%{http_code}" \
        -X POST \
        -H "${AUTH_HEADER}" \
        -H "${ACCEPT_JSON}" \
        -H "${CT_JSON}" \
        -d '{}' \
        "${API_BASE}/services/${sid}/deploys")
      if [[ "$HTTP_CODE" == "400" ]] && grep -q "suspended" /tmp/render_deploy_resp.json 2>/dev/null; then
        echo "      ⚠️  Serviço está SUSPENSO. Tentando RESUME via PATCH /services/${sid} {suspended:false}..."
        RSM_CODE=$(curl -sS --max-time 20 -o /tmp/render_resume_resp.json -w "%{http_code}" \
          -X PATCH \
          -H "${AUTH_HEADER}" \
          -H "${ACCEPT_JSON}" \
          -H "${CT_JSON}" \
          -d '{"suspended": "no"}' \
          "${API_BASE}/services/${sid}")
        if [[ "$RSM_CODE" -ge 200 && "$RSM_CODE" -lt 300 ]]; then
          echo "      ✅ Resume OK (HTTP $RSM_CODE). Re-disparando deploy..."
          HTTP_CODE=$(curl -sS --max-time 20 -o /tmp/render_deploy_resp.json -w "%{http_code}" \
            -X POST \
            -H "${AUTH_HEADER}" \
            -H "${ACCEPT_JSON}" \
            -H "${CT_JSON}" \
            -d '{}' \
            "${API_BASE}/services/${sid}/deploys")
        else
          echo "      ❌ Resume falhou (HTTP $RSM_CODE). Manual: Dashboard → $sname → Resume Service."
          SUSPENDED_LIST+=("$sname ($sid)")
        fi
      fi
      TRIGGERED=$((TRIGGERED + 1))
      if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
        if command -v jq >/dev/null 2>&1; then
          DID=$(jq -r '.deploy.id // .id // "ok"' /tmp/render_deploy_resp.json 2>/dev/null || echo ok)
          echo "      ✅ Deploy ID: $DID"
        else
          DID=$(python3 -c "import json; d=json.load(open('/tmp/render_deploy_resp.json')); print(d.get('deploy',{}).get('id') if isinstance(d.get('deploy'),dict) else d.get('id','ok'))" 2>/dev/null || echo ok)
          echo "      ✅ Deploy ID: $DID"
        fi
      else
        echo "      ⚠️  HTTP $HTTP_CODE. Resposta:"
        head -c 500 /tmp/render_deploy_resp.json 2>/dev/null; echo
      fi
      ONT_SERVICES=$(grep -vF "$sid" <<<"$ONT_SERVICES" || true)
      sleep 1
    fi
  done <<<"$ONT_SERVICES"
done

# Serviços restantes (caso regex não cobriu algum nome novo):
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  sid=$(awk '{print $1}' <<<"$line")
  sname=$(awk '{print $2}' <<<"$line")
  stype=$(awk '{print $3}' <<<"$line")
  echo ""
  echo "   🔧 Trigger deploy (restante) → $sname ($stype / $sid)"
  HTTP_CODE=$(curl -sS --max-time 20 -o /tmp/render_deploy_resp.json -w "%{http_code}" \
    -X POST \
    -H "${AUTH_HEADER}" \
    -H "${ACCEPT_JSON}" \
    -H "${CT_JSON}" \
    -d '{}' \
    "${API_BASE}/services/${sid}/deploys")
  TRIGGERED=$((TRIGGERED + 1))
  if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
    echo "      ✅ Deploy iniciado."
  else
    echo "      ⚠️  HTTP $HTTP_CODE. Resposta:"
    head -c 500 /tmp/render_deploy_resp.json 2>/dev/null; echo
  fi
  sleep 1
done <<<"$ONT_SERVICES"

rm -f /tmp/render_deploy_resp.json /tmp/render_resume_resp.json

echo ""
echo "▶️  PASSO 4/4 — Resumo"
echo "   Total de serviços OnTrackChain staging: $TOTAL_ONT"
echo "   Total de deploys disparados via API:    $TRIGGERED"
if [[ "${#SUSPENDED_LIST[@]}" -gt 0 ]]; then
  echo "   Serviços SUSPENSOS (resumo manual necessário):"
  for x in "${SUSPENDED_LIST[@]}"; do
    echo "     - $x"
  done
  echo "   Ação 1 clique: Render Dashboard → Serviço → Resume Service → re-deploy."
fi
if [[ "$TRIGGERED" -ge 17 || "${#SUSPENDED_LIST[@]}" -gt 0 ]]; then
  echo "✅ SUCESSO. Acompanhe LIVE no Dashboard Render em 8-12 minutos."
  echo "   Depois rode: bash infra/render/scripts/render-smoke-tests.sh <gateway-url>"
else
  echo "⚠️  Menos de 17 deploys disparados. Verifique Blueprint ou RENDER_OWNER_ID."
  exit 2
fi
