from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional

SUPPORTED_RPC_PROVIDERS = frozenset({"evm_rpc"})
SUPPORTED_EVM_CHAINS = frozenset({"ethereum", "polygon", "bsc", "arbitrum", "base"})


@dataclass(frozen=True)
class RpcProviderConfig:
    enabled: bool
    primary_url: str
    fallback_url: str
    timeout_ms: int
    max_retries: int


@dataclass(frozen=True)
class RpcProviderOutcome:
    provider_name: str
    provider_status: str
    degraded_reason: Optional[str]
    latest_block_number: Optional[int]
    balance_wei: Optional[int]
    raw_payload: dict[str, Any]
    latency_ms: int
    retries_used: int
    rpc_source: str


@dataclass(frozen=True)
class RpcProviderReadiness:
    provider_name: str
    provider_supported: bool
    enabled: bool
    configured: bool
    ready: bool
    degraded_reason: Optional[str]
    details: dict[str, Any]


def _build_degraded_outcome(
    *,
    provider_name: str = "evm_rpc",
    reason: str,
    latency_ms: int,
    retries_used: int,
    rpc_source: str = "unavailable",
    raw_payload: Optional[dict[str, Any]] = None,
) -> RpcProviderOutcome:
    return RpcProviderOutcome(
        provider_name=provider_name,
        provider_status="degraded",
        degraded_reason=reason,
        latest_block_number=None,
        balance_wei=None,
        raw_payload=raw_payload or {},
        latency_ms=latency_ms,
        retries_used=retries_used,
        rpc_source=rpc_source,
    )


def _coerce_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized.startswith("0x"):
            try:
                return int(normalized, 16)
            except ValueError:
                return None
        if normalized.isdigit():
            return int(normalized)
    return None


def _rpc_call(url: str, *, method: str, params: list[Any], timeout_seconds: float) -> dict[str, Any]:
    request_body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=request_body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _query_evm_rpc(*, url: str, address: str, timeout_seconds: float) -> dict[str, Any]:
    block_payload = _rpc_call(url, method="eth_blockNumber", params=[], timeout_seconds=timeout_seconds)
    balance_payload = _rpc_call(url, method="eth_getBalance", params=[address, "latest"], timeout_seconds=timeout_seconds)
    return {
        "eth_blockNumber": block_payload,
        "eth_getBalance": balance_payload,
    }


def _coerce_live_outcome(*, payload: dict[str, Any], latency_ms: int, retries_used: int, rpc_source: str) -> RpcProviderOutcome:
    latest_block_number = _coerce_int(((payload.get("eth_blockNumber") or {}).get("result")))
    balance_wei = _coerce_int(((payload.get("eth_getBalance") or {}).get("result")))
    if latest_block_number is None:
        return _build_degraded_outcome(
            reason="provider_response_unmapped",
            latency_ms=latency_ms,
            retries_used=retries_used,
            rpc_source=rpc_source,
            raw_payload=payload,
        )
    return RpcProviderOutcome(
        provider_name="evm_rpc",
        provider_status="live",
        degraded_reason=None,
        latest_block_number=latest_block_number,
        balance_wei=balance_wei,
        raw_payload=payload,
        latency_ms=latency_ms,
        retries_used=retries_used,
        rpc_source=rpc_source,
    )


def fetch_chain_context(*, provider_name: str, config: RpcProviderConfig, address: str, chain: str) -> RpcProviderOutcome:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider != "evm_rpc":
        return _build_degraded_outcome(
            provider_name=normalized_provider or "unknown",
            reason="provider_unsupported",
            latency_ms=0,
            retries_used=0,
            raw_payload={
                "requested_provider": provider_name,
                "supported_providers": sorted(SUPPORTED_RPC_PROVIDERS),
            },
        )

    if not config.enabled:
        return _build_degraded_outcome(reason="provider_disabled", latency_ms=0, retries_used=0)

    if chain not in SUPPORTED_EVM_CHAINS:
        return _build_degraded_outcome(
            reason="chain_not_supported",
            latency_ms=0,
            retries_used=0,
            raw_payload={"chain": chain, "supported_chains": sorted(SUPPORTED_EVM_CHAINS)},
        )

    primary_configured = bool(config.primary_url.strip())
    fallback_configured = bool(config.fallback_url.strip())
    if not primary_configured and not fallback_configured:
        return _build_degraded_outcome(reason="provider_not_configured", latency_ms=0, retries_used=0)

    timeout_seconds = max(config.timeout_ms, 1) / 1000
    started_at = time.perf_counter()
    last_raw_payload: dict[str, Any] = {}
    providers_to_try = [("primary", config.primary_url.strip()), ("fallback", config.fallback_url.strip())]
    retries_used = 0

    for source_name, url in providers_to_try:
        if not url:
            continue
        for attempt in range(config.max_retries + 1):
            retries_used = attempt
            try:
                payload = _query_evm_rpc(url=url, address=address, timeout_seconds=timeout_seconds)
                latency_ms = int(round((time.perf_counter() - started_at) * 1000))
                return _coerce_live_outcome(
                    payload=payload,
                    latency_ms=latency_ms,
                    retries_used=retries_used,
                    rpc_source=f"provider_{source_name}",
                )
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_raw_payload = {"source": source_name, "error": str(exc), "url": url}

    latency_ms = int(round((time.perf_counter() - started_at) * 1000))
    return _build_degraded_outcome(
        reason="provider_unavailable",
        latency_ms=latency_ms,
        retries_used=retries_used,
        rpc_source="provider_fallback_exhausted" if fallback_configured else "provider_primary_exhausted",
        raw_payload=last_raw_payload,
    )


def describe_rpc_readiness(*, provider_name: str, config: RpcProviderConfig) -> RpcProviderReadiness:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider != "evm_rpc":
        return RpcProviderReadiness(
            provider_name=normalized_provider or "unknown",
            provider_supported=False,
            enabled=False,
            configured=False,
            ready=False,
            degraded_reason="provider_unsupported",
            details={
                "requested_provider": provider_name,
                "supported_providers": sorted(SUPPORTED_RPC_PROVIDERS),
            },
        )

    primary_configured = bool(config.primary_url.strip())
    fallback_configured = bool(config.fallback_url.strip())
    configured = primary_configured or fallback_configured
    enabled = config.enabled
    degraded_reason = None
    operating_mode = "disabled"
    if not enabled:
        degraded_reason = "provider_disabled"
    elif primary_configured:
        operating_mode = "live"
    elif fallback_configured:
        operating_mode = "fallback_only"
    else:
        degraded_reason = "provider_not_configured"
        operating_mode = "misconfigured"

    return RpcProviderReadiness(
        provider_name="evm_rpc",
        provider_supported=True,
        enabled=enabled,
        configured=configured,
        ready=enabled and configured,
        degraded_reason=degraded_reason,
        details={
            "operating_mode": operating_mode,
            "primary_url_configured": primary_configured,
            "fallback_url_configured": fallback_configured,
            "timeout_ms": config.timeout_ms,
            "max_retries": config.max_retries,
        },
    )
