"""Tests for LLM structured output parsing."""

from __future__ import annotations

from unittest.mock import MagicMock

from pydantic import BaseModel

from llm.structured_output import _extract_json, parse_structured_output


class SimpleSchema(BaseModel):
    name: str
    value: int


class TestExtractJson:
    def test_plain_json(self) -> None:
        raw = '{"name": "test", "value": 42}'
        result = _extract_json(raw)
        assert result == raw

    def test_json_in_code_fence(self) -> None:
        raw = '```json\n{"name": "test", "value": 42}\n```'
        result = _extract_json(raw)
        assert result is not None
        assert '"name"' in result

    def test_json_embedded_in_text(self) -> None:
        raw = 'Here is the response: {"name": "test", "value": 42} end.'
        result = _extract_json(raw)
        assert result is not None

    def test_no_json_returns_none(self) -> None:
        raw = "This is just text, no JSON here."
        result = _extract_json(raw)
        assert result is None


class TestParseStructuredOutput:
    def test_valid_output_parsed(self) -> None:
        mock_provider = MagicMock()
        mock_provider.chat.return_value = '{"name": "Alice", "value": 10}'
        result = parse_structured_output(
            provider=mock_provider,
            messages=[],
            schema=SimpleSchema,
        )
        assert result is not None
        assert result.name == "Alice"
        assert result.value == 10

    def test_invalid_json_uses_fallback(self) -> None:
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "this is not json at all"
        fallback = SimpleSchema(name="fallback", value=0)
        result = parse_structured_output(
            provider=mock_provider,
            messages=[],
            schema=SimpleSchema,
            fallback=fallback,
        )
        assert result is not None
        assert result.name == "fallback"

    def test_empty_response_uses_fallback(self) -> None:
        mock_provider = MagicMock()
        mock_provider.chat.return_value = ""
        fallback = SimpleSchema(name="empty_fallback", value=-1)
        result = parse_structured_output(
            provider=mock_provider,
            messages=[],
            schema=SimpleSchema,
            fallback=fallback,
        )
        assert result is not None
        assert result.name == "empty_fallback"

    def test_schema_mismatch_retries_and_falls_back(self) -> None:
        mock_provider = MagicMock()
        # Both primary and retry return invalid JSON
        mock_provider.chat.return_value = '{"wrong_field": "bad"}'
        fallback = SimpleSchema(name="safe_fallback", value=99)
        result = parse_structured_output(
            provider=mock_provider,
            messages=[],
            schema=SimpleSchema,
            max_retries=1,
            fallback=fallback,
        )
        assert result is not None
        assert result.name == "safe_fallback"
        assert mock_provider.chat.call_count == 2  # Tried once + 1 retry

    def test_no_fallback_returns_none_on_failure(self) -> None:
        mock_provider = MagicMock()
        mock_provider.chat.return_value = "garbage"
        result = parse_structured_output(
            provider=mock_provider,
            messages=[],
            schema=SimpleSchema,
            fallback=None,
        )
        assert result is None
