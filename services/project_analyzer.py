"""Project Analyzer — uses LLM to extract structured requirements from raw input.

The LLM extracts; it does NOT invent employee data.
All raw requirement text is treated as untrusted user input.
"""

from __future__ import annotations

import logging
import time

from llm.prompts import PROJECT_EXTRACTION_SYSTEM, PROJECT_EXTRACTION_USER
from llm.provider import BaseLLMProvider, get_llm_provider
from llm.structured_output import parse_structured_output
from schemas.project import StructuredRequirements

logger = logging.getLogger(__name__)

# Deterministic fallback when LLM fails
_FALLBACK_REQUIREMENTS = StructuredRequirements(
    title="Untitled Project",
    domain="general",
    required_skills=[],
    preferred_skills=[],
    certifications=[],
    seniority_levels=[],
    team_size_min=1,
    team_size_max=5,
    duration_weeks=None,
    key_responsibilities=[],
    risks=[],
    additional_context="Requirement extraction failed — please review manually.",
)


class ProjectAnalyzer:
    """Extracts structured requirements from raw project descriptions."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self._provider = provider or get_llm_provider()

    def analyze(self, raw_requirement: str) -> StructuredRequirements:
        """Parse raw project text into a StructuredRequirements object.

        If LLM extraction fails after retry, returns a deterministic fallback.
        Never invents skills or team composition.
        """
        if not raw_requirement or not raw_requirement.strip():
            logger.warning("ProjectAnalyzer: empty requirement received")
            return _FALLBACK_REQUIREMENTS

        # Sanitize input length (prevent token exhaustion)
        safe_input = raw_requirement[:8000]

        messages = [
            {"role": "system", "content": PROJECT_EXTRACTION_SYSTEM},
            {
                "role": "user",
                "content": PROJECT_EXTRACTION_USER.format(raw_requirement=safe_input),
            },
        ]

        start_time = time.time()
        result = parse_structured_output(
            provider=self._provider,
            messages=messages,
            schema=StructuredRequirements,
            fallback=_FALLBACK_REQUIREMENTS,
        )
        elapsed = time.time() - start_time
        logger.info("LLM requirement extraction: %.1fs", elapsed)

        if result is None:
            logger.error("ProjectAnalyzer: all attempts failed, using fallback")
            return _FALLBACK_REQUIREMENTS

        logger.info(
            "ProjectAnalyzer: extracted requirements — domain=%s, skills=%s",
            result.domain,
            result.required_skills,
        )
        return result
