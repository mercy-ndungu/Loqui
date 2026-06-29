"""Claude API integration for eloquence analysis."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import anthropic
from anthropic import APIError, APIStatusError
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.config import get_settings
from app.prompts.eloquence import ELOQUENCE_SYSTEM_PROMPT
from app.prompts.topic_generation import TOPIC_GENERATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_OUTPUT_TOKENS = 4096
TOPIC_MAX_OUTPUT_TOKENS = 256


class FillerWordsAnalysis(BaseModel):
    """Filler word breakdown from Claude."""

    count: int = Field(ge=0)
    words: list[str] = Field(default_factory=list, alias="list")
    improvement: str

    model_config = {"populate_by_name": True}


class ClaudeEloquenceResult(BaseModel):
    """Validated structure of Claude's eloquence analysis JSON."""

    grammar_score: int = Field(ge=0, le=100)
    grammar_feedback: str
    vocabulary_score: int = Field(ge=0, le=100)
    vocabulary_feedback: str
    filler_words: FillerWordsAnalysis
    pacing_score: int = Field(ge=0, le=100)
    pacing_feedback: str
    overall_score: int = Field(ge=0, le=100)
    top_3_improvements: list[str]
    strengths: list[str]

    @field_validator("top_3_improvements")
    @classmethod
    def validate_improvements(cls, value: list[str]) -> list[str]:
        """Ensure exactly three improvement items are present."""
        if len(value) < 1:
            raise ValueError("top_3_improvements must not be empty")
        return value[:3]


@dataclass(frozen=True)
class ClaudeUsage:
    """Token usage metadata from a Claude API call."""

    model: str
    input_tokens: int
    output_tokens: int


def _extract_json_payload(text: str) -> dict[str, Any]:
    """Safely extract a JSON object from Claude's response text."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    return json.loads(cleaned)


def parse_claude_response(text: str) -> ClaudeEloquenceResult | None:
    """Parse and validate Claude's JSON analysis response."""
    try:
        payload = _extract_json_payload(text)
        return ClaudeEloquenceResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.error("Failed to parse Claude JSON response: %s", exc)
        return None


def analyze_eloquence(transcription: str) -> tuple[ClaudeEloquenceResult | None, ClaudeUsage | None]:
    """
    Send a transcription to Claude for eloquence analysis.

    Returns parsed analysis and usage metadata, or (None, None) on failure.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is not configured")
        return None, None

    model = settings.claude_model
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=ELOQUENCE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": transcription}],
        )
    except (APIError, APIStatusError) as exc:
        logger.error("Claude API request failed model=%s status=%s", model, getattr(exc, "status_code", "unknown"))
        return None, None
    except Exception as exc:
        logger.error("Unexpected Claude API error model=%s: %s", model, exc)
        return None, None

    text_blocks = [block.text for block in message.content if block.type == "text"]
    if not text_blocks:
        logger.error("Claude API returned no text content model=%s", model)
        return None, None

    usage = ClaudeUsage(
        model=model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )
    result = parse_claude_response("\n".join(text_blocks))
    return result, usage


def generate_speaking_topic() -> tuple[str | None, ClaudeUsage | None]:
    """
    Ask Claude to generate a single speaking topic for the Random Topic Challenge.

    Returns (topic_text, usage) or (None, None) on failure.
    """
    settings = get_settings()
    if not settings.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is not configured for topic generation")
        return None, None

    model = settings.claude_model
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=TOPIC_MAX_OUTPUT_TOKENS,
            system=TOPIC_GENERATION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": "Generate a new speaking topic now.",
                }
            ],
        )
    except (APIError, APIStatusError) as exc:
        logger.error(
            "Claude topic generation failed model=%s status=%s",
            model,
            getattr(exc, "status_code", "unknown"),
        )
        return None, None
    except Exception as exc:
        logger.error("Unexpected Claude topic generation error model=%s: %s", model, exc)
        return None, None

    text_blocks = [block.text for block in message.content if block.type == "text"]
    if not text_blocks:
        logger.error("Claude topic generation returned no text model=%s", model)
        return None, None

    topic = " ".join(text_blocks).strip().strip('"').strip("'").strip("“”")
    topic = topic.split("\n")[0].strip()
    # Strip leading numbering like "1. " or "1) "
    if len(topic) > 2 and topic[0].isdigit() and topic[1] in ".)":
        topic = topic[2:].strip()
    if not topic or len(topic) > 500:
        logger.error("Claude topic generation returned invalid topic length=%d", len(topic))
        return None, None

    usage = ClaudeUsage(
        model=model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )
    logger.info(
        "Claude topic generated model=%s input_tokens=%s output_tokens=%s",
        model,
        usage.input_tokens,
        usage.output_tokens,
    )
    return topic, usage
