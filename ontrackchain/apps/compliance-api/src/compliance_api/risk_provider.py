from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import Any, Optional

SUPPORTED_RISK_PROVIDERS = frozenset({"trm_labs"})


@dataclass(frozen=True)
class RiskProviderOutcome:
    provider_name: str
    provider_status: str
    degraded_reason: Optional[str]
    risk_score: Optional[int]
    dimensions: Optional[dict[str, int]]
    raw_payload: dict[str, Any]
    latency_ms: int
    retries_used: int
    score_source: str
    upstream_status_code: Optional[int]
    screening_host: Optional[str]
    request_id_forwarded: bool


@dataclass(frozen=True)
class TrmRiskProviderConfig:
    enabled: bool
    screening_url: str
    api_key: str
    api_key_header: str
    api_key_prefix: str
    timeout_ms: int
    max_retries: int


@dataclass(frozen=True)
class RiskProviderReadiness:
    provider_name: str
    provider_supported: bool
    enabled: bool
    configured: bool
    ready: bool
    degraded_reason: Optional[str]
    details: dict[str, Any]


def _extract_nested_value(payload: Any, candidate_paths: list[tuple[str, ...]]) -> Optional[Any]:
    for path in candidate_paths:
        current = payload
        found = True
        for key in path:
            if not isinstance(current, dict) or key not in current:
                found = False
                break
            current = current[key]
        if found:
            return current
    return None


def _coerce_risk_score(payload: dict[str, Any]) -> Optional[int]:
    candidate = _extract_nested_value(
        payload,
        [
            ("risk_score",),
            ("riskScore",),
            ("score",),
            ("data", "risk_score"),
            ("data", "riskScore"),
            ("data", "score"),
            ("risk", "score"),
            ("wallet", "risk_score"),
            ("wallet", "riskScore"),
        ],
    )
    if candidate is None:
        return None
    if isinstance(candidate, bool):
        return None
    if isinstance(candidate, (int, float)):
        return max(0, min(100, int(round(candidate))))
    if isinstance(candidate, str):
        normalized = candidate.strip()
        if normalized.isdigit():
            return max(0, min(100, int(normalized)))
    return None


