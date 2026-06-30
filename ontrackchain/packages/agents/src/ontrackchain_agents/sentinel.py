from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


AlertType = Literal[
    "NEW_INFLOW",
    "NEW_OUTFLOW",
    "HIGH_RISK_CONTACT",
    "SANCTIONED_CONTACT",
    "BRIDGE_ACTIVITY",
    "MIXER_CONTACT",
    "WALLET_REACTIVATED",
    "UNUSUAL_VOLUME",
    "PATTERN_CHANGE",
    "RISK_SCORE_CHANGE",
]


@dataclass(frozen=True)
class Alert:
    alert_type: AlertType
    address: str
    chain: str
    severity: Literal["low", "medium", "high", "critical"]
    occurred_at: str
    details: dict


class SentinelAgent:
    async def scan_watchlist(self, priority: str) -> list[Alert]:
        return []

    async def send_alert(self, alert: Alert) -> None:
        _ = alert
        return None

