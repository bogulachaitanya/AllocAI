"""Groq LLM provider implementation.

Uses the Groq OpenAI-compatible API. Credentials are read from env only.
"""

from __future__ import annotations

import logging
from typing import Any

from config.settings import get_settings
from llm.provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq-backed LLM provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._base_url = settings.groq_base_url
        self._model = settings.llm_model
        self._fallback = settings.llm_fallback_model
        self._temperature = settings.llm_temperature
        self._max_tokens = settings.llm_max_tokens

    @property
    def default_model(self) -> str:
        return self._model

    @property
    def fallback_model(self) -> str:
        return self._fallback

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send chat completion; falls back to fallback model on failure."""
        if not self._api_key:
            logger.warning("GROQ_API_KEY not set — returning empty LLM response")
            return ""

        try:
            from openai import OpenAI  # Groq uses OpenAI-compatible client
        except ImportError:
            logger.error("openai package not installed")
            return ""

        client = OpenAI(api_key=self._api_key, base_url=self._base_url)

        use_model = model or self._model
        use_temp = temperature if temperature is not None else self._temperature
        use_tokens = max_tokens or self._max_tokens

        kwargs: dict[str, Any] = {
            "model": use_model,
            "messages": messages,
            "temperature": use_temp,
            "max_tokens": use_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return content
        except Exception as primary_exc:
            logger.warning(
                "Primary model %s failed: %s — retrying with fallback %s",
                use_model,
                primary_exc,
                self._fallback,
            )
            try:
                kwargs["model"] = self._fallback
                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content or ""
            except Exception as fallback_exc:
                logger.error("Fallback model also failed: %s", fallback_exc)
                return ""
