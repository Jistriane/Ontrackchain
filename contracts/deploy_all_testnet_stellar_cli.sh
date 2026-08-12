#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DEPLOYER_PK="GBPX3KRAFQPGEOI6453KT67C44KY3R54UTZIBX57IDXCSG7WSJZZ4JR3"
DEPLOYER_SEED="umbrella pizza average bus plug genius admit slam grant sell coach chunk"

CONFIG_DIR="$SCRIPT_DIR/.stellar-cli"
WASM_DIR="$SCRIPT_DIR/target/wasm32-unknown-unknown/release"
DEPLOYMENTS_DIR="$SCRIPT_DIR/deployments"
mkdir -p "$DEPLOYMENTS_DIR"

RPC_URL="https://soroban-testnet.stellar.org"
RETRIES=8
RETRY_SLEEP=25
STEP_SLEEP=15

STELLAR_CLI="stellar --config-dir $CONFIG_DIR --no-cache"

declare -A IDS
declare -A WASMS
declare -A ARGS_DEBUG

log() {
    local step="$1"; shift
    printf '[%s] [%s] %s\n' "$(date +%H:%M:%S)" "$step" "$*" >&2
}

deploy_with_retry() {
    local label="$1"; shift
    local wasm_file="$1"; shift
    local -a ctor_args=("$@")

    log "STEP" "============================================================"
    log "STEP" "▶ Deploying $label ..."

    local wasm_path="$WASM_DIR/$wasm_file"
    if [[ ! -f "$wasm_path" ]]; then
        log "FATAL" "WASM not found: $wasm_path"
        exit 1
    fi
    local size
    size=$(wc -c < "$wasm_path")
    log "FILE" "wasm=$wasm_file size=${size}B"

    local attempt=1
    while (( attempt <= RETRIES )); do
        log "TX" "$label attempt $attempt/$RETRIES"
        set +e
        local output rc
        output=$(
            $STELLAR_CLI contract deploy \
                --source-account "$DEPLOYER_SEED" \
                --wasm "$wasm_path" \
                --resource-fee 500000 \
                --instruction-leeway 5000000 \
                -- "${ctor_args[@]}" \
                2>&1
        )
        rc=$?
        set -e
        local cid
        cid=$(echo "$output" | grep -oE 'C[A-Z0-9]{55}' | tail -1 || true)
        if [[ $rc -eq 0 && -n "$cid" ]]; then
            printf '%s\n' "$output" >&2
            log "STEP" "✅ $label → $cid"
            sleep "$STEP_SLEEP"
            printf '%s\n' "$cid"
            return 0
        fi
        printf '%s\n' "$output" >&2
        log "TX" "$label attempt $attempt FAILED rc=$rc. Sleep ${RETRY_SLEEP}s..."
        if (( attempt < RETRIES )); then
            sleep "$RETRY_SLEEP"
        fi
        ((attempt++))
    done
    log "FATAL" "$label failed after $RETRIES attempts."
    exit 1
}

invoke_with_retry() {
    local cid="$1"; shift
    local fn="$1"; shift
    local -a fn_args=("$@")

    local attempt=1
    while (( attempt <= RETRIES )); do
        log "INVOKE" "$fn @ ${cid:0:16}... attempt $attempt/$RETRIES"
        local rc=0
        $STELLAR_CLI contract invoke \
            --id "$cid" \
            --source-account "$DEPLOYER_SEED" \
            --send=yes \
            --resource-fee 500000 \
            --instruction-leeway 5000000 \
            -- "$fn" "${fn_args[@]}" \
            2>&1 || rc=$?
        if [[ $rc -eq 0 ]]; then
            sleep "$STEP_SLEEP"
            return 0
        fi
        log "INVOKE" "$fn attempt $attempt FAILED rc=$rc. Sleep ${RETRY_SLEEP}s..."
        if (( attempt < RETRIES )); then
            sleep "$RETRY_SLEEP"
        fi
        ((attempt++))
    done
    log "FATAL" "$fn on ${cid:0:16}... failed after $RETRIES attempts."
    exit 1
}

log "NET" "Stellar CLI: $(stellar --version | head -1)"
log "NET" "Network: testnet | RPC: $RPC_URL"
log "NET" "Deployer: $DEPLOYER_PK"

ts_utc=$(date -u +%Y%m%d-%H%M%S)
ts_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# ===== 01 eternal-storage (admin: Address) =====
WASMS[eternal-storage]="eternal_storage.wasm"
IDS[eternal-storage]=$(deploy_with_retry \
    "eternal-storage" "eternal_storage.wasm" \
    "--admin" "$DEPLOYER_PK")
ARGS_DEBUG[eternal-storage]="admin=$DEPLOYER_PK"

# ===== 02 access-control-multisig (owner: Address, threshold_writers: u32) =====
WASMS[access-control-multisig]="access_control_multisig.wasm"
IDS[access-control-multisig]=$(deploy_with_retry \
    "access-control-multisig" "access_control_multisig.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--threshold-writers" "1")