def _coerce_dimensions(payload: dict[str, Any]) -> Optional[dict[str, int]]:
    candidate = _extract_nested_value(payload, [("dimensions",), ("risk_dimensions",), ("data", "dimensions")])
    if not isinstance(candidate, dict):
        return None
    expected_keys = ("ownership", "behavioral", "counterparty", "exposure", "aml")
    if not all(key in candidate for key in expected_keys):
        return None
    normalized: dict[str, int] = {}
    for key in expected_keys:
        value = candidate[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        normalized[key] = max(0, min(100, int(round(value))))
    return normalized


def _build_degraded_outcome(
    *,
    provider_name: str = "trm_labs",
    reason: str,
    latency_ms: int,
    retries_used: int,
    raw_payload: Optional[dict[str, Any]] = None,
    upstream_status_code: Optional[int] = None,
    screening_host: Optional[str] = None,
    request_id_forwarded: bool = False,
) -> RiskProviderOutcome:
    return RiskProviderOutcome(
        provider_name=provider_name,
        provider_status="degraded",
        degraded_reason=reason,
        risk_score=None,
        dimensions=None,
        raw_payload=raw_payload or {},
        latency_ms=latency_ms,
        retries_used=retries_used,
        score_source="unavailable",
        upstream_status_code=upstream_status_code,
        screening_host=screening_host,
        request_id_forwarded=request_id_forwarded,
    )


def screen_address_with_trm(
    *,
    config: TrmRiskProviderConfig,
    address: str,
    chain: str,
    entity_name: Optional[str],
    declared_source: Optional[str],
    request_id: Optional[str] = None,
) -> RiskProviderOutcome:
    screening_host = urlparse(config.screening_url).netloc or None
    request_id_forwarded = bool(request_id)
    if not config.enabled:
        return _build_degraded_outcome(
            provider_name="trm_labs",
            reason="provider_disabled",
            latency_ms=0,
            retries_used=0,
            screening_host=screening_host,
            request_id_forwarded=request_id_forwarded,
        )
    if not config.screening_url.strip() or not config.api_key.strip():
        return _build_degraded_outcome(
            provider_name="trm_labs",
            reason="provider_not_configured",
            latency_ms=0,
            retries_used=0,
            screening_host=screening_host,
            request_id_forwarded=request_id_forwarded,
        )

    payload = {
        "address": address,
        "chain": chain,
        "entity_name": entity_name,
        "declared_source": declared_source,
    }
    request_body = json.dumps(payload).encode("utf-8")
    timeout_seconds = max(config.timeout_ms, 1) / 1000
    retries_used = 0
    started_at = time.perf_counter()
    last_raw_payload: dict[str, Any] = {}

    for attempt in range(config.max_retries + 1):
        retries_used = attempt
        try:
            headers = {"content-type": "application/json"}
            headers[config.api_key_header] = f"{config.api_key_prefix}{config.api_key}"
            if request_id:
                headers["X-Request-Id"] = request_id
            request = urllib.request.Request(
                config.screening_url,
                data=request_body,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
                parsed_payload = json.loads(raw_body) if raw_body else {}
                if not isinstance(parsed_payload, dict):
                    parsed_payload = {"raw_response": parsed_payload}
                last_raw_payload = parsed_payload
                risk_score = _coerce_risk_score(parsed_payload)
                dimensions = _coerce_dimensions(parsed_payload)
                latency_ms = int(round((time.perf_counter() - started_at) * 1000))
                if risk_score is None:
                    return _build_degraded_outcome(
                        provider_name="trm_labs",
                        reason="provider_response_unmapped",
                        latency_ms=latency_ms,
                        retries_used=retries_used,
                        raw_payload=last_raw_payload,
                        screening_host=screening_host,
                        request_id_forwarded=request_id_forwarded,
                    )
                return RiskProviderOutcome(
                    provider_name="trm_labs",
                    provider_status="live",
                    degraded_reason=None,
                    risk_score=risk_score,
                    dimensions=dimensions,
                    raw_payload=last_raw_payload,
                    latency_ms=latency_ms,
                    retries_used=retries_used,
                    score_source="provider_live",
                    upstream_status_code=getattr(response, "status", None),
                    screening_host=screening_host,
                    request_id_forwarded=request_id_forwarded,
                )
        except urllib.error.HTTPError as exc:
            if attempt >= config.max_retries:
                latency_ms = int(round((time.perf_counter() - started_at) * 1000))
                return _build_degraded_outcome(
                    provider_name="trm_labs",
                    reason="provider_unavailable",
                    latency_ms=latency_ms,
                    retries_used=retries_used,
                    raw_payload=last_raw_payload,
                    upstream_status_code=exc.code,
                    screening_host=screening_host,
                    request_id_forwarded=request_id_forwarded,
                )
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError):
            if attempt >= config.max_retries:
                latency_ms = int(round((time.perf_counter() - started_at) * 1000))
                return _build_degraded_outcome(
                    provider_name="trm_labs",
                    reason="provider_unavailable",
                    latency_ms=latency_ms,
                    retries_used=retries_used,
                    raw_payload=last_raw_payload,
                    screening_host=screening_host,
                    request_id_forwarded=request_id_forwarded,
                )

    latency_ms = int(round((time.perf_counter() - started_at) * 1000))
    return _build_degraded_outcome(
        provider_name="trm_labs",
        reason="provider_unavailable",
        latency_ms=latency_ms,
        retries_used=retries_used,
        raw_payload=last_raw_payload,
        screening_host=screening_host,
        request_id_forwarded=request_id_forwarded,
    )


def screen_address(
    *,
    provider_name: str,
    trm_config: TrmRiskProviderConfig,
    address: str,
    chain: str,
    entity_name: Optional[str],
    declared_source: Optional[str],
    request_id: Optional[str] = None,
) -> RiskProviderOutcome:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider == "trm_labs":
        return screen_address_with_trm(
            config=trm_config,
            address=address,
            chain=chain,
            entity_name=entity_name,
            declared_source=declared_source,
            request_id=request_id,
        )

    return _build_degraded_outcome(
        provider_name=normalized_provider or "unknown",
        reason="provider_unsupported",
        latency_ms=0,
        retries_used=0,
        raw_payload={
            "requested_provider": provider_name,
            "supported_providers": sorted(SUPPORTED_RISK_PROVIDERS),
        },
        screening_host=None,
        request_id_forwarded=bool(request_id),
    )


def describe_provider_readiness(*, provider_name: str, trm_config: TrmRiskProviderConfig) -> RiskProviderReadiness:
    normalized_provider = provider_name.strip().lower()
    if normalized_provider != "trm_labs":
        return RiskProviderReadiness(
            provider_name=normalized_provider or "unknown",
            provider_supported=False,
            enabled=False,
            configured=False,
            ready=False,
            degraded_reason="provider_unsupported",
            details={
                "requested_provider": provider_name,
                "supported_providers": sorted(SUPPORTED_RISK_PROVIDERS),
            },
        )

    live_configured = bool(trm_config.screening_url.strip()) and bool(trm_config.api_key.strip())
    configured = live_configured
    enabled = trm_config.enabled
    degraded_reason = None
    operating_mode = "disabled"
    if not enabled:
        degraded_reason = "provider_disabled"
    elif live_configured:
        operating_mode = "live"
    elif not configured:
        degraded_reason = "provider_not_configured"
        operating_mode = "misconfigured"

    return RiskProviderReadiness(
        provider_name="trm_labs",
        provider_supported=True,
        enabled=enabled,
        configured=configured,
        ready=enabled and configured,
        degraded_reason=degraded_reason,
        details={
            "operating_mode": operating_mode,
            "screening_url_configured": bool(trm_config.screening_url.strip()),
            "screening_host": urlparse(trm_config.screening_url).netloc or None,
            "api_key_configured": bool(trm_config.api_key.strip()),
            "api_key_header": trm_config.api_key_header,
            "api_key_prefix_configured": bool(trm_config.api_key_prefix),
            "timeout_ms": trm_config.timeout_ms,
            "max_retries": trm_config.max_retries,
        },
    )
