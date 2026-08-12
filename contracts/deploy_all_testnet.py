#!/usr/bin/env python3
"""
Ontrackchain — Soroban Testnet Deploy Script (stellar-sdk v15 / Protocol 27)
Deploy order: bottom-up respecting cross-contract constructor dependencies.
2 transactions per contract: (1) Upload WASM -> wasm_id (2) Create Contract + __constructor inline -> contract_id.
Output: deployments/testnet-<timestamp>.json (gitignored) + stdout log.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent / ".python-local"))

from stellar_sdk import (  # noqa: E402
    Address,
    Keypair,
    Network,
    Server,
    SorobanDataBuilder,
    SorobanServer,
    TransactionBuilder,
    scval,
)

DEPLOY_DIR = Path(__file__).parent.resolve()
WASM_DIR = DEPLOY_DIR / "target" / "wasm32-unknown-unknown" / "release"
DEPLOYMENTS_DIR = DEPLOY_DIR / "deployments"
DEPLOYMENTS_DIR.mkdir(exist_ok=True)
IDENTITY_DIR = DEPLOY_DIR / ".stellar" / "identity"

RPC_URL = "https://soroban-testnet.stellar.org:443"
HORIZON_URL = "https://horizon-testnet.stellar.org"
NETWORK_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE
BASE_FEE_STROOPS = 100_000  # 0.1 XLM max per op
TIMEBOUNDS_SEC = 300
POLL_ATTEMPTS = 40


def log(step: str, msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{step}] {msg}", flush=True)


def load_deployer() -> tuple[Keypair, str]:
    tomls = sorted(IDENTITY_DIR.glob("*.toml"))
    if not tomls:
        raise RuntimeError(f"Nenhuma identidade encontrada em {IDENTITY_DIR}")
    seed = None
    for line in tomls[0].read_text().splitlines():
        if line.strip().startswith("seed_phrase") and "=" in line:
            seed = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    if not seed:
        raise RuntimeError(f"seed_phrase ausente em {tomls[0]}")
    kp = Keypair.from_mnemonic_phrase(seed)
    log("IDENTITY", f"Deployer: {kp.public_key}  (seed file: {tomls[0].name})")
    return kp, kp.public_key


RETRIES_SEND = 25
RETRY_SLEEP_SEC = 8


def soroban_flow(rpc: SorobanServer, horizon: Server, kp: Keypair, builder_factory,
                 tx_label: str, acc) -> tuple[Any, Any, Any]:
    """Build (via factory) -> simulate -> prepare -> sign -> send -> poll. RETRIES on TRY_AGAIN_LATER with sequence rollback.
    builder_factory is a callable: () -> TransactionBuilder  (called FRESH on each retry).
    Returns (send_resp, poll_resp, last_success_simulate_resp)."""
    last_sim = None
    for attempt in range(1, RETRIES_SEND + 1):
        seq_before = acc.sequence
        try:
            builder = builder_factory()
            tx = builder.build()
            sim = rpc.simulate_transaction(tx)
            last_sim = sim
            sim_err = getattr(sim, "error", None)
            if sim_err:
                err_lc = str(sim_err).lower()
                if "BAD_SEQ" in str(sim_err) or "sequence" in err_lc:
                    log("TX", f"{tx_label} attempt{attempt}: simulate sequence desync → reload acc from horizon")
                    fresh = horizon.load_account(kp.public_key)
                    acc.sequence = fresh.sequence
                    time.sleep(RETRY_SLEEP_SEC)
                    continue
                if "missingvalue" in err_lc or "wasm does not exist" in err_lc or "storage" in err_lc:
                    log("TX", f"{tx_label} attempt{attempt}: simulate MissingValue/Wasm not yet visible → ledger lag. Sleep {RETRY_SLEEP_SEC}s & retry")
                    time.sleep(RETRY_SLEEP_SEC)
                    continue
                extras = {}
                for k in ("error", "min_resource_fee", "latest_ledger", "created_contract_ids"):
                    v = getattr(sim, k, None)
                    if v is not None: extras[k] = str(v)[:300]
                raise RuntimeError(f"{tx_label} SIMULATE ERROR: {sim_err}\n{json.dumps(extras, indent=2, default=str)[:2000]}")
            results = getattr(sim, "results", None) or []
            for i, r in enumerate(results):
                r_err = getattr(r, "error", None)
                if r_err:
                    raise RuntimeError(f"{tx_label} SIM result[{i}] error: {r_err}")
            created = getattr(sim, "created_contract_ids", None) or []
            if created:
                log("SIM", f"{tx_label} attempt{attempt}: simulate created_contract_ids = {[c[:16]+'...' for c in created]}")
            tx_prep = rpc.prepare_transaction(tx, sim)
            tx_prep.sign(kp)
            send = rpc.send_transaction(tx_prep)
            tx_hash = send.hash
            send_status = str(getattr(send, "status", "?"))
            log("TX", f"{tx_label} attempt{attempt}: hash={tx_hash[:16]}... send_status={send_status} (seq_before→{acc.sequence})")

            if "TRY_AGAIN_LATER" in send_status:
                # Transaction NOT accepted. Rollback sequence because build incremented it prematurely.
                log("TX", f"{tx_label} attempt{attempt}: TRY_AGAIN_LATER. Rollback seq {acc.sequence}→{seq_before}. Sleep {RETRY_SLEEP_SEC}s…")
                try:
                    acc.sequence = seq_before
                except Exception:
                    # if sequence cannot be set directly, reload from horizon:
                    fresh = horizon.load_account(kp.public_key)
                    acc.sequence = fresh.sequence
                time.sleep(RETRY_SLEEP_SEC)
                continue

            if "ERROR" in send_status:
                errs = {
                    k: (str(v)[:500] if not isinstance(v, (dict, list)) else str(v)[:500])
                    for k, v in vars(send).items()
                    if k not in ("hash", "status")
                }
                err_text = json.dumps(errs, indent=2, default=str)[:3000]
                # Is this BAD_SEQ (txBAD_SEQ)? Retry with fresh sequence from horizon.
                # BAD_SEQ XDR encodes with negative op codes -> base64 contains patterns like ////, nyP=, nyP////7, wQP////7
                if (
                    "txBAD_SEQ" in err_text
                    or "BAD_SEQ" in err_text
                    or "nyP////7" in err_text
                    or "nyP=" in err_text
                    or "////7" in err_text
                    or "wQP" in err_text
                ):
                    log("TX", f"{tx_label} attempt{attempt}: BAD_SEQ send error → reload sequence from horizon + sleep")
                    fresh = horizon.load_account(kp.public_key)
                    acc.sequence = fresh.sequence
                    time.sleep(RETRY_SLEEP_SEC)
                    continue
                raise RuntimeError(f"{tx_label} SEND ERROR tx={tx_hash} status={send_status}\nDETAILS: {err_text}")

            # Status = PENDING (ou outro sucesso). Vamos pollar.
            poll = rpc.poll_transaction(tx_hash, max_attempts=POLL_ATTEMPTS)
            poll_status_raw = getattr(poll, "status", "UNKNOWN")
            poll_status = str(poll_status_raw)
            if "SUCCESS" in poll_status:
                log("TX", f"{tx_label}: CONFIRMED status=SUCCESS ledger={getattr(poll,'ledger', '?')} (took {attempt} attempt(s))")
                return send, poll, sim
            elif "NOT_FOUND" in poll_status and attempt < RETRIES_SEND:
                # Send disse PENDING mas poll deu NOT_FOUND = mempool perdeu a TX.
                log("TX", f"{tx_label} attempt{attempt}: PENDING mas NOT_FOUND no poll. Rollback seq {acc.sequence}→{seq_before}, sleep e retry.")
                try:
                    acc.sequence = seq_before
                except Exception:
                    fresh = horizon.load_account(kp.public_key)
                    acc.sequence = fresh.sequence
                time.sleep(RETRY_SLEEP_SEC)
                continue
            else:
                err = getattr(poll, "result_xdr", None) or getattr(poll, "error", None) or poll
                raise RuntimeError(f"{tx_label} POLL status={poll_status} tx={tx_hash}\n{str(err)[:3000]}")
        except RuntimeError:
            raise
        except Exception as e:
            log("TX", f"{tx_label} attempt{attempt}: EXCEPTION inesperada: {type(e).__name__}: {e}. Sleep e retry…")
            try:
                acc.sequence = seq_before
            except Exception:
                pass
            time.sleep(RETRY_SLEEP_SEC)
    raise RuntimeError(f"{tx_label}: falhou em todos {RETRIES_SEND} envios. Ultimo sim disponivel: {last_sim}")


def extract_first_return(poll_resp: Any) -> Any:
    """Pega return_value da primeira operation (0-index) do resultado confirmado."""
    # stellar-sdk 15: poll_resp.results ou resultado por operation via poll_resp.result_meta_xdr?
    # Tenta varios atributos em ordem de plausibilidade.
    opts = [
        lambda: poll_resp.results[0].value if hasattr(poll_resp, "results") and poll_resp.results else None,
        lambda: poll_resp.return_value if hasattr(poll_resp, "return_value") else None,
        lambda: poll_resp.result if hasattr(poll_resp, "result") else None,
    ]
    for fn in opts:
        try:
            v = fn()
            if v is not None:
                return v
        except Exception:
            continue
    return None


def scv_address(s: str | Address) -> Any:
    raw = s.address if isinstance(s, Address) else str(s)
    return scval.to_address(raw)


def wasm_hash(wasm_bytes: bytes) -> bytes:
    return hashlib.sha256(wasm_bytes).digest()


def deterministic_contract_id(kp: Keypair, wasm_id: bytes) -> str:
    """Compute the deterministic C... contract ID for create_contract with salt=0.
    Uses stellar-sdk v15 compatible XDR API (positional discriminants, SCAddress wrapper).
    """
    from stellar_sdk import xdr as stellar_xdr
    raw_pk = kp.raw_public_key()
    account_id = stellar_xdr.AccountID(stellar_xdr.Uint256(raw_pk))
    sc_address = stellar_xdr.SCAddress(
        stellar_xdr.SCAddressType.SC_ADDRESS_TYPE_ACCOUNT,
        account_id=account_id,
    )
    salt = stellar_xdr.Uint256(b"\x00" * 32)
    preimage_from_addr = stellar_xdr.ContractIDPreimageFromAddress(
        address=sc_address, salt=salt,
    )
    preimage = stellar_xdr.ContractIDPreimage(
        stellar_xdr.ContractIDPreimageType.CONTRACT_ID_PREIMAGE_FROM_ADDRESS,
        from_address=preimage_from_addr,
    )
    executable = stellar_xdr.ContractExecutable(
        stellar_xdr.ContractExecutableType.CONTRACT_EXECUTABLE_WASM,
        wasm_hash=stellar_xdr.Hash(wasm_id),
    )
    args_xdr = stellar_xdr.CreateContractArgs(
        contract_id_preimage=preimage, executable=executable,
    )
    cid_raw = hashlib.sha256(args_xdr.to_xdr_bytes()).digest()
    return Address.from_raw_contract(cid_raw).address


def contract_exists_on_chain(rpc: SorobanServer, contract_id_str: str) -> bool:
    """Quick check: try fetching ledger key for the contract code.
    Returns True if the contract is already deployed (has code storage)."""
    from stellar_sdk import xdr as stellar_xdr
    try:
        cid_sc = stellar_xdr.SCAddress(
            stellar_xdr.SCAddressType.SC_ADDRESS_TYPE_CONTRACT,
            contract_id=stellar_xdr.Hash(
                Address(contract_id_str).to_xdr_sc_address().contract_id.hash
            ),
        )
        ledger_key = stellar_xdr.LedgerKey(
            stellar_xdr.LedgerEntryType.CONTRACT_DATA,
            contract_data=stellar_xdr.LedgerKeyContractData(
                contract=cid_sc,
                key=stellar_xdr.SCVal(
                    stellar_xdr.SCValType.SCV_LEDGER_KEY_CONTRACT_INSTANCE
                ),
                durability=stellar_xdr.ContractDataDurability.PERSISTENT,
            ),
        )
        resp = rpc.get_ledger_entries([ledger_key.to_xdr()])
        entries = getattr(resp, "entries", None) or []
        return len(entries) > 0
    except Exception as _e:
        return False


def txn_builder(acc, deployer_pk: str) -> TransactionBuilder:
    """Reuses the single Account object (caller loaded it ONCE and increments seq after each sign)."""
    tb = TransactionBuilder(
        source_account=acc,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=BASE_FEE_STROOPS,
    )
    now = int(time.time())
    tb.add_time_bounds(min_time=now - 60, max_time=now + TIMEBOUNDS_SEC)
    tb.set_soroban_data(SorobanDataBuilder().build())
    return tb


def upload_wasm(rpc: SorobanServer, horizon: Server, kp: Keypair, name: str, wasm_bytes: bytes, acc) -> bytes:
    """Retorna wasm_id (32 bytes). Usa builder factory para retry on-demand."""
    def factory() -> TransactionBuilder:
        tb = txn_builder(acc, kp.public_key)
        tb.append_upload_contract_wasm_op(contract=wasm_bytes)
        return tb
    _send, _poll, _sim = soroban_flow(rpc, horizon, kp, factory, f"UPLOAD {name}", acc)
    expected = wasm_hash(wasm_bytes)
    log("UPLOAD", f"wasm_id (sha256(wasm)) = {expected.hex()[:16]}...")
    return expected


def create_contract(rpc: SorobanServer, horizon: Server, kp: Keypair, name: str,
                    wasm_id: bytes, deployer_pk: str, constructor_args: list[Any], acc) -> str:
    """Retorna contract_id str formato C...
    SOURCE OF TRUTH = deterministic_contract_id (100% reliable for deployer+wasm+salt=0).
    The tx is still broadcast + confirmed on-chain to actually instantiate the contract."""
    expected_cid = deterministic_contract_id(kp, wasm_id)
    def factory() -> TransactionBuilder:
        tb = txn_builder(acc, deployer_pk)
        tb.append_create_contract_op(
            wasm_id=wasm_id,
            address=deployer_pk,
            constructor_args=constructor_args,
        )
        return tb
    _send, poll, sim = soroban_flow(rpc, horizon, kp, factory, f"CREATE {name}", acc)
    log("CREATE", f"{name} contract_id (deterministic) = {expected_cid}")
    return expected_cid


# ================================================================
# ORDEM DEPLOY BOTTOM-UP + CONSTRUCTORS DEFAULT
# ================================================================
def deploy_all() -> dict[str, Any]:
    kp, deployer_pk = load_deployer()
    rpc = SorobanServer(RPC_URL)
    horizon = Server(horizon_url=HORIZON_URL)

    # Confirm network connectivity: horizon load_account já provou conectividade acima.

    acc = horizon.load_account(deployer_pk)
    log("NET", f"Horizon {HORIZON_URL} — source seq={acc.sequence}")

    # ------------------------------------------------------------------
    # Helper: lookup wasm crate filename
    # ------------------------------------------------------------------
    def wasm_path(crate_kebab: str) -> Path:
        snake = crate_kebab.replace("-", "_")
        p = WASM_DIR / f"{snake}.wasm"
        if not p.exists():
            raise FileNotFoundError(f"WASM ausente: {p}")
        return p

    result: dict[str, Any] = {
        "network": "testnet",
        "rpc": RPC_URL,
        "horizon": HORIZON_URL,
        "deployer": deployer_pk,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contracts": {},
    }

    # --- WORKER --------------------------------------------------
    def deploy_one(crate_kebab: str, constructor_args: list[Any]) -> str:
        name = crate_kebab
        log("STEP", "=" * 60)
        log("STEP", f"▶ Deploying {name} ...")
        p = wasm_path(name)
        wasm_bytes = p.read_bytes()
        log("FILE", f"wasm={p.name} size={len(wasm_bytes)} bytes")
        wid = wasm_hash(wasm_bytes)
        expected_cid = deterministic_contract_id(kp, wid)
        # IDEMPOTENCY: skip if contract already deployed on-chain
        if contract_exists_on_chain(rpc, expected_cid):
            log("SKIP", f"{name} already deployed → {expected_cid}")
            cid = expected_cid
        else:
            wid = upload_wasm(rpc, horizon, kp, name, wasm_bytes, acc)
            cid = create_contract(rpc, horizon, kp, name, wid, deployer_pk, constructor_args, acc)
        result["contracts"][name] = {
            "wasm_file": p.name,
            "wasm_size_bytes": len(wasm_bytes),
            "wasm_id_sha256": wid.hex(),
            "contract_id": cid,
            "constructor_args_debug": [
                "(bytes)" if isinstance(v, (bytes, bytearray)) and len(v) > 32 else str(v)
                for v in constructor_args
            ],
        }
        log("STEP", f"✅ {name} → {cid}")
        return cid

    # 01  eternal-storage  (sem dep)
    ids = {}
    ids["eternal-storage"] = deploy_one(
        "eternal-storage",
        [scv_address(deployer_pk)],
    )

    # 02  access-control-multisig  (sem dep)
    ids["access-control-multisig"] = deploy_one(
        "access-control-multisig",
        [scv_address(deployer_pk), scval.to_uint32(1)],
    )

    # 03  evidence-anchor-v1  (sem dep)
    ids["evidence-anchor-v1"] = deploy_one(
        "evidence-anchor-v1",
        [scv_address(deployer_pk)],
    )

    # 04  protocol-address-book  (sem dep)
    ids["protocol-address-book"] = deploy_one(
        "protocol-address-book",
        [scv_address(deployer_pk)],
    )

    # 05  reputation-sbt-badge  (sem dep)
    ids["reputation-sbt-badge"] = deploy_one(
        "reputation-sbt-badge",
        [scv_address(deployer_pk)],
    )

    # 06  reputation-scoring-oracle  → depende 05 sbt_contract
    ids["reputation-scoring-oracle"] = deploy_one(
        "reputation-scoring-oracle",
        [scv_address(deployer_pk), scv_address(ids["reputation-sbt-badge"])],
    )

    # 07  fee-distribution-multisig  → recipients=[deployer] threshold=1
    ids["fee-distribution-multisig"] = deploy_one(
        "fee-distribution-multisig",
        [
            scv_address(deployer_pk),
            scval.to_vec([scv_address(deployer_pk)]),
            scval.to_uint32(1),
        ],
    )

    # 08  payment-escrow-v1  → depende evidence(03), fee_distributor(07)
    ids["payment-escrow-v1"] = deploy_one(
        "payment-escrow-v1",
        [
            scv_address(deployer_pk),
            scv_address(ids["evidence-anchor-v1"]),
            scv_address(ids["fee-distribution-multisig"]),
            scval.to_int128(0),  # base_fee_stroops = 0 (constructor ja aplica max(1) internamente se >0)
        ],
    )

    # 09  governance-voting-weight-calculator  → depende sbt(05)
    ids["governance-voting-weight-calculator"] = deploy_one(
        "governance-voting-weight-calculator",
        [scv_address(deployer_pk), scv_address(ids["reputation-sbt-badge"])],
    )

    # 10  governance-timelock-controller  → guardian=deployer, delay=172800 (48h)
    ids["governance-timelock-controller"] = deploy_one(
        "governance-timelock-controller",
        [
            scv_address(deployer_pk),
            scv_address(deployer_pk),
            scval.to_uint64(172_800),
        ],
    )

    # 11  governance-governor-v1  → depende weight_calc(09), timelock(10)
    ids["governance-governor-v1"] = deploy_one(
        "governance-governor-v1",
        [
            scv_address(deployer_pk),
            scv_address(ids["governance-voting-weight-calculator"]),
            scv_address(ids["governance-timelock-controller"]),
            scval.to_uint64(259_200),  # 3 dias
            scval.to_uint32(10),        # min_quorum_weight
            scval.to_uint32(1),         # min_proposer_weight
        ],
    )

    log("FINAL", "=" * 60)
    log("FINAL", f"✅ Todos os {len(ids)} contratos deployados com sucesso!")
    for name, cid in ids.items():
        log("FINAL", f"   {name:40s} → {cid}")

    # Save JSON deployments
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_path = DEPLOYMENTS_DIR / f"testnet-{ts}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    log("OUTPUT", f"Deployments salvos → {out_path}")
    # Symlink / copy latest
    latest = DEPLOYMENTS_DIR / "testnet-latest.json"
    try:
        if latest.exists():
            latest.unlink()
        latest.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        log("OUTPUT", f"Latest copy → {latest}")
    except Exception as e:
        log("OUTPUT", f"WARNING (latest copy): {e}")

    return result


if __name__ == "__main__":
    try:
        deploy_all()
    except Exception as exc:
        log("FATAL", f"DEPLOY ABORTADO: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