ARGS_DEBUG[access-control-multisig]="owner=$DEPLOYER_PK threshold_writers=1"

# ===== 03 evidence-anchor-v1 (owner: Address) =====
WASMS[evidence-anchor-v1]="evidence_anchor_v1.wasm"
IDS[evidence-anchor-v1]=$(deploy_with_retry \
    "evidence-anchor-v1" "evidence_anchor_v1.wasm" \
    "--owner" "$DEPLOYER_PK")
ARGS_DEBUG[evidence-anchor-v1]="owner=$DEPLOYER_PK"

# ===== 04 protocol-address-book (owner: Address) =====
WASMS[protocol-address-book]="protocol_address_book.wasm"
IDS[protocol-address-book]=$(deploy_with_retry \
    "protocol-address-book" "protocol_address_book.wasm" \
    "--owner" "$DEPLOYER_PK")
ARGS_DEBUG[protocol-address-book]="owner=$DEPLOYER_PK"

# ===== 05 reputation-sbt-badge (owner: Address) =====
WASMS[reputation-sbt-badge]="reputation_sbt_badge.wasm"
IDS[reputation-sbt-badge]=$(deploy_with_retry \
    "reputation-sbt-badge" "reputation_sbt_badge.wasm" \
    "--owner" "$DEPLOYER_PK")
ARGS_DEBUG[reputation-sbt-badge]="owner=$DEPLOYER_PK"

# ===== 06 reputation-scoring-oracle (owner: Address, sbt_contract: Address) =====
WASMS[reputation-scoring-oracle]="reputation_scoring_oracle.wasm"
IDS[reputation-scoring-oracle]=$(deploy_with_retry \
    "reputation-scoring-oracle" "reputation_scoring_oracle.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--sbt-contract" "${IDS[reputation-sbt-badge]}")
ARGS_DEBUG[reputation-scoring-oracle]="owner=$DEPLOYER_PK sbt=${IDS[reputation-sbt-badge]}"

# ===== 07 fee-distribution-multisig (owner, recipients: Vec<Address>, threshold: u32) =====
WASMS[fee-distribution-multisig]="fee_distribution_multisig.wasm"
IDS[fee-distribution-multisig]=$(deploy_with_retry \
    "fee-distribution-multisig" "fee_distribution_multisig.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--recipients" "[\"$DEPLOYER_PK\"]" \
    "--threshold" "1")
ARGS_DEBUG[fee-distribution-multisig]="owner=$DEPLOYER_PK recipients=[$DEPLOYER_PK] threshold=1"

# ===== 08 payment-escrow-v1 (owner, evidence_contract, fee_distributor, base_fee_stroops: i128) =====
WASMS[payment-escrow-v1]="payment_escrow_v1.wasm"
IDS[payment-escrow-v1]=$(deploy_with_retry \
    "payment-escrow-v1" "payment_escrow_v1.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--evidence-contract" "${IDS[evidence-anchor-v1]}" \
    "--fee-distributor" "${IDS[fee-distribution-multisig]}" \
    "--base-fee-stroops" "0")
ARGS_DEBUG[payment-escrow-v1]="owner=$DEPLOYER_PK evidence=${IDS[evidence-anchor-v1]} fee=${IDS[fee-distribution-multisig]} base_fee=0"

# ===== 09 governance-voting-weight-calculator (owner: Address, sbt_contract: Address) =====
WASMS[governance-voting-weight-calculator]="governance_voting_weight_calculator.wasm"
IDS[governance-voting-weight-calculator]=$(deploy_with_retry \
    "governance-voting-weight-calculator" "governance_voting_weight_calculator.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--sbt-contract" "${IDS[reputation-sbt-badge]}")
ARGS_DEBUG[governance-voting-weight-calculator]="owner=$DEPLOYER_PK sbt=${IDS[reputation-sbt-badge]}"

# ===== 10 governance-timelock-controller (owner, guardian: Address, delay_seconds: u64) =====
WASMS[governance-timelock-controller]="governance_timelock_controller.wasm"
IDS[governance-timelock-controller]=$(deploy_with_retry \
    "governance-timelock-controller" "governance_timelock_controller.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--guardian" "$DEPLOYER_PK" \
    "--delay-seconds" "172800")
ARGS_DEBUG[governance-timelock-controller]="owner=$DEPLOYER_PK guardian=$DEPLOYER_PK delay=172800s"

# ===== 11 governance-governor-v1 (owner, weight_calculator, timelock, vote_duration_secs: u64, min_quorum_weight: u32, min_proposer_weight: u32) =====
WASMS[governance-governor-v1]="governance_governor_v1.wasm"
IDS[governance-governor-v1]=$(deploy_with_retry \
    "governance-governor-v1" "governance_governor_v1.wasm" \
    "--owner" "$DEPLOYER_PK" \
    "--weight-calculator" "${IDS[governance-voting-weight-calculator]}" \
    "--timelock" "${IDS[governance-timelock-controller]}" \
    "--vote-duration-secs" "259200" \
    "--min-quorum-weight" "10" \
    "--min-proposer-weight" "1")
