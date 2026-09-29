"""Abstract LLM provider interface.

All LLM interactions go through this abstraction so providers are swappable.
The LLM must never invent employee data.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMMessage(dict):
    """Typed message dict for provider calls."""


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a chat completion request and return the raw response string."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model identifier for this provider."""

    @property
    @abstractmethod
    def fallback_model(self) -> str:
        """The fallback model when the primary fails."""


def get_llm_provider() -> BaseLLMProvider:
    """Factory — returns the configured LLM provider."""
    from config.settings import get_settings
    from llm.groq_provider import GroqProvider

    settings = get_settings()

    if settings.llm_provider.value == "groq":
        return GroqProvider()
    # Add more providers here as needed
    return GroqProvider()
