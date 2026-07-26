"""
LLM Provider Abstraction — Anthropic (primary) + Groq (fallback).

Fallback policy:
  - Groq (Llama 3.3 70B) used ONLY when Anthropic latency > 3500ms or unavailable
  - NEVER as quality substitute for critical regulatory decisions
  - Zero-retention policy: no data retained by providers beyond the call
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cached: bool = False
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str = "end_turn"
    error: Optional[str] = None


@dataclass
class ToolCall:
    """Parsed tool call from LLM response."""
    id: str
    name: str
    arguments: dict[str, Any]


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
        timeout_ms: int = 3500,
    ) -> LLMResponse:
        """Send a completion request to the LLM."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com") -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

    async def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self._api_key,
                    base_url=self._base_url,
                )
            except ImportError:
                raise RuntimeError("anthropic package not installed: pip install anthropic")
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
        timeout_ms: int = 3500,
    ) -> LLMResponse:
        client = await self._get_client()
        start = time.monotonic()

        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = await client.messages.create(**kwargs)
            latency_ms = int((time.monotonic() - start) * 1000)

            content = ""
            tool_calls = None
            if response.content:
                for block in response.content:
                    if block.type == "text":
                        content += block.text
                    elif block.type == "tool_use":
                        if tool_calls is None:
                            tool_calls = []
                        tool_calls.append({
                            "id": block.id,
                            "name": block.name,
                            "arguments": block.input,
                        })

            return LLMResponse(
                content=content,
                model=response.model,
                provider="anthropic",
                input_tokens=response.usage.input_tokens if response.usage else 0,
                output_tokens=response.usage.output_tokens if response.usage else 0,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason or "end_turn",
            )

        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "llm.anthropic.error",
                extra={"model": model, "latency_ms": latency_ms, "error": str(e)},
            )
            return LLMResponse(
                content="",
                model=model,
                provider="anthropic",
                latency_ms=latency_ms,
                error=str(e),
            )

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            await client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False


class GroqProvider(LLMProvider):
    """Groq fallback provider (Llama 3.3 70B)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = None

    @property
    def name(self) -> str:
        return "groq"

    async def _get_client(self):
        if self._client is None:
            try:
                import groq
                self._client = groq.AsyncGroq(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("groq package not installed: pip install groq")
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
        timeout_ms: int = 3500,
    ) -> LLMResponse:
        client = await self._get_client()
        start = time.monotonic()

        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = self._convert_tools_to_openai(tools)

            try:
                response = await client.chat.completions.create(**kwargs)
            except Exception as e:
                if tools and "tool_use_failed" in str(e):
                    kwargs.pop("tools", None)
                    response = await client.chat.completions.create(**kwargs)
                else:
                    raise
            latency_ms = int((time.monotonic() - start) * 1000)

            content = response.choices[0].message.content or ""
            tool_calls = None
            if response.choices[0].message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": __import__("json").loads(tc.function.arguments),
                    }
                    for tc in response.choices[0].message.tool_calls
                ]

            return LLMResponse(
                content=content,
                model=response.model,
                provider="groq",
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason or "stop",
            )

        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                "llm.groq.error",
                extra={"model": model, "latency_ms": latency_ms, "error": str(e)},
            )
            return LLMResponse(
                content="",
                model=model,
                provider="groq",
                latency_ms=latency_ms,
                error=str(e),
            )

    @staticmethod
    def _convert_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Anthropic-format tools to OpenAI-compatible format."""
        converted = []
        for tool in tools:
            if "function" in tool:
                converted.append(tool)
            elif "input_schema" in tool:
                converted.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool["input_schema"],
                    },
                })
            else:
                converted.append(tool)
        return converted

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False


class LLMRouter:
    """
    Smart router with automatic fallback.

    Routes to Anthropic by default.
    Falls back to Groq when:
      - Anthropic latency > 3500ms
      - Anthropic returns error
      - Anthropic is unavailable
    """

    FALLBACK_LATENCY_THRESHOLD_MS = 3500

    def __init__(self, anthropic: AnthropicProvider, groq: GroqProvider) -> None:
        self._anthropic = anthropic
        self._groq = groq
        self._anthropic_avg_latency_ms: float = 0.0
        self._call_count: int = 0

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str,
        fallback_model: str = "llama-3.3-70b",
        max_tokens: int = 4096,
        temperature: float = 0.1,
        tools: list[dict[str, Any]] | None = None,
        timeout_ms: int = 3500,
        fallback_enabled: bool = True,
    ) -> LLMResponse:
        """Route completion request with automatic fallback."""

        # Try primary (Anthropic)
        response = await self._anthropic.complete(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools,
            timeout_ms=timeout_ms,
        )

        # Update rolling average latency
        self._call_count += 1
        self._anthropic_avg_latency_ms = (
            (self._anthropic_avg_latency_ms * (self._call_count - 1) + response.latency_ms)
            / self._call_count
        )

        # Check if fallback is needed
        if fallback_enabled and (
            response.error
            or response.latency_ms > self.FALLBACK_LATENCY_THRESHOLD_MS
        ):
            logger.warning(
                "llm.router.fallback_triggered",
                extra={
                    "primary_provider": "anthropic",
                    "primary_latency_ms": response.latency_ms,
                    "primary_error": response.error,
                    "fallback_provider": "groq",
                },
            )

            fallback_response = await self._groq.complete(
                messages=messages,
                model=fallback_model,
                max_tokens=max_tokens,
                temperature=temperature,
                tools=tools,
                timeout_ms=timeout_ms,
            )

            if not fallback_response.error:
                return fallback_response

            # Both failed — return original error
            logger.error(
                "llm.router.both_providers_failed",
                extra={
                    "anthropic_error": response.error,
                    "groq_error": fallback_response.error,
                },
            )

        return response

    async def health_check(self) -> dict[str, bool]:
        """Check health of both providers."""
        return {
            "anthropic": await self._anthropic.health_check(),
            "groq": await self._groq.health_check(),
        }


def create_llm_router(
    anthropic_api_key: str,
    groq_api_key: str,
    anthropic_base_url: str = "https://api.anthropic.com",
) -> LLMRouter:
    """Factory function to create an LLM router."""
    anthropic = AnthropicProvider(api_key=anthropic_api_key, base_url=anthropic_base_url)
    groq = GroqProvider(api_key=groq_api_key)
    return LLMRouter(anthropic=anthropic, groq=groq)
