"""Feedback request and response schemas."""

from typing import Annotated

from pydantic import BaseModel, Field


class FeedbackAnalyzeRequest(BaseModel):
    """Payload for eloquence analysis."""

    recording_id: str
    transcription: Annotated[str, Field(min_length=1, max_length=100_000)]


class FeedbackScores(BaseModel):
    """Eloquence dimension scores."""

    grammar: int
    vocabulary: int
    filler_words_count: int
    pacing: int
    overall: int


class FeedbackAnalyzeResponse(BaseModel):
    """Structured eloquence feedback returned to clients."""

    scores: FeedbackScores
    feedback_text: dict[str, str]
    improvements: list[str]
    strengths: list[str]