ARGS_DEBUG[governance-governor-v1]="owner=$DEPLOYER_PK weight_calc=${IDS[governance-voting-weight-calculator]} timelock=${IDS[governance-timelock-controller]} vote_dur=259200s min_quorum=10 min_proposer=1"

# ===== FINAL REPORT =====
log "FINAL" "============================================================"
log "FINAL" "✅ Todos os ${#IDS[@]} contratos deployados com sucesso!"
for name in \
    "eternal-storage" \
    "access-control-multisig" \
    "evidence-anchor-v1" \
    "protocol-address-book" \
    "reputation-sbt-badge" \
    "reputation-scoring-oracle" \
    "fee-distribution-multisig" \
    "payment-escrow-v1" \
    "governance-voting-weight-calculator" \
    "governance-timelock-controller" \
    "governance-governor-v1"
do
    log "FINAL" "   ${name:40s} → ${IDS[$name]}"
done

# ===== POPULATE PROTOCOL-ADDRESS-BOOK (slots 1..11) =====
log "ADDRBOOK" "============================================================"
log "ADDRBOOK" "Populando protocol-address-book..."
PAB_CID="${IDS[protocol-address-book]}"
SLOT=0
for name in \
    "eternal-storage" \
    "access-control-multisig" \
    "evidence-anchor-v1" \
    "protocol-address-book" \
    "reputation-sbt-badge" \
    "reputation-scoring-oracle" \
    "fee-distribution-multisig" \
    "payment-escrow-v1" \
    "governance-voting-weight-calculator" \
    "governance-timelock-controller" \
    "governance-governor-v1"
do
    SLOT=$((SLOT + 1))
    ADDR="${IDS[$name]}"
    log "ADDRBOOK" "slot=$SLOT $name"
    invoke_with_retry "$PAB_CID" set_address \
        --from "$DEPLOYER_PK" \
        --slot "$SLOT" \
        --contract-address "$ADDR"
done
log "ADDRBOOK" "✅ Address book populado (11 slots)."

# ===== SAVE JSON via Python =====
OUT_PATH="$DEPLOYMENTS_DIR/testnet-$ts_utc.json"

NAMES_ORDERED=(
    "eternal-storage"
    "access-control-multisig"
    "evidence-anchor-v1"
    "protocol-address-book"
    "reputation-sbt-badge"
    "reputation-scoring-oracle"
    "fee-distribution-multisig"
    "payment-escrow-v1"
    "governance-voting-weight-calculator"
    "governance-timelock-controller"
    "governance-governor-v1"
)

export IDS_LIST=""
export WASMS_LIST=""
export ARGS_LIST=""
for nm in "${NAMES_ORDERED[@]}"; do
    IDS_LIST+="${IDS[$nm]}|"
    WASMS_LIST+="${WASMS[$nm]}|"
    ARGS_LIST+="${ARGS_DEBUG[$nm]}|"
done
IDS_LIST="${IDS_LIST%|}"
WASMS_LIST="${WASMS_LIST%|}"
ARGS_LIST="${ARGS_LIST%|}"

export NAMES_LIST
NAMES_LIST="$(IFS='|'; echo "${NAMES_ORDERED[*]}")"

python3 - "$OUT_PATH" "$ts_iso" "$RPC_URL" "$DEPLOYER_PK" "$WASM_DIR" <<PYEOF
import json, sys, os, hashlib
out_path = sys.argv[1]
ts_iso = sys.argv[2]
rpc_url = sys.argv[3]
deployer_pk = sys.argv[4]
wasm_dir = sys.argv[5]

names  = os.environ["NAMES_LIST"].split("|")
ids    = os.environ["IDS_LIST"].split("|")
wasms  = os.environ["WASMS_LIST"].split("|")
argsd  = os.environ["ARGS_LIST"].split("|")

contracts = {}
for i, nm in enumerate(names):
    wasm_file = wasms[i]
    wasm_path = os.path.join(wasm_dir, wasm_file)
    with open(wasm_path, "rb") as f:
        wb = f.read()
    contracts[nm] = {
        "wasm_file": wasm_file,
        "wasm_size_bytes": len(wb),
        "wasm_id_sha256": hashlib.sha256(wb).hexdigest(),
        "contract_id": ids[i],
        "constructor_args_debug": argsd[i],
    }

result = {
    "network": "testnet",
    "rpc": rpc_url,
    "horizon": "https://horizon-testnet.stellar.org",
    "deployer": deployer_pk,
    "timestamp_utc": ts_iso,
    "contracts": contracts,
}
with open(out_path, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"Wrote {out_path}")
PYEOF

LATEST="$DEPLOYMENTS_DIR/testnet-latest.json"
cp -f "$OUT_PATH" "$LATEST"
log "OUTPUT" "Deployments → $OUT_PATH"
log "OUTPUT" "Latest copy  → $LATEST"

log "DONE" "============================================================"
log "DONE" "🎉 Deploy completo! Explore via:"
log "DONE" "  lab.stellar.org/r/testnet/contract/${IDS[eternal-storage]}"
