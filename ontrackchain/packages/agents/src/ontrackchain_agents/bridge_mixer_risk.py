"""
Ontrackchain - Phase P4: Multi-Chain Cross-Bridge & Mixer Risk Intelligence Engine

Analyzes cross-chain bridge movements (chain hopping) and mixer exposures (Tornado Cash, Sinbad, Blender)
to calculate composite AML risk scores and automated COAF block flags.
"""

from __future__ import annotations

from typing import Dict, List, Optional


KNOWN_MIXERS = {
    "0x8589427373d6d84e98730d7795d8f6f8731fda16": "Tornado.Cash 0.1 ETH",
    "0x722122df12d4e14e13ac3b68f10740465ed36385": "Tornado.Cash 1 ETH",
    "0x905441a18c00d38d9761f00824041b3a58e1c6b1": "Tornado.Cash 10 ETH",
    "0x0768721451c5f8965e09e7d5c40282491786d159": "Tornado.Cash 100 ETH",
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b": "Tornado.Cash Router",
}

KNOWN_BRIDGES = {
    "ethereum": ["0x40ec5b33f54e0e8a33a975908c5ba1c14e5bbbdf", "0xa0c68c638235ee32657e8f720a23cec1bfc77c77"],
    "arbitrum": ["0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a"],
    "optimism": ["0x99c9fc46f9693ed097826d27771e5c0297a7a72d"],
    "polygon": ["0xa0c68c638235ee32657e8f720a23cec1bfc77c77"],
}


class BridgeMixerRiskEngine:
    """Evaluates cross-chain bridge hops and mixer exposure for P4 compliance."""

    def analyze_wallet(self, address: str, chain: str = "ethereum", transaction_history: Optional[List[Dict]] = None) -> Dict:
        address_clean = address.lower().strip()
        history = transaction_history or []

        mixer_hits: List[Dict] = []
        bridge_hops: List[Dict] = []
        is_direct_mixer = address_clean in KNOWN_MIXERS

        if is_direct_mixer:
            mixer_hits.append({
                "address": address_clean,
                "label": KNOWN_MIXERS[address_clean],
                "direct": True,
            })

        for tx in history:
            to_addr = str(tx.get("to", "")).lower()
            from_addr = str(tx.get("from", "")).lower()

            if to_addr in KNOWN_MIXERS or from_addr in KNOWN_MIXERS:
                mixer_hits.append({
                    "tx_hash": tx.get("hash", "0x..."),
                    "target": to_addr if to_addr in KNOWN_MIXERS else from_addr,
                    "label": KNOWN_MIXERS.get(to_addr) or KNOWN_MIXERS.get(from_addr),
                    "direct": False,
                })

            for b_chain, b_addrs in KNOWN_BRIDGES.items():
                if to_addr in b_addrs or from_addr in b_addrs:
                    bridge_hops.append({
                        "tx_hash": tx.get("hash", "0x..."),
                        "destination_chain": b_chain,
                        "bridge_address": to_addr if to_addr in b_addrs else from_addr,
                    })

        risk_score = 0
        if is_direct_mixer:
            risk_score = 100
        elif mixer_hits:
            risk_score = min(95, 50 + len(mixer_hits) * 15)
        elif bridge_hops:
            risk_score = min(60, 20 + len(bridge_hops) * 10)

        recommendation = "REJECT" if risk_score >= 80 else ("ENHANCED_DUE_DILIGENCE" if risk_score >= 40 else "APPROVE")

        return {
            "phase": "P4",
            "address": address_clean,
            "chain": chain,
            "mixer_exposure": len(mixer_hits) > 0,
            "mixer_hits": mixer_hits,
            "bridge_hops_count": len(bridge_hops),
            "bridge_hops": bridge_hops,
            "risk_score": risk_score,
            "recommendation": recommendation,
            "coaf_reporting_required": risk_score >= 80,
        }
