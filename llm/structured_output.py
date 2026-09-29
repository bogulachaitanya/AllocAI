"""Pydantic-based structured output parsing with validate → retry → fallback."""

from __future__ import annotations

import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from llm.provider import BaseLLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def parse_structured_output[T: BaseModel](
    provider: BaseLLMProvider,
    messages: list[dict[str, str]],
    schema: type[T],
    model: str | None = None,
    max_retries: int = 1,
    fallback: T | None = None,
) -> T | None:
    """
    Call the LLM, parse JSON, validate with Pydantic.

    Strategy:
    1. Call provider.chat()
    2. Parse JSON from response
    3. Validate with Pydantic schema
    4. If invalid: retry once with validation error context
    5. If still invalid: return deterministic fallback or None
    6. Show explicit failure log — never silently hide failures.
    """
    try:
        raw_response = provider.chat(messages=messages, model=model)
    except Exception as e:
        logger.error("LLM connection failed: %s", e)
        return fallback

    for attempt in range(max_retries + 1):
        if attempt > 0:
            # Retry: inject validation error feedback into messages
            retry_messages = [
                *messages,
                {"role": "assistant", "content": raw_response},
                {
                    "role": "user",
                    "content": f"Your previous response could not be parsed as valid JSON "
                    f"or did not match the expected schema. "
                    f"Please return ONLY a valid JSON object matching this schema: "
                    f"{json.dumps(schema.model_json_schema(), indent=2)}",
                },
            ]
            try:
                raw_response = provider.chat(messages=retry_messages, model=model)
            except Exception as e:
                logger.error("LLM connection failed on retry: %s", e)
                return fallback

        result = _try_parse(raw_response, schema)
        if result is not None:
            return result

        if attempt == 0:
            logger.warning(
                "LLM output failed validation (attempt %d). Will retry once.", attempt + 1
            )

    # All attempts exhausted
    logger.error(
        "LLM structured output failed after %d attempt(s). "
        "Using deterministic fallback if available.",
        max_retries + 1,
    )

    if fallback is not None:
        return fallback

    return None


def _try_parse[T: BaseModel](raw: str, schema: type[T]) -> T | None:
    """Extract JSON from raw string and validate against schema."""
    if not raw:
        return None

    # Try to find JSON block in the response
    json_str = _extract_json(raw)
    if json_str is None:
        return None

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.debug("JSON parse error: %s | raw=%r", e, raw[:200])
        return None

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        logger.debug("Schema validation error: %s", e)
        return None


def _extract_json(text: str) -> str | None:
    """Extract JSON block from text, handling markdown code fences."""
    text = text.strip()

    # Try direct parse first
    if text.startswith("{"):
        return text

    # Look for ```json ... ``` or ``` ... ```
    import re

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)

    # Find first { ... } block
    start = text.find("{")
    if start == -1:
        return None
    # Find matching closing brace
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None
